#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenoStream v4.0.3 - Scientific Edition (Final)
----------------------------------------------
Author: DNA Academy Team
"""

import os
import requests
import argparse
import sys
import math
import csv
import time
import urllib.parse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# --- 🧠 LEVEL 3: GENOME INTELLIGENCE DATABASE ---
GENOME_SIZES_DB = {
    "escherichia coli": 4600000,
    "e. coli": 4600000,
    "staphylococcus aureus": 2800000,
    "s. aureus": 2800000,
    "bacillus subtilis": 4200000,
    "pseudomonas aeruginosa": 6300000,
    "saccharomyces cerevisiae": 12000000,
    "homo sapiens": 3200000000,
    "human": 3200000000,
}

ENA_API_URL = "https://www.ebi.ac.uk/ena/portal/api/search"

def get_genome_size(organism_name, user_size=None):
    if user_size: return int(user_size)
    key = organism_name.lower().strip()
    if key in GENOME_SIZES_DB:
        size = GENOME_SIZES_DB[key]
        print(f"🧠 Smart Info: '{organism_name}' için veritabanı boyutu kullanılıyor: {size/1e6:.2f} Mb")
        return size
    print(f"⚠️ Uyarı: Genom boyutu bilinmiyor. Varsayılan bakteri boyutu (5 Mb) kullanılıyor.")
    return 5000000

def create_resilient_session():
    session = requests.Session()
    retry = Retry(total=5, read=5, connect=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_metadata(organism, strategy):
    print(f"🔍 ENA Taranıyor: {organism} ({strategy})...")
    fields = "run_accession,fastq_ftp,fastq_bytes,read_count,base_count,library_strategy,instrument_platform,scientific_name"
    raw_query = f'scientific_name="{organism}"'
    if strategy == "WGS": raw_query += ' AND library_strategy="WGS"'
    elif strategy == "AMPLICON": raw_query += ' AND library_strategy="AMPLICON"'

    safe_query = urllib.parse.quote(raw_query)
    # Limit 200'e çıkarıldı (Long read bulma şansı için)
    final_url = f"{ENA_API_URL}?result=read_run&format=json&limit=200&fields={fields}&query={safe_query}"

    session = create_resilient_session()
    try:
        response = session.get(final_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data:
            print("❌ Eşleşen veri bulunamadı.")
            sys.exit(1)
        return data
    except Exception as e:
        print(f"❌ API Hatası: {e}")
        sys.exit(1)

def smart_select_and_download(metadata, target_platform, target_cov, genome_size, output_dir, session, manifest_writer):
    print(f"\n🚀 Platform Hedefleniyor: {target_platform} | Hedef Coverage: {target_cov}x")
    candidates = []
    for item in metadata:
        inst = item.get('instrument_platform', '').upper()
        if target_platform == "SHORT":
            if "ILLUMINA" in inst or "ION" in inst: candidates.append(item)
        elif target_platform == "LONG":
            if "PACBIO" in inst or "NANOPORE" in inst or "OXFORD" in inst: candidates.append(item)

    if not candidates:
        print(f"⚠️ {target_platform} için uygun aday bulunamadı.")
        return

    for candidate in candidates:
        acc = candidate['run_accession']
        ftp_str = candidate.get('fastq_ftp', '')
        if not ftp_str: continue

        urls = ftp_str.split(';')
        if target_platform == "SHORT":
            if len(urls) < 2: continue
            download_urls = urls[:2]
        else:
            download_urls = [urls[0]]

        needed_bases = int(genome_size * target_cov * 1.1)
        print(f"✅ Aday Seçildi: {acc} ({candidate['instrument_platform']})")

        success = stream_download(acc, download_urls, needed_bases, output_dir, session, manifest_writer, candidate['instrument_platform'])
        if success:
            print(f"🎉 {target_platform} görevi tamamlandı.")
            return

    print(f"❌ Tüm adaylar denendi ancak {target_platform} indirmesi tamamlanamadı.")

def stream_download(acc, urls, needed_bases_total, output_dir, session, manifest_writer, platform_name):
    filenames = []
    download_limit_bytes = 200 * 1024 * 1024
    if needed_bases_total < 100000000: download_limit_bytes = 100 * 1024 * 1024

    for i, url in enumerate(urls):
        filename = f"{acc}_{platform_name}_{i+1}.fastq.gz".replace(" ", "_")
        filepath = os.path.join(output_dir, filename)

        # PROTOCOL FIX: FTP -> HTTP
        if url.startswith("ftp://"): full_url = url.replace("ftp://", "http://")
        elif not url.startswith("http"): full_url = f"http://{url}"
        else: full_url = url

        print(f"   ⬇️ İndiriliyor (Stream): {filename} ...")
        try:
            with session.get(full_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if downloaded >= download_limit_bytes:
                                print(f"      ⏹️ Hedef boyuta ulaşıldı. Kesiliyor.")
                                break
            filenames.append(filename)
            manifest_writer.writerow({'filename': filename, 'organism': acc, 'platform': platform_name, 'filesize': downloaded})
        except Exception as e:
            print(f"      ❌ İndirme hatası: {e}")
            if os.path.exists(filepath): os.remove(filepath)
            return False
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--organism", type=str, required=True)
    parser.add_argument("--strategy", type=str, default="WGS")
    parser.add_argument("--cov-short", type=int, default=50)
    parser.add_argument("--cov-long", type=int, default=30)
    parser.add_argument("--genome-size", type=int)
    args = parser.parse_args()

    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    manifest_path = os.path.join(data_dir, "manifest.tsv")

    file_exists = os.path.isfile(manifest_path)
    manifest_file = open(manifest_path, 'a', newline='')
    fields = ['filename', 'organism', 'platform', 'filesize']
    writer = csv.DictWriter(manifest_file, fieldnames=fields, delimiter='\t')
    if not file_exists: writer.writeheader()

    session = create_resilient_session()
    metadata = fetch_metadata(args.organism, args.strategy)
    g_size = get_genome_size(args.organism, args.genome_size)

    print(f"\n🧬 İşlem Başlıyor: {args.organism} (Genom: {g_size/1e6:.2f} Mb)")
    smart_select_and_download(metadata, "SHORT", args.cov_short, g_size, data_dir, session, writer)
    smart_select_and_download(metadata, "LONG", args.cov_long, g_size, data_dir, session, writer)
    manifest_file.close()
    print("\n✅ GenoStream v4.0.3 tamamlandı.")

if __name__ == "__main__":
    main()
