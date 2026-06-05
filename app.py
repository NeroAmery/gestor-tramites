import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

st.set_page_config(page_title="Gestor de Trámites - Melisa", layout="wide")
st.title("📋 Gestor de Trámites - Melisa")

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

# Crear columnas de pasos y notas
for paso in PASOS:
    if paso not in df.columns:
        df[paso] = False
        df[paso + "_nota"] = ""

# ================= SIDEBAR - Gestionar Pasos =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    
    st.subheader("Agregar Nuevo Paso")
    nuevo_paso = st.text_input("Nombre del nuevo paso:")
    if st.button("➕ Agregar Paso"):
        if nuevo_paso.strip() and nuevo_paso.strip() not in PASOS:
            PASOS.append(nuevo_paso.strip())
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            st.success("Paso agregado")
            st.rerun()

    st.subheader("Reordenar / Editar Pasos")
    for i, paso in enumerate(PASOS):
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.write(f"• {paso}")
        with col2:
            if st.button("✏️", key=f"edit_{i}"):
                st.session_state.edit_paso = i
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                PASOS.pop(i)
                with open(PASOS_FILE, "w", encoding="utf-8") as f:
                    json.dump(PASOS, f, ensure_ascii=False, indent=4)
                st.rerun()

    # Editar nombre de paso
    if st.session_state.get("edit_paso") is not None:
        i = st.session_state.edit_paso
        nuevo = st.text_input("Nuevo nombre:", PASOS[i])
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
        nombre = st.text_input("Nombre o Número del Trámite *", key="nombre_tramite")
    with col2:
        fecha_ingreso = st.date_input("Fecha de Ingreso", value=date.today())
    fecha_limite = st.date_input("Fecha Límite", value=date.today())

    if st.button("Guardar Trámite", type="primary"):
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
            st.success("✅ Trámite guardado correctamente")
            st.rerun()
        else:
            st.error("El nombre del trámite es obligatorio")

# ================= LISTA COMPLETA DE TRÁMITES =================
st.subheader("📋 Mis Trámites")

# Búsqueda
busqueda = st.text_input("🔍 Buscar por nombre o nota", "")

df_mostrar = df.copy()
if busqueda:
    mask = df_mostrar['Nombre_Tramite'].str.contains(busqueda, case=False, na=False)
    for col in df.columns:
        if col.endswith("_nota"):
            mask |= df_mostrar[col].astype(str).str.contains(busqueda, case=False, na=False)
    df_mostrar = df_mostrar[mask]

if len(df_mostrar) == 0 and len(df) > 0:
    st.info("No se encontraron trámites con ese criterio.")
elif len(df) == 0:
    st.info("Aún no tienes trámites. Agrega uno arriba.")

# Mostrar todos los trámites (filtrados)
for idx, row in df_mostrar.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            st.write(f"**{row['Nombre_Tramite']}**")
            st.caption(f"📅 Ingreso: {row['Fecha_Ingreso']} | ⏰ Límite: {row['Fecha_Limite']}")
        with col2:
            if st.button("✏️ Editar", key=f"editname_{idx}"):
                st.session_state.edit_tramite_id = row['ID']
                st.rerun()
        with col3:
            if st.button("🖨️ Imprimir", key=f"print_{idx}"):
                st.session_state.tramite_a_imprimir = row.to_dict()
                st.rerun()

        # Pasos y notas
        for paso in PASOS:
            c1, c2 = st.columns([1, 4])
            with c1:
                checked = st.checkbox(paso, value=bool(row.get(paso, False)), key=f"check_{idx}_{paso}")
                if checked != row.get(paso, False):
                    real_idx = df.index[df['ID'] == row['ID']][0]
                    df.at[real_idx, paso] = checked
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()
            with c2:
                nota = st.text_input("Nota:", value=row.get(paso + "_nota", ""), key=f"nota_{idx}_{paso}")
                if nota != row.get(paso + "_nota", ""):
                    real_idx = df.index[df['ID'] == row['ID']][0]
                    df.at[real_idx, paso + "_nota"] = nota
                    df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                    st.rerun()

# ================= EDICIÓN DE NOMBRE =================
if st.session_state.get("edit_tramite_id"):
    # (código de edición de nombre)
    pass  # Podemos agregarlo después si hace falta

st.info("✅ Usa el sidebar para agregar y editar pasos. La lista completa se muestra abajo.")