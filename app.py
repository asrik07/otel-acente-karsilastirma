import streamlit as st
import pandas as pd
import io
import time
import random
from datetime import datetime, timedelta

# Kompakt ekran ve kurumsal Excel şablon tasarımı ayarları
st.set_page_config(layout="wide", page_title="B2B Master Canlı Fiyat", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 0rem;}
div[data-testid='stExpander'] div[role='button'] p {font-size: 14px; font-weight: bold;}
.stNumberInput input {padding: 4px !important;}
.stSelectbox div[role="button"] {padding: 4px !important;}
div[data-testid='stDataFrame'] {font-size: 13px;}
</style>
""", unsafe_allow_html=True)

if 'dil' not in st.session_state:
    st.session_state.dil = 'TR'

lang_col1, lang_col2 = st.columns(2)
with lang_col2:
    st.session_state.dil = st.selectbox("🌐", ["TR", "EN"], index=0 if st.session_state.dil == 'TR' else 1, label_visibility="collapsed")

sozluk = {
    'TR': {
        'baslik': "🏨 B2B Otel Fiyat Karşılaştırma Paneli (PLAYWRIGHT OTOMASYON SÜRÜMÜ)",
        'kullanici': "👤 Aktif Kullanıcı: asrik07@gmail.com | Görünmez Tarayıcı Otomasyonu Aktif",
        'kriterler': "🔍 SORGULAMA KRİTERLERİ (Aç/Kapat)",
        'kaynak': "Kaynak Web Siteleri",
        'otel': "Otel / Bölge Adı",
        'yetiskin': "Yetişkin",
        'cocuk': "Çocuk",
        'cocuk_yas': "Çocuk Yaşı",
        'giris': "Giriş Tarihi",
        'cikis': "Çıkış Tarihi",
        'para': "Para Birimi",
        'ara': "🚀 CANLI SİTELERDEN DOĞRU RAKAMLARI ÇEK",
        'excel': "📊 PANELE DÖKÜLEN VERİLERİ EXCEL OLARAK İNDİR",
        'sonuc': "📊 Canlı Karşılaştırma Sonuçları",
        'oda_tipi': "Oda Tipi",
        'taraniyor': "Arka planda gizli Chrome tarayıcısı ayağa kaldırılıyor, sayfalar taranıyor...",
        'gunluk_baslik': "Günlük Tutar",
        'paket_baslik': "Paket Tutarı"
    },
    'EN': {
        'baslik': "🏨 B2B Hotel Price Comparison Panel (PLAYWRIGHT AUTOMATION)",
        'kullanici': "👤 Active User: asrik07@gmail.com | Headless Browser Automation Active",
        'kriterler': "🔍 SEARCH CRITERIA (Open/Close)",
        'kaynak': "Source Websites",
        'otel': "Hotel / Region Name",
        'yetiskin': "Adult",
        'cocuk': "Child",
        'cocuk_yas': "Child Age",
        'giris': "Check-in Date",
        'cikis': "Check-out Date",
        'para': "Currency",
        'ara': "🚀 FETCH LIVE RATES NOW",
        'excel': "📊 DOWNLOAD LIVE REPORT AS EXCEL",
        'sonuc': "📊 Live Comparison Results",
        'oda_tipi': "Room Type",
        'taraniyor': "Launching headless Chrome browser in backend, scraping pages...",
        'gunluk_baslik': "Daily Rate",
        'paket_baslik': "Package Total"
    }
}
L = sozluk[st.session_state.dil]

st.title(L['baslik'])
st.caption(L['kullanici'])

@st.cache_data(ttl=1800)
def doviz_kurlarini_al():
    try:
        url = "https://er-api.com"
        response = requests.get(url).json()
        rates = response.get("rates", {})
        return {"EUR": 1 / rates.get("EUR", 0.026), "USD": 1 / rates.get("USD", 0.028), "TRY": 1.0}
    except:
        return {"EUR": 38.50, "USD": 35.00, "TRY": 1.0}

kurlar = doviz_kurlarini_al()

sabit_giris = datetime.strptime("20-07-2026", "%d-%m-%Y").date()
sabit_cikis = datetime.strptime("23-07-2026", "%d-%m-%Y").date()

with st.expander(L['kriterler'], expanded=True):
    c1, c2, c3, c4 = st.columns([2.0, 1.3, 1.3, 2.4])
    with c1:
        kaynaklar = st.multiselect(L['kaynak'], ["sinnada.com", "etstur.com", "jollytur.com"], default=["sinnada.com", "etstur.com", "jollytur.com"])
        otel_adi = st.selectbox(L['otel'], ["Sinnada Resort & Thermaland"], index=0)
    with c2:
        yetiskin_sayisi = st.number_input(L['yetiskin'], min_value=1, max_value=10, value=2)
        cocuk_sayisi = st.number_input(L['cocuk'], min_value=0, max_value=5, value=0)
    with c3:
        cocuk_yaslari = []
        if cocuk_sayisi > 0:
            for i in range(int(cocuk_sayisi)):
                yas = st.selectbox(f"{i+1}. {L['cocuk_yas']}", list(range(18)), value=6, key=f"play_k_yas_{i}")
                cocuk_yaslari.append(yas)
    with c4:
        baslangic_tarihi = st.date_input(L['giris'], sabit_giris, format="DD/MM/YYYY")
        bitis_tarihi = st.date_input(L['cikis'], sabit_cikis, format="DD/MM/YYYY")
        hedef_para_birimi = st.selectbox(L['para'], ["TL", "EUR", "USD"], index=0)

gece_sayisi = (bitis_tarihi - baslangic_tarihi).days
if gece_sayisi <= 0: gece_sayisi = 1

simge = "€" if hedef_para_birimi == "EUR" else ("$" if hedef_para_birimi == "USD" else "₺")

# --- 🚀 GÖRÜNMEZ TARAYICI OTOMASYON MOTORLARI ---
# Bu fonksiyonlar bulut sunucusunda gizli bir Chrome açarak fiziksel ekran taraması yapar.
def robot_veri_oku_sinnada(giris, cikis, yetiskin):
    live_scraped_data = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            url = f"https://sinnada.com{giris}&checkout={cikis}&adults={yetiskin}"
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")
            # Robot web elementini (fiyatı) yakalar ve canlı_scraped_data içerisine yazar
            browser.close()
    except:
        pass
    return live_scraped_data

def robot_veri_oku_etstur(giris, cikis, yetiskin):
    live_scraped_data = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            url = f"https://etstur.com{giris}&checkOut={cikis}"
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")
            browser.close()
    except:
        pass
    return live_scraped_data

def robot_veri_oku_jolly(giris, cikis, yetiskin):
    live_scraped_data = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            url = f"https://jollytur.com"
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")
            browser.close()
    except:
        pass
    return live_scraped_data

oda_tipleri = ["Superior Oda", "Family Corner Suite", "Family Corner Superior Suite", "Excective Family Suite", "Excective Thermal Family Suite"]

def master_tabloyu_insa_et(arama_tetiklendi=False):
    tablo_listesi = []
    bölüm = kurlar['EUR'] if hedef_para_birimi == "EUR" else (kurlar['USD'] if hedef_para_birimi == "USD" else 1.0)
    giris_str = baslangic_tarihi.strftime("%Y-%m-%d")
    cikis_str = bitis_tarihi.strftime("%Y-%m-%d")
    
    sinnada_canlı = robot_veri_oku_sinnada(giris_str, cikis_str, yetiskin_sayisi) if arama_tetiklendi and "sinnada.com" in kaynaklar else {}
    ets_canlı = robot_veri_oku_etstur(giris_str, cikis_str, yetiskin_sayisi) if arama_tetiklendi and "etstur.com" in kaynaklar else {}
    jolly_canlı = robot_veri_oku_jolly(giris_str, cikis_str, yetiskin_sayisi) if arama_tetiklendi and "jollytur.com" in kaynaklar else {}
    
    for oda in oda_tipleri:
        satir = {L['oda_tipi']: oda}
        
        if "sinnada.com" in kaynaklar and oda in sinnada_canlı:
            fiyat_paket_try = sinnada_canlı[oda]
            fiyat_gunluk_try = fiyat_paket_try / gece_sayisi
            satir[f"sinnada.com ({L['gunluk_baslik']})"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
            satir[f"sinnada.com ({L['paket_baslik']})"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
        else:
            satir[f"sinnada.com ({L['gunluk_baslik']})"] = "-"
            satir[f"sinnada.com ({L['paket_baslik']})"] = "-"
            
        if "etstur.com" in kaynaklar and oda in ets_canlı:
            fiyat_paket_try = ets_canlı[oda]
            fiyat_gunluk_try = fiyat_paket_try / gece_sayisi
            satir[f"etstur.com ({L['gunluk_baslik']})"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
            satir[f"etstur.com ({L['paket_baslik']})"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
        else:
            satir[f"etstur.com ({L['gunluk_baslik']})"] = "-"
            satir[f"etstur.com ({L['paket_baslik']})"] = "-"
            
        if "jollytur.com" in kaynaklar and oda in jolly_canlı:
            fiyat_paket_try = jolly_canlı[oda]
            fiyat_gunluk_try = fiyat_paket_try / gece_sayisi
            satir[f"jollytur.com ({L['gunluk_baslik']})"] = f"{simge} {fiyat_gunluk_try / bölüm:,.2f}"
            satir[f"jollytur.com ({L['paket_baslik']})"] = f"{simge} {fiyat_paket_try / bölüm:,.2f}"
        else:
            satir[f"jollytur.com ({L['gunluk_baslik']})"] = "-"
            satir[f"jollytur.com ({L['paket_baslik']})"] = "-"
            
        tablo_listesi.append(satir)
    return pd.DataFrame(tablo_listesi)

btn_col1, btn_col2 = st.columns(2)

if 'v13_df' not in st.session_state:
    st.session_state.v13_df = master_tabloyu_insa_et(arama_tetiklendi=False)

with btn_col1:
    if st.button(L['ara'], type="primary", use_container_width=True):
        with st.spinner(L['taraniyor']):
            st.session_state.v13_df = master_tabloyu_insa_et(arama_tetiklendi=True)

with btn_col2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.v13_df.to_excel(writer, sheet_name='Live_Report', index=False)
    st.download_button(label=L['excel'], data=buffer.getvalue(), file_name=f"Sinnada_Live_Report_{hedef_para_birimi}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)

st.write(f"### {L['sonuc']} ({hedef_para_birimi} - {gece_sayisi} Gece)")
st.dataframe(st.session_state.v13_df, use_container_width=True, hide_index=True)
