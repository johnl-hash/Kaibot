import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- CONFIGURACIÓN DE PÁGINA (AQUÍ FORZAMOS QUE SE ABRA EL MENÚ) ---
st.set_page_config(
    page_title="Asistente Kaiowa",
    page_icon="🟦",
    layout="centered",
    initial_sidebar_state="expanded"  # <--- ESTO OBLIGA A MOSTRAR LA BARRA LATERAL
)

# --- URL PRINCIPAL (RAÍZ) ---
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

    .st-emotion-cache-10trblm.e1nzilvr1 {
        background-color: #f0f2f6 !important;
        color: black !important;
        border: 1px solid #e0e0e0;
    }
    
    h1 { color: #3f5fdf; font-family: sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN 1: RASTREADOR ---
def find_subpages(base_url):
    found_urls = {base_url}
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                if "sites.google.com" in full_url and "/informate-kaiowa/" in full_url:
                    found_urls.add(full_url)
    except Exception as e:
        pass
    return list(found_urls)

# --- FUNCIÓN 2: LECTOR ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_knowledge_base(start_url):
    all_urls = find_subpages(start_url)
    st.toast(f"🔎 He encontrado {len(all_urls)} páginas.", icon="info")
    combined_text = ""
    progress_text = "Leyendo manuales..."
    my_bar = st.progress(0, text=progress_text)
    
    for idx, url in enumerate(all_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = f"\n--- FUENTE: {url} ---\n"
                tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'li', 'span'])
                for tag in tags:
                    text = tag.get_text().strip()
                    if len(text) > 30:
                        page_text += text + "\n"
                combined_text += page_text
        except:
            continue
        my_bar.progress((idx + 1) / len(all_urls), text=progress_text)
    my_bar.empty()
    return combined_text

# --- INTERFAZ ---
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/1x/keep_2020q4_48dp.png", width=40)
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    if st.button("🔄 Actualizar Info"):
        st.cache_data.clear()
        st.rerun()

st.title("Asistente Kaiowa 💬")

if not api_key:
    st.warning("👈 Ingresa la API Key en el menú izquierdo para comenzar.")
    st.stop()

if "kb_text" not in st.session_state:
    with st.spinner("Conectando con el sitio web..."):
        st.session_state.kb_text = get_knowledge_base(BASE_URL)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! 👋 Estoy lista. ¿Qué duda tienes?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu duda aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        genai.configure(api_key=api_key)
        system_instruction = f"""
        Eres un asistente experto de Kaiowa.
        INFORMACIÓN: {st.session_state.kb_text}
        INSTRUCCIONES: Responde SOLO con la información provista. Tutea y sé amable.
        """
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Error: {e}")
