import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

st.set_page_config(page_title="Gestor de Trámites - Melisa", layout="wide")
st.title("📋 Gestor de Trámites - Melisa")

DATA_FILE = "tramites.csv"
PASOS_FILE = "pasos.json"

# ================= CARGAR / GUARDAR PASOS =================
if os.path.exists(PASOS_FILE):
    with open(PASOS_FILE, "r", encoding="utf-8") as f:
        PASOS = json.load(f)
else:
    PASOS = [
        "Análisis", "Oficio Secretaría de Hacienda", "Acuerdo c/ Jefe",
        "Of. CGJ → SG", "Of. SG → DG", "Acuerdo SG", "En espera de causas",
        "Sanción", "Rúbrica DGEL", "Rúbrica CGJ", "Ingreso a 4to piso", 
        "Remitir a POEH"
    ]
    with open(PASOS_FILE, "w", encoding="utf-8") as f:
        json.dump(PASOS, f, ensure_ascii=False, indent=4)

# ================= CARGAR TRÁMITES =================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    for col in ['Fecha_Ingreso', 'Fecha_Limite']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
else:
    df = pd.DataFrame(columns=['ID', 'Nombre_Tramite', 'Fecha_Ingreso', 'Fecha_Limite'] + PASOS)

# ================= SIDEBAR - GESTIÓN DE PASOS =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    nuevo_paso = st.text_input("Agregar nuevo paso:")
    if st.button("➕ Agregar"):
        if nuevo_paso.strip() and nuevo_paso.strip() not in PASOS:
            PASOS.append(nuevo_paso.strip())
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            st.success(f"✅ '{nuevo_paso}' agregado")
            st.rerun()
    
    st.subheader("Pasos actuales:")
    for i, paso in enumerate(PASOS):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {paso}")
        with col2:
            if st.button("🗑️", key=f"delpaso_{i}"):
                PASOS.pop(i)
                with open(PASOS_FILE, "w", encoding="utf-8") as f:
                    json.dump(PASOS, f, ensure_ascii=False, indent=4)
                st.rerun()

# ================= AGREGAR TRÁMITE =================
with st.expander("➕ Agregar Nuevo Trámite", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre o Número del Trámite *")
    with col2:
        fecha_ingreso = st.date_input("Fecha de Ingreso", value=date.today())
    
    fecha_limite = st.date_input("Fecha Límite", value=date.today())

    if st.button("Guardar Trámite"):
        if nombre.strip():
            nuevo = {
                'ID': len(df) + 1,
                'Nombre_Tramite': nombre.strip(),
                'Fecha_Ingreso': fecha_ingreso,
                'Fecha_Limite': fecha_limite
            }
            for paso in PASOS:
                nuevo[paso] = False
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success("✅ Trámite guardado correctamente")
            st.rerun()
        else:
            st.error("El nombre del trámite es obligatorio")

# ================= LISTA DE TRÁMITES =================
st.subheader("📋 Mis Trámites")

busqueda = st.text_input("🔍 Buscar trámite", "")

df_mostrar = df.copy()
if busqueda:
    df_mostrar = df_mostrar[df_mostrar['Nombre_Tramite'].str.contains(busqueda, case=False)]

if len(df_mostrar) > 0:
    for idx, row in df_mostrar.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"**{row['Nombre_Tramite']}**")
                st.caption(f"📅 Ingreso: {row['Fecha_Ingreso']} | ⏰ Límite: {row['Fecha_Limite']}")
            
            with col2:
                if st.button("🖨️ Imprimir", key=f"print_{idx}"):
                    st.session_state.tramite_a_imprimir = row.to_dict()
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Eliminar", key=f"del_{idx}"):
                    df = df[df['ID'] != row['ID']]
                    df.to_csv(DATA_FILE, index=False)
                    st.success("Trámite eliminado")
                    st.rerun()

            # Checkboxes dinámicos
            cols = st.columns(3)
            for i, paso in enumerate(PASOS):
                with cols[i % 3]:
                    valor = st.checkbox(paso, value=bool(row.get(paso, False)), key=f"check_{idx}_{paso}")
                    if valor != row.get(paso, False):
                        real_idx = df.index[df['ID'] == row['ID']].tolist()[0]
                        df.at[real_idx, paso] = valor
                        df.to_csv(DATA_FILE, index=False)
                        st.rerun()
            
            # Estado de fecha
            hoy = date.today()
            if row['Fecha_Limite'] < hoy:
                st.error("⛔ ATRASADO")
            elif row['Fecha_Limite'] == hoy:
                st.warning("⚠️ Vence hoy")
            else:
                st.success("✅ A tiempo")
else:
    st.info("No hay trámites aún.")

# ================= IMPRESIÓN =================
if 'tramite_a_imprimir' in st.session_state:
    tramite = st.session_state.tramite_a_imprimir
    st.markdown("---")
    st.subheader(f"🖨️ Vista de Impresión: {tramite['Nombre_Tramite']}")

    html = f"""
    <style>
        @media print {{ body {{ font-family: Arial; }} }}
        h1, h2 {{ text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid black; padding: 10px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
    </style>
    <h1>CHECKLIST DE TRÁMITE</h1>
    <h2>{tramite['Nombre_Tramite']}</h2>
    <p><strong>Fecha de Ingreso:</strong> {tramite['Fecha_Ingreso']} &nbsp;&nbsp;&nbsp;
       <strong>Fecha Límite:</strong> {tramite['Fecha_Limite']}</p>
    <table>
        <tr><th>Paso</th><th>Estado</th></tr>
    """
    
    for paso in PASOS:
        completado = "✅ SÍ" if tramite.get(paso, False) else "☐ COMPLETADO"
        html += f"<tr><td>{paso}</td><td>{completado}</td></tr>"
    
    html += f"</table><br><p>Impreso el: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>"

    st.components.v1.html(html, height=700)
    
    st.download_button("📥 Descargar HTML para imprimir", 
                      data=html, 
                      file_name=f"tramite_{tramite['Nombre_Tramite']}.html",
                      mime="text/html")
    
    if st.button("Cerrar vista de impresión"):
        del st.session_state.tramite_a_imprimir
        st.rerun()