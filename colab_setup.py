import os
import subprocess
import sys

def setup_environment():
    """
    BIF101 - Google Colab Otomatik Kurulum Scripti
    Bu script:
    1. Linux tabanlı araçları (FastQC) kurar.
    2. Python kütüphanelerini (MultiQC, NanoPlot, vb.) requirements.txt üzerinden yükler.
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
    except subprocess.CalledProcessError:
        print("   ❌ HATA: FastQC kurulamadı.")

    # 2. ADIM: Python Kütüphaneleri (NanoPlot, MultiQC, Plotly)
    print("-> [2/2] Python analiz araçları (NanoPlot, MultiQC) kuruluyor...")
    req_file = "requirements.txt"
    
    if os.path.exists(req_file):
        try:
            # pip install -r requirements.txt komutunu çalıştır
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", req_file], check=True)
            print("   ✅ Başarılı: Tüm Python kütüphaneleri yüklendi.")
        except subprocess.CalledProcessError:
            print("   ❌ HATA: Python kütüphaneleri yüklenirken sorun oluştu.")
    else:
        print(f"   ⚠️ UYARI: '{req_file}' dosyası bulunamadı! Lütfen repoda olduğundan emin olun.")

    print("\n🎉 KURULUM TAMAMLANDI! Analize başlayabilirsiniz.")

if __name__ == "__main__":
    setup_environment()
