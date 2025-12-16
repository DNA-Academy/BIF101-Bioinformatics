#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenoStream Genomic Data Downloader v3.5 (Scientific Integrity Edition)

Purpose
- Reproducible, audit-ready retrieval of public genomics FASTQ/FASTQ.GZ datasets
  (Illumina/Ion for short reads; ONT/PacBio for long reads) via ENA Portal API.
- Streaming subsampling: creates valid FASTQ.GZ subsets without downloading full datasets.

Key Features (v3.5)
- Scientific Integrity Discovery Loop: iterates ENA search candidates and validates metadata+links.
- Strict species validation: prevents "wrong organism" surprises when candidate metadata is inconsistent.
- Multi-part URL support: streams sequentially across multiple FASTQ files (e.g., lanes).
- Paired-End integrity fix (requested):
    Instead of target_bases_short // 2, it estimates mean read length for R1 and R2
    via a small probe and computes reads_needed to hit the desired TOTAL bases.
    Then downloads R1 and R2 using READS-based sync (same read count).
- Fixed manifest schema (audit trail): data/manifest.tsv (stable columns).

Typical Usage
  python download_data.py
  python download_data.py --organism "Staphylococcus aureus" --genome-size 2.8M --strategy WGS
  python download_data.py --organism "Escherichia coli" --genome-size 4.6M --strategy WGS
  python download_data.py --strategy AMPLICON --organism "Staphylococcus aureus" --genome-size 2.8M
  python download_data.py --short-run ERR2935805 --long-run ERR3336961 --genome-size 2.8M --strategy WGS

Notes
- This tool pulls PUBLIC data from ENA; it does not access private/controlled datasets.
- Coverage is approximate; exact coverage depends on read length distribution and quality filtering in downstream QC.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import requests

# -------------------------
# CONFIG
# -------------------------
DATA_DIR_DEFAULT = "data"

ENA_FILEREPORT = "https://www.ebi.ac.uk/ena/portal/api/filereport"
ENA_SEARCH = "https://www.ebi.ac.uk/ena/portal/api/search"

DEFAULT_ORGANISM = "Staphylococcus aureus"
DEFAULT_GENOME_SIZE_BP = 2_800_000  # 2.8 Mb
DEFAULT_STRATEGY = "WGS"            # WGS / AMPLICON / Any

DEFAULT_COV_SHORT = 50              # short-read target coverage
DEFAULT_COV_LONG = 30               # long-read target coverage

DEFAULT_MAX_CANDIDATES = 50
DEFAULT_PROBE_READS = 5000          # probe size to estimate mean read length (per file)

# User-Agent (as requested)
USER_AGENT_DEFAULT = "GenoStream/3.5 (Scientific Integrity Edition) - DNA Academy"

# Fixed, stable manifest schema (v2.5 premium requirement)
MANIFEST_FIELDS = [
    "filename",
    "role",
    "run_accession",
    "sample_accession",
    "study_accession",
    "platform",
    "instrument_model",
    "organism",
    "library_strategy",
    "library_layout",
    "source_urls",
    "subset_mode",
    "target_val",
    "reads",
    "bases",
    "final_mb",
    "coverage_approx",
    "sha256",
    "created_utc",
]

# -------------------------
# DATA STRUCTURES
# -------------------------
@dataclass
class EnaRun:
    run_accession: str
    sample_accession: str
    study_accession: str
    scientific_name: str
    strain: str
    instrument_platform: str
    instrument_model: str
    library_layout: str
    library_strategy: str
    library_source: str
    fastq_urls: List[str]
    submitted_urls: List[str]
    submitted_format: str


# -------------------------
# CORE HELPERS
# -------------------------
def get_utc_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def calculate_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            sha256.update(block)
    return sha256.hexdigest()


def normalize_species(s: str) -> str:
    # strict-ish normalization: lowercase, collapse whitespace
    return " ".join((s or "").strip().lower().split())


def parse_genome_size(size_str: str) -> int:
    s = str(size_str).strip().upper()
    if s.endswith("G"):
        return int(float(s[:-1]) * 1_000_000_000)
    if s.endswith("M"):
        return int(float(s[:-1]) * 1_000_000)
    if s.endswith("K"):
        return int(float(s[:-1]) * 1_000)
    return int(float(s))


def calculate_target_bases(genome_size_bp: int, coverage_x: int) -> int:
    return genome_size_bp * coverage_x


def ftp_path_to_https(url_or_path: str) -> str:
    s = (url_or_path or "").strip()
    if s.startswith("ftp://"):
        s = s[len("ftp://") :]
    if s.startswith("http://"):
        s = "https://" + s[len("http://") :]
    if s.startswith("https://"):
        return s
    return "https://" + s


def parse_semicolon_list(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def get_platform_tag(platform_str: str) -> str:
    p = (platform_str or "").upper()
    if "PACBIO" in p:
        return "PACBIO"
    if "NANOPORE" in p or "OXFORD" in p:
        return "ONT"
    if "ION" in p or "TORRENT" in p:
        return "ION"
    if "ILLUMINA" in p:
        return "ILLUMINA"
    return "SHORTREAD"


def detect_r1_r2(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Returns (r1_urls, r2_urls).
    Supports multi-part lanes. If it cannot confidently detect, falls back:
    - if exactly 2 files: sorted[0]=R1, sorted[1]=R2
    - if exactly 1 file: R1 only (single-end)
    """
    r1, r2 = [], []
    for u in urls:
        ul = u.lower()
        # common ENA naming: *_1.fastq.gz, *_2.fastq.gz
        if "_1.fastq" in ul or "_r1" in ul or ".r1." in ul:
            r1.append(u)
        elif "_2.fastq" in ul or "_r2" in ul or ".r2." in ul:
            r2.append(u)

    if (not r1 or not r2) and len(urls) == 2:
        xs = sorted(urls)
        return [xs[0]], [xs[1]]
    if len(urls) == 1 and not r1:
        return [urls[0]], []
    return r1, r2


# -------------------------
# HTTP (ROBUST)
# -------------------------
def http_get_with_retries(
    session: requests.Session,
    url: str,
    *,
    params: Optional[dict] = None,
    stream: bool = True,
    headers: Optional[dict] = None,
    timeout: Tuple[int, int] = (10, 120),
    retries: int = 4,
    backoff: float = 2.0,
) -> requests.Response:
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 2):
        try:
            r = session.get(
                url,
                params=params,
                stream=stream,
                timeout=timeout,
                allow_redirects=True,
                headers=headers,
            )
            if r.status_code in (429, 500, 502, 503, 504):
                wait = backoff * attempt
                r.close()
                print(f"    ⚠️ HTTP {r.status_code}. retry in {wait:.1f}s ...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e
            wait = backoff * attempt
            if attempt <= retries:
                print(f"    ⚠️ Network error. retry in {wait:.1f}s ... ({e})")
                time.sleep(wait)
                continue
            break
    raise RuntimeError(f"Request failed: {url} | last error: {last_exc}")


# -------------------------
# ENA METADATA
# -------------------------
def get_run_info(session: requests.Session, accession: str) -> Optional[EnaRun]:
    params = {
        "accession": accession,
        "result": "read_run",
        "fields": ",".join(
            [
                "run_accession",
                "sample_accession",
                "study_accession",
                "scientific_name",
                "strain",
                "instrument_platform",
                "instrument_model",
                "library_layout",
                "library_strategy",
                "library_source",
                "fastq_ftp",
                "submitted_ftp",
                "submitted_format",
            ]
        ),
        "format": "tsv",
    }

    try:
        r = http_get_with_retries(session, ENA_FILEREPORT, params=params, stream=False)
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return None

        rec = next(csv.DictReader(lines, delimiter="\t"))

        fastq_urls = [ftp_path_to_https(u) for u in parse_semicolon_list(rec.get("fastq_ftp", ""))]
        submitted_urls = [ftp_path_to_https(u) for u in parse_semicolon_list(rec.get("submitted_ftp", ""))]
        submitted_format = (rec.get("submitted_format") or "").strip()

        # VALIDATION: must have at least one viable FASTQ source
        valid_link = False
        if fastq_urls:
            valid_link = True
        elif submitted_urls and "fastq" in submitted_format.lower():
            valid_link = True

        if not valid_link:
            return None

        return EnaRun(
            run_accession=(rec.get("run_accession") or "").strip(),
            sample_accession=(rec.get("sample_accession") or "").strip(),
            study_accession=(rec.get("study_accession") or "").strip(),
            scientific_name=(rec.get("scientific_name") or "Unknown").strip(),
            strain=(rec.get("strain") or "").strip(),
            instrument_platform=(rec.get("instrument_platform") or "").strip(),
            instrument_model=(rec.get("instrument_model") or "").strip(),
            library_layout=(rec.get("library_layout") or "").strip(),
            library_strategy=(rec.get("library_strategy") or "").strip(),
            library_source=(rec.get("library_source") or "").strip(),
            fastq_urls=fastq_urls,
            submitted_urls=submitted_urls,
            submitted_format=submitted_format,
        )
    except Exception:
        return None


def pick_best_fastq_urls(run: EnaRun) -> List[str]:
    """
    SAFE FASTQ link selection:
    - prefer ENA fastq_ftp (processed FASTQ)
    - else fallback to submitted_ftp if submitted_format includes fastq
    """
    if run.fastq_urls:
        return run.fastq_urls
    if run.submitted_urls and "fastq" in (run.submitted_format or "").lower():
        return run.submitted_urls
    return []


def ena_search_candidates(
    session: requests.Session,
    query: str,
    *,
    limit: int,
) -> List[Dict[str, str]]:
    params = {
        "result": "read_run",
        "query": query,
        "fields": "run_accession,instrument_platform,library_layout,library_strategy",
        "format": "tsv",
        "limit": str(limit),
    }
    r = http_get_with_retries(session, ENA_SEARCH, params=params, stream=False)
    lines = r.text.strip().splitlines()
    if len(lines) < 2:
        return []
    return list(csv.DictReader(lines, delimiter="\t"))


def build_query(scientific_name: str, platform_type: str, strategy: str) -> str:
    """
    platform_type:
      SHORT -> Illumina / Ion Torrent
      LONG  -> ONT / PacBio

    strategy:
      WGS / AMPLICON / Any
    """
    parts: List[str] = [f'scientific_name="{scientific_name}"']

    if platform_type == "SHORT":
        parts.append('(instrument_platform="ILLUMINA" OR instrument_platform="ION_TORRENT")')
        # For short reads, paired is preferable, but we enforce it via 2-phase search below.
    else:
        parts.append('(instrument_platform="OXFORD_NANOPORE" OR instrument_platform="PACBIO_SMRT")')

    if strategy != "Any":
        parts.append(f'library_strategy="{strategy}"')

    # library_source=GENOMIC is usually correct for WGS; for AMPLICON it can still be GENOMIC,
    # but being too strict may reduce hits. We only enforce for WGS.
    if strategy == "WGS":
        parts.append('library_source="GENOMIC"')

    return " AND ".join(parts)


def find_valid_run(
    session: requests.Session,
    scientific_name: str,
    platform_type: str,
    strategy: str,
    *,
    max_candidates: int,
    prefer_paired_illumina: bool = True,
) -> Optional[EnaRun]:
    """
    Context-aware failover:
    - search candidates
    - iterate and validate: metadata present, FASTQ links present, strict species match
    - return first VALID run
    """
    target_species = normalize_species(scientific_name)

    # Two-phase preference for SHORT:
    # 1) Illumina + PAIRED (if requested)
    # 2) general SHORT query (Illumina/Ion any layout)
    queries: List[str] = []
    if platform_type == "SHORT" and prefer_paired_illumina:
        q1 = build_query(scientific_name, platform_type, strategy) + ' AND instrument_platform="ILLUMINA" AND library_layout="PAIRED"'
        queries.append(q1)
        q2 = build_query(scientific_name, platform_type, strategy)
        queries.append(q2)
    else:
        queries.append(build_query(scientific_name, platform_type, strategy))

    for q in queries:
        print(f"🔎 Discovery Loop | {platform_type} | strategy={strategy} | query=\n    {q}")
        try:
            cands = ena_search_candidates(session, q, limit=max_candidates)
        except Exception as e:
            print(f"    ⚠️ ENA search error: {e}")
            continue

        if not cands:
            print("    ⚠️ No candidates returned.")
            continue

        print(f"    found {len(cands)} candidates. Validating...")

        for i, row in enumerate(cands, start=1):
            acc = (row.get("run_accession") or "").strip()
            if not acc:
                continue

            run = get_run_info(session, acc)
            if not run:
                print(f"    [{i}/{len(cands)}] ⚠️ GHOST/BROKEN: {acc} (skip)")
                continue

            # STRICT species validation (Scientific Integrity Patch)
            if normalize_species(run.scientific_name) != target_species:
                print(f"    [{i}/{len(cands)}] ⚠️ SPECIES MISMATCH: {acc} -> '{run.scientific_name}' (skip)")
                continue

            urls = pick_best_fastq_urls(run)
            if not urls:
                print(f"    [{i}/{len(cands)}] ⚠️ NO FASTQ URLS: {acc} (skip)")
                continue

            print(f"    [{i}/{len(cands)}] ✅ VALIDATED: {run.instrument_platform} {run.library_layout} -> {run.run_accession}")
            return run

        print("    ⚠️ All candidates failed validation for this query.")

    return None


def find_long_read_for_sample(
    session: requests.Session,
    sample_accession: str,
    *,
    strategy: str,
    max_candidates: int,
) -> Optional[EnaRun]:
    """
    Prefer same sample_accession for long-read if possible.
    """
    if not sample_accession:
        return None

    q = f'sample_accession="{sample_accession}" AND (instrument_platform="OXFORD_NANOPORE" OR instrument_platform="PACBIO_SMRT")'
    if strategy != "Any":
        q += f' AND library_strategy="{strategy}"'

    print(f"🔎 Sample-match scan for long reads: {sample_accession}")
    try:
        cands = ena_search_candidates(session, q, limit=max_candidates)
    except Exception:
        return None

    for row in cands:
        acc = (row.get("run_accession") or "").strip()
        if not acc:
            continue
        run = get_run_info(session, acc)
        if not run:
            continue
        urls = pick_best_fastq_urls(run)
        if urls:
            return run
    return None


# -------------------------
# STREAMING / SUBSAMPLING
# -------------------------
def iter_lines_from_urls(session: requests.Session, urls: List[str]) -> Iterable[bytes]:
    """
    Multi-part URL support:
    Streams each URL sequentially. If a URL is gz, it is decompressed on-the-fly.
    Yields FASTQ lines as bytes (including newline).
    """
    headers = {"Accept-Encoding": "identity"}
    for url in urls:
        r = http_get_with_retries(session, url, stream=True, headers=headers)
        try:
            r.raw.decode_content = False
            is_gz = url.lower().endswith((".gz", ".gzip"))
            stream_obj = gzip.GzipFile(fileobj=r.raw) if is_gz else r.raw

            while True:
                line = stream_obj.readline()
                if not line:
                    break
                yield line
        finally:
            r.close()


def probe_mean_read_length(session: requests.Session, urls: List[str], *, probe_reads: int) -> Optional[float]:
    """
    Reads a small number of FASTQ records from the stream (without writing to disk)
    and estimates mean read length from the SEQUENCE line.
    """
    if not urls:
        return None

    reads = 0
    bases = 0
    line_mod = 0

    try:
        for line in iter_lines_from_urls(session, [urls[0]]):  # probe only first part (fast)
            line_mod = (line_mod + 1) % 4
            if line_mod == 2:  # sequence line
                bases += len(line.strip())
            if line_mod == 0:  # completed a record
                reads += 1
                if reads >= probe_reads:
                    break
        if reads == 0:
            return None
        return bases / reads
    except Exception:
        return None


def stream_subsample_to_gz(
    session: requests.Session,
    urls: List[str],
    out_path_gz: str,
    *,
    mode: str,
    target_val: int,
    check_every_reads: int = 2000,
    hard_cap_mb: Optional[int] = None,
) -> Tuple[int, int, float]:
    """
    Writes a valid .fastq.gz subset.

    mode:
      READS -> target_val = number of reads (exact stop at record boundary)
      BASES -> target_val = number of bases (approx stop at record boundary)
      MB    -> target_val = compressed output MB (best-effort; overshoot controlled)
    """
    os.makedirs(os.path.dirname(out_path_gz) or ".", exist_ok=True)
    tmp = out_path_gz + ".part"

    reads = 0
    bases = 0
    line_mod = 0

    max_bytes_mb = int(target_val * 1024 * 1024) if mode == "MB" else 0
    cap_bytes = int(hard_cap_mb * 1024 * 1024) if hard_cap_mb else None

    # Overshoot control for MB mode: tighten checks near the limit
    def should_check_now() -> bool:
        if mode != "MB":
            return False
        if reads == 0:
            return False
        # once we approach 90% of target, check more frequently
        current = os.path.getsize(tmp) if os.path.exists(tmp) else 0
        if current >= 0.90 * max_bytes_mb:
            return True
        return (reads % check_every_reads) == 0

    print(f"⬇️  Downloading subset ({mode}={target_val}): {os.path.basename(out_path_gz)}")
    if len(urls) == 1:
        print(f"    -> Source: {urls[0]}")
    else:
        print(f"    -> Sources: {len(urls)} parts (multi-part streaming)")

    try:
        with gzip.open(tmp, "wb") as gz_out:
            for line in iter_lines_from_urls(session, urls):
                gz_out.write(line)
                line_mod = (line_mod + 1) % 4

                if line_mod == 2:
                    bases += len(line.strip())

                if line_mod == 0:
                    reads += 1

                    if mode == "READS" and reads >= target_val:
                        break
                    if mode == "BASES" and bases >= target_val:
                        break

                    if mode == "MB":
                        if should_check_now():
                            gz_out.flush()
                            current_bytes = os.path.getsize(tmp)
                            if current_bytes >= max_bytes_mb:
                                break

                    # Hard cap (guardrail)
                    if cap_bytes is not None and reads % 2000 == 0:
                        gz_out.flush()
                        if os.path.getsize(tmp) >= cap_bytes:
                            print(f"    ⚠️ Hard cap reached: ~{hard_cap_mb} MB (stopping early).")
                            break

        os.replace(tmp, out_path_gz)
        final_mb = file_size_mb(out_path_gz)
        print(f"    ✅ Done: {reads:,} reads | {bases:,} bases | {final_mb:.2f} MB")
        return reads, bases, final_mb

    except Exception as e:
        print(f"    ❌ Stream error: {e}")
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
        return 0, 0, 0.0


# -------------------------
# MANIFEST
# -------------------------
def manifest_append(manifest_path: str, row: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
    file_exists = os.path.exists(manifest_path)

    with open(manifest_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, delimiter="\t")
        if not file_exists:
            writer.writeheader()
        # enforce stable schema order
        writer.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})


# -------------------------
# MAIN PIPELINE
# -------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="GenoStream Genomic Data Downloader v3.5 (Scientific Integrity Edition)")

    ap.add_argument("--out-dir", default=DATA_DIR_DEFAULT, help="Output directory (default: data/)")
    ap.add_argument("--organism", default=DEFAULT_ORGANISM, help='Scientific name, e.g. "Staphylococcus aureus"')
    ap.add_argument("--genome-size", default=str(DEFAULT_GENOME_SIZE_BP), help="Genome size (e.g. 2.8M, 4.6M, 2800000)")
    ap.add_argument("--strategy", default=DEFAULT_STRATEGY, choices=["WGS", "AMPLICON", "Any"], help="Library strategy filter")
    ap.add_argument("--cov-short", type=int, default=DEFAULT_COV_SHORT, help="Target coverage for short reads (x)")
    ap.add_argument("--cov-long", type=int, default=DEFAULT_COV_LONG, help="Target coverage for long reads (x)")

    ap.add_argument("--short-run", default=None, help="Manual short-read run accession (optional override)")
    ap.add_argument("--long-run", default=None, help="Manual long-read run accession (optional override)")

    ap.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES, help="Max ENA candidates to validate per query")
    ap.add_argument("--probe-reads", type=int, default=DEFAULT_PROBE_READS, help="Probe reads for mean length estimation (PE fix)")

    # Optional guardrails (kept conservative / optional)
    ap.add_argument("--cap-short-mb", type=int, default=None, help="Hard cap MB per short-read output file (optional)")
    ap.add_argument("--cap-long-mb", type=int, default=None, help="Hard cap MB for long-read output file (optional)")

    ap.add_argument("--user-agent", default=USER_AGENT_DEFAULT, help="HTTP User-Agent")
    args = ap.parse_args()

    out_dir = args.out_dir
    manifest_path = os.path.join(out_dir, "manifest.tsv")

    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})

    genome_size_bp = parse_genome_size(args.genome_size)
    target_bases_short = calculate_target_bases(genome_size_bp, args.cov_short)
    target_bases_long = calculate_target_bases(genome_size_bp, args.cov_long)

    print("🚀 GenoStream Genomic Data Downloader v3.5 (Scientific Integrity Edition)\n")
    print("📊 Targets")
    print(f"   - Organism:  {args.organism}")
    print(f"   - Strategy:  {args.strategy}")
    print(f"   - Genome:    {genome_size_bp:,} bp")
    print(f"   - Short:     {args.cov_short}x  -> {target_bases_short:,} bases (TOTAL)")
    print(f"   - Long:      {args.cov_long}x  -> {target_bases_long:,} bases\n")

    ts = get_utc_timestamp()

    # -----------------
    # DISCOVERY
    # -----------------
    if args.short_run:
        short_run = get_run_info(session, args.short_run)
        if not short_run:
            raise SystemExit(f"❌ Short-run override is invalid or has no FASTQ links: {args.short_run}")
        # strict organism mismatch warning (do not hard fail on manual override)
        if normalize_species(short_run.scientific_name) != normalize_species(args.organism):
            print(f"⚠️ Manual short-run species differs: '{short_run.scientific_name}' vs '{args.organism}'")
    else:
        short_run = find_valid_run(
            session,
            args.organism,
            "SHORT",
            args.strategy,
            max_candidates=args.max_candidates,
            prefer_paired_illumina=True,
        )
        if not short_run:
            raise SystemExit("❌ Fatal: No VALID short-read dataset found for the given criteria.")

    print(f"ℹ️  Short Read: {short_run.instrument_platform} | {short_run.library_layout} | {short_run.run_accession}")

    # Long-read selection: prefer same sample_accession first (if no manual override)
    if args.long_run:
        long_run = get_run_info(session, args.long_run)
        if not long_run:
            raise SystemExit(f"❌ Long-run override is invalid or has no FASTQ links: {args.long_run}")
        if normalize_species(long_run.scientific_name) != normalize_species(args.organism):
            print(f"⚠️ Manual long-run species differs: '{long_run.scientific_name}' vs '{args.organism}'")
    else:
        long_run = find_long_read_for_sample(
            session,
            short_run.sample_accession,
            strategy=args.strategy,
            max_candidates=args.max_candidates,
        )
        if not long_run:
            long_run = find_valid_run(
                session,
                args.organism,
                "LONG",
                args.strategy,
                max_candidates=args.max_candidates,
                prefer_paired_illumina=False,
            )
        if not long_run:
            raise SystemExit("❌ Fatal: No VALID long-read dataset found for the given criteria.")

    print(f"ℹ️  Long Read:  {long_run.instrument_platform} | {long_run.library_layout} | {long_run.run_accession}")
    if short_run.sample_accession and long_run.sample_accession:
        if short_run.sample_accession == long_run.sample_accession:
            print(f"✅ Sample match: {short_run.sample_accession}")
        else:
            print(f"ℹ️  Sample differs (acceptable for training/QC): short={short_run.sample_accession} | long={long_run.sample_accession}")
    print("")

    # -----------------
    # DOWNLOAD SHORT READS
    # -----------------
    short_urls = pick_best_fastq_urls(short_run)
    if not short_urls:
        raise SystemExit("❌ Short read: no usable FASTQ urls after selection.")

    short_tag = get_platform_tag(short_run.instrument_platform)
    r1_urls, r2_urls = detect_r1_r2(short_urls)

    if short_tag in ("ILLUMINA", "ION"):
        if r2_urls:
            # --- v3.5 FIX (requested): compute reads_needed from mean R1+R2 lengths ---
            print("🧠 Paired-End integrity mode (v3.5): estimating reads_needed via mean R1/R2 length probe ...")
            mean_r1 = probe_mean_read_length(session, r1_urls, probe_reads=args.probe_reads)
            mean_r2 = probe_mean_read_length(session, r2_urls, probe_reads=args.probe_reads)

            if not mean_r1 or not mean_r2 or (mean_r1 + mean_r2) <= 0:
                # Fallback: old safe behavior (still better than //2): use BASES on R1 then sync reads
                print("    ⚠️ Probe failed. Fallback: BASES on R1 (total/2) then sync R2 by READS.")
                target_r1_bases = target_bases_short // 2
                reads_r1, bases_r1, mb_r1 = stream_subsample_to_gz(
                    session,
                    r1_urls,
                    os.path.join(out_dir, f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R1.fastq.gz"),
                    mode="BASES",
                    target_val=target_r1_bases,
                    hard_cap_mb=args.cap_short_mb,
                )
                reads_r2, bases_r2, mb_r2 = stream_subsample_to_gz(
                    session,
                    r2_urls,
                    os.path.join(out_dir, f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R2.fastq.gz"),
                    mode="READS",
                    target_val=reads_r1,
                    hard_cap_mb=args.cap_short_mb,
                )
            else:
                reads_needed = int(math.ceil(target_bases_short / (mean_r1 + mean_r2)))
                print(f"    mean(R1)≈{mean_r1:.1f} bp | mean(R2)≈{mean_r2:.1f} bp | reads_needed≈{reads_needed:,}")

                r1_out = os.path.join(out_dir, f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R1.fastq.gz")
                r2_out = os.path.join(out_dir, f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R2.fastq.gz")

                reads_r1, bases_r1, mb_r1 = stream_subsample_to_gz(
                    session,
                    r1_urls,
                    r1_out,
                    mode="READS",
                    target_val=reads_needed,
                    hard_cap_mb=args.cap_short_mb,
                )
                reads_r2, bases_r2, mb_r2 = stream_subsample_to_gz(
                    session,
                    r2_urls,
                    r2_out,
                    mode="READS",
                    target_val=reads_r1,  # sync to what we actually got on R1
                    hard_cap_mb=args.cap_short_mb,
                )

            # Manifest (stable schema)
            for role, fname, reads, bases, mb in [
                ("SHORT_R1", os.path.basename(f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R1.fastq.gz"), reads_r1, bases_r1, mb_r1),
                ("SHORT_R2", os.path.basename(f"{short_run.run_accession}_ILLUMINA_{args.strategy}_cov{args.cov_short}x_R2.fastq.gz"), reads_r2, bases_r2, mb_r2),
            ]:
                path = os.path.join(out_dir, fname)
                cov = (bases / genome_size_bp) if genome_size_bp > 0 else 0.0
                manifest_append(
                    manifest_path,
                    {
                        "filename": fname,
                        "role": role,
                        "run_accession": short_run.run_accession,
                        "sample_accession": short_run.sample_accession,
                        "study_accession": short_run.study_accession,
                        "platform": short_run.instrument_platform,
                        "instrument_model": short_run.instrument_model,
                        "organism": f"{short_run.scientific_name} {short_run.strain}".strip(),
                        "library_strategy": short_run.library_strategy,
                        "library_layout": short_run.library_layout,
                        "source_urls": ";".join(r1_urls if role == "SHORT_R1" else r2_urls),
                        "subset_mode": "paired_reads_needed" if role == "SHORT_R1" else "paired_sync_reads",
                        "target_val": str(reads if role == "SHORT_R2" else target_bases_short),
                        "reads": str(reads),
                        "bases": str(bases),
                        "final_mb": f"{mb:.2f}",
                        "coverage_approx": f"{cov:.2f}",
                        "sha256": calculate_sha256(path) if os.path.exists(path) else "",
                        "created_utc": ts,
                    },
                )
        else:
            # Single-end short reads
            se_out = os.path.join(out_dir, f"{short_run.run_accession}_{short_tag}_{args.strategy}_cov{args.cov_short}x_SE.fastq.gz")
            reads_s, bases_s, mb_s = stream_subsample_to_gz(
                session,
                r1_urls,
                se_out,
                mode="BASES",
                target_val=target_bases_short,
                hard_cap_mb=args.cap_short_mb,
            )
            cov = (bases_s / genome_size_bp) if genome_size_bp > 0 else 0.0
            manifest_append(
                manifest_path,
                {
                    "filename": os.path.basename(se_out),
                    "role": "SHORT_SE",
                    "run_accession": short_run.run_accession,
                    "sample_accession": short_run.sample_accession,
                    "study_accession": short_run.study_accession,
                    "platform": short_run.instrument_platform,
                    "instrument_model": short_run.instrument_model,
                    "organism": f"{short_run.scientific_name} {short_run.strain}".strip(),
                    "library_strategy": short_run.library_strategy,
                    "library_layout": short_run.library_layout,
                    "source_urls": ";".join(r1_urls),
                    "subset_mode": "target_bases",
                    "target_val": str(target_bases_short),
                    "reads": str(reads_s),
                    "bases": str(bases_s),
                    "final_mb": f"{mb_s:.2f}",
                    "coverage_approx": f"{cov:.2f}",
                    "sha256": calculate_sha256(se_out) if os.path.exists(se_out) else "",
                    "created_utc": ts,
                },
            )
    else:
        print("⚠️ Short platform is not recognized as Illumina/Ion; proceeding with BASES mode on first URL set.")
        se_out = os.path.join(out_dir, f"{short_run.run_accession}_{short_tag}_{args.strategy}_cov{args.cov_short}x_SE.fastq.gz")
        reads_s, bases_s, mb_s = stream_subsample_to_gz(
            session, short_urls, se_out, mode="BASES", target_val=target_bases_short, hard_cap_mb=args.cap_short_mb
        )
        cov = (bases_s / genome_size_bp) if genome_size_bp > 0 else 0.0
        manifest_append(
            manifest_path,
            {
                "filename": os.path.basename(se_out),
                "role": "SHORT_SE",
                "run_accession": short_run.run_accession,
                "sample_accession": short_run.sample_accession,
                "study_accession": short_run.study_accession,
                "platform": short_run.instrument_platform,
                "instrument_model": short_run.instrument_model,
                "organism": f"{short_run.scientific_name} {short_run.strain}".strip(),
                "library_strategy": short_run.library_strategy,
                "library_layout": short_run.library_layout,
                "source_urls": ";".join(short_urls),
                "subset_mode": "target_bases",
                "target_val": str(target_bases_short),
                "reads": str(reads_s),
                "bases": str(bases_s),
                "final_mb": f"{mb_s:.2f}",
                "coverage_approx": f"{cov:.2f}",
                "sha256": calculate_sha256(se_out) if os.path.exists(se_out) else "",
                "created_utc": ts,
            },
        )

    print("\n" + "-" * 56 + "\n")

    # -----------------
    # DOWNLOAD LONG READS
    # -----------------
    long_urls = pick_best_fastq_urls(long_run)
    if not long_urls:
        raise SystemExit("❌ Long read: no usable FASTQ urls after selection.")

    long_tag = get_platform_tag(long_run.instrument_platform)
    long_out = os.path.join(out_dir, f"{long_run.run_accession}_{long_tag}_{args.strategy}_cov{args.cov_long}x.fastq.gz")

    reads_l, bases_l, mb_l = stream_subsample_to_gz(
        session,
        long_urls,
        long_out,
        mode="BASES",
        target_val=target_bases_long,
        check_every_reads=500,   # long reads: check more often
        hard_cap_mb=args.cap_long_mb,
    )

    cov_l = (bases_l / genome_size_bp) if genome_size_bp > 0 else 0.0
    manifest_append(
        manifest_path,
        {
            "filename": os.path.basename(long_out),
            "role": "LONG_READ",
            "run_accession": long_run.run_accession,
            "sample_accession": long_run.sample_accession,
            "study_accession": long_run.study_accession,
            "platform": long_run.instrument_platform,
            "instrument_model": long_run.instrument_model,
            "organism": f"{long_run.scientific_name} {long_run.strain}".strip(),
            "library_strategy": long_run.library_strategy,
            "library_layout": long_run.library_layout,
            "source_urls": ";".join(long_urls),
            "subset_mode": "target_bases",
            "target_val": str(target_bases_long),
            "reads": str(reads_l),
            "bases": str(bases_l),
            "final_mb": f"{mb_l:.2f}",
            "coverage_approx": f"{cov_l:.2f}",
            "sha256": calculate_sha256(long_out) if os.path.exists(long_out) else "",
            "created_utc": ts,
        },
    )

    print("\n🎉 Completed successfully.")
    print(f"   - Output dir:  {out_dir}")
    print(f"   - Manifest:    {manifest_path}")


if __name__ == "__main__":
    main()
