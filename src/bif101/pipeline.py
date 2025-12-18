import os
import subprocess
import glob

# Çıktıların kaydedileceği ana klasörler
REPORT_DIRS = ["reports/fastqc", "reports/nanoplot", "reports/multiqc"]

def setup_folders():
    """Rapor klasörlerini oluşturur."""
    for d in REPORT_DIRS:
        os.makedirs(d, exist_ok=True)

def run_qc_pipeline():
    """
    BIF101 - Scientific Integrity QC Pipeline (v4.0.3)
    Dünkü başarılı Colab denemesindeki parametre fixlerini içerir.
    """
    setup_folders()
    print("🚀 DNA Academy: QC Süreci Başlatılıyor...")

    # 1. FastQC Analizi (Illumina Verileri)
    print("\n⚙️ FastQC Başlıyor...")
    illumina_files = glob.glob("data/*ILLUMINA*.fastq.gz")

    if illumina_files:
        for fastq in illumina_files:
            print(f"Analiz ediliyor: {os.path.basename(fastq)}")
            subprocess.run(["fastqc", fastq, "-o", "reports/fastqc", "-q"], check=True)
        print("✅ FastQC bitti.")
    else:
        print("⚠️ Illumina dosyası bulunamadı, FastQC atlanıyor.")

    # 2. NanoPlot Analizi (PacBio/Long Read Verileri)
    print("\n⚙️ NanoPlot Başlıyor...")
    pacbio_files = glob.glob("data/*PACBIO*.fastq.gz")

    if pacbio_files:
        # KRİTİK DÜZELTME: Dünkü denemede çöküşü engelleyen hamle: 
        # '--plots' parametresi kaldırıldı, kaleido yükü hafifletildi.
        nanoplot_cmd = ["NanoPlot", "--fastq"] + pacbio_files + ["-o", "reports/nanoplot"]
        try:
            subprocess.run(nanoplot_cmd, check=True)
            print("✅ NanoPlot tamamlandı.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ NanoPlot hatası (Lansman öncesi kontrol edilmeli): {e}")
    else:
        print("⚠️ Uzun okuma (PacBio) dosyası bulunamadı, NanoPlot atlanıyor.")

    # 3. MultiQC (Tüm Raporları Birleştirme)
    print("\n⚙️ MultiQC Başlıyor...")
    # Mevcut dizini tarayıp tüm raporları reports/multiqc altına toplar
    subprocess.run(["multiqc", ".", "-o", "reports/multiqc", "-f"], check=False)

    print("\n🎉 QC SÜRECİ TAMAMLANDI! Raporlar 'reports/' klasöründedir.")

if __name__ == "__main__":
    run_qc_pipeline()
