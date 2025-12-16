import os
import subprocess
import sys

# Çıktıların kaydedileceği ana klasör
OUTPUT_DIR = "qc_results"

def run_command(command):
    """Terminal komutlarını çalıştırır ve çıktıları ekrana yazar."""
    try:
        subprocess.run(command, check=True, shell=False)
    except subprocess.CalledProcessError as e:
        print(f"❌ HATA: Komut başarısız oldu -> {' '.join(command)}")
        # Hata olsa bile scriptin devam etmesi için exit yapmıyoruz (demo amaçlı)

def run_pipeline(short_reads=None, long_reads=None):
    """
    BIF101 Otomatik QC İş Akışı
    ---------------------------
    1. Short Reads (Illumina) -> FastQC
    2. Long Reads (Nanopore) -> NanoPlot
    3. Raporlama -> MultiQC
    """
    
    # Klasör oluştur
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"🚀 QC Pipeline Başlatılıyor... (Çıktı Hedefi: {OUTPUT_DIR})")

    # --- ADIM 1: FASTQC (Kısa Okumalar) ---
    if short_reads:
        print("\n--- [1/3] FastQC Analizi (Illumina) ---")
        # Komut: fastqc dosya1 dosya2 -o output_dir
        cmd = ["fastqc"] + short_reads + ["-o", OUTPUT_DIR]
        run_command(cmd)
    else:
        print("\nℹ️  Kısa okuma dosyası verilmedi, FastQC atlanıyor.")

    # --- ADIM 2: NANOPLOT (Uzun Okumalar) ---
    if long_reads:
        print("\n--- [2/3] NanoPlot Analizi (Uzun Okuma) ---")
        for lr in long_reads:
            # Her dosya için ayrı klasör açmamak adına prefix kullanıyoruz
            prefix = f"nanoplot_{os.path.basename(lr).split('.')[0]}_"
            
            # Komut: NanoPlot --fastq dosya --outdir output_dir --prefix ...
            cmd = [
                "NanoPlot",
                "--fastq", lr,
                "--outdir", OUTPUT_DIR,
                "--prefix", prefix,
                "--plots", "hex", # Hız için hexbin grafiği
                "--format", "png" 
            ]
            run_command(cmd)
    else:
        print("\nℹ️  Uzun okuma dosyası verilmedi, NanoPlot atlanıyor.")

    # --- ADIM 3: MULTIQC (Rapor Birleştirme) ---
    print("\n--- [3/3] MultiQC Raporlama ---")
    # Komut: multiqc output_dir -o output_dir
    cmd = ["multiqc", OUTPUT_DIR, "-o", OUTPUT_DIR, "--force"]
    run_command(cmd)

    print(f"\n✅ Pipeline Tamamlandı! Raporu şurada görüntüleyebilirsiniz: {OUTPUT_DIR}/multiqc_report.html")

# --- KULLANIM ÖRNEĞİ ---
if __name__ == "__main__":
    print("Bu script bir modüldür. Doğrudan çalıştırmak yerine Colab not defterinden çağırın.")
    print("Örnek:")
    print("run_pipeline(short_reads=['sample_R1.fastq'], long_reads=['nanopore.fastq'])")
