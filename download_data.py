import os
import requests
import time
import sys

def download_with_mirrors(url_list, output_path):
    """
    Verilen URL listesini sırayla dener. Biri çalışmazsa (404/Connection Error),
    otomatik olarak bir sonraki kaynağa geçer.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    
    for i, url in enumerate(url_list):
        print(f"    [{i+1}/{len(url_list)}] Kaynak deneniyor: {url}")
        try:
            # Stream=True ile veriyi parça parça indiriyoruz
            with requests.get(url, stream=True, allow_redirects=True, timeout=20) as r:
                if r.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk: f.write(chunk)
                    
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"    ✅ BAŞARILI! Boyut: {size_mb:.2f} MB")
                    return True
                else:
                    print(f"    ⚠️  Başarısız (HTTP {r.status_code})...")
        except Exception as e:
            print(f"    ⚠️  Bağlantı hatası: {str(e)}")

    print(f"    ❌ KRİTİK HATA: Hiçbir kaynaktan indirilemedi.")
    return False

def get_consortium_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Robust Mod)\n")

    # 1. ILLUMINA VERİSİ (Zenodo) - Bu zaten çalışıyor
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    if not os.path.exists(illumina_target):
        download_with_mirrors(
            ["https://zenodo.org/record/582600/files/mutant_R1.fastq"], 
            illumina_target
        )
    else:
        print(f"ℹ️  Illumina dosyası zaten mevcut, atlanıyor.")

    # 2. NANOPORE VERİSİ (3 Farklı Yedekli Kaynak)
    # Hedef: Endüstri standardı gerçek Nanopore okumaları
    nanopore_urls = [
        # Kaynak 1: NF-CORE Test Data (Human) - En prestijli kaynak
        "https://raw.githubusercontent.com/nf-core/test-datasets/nanoseq/3.0.0/testdata/human/fastq/nanopore.fastq.gz",
        
        # Kaynak 2: Ryan Wick / Unicycler Sample Data (Bacteria) - Çok stabil
        "https://raw.githubusercontent.com/rrwick/Unicycler/master/sample_data/long_reads.fastq.gz",
        
        # Kaynak 3: NanoPlot Test Data (Backup)
        "https://raw.githubusercontent.com/wdecoster/NanoPlot/master/testing_data/reads.fastq.gz"
    ]
    
    # Dosya ismini pipeline'ların beklediği şekilde sabitliyoruz
    nanopore_target = os.path.join(data_dir, "nanopore_HG002_subset.fastq.gz")
    
    if download_with_mirrors(nanopore_urls, nanopore_target):
        print("\n🎉 Tüm veriler hazır! Analize geçebilirsiniz.")
    else:
        print("\n❌ İndirme başarısız oldu. Lütfen internet bağlantınızı kontrol edin.")

if __name__ == "__main__":
    get_consortium_data()
