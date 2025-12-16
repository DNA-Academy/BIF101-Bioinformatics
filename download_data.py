import os
import requests
import time
import sys

def download_file_python(url, output_path):
    """
    Python requests kütüphanesi ile indirme yapar.
    wget'e göre çok daha güvenilirdir ve Zenodo redirectlerini sorunsuz yönetir.
    """
    filename = os.path.basename(output_path)
    print(f"⬇️  İndiriliyor: {filename}...")
    start_time = time.time()
    
    try:
        # allow_redirects=True ile Zenodo linklerini takip eder
        with requests.get(url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()
            
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
    illumina_url = "https://zenodo.org/record/582600/files/mutant_R1.fastq"
    illumina_target = os.path.join(data_dir, "illumina_HG002_subset_R1.fastq")
    download_file_python(illumina_url, illumina_target)

    # 2. NANOPORE (Zenodo - ONT Open Data)
    # GÜNCELLEME: GitHub yerine tekrar Zenodo'ya döndük ama requests kütüphanesi ile.
    # Dosya ismi: 'nanopore_HG002_subset.fastq' (Sizin manuel kodunuzla birebir uyumlu)
    nanopore_url = "https://zenodo.org/record/3247731/files/reference_design_hac_pass_subset.fastq"
    nanopore_target = os.path.join(data_dir, "nanopore_HG002_subset.fastq")
    
    if download_file_python(nanopore_url, nanopore_target):
        print("\n🎉 Tüm veriler hazır! Analize geçebilirsiniz.")
    else:
        print("\n⚠️ İndirme hatası oluştu.")

if __name__ == "__main__":
    get_consortium_data()
