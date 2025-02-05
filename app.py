import streamlit as st
import pandas as pd
import datetime
import sqlite3
import hashlib
import os
from PIL import Image
import io
import sys
import traceback
import requests
from io import BytesIO
import re
import time

# Talep numarası oluşturma fonksiyonu - EN BAŞA EKLENDİ
def generate_talep_no():
    try:
        conn = sqlite3.connect('laboratuvar.db')
        cur = conn.cursor()
        
        # Son talep numarasını al
        cur.execute("SELECT talep_no FROM numune_talepler ORDER BY talep_no DESC LIMIT 1")
        son_talep = cur.fetchone()
        
        if son_talep:
            try:
                # Son talep numarasından sayıyı çıkar ve 1 artır
                son_no = int(son_talep[0].split('-')[1])
                yeni_no = son_no + 1
            except (IndexError, ValueError):
                # Eğer mevcut format farklıysa yeni seri başlat
                yeni_no = 100001
        else:
            # İlk talep numarası
            yeni_no = 100001
        
        # Yeni talep numarasını oluştur
        yeni_talep_no = f"BRSN-{yeni_no}"
        
        return yeni_talep_no
        
    except Exception as e:
        st.error(f"Talep numarası oluşturma hatası: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

try:
    from streamlit_option_menu import option_menu
except ImportError:
    st.error("streamlit-option-menu modülü eksik. Lütfen 'pip install streamlit-option-menu' komutunu çalıştırın.")
    st.stop()

# Uygulama dizinini Python yoluna ekle
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.append(app_dir)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'user_type' not in st.session_state:
    st.session_state['user_type'] = None  # 'lab' veya 'external'

if 'username' not in st.session_state:
    st.session_state['username'] = None

if 'form_data' not in st.session_state:
    st.session_state['form_data'] = {}

# Kullanıcı bilgileri
LAB_USERS = {
    "rızakutlu": hashlib.sha256("1234".encode()).hexdigest(),
    "lab_user2": hashlib.sha256("pass2".encode()).hexdigest()
}

# Global sabitler
KATEGORILER = [
    "Kimyasal",
    "Sarf Malzeme",
    "Hammadde",
    "Standart",
    "Kalibrasyon Malzemesi",
    "Diğer"
]

BIRIMLER = [
    "adet",
    "gram (g)",
    "kilogram (kg)",
    "mililitre (ml)",
    "litre (L)",
    "paket",
    "kutu"
]

# Veritabanı bağlantı fonksiyonlarını en başa taşıyalım (import'lardan sonra)
def get_database_connection():
    """Veritabanı bağlantısını kontrol eder ve döndürür"""
    try:
        # Veritabanı dosyasının tam yolunu belirle
        db_path = os.path.join(os.getcwd(), "laboratuvar.db")
        
        # Veritabanı bağlantısını oluştur
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {str(e)}")
        return None

# Veritabanı yönetimi için yeni fonksiyonlar
def create_new_db(db_path):
    """Yeni bir veritabanı oluşturur"""
    try:
        # Yeni bir bağlantı oluştur
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Foreign key desteğini aktifleştir
        c.execute("PRAGMA foreign_keys = ON")
        
        # Tabloyu oluştur
        c.execute('''
            CREATE TABLE IF NOT EXISTS numune_talepler (
                talep_no TEXT PRIMARY KEY,
                numune_adi TEXT NOT NULL,
                firma TEXT NOT NULL,
                analiz_turu TEXT NOT NULL,
                tahribat TEXT,
                iade TEXT,
                numune_gorseli BLOB,
                miktar TEXT NOT NULL,
                saklama_kosullari TEXT,
                termin_tarihi DATE,
                tds_dosya BLOB,
                durum TEXT DEFAULT 'Beklemede',
                red_nedeni TEXT,
                red_gorseli BLOB,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Analiz sonuç alanları
                test_tekrar_sayisi INTEGER,
                cihaz_adi_kodu TEXT,
                analist_personel TEXT,
                raporlayan_personel TEXT,
                teslim_alan_personel TEXT,
                uygulanan_testler TEXT,
                analiz_raporu BLOB,
                analiz_tarihi DATE,
                
                -- Yeni eklenen kişisel bilgi alanları
                talep_eden_adsoyad TEXT,
                talep_eden_gorev TEXT,
                talep_eden_telefon TEXT,
                talep_eden_email TEXT,
                analiz_turleri TEXT,
                aciklama TEXT,
                kimyasal_risk TEXT
            )
        ''')
        
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Veritabanı oluşturma hatası: {str(e)}")
        return None

def init_db():
    conn = sqlite3.connect('laboratuvar.db')
    c = conn.cursor()
    
    # Tabloyu sadece yoksa oluştur
    c.execute("""
        CREATE TABLE IF NOT EXISTS numune_talepler (
            talep_no TEXT PRIMARY KEY,
            numune_adi TEXT NOT NULL,
            firma TEXT NOT NULL,
            analiz_turu TEXT NOT NULL,
            miktar TEXT NOT NULL,
            talep_eden_adsoyad TEXT,
            talep_eden_gorev TEXT,
            talep_eden_telefon TEXT,
            talep_eden_email TEXT,
            saklama_kosullari TEXT,
            termin_tarihi DATE,
            tds_dosya BLOB,
            numune_gorseli BLOB,
            aciklama TEXT,
            kimyasal_risk TEXT,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            durum TEXT DEFAULT 'Yeni Talep', -- Varsayılan durum
            red_nedeni TEXT,
            red_gorseli BLOB,
            test_tekrar INTEGER,
            kullanilan_cihaz TEXT,
            analist_adsoyad TEXT,
            analiz_tarihi DATE,
            analiz_sonucu TEXT,
            analiz_raporu BLOB,
            analiz_aciklama TEXT,
            sonuc_onaylayan TEXT
        )
    """)
    
    conn.commit()
    return conn

def check_db_connection(conn):
    """Veritabanı bağlantısını kontrol eder"""
    if conn is None:
        return False
    try:
        conn.cursor().execute("SELECT 1")
        return True
    except:
        return False

# Veritabanı bağlantı testi
def test_db():
    """Veritabanı bağlantısını test eder"""
    conn = init_db()
    if conn is not None:
        try:
            c = conn.cursor()
            c.execute("SELECT 1")
            conn.close()
            return True
        except:
            if conn:
                conn.close()
            return False
    return False

# Uygulama başlangıcında veritabanını test et
if not test_db():
    st.error("Veritabanı başlatılamadı! Lütfen uygulamayı yeniden başlatın.")
    st.stop()

# Stil ayarları için fonksiyon
def set_page_style(user_type):
    if user_type == 'lab':
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(to right bottom, 
                                          rgba(240, 249, 255, 0.9), 
                                          rgba(179, 213, 255, 0.9)) !important;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(to right bottom, 
                                          rgba(246, 248, 250, 0.9), 
                                          rgba(176, 196, 222, 0.9)) !important;
            }
            </style>
        """, unsafe_allow_html=True)

# Talep sorgulama fonksiyonu
def show_request_query():
    st.title("🔍 Talep Sorgula")
    
    talep_no = st.text_input("Talep Numarasını Giriniz:")
    
    if talep_no:
        try:
            conn = sqlite3.connect('laboratuvar.db')
            cur = conn.cursor()
            
            # Tüm sütunları getir
            cur.execute("""
                SELECT * FROM numune_talepler 
                WHERE talep_no = ?
            """, (talep_no,))
            
            talep = cur.fetchone()
            
            if talep:
                # Durum bilgisi
                durum_renk = {
                    "Yeni Talep": "🟡",
                    "İnceleniyor": "🔵",
                    "Tamamlandı": "🟢",
                    "Red": "🔴"
                }
                st.markdown(f"### {durum_renk.get(talep[16], '⚪')} Talep Durumu: {talep[16]}")
                
                # Talep detayları
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📝 Talep Bilgileri")
                    st.write(f"**Talep No:** {talep[0]}")
                    st.write(f"**Oluşturma Tarihi:** {talep[15]}")
                    st.write(f"**Termin Tarihi:** {talep[10]}")
                    
                    st.markdown("\n#### 🧪 Numune Bilgileri")
                    st.write(f"**Numune Adı:** {talep[1]}")
                    st.write(f"**Firma:** {talep[2]}")
                    st.write(f"**Analiz Türü:** {talep[3]}")
                    st.write(f"**Miktar:** {talep[4]}")
                    
                    if talep[9]:  # saklama_kosullari
                        st.write(f"**Saklama Koşulları:** {talep[9]}")
                    if talep[14]:  # kimyasal_risk
                        st.write(f"**Kimyasal Risk:** {talep[14]}")
                
                with col2:
                    st.markdown("#### 👤 İletişim Bilgileri")
                    st.write(f"**Ad Soyad:** {talep[5]}")
                    st.write(f"**Görev:** {talep[6]}")
                    st.write(f"**Telefon:** {talep[7]}")
                    st.write(f"**E-posta:** {talep[8]}")
                    
                    if talep[13]:  # aciklama
                        st.markdown("\n#### 📝 Açıklama")
                        st.info(talep[13])
                
                # Dosya ve görseller
                col3, col4 = st.columns(2)
                
                with col3:
                    if talep[12]:  # numune_gorseli
                        st.markdown("#### 📷 Numune Görseli")
                        image = Image.open(io.BytesIO(talep[12]))
                        st.image(image, use_column_width=True)
                
                with col4:
                    if talep[11]:  # tds_dosya
                        st.markdown("#### 📄 TDS/SDS Dosyası")
                        st.download_button(
                            label="📄 TDS/SDS Dosyasını İndir",
                            data=talep[11],
                            file_name=f"TDS_{talep[0]}.pdf",
                            mime="application/pdf"
                        )
                
                # Analiz sonuçları (eğer tamamlandıysa)
                if talep[16] == "Tamamlandı":
                    st.markdown("### 📊 Analiz Sonuçları")
                    col5, col6 = st.columns(2)
                    
                    with col5:
                        st.write("**Test Bilgileri**")
                        st.write(f"**Test Tekrar Sayısı:** {talep[19]}")
                        st.write(f"**Kullanılan Cihaz:** {talep[20]}")
                        st.write(f"**Analist:** {talep[21]}")
                        st.write(f"**Analiz Tarihi:** {talep[22]}")
                    
                    with col6:
                        st.write("**Sonuç Bilgileri**")
                        st.write(f"**Analiz Sonucu:** {talep[23]}")
                        if talep[25]:  # analiz_aciklama
                            st.write(f"**Açıklama:** {talep[25]}")
                        st.write(f"**Onaylayan:** {talep[26]}")
                    
                    if talep[24]:  # analiz_raporu
                        st.download_button(
                            label="📄 Analiz Raporunu İndir",
                            data=talep[24],
                            file_name=f"Analiz_Raporu_{talep[0]}.pdf",
                            mime="application/pdf"
                        )
                
                # Red durumu
                elif talep[16] == "Red":
                    st.error("❌ Talep Reddedildi")
                    st.write(f"**Red Nedeni:** {talep[17]}")
                    
                    if talep[18]:  # red_gorseli
                        st.markdown("### 📷 Red Görseli")
                        image = Image.open(io.BytesIO(talep[18]))
                        st.image(image, use_column_width=True)
            
            else:
                st.error("❌ Talep bulunamadı!")
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")
            st.error(traceback.format_exc())
        finally:
            if conn:
                conn.close()

# Analytics Dashboard fonksiyonu
def show_analytics_dashboard():
    st.title("📊 Analiz ve Raporlar")
    
    # Tarih filtresi
    col1, col2 = st.columns(2)
    with col1:
        baslangic = st.date_input("Başlangıç Tarihi", 
                                 value=datetime.date.today() - datetime.timedelta(days=30))
    with col2:
        bitis = st.date_input("Bitiş Tarihi", 
                             value=datetime.date.today())
    
    # İstatistikler
    try:
        conn = init_db()
        if conn:
            cur = conn.cursor()
            
            # Toplam talep ve durum istatistikleri
            cur.execute("""
                SELECT 
                    COUNT(*) as toplam,
                    SUM(CASE WHEN durum = 'Kabul' THEN 1 ELSE 0 END) as kabul,
                    SUM(CASE WHEN durum = 'Red' THEN 1 ELSE 0 END) as red,
                    SUM(CASE WHEN durum = 'Beklemede' THEN 1 ELSE 0 END) as beklemede
                FROM numune_talepler 
                WHERE DATE(olusturma_tarihi) BETWEEN ? AND ?
            """, (baslangic, bitis))
            
            istatistikler = cur.fetchone()
            
            # İstatistik kartları
            st.markdown("### 📈 Genel İstatistikler")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Toplam Talep", istatistikler[0] if istatistikler[0] else 0)
            with col2:
                st.metric("Kabul Edilen", istatistikler[1] if istatistikler[1] else 0)
            with col3:
                st.metric("Reddedilen", istatistikler[2] if istatistikler[2] else 0)
            with col4:
                st.metric("Beklemede", istatistikler[3] if istatistikler[3] else 0)
            
            # Analiz türlerine göre dağılım
            st.markdown("### 📊 Analiz Türlerine Göre Dağılım")
            cur.execute("""
                SELECT analiz_turu, COUNT(*) as sayi
                FROM numune_talepler
                WHERE DATE(olusturma_tarihi) BETWEEN ? AND ?
                GROUP BY analiz_turu
                ORDER BY sayi DESC
            """, (baslangic, bitis))
            
            analiz_dagilimi = cur.fetchall()
            if analiz_dagilimi:
                df_analiz = pd.DataFrame(analiz_dagilimi, columns=['Analiz Türü', 'Talep Sayısı'])
                st.bar_chart(df_analiz.set_index('Analiz Türü'))
            else:
                st.info("Bu tarih aralığında analiz verisi bulunmuyor.")
            
            # Firma bazlı analiz
            st.markdown("### 🏢 Firma Bazlı Analiz")
            cur.execute("""
                SELECT firma, COUNT(*) as talep_sayisi
                FROM numune_talepler
                WHERE DATE(olusturma_tarihi) BETWEEN ? AND ?
                GROUP BY firma
                ORDER BY talep_sayisi DESC
                LIMIT 10
            """, (baslangic, bitis))
            
            firma_dagilimi = cur.fetchall()
            if firma_dagilimi:
                df_firma = pd.DataFrame(firma_dagilimi, columns=['Firma', 'Talep Sayısı'])
                st.bar_chart(df_firma.set_index('Firma'))
            else:
                st.info("Bu tarih aralığında firma verisi bulunmuyor.")
            
            # Detaylı rapor indirme
            st.markdown("### 📑 Detaylı Rapor")
            if st.button("📥 Excel Raporu İndir"):
                cur.execute("""
                    SELECT 
                        talep_no as 'Talep No',
                        numune_adi as 'Numune',
                        firma as 'Firma',
                        analiz_turu as 'Analiz Türü',
                        durum as 'Durum',
                        olusturma_tarihi as 'Oluşturma Tarihi',
                        termin_tarihi as 'Termin Tarihi'
                    FROM numune_talepler
                    WHERE DATE(olusturma_tarihi) BETWEEN ? AND ?
                    ORDER BY olusturma_tarihi DESC
                """, (baslangic, bitis))
                
                df_rapor = pd.DataFrame(cur.fetchall(), 
                                      columns=['Talep No', 'Numune', 'Firma', 'Analiz Türü', 
                                              'Durum', 'Oluşturma Tarihi', 'Termin Tarihi'])
                
                # Excel dosyası oluştur
                excel_buffer = io.BytesIO()
                df_rapor.to_excel(excel_buffer, index=False)
                excel_data = excel_buffer.getvalue()
                
                # Download butonu
                st.download_button(
                    label="📥 Excel Raporunu İndir",
                    data=excel_data,
                    file_name=f"analiz_raporu_{baslangic}_{bitis}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
    except Exception as e:
        st.error(f"Veri analizi hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

# Login sayfası
def show_login():
    st.markdown("""
        <style>
            .stApp {
                background: linear-gradient(to right bottom, 
                                          rgba(246, 248, 250, 0.9), 
                                          rgba(176, 196, 222, 0.9)) !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🧪 Laboratuvar Yönetim Sistemi")
    
    # Eğer logo/resim kullanıyorsanız:
    if 'logo' in st.session_state:
        st.image(st.session_state.logo, 
                use_container_width=True)  # use_column_width yerine use_container_width
    
    st.markdown('<p class="subtitle">Numune Analiz ve Takip Sistemi</p>', unsafe_allow_html=True)
    
    user_type = st.radio("Kullanıcı Tipi", ["Laboratuvar Personeli", "Numune Analiz Talebi"])
    
    if user_type == "Laboratuvar Personeli":
        with st.form("login_form"):
            username = st.text_input("👤 Kullanıcı Adı")
            password = st.text_input("🔒 Şifre", type="password")
            submitted = st.form_submit_button("Giriş Yap")
            
            if submitted:
                if username in LAB_USERS and LAB_USERS[username] == hashlib.sha256(password.encode()).hexdigest():
                    # Session state'i güncelle
                    st.session_state.logged_in = True
                    st.session_state.user_type = 'lab'
                    st.session_state.username = username
                    st.rerun()  # experimental_rerun yerine rerun
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")
    else:
        # Dış kullanıcı için session state güncelle
        st.session_state.logged_in = True
        st.session_state.user_type = 'external'
        st.session_state.username = 'Misafir'
        st.rerun()
    
    # Ana içerik div'ini kapat
    st.markdown("</div>", unsafe_allow_html=True)

# Dış kullanıcı formu
def show_external_form():
    st.title("Numune Analiz Talebi")
    
    # Form alanları
    with st.form("numune_talep_formu"):
        # Kişisel bilgiler bölümü
        st.markdown("### 👤 Kişisel Bilgiler")
        col1, col2 = st.columns(2)
        with col1:
            talep_eden_adsoyad = st.text_input("Ad Soyad*")
            talep_eden_gorev = st.text_input("Görev/Ünvan*")
        with col2:
            talep_eden_telefon = st.text_input("Telefon*")
            talep_eden_email = st.text_input("E-posta*")

        # Numune bilgileri bölümü
        st.markdown("### 📋 Numune Bilgileri")
        numune_adi = st.text_input("Numune Adı*", key="numune_adi")
        
        # Firma listesi
        FIRMA_LISTESI = [
            "CANİK",
            "SAMPA",
            "REEDER",
            "YEŞİLYURT",
            "POELSAN",
            "ROKETSAN",
            "TUSAŞ",
            "ASELSAN",
            "BORSAN",
            "BORLED",
            "Diğer"
        ]
        
        firma_secimi = st.selectbox("Firma*", FIRMA_LISTESI, key="firma_secimi")
        
        # Eğer "Diğer" seçilirse, manuel firma girişi göster
        if firma_secimi == "Diğer":
            firma = st.text_input("Firma Adı*", key="firma_manuel")
        else:
            firma = firma_secimi
        
        # Analiz türü seçimi - çoklu seçim için değiştirildi
        analiz_turleri = [
            "MFI (Erime Akış İndeksi)",
            "TGA (Termogravimetrik Analiz)",
            "LOI (Limit Oksijen İndeksi)",
            "FTIR (Fourier Dönüşümlü Kızılötesi Spektroskopisi)",
            "SERTLİK",
            "Diğer"
        ]
        
        # Çoklu seçim için multiselect kullan
        secilen_analizler = st.multiselect(
            "Analiz Türü*",
            analiz_turleri,
            help="Birden fazla analiz seçebilirsiniz"
        )
        
        # Eğer "Diğer" seçildiyse, açıklama alanı göster
        if "Diğer" in secilen_analizler:
            diger_analiz = st.text_input("Diğer Analiz Türü Açıklaması")
            # "Diğer" seçeneğini açıklamasıyla değiştir
            secilen_analizler = [x if x != "Diğer" else f"Diğer: {diger_analiz}" for x in secilen_analizler]
        
        # Seçilen analizleri string'e çevir
        analiz_turu = ", ".join(secilen_analizler)
        
        # Diğer form alanları
        miktar = st.number_input("Miktar*", min_value=0.1, value=1.0, step=0.1)
        birim = st.selectbox("Birim*", ["gram (g)", "kilogram (kg)", "adet", "mililitre (ml)", "litre (L)"])
        miktar_tam = f"{miktar} {birim}"
        
        saklama_kosullari = st.text_area("Saklama Koşulları")
        termin_tarihi = st.date_input("Termin Tarihi*", min_value=datetime.date.today())
        
        # Kimyasal risk sorusu
        kimyasal_risk = st.radio(
            "Numune Kimyasal Risk Taşır",
            options=["Evet", "Hayır"],
            horizontal=True
        )
        
        aciklama = st.text_area("Açıklama")
        
        # Dosya yükleme
        numune_gorseli = st.file_uploader("Numune Görseli", type=['png', 'jpg', 'jpeg'])
        tds_dosya = st.file_uploader("TDS/SDS Dosyası", type=['pdf', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Talebi Gönder")
        
        if submitted:
            if not all([talep_eden_adsoyad, talep_eden_gorev, talep_eden_telefon, 
                       talep_eden_email, numune_adi, firma, secilen_analizler, miktar_tam]):
                st.error("Lütfen zorunlu alanları doldurunuz!")
                return
            
            try:
                conn = init_db()
                cur = conn.cursor()
                
                # Talep numarası oluştur
                talep_no = generate_talep_no()
                if not talep_no:
                    st.error("Talep numarası oluşturulamadı!")
                    return
                
                # Dosya verilerini hazırla
                numune_gorseli_data = numune_gorseli.read() if numune_gorseli else None
                tds_dosya_data = tds_dosya.read() if tds_dosya else None
                
                # SQL sorgusunu düzelt
                cur.execute("""
                    INSERT INTO numune_talepler (
                        talep_no,
                        numune_adi,
                        firma,
                        analiz_turu,
                        miktar,
                        talep_eden_adsoyad,
                        talep_eden_gorev,
                        talep_eden_telefon,
                        talep_eden_email,
                        saklama_kosullari,
                        termin_tarihi,
                        tds_dosya,
                        numune_gorseli,
                        aciklama,
                        kimyasal_risk,
                        durum,
                        olusturma_tarihi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    talep_no,
                    numune_adi,
                    firma,
                    analiz_turu,
                    miktar_tam,
                    talep_eden_adsoyad,
                    talep_eden_gorev,
                    talep_eden_telefon,
                    talep_eden_email,
                    saklama_kosullari,
                    termin_tarihi,
                    tds_dosya_data,
                    numune_gorseli_data,
                    aciklama,
                    kimyasal_risk,
                    "Yeni Talep",  # Durum "Yeni Talep" olarak değiştirildi
                    # olusturma_tarihi otomatik ekleniyor
                ))
                
                conn.commit()
                st.success(f"""
                ✅ Analiz talebiniz başarıyla oluşturuldu!
                
                📝 Talep Numaranız: {talep_no}
                
                ℹ️ Bu numara ile talebinizin durumunu sorgulayabilirsiniz.
                """)
                
            except Exception as e:
                st.error(f"Kayıt hatası: {str(e)}")
                st.error(traceback.format_exc())
            finally:
                if conn:
                    conn.close()

# Laboratuvar personeli değerlendirme sayfası
def show_lab_evaluation():
    st.title("📋 Numune Değerlendirme")
    
    try:
        conn = sqlite3.connect('laboratuvar.db')
        cur = conn.cursor()
        
        # Durum filtresi
        durumlar = ["Hepsi", "Yeni Talep", "İnceleniyor", "Tamamlandı", "Red"]
        secili_durum = st.selectbox("Durum Filtresi", durumlar)
        
        # Tüm talepleri getir
        where_clause = "WHERE durum = ?" if secili_durum != "Hepsi" else ""
        query = f"""
            SELECT * FROM numune_talepler 
            {where_clause}
            ORDER BY olusturma_tarihi DESC
        """
        
        if secili_durum != "Hepsi":
            cur.execute(query, (secili_durum,))
        else:
            cur.execute("SELECT * FROM numune_talepler ORDER BY olusturma_tarihi DESC")
        
        talepler = cur.fetchall()
        
        if talepler:
            for talep in talepler:
                with st.expander(f"{talep[0]} - {talep[1]} ({talep[2]})"):
                    # Talep detayları
                    st.markdown("### 📋 Talep Detayları")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📝 Talep Bilgileri")
                        st.write(f"**Talep No:** {talep[0]}")
                        st.write(f"**Oluşturma Tarihi:** {talep[15]}")
                        st.write(f"**Termin Tarihi:** {talep[10]}")
                        st.write(f"**Durum:** {talep[16]}")
                        
                        st.markdown("\n#### 🧪 Numune Bilgileri")
                        st.write(f"**Numune Adı:** {talep[1]}")
                        st.write(f"**Firma:** {talep[2]}")
                        st.write(f"**Analiz Türü:** {talep[3]}")
                        st.write(f"**Miktar:** {talep[4]}")
                        
                        if talep[9]:  # saklama_kosullari
                            st.write(f"**Saklama Koşulları:** {talep[9]}")
                        if talep[14]:  # kimyasal_risk
                            st.write(f"**Kimyasal Risk:** {talep[14]}")
                    
                    with col2:
                        st.markdown("#### 👤 İletişim Bilgileri")
                        st.write(f"**Ad Soyad:** {talep[5]}")
                        st.write(f"**Görev:** {talep[6]}")
                        st.write(f"**Telefon:** {talep[7]}")
                        st.write(f"**E-posta:** {talep[8]}")
                        
                        if talep[13]:  # aciklama
                            st.markdown("\n#### 📝 Açıklama")
                            st.info(talep[13])
                    
                    # Dosya ve görseller
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        if talep[12]:  # numune_gorseli
                            st.markdown("#### 📷 Numune Görseli")
                            image = Image.open(io.BytesIO(talep[12]))
                            st.image(image, use_column_width=True)
                    
                    with col4:
                        if talep[11]:  # tds_dosya
                            st.markdown("#### 📄 TDS/SDS Dosyası")
                            st.download_button(
                                label="📄 TDS/SDS Dosyasını İndir",
                                data=talep[11],
                                file_name=f"TDS_{talep[0]}.pdf",
                                mime="application/pdf"
                            )
                    
                    # Durum güncelleme bölümü
                    st.markdown("### ⚙️ Durum Güncelleme")
                    col5, col6 = st.columns(2)
                    
                    with col5:
                        if talep[16] == "Yeni Talep" and st.button("✅ Kabul Et", key=f"kabul_{talep[0]}"):
                            cur.execute("""
                                UPDATE numune_talepler 
                                SET durum = 'İnceleniyor'
                                WHERE talep_no = ?
                            """, (talep[0],))
                            conn.commit()
                            st.success("✅ Numune kabul edildi!")
                            st.rerun()
                    
                    with col6:
                        if talep[16] in ["Yeni Talep", "İnceleniyor"] and st.button("❌ Reddet", key=f"red_{talep[0]}"):
                            red_nedeni = st.text_area("Red Nedeni", key=f"red_nedeni_{talep[0]}")
                            if red_nedeni:
                                cur.execute("""
                                    UPDATE numune_talepler 
                                    SET durum = 'Red',
                                        red_nedeni = ?
                                    WHERE talep_no = ?
                                """, (red_nedeni, talep[0]))
                                conn.commit()
                                st.error("❌ Numune reddedildi!")
                                st.rerun()
        else:
            st.info("📭 Bekleyen numune talebi bulunmuyor.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
        st.error(traceback.format_exc())
    finally:
        if conn:
            conn.close()

def execute_db_operation(operation, params=None):
    """Veritabanı işlemlerini güvenli bir şekilde yürütür"""
    conn = init_db()
    if not check_db_connection(conn):
        return False
    
    try:
        c = conn.cursor()
        if params:
            c.execute(operation, params)
        else:
            c.execute(operation)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Veritabanı işlem hatası: {str(e)}")
        return False
    finally:
        conn.close()

# Stil tanımlamaları - Ana stil bloğunu güncelleyin
st.markdown("""
    <style>
    /* Login sayfası için gradient */
    .stApp {
        background: linear-gradient(to right bottom, 
                                  rgba(246, 248, 250, 0.9), 
                                  rgba(176, 196, 222, 0.9)) !important;
    }
    
    /* Laboratuvar personeli sayfası için stil */
    .lab-page {
        background: linear-gradient(to right bottom, 
                                  rgba(200, 230, 255, 0.9), 
                                  rgba(150, 180, 220, 0.9)) !important;
    }
    
    /* Numune talep sayfası için stil */
    .external-page {
        background: linear-gradient(to right bottom, 
                                  rgba(230, 240, 255, 0.9), 
                                  rgba(180, 200, 230, 0.9)) !important;
    }
    
    /* Genel container stilleri */
    .content-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 30px;
        border-radius: 15px;
        margin: 20px auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Form elemanları için stil */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        background-color: white !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        padding: 10px !important;
        border-radius: 5px !important;
    }
    
    /* Radio butonları için stil */
    .stRadio>div {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    /* Butonlar için stil */
    .stButton>button {
        width: 100%;
        background-color: #0066cc !important;
        color: white !important;
        height: 45px;
        font-size: 16px;
        border-radius: 8px;
        border: none;
        margin-top: 10px;
        transition: all 0.3s ease;
    }
    
    /* Çıkış butonu için özel stil */
    .logout-btn>button {
        background-color: #dc3545 !important;
    }
    
    /* Başlıklar için stil */
    h1, h2, h3 {
        color: #1E1E1E;
        margin-bottom: 20px;
        padding: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
    }
    
    /* Expander için stil */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 5px !important;
    }
    
    /* Tab için stil */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        padding: 10px 5px 0 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 5px 5px 0 0;
    }
    
    /* Çıkış butonu için özel stil */
    .stButton>button[kind="primary"] {
        background-color: #dc3545 !important;
        color: white !important;
        width: 150px !important;  /* Butonu genişlet */
        height: 45px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    /* Çıkış butonu hover efekti */
    .stButton>button[kind="primary"]:hover {
        background-color: #c82333 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.2) !important;
    }
    
    /* Çıkış butonu container */
    .logout-container {
        display: flex;
        justify-content: flex-end;
        padding: 10px;
    }
    
    /* Selectbox için özel stil */
    div[data-baseweb="select"] {
        margin-bottom: 15px;
    }
    
    div[data-baseweb="select"] > div {
        min-height: 45px;
        white-space: normal;
        word-wrap: break-word;
    }
    
    div[data-baseweb="select"] span {
        white-space: normal;
        line-height: 1.2;
        padding: 5px 0;
    }
    
    div[data-baseweb="popover"] div {
        white-space: normal;
        word-wrap: break-word;
        line-height: 1.2;
        padding: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Yeni fonksiyon ekleyelim - Benzersiz talep numarası oluşturma
def generate_unique_talep_no():
    conn = None
    try:
        conn = init_db()
        c = conn.cursor()
        
        # En son talep numarasını bul
        c.execute("SELECT talep_no FROM numune_talepler ORDER BY talep_no DESC LIMIT 1")
        last_no = c.fetchone()
        
        if last_no and last_no[0]:
            try:
                # Son talep numarasından sayıyı çıkar ve 1 artır
                last_number = int(last_no[0].split('-')[1])
                new_number = last_number + 1
            except (IndexError, ValueError):
                new_number = 100001
        else:
            # İlk talep numarası
            new_number = 100001
        
        # Yeni talep numarasını formatla
        new_talep_no = f"BRSN-{new_number}"
        
        # Benzersizlik kontrolü
        while True:
            c.execute("SELECT COUNT(*) FROM numune_talepler WHERE talep_no = ?", (new_talep_no,))
            if c.fetchone()[0] == 0:
                break
            new_number += 1
            new_talep_no = f"BRSN-{new_number}"
        
        return new_talep_no
    
    except Exception as e:
        st.error(f"Talep numarası oluşturma hatası: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

# Tamamlanan analizleri gösteren yeni fonksiyon
def show_completed_analysis():
    conn = init_db()
    try:
        # Analizi tamamlanmış talepleri getir (analiz_raporu dolu olanlar)
        df = pd.read_sql_query("""
            SELECT * FROM numune_talepler 
            WHERE durum='Kabul' 
            AND analiz_raporu IS NOT NULL 
            ORDER BY analiz_tarihi DESC
        """, conn)
        
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"📊 {row['talep_no']} - {row['numune_adi']} ({row['firma']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("*Analiz Bilgileri*")
                        st.write(f"🔬 Analiz: {row['analiz_turu']}")
                        st.write(f"📅 Analiz Tarihi: {row['analiz_tarihi']}")
                        st.write(f"🧪 Test Tekrarı: {row['test_tekrar_sayisi']}")
                        st.write(f"⚙️ Cihaz: {row['cihaz_adi_kodu']}")
                    
                    with col2:
                        st.write("*Personel Bilgileri*")
                        st.write(f"👨‍🔬 Analist: {row['analist_personel']}")
                        st.write(f"📝 Raporlayan: {row['raporlayan_personel']}")
                        st.write(f"👥 Teslim Alan: {row['teslim_alan_personel']}")
                    
                    st.write("*Uygulanan Testler*")
                    st.info(row['uygulanan_testler'])
                    
                    if row['analiz_raporu']:
                        st.download_button(
                            "📄 Analiz Raporunu İndir",
                            row['analiz_raporu'],
                            file_name=f"Analiz_Raporu_{row['talep_no']}.pdf",
                            mime="application/pdf"
                        )
        else:
            st.info("Tamamlanmış analiz bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        conn.close()

# show_accepted_requests fonksiyonunu güncelleyelim
def show_accepted_requests():
    conn = init_db()
    try:
        # Sadece analiz raporu olmayan kabul edilmiş talepleri getir
        df = pd.read_sql_query("""
            SELECT * FROM numune_talepler 
            WHERE durum='Kabul' 
            AND (analiz_raporu IS NULL OR analiz_raporu = '')
            ORDER BY olusturma_tarihi DESC
        """, conn)
        
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"🧪 {row['talep_no']} - {row['numune_adi']} ({row['firma']})"):
                    # Mevcut bilgiler
                    st.markdown("#### 📋 Talep Bilgileri")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"*Firma:* {row['firma']}")
                        st.write(f"*Analiz Türü:* {row['analiz_turleri']}")
                        st.write(f"*Miktar:* {row['miktar']}")
                    with col2:
                        st.write(f"*Tahribat:* {row['tahribat']}")
                        st.write(f"*İade:* {row['iade']}")
                        st.write(f"*Termin:* {row['termin_tarihi']}")
                    
                    # Analiz formu
                    st.markdown("#### 🔬 Analiz Detayları")
                    with st.form(f"analiz_form_{row['talep_no']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            test_tekrar = st.number_input(
                                "Test Tekrar Sayısı",
                                min_value=1,
                                value=int(row['test_tekrar_sayisi']) if row['test_tekrar_sayisi'] else 1
                            )
                            
                            cihaz_adi = st.text_input(
                                "Cihaz Adı ve Kodu",
                                value=row['cihaz_adi_kodu'] if row['cihaz_adi_kodu'] else ""
                            )
                            
                            analist = st.text_input(
                                "Analist Personel",
                                value=row['analist_personel'] if row['analist_personel'] else ""
                            )
                        
                        with col2:
                            raporlayan = st.text_input(
                                "Raporlayan Personel",
                                value=row['raporlayan_personel'] if row['raporlayan_personel'] else ""
                            )
                            
                            teslim_alan = st.text_input(
                                "Teslim Alan Personel",
                                value=row['teslim_alan_personel'] if row['teslim_alan_personel'] else ""
                            )
                        
                        uygulanan_testler = st.text_area(
                            "Uygulanan Testler",
                            value=row['uygulanan_testler'] if row['uygulanan_testler'] else ""
                        )
                        
                        analiz_raporu = st.file_uploader(
                            "Analiz Raporu (PDF/DOC)",
                            type=['pdf', 'doc', 'docx']
                        )
                        
                        if st.form_submit_button("💾 Analiz Detaylarını Kaydet"):
                            try:
                                analiz_raporu_data = analiz_raporu.read() if analiz_raporu else None
                                
                                c = conn.cursor()
                                c.execute("""
                                    UPDATE numune_talepler 
                                    SET test_tekrar_sayisi=?,
                                        cihaz_adi_kodu=?,
                                        analist_personel=?,
                                        raporlayan_personel=?,
                                        teslim_alan_personel=?,
                                        uygulanan_testler=?,
                                        analiz_raporu=?,
                                        analiz_tarihi=CURRENT_DATE,
                                        durum='Tamamlandı'
                                    WHERE talep_no=?
                                """, (
                                    test_tekrar,
                                    cihaz_adi,
                                    analist,
                                    raporlayan,
                                    teslim_alan,
                                    uygulanan_testler,
                                    analiz_raporu_data,
                                    row['talep_no']
                                ))
                                
                                conn.commit()
                                st.success("✅ Analiz detayları başarıyla kaydedildi ve müşteriye iletildi!")
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Kayıt hatası: {str(e)}")
        else:
            st.info("📝 Analiz bekleyen numune bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_lab_analysis():
    st.title("📊 Numune Analiz Sonuçları")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # Bekleyen talepleri getir - sütun isimlerini açıkça belirtelim
        cur.execute("""
            SELECT 
                talep_no,
                numune_adi,
                firma,
                analiz_turu,
                miktar,
                talep_eden_adsoyad,
                talep_eden_gorev,
                talep_eden_telefon,
                talep_eden_email,
                saklama_kosullari,
                termin_tarihi,
                durum
            FROM numune_talepler 
            WHERE durum IN ('İnceleniyor', 'Numune Bekleniyor')
            ORDER BY olusturma_tarihi DESC
        """)
        
        talepler = cur.fetchall()
        
        if talepler:
            for talep in talepler:
                with st.expander(f"{talep[0]} - {talep[1]} ({talep[2]})"):
                    # Talep bilgileri
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Talep Bilgileri**")
                        st.write(f"**Talep No:** {talep[0]}")
                        st.write(f"**Numune Adı:** {talep[1]}")
                        st.write(f"**Firma:** {talep[2]}")
                        st.write(f"**Analiz Türü:** {talep[3]}")
                        st.write(f"**Miktar:** {talep[4]}")
                        
                        if talep[9]:  # saklama_kosullari
                            st.write(f"**Saklama Koşulları:** {talep[9]}")
                    
                    with col2:
                        st.write("**İletişim Bilgileri**")
                        st.write(f"**Ad Soyad:** {talep[5]}")  # talep_eden_adsoyad
                        st.write(f"**Görev:** {talep[6]}")     # talep_eden_gorev
                        st.write(f"**Telefon:** {talep[7]}")    # talep_eden_telefon
                        st.write(f"**E-posta:** {talep[8]}")    # talep_eden_email
                    
                    # Analiz sonuç formu
                    with st.form(f"analiz_form_{talep[0]}"):
                        st.markdown("### 📝 Analiz Sonuçları")
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            test_tekrar = st.number_input(
                                "Test Tekrar Sayısı*", 
                                min_value=1, 
                                value=1,
                                key=f"tekrar_{talep[0]}"
                            )
                            
                            kullanilan_cihaz = st.selectbox(
                                "Kullanılan Cihaz*",
                                ["MFI Cihazı", "TGA Cihazı", "LOI Cihazı", "FTIR Cihazı", "Sertlik Cihazı"],
                                key=f"cihaz_{talep[0]}"
                            )
                            
                            analist = st.text_input(
                                "Analist Ad Soyad*",
                                key=f"analist_{talep[0]}"
                            )
                            
                            analiz_tarihi = st.date_input(
                                "Analiz Tarihi*",
                                key=f"tarih_{talep[0]}"
                            )
                        
                        with col4:
                            analiz_sonucu = st.text_area(
                                "Analiz Sonucu*",
                                height=100,
                                key=f"sonuc_{talep[0]}"
                            )
                            
                            analiz_aciklama = st.text_area(
                                "Analiz Açıklaması",
                                height=100,
                                key=f"aciklama_{talep[0]}"
                            )
                            
                            sonuc_onaylayan = st.text_input(
                                "Sonucu Onaylayan*",
                                key=f"onaylayan_{talep[0]}"
                            )
                        
                        # Rapor yükleme
                        analiz_raporu = st.file_uploader(
                            "Analiz Raporu*",
                            type=['pdf', 'xlsx'],
                            key=f"rapor_{talep[0]}"
                        )
                        
                        submitted = st.form_submit_button("💾 Sonuçları Kaydet")
                        
                        if submitted:
                            if not all([analist, analiz_sonucu, sonuc_onaylayan, analiz_raporu]):
                                st.error("Lütfen zorunlu alanları doldurunuz!")
                                return
                            
                            try:
                                # Rapor dosyasını binary formata çevir
                                rapor_data = analiz_raporu.read() if analiz_raporu else None
                                
                                # Veritabanını güncelle
                                cur.execute("""
                                    UPDATE numune_talepler 
                                    SET durum = 'Tamamlandı',
                                        test_tekrar = ?,
                                        kullanilan_cihaz = ?,
                                        analist_adsoyad = ?,
                                        analiz_tarihi = ?,
                                        analiz_sonucu = ?,
                                        analiz_raporu = ?,
                                        analiz_aciklama = ?,
                                        sonuc_onaylayan = ?
                                    WHERE talep_no = ?
                                """, (
                                    test_tekrar,
                                    kullanilan_cihaz,
                                    analist,
                                    analiz_tarihi,
                                    analiz_sonucu,
                                    rapor_data,
                                    analiz_aciklama,
                                    sonuc_onaylayan,
                                    talep[0]
                                ))
                                
                                conn.commit()
                                st.success("""
                                ✅ Analiz sonuçları başarıyla kaydedildi!
                                
                                Talep sahibi, talep numarası ile sonuçları görüntüleyebilir.
                                """)
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Kayıt hatası: {str(e)}")
        else:
            st.info("📝 Bekleyen analiz talebi bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_stock_list(KATEGORILER):
    st.markdown("### 📋 Stok Listesi")
    
    # Filtreleme seçenekleri
    col1, col2 = st.columns(2)
    with col1:
        kategori_filtre = st.selectbox("Kategori Filtresi", ["Tümü"] + KATEGORILER)
    with col2:
        arama = st.text_input("🔍 Ürün Ara")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        sorgu = "SELECT * FROM stok WHERE 1=1"
        params = []
        
        if kategori_filtre != "Tümü":
            sorgu += " AND kategori = ?"
            params.append(kategori_filtre)
        
        if arama:
            sorgu += " AND (urun_adi LIKE ? OR tedarikci LIKE ?)"
            params.extend([f"%{arama}%", f"%{arama}%"])
        
        cur.execute(sorgu, params)
        stoklar = cur.fetchall()
        
        if stoklar:
            for stok in stoklar:
                with st.expander(f"{stok[1]} - {stok[4]} {stok[3]} {stok[2]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Kategori:** {stok[2]}")
                        st.write(f"**Miktar:** {stok[3]} {stok[4]}")
                        st.write(f"**Minimum Miktar:** {stok[5] or 'Belirtilmemiş'}")
                    with col2:
                        st.write(f"**Tedarikçi:** {stok[8] or 'Belirtilmemiş'}")
                        st.write(f"**Lot No:** {stok[10] or 'Belirtilmemiş'}")
                        st.write(f"**Son Güncelleme:** {stok[6]}")
                    
                    if stok[7]:  # Açıklama
                        st.info(stok[7])
                    
                    if stok[5] and stok[3] <= stok[5]:
                        st.warning("⚠️ Stok minimum seviyenin altında!")
        else:
            st.info("📦 Stok bulunamadı.")
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_stock_movement(KATEGORILER, BIRIMLER):
    st.markdown("### 📦 Stok Giriş / Çıkış")
    
    # Veritabanı bağlantısı
    conn = init_db()
    cur = conn.cursor()
    
    # Önce stok listesini kontrol et
    cur.execute("SELECT COUNT(*) FROM stok")
    stok_sayisi = cur.fetchone()[0]
    
    if stok_sayisi == 0:
        st.warning("⚠️ Henüz stok kaydı bulunmuyor. Önce stok ekleyin!")
        if conn:
            conn.close()
        return
    
    with st.form("stok_hareket_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Stok seçimi - Birim bilgisiyle birlikte
            cur.execute("""
                SELECT id, urun_adi, birim, miktar 
                FROM stok 
                ORDER BY urun_adi
            """)
            stoklar = cur.fetchall()
            stok_secenekleri = {
                f"{stok[1]} ({stok[2]}) - Mevcut: {stok[3]} {stok[2]}": stok[0] 
                for stok in stoklar
            }
            
            secilen_stok = st.selectbox(
                "Ürün Seçin*",
                options=list(stok_secenekleri.keys())
            )
            
            hareket_tipi = st.selectbox(
                "Hareket Tipi*",
                ["Giriş", "Çıkış"]
            )
            
            miktar = st.number_input("Miktar*", min_value=0.0, step=0.1)
            
            # Hareket tipine göre dinamik tarih alanı
            if hareket_tipi == "Giriş":
                tarih = st.date_input("Stok Giriş Tarihi")
            else:
                tarih = st.date_input("Stok Çıkış Tarihi")
        
        with col2:
            kullanici = st.text_input("İşlemi Yapan*")
            aciklama = st.text_area("Açıklama")
        
        submitted = st.form_submit_button("Kaydet")
        
        if submitted:
            if not all([secilen_stok, miktar, kullanici]):
                st.error("Lütfen zorunlu alanları doldurun!")
            else:
                try:
                    stok_id = stok_secenekleri[secilen_stok]
                    
                    # Stok hareketi ekle
                    cur.execute("""
                        INSERT INTO stok_hareket 
                        (stok_id, hareket_tipi, miktar, tarih, aciklama, kullanici)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (stok_id, hareket_tipi, miktar, tarih, aciklama, kullanici))
                    
                    # Stok miktarını güncelle
                    if hareket_tipi == "Giriş":
                        cur.execute("""
                            UPDATE stok 
                            SET miktar = miktar + ?,
                                son_guncelleme = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (miktar, stok_id))
                    else:
                        # Çıkış için stok kontrolü
                        cur.execute("SELECT miktar FROM stok WHERE id = ?", (stok_id,))
                        mevcut_miktar = cur.fetchone()[0]
                        
                        if mevcut_miktar < miktar:
                            st.error(f"⚠️ Yetersiz stok! Mevcut stok: {mevcut_miktar}")
                            return
                        
                        cur.execute("""
                            UPDATE stok 
                            SET miktar = miktar - ?,
                                son_guncelleme = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (miktar, stok_id))
                    
                    conn.commit()
                    st.success("✅ Stok hareketi başarıyla kaydedildi!")
                    st.rerun()
                    
                    # Minimum stok kontrolü
                    cur.execute("""
                        SELECT urun_adi, miktar, minimum_miktar 
                        FROM stok 
                        WHERE id = ? AND minimum_miktar IS NOT NULL
                    """, (stok_id,))
                    
                    stok_bilgi = cur.fetchone()
                    if stok_bilgi and stok_bilgi[1] <= stok_bilgi[2]:
                        st.warning(f"⚠️ {stok_bilgi[0]} için stok seviyesi minimum değerin altına düştü!")
                    
                except Exception as e:
                    st.error(f"Kayıt hatası: {str(e)}")
                finally:
                    if conn:
                        conn.close()

def show_stock_history():
    st.markdown("### 📊 Stok Hareketleri")
    
    col1, col2 = st.columns(2)
    with col1:
        baslangic = st.date_input(
            "Başlangıç Tarihi", 
            value=datetime.date.today() - datetime.timedelta(days=30),
            key="stok_hareket_baslangic"  # Benzersiz key
        )
    with col2:
        bitis = st.date_input(
            "Bitiş Tarihi", 
            value=datetime.date.today(),
            key="stok_hareket_bitis"  # Benzersiz key
        )
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT sh.*, s.urun_adi, s.kategori, s.birim
            FROM stok_hareket sh
            JOIN stok s ON sh.stok_id = s.id
            WHERE DATE(sh.tarih) BETWEEN ? AND ?
            ORDER BY sh.tarih DESC
        """, (baslangic, bitis))
        
        hareketler = cur.fetchall()
        
        if hareketler:
            for hareket in hareketler:
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**{hareket[10]} ({hareket[11]})**")
                        st.write(f"**{hareket[2]}:** {hareket[3]} {hareket[12]}")
                    with col2:
                        st.write(f"**Tarih:** {hareket[4]}")
                        st.write(f"**Kullanıcı:** {hareket[6]}")
                    
                    if hareket[5]:  # Açıklama
                        st.info(hareket[5])
                    st.markdown("---")
        else:
            st.info("📝 Seçili kriterlere uygun stok hareketi bulunmuyor.")
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_cabinet_layout(BIRIMLER):
    st.markdown("### 🗄️ Laboratuvar Dolap Düzeni")
    
    # Sekme seçimi
    tab1, tab2 = st.tabs(["🗄️ Laboratuvar Dolapları", "⏳ Numune Bekleme Alanı"])
    
    with tab1:
        # Normal dolap düzeni
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="cabinet-container">', unsafe_allow_html=True)
            for dolap_no in range(1, 33):
                conn = init_db()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM dolap_icerik WHERE dolap_no = ? AND dolap_tipi = 'lab'", (dolap_no,))
                malzeme_sayisi = cur.fetchone()[0]
                conn.close()
                
                # İkon ve stil belirleme
                icon = "📦" if malzeme_sayisi > 0 else "🔓"
                
                if st.button(
                    f"{icon} Dolap {dolap_no}",
                    key=f"dolap_{dolap_no}",
                    help="Dolap içeriğini görüntüle",
                    use_container_width=True  # use_column_width yerine use_container_width
                ):
                    st.session_state.selected_cabinet = dolap_no
                    st.session_state.selected_type = "lab"
                    st.rerun()
    
    with tab2:
        # Numune bekleme alanı
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="cabinet-container">', unsafe_allow_html=True)
            for bolme_no in range(1, 13):
                conn = init_db()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM dolap_icerik WHERE dolap_no = ? AND dolap_tipi = 'numune'", (bolme_no,))
                numune_sayisi = cur.fetchone()[0]
                conn.close()
                
                # İkon ve stil belirleme
                icon = "🧪" if numune_sayisi > 0 else "🔓"
                
                if st.button(
                    f"{icon} Bölme {bolme_no}",
                    key=f"numune_{bolme_no}",
                    help="Numune bölmesi içeriğini görüntüle",
                    use_container_width=True  # use_column_width yerine use_container_width
                ):
                    st.session_state.selected_cabinet = bolme_no
                    st.session_state.selected_type = "numune"
                    st.rerun()
    
    # Sağ panel - İçerik görüntüleme
    with col2:
        if 'selected_cabinet' in st.session_state:
            dolap_no = st.session_state.selected_cabinet
            dolap_tipi = st.session_state.get('selected_type', 'lab')
            
            baslik = "📦 Dolap" if dolap_tipi == "lab" else "🧪 Numune Bölmesi"
            st.markdown(f"### {baslik} {dolap_no} İçeriği")
            
            # Yeni malzeme ekleme formu
            with st.form(f"dolap_form_{dolap_no}_{dolap_tipi}"):
                if dolap_tipi == "lab":
                    malzeme_adi = st.text_input("Malzeme Adı*")
                else:
                    malzeme_adi = st.text_input("Numune Adı/Kodu*")
                
                col1, col2 = st.columns(2)
                with col1:
                    miktar = st.number_input("Miktar*", min_value=0.0, step=0.1)
                with col2:
                    birim = st.selectbox("Birim*", BIRIMLER)
                
                aciklama = st.text_area("Açıklama")
                
                submitted = st.form_submit_button("Ekle")
                if submitted:
                    if not all([malzeme_adi, miktar]):
                        st.error("Lütfen zorunlu alanları doldurun!")
                    else:
                        try:
                            conn = init_db()
                            cur = conn.cursor()
                            cur.execute("""
                                INSERT INTO dolap_icerik 
                                (dolap_no, malzeme_adi, miktar, birim, aciklama, dolap_tipi)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (dolap_no, malzeme_adi, miktar, birim, aciklama, dolap_tipi))
                            conn.commit()
                            st.success("✅ Başarıyla eklendi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {str(e)}")
                        finally:
                            if conn:
                                conn.close()

def show_stock_management(KATEGORILER, BIRIMLER):
    st.markdown("### 📦 Stok Yönetimi")
    
    # Alt sekmeler
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Stok Ekle",
        "🔄 Stok Giriş/Çıkış",
        "📋 Stok Geçmişi",
        "🗄️ Dolap Düzeni"
    ])
    
    with tab1:
        show_add_stock(KATEGORILER, BIRIMLER)
    with tab2:
        show_stock_movement(KATEGORILER, BIRIMLER)
    with tab3:
        show_stock_history()
    with tab4:
        show_cabinet_layout(BIRIMLER)

def show_add_stock(KATEGORILER, BIRIMLER):
    st.markdown("#### 📥 Yeni Stok Ekle")
    
    with st.form("stok_ekle_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            urun_adi = st.text_input("Ürün Adı*")
            kategori = st.selectbox("Kategori*", KATEGORILER)
            miktar = st.number_input("Başlangıç Miktarı*", min_value=0.0, step=0.1)
            birim = st.selectbox("Birim*", BIRIMLER)
            minimum_miktar = st.number_input("Minimum Stok Miktarı", min_value=0.0, step=0.1)
        
        with col2:
            tedarikci = st.text_input("Tedarikçi")
            lot_no = st.text_input("Lot No")
            sertifika_no = st.text_input("Sertifika No")
            raf_omru = st.date_input("Raf Ömrü", min_value=datetime.date.today())
            aciklama = st.text_area("Açıklama")
        
        submitted = st.form_submit_button("Stok Ekle")
        
        if submitted:
            if not all([urun_adi, kategori, miktar, birim]):
                st.error("Lütfen zorunlu alanları doldurun!")
            else:
                try:
                    conn = init_db()
                    cur = conn.cursor()
                    
                    # Stok ekle
                    cur.execute("""
                        INSERT INTO stok 
                        (urun_adi, kategori, miktar, birim, minimum_miktar,
                         tedarikci, lot_no, sertifika_no, raf_omru, aciklama)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (urun_adi, kategori, miktar, birim, minimum_miktar,
                          tedarikci, lot_no, sertifika_no, raf_omru, aciklama))
                    
                    conn.commit()
                    st.success("✅ Stok başarıyla eklendi!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Kayıt hatası: {str(e)}")
                finally:
                    if conn:
                        conn.close()

def show_training_materials():
    st.markdown("### 📚 Eğitim Materyalleri")
    
    # Veritabanı tablosu oluşturma
    conn = init_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS egitim_materyalleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT NOT NULL,
            tip TEXT NOT NULL,  -- 'video' veya 'sunum'
            link TEXT NOT NULL,
            aciklama TEXT,
            kategori TEXT,
            eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Materyal ekleme formu
    with st.expander("➕ Yeni Eğitim Materyali Ekle"):
        with st.form("materyal_form"):
            baslik = st.text_input("Başlık*")
            tip = st.selectbox("Materyal Tipi*", ["Video", "Sunum"])
            link = st.text_input("Link*")
            kategori = st.selectbox("Kategori", [
                "Cihaz Kullanımı",
                "Metot Validasyonu",
                "Kalite Kontrol",
                "Güvenlik",
                "Prosedürler",
                "Diğer"
            ])
            aciklama = st.text_area("Açıklama")
            
            submitted = st.form_submit_button("Ekle")
            if submitted:
                if not all([baslik, link]):
                    st.error("Lütfen zorunlu alanları doldurun!")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO egitim_materyalleri 
                            (baslik, tip, link, kategori, aciklama)
                            VALUES (?, ?, ?, ?, ?)
                        """, (baslik, tip, link, kategori, aciklama))
                        conn.commit()
                        st.success("✅ Materyal başarıyla eklendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Kayıt hatası: {str(e)}")

    # Materyal filtreleme
    col1, col2 = st.columns(2)
    with col1:
        filtre_tip = st.multiselect("Materyal Tipi", ["Video", "Sunum"], default=["Video", "Sunum"])
    with col2:
        filtre_kategori = st.selectbox("Kategori", ["Tümü"] + [
            "Cihaz Kullanımı",
            "Metot Validasyonu",
            "Kalite Kontrol",
            "Güvenlik",
            "Prosedürler",
            "Diğer"
        ])

    # Materyalleri listele
    try:
        sorgu = "SELECT * FROM egitim_materyalleri WHERE tip IN (%s)" % ','.join('?' * len(filtre_tip))
        params = filtre_tip.copy()
        
        if filtre_kategori != "Tümü":
            sorgu += " AND kategori = ?"
            params.append(filtre_kategori)
            
        sorgu += " ORDER BY eklenme_tarihi DESC"
        
        cur.execute(sorgu, params)
        materyaller = cur.fetchall()
        
        if materyaller:
            for materyal in materyaller:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {materyal[1]}")
                        if materyal[2] == "Video":
                            st.video(materyal[3])
                        else:
                            st.markdown(f"[🔗 Sunumu Görüntüle]({materyal[3]})")
                        
                        if materyal[4]:  # açıklama
                            st.info(materyal[4])
                            
                        st.caption(f"Kategori: {materyal[5]} | Eklenme: {materyal[6]}")
                    
                    with col2:
                        if st.button("🗑️", key=f"sil_materyal_{materyal[0]}"):
                            cur.execute("DELETE FROM egitim_materyalleri WHERE id = ?", (materyal[0],))
                            conn.commit()
                            st.success("Materyal silindi!")
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("📭 Henüz materyal eklenmemiş.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_library():
    st.markdown("### 📚 Kütüphane")
    
    # Alt sekmeler
    lib_tab1, lib_tab2 = st.tabs([
        "📖 Dokümanlar",
        "🎓 Eğitim Materyalleri"
    ])
    
    # Dokümanlar sekmesi
    with lib_tab1:
        show_documents()  # Mevcut doküman yönetimi fonksiyonu
    
    # Eğitim Materyalleri sekmesi
    with lib_tab2:
        show_training_materials()

def show_documents():
    st.markdown("#### 📖 Dokümanlar")
    
    # Veritabanı tablosu oluşturma
    conn = init_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dokumanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT NOT NULL,
            dosya_tipi TEXT NOT NULL,
            link TEXT NOT NULL,
            aciklama TEXT,
            kategori TEXT,
            eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Doküman ekleme formu
    with st.expander("➕ Yeni Doküman Ekle"):
        with st.form("dokuman_form"):
            baslik = st.text_input("Başlık*")
            dosya_tipi = st.selectbox("Doküman Tipi*", [
                "SOP (Standart Operasyon Prosedürü)",
                "Metot",
                "Form",
                "Rapor Şablonu",
                "Kalite Dokümanı",
                "Diğer"
            ])
            link = st.text_input("Doküman Linki*")
            kategori = st.selectbox("Kategori", [
                "Analiz Metotları",
                "Kalite Kontrol",
                "Güvenlik",
                "Cihaz Kullanımı",
                "Raporlama",
                "Diğer"
            ])
            aciklama = st.text_area("Açıklama")
            
            submitted = st.form_submit_button("Ekle")
            if submitted:
                if not all([baslik, link]):
                    st.error("Lütfen zorunlu alanları doldurun!")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO dokumanlar 
                            (baslik, dosya_tipi, link, kategori, aciklama)
                            VALUES (?, ?, ?, ?, ?)
                        """, (baslik, dosya_tipi, link, kategori, aciklama))
                        conn.commit()
                        st.success("✅ Doküman başarıyla eklendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Kayıt hatası: {str(e)}")

    # Doküman filtreleme
    col1, col2 = st.columns(2)
    with col1:
        filtre_tip = st.multiselect(
            "Doküman Tipi",
            ["SOP", "Metot", "Form", "Rapor Şablonu", "Kalite Dokümanı", "Diğer"],
            default=["SOP", "Metot", "Form", "Rapor Şablonu", "Kalite Dokümanı", "Diğer"]
        )
    with col2:
        filtre_kategori = st.selectbox("Kategori", ["Tümü"] + [
            "Analiz Metotları",
            "Kalite Kontrol",
            "Güvenlik",
            "Cihaz Kullanımı",
            "Raporlama",
            "Diğer"
        ])

    # Dokümanları listele
    try:
        sorgu = "SELECT * FROM dokumanlar WHERE dosya_tipi IN (%s)" % ','.join('?' * len(filtre_tip))
        params = filtre_tip.copy()
        
        if filtre_kategori != "Tümü":
            sorgu += " AND kategori = ?"
            params.append(filtre_kategori)
            
        sorgu += " ORDER BY eklenme_tarihi DESC"
        
        cur.execute(sorgu, params)
        dokumanlar = cur.fetchall()
        
        if dokumanlar:
            for dokuman in dokumanlar:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {dokuman[1]}")
                        st.markdown(f"**Tip:** {dokuman[2]}")
                        st.markdown(f"[🔗 Dokümanı Görüntüle]({dokuman[3]})")
                        
                        if dokuman[4]:  # açıklama
                            st.info(dokuman[4])
                            
                        st.caption(f"Kategori: {dokuman[5]} | Eklenme: {dokuman[6]}")
                    
                    with col2:
                        if st.button("🗑️", key=f"sil_dokuman_{dokuman[0]}"):
                            cur.execute("DELETE FROM dokumanlar WHERE id = ?", (dokuman[0],))
                            conn.commit()
                            st.success("Doküman silindi!")
                            st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("📚 Henüz doküman eklenmemiş.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_analysis_request_form():
    st.markdown("### 🧪 Numune Analiz Talebi")
    
    with st.form("analiz_talebi"):
        col1, col2 = st.columns(2)
        
        with col1:
            firma_adi = st.text_input("Firma Adı*")
            yetkili_kisi = st.text_input("Yetkili Kişi*")
            email = st.text_input("E-posta*")
            telefon = st.text_input("Telefon*")
            
        with col2:
            numune_adi = st.text_input("Numune Adı/Kodu*")
            numune_adedi = st.number_input("Numune Adedi*", min_value=1, value=1)
            # Analiz türü seçimi güncellendi
            analiz_turu = st.selectbox("Analiz Türü*", [
                "MFI (Erime Akış İndeksi)",
                "TGA (Termogravimetrik Analiz)",
                "LOI (Limit Oksijen İndeksi)",
                "FTIR (Fourier Dönüşümlü Kızılötesi Spektroskopisi)",
                "SERTLİK",
                "Diğer"
            ])
            
            if analiz_turu == "Diğer":
                diger_analiz = st.text_input("Diğer Analiz Türü Açıklaması")
                analiz_turu = f"Diğer: {diger_analiz}" if diger_analiz else "Diğer"
            
            numune_turu = st.text_input("Numune Türü*")
        
        aciklama = st.text_area("Ek Açıklamalar")
        
        submitted = st.form_submit_button("Talep Gönder")
        
        if submitted:
            if not all([firma_adi, yetkili_kisi, email, telefon, numune_adi, numune_turu, analiz_turu]):
                st.error("Lütfen zorunlu alanları doldurun!")
            else:
                try:
                    conn = init_db()
                    cur = conn.cursor()
                    
                    # Talep numarası oluştur
                    talep_no = generate_talep_no()
                    if not talep_no:
                        st.error("Talep numarası oluşturulamadı!")
                        return
                    
                    cur.execute("""
                        INSERT INTO numune_talepler 
                        (talep_no, numune_adi, firma, analiz_turu, miktar,
                         talep_eden_adsoyad, talep_eden_telefon, talep_eden_email,
                         analiz_turleri, aciklama, kimyasal_risk)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (talep_no, numune_adi, firma_adi, analiz_turu, str(numune_adedi),
                          yetkili_kisi, telefon, email, analiz_turu, saklama_kosullari,
                          termin_tarihi, tds_dosya_data, talep_eden_adsoyad,
                          talep_eden_gorev, talep_eden_telefon, talep_eden_email,
                          analiz_turu, aciklama, kimyasal_risk))
                    
                    conn.commit()
                    st.success("✅ Analiz talebiniz başarıyla gönderildi!")
                    
                except Exception as e:
                    st.error(f"Kayıt hatası: {str(e)}")
                finally:
                    if conn:
                        conn.close()

def show_sample_evaluation():
    st.markdown("### 📋 Numune Değerlendirme")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # Bekleyen talepleri getir
        cur.execute("""
            SELECT 
                talep_no,
                numune_adi,
                firma,
                analiz_turu,
                tahribat,
                iade,
                numune_gorseli,
                miktar,
                saklama_kosullari,
                termin_tarihi,
                tds_dosya,
                durum,
                red_nedeni,
                red_gorseli,
                olusturma_tarihi,
                talep_eden_adsoyad,
                talep_eden_gorev,
                talep_eden_telefon,
                talep_eden_email,
                analiz_turleri,
                aciklama
            FROM numune_talepler 
            WHERE durum = 'Beklemede'
            ORDER BY olusturma_tarihi DESC
        """)
        
        talepler = cur.fetchall()
        
        if talepler:
            for talep in talepler:
                with st.expander(f"📦 {talep[0]} - {talep[1]}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📝 Talep Bilgileri")
                        st.write(f"**Talep No:** {talep[0]}")
                        st.write(f"**Firma:** {talep[2]}")
                        st.write(f"**Numune Adı:** {talep[1]}")
                        st.write(f"**Analiz Türü:** {talep[3]}")
                        st.write(f"**Miktar:** {talep[7]}")
                        
                        if talep[6]:  # numune görseli
                            st.markdown("#### 📷 Numune Görseli")
                            st.image(talep[6], use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 👤 İletişim Bilgileri")
                        st.write(f"**Talep Eden:** {talep[15] or 'Belirtilmemiş'}")
                        st.write(f"**Görevi:** {talep[16] or 'Belirtilmemiş'}")
                        st.write(f"**Telefon:** {talep[17] or 'Belirtilmemiş'}")
                        st.write(f"**E-posta:** {talep[18] or 'Belirtilmemiş'}")
                    
                    # Değerlendirme butonları
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Kabul Et", key=f"kabul_{talep[0]}"):
                            cur.execute("""
                                UPDATE numune_talepler 
                                SET durum = 'Kabul Edildi'
                                WHERE talep_no = ?
                            """, (talep[0],))
                            conn.commit()
                            st.success("✅ Numune kabul edildi!")
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Reddet", key=f"red_{talep[0]}"):
                            red_nedeni = st.text_area("Red Nedeni", key=f"red_nedeni_{talep[0]}")
                            if red_nedeni:
                                cur.execute("""
                                    UPDATE numune_talepler 
                                    SET durum = 'Reddedildi',
                                        red_nedeni = ?,
                                        red_gorseli = ?,
                                        aciklama = ?
                                    WHERE talep_no = ?
                                """, (red_nedeni, talep[7], saklama_kosullari, talep[0]))
                                conn.commit()
                                st.error("❌ Numune reddedildi!")
                                st.rerun()
        else:
            st.info("📭 Bekleyen numune talebi bulunmuyor.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
        st.error(f"Hata detayı: {traceback.format_exc()}")
    finally:
        if conn:
            conn.close()

def show_analysis_management():
    st.title("📊 Analiz Yönetimi")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # Durum filtreleme
        durumlar = ["Hepsi", "Beklemede", "İnceleniyor", "Tamamlandı", "Red"]
        secili_durum = st.selectbox("Durum Filtresi", durumlar)
        
        # Talepleri getir
        cur.execute("""
            SELECT * FROM numune_talepler 
            ORDER BY olusturma_tarihi DESC
        """)
        talepler = cur.fetchall()
        
        if talepler:
            for talep in talepler:
                if secili_durum == "Hepsi" or talep[16] == secili_durum:  # durum indeksi
                    with st.expander(f"{talep[0]} - {talep[1]} ({talep[2]})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Talep Bilgileri**")
                            st.write(f"- Talep No: {talep[0]}")
                            st.write(f"- Oluşturma Tarihi: {talep[15]}")  # olusturma_tarihi
                            st.write(f"- Termin Tarihi: {talep[10]}")  # termin_tarihi
                            st.write(f"- Durum: {talep[16]}")  # durum
                            
                            st.write("\n**Numune Bilgileri**")
                            st.write(f"- Numune Adı: {talep[1]}")
                            st.write(f"- Firma: {talep[2]}")
                            st.write(f"- Analiz Türü: {talep[3]}")
                            st.write(f"- Miktar: {talep[4]}")
                            
                            if talep[9]:  # saklama_kosullari
                                st.write(f"- Saklama Koşulları: {talep[9]}")
                            if talep[14]:  # kimyasal_risk
                                st.write(f"- Kimyasal Risk: {talep[14]}")
                        
                        with col2:
                            st.write("**İletişim Bilgileri**")
                            st.write(f"- Ad Soyad: {talep[5]}")  # talep_eden_adsoyad
                            st.write(f"- Görev: {talep[6]}")  # talep_eden_gorev
                            st.write(f"- Telefon: {talep[7]}")  # talep_eden_telefon
                            st.write(f"- E-posta: {talep[8]}")  # talep_eden_email
                            
                            if talep[13]:  # aciklama
                                st.write("\n**Açıklama**")
                                st.info(talep[13])
                        
                        # Durum güncelleme formu
                        with st.form(f"durum_form_{talep[0]}"):
                            st.write("### Durum Güncelleme")
                            yeni_durum = st.selectbox(
                                "Yeni Durum",
                                ["Beklemede", "İnceleniyor", "Tamamlandı", "Red"],
                                key=f"durum_{talep[0]}"
                            )
                            
                            if yeni_durum == "Tamamlandı":
                                test_sayisi = st.number_input("Test Tekrar Sayısı", min_value=1)
                                cihaz = st.text_input("Kullanılan Cihaz")
                                analist = st.text_input("Analist")
                                analiz_tarihi = st.date_input("Analiz Tarihi")
                                sonuc = st.text_area("Analiz Sonucu")
                                aciklama = st.text_area("Açıklama")
                                onaylayan = st.text_input("Onaylayan")
                                rapor = st.file_uploader("Analiz Raporu", type=['pdf'])
                                
                            elif yeni_durum == "Red":
                                red_nedeni = st.text_area("Red Nedeni")
                                red_gorseli = st.file_uploader("Red Görseli", type=['png', 'jpg', 'jpeg'])
                            
                            if st.form_submit_button("Güncelle"):
                                try:
                                    if yeni_durum == "Tamamlandı":
                                        if not (cihaz and analist and sonuc and onaylayan):
                                            st.error("Lütfen tüm alanları doldurun!")
                                            continue
                                            
                                        cur.execute("""
                                            UPDATE numune_talepler
                                            SET durum = ?,
                                                test_sayisi = ?,
                                                cihaz = ?,
                                                analist = ?,
                                                analiz_tarihi = ?,
                                                sonuc = ?,
                                                aciklama = ?,
                                                onaylayan = ?,
                                                rapor = ?
                                            WHERE talep_no = ?
                                        """, (yeni_durum, test_sayisi, cihaz, analist, 
                                             analiz_tarihi, sonuc, aciklama, onaylayan,
                                             rapor.read() if rapor else None, talep[0]))
                                        
                                    elif yeni_durum == "Red":
                                        if not red_nedeni:
                                            st.error("Lütfen red nedenini belirtin!")
                                            continue
                                            
                                        cur.execute("""
                                            UPDATE numune_talepler
                                            SET durum = ?,
                                                red_nedeni = ?,
                                                red_gorseli = ?
                                            WHERE talep_no = ?
                                        """, (yeni_durum, red_nedeni,
                                             red_gorseli.read() if red_gorseli else None,
                                             talep[0]))
                                    else:
                                        cur.execute("""
                                            UPDATE numune_talepler
                                            SET durum = ?
                                            WHERE talep_no = ?
                                        """, (yeni_durum, talep[0]))
                                    
                                    conn.commit()
                                    st.success("✅ Durum güncellendi!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Güncelleme hatası: {str(e)}")
        else:
            st.info("📝 Henüz talep bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_calendar_view():
    st.title("📅 Laboratuvar Takvimi")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # Tüm talepleri getir
        cur.execute("""
            SELECT talep_no, numune_adi, firma, analiz_turu, termin_tarihi, durum 
            FROM numune_talepler 
            ORDER BY termin_tarihi
        """)
        
        talepler = cur.fetchall()
        
        if talepler:
            # Bugünün tarihi
            bugun = datetime.date.today()
            
            # Yaklaşan talepler
            st.subheader("📋 Yaklaşan Talepler")
            yaklasan_talepler = [t for t in talepler if t[4] and 
                               datetime.datetime.strptime(t[4], '%Y-%m-%d').date() >= bugun]
            
            if yaklasan_talepler:
                for talep in yaklasan_talepler:
                    with st.expander(f"{talep[0]} - {talep[1]} ({talep[2]})"):
                        st.write(f"**Analiz Türü:** {talep[3]}")
                        st.write(f"**Termin Tarihi:** {talep[4]}")
                        st.write(f"**Durum:** {talep[5]}")
                        
                        # Kalan gün hesaplama
                        termin = datetime.datetime.strptime(talep[4], '%Y-%m-%d').date()
                        kalan_gun = (termin - bugun).days
                        
                        if kalan_gun < 0:
                            st.error(f"⚠️ Termin tarihi {abs(kalan_gun)} gün geçti!")
                        elif kalan_gun == 0:
                            st.warning("⚠️ Termin tarihi bugün!")
                        elif kalan_gun <= 3:
                            st.warning(f"⚡ Son {kalan_gun} gün!")
                        else:
                            st.info(f"✅ {kalan_gun} gün kaldı")
            else:
                st.info("Yaklaşan talep bulunmamaktadır.")
            
            # Aylık görünüm
            st.subheader("📅 Aylık Görünüm")
            ay = st.selectbox(
                "Ay Seçin",
                ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            )
            
            # Seçilen aya göre talepleri filtrele
            ay_no = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"].index(ay) + 1
            
            aylik_talepler = [t for t in talepler if t[4] and 
                            datetime.datetime.strptime(t[4], '%Y-%m-%d').date().month == ay_no]
            
            if aylik_talepler:
                for talep in aylik_talepler:
                    st.write(f"- {talep[4]}: {talep[0]} - {talep[1]} ({talep[2]})")
            else:
                st.info(f"{ay} ayında planlanmış talep bulunmamaktadır.")
            
        else:
            st.info("Henüz talep bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_device_maintenance():
    st.title("🔧 Cihaz Bakım Takibi")
    
    try:
        conn = init_db()
        cur = conn.cursor()
        
        # Cihaz bakım tablosunu oluştur
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cihaz_bakim (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cihaz_adi TEXT NOT NULL,
                son_bakim_tarihi DATE,
                planlanan_bakim_tarihi DATE,
                bakim_tipi TEXT,
                bakim_yapan TEXT,
                aciklama TEXT,
                durum TEXT DEFAULT 'Beklemede',
                bakim_raporu BLOB,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Yeni bakım kaydı ekleme formu
        st.subheader("📝 Yeni Bakım Kaydı")
        with st.form("bakim_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                cihaz_adi = st.selectbox(
                    "Cihaz*",
                    ["MFI Cihazı", "TGA Cihazı", "LOI Cihazı", "FTIR Cihazı", "Sertlik Cihazı"]
                )
                son_bakim = st.date_input("Son Bakım Tarihi*")
                planlanan_bakim = st.date_input("Planlanan Bakım Tarihi*")
            
            with col2:
                bakim_tipi = st.selectbox(
                    "Bakım Tipi*",
                    ["Periyodik Bakım", "Kalibrasyon", "Arıza Bakımı", "Önleyici Bakım"]
                )
                bakim_yapan = st.text_input("Bakım Yapan*")
                durum = st.selectbox(
                    "Durum",
                    ["Beklemede", "Tamamlandı", "Ertelendi", "İptal"]
                )
            
            aciklama = st.text_area("Açıklama")
            rapor = st.file_uploader("Bakım Raporu", type=['pdf'])
            
            if st.form_submit_button("Kaydet"):
                if not all([cihaz_adi, son_bakim, planlanan_bakim, bakim_tipi, bakim_yapan]):
                    st.error("Lütfen zorunlu (*) alanları doldurun!")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO cihaz_bakim 
                            (cihaz_adi, son_bakim_tarihi, planlanan_bakim_tarihi,
                             bakim_tipi, bakim_yapan, aciklama, durum, bakim_raporu)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (cihaz_adi, son_bakim, planlanan_bakim,
                              bakim_tipi, bakim_yapan, aciklama, durum,
                              rapor.read() if rapor else None))
                        
                        conn.commit()
                        st.success("✅ Bakım kaydı oluşturuldu!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Kayıt hatası: {str(e)}")
        
        # Bakım kayıtlarını listele
        st.subheader("📋 Bakım Kayıtları")
        
        # Filtreleme seçenekleri
        col3, col4 = st.columns(2)
        with col3:
            filtre_cihaz = st.selectbox(
                "Cihaz Filtresi",
                ["Tümü", "MFI Cihazı", "TGA Cihazı", "LOI Cihazı", "FTIR Cihazı", "Sertlik Cihazı"]
            )
        with col4:
            filtre_durum = st.selectbox(
                "Durum Filtresi",
                ["Tümü", "Beklemede", "Tamamlandı", "Ertelendi", "İptal"]
            )
        
        # Kayıtları getir
        cur.execute("""
            SELECT * FROM cihaz_bakim 
            ORDER BY planlanan_bakim_tarihi DESC
        """)
        kayitlar = cur.fetchall()
        
        if kayitlar:
            for kayit in kayitlar:
                # Filtreleme kontrolü
                if (filtre_cihaz == "Tümü" or kayit[1] == filtre_cihaz) and \
                   (filtre_durum == "Tümü" or kayit[7] == filtre_durum):
                    
                    with st.expander(f"{kayit[1]} - {kayit[4]} ({kayit[2]})"):
                        col5, col6 = st.columns(2)
                        
                        with col5:
                            st.write("**Bakım Bilgileri**")
                            st.write(f"- Cihaz: {kayit[1]}")
                            st.write(f"- Son Bakım: {kayit[2]}")
                            st.write(f"- Planlanan Bakım: {kayit[3]}")
                            st.write(f"- Bakım Tipi: {kayit[4]}")
                        
                        with col6:
                            st.write("**Durum Bilgileri**")
                            st.write(f"- Bakım Yapan: {kayit[5]}")
                            st.write(f"- Durum: {kayit[7]}")
                            st.write(f"- Kayıt Tarihi: {kayit[9]}")
                        
                        if kayit[6]:  # aciklama
                            st.write("**Açıklama**")
                            st.info(kayit[6])
                        
                        if kayit[8]:  # bakim_raporu
                            st.download_button(
                                "📄 Bakım Raporunu İndir",
                                kayit[8],
                                file_name=f"Bakim_Raporu_{kayit[0]}.pdf",
                                mime="application/pdf"
                            )
        else:
            st.info("Henüz bakım kaydı bulunmamaktadır.")
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {str(e)}")
    finally:
        if conn:
            conn.close()

def show_device_management():
    st.title("🔧 Cihaz Yönetimi")
    
    # Proje kök dizinini al
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Cihaz bilgileri sözlüğü
    cihazlar = {
        "MFI Cihazı": {
            "image": "mfı.jpg",  # Doğrudan dosya adı
            "description": """
            Ergimiş Akış İndeksi (MFI) test cihazı, termoplastik malzemelerin akışkanlık özelliklerini 
            ölçmek için kullanılır. Belirli bir sıcaklık ve yük altında malzemenin akış hızını belirler.
            
            Özellikler:
            - Sıcaklık Aralığı: 0-400°C
            - Yük Aralığı: 0.325-21.6 kg
            - Test Standardı: ISO 1133, ASTM D1238
            """,
            "status": "Aktif",
            "last_maintenance": "2024-01-15",
            "next_maintenance": "2024-04-15",
            "report_path": "MFI.xlsx"
        },
        "TGA Cihazı": {
            "image": "tga.jpg",  # Doğrudan dosya adı
            "description": """
            Termogravimetrik Analiz (TGA) cihazı, malzemelerin sıcaklığa bağlı kütle değişimini ölçer. 
            Termal kararlılık, bozunma sıcaklığı ve içerik analizi için kullanılır.
            
            Özellikler:
            - Sıcaklık Aralığı: Oda sıcaklığı-1000°C
            - Hassasiyet: 0.1 μg
            - Isıtma Hızı: 0.1-100°C/dk
            """,
            "status": "Aktif",
            "last_maintenance": "2024-02-01",
            "next_maintenance": "2024-05-01",
            "report_path": "TGA.xlsx"
        }
    }
    
    try:
        # Cihazları listele
        for cihaz_adi, cihaz_bilgi in cihazlar.items():
            with st.expander(f"📊 {cihaz_adi}", expanded=True):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    try:
                        if os.path.exists(cihaz_bilgi["image"]):
                            image = Image.open(cihaz_bilgi["image"])
                            st.image(image, caption=cihaz_adi, use_container_width=True)  # use_container_width kullanıldı
                        else:
                            st.error(f"Görsel bulunamadı: {cihaz_bilgi['image']}")
                    except Exception as e:
                        st.error(f"Görsel yükleme hatası ({cihaz_adi}): {str(e)}")
                
                with col2:
                    st.markdown("#### 📝 Cihaz Bilgileri")
                    st.markdown(cihaz_bilgi["description"])
                    
                    st.markdown("#### 📊 Durum Bilgileri")
                    status_color = "🟢" if cihaz_bilgi["status"] == "Aktif" else "🔴"
                    st.write(f"**Durum:** {status_color} {cihaz_bilgi['status']}")
                    st.write(f"**Son Bakım:** {cihaz_bilgi['last_maintenance']}")
                    st.write(f"**Sonraki Bakım:** {cihaz_bilgi['next_maintenance']}")
                    
                    # Excel raporu indirme butonu
                    if "report_path" in cihaz_bilgi:
                        try:
                            if os.path.exists(cihaz_bilgi["report_path"]):
                                with open(cihaz_bilgi["report_path"], "rb") as file:
                                    excel_data = file.read()
                                    st.download_button(
                                        label=f"📊 {cihaz_adi} Raporunu İndir",
                                        data=excel_data,
                                        file_name=cihaz_bilgi["report_path"],
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            else:
                                st.error(f"Rapor dosyası bulunamadı: {cihaz_bilgi['report_path']}")
                        except Exception as e:
                            st.error(f"Rapor yükleme hatası ({cihaz_adi}): {str(e)}")
                    
                    # Bakım planla butonu
                    if st.button("🔧 Bakım Planla", key=f"bakim_{cihaz_adi}"):
                        st.session_state['selected_device'] = cihaz_adi
                        st.rerun()
    
    except Exception as e:
        st.error(f"Beklenmeyen bir hata oluştu: {str(e)}")
        st.error(traceback.format_exc())

def main():
    st.set_page_config(
        page_title="Laboratuvar Yönetim Sistemi",
        page_icon="🧪",
        layout="wide"
    )

    # Sidebar menüsü
    with st.sidebar:
        st.title("🧪 Lab Yönetim")
        selected = st.radio(
            "Menü",
            options=["Ana Sayfa", "Numune Analiz", "Stok Yönetimi", 
                    "Eğitim Materyalleri", "Ayarlar"],
            format_func=lambda x: {
                "Ana Sayfa": "🏠 Ana Sayfa",
                "Numune Analiz": "📝 Numune Analiz",
                "Stok Yönetimi": "📦 Stok Yönetimi",
                "Eğitim Materyalleri": "📚 Eğitim Materyalleri",
                "Ayarlar": "⚙️ Ayarlar"
            }[x]
        )
    
    if selected == "Ana Sayfa":
        show_homepage()
    elif selected == "Numune Analiz":
        show_sample_analysis()
    elif selected == "Stok Yönetimi":
        show_stock_management(KATEGORILER, BIRIMLER)  # Listeleri parametre olarak geç
    elif selected == "Eğitim Materyalleri":
        show_training_materials()
    elif selected == "Ayarlar":
        show_settings()

# Ana uygulama
if __name__ == "__main__":
    try:
        if not st.session_state['logged_in']:
            show_login()
        else:
            # Sayfa tipine göre stili ayarla
            set_page_style(st.session_state['user_type'])
            
            # Üst kısımda kullanıcı bilgisi ve çıkış butonu
            col1, col2, col3 = st.columns([3, 4, 1])
            with col1:
                if st.session_state.username:
                    st.write(f"👤 Kullanıcı: {st.session_state.username}")
            with col3:
                if st.button("🚪 Çıkış Yap", type="primary"):
                    # Session state'i temizle
                    st.session_state.logged_in = False
                    st.session_state.user_type = None
                    st.session_state.username = None
                    st.rerun()
            
            # Ana içerik
            if st.session_state['user_type'] == 'lab':
                st.markdown("## 🔬 Laboratuvar Yönetim Sistemi")
                
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                    "📥 Yeni Talepler", 
                    "🧪 Kabul Edilen Numuneler", 
                    "⚙️ Analiz Yönetimi",
                    "📚 Kütüphane",
                    "📊 Raporlar",
                    "📅 Takvim",
                    "🔧 Bakım",
                    "📦 Stok"
                ])
                
                with tab1:
                    show_lab_evaluation()
                with tab2:
                    show_lab_analysis()
                with tab3:
                    menu_choice = option_menu(
                        menu_title=None,
                        options=[
                            "Numune Değerlendirme",
                            "Analiz Yönetimi",
                            "Cihaz Yönetimi",
                            "Doküman Kütüphanesi",
                            "Cihaz Bakım"
                        ],
                        icons=["clipboard-check", "graph-up", "tools", "folder", "wrench"],
                        orientation="horizontal"
                    )
                    
                    if menu_choice == "Analiz Yönetimi":
                        show_analysis_management()
                    elif menu_choice == "Cihaz Yönetimi":  # Bu kısmı ekleyin
                        show_device_management()
                with tab4:
                    show_library()
                with tab5:
                    show_analytics_dashboard()
                with tab6:
                    show_calendar_view()
                with tab7:
                    show_device_maintenance()
                with tab8:
                    show_stock_management(KATEGORILER, BIRIMLER)
            
            elif st.session_state['user_type'] == 'external':
                tab1, tab2 = st.tabs(["Yeni Talep", "Talep Sorgula"])
                with tab1:
                    show_external_form()
                with tab2:
                    show_request_query()
    except Exception as e:
        st.error(f"Hata: {str(e)}")
        st.error(traceback.format_exc())

def initialize_database():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Create stok table if it doesn't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS stok (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        urun_adi TEXT NOT NULL,
        kategori TEXT,
        miktar REAL,
        birim TEXT,
        tarih DATE,
        hareket_tipi TEXT,
        aciklama TEXT
    )''')
    
    conn.commit()
    conn.close()

# Call this function when your program starts
initialize_database()

