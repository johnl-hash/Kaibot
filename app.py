import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asistente Kaiowa", page_icon="🟦", layout="centered")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Estilos del Chat */
    .st-emotion-cache-16idsys.e1nzilvr5 { background-color: #3f5fdf !important; color: white !important; }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }
    h1 { color: #3f5fdf; }
    /* Estilo para el input de la llave */
    .stTextInput input { background-color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

# --- URL DEL SITIO ---
BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

# --- FUNCIONES ---
def get_knowledge_base(base_url):
    # 1. Buscar enlaces
    urls = {base_url}
    try:
        r = requests.get(base_url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                full = urljoin(base_url, a['href'])
                if "sites.google.com" in full and "/informate-kaiowa/" in full:
                    urls.add(full)
    except: pass

    # 2. Leer contenido
    text = ""
    my_bar = st.progress(0, text="Escaneando sitio web...")
    url_list = list(urls)
    
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

# --- LOGICA PRINCIPAL (SIN MENÚ LATERAL) ---

st.title("Asistente Kaiowa 💬")

# 1. GESTIÓN DE LA LLAVE (EN EL CENTRO DE LA PANTALLA)
if "my_api_key" not in st.session_state:
    st.session_state.my_api_key = ""

if not st.session_state.my_api_key:
    st.info("👋 Hola. Para comenzar, necesito configuración.")
    st.write("Por favor, pega tu **Gemini API Key** aquí abajo:")
    
    key_input = st.text_input("API Key", type="password")
    
    if st.button("🚀 Iniciar Asistente"):
        if key_input:
            st.session_state.my_api_key = key_input
            st.rerun() # Recarga la página para entrar al chat
        else:
            st.error("Por favor pega la llave primero.")
    
    st.stop() # DETIENE EL CÓDIGO AQUÍ SI NO HAY LLAVE

# 2. CARGA DE INFORMACIÓN (SOLO SI YA HAY LLAVE)
if "kb_text" not in st.session_state:
    with st.spinner("Conectando con la Intranet Kaiowa..."):
        st.session_state.kb_text = get_knowledge_base(BASE_URL)
        st.success("¡Información cargada!")
        time.sleep(1)

# 3. EL CHATBOT
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Listo! Ya leí el sitio web. ¿En qué te ayudo?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        genai.configure(api_key=st.session_state.my_api_key)
        
        system_instruction = f"""
        Eres el asistente de Kaiowa.
        INFORMACIÓN DEL SITIO: {st.session_state.kb_text}
        INSTRUCCIONES: Responde amable y SOLO con la info de arriba.
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")
        if "API key" in str(e):
            st.warning("Tu llave parece inválida. Recarga la página para ponerla de nuevo.")
