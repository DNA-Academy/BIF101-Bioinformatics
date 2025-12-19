import os
from pathlib import Path

# Klasör Yapısı (Docs ve Notebooks öncelikli)
folders = [
    "docs/tr",
    "docs/en",
    "notebooks/tr",
    "notebooks/en",
    "src/bif101",
    "data",      
    "reports",   
    ".github/workflows"
]

# Oluşturulacak Dosyalar
files = [
    # Dokümantasyon (TR)
    "docs/tr/Egitim_Detaylari.md",
    "docs/tr/Mufredat.md",
    "docs/tr/Hazirlik_Rehberi.md",
    "docs/tr/SSS.md",

    # Documentation (EN)
    "docs/en/Training_Details.md",
    "docs/en/Syllabus.md",
    "docs/en/Setup_Guide.md",
    "docs/en/FAQ.md",

    # Notebooks
    "notebooks/tr/00_Veri_Hazirlik.ipynb",
    "notebooks/tr/01_Lab_Uygulamasi.ipynb",
    "notebooks/en/00_Data_Setup.ipynb",
    "notebooks/en/01_Lab_Workshop.ipynb",

    # Source Code (Eksik varsa tamamlar)
    "src/bif101/__init__.py",
    "src/bif101/genostream.py",
    "src/bif101/pipeline.py",
    "src/bif101/plotting.py",
    "src/bif101/utils.py",
]

def create_structure():
    print(f"📂 İşlem başlıyor...")
    
    # 1. Klasörleri Oluştur
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Klasör: {folder}")

    # 2. Dosyaları Oluştur (Varsa dokunmaz)
    for file_path in files:
        file = Path(file_path)
        if not file.exists():
            file.touch()
            print(f"📄 Oluşturuldu: {file_path}")
        else:
            print(f"⚠️ Zaten var (atlanıyor): {file_path}")

    print("\n🎉 Tüm yapı hazır!")

if __name__ == "__main__":
    create_structure()
