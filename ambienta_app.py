import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de página nivel profesional
st.set_page_config(page_title="Ambienta Kids Pro ERP", page_icon="🌸", layout="wide")

# 1. CONEXIÓN A DATOS
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Funciones de Soporte
def formatear_rut(rut_sucio):
    rut = rut_sucio.replace(".", "").replace("-", "").upper()
    if len(rut) < 2: return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"

def cargar_datos(nombre_hoja, columnas):
    try:
        return conn.read(spreadsheet=url_planilla, worksheet=nombre_hoja)
    except:
        return pd.DataFrame(columns=columnas)

# Carga inicial de Dataframes
df_insumos = cargar_datos("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_datos("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Cumpleaños', 'Dirección'])
df_ventas = cargar_datos("Ventas", ['Fecha', 'RUT_Cliente', 'Producto', 'Total'])

# 2. MENÚ LATERAL
st.sidebar.title("🌸 AMBIENTA KIDS")
st.sidebar.write("Sistema de Gestión Integral")
menu = st.sidebar.radio("SELECCIONE MÓDULO:", 
    ["📊 Salud Financiera", "👥 Clientes", "🛒 Caja y Ventas", "📦 Inventario", "👩‍🍳 Producción"])

# --- MÓDULO 1: SALUD FINANCIERA (NUEVO) ---
if menu == "📊 Salud Financiera":
    st.header("📊 Inteligencia de Negocios y Punto de Equilibrio")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.subheader("🏢 Gastos Fijos y Metas")
        sueldo_deseado = st.number_input("Sueldo Mensual Deseado ($)", min_value=0, value=600000, step=50000)
        arriendo = st.number_input("Arriendo y Gastos Taller ($)", min_value=0, value=250000, step=10000)
        meta_ahorro = st.number_input("Meta de Utilidad / Reinversión ($)", min_value=0, value=150000)
        
        costos_fijos_totales = sueldo_deseado + arriendo + meta_ahorro
        st.metric("Total mensual a cubrir", f"${costos_fijos_totales:,.0f}")

    with col_f2:
        st.subheader("📈 Análisis de Productos")
        if not df_ventas.empty:
            ranking = df_ventas['Producto'].value_counts()
            top_prod = ranking.idxmax()
            st.success(f"🏆 Producto más pedido: **{top_prod}**")
            st.write(f"Has realizado {ranking.max()} ventas de este producto.")
        else:
            st.info("Registra ventas para analizar tu producto estrella.")

        precio_v_prom = st.number_input("Precio de Venta Promedio ($)", min_value=1, value=25000)
        # Costo variable estimado desde el inventario
        costo_v_prom = df_insumos['Costo_U'].mean() if not df_insumos.empty else 5000
        
        margen_unitario = precio_v_prom - costo_v_prom
        
        if margen_unitario > 0:
            pe_unidades = costos_fijos_totales / margen_unitario
            st.metric("Punto de Equilibrio (Unidades)", f"{round(pe_unidades)} ventas/mes")
            st.info(f"Venta mensual mínima: **${round(pe_unidades * precio_v_prom):,.0f}**")
        else:
            st.error("Alerta: El costo de materiales supera el precio de venta.")

# --- MÓDULO 2: CLIENTES (CRM ROBUSTO) ---
elif menu == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    t1, t2 = st.tabs(["🆕 Registrar Nuevo", "📜 Historial de Compras"])
    
    with t1:
        with st.form("form_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre Completo")
            r = c1.text_input("RUT (sin puntos ni guion)")
            w = c2.text_input("WhatsApp")
            m = c2.text_input("Correo")
            cumple = st.date_input("Fecha de Cumpleaños", min_value=datetime(1950,1,1))
            dir = st.text_input("Dirección de Despacho")
            
            if st.form_submit_button("💾 Guardar Cliente"):
                if n and r:
                    r_f = formatear_rut(r)
                    nuevo = pd.DataFrame([{"Nombre":n, "RUT":r_f, "WhatsApp":w, "Correo":m, "Cumpleaños":str(cumple), "Dirección":dir}])
                    df_c_final = pd.concat([df_clientes, nuevo], ignore_index=True)
                    conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=df_c_final)
                    st.success("Cliente registrado con éxito"); st.rerun()

    with t2:
        if not df_clientes.empty:
            busqueda = st.selectbox("Seleccione Cliente:", df_clientes['Nombre'].unique())
            rut_sel = df_clientes[df_clientes['Nombre'] == busqueda]['RUT'].values[0]
            st.subheader(f"Historial de {busqueda} (RUT: {rut_sel})")
            historial = df_ventas[df_ventas['RUT_Cliente'] == rut_sel]
            st.dataframe(historial, use_container_width=True)
        else: st.warning("No hay clientes registrados.")

# --- MÓDULO 3: CAJA Y VENTAS ---
elif menu == "🛒 Caja y Ventas":
    st.header("🛒 Registro de Ventas")
    if df_clientes.empty:
        st.error("⚠️ Debe registrar clientes primero.")
    else:
        with st.form("form_ventas", clear_on_submit=True):
            cliente_sel = st.selectbox("Cliente:", df_clientes['Nombre'] + " | " + df_clientes['RUT'])
            rut_v = cliente_sel.split(" | ")[1]
            prod_v = st.text_input("Producto Vendido")
            monto_v = st.number_input("Total Venta $", min_value=0)
            
            if st.form_submit_button("✅ Registrar Venta"):
                nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "RUT_Cliente": rut_v, "Producto": prod_v, "Total": monto_v}])
                df_v_final = pd.concat([df_ventas, nv], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_final)
                st.success("Venta guardada y asociada al RUT"); st.rerun()
    st.dataframe(df_ventas, use_container_width=True)

# --- MÓDULO 4: INVENTARIO ---
elif menu == "📦 Inventario":
    st.header("📦 Gestión de Insumos")
