import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Ambienta Kids Pro", page_icon="🌸", layout="wide")

url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("SELECCIONE MÓDULO:", 
    ["📦 Inventario", "👩‍🍳 Producción", "👥 Clientes", "🛒 Caja y Ventas"])

# CARGA DE DATOS (Con nuevas columnas para clientes)
def cargar_datos(nombre_hoja, columnas):
    try:
        return conn.read(spreadsheet=url_planilla, worksheet=nombre_hoja)
    except:
        return pd.DataFrame(columns=columnas)

df_insumos = cargar_datos("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_datos("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Dirección'])
df_ventas = cargar_datos("Ventas", ['Fecha', 'Cliente', 'Producto', 'Total'])

# --- MÓDULO 1: INVENTARIO ---
if menu == "📦 Inventario":
    st.header("📦 Gestión de Insumos")
    with st.form("form_inv"):
        col1, col2 = st.columns(2)
        n = col1.text_input("Nombre del Material")
        u = col1.selectbox("Unidad de Medida", ["Metros", "Unidades", "Gramos", "Rollos"])
        p = col2.number_input("Precio Compra $", min_value=0)
        c = col2.number_input("Cantidad que trae", min_value=0.1)
        
        if st.form_submit_button("💾 Guardar Material"):
            if n:
                nuevo = pd.DataFrame([{"Material": n, "Costo_U": p/c, "Unidad": u}])
                df_final = pd.concat([df_insumos, nuevo], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Insumos", data=df_final)
                st.success(f"¡{n} guardado!"); st.rerun()

    st.subheader("Inventario Actual")
    st.dataframe(df_insumos, use_container_width=True)

# --- MÓDULO 2: PRODUCCIÓN ---
elif menu == "👩‍🍳 Producción":
    st.header("👩‍🍳 Calculadora de Costos")
    if not df_insumos.empty:
        mat = st.selectbox("Seleccionar Insumo:", df_insumos['Material'])
        cant = st.number_input("Cantidad a usar:", min_value=0.1)
        fila_mat = df_insumos[df_insumos['Material'] == mat].iloc[0]
        costo_r = fila_mat['Costo_U'] * cant
        st.metric(f"Costo por {cant} {fila_mat['Unidad']}", f"${costo_r:,.2f}")
    else: st.warning("Carga insumos primero.")

# --- MÓDULO 3: CLIENTES (ACTUALIZADO CON RUT Y CORREO) ---
elif menu == "👥 Clientes":
    st.header("👥 Base de Datos de Clientes")
    with st.form("form_cli"):
        col_c1, col_c2 = st.columns(2)
        nom = col_c1.text_input("Nombre Completo")
        rut = col_c1.text_input("RUT (ej: 12.345.678-9)")
        tel = col_c2.text_input("WhatsApp (+569...)")
        mail = col_c2.text_input("Correo Electrónico")
        dire = st.text_input("Dirección de Despacho")
        
        if st.form_submit_button("💾 REGISTRAR CLIENTE"):
            if nom and rut:
                nuevo_c = pd.DataFrame([{"Nombre": nom, "RUT": rut, "WhatsApp": tel, "Correo": mail, "Dirección": dire}])
                df_c_final = pd.concat([df_clientes, nuevo_c], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=df_c_final)
                st.success("Cliente guardado exitosamente"); st.rerun()
            else:
                st.error("Nombre y RUT son obligatorios")
    
    st.subheader("Lista de Clientes Registrados")
    st.dataframe(df_clientes, use_container_width=True)

# --- MÓDULO 4: CAJA Y VENTAS ---
elif menu == "🛒 Caja y Ventas":
    st.header("🛒 Registro de Ventas")
    with st.form("form_vta"):
        cli = st.selectbox("Cliente:", df_clientes['Nombre'] if not df_clientes.empty else ["Sin Clientes"])
        prod = st.text_input("Producto")
        tot = st.number_input("Total $", min_value=0)
        if st.form_submit_button("✅ Finalizar Venta"):
            nv = pd.DataFrame([{"Fecha": pd.Timestamp.now().strftime("%d/%m/%Y"), "Cliente": cli, "Producto": prod, "Total": tot}])
            df_v_final = pd.concat([df_ventas, nv], ignore_index=True)
            conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_final)
            st.success("Venta registrada"); st.rerun()
    st.dataframe(df_ventas, use_container_width=True)