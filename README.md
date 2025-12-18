# 🧬 BIF101: Biyoinformatik - Genomik Veri Analizlerine Giriş / Introduction to Genomic Data Analysis

![Version](https://img.shields.io/badge/version-4.0.3-blue)
![Platform](https://img.shields.io/badge/platform-Google%20Colab-orange)
![Course](https://img.shields.io/badge/course-BIF101-red)
![License](https://img.shields.io/badge/license-MIT-green)
![Language](https://img.shields.io/badge/language-TR%20%7C%20EN-red)

> DNA Academy BIF101 modülü için uçtan uca veri edinimi, kalite kontrol ve uygulamalı analiz kütüphanesi.
> An end-to-end data acquisition, QC, and applied analysis library for the DNA Academy BIF101 module.

---

## 🇹🇷 Hakkında / 🇺🇸 About
DNA Academy BIF101 modülü için geliştirilmiş; genomik verilerin indirilmesi, kalite kontrolü ve biyoinformatik analizleri için tasarlanmış profesyonel bir eğitim ve uygulama kütüphanesidir. Küresel yazılım standartlarına (**src-layout**) uygun olarak yapılandırılan bu modül, Google Colab üzerinde tak-çalıştır deneyimi sunmak üzere optimize edilmiştir.

**"Genomik veri analizlerine sağlam bir adım; bilgi kirliliğinden uzak, yalın temellerle başlar... Ham veri kalitesi, analiz başarısının dörtte üçünü belirler."**

---

## 🚀 Hızlı Başlangıç | Quickstart (Colab)

- 🗓️ **Güncel Eğitim Takvimi ve Detaylar / Training Schedule & Details:** [Egitim_Detaylari.md](docs/tr/Egitim_Detaylari.md)
- ✍️ **Bilgi ve Kayıt / Info & Enrollment:** [www.dnaacademy.com.tr](https://www.dnaacademy.com.tr)
- 📓 **Uygulama Rehberleri / Tutorials:** `notebooks/tr/` (Türkçe) & `notebooks/en/` (English)

---

## 📚 Sertifika Programı Müfredatı / Course Curriculum

Program, katılımcıların kodlama bilgisi gerekmeden genomik veri analizlerini gerçekleştirmesini hedefler:

1. **Eğitim Programının Tanıtımı ve Genel Bilgilendirme / Introduction to the Training Program and General Information**
2. **Ham Genomik Veri ve Veri Formatları (FASTQ, vb.) / Raw Genomic Data and Data Formats (FASTQ, etc.)**
3. **Biyoinformatik – Genomik Veri Analizlerine Giriş / Bioinformatics – Introduction to Genomic Data Analysis**
4. **Veri Kalite Kontrolü ve Filtreleme Araçları / Data Quality Control and Filtering Tools**
5. **Hizalama (Mapping) ve Veri İşleme Araçları / Alignment (Mapping) and Data Processing Tools**
6. **Varyant Tespiti ve Analiz Araçları / Variant Calling and Analysis Tools**
7. **Veri Görselleştirme ve Raporlama Araçları / Data Visualization and Reporting Tools**
8. **Biyoinformatik Platformlar ve Bulut Sistemleri / Bioinformatics Platforms and Cloud Systems**
9. **Deneysel Tasarım ve Uygulama Stratejileri / Experimental Design and Implementation Strategies**
10. **Genomik Veri Analizlerinde Gelecek Perspektifleri / Future Perspectives in Genomic Data Analysis**
11. **Vaka Sunumu ve Temel İş Akışı İncelemesi / Case Study and Core Workflow Review**
12. **Uygulamalı Örnek Genomik Veri Analizi Demosu / Applied Sample Genomic Data Analysis Demo**

---

## ✨ Öne Çıkan Özellikler / Key Features

- **GenoStream v4.0.3:** NCBI & EBI/ENA üzerinden akıllı veri edinimi / Smart data acquisition via NCBI & EBI/ENA.
- **Resilient QC Pipeline:** Stabilize edilmiş kalite kontrol iş akışı / Stabilized quality control workflow.
- **Interactive Visuals:** Bellek dostu görselleştirme motoru / Memory-efficient visualization engine.

---

## ✅ Destek Durumu / Support Status

**Şu an hedeflenen / Current focus:**
- **Google Colab (Primary):** Colab çalışma zamanı uyumluluğu / Colab runtime compatibility.
- **FASTQ Tabanlı Analiz / FASTQ Based Analysis:** Ham veri işleme / Raw data processing.

**Genişletilebilir / Roadmap:**
- **Platform Çeşitliliği / Platform Diversity:** Illumina, Ion Torrent, PacBio, Oxford Nanopore.

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
