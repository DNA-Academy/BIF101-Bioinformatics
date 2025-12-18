import gzip
import numpy as np
import pandas as pd
import plotly.express as px
import os

def parse_fastq(file_path, sampling_rate=0.1):
    """Bellek dostu FASTQ analizi (%10 örnekleme ile)."""
    lengths, quals, gc_contents = [], [], []
    print(f"📂 Analiz ediliyor: {os.path.basename(file_path)}")
    open_func = gzip.open if file_path.endswith(".gz") else open
    try:
        with open_func(file_path, "rt") as f:
            while True:
                header = f.readline()
                if not header: break
                seq = f.readline().strip()
                f.readline() # +
                qual_str = f.readline().strip()
                if np.random.random() > sampling_rate: continue
                if len(seq) == 0: continue
                lengths.append(len(seq))
                quals.append(np.mean([ord(c) - 33 for c in qual_str]))
                gc_contents.append(((seq.count('G') + seq.count('C')) / len(seq)) * 100)
    except Exception as e:
        print(f"❌ HATA: {e}")
        return pd.DataFrame()
    return pd.DataFrame({"file": os.path.basename(file_path), "length": lengths, "mean_quality": quals, "gc_percent": gc_contents})

def create_qc_dashboard(df):
    """Plotly Isı Haritası (Heatmap) ile görselleştirme."""
    if df.empty: return
    for filename, group in df.groupby("file"):
        fig = px.density_heatmap(group, x="length", y="mean_quality", title=f"Kalite Yoğunluğu: {filename}", template="plotly_white", marginal_x="histogram", marginal_y="histogram")
        fig.show()
