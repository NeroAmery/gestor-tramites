import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

st.set_page_config(page_title="Gestor de Trámites - G", layout="wide")
st.title("📋 Gestor de Trámites - Agente G")

DATA_FILE = "tramites.json"
PASOS_FILE = "pasos.json"

# Cargar Pasos
if os.path.exists(PASOS_FILE):
    with open(PASOS_FILE, "r", encoding="utf-8") as f:
        PASOS = json.load(f)
else:
    PASOS = ["Análisis", "Oficio Secretaría de Hacienda", "Acuerdo c/ Jefe", "Of. CGJ → SG", "Of. SG → DG", "Acuerdo SG", "En espera de causas", "Sanción", "Rúbrica DGEL", "Rúbrica CGJ", "Ingreso a 4to piso", "Remitir a POEH"]

# Cargar Trámites
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
else:
    df = pd.DataFrame(columns=['ID', 'Nombre_Tramite', 'Fecha_Ingreso', 'Fecha_Limite'])

# Crear columnas faltantes
for paso in PASOS:
    if paso not in df.columns:
        df[paso] = False
        df[paso + "_nota"] = ""

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    st.subheader("Reordenar / Editar")

    for i, paso in enumerate(PASOS):
        col1, col2, col3, col4 = st.columns([3,1,1,1])
        with col1:
            st.write(f"• {paso}")
        with col2:
            if st.button("✏️", key=f"ep_{i}"):
                st.session_state.edit_paso_i = i
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

    # Editar paso
    if st.session_state.get("edit_paso_i") is not None:
        i = st.session_state.edit_paso_i
        nuevo = st.text_input("Nuevo nombre:", PASOS[i], key="edit_paso")
        if st.button("Guardar"):
            PASOS[i] = nuevo.strip()
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            del st.session_state.edit_paso_i
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
                'Fecha_Ingreso': str(fecha_ingreso),
                'Fecha_Limite': str(fecha_limite)
            }
            for paso in PASOS:
                nuevo[paso] = False
                nuevo[paso + "_nota"] = ""
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
            st.success("✅ Trámite guardado")
            st.rerun()

# ================= BÚSQUEDA Y LISTA =================
st.subheader("📋 Mis Trámites")

colb1, colb2 = st.columns([3, 2])
with colb1:
    busqueda = st.text_input("🔍 Buscar por nombre o nota", "")
with colb2:
    if st.button("Limpiar"):
        busqueda = ""
        st.rerun()

# Filtrar
df_mostrar = df.copy()
if busqueda:
    mask = df_mostrar['Nombre_Tramite'].str.contains(busqueda, case=False, na=False)
    for col in [c for c in df.columns if c.endswith("_nota")]:
        mask |= df_mostrar[col].astype(str).str.contains(busqueda, case=False, na=False)
    df_mostrar = df_mostrar[mask]

for idx, row in df_mostrar.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.write(f"**{row['Nombre_Tramite']}**")
            st.caption(f"Ingreso: {row['Fecha_Ingreso']} | Límite: {row['Fecha_Limite']}")
        with col2:
            if st.button("✏️ Editar", key=f"en_{idx}"):
                st.session_state.edit_tramite = row['ID']
                st.rerun()
        with col3:
            if st.button("🖨️ Imprimir", key=f"pr_{idx}"):
                st.session_state.tramite_a_imprimir = row.to_dict()
                st.rerun()

        for paso in PASOS:
            c1, c2 = st.columns([1,4])
            with c1:
                valor = st.checkbox(paso, bool(row.get(paso, False)), key=f"ch_{idx}_{paso}")
                if valor != row.get(paso, False):
                    real = df.index[df['ID'] == row['ID']][0]
                    df.at[real, paso] = valor
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()
            with c2:
                nota = st.text_input("Nota:", row.get(paso+"_nota", ""), key=f"nt_{idx}_{paso}")
                if nota != row.get(paso+"_nota", ""):
                    real = df.index[df['ID'] == row['ID']][0]
                    df.at[real, paso+"_nota"] = nota
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()

# ================= IMPRESIÓN =================
if 'tramite_a_imprimir' in st.session_state:
    t = st.session_state.tramite_a_imprimir
    st.markdown("---")
    st.subheader(f"Imprimiendo: {t['Nombre_Tramite']}")
    
    html = f"""<style>@media print {{body {{margin:30px;}}}} h1,h2{{text-align:center;}} table{{width:100%; border-collapse:collapse;}} th,td{{border:1px solid black; padding:8px;}}</style>
    <h1>CHECKLIST DE TRÁMITE</h1>
    <h2>{t['Nombre_Tramite']}</h2>
    <p><b>Ingreso:</b> {t['Fecha_Ingreso']} &nbsp; <b>Límite:</b> {t['Fecha_Limite']}</p><table><tr><th>Paso</th><th>Estado</th><th>Nota</th></tr>"""
    
    for paso in PASOS:
        estado = "✅" if t.get(paso, False) else "☐"
        nota = t.get(paso+"_nota", "")
        html += f"<tr><td>{paso}</td><td>{estado}</td><td>{nota}</td></tr>"
    html += "</table>"

    st.components.v1.html(html, height=700)
    st.download_button("Descargar HTML", html, f"{t['Nombre_Tramite']}.html", "text/html")
    st.info("Para guardar como PDF: Ctrl + P → Guardar como PDF")

    if st.button("Cerrar"):
        del st.session_state.tramite_a_imprimir
        st.rerun()