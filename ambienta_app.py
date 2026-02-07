import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ambienta Kids POS", page_icon="🌸", layout="wide")

# --- 1. CONEXIÓN Y FUNCIONES DE SEGURIDAD ---
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(hoja, columnas):
    try:
        df = conn.read(spreadsheet=url_planilla, worksheet=hoja)
        if df is None: return pd.DataFrame(columns=columnas)
        # Convertir todo a texto para evitar errores de cálculo con RUTs
        if not df.empty:
            df = df.astype(str)
        return df
    except:
        return pd.DataFrame(columns=columnas)

def formatear_rut(rut_sucio):
    rut = str(rut_sucio).replace(".", "").replace("-", "").upper()
    if len(rut) < 2: return rut
    return f"{rut[:-1]}-{rut[-1]}"

# Carga de bases de datos
df_insumos = cargar_datos("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_datos("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Cumpleaños', 'Dirección'])
df_ventas = cargar_datos("Ventas", ['Fecha', 'RUT_Cliente', 'Producto', 'Total', 'Metodo_Pago'])

# Convertir columnas numéricas que sean necesarias para cálculos
try:
    if not df_insumos.empty: 
        df_insumos['Costo_U'] = pd.to_numeric(df_insumos['Costo_U'], errors='coerce').fillna(0)
    if not df_ventas.empty:
        df_ventas['Total'] = pd.to_numeric(df_ventas['Total'], errors='coerce').fillna(0)
except:
    pass

# Inicializar Carrito
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 2. MENÚ LATERAL ---
st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("IR A:", ["🛒 Caja POS", "📊 Salud Financiera", "👥 Clientes", "📦 Inventario", "👩‍🍳 Producción"])

# ==========================================
# MÓDULO 1: CAJA POS
# ==========================================
if menu == "🛒 Caja POS":
    st.header("🛒 Punto de Venta Profesional")
    
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.info("💡 Tip: Usa tu lector de código de barras en el recuadro de abajo.")
        
        prod_input = st.text_input("🔍 Escanear o Buscar Producto:", key="input_pos", placeholder="Escribe o escanea...")
        
        c1, c2 = st.columns(2)
        precio_input = c1.number_input("Precio $", min_value=0, step=100, key="price_pos")
        cant_input = c2.number_input("Cantidad", min_value=1, value=1, key="qty_pos")
        
        if st.button("➕ AGREGAR AL CARRO", use_container_width=True):
            if prod_input and precio_input > 0:
                subtotal = precio_input * cant_input
                st.session_state.carrito.append({
                    "Producto": prod_input,
                    "Precio": precio_input,
                    "Cantidad": cant_input,
                    "Subtotal": subtotal
                })
                st.success(f"Agregado: {prod_input}")
                st.rerun()

        st.divider()
        st.caption("Productos en el carro:")
        if st.session_state.carrito:
            df_carro = pd.DataFrame(st.session_state.carrito)
            st.dataframe(df_carro, use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.warning("El carrito está vacío.")

    with col_der:
        st.markdown("### 🧾 Resumen de Pago")
        total_a_pagar = sum(item['Subtotal'] for item in st.session_state.carrito)
        st.metric("TOTAL A PAGAR", f"${total_a_pagar:,.0f}")
        
        st.markdown("---")
        
        # Identificación de Cliente (Blindado contra errores)
        opciones = ["Público General"]
        if not df_clientes.empty:
            # Aseguramos que RUT y Nombre sean texto
            lista = (df_clientes['RUT'].astype(str) + " | " + df_clientes['Nombre'].astype(str)).tolist()
            opciones += lista
            
        cliente_sel = st.selectbox("Cliente (Boleta Nominativa):", opciones)
        
        if cliente_sel == "Público General":
            rut_final = "66666666-6"
        else:
            rut_final = cliente_sel.split(" | ")[0]

        metodo = st.radio("Método de Pago:", ["💳 Débito", "💳 Crédito", "💵 Efectivo", "📱 Transferencia"])

        st.markdown("---")
        
        if st.button("✅ FINALIZAR VENTA", type="primary", use_container_width=True):
            if st.session_state.carrito:
                resumen_txt = ", ".join([f"{x['Cantidad']}x {x['Producto']}" for x in st.session_state.carrito])
                
                nueva_venta = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "RUT_Cliente": rut_final,
                    "Producto": resumen_txt,
                    "Total": total_a_pagar,
                    "Metodo_Pago": metodo
                }])
                
                # Asegurar compatibilidad antes de guardar
                if not df_ventas.empty:
                    df_v_up = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                else:
                    df_v_up = nueva_venta
                    
                conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_up)
                
                msg = f"Hola! Gracias por tu compra en Ambienta Kids.\nDetalle: {resumen_txt}\nTotal: ${total_a_pagar:,.0f}\nMedio de pago: {metodo}"
                link_ws = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                
                st.balloons()
                st.success("¡Venta Registrada!")
                st.markdown(f"### [📲 Enviar Comprobante WhatsApp]({link_ws})")
                st.session_state.carrito = []
                st.rerun()
            else:
                st.error("El carrito está vacío")

# ==========================================
# MÓDULO 2: SALUD FINANCIERA (CORREGIDO)
# ==========================================
elif menu == "📊 Salud Financiera":
    st.header("📊 Tablero Financiero")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Costos Fijos")
        sueldo = st.number_input("Sueldo Deseado", value=600000, step=50000)
        arriendo = st.number_input("Arriendo/Gastos", value=250000, step=10000)
        ahorro = st.number_input("Meta Ahorro", value=150000)
        total_fijos = sueldo + arriendo + ahorro
        st.metric("Total Costos Fijos", f"${total_fijos:,.0f}")
    
    with c2:
        st.subheader("Punto de Equilibrio")
        precio_prom = st
