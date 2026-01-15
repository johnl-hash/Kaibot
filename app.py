import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Interfaz
st.set_page_config(page_title="Asistente Kaiowa", layout="centered")

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
def get_info():
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
    u_list = list(urls)
    bar = st.progress(0, text="Cargando datos...")
    for i, l in enumerate(u_list):
        try:
            res = requests.get(l, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                t += f"\n--- Seccion: {l} ---\n"
                for tag in soup.find_all(['p', 'h1', 'h2', 'li']):
                    c = tag.get_text().strip()
                    if len(c) > 20: t += c + "\n"
        except: pass
        bar.progress((i + 1) / len(u_list))
    bar.empty()
    return t

st.title("Asistente Kaiowa 💬")

# Llave desde Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Error: Falta la llave en Secrets.")
    st.stop()

if "kb_text" not in st.session_state:
    st.session_state.kb_text = get_info()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hola. ¿En qué proceso tienes duda?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        # CONEXIÓN BÁSICA SIN ARGUMENTOS EXTRA
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        instrucciones = f"Eres el asistente de Kaiowa. Responde amable, tuteando y usa SOLO esta info: {st.session_state.kb_text}"
        
        with st.chat_message("assistant"):
            # Usamos el método más estándar posible
            response = model.generate_content(instrucciones + "\n\nPregunta: " + prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")
