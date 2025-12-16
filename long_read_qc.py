import gzip
import numpy as np
import pandas as pd
import plotly.express as px
import os

def parse_fastq(file_path):
    """
    FASTQ dosyasını okur ve kalite metriklerini çıkarır.
    Kaynak: BIF101 - 5-alt
    """
    lengths = []
    quals = []
    gc_contents = []
    
    print(f"📂 Dosya okunuyor: {file_path}")
    
    # Dosya .gz ise gzip ile, değilse normal aç
    open_func = gzip.open if file_path.endswith(".gz") else open
    mode = "rt" # Read Text modu
    
    try:
        with open_func(file_path, mode) as f:
            while True:
                # FASTQ Formatı: 4 satırdan oluşur
                header = f.readline()
                if not header: break # Dosya bitti
                
                seq = f.readline().strip() # Dizi
                f.readline()               # + işareti
                qual_str = f.readline().strip() # Kalite karakterleri
                
                # --- HESAPLAMALAR ---
                L = len(seq)
                if L == 0: continue
                
                # 1. Uzunluk
                lengths.append(L)
                
                # 2. Kalite (Phred Score: ASCII - 33)
                # Ortalama kaliteyi hesapla
                q_scores = [ord(c) - 33 for c in qual_str]
                quals.append(np.mean(q_scores))
                
                # 3. GC Oranı (%)
                gc_count = seq.count('G') + seq.count('C')
                gc_contents.append((gc_count / L) * 100)
                
    except FileNotFoundError:
        print(f"❌ HATA: '{file_path}' bulunamadı!")
        return pd.DataFrame()

    # Veriyi DataFrame'e çevir
    df = pd.DataFrame({
        "file": os.path.basename(file_path),
        "length": lengths,
        "mean_quality": quals,
        "gc_percent": gc_contents
    })
    
    return df

def create_qc_dashboard(df):
    """
    Elde edilen verilerle Plotly grafikleri çizer.
    Kaynak: BIF101 - 6-alt
    """
    if df.empty:
        print("⚠️ Grafik çizilecek veri yok.")
        return

    print("\n📊 Grafikler hazırlanıyor...")
    
    # Dosya bazında grupla (Birden fazla dosya varsa)
    for filename, group in df.groupby("file"):
        print(f"   -> {filename} için analiz:")
        print(group.describe().T) # İstatistiksel özet
        
        # Grafik 1: Okuma Uzunluğu Dağılımı (Histogram)
        fig1 = px.histogram(
            group, x="length", nbins=100,
            title=f"Okuma Uzunluğu Dağılımı: {filename}",
            labels={"length": "Uzunluk (bp)", "count": "Okuma Sayısı"},
            template="plotly_dark"
        )
        fig1.show()
        
        # Grafik 2: Uzunluk vs Kalite (Scatter)
        # Performans için sadece 2000 nokta örnekle
        sample_df = group.sample(n=min(len(group), 2000), random_state=42)
        
        fig2 = px.scatter(
            sample_df, x="length", y="mean_quality",
            title=f"Uzunluk vs Kalite: {filename}",
            labels={"length": "Uzunluk (bp)", "mean_quality": "Ortalama Kalite (Phred)"},
            opacity=0.5,
            template="plotly_dark"
        )
        fig2.show()

# --- DEMO ÇALIŞTIRMA ---
if __name__ == "__main__":
    print("Bu modül, dışarıdan çağrılmak üzere tasarlanmıştır.")
    print("Kullanım: df = parse_fastq('dosya.fastq')")
