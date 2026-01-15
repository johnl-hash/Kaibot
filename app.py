import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuración de la App
st.set_page_config(page_title="Asistente Kaiowa", layout="centered")

# Estilo visual solicitado
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    .st-emotion-cache-16idsys.e1nzilvr5 { background-color: #3f5fdf !important; color: white !important; }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }
    h1 { color: #3f5fdf; }
</style>
""", unsafe_allow_html=True)

BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

@st.cache_resource
def leer_sitio():
    urls = {BASE_URL}
    try:
        r = requests.get(BASE_URL, timeout=10)
        if r.status_code == 200:
            s = BeautifulSoup(r.content, 'html.parser')
            for a in s.find_all('a', href=True):
                f = urljoin(BASE_URL, a['href'])
                if "sites.google.com" in f and "/informate-kaiowa/" in f: urls.add(f)
    except: pass
    texto = ""
    for link in list(urls):
        try:
            res = requests.get(link, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                texto += f"\n--- SECCION: {link} ---\n"
                for tag in soup.find_all(['p', 'h1', 'h2', 'li']):
                    c = tag.get_text().strip()
                    if len(c) > 20: texto += c + "\n"
        except: pass
    return texto

st.title("Asistente Kaiowa 💬")

# Verificar API Key en Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura GEMINI_API_KEY en Secrets.")
    st.stop()

if "kb" not in st.session_state:
    with st.spinner("Cargando información del portal..."):
        st.session_state.kb = leer_sitio()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Estoy lista. ¿Qué duda tienes sobre los procesos?"}]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        # LLAMADA DIRECTA (SIN LIBRERÍAS DE GOOGLE)
        api_key = st.secrets["GEMINI_API_KEY"]
        # Usamos la versión estable 'v1' para asegurar compatibilidad
        url_api = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Eres el asistente de Kaiowa. Tutea siempre. Usa solo esta información: {st.session_state.kb}\n\nPregunta: {prompt}"
                }]
            }]
        }
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                response = requests.post(url_api, json=payload, headers=headers, timeout=30)
                data = response.json()
                
                if "candidates" in data:
                    respuesta = data["candidates"][0]["content"]["parts"][0]["text"]
                    st.markdown(respuesta)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})
                else:
                    st.error(f"Error de Google: {data.get('error', {}).get('message', 'Desconocido')}")

    except Exception as e:
        st.error(f"Error de conexión: {e}")
