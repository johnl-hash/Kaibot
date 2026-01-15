import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

st.set_page_config(page_title="Asistente Kaiowa", layout="centered")

# Estilo visual limpio
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
def get_kb_content():
    urls = {BASE_URL}
    try:
        r = requests.get(BASE_URL, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                full = urljoin(BASE_URL, a['href'])
                if "sites.google.com" in full and "/informate-kaiowa/" in full:
                    urls.add(full)
    except: pass
    text = ""
    for link in list(urls):
        try:
            res = requests.get(link, timeout=10)
            if res.status_code == 200:
                s = BeautifulSoup(res.content, 'html.parser')
                text += f"\n--- PAGINA: {link} ---\n"
                for tag in s.find_all(['p', 'h1', 'h2', 'li']):
                    clean = tag.get_text().strip()
                    if len(clean) > 20: text += clean + "\n"
        except: pass
    return text

st.title("Asistente Kaiowa 💬")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura GEMINI_API_KEY en Secrets.")
    st.stop()

if "kb" not in st.session_state:
    st.session_state.kb = get_kb_content()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Conexión establecida. ¿Qué duda tienes?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # EL CAMBIO TÉCNICO DEFINITIVO:
        # Buscamos la ruta interna del modelo antes de usarlo para evitar el 404
        model_info = genai.get_model('models/gemini-1.5-flash')
        model = genai.GenerativeModel(model_name=model_info.name)
        
        instrucciones = f"Eres el asistente de Kaiowa. Tutea. Usa solo esto: {st.session_state.kb}"
        
        with st.chat_message("assistant"):
            response = model.generate_content(instrucciones + "\n\nPregunta: " + prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        # Si falla el Flash, intentamos la ruta directa del Pro sin intermediarios
        try:
            model = genai.GenerativeModel('gemini-1.0-pro')
            response = model.generate_content(prompt)
            st.markdown(response.text)
        except:
            st.error(f"Error de acceso: {e}")
