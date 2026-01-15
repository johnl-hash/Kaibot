import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asistente Kaiowa", page_icon="🟦", layout="centered")

# --- ESTILOS VISUALES (Tus colores) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-16idsys.e1nzilvr5 { background-color: #3f5fdf !important; color: white !important; }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }
    h1 { color: #3f5fdf; }
</style>
""", unsafe_allow_html=True)

# --- URL DEL SITIO (TU BASE DE DATOS) ---
BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

# --- FUNCIONES DE LECTURA ---
@st.cache_resource
def get_knowledge_base():
    # 1. Buscar enlaces
    urls = {BASE_URL}
    try:
        r = requests.get(BASE_URL)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                full = urljoin(BASE_URL, a['href'])
                if "sites.google.com" in full and "/informate-kaiowa/" in full:
                    urls.add(full)
    except: pass

    # 2. Leer contenido
    text = ""
    url_list = list(urls)
    
    # Barra de progreso visual
    progress_text = "Conectando con la base de conocimientos..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, link in enumerate(url_list):
        try:
            resp = requests.get(link)
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

# --- INICIO DE LA APP ---

st.title("Asistente Kaiowa 💬")

# 1. RECUPERAR LA LLAVE SECRETA (INVISIBLE)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ No he encontrado la API Key en los 'Secrets' de Streamlit.")
    st.info("Ve a Settings > Secrets y pega: GEMINI_API_KEY = 'tu_clave'")
    st.stop()

# 2. CARGAR INFORMACIÓN
if "kb_text" not in st.session_state:
    st.session_state.kb_text = get_knowledge_base()

# 3. CHATBOT
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Ya estoy conectada a la intranet. ¿En qué te ayudo?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        genai.configure(api_key=api_key)
        
        system_instruction = f"""
        Eres el asistente de Kaiowa.
        INFORMACIÓN DEL SITIO: {st.session_state.kb_text}
        INSTRUCCIONES: Responde amable y SOLO con la info de arriba. Si no sabes, dilo.
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")
