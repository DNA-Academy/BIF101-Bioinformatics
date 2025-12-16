import os
import subprocess
import time

def download_file(url, output_path):
    """Linkten dosyayı indirir."""
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    
    start_time = time.time()
    # DÜZELTME: --no-check-certificate eklendi (SSL hatalarını yoksayar)
    # DÜZELTME: raw.githubusercontent.com kullanıldığı için -L (redirect) şart değil ama kalsın.
    cmd = f"wget --no-check-certificate -q -O {output_path} {url}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"    ✅ Tamamlandı! Boyut: {size_mb:.2f} MB (Süre: {time.time() - start_time:.1f} sn)")
        else:
            print(f"    ❌ HATA: Dosya indirilemedi (0 byte) -> {filename}")
            
    except subprocess.CalledProcessError:
        print(f"    ❌ HATA: İndirme başarısız -> {filename}")

def get_consortium_data():
    """
    BIF101 Veri İndirme Scripti (Final Versiyon)
    """
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Hedef: {data_dir}/)\n")

    # 1. ILLUMINA (Zenodo)
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    download_file(illumina_url, illumina_target)

    # 2. NANOPORE (GitHub Raw Content)
    # GÜNCELLEME: Link yapısı 'raw.githubusercontent.com' olarak değiştirildi.
    nanopore_url = "https://raw.githubusercontent.com/wdecoster/NanoPlot/master/testing_data/reads.fastq.gz"
    nanopore_target = os.path.join(data_dir, "nanopore_test_data.fastq.gz")
    download_file(nanopore_url, nanopore_target)

    print("\n🎉 İşlem tamamlandı.")

if __name__ == "__main__":
    get_consortium_data()
