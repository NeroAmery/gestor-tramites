import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

st.set_page_config(page_title="Gestor de Trámites - Melisa", layout="wide")
st.title("📋 Gestor de Trámites - Melisa")

DATA_FILE = "tramites.json"
PASOS_FILE = "pasos.json"

# ================= CARGAR PASOS =================
if os.path.exists(PASOS_FILE):
    with open(PASOS_FILE, "r", encoding="utf-8") as f:
        PASOS = json.load(f)
else:
    PASOS = ["Análisis", "Oficio Secretaría de Hacienda", "Acuerdo c/ Jefe", "Of. CGJ → SG", "Of. SG → DG", "Acuerdo SG", "En espera de causas", "Sanción", "Rúbrica DGEL", "Rúbrica CGJ", "Ingreso a 4to piso", "Remitir a POEH"]

# ================= CARGAR TRÁMITES =================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
else:
    df = pd.DataFrame(columns=['ID', 'Nombre_Tramite', 'Fecha_Ingreso', 'Fecha_Limite'])

for paso in PASOS:
    if paso not in df.columns:
        df[paso] = False
        df[paso + "_nota"] = ""

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    
    st.subheader("Reordenar / Editar Pasos")
    for i, paso in enumerate(PASOS):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"• {paso}")
        with col2:
            if st.button("✏️", key=f"editp_{i}"):
                st.session_state.edit_paso_index = i
                st.rerun()
        with col3:
            if i > 0 and st.button("↑", key=f"up_{i}"):
                PASOS[i], PASOS[i-1] = PASOS[i-1], PASOS[i]
                with open(PASOS_FILE, "w", encoding="utf-8") as f:
                    json.dump(PASOS, f, ensure_ascii=False, indent=4)
                st.rerun()
        with col4:
            if i < len(PASOS)-1 and st.button("↓", key=f"down_{i}"):
                PASOS[i], PASOS[i+1] = PASOS[i+1], PASOS[i]
                with open(PASOS_FILE, "w", encoding="utf-8") as f:
                    json.dump(PASOS, f, ensure_ascii=False, indent=4)
                st.rerun()

    if st.session_state.get('edit_paso_index') is not None:
        i = st.session_state.edit_paso_index
        nuevo = st.text_input("Nuevo nombre:", PASOS[i])
        if st.button("Guardar"):
            PASOS[i] = nuevo.strip()
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            del st.session_state.edit_paso_index
            st.rerun()

# ================= BÚSQUEDA AVANZADA =================
st.subheader("📋 Mis Trámites")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    busqueda = st.text_input("🔍 Buscar por nombre o nota", "").strip()
with col2:
    fecha_filtro = st.date_input("Filtrar por fecha límite desde", value=None, label_visibility="collapsed")
with col3:
    if st.button("Limpiar filtros"):
        busqueda = ""
        fecha_filtro = None
        st.rerun()

# Aplicar filtros
df_mostrar = df.copy()
if busqueda:
    mask = (
        df_mostrar['Nombre_Tramite'].str.contains(busqueda, case=False, na=False) |
        df_mostrar[[col for col in df_mostrar.columns if col.endswith("_nota")]].apply(
            lambda x: x.astype(str).str.contains(busqueda, case=False, na=False)
        ).any(axis=1)
    )
    df_mostrar = df_mostrar[mask]

if fecha_filtro:
    df_mostrar = df_mostrar[pd.to_datetime(df_mostrar['Fecha_Limite']) >= pd.to_datetime(fecha_filtro)]

# ================= MOSTRAR TRÁMITES =================
for idx, row in df_mostrar.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{row['Nombre_Tramite']}**")
            st.caption(f"📅 Ingreso: {row['Fecha_Ingreso']} | ⏰ Límite: {row['Fecha_Limite']}")
        
        with col2:
            if st.button("✏️ Editar Nombre", key=f"editname_{idx}"):
                st.session_state.edit_id = row['ID']
                st.rerun()
        with col3:
            if st.button("🖨️ Imprimir", key=f"print_{idx}"):
                st.session_state.tramite_a_imprimir = row.to_dict()
                st.rerun()

        # Checkboxes y Notas
        for paso in PASOS:
            c1, c2 = st.columns([1, 4])
            with c1:
                valor = st.checkbox(paso, value=bool(row.get(paso, False)), key=f"ch_{idx}_{paso}")
                if valor != row.get(paso, False):
                    real_idx = df.index[df['ID'] == row['ID']].tolist()[0]
                    df.at[real_idx, paso] = valor
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()
            with c2:
                nota = st.text_input("Nota:", value=row.get(paso + "_nota", ""), key=f"nota_{idx}_{paso}")
                if nota != row.get(paso + "_nota", ""):
                    real_idx = df.index[df['ID'] == row['ID']].tolist()[0]
                    df.at[real_idx, paso + "_nota"] = nota
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()

# ================= EDICIÓN NOMBRE TRÁMITE =================
if st.session_state.get('edit_id'):
    tramite = df[df['ID'] == st.session_state.edit_id].iloc[0]
    nuevo_nombre = st.text_input("Nuevo nombre del trámite:", tramite['Nombre_Tramite'])
    if st.button("Guardar Nombre"):
        real_idx = df.index[df['ID'] == st.session_state.edit_id].tolist()[0]
        df.at[real_idx, 'Nombre_Tramite'] = nuevo_nombre
        df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
        del st.session_state.edit_id
        st.success("✅ Nombre actualizado")
        st.rerun()

# ================= IMPRESIÓN MEJORADA =================
if 'tramite_a_imprimir' in st.session_state:
    tramite = st.session_state.tramite_a_imprimir
    st.markdown("---")
    st.subheader(f"🖨️ Imprimir: {tramite['Nombre_Tramite']}")

    html = f"""
    <style>
        @media print {{ body {{ font-family: Arial, sans-serif; margin: 20px; }} }}
        h1, h2 {{ text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #333; padding: 10px; }}
        th {{ background-color: #f0f0f0; }}
        .nota {{ font-style: italic; color: #555; }}
    </style>
    <h1>CHECKLIST DE TRÁMITE</h1>
    <h2>{tramite['Nombre_Tramite']}</h2>
    <p><strong>Fecha Ingreso:</strong> {tramite['Fecha_Ingreso']} &nbsp;&nbsp;&nbsp; 
       <strong>Fecha Límite:</strong> {tramite['Fecha_Limite']}</p>
    <table>
        <tr><th>Paso</th><th>Estado</th><th>Nota</th></tr>
    """
    for paso in PASOS:
        estado = "✅ COMPLETADO" if tramite.get(paso, False) else "☐ PENDIENTE"
        nota = tramite.get(paso + "_nota", "")
        html += f"<tr><td>{paso}</td><td>{estado}</td><td class='nota'>{nota}</td></tr>"

    html += f"</table><br><p>Impreso el: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>"

    st.components.v1.html(html, height=800)

    st.download_button("📥 Descargar como HTML", data=html, file_name=f"tramite_{tramite['Nombre_Tramite']}.html", mime="text/html")

    st.info("💡 Para guardar como **PDF**: Usa Ctrl + P (o Cmd + P) → Guardar como PDF")

    if st.button("Cerrar impresión"):
        del st.session_state.tramite_a_imprimir
        st.rerun()