#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DNA Academy – GenoStream (Bio-Intelligent Engine v3.1)

Description:
A precision data ingestion pipeline for genomic analysis.
Capabalities:
- Bio-Intelligent Subsampling: Calculates download targets based on genome size and desired coverage (x).
- Omni-Platform Support: Native handling for Illumina, Ion Torrent, PacBio (HiFi), and Oxford Nanopore.
- Strategy-Aware Discovery: Filters specific library strategies (e.g., AMPLICON vs WGS) for targeted analysis.
- Live Stream Processing: Filters and subsets data in-memory without full disk writes.
"""

import os
import csv
import gzip
import time
import hashlib
import datetime
import argparse
import requests
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

# -------------------------
# CONFIGURATION
# -------------------------
DATA_DIR = "data"
ENA_FILEREPORT = "https://www.ebi.ac.uk/ena/portal/api/filereport"
ENA_SEARCH = "https://www.ebi.ac.uk/ena/portal/api/search"

# Defaults
DEFAULT_ORGANISM = "Staphylococcus aureus" 
DEFAULT_GENOME_SIZE = 2800000 # 2.8 Mb
DEFAULT_COVERAGE_SHORT = 50   # 50x
DEFAULT_COVERAGE_LONG = 30    # 30x

MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.tsv")
USER_AGENT = "GenoStream/3.1 (Bio-Intelligent Engine)"

MANIFEST_FIELDS = [
    "filename", "role", "run_accession", "sample_accession", "platform", 
    "organism", "library_strategy", "subset_mode", "target_val", "reads", 
    "bases", "final_mb", "coverage_approx", "sha256", "created_utc"
]

@dataclass
class EnaRun:
    run_accession: str
    sample_accession: str
    scientific_name: str
    instrument_platform: str
    library_layout: str
    library_strategy: str
    fastq_urls: List[str]
    submitted_urls: List[str]
    submitted_format: str

# -------------------------
# CALCULATION ENGINE
# -------------------------
def parse_genome_size(size_str: str) -> int:
    s = str(size_str).upper().strip()
    if s.endswith("G"): return int(float(s[:-1]) * 1_000_000_000)
    if s.endswith("M"): return int(float(s[:-1]) * 1_000_000)
    if s.endswith("K"): return int(float(s[:-1]) * 1_000)
    return int(float(s))

def calculate_target_bases(genome_size: int, coverage: int) -> int:
    return genome_size * coverage

# -------------------------
# HTTP CORE
# -------------------------
def http_get_with_retries(session: requests.Session, url: str, params: Optional[dict] = None, stream: bool = True, headers: Optional[dict] = None, timeout: Tuple[int, int] = (10, 120), retries: int = 3, backoff: float = 2.0) -> requests.Response:
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            r = session.get(url, params=params, stream=stream, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff * attempt); continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e; time.sleep(backoff * attempt); continue
            break
    raise RuntimeError(f"Request Failed: {url} | Error: {last_exc}")

# -------------------------
# UTILITIES
# -------------------------
def ftp_path_to_https(url_or_path: str) -> str:
    s = (url_or_path or "").strip()
    if s.startswith("ftp://"): s = s[len("ftp://"):]
    if s.startswith("http://"): s = "https://" + s[len("http://"):]
    if s.startswith("https://"): return s
    return "https://" + s

def parse_semicolon_list(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]

def detect_r1_r2(urls: List[str]) -> Tuple[List[str], List[str]]:
    r1, r2 = [], []
    for u in urls:
        ul = u.lower()
        if "_1.fastq" in ul or "_r1" in ul: r1.append(u)
        elif "_2.fastq" in ul or "_r2" in ul: r2.append(u)
    if (not r1 or not r2) and len(urls) == 2: urls.sort(); return [urls[0]], [urls[1]]
    if len(urls) == 1 and not r1: return [urls[0]], []
    return r1, r2

def get_platform_tag(platform_str: str) -> str:
    p = (platform_str or "").upper()
    if "PACBIO" in p: return "PACBIO"
    if "NANOPORE" in p or "OXFORD" in p: return "ONT"
    if "ILLUMINA" in p: return "ILLUMINA"
    if "ION" in p or "TORRENT" in p: return "ION"
    return "SHORTREAD"

def calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""): sha256_hash.update(block)
    return sha256_hash.hexdigest()

def file_size_mb(path: str) -> float: return os.path.getsize(path) / (1024 * 1024)
def get_utc_timestamp() -> str: return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

# -------------------------
# DISCOVERY ENGINE
# -------------------------
def search_best_run(session: requests.Session, scientific_name: str, platform_type: str, strategy: str = "WGS") -> Optional[str]:
    print(f"🔎 Discovery: '{scientific_name}' | Plat: {platform_type} | Strategy: {strategy}")
    query_parts = [f'scientific_name="{scientific_name}"']
    
    if platform_type == "SHORT":
        query_parts.append('(instrument_platform="ILLUMINA" OR instrument_platform="ION_TORRENT")')
    else:
        query_parts.append('(instrument_platform="OXFORD_NANOPORE" OR instrument_platform="PACBIO_SMRT")')
        
    if strategy != "Any":
        query_parts.append(f'library_strategy="{strategy}"')
        
    query_parts.append('library_source="GENOMIC"')
    full_query = " AND ".join(query_parts)

    params = {
        "result": "read_run", "query": full_query,
        "fields": "run_accession,fastq_ftp,instrument_platform,library_strategy",
        "format": "tsv", "limit": "20"
    }
    
    try:
        r = http_get_with_retries(session, ENA_SEARCH, params=params, stream=False)
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            print(f"    ❌ No data found for strategy: '{strategy}'")
            return None
        reader = csv.DictReader(lines, delimiter="\t")
        candidates = [row for row in reader if row.get("fastq_ftp")]
        if not candidates: return None
        chosen = candidates[0]
        print(f"    ✅ FOUND: {chosen['instrument_platform']} ({chosen['library_strategy']}) -> {chosen['run_accession']}")
        return chosen['run_accession']
    except Exception as e:
        print(f"    ⚠️ Search Error: {e}")
        return None

# -------------------------
# INGESTION ENGINE
# -------------------------
def get_run_info(session: requests.Session, accession: str) -> Optional[EnaRun]:
    params = {
        "accession": accession, "result": "read_run",
        "fields": "run_accession,sample_accession,scientific_name,instrument_platform,library_layout,library_strategy,fastq_ftp,submitted_ftp,submitted_format",
        "format": "tsv",
    }
    try:
        r = http_get_with_retries(session, ENA_FILEREPORT, params=params, stream=False)
        lines = r.text.strip().splitlines()
        if len(lines) < 2: return None
        rec = next(csv.DictReader(lines, delimiter="\t"))
        return EnaRun(
            run_accession=rec.get("run_accession", "").strip(),
            sample_accession=rec.get("sample_accession", "").strip(),
            scientific_name=rec.get("scientific_name", "Unknown").strip(),
            instrument_platform=rec.get("instrument_platform", "").strip(),
            library_layout=rec.get("library_layout", "").strip(),
            library_strategy=rec.get("library_strategy", "Unknown").strip(),
            fastq_urls=[ftp_path_to_https(u) for u in parse_semicolon_list(rec.get("fastq_ftp"))],
            submitted_urls=[ftp_path_to_https(u) for u in parse_semicolon_list(rec.get("submitted_ftp"))],
            submitted_format=rec.get("submitted_format", "").strip()
        )
    except: return None

def stream_subsample(
    session: requests.Session, 
    url: str, 
    out_path_gz: str, 
    *, 
    mode: str, 
    target_val: int, 
    check_every: int = 2000
) -> Tuple[int, int, float]:
    
    os.makedirs(os.path.dirname(out_path_gz) or ".", exist_ok=True)
    tmp = out_path_gz + ".part"
    headers = {"Accept-Encoding": "identity"}
    limit_mb = int(target_val * 1024 * 1024) if mode == "MB" else 0
    limit_reads = target_val if mode == "READS" else 0
    limit_bases = target_val if mode == "BASES" else 0
    
    reads = 0; bases = 0; line_mod = 0
    print(f"⬇️  Ingesting ({mode}={target_val:,}): {os.path.basename(out_path_gz)}")
    
    r = http_get_with_retries(session, url, stream=True, headers=headers)
    try:
        r.raw.decode_content = False
        is_gz = url.lower().endswith((".gz", ".gzip"))
        in_stream = gzip.GzipFile(fileobj=r.raw) if is_gz else r.raw
        
        with gzip.open(tmp, "wb") as gz_out:
            while True:
                line = in_stream.readline()
                if not line: break
                gz_out.write(line)
                line_mod = (line_mod + 1) % 4
                if line_mod == 2: bases += len(line.strip())
                if line_mod == 0: 
                    reads += 1
                    if mode == "READS" and reads >= limit_reads: break
                    if mode == "BASES" and bases >= limit_bases: break
                    if mode == "MB" and reads % check_every == 0:
                        gz_out.flush()
                        if os.path.getsize(tmp) >= limit_mb: break
                    if mode == "BASES" and reads % 1000 == 0:
                        if bases >= limit_bases: break

        os.replace(tmp, out_path_gz)
        final_mb = file_size_mb(out_path_gz)
        print(f"    ✅ Complete: {reads} reads | {bases} bases | {final_mb:.2f} MB")
        return reads, bases, final_mb
    except Exception as e:
        print(f"    ❌ Stream Error: {e}")
        if os.path.exists(tmp): os.remove(tmp)
        return 0, 0, 0.0
    finally: r.close()

def manifest_append(row: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(MANIFEST_FILE) or ".", exist_ok=True)
    file_exists = os.path.exists(MANIFEST_FILE)
    with open(MANIFEST_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, delimiter="\t")
        if not file_exists: writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})

# -------------------------
# CLI & EXECUTION
# -------------------------
def main():
    ap = argparse.ArgumentParser(description="GenoStream – Bio-Intelligent Data Ingestion")
    ap.add_argument("--organism", default=DEFAULT_ORGANISM)
    ap.add_argument("--genome-size", default=str(DEFAULT_GENOME_SIZE))
    ap.add_argument("--strategy", default="WGS", choices=["WGS", "AMPLICON", "Any"])
    ap.add_argument("--cov-short", type=int, default=DEFAULT_COVERAGE_SHORT)
    ap.add_argument("--cov-long", type=int, default=DEFAULT_COVERAGE_LONG)
    ap.add_argument("--short-read", default=None)
    ap.add_argument("--long-read", default=None)
    ap.add_argument("--user-agent", default=USER_AGENT)
    
    args = ap.parse_args()
    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})
    if os.path.exists(MANIFEST_FILE): os.remove(MANIFEST_FILE)
    
    print("🚀 GenoStream | Bio-Intelligent Engine v3.1\n")
    
    g_size = parse_genome_size(args.genome_size)
    target_bases_short = calculate_target_bases(g_size, args.cov_short)
    target_bases_long = calculate_target_bases(g_size, args.cov_long)
    
    print(f"📊 Precision Targets:")
    print(f"   - Organism: {args.organism}")
    print(f"   - Strategy: {args.strategy}")
    print(f"   - Genome:   {g_size:,} bp")
    print(f"   - Short Read Target: {args.cov_short}x ({target_bases_short:,} bases)")
    print(f"   - Long Read Target:  {args.cov_long}x ({target_bases_long:,} bases)\n")

    # 1. Short Read Discovery
    short_acc = args.short_read
    if not short_acc:
        short_acc = search_best_run(session, args.organism, "SHORT", args.strategy)
        if not short_acc: print("❌ No Short Read data found."); return

    short_run = get_run_info(session, short_acc)
    print(f"ℹ️  Short Read: {short_run.instrument_platform} | {short_run.library_strategy}")

    # 2. Long Read Discovery
    long_acc = args.long_read
    if not long_acc:
        # Prefer matching sample if available, though currently using generic search
        long_acc = search_best_run(session, args.organism, "LONG", args.strategy)

    if not long_acc: print("❌ No Long Read data found."); return
    lr = get_run_info(session, long_acc)
    print(f"ℹ️  Long Read:  {lr.instrument_platform} | {lr.library_strategy}")
    
    ts = get_utc_timestamp()

    # INGESTION - Short Read
    s_urls = short_run.fastq_urls or (short_run.submitted_urls if "fastq" in (short_run.submitted_format or "").lower() else [])
    
    if s_urls:
        plat_tag = get_platform_tag(short_run.instrument_platform)
        if plat_tag == "ION":
            name = f"{short_run.run_accession}_ION_SE.fastq.gz"
            r, b, m = stream_subsample(session, s_urls[0], os.path.join(DATA_DIR, name), mode="BASES", target_val=target_bases_short)
            if r > 0: manifest_append({"filename": name, "role": "SHORT_SE", "run_accession": short_run.run_accession, "platform": "ION_TORRENT", "subset_mode": "target_bases", "reads": str(r), "bases": str(b), "final_mb": f"{m:.2f}", "created_utc": ts})
        else:
            r1, r2 = detect_r1_r2(s_urls)
            r1_name = f"{short_run.run_accession}_R1.fastq.gz"
            target_r1 = int(target_bases_short / 2) if r2 else target_bases_short
            
            r_cnt, b_cnt, m_cnt = stream_subsample(session, r1[0], os.path.join(DATA_DIR, r1_name), mode="BASES", target_val=target_r1)
            
            if r_cnt > 0:
                manifest_append({"filename": r1_name, "role": "SHORT_R1", "run_accession": short_run.run_accession, "platform": "ILLUMINA", "subset_mode": "target_bases", "reads": str(r_cnt), "bases": str(b_cnt), "final_mb": f"{m_cnt:.2f}", "created_utc": ts})
                if r2:
                    r2_name = f"{short_run.run_accession}_R2.fastq.gz"
                    r_cnt2, b_cnt2, m_cnt2 = stream_subsample(session, r2[0], os.path.join(DATA_DIR, r2_name), mode="READS", target_val=r_cnt)
                    manifest_append({"filename": r2_name, "role": "SHORT_R2", "run_accession": short_run.run_accession, "platform": "ILLUMINA", "subset_mode": "target_reads_sync", "reads": str(r_cnt2), "bases": str(b_cnt2), "final_mb": f"{m_cnt2:.2f}", "created_utc": ts})

    # INGESTION - Long Read
    l_urls = lr.fastq_urls or (lr.submitted_urls if "fastq" in (lr.submitted_format or "").lower() else [])
    if l_urls:
        lr_tag = get_platform_tag(lr.instrument_platform)
        name = f"{lr.run_accession}_{lr_tag}.fastq.gz"
        r_l, b_l, m_l = stream_subsample(session, l_urls[0], os.path.join(DATA_DIR, name), mode="BASES", target_val=target_bases_long, check_every=500)
        if r_l > 0:
             manifest_append({"filename": name, "role": "LONG_READ", "run_accession": lr.run_accession, "platform": lr.instrument_platform, "subset_mode": "target_bases", "reads": str(r_l), "bases": str(b_l), "final_mb": f"{m_l:.2f}", "created_utc": ts})

    print(f"\n🎉 Ingestion Complete. Audit Trail: {MANIFEST_FILE}")

if __name__ == "__main__":
    main()
