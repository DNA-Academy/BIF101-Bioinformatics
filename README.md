**BIF101 — Biyoinformatik: Genomik Veri Analizlerine Giriş (Sertifika Eğitimi)**  
**BIF101 — Introduction to Genomic Data Analysis (Certificate Training)**

#### Modül Künyesi / Module Metadata

**Genel / General:**  
![DNA Academy](https://img.shields.io/badge/DNA_Academy-Bioinformatics-blue?style=flat-square) ![Platform](https://img.shields.io/badge/Platform-Google_Colab-orange?style=flat-square&logo=googlecolab&logoColor=white) ![Language](https://img.shields.io/badge/Language-Python_3.10+-blue?style=flat-square&logo=python&logoColor=white) ![GenoStream](https://img.shields.io/badge/GenoStream-v4.0-blue?style=flat-square) ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Dizileme / Sequencing:**  
![Short-read](https://img.shields.io/badge/Short--read-Sequencing-green?style=flat-square) ![Long-read](https://img.shields.io/badge/Long--read-Sequencing-red?style=flat-square)

**Platformlar / Platforms:**  
![Illumina](https://img.shields.io/badge/NGS-Illumina-f7941e?style=flat-square)
![Ion Torrent](https://img.shields.io/badge/NGS-Ion_Torrent-882181?style=flat-square)
![ONT](https://img.shields.io/badge/Long_Read-Nanopore-1E88E5?style=flat-square)
![PacBio](https://img.shields.io/badge/Long_Read-PacBio-E91E63?style=flat-square)

**Analiz / Analysis:**  
![FastQC](https://img.shields.io/badge/QC-FastQC-blueviolet?style=flat-square) ![NanoPlot](https://img.shields.io/badge/QC-NanoPlot-blueviolet?style=flat-square) ![MultiQC](https://img.shields.io/badge/Reporting-MultiQC-blueviolet?style=flat-square)

**Katmanlar / Layers:**  
- **DNA Academy Öğrenme Ekosistemi:** LMS + canlı ders + değerlendirme/sertifikasyon (**www.dnaacademy.com.tr**)  
- **Dokümantasyon:** `docs/`  
- **Çalışma ortamı:** Google Colab + `requirements.txt`  
- **Uygulama defterleri:** `notebooks/`  
- **Çekirdek kütüphane:** `src/`  
- **Veri kaynakları:** NCBI / ENA / EBI  
- **Veri indirme & hazırlama:** **GenoStream v4.0** (hedefli indirme + streaming + resumable)  
- **QC & raporlama:** FastQC / NanoPlot → MultiQC  
- **Çıktılar:** `reports/`, `data/` (gitignored)  

**Ekosistem / Ecosystem:**  
Bu repo, BIF101 modülünün canlı oturumlarında kullanılan resmi uygulama altyapısını (notebook’lar + çekirdek kod + veri indirme/QC/raporlama) sağlar; öğrenme akışı ve sertifikasyon süreçleri DNA Academy Öğrenme Ekosistemi üzerinden yürütülür (**www.dnaacademy.com.tr**).

---

#### Türkçe
Bu depo, DNA Academy BIF101 modülü kapsamında genomik veriler için **veri indirme ve hazırlama**, **kalite kontrol (QC)** ve **raporlama** odaklı uygulamalı iş akışlarını destekleyen eğitim kütüphanesi ve notebook koleksiyonudur. Kod tabanı sürdürülebilirlik amacıyla **src-layout** yaklaşımıyla yapılandırılmış olup birincil yürütme ortamı **Google Colab**’dır.

Bu repo, gerçek veri setleri üzerinde **veri indirme ve hazırlama** adımlarını; **ihtiyaca göre hedefli indirme**, **akış temelli (streaming) aktarım** ve **yeniden başlatılabilir (resumable) transfer** prensipleriyle ele alır.

> "Genomik veri analizlerine sağlam bir adım; bilgi kirliliğinden uzak, yalın temellerle başlar. Ham veri kalitesi, analiz başarısının dörtte üçünü belirler."

#### Hızlı başlangıç
- Eğitim takvimi, kapsam, kayıt ve sertifika detayları: `docs/tr/Egitim_Detaylari.md`
- Bilgi & kayıt: https://www.dnaacademy.com.tr
- 🚀 **Colab (TR) ile başla:** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DNA-Academy/BIF101-Bioinformatics/blob/main/notebooks/tr/00_Veri_Hazirlik.ipynb)
- Uygulama defterleri: `notebooks/tr/` (önerilen başlangıç: `00_...`)

#### Kapsam
- Ham veri formatları (FASTQ vb.) ve QC mantığı; temel metriklerin yorumlanması
- Veri karakteristiğine göre QC yaklaşımı (short-read vs long-read)
- Raporlama çıktıları üzerinden yorumlamaya hazırlık (özet metrikler ve görsel raporlar)
- Colab üzerinde tekrarlanabilir uygulama adımları

#### Araç zinciri (yüksek seviye)
- **QC:** FastQC (çoğunlukla short-read), NanoPlot (long-read; NanoStats özetleri), MultiQC (konsolidasyon)
- **Görselleştirme:** Plotly tabanlı bellek-dostu örnekleme yaklaşımı (modül içeriğine bağlı)
- *Not: MultiQC, long-read özetlerini çoğunlukla NanoPlot’un ürettiği NanoStats çıktıları üzerinden toplar.*

---

#### English
This repository supports the DNA Academy BIF101 module with applied workflows for **data download and preparation**, **quality control (QC)**, and **reporting** on genomic sequencing data. The codebase follows a maintainable **src-layout** structure and is primarily optimized for execution on **Google Colab**.

This repository addresses **data download and preparation** on real-world datasets using **targeted retrieval**, **streaming-based transfer**, and **resumable downloads**.

> "A solid step into genomic data analysis begins with simple foundations, away from noise. Raw data quality determines three-quarters of analytical success."

#### Getting started
- Training schedule, scope, enrollment, and certification details: `docs/en/Training_Details.md`
- Info & enrollment: https://www.dnaacademy.com.tr
- 🚀 **Start on Colab (EN):** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DNA-Academy/BIF101-Bioinformatics/blob/main/notebooks/en/00_Data_Setup.ipynb)
- Tutorials: `notebooks/en/` (recommended start: `00_...`)

#### Scope
- QC rationale for raw data (FASTQ, etc.) and interpretation of key metrics
- Tooling aligned with data characteristics (short-read vs long-read)
- Consolidated reporting outputs to support downstream interpretation
- Reproducible, guided execution in Google Colab

#### Toolchain (high level)
- **QC:** FastQC (primarily short-read), NanoPlot (long-read; NanoStats summaries), MultiQC (aggregation)
- **Visualization:** Plotly-based, memory-efficient sampling approach (module-dependent)
- *Note: MultiQC commonly collects long-read summaries via NanoStats outputs produced by NanoPlot.*

---

#### Depo Yapısı / Repository Structure

```text
BIF101-Bioinformatics/
├── README.md                     # Vitrin (TR blok + EN blok)
├── LICENSE                       # MIT
├── requirements.txt              # Ortak bağımlılıklar (runtime)
├── .gitignore
│
├── docs/                         # Müfredat & Rehber / Curriculum & Guides
│   ├── tr/                       # Türkçe Dokümantasyon
│   │   ├── Egitim_Detaylari.md   # Güncel takvim, kayıt, sertifika vb.
│   │   ├── Mufredat.md           # 4 günlük program / ders akışı
│   │   ├── Hazirlik_Rehberi.md   # Hesap açılışları, kurulum adımları
│   │   └── SSS.md                # Sıkça Sorulan Sorular
│   │
│   └── en/                       # English Documentation
│       ├── Training_Details.md   # Schedule, enrollment, certification info
│       ├── Syllabus.md           # 4-day schedule / session flow
│       ├── Setup_Guide.md        # Accounts, setup steps
│       └── FAQ.md                # Frequently Asked Questions
│
├── notebooks/                    # Uygulama Alanı / Tutorials
│   ├── tr/
│   │   ├── 00_Veri_Hazirlik.ipynb
│   │   └── 01_Lab_Uygulamasi.ipynb
│   │
│   └── en/
│       ├── 00_Data_Setup.ipynb
│       └── 01_Lab_Workshop.ipynb
│
└── src/                          # Çekirdek Yazılım / Core Technology
    └── bif101/
        ├── __init__.py
        ├── genostream.py         # Veri indirme ve hazırlama / data download & preparation
        ├── pipeline.py           # İş akışı / workflow
        ├── plotting.py           # Görselleştirme / visualization
        └── utils.py              # Kurulum yardımcıları / setup utilities
