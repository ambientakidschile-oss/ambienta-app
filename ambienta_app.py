import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ... (Mantener conexión y carga de datos igual que antes)

# Función para formatear RUT automáticamente al guardar
def formatear_rut(rut_sucio):
    # Elimina puntos y guiones previos
    rut = rut_sucio.replace(".", "").replace("-", "").upper()
    if len(rut) < 2: return rut
    cuerpo = rut[:-1]
    dv = rut[-1]
    # Retorna con puntos y guion: 12.345.678-9
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"

# --- MÓDULO 3: CLIENTES (VERSION CRM ROBUSTA) ---
elif menu == "👥 Clientes":
    st.header("👥 Gestión de Clientes y Fidelización")
    
    # Creamos pestañas para separar el registro del historial
    tab_registro, tab_historial = st.tabs(["🆕 Registrar Nuevo", "📜 Historial por RUT"])

    with tab_registro:
        # 'clear_on_submit=True' hace que los campos queden vacíos al pinchar el botón
        with st.form("form_fidelizacion", clear_on_submit=True):
            st.subheader("Datos del Cliente")
            c1, c2 = st.columns(2)
            
            nombre_c = c1.text_input("Nombre Completo")
            # El RUT se ingresa normal, el programa lo arregla solo al guardar
            rut_c = c1.text_input("RUT (ej: 123456789)")
            
            whatsapp_c = c2.text_input("WhatsApp (+569...)")
            correo_c = c2.text_input("Correo Electrónico")
            
            st.divider()
            st.subheader("Información VIP")
            c3, c4 = st.columns(2)
            
            # Viñeta de Cumpleaños
            fecha_cumple = c3.date_input("Fecha de Cumpleaños", min_value=datetime(1940, 1, 1))
            dirección_c = c4.text_input("Dirección de Despacho")
            
            if st.form_submit_button("💾 REGISTRAR Y LIMPIAR"):
                if nombre_c and rut_c:
                    # Formateamos el RUT antes de enviarlo a la nube
                    rut_final = formatear_rut(rut_c)
                    
                    nuevo_cliente = pd.DataFrame([{
                        "Nombre": nombre_c,
                        "RUT": rut_final,
                        "WhatsApp": whatsapp_c,
                        "Correo": correo_c,
                        "Cumpleaños": str(fecha_cumple),
                        "Dirección": dirección_c
                    }])
                    
                    df_c_final = pd.concat([df_clientes, nuevo_cliente], ignore_index=True)
                    conn.update(spreadsheet=url_planilla, worksheet="Clientes", data=df_c_final)
                    st.success(f"✅ Cliente {nombre_c} registrado con RUT {rut_final}")
                    # Al terminar, el formulario se limpia solo por el clear_on_submit
                else:
                    st.error("⚠️ Nombre y RUT son obligatorios para la base de datos.")

    with tab_historial:
        st.subheader("Buscador de Compras")
        if not df_clientes.empty:
            # Buscador inteligente por nombre o RUT
            opciones_clientes = df_clientes['RUT'] + " | " + df_clientes['Nombre']
            seleccion = st.selectbox("Buscar Cliente para ver historial:", opciones_clientes)
            rut_buscado = seleccion.split(" | ")[0]
            
            # Aquí filtraremos la hoja de "Ventas" por este RUT
            st.info(f"Mostrando historial para el RUT: {rut_buscado}")
            
            # (Este espacio mostrará las compras cuando conectemos el módulo de Ventas con el RUT)
            ventas_cliente = df_ventas[df_ventas['Cliente_RUT'] == rut_buscado] if 'Cliente_RUT' in df_ventas.columns else pd.DataFrame()
            
            if not ventas_cliente.empty:
                st.dataframe(ventas_cliente)
            else:
                st.write("Aún no hay compras registradas para este cliente.")
        else:
            st.warning("No hay clientes en la base de datos.")

    st.subheader("Base de Datos General")
    st.dataframe(df_clientes, use_container_width=True)
