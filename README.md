# 🧬 BIF101: Biyoinformatik - Genomik Veri Analizlerine Giriş - Sertifika Eğitimi

![Version](https://img.shields.io/badge/version-4.0.3-blue)
![Platform](https://img.shields.io/badge/platform-Google%20Colab-orange?logo=googlecolab)
![Sanger](https://img.shields.io/badge/Sanger-Thermo_Fisher-882181?logo=thermofisherscientific&logoColor=white)
![NGS](https://img.shields.io/badge/NGS-Illumina-f7941e?logo=illumina&logoColor=white)
![LongRead](https://img.shields.io/badge/Long_Read-ONT-black?logo=oxfordnanoporetechnologies&logoColor=white)
![PacBio](https://img.shields.io/badge/HiFi-PacBio-00a3e0?logo=pacificbiosciences&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

> DNA Academy BIF101 modülü için uçtan uca veri edinimi, kalite kontrol ve uygulamalı analiz kütüphanesi.

---

## 🇹🇷 Hakkında
DNA Academy BIF101 modülü için geliştirilmiş; genomik verilerin indirilmesi, kalite kontrolü ve biyoinformatik analizleri için tasarlanmış profesyonel bir eğitim ve uygulama kütüphanesidir. Küresel yazılım standartlarına (**src-layout**) uygun olarak yapılandırılan bu modül, Google Colab üzerinde tak-çalıştır deneyimi sunmak üzere optimize edilmiştir.

**"Genomik veri analizlerine sağlam bir adım; bilgi kirliliğinden uzak, yalın temellerle başlar... Ham veri kalitesi, analiz başarısının dörtte üçünü belirler".**

### 🚀 Hızlı Başlangıç
* 🗓️ **Güncel Eğitim Takvimi ve Detaylar**: [Egitim_Detaylari.md](docs/tr/Egitim_Detaylari.md)
* ✍️ **Bilgi ve Kayıt**: [www.dnaacademy.com.tr](https://www.dnaacademy.com.tr)
* 📓 **Uygulama Rehberleri**: `notebooks/tr/`

### 📚 Sertifika Programı Müfredatı
Program, katılımcıların kodlama bilgisi gerekmeden genomik veri analizlerini gerçekleştirmesini hedefler:

1. Eğitim Programının Tanıtımı ve Genel Bilgilendirme
2. Ham Genomik Veri ve Veri Formatları (FASTQ, vb.)
3. Biyoinformatik – Genomik Veri Analizlerine Giriş
4. Veri Kalite Kontrolü ve Filtreleme Araçları
5. Hizalama (Mapping) ve Veri İşleme Araçları
6. Varyant Tespiti ve Analizi Araçları
7. Veri Görselleştirme ve Raporlama Araçları
8. Biyoinformatik Platformlar ve Bulut Sistemleri
9. Deneysel Tasarım ve Uygulama Stratejileri
10. Genomik Veri Analizlerinde Gelecek Perspektifleri
11. Vaka Sunumu: Genomik Veri Analizi Temel İş Akışı İncelemesi
12. Demo: Örnek Genomik Veri Analizi Temel İş Akışı

### ✨ Öne Çıkan Özellikler
* **GenoStream v4.0.3**: NCBI & EBI/ENA üzerinden akıllı veri edinimi.
* **Resilient QC Pipeline**: NanoPlot & FastQC sonuçlarını MultiQC altında birleştiren stabilize iş akışı.
* **Interactive Visuals**: Plotly tabanlı, bellek dostu örnekleme görselleştirme motoru.

---

# 🧬 BIF101: Introduction to Genomic Data Analysis - Certificate Training

> An end-to-end data acquisition, QC, and applied analysis library for the DNA Academy BIF101 module.

---

## 🇺🇸 About
A professional training and application library developed for the DNA Academy BIF101 module, designed for genomic data acquisition, quality control, and bioinformatics analysis. Engineered to **src-layout** standards, this module is optimized for a seamless plug-and-play experience on Google Colab.

**"A solid step into genomic data analysis begins with simple foundations, away from information pollution... Raw data quality determines three-quarters of analytical success".**

### 🚀 Quickstart
* 🗓️ **Training Schedule & Details**: [Egitim_Detaylari.md](docs/tr/Egitim_Detaylari.md)
* ✍️ **Info & Enrollment**: [www.dnaacademy.com.tr](https://www.dnaacademy.com.tr)
* 📓 **Tutorials**: `notebooks/en/`

### 📚 Course Curriculum
The program aims to enable participants to perform genomic data analysis without requiring prior coding knowledge:

1. Introduction to the Training Program and General Information
2. Raw Genomic Data and Data Formats (FASTQ, etc.)
3. Bioinformatics – Introduction to Genomic Data Analysis
4. Data Quality Control and Filtering Tools
5. Alignment (Mapping) and Data Processing Tools
6. Variant Calling and Analysis Tools
7. Data Visualization and Reporting Tools
8. Bioinformatics Platforms and Cloud Systems
9. Experimental Design and Implementation Strategies
10. Future Perspectives in Genomic Data Analysis
11. Case Study: Core Genomic Data Analysis Workflow Review
12. Demo: Applied Sample Genomic Data Analysis Workflow

### ✨ Key Features
* **GenoStream v4.0.3**: Smart data acquisition via NCBI & EBI/ENA.
* **Resilient QC Pipeline**: Stabilized workflow merging NanoPlot & FastQC results into MultiQC.
* **Interactive Visuals**: Plotly-based visualization engine with memory-efficient sampling.

---

## 📂 Dosya Yapısı / Directory Structure

```text
├── src/bif101/                 # Core Library / Çekirdek Kütüphane
│   ├── genostream.py           # Data Streaming / Veri İndirme
│   ├── plotting.py             # Analysis & Dashboards / Görselleştirme
│   ├── pipeline.py             # Workflow Management / İş Akışı
│   └── utils.py                # Setup & Patches / Kurulum ve Onarım
├── docs/                       # Curriculum & Guides / Müfredat & Rehber
├── notebooks/                  # Tutorials / Uygulama Rehberleri
├── data/                       # Generated Data (gitignored) / Veri Havuzu
└── reports/                    # QC Reports (gitignored) / Raporlar
