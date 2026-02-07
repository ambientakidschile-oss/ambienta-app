import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="Ambienta Kids POS", page_icon="🌸", layout="wide")

# --- 1. CONEXIÓN Y FUNCIONES DE SEGURIDAD ---
url_planilla = "https://docs.google.com/spreadsheets/d/18Ps9MX7EB7MNg29qVVbc_ITJuy4o536aJbrOrHidNhE/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos(hoja, columnas):
    try:
        df = conn.read(spreadsheet=url_planilla, worksheet=hoja)
        # Limpieza básica para evitar errores vacíos
        if df is None: return pd.DataFrame(columns=columnas)
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

# Inicializar Carrito de Compras en la memoria del navegador
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- 2. MENÚ LATERAL ---
st.sidebar.title("🌸 AMBIENTA KIDS")
menu = st.sidebar.radio("IR A:", ["🛒 Caja POS", "📊 Salud Financiera", "👥 Clientes", "📦 Inventario", "👩‍🍳 Producción"])

# ==========================================
# MÓDULO 1: CAJA POS (ESTILO SUPERMERCADO)
# ==========================================
if menu == "🛒 Caja POS":
    st.header("🛒 Punto de Venta Profesional")
    
    # Dividimos la pantalla: Izquierda (Buscador) | Derecha (Boleta)
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.info("💡 Tip: Usa tu lector de código de barras en el recuadro de abajo.")
        
        # BUSCADOR INTELIGENTE
        # Creamos una lista de productos disponibles desde Ventas anteriores o manual
        # (Aquí puedes conectar tu base de productos real si tienes una hoja de 'Productos')
        prod_input = st.text_input("🔍 Escanear o Buscar Producto:", key="input_pos", placeholder="Escribe o escanea...")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        precio_input = c1.number_input("Precio $", min_value=0, step=100, key="price_pos")
        cant_input = c2.number_input("Cantidad", min_value=1, value=1, key="qty_pos")
        
        # Botón grande para agregar
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
                st.rerun() # Refrescar para ver cambios

        st.divider()
        st.caption("Productos en el carro:")
        if st.session_state.carrito:
            df_carro = pd.DataFrame(st.session_state.carrito)
            # Mostramos tabla limpia
            st.dataframe(df_carro, use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.warning("El carrito está vacío.")

    with col_der:
        st.markdown("### 🧾 Resumen de Pago")
        
        # Cálculo del Total
        total_a_pagar = sum(item['Subtotal'] for item in st.session_state.carrito)
        st.metric("TOTAL A PAGAR", f"${total_a_pagar:,.0f}")
        
        st.markdown("---")
        
        # IDENTIFICACIÓN DEL CLIENTE (CORREGIDO EL ERROR AQUÍ)
        # Convertimos todo a texto (.astype(str)) para evitar el error numpy
        if not df_clientes.empty:
            lista_clientes = (df_clientes['RUT'].astype(str) + " | " + df_clientes['Nombre'].astype(str)).tolist()
            opciones = ["Público General"] + lista_clientes
        else:
            opciones = ["Público General"]
            
        cliente_sel = st.selectbox("Cliente (Boleta Nominativa):", opciones)
        
        # Lógica para obtener el RUT limpio
        if cliente_sel == "Público General":
            rut_final = "66666666-6"
        else:
            rut_final = cliente_sel.split(" | ")[0]

        # Forma de Pago
        metodo = st.radio("Método de Pago:", ["💳 Débito", "💳 Crédito", "💵 Efectivo", "📱 Transferencia"])

        st.markdown("---")
        
        # BOTÓN FINALIZAR
        if st.button("✅ FINALIZAR VENTA", type="primary", use_container_width=True):
            if st.session_state.carrito:
                # 1. Crear resumen texto
                resumen_txt = ", ".join([f"{x['Cantidad']}x {x['Producto']}" for x in st.session_state.carrito])
                
                # 2. Guardar en Base de Datos
                nueva_venta = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "RUT_Cliente": rut_final,
                    "Producto": resumen_txt,
                    "Total": total_a_pagar,
                    "Metodo_Pago": metodo
                }])
                
                df_v_up = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                conn.update(spreadsheet=url_planilla, worksheet="Ventas", data=df_v_up)
                
                # 3. Generar Link WhatsApp
                msg = f"Hola! Gracias por tu compra en Ambienta Kids.\nDetalle: {resumen_txt}\nTotal: ${total_a_pagar:,.0f}\nMedio de pago: {metodo}"
                link_ws = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                
                st.balloons()
                st.success("¡Venta Registrada!")
                st.markdown(f"### [📲 Enviar Comprobante WhatsApp]({link_ws})")
                
                # Limpiar carro
                st.session_state.carrito = []
            else:
                st.error("El carrito está vacío")

# ==========================================
# MÓDULO 2: SALUD FINANCIERA (TU SOLICITUD EXPERTA)
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
        precio_prom = st.number_input("Ticket Promedio Venta ($)", value=25000)
        costo_prom = st.number_input("Costo Promedio Insumos ($)", value=8000)
        margen = precio_prom - costo_prom
        
        if margin > 0:
            pe = total_fijos / margen
            st.metric("Debes vender (Unidades)", f"{int(pe)} productos")
            st.info(f"Meta en Dinero: ${int(pe * precio_prom):,.0f}")

# ==========================================
# MÓDULO 3: CLIENTES (RECUPERADO)
# ==========================================
elif menu == "👥 Clientes":
    st.header("👥 Gestión de Clientes")
    tab1, tab2 = st.tabs(["Nuevo Cliente", "Base de Datos"])
    
    with tab1:
        with st.form("new_client", clear_on_submit=True):
            nom = st.text_input("Nombre")
            rut = st.text_input("RUT")
            mail = st.text_input("Correo")
            if st.form_submit_button("Guardar"):
                nuevo = pd.DataFrame([{"Nombre": nom, "RUT": formatear_rut(rut), "Correo": mail, "WhatsApp": "", "Cumpleaños": "", "Dirección": ""}])
                conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=pd.concat([df_clientes, nuevo], ignore_index=True))
                st.success("Guardado")
                st.rerun()
    with tab2:
        st.dataframe(df_clientes)

# ==========================================
# MÓDULOS 4 y 5: INVENTARIO Y PRODUCCIÓN (RECUPERADOS)
# ==========================================
elif menu == "📦 Inventario":
    st.header("📦 Inventario de Insumos")
    st.dataframe(df_insumos)

elif menu == "👩‍🍳 Producción":
    st.header("👩‍🍳 Calculadora de Costos")
    st.write("Selecciona insumos del inventario para calcular costos unitarios.")
    if not df_insumos.empty:
        sel = st.selectbox("Insumo", df_insumos['Material'])
        precio = df_insumos[df_insumos['Material']==sel]['Costo_U'].values[0]
        st.write(f"Costo unitario: ${precio:,.0f}")
