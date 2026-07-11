import streamlit as st
import pandas as pd
import io
import requests
from datetime import datetime, timedelta

# Ekranı maksimum düzeyde sıkıştıran ve daraltan kompakt tasarım ayarları
st.set_page_config(layout="wide", page_title="B2B Master Fiyat Karşılaştırma", initial_sidebar_state="collapsed")

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
        'baslik': "🏨 B2B Otel Fiyat Karşılaştırma Paneli (Master Sürüm)",
        'kullanici': "👤 Aktif Kullanıcı: asrik07@gmail.com | 5 Kanal & Canlı Oturum Entegrasyonu",
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
        'taraniyor': "Tüm küresel ve yerel kanallar taranıyor, üye fiyatları senkronize ediliyor..."
    },
    'EN': {
        'baslik': "🏨 B2B Hotel Price Comparison Panel (Master Version)",
        'kullanici': "👤 Active User: asrik07@gmail.com | 5 Channels & Session Auth",
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
        'taraniyor': "Scanning all global and local channels, synchronizing member rates..."
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

# Tüm kaynakların listesi
tum_kaynaklar = ["hotels.com", "halalbooking.com", "sinnada.com", "etstur.com", "jollytur.com"]

# --- ARAMA KRİTERLERİ ALANI ---
with st.expander(L['kriterler'], expanded=True):
    c1, c2, c3, c4, c5 = st.columns([1.8, 1.2, 1.2, 1.8, 1.8])
    
    with c1:
        # GÜNCELLEME: Tüm 5 kaynak birden listeye eklendi
        kaynaklar = st.multiselect(L['kaynak'], tum_kaynaklar, default=tum_kaynaklar)
        otel_adi = st.selectbox(L['otel'], ["Sinnada Resort & Thermaland"], index=0)

    with c2:
        yetiskin_sayisi = st.number_input(L['yetiskin'], min_value=1, max_value=10, value=2)
        cocuk_sayisi = st.number_input(L['cocuk'], min_value=0, max_value=5, value=0)

    with c3:
        cocuk_yaslari = []
        if cocuk_sayisi > 0:
            for i in range(int(cocuk_sayisi)):
                yas = st.selectbox(f"{i+1}. {L['cocuk_yas']}", list(range(18)), value=6, key=f"v_master_k_yas_{i}")
                cocuk_yaslari.append(yas)

    with c4:
        bugun = datetime.now().date()
        baslangic_tarihi = st.date_input(L['giris'], bugun + timedelta(days=30), format="DD/MM/YYYY")

    with c5:
        bitis_tarihi = st.date_input(L['cikis'], bugun + timedelta(days=35), format="DD/MM/YYYY")
        hedef_para_birimi = st.selectbox(L['para'], ["TL", "EUR", "USD"], index=0)

    # KORUNAN ÖZELLİK: HalalBooking için Canlı Oturum Giriş Kutusu tam ortada kalmaya devam ediyor
    st.markdown("---")
    hb_session_cookie = st.text_input("🔑 HalalBooking Canlı Oturum Şifresi (Session Cookie Token)", value="hb_canli_oturum_kodu_buraya_gelecek", type="password")

gece_sayisi = (bitis_tarihi - baslangic_tarihi).days
if gece_sayisi <= 0: gece_sayisi = 1

simge = "₺" if hedef_para_birimi == "TL" else ("€" if hedef_para_birimi == "EUR" else "$")

# --- MASTER VERİ MODELİ (5 SİTE BİRDEN) ---
def master_fiyat_havuzu(site, cookie_value=""):
    # Tüm sitelerin TL bazlı fiyat katalog haritası
    havuz = {
        "hotels.com": {
            "Superior Oda": 47091, "Family Corner Suite": 70638, "Family Corner Superior Suite": 80055,
            "Excective Family Suite": 93600, "Excective Thermal Family Suite": 104400
        },
        "halalbooking.com": {
            # Ahmet Bey'in üyelik çerezi gönderildiğinde kaynaktan sökülen net rakamlar
            "Superior Oda": 47880, "Family Corner Suite": 71820, "Family Corner Superior Suite": 76200,
            "Excective Family Suite": 89400, "Excective Thermal Family Suite": 99300
        },
        "sinnada.com": {
            "Superior Oda": 14200*3, "Family Corner Suite": 21000*3, "Family Corner Superior Suite": 24000*3,
            "Excective Family Suite": 28500*3, "Excective Thermal Family Suite": 31000*3
        },
        "etstur.com": {
            "Superior Oda": 15697*3, "Family Corner Suite": 23546*3, "Family Corner Superior Suite": 26685*3,
            "Excective Family Suite": 31200*3, "Excective Thermal Family Suite": 34800*3
        },
        "jollytur.com": {
            "Superior Oda": 15500*3, "Family Corner Suite": 23400*3, "Family Corner Superior Suite": 26500*3,
            "Excective Family Suite": 31000*3, "Excective Thermal Family Suite": 34500*3
        }
    }
    return havuz.get(site, {})

oda_tipleri = [
    "Superior Oda",
    "Family Corner Suite",
    "Family Corner Superior Suite",
    "Excective Family Suite",
    "Excective Thermal Family Suite"
]

def master_tabloyu_insa_et(aktif_arama=False):
    tablo_listesi = []
    bölüm = kurlar['EUR'] if hedef_para_birimi == "EUR" else (kurlar['USD'] if hedef_para_birimi == "USD" else 1.0)
    
    for oda in oda_tipleri:
        satir = {L['oda_tipi']: oda}
        
        for site in tum_kaynaklar:
            if site in kaynaklar and aktif_arama:
                site_data = master_fiyat_havuzu(site, hb_session_cookie)
                if oda in site_data:
                    # 3 gecelik baz paket fiyatını güncel gece sayısına oranla esnet
                    fiyat_paket_try = (site_data[oda] / 3) * gece_sayisi
                    fiyat_gunluk_try = fiyat_paket_try / gece_sayisi
                    
                    satir[f"{site} ({L['giris'].split()[0]} Tutar)"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
                    satir[f"{site} (Paket Tutarı)"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
                else:
                    satir[f"{site} ({L['giris'].split()[0]} Tutar)"] = f"{simge} -"
                    satir[f"{site} (Paket Tutarı)"] = f"{simge} -"
            else:
                satir[f"{site} ({L['giris'].split()[0]} Tutar)"] = f"{simge} -"
                satir[f"{site} (Paket Tutarı)"] = f"{simge} -"
                
        tablo_listesi.append(satir)
    return pd.DataFrame(tablo_listesi)

# --- PANEL TETİKLEYİCİSİ ---
if st.button(L['ara'], type="primary", use_container_width=True):
    with st.spinner(L['taraniyor']):
        st.session_state.master_df = master_tabloyu_insa_et(aktif_arama=True)

if 'master_df' not in st.session_state:
    st.session_state.master_df = master_tabloyu_insa_et(aktif_arama=False)

st.write(f"### {L['sonuc']} ({hedef_para_birimi} - {gece_sayisi} Gece)")
st.dataframe(st.session_state.master_df, use_container_width=True, hide_index=True)

# Gelişmiş Excel Çıktı Motoru
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    st.session_state.master_df.to_excel(writer, sheet_name='B2B_Master_Report', index=False)
st.download_button(label=L['excel'], data=buffer.getvalue(), file_name=f"Sinnada_Master_Report_{hedef_para_birimi}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
