import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asistente Kaiowa",
    page_icon="🟦",
    layout="centered"
)

# --- URL PRINCIPAL (RAÍZ) ---
# Solo necesitas poner la página de inicio. El bot buscará el resto.
BASE_URL = "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio"

# --- ESTILOS CSS (TU DISEÑO EXACTO) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Globo del USUARIO (Azul #3f5fdf) */
    .st-emotion-cache-16idsys.e1nzilvr5 {
        background-color: #3f5fdf !important;
        color: white !important;
    }
    .st-emotion-cache-16idsys.e1nzilvr5 p { color: white !important; }

    /* Globo del BOT (Gris Claro) */
    .st-emotion-cache-10trblm.e1nzilvr1 {
        background-color: #f0f2f6 !important;
        color: black !important;
        border: 1px solid #e0e0e0;
    }
    
    h1 { color: #3f5fdf; font-family: sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN 1: RASTREADOR (DESCUBRE PÁGINAS) ---
def find_subpages(base_url):
    """Entra al inicio y busca enlaces a otras secciones del mismo sitio."""
    found_urls = {base_url} # Usamos un set para evitar duplicados
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Busca todos los links 'a'
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Regla: Solo guardar links que sean del mismo dominio (Google Sites)
                # y que pertenezcan a tu sitio específico
                if "sites.google.com" in full_url and "/informate-kaiowa/" in full_url:
                    found_urls.add(full_url)
    except Exception as e:
        pass # Si falla el rastreo, al menos devuelve la home
    
    return list(found_urls)

# --- FUNCIÓN 2: LECTOR DE CONTENIDO ---
@st.cache_data(ttl=3600, show_spinner=False) # Se guarda en caché 1 hora
def get_knowledge_base(start_url):
    
    # 1. Descubrir páginas
    all_urls = find_subpages(start_url)
    st.toast(f"🔎 He encontrado {len(all_urls)} páginas en tu sitio web.", icon="info")
    
    combined_text = ""
    
    # 2. Barra de progreso visual
    progress_text = "Leyendo manuales actualizados..."
    my_bar = st.progress(0, text=progress_text)
    
    # 3. Leer cada página
    for idx, url in enumerate(all_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Título de la sección (para contexto del bot)
                page_text = f"\n--- FUENTE: {url} ---\n"
                
                # Extraer texto útil
                tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'li', 'span'])
                for tag in tags:
                    text = tag.get_text().strip()
                    if len(text) > 30: # Evitar textos basura muy cortos
                        page_text += text + "\n"
                
                combined_text += page_text
        except:
            continue
        
        # Actualizar barra
        my_bar.progress((idx + 1) / len(all_urls), text=progress_text)
            
    my_bar.empty()
    return combined_text

# --- INTERFAZ ---

with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/1x/keep_2020q4_48dp.png", width=40)
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    st.write("🔄 **Actualización**")
    if st.button("Buscar nuevas páginas"):
        st.cache_data.clear() # Borra la memoria para volver a escanear
        st.rerun()
    st.caption("Si agregas info al sitio, presiona el botón de arriba.")

st.title("Asistente Kaiowa 💬")
st.markdown("Tu herramienta de consulta para cobranza administrativa.")

# Validar API Key
if not api_key:
    st.warning("👈 Ingresa la API Key para comenzar.")
    st.stop()

# Cargar Base de Conocimientos (Automática)
if "kb_text" not in st.session_state:
    with st.spinner("Conectando con el sitio web..."):
        st.session_state.kb_text = get_knowledge_base(BASE_URL)

# --- CHATBOT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! 👋 He leído toda la información publicada en el sitio. ¿En qué puedo ayudarte hoy?"}
    ]

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
        Eres un asistente experto de Kaiowa (Cobranza Administrativa).
        
        INFORMACIÓN ACTUALIZADA DEL SITIO WEB:
        {st.session_state.kb_text}
        
        INSTRUCCIONES:
        1. Responde SOLO con la información provista arriba.
        2. Tutea, sé amable, usa emojis.
        3. Si la info no está en el texto, di: "No encuentro esa información publicada en el sitio web."
        4. Explica simple, sin palabras técnicas.
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")
