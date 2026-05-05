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
    from datetime import datetime, timedelta
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("📄 Fábrica Inteligente de Documentos")
    st.markdown("### *AboAgrim Pro: Motor de Redacción y Plantillas*")

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

    carpetas_base = ["1_mensuras_catastrales", "2_jurisdiccion_original", "3_registro_titulos", "4_otros", "5_tribunal_superior_de_tierras"]

    tab_redaccion, tab_boveda = st.tabs(["⚙️ Taller de Forjado (Generar)", "📂 Bóveda de Modelos (Administrar)"])

    with tab_redaccion:
        # 🚀 1. DESCARGAMOS LOS EXPEDIENTES DE LA NUBE
        try:
            respuesta = supabase.table("expedientes").select("*").execute()
            db_expedientes_cloud = {row['id_expediente']: row for row in respuesta.data}
        except Exception:
            db_expedientes_cloud = {}

        lista_exps = ["-- Expediente Independiente (Modo Manual) --"] + list(db_expedientes_cloud.keys())
        
        # --- PANEL SUPERIOR: SELECCIÓN DE CASO ---
        with st.container(border=True):
            st.markdown("#### 🔗 1. Vincular a un Expediente")
            exp_seleccionado = st.selectbox("Seleccione el caso para inyectar sus datos automáticamente:", lista_exps)

        organo_default = "Otros Documentos"
        tipo_caso_db = "Proceso Legal General"
        organo_db_real = "No Especificado"

        # Variables de listas para la inyección (vacías por defecto)
        lista_clientes, lista_apoderados = [], []
        lista_abogados, lista_agrimensores, lista_notarios, lista_alguaciles = [], [], [], []
        lista_inmuebles, lista_pagos, lista_depositantes = [], [], []
        impuestos_pagados = []
        inventario_anexos = ""
        testigos = ""

        # 🧠 2. LÓGICA INTELIGENTE DE CARGA DE DATOS
        if exp_seleccionado != "-- Expediente Independiente (Modo Manual) --":
            exp_data = db_expedientes_cloud[exp_seleccionado]
            organo_db_real = exp_data.get("organo_jurisdiccional", "")
            tipo_caso_db = exp_data.get("tipo_caso", "Proceso Legal General")
            
            # El sistema adivina qué carpeta de plantillas abrir
            if "Mensuras" in organo_db_real: organo_default = "Mensuras Catastrales"
            elif "Original" in organo_db_real: organo_default = "Jurisdicción Original"
            elif "Títulos" in organo_db_real: organo_default = "Registro de Títulos"
            elif "Superior" in organo_db_real: organo_default = "Tribunal Superior de Tierras"

            lista_clientes = exp_data.get("clientes", [])
            lista_apoderados = exp_data.get("apoderados", [])
            lista_abogados = exp_data.get("abogados", [])
            lista_agrimensores = exp_data.get("agrimensores", [])
            lista_notarios = exp_data.get("notarios", [])
            lista_alguaciles = exp_data.get("alguaciles", [])
            lista_inmuebles = exp_data.get("inmuebles", [])

            st.success(f"✅ **DATOS MAESTROS CARGADOS DESDE SUPABASE**")
            
            # --- PANEL DE RAYOS X (RESUMEN INTELIGENTE) ---
            with st.container(border=True):
                st.markdown(f"**Radiografía del Caso: {exp_seleccionado}**")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Proceso", tipo_caso_db)
                c2.metric("Partes (Cli/Apo)", len(lista_clientes) + len(lista_apoderados))
                c3.metric("Equipo Técnico", len(lista_abogados) + len(lista_agrimensores))
                c4.metric("Inmuebles", len(lista_inmuebles))
                
                st.caption(f"🏛️ **Tribunal/Órgano:** {organo_db_real}")

            # Datos específicos del documento (Aún en modo automático, hay datos que cambian por documento)
            with st.expander("📝 Completar Datos Específicos del Documento (Transacción, Impuestos, Testigos)"):
                c_btn1, c_btn2 = st.columns([1, 4])
                c_btn1.button("➕ Pago", on_click=mod_cant, args=("cant_pg", "add"), key="add_pg_a")
                c_btn2.button("➖ Quitar", on_click=mod_cant, args=("cant_pg", "del"), key="del_pg_a")
                for i in range(st.session_state["cant_pg"]):
                    c1, c2, c3 = st.columns(3)
                    m = c1.text_input("Monto / Precio:", key=f"pg_m_a_{i}")
                    f = c2.text_input("Forma de Pago:", key=f"pg_f_a_{i}")
                    b = c3.text_input("Banco o Detalle:", key=f"pg_b_a_{i}")
                    if m: lista_pagos.append({"monto": m, "forma": f, "banco": b})
                
                testigos = st.text_input("Testigos Instrumentales (Nombres y Cédulas):")
                impuestos_pagados = st.multiselect("Impuestos/Recibos Anexos:", ["Recibo de Ley 108-05 (JI)", "Sello de Ley 33-91 (CARD)", "Recibo CODIA", "Impuesto DGII", "Recibo Ley 196", "Poder Legalizado PGR"])
                inventario_anexos = st.text_area("Lista de Anexos Físicos:", height=68)

        else:
            st.info("📝 **Modo Manual Activo:** Rellene el formulario a través de las pestañas.")
            # --- FORMULARIO MANUAL CON PESTAÑAS (DISEÑO LIMPIO) ---
            tab_m1, tab_m2, tab_m3, tab_m4 = st.tabs(["👥 Partes", "⚖️ Profesionales", "📍 Inmuebles", "💰 Transacción y Extras"])
            
            with tab_m1:
                col1, col2 = st.columns(2)
                with col1:
                    st.button("➕ Cliente", on_click=mod_cant, args=("cant_cl", "add"), key="add_cl")
                    for i in range(st.session_state["cant_cl"]):
                        with st.container(border=True):
                            n = st.text_input(f"Nombre Cliente {i+1}:", key=f"cl_n_{i}")
                            c = st.text_input("Cédula/RNC:", key=f"cl_c_{i}")
                            t = st.text_input("Teléfono:", key=f"cl_t_{i}")
                            d = st.text_input("Domicilio:", key=f"cl_d_{i}")
                            e = st.text_input("Email:", key=f"cl_e_{i}")
                            if n: lista_clientes.append({"nombre": n, "cedula": c, "telefono": t, "domicilio": d, "email": e})
                with col2:
                    st.button("➕ Apoderado", on_click=mod_cant, args=("cant_ap", "add"), key="add_ap")
                    for i in range(st.session_state["cant_ap"]):
                        with st.container(border=True):
                            n = st.text_input(f"Nombre Apoderado {i+1}:", key=f"ap_n_{i}")
                            c = st.text_input("Cédula:", key=f"ap_c_{i}")
                            q = st.text_input("Calidad (Ej. Poder Especial):", key=f"ap_q_{i}")
                            d = st.text_input("Domicilio:", key=f"ap_d_{i}")
                            te = st.text_input("Contacto:", key=f"ap_te_{i}")
                            if n: lista_apoderados.append({"nombre": n, "cedula": c, "calidad": q, "domicilio": d, "contacto": te})

            with tab_m2:
                s_tab_ab, s_tab_ag, s_tab_no, s_tab_al = st.tabs(["Abogados", "Agrimensores", "Notarios", "Alguaciles"])
                with s_tab_ab:
                    st.button("➕ Abogado", on_click=mod_cant, args=("cant_ab", "add"), key="add_ab")
                    for i in range(st.session_state["cant_ab"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"ab_n_{i}")
                        c = c2.text_input("Cédula:", key=f"ab_c_{i}")
                        m = c3.text_input("CARD:", key=f"ab_m_{i}")
                        d = st.text_input(f"Estudio (Ab. {i+1}):", key=f"ab_d_{i}")
                        t = st.text_input(f"Teléfono (Ab. {i+1}):", key=f"ab_t_{i}")
                        if n: lista_abogados.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": ""})
                with s_tab_ag:
                    st.button("➕ Agrimensor", on_click=mod_cant, args=("cant_ag", "add"), key="add_ag")
                    for i in range(st.session_state["cant_ag"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"ag_n_{i}")
                        c = c2.text_input("Cédula:", key=f"ag_c_{i}")
                        m = c3.text_input("CODIA:", key=f"ag_m_{i}")
                        d = st.text_input(f"Oficina (Ag. {i+1}):", key=f"ag_d_{i}")
                        t = st.text_input(f"Teléfono (Ag. {i+1}):", key=f"ag_t_{i}")
                        if n: lista_agrimensores.append({"nombre": n, "cedula": c, "matricula": m, "domicilio": d, "telefono": t, "email": ""})
                with s_tab_no:
                    st.button("➕ Notario", on_click=mod_cant, args=("cant_no", "add"), key="add_no")
                    for i in range(st.session_state["cant_no"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"no_n_{i}")
                        c = c2.text_input("Cédula:", key=f"no_c_{i}")
                        m = c3.text_input("Matrícula Notarial:", key=f"no_m_{i}")
                        if n: lista_notarios.append({"nombre": n, "cedula": c, "matricula": m})
                with s_tab_al:
                    st.button("➕ Alguacil", on_click=mod_cant, args=("cant_al", "add"), key="add_al")
                    for i in range(st.session_state["cant_al"]):
                        c1, c2, c3 = st.columns(3)
                        n = c1.text_input("Nombre:", key=f"al_n_{i}")
                        c = c2.text_input("Cédula:", key=f"al_c_{i}")
                        m = c3.text_input("Tribunal:", key=f"al_m_{i}")
                        if n: lista_alguaciles.append({"nombre": n, "cedula": c, "matricula": m})

            with tab_m3:
                st.button("➕ Inmueble", on_click=mod_cant, args=("cant_in", "add"), key="add_in")
                for i in range(st.session_state["cant_in"]):
                    with st.container(border=True):
                        c1, c2, c3 = st.columns(3)
                        p = c1.text_input("Parcela/Solar:", key=f"in_p_{i}")
                        dc = c2.text_input("DC / Municipio:", key=f"in_dc_{i}")
                        prov = c3.text_input("Provincia:", key=f"in_prov_{i}")
                        c4, c5, c6 = st.columns(3)
                        coord = c4.text_input("Coordenadas:", key=f"in_co_{i}")
                        sup = c5.text_input("Superficie:", key=f"in_sup_{i}")
                        tdoc = c6.selectbox("Tipo Documento:", ["Certificado de Título", "Constancia Anotada", "Acto de Venta", "Otro"], key=f"in_td_{i}")
                        c7, c8, c9 = st.columns(3)
                        num = c7.text_input("No. Doc:", key=f"in_n_{i}")
                        lib = c8.text_input("Libro:", key=f"in_l_{i}")
                        fol = c9.text_input("Folio:", key=f"in_f_{i}")
                        if p: lista_inmuebles.append({"parcela": p, "dc": dc, "provincia": prov, "coordenadas": coord, "superficie": sup, "tipo_doc": tdoc, "numero": num, "libro": lib, "folio": fol})

            with tab_m4:
                st.button("➕ Agregar Pago", on_click=mod_cant, args=("cant_pg", "add"), key="add_pg_m")
                for i in range(st.session_state["cant_pg"]):
                    c1, c2, c3 = st.columns(3)
                    m = c1.text_input("Monto / Precio:", key=f"pg_m_m_{i}")
                    f = c2.text_input("Forma de Pago:", key=f"pg_f_m_{i}")
                    b = c3.text_input("Banco o Detalle:", key=f"pg_b_m_{i}")
                    if m: lista_pagos.append({"monto": m, "forma": f, "banco": b})
                testigos = st.text_input("Testigos Instrumentales (Nombres y Cédulas):", key="test_m")
                impuestos_pagados = st.multiselect("Impuestos/Recibos:", ["Recibo de Ley 108-05 (JI)", "Sello de Ley 33-91 (CARD)", "Recibo CODIA", "Impuesto DGII"], key="imp_m")

        st.write("---")
        
        # --- 3. SELECCIÓN DE PLANTILLA Y MOTOR DE COMPILACIÓN ---
        st.markdown("#### 📑 2. Selección de Plantillas Corporativas")
        opciones_organos_ui = ["Mensuras Catastrales", "Jurisdicción Original", "Registro de Títulos", "Tribunal Superior de Tierras", "Otros Documentos"]
        idx_org = opciones_organos_ui.index(organo_default) if organo_default in opciones_organos_ui else 4
        
        organo_ji = st.selectbox("Clasificación de la Plantilla (Filtro):", opciones_organos_ui, index=idx_org)
        
        mapping_carpetas = {
            "Mensuras Catastrales": "1_mensuras_catastrales", 
            "Jurisdicción Original": "2_jurisdiccion_original", 
            "Registro de Títulos": "3_registro_titulos",
            "Tribunal Superior de Tierras": "5_tribunal_superior_de_tierras",
            "Otros Documentos": "4_otros"
        }
        ruta_carpeta = mapping_carpetas[organo_ji]
        
        try:
            archivos_nube = supabase.storage.from_("plantillas_maestras").list(ruta_carpeta)
            opciones = [f["name"] for f in archivos_nube if f["name"].endswith(".docx")]
        except Exception:
            opciones = []
            
        if opciones:
            plantillas_elegidas = st.multiselect("Seleccione los documentos a generar:", opciones)
            
            st.write("")
            # 🔥 EL GRAN BOTÓN DE FORJADO 🔥
            if st.button("⚙️ FORJAR Y BLINDAR DOCUMENTOS", type="primary", use_container_width=True):
                if plantillas_elegidas:
                    
                    # Generadores de texto
                    cl_nombres = " y ".join([c.get('nombre', '') for c in lista_clientes]) if lista_clientes else "N/A"
                    cl_generales = "; y ".join([f"{c.get('nombre', '')}, dominicano(a), mayor de edad, portador(a) de la cédula No. {c.get('cedula', '')}, domiciliado(a) en {c.get('domicilio', '')}, Tel: {c.get('telefono', '')}" for c in lista_clientes]) if lista_clientes else "N/A"
                    
                    ap_nombres = " y ".join([a.get('nombre', '') for a in lista_apoderados]) if lista_apoderados else "N/A"
                    ap_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, actuando como {a.get('calidad', '')}, domicilio en {a.get('domicilio', '')}" for a in lista_apoderados]) if lista_apoderados else "N/A"

                    ab_nombres = " y ".join([a.get('nombre', '') for a in lista_abogados]) if lista_abogados else "N/A"
                    ab_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, CARD {a.get('matricula', '')}, estudio en {a.get('domicilio', '')}" for a in lista_abogados]) if lista_abogados else "N/A"
                    
                    ag_nombres = " y ".join([a.get('nombre', '') for a in lista_agrimensores]) if lista_agrimensores else "N/A"
                    ag_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, CODIA {a.get('matricula', '')}, oficina en {a.get('domicilio', '')}" for a in lista_agrimensores]) if lista_agrimensores else "N/A"
                    
                    no_nombres = " y ".join([a.get('nombre', '') for a in lista_notarios]) if lista_notarios else "N/A"
                    no_generales = "; y ".join([f"{a.get('nombre', '')}, Notario, Matrícula {a.get('matricula', '')}, cédula No. {a.get('cedula', '')}" for a in lista_notarios]) if lista_notarios else "N/A"
                    
                    al_nombres = " y ".join([a.get('nombre', '') for a in lista_alguaciles]) if lista_alguaciles else "N/A"
                    al_generales = "; y ".join([f"{a.get('nombre', '')}, cédula No. {a.get('cedula', '')}, Alguacil del {a.get('matricula', '')}" for a in lista_alguaciles]) if lista_alguaciles else "N/A"

                    in_descripciones = "\n".join([f"Parcela {i.get('parcela', '')}, DC {i.get('dc', '')}, {i.get('provincia', '')}. Superficie: {i.get('superficie', '')}. Coordenadas: {i.get('coordenadas', i.get('coord', ''))}. Sustentado en {i.get('tipo_doc', '')} No. {i.get('numero', '')}, Libro {i.get('libro', '')}, Folio {i.get('folio', '')}." for i in lista_inmuebles]) if lista_inmuebles else "N/A"

                    pg_detalles = "\n".join([f"Monto de {p.get('monto', '')} pagadero mediante {p.get('forma', '')} ({p.get('banco', '')})." for p in lista_pagos]) if lista_pagos else "N/A"
                    
                    impuestos_str = ", ".join(impuestos_pagados) if impuestos_pagados else "N/A"
                    
                    datos_para_word = {
                        "expediente": exp_seleccionado, "fecha_hoy": datetime.now().strftime("%d de %B del %Y"),
                        "tipo_caso": tipo_caso_db, "organo_jurisdiccional": organo_db_real,
                        "clientes_nombres": cl_nombres, "clientes_generales": cl_generales,
                        "apoderados_nombres": ap_nombres, "apoderados_generales": ap_generales,
                        "abogados_nombres": ab_nombres, "abogados_generales": ab_generales,
                        "agrimensores_nombres": ag_nombres, "agrimensores_generales": ag_generales,
                        "notarios_nombres": no_nombres, "notarios_generales": no_generales,
                        "alguaciles_nombres": al_nombres, "alguaciles_generales": al_generales,
                        "inmuebles_detalle": in_descripciones,
                        "pagos_detalle": pg_detalles, "testigos": testigos,
                        "impuestos_pagados": impuestos_str, "inventario_anexos": inventario_anexos
                    }
                    
                    archivos_generados = 0
                    for p in plantillas_elegidas:
                        try:
                            # 1. Descarga plantilla
                            bytes_plantilla = supabase.storage.from_("plantillas_maestras").download(f"{ruta_carpeta}/{p}")
                            ruta_temp = f"temp_{p}"
                            with open(ruta_temp, "wb") as f: f.write(bytes_plantilla)
                                
                            # 2. Rellena el Word
                            buffer = generar_documento_word(ruta_temp, datos_para_word)
                            
                            if buffer:
                                prefijo = exp_seleccionado if exp_seleccionado != "-- Expediente Independiente (Modo Manual) --" else "Doc"
                                nombre_doc_final = f"{prefijo}_{p}"
                                
                                # 3. Botón para descarga inmediata
                                st.download_button(label=f"⬇️ Descargar Word: {nombre_doc_final}", data=buffer, file_name=nombre_doc_final)
                                archivos_generados += 1
                                
                                # 4. 💾 GUARDADO MAESTRO EN BÓVEDA DIGITAL
                                if exp_seleccionado != "-- Expediente Independiente (Modo Manual) --":
                                    año_actual = datetime.now().strftime("%Y")
                                    tipo_folder = tipo_caso_db.replace("/", "-").replace(" ", "_")
                                    ruta_anexos = f"boveda_digital/Expedientes_{año_actual}/{tipo_folder}/{exp_seleccionado}"
                                    if not os.path.exists(ruta_anexos):
                                        os.makedirs(ruta_anexos)
                                    with open(os.path.join(ruta_anexos, nombre_doc_final), "wb") as f_out:
                                        f_out.write(buffer.getvalue())

                                    # 5. ⏰ GENERADOR DE ALERTAS Y PLAZOS
                                    reglas_plazos = {
                                        "aviso_de_mensura": (15, "Notificación a colindantes y publicidad"),
                                        "contrato_venta": (60, "Pago de impuestos DGII (Transferencia)"),
                                        "saneamiento": (60, "Plazo máximo para trabajos técnicos"),
                                        "recurso_revision": (30, "Plazo de interposición"),
                                        "litis": (15, "Octava franca de ley para emplazamiento")
                                    }
                                    nombre_minuscula = p.lower()
                                    plazo_dias, descripcion_alerta = 0, ""
                                    
                                    for clave, datos_plazo in reglas_plazos.items():
                                        if clave in nombre_minuscula:
                                            plazo_dias, descripcion_alerta = datos_plazo
                                            break
                                            
                                    if plazo_dias > 0:
                                        fv = datetime.now() + timedelta(days=plazo_dias)
                                        try:
                                            exp_data_nube = supabase.table("expedientes").select("alertas").eq("id_expediente", exp_seleccionado).execute().data[0]
                                            alertas_ext = exp_data_nube.get("alertas", []) or []
                                            alertas_ext.append({
                                                "fecha_creacion": datetime.now().strftime("%Y-%m-%d"),
                                                "documento_origen": p,
                                                "descripcion": descripcion_alerta,
                                                "fecha_vencimiento": fv.strftime("%Y-%m-%d"),
                                                "estado": "Pendiente"
                                            })
                                            supabase.table("expedientes").update({"alertas": alertas_ext}).eq("id_expediente", exp_seleccionado).execute()
                                            st.toast(f"⏰ Alerta conectada al Radar: Vence en {plazo_dias} días.")
                                        except Exception:
                                            pass

                            if os.path.exists(ruta_temp): os.remove(ruta_temp)
                        except Exception as e:
                            st.error(f"❌ Falló {p}: {e}")
                            
                    if archivos_generados > 0:
                        st.success(f"🎉 ¡Éxito Total! {archivos_generados} documento(s) forjados y enviados directo a su Archivo Digital.")
                        st.balloons()
        else:
            st.info("📂 Carpeta vacía en la nube. Vaya a 'Bóveda de Modelos' para subir sus plantillas de Word.")

    with tab_boveda:
        st.subheader("Gestión de Archivos Maestros en la Nube (.docx)")
        if st.session_state.get("rol_actual") == "Presidente Fundador":
            with st.form("form_subida_plantillas", clear_on_submit=True):
                col_up1, col_up2 = st.columns([2, 3])
                with col_up1: destino = st.selectbox("Cargar en:", carpetas_base)
                with col_up2: archivos_subidos = st.file_uploader("Arrastrar Plantillas Nuevas", type=["docx"], accept_multiple_files=True)
                btn_subir = st.form_submit_button("☁️ Subir y Guardar en la Nube", use_container_width=True)

            if btn_subir and archivos_subidos:
                for archivo in archivos_subidos:
                    try:
                        supabase.storage.from_("plantillas_maestras").upload(
                            path=f"{destino}/{archivo.name}", file=archivo.getvalue(),
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                        )
                    except Exception as e: st.error(f"Error con {archivo.name}: {e}")
                st.success(f"✅ Se guardaron las plantillas en la nube corporativa.")
                st.rerun()

            st.divider()
            st.write("**⚠️ Zona de Eliminación**")
            cat_ver = st.selectbox("Revisar categoría para borrar:", carpetas_base)
            try:
                archivos_en_cat = [f["name"] for f in supabase.storage.from_("plantillas_maestras").list(cat_ver) if f["name"].endswith(".docx")]
            except: archivos_en_cat = []
                
            if archivos_en_cat:
                c_del1, c_del2 = st.columns([3, 1])
                archivo_borrar = c_del1.selectbox("Seleccione para eliminar:", archivos_en_cat)
                if c_del2.button("🔥 Eliminar Definitivamente"):
                    supabase.storage.from_("plantillas_maestras").remove([f"{cat_ver}/{archivo_borrar}"])
                    st.success("Eliminado.")
                    st.rerun()
        else:
            st.error("⛔ Acceso Restringido para el Presidente Fundador.")

def vista_honorarios():
    import streamlit as st
    from datetime import datetime
    from database import db as supabase  # ☁️ Conexión maestra a la nube

    st.title("💳 Gestión de Honorarios y Facturación")
    st.markdown("### 💰 Cotizaciones, Acuerdos y Estado de Cuentas")

    # 🛡️ Seguridad: Solo Administradores ven el dinero
    if st.session_state.get("rol_actual") != "Presidente Fundador":
        st.error("⛔ Acceso Denegado. Área exclusiva de la Presidencia.")
        return

    # --- 1. VINCULACIÓN AL CASO (DESDE SUPABASE) ---
    try:
        respuesta = supabase.table("expedientes").select("*").execute()
        db_expedientes_cloud = {row['id_expediente']: row for row in respuesta.data}
    except Exception:
        db_expedientes_cloud = {}

    lista_exps = ["-- Cliente Independiente --"] + list(db_expedientes_cloud.keys())
    exp_seleccionado = st.selectbox("Vincular Facturación a Expediente:", lista_exps)

    cliente_proforma = "Cliente no especificado"
    asunto_proforma = "Servicios Legales / Agrimensura"

    if exp_seleccionado != "-- Cliente Independiente --":
        # Extraemos los datos del expediente para inyectarlos en la proforma
        exp_data = db_expedientes_cloud[exp_seleccionado]
        asunto_proforma = exp_data.get("asunto", "Servicios Legales")
        
        # Intentamos obtener el nombre del primer cliente
        lista_clientes = exp_data.get("clientes", [])
        if lista_clientes and isinstance(lista_clientes, list) and len(lista_clientes) > 0:
            cliente_proforma = lista_clientes[0].get("nombre", "Cliente del Expediente")
            
        st.success(f"🔗 Vinculado a Expediente: **{asunto_proforma}** (Cliente: {cliente_proforma})")

    st.write("---")

    # --- 2. ACUERDOS Y FORMAS DE PAGO ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 Acuerdos y Condiciones")
        tipo_acuerdo = st.selectbox("Tipo de Acuerdo de Honorarios:", [
            "Monto Fijo (Suma Alzada)",
            "Cuota Litis (Porcentaje de los resultados)",
            "Iguala Mensual (Servicios recurrentes)",
            "Tarifa por Hora",
            "Pago por Etapa / Hito Catastral"
        ])
        
        plan_pago = st.selectbox("Plan de Pago Estipulado:", [
            "50% Avance Inicial / 50% Contra Entrega",
            "100% Por Adelantado",
            "30% Inicio / 30% Proceso / 40% Final",
            "Pagos Mensuales Fijos",
            "Al Finalizar el Caso (Cuota Litis)"
        ])

    with col2:
        st.subheader("💵 Métodos de Pago")
        forma_pago = st.selectbox("Forma de Pago Esperada:", [
            "Transferencia Bancaria",
            "Depósito en Cuenta",
            "Cheque Certificado",
            "Cheque de Administración",
            "Efectivo"
        ])
        moneda = st.selectbox("Moneda de Facturación:", ["RD$ (Pesos Dominicanos)", "US$ (Dólares Estadounidenses)"])

    # --- 3. CONCEPTOS A FACTURAR (DINÁMICO) ---
    st.write("---")
    st.subheader("🛒 Conceptos y Servicios")
    
    if "cant_conceptos" not in st.session_state:
        st.session_state["cant_conceptos"] = 1

    c_btn1, c_btn2 = st.columns([1, 4])
    if c_btn1.button("➕ Agregar Concepto"): st.session_state["cant_conceptos"] += 1
    if c_btn2.button("➖ Quitar") and st.session_state["cant_conceptos"] > 1: st.session_state["cant_conceptos"] -= 1

    subtotal = 0.0
    conceptos_factura = []
    
    for i in range(st.session_state["cant_conceptos"]):
        c1, c2, c3 = st.columns([3, 1, 1])
        desc = c1.text_input(f"Descripción del Servicio {i+1}:", placeholder="Ej. Saneamiento Parcela 44...", key=f"fac_desc_{i}")
        cant = c2.number_input("Cantidad:", min_value=1, value=1, key=f"fac_cant_{i}")
        precio = c3.number_input("Precio Unitario:", min_value=0.0, value=0.0, step=1000.0, key=f"fac_prec_{i}")
        
        total_linea = cant * precio
        subtotal += total_linea
        if desc: conceptos_factura.append({"desc": desc, "cant": cant, "precio": precio, "total": total_linea})

    # --- 4. IMPUESTOS Y RETENCIONES ---
    st.write("---")
    st.subheader("📊 Impuestos y Retenciones")
    col_imp1, col_imp2, col_imp3 = st.columns(3)
    aplicar_itbis = col_imp1.checkbox("➕ Sumar ITBIS (18%)", value=False) # Falso por defecto para honorarios legales
    retencion_isr = col_imp2.checkbox("➖ Retención ISR (10% - Empresas)")
    retencion_itbis = col_imp3.checkbox("➖ Retención ITBIS (100% o 30%)")

    itbis = subtotal * 0.18 if aplicar_itbis else 0.0
    isr = subtotal * 0.10 if retencion_isr else 0.0
    ret_itbis = itbis if retencion_itbis else 0.0
    
    total_pagar = subtotal + itbis - isr - ret_itbis

    # --- 5. CUENTAS BANCARIAS OFICIALES ---
    st.write("---")
    st.subheader("🏦 Cuentas Bancarias para Depósitos")
    st.info("Estas cuentas oficiales de la firma se incluirán en el recibo/proforma del cliente.")
    
    c_banco1, c_banco2 = st.columns(2)
    with c_banco1:
        st.success("**🏦 Banco BHD**\n\nTipo: **Cuenta de Ahorros**\n\nNo. Cuenta: **08010850011**")
    with c_banco2:
        st.info("**🏦 Banco de Reservas**\n\nTipo: **Cuenta de Ahorros**\n\nNo. Cuenta: **9601369253**")

    # --- 6. RESUMEN Y EMISIÓN ---
    st.write("---")
    st.markdown(f"### 🧾 Resumen Total a Pagar: {moneda} {total_pagar:,.2f}")
    
    if st.button("🚀 Registrar Acuerdo y Generar Proforma", type="primary", use_container_width=True):
        if conceptos_factura:
            st.success("✅ Acuerdo de honorarios estructurado correctamente.")
            
            # --- VISTA PREVIA DEL RECIBO ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center;'>📄 Proforma de Honorarios y Servicios</h3>", unsafe_allow_html=True)
                col_prof1, col_prof2 = st.columns(2)
                col_prof1.markdown(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y')}")
                col_prof1.markdown(f"**Cliente:** {cliente_proforma}")
                col_prof2.markdown(f"**Expediente:** {exp_seleccionado}")
                col_prof2.markdown(f"**Asunto:** {asunto_proforma}")
                st.divider()
                st.markdown(f"**Términos del Acuerdo:** {tipo_acuerdo}")
                st.markdown(f"**Plan de Pago:** {plan_pago}")
                st.markdown(f"**Método de Pago:** {forma_pago}")
                st.divider()
                
                # Detalle de servicios
                for c in conceptos_factura:
                    st.write(f"🔹 **{c['cant']}x** {c['desc']}  .................  **{moneda} {c['total']:,.2f}**")
                
                st.divider()
                st.write(f"Subtotal: {moneda} {subtotal:,.2f}")
                if aplicar_itbis: st.write(f"ITBIS (18%): {moneda} {itbis:,.2f}")
                if retencion_isr: st.write(f"Retención ISR (10%): -{moneda} {isr:,.2f}")
                if retencion_itbis: st.write(f"Retención ITBIS: -{moneda} {ret_itbis:,.2f}")
                
                st.markdown(f"#### **MONTO TOTAL: {moneda} {total_pagar:,.2f}**")
                st.divider()
                
                # Cuentas bancarias impresas en la proforma
                st.markdown("**Realizar pagos exclusivamente a las siguientes cuentas a nombre de la firma:**")
                st.markdown("✅ **Banco BHD:** Cuenta de Ahorros # **08010850011**")
                st.markdown("✅ **Banco de Reservas:** Cuenta de Ahorros # **9601369253**")
                
        else:
            st.error("⚠️ Debe agregar al menos un servicio o concepto con su valor antes de generar la proforma.")

# ==========================================
# 🎨 APLICADOR DE DISEÑO GLOBAL
# ==========================================
if "color_primario" in st.session_state:
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {st.session_state["color_fondo"]};
            font-family: {st.session_state["tipo_letra"]};
        }}
        .stButton>button[kind="primary"] {{
            background-color: {st.session_state["color_primario"]};
            border-color: {st.session_state["color_primario"]};
        }}
        h1, h2, h3 {{
            color: {st.session_state["color_primario"]} !important;
            font-family: {st.session_state["tipo_letra"]};
        }}
        </style>
    """, unsafe_allow_html=True)
# =====================================================================
# 🔐 CANDADO MAESTRO Y NAVEGACIÓN DINÁMICA (AL FONDO DEL ARCHIVO)
# =====================================================================
import streamlit as st
from database import db as supabase # Asegúrese de que este import coincida con su sistema

# 1. Inicializar la memoria de seguridad del sistema
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""
if "rol_actual" not in st.session_state:
    st.session_state.rol_actual = ""

# ==========================================
# 🛑 LA PUERTA DE HIERRO (LOGIN GLOBAL)
# ==========================================
if not st.session_state.autenticado:
    # Ocultamos el menú lateral nativo de Streamlit con un pequeño truco visual
    st.markdown("""<style>[data-testid="collapsedControl"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; color: #1E3A8A; font-size: 4rem;'>🏛️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AboAgrim Pro</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Acceso Restringido</h4>", unsafe_allow_html=True)
    
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    
    with col_centro:
        with st.container(border=True):
            st.write("Por favor, identifíquese para acceder a la bóveda:")
            u_login = st.text_input("Usuario:")
            p_login = st.text_input("PIN de Acceso:", type="password")
            
            if st.button("🔓 Iniciar Sesión", use_container_width=True, type="primary"):
                if u_login and p_login:
                    try:
                        # Vamos a Supabase a verificar si existe y si la clave es correcta
                        res = supabase.table("usuarios").select("*").eq("nombre_usuario", u_login).eq("pin_acceso", p_login).execute()
                        
                        if res.data and len(res.data) > 0:
                            usuario_valido = res.data[0]
                            st.session_state.autenticado = True
                            st.session_state.usuario_actual = usuario_valido["nombre_usuario"]
                            st.session_state.rol_actual = usuario_valido["rol"]
                            st.rerun() # Recargamos la página para abrir el sistema
                        else:
                            # 🔑 RESPALDO MASTER (Por si Supabase falla o usted queda fuera)
                            if u_login == "JhonnyMatos" and p_login == "0681":
                                st.session_state.autenticado = True
                                st.session_state.usuario_actual = "Jhonny Matos"
                                st.session_state.rol_actual = "Presidente Fundador"
                                st.rerun()
                            else:
                                st.error("❌ Usuario o PIN incorrectos. Acceso denegado.")
                    except Exception as e:
                        st.error(f"Error en los servidores de autenticación: {e}")
                else:
                    st.warning("⚠️ Ingrese credenciales.")

# ==========================================
# 🟢 EL SISTEMA INTERNO (Si ya pasó el Login)
# ==========================================
else:
    # Recuperamos el menú lateral nativo
    st.markdown("""<style>[data-testid="collapsedControl"] {display: block;}</style>""", unsafe_allow_html=True)
    
    # --- MENÚ LATERAL DINÁMICO ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.usuario_actual}")
        st.caption(f"🛡️ Nivel: **{st.session_state.rol_actual}**")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
            
        st.divider()
        st.markdown("**Navegación Principal:**")
        
        opciones_menu = [
            "🏠 Mando Central", 
            "👤 Registro Maestro", 
            "📁 Archivo Digital", 
            "⏰ Alertas y Plazos"
        ]
        
        # --- ⚖️ MATRIZ DE PERMISOS INTELIGENTE ---
        rol = st.session_state.rol_actual
        es_presidente = (rol == "Presidente Fundador")
        
        puede_ver_plantillas = es_presidente or (rol in ["Abogado", "Agrimensor"])
        puede_ver_honorarios = es_presidente or (rol in ["Contabilidad"]) 
        puede_ver_config = es_presidente # Exclusivo de la Presidencia
        
        if puede_ver_plantillas:
            opciones_menu.append("📄 Plantillas Auto")
        if puede_ver_honorarios:
            opciones_menu.append("💳 Gestión de Honorarios")
        if puede_ver_config:
            opciones_menu.append("⚙️ Configuración")

        # ESTO DIBUJA LOS BOTONES DENTRO DE LA BARRA LATERAL
        seleccion = st.radio("Módulos", opciones_menu, label_visibility="collapsed")
        
        st.divider()
        st.caption("📍 AboAgrim Pro | Santiago")

    # --- RUTAS DE NAVEGACIÓN (Enlazando sus funciones) ---
    # ESTO VA AFUERA DE LA BARRA (Para que el contenido salga en el centro)
    if seleccion == "🏠 Mando Central":
        vista_mando()
    elif seleccion == "👤 Registro Maestro":
        vista_registro_maestro()
    elif seleccion == "📁 Archivo Digital":
        vista_archivo_digital()
    elif seleccion == "⏰ Alertas y Plazos":
        vista_alertas_plazos()
    elif seleccion == "📄 Plantillas Auto":
        vista_plantillas()
    elif seleccion == "💳 Gestión de Honorarios":
        vista_honorarios()
    elif seleccion == "⚙️ Configuración":
        vista_configuracion()
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
