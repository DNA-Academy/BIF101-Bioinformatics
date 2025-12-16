#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DNA Academy – BIF101 Veri İndirici (Enterprise Edition v2.4)

Düzeltmeler & Yenilikler:
1) Fix: Yanlış LS454 verisi yerine kesinleşmiş Illumina Paired-End (ERR2935805) eklendi.
2) Fail-Safe: Eğer veri seti Paired-End (R1+R2) beklenirken Single-End gelirse,
   script çökmek yerine otomatik olarak 'Single-End Modu'na geçer.
3) Robustness: URL ayrıştırma mantığı iyileştirildi.
"""

import os
import csv
import gzip
import time
import hashlib
import datetime
import requests
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

# -------------------------
# AYARLAR
# -------------------------
DATA_DIR = "data"
ENA_FILEREPORT = "https://www.ebi.ac.uk/ena/portal/api/filereport"

# Illumina: ERR2935805 (S. aureus, HiSeq 2500, PAIRED, Verified)
# Nanopore: ERR3336961 (S. aureus, MinION, SINGLE, Verified)
ILLUMINA_ACCESSION = "ERR2935805"
NANOPORE_ACCESSION = "ERR3336961"

TARGET_MB_LONG = 200   # Nanopore hedef boyut (MB)
TARGET_MB_SHORT = 50   # Illumina R1 hedef boyut (MB)

ALLOW_SAMPLE_MISMATCH = True
MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.tsv")
USER_AGENT = "DNA-Academy-BIF101-EnterpriseDownloader/2.4"

# -------------------------
# VERİ YAPILARI
# -------------------------
@dataclass
class EnaRun:
    run_accession: str
    sample_accession: str
    scientific_name: str
    strain: str
    instrument_platform: str
    instrument_model: str
    library_layout: str
    fastq_urls: List[str]

# -------------------------
# HTTP / RETRY ENGINE
# -------------------------
def http_get_with_retries(session: requests.Session, url: str, params: Optional[dict] = None, stream: bool = True, headers: Optional[dict] = None, timeout: Tuple[int, int] = (10, 120), retries: int = 3, backoff: float = 2.0) -> requests.Response:
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            r = session.get(url, params=params, stream=stream, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff * attempt)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e
            if attempt <= retries:
                time.sleep(backoff * attempt)
                continue
            break
    raise RuntimeError(f"İstek başarısız: {url} | Hata: {last_exc}")

# -------------------------
# YARDIMCILAR
# -------------------------
def ftp_path_to_https(url_or_path: str) -> str:
    s = (url_or_path or "").strip()
    if s.startswith("ftp://"): s = s[len("ftp://"):]
    if s.startswith("http://"): s = "https://" + s[len("http://"):]
    if s.startswith("https://"): return s
    return "https://" + s

def detect_r1_r2(urls: List[str]) -> Tuple[List[str], List[str]]:
    r1, r2 = [], []
    for u in urls:
        ul = u.lower()
        if "_1.fastq" in ul or "_r1" in ul: r1.append(u)
        elif "_2.fastq" in ul or "_r2" in ul: r2.append(u)
    
    # Fallback: Eğer standart dışı isimse ve 2 dosya varsa
    if (not r1 or not r2) and len(urls) == 2:
        urls.sort()
        return [urls[0]], [urls[1]]
    
    # Fallback: Sadece 1 dosya varsa R1 kabul et (Single End)
    if len(urls) == 1 and not r1:
        return [urls[0]], []
        
    return r1, r2

def calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            sha256_hash.update(block)
    return sha256_hash.hexdigest()

def file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)

def get_utc_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

# -------------------------
# ENA METADATA
# -------------------------
def get_run_info(session: requests.Session, accession: str) -> Optional[EnaRun]:
    print(f"🔍 Metadata sorgulanıyor: {accession} ...")
    params = {
        "accession": accession,
        "result": "read_run",
        "fields": "run_accession,sample_accession,scientific_name,strain,instrument_platform,instrument_model,library_layout,fastq_ftp,sra_ftp",
        "format": "tsv",
    }
    try:
        r = http_get_with_retries(session, ENA_FILEREPORT, params=params, stream=False)
        lines = r.text.strip().splitlines()
        if len(lines) < 2: return None

        rec = next(csv.DictReader(lines, delimiter="\t"))
        raw_urls = rec.get("fastq_ftp") or rec.get("sra_ftp") or ""
        urls = [ftp_path_to_https(u) for u in raw_urls.split(";") if u.strip()]

        if not urls: return None

        return EnaRun(
            run_accession=(rec.get("run_accession") or "").strip(),
            sample_accession=(rec.get("sample_accession") or "").strip(),
            scientific_name=(rec.get("scientific_name") or "Unknown").strip(),
            strain=(rec.get("strain") or "").strip(),
            instrument_platform=(rec.get("instrument_platform") or "").strip(),
            instrument_model=(rec.get("instrument_model") or "").strip(),
            library_layout=(rec.get("library_layout") or "").strip(),
            fastq_urls=urls,
        )
    except Exception as e:
        print(f"⚠️ Metadata Hatası ({accession}): {e}")
        return None

# -------------------------
# STREAMING ENGINE
# -------------------------
def stream_subsample(session: requests.Session, url: str, out_path_gz: str, *, mode: str, target: int, check_every_reads: int = 5000) -> Tuple[int, float]:
    os.makedirs(os.path.dirname(out_path_gz) or ".", exist_ok=True)
    tmp = out_path_gz + ".part"
    headers = {"Accept-Encoding": "identity"}
    max_bytes = int(target * 1024 * 1024) if mode == "MB" else 0
    read_count = 0
    line_count = 0

    print(f"⬇️  İndiriliyor ({mode}={target}): {os.path.basename(out_path_gz)}")
    print(f"    -> Kaynak: {url}")

    r = http_get_with_retries(session, url, stream=True, headers=headers)
    try:
        r.raw.decode_content = False
        is_gz = url.lower().endswith((".gz", ".gzip"))
        
        if is_gz:
            in_stream = gzip.GzipFile(fileobj=r.raw)
            read_line = in_stream.readline
        else:
            read_line = r.raw.readline

        with gzip.open(tmp, "wb") as gz_out:
            while True:
                line = read_line()
                if not line: break

                gz_out.write(line)
                line_count += 1

                if line_count % 4 == 0:
                    read_count += 1
                    if mode == "READS" and read_count >= target: break
                    if mode == "MB" and (read_count % check_every_reads == 0):
                        gz_out.flush()
                        if os.path.getsize(tmp) >= max_bytes: break

        os.replace(tmp, out_path_gz)
        final_mb = file_size_mb(out_path_gz)
        print(f"    ✅ Tamamlandı: {read_count} reads | {final_mb:.2f} MB")
        return read_count, final_mb

    except Exception as e:
        print(f"    ❌ İndirme Hatası: {e}")
        if os.path.exists(tmp): 
            try: os.remove(tmp)
            except: pass
        return 0, 0.0
    finally:
        r.close()

# -------------------------
# MANIFEST LOGGER
# -------------------------
def manifest_append(row: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(MANIFEST_FILE) or ".", exist_ok=True)
    file_exists = os.path.exists(MANIFEST_FILE)
    with open(MANIFEST_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()), delimiter="\t")
        if not file_exists: writer.writeheader()
        writer.writerow(row)

# -------------------------
# ANA AKIŞ
# -------------------------
def get_consortium_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(MANIFEST_FILE): os.remove(MANIFEST_FILE)
    
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print("🚀 BIF101 Enterprise Veri İndirici (v2.4 Final)\n")

    # 1) METADATA
    ill = get_run_info(session, ILLUMINA_ACCESSION)
    ont = get_run_info(session, NANOPORE_ACCESSION)

    if not ill:
        print(f"❌ Illumina ({ILLUMINA_ACCESSION}) metadata bulunamadı."); return
    if not ont:
        print(f"❌ Nanopore ({NANOPORE_ACCESSION}) metadata bulunamadı."); return

    print(f"ℹ️  Illumina: {ill.instrument_platform} ({ill.library_layout})")
    print(f"ℹ️  Nanopore: {ont.instrument_platform}")

    ts = get_utc_timestamp()

    # 3) ILLUMINA İŞLEMLERİ
    r1_urls, r2_urls = detect_r1_r2(ill.fastq_urls)
    
    if not r1_urls:
        print(f"❌ Illumina dosya URL'leri bulunamadı: {ill.fastq_urls}")
        return

    ill_r1_name = "illumina_R1.fastq.gz"
    ill_r2_name = "illumina_R2.fastq.gz"
    ill_r1_path = os.path.join(DATA_DIR, ill_r1_name)
    ill_r2_path = os.path.join(DATA_DIR, ill_r2_name)
    
    # R1 İndir
    reads_r1, mb_r1 = stream_subsample(session, r1_urls[0], ill_r1_path, mode="MB", target=TARGET_MB_SHORT)
    
    if reads_r1 > 0:
        manifest_append({
            "filename": ill_r1_name, "role": "SHORT_R1", "run_accession": ill.run_accession,
            "sample_accession": ill.sample_accession, "platform": ill.instrument_platform,
            "organism": ill.scientific_name, "source_url": r1_urls[0],
            "subset_mode": "target_mb", "target": str(TARGET_MB_SHORT),
            "reads": str(reads_r1), "final_mb": f"{mb_r1:.2f}",
            "sha256": calculate_sha256(ill_r1_path), "created_utc": ts
        })

        # R2 İndir (Sadece R2 URL'si varsa)
        if r2_urls:
            reads_r2, mb_r2 = stream_subsample(session, r2_urls[0], ill_r2_path, mode="READS", target=reads_r1)
            if reads_r2 > 0:
                manifest_append({
                    "filename": ill_r2_name, "role": "SHORT_R2", "run_accession": ill.run_accession,
                    "sample_accession": ill.sample_accession, "platform": ill.instrument_platform,
                    "organism": ill.scientific_name, "source_url": r2_urls[0],
                    "subset_mode": "target_reads_sync", "target": str(reads_r1),
                    "reads": str(reads_r2), "final_mb": f"{mb_r2:.2f}",
                    "sha256": calculate_sha256(ill_r2_path), "created_utc": ts
                })
        else:
            print("⚠️ UYARI: Paired-End bekleniyordu ama R2 dosyası bulunamadı. Single-End olarak devam ediliyor.")

    print("-" * 40)

    # 4) NANOPORE INDIRME
    if ont.fastq_urls:
        ont_name = "nanopore.fastq.gz"
        ont_path = os.path.join(DATA_DIR, ont_name)
        reads_ont, mb_ont = stream_subsample(session, ont.fastq_urls[0], ont_path, mode="MB", target=TARGET_MB_LONG)
        
        if reads_ont > 0:
            manifest_append({
                "filename": ont_name, "role": "LONG_READ", "run_accession": ont.run_accession,
                "sample_accession": ont.sample_accession, "platform": ont.instrument_platform,
                "organism": ont.scientific_name, "source_url": ont.fastq_urls[0],
                "subset_mode": "target_mb", "target": str(TARGET_MB_LONG),
                "reads": str(reads_ont), "final_mb": f"{mb_ont:.2f}",
                "sha256": calculate_sha256(ont_path), "created_utc": ts
            })
    else:
        print("❌ Nanopore URL bulunamadı.")

    print(f"\n🎉 İşlem Tamamlandı. Detaylı rapor: {MANIFEST_FILE}")

if __name__ == "__main__":
    get_consortium_data()
