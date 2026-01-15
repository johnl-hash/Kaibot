import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURACIÓN: ESTO OBLIGA A ABRIR EL MENÚ ---
st.set_page_config(
    page_title="Asistente Kaiowa",
    page_icon="🟦",
    layout="centered",
    initial_sidebar_state="expanded"  # <--- ESTO ES LA CLAVE
)

# --- URL BASE ---
BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

# --- ESTILOS CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-16idsys.e1nzilvr5 {
        background-color: #3f5fdf !important;
        color: white !important;
    }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }
    h1 { color: #3f5fdf; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
def find_subpages(base_url):
    urls = {base_url}
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a', href=True):
                full = urljoin(base_url, link['href'])
                if "sites.google.com" in full and "/informate-kaiowa/" in full:
                    urls.add(full)
    except: pass
    return list(urls)

@st.cache_data(ttl=3600, show_spinner=False)
def get_knowledge_base(url):
    all_urls = find_subpages(url)
    text = ""
    bar = st.progress(0, text="Leyendo sitio web...")
    for i, link in enumerate(all_urls):
        try:
            r = requests.get(link)
            if r.status_code == 200:
                s = BeautifulSoup(r.content, 'html.parser')
                text += f"\n--- URL: {link} ---\n"
                for t in s.find_all(['p', 'h1', 'h2', 'li']):
                    clean = t.get_text().strip()
                    if len(clean) > 20: text += clean + "\n"
        except: pass
        bar.progress((i + 1) / len(all_urls))
    bar.empty()
    return text

# --- INTERFAZ ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Pegar API Key aquí", type="password")
    st.info("Si no ves este menú, recarga la página.")
    if st.button("🔄 Recargar Info"):
        st.cache_data.clear()
        st.rerun()

st.title("Asistente Kaiowa 💬")

if not api_key:
    st.warning("⬅️ Por favor, pega tu API Key en el menú de la izquierda.")
    st.stop()

if "kb" not in st.session_state:
    with st.spinner("Conectando..."):
        st.session_state.kb = get_knowledge_base(BASE_URL)

if "msg" not in st.session_state:
    st.session_state.msg = [{"role": "assistant", "content": "¡Hola! ¿En qué te ayudo?"}]

for m in st.session_state.msg:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if p := st.chat_input("Tu pregunta..."):
    st.session_state.msg.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=f"Responde solo con esto: {st.session_state.kb}")
        with st.chat_message("assistant"):
            r = model.generate_content(p)
            st.markdown(r.text)
        st.session_state.msg.append({"role": "assistant", "content": r.text})
    except Exception as e:
        st.error(f"Error: {e}")
