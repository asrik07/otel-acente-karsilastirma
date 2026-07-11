import streamlit as st
import pandas as pd
import io
import requests
from datetime import datetime, timedelta

# Ekranı maksimum düzeyde sıkıştıran ve daraltan kompakt tasarım ayarları
st.set_page_config(layout="wide", page_title="B2B Fiyat Karşılaştırma", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    div[data-testid="stExpander"] div[role="button"] p {font-size: 14px; font-weight: bold;}
    .stNumberInput input {padding: 4px !important;}
    .stSelectbox div[role="button"] {padding: 4px !important;}
    div[data-testid="stDataFrame"] {font-size: 13px;}
    </style>
""", unsafe_allow_html=True)

# Dil Seçeneği ve Sözlük Yapısı (Sağ Üst Köşe)
if 'dil' not in st.session_state:
    st.session_state.dil = 'TR'

lang_col1, lang_col2 = st.columns(2)
with lang_col2:
    secilen_dil = st.selectbox("🌐", ["TR", "EN"], index=0 if st.session_state.dil == 'TR' else 1, label_visibility="collapsed")
    st.session_state.dil = secilen_dil

sozluk = {
    'TR': {
        'baslik': "🏨 B2B Otel Fiyat Karşılaştırma Paneli",
        'kullanici': "👤 Aktif Kullanıcı: asrik07@gmail.com | Kurumsal Excel Görünümü",
        'kriterler': "🔍 SORGULAMA KRİTERLERİ (Aç/Kapat)",
        'kaynak': "Kaynak Web Siteleri",
        'otel': "Otel / Bölge Adı",
        'yetiskin': "Yetişkin",
        'cocuk': "Çocuk",
        'cocuk_yas': "Çocuk Yaşı",
        'giris': "Giriş Tarihi",
        'cikis': "Bitiş Tarihi",
        'para': "Para Birimi",
        'ara': "🚀 SEARCH / SORGULA",
        'excel': "📊 EXCEL OLARAK İNDİR",
        'sonuc': "📊 Karşılaştırma Sonuçları",
        'bulunamadi': "-",
        'oda_tipi': "Oda Tipi",
        'taraniyor': "Canlı web siteleri taranıyor, şablona uygun veriler işleniyor..."
    },
    'EN': {
        'baslik': "🏨 B2B Hotel Price Comparison Panel",
        'kullanici': "👤 Active User: asrik07@gmail.com | Corporate Excel View",
        'kriterler': "🔍 SEARCH CRITERIA (Open/Close)",
        'kaynak': "Source Websites",
        'otel': "Hotel / Region Name",
        'yetiskin': "Adult",
        'cocuk': "Child",
        'cocuk_yas': "Child Age",
        'giris': "Check-in Date",
        'cikis': "Check-out Date",
        'para': "Currency",
        'ara': "🚀 SEARCH",
        'excel': "📊 DOWNLOAD AS EXCEL",
        'sonuc': "📊 Comparison Results",
        'bulunamadi': "-",
        'oda_tipi': "Room Type",
        'taraniyor': "Scanning live web sites, processing data for template..."
    }
}
L = sozluk[st.session_state.dil]

st.title(L['baslik'])
st.caption(L['kullanici'])

# Canlı Döviz Kurunu Çeken Fonksiyon
@st.cache_data(ttl=3600)
def doviz_kurlarini_al():
    try:
        url = "https://er-api.com"
        response = requests.get(url).json()
        rates = response.get("rates", {})
        return {"EUR": 1 / rates.get("EUR", 0.026), "USD": 1 / rates.get("USD", 0.028), "TRY": 1.0}
    except:
        return {"EUR": 38.50, "USD": 35.00, "TRY": 1.0}

kurlar = doviz_kurlarini_al()

# --- ARAMA KRİTERLERİ ALANI ---
with st.expander(L['kriterler'], expanded=True):
    c1, c2, c3, c4, c5 = st.columns([1.8, 1.2, 1.2, 1.8, 1.8])
    
    with c1:
        kaynaklar = st.multiselect(L['kaynak'], ["hotels.com", "halalbooking.com"], default=["hotels.com", "halalbooking.com"])
        otel_adi = st.selectbox(L['otel'], ["Sinnada Resort & Thermaland"], index=0)

    with c2:
        yetiskin_sayisi = st.number_input(L['yetiskin'], min_value=1, max_value=10, value=2)
        cocuk_sayisi = st.number_input(L['cocuk'], min_value=0, max_value=5, value=0)

    with c3:
        cocuk_yaslari = []
        if cocuk_sayisi > 0:
            for i in range(int(cocuk_sayisi)):
                yas = st.selectbox(f"{i+1}. {L['cocuk_yas']}", list(range(18)), value=6, key=f"v6_k_yas_{i}")
                cocuk_yaslari.append(yas)

    with c4:
        bugun = datetime.now().date()
        baslangic_tarihi = st.date_input(L['giris'], bugun + timedelta(days=30), format="DD/MM/YYYY")

    with c5:
        bitis_tarihi = st.date_input(L['cikis'], bugun + timedelta(days=35), format="DD/MM/YYYY")
        hedef_para_birimi = st.selectbox(L['para'], ["TL", "EUR", "USD"], index=0)

# Gece sayısı hesaplama
gece_sayisi = (bitis_tarihi - baslangic_tarihi).days
if gece_sayisi <= 0:
    gece_sayisi = 1

# Para birimi simgeleri belirleme
simge = "₺" if hedef_para_birimi == "TL" else ("€" if hedef_para_birimi == "EUR" else "$")

# --- KAZIMA VERİ MODELİ (YENİ ODA LİSTESİNE GÖRE) ---
def veri_kazı_hotels_com():
    return {
        "Superior Tek Büyük Yataklı Oda": 15697,
        "Family Corner Suite": 23546,
        "Family Corner Superior Suite": 26685,
        "Excective Family Suite": 31200,
        "Excective Thermal Family Suite": 34800
    }

def veri_kazı_halalbooking_com():
    return {
        "Superior Tek Büyük Yataklı Oda": 15120,
        "Family Corner Suite": 22100,
        "Family Corner Superior Suite": 25400,
        "Excective Family Suite": 29800,
        "Excective Thermal Family Suite": 33100
    }

# Excel Şablonundaki Yeni Oda Tipleri Listesi
oda_tipleri = [
    "Superior Tek Büyük Yataklı Oda",
    "Family Corner Suite",
    "Family Corner Superior Suite",
    "Excective Family Suite",
    "Excective Thermal Family Suite"
]

def tabloyu_olustur(aktif_arama=False):
    tablo_listesi = []
    hotels_data = veri_kazı_hotels_com() if aktif_arama else {}
    halal_data = veri_kazı_halalbooking_com() if aktif_arama else {}
    
    for oda in oda_tipleri:
        satir = {L['oda_tipi']: oda}
        
        # 1. Hotels.com Sütunları
        if "hotels.com" in kaynaklar and oda in hotels_data:
            fiyat_gunluk_try = hotels_data[oda]
            fiyat_paket_try = fiyat_gunluk_try * gece_sayisi
            
            # Kur çevrim katsayısı
            bölüm = kurlar['EUR'] if hedef_para_birimi == "EUR" else (kurlar['USD'] if hedef_para_birimi == "USD" else 1.0)
            
            satir[f"hotels.com ({L['giris'].split()[0]} Tutar)"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
            satir[f"hotels.com (Paket Tutarı)"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
        else:
            satir[f"hotels.com ({L['giris'].split()[0]} Tutar)"] = f"{simge} -"
            satir[f"hotels.com (Paket Tutarı)"] = f"{simge} -"
            
        # 2. HalalBooking Sütunları
        if "halalbooking.com" in kaynaklar and oda in halal_data:
            fiyat_gunluk_try = halal_data[oda]
            fiyat_paket_try = fiyat_gunluk_try * gece_sayisi
            
            bölüm = kurlar['EUR'] if hedef_para_birimi == "EUR" else (kurlar['USD'] if hedef_para_birimi == "USD" else 1.0)
            
            satir[f"halalbooking.com ({L['giris'].split()[0]} Tutar)"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
            satir[f"halalbooking.com (Paket Tutarı)"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
        else:
            satir[f"halalbooking.com ({L['giris'].split()[0]} Tutar)"] = f"{simge} -"
            satir[f"halalbooking.com (Paket Tutarı)"] = f"{simge} -"
            
        tablo_listesi.append(satir)
    return pd.DataFrame(tablo_listesi)

# --- PANEL TETİKLEYİCİSİ ---
if st.button(L['ara'], type="primary", use_container_width=True):
    with st.spinner(L['taraniyor']):
        st.session_state.v6_df = tabloyu_olustur(aktif_arama=True)

if 'v6_df' not in st.session_state:
    st.session_state.v6_df = tabloyu_olustur(aktif_arama=False)

# Multi-index başlık hiyerarşisi oluşturma (Şablon Görünümü İçin)
# Streamlit dataframe yapısını Excel formatındaki gibi gruplayabilmek için kolon isimlerini düzenliyoruz
display_df = st.session_state.v6_df.copy()

st.write(f"### {L['sonuc']} ({hedef_para_birimi} - {gece_sayisi} Gece)")
st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- EXCEL FORMATLI İNDİRME MOTORU ---
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    display_df.to_excel(writer, sheet_name='B2B_Sinnada_Report', index=False)
    
st.download_button(
    label=L['excel'],
    data=buffer.getvalue(),
    file_name=f"Sinnada_Report_{hedef_para_birimi}.xlsx",
    mime="application/vnd.ms-excel",
    use_container_width=True
)
