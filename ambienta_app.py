import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# Configuración profesional
st.set_page_config(page_title="Ambienta Kids POS Pro", page_icon="🌸", layout="wide")

# 1. CONEXIÓN Y CARGA DE DATOS
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(hoja, columnas):
    try: return conn.read(spreadsheet=url_planilla, worksheet=hoja)
    except: return pd.DataFrame(columns=columnas)

df_insumos = cargar_datos("Insumos", ['Material', 'Costo_U', 'Unidad'])
df_clientes = cargar_datos("Clientes", ['Nombre', 'RUT', 'WhatsApp', 'Correo', 'Cumpleaños', 'Dirección'])
df_ventas = cargar_datos("Ventas", ['Fecha', 'RUT_Cliente', 'Producto', 'Total', 'Metodo_Pago'])

# Inicializar Carrito en la sesión
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Menú Lateral
st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("MÓDULOS:", ["🛒 Caja y Ventas (POS)", "📊 Salud Financiera", "👥 Clientes", "📦 Inventario", "👩‍🍳 Producción"])

# --- MÓDULO 3: CAJA Y VENTAS (PUNTO DE VENTA PROFESIONAL) ---
if menu == "🛒 Caja y Ventas (POS)":
    st.header("🛒 Punto de Venta Profesional")
    
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        # Buscador de Producto (Compatible con Lector USB)
        st.subheader("🔍 Escanear o Buscar Productos")
        # El lector USB escribe el código y presiona 'Enter' automáticamente
        prod_input = st.text_input("Escanear Código de Barras o Buscar por Palabra:", key="scan", placeholder="Use el lector o escriba aquí...")
        
        c1, c2 = st.columns(2)
        precio_v = c1.number_input("Precio Unitario $", min_value=0, step=100)
        cant_v = c2.number_input("Cantidad", min_value=1, value=1)

        if st.button("➕ AGREGAR AL CARRITO"):
            if prod_input:
                st.session_state.carrito.append({
                    "Producto": prod_input, 
                    "Precio": precio_v, 
                    "Cantidad": cant_v,
                    "Subtotal": precio_v * cant_v
                })
                st.rerun()

        # Visualización del Listado (Como en la imagen del POS)
        st.divider()
        st.subheader("📋 Detalle de la Venta")
        if st.session_state.carrito:
            df_pos = pd.DataFrame(st.session_state.carrito)
            st.table(df_pos)
            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.info("El carrito está vacío. Escanee un producto para comenzar.")

    with col_der:
        st.subheader("💰 Resumen y Pago")
        total_pago = sum(item['Subtotal'] for item in st.session_state.carrito)
        st.metric("TOTAL A PAGAR", f"${total_pago:,.0f}")

        # Identificación del Cliente (Boleta Nominativa)
        st.divider()
        opciones_c = ["Público General"] + (df_clientes['RUT'] + " | " + df_clientes['Nombre']).tolist()
        cliente_sel = st.selectbox("Boleta Nominativa (RUT):", opciones_c)
        rut_final = "66.666.666-6" if cliente_sel == "Público General" else cliente_sel.split(" | ")[0]

        # Método de Pago
        tipo_pago = st.radio("Forma de Pago:", ["Débito", "Crédito", "Efectivo", "Transferencia"], horizontal=True)

        if st.button("🏁 FINALIZAR VENTA", type="primary"):
            if st.session_state.carrito:
                # Guardar en base de datos
                productos_resumen = ", ".join([f"{i['Cantidad']}x {i['Producto']}" for i in st.session_state.carrito])
                nueva_v = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "RUT_Cliente": rut_final,
                    "Producto": productos_resumen,
                    "Total": total_pago,
                    "Metodo_Pago": tipo_pago
                }])
                df_v_up = pd.concat([df_ventas, nueva_v], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_up)
                
                # Generación de Link para WhatsApp (Simulación de Comprobante)
                texto_ws = f"Hola! Gracias por comprar en Ambienta Kids. Detalle: {productos_resumen}. Total: ${total_pago:,.0f}. Pagado con: {tipo_pago}."
                link_ws = f"https://wa.me/?text={urllib.parse.quote(texto_ws)}"
                
                st.success("✅ Venta registrada con éxito.")
                st.markdown(f"[📲 Enviar Comprobante por WhatsApp]({link_ws})")
                st.session_state.carrito = [] # Limpiar carrito
            else:
                st.error("Agregue productos antes de finalizar.")

# --- MANTENIMIENTO DE OTROS MÓDULOS (Salud Financiera, Clientes, etc.) ---
elif menu == "📊 Salud Financiera":
    st.header("📊 Inteligencia Comercial")
    # (Aquí va el código de punto de equilibrio compartido anteriormente)
    # ...
