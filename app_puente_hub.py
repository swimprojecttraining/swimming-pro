import streamlit as st
import time
import hmac
import hashlib
import base64
from supabase import create_client

def generar_token_handshake(nombre_club, secret_key_exclusivo):
    """
    Genera un token firmado criptográficamente mediante HMAC-SHA256
    con una validez estricta basada en tiempo Unix.
    """
    timestamp = str(int(time.time()))
    mensaje = f"{nombre_club}|{timestamp}"
    firma = hmac.new(secret_key_exclusivo.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    token_completo = f"{mensaje}|{firma}"
    return base64.b64encode(token_completo.encode()).decode()

# **********************************************************************************
# INTERFAZ Y CONFIGURACIÓN VISUAL
# **********************************************************************************
st.set_page_config(page_title="Swim Analytics PRO - Portal Central", page_icon="🔑", layout="centered")

st.markdown("<h1 style='text-align: center;'>🏊 Swim Analytics PRO</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>Consola Central de Acceso</h3>", unsafe_allow_html=True)
st.markdown("---")

# 🔒 INICIALIZACIÓN SEGURA: Previene el NameError si la infraestructura falla
conectar = False
clubes = []
dict_clubes = {}

# 1. Intentar conectar con la base de datos de infraestructura central del Hub
try:
    hub_url = st.secrets["HUB_SUPABASE_URL"]
    hub_key = st.secrets["HUB_SUPABASE_KEY"]
    supabase_hub = create_client(hub_url, hub_key)
    
    # 2. Extraer los clubes configurados y sus llaves secretas de firma
    resp = supabase_hub.table("clubes_adscritos").select("nombre_club", "url_subdominio", "club_secret_key").execute()
    clubes = resp.data if resp.data else []
except Exception as e:
    st.error(f"❌ Error de conexión o infraestructura central: {e}")
    st.info("Por favor, verifique los Secrets de Streamlit Cloud y la disponibilidad de Supabase.")

# **********************************************************************************
# CONTROL DE INTERFAZ DE USUARIO
# **********************************************************************************
if clubes:
    # Mapear los datos de la fila de la BD al selector visual
    dict_clubes = {c["nombre_club"]: c for c in clubes}

    with st.form("form_acceso_hub"):
        st.markdown("#### 🏢 Selección de Institución")
        club_seleccionado = st.selectbox(
            "Seleccione el Club de Natación al que desea ingresar:",
            options=list(dict_clubes.keys())
        )
        
        conectar = st.form_submit_button("🚀 Validar e Ingresar al Portal del Club", use_container_width=True)
else:
    if "supabase_hub" in locals():
        st.info("💡 Actualmente no hay clubes registrados en la plataforma central.")

# **********************************************************************************
# PROCESAMIENTO DEL ACCESO INTERCLUBES
# **********************************************************************************
if conectar and dict_clubes:
    club_info = dict_clubes[club_seleccionado]
    url_destino = club_info["url_subdominio"]
    secret_exclusivo = club_info["club_secret_key"]
    
    with st.spinner("Generando pase de abordaje digital seguro..."):
        # Crear el token criptográfico al vuelo (en memoria RAM)
        token_dinamico = generar_token_handshake(club_seleccionado, secret_exclusivo)
        
        # Asegurar que la URL termine sin barras inclinadas antes del parámetro
        base_url = url_destino.rstrip("/")
        url_final = f"{base_url}/?auth={token_dinamico}"
        
        # ✨ REDIRECCIÓN SEGURA SIN BUCLES: Cambiamos la inyección HTML por un botón dinámico nativo
        st.success(f"🎯 Pase de acceso autorizado para **{club_seleccionado}**.")
        st.markdown("Haga clic en el siguiente enlace oficial para abrir de forma segura el nodo de la institución:")
        st.link_button(
            f"🔓 Abrir Portal del {club_seleccionado}", 
            url_final, 
            use_container_width=True
        )
        
        # 📌 MENSAJE COSMÉTICO E INTUITIVO PARA EL USUARIO
        st.markdown("---")
        st.warning(
            "💡 **Aviso del Sistema:** Gracias por ingresar a **Swim Club Control**.\n\n"
            "Su portal operativo se abrirá en una pestaña paralela de forma segura. "
            "Si requiere generar una nueva pantalla de acceso o cambiar de institución, simplemente **actualice esta página**."
        )
