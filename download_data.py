#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DNA Academy – BIF101 Veri İndirici (Enterprise Edition v2.2 - AutoPair)

Amaç:
- Aynı BioSample (sample_accession) üzerinden Illumina (PE) + ONT/PacBio (LR) FASTQ(.gz) indirip,
  büyük veriyi TAM indirmeden stream + subsample ile eğitim boyutuna (MB) düşürmek.
- Manifest ile tam izlenebilirlik.

Not:
- ENA "filereport" ile run/sample/study + fastq_ftp alanlarını dinamik çekiyoruz.
"""

import os
import csv
import gzip
import time
import hashlib
import requests
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

# -------------------------
# AYARLAR (SİZİN HEDEFLERİNİZ)
# -------------------------
DATA_DIR = "data"
ENA_FILEREPORT = "https://www.ebi.ac.uk/ena/portal/api/filereport"

# Seed'ler: İsterseniz bunları bırakın; script mismatch olursa otomatik eşleştirmeyi dener.
SEED_ILLUMINA_RUN = "ERR3336960"
SEED_LONGREAD_RUN = "ERR3336961"

# Çıktı boyut hedefleri (gz dosya boyutu)
TARGET_MB_LONG = 200   # ONT/PacBio
TARGET_MB_SHORT = 50   # Illumina R1 (R2 reads ile sync edilecek)

STRICT_SAMPLE_MATCH = True     # premium kural
AUTO_REPAIR_ON_MISMATCH = True # mismatch ise otomatik çözümle

MANIFEST_FILE = os.path.join(DATA_DIR, "manifest.tsv")

# ENA platform kodları
PLATFORM_ILLUMINA = "ILLUMINA"
PLATFORM_LONGREADS = ("OXFORD_NANOPORE", "PACBIO_SMRT")

# -------------------------
# VERİ YAPISI
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
    fastq_bytes: Optional[int] = None

# -------------------------
# GENEL YARDIMCILAR
# -------------------------
def ftp_path_to_https(url_or_path: str) -> str:
    s = (url_or_path or "").strip()
    if s.startswith("ftp://"):
        s = s[len("ftp://"):]
    if s.startswith("http://"):
        s = "https://" + s[len("http://"):]
    if s.startswith("https://"):
        return s
    return "https://" + s

def parse_sizes(s: str) -> Optional[int]:
    # ENA bazen ";" ile çoklu dosya boyutu döner (PE vb.)
    parts = [p.strip() for p in (s or "").split(";") if p.strip().isdigit()]
    return sum(int(x) for x in parts) if parts else None

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# -------------------------
# HTTP RETRY
# -------------------------
def http_get_with_retries(
    session: requests.Session,
    url: str,
    *,
    stream: bool = True,
    retries: int = 4,
    backoff: float = 2.0,
    headers: Optional[dict] = None,
    timeout: Tuple[int, int] = (10, 180),
) -> requests.Response:
    headers = headers or {}
    last_err = None
    for attempt in range(1, retries + 2):
        try:
            r = session.get(url, stream=stream, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                r.close()
                time.sleep(backoff * attempt)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_err = e
            if attempt <= retries:
                time.sleep(backoff * attempt)
                continue
            break
    raise RuntimeError(f"HTTP başarısız: {url} | Hata: {last_err}")

# -------------------------
# ENA API
# -------------------------
def ena_filereport(session: requests.Session, accession: str, fields: str, result: str = "read_run") -> List[Dict[str, str]]:
    params = {
        "accession": accession,
        "result": result,
        "fields": fields,
        "format": "tsv",
    }
    r = http_get_with_retries(session, ENA_FILEREPORT, stream=False, retries=3, backoff=2.0, timeout=(10, 60), headers=None)
    # Yukarıdaki satır ENA_FILEREPORT'a yanlış olur: url sabit, param lazım.
    # requests.get paramları için ayrı çağrı yapalım:
    r.close()
    try:
        rr = session.get(ENA_FILEREPORT, params=params, timeout=(10, 60))
        rr.raise_for_status()
        lines = rr.text.strip().splitlines()
        if len(lines) < 2:
            return []
        return list(csv.DictReader(lines, delimiter="\t"))
    except Exception as e:
        print(f"⚠️ ENA filereport hatası ({accession}): {e}")
        return []

def get_run_info(session: requests.Session, run_accession: str) -> Optional[EnaRun]:
    print(f"🔍 Metadata sorgulanıyor: {run_accession} ...")
    fields = ",".join([
        "run_accession",
        "sample_accession",
        "study_accession",
        "scientific_name",
        "strain",
        "instrument_platform",
        "instrument_model",
        "library_layout",
        "fastq_ftp",
        "fastq_bytes",
    ])
    recs = ena_filereport(session, run_accession, fields=fields, result="read_run")
    if not recs:
        return None
    rec = recs[0]
    urls = [ftp_path_to_https(u) for u in (rec.get("fastq_ftp") or "").split(";") if u.strip()]
    return EnaRun(
        run_accession=rec.get("run_accession", run_accession),
        sample_accession=rec.get("sample_accession", ""),
        study_accession=rec.get("study_accession", ""),
        scientific_name=rec.get("scientific_name", "Unknown"),
        strain=rec.get("strain", ""),
        instrument_platform=rec.get("instrument_platform", ""),
        instrument_model=rec.get("instrument_model", ""),
        library_layout=rec.get("library_layout", ""),
        fastq_urls=urls,
        fastq_bytes=parse_sizes(rec.get("fastq_bytes") or ""),
    )

def list_runs_for_sample(session: requests.Session, sample_accession: str) -> List[EnaRun]:
    fields = ",".join([
        "run_accession",
        "sample_accession",
        "study_accession",
        "scientific_name",
        "strain",
        "instrument_platform",
        "instrument_model",
        "library_layout",
        "fastq_ftp",
        "fastq_bytes",
    ])
    recs = ena_filereport(session, sample_accession, fields=fields, result="read_run")
    runs = []
    for rec in recs:
        urls = [ftp_path_to_https(u) for u in (rec.get("fastq_ftp") or "").split(";") if u.strip()]
        if not urls:
            continue
        runs.append(EnaRun(
            run_accession=rec.get("run_accession", ""),
            sample_accession=rec.get("sample_accession", sample_accession),
            study_accession=rec.get("study_accession", ""),
            scientific_name=rec.get("scientific_name", "Unknown"),
            strain=rec.get("strain", ""),
            instrument_platform=rec.get("instrument_platform", ""),
            instrument_model=rec.get("instrument_model", ""),
            library_layout=rec.get("library_layout", ""),
            fastq_urls=urls,
            fastq_bytes=parse_sizes(rec.get("fastq_bytes") or ""),
        ))
    return runs

def list_runs_for_study(session: requests.Session, study_accession: str) -> List[EnaRun]:
    fields = ",".join([
        "run_accession",
        "sample_accession",
        "study_accession",
        "scientific_name",
        "strain",
        "instrument_platform",
        "instrument_model",
        "library_layout",
        "fastq_ftp",
        "fastq_bytes",
    ])
    recs = ena_filereport(session, study_accession, fields=fields, result="read_run")
    runs = []
    for rec in recs:
        urls = [ftp_path_to_https(u) for u in (rec.get("fastq_ftp") or "").split(";") if u.strip()]
        if not urls:
            continue
        runs.append(EnaRun(
            run_accession=rec.get("run_accession", ""),
            sample_accession=rec.get("sample_accession", ""),
            study_accession=rec.get("study_accession", study_accession),
            scientific_name=rec.get("scientific_name", "Unknown"),
            strain=rec.get("strain", ""),
            instrument_platform=rec.get("instrument_platform", ""),
            instrument_model=rec.get("instrument_model", ""),
            library_layout=rec.get("library_layout", ""),
            fastq_urls=urls,
            fastq_bytes=parse_sizes(rec.get("fastq_bytes") or ""),
        ))
    return runs

# -------------------------
# RUN SEÇİMİ (PREMIUM)
# -------------------------
def pick_best_illumina(runs: List[EnaRun]) -> Optional[EnaRun]:
    cands = []
    for r in runs:
        if r.instrument_platform != PLATFORM_ILLUMINA:
            continue
        # PE tercih
        pe_bonus = 0 if (r.library_layout.upper() == "PAIRED" and len(r.fastq_urls) >= 2) else 1
        size = r.fastq_bytes if r.fastq_bytes is not None else 10**18
        cands.append((pe_bonus, size, r))
    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], x[1]))
    return cands[0][2]

def pick_best_longread(runs: List[EnaRun]) -> Optional[EnaRun]:
    cands = []
    for r in runs:
        if r.instrument_platform not in PLATFORM_LONGREADS:
            continue
        # ONT öncelik
        plat_bonus = 0 if r.instrument_platform == "OXFORD_NANOPORE" else 1
        size = r.fastq_bytes if r.fastq_bytes is not None else 10**18
        cands.append((plat_bonus, size, r))
    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], x[1]))
    return cands[0][2]

def detect_r1_r2(urls: List[str]) -> Tuple[str, str]:
    # ENA naming genelde *_1.fastq.gz / *_2.fastq.gz
    r1 = next((u for u in urls if "_1.fastq" in u), None)
    r2 = next((u for u in urls if "_2.fastq" in u), None)
    if not r1 and urls:
        r1 = urls[0]
    if not r2 and len(urls) >= 2:
        r2 = urls[1]
    if not r1 or not r2:
        raise RuntimeError("Illumina için R1/R2 URL tespiti başarısız.")
    return r1, r2

def resolve_pair(session: requests.Session, ill: EnaRun, lr: EnaRun) -> Tuple[EnaRun, EnaRun]:
    # Zaten eşleşiyorsa bitir
    if ill.sample_accession and lr.sample_accession and ill.sample_accession == lr.sample_accession:
        print(f"✅ Numune Eşleşmesi: {ill.sample_accession}")
        return ill, lr

    print(f"❌ KRİTİK: Numuneler eşleşmiyor! Illumina={ill.sample_accession} vs LR={lr.sample_accession}")

    if not AUTO_REPAIR_ON_MISMATCH:
        if STRICT_SAMPLE_MATCH:
            raise RuntimeError("Sample mismatch (AUTO_REPAIR kapalı).")
        return ill, lr

    # 1) Illumina sample'ında long-read var mı?
    if ill.sample_accession:
        runs = list_runs_for_sample(session, ill.sample_accession)
        lr2 = pick_best_longread(runs)
        if lr2:
            print(f"🔧 AutoRepair: Illumina sample içinde LR bulundu: {lr2.run_accession}")
            return ill, lr2

    # 2) Long-read sample'ında Illumina var mı?
    if lr.sample_accession:
        runs = list_runs_for_sample(session, lr.sample_accession)
        ill2 = pick_best_illumina(runs)
        if ill2:
            print(f"🔧 AutoRepair: LR sample içinde Illumina bulundu: {ill2.run_accession}")
            return ill2, lr

    # 3) Study içinde paired sample ara
    study = ill.study_accession or lr.study_accession
    if study:
        print(f"🔧 AutoRepair: Study içinde paired sample aranıyor: {study}")
        all_runs = list_runs_for_study(session, study)
        by_sample: Dict[str, List[EnaRun]] = {}
        for r in all_runs:
            if r.sample_accession:
                by_sample.setdefault(r.sample_accession, []).append(r)

        candidates: List[Tuple[int, int, str, EnaRun, EnaRun]] = []
        for sacc, rs in by_sample.items():
            i = pick_best_illumina(rs)
            l = pick_best_longread(rs)
            if i and l:
                size_i = i.fastq_bytes or 10**18
                size_l = l.fastq_bytes or 10**18
                candidates.append((size_i + size_l, size_l, sacc, i, l))

        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]))
            _, __, sacc, i, l = candidates[0]
            print(f"✅ AutoRepair: Paired sample seçildi: {sacc} | Illumina={i.run_accession} | LR={l.run_accession}")
            return i, l

    if STRICT_SAMPLE_MATCH:
        raise RuntimeError("AutoRepair başarısız: aynı sample içinde Illumina+LongRead bulunamadı.")
    return ill, lr

# -------------------------
# STREAM SUBSAMPLE
# -------------------------
def stream_subsample_gz(
    session: requests.Session,
    url: str,
    out_path: str,
    *,
    mode: str,         # "MB" or "READS"
    target: int,       # MB veya read sayısı
    check_every_reads: int = 5000
) -> int:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + ".part"

    headers = {"Accept-Encoding": "identity"}  # HTTP-level gzip'i kapat, file zaten .gz
    max_bytes = int(target * 1024 * 1024) if mode == "MB" else None

    read_count = 0
    line_count = 0

    print(f"⬇️  Streaming: {os.path.basename(out_path)} | mode={mode} target={target}")
    print(f"    -> {url}")

    r = http_get_with_retries(session, url, stream=True, retries=4, backoff=2.0, headers=headers, timeout=(10, 240))
    try:
        r.raw.decode_content = False
        gz_in = gzip.GzipFile(fileobj=r.raw)

        with gzip.open(tmp, "wb") as gz_out:
            while True:
                line = gz_in.readline()
                if not line:
                    break

                gz_out.write(line)
                line_count += 1

                if line_count % 4 == 0:
                    read_count += 1

                    if mode == "READS" and read_count >= target:
                        break

                    if mode == "MB" and (read_count % check_every_reads == 0):
                        gz_out.flush()
                        if os.path.getsize(tmp) >= max_bytes:
                            break

        os.replace(tmp, out_path)
        final_mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"    ✅ OK: reads={read_count} | size={final_mb:.2f} MB")
        return read_count

    except Exception as e:
        print(f"    ❌ Streaming hata: {e}")
        if os.path.exists(tmp):
            os.remove(tmp)
        return 0
    finally:
        r.close()

# -------------------------
# MANIFEST
# -------------------------
def manifest_write_header_if_needed():
    if os.path.exists(MANIFEST_FILE):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            "created_utc",
            "filename",
            "type",
            "run_accession",
            "sample_accession",
            "study_accession",
            "platform",
            "model",
            "library_layout",
            "organism",
            "strain",
            "source_url",
            "reads",
            "output_mb",
            "sha256",
        ])

def manifest_append(run: EnaRun, filename: str, filetype: str, source_url: str, reads: int):
    path = os.path.join(DATA_DIR, filename)
    manifest_write_header_if_needed()
    out_mb = os.path.getsize(path) / (1024 * 1024)
    sha = sha256_file(path)

    with open(MANIFEST_FILE, "a", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            now_iso(),
            filename,
            filetype,
            run.run_accession,
            run.sample_accession,
            run.study_accession,
            run.instrument_platform,
            run.instrument_model,
            run.library_layout,
            run.scientific_name,
            run.strain,
            source_url,
            reads,
            f"{out_mb:.2f}",
            sha,
        ])

# -------------------------
# MAIN
# -------------------------
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(MANIFEST_FILE):
        os.remove(MANIFEST_FILE)

    session = requests.Session()

    print("🚀 BIF101 Enterprise Veri İndirici (v2.2 AutoPair)\n")

    ill = get_run_info(session, SEED_ILLUMINA_RUN)
    lr = get_run_info(session, SEED_LONGREAD_RUN)

    if not ill or not lr:
        raise SystemExit("❌ Seed metadata alınamadı. Seed accession'ları kontrol edin.")

    # Premium: AutoPair / strict sample validation
    ill, lr = resolve_pair(session, ill, lr)

    print("\n--- İNDİRME BAŞLIYOR ---\n")

    # Illumina PE: R1 boyuta göre, R2 read sayısına göre sync
    if ill.instrument_platform == PLATFORM_ILLUMINA:
        r1_url, r2_url = detect_r1_r2(ill.fastq_urls)

        prefix = f"{ill.run_accession}_ILLUMINA_{TARGET_MB_SHORT}MB"
        r1_name = f"{prefix}_R1.fastq.gz"
        r2_name = f"{prefix}_R2.fastq.gz"

        reads_r1 = stream_subsample_gz(session, r1_url, os.path.join(DATA_DIR, r1_name), mode="MB", target=TARGET_MB_SHORT)
        if reads_r1 > 0:
            manifest_append(ill, r1_name, "Short-PE-R1", r1_url, reads_r1)

            reads_r2 = stream_subsample_gz(session, r2_url, os.path.join(DATA_DIR, r2_name), mode="READS", target=reads_r1)
            if reads_r2 > 0:
                manifest_append(ill, r2_name, "Short-PE-R2", r2_url, reads_r2)
        else:
            print("❌ Illumina R1 indirilemedi.")
    else:
        print(f"⚠️ Seçilen short-run Illumina değil: {ill.instrument_platform}")

    print("-" * 60)

    # Long read: boyuta göre subset
    if lr.instrument_platform in PLATFORM_LONGREADS and lr.fastq_urls:
        plat_tag = "ONT" if lr.instrument_platform == "OXFORD_NANOPORE" else "PACBIO"
        lr_name = f"{lr.run_accession}_{plat_tag}_{TARGET_MB_LONG}MB.fastq.gz"
        lr_url = lr.fastq_urls[0]

        reads_lr = stream_subsample_gz(session, lr_url, os.path.join(DATA_DIR, lr_name), mode="MB", target=TARGET_MB_LONG)
        if reads_lr > 0:
            manifest_append(lr, lr_name, "Long-Read", lr_url, reads_lr)
        else:
            print("❌ Long-read indirilemedi.")
    else:
        print(f"❌ Long-run uygun değil veya URL yok: {lr.instrument_platform}")

    print(f"\n🎉 Tamamlandı. Manifest: {MANIFEST_FILE}")

if __name__ == "__main__":
    main()
