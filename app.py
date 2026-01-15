import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuración de interfaz
st.set_page_config(page_title="Asistente Kaiowa", page_icon="🟦", layout="centered")

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
def get_knowledge_base():
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
    url_list = list(urls)
    my_bar = st.progress(0, text="Cargando información del sitio...")
    for i, link in enumerate(url_list):
        try:
            resp = requests.get(link, timeout=10)
            if resp.status_code == 200:
                s = BeautifulSoup(resp.content, 'html.parser')
                text += f"\n--- PAGINA: {link} ---\n"
                for tag in s.find_all(['p', 'h1', 'h2', 'li']):
                    clean = tag.get_text().strip()
                    if len(clean) > 20: text += clean + "\n"
        except: pass
        my_bar.progress((i + 1) / len(url_list))
    my_bar.empty()
    return text

st.title("Asistente Kaiowa 💬")

# Carga de llave desde Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Error: Configura GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

if "kb_text" not in st.session_state:
    st.session_state.kb_text = get_knowledge_base()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Conexión establecida. ¿En qué proceso tienes duda?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        genai.configure(api_key=api_key)
        
        # Ajuste técnico para evitar el error 404
        # Se define el modelo sin el prefijo 'models/'
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest"
        )
        
        chat = model.start_chat(history=[])
        
        instrucciones = f"Eres el asistente de Kaiowa. Responde de forma amable y tuteando. Usa SOLAMENTE esta información: {st.session_state.kb_text}"
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando manuales..."):
                response = chat.send_message(f"{instrucciones}\n\nPregunta del usuario: {prompt}")
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error técnico: {e}")
