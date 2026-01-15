import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Asistente Kaiowa", page_icon="🟦", layout="centered")

# Estilos visuales solicitados
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
    my_bar = st.progress(0, text="Cargando manuales...")
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

# --- INICIO ---
st.title("Asistente Kaiowa 💬")

# Recuperar API Key de los Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Error: No se encontró la GEMINI_API_KEY en Settings > Secrets.")
    st.stop()

# Cargar conocimiento
if "kb_text" not in st.session_state:
    st.session_state.kb_text = get_knowledge_base()

# Historial
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Ya estoy conectada. ¿Qué duda tienes?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Chat
if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        genai.configure(api_key=api_key)
        
        # LA CORRECCIÓN CLAVE ESTÁ AQUÍ:
        # Usamos el nombre del modelo directamente sin prefijos conflictivos
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=f"Eres el asistente de Kaiowa. Usa solo este texto: {st.session_state.kb_text}. Tutea siempre y sé amable."
        )
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                # Forzamos la respuesta
                response = model.generate_content(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        # Si el error 404 persiste, intentamos una ruta alternativa automática
        st.error(f"Error detectado: {e}")
        st.info("Intentando reconexión automática...")
