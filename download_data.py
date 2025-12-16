import os
import requests
import time
import sys

def download_file_python(url, output_path):
    """
    Terminal komutları (wget) yerine Python requests kütüphanesini kullanır.
    Bu yöntem GitHub/Zenodo bağlantılarında çok daha kararlıdır.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    start_time = time.time()
    
    try:
        # Stream=True, büyük dosyaları RAM'i şişirmeden indirmeyi sağlar
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status() # Link kırık (404) ise hata ver
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    
        # Boyut hesapla
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    ✅ Tamamlandı! Boyut: {size_mb:.2f} MB (Süre: {time.time() - start_time:.1f} sn)")
        return True
        
    except Exception as e:
        print(f"    ❌ HATA: İndirme başarısız -> {e}")
        return False

def get_consortium_data():
    """BIF101 Veri İndirme Scripti"""
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Hedef: {data_dir}/)\n")

    # 1. ILLUMINA (Zenodo)
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    download_file_python(illumina_url, illumina_target)

    # 2. NANOPORE (GitHub Raw)
    # Link: NanoPlot geliştiricisinin test verisi
    nanopore_url = "https://raw.githubusercontent.com/wdecoster/NanoPlot/master/testing_data/reads.fastq.gz"
    nanopore_target = os.path.join(data_dir, "nanopore_test_data.fastq.gz")
    success = download_file_python(nanopore_url, nanopore_target)

    if success:
        print("\n🎉 Tüm veriler hazır! Analize geçebilirsiniz.")
    else:
        print("\n⚠️ Nanopore verisi indirilemedi. Lütfen bağlantınızı kontrol edin.")

if __name__ == "__main__":
    get_consortium_data()
