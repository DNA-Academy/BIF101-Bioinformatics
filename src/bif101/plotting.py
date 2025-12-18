import gzip
import numpy as np
import pandas as pd
import plotly.express as px
import os

def parse_fastq(file_path, sampling_rate=0.1):
    """
    FASTQ dosyasını okur ve kalite metriklerini çıkarır.
    Dünkü Başarı: Bellek yönetimi için %10 örnekleme (sampling) eklendi.
    """
    lengths = []
    quals = []
    gc_contents = []
    
    print(f"📂 Dosya analiz ediliyor: {os.path.basename(file_path)}")
    
    open_func = gzip.open if file_path.endswith(".gz") else open
    mode = "rt" 
    
    try:
        with open_func(file_path, mode) as f:
            while True:
                header = f.readline()
                if not header: break 
                
                seq = f.readline().strip() 
                f.readline() # + işareti
                qual_str = f.readline().strip() 
                
                # Hızlandırma: Her okumayı değil, rastgele %10'unu işleyerek hızı 10 kat artırıyoruz
                if np.random.random() > sampling_rate:
                    continue

                L = len(seq)
                if L == 0: continue
                
                lengths.append(L)
                # Phred Skor Hesaplama
                q_scores = [ord(c) - 33 for c in qual_str]
                quals.append(np.mean(q_scores))
                
                gc_count = seq.count('G') + seq.count('C')
                gc_contents.append((gc_count / L) * 100)
                
    except Exception as e:
        print(f"❌ HATA: {file_path} okunurken sorun oluştu: {e}")
        return pd.DataFrame()

    return pd.DataFrame({
        "file": os.path.basename(file_path),
        "length": lengths,
        "mean_quality": quals,
        "gc_percent": gc_contents
    })

def create_qc_dashboard(df):
    """
    Dünkü Başarı: Scatter yerine Density Heatmap kullanarak çökmeyi engelliyoruz.
    """
    if df.empty:
        print("⚠️ Grafik çizilecek veri yok.")
        return

    print("📊 DNA Academy Görselleştirme Motoru Çalışıyor...")
    
    for filename, group in df.groupby("file"):
        # Grafik 1: Okuma Uzunluğu Dağılımı
        fig1 = px.histogram(
            group, x="length", nbins=50,
            title=f"Okuma Uzunluğu Dağılımı: {filename}",
            template="plotly_white",
            color_discrete_sequence=['#2E86C1']
        )
        fig1.show()
        
        # Grafik 2: Kalite ve Uzunluk Yoğunluğu (Isı Haritası)
        fig2 = px.density_heatmap(
            group, x="length", y="mean_quality",
            title=f"Kalite ve Uzunluk Yoğunluğu: {filename}",
            template="plotly_white",
            marginal_x="histogram",
            marginal_y="histogram"
        )
        fig2.show()
