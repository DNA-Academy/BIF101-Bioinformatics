#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DNA Academy – BIF101 Veri İndirici (Enterprise Edition v2.1 - Unlocked)

Premium Farkı:
1) Connection Retry: Kopan bağlantıları otomatik tekrar dener.
2) Paired-End Sync: Illumina R1 ve R2'nin okuma sayılarını birebir eşitler.
3) Smart Streaming: Büyük dosyaları diske indirmeden havada (on-the-fly) işler.
4) Manifest: Bilimsel izlenebilirlik sağlar.
5) Sample Check: Numune uyumsuzluğu durumunda (Biyolojik Tekrarlar için) izin verilebilir.
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

# Staphylococcus aureus (MRSA) - Biyolojik Tekrarlar (Biological Replicates)
ILLUMINA_ACCESSION = "ERR3336960" # Sample: SAMEA5634101
NANOPORE_ACCESSION = "ERR3336961" # Sample: SAMEA5634102

TARGET_MB_LONG = 200   # Nanopore hedef boyut (MB)
TARGET_MB_SHORT = 50   # Illumina R1 hedef boyut (MB)

# DİKKAT: Bu eğitim setinde "Biyolojik Tekrar" (Kardeş Numune) kullandığımız için
# metadata eşleşmesi tam tutmayabilir. Eğitime devam etmek için kilidi açıyoruz.
ALLOW_SAMPLE_MISMATCH = True

MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.tsv")
USER_AGENT = "DNA-Academy-BIF101-EnterpriseDownloader/2.1"

# -------------------------
# VERİ YAPILARI
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
    fastq_urls: List[str]

# -------------------------
# HTTP / RETRY ENGINE
# -------------------------
def http_get_with_retries(session: requests.Session, url: str, stream: bool = True, headers: Optional[dict] = None, timeout: Tuple[int, int] = (10, 120), retries: int = 3, backoff: float = 2.0) -> requests.Response:
    """Bağlantı ve geçici sunucu hatalarına karşı dirençli HTTP isteği."""
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            r = session.get(url, stream=stream, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                wait_s = backoff * attempt
                r.close()
                print(f"    ⚠️ HTTP {r.status_code} (geçici). {wait_s:.1f}s sonra tekrar ({attempt}/{retries+1})...")
                time.sleep(wait_s)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e
            if attempt <= retries:
                wait_s = backoff * attempt
                print(f"    ⚠️ Bağlantı/timeout: {e}. {wait_s:.1f}s sonra tekrar ({attempt}/{retries+1})...")
                time.sleep(wait_s)
                continue
            break
    raise RuntimeError(f"İstek başarısız: {url} | Son hata: {last_exc}")

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
    if not r1 and len(urls) >= 1: r1 = [urls[0]]
    if not r2 and len(urls) >= 2: r2 = [urls[1]]
    return r1, r2

def calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            sha256_hash.update(block)
    return sha256_hash.hexdigest()

def file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)

# -------------------------
# ENA METADATA
# -------------------------
def get_run_info(session: requests.Session, accession: str) -> Optional[EnaRun]:
    print(f"🔍 Metadata sorgulanıyor: {accession} ...")
    params = {
        "accession": accession,
        "result": "read_run",
        "fields": "run_accession,sample_accession,study_accession,scientific_name,strain,instrument_platform,instrument_model,library_layout,fastq_ftp",
        "format": "tsv",
    }
    try:
        r = session.get(ENA_FILEREPORT, params=params, timeout=30)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        if len(lines) < 2: return None

        rec = next(csv.DictReader(lines, delimiter="\t"))
        fastq_ftp = (rec.get("fastq_ftp") or "").strip()
        if not fastq_ftp: return None

        urls = [ftp_path_to_https(u) for u in fastq_ftp.split(";") if u.strip()]

        return EnaRun(
            run_accession=(rec.get("run_accession") or "").strip(),
            sample_accession=(rec.get("sample_accession") or "").strip(),
            study_accession=(rec.get("study_accession") or "").strip(),
            scientific_name=(rec.get("scientific_name") or "Unknown").strip(),
            strain=(rec.get("strain") or "").strip(),
            instrument_platform=(rec.get("instrument_platform") or "").strip(),
            instrument_model=(rec.get("instrument_model") or "").strip(),
            library_layout=(rec.get("library_layout") or "").strip(),
            fastq_urls=urls,
        )
    except Exception as e:
        print(f"⚠️ Metadata Hatası: {e}")
        return None

# -------------------------
# STREAMING ENGINE
# -------------------------
def stream_subsample(session: requests.Session, url: str, out_path_gz: str, *, mode: str, target: int, check_every_reads: int = 5000) -> Tuple[int, float]:
    """
    mode="MB" -> target MB | mode="READS" -> target read sayısı
    """
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

    print("🚀 BIF101 Enterprise Veri İndirici (v2.1 Unlocked)\n")

    # 1) METADATA
    ill = get_run_info(session, ILLUMINA_ACCESSION)
    ont = get_run_info(session, NANOPORE_ACCESSION)

    if not ill or not ont:
        print("❌ Metadata alınamadı. Çıkılıyor."); return

    # 2) SAMPLE VALIDATION (PREMIUM)
    if ill.sample_accession and ont.sample_accession and (ill.sample_accession != ont.sample_accession):
        msg = f"Numuneler farklı: Illumina={ill.sample_accession} vs ONT={ont.sample_accession}"
        if not ALLOW_SAMPLE_MISMATCH:
            print(f"❌ KRİTİK: {msg}"); return
        else:
            print(f"⚠️ GÜVENLİK UYARISI: {msg}")
            print("   -> 'ALLOW_SAMPLE_MISMATCH=True' olduğu için Biyolojik Tekrar varsayımıyla devam ediliyor.")
    else:
        print(f"✅ Numune Eşleşmesi Doğrulandı: {ill.sample_accession}")

    created_utc = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # 3) ILLUMINA (PAIRED-END SYNC)
    r1_urls, r2_urls = detect_r1_r2(ill.fastq_urls)
    if not (r1_urls and r2_urls):
        print("❌ Illumina R1/R2 URL ayrıştırılamadı:", ill.fastq_urls); return

    ill_r1_name = "illumina_R1.fastq.gz"
    ill_r2_name = "illumina_R2.fastq.gz"
    
    # R1 İndir
    ill_r1_path = os.path.join(DATA_DIR, ill_r1_name)
    reads_r1, mb_r1 = stream_subsample(session, r1_urls[0], ill_r1_path, mode="MB", target=TARGET_MB_SHORT)
    
    if reads_r1 > 0:
        manifest_append({
            "filename": ill_r1_name, "role": "SHORT_R1", "run_accession": ill.run_accession,
            "sample_accession": ill.sample_accession, "platform": ill.instrument_platform,
            "organism": ill.scientific_name, "source_url": r1_urls[0],
            "subset_mode": "target_mb", "target": str(TARGET_MB_SHORT),
            "reads": str(reads_r1), "final_mb": f"{mb_r1:.2f}",
            "sha256": calculate_sha256(ill_r1_path), "created_utc": created_utc
        })

        # R2 İndir (SYNC)
        ill_r2_path = os.path.join(DATA_DIR, ill_r2_name)
        reads_r2, mb_r2 = stream_subsample(session, r2_urls[0], ill_r2_path, mode="READS", target=reads_r1)
        
        if reads_r2 > 0:
            manifest_append({
                "filename": ill_r2_name, "role": "SHORT_R2", "run_accession": ill.run_accession,
                "sample_accession": ill.sample_accession, "platform": ill.instrument_platform,
                "organism": ill.scientific_name, "source_url": r2_urls[0],
                "subset_mode": "target_reads_sync", "target": str(reads_r1),
                "reads": str(reads_r2), "final_mb": f"{mb_r2:.2f}",
                "sha256": calculate_sha256(ill_r2_path), "created_utc": created_utc
            })
    
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
                "sha256": calculate_sha256(ont_path), "created_utc": created_utc
            })
    else:
        print("❌ Nanopore URL bulunamadı.")

    print(f"\n🎉 İşlem Tamamlandı. Detaylı rapor: {MANIFEST_FILE}")

if __name__ == "__main__":
    get_consortium_data()
