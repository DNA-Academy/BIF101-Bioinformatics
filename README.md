# 🧬 BIF101: Bioinformatics Data Analysis Pipeline

![Version](https://img.shields.io/badge/version-4.0.3-blue)
![Platform](https://img.shields.io/badge/platform-Google%20Colab-orange)
![Course](https://img.shields.io/badge/course-BIF101-red)
![License](https://img.shields.io/badge/license-MIT-green)

> DNA Academy BIF101 modülü için uçtan uca veri indirme, kalite kontrol ve raporlama altyapısı.  
> An end-to-end data fetching, QC, and reporting toolkit for the DNA Academy BIF101 module.

---

## 🎓 Biyoinformatik - Genomik Veri Analizlerine Giriş (BIF101)
[cite_start]**"Genomik veri analizlerine sağlam bir adım; bilgi kirliliğinden uzak, yalın temellerle başlar."** [cite: 143]

Bu depo, DNA Academy tarafından düzenlenen **Sertifika Eğitimi** kapsamında kullanılan resmi uygulama platformudur. [cite_start]Program, ham veri kalitesinin analiz başarısının %75'ini belirlediği vizyonuyla, katılımcılara çözüm odaklı bir biyoinformatik deneyimi sunar.

### 🗓️ Eğitim Bilgileri & Kayıt / Enrollment
Yeni dönem eğitim tarihleri, saatleri ve kontenjan bilgileri için aşağıdaki bağlantıları kullanabilirsiniz:

[![Eğitim Takvimi](https://img.shields.io/badge/🗓️-Eğitim_Takvimi-blue?style=for-the-badge)](https://github.com/DNA-Academy/BIF101-Bioinformatics/tree/main/docs/tr/Egitim_Detaylari.md)
[![Kayıt Ol](https://img.shields.io/badge/✍️-Şimdi_Kaydol-green?style=for-the-badge)](https://www.nardobiotech.com/dna-academy)

---

## 📚 Sertifika Programı Müfredatı | Course Curriculum
[cite_start]Katılımcıların kodlama bilgisi gerekmeden [cite: 147] genomik veri analizlerini adım adım gerçekleştirmesini sağlayan modüllerimiz:

1. [cite_start]**NGS ve 3. Nesil Dizileme:** Illumina, Ion Torrent ve ONT teknolojilerinin prensipleri[cite: 65, 87, 106].
2. [cite_start]**Veri Kalite Kontrolü (QC):** FastQC ve NanoPlot ile ham veri değerlendirme ve temizleme[cite: 134, 143].
3. [cite_start]**Hizalama (Mapping):** Minimap2 ve BWA ile referans genoma hizalama, SAM/BAM yönetimi[cite: 142].
4. [cite_start]**Varyant Tespiti:** SNP ve Indel analizi, VCF dosyalarının yorumlanması[cite: 135].
5. [cite_start]**Görselleştirme & Raporlama:** IGV kullanımı ve biyolojik anlamlandırma[cite: 142].
6. **Biyoinformatik Platformlar:** Google Colab, Galaxy ve bulut tabanlı araçların etkin kullanımı.

---

## ✨ Öne Çıkan Özellikler | Key Features

- [cite_start]**GenoStream v4.0.3:** NCBI & EBI/ENA entegrasyonu ile gerçek NGS (Illumina - Ion Torrent) ve ONT verileri üzerinde uygulamalı veri edinimi[cite: 65, 87, 106, 137].
- **Resilient QC Pipeline:** FastQC / NanoPlot çıktılarını MultiQC altında birleştiren, Google Colab için stabilize edilmiş iş akışı.
- **Interactive Visuals:** Plotly tabanlı, bellek dostu örnekleme yaklaşımıyla görselleştirme.

---

## ✅ Destek Durumu | Support Status

**Şu an hedeflenen / pratikte kullanılan:**
- Google Colab (primary)
- FASTQ tabanlı QC ve MultiQC raporlama

**Genişletilebilir (yol haritası / senaryoya bağlı):**
- [cite_start]Platform çeşitliliği (Illumina / ONT / PacBio / Ion Torrent) veri formatına ve indirme kaynağına bağlı olarak ele alınır[cite: 65, 68, 87, 106].

> Not: Platform isimleri “cihaz” değil, üretilen verinin format ve QC karakteristiği bağlamında kullanılmaktadır.

---

## 📂 Dosya Yapısı | Directory Structure

```text
├── src/bif101/                 # Core Library / Çekirdek Kütüphane
│   ├── genostream.py           # Data Streaming / Veri İndirme
│   ├── plotting.py             # Analysis & Dashboards / Görselleştirme
│   ├── pipeline.py             # Workflow Management / İş Akışı
│   └── utils.py                # Setup & Patches / Kurulum ve Onarım
├── docs/                       # Curriculum & Guides / Müfredat & Rehber (TR/EN)
├── notebooks/                  # Tutorials / Uygulama Rehberleri (TR/EN)
├── data/                       # Local/Generated Data (gitignored)
└── reports/                    # QC Reports (gitignored)
