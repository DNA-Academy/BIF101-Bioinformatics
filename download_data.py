import os
import requests
import time
import sys

def download_from_zenodo(url, output_path):
    """
    Sadece Zenodo üzerinden indirme yapar. 
    GitHub raw linkleri Colab'de bloklandığı için bu yöntem en kararlısıdır.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    print(f"    -> Kaynak: {url}")
    
    start_time = time.time()
    try:
        # Zenodo redirectlerini takip et ve stream et
        with requests.get(url, stream=True, allow_redirects=True, timeout=15) as r:
            if r.status_code != 200:
                print(f"    ❌ HATA: Kaynak erişilemedi (HTTP {r.status_code})")
                return False
                
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                    f.write(chunk)
                    
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    ✅ BAŞARILI! Boyut: {size_mb:.2f} MB (Süre: {time.time() - start_time:.1f} sn)")
        return True
        
    except Exception as e:
        print(f"    ❌ Bağlantı Hatası: {e}")
        return False

def get_consortium_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Kaynak: Zenodo Arşivleri)\n")

    # 1. ILLUMINA VERİSİ (Zenodo - GIAB)
    # Bu link zaten çalışıyordu, koruyoruz.
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    
    if not os.path.exists(illumina_target):
        download_from_zenodo(illumina_url, illumina_target)
    else:
        print(f"ℹ️  Illumina dosyası zaten var, pas geçiliyor.")

    # 2. NANOPORE VERİSİ (Zenodo - Galaxy Training Material)
    # Kaynak: Galaxy Project Training Network (Staphylococcus aureus - MRSA)
    # GitHub yerine Zenodo Record 4541743 kullanıyoruz. Asla silinmez/değişmez.
    nanopore_url = "https://zenodo.org/record/4541743/files/NCTC_nanopore.fastq.gz"
    
    # Dosya ismini pipeline'a uygun kaydediyoruz
    nanopore_target = os.path.join(data_dir, "nanopore_HG002_subset.fastq.gz")
    
    # Eğer önceki denemelerden bozuk dosya kaldıysa silelim
    if os.path.exists(nanopore_target) and os.path.getsize(nanopore_target) < 1024:
        os.remove(nanopore_target)

    download_from_zenodo(nanopore_url, nanopore_target)

    print("\n🎉 İşlem tamamlandı.")

if __name__ == "__main__":
    get_consortium_data()
