import base64
import hashlib
import hmac
import time
import requests
import streamlit as st
from supabase import create_client


# ============================================================
# ⚙️ CONEXIÓN GLOBAL CACHEADA (A nivel raíz del archivo)
# ============================================================
@st.cache_resource
def obtener_cliente_supabase():
  """Crea y mantiene viva la instancia de conexión a Supabase en memoria."""
  return create_client(
      st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
  )


def generar_token_handshake(nombre_club, secret_key_exclusivo):
  """Genera un token firmado criptográficamente mediante HMAC-SHA256."""
  timestamp = str(int(time.time()))
  mensaje = f"{nombre_club}|{timestamp}"
  firma = hmac.new(
      secret_key_exclusivo.encode(), mensaje.encode(), hashlib.sha256
  ).hexdigest()
  token_completo = f"{mensaje}|{firma}"
  return base64.b64encode(token_completo.encode()).decode()


# ============================================================
# 🎨 FUNCIÓN PARA INYECTAR FONDO / MARCA DE AGUA DEL CLUB
# ============================================================
@st.cache_data(ttl=3600)
def obtener_base64_desde_url(url_imagen):
  """Descarga la imagen del logo y la convierte a Base64 para inyección CSS."""
  try:
    response = requests.get(url_imagen, timeout=5)
    if response.status_code == 200:
      return base64.b64encode(response.content).decode()
  except Exception:
    pass
  return None


def aplicar_fondo_club(url_o_path_logo):
  """Inyecta CSS para mostrar el logo del club seleccionado como marca de agua en el fondo."""
  if not url_o_path_logo:
    return

  # Verificar si es URL o archivo local
  if url_o_path_logo.startswith("http://") or url_o_path_logo.startswith(
      "https://"
  ):
    b64_img = obtener_base64_desde_url(url_o_path_logo)
  else:
    try:
      with open(url_o_path_logo, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode()
    except Exception:
      b64_img = None

  if b64_img:
    css_bg = f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)), 
                              url("data:image/png;base64,{b64_img}");
            background-size: 320px auto;
            background-repeat: no-repeat;
            background-position: center 35%;
            background-attachment: fixed;
        }}
        </style>
        """
    st.markdown(css_bg, unsafe_allow_html=True)


# **********************************************************************************
# INTERFAZ Y CONFIGURACIÓN VISUAL
# **********************************************************************************
st.set_page_config(
    page_title="Swim Analytics PRO - Portal Central",
    page_icon="🔑",
    layout="centered",
)

st.markdown(
    "<h1 style='text-align: center;'>🏊 Swim Analytics PRO</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h3 style='text-align: center; color: gray;'>Consola Central de Acceso</h3>",
    unsafe_allow_html=True,
)
st.markdown("---")

# 🔒 INICIALIZACIÓN SEGURA
conectar = False
clubes = []
dict_clubes = {}

# 1. Intentar conectar con la base de datos central del Hub
try:
  hub_url = st.secrets["HUB_SUPABASE_URL"]
  hub_key = st.secrets["HUB_SUPABASE_KEY"]
  supabase_hub = create_client(hub_url, hub_key)

  # 2. Extraer los clubes adscritos (incluyendo el campo opcional 'url_logo')
  resp = (
      supabase_hub.table("clubes_adscritos")
      .select("nombre_club", "url_subdominio", "club_secret_key", "url_logo")
      .execute()
  )
  clubes = resp.data if resp.data else []
except Exception as e:
  st.error(f"❌ Error de conexión o infraestructura central: {e}")
  st.info(
      "Por favor, verifique los Secrets de Streamlit Cloud y la disponibilidad"
      " de Supabase."
  )

# **********************************************************************************
# CONTROL DE INTERFAZ DE USUARIO CON CAMBIO DE FONDO DINÁMICO
# **********************************************************************************
if clubes:
  dict_clubes = {c["nombre_club"]: c for c in clubes}

  st.markdown("#### 🏢 Selección de Institución")
  club_seleccionado = st.selectbox(
      "Seleccione el Club de Natación al que desea ingresar:",
      options=list(dict_clubes.keys()),
      key="selector_club_hub",
  )

  # Aplicar de inmediato el fondo/marca de agua del club seleccionado
  logo_actual = dict_clubes[club_seleccionado].get("url_logo")
  if logo_actual:
    aplicar_fondo_club(logo_actual)

  with st.form("form_acceso_hub"):
    conectar = st.form_submit_button(
        "🚀 Validar e Ingresar al Portal del Club", use_container_width=True
    )
else:
  if "supabase_hub" in locals():
    st.info(
        "💡 Actualmente no hay clubes registrados en la plataforma central."
    )

# **********************************************************************************
# PROCESAMIENTO DEL ACCESO INTERCLUBES
# **********************************************************************************
if conectar and dict_clubes:
  club_info = dict_clubes[club_seleccionado]
  url_destino = club_info["url_subdominio"]
  secret_exclusivo = club_info["club_secret_key"]

  with st.spinner("Generando pase de abordaje digital seguro..."):
    token_dinamico = generar_token_handshake(
        club_seleccionado, secret_exclusivo
    )
    base_url = url_destino.rstrip("/")
    url_final = f"{base_url}/?auth={token_dinamico}"

    st.success(f"🎯 Pase de acceso autorizado para **{club_seleccionado}**.")
    st.markdown(
        "Haga clic en el siguiente enlace oficial para abrir de forma segura"
        " el nodo de la institución:"
    )
    st.link_button(
        f"🔓 Abrir Portal del {club_seleccionado}",
        url_final,
        use_container_width=True,
    )

    st.markdown("---")
    st.warning(
        "💡 **Aviso del Sistema:** Gracias por ingresar a **Swim Club"
        " Control**.\n\nSu portal operativo se abrirá en una pestaña paralela"
        " de forma segura. Si requiere generar una nueva pantalla de acceso o"
        " cambiar de institución, simplemente **actualice esta página**."
    )
