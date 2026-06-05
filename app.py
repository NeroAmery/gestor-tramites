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

for paso in PASOS:
    if paso not in df.columns:
        df[paso] = False
        df[paso + "_nota"] = ""

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    
    # Agregar paso
    nuevo_paso = st.text_input("Nuevo paso:")
    if st.button("➕ Agregar Paso"):
        if nuevo_paso.strip() and nuevo_paso.strip() not in PASOS:
            PASOS.append(nuevo_paso.strip())
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            st.success("Paso agregado")
            st.rerun()

    # Reordenar y editar
    st.subheader("Reordenar / Editar")
    for i, paso in enumerate(PASOS):
        col1, col2, col3, col4 = st.columns([3,1,1,1])
        with col1:
            st.write(f"• {paso}")
        with col2:
            if st.button("✏️", key=f"ep_{i}"):
                st.session_state.edit_paso = i
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

    if st.session_state.get("edit_paso") is not None:
        i = st.session_state.edit_paso
        nuevo = st.text_input("Nuevo nombre del paso:", PASOS[i])
        if st.button("Guardar"):
            PASOS[i] = nuevo.strip()
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            del st.session_state.edit_paso
            st.rerun()

# ================= AGREGAR TRÁMITE =================
with st.expander("➕ Agregar Nuevo Trámite", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre o Número del Trámite *")
    with col2:
        fecha_ingreso = st.date_input("Fecha de Ingreso", value=date.today())
    fecha_limite = st.date_input("Fecha Límite", value=date.today())

    if st.button("Guardar Trámite", type="primary"):
        if nombre.strip():
            nuevo = {'ID': len(df) + 1, 'Nombre_Tramite': nombre.strip(),
                     'Fecha_Ingreso': str(fecha_ingreso), 'Fecha_Limite': str(fecha_limite)}
            for paso in PASOS:
                nuevo[paso] = False
                nuevo[paso + "_nota"] = ""
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
            st.success("✅ Trámite guardado")
            st.rerun()

# ================= LISTA Y EDICIÓN =================
st.subheader("📋 Mis Trámites")

busqueda = st.text_input("🔍 Buscar", "")

df_mostrar = df.copy()
if busqueda:
    df_mostrar = df_mostrar[df_mostrar['Nombre_Tramite'].str.contains(busqueda, case=False, na=False)]

for idx, row in df_mostrar.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.write(f"**{row['Nombre_Tramite']}**")
            st.caption(f"Ingreso: {row['Fecha_Ingreso']} | Límite: {row['Fecha_Limite']}")
        with col2:
            if st.button("✏️ Editar", key=f"edit_{idx}"):
                st.session_state.edit_id = row['ID']
                st.rerun()
        with col3:
            if st.button("🖨️ Imprimir", key=f"print_{idx}"):
                st.session_state.tramite_a_imprimir = row.to_dict()
                st.rerun()

        for paso in PASOS:
            c1, c2 = st.columns([1,4])
            with c1:
                valor = st.checkbox(paso, bool(row.get(paso, False)), key=f"ch_{idx}_{paso}")
                if valor != row.get(paso, False):
                    real_idx = df.index[df['ID'] == row['ID']][0]
                    df.at[real_idx, paso] = valor
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()
            with c2:
                nota = st.text_input("Nota:", row.get(paso+"_nota", ""), key=f"nt_{idx}_{paso}")
                if nota != row.get(paso+"_nota", ""):
                    real_idx = df.index[df['ID'] == row['ID']][0]
                    df.at[real_idx, paso+"_nota"] = nota
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()

# Editar trámite completo
if st.session_state.get("edit_id"):
    row = df[df['ID'] == st.session_state.edit_id].iloc[0]
    st.subheader("Editar Trámite")
    nuevo_nombre = st.text_input("Nombre", row['Nombre_Tramite'])
    col1, col2 = st.columns(2)
    with col1:
        nueva_ing = st.date_input("Ingreso", pd.to_datetime(row['Fecha_Ingreso']).date())
    with col2:
        nueva_lim = st.date_input("Límite", pd.to_datetime(row['Fecha_Limite']).date())
    if st.button("Guardar Cambios"):
        idx = df.index[df['ID'] == st.session_state.edit_id][0]
        df.at[idx, 'Nombre_Tramite'] = nuevo_nombre
        df.at[idx, 'Fecha_Ingreso'] = str(nueva_ing)
        df.at[idx, 'Fecha_Limite'] = str(nueva_lim)
        df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
        del st.session_state.edit_id
        st.success("Actualizado")
        st.rerun()

st.info("Prueba reordenar pasos y editar trámites")
