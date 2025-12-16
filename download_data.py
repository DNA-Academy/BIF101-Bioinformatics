import os
import subprocess
import time

def download_file(url, output_path):
    """Linkten dosyayı indirir (Redirectleri takip eder)."""
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    
    start_time = time.time()
    # -L: Redirectleri takip et (GitHub/Zenodo için kritik)
    # -q: Sessiz mod
    cmd = f"wget -L -q -O {output_path} {url}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        
        # Boyut kontrolü
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"    ✅ Tamamlandı! Boyut: {size_mb:.2f} MB (Süre: {time.time() - start_time:.1f} sn)")
        else:
            print(f"    ❌ HATA: Dosya oluşmadı -> {filename}")
            
    except subprocess.CalledProcessError:
        print(f"    ❌ HATA: İndirme komutu başarısız oldu -> {filename}")

def get_consortium_data():
    """
    BIF101 için Gerçek Konsorsiyum Verilerini İndirir.
    Veriler: Sıkıştırılmış (.gz) formatta iner.
    """
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Hedef: {data_dir}/)\n")

    # 1. ILLUMINA VERİSİ (Zenodo - GIAB)
    # Çalışan linki koruduk
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    download_file(illumina_url, illumina_target)

    # 2. NANOPORE VERİSİ (GitHub Raw - NanoPlot Test Data)
    # Link güncellendi: Çok daha hızlı ve kararlı GitHub Raw linki.
    # Not: Dosya .gz formatındadır (Sıkıştırılmış)
    nanopore_url = "https://github.com/wdecoster/NanoPlot/raw/master/testing_data/reads.fastq.gz"
    nanopore_target = os.path.join(data_dir, "nanopore_test_data.fastq.gz")
    download_file(nanopore_url, nanopore_target)

    print("\n🎉 İndirme işlemleri tamamlandı.")

if __name__ == "__main__":
    get_consortium_data()
