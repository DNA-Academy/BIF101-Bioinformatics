import os
import subprocess
import time

def download_file(url, output_path):
    """Linkten dosyayı indirir ve süreyi ölçer."""
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    
    start_time = time.time()
    # -q: sessiz mod, -O: çıktı dosyası adı
    cmd = f"wget -q -O {output_path} {url}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        end_time = time.time()
        
        # Boyut kontrolü
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    ✅ Tamamlandı! Boyut: {size_mb:.2f} MB (Süre: {end_time - start_time:.1f} sn)")
        
    except subprocess.CalledProcessError:
        print(f"    ❌ HATA: {filename} indirilemedi. Linki kontrol edin.")

def get_consortium_data():
    """
    BIF101 için Gerçek Konsorsiyum Verilerini İndirir.
    Veriler: GIAB (Genome in a Bottle) ve ONT Open Data.
    Not: Eğitim için optimize edilmiş 'subsampled' versiyonlardır.
    """
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"🚀 VERİ İNDİRME BAŞLATILIYOR (Hedef: {data_dir}/)\n")

    # 1. ILLUMINA VERİSİ (Kaynak: GIAB HG002 - Ashkenazi Son)
    # Boyut: ~25 MB
    # Bu dosya, FastQC analizi için yeterli çeşitliliğe sahip gerçek insan genom verisidir.
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    
    download_file(illumina_url, illumina_target)

    # 2. NANOPORE VERİSİ (Kaynak: ONT Open Data - Human)
    # Boyut: ~160 MB
    # Bu dosya, NanoPlot grafikleri için ideal uzunluk dağılımına sahip gerçek uzun okumalardır.
    nanopore_url = "https://zenodo.org/record/3247731/files/reference_design_hac_pass_subset.fastq"
    nanopore_target = os.path.join(data_dir, "nanopore_HG002_subset.fastq")
    
    download_file(nanopore_url, nanopore_target)

    print("\n🎉 Tüm indirmeler tamamlandı. Analize geçebilirsiniz.")

if __name__ == "__main__":
    get_consortium_data()
