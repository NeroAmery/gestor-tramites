import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

st.set_page_config(page_title="Gestor de Trámites - G", layout="wide")
st.title("📋 Gestor de Trámites - Agente G")

DATA_FILE = "tramites.json"
PASOS_FILE = "pasos.json"

# ================= CARGAR DATOS =================
if os.path.exists(PASOS_FILE):
    with open(PASOS_FILE, "r", encoding="utf-8") as f:
        PASOS = json.load(f)
else:
    PASOS = ["Análisis", "Oficio Secretaría de Hacienda", "Acuerdo c/ Jefe", "Of. CGJ → SG", "Of. SG → DG", "Acuerdo SG", "En espera de causas", "Sanción", "Rúbrica DGEL", "Rúbrica CGJ", "Ingreso a 4to piso", "Remitir a POEH"]

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
else:
    df = pd.DataFrame(columns=['ID', 'Nombre_Tramite', 'Fecha_Ingreso', 'Fecha_Limite'])

for paso in PASOS:
    if paso not in df.columns:
        df[paso] = False
        df[paso + "_nota"] = ""

# ================= SIDEBAR - GESTIÓN DE PASOS =================
with st.sidebar:
    st.header("⚙️ Gestionar Pasos")
    
    nuevo_paso = st.text_input("Nuevo paso:")
    if st.button("➕ Agregar Paso"):
        if nuevo_paso.strip() and nuevo_paso.strip() not in PASOS:
            PASOS.append(nuevo_paso.strip())
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            st.rerun()

    st.subheader("Pasos Actuales")
    for i, paso in enumerate(PASOS):
        col1, col2, col3, col4, col5 = st.columns([3.5, 1, 1, 1, 1])
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
        with col5:
            if st.button("🗑️", key=f"dp_{i}"):
                st.session_state.del_paso = i
                st.rerun()

    # Confirmar eliminación de paso
    if st.session_state.get("del_paso") is not None:
        i = st.session_state.del_paso
        st.warning(f"¿Eliminar '{PASOS[i]}'?")
        if st.button("Sí, eliminar"):
            PASOS.pop(i)
            with open(PASOS_FILE, "w", encoding="utf-8") as f:
                json.dump(PASOS, f, ensure_ascii=False, indent=4)
            del st.session_state.del_paso
            st.rerun()
        if st.button("Cancelar"):
            del st.session_state.del_paso
            st.rerun()

    # Editar paso
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
with st.expander("➕ Agregar Nuevo Trámite", expanded=False):
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

# ================= LISTA DE TRÁMITES =================
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
            hoy = date.today()
            fl = pd.to_datetime(row['Fecha_Limite']).date()
            if fl < hoy:
                st.error("⛔ VENCIDO")
            elif fl == hoy:
                st.warning("⚠️ Hoy vence")
            else:
                st.success("✅ A tiempo")
            st.caption(f"Ingreso: {row['Fecha_Ingreso']} | Límite: {row['Fecha_Limite']}")

        with col2:
            if st.button("✏️ Editar", key=f"edit_{idx}"):
                st.session_state.edit_id = row['ID']
                st.rerun()
        with col3:
            if st.button("🖨️ Imprimir", key=f"print_{idx}"):
                st.session_state.tramite_a_imprimir = row.to_dict()
                st.rerun()

        with st.expander("Ver pasos y notas", expanded=False):
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
                    nota = st.text_input("Nota:", row.get(paso+"_nota",""), key=f"nt_{idx}_{paso}")
                    if nota != row.get(paso+"_nota",""):
                        real_idx = df.index[df['ID'] == row['ID']][0]
                        df.at[real_idx, paso+"_nota"] = nota
                        df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
                        st.rerun()

        # Eliminar trámite
        if st.button("🗑️ Eliminar Trámite", key=f"deltram_{idx}"):
            st.session_state.del_tramite = row['ID']
            st.rerun()

# ================= IMPRESIÓN =================
if 'tramite_a_imprimir' in st.session_state:
    t = st.session_state.tramite_a_imprimir
    st.markdown("---")
    st.subheader(f"🖨️ Imprimiendo: {t['Nombre_Tramite']}")
    
    html = f"""
    <style>@media print {{body {{margin: 20px; font-family: Arial;}}}} h1,h2{{text-align:center;}} table{{width:100%; border-collapse:collapse;}} th,td{{border:1px solid black; padding:10px;}}</style>
    <h1>CHECKLIST DE TRÁMITE</h1>
    <h2>{t['Nombre_Tramite']}</h2>
    <p><strong>Ingreso:</strong> {t['Fecha_Ingreso']} &nbsp;&nbsp; <strong>Límite:</strong> {t['Fecha_Limite']}</p>
    <table><tr><th>Paso</th><th>Estado</th><th>Nota</th></tr>
    """
    for paso in PASOS:
        estado = "✅" if t.get(paso, False) else "☐"
        nota = t.get(paso+"_nota", "")
        html += f"<tr><td>{paso}</td><td>{estado}</td><td>{nota}</td></tr>"
    html += "</table><br><p>Impreso el: " + datetime.now().strftime("%d/%m/%Y %H:%M") + "</p>"

    st.components.v1.html(html, height=700)
    st.download_button("📥 Descargar HTML", html, f"{t['Nombre_Tramite']}.html", "text/html")
    st.info("💡 Para guardar como PDF: Presiona Ctrl + P → 'Guardar como PDF'")

    if st.button("Cerrar"):
        del st.session_state.tramite_a_imprimir
        st.rerun()

# ================= ELIMINAR TRÁMITE =================
if st.session_state.get("del_tramite"):
    if st.button("¿Seguro que quieres eliminar este trámite?"):
        df = df[df['ID'] != st.session_state.del_tramite]
        df.to_json(DATA_FILE, orient="records", force_ascii=False, indent=4)
        del st.session_state.del_tramite
        st.success("Trámite eliminado")
        st.rerun()
    if st.button("Cancelar"):
        del st.session_state.del_tramite
        st.rerun()