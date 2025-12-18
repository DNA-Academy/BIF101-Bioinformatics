import os
import subprocess
import sys

def apply_nanoplot_patch():
    """NanoPlot'un çökmesine neden olan Kaleido hatasını kaynak kodda onarır."""
    print("🛠️ NanoPlot kütüphanesine cerrahi müdahale yapılıyor...")
    target_file = "/usr/local/lib/python3.12/dist-packages/nanoplotter/plot.py"
    if os.path.exists(target_file):
        try:
            # YAMA: Kaleido çağrılarını sustur
            subprocess.run(["sed", "-i", 's/from kaleido import write_fig_sync/# from kaleido import write_fig_sync/g', target_file], check=True)
            subprocess.run(["sed", "-i", 's/kaleido.get_chrome_sync()/# kaleido.get_chrome_sync()/g', target_file], check=True)
            print("   ✅ Cerrahi müdahale başarılı (Stabilizasyon tamam).")
        except Exception as e:
            print(f"   ⚠️ Yama başarısız: {e}")

def setup_environment():
    print("🚀 BIF101 Laboratuvar Ortamı Hazırlanıyor...")
    # 1. FastQC
    subprocess.run("apt-get update -qq && apt-get install -y -qq fastqc", shell=True, check=True)
    # 2. Kütüphaneler
    libs = ["multiqc", "NanoPlot", "biopython", "plotly", "kaleido==0.2.1", "pandas", "requests"]
    subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + libs, check=True)
    # 3. Kritik Ameliyat
    apply_nanoplot_patch()
    print("\n🎉 KURULUM VE STABİLİZASYON TAMAMLANDI!")

if __name__ == "__main__":
    setup_environment()
