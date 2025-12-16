import os
import requests
import time
import sys

def download_with_mirrors(url_list, output_path):
    """
    Verilen URL listesini sırayla dener. Biri çalışmazsa diğerine geçer.
    Böylece '404' veya 'Branch Name' hatalarından etkilenmez.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    
    for url in url_list:
        try:
            print(f"    -> Deneniyor: {url} ...")
            with requests.get(url, stream=True, allow_redirects=True, timeout=10) as r:
                if r.status_code == 200:
                    # Başarılı bağlantı, indirmeye başla
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"    ✅ BAŞARILI! Boyut: {size_mb:.2f} MB")
                    return True
                else:
                    print(f"    ⚠️  Kaynak yanıt vermedi (HTTP {r.status_code}), sonraki kaynak deneniyor...")
        except Exception as e:
            print(f"    ⚠️  Bağlantı hatası, sonraki kaynak deneniyor...")

    print(f"    ❌ HATA: Hiçbir kaynaktan indirilemedi.")
    return False

def get_consortium_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    print(f"🚀 ENDÜSTRİ STANDARDİ VERİLER HAZIRLANIYOR (Hedef: {data_dir}/)\n")

    # --- 1. ILLUMINA VERİSİ (GIAB - HG002) ---
    # Kaynak: Genome in a Bottle (Zenodo Mirror)
    illumina_urls = [
        "https://zenodo.org/record/582600/files/mutant_R1.fastq", # Ana Kaynak
        "https://zenodo.org/record/582600/files/mutant_R2.fastq"  # Yedek (R2)
    ]
    download_with_mirrors(illumina_urls, os.path.join(data_dir, "illumina_HG002_subset_R1.fastq"))

    # --- 2. NANOPORE VERİSİ (Human - QC Benchmark) ---
    # Kaynaklar: 
    # 1. NanoPlot Test Verisi (GitHub Main)
    # 2. NanoPlot Test Verisi (GitHub Master - Eski yapı)
    # 3. nf-core/nanoseq Pipeline Test Verisi (İnsan Genomu)
    nanopore_urls = [
        "https://raw.githubusercontent.com/wdecoster/NanoPlot/main/testing_data/reads.fastq.gz",
        "https://raw.githubusercontent.com/wdecoster/NanoPlot/master/testing_data/reads.fastq.gz",
        "https://raw.githubusercontent.com/nf-core/test-datasets/nanoseq/3.0.0/testdata/human/fastq/nanopore.fastq.gz"
    ]
    
    # Dosya '.gz' olarak kaydedilecek
    target_file = os.path.join(data_dir, "nanopore_HG002_subset.fastq.gz")
    
    if download_with_mirrors(nanopore_urls, target_file):
        print("\n🎉 Veriler başarıyla indirildi. Analize geçebilirsiniz.")
    else:
        print("\n❌ Kritik indirme hatası. İnternet bağlantınızı kontrol edin.")

if __name__ == "__main__":
    get_consortium_data()
