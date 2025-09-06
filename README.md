# 🧪 LYS - Laboratuvar Yönetim Sistemi

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.27+-red.svg)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-3-green.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Laboratuvar Yönetim Sistemi**, laboratuvarlar için geliştirilmiş kapsamlı bir numune analiz ve yönetim sistemidir. Modern web teknolojileri kullanılarak geliştirilmiş olan bu sistem, numune taleplerinden analiz sonuçlarına kadar tüm süreçleri dijitalleştiren bir demodur.

## 🚀 Canlı Demo

**Uygulamayı hemen deneyin:** [https://labyzlm-rizakutlu.streamlit.app/](https://labyzlm-rizakutlu.streamlit.app/)


## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Teknoloji Stack](#-teknoloji-stack)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Proje Yapısı](#-proje-yapısı)
- [API Dokümantasyonu](#-api-dokümantasyonu)
- [Güvenlik](#-güvenlik)
- [Katkıda Bulunma](#-katkıda-bulunma)
- [Lisans](#-lisans)
- [İletişim](#-iletişim)

## ✨ Özellikler

### 🔬 Numune Yönetimi
- **Numune Talep Sistemi**: Dış kullanıcılar için kolay talep oluşturma
- **Talep Takibi**: Gerçek zamanlı durum takibi
- **Çoklu Analiz Türü**: MFI, TGA, LOI, FTIR, Sertlik analizleri
- **Dosya Yönetimi**: Numune görselleri ve TDS/SDS dosya yükleme
- **Termin Takibi**: Analiz termin tarihleri ve uyarılar

### 👥 Kullanıcı Yönetimi
- **Çoklu Kullanıcı Desteği**: Laboratuvar personeli ve dış kullanıcılar
- **Rol Tabanlı Erişim**: Farklı yetki seviyeleri
- **Güvenli Giriş**: SHA-256 hash ile şifre koruması

### 📊 Analiz Yönetimi
- **Analiz Sonuç Girişi**: Detaylı test sonuçları
- **Rapor Oluşturma**: PDF formatında analiz raporları
- **Cihaz Takibi**: Kullanılan cihazlar ve kalibrasyon bilgileri
- **Personel Atama**: Analist ve onaylayan personel bilgileri

### 📦 Stok Yönetimi
- **Envanter Takibi**: Kimyasal ve malzeme stokları
- **Giriş/Çıkış**: Stok hareketleri ve miktar takibi
- **Minimum Stok Uyarıları**: Otomatik stok seviyesi kontrolü
- **Dolap Organizasyonu**: Laboratuvar dolap düzeni

### 📚 Dokümantasyon
- **Eğitim Materyalleri**: Video ve sunum arşivi
- **SOP Yönetimi**: Standart operasyon prosedürleri
- **Metot Dokümanları**: Analiz metotları ve formlar

### 📈 Raporlama ve Analitik
- **Dashboard**: Genel istatistikler ve metrikler
- **Excel Raporları**: Detaylı veri dışa aktarma
- **Grafik Analizler**: Analiz türleri ve firma bazlı dağılımlar
- **Takvim Görünümü**: Termin takibi ve planlama

### 🔧 Cihaz Yönetimi
- **Cihaz Envanteri**: MFI, TGA, LOI, FTIR cihazları
- **Bakım Takibi**: Periyodik bakım ve kalibrasyon
- **Rapor Arşivi**: Cihaz performans raporları

## 🛠 Teknoloji Stack

### Backend
- **Python 3.8+**: Ana programlama dili
- **Streamlit**: Web uygulaması framework'ü
- **SQLite**: Veritabanı yönetimi
- **Pandas**: Veri işleme ve analiz

### Frontend
- **Streamlit Components**: Modern UI bileşenleri
- **CSS3**: Özel stil ve animasyonlar
- **Responsive Design**: Mobil uyumlu tasarım

### Veri İşleme
- **PIL (Pillow)**: Görsel işleme
- **OpenPyXL**: Excel dosya işleme
- **Hashlib**: Güvenlik ve şifreleme

### Geliştirme Araçları
- **Git**: Versiyon kontrolü
- **GitHub**: Kod deposu ve işbirliği
- **Streamlit Cloud**: Deployment platformu

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git

### Adım 1: Projeyi Klonlayın
```bash
git clone https://github.com/RzaKUTLU/labyzlm.git
cd labyzlm
```

### Adım 2: Sanal Ortam Oluşturun (Önerilen)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Adım 3: Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### Adım 4: Uygulamayı Başlatın
```bash
streamlit run app.py
```

### Adım 5: Tarayıcıda Açın
Uygulama otomatik olarak `http://localhost:8501` adresinde açılacaktır.

## 📖 Kullanım

### İlk Giriş
1. Uygulamayı başlattıktan sonra giriş sayfası açılır
2. **Laboratuvar Personeli** veya **Numune Analiz Talebi** seçin
3. Laboratuvar personeli için:
   - Kullanıcı adı: `rızakutlu`
   - Şifre: `1234`

### Numune Talep Etme
1. "Numune Analiz Talebi" seçin
2. Kişisel bilgilerinizi girin
3. Numune detaylarını belirtin
4. Analiz türünü seçin
5. Gerekli dosyaları yükleyin
6. Talebi gönderin

### Laboratuvar Yönetimi
1. Laboratuvar personeli olarak giriş yapın
2. **Yeni Talepler** sekmesinden gelen talepleri değerlendirin
3. **Analiz Yönetimi** ile test sonuçlarını girin
4. **Raporlar** sekmesinden istatistikleri görüntüleyin

## 📁 Proje Yapısı

```
labyzlm/
├── app.py                 # Ana uygulama dosyası
├── requirements.txt       # Python bağımlılıkları
├── laboratuvar.db        # Ana veritabanı
├── database.db           # İkincil veritabanı
├── MFI.xlsx             # MFI cihaz raporu
├── TGA.xlsx             # TGA cihaz raporu
├── mfı.jpg              # MFI cihaz görseli
├── tga.jpg              # TGA cihaz görseli
├── README.md            # Proje dokümantasyonu
└── .gitignore           # Git ignore dosyası
```

### Veritabanı Şeması

#### Ana Tablolar
- **numune_talepler**: Numune talep bilgileri
- **stok**: Stok envanteri
- **stok_hareket**: Stok giriş/çıkış kayıtları
- **dolap_icerik**: Laboratuvar dolap organizasyonu
- **cihaz_bakim**: Cihaz bakım kayıtları
- **egitim_materyalleri**: Eğitim içerikleri
- **dokumanlar**: Doküman arşivi

## 🔧 API Dokümantasyonu

### Temel Fonksiyonlar

#### Veritabanı İşlemleri
```python
def init_db():
    """Veritabanı bağlantısını başlatır"""
    
def generate_talep_no():
    """Benzersiz talep numarası oluşturur"""
    
def check_db_connection(conn):
    """Veritabanı bağlantısını kontrol eder"""
```

#### Kullanıcı Yönetimi
```python
def show_login():
    """Giriş sayfasını gösterir"""
    
def show_external_form():
    """Dış kullanıcı talep formunu gösterir"""
```

#### Numune Yönetimi
```python
def show_lab_evaluation():
    """Laboratuvar değerlendirme sayfası"""
    
def show_request_query():
    """Talep sorgulama sayfası"""
    
def show_analytics_dashboard():
    """Analitik dashboard"""
```

## 🔒 Güvenlik

### Mevcut Güvenlik Önlemleri
- SHA-256 ile şifre hash'leme
- Session state yönetimi
- SQL injection koruması (parametreli sorgular)
- Dosya türü validasyonu

### Güvenlik Önerileri
- [ ] JWT token tabanlı kimlik doğrulama
- [ ] HTTPS zorunluluğu
- [ ] Rate limiting
- [ ] Input sanitization
- [ ] Audit logging

## 🧪 Test

### Test Çalıştırma
```bash
# Unit testler (gelecekte eklenecek)
python -m pytest tests/

# Kod kalitesi kontrolü
flake8 app.py
black app.py
```

### Test Kapsamı
- [ ] Unit testler
- [ ] Integration testler
- [ ] UI testler
- [ ] Performance testler

## 🚀 Deployment

### Streamlit Cloud
1. GitHub repository'sini Streamlit Cloud'a bağlayın
2. `app.py` dosyasını ana dosya olarak seçin
3. Gerekli environment variables'ları ayarlayın
4. Deploy edin

### Docker (Gelecek)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 📊 Performans

### Sistem Gereksinimleri
- **Minimum**: 2GB RAM, 1 CPU core
- **Önerilen**: 4GB RAM, 2 CPU core
- **Disk**: 1GB boş alan

### Optimizasyon Önerileri
- Veritabanı indeksleme
- Görsel sıkıştırma
- Lazy loading
- Caching mekanizması

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

### Geliştirme Kuralları
- PEP 8 kod stili
- Anlamlı commit mesajları
- Test coverage %80+
- Dokümantasyon güncellemeleri

## 🐛 Bilinen Sorunlar

- [ ] Büyük dosya yüklemelerinde performans sorunu
- [ ] Mobil cihazlarda bazı UI sorunları
- [ ] Çoklu kullanıcı eş zamanlı işlem sorunları

## 📝 Changelog

### v1.0.0 (2024-09-06)
- İlk sürüm yayınlandı
- Temel numune yönetimi özellikleri
- Stok yönetimi sistemi
- Raporlama ve analitik

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👨‍💻 Geliştirici

**Rıza Kutlu**
- GitHub: [@RzaKUTLU](https://github.com/RzaKUTLU)
- Email: [İletişim için GitHub üzerinden mesaj atın]

## 🙏 Teşekkürler

- Streamlit ekibine harika framework için
- Python topluluğuna açık kaynak kütüphaneler için
- Tüm katkıda bulunanlara

## 📞 Destek

Sorularınız için:
- GitHub Issues: [Issues sayfası](https://github.com/RzaKUTLU/labyzlm/issues)
- Email: GitHub üzerinden iletişim
- Dokümantasyon: Bu README dosyası

---

**Not**: Bu proje eğitim ve geliştirme amaçlıdır. Üretim ortamında kullanmadan önce güvenlik testlerini yapın.

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
