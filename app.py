import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- 1. MODEL YAPILANDIRMASI ---
GEMINI_API_KEY = "AIzaSyCdVwaAATWX2d2Q10YYosgonjbOy4-T3Rw"
genai.configure(api_key=GEMINI_API_KEY)

def model_baslat():
    try:
        mevcut_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        tercih_sirasi = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for tercih in tercih_sirasi:
            if tercih in mevcut_modeller:
                return genai.GenerativeModel(tercih)
        if mevcut_modeller:
            return genai.GenerativeModel(mevcut_modeller[0])
        return None
    except Exception as e:
        st.sidebar.error(f"Model başlatma hatası: {str(e)}")
        return None

model = model_baslat()

st.set_page_config(page_title="Ethosoft Haber Analizi", layout="wide")

# --- 2. FONKSİYONLAR ---

def ai_islem(prompt_text):
    if not model:
        return "❌ Model başlatılamadı. API anahtarınızı kontrol edin."
    try:
        response = model.generate_content(prompt_text)
        return response.text if response else "AI boş yanıt döndürdü."
    except Exception as e:
        return f"❌ Analiz Hatası: {str(e)}"

def kiyamet_etkisi_hesapla(haber_baslik, haber_ozet):
    """Haberin Kıyamet Saati'ne etkisini hesaplar."""
    prompt = f"""
Sen Kıyamet Saati (Doomsday Clock) uzmanısın. Tarihsel olarak saati etkileyen olayları biliyorsun:
- Nükleer silah denemeleri, savaş tehditleri saati ileri alır
- Barış anlaşmaları, silah azaltma saati geri alır
- İklim krizi, biyolojik tehditler saati ileri alır

Haber Başlığı: {haber_baslik}
Haber Özeti: {haber_ozet}

Bu haberin Kıyamet Saati'ne etkisini analiz et ve SADECE şu formatta yanıt ver (başka hiçbir şey yazma):
ETKİ: [+30 saniye / -15 saniye / 0 saniye gibi, tahmini saniye cinsinden]
GEREKÇE: [1 cümle açıklama]
    """
    return ai_islem(prompt)

def haberleri_getir(rss_url):
    if rss_url == "WAR_ZONE":
        return [
            {"baslik": "İran - İsrail Çatışma Riski", "link": "#", "ham_ozet": "Bölgede askeri hareketlilik en üst düzeyde."},
            {"baslik": "Rusya - Ukrayna Savaşı", "link": "#", "ham_ozet": "Stratejik enerji hatları hedef alınıyor."}
        ]
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(rss_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "lxml-xml")
        return [{"baslik": i.title.text, "link": i.link.text, "ham_ozet": i.description.text if i.description else "Açıklama yok."} for i in soup.find_all('item')[:5]]
    except Exception as e:
        st.warning(f"RSS çekme hatası: {str(e)}")
        return []

# --- 3. ARAYÜZ ---

# Kıyamet Saati Açıklaması
st.markdown("""
    <div style="background: linear-gradient(135deg, #1a0000, #2d0000); border: 2px solid #ff4444; border-radius: 15px; padding: 25px; margin-bottom: 30px;">
        <h2 style="color: #ff4444; margin-top: 0;">⏰ Kıyamet Saati Nedir?</h2>
        <p style="color: #cccccc; font-size: 15px; line-height: 1.7; margin: 0;">
        <b style="color: #ff6666;">Kıyamet Saati (Doomsday Clock)</b>, 1947'den bu yana Bulletin of the Atomic Scientists tarafından yayımlanan sembolik bir saattir. 
        Saatin <b style="color: #ff6666;">gece yarısına</b> olan yakınlığı, insanlığın küresel yıkıma ne kadar yakın olduğunu temsil eder. 
        Nükleer savaş, iklim krizi, biyolojik tehditler ve jeopolitik gerilimler saati ileri alırken; barış anlaşmaları ve silah azaltma saati geri alır. 
        <b style="color: #ff6666;">Şu an saat 23:58:30</b> — gece yarısına yalnızca <b style="color: #ff6666;">90 saniye</b> kala, tarihin en tehlikeli noktasındayız.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Bilgilendirme ve Arama
st.markdown("### 🔍 Haber Araştırma ve Teyit Merkezi")
sorgu = st.text_input("Yapay Zeka ile dünyayı tarayın...", placeholder="Örn: İklim krizi son durum...")

if sorgu:
    with st.spinner("AI araştırıyor..."):
        st.info(ai_islem(f"'{sorgu}' hakkında en güncel bilgileri ve risk analizini Türkçe ver."))

st.divider()

col_t, col_l = st.columns([3, 1])
with col_t:
    st.title("☢️ Ethosoft Haber Analizi")
with col_l:
    dil = st.selectbox("🌐 Dil / Language", ["Türkçe", "English", "Deutsch", "French"])

# Kategoriler
urls = {
    "Gündem": "https://www.haberturk.com/rss/gundem.xml",
    "Dünya": "https://www.haberturk.com/rss/dunya.xml",
    "Teknoloji": "https://www.haberturk.com/rss/ekonomi/teknoloji.xml",
    "Ekonomi": "https://www.haberturk.com/rss/ekonomi.xml",
    "Kıyamet Saati (ÖZEL)": "WAR_ZONE"
}

kategori = st.sidebar.selectbox("Kategori", list(urls.keys()))
haberler = haberleri_getir(urls[kategori])

# Haber Listeleme
if haberler:
    for i, h in enumerate(haberler):
        # Her haber yüklendiğinde Kıyamet etkisini otomatik hesapla
        etki_key = f"etki_{kategori}_{i}"
        if etki_key not in st.session_state:
            st.session_state[etki_key] = kiyamet_etkisi_hesapla(h['baslik'], h['ham_ozet'])

        etki_raw = st.session_state.get(etki_key, "")
        
        # Etki rengini belirle
        etki_renk = "#888888"
        etki_sembol = "⚪"
        if "ETKİ:" in etki_raw:
            etki_satir = [l for l in etki_raw.split('\n') if "ETKİ:" in l]
            if etki_satir:
                etki_deger = etki_satir[0]
                if "+" in etki_deger:
                    etki_renk = "#ff4444"
                    etki_sembol = "🔴"
                elif "-" in etki_deger:
                    etki_renk = "#44ff44"
                    etki_sembol = "🟢"

        with st.expander(f"🔹 {h['baslik']}  {etki_sembol} {etki_raw.split(chr(10))[0].replace('ETKİ:', '').strip() if 'ETKİ:' in etki_raw else ''}"):
            
            # Kıyamet etkisi kutusu
            if etki_raw:
                gerekce = ""
                etki_goster = etki_raw
                satirlar = etki_raw.split('\n')
                for satir in satirlar:
                    if "GEREKÇE:" in satir:
                        gerekce = satir.replace("GEREKÇE:", "").strip()
                    if "ETKİ:" in satir:
                        etki_goster = satir.replace("ETKİ:", "").strip()

                st.markdown(f"""
                    <div style="background: #1a1a1a; border-left: 4px solid {etki_renk}; padding: 10px 15px; border-radius: 5px; margin-bottom: 10px;">
                        <span style="color: #888; font-size: 12px;">⏰ KİYAMET SAATİ ETKİSİ</span><br>
                        <span style="color: {etki_renk}; font-size: 18px; font-weight: bold;">{etki_goster}</span><br>
                        <span style="color: #aaa; font-size: 13px;">{gerekce}</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Teyit butonu — her habere özel key
            teyit_key = f"teyit_{kategori}_{i}"
            if st.button(f"🔍 Teyit Et & Analiz Yap", key=f"btn_{kategori}_{i}"):
                with st.spinner("İnceleniyor..."):
                    p = f"Haber: {h['baslik']}. Özet: {h['ham_ozet']}. Bu haberi {dil} dilinde teyit et. Taraflı mı? Kıyamet Saati etkisi nedir? Detaylı analiz yap."
                    st.session_state[teyit_key] = ai_islem(p)

            if teyit_key in st.session_state:
                st.success(f"**AI Analiz Raporu:**\n{st.session_state[teyit_key]}")

            st.write(f"**Özet:** {h['ham_ozet']}")
            st.caption(f"[Kaynağa Git]({h['link']})")

# --- 4. KIYAMET SAATİ ---
st.markdown("""
    <div style="position: relative; margin-top: 50px; padding: 30px; background: #000; border: 4px solid #ff0000; border-radius: 20px; text-align: center; box-shadow: 0px 0px 20px rgba(255,0,0,0.5);">
        <h1 style="color: #ff0000; font-family: 'Courier New', monospace; font-size: 70px; margin: 0;">23:58:30</h1>
        <p style="color: #fff; font-size: 20px; font-weight: bold; letter-spacing: 5px; margin: 10px 0;">GECE YARISINA 90 SANİYE KALA</p>
        <div style="height: 2px; background: #333; width: 80%; margin: 15px auto;"></div>
        <p style="color: #888; font-size: 14px;">Ethosoft Haber Analizi: AI Destekli Küresel Risk Analizi</p>
    </div>
    <style>
        .stApp { background-color: #050505; color: white; }
    </style>
    """, unsafe_allow_html=True)