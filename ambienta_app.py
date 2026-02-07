import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Ambienta Kids CRM", page_icon="🌸", layout="wide")

# Conexión principal
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def formatear_rut(rut_sucio):
    rut = rut_sucio.replace(".", "").replace("-", "").upper()
    if len(rut) < 2: return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"

def cargar_hoja(nombre, columnas):
    try: return conn.read(spreadsheet=url_planilla, worksheet=nombre)
    except: return pd.DataFrame(columns=columnas)

# Cargar bases de datos
df_insumos = cargar_hoja("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_hoja("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Cumpleaños', 'Dirección'])
df_ventas = cargar_hoja("Ventas", ['Fecha', 'RUT_Cliente', 'Producto', 'Total'])

st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("MENÚ:", ["👥 Clientes", "📦 Inventario", "🛒 Caja y Ventas"])

# --- MÓDULO CLIENTES ---
if menu == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    tab1, tab2 = st.tabs(["🆕 Registrar Nuevo", "📜 Historial por RUT"])

    with tab1:
        with st.form("nuevo_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Completo")
            rut_in = col1.text_input("RUT (ej: 12345678k)")
            whatsapp = col2.text_input("WhatsApp (+569...)")
            correo = col2.text_input("Correo Electrónico")
            
            st.divider()
            col3, col4 = st.columns(2)
            cumple = col3.date_input("Fecha de Cumpleaños", min_value=datetime(1940, 1, 1))
            direc = col4.text_input("Dirección de Despacho")

            if st.form_submit_button("💾 GUARDAR CLIENTE"):
                if nombre and rut_in:
                    rut_f = formatear_rut(rut_in)
                    nueva_fila = pd.DataFrame([{"Nombre": nombre, "RUT": rut_f, "WhatsApp": whatsapp, "Correo": correo, "Cumpleaños": str(cumple), "Dirección": direc}])
                    df_up = pd.concat([df_clientes, nueva_fila], ignore_index=True)
                    conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=df_up)
                    st.success(f"¡{nombre} guardado!"); st.rerun()

    with tab2:
        if not df_clientes.empty:
            busq = st.selectbox("Seleccione Cliente:", df_clientes['Nombre'].unique())
            r_sel = df_clientes[df_clientes['Nombre'] == busq]['RUT'].values[0]
            st.info(f"Historial RUT: {r_sel}")
            hist = df_ventas[df_ventas['RUT_Cliente'] == r_sel]
            st.dataframe(hist)
        else: st.warning("No hay clientes registrados.")

    st.subheader("Base de Datos General")
    st.dataframe(df_clientes, use_container_width=True)

# --- MÓDULO VENTAS ---
elif menu == "🛒 Caja y Ventas":
    st.header("🛒 Registro de Ventas")
    if df_clientes.empty: st.warning("Registre un cliente primero.")
    else:
        with st.form("vta", clear_on_submit=True):
            c_op = st.selectbox("Cliente:", df_clientes['Nombre'] + " | " + df_clientes['RUT'])
            r_vta = c_op.split(" | ")[1]
            prod = st.text_input("Producto")
            monto = st.number_input("Total $", min_value=0)
            if st.form_submit_button("✅ REGISTRAR VENTA"):
                nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "RUT_Cliente": r_vta, "Producto": prod, "Total": monto}])
                df_v_up = pd.concat([df_ventas, nv], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_up)
                st.success("Venta asociada al cliente!"); st.rerun()
    st.dataframe(df_ventas)

# --- MÓDULO INVENTARIO ---
elif menu == "📦 Inventario":
    st.header("📦 Inventario")
    st.dataframe(df_insumos)
