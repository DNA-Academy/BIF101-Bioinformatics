import os
import subprocess
import sys

def setup_environment():
    """
    BIF101 - Google Colab Otomatik Kurulum Scripti (v1.0.1)
    DNA Academy - Professional Edition
    """
    print("🛠️  BIF101 Laboratuvar Ortamı Hazırlanıyor... Lütfen bekleyin.")

    # 1. ADIM: FastQC Kurulumu (Linux Sistemi)
    print("-> [1/2] FastQC (Kısa Okuma Analizi) kuruluyor...")
    try:
        # Sessiz modda (-qq) kurulum yap
        subprocess.run("apt-get update -qq && apt-get install -y -qq fastqc", shell=True, check=True)
        
        # Versiyon kontrolü
        version = subprocess.run(["fastqc", "--version"], stdout=subprocess.PIPE, text=True).stdout.strip()
        print(f"   ✅ Başarılı: {version} yüklendi.")
    except Exception:
        print("   ❌ HATA: FastQC kurulamadı.")

    # 2. ADIM: Python Kütüphaneleri (NanoPlot, MultiQC, Plotly, Kaleido)
    print("-> [2/2] Python analiz araçları (NanoPlot, MultiQC) kuruluyor...")
    
    # Profesyonel Yol Mantığı: requirements.txt ana dizinde (../../)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.abspath(os.path.join(current_dir, "../../requirements.txt"))
    
    # Dünkü başarının anahtarı olan kütüphaneler
    # Not: NanoPlot çökmemesi için kaleido==0.2.1 burada da garantiye alındı.
    libraries = ["multiqc", "NanoPlot", "biopython", "plotly", "kaleido==0.2.1", "pandas", "requests"]

    try:
        if os.path.exists(req_file):
            # Dosya varsa requirements üzerinden yükle
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", req_file], check=True)
            print(f"   ✅ Başarılı: Kütüphaneler '{req_file}' üzerinden yüklendi.")
        else:
            # Dosya bulunamazsa (veya manuel kurulum gerekirse) listeyi kullan
            print("   ℹ️ Bilgi: requirements.txt bulunamadı, manuel liste yükleniyor...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + libraries, check=True)
            print("   ✅ Başarılı: Tüm Python kütüphaneleri yüklendi.")
    except subprocess.CalledProcessError:
        print("   ❌ HATA: Python kütüphaneleri yüklenirken sorun oluştu.")

    print("\n🎉 KURULUM TAMAMLANDI! Analize başlayabilirsiniz.")

if __name__ == "__main__":
    setup_environment()
