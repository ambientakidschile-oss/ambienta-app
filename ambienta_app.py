import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Ambienta Kids CRM", page_icon="🌸", layout="wide")

# Conexión con Google Sheets
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para formatear RUT automáticamente
def formatear_rut(rut_sucio):
    rut = rut_sucio.replace(".", "").replace("-", "").upper()
    if len(rut) < 2: return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"

# --- CARGA DE DATOS ---
def cargar_hoja(sheet_name, cols):
    try: 
        return conn.read(spreadsheet=url_planilla, worksheet=sheet_name)
    except: 
        return pd.DataFrame(columns=cols)

df_insumos = cargar_hoja("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_hoja("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Cumpleaños', 'Dirección'])
df_ventas = cargar_hoja("Ventas", ['Fecha', 'RUT_Cliente', 'Producto', 'Total'])

st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("SELECCIONE MÓDULO:", ["👥 Clientes", "📦 Inventario", "👩‍🍳 Producción", "🛒 Caja y Ventas"])

# --- MÓDULO CLIENTES ---
if menu == "👥 Clientes":
    st.header("👥 Gestión de Clientes y Fidelización")
    
    tab1, tab2 = st.tabs(["🆕 Registrar Nuevo", "📜 Historial por RUT"])

    with tab1:
        # 'clear_on_submit=True' limpia las celdas automáticamente al guardar
        with st.form("nuevo_cliente", clear_on_submit=True):
            st.subheader("Datos del Cliente")
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre Completo")
            rut_in = c1.text_input("RUT (ej: 12345678k)")
            whatsapp = c2.text_input("WhatsApp (+569...)")
            correo = c2.text_input("Correo Electrónico")
            
            st.divider()
            c3, c4 = st.columns(2)
            # Aquí está el campo de Cumpleaños
            cumple = c3.date_input("Fecha de Cumpleaños", min_value=datetime(1940, 1, 1))
            dirección = c4.text_input("Dirección de Despacho")

            if st.form_submit_button("💾 GUARDAR Y LIMPIAR"):
                if nombre and rut_in:
                    rut_fmt = formatear_rut(rut_in)
                    nuevo_c = pd.DataFrame([{
                        "Nombre": nombre, "RUT": rut_fmt, "WhatsApp": whatsapp, 
                        "Correo": correo, "Cumpleaños": str(cumple), "Dirección": dirección
                    }])
                    df_c_final = pd.concat([df_clientes, nuevo_c], ignore_index=True)
                    conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=df_c_final)
                    st.success(f"¡Cliente {nombre} registrado!")
                    st.rerun()
                else:
                    st.error("Nombre y RUT son obligatorios")

    with tab2:
        if not df_clientes.empty:
            busqueda = st.selectbox("Buscar por Nombre:", df_clientes['Nombre'].unique())
            rut_sel = df_clientes[df_clientes['Nombre'] == busqueda]['RUT'].values[0]
            
            st.info(f"Historial para el RUT: {rut_sel}")
            # Filtra ventas por RUT
            compras = df_ventas[df_ventas['RUT_Cliente'] == rut_sel]
            if not compras.empty:
                st.dataframe(compras)
            else:
                st.write("No registra compras aún.")
        else:
            st.warning("No hay clientes registrados.")

    st.subheader("Base de Datos General")
    st.dataframe(df_clientes, use_container_width=True)

# --- LOS OTROS MÓDULOS (Resumen para evitar errores) ---
elif menu == "📦 Inventario":
    st.header("📦 Inventario")
    st.dataframe(df_insumos)

elif menu == "👩‍🍳 Producción":
    st.header("👩‍🍳 Producción")
    st.write("Módulo listo para cálculos.")

elif menu == "🛒 Caja y Ventas":
    st.header("🛒 Registro de Ventas")
    st.write("Asocia ventas por RUT en la siguiente actualización.")
