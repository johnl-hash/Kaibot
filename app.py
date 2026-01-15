import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.set_page_config(page_title="Asistente Kaiowa", layout="centered")

# Estilos visuales
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-16idsys.e1nzilvr5 { background-color: #3f5fdf !important; color: white !important; }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }
    h1 { color: #3f5fdf; }
</style>
""", unsafe_allow_html=True)

BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

@st.cache_resource
def get_kb():
    urls = {BASE_URL}
    try:
        r = requests.get(BASE_URL, timeout=10)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for a in s.find_all('a', href=True):
                f = urljoin(BASE_URL, a['href'])
                if "sites.google.com" in f and "/informate-kaiowa/" in f: urls.add(f)
    except: pass
    t = ""
    for l in list(urls):
        try:
            res = requests.get(l, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                t += f"\n--- Seccion: {l} ---\n"
                for tag in soup.find_all(['p', 'h1', 'h2', 'li']):
                    c = tag.get_text().strip()
                    if len(c) > 20: t += c + "\n"
        except: pass
    return t

st.title("Asistente Kaiowa 💬")

# Verificar Secret
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Error: Configura la API Key en Secrets.")
    st.stop()

if "kb" not in st.session_state:
    st.session_state.kb = get_kb()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hola. ¿En qué proceso tienes duda?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # PROBAR MODELO FLASH (SI FALLA, PROBAR MODELO PRO)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            contexto = f"Usa solo esta info: {st.session_state.kb}. Tutea siempre. Pregunta: {prompt}"
            response = model.generate_content(contexto)
        except:
            model = genai.GenerativeModel('gemini-pro')
            contexto = f"Usa solo esta info: {st.session_state.kb}. Tutea siempre. Pregunta: {prompt}"
            response = model.generate_content(contexto)
            
        with st.chat_message("assistant"):
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error de Google: {e}")
