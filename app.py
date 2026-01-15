import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asistente Kaiowa - Administrativa",
    page_icon="🟦",
    layout="centered"
)

# --- LISTA DE URLs A CONSULTAR (CEREBRO DEL BOT) ---
# Agrega aquí todas las subpáginas que quieras que el bot lea.
URLS = [
    "https://sites.google.com/kaiowa.co/informate-kaiowa/inicio",
    # "https://sites.google.com/kaiowa.co/informate-kaiowa/otra-pagina", 
]

# --- ESTILOS CSS (DISEÑO KAIOWA) ---
st.markdown("""
<style>
    /* Ocultar menú y footer de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fondo General (Blanco por defecto) */
    
    /* Globo del USUARIO (Azul #3f5fdf, Texto Blanco) */
    .st-emotion-cache-16idsys.e1nzilvr5 {
        background-color: #3f5fdf !important;
        color: white !important;
    }
    /* Forzar color de texto dentro del globo usuario */
    .st-emotion-cache-16idsys.e1nzilvr5 p, 
    .st-emotion-cache-16idsys.e1nzilvr5 div {
        color: white !important;
    }

    /* Globo del BOT (Gris Claro, Texto Negro) */
    .st-emotion-cache-10trblm.e1nzilvr1 {
        background-color: #f0f2f6 !important;
        color: black !important;
        border: 1px solid #e0e0e0;
    }
    
    /* Estilo del Título */
    h1 {
        color: #3f5fdf;
        font-family: sans-serif;
        font-weight: 700;
    }
    
    /* Estilo del subtítulo */
    .caption {
        font-size: 14px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN: LEER EL SITIO WEB ---
@st.cache_data(ttl=3600) # Se actualiza cada hora automáticamente
def get_knowledge_base(urls):
    combined_text = ""
    total_urls = len(urls)
    
    # Barra de progreso simple si son muchas urls
    if total_urls > 1:
        progress_bar = st.progress(0)
    
    for i, url in enumerate(urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer texto limpio de parrafos y titulos
                page_text = f"\n--- INFORMACIÓN DE LA URL: {url} ---\n"
                tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
                
                for tag in tags:
                    text = tag.get_text().strip()
                    if len(text) > 20: # Filtrar textos muy cortos (menús, etc)
                        page_text += text + "\n"
                
                combined_text += page_text
            else:
                combined_text += f"\n[Error leyendo {url}: Status {response.status_code}]\n"
        except Exception as e:
            combined_text += f"\n[Error conexión {url}: {e}]\n"
        
        if total_urls > 1:
            progress_bar.progress((i + 1) / total_urls)
            
    if total_urls > 1:
        progress_bar.empty()
        
    return combined_text

# --- INTERFAZ PRINCIPAL ---

# Sidebar Limpio
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/1x/keep_2020q4_48dp.png", width=40) # Icono genérico
    st.header("Configuración")
    api_key = st.text_input("Gemini API Key", type="password", help="Ingresa tu clave de Google AI Studio")
    st.markdown("---")
    st.info("🔹 Bot exclusivo: Cartera Administrativa")
    st.caption("v1.0 - Kaiowa")

# Título
st.title("Asistente Kaiowa 💬")
st.markdown("<p class='caption'>Hola, soy tu herramienta de consulta rápida para procesos de cobranza administrativa (1-90 días).</p>", unsafe_allow_html=True)

# Cargar Base de Conocimiento (Solo si hay API Key para no gastar recursos)
if api_key:
    if "kb_text" not in st.session_state:
        with st.spinner("Leyendo manuales operativos..."):
            st.session_state.kb_text = get_knowledge_base(URLS)
            if len(st.session_state.kb_text) < 100:
                st.error("⚠️ Parece que no pude leer el sitio web. Verifica que sea PÚBLICO.")
else:
    st.warning("👈 Por favor ingresa tu API Key en el menú lateral para comenzar.")
    st.stop()

# --- GESTIÓN DEL CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! 👋 Soy tu compañera virtual. ¿Tienes dudas sobre algún proceso de cobranza o manejo del sistema? Pregúntame con confianza."}
    ]

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # 1. Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Llamada a Gemini
    try:
        genai.configure(api_key=api_key)
        
        # EL PROMPT DEL SISTEMA (La personalidad)
        system_instruction = f"""
        Eres una asistente experta en cobranza administrativa de la empresa Kaiowa.
        Tu misión es ayudar a las asesoras a resolver dudas operativas rápidamente.
        
        BASE DE CONOCIMIENTO (LEÍDA DEL SITIO WEB):
        {st.session_state.kb_text}
        
        REGLAS DE COMPORTAMIENTO:
        1. Tono: Amable, cercano, usa "tú" (tutea), usa emojis ocasionalmente. Profesional pero no rígido.
        2. Lenguaje: Sencillo, claro, evita tecnicismos complejos. Explica paso a paso.
        3. Fuente: Responde ÚNICAMENTE basándote en la "Base de Conocimiento" de arriba.
        4. Límites: Si la información no está en el texto provisto, di amablemente: "Lo siento, esa info no la tengo en mis manuales actuales. Por favor consúltalo con tu líder." NO busques en internet ni inventes.
        5. Contexto: Recuerda que cobramos cartera de 1 a 90 días.
        """
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                response = model.generate_content(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
