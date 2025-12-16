import os
import requests
import time
import sys

def download_file_python(url, output_path):
    """
    Python requests kütüphanesi ile indirme yapar.
    Güvenilir, redirectleri takip eder ve hata durumunda bilgi verir.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    start_time = time.time()
    
    try:
        # stream=True ile büyük dosyaları parça parça indirir
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status() # 404 gibi hatalarda durur
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    ✅ Tamamlandı! Boyut: {size_mb:.2f} MB (Süre: {time.time() - start_time:.1f} sn)")
        return True
        
    except Exception as e:
        print(f"    ❌ HATA: İndirme başarısız -> {e}")
        return False

def get_consortium_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Hedef: {data_dir}/)\n")

    # 1. ILLUMINA (Zenodo - GIAB)
    # Bu link çalışıyor, dokunmuyoruz.
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    download_file_python(illumina_url, illumina_target)

    # 2. NANOPORE (GitHub - Ryan Wick / Unicycler Sample Data)
    # DEĞİŞİKLİK: Link ve Dosya Uzantısı güncellendi.
    # Ryan Wick'in deposu biyoinformatik camiasının en stabil depolarından biridir.
    nanopore_url = "https://raw.githubusercontent.com/rrwick/Unicycler/master/sample_data/long_reads.fastq.gz"
    
    # Dikkat: İndirilen dosya .gz (sıkıştırılmış) formatında olacak
    nanopore_target = os.path.join(data_dir, "nanopore_HG002_subset.fastq.gz")
    
    if download_file_python(nanopore_url, nanopore_target):
        print("\n🎉 Tüm veriler hazır! Analize geçebilirsiniz.")
    else:
        print("\n⚠️ İndirme hatası devam ediyor. Lütfen bağlantınızı kontrol edin.")

if __name__ == "__main__":
    get_consortium_data()
