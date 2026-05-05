# ====================================================================
# INTERFAZ GRÁFICA Y SISTEMA EXPERTO LEGAL JI (EDICIÓN PREMIUM FULL)
# Sistema: AboAgrim Pro DMS
# ====================================================================
from database import db as supabase
import streamlit as st
import zipfile
import os
import shutil
import io
import json
from datetime import datetime, timedelta
from docxtpl import DocxTemplate

# --- CONFIGURACIÓN MAESTRA (DEBE SER EL PRIMER COMANDO) ---
st.set_page_config(page_title="AboAgrim Pro", page_icon="🏛️", layout="centered", initial_sidebar_state="expanded")

# === DATOS MAESTROS DE LA FIRMA ABOAGRIM ===
PRESIDENTE_FIRMA = "Lic. Jhonny Matos, M.A."
DIRECCION_FIRMA = "Calle Boy Scout 83, Plaza Jasansa, Mod. 5-B, Centro Ciudad, Santiago."
TELEFONOS_FIRMA = "829-826-5888 / 809-691-3333"
CORREO_FIRMA = "aboagrim@gmail.com"
# ☁️ SINCRONIZACIÓN MAESTRA CON LA NUBE (SUPABASE) ☁️
# Este bloque alimenta automáticamente a todos los módulos (Mando Central, Alertas, etc.)
try:
    respuesta_global = supabase.table("expedientes").select("*").execute()
    if respuesta_global.data:
        # Traducimos los datos de la nube al formato de diccionario que usa el Mando Central
        st.session_state["db_expedientes"] = {fila["id_expediente"]: fila for fila in respuesta_global.data}
    else:
        st.session_state["db_expedientes"] = {}
except Exception as e:
    # Si hay un micro-corte de internet, creamos una memoria vacía de emergencia para que no colapse
    if "db_expedientes" not in st.session_state:
        st.session_state["db_expedientes"] = {}

# --- INICIALIZACIÓN DE MEMORIA DEL SISTEMA ---
if "bandeja_descargas" not in st.session_state:
    st.session_state["bandeja_descargas"] = []
    
if "plantillas_cargadas" not in st.session_state:
    st.session_state["plantillas_cargadas"] = []

# --- MOTOR DE GENERACIÓN DE DOCUMENTOS WORD ---
def generar_documento_word(ruta_plantilla, diccionario_datos):
    """
    Toma una plantilla .docx y la llena con los datos del diccionario.
    """
    try:
        doc = DocxTemplate(ruta_plantilla)
        
        # Agregamos metadatos de la firma automáticamente
        diccionario_datos.update({
            "firma_nombre": PRESIDENTE_FIRMA,
            "firma_direccion": DIRECCION_FIRMA,
            "firma_tel": TELEFONOS_FIRMA,
            "firma_correo": CORREO_FIRMA,
            "fecha_hoy": datetime.now().strftime("%d de %B de %Y")
        })
        
        doc.render(diccionario_datos)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Error en la forja del documento: {e}")
        return None


# ==========================================
# 👔 ESTILO VISUAL PROFESIONAL (CSS)
# ==========================================
st.markdown("""
    <style>
    /* Fondo principal elegante (Gris oscuro/Azul noche) */
    .stApp {
        background-color: #0b0f19;
    }
    
    /* Contenedores y formularios con borde sutil */
    div[data-testid="stForm"], div[data-testid="stContainer"] {
        background-color: #131a2a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Títulos con el color institucional */
    h1, h2, h3 {
        color: #e2e8f0;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Botones ejecutivos */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid #334155;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #d4af37; /* Toque dorado elegante al pasar el ratón */
        color: #d4af37;
    }
    </style>
""", unsafe_allow_html=True)
# ==========================================
# MOTOR DE GENERACIÓN DE DOCUMENTOS WORD
# ==========================================
from docxtpl import DocxTemplate
import io


# --- CONEXIÓN A SUPABASE (CEREBRO DIGITAL) ---
url_supabase = "https://wqcpbxrltttfnusdrawq.supabase.co"
clave_supabase = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndxY3BieHJsdHR0Zm51c2RyYXdxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYyMTI2NjEsImV4cCI6MjA5MTc4ODY2MX0.uD7v_-rY0b4dJGRSeF1mtDeftNzopFNnyyx7IEhPKPs"

try:
    supabase: Client = create_client(url_supabase, clave_supabase)
except Exception as e:
    pass

from google.oauth2 import service_account
from googleapiclient.discovery import build

def crear_oficina_virtual(nombre_cliente, id_expediente, id_maestra):
    try:
        # Cargamos los secretos que pegamos en Streamlit
        info_llave = st.secrets["google_drive"]
        creds = service_account.Credentials.from_service_account_info(info_llave)
        drive_service = build('drive', 'v3', credentials=creds)

        nombre_carpeta = f"EXP-{id_expediente} | {nombre_cliente}"

        # 1. Crear Carpeta Principal
        meta_principal = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [id_maestra]
        }
        archivo = drive_service.files().create(body=meta_principal, fields='id, webViewLink').execute()
        folder_id = archivo.get('id')
        link_web = archivo.get('webViewLink')

        # 2. Crear las 3 Subcarpetas (Orden Diamante)
        subcarpetas = ["01_DOCUMENTOS_LEGALES", "02_PLANOS_Y_TECNICO", "03_RECIBOS_Y_PAGOS"]
        for sub in subcarpetas:
            meta_sub = {'name': sub, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [folder_id]}
            drive_service.files().create(body=meta_sub).execute()

        return link_web
    except Exception as e:
        st.error(f"Error en Drive: {e}")
        return None
def generar_paquete_documentos(datos_formulario, rutas_plantillas):
    import io
    
    # 1. El Mega Diccionario (Atrapa todo lo de la pantalla)
    contexto = dict(datos_formulario)
    contexto['profesional'] = "Lic. Jhonny Matos. M.A."
    contexto['cargo'] = "Presidente fundador AboAgrim"
    
    # 2. Si solo es un archivo, lo procesamos normal
    if len(rutas_plantillas) == 1:
        doc = DocxTemplate(rutas_plantillas[0])
        doc.render(contexto)
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer, f"Expediente_{contexto.get('nom_prop', 'AboAgrim')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # 3. Si son VARIOS archivos, creamos un archivo .ZIP con todos adentro
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for ruta in rutas_plantillas:
            doc = DocxTemplate(ruta)
            doc.render(contexto)
            
            temp_buffer = io.BytesIO()
            doc.save(temp_buffer)
            
            # Nombre del archivo procesado
            nombre_archivo = f"Listo_{os.path.basename(ruta)}"
            zip_file.writestr(nombre_archivo, temp_buffer.getvalue())
            
    zip_buffer.seek(0)
    return zip_buffer, f"Paquete_Expediente_{contexto.get('nom_prop', 'AboAgrim')}.zip", "application/zip"
# Asegúrese de que no haya nada repetido debajo de este bloque.
# =====================================================================
# MÓDULO 1: MANDO CENTRAL
# =====================================================================
def vista_mando():
    import streamlit as st
    import os
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    # --- ENCABEZADO CORPORATIVO ---
    with st.container(border=True):
        col_logo, col_titulo = st.columns([1, 4])
        
        with col_logo:
            import os
            
            # 🕵️‍♂️ EL CAZADOR DE LOGOS: Escanea la carpeta buscando su imagen
            archivo_encontrado = None
            try:
                # Revisa todos los archivos en la carpeta principal
                for archivo in os.listdir('.'): 
                    if "logo" in archivo.lower() and archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                        archivo_encontrado = archivo
                        break  # Si lo encuentra, detiene la búsqueda
            except Exception:
                pass
                
            # Si el cazador encontró la imagen, la muestra
            if archivo_encontrado:
                st.image(archivo_encontrado, use_container_width=True)
            elif st.session_state.get("logo_firma"):
                st.image(st.session_state["logo_firma"], use_container_width=True)
            else:
                # El escudo azul aparece si definitivamente no hay ningún archivo llamado "logo"
                st.markdown("<h1 style='text-align: center; font-size: 4.5rem; color: #1E3A8A;'>🛡️</h1>", unsafe_allow_html=True)
                
        with col_titulo:
            st.title(st.session_state.get("nombre_oficina", "AboAgrim Pro"))
            st.markdown("##### *Sistema Integrado de Gestión Legal y Topográfica*")
            st.caption(f"📍 {st.session_state.get('dir_oficina', 'Santiago')} | 📞 {st.session_state.get('tel_oficina', '829-826-5888')}")
            st.markdown("**Lic. Jhonny Matos. M.A.** - *Presidente Fundador*")

    st.write("")
    
    # --- 1. EXTRACCIÓN DE DATOS DESDE SUPABASE ---
    try:
        res = supabase.table("expedientes").select("*").execute()
        expedientes_db = res.data if res.data else []
    except Exception as e:
        expedientes_db = []
        st.error(f"Error de conexión con la matriz de datos: {e}")

    # Cálculos dinámicos
    total_exps = len(expedientes_db)
    total_clientes = sum(len(e.get("clientes", [])) for e in expedientes_db if isinstance(e.get("clientes"), list))
    total_inmuebles = sum(len(e.get("inmuebles", [])) for e in expedientes_db if isinstance(e.get("inmuebles"), list))

    # --- 2. MÉTRICAS DEL SISTEMA ---
    st.markdown("### 📊 Panel de Control y Estadísticas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.metric("📁 Expedientes Activos", total_exps)
    with col2:
        with st.container(border=True):
            st.metric("👤 Clientes Registrados", total_clientes)
    with col3:
        with st.container(border=True):
            st.metric("📍 Inmuebles Procesados", total_inmuebles)

    st.write("---")

    # --- 3. RECIENTES Y ACCESOS (DISEÑO COLAPSABLE) ---
    c_izq, c_der = st.columns([2, 1])
    
    with c_izq:
        # Panel desplegable para mantener el escritorio limpio
        with st.expander("⏱️ Últimos Casos Ingresados al Sistema", expanded=True):
            if total_exps > 0:
                # Ordenamos para mostrar los 5 más recientes
                ultimos_5 = sorted(expedientes_db, key=lambda x: x.get('fecha_creacion', ''), reverse=True)[:5]
                for caso in ultimos_5:
                    st.info(f"**{caso['id_expediente']}** | {caso.get('asunto', 'Sin asunto')} - *{caso.get('tipo_caso', '')}*")
            else:
                st.warning("No hay expedientes registrados aún en la bóveda de Supabase.")

    with c_der:
        # Menú de acciones rápidas organizado y discreto
        with st.expander("⚡ Panel de Acciones Rápidas", expanded=True):
            st.info("Navegue por el menú lateral para ejecutar estas operaciones:")
            st.button("➕ Crear Nuevo Caso", use_container_width=True, disabled=True, help="Vaya a 'Registro Maestro'")
            st.button("📄 Forjar Documento", use_container_width=True, disabled=True, help="Vaya a 'Plantillas Auto'")
            st.button("💸 Facturar Honorarios", use_container_width=True, disabled=True, help="Vaya a 'Gestión de Honorarios'")
# =====================================================================
# MÓDULO 2: REGISTRO MAESTRO (CON PESTAÑAS Y 7 ROLES)
# =====================================================================

# =====================================================================
# MÓDULO 3: ARCHIVO DIGITAL (BÓVEDA, EXPLORADOR Y DESCARGA ZIP)
# =====================================================================


# =====================================================================
# MÓDULO 4: PLANTILLAS Y LEY 108-05
# =====================================================================
def vista_registro_maestro():
    import streamlit as st
    from datetime import datetime
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("👤 Registro Maestro de Expedientes")
    st.markdown("### 🗃️ Creación y Actualización de Casos en la Nube")

    # --- 0. INICIALIZACIÓN DE MEMORIA DINÁMICA ---
    roles_rm = ["cant_cl_rm", "cant_ap_rm", "cant_ab_rm", "cant_ag_rm", "cant_no_rm", "cant_al_rm", "cant_in_rm", "cant_do_rm"]
    for rol in roles_rm:
        if rol not in st.session_state:
            st.session_state[rol] = 1

    def mod_cant_rm(rol, operacion):
        if operacion == "add":
            st.session_state[rol] += 1
        elif operacion == "del" and st.session_state[rol] > 0:
            st.session_state[rol] -= 1

    # --- 1. EXTRACCIÓN DE DATOS DESDE SUPABASE ---
    try:
        respuesta_db = supabase.table("expedientes").select("*").execute()
        datos_nube = respuesta_db.data if respuesta_db.data else []
    except Exception as e:
        datos_nube = []
        st.error(f"Error al conectar con la base de datos: {e}")

    # --- 🤖 MOTOR DE AUTONUMERACIÓN INTELIGENTE (AHORA CONECTADO A LA NUBE) ---
    año_actual = datetime.now().year
    numeros_este_año = []
    
    for exp_data in datos_nube:
        id_exp = exp_data.get('id_expediente', '')
        if id_exp.startswith(f"{año_actual}-"):
            try:
                numero = int(id_exp.split("-")[1])
                numeros_este_año.append(numero)
            except:
                pass
                
    siguiente_numero = max(numeros_este_año) + 1 if numeros_este_año else 1001
    numero_sugerido = f"{año_actual}-{siguiente_numero:04d}"

    # --- 2. PANEL SUPERIOR: BÚSQUEDA Y CONTROL ---
    with st.expander("🔍 Buscador y Carga de Expedientes Existentes", expanded=False):
        col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
        exp_buscar = col_b1.text_input("📁 Buscar por Número de Expediente:", placeholder="Ej. 2026-1001")
        
        if col_b2.button("🔎 Buscar y Cargar", use_container_width=True):
            if exp_buscar:
                # Buscamos en los datos que ya descargamos de la nube
                exp_encontrado = next((item for item in datos_nube if item["id_expediente"] == exp_buscar), None)
                
                if exp_encontrado:
                    st.session_state["exp_cargado"] = exp_encontrado
                    # Ajustamos los contadores dinámicos
                    st.session_state["cant_cl_rm"] = len(exp_encontrado.get("clientes", [])) or 1
                    st.session_state["cant_ap_rm"] = len(exp_encontrado.get("apoderados", [])) or 1
                    st.session_state["cant_ab_rm"] = len(exp_encontrado.get("abogados", [])) or 1
                    st.session_state["cant_ag_rm"] = len(exp_encontrado.get("agrimensores", [])) or 1
                    st.session_state["cant_in_rm"] = len(exp_encontrado.get("inmuebles", [])) or 1
                    st.session_state["cant_do_rm"] = len(exp_encontrado.get("documentos", [])) or 1
                    
                    st.success(f"✅ Expediente {exp_buscar} cargado con éxito.")
                    st.rerun()
                else:
                    st.warning(f"⚠️ El expediente {exp_buscar} no existe en la nube.")

        if col_b3.button("🧹 Limpiar Formulario", use_container_width=True):
            st.session_state.pop("exp_cargado", None)
            st.rerun()

    # --- CARGA DE DATOS AL FORMULARIO ---
    expediente_actual = st.session_state.get("exp_cargado", {})
    
    st.write("---")
    
    # --- 3. PANEL CENTRAL DE TRABAJO (PESTAÑAS HORIZONTALES) ---
    st.markdown("### 📝 Formulario de Edición del Expediente")
    
    tab_gen, tab_partes, tab_prof, tab_inm, tab_docs = st.tabs([
        "📋 Datos Generales", 
        "👥 Partes y Apoderados", 
        "⚖️ Profesionales", 
        "📍 Inmuebles", 
        "📄 Actuaciones"
    ])

    with tab_gen:
        st.write("Defina la estructura principal del caso.")
        col_e1, col_e2 = st.columns([1, 2])
        num_expediente = col_e1.text_input("📁 Número de Expediente:", value=expediente_actual.get("id_expediente", numero_sugerido))
        asunto = col_e2.text_input("📌 Asunto o Referencia del Caso:", value=expediente_actual.get("asunto", ""))
        
        col_e3, col_e4 = st.columns(2)
        opciones_tipo_caso = ["Deslinde", "Saneamiento", "Mensura Catastral", "Litis sobre Derechos Registrados", "Determinación de Herederos", "Transferencia / Venta", "Hipotecas / Privilegios", "Civil Ordinario", "Otro"]
        tipo_caso_guardado = expediente_actual.get("tipo_caso", "Deslinde")
        idx_tipo = opciones_tipo_caso.index(tipo_caso_guardado) if tipo_caso_guardado in opciones_tipo_caso else 0
        tipo_caso = col_e3.selectbox("⚙️ Tipo de Proceso (Fábrica de Plantillas):", opciones_tipo_caso, index=idx_tipo)

        opciones_organo = ["Dirección Regional de Mensuras Catastrales", "Registro de Títulos", "Tribunal de Jurisdicción Original", "Tribunal Superior de Tierras", "Corte de Apelación", "Juzgado de Paz", "Cámara Civil y Comercial", "Administrativo / Interno"]
        organo_guardado = expediente_actual.get("organo_jurisdiccional", "Dirección Regional de Mensuras Catastrales")
        idx_organo = opciones_organo.index(organo_guardado) if organo_guardado in opciones_organo else 0
        organo_jurisdiccional = col_e4.selectbox("🏛️ Órgano Jurisdiccional / Entidad:", opciones_organo, index=idx_organo)

    with tab_partes:
        st.write("Registre a los reclamantes, solicitantes y sus representantes legales.")
        col_cli, col_apo = st.columns(2)
        
        with col_cli:
            st.markdown("#### 👤 Clientes / Propietarios")
            c_btn1, c_btn2 = st.columns(2)
            c_btn1.button("➕ Agregar", on_click=mod_cant_rm, args=("cant_cl_rm", "add"), key="rm_add_cl", use_container_width=True)
            c_btn2.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_cl_rm", "del"), key="rm_del_cl", use_container_width=True)
            lista_clientes = []
            clientes_data = expediente_actual.get("clientes", [])
            for i in range(st.session_state["cant_cl_rm"]):
                cd = clientes_data[i] if i < len(clientes_data) else {}
                with st.container(border=True):
                    n = st.text_input(f"Nombre (Cliente {i+1}):", value=cd.get("nombre", ""), key=f"rm_cl_n_{i}")
                    c = st.text_input(f"Cédula:", value=cd.get("cedula", ""), key=f"rm_cl_c_{i}")
                    t = st.text_input(f"Teléfono:", value=cd.get("telefono", ""), key=f"rm_cl_t_{i}")
                    d = st.text_input(f"Domicilio:", value=cd.get("domicilio", ""), key=f"rm_cl_d_{i}")
                    e = st.text_input(f"Email:", value=cd.get("email", ""), key=f"rm_cl_e_{i}")
                    if n: lista_clientes.append({"nombre": n, "cedula": c, "telefono": t, "domicilio": d, "email": e})

        with col_apo:
            st.markdown("#### 🤝 Apoderados")
            c_btn1, c_btn2 = st.columns(2)
            c_btn1.button("➕ Agregar", on_click=mod_cant_rm, args=("cant_ap_rm", "add"), key="rm_add_ap", use_container_width=True)
            c_btn2.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_ap_rm", "del"), key="rm_del_ap", use_container_width=True)
            lista_apoderados = []
            apoderados_data = expediente_actual.get("apoderados", [])
            for i in range(st.session_state["cant_ap_rm"]):
                ad = apoderados_data[i] if i < len(apoderados_data) else {}
                with st.container(border=True):
                    n = st.text_input(f"Nombre (Apoderado {i+1}):", value=ad.get("nombre", ""), key=f"rm_ap_n_{i}")
                    c = st.text_input(f"Cédula:", value=ad.get("cedula", ""), key=f"rm_ap_c_{i}")
                    q = st.text_input(f"Calidad:", value=ad.get("calidad", ""), key=f"rm_ap_q_{i}")
                    d = st.text_input(f"Domicilio:", value=ad.get("domicilio", ""), key=f"rm_ap_d_{i}")
                    te = st.text_input(f"Contacto:", value=ad.get("contacto", ""), key=f"rm_ap_te_{i}")
                    if n: lista_apoderados.append({"nombre": n, "cedula": c, "calidad": q, "domicilio": d, "contacto": te})

    with tab_prof:
        st.write("Agregue el equipo técnico y legal.")
        sub_tab_ab, sub_tab_ag, sub_tab_no, sub_tab_al = st.tabs(["Abogados", "Agrimensores", "Notarios", "Alguaciles"])
        
        with sub_tab_ab:
            st.button("➕ Abogado", on_click=mod_cant_rm, args=("cant_ab_rm", "add"), key="rm_add_ab")
            st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_ab_rm", "del"), key="rm_del_ab")
            lista_abogados = []
            abogados_data = expediente_actual.get("abogados", [])
            for i in range(st.session_state["cant_ab_rm"]):
                abd = abogados_data[i] if i < len(abogados_data) else {}
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre:", value=abd.get("nombre", ""), key=f"rm_ab_n_{i}")
                c = c2.text_input("Cédula:", value=abd.get("cedula", ""), key=f"rm_ab_c_{i}")
                m = c3.text_input("CARD:", value=abd.get("matricula", ""), key=f"rm_ab_m_{i}")
                c4, c5, c6 = st.columns(3)
                d = c4.text_input("Domicilio:", value=abd.get("domicilio", ""), key=f"rm_ab_d_{i}")
                t = c5.text_input("Teléfono:", value=abd.get("telefono", ""), key=f"rm_ab_t_{i}")
                e = c6.text_input("Email:", value=abd.get("email", ""), key=f"rm_ab_e_{i}")
                if n: lista_abogados.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": e})

        with sub_tab_ag:
            st.button("➕ Agrimensor", on_click=mod_cant_rm, args=("cant_ag_rm", "add"), key="rm_add_ag")
            st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_ag_rm", "del"), key="rm_del_ag")
            lista_agrimensores = []
            agrimensores_data = expediente_actual.get("agrimensores", [])
            for i in range(st.session_state["cant_ag_rm"]):
                agd = agrimensores_data[i] if i < len(agrimensores_data) else {}
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre:", value=agd.get("nombre", ""), key=f"rm_ag_n_{i}")
                c = c2.text_input("Cédula:", value=agd.get("cedula", ""), key=f"rm_ag_c_{i}")
                m = c3.text_input("CODIA:", value=agd.get("matricula", ""), key=f"rm_ag_m_{i}")
                c4, c5, c6 = st.columns(3)
                d = c4.text_input("Oficina:", value=agd.get("domicilio", ""), key=f"rm_ag_d_{i}")
                t = c5.text_input("Teléfono:", value=agd.get("telefono", ""), key=f"rm_ag_t_{i}")
                e = c6.text_input("Email:", value=agd.get("email", ""), key=f"rm_ag_e_{i}")
                if n: lista_agrimensores.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": e})

        with sub_tab_no:
            st.button("➕ Notario", on_click=mod_cant_rm, args=("cant_no_rm", "add"), key="rm_add_no")
            st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_no_rm", "del"), key="rm_del_no")
            lista_notarios = []
            notarios_data = expediente_actual.get("notarios", [])
            for i in range(st.session_state["cant_no_rm"]):
                nd = notarios_data[i] if i < len(notarios_data) else {}
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre:", value=nd.get("nombre", ""), key=f"rm_no_n_{i}")
                c = c2.text_input("Cédula:", value=nd.get("cedula", ""), key=f"rm_no_c_{i}")
                m = c3.text_input("Matrícula:", value=nd.get("matricula", ""), key=f"rm_no_m_{i}")
                if n: lista_notarios.append({"nombre": n, "cedula": c, "matricula": m})

        with sub_tab_al:
            st.button("➕ Alguacil", on_click=mod_cant_rm, args=("cant_al_rm", "add"), key="rm_add_al")
            st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_al_rm", "del"), key="rm_del_al")
            lista_alguaciles = []
            alguaciles_data = expediente_actual.get("alguaciles", [])
            for i in range(st.session_state["cant_al_rm"]):
                ald = alguaciles_data[i] if i < len(alguaciles_data) else {}
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre:", value=ald.get("nombre", ""), key=f"rm_al_n_{i}")
                c = c2.text_input("Cédula:", value=ald.get("cedula", ""), key=f"rm_al_c_{i}")
                m = c3.text_input("Tribunal:", value=ald.get("matricula", ""), key=f"rm_al_m_{i}")
                if n: lista_alguaciles.append({"nombre": n, "cedula": c, "matricula": m})

    with tab_inm:
        st.write("Identifique las propiedades en litis o mensura.")
        st.button("➕ Inmueble", on_click=mod_cant_rm, args=("cant_in_rm", "add"), key="rm_add_in")
        st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_in_rm", "del"), key="rm_del_in")
        lista_inmuebles = []
        inmuebles_data = expediente_actual.get("inmuebles", [])
        for i in range(st.session_state["cant_in_rm"]):
            ind = inmuebles_data[i] if i < len(inmuebles_data) else {}
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                p = c1.text_input("Parcela/Solar:", value=ind.get("parcela", ""), key=f"rm_in_p_{i}")
                dc = c2.text_input("DC / Municipio:", value=ind.get("dc", ""), key=f"rm_in_dc_{i}")
                prov = c3.text_input("Provincia:", value=ind.get("provincia", ""), key=f"rm_in_prov_{i}")
                
                c4, c5, c6 = st.columns(3)
                coord = c4.text_input("Coordenadas:", value=ind.get("coordenadas", ""), key=f"rm_in_co_{i}")
                sup = c5.text_input("Superficie:", value=ind.get("superficie", ""), key=f"rm_in_sup_{i}")
                
                opciones_tdoc = ["Certificado de Título", "Constancia Anotada", "Acto de Venta", "Otro"]
                tdoc_guardado = ind.get("tipo_doc", "Certificado de Título")
                tdoc_idx = opciones_tdoc.index(tdoc_guardado) if tdoc_guardado in opciones_tdoc else 0
                tdoc = c6.selectbox("Tipo Doc:", opciones_tdoc, index=tdoc_idx, key=f"rm_in_td_{i}")
                
                c7, c8, c9, c10 = st.columns(4)
                num = c7.text_input("Matrícula/No.:", value=ind.get("numero", ""), key=f"rm_in_n_{i}")
                lib = c8.text_input("Libro:", value=ind.get("libro", ""), key=f"rm_in_l_{i}")
                fol = c9.text_input("Folio:", value=ind.get("folio", ""), key=f"rm_in_f_{i}")
                f_ins = c10.text_input("Fecha Inscr.:", value=ind.get("fecha_ins", ""), key=f"rm_in_fi_{i}")
                
                if p: lista_inmuebles.append({"parcela": p, "dc": dc, "provincia": prov, "coordenadas": coord, "superficie": sup, "tipo_doc": tdoc, "numero": num, "libro": lib, "folio": fol, "fecha_ins": f_ins})

    with tab_docs:
        st.write("Historial de actuaciones legales y depósitos técnicos.")
        st.button("➕ Documento", on_click=mod_cant_rm, args=("cant_do_rm", "add"), key="rm_add_do")
        st.button("➖ Quitar", on_click=mod_cant_rm, args=("cant_do_rm", "del"), key="rm_del_do")
        lista_documentos = []
        docs_data = expediente_actual.get("documentos", [])
        for i in range(st.session_state["cant_do_rm"]):
            dod = docs_data[i] if i < len(docs_data) else {}
            c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
            
            opciones_clasif = ["Acto", "Acta", "Instancia", "Solicitud", "Informe", "Demanda", "Carta", "Notificación", "Otro"]
            clasif_guardada = dod.get("tipo", "Acto")
            clasif_idx = opciones_clasif.index(clasif_guardada) if clasif_guardada in opciones_clasif else 0
            tipo_d = c1.selectbox("Clasificación:", opciones_clasif, index=clasif_idx, key=f"rm_do_t_{i}")
            
            desc_d = c2.text_input("Descripción:", value=dod.get("descripcion", ""), key=f"rm_do_d_{i}")
            
            fecha_guardada = dod.get("fecha", "")
            try:
                fecha_obj = datetime.strptime(fecha_guardada, "%Y-%m-%d").date() if fecha_guardada else datetime.today().date()
            except ValueError:
                fecha_obj = datetime.today().date()
                
            fecha_d = c3.date_input("Fecha:", value=fecha_obj, key=f"rm_do_f_{i}")
            
            opciones_estado = ["Redactado", "Depositado", "Notificado", "Aprobado", "Rechazado"]
            estado_guardado = dod.get("estado", "Redactado")
            estado_idx = opciones_estado.index(estado_guardado) if estado_guardado in opciones_estado else 0
            estado_d = c4.selectbox("Estado:", opciones_estado, index=estado_idx, key=f"rm_do_e_{i}")
            
            if desc_d: lista_documentos.append({"tipo": tipo_d, "descripcion": desc_d, "fecha": str(fecha_d), "estado": estado_d})

    st.write("---")
    
    # 🚀 --- INTEGRACIÓN CON SUPABASE: GUARDAR --- 🚀
    if st.button("💾 Guardar Expediente en la Nube", type="primary", use_container_width=True):
        if num_expediente and asunto:
            datos_expediente = {
                "id_expediente": num_expediente, 
                "asunto": asunto,
                "tipo_caso": tipo_caso,                     
                "organo_jurisdiccional": organo_jurisdiccional, 
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                "clientes": lista_clientes,
                "apoderados": lista_apoderados,
                "abogados": lista_abogados,
                "agrimensores": lista_agrimensores,
                "notarios": lista_notarios,
                "alguaciles": lista_alguaciles,
                "inmuebles": lista_inmuebles,
                "documentos": lista_documentos
            }
            
            try:
                supabase.table("expedientes").upsert(datos_expediente).execute()
                st.success(f"✅ ¡Expediente {num_expediente} ({tipo_caso}) guardado en la base de datos maestra!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al conectar con Supabase. Detalle técnico: {e}")
        else:
            st.error("⚠️ Debe indicar al menos el Número de Expediente y el Asunto para poder guardar.")
    
    st.write("---")
    
    # --- 4. PANEL INFERIOR: ARCHIVO Y GESTIÓN ---
    with st.expander("🗄️ Ver Expedientes Guardados en la Nube", expanded=False):
        if datos_nube:
            for idx, exp_data in enumerate(datos_nube):
                exp_num = exp_data.get('id_expediente', 'Sin ID')
                with st.container(border=True):
                    col_d1, col_d2, col_d3, col_d4 = st.columns([2, 1, 1, 1])
                    col_d1.markdown(f"**{exp_num}** | {exp_data.get('asunto', '')}")
                    col_d2.caption(f"Registro: {exp_data.get('fecha_creacion', '')}")
                    col_d3.caption(f"Partes: {len(exp_data.get('clientes', []))} | Inmuebles: {len(exp_data.get('inmuebles', []))}")
                    
                    if col_d4.button("🗑️ Eliminar", key=f"del_exp_{exp_num}_{idx}", use_container_width=True):
                        supabase.table("expedientes").delete().eq("id_expediente", exp_num).execute()
                        st.rerun()
        else:
            st.info("La base de datos está limpia. Registre su primer expediente en el formulario.")
# =====================================================================
# MÓDULO 5: ALERTAS Y PLAZOS
# =====================================================================

def vista_alertas_plazos():
    import streamlit as st
    from datetime import datetime
    from database import db as supabase  # ☁️ Conexión a la nube

    st.title("📅 Radar de Alertas y Plazos")
    st.subheader("Control Normativo Inteligente | AboAgrim Pro")
    
    st.info("💡 Este radar lee automáticamente las fechas de vencimiento generadas por la Fábrica de Documentos al forjar instancias y contratos.")

    if st.button("🚀 Escanear Plazos en la Nube", type="primary", use_container_width=True):
        
        try:
            # 1. Descargamos todos los expedientes de la nube
            res = supabase.table("expedientes").select("id_expediente, asunto, alertas").execute()
            expedientes = res.data if res.data else []
            
            alertas_rojas = []
            alertas_amarillas = []
            alertas_verdes = []
            
            hoy = datetime.now().date()
            
            # 2. Clasificamos las alertas en el semáforo
            for exp in expedientes:
                lista_alertas = exp.get("alertas")
                if lista_alertas and isinstance(lista_alertas, list):
                    for alerta in lista_alertas:
                        if alerta.get("estado") != "Completado": # Ignoramos las ya resueltas
                            fv_str = alerta.get("fecha_vencimiento")
                            if fv_str:
                                try:
                                    fv = datetime.strptime(fv_str, "%Y-%m-%d").date()
                                    dias_restantes = (fv - hoy).days
                                    
                                    # Empaquetamos los datos para mostrarlos bonito
                                    datos_alerta = {
                                        "exp": exp["id_expediente"],
                                        "asunto": exp["asunto"],
                                        "doc": alerta["documento_origen"],
                                        "desc": alerta["descripcion"],
                                        "vence": fv_str,
                                        "dias": dias_restantes
                                    }
                                    
                                    # Lógica del semáforo
                                    if dias_restantes <= 5:     # 0 a 5 días (Rojo)
                                        alertas_rojas.append(datos_alerta)
                                    elif dias_restantes <= 20:  # 6 a 20 días (Amarillo)
                                        alertas_amarillas.append(datos_alerta)
                                    else:                       # Más de 20 días (Verde)
                                        alertas_verdes.append(datos_alerta)
                                except Exception:
                                    pass # Si hay error en una fecha, la saltamos

            # 3. DIBUJAMOS EL DASHBOARD VISUAL
            st.write("---")
            st.markdown("### 🚦 Tablero de Control de Vencimientos")
            
            col_r, col_a, col_v = st.columns(3)
            with col_r:
                st.error(f"🔴 CRÍTICO: {len(alertas_rojas)}")
            with col_a:
                st.warning(f"🟡 PRÓXIMOS: {len(alertas_amarillas)}")
            with col_v:
                st.success(f"🟢 A TIEMPO: {len(alertas_verdes)}")
                
            st.write("---")
            
            # --- ZONA ROJA ---
            if alertas_rojas:
                st.subheader("🚨 Plazos Críticos (Vencen en menos de 5 días o vencidos)")
                # Ordenamos de menor a mayor (los más atrasados primero)
                alertas_rojas = sorted(alertas_rojas, key=lambda x: x["dias"])
                for a in alertas_rojas:
                    with st.container(border=True):
                        st.markdown(f"**Expediente:** {a['exp']} - {a['asunto']}")
                        st.markdown(f"**Alerta:** {a['desc']} *(Doc: {a['doc']})*")
                        if a['dias'] < 0:
                            st.error(f"⚠️ VENCIDO HACE {abs(a['dias'])} DÍAS (Límite: {a['vence']})")
                        else:
                            st.error(f"⏳ Vence en {a['dias']} días (Límite: {a['vence']})")

            # --- ZONA AMARILLA ---
            if alertas_amarillas:
                st.subheader("⚠️ Atención Próxima (Vencen entre 6 y 20 días)")
                alertas_amarillas = sorted(alertas_amarillas, key=lambda x: x["dias"])
                for a in alertas_amarillas:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**{a['exp']}** | {a['desc']}")
                        c1.caption(f"Trámite: {a['doc']}")
                        c2.warning(f"Faltan {a['dias']} días\n({a['vence']})")

            # --- ZONA VERDE ---
            if alertas_verdes:
                with st.expander(f"✅ Plazos Cómodos y a Tiempo ({len(alertas_verdes)} expedientes)", expanded=False):
                    alertas_verdes = sorted(alertas_verdes, key=lambda x: x["dias"])
                    for a in alertas_verdes:
                        st.markdown(f"🟢 **{a['exp']}**: {a['desc']} *(Vence en {a['dias']} días)*")

            if not alertas_rojas and not alertas_amarillas and not alertas_verdes:
                st.info("No hay alertas activas en el sistema. Todo está al día.")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error al conectar con la bóveda de alertas: {e}")
            
    else:
        # Pantalla en espera si no se ha hecho clic en el botón
        st.write("")
        st.write("")
            
def vista_configuracion():
    import streamlit as st
    import pandas as pd
    from database import db as supabase
    
    st.title("⚙️ Panel de Control Maestro")
    
    if st.session_state.get("admin_autenticado", False):
        tab_perfil, tab_usuarios, tab_sistema = st.tabs(["👤 Mi Perfil", "👥 Gestión de Personal", "🛠️ Base de Datos"])
        
        # --- TAB 1: PERFIL PROFESIONAL ---
        with tab_perfil:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                c1.markdown("## ⚖️")
                c2.markdown(f"### {st.session_state.get('usuario', 'Lic. Jhonny Matos')}")
                c2.caption(f"**Cargo:** {st.session_state.get('rol', 'Presidente Fundador')}")
                
                st.divider()
                st.markdown("**Información de Contacto Institucional:**")
                st.write("📧 **Email:** Aboagrim@gmail.com")
                st.write("📞 **Teléfonos:** 829-826-5888 | 809-691-3333")
                st.write("📍 **Oficina:** Calle Boy Scout 83, Plaza Jasansa, Santiago.")
        
        # === 2. PESTAÑA DE USUARIOS (CONECTADA A SUPABASE) ===
        with tab_usuarios:
            st.subheader("👥 Gestión de Capital Humano y Permisos")
            st.write("Administre los niveles de acceso y roles oficiales de la firma.")

            # --- SECCIÓN A: LISTA OFICIAL DE PERSONAL ---
            st.markdown("### 📋 Directorio de Usuarios (Base de Datos)")
            
            try:
                # Descargamos los usuarios directamente de la nube
                res_usuarios = supabase.table("usuarios").select("*").execute()
                usuarios_db = res_usuarios.data
            except Exception as e:
                st.error(f"Error conectando a la base de datos: {e}")
                usuarios_db = []
                
            if usuarios_db:
                df_usuarios = pd.DataFrame(usuarios_db)
                # Filtramos las columnas para que se vea limpio
                cols_mostrar = [col for col in ["nombre_usuario", "rol", "pin_acceso", "fecha_creacion"] if col in df_usuarios.columns]
                st.dataframe(df_usuarios[cols_mostrar], use_container_width=True)
            else:
                st.info("Aún no hay usuarios registrados en el sistema.")

            st.divider()

            # --- SECCIÓN B: REGISTRO DE NUEVO TALENTO ---
            with st.expander("➕ Dar de Alta a Nuevo Miembro del Equipo", expanded=False):
                c_u1, c_u2 = st.columns(2)
                with c_u1:
                    nuevo_user = st.text_input("Nombre de Usuario (Login):", placeholder="Ej. PAlmonte")
                    nueva_clave = st.text_input("PIN / Contraseña de Acceso:", type="password")
                with c_u2:
                    nuevo_rol = st.selectbox("Rol en el Sistema:", [
                        "Presidente Fundador",
                        "Abogado", 
                        "Agrimensor", 
                        "Asistente", 
                        "Pasante",
                        "Contabilidad"
                    ])

                if st.button("💾 Guardar Usuario en la Nube", use_container_width=True):
                    if nuevo_user and nueva_clave:
                        try:
                            # Inyectamos en las columnas exactas que usted creó
                            supabase.table("usuarios").insert({
                                "nombre_usuario": nuevo_user,
                                "pin_acceso": nueva_clave,
                                "rol": nuevo_rol
                            }).execute()
                            st.success(f"✅ ¡Usuario {nuevo_user} creado exitosamente y guardado de forma permanente!")
                            st.rerun() # Refresca la pantalla para mostrarlo en la tabla
                        except Exception as e:
                            st.error(f"Error al guardar el usuario: {e}")
                    else:
                        st.warning("⚠️ Debe llenar el usuario y la contraseña para continuar.")

            st.divider()
            
            # --- SECCIÓN C: GESTIÓN Y BAJAS (NUEVO) ---
            if usuarios_db:
                st.markdown("### 🗑️ Dar de Baja (Eliminar Usuario)")
                # Filtramos para que usted nunca pueda borrarse a sí mismo por accidente
                lista_nombres = [u["nombre_usuario"] for u in usuarios_db if u["nombre_usuario"] != "JhonnyMatos"]
                
                if lista_nombres:
                    c_del1, c_del2 = st.columns([3, 1])
                    usuario_a_borrar = c_del1.selectbox("Seleccione el usuario que desea eliminar del sistema:", lista_nombres)
                    
                    if c_del2.button("🚨 Eliminar Acceso", type="primary"):
                        try:
                            supabase.table("usuarios").delete().eq("nombre_usuario", usuario_a_borrar).execute()
                            st.success(f"🗑️ El usuario {usuario_a_borrar} ha sido eliminado permanentemente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al intentar eliminar: {e}")
                else:
                    st.info("No hay usuarios adicionales para eliminar.")

            st.divider()

            # --- SECCIÓN D: MATRIZ DE PERMISOS (Visual) ---
            st.markdown("### 🔐 Matriz de Acceso por Módulo")
            st.info("Configure qué módulos son visibles para cada rol. (Blindaje de Seguridad)")
            
            col_perm1, col_perm2 = st.columns(2)
            with col_perm1:
                st.markdown("**📂 Gestión de Expedientes**")
                p_abog = st.checkbox("Abogados", value=True)
                p_agrim = st.checkbox("Agrimensores", value=True)
                p_pasant = st.checkbox("Pasantes", value=False)
                
                st.markdown("**💰 Gestión de Honorarios (Finanzas)**")
                f_abog = st.checkbox("Abogados (Solo ver)", value=True)
                f_cont = st.checkbox("Contabilidad (Acceso Total)", value=True)
                f_pasant = st.checkbox("Pasantes (Acceso Denegado)", value=False, disabled=True)

            with col_perm2:
                st.markdown("**📄 Fábrica de Documentos**")
                d_abog = st.checkbox("Acceso Abogados", value=True)
                d_agrim = st.checkbox("Acceso Agrimensores", value=True)
                
                st.markdown("**⚙️ Configuración del Sistema**")
                c_master = st.checkbox("Solo Presidente (Blindaje Activo)", value=True, disabled=True)
                
            if st.button("🔄 Actualizar Matriz de Blindaje"):
                st.warning("Los permisos han sido actualizados. Los usuarios verán los cambios en su próximo inicio de sesión.")

        # --- TAB 3: ESTADO DE LA BASE DE DATOS ---
        with tab_sistema:
            st.subheader("Estado de la Nube (Supabase)")
            
            try:
                res_exp = supabase.table("expedientes").select("id_expediente", count="exact").execute()
                count_exp = res_exp.count if res_exp.count else 0
                
                res_doc = supabase.table("archivo_digital").select("id", count="exact").execute()
                count_doc = res_doc.count if res_doc.count else 0
            except:
                count_exp, count_doc = 0, 0

            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Expedientes", count_exp)
            col_s1.caption("Total de casos en nube")
            
            col_s2.metric("Documentos", count_doc)
            col_s2.caption("Archivos vinculados")
            
            col_s3.metric("Estado", "Online", delta="Conectado")
            
            st.divider()
            st.info("💡 La base de datos está sincronizada con Supabase Cloud. Los respaldos se realizan cada 24 horas automáticamente.")

        st.divider()
        if st.button("🚪 Cerrar Sesión del Sistema"):
            st.session_state.admin_autenticado = False
            st.rerun()

    else:
        # LOGIN (Para cuando no está autenticado en la configuración)
        st.markdown("### 🔑 Autenticación Requerida")
        u = st.text_input("Usuario Master:")
        p = st.text_input("PIN de Seguridad:", type="password")
        
        if st.button("Desbloquear Panel"):
            if u == "JhonnyMatos" and p == "0681":
                st.session_state.admin_autenticado = True
                st.session_state.usuario = "Jhonny Matos"
                st.session_state.rol = "Presidente Fundador"
                st.rerun()
            else:
                st.error("Credenciales inválidas.")
            # Nota: Esto se complementa con CSS personalizado en el inicio del script
        # Aquí va la función de agregar/borrar usuarios...
def login_sistema():
    st.markdown("""
        <style>
        .login-box {
            background-color: #f0f2f6;
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #1E3A8A;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.image("https://vuestra-url-logo.com/logo.png", width=200) # Si tiene logo
        st.header("🔐 Acceso AboAgrim Pro")
        
        u_ingreso = st.text_input("Nombre de Usuario:")
        p_ingreso = st.text_input("PIN de Seguridad:", type="password", max_chars=4)
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            # Buscamos en la tabla de usuarios que ya creamos en Supabase
            res = supabase.table("usuarios_sistema").select("*").eq("nombre_usuario", u_ingreso).eq("pin_acceso", p_ingreso).eq("estado", "Activo").execute()
            
            if res.data:
                st.session_state.autenticado_global = True
                st.session_state.usuario_actual = u_ingreso
                st.success(f"Bienvenido, {u_ingreso}")
                st.rerun()
            else:
                st.error("Usuario o PIN incorrectos, o cuenta inactiva.")

def vista_archivo_digital():
    import streamlit as st
    import os
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("🗄️ Archivo Digital y Bóveda")
    st.markdown("### Repositorio Central de Expedientes y Anexos Técnicos")
    
    # --- 1. SINCRONIZACIÓN MAESTRA CON SUPABASE ---
    try:
        res = supabase.table("expedientes").select("*").execute()
        db_expedientes_cloud = {row['id_expediente']: row for row in res.data}
    except Exception as e:
        st.error(f"Error al conectar con la bóveda en la nube: {e}")
        return

    if not db_expedientes_cloud:
        st.info("ℹ️ El Archivo Digital está esperando datos. Registre un caso en el 'Registro Maestro' primero para que aparezca aquí.")
        return

    st.write("---")

    # --- 2. BUSCADOR INTELIGENTE INTERCONECTADO ---
    lista_exps = list(db_expedientes_cloud.keys())
    
    col_busq1, col_busq2 = st.columns([3, 1])
    with col_busq1:
        exp_seleccionado = st.selectbox("🔍 Buscar y Seleccionar Expediente:", lista_exps)
    
    # Extraemos los datos que usted llenó en el Registro Maestro desde la nube
    datos_exp = db_expedientes_cloud[exp_seleccionado]

    # 🚀 EL TRUCO: Reconstruimos la ruta exacta que usa la Fábrica de Documentos
    tipo_caso_db = datos_exp.get("tipo_caso", "Proceso Legal General")
    tipo_folder = tipo_caso_db.replace("/", "-").replace(" ", "_")
    
    # Sacamos el año de la fecha de creación
    fecha_creacion = datos_exp.get("fecha_creacion", "2026-01-01")
    año_creacion = fecha_creacion.split("-")[0] if "-" in fecha_creacion else "2026"

    # Ahora sí, el Archivo Digital y las Plantillas apuntan al MISMO almacén
    ruta_exp = f"boveda_digital/Expedientes_{año_creacion}/{tipo_folder}/{exp_seleccionado}"

    # Crear estructura física de la bóveda si no existe
    if not os.path.exists(ruta_exp):
        os.makedirs(ruta_exp)

    # --- 3. INTERFAZ DE GESTIÓN DOCUMENTAL ---
    tab_resumen, tab_anexos, tab_zip = st.tabs([
        "📋 Resumen del Caso", "📎 Subir Anexos (Planos, PDF)", "📦 Empaquetar Expediente"
    ])

    # PESTAÑA A: Visor de Memoria
    with tab_resumen:
        st.subheader(f"Radiografía: {exp_seleccionado}")
        st.markdown(f"**Proceso Legal:** {tipo_caso_db}")
        st.markdown(f"**Jurisdicción:** {datos_exp.get('organo_jurisdiccional', 'No especificada')}")
        
        clientes = datos_exp.get("clientes", [])
        nombres_cli = ", ".join([c.get("nombre", "") for c in clientes]) if clientes else "No registrado"
        st.markdown(f"**Clientes / Propietarios:** {nombres_cli}")
            
        st.info("💡 Este módulo lee en tiempo real los datos blindados en Supabase.")

    # PESTAÑA B: Bóveda de Anexos
    with tab_anexos:
        st.subheader("Bóveda de Anexos Físicos y Planos")
        st.write("Suba aquí copias de cédulas, planos topográficos (DWG), sentencias y actos firmados.")
        
        archivos_subidos = st.file_uploader(f"Anexar a {exp_seleccionado}", accept_multiple_files=True, help="Puede subir PDF, JPG, DWG, DOCX...")
        
        if archivos_subidos:
            if st.button("💾 Guardar Anexos en Bóveda", type="primary"):
                for archivo in archivos_subidos:
                    with open(os.path.join(ruta_exp, archivo.name), "wb") as f:
                        f.write(archivo.getbuffer())
                st.success(f"✅ {len(archivos_subidos)} documento(s) guardado(s) junto a los Word generados.")
                st.rerun()
        
        # Listador de documentos anexos con opción a borrar
        st.write("---")
        st.markdown(f"**Documentos actualmente unificados en la carpeta del caso:**")
        st.caption(f"📁 Ruta: `{ruta_exp}`")
        archivos_guardados = os.listdir(ruta_exp)
        
        if archivos_guardados:
            for arch in archivos_guardados:
                col_file, col_del = st.columns([4, 1])
                col_file.markdown(f"📄 `{arch}`")
                if col_del.button("❌ Borrar", key=f"del_{exp_seleccionado}_{arch}"):
                    os.remove(os.path.join(ruta_exp, arch))
                    st.rerun()
        else:
            st.caption("No hay documentos anexos todavía.")

    # PESTAÑA C: Empaquetado para el Tribunal
    with tab_zip:
        st.subheader("Preparación para Depósito / Entrega")
        st.write("Genere un archivo comprimido (.zip) con TODO el contenido (Las instancias Word forjadas + Los PDF/Planos anexados).")
        
        if st.button("📦 Empaquetar Todo en ZIP", use_container_width=True):
            if not os.listdir(ruta_exp):
                st.warning("⚠️ El expediente no tiene documentos para empaquetar.")
            else:
                import io
                import zipfile
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(ruta_exp):
                        for file in files:
                            ruta_completa = os.path.join(root, file)
                            zip_file.write(ruta_completa, file)
                
                zip_buffer.seek(0)
                st.success("✅ Paquete de depósito consolidado con éxito.")
                st.download_button(
                    label=f"⬇️ Descargar {exp_seleccionado}_Completo.zip",
                    data=zip_buffer,
                    file_name=f"{exp_seleccionado}_AboAgrim_Completo.zip",
                    mime="application/zip",
                    type="primary"
                )

def generar_documento_word(ruta_plantilla, diccionario_datos):
    """
    Toma una plantilla de la carpeta 'plantillas_maestras' y la llena con los datos.
    Devuelve un objeto de memoria (BytesIO) listo para descargar o subir a Drive.
    """
    try:
        # Cargamos el archivo base usando la ruta exacta que le manda el sistema
        doc = DocxTemplate(ruta_plantilla)
        
        # Fusionamos el Word con el diccionario de datos (las llaves {{ }})
        doc.render(diccionario_datos)
        
        # Lo guardamos en memoria para que descargue rápido
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
        
    except FileNotFoundError:
        st.error(f"❌ No se encontró la plantilla en la ruta: {ruta_plantilla}. Verifique en su Administrador de Archivos.")
        return None
    except Exception as e:
        st.error(f"❌ Error en la forja del documento: {e}")
        return None

# =======================================================
# 1. DISEÑO DE LA PANTALLA DE PLANTILLAS
# =======================================================

# ==========================================
# 🚦 ENRUTADOR REFORZADO - ABOAGRIM PRO
# ==========================================

# 1. Asegurar el Rol de Presidente (Blindaje)
usuario_actual = st.session_state.get("usuario", "Invitado")

# Si es usted, forzamos el rango máximo automáticamente
if "Jhonny" in usuario_actual or usuario_actual == "JhonnyMatos":
    st.session_state["rol"] = "Presidente Fundador"
    st.session_state["admin_autenticado"] = True

rol_usuario = st.session_state.get("rol", "Pasante")


def vista_alertas_plazos():
    import streamlit as st
    from datetime import date, datetime
    import pandas as pd
    from database import db as supabase

    st.title("⏱️ Sistema Integrado de Plazos (SIP)")
    st.markdown("### Motor Lógico de Caducidad y Rutas Críticas")

    # --- 1. CATÁLOGO LEGAL ---
    catalogo_acciones = {
        # MENSURAS CATASTRALES
        'Vigencia Autorización de Mensura': {
            'cat': 'Mensuras Catastrales', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 60,
            'baseLegal': "Art. 25, Ley 108-05 | Reg. Mensuras Catastrales",
            'jurisprudencia': "SCJ: Plazo busca evitar la inercia en el saneamiento (Art. 51 Const).",
            'diagnosticoAprobado': "Autorización para trabajos de mensura vigente.",
            'diagnosticoRechazado': "¡Caducidad! Han pasado más de 60 días sin presentar los trabajos.",
            'estrategia': "Solicitar prórroga justificada o tramitar nueva autorización.",
            'requisitos': ["Contrato de mensura firmado", "Copia de cédulas de los reclamantes", "Croquis ilustrativo de la porción a sanear", "Instancia motivada de solicitud"],
            'procedimientos': ["1. Depósito de solicitud vía ventanilla de la Jurisdicción Original.", "2. Apoderamiento del tribunal y emisión de la Autorización (Auto).", "3. Notificación a la Dirección Regional de Mensuras Catastrales."]
        },
        'Plazo Aviso de Mensura (Colindantes)': {
            'cat': 'Mensuras Catastrales', 'tipo': 'plazo_inverso', 'unidad': 'dias', 'plazo': 15,
            'baseLegal': "Art. 69, Reglamento General de Mensuras Catastrales",
            'jurisprudencia': "TC: La falta de notificación vulnera el debido proceso y acarrea nulidad.",
            'diagnosticoAprobado': "Plazo correcto para avisar a colindantes antes del terreno.",
            'diagnosticoRechazado': "Defecto de Plazo. No hay tiempo para el aviso previo legal.",
            'estrategia': "Reprogramar la fecha del levantamiento en el terreno.",
            'requisitos': ["Autorización de mensura / Contrato", "Formulario de Aviso de Mensura", "Lista de colindantes e interesados"],
            'procedimientos': ["1. Redactar el aviso indicando fecha y hora del levantamiento.", "2. Notificar vía acto de alguacil, carta con acuse o publicación en prensa.", "3. Anexar constancias de notificación al expediente técnico."]
        },
        'Subsanar Expediente Técnico Observado': {
            'cat': 'Mensuras Catastrales', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 30,
            'baseLegal': "Art. 22, Reglamento General de Mensuras Catastrales (Res. 790-2022)",
            'jurisprudencia': "Garantía de debido proceso administrativo ante rechazos provisionales.",
            'diagnosticoAprobado': "Plazo hábil para reingresar el expediente técnico.",
            'diagnosticoRechazado': "Rechazo Definitivo. Se agotó el plazo para subsanar.",
            'estrategia': "Someter como expediente nuevo y pagar tasas.",
            'requisitos': ["Oficio de observaciones emitido por el calificador", "Planos o XML corregidos", "Carta de reingreso motivada"],
            'procedimientos': ["1. Corregir los defectos indicados en el sistema gráfico/documental.", "2. Reingresar el expediente.", "3. Dar seguimiento al nuevo turno de calificación."]
        },
        'Recurso Reconsideración (Dir. Regional)': {
            'cat': 'Mensuras Catastrales', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 15,
            'baseLegal': "Art. 74, Ley 108-05",
            'jurisprudencia': "Agotamiento obligatorio de vías administrativas previas.",
            'diagnosticoAprobado': "Plazo hábil para recurrir ante el Dir. Regional.",
            'diagnosticoRechazado': "Caducidad. Acto técnico firme.",
            'estrategia': "La calificación técnica adquiere carácter definitivo.",
            'requisitos': ["Instancia motivada dirigida al Director Regional", "Acto impugnado (Calificación rechazada)", "Pruebas técnicas que desmientan la observación"],
            'procedimientos': ["1. Redactar instancia de reconsideración anexando pruebas.", "2. Depositar vía Secretaría de la Dirección Regional.", "3. Esperar resolución administrativa en un plazo de 15 días."]
        },

        # REGISTRO DE TÍTULOS
        'Subsanar Expediente Registral Observado': {
            'cat': 'Registro de Títulos', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 30,
            'baseLegal': "Art. 54, Reglamento General de Registro de Títulos",
            'jurisprudencia': "Principios registrales de rogación y legalidad.",
            'diagnosticoAprobado': "Plazo hábil para levantar el Rechazo Provisional.",
            'diagnosticoRechazado': "Rechazo Definitivo Registral.",
            'estrategia': "Reingresar la solicitud como expediente nuevo.",
            'requisitos': ["Documento faltante (Impuestos DGII, Cédulas, Actas de Estado Civil)", "Copia del oficio de rechazo provisional"],
            'procedimientos': ["1. Obtener la documentación omitida o corregir el acto jurídico.", "2. Depositar por ventanilla el complemento del expediente.", "3. Esperar la calificación definitiva."]
        },
        'Caducidad de Anotación Preventiva': {
            'cat': 'Registro de Títulos', 'tipo': 'plazo', 'unidad': 'anos', 'plazo': 1,
            'baseLegal': "Art. 89, Ley 108-05 | Reg. de Registro de Títulos",
            'jurisprudencia': "La anotación caduca de pleno derecho si no se interpone demanda de fondo.",
            'diagnosticoAprobado': "Anotación Preventiva mantiene vigencia.",
            'diagnosticoRechazado': "Anotación Caducada de pleno derecho.",
            'estrategia': "Solicitar cancelación administrativa por caducidad.",
            'requisitos': ["Instancia solicitando anotación preventiva", "Prueba fehaciente del derecho o crédito reclamado", "Pago de tasas registrales"],
            'procedimientos': ["1. Depositar instancia con pruebas ante el Registro de Títulos.", "2. El registrador inscribe el bloqueo preventivo.", "3. Obligación de demandar el fondo en los tribunales antes de 1 año."]
        },
        'Reclamo Indemnización (Fondo de Garantía)': {
            'cat': 'Registro de Títulos', 'tipo': 'plazo', 'unidad': 'anos', 'plazo': 1,
            'baseLegal': "Art. 39, Ley 108-05",
            'jurisprudencia': "SCJ: La indemnización por errores registrales o desalojos sin negligencia del titular tiene un plazo de caducidad estricto de 1 año.",
            'diagnosticoAprobado': "Acción indemnizatoria viable ante el Estado.",
            'diagnosticoRechazado': "Acción caducada frente al Fondo de Garantía.",
            'estrategia': "Reclamación inadmisible. No hay fondos públicos disponibles.",
            'requisitos': ["Sentencia definitiva de privación de derecho", "Prueba de no negligencia del titular", "Tasación del inmueble"],
            'procedimientos': ["1. Incoar demanda contra el Fondo ante el Tribunal Superior de Tierras.", "2. Demostrar el daño emergente.", "3. Ejecutar sentencia contra el Estado para el pago compensatorio."]
        },

        # TRIBUNALES
        'Notificar Demanda Introductiva (10 días)': {
            'cat': 'Tribunales (Litis e Incidentes)', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 10,
            'baseLegal': "Art. 30, Ley 108-05 | Art. 62, Reglamento Tribunales",
            'jurisprudencia': "TC/0071/13: La notificación oportuna garantiza la tutela judicial efectiva.",
            'diagnosticoAprobado': "Plazo hábil para emplazar a la contraparte.",
            'diagnosticoRechazado': "Caducidad del depósito por falta de emplazamiento.",
            'estrategia': "Depositar nueva demanda inicial en Secretaría.",
            'requisitos': ["Instancia original sellada por el tribunal", "Acto de alguacil (Emplazamiento)", "Fijación de audiencia (Si aplica)"],
            'procedimientos': ["1. Depositar instancia en la Secretaría.", "2. Retirar instancia sellada.", "3. Alguacil notifica en 10 días máximo.", "4. Depositar acto de notificación en tribunal."]
        },
        'Caducidad de Instancia (Inactividad 3 años)': {
            'cat': 'Tribunales (Litis e Incidentes)', 'tipo': 'plazo', 'unidad': 'anos', 'plazo': 3,
            'baseLegal': "Art. 397 y ss. del Código de Procedimiento Civil",
            'jurisprudencia': "SCJ: La inactividad de las partes por 3 años extingue el proceso, asimilándose al abandono.",
            'diagnosticoAprobado': "Proceso activo. Se interrumpió la caducidad.",
            'diagnosticoRechazado': "Presunción de abandono. Plazo cumplido.",
            'estrategia': "Oponer incidente de Caducidad de Instancia.",
            'requisitos': ["Certificación de inactividad expedida por Secretaría", "Último acto procesal fechado hace más de 3 años", "Conclusiones incidentales"],
            'procedimientos': ["1. Solicitar fijación de audiencia.", "2. Presentar in limine litis la demanda en caducidad.", "3. El tribunal extingue el proceso sin fallar el fondo."]
        },
        'Litis: Nulidad Absoluta (Falsedad/Simulación)': {
            'cat': 'Tribunales (Litis e Incidentes)', 'tipo': 'plazo', 'unidad': 'anos', 'plazo': 20,
            'baseLegal': "Art. 2262, Código Civil | Principio VIII, Ley 108-05",
            'jurisprudencia': "SCJ: Cómputo inicia desde publicidad en Registro de Títulos.",
            'diagnosticoAprobado': "Litis viable. Acción viva.",
            'diagnosticoRechazado': "Acción prescrita. Consolidación veintenal.",
            'estrategia': "Oponer Medio de Inadmisión por prescripción.",
            'requisitos': ["Acto atacado (Contrato falso/simulado)", "Pruebas del vicio", "Certificación de Estado Jurídico"],
            'procedimientos': ["1. Depósito de demanda en Jurisdicción Original.", "2. Notificación en 10 días.", "3. Audiencia de Sometimiento de Pruebas.", "4. Audiencia de Fondo y conclusiones."]
        },
        'Solicitud Fuerza Pública (Abogado del Estado)': {
            'cat': 'Tribunales (Litis e Incidentes)', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 15,
            'baseLegal': "Art. 47, Ley 108-05",
            'jurisprudencia': "SCJ: El Abogado del Estado ejecuta desalojos de intrusos sin título.",
            'diagnosticoAprobado': "Plazo de intimación voluntaria corriendo.",
            'diagnosticoRechazado': "Venció el plazo. Fuerza pública ejecutable.",
            'estrategia': "Coordinar fuerza pública con Policía Nacional.",
            'requisitos': ["Certificado de Título a nombre del solicitante", "Certificación de Estado Jurídico", "Acto de intimación a desocupar (15 días antelación)", "Comprobación de invasión"],
            'procedimientos': ["1. Notificar acto de alguacil a los intrusos dando 15 días.", "2. Solicitar Fuerza Pública al Abogado del Estado anexando pruebas.", "3. Autorización y coordinación con fuerza pública para el lanzamiento."]
        },

        # ALTAS CORTES Y RECURSOS
        'Recurso de Apelación (TST)': {
            'cat': 'Altas Cortes y Recursos', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 30,
            'baseLegal': "Art. 80, Ley 108-05",
            'jurisprudencia': "SCJ: Plazos de orden público; inobservancia acarrea inadmisibilidad.",
            'diagnosticoAprobado': "Plazo abierto para depositar apelación.",
            'diagnosticoRechazado': "Plazo vencido. Sentencia firme.",
            'estrategia': "Solicitar Certificado de No Apelación.",
            'requisitos': ["Instancia de recurso motivando los agravios", "Sentencia impugnada notificada", "Pago de tasas judiciales"],
            'procedimientos': ["1. Depositar recurso en la Secretaría del Tribunal que dictó la sentencia.", "2. Notificar a la contraparte en 10 días.", "3. El expediente es remitido al Tribunal Superior de Tierras."]
        },
        'Revisión Constitucional (Tribunal Constitucional)': {
            'cat': 'Altas Cortes y Recursos', 'tipo': 'plazo', 'unidad': 'dias', 'plazo': 30,
            'baseLegal': "Art. 53, Ley 137-11 (Orgánica del Tribunal Constitucional)",
            'jurisprudencia': "TC: Procede contra decisiones jurisdiccionales firmes que vulneren derechos fundamentales.",
            'diagnosticoAprobado': "Plazo hábil para interponer revisión ante el TC.",
            'diagnosticoRechazado': "Recurso extemporáneo. Sentencia inatacable.",
            'estrategia': "Ejecutar de forma definitiva la decisión de la SCJ.",
            'requisitos': ["Sentencia de la Suprema Corte (irrevocable)", "Escrito motivando la vulneración constitucional", "Notificación previa a la SCJ"],
            'procedimientos': ["1. Depositar recurso ante la Secretaría de la corte que dictó la decisión (SCJ).", "2. La corte lo tramita al TC.", "3. Notificar a la contraparte y esperar juicio de admisibilidad del TC."]
        },

        # IMPRESCRIPTIBLES
        'Reivindicación, Deslinde, Saneamiento y Partición': {
            'cat': 'Acciones Imprescriptibles', 'tipo': 'imprescriptible', 'unidad': None, 'plazo': None,
            'baseLegal': "Principio IV, Ley 108-05 | Art. 51 Constitución",
            'jurisprudencia': "TC/0214/18: Derechos registrados son imprescriptibles contra ocupantes ilegales.",
            'diagnosticoAprobado': "La acción es de orden público y NO prescribe.",
            'diagnosticoRechazado': "La acción es de orden público y NO prescribe.",
            'estrategia': "Proceder sin restricciones de tiempo.",
            'requisitos': ["Certificado de Título", "Identificación de ocupantes o linderos conflictivos", "Levantamiento planimétrico del agrimensor (Evidencia técnica)"],
            'procedimientos': ["1. Preparar el plano de levantamiento o replanteo.", "2. Incoar la demanda en Reivindicación (o Deslinde) ante J.O.", "3. Probar la titularidad y la ocupación ilegal en audiencia."]
        }
    }
# ==========================================
    # 🗂️ SISTEMA DE PESTAÑAS (FUSIÓN MAESTRA)
    # ==========================================
    tab_radar, tab_calculadora = st.tabs([
        "🚦 Radar Automático (Expedientes AboAgrim)",
        "🧮 Depuración Manual (Calculadora SIP)"
    ])

    with tab_radar:
        try:
            respuesta = supabase.table("expedientes").select("id_expediente, alertas").execute()
            todos_los_expedientes = respuesta.data
        except Exception as e:
            st.error(f"Error conectando a la base de datos: {e}")
            todos_los_expedientes = []

        todas_las_alertas = []
        lista_expedientes = ["-- Todos los Expedientes --"]
        
        def clasificar_categoria(texto):
            t = str(texto).lower()
            if "mensura" in t or "saneamiento" in t: return "Mensuras Catastrales"
            if "venta" in t or "dgii" in t or "transferencia" in t: return "Registro de Títulos"
            if "litis" in t or "octava" in t or "audiencia" in t: return "Tribunales (Litis e Incidentes)"
            if "recurso" in t or "revisión" in t: return "Altas Cortes y Recursos"
            return "Otras Actuaciones"

        if todos_los_expedientes:
            for exp in todos_los_expedientes:
                id_exp = exp.get("id_expediente")
                alertas = exp.get("alertas")
                
                if alertas and isinstance(alertas, list):
                    tiene_pendientes = False
                    for alerta in alertas:
                        if alerta.get("estado") != "Completado":
                            tiene_pendientes = True
                            cat_detectada = clasificar_categoria(alerta.get("documento_origen", "") + " " + alerta.get("descripcion", ""))
                            
                            todas_las_alertas.append({
                                "Expediente": id_exp,
                                "Categoría": cat_detectada,
                                "Vencimiento": alerta.get("fecha_vencimiento"),
                                "Actuación / Tarea": alerta.get("descripcion"),
                                "Doc. Vinculado": alerta.get("documento_origen"),
                            })
                    
                    if tiene_pendientes and id_exp not in lista_expedientes:
                        lista_expedientes.append(id_exp)

        st.markdown("### 🔍 Panel Automático de Vencimientos")
        col_f1, col_f2 = st.columns(2)
        filtro_exp = col_f1.selectbox("1. Filtrar por Expediente:", lista_expedientes)
        
        categorias_disp = ["-- Todas las Categorías --", "Mensuras Catastrales", "Registro de Títulos", "Tribunales (Litis e Incidentes)", "Altas Cortes y Recursos", "Otras Actuaciones"]
        filtro_cat = col_f2.selectbox("2. Filtrar por Categoría:", categorias_disp)

        alertas_filtradas = todas_las_alertas
        if filtro_exp != "-- Todos los Expedientes --":
            alertas_filtradas = [a for a in alertas_filtradas if a["Expediente"] == filtro_exp]
        if filtro_cat != "-- Todas las Categorías --":
            alertas_filtradas = [a for a in alertas_filtradas if a["Categoría"] == filtro_cat]

        st.write("---")

        if not alertas_filtradas:
            st.success("🎉 ¡El radar está despejado para esta selección, Licenciado!")
        else:
            df_alertas = pd.DataFrame(alertas_filtradas)
            df_alertas['Vencimiento_DT'] = pd.to_datetime(df_alertas['Vencimiento'])
            hoy = pd.to_datetime(datetime.now().date())
            df_alertas['Días Restantes'] = (df_alertas['Vencimiento_DT'] - hoy).dt.days

            def obtener_semaforo(dias):
                if dias < 0: return "🔴 Vencido"
                elif dias <= 15: return "🟡 Urgente"
                else: return "🟢 A tiempo"
                
            df_alertas['Estado'] = df_alertas['Días Restantes'].apply(obtener_semaforo)
            df_alertas = df_alertas.sort_values(by='Días Restantes')

            col1, col2, col3 = st.columns(3)
            vencidos = df_alertas[df_alertas['Días Restantes'] < 0]
            urgentes = df_alertas[(df_alertas['Días Restantes'] >= 0) & (df_alertas['Días Restantes'] <= 15)]
            a_tiempo = df_alertas[df_alertas['Días Restantes'] > 15]
            
            col1.error(f"🔴 Vencidos: {len(vencidos)}")
            col2.warning(f"🟡 Urgentes: {len(urgentes)}")
            col3.success(f"🟢 A tiempo: {len(a_tiempo)}")

            st.write("---")
            df_mostrar = df_alertas[['Expediente', 'Categoría', 'Estado', 'Días Restantes', 'Vencimiento', 'Actuación / Tarea', 'Doc. Vinculado']]
            st.dataframe(
                df_mostrar,
                column_config={"Días Restantes": st.column_config.NumberColumn("Faltan (Días)")},
                hide_index=True,
                use_container_width=True
            )

    with tab_calculadora:
        # --- 2. INTERFAZ DE USUARIO ---
        with st.container(border=True):
            st.markdown("#### Depuración y Operaciones")
            
            c_cat, c_acc = st.columns(2)
            with c_cat:
                categoria_sel = st.selectbox("1. Categoría de la Actuación:", 
                                             ["Mensuras Catastrales", "Registro de Títulos", "Tribunales (Litis e Incidentes)", "Altas Cortes y Recursos", "Acciones Imprescriptibles"])
            
            acciones_filtradas = [k for k, v in catalogo_acciones.items() if v['cat'] == categoria_sel]
            
            with c_acc:
                accion_sel = st.selectbox("2. Actuación Legal o Técnica:", acciones_filtradas)
            
            datos_accion = catalogo_acciones[accion_sel]
    
            fecha_ref = None
            if datos_accion['tipo'] != 'imprescriptible':
                if accion_sel == 'Plazo Aviso de Mensura (Colindantes)':
                    label_f = "Fecha proyectada para los trabajos de terreno:"
                elif accion_sel == 'Solicitud Fuerza Pública (Abogado del Estado)':
                    label_f = "Fecha en que se notificó la intimación a desocupar:"
                else:
                    label_f = "Fecha de inicio del cómputo (Depósito, Notificación o Título):"
                    
                fecha_ref = st.date_input(label_f, value=date.today())
                st.info("⚠️ **Atención:** Para plazos procesales, el cálculo excluye fines de semana si la norma indica 'días hábiles' o francos. El sistema calcula en días calendario base.")
    
        # --- 3. MOTOR DE CÁLCULO Y RESULTADOS ---
        if st.button("🚀 Generar Ruta Crítica y Diagnóstico", type="primary", use_container_width=True):
            st.write("---")
            
            hoy = date.today()
            esta_prescrita = False
            texto_tiempo = ""
            limite_ley = "No aplica"
    
            if datos_accion['tipo'] == 'imprescriptible':
                color_badge = "#007bff"
                titulo_alerta = "🔵 ACCIÓN DE ORDEN PÚBLICO (IMPRESCRIPTIBLE)"
                texto_tiempo = "N/A"
                diag_final = datos_accion['diagnosticoAprobado']
            else:
                limite_ley = f"{datos_accion['plazo']} {datos_accion['unidad']}"
                
                if datos_accion['tipo'] == 'plazo_inverso':
                    if fecha_ref < hoy:
                        st.error("❌ Error: Para avisos y desalojos, la fecha objetivo debe ser futura.")
                        st.stop()
                    dias_faltantes = (fecha_ref - hoy).days
                    esta_prescrita = dias_faltantes < datos_accion['plazo']
                    texto_tiempo = f"Faltan {dias_faltantes} días para el evento"
                    
                elif datos_accion['unidad'] == 'anos':
                    anios_transcurridos = hoy.year - fecha_ref.year - ((hoy.month, hoy.day) < (fecha_ref.month, fecha_ref.day))
                    esta_prescrita = anios_transcurridos >= datos_accion['plazo']
                    texto_tiempo = f"{anios_transcurridos} años completos"
                    
                elif datos_accion['unidad'] == 'dias':
                    dias_transcurridos = (hoy - fecha_ref).days
                    esta_prescrita = dias_transcurridos > datos_accion['plazo']
                    texto_tiempo = f"{dias_transcurridos} días transcurridos"
    
                if esta_prescrita:
                    color_badge = "#dc3545"
                    titulo_alerta = "🔴 PLAZO VENCIDO / CADUCIDAD"
                    diag_final = datos_accion['diagnosticoRechazado']
                else:
                    color_badge = "#28a745"
                    titulo_alerta = "🟢 DENTRO DEL PLAZO LEGAL / ACTIVO"
                    diag_final = datos_accion['diagnosticoAprobado']
    
            # --- 4. RENDERIZADO DEL DICTAMEN ---
            with st.container(border=True):
                st.markdown(f"<h2 style='text-align: center; color: #0d253f; font-family: serif;'>DICTAMEN TÉCNICO-LEGAL</h2>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: gray; font-size: 0.85rem;'>Expedido vía plataforma automatizada • {hoy.strftime('%d de %B de %Y')}</p>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: {color_badge}20; color: {color_badge}; border: 1px solid {color_badge}; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 1.1rem; margin-bottom: 20px;'>
                    {titulo_alerta}
                </div>
                """, unsafe_allow_html=True)
    
                if datos_accion['tipo'] != 'imprescriptible':
                    st.markdown(f"**Tiempo medido:** {texto_tiempo}")
                    st.markdown(f"**Límite normativo:** {limite_ley}")
                
                st.markdown(f"**Diagnóstico:** <span style='color: #0d253f; font-size: 1.1rem; font-weight: bold;'>{diag_final}</span>", unsafe_allow_html=True)
                st.markdown(f"**Acción a tomar:** {datos_accion['estrategia']}")
                
                st.write("---")
                
                c_req, c_proc = st.columns(2)
                with c_req:
                    st.markdown("#### 📌 Requisitos Documentales")
                    for req in datos_accion['requisitos']:
                        st.markdown(f"- {req}")
                with c_proc:
                    st.markdown("#### ⚙️ Procedimiento (Ruta Crítica)")
                    for proc in datos_accion['procedimientos']:
                        st.markdown(f"{proc}")
                
                st.write("---")
                st.info(f"**⚖️ Normativa Legal:** {datos_accion['baseLegal']}\n\n**🏛️ Jurisprudencia:** {datos_accion['jurisprudencia']}")
                
                st.markdown(f"""
                <div style="margin-top: 20px; text-align: right; font-size: 0.95rem; color: #333;">
                    <div style="font-family: serif; font-size: 1.4rem; color: #c5a059; font-weight: bold; margin-bottom: 5px;">ABOAGRIM</div>
                    <strong>Lic. Jhonny Matos, M.A.</strong><br>
                    <span style="color: #0d253f; font-weight: 600;">Presidente | Abogado y Agrimensor</span><br>
                    <span style="color: gray; font-size: 0.85rem;">Tel: 829-826-5888</span>
                </div>
                """, unsafe_allow_html=True)
    
            # --- 5. BOTÓN DE EXPORTACIÓN (Instrucción visual) ---
            st.write("")
            if st.button("🖨️ Exportar Dictamen a PDF", use_container_width=True):
                st.toast("⌨️ Presione Ctrl + P en su teclado para abrir el menú de impresión o guardado PDF.", icon="🖨️")
                st.success("💡 **Instrucción para el equipo:** Presione **`Ctrl + P`** (o `Cmd + P` en Mac) y seleccione **Guardar como PDF** en la ventana que aparecerá en su navegador.")
def vista_plantillas():
    import streamlit as st
    import os
    import io
    from datetime import datetime
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("📄 Motor de Redacción y Plantillas")
    st.markdown("### *AboAgrim Pro: Sistema Experto de Forja Documental*")

    # --- 0. INICIALIZACIÓN DE MEMORIA DINÁMICA GLOBAL ---
    roles_dinamicos = ["cant_ab", "cant_ag", "cant_no", "cant_al", "cant_cl", "cant_ap", "cant_in", "cant_pg", "cant_de"]
    for rol in roles_dinamicos:
        if rol not in st.session_state:
            st.session_state[rol] = 1

    def mod_cant(rol, operacion):
        if operacion == "add":
            st.session_state[rol] += 1
        elif operacion == "del" and st.session_state[rol] > 0:
            st.session_state[rol] -= 1

    # 🗂️ ACTUALIZADO CON SUS 5 CARPETAS MAESTRAS
    carpetas_base = [
        "1_mensuras_catastrales", 
        "2_jurisdiccion_original", 
        "3_registro_titulos",
        "4_otros",
        "5_tribunal_superior_de_tierras"
    ]

    tab_redaccion, tab_boveda = st.tabs(["⚙️ Taller de Redacción (Generar)", "📂 Bóveda de Modelos (Administrar)"])

    with tab_redaccion:
        # 🚀 1. DESCARGAMOS LOS EXPEDIENTES DE LA NUBE
        try:
            respuesta = supabase.table("expedientes").select("*").execute()
            db_expedientes_cloud = {row['id_expediente']: row for row in respuesta.data}
        except Exception:
            db_expedientes_cloud = {}

        lista_exps = ["-- Expediente Independiente (Manual) --"] + list(db_expedientes_cloud.keys())
            
        # --- NUEVO: RADAR DE ÓRGANO AUTOMÁTICO ---
        exp_seleccionado = st.selectbox("Vincular a Expediente:", lista_exps)
        
        organo_default = "Otros Documentos"
        tipo_caso_db = "Proceso Legal General"
        organo_db_real = "No Especificado"

        if exp_seleccionado != "-- Expediente Independiente (Manual) --":
            # Leemos los datos recién guardados de la base de datos
            exp_data = db_expedientes_cloud[exp_seleccionado]
            organo_db_real = exp_data.get("organo_jurisdiccional", "")
            tipo_caso_db = exp_data.get("tipo_caso", "Proceso Legal General")
            
            # El sistema adivina qué carpeta de plantillas abrir basado en el tribunal
            if "Mensuras" in organo_db_real: organo_default = "Mensuras Catastrales"
            elif "Original" in organo_db_real: organo_default = "Jurisdicción Original"
            elif "Títulos" in organo_db_real: organo_default = "Registro de Títulos"
            elif "Superior" in organo_db_real: organo_default = "Tribunal Superior de Tierras"

        opciones_organos_ui = ["Mensuras Catastrales", "Jurisdicción Original", "Registro de Títulos", "Tribunal Superior de Tierras", "Otros Documentos"]
        idx_org = opciones_organos_ui.index(organo_default) if organo_default in opciones_organos_ui else 4
        
        organo_ji = st.selectbox("🏛️ Órgano Destino (Filtra las Plantillas):", opciones_organos_ui, index=idx_org)

        st.write("---")
        
        # 🧠 2. LÓGICA INTELIGENTE DE CARGA DE DATOS
        if exp_seleccionado != "-- Expediente Independiente (Manual) --":
            st.success(f"🔗 **Conectado: {exp_seleccionado} ({tipo_caso_db}).** Los datos maestros se inyectaron en la memoria.")
            
            lista_clientes = exp_data.get("clientes", [])
            lista_apoderados = exp_data.get("apoderados", [])
            lista_abogados = exp_data.get("abogados", [])
            lista_agrimensores = exp_data.get("agrimensores", [])
            lista_notarios = exp_data.get("notarios", [])
            lista_alguaciles = exp_data.get("alguaciles", [])
            lista_inmuebles = exp_data.get("inmuebles", [])
            
            with st.expander("👁️ Ver resumen de datos maestros cargados", expanded=False):
                st.info("Estos datos se inyectarán en su documento de Word:")
                st.write(f"- 📋 **Proceso:** {tipo_caso_db} | 🏛️ **Tribunal:** {organo_db_real}")
                st.write(f"- 👤 **Clientes:** {len(lista_clientes)} | 🤝 **Apoderados:** {len(lista_apoderados)}")
                st.write(f"- ⚖️ **Profesionales:** {len(lista_abogados)} Abogados, {len(lista_agrimensores)} Agrimensores")
                st.write(f"- 📍 **Inmuebles:** {len(lista_inmuebles)}")
                
        else:
            st.info("📝 **Modo Manual:** Complete los datos a continuación para forjar un documento sin vincularlo a la base de datos.")
            # --- FORMULARIOS MANUALES ---
            with st.expander("👥 1. Partes, Clientes y Representantes", expanded=True):
                t_cli, t_apo = st.tabs(["👤 Clientes / Propietarios", "🤝 Apoderados / Representantes"])
                
                with t_cli:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Agregar Cliente", on_click=mod_cant, args=("cant_cl", "add"), key="add_cl")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_cl", "del"), key="del_cl")
                    lista_clientes = []
                    for i in range(st.session_state["cant_cl"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre / Razón Social:", key=f"cl_n_{i}")
                        c = c2.text_input("Cédula / RNC:", key=f"cl_c_{i}")
                        t = c3.text_input("Teléfono(s):", key=f"cl_t_{i}")
                        c4, c5 = st.columns([2, 1])
                        d = c4.text_input("Domicilio Exacto:", key=f"cl_d_{i}")
                        e = c5.text_input("Correo Electrónico:", key=f"cl_e_{i}")
                        if n: lista_clientes.append({"nombre": n, "cedula": c, "telefono": t, "domicilio": d, "email": e})

                with t_apo:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Agregar Apoderado", on_click=mod_cant, args=("cant_ap", "add"), key="add_ap")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_ap", "del"), key="del_ap")
                    lista_apoderados = []
                    for i in range(st.session_state["cant_ap"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre Completo:", key=f"ap_n_{i}")
                        c = c2.text_input("Cédula:", key=f"ap_c_{i}")
                        q = c3.text_input("Calidad:", key=f"ap_q_{i}")
                        c4, c5 = st.columns([2, 1])
                        d = c4.text_input("Domicilio:", key=f"ap_d_{i}")
                        te = c5.text_input("Teléfono / Email:", key=f"ap_te_{i}")
                        if n: lista_apoderados.append({"nombre": n, "cedula": c, "calidad": q, "domicilio": d, "contacto": te})

            with st.expander("⚖️ 2. Profesionales Actuantes", expanded=False):
                t_abo, t_agr, t_not, t_alg = st.tabs(["💼 Abogados", "📐 Agrimensores", "✒️ Notarios", "⚖️ Alguaciles"])
                with t_abo:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Abogado", on_click=mod_cant, args=("cant_ab", "add"), key="add_ab")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_ab", "del"), key="del_ab")
                    lista_abogados = []
                    for i in range(st.session_state["cant_ab"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"ab_n_{i}")
                        c = c2.text_input("Cédula:", key=f"ab_c_{i}")
                        m = c3.text_input("CARD:", key=f"ab_m_{i}")
                        c4, c5, c6 = st.columns(3)
                        d = c4.text_input("Estudio/Domicilio:", key=f"ab_d_{i}")
                        t = c5.text_input("Teléfono:", key=f"ab_t_{i}")
                        e = c6.text_input("Email:", key=f"ab_e_{i}")
                        if n: lista_abogados.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": e})
                with t_agr:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Agrimensor", on_click=mod_cant, args=("cant_ag", "add"), key="add_ag")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_ag", "del"), key="del_ag")
                    lista_agrimensores = []
                    for i in range(st.session_state["cant_ag"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"ag_n_{i}")
                        c = c2.text_input("Cédula:", key=f"ag_c_{i}")
                        m = c3.text_input("CODIA:", key=f"ag_m_{i}")
                        c4, c5, c6 = st.columns(3)
                        d = c4.text_input("Oficina:", key=f"ag_d_{i}")
                        t = c5.text_input("Teléfono:", key=f"ag_t_{i}")
                        e = c6.text_input("Email:", key=f"ag_e_{i}")
                        if n: lista_agrimensores.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": e})
                with t_not:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Notario", on_click=mod_cant, args=("cant_no", "add"), key="add_no")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_no", "del"), key="del_no")
                    lista_notarios = []
                    for i in range(st.session_state["cant_no"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"no_n_{i}")
                        c = c2.text_input("Cédula:", key=f"no_c_{i}")
                        m = c3.text_input("Matrícula:", key=f"no_m_{i}")
                        c4, c5, c6 = st.columns(3)
                        d = c4.text_input("Jurisdicción:", key=f"no_d_{i}")
                        t = c5.text_input("Teléfono:", key=f"no_t_{i}")
                        e = c6.text_input("Email:", key=f"no_e_{i}")
                        if n: lista_notarios.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": e})
                with t_alg:
                    c_btn1, c_btn2 = st.columns([1, 4])
                    c_btn1.button("➕ Alguacil", on_click=mod_cant, args=("cant_al", "add"), key="add_al")
                    c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_al", "del"), key="del_al")
                    lista_alguaciles = []
                    for i in range(st.session_state["cant_al"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"al_n_{i}")
                        c = c2.text_input("Cédula:", key=f"al_c_{i}")
                        m = c3.text_input("Tribunal:", key=f"al_m_{i}")
                        c4, c5 = st.columns([2, 1])
                        d = c4.text_input("Domicilio:", key=f"al_d_{i}")
                        t = c5.text_input("Teléfono:", key=f"al_t_{i}")
                        if n: lista_alguaciles.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t})

            with st.expander("📍 3. Inmuebles y Sustentos Legales", expanded=False):
                c_btn1, c_btn2 = st.columns([1, 4])
                c_btn1.button("➕ Agregar Inmueble", on_click=mod_cant, args=("cant_in", "add"), key="add_in")
                c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_in", "del"), key="del_in")
                lista_inmuebles = []
                for i in range(st.session_state["cant_in"]):
                    c1, c2, c3 = st.columns(3)
                    p = c1.text_input("Parcela/Solar:", key=f"in_p_{i}")
                    dc = c2.text_input("DC / Municipio:", key=f"in_dc_{i}")
                    prov = c3.text_input("Provincia:", key=f"in_prov_{i}")
                    c4, c5, c6 = st.columns(3)
                    coord = c4.text_input("Coordenadas:", key=f"in_co_{i}")
                    sup = c5.text_input("Superficie:", key=f"in_sup_{i}")
                    tdoc = c6.selectbox("Tipo Documento:", ["Certificado de Título", "Constancia Anotada", "Acto de Venta", "Otro"], key=f"in_td_{i}")
                    c7, c8, c9, c10 = st.columns(4)
                    num = c7.text_input("No.:", key=f"in_n_{i}")
                    lib = c8.text_input("Libro:", key=f"in_l_{i}")
                    fol = c9.text_input("Folio:", key=f"in_f_{i}")
                    f_ins = c10.text_input("Fecha Inscripción:", key=f"in_fi_{i}")
                    if p: lista_inmuebles.append({"parcela": p, "dc": dc, "provincia": prov, "coord": coord, "superficie": sup, "tipo_doc": tdoc, "numero": num, "libro": lib, "folio": fol, "fecha_ins": f_ins})

        # --- 3. SECCIONES SIEMPRE VISIBLES (Transacciones y Anexos varían por documento) ---
        with st.expander("💰 4. Datos Transaccionales y Testigos (Específico del Doc.)", expanded=False):
            c_btn1, c_btn2 = st.columns([1, 4])
            c_btn1.button("➕ Agregar Pago", on_click=mod_cant, args=("cant_pg", "add"), key="add_pg")
            c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_pg", "del"), key="del_pg")
            
            lista_pagos = []
            for i in range(st.session_state["cant_pg"]):
                c1, c2, c3 = st.columns(3)
                m = c1.text_input("Monto / Precio:", key=f"pg_m_{i}")
                f = c2.text_input("Forma de Pago:", key=f"pg_f_{i}")
                b = c3.text_input("Banco o Detalle:", key=f"pg_b_{i}")
                if m: lista_pagos.append({"monto": m, "forma": f, "banco": b})
            
            st.write("---")
            testigos = st.text_area("Testigos Instrumentales (Nombres y Cédulas):", height=68)

        with st.expander("📝 5. Tramitantes, Impuestos y Requisitos", expanded=False):
            c_btn1, c_btn2 = st.columns([1, 4])
            c_btn1.button("➕ Tramitante", on_click=mod_cant, args=("cant_de", "add"), key="add_de")
            c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_de", "del"), key="del_de")
            
            lista_depositantes = []
            for i in range(st.session_state["cant_de"]):
                c1, c2, c3 = st.columns(3)
                n = c1.text_input("Nombre Tramitante:", key=f"de_n_{i}")
                c = c2.text_input("Cédula:", key=f"de_c_{i}")
                q = c3.text_input("Calidad:", key=f"de_q_{i}")
                c4, c5 = st.columns(2)
                t = c4.text_input("Teléfono:", key=f"de_t_{i}")
                e = c5.text_input("Email:", key=f"de_e_{i}")
                if n: lista_depositantes.append({"nombre": n, "cedula": c, "calidad": q, "telefono": t, "email": e})
            
            st.write("---")
            impuestos_pagados = st.multiselect("Impuestos/Recibos:", ["Recibo de Ley 108-05 (JI)", "Sello de Ley 33-91 (CARD)", "Recibo CODIA", "Impuesto DGII", "Recibo Ley 196", "Poder Legalizado PGR"])
            inventario_anexos = st.text_area("Lista de Anexos Físicos:", height=100)

        st.write("---")
        
        # --- 🚀 MOTOR DE COMPILACIÓN CONECTADO A SUPABASE STORAGE 🚀 ---
        mapping_carpetas = {
            "Mensuras Catastrales": "1_mensuras_catastrales", 
            "Jurisdicción Original": "2_jurisdiccion_original", 
            "Registro de Títulos": "3_registro_titulos",
            "Tribunal Superior de Tierras": "5_tribunal_superior_de_tierras",
            "Otros Documentos": "4_otros"
        }
        ruta_carpeta = mapping_carpetas[organo_ji]
        
        # Leemos las plantillas directamente desde la nube
        try:
            archivos_nube = supabase.storage.from_("plantillas_maestras").list(ruta_carpeta)
            opciones = [f["name"] for f in archivos_nube if f["name"].endswith(".docx")]
        except Exception:
            opciones = []
            
        if opciones:
            plantillas_elegidas = st.multiselect("📑 Seleccione la(s) plantilla(s) a forjar:", opciones)
            
            if st.button("🚀 FORJAR DOCUMENTO AHORA", type="primary", use_container_width=True):
                if plantillas_elegidas:
                    
                    # Generadores blindados: Usamos .get()
                    cl_nombres = " y ".join([c.get('nombre', '') for c in lista_clientes]) if lista_clientes else "N/A"
                    cl_generales = "; y ".join([f"{c.get('nombre', '')}, dominicano(a), mayor de edad, portador(a) de la cédula No. {c.get('cedula', '')}, domiciliado(a) en {c.get('domicilio', '')}, Tel: {c.get('telefono', '')}" for c in lista_clientes]) if lista_clientes else "N/A"
                    
                    ap_nombres = " y ".join([a.get('nombre', '') for a in lista_apoderados]) if lista_apoderados else "N/A"
                    ap_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, actuando como {a.get('calidad', '')}, domicilio en {a.get('domicilio', '')}, Contacto: {a.get('contacto', a.get('telefono', ''))}" for a in lista_apoderados]) if lista_apoderados else "N/A"

                    ab_nombres = " y ".join([a.get('nombre', '') for a in lista_abogados]) if lista_abogados else "N/A"
                    ab_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, CARD {a.get('matricula', '')}, estudio en {a.get('domicilio', '')}, Tel: {a.get('telefono', '')}" for a in lista_abogados]) if lista_abogados else "N/A"
                    
                    ag_nombres = " y ".join([a.get('nombre', '') for a in lista_agrimensores]) if lista_agrimensores else "N/A"
                    ag_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, CODIA {a.get('matricula', '')}, oficina en {a.get('domicilio', '')}, Tel: {a.get('telefono', '')}" for a in lista_agrimensores]) if lista_agrimensores else "N/A"
                    
                    no_nombres = " y ".join([a.get('nombre', '') for a in lista_notarios]) if lista_notarios else "N/A"
                    no_generales = "; y ".join([f"{a.get('nombre', '')}, Notario, Matrícula {a.get('matricula', '')}, cédula No. {a.get('cedula', '')}" for a in lista_notarios]) if lista_notarios else "N/A"
                    
                    al_nombres = " y ".join([a.get('nombre', '') for a in lista_alguaciles]) if lista_alguaciles else "N/A"
                    al_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, Alguacil del {a.get('matricula', '')}, Tel: {a.get('telefono', '')}" for a in lista_alguaciles]) if lista_alguaciles else "N/A"

                    in_descripciones = "\n".join([f"Parcela {i.get('parcela', '')}, DC {i.get('dc', '')}, {i.get('provincia', '')}. Superficie: {i.get('superficie', '')}. Coordenadas: {i.get('coordenadas', i.get('coord', ''))}. Sustentado en {i.get('tipo_doc', '')} No. {i.get('numero', '')}, Libro {i.get('libro', '')}, Folio {i.get('folio', '')}." for i in lista_inmuebles]) if lista_inmuebles else "N/A"

                    pg_detalles = "\n".join([f"Monto de {p.get('monto', '')} pagadero mediante {p.get('forma', '')} ({p.get('banco', '')})." for p in lista_pagos]) if lista_pagos else "N/A"
                    
                    de_nombres = " y ".join([d.get('nombre', '') for d in lista_depositantes]) if lista_depositantes else "N/A"
                    de_generales = "; y ".join([f"{d.get('nombre', '')}, cédula No. {d.get('cedula', '')}, calidad: {d.get('calidad', '')}, Tel: {d.get('telefono', '')}" for d in lista_depositantes]) if lista_depositantes else "N/A"

                    impuestos_str = ", ".join(impuestos_pagados) if impuestos_pagados else "N/A"
                    
                    datos_para_word = {
                        "expediente": exp_seleccionado, "fecha_hoy": datetime.now().strftime("%d de %B del %Y"),
                        "tipo_caso": tipo_caso_db,
                        "organo_jurisdiccional": organo_db_real,
                        "clientes_nombres": cl_nombres, "clientes_generales": cl_generales,
                        "apoderados_nombres": ap_nombres, "apoderados_generales": ap_generales,
                        "abogados_nombres": ab_nombres, "abogados_generales": ab_generales,
                        "agrimensores_nombres": ag_nombres, "agrimensores_generales": ag_generales,
                        "notarios_nombres": no_nombres, "notarios_generales": no_generales,
                        "alguaciles_nombres": al_nombres, "alguaciles_generales": al_generales,
                        "inmuebles_detalle": in_descripciones,
                        "pagos_detalle": pg_detalles, "testigos": testigos,
                        "depositantes_nombres": de_nombres, "depositantes_generales": de_generales,
                        "impuestos_pagados": impuestos_str, "inventario_anexos": inventario_anexos
                    }
                    
                    archivos_generados = 0
                    for p in plantillas_elegidas:
                        try:
                            # Descargamos temporalmente la plantilla de la nube para inyectarle los datos
                            bytes_plantilla = supabase.storage.from_("plantillas_maestras").download(f"{ruta_carpeta}/{p}")
                            ruta_temp = f"temp_{p}"
                            with open(ruta_temp, "wb") as f:
                                f.write(bytes_plantilla)
                                
                            # Ejecutamos el motor de rellenado
                            buffer = generar_documento_word(ruta_temp, datos_para_word)
                            
                            if buffer:
                                prefijo = exp_seleccionado if exp_seleccionado != "-- Expediente Independiente (Manual) --" else "Doc"
                                nombre_doc_final = f"{prefijo}_{p}"
                                
                                # Botón de descarga manual
                                st.download_button(label=f"⬇️ Descargar: {p}", data=buffer, file_name=nombre_doc_final)
                                archivos_generados += 1
                                
                                # 💾 GUARDADO AUTOMÁTICO EN EL ARCHIVO DIGITAL
                                if exp_seleccionado != "-- Expediente Independiente (Manual) --":
                                    # Crea carpetas por año y tipo de proceso automáticamente
                                    año_actual = datetime.now().strftime("%Y")
                                    tipo_folder = tipo_caso_db.replace("/", "-").replace(" ", "_")
                                    ruta_anexos = f"boveda_digital/Expedientes_{año_actual}/{tipo_folder}/{exp_seleccionado}"
                                    if not os.path.exists(ruta_anexos):
                                        os.makedirs(ruta_anexos)
                                    with open(os.path.join(ruta_anexos, nombre_doc_final), "wb") as f_out:
                                        f_out.write(buffer.getvalue())

                                    # ⏱️ NUEVO: DICCIONARIO LEGAL Y DISPARADOR DE PLAZOS
                                    from datetime import datetime, timedelta
                                    
                                    # 1. Definimos las reglas de negocio (Ley 108-05 y reglamentos)
                                    reglas_plazos = {
                                        "aviso_de_mensura": (15, "Notificación a colindantes y publicidad"),
                                        "contrato_venta": (60, "Pago de impuestos DGII (Transferencia)"),
                                        "saneamiento": (60, "Plazo máximo para trabajos técnicos"),
                                        "recurso_revision": (30, "Plazo de interposición desde notificación"),
                                        "litis": (15, "Octava franca de ley para emplazamiento")
                                    }
                                    
                                    nombre_minuscula = p.lower()
                                    plazo_dias = 0
                                    descripcion_alerta = ""
                                    
                                    for clave, datos_plazo in reglas_plazos.items():
                                        if clave in nombre_minuscula:
                                            plazo_dias = datos_plazo[0]
                                            descripcion_alerta = datos_plazo[1]
                                            break
                                            
                                    if plazo_dias > 0:
                                        fecha_actual = datetime.now()
                                        fecha_vencimiento = fecha_actual + timedelta(days=plazo_dias)
                                        
                                        try:
                                            exp_data = supabase.table("expedientes").select("*").eq("id_expediente", exp_seleccionado).execute().data[0]
                                            
                                            alertas_existentes = exp_data.get("alertas", [])
                                            if alertas_existentes is None:
                                                alertas_existentes = []
                                                
                                            nueva_alerta = {
                                                "fecha_creacion": fecha_actual.strftime("%Y-%m-%d"),
                                                "documento_origen": p,
                                                "descripcion": descripcion_alerta,
                                                "fecha_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d"),
                                                "estado": "Pendiente"
                                            }
                                            
                                            alertas_existentes.append(nueva_alerta)
                                            
                                            supabase.table("expedientes").update({"alertas": alertas_existentes}).eq("id_expediente", exp_seleccionado).execute()
                                            st.toast(f"⏰ ¡Alerta automática generada para {exp_seleccionado}! Vence en {plazo_dias} días.")
                                        except Exception as e:
                                            st.error(f"Error al guardar la alerta: {e}")

                            # Borramos el temporal de la computadora virtual para no ocupar espacio
                            if os.path.exists(ruta_temp):
                                os.remove(ruta_temp)
                        except Exception as e:
                            st.error(f"❌ Falló la generación de {p}. Detalle: {e}")
                            
                    if archivos_generados > 0:
                        st.success(f"⚖️ ¡Impecable! Se redactaron {archivos_generados} documentos listos para impresión.")
        else:
            st.info("📂 Esta carpeta está vacía en la nube. Suba sus plantillas en la pestaña 'Bóveda de Modelos'.")

    with tab_boveda:
        st.subheader("Gestión de Archivos Maestros en la Nube (.docx)")
        
        # 🔒 BLOQUEO PRESIDENCIAL
        if st.session_state.get("rol_actual") == "Presidente Fundador":
            
            with st.form("form_subida_plantillas", clear_on_submit=True):
                col_up1, col_up2 = st.columns([2, 3])
                with col_up1:
                    destino = st.selectbox("Cargar en:", carpetas_base)
                with col_up2:
                    archivos_subidos = st.file_uploader("Arrastrar Plantillas Nuevas", type=["docx"], accept_multiple_files=True)
                
                btn_subir = st.form_submit_button("☁️ Subir y Guardar en la Nube", use_container_width=True)

            if btn_subir:
                if archivos_subidos:
                    hubo_errores = False
                    for archivo in archivos_subidos:
                        try:
                            # Subimos el archivo a Supabase Storage
                            supabase.storage.from_("plantillas_maestras").upload(
                                path=f"{destino}/{archivo.name}",
                                file=archivo.getvalue(),
                                file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                            )
                        except Exception as e:
                            st.error(f"❌ Supabase rechazó el archivo '{archivo.name}'. Motivo: {e}")
                            hubo_errores = True
                    
                    if not hubo_errores:
                        st.success(f"✅ Se guardaron {len(archivos_subidos)} plantilla(s) exitosamente en la bóveda corporativa.")
                        st.rerun() # Solo refrescamos si TODO salió perfecto
                else:
                    st.warning("⚠️ Debe arrastrar al menos un archivo (.docx) antes de guardar.")

            st.divider()
            st.write("**⚠️ Zona de Eliminación (Solo Presidente)**")
            cat_ver = st.selectbox("Revisar categoría para borrar:", carpetas_base)
            
            try:
                # Leemos qué hay en esa carpeta en la nube
                archivos_nube_del = supabase.storage.from_("plantillas_maestras").list(cat_ver)
                archivos_en_cat = [f["name"] for f in archivos_nube_del if f["name"].endswith(".docx")]
            except Exception:
                archivos_en_cat = []
                
            if archivos_en_cat:
                c_del1, c_del2 = st.columns([3, 1])
                archivo_borrar = c_del1.selectbox("Seleccione para eliminar:", archivos_en_cat)
                if c_del2.button("🔥 Eliminar Modelo Definitivamente"):
                    try:
                        supabase.storage.from_("plantillas_maestras").remove([f"{cat_ver}/{archivo_borrar}"])
                        st.success(f"🗑️ El archivo {archivo_borrar} fue eliminado permanentemente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo eliminar: {e}")
            else:
                st.info("No hay documentos en esta carpeta de la nube para eliminar.")
        else:
            st.error("⛔ Acceso Restringido")
            st.warning("Usted no tiene permisos para subir o borrar plantillas. Esta función es exclusiva del Presidente.")

def vista_honorarios():
    import streamlit as st
    import pandas as pd
    from datetime import datetime
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("💳 Bóveda Financiera y Honorarios")
    st.markdown("### *AboAgrim Pro: Control de Facturación, Cotizaciones y Cobros*")

    # 🛡️ Seguridad: Solo Administradores ven el dinero
    if st.session_state.get("rol_actual") not in ["Presidente Fundador", "Contabilidad"]:
        st.error("⛔ Acceso Denegado. Área exclusiva de la Presidencia y Dirección Financiera.")
        return

    # --- 0. INICIALIZACIÓN DE MEMORIA DINÁMICA ---
    if "cant_conceptos" not in st.session_state:
        st.session_state["cant_conceptos"] = 1

    def mod_cant_conceptos(operacion):
        if operacion == "add":
            st.session_state["cant_conceptos"] += 1
        elif operacion == "del" and st.session_state["cant_conceptos"] > 1:
            st.session_state["cant_conceptos"] -= 1

    # --- 1. EXTRACCIÓN MAESTRA DE DATOS DESDE SUPABASE ---
    # Traemos expedientes
    try:
        res_exp = supabase.table("expedientes").select("*").execute()
        db_expedientes = {row['id_expediente']: row for row in res_exp.data} if res_exp.data else {}
    except Exception:
        db_expedientes = {}

    # Traemos facturas (Creamos la lógica por si la tabla no existe o está vacía)
    try:
        res_fac = supabase.table("facturas").select("*").execute()
        db_facturas = res_fac.data if res_fac.data else []
    except Exception:
        db_facturas = []

    # --- ESTRUCTURA DE PESTAÑAS FINANCIERAS ---
    tab_dash, tab_nueva, tab_historial = st.tabs([
        "📊 Tablero de Rendimiento", 
        "🧾 Emitir Cotización / Acuerdo", 
        "🗄️ Historial de Cuentas"
    ])

    # =========================================================
    # PESTAÑA A: TABLERO FINANCIERO (DASHBOARD)
    # =========================================================
    with tab_dash:
        st.subheader("Rendimiento Financiero de la Firma")
        
        # Cálculos del Dashboard
        total_facturado = sum(f.get("total", 0) for f in db_facturas)
        total_pagado = sum(f.get("monto_pagado", 0) for f in db_facturas)
        total_pendiente = total_facturado - total_pagado
        facturas_activas = len(db_facturas)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.metric("🧾 Cotizaciones Emitidas", facturas_activas)
        with col2:
            with st.container(border=True):
                st.metric("💰 Total Facturado (RD$)", f"${total_facturado:,.2f}")
        with col3:
            with st.container(border=True):
                st.metric("✅ Total Cobrado (RD$)", f"${total_pagado:,.2f}")
        with col4:
            with st.container(border=True):
                st.metric("⚠️ Cuentas por Cobrar", f"${total_pendiente:,.2f}")

        st.info("💡 Este tablero lee en tiempo real todas las cotizaciones y pagos registrados en Supabase.")

    # =========================================================
    # PESTAÑA B: NUEVA PROFORMA / FACTURA
    # =========================================================
    with tab_nueva:
        st.subheader("Crear Nuevo Acuerdo de Honorarios")
        
        lista_exps = ["-- Cliente Independiente (Sin Expediente) --"] + list(db_expedientes.keys())
        exp_seleccionado = st.selectbox("🔗 Vincular a Expediente (Opcional):", lista_exps)

        cliente_proforma = ""
        asunto_proforma = "Servicios Legales y Topográficos"
        cedula_proforma = ""

        # Autocompletado si selecciona un expediente
        if exp_seleccionado != "-- Cliente Independiente (Sin Expediente) --":
            exp_data = db_expedientes[exp_seleccionado]
            asunto_proforma = exp_data.get("asunto", "Servicios Legales")
            lista_clientes = exp_data.get("clientes", [])
            if lista_clientes:
                cliente_proforma = lista_clientes[0].get("nombre", "")
                cedula_proforma = lista_clientes[0].get("cedula", "")
            st.success(f"Datos inyectados desde el expediente: **{asunto_proforma}**")

        with st.container(border=True):
            st.markdown("#### 1. Datos Generales")
            c_g1, c_g2, c_g3 = st.columns(3)
            cliente_final = c_g1.text_input("Nombre del Cliente/Empresa:", value=cliente_proforma)
            cedula_final = c_g2.text_input("Cédula / RNC:", value=cedula_proforma)
            asunto_final = c_g3.text_input("Concepto General:", value=asunto_proforma)

        with st.container(border=True):
            st.markdown("#### 2. Condiciones del Acuerdo")
            col1, col2, col3 = st.columns(3)
            tipo_acuerdo = col1.selectbox("Tipo de Honorarios:", ["Monto Fijo (Suma Alzada)", "Cuota Litis (%)", "Iguala Mensual", "Pago por Etapa"])
            plan_pago = col2.selectbox("Plan de Pago:", ["50% Inicio / 50% Final", "100% Adelantado", "30% / 30% / 40%", "Contra Entrega"])
            moneda = col3.selectbox("Moneda:", ["RD$ (Pesos)", "US$ (Dólares)"])

        with st.container(border=True):
            st.markdown("#### 3. Detalle de Servicios")
            c_btn1, c_btn2, _ = st.columns([1, 1, 3])
            c_btn1.button("➕ Agregar Línea", on_click=mod_cant_conceptos, args=("add",), key="add_conc")
            c_btn2.button("➖ Quitar Línea", on_click=mod_cant_conceptos, args=("del",), key="del_conc")

            subtotal = 0.0
            conceptos_factura = []
            
            for i in range(st.session_state["cant_conceptos"]):
                c1, c2, c3, c4 = st.columns([4, 1, 2, 2])
                desc = c1.text_input(f"Descripción {i+1}:", key=f"fac_desc_{i}")
                cant = c2.number_input("Cant:", min_value=1, value=1, key=f"fac_cant_{i}")
                precio = c3.number_input("Precio Unit.:", min_value=0.0, value=0.0, step=1000.0, key=f"fac_prec_{i}")
                
                total_linea = cant * precio
                c4.markdown(f"<div style='padding-top: 35px; font-weight: bold;'>{moneda} {total_linea:,.2f}</div>", unsafe_allow_html=True)
                subtotal += total_linea
                
                if desc: conceptos_factura.append({"desc": desc, "cant": cant, "precio": precio, "total": total_linea})

        with st.container(border=True):
            st.markdown("#### 4. Impuestos y Emisión")
            col_imp1, col_imp2, col_imp3 = st.columns(3)
            aplicar_itbis = col_imp1.checkbox("Sumar ITBIS (18%)", value=False)
            retencion_isr = col_imp2.checkbox("Retención ISR (10%)")
            ret_itbis = col_imp3.number_input("Monto Retención ITBIS (RD$):", min_value=0.0, value=0.0)

            itbis = subtotal * 0.18 if aplicar_itbis else 0.0
            isr = subtotal * 0.10 if retencion_isr else 0.0
            total_pagar = subtotal + itbis - isr - ret_itbis

            st.markdown(f"### 🧾 Total a Facturar: {moneda} {total_pagar:,.2f}")

            if st.button("💾 Guardar Acuerdo en Supabase", type="primary", use_container_width=True):
                if not cliente_final or not conceptos_factura:
                    st.error("⚠️ Debe indicar el cliente y al menos un concepto a facturar.")
                else:
                    id_factura = f"FAC-{datetime.now().strftime('%Y%m%d%H%M')}"
                    datos_factura = {
                        "id_factura": id_factura,
                        "id_expediente": exp_seleccionado if exp_seleccionado != "-- Cliente Independiente (Sin Expediente) --" else None,
                        "cliente": cliente_final,
                        "cedula": cedula_final,
                        "asunto": asunto_final,
                        "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                        "tipo_acuerdo": tipo_acuerdo,
                        "plan_pago": plan_pago,
                        "moneda": moneda,
                        "conceptos": conceptos_factura,
                        "subtotal": subtotal,
                        "itbis": itbis,
                        "retenciones": isr + ret_itbis,
                        "total": total_pagar,
                        "monto_pagado": 0.0, # Nace con 0 pagado
                        "estado": "Pendiente"
                    }
                    try:
                        supabase.table("facturas").upsert(datos_factura).execute()
                        st.success(f"✅ ¡Factura {id_factura} registrada en la bóveda contable!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al guardar en Supabase. Asegúrese de haber creado la tabla 'facturas'. Detalle: {e}")

    # =========================================================
    # PESTAÑA C: HISTORIAL Y ESTADO DE CUENTAS
    # =========================================================
    with tab_historial:
        st.subheader("🗄️ Registro Histórico de Facturas")
        
        if db_facturas:
            for idx, fac in enumerate(reversed(db_facturas)):
                color_estado = "green" if fac.get('estado') == "Pagada" else "red"
                
                with st.expander(f"🧾 {fac.get('id_factura')} | {fac.get('cliente')} - {fac.get('moneda')} {fac.get('total', 0):,.2f}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Fecha:** {fac.get('fecha_emision')}")
                    c2.write(f"**Expediente:** {fac.get('id_expediente', 'N/A')}")
                    c3.markdown(f"**Estado:** <span style='color:{color_estado}; font-weight:bold;'>{fac.get('estado', 'Pendiente')}</span>", unsafe_allow_html=True)
                    
                    st.write(f"**Asunto:** {fac.get('asunto')}")
                    
                    # 🖨️ Generador Visual HTML para Imprimir a PDF
                    st.divider()
                    st.write("**Vista Previa del Documento:**")
                    
                    # Construimos una vista HTML elegante del recibo
                    lineas_html = "".join([f"<tr><td style='border-bottom: 1px solid #ddd; padding: 8px;'>{c['cant']}</td><td style='border-bottom: 1px solid #ddd; padding: 8px;'>{c['desc']}</td><td style='border-bottom: 1px solid #ddd; padding: 8px;'>{fac.get('moneda')} {c['total']:,.2f}</td></tr>" for c in fac.get('conceptos', [])])
                    
                    html_recibo = f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 10px; max-width: 800px; margin: auto; background-color: white; color: black;">
                        <h2 style="color: #B8860B; text-align: center; border-bottom: 2px solid #B8860B; padding-bottom: 10px;">ABOAGRIM PRO</h2>
                        <h4 style="text-align: center; margin-top: -10px; color: #333;">Firma de Abogados & Agrimensores</h4>
                        <table style="width: 100%; margin-top: 20px;">
                            <tr>
                                <td><strong>Cotización / Acuerdo No.:</strong> {fac.get('id_factura')}</td>
                                <td style="text-align: right;"><strong>Fecha:</strong> {fac.get('fecha_emision')}</td>
                            </tr>
                            <tr>
                                <td><strong>Cliente:</strong> {fac.get('cliente')}</td>
                                <td style="text-align: right;"><strong>Cédula/RNC:</strong> {fac.get('cedula', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td colspan="2"><strong>Asunto:</strong> {fac.get('asunto')}</td>
                            </tr>
                        </table>
                        
                        <table style="width: 100%; margin-top: 20px; border-collapse: collapse;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="padding: 8px; text-align: left;">Cant.</th>
                                    <th style="padding: 8px; text-align: left;">Descripción de los Servicios</th>
                                    <th style="padding: 8px; text-align: left;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {lineas_html}
                            </tbody>
                        </table>
                        
                        <table style="width: 100%; margin-top: 20px;">
                            <tr>
                                <td style="width: 60%; vertical-align: top;">
                                    <p><strong>Condiciones:</strong> {fac.get('tipo_acuerdo')} - {fac.get('plan_pago')}</p>
                                    <p><strong>Cuentas Bancarias Oficiales:</strong><br>
                                    - Banco BHD (Ahorros): 08010850011<br>
                                    - Banreservas (Ahorros): 9601369253</p>
                                </td>
                                <td style="width: 40%; text-align: right; background-color: #f9f9f9; padding: 10px; border-radius: 5px;">
                                    <p><strong>Subtotal:</strong> {fac.get('moneda')} {fac.get('subtotal', 0):,.2f}</p>
                                    <p><strong>Impuestos/Retenciones:</strong> {fac.get('moneda')} {(fac.get('itbis',0) - fac.get('retenciones',0)):,.2f}</p>
                                    <h3 style="color: #1E3A8A;">TOTAL A PAGAR: {fac.get('moneda')} {fac.get('total', 0):,.2f}</h3>
                                </td>
                            </tr>
                        </table>
                    </div>
                    """
                    st.components.v1.html(html_recibo, height=450, scrolling=True)
                    
                    # Botón para descargar el código HTML (Que luego se puede imprimir a PDF)
                    st.download_button(
                        label="⬇️ Descargar Archivo para Imprimir",
                        data=html_recibo,
                        file_name=f"Factura_{fac.get('id_factura')}.html",
                        mime="text/html",
                        key=f"dl_{idx}"
                    )
                    
                    # Eliminar factura (Solo si hubo un error)
                    if st.button("🗑️ Eliminar Registro", key=f"del_{fac.get('id_factura')}_{idx}"):
                        supabase.table("facturas").delete().eq("id_factura", fac.get('id_factura')).execute()
                        st.rerun()
        else:
            st.info("No hay facturas registradas en la nube. Comience creando una en la pestaña anterior.")
# --- CENTRO DE ENLACES INSTITUCIONALES (BARRA LATERAL) ---
    st.sidebar.divider()
    
    with st.sidebar.expander("🔗 Accesos Institucionales (R.D.)", expanded=False):
        st.markdown("**Jurisdicción Inmobiliaria**")
        st.link_button("📍 Consulta Parcelaria RI", "https://oficinavirtual.ri.gob.do/ConsultaParcelaria", use_container_width=True, help="Verificar estado de parcelas")
        st.link_button("🏛️ Portal Acceso Digital", "https://oficinavirtual.ri.gob.do/", use_container_width=True, help="Someter expedientes a Mensuras/Registro")
        st.link_button("🌐 Portal RI Principal", "https://ri.gob.do/", use_container_width=True)
        
        st.divider()
        st.markdown("**Otras Entidades**")
        st.link_button("💰 DGII - Oficina Virtual", "https://dgii.gov.do/ofv/", use_container_width=True, help="Consultar IPI y transferencias")
        st.link_button("⚖️ Poder Judicial", "https://poderjudicial.gob.do/", use_container_width=True)
        st.link_button("📐 CODIA", "https://codia.org.do/", use_container_width=True)
