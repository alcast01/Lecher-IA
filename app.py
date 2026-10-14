import streamlit as st
import pandas as pd
import numpy as np
import pulp
import io
import json
import cv2
from PIL import Image
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Lecher-IA Pro | Plataforma IoT, Visión AI & Hato Inteligente",
    page_icon="🥛",
    layout="wide"
)

# Inicializar estados de sesión para inventario, citas y notificaciones
if "cita_pagada" not in st.session_state:
    st.session_state.cita_pagada = False
if "detalles_cita" not in st.session_state:
    st.session_state.detalles_cita = {}
if "ver_videollamada" not in st.session_state:
    st.session_state.ver_videollamada = False

# Inicializar base de datos de inventario del hato si no existe
if "df_hato" not in st.session_state:
    st.session_state.df_hato = pd.DataFrame([
        {
            "SINIGA": "MX-14-032-8811",
            "Arete Interno": "101",
            "Etapa Productiva": "En producción",
            "DIM / Edad (días)": 240,
            "Días Gestación": 150,
            "Prod. Leche (L)": 32.5,
            "Estado Salud": "Óptimo"
        },
        {
            "SINIGA": "MX-14-032-9012",
            "Arete Interno": "102",
            "Etapa Productiva": "En transición",
            "DIM / Edad (días)": 12,
            "Días Gestación": 0,
            "Prod. Leche (L)": 38.0,
            "Estado Salud": "Monitoreo CETOSIS"
        },
        {
            "SINIGA": "MX-14-033-1045",
            "Arete Interno": "103",
            "Etapa Productiva": "Vaca seca",
            "DIM / Edad (días)": 285,
            "Días Gestación": 230,
            "Prod. Leche (L)": 0.0,
            "Estado Salud": "Preparación Parto"
        },
        {
            "SINIGA": "MX-14-034-5521",
            "Arete Interno": "201",
            "Etapa Productiva": "Para inseminar",
            "DIM / Edad (días)": 75,
            "Días Gestación": 0,
            "Prod. Leche (L)": 42.0,
            "Estado Salud": "Espera Voluntaria OK"
        },
        {
            "SINIGA": "MX-14-035-7788",
            "Arete Interno": "301",
            "Etapa Productiva": "Becerra de reemplazo gestante",
            "DIM / Edad (días)": 450,
            "Días Gestación": 110,
            "Prod. Leche (L)": 0.0,
            "Estado Salud": "Crecimiento Normal"
        },
        {
            "SINIGA": "MX-14-035-8899",
            "Arete Interno": "302",
            "Etapa Productiva": "Becerra de reemplazo no gestante",
            "DIM / Edad (días)": 380,
            "Días Gestación": 0,
            "Prod. Leche (L)": 0.0,
            "Estado Salud": "Desarrollo"
        },
        {
            "SINIGA": "MX-14-036-1234",
            "Arete Interno": "401",
            "Etapa Productiva": "Becerra recién nacida",
            "DIM / Edad (días)": 5,
            "Días Gestación": 0,
            "Prod. Leche (L)": 0.0,
            "Estado Salud": "Calostro OK"
        }
    ])

# --- MÓDULO 5: REPORTE OPERATIVO, FINANCIERO E IOT EN PDF ---
def generar_pdf_tmr_financiero(df_resultados, costo_alimento, cms_req, ecm, raza, estado_prod, tam_corral, precio_leche, iofc, ebitda_diario, costo_total_litro, break_even_leche, ch4_vaca, n_exc_vaca, iot_status):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#054A29'), spaceAfter=4)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=10)
    
    story.append(Paragraph("<b>LECHER-IA Pro — REPORTE FINANCIERO, TMR & VISIÓN AI</b>", title_style))
    story.append(Paragraph(f"<b>Formulador:</b> Dr. Alejandro Castañeda Correa &bull; <b>Perfil:</b> {raza} ({estado_prod}) &bull; <b>Corral:</b> {tam_corral} vacas &bull; <b>IoT/AI Link:</b> {iot_status}", subtitle_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph(f"<b>Costo Alimento/Vaca:</b> ${costo_alimento:.2f} MXN &bull; <b>Costo Total/L:</b>${costo_total_litro:.2f} MXN &bull; <b>Punto Equilibrio:</b> {break_even_leche:.1f} L/vaca", styles['Normal']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>IOFC/Vaca:</b> ${iofc:.2f} MXN/día &bull; <b>EBITDA Corral/Mes:</b> ${ebitda_diario * tam_corral * 30.5:,.2f} MXN &bull; <b>Huella CH₄:</b> {ch4_vaca:.1f} g/día", styles['Normal']))
    story.append(Spacer(1, 10))
    
    table_data = [["Ingrediente", "MS %", "Base Seca (kg/vaca)", "Base Fresca (kg/vaca)", f"Carga Corral ({tam_corral} vacas)"]]
    for _, row in df_resultados.iterrows():
        table_data.append([
            str(row["Ingrediente"]),
            f"{row['MS %']:.1f}%",
            f"{row['Inclusión (kg MS)']:.2f}",
            f"{row['Base Fresca (kg/vaca)']:.2f}",
            f"{row['Total Corral (kg)']:.1f} kg"
        ])
        
    t = Table(table_data, colWidths=[150, 50, 100, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#137547')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<i>Optimización bio-económica integrada con estimación de peso por visión artificial y telemetría PLF.</i>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 2. ENCABEZADO Y BRANDING ---
col_logo, col_titulo = st.columns([1.2, 4.8])

with col_logo:
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #054A29 0%, #137547 50%, #2A9D8F 100%);
            padding: 16px 12px;
            border-radius: 16px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            border: 1px solid rgba(255,255,255,0.15);
        ">
            <span style="font-size: 38px; line-height: 1;">🧬🐮</span>
            <div style="font-size: 15px; font-weight: 800; letter-spacing: 1.5px; margin-top: 4px; text-transform: uppercase;">LECHER-IA</div>
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">HERD INVENTORY & AI SUITE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Nutrición de Precisión, Inventario SINIGA y Telemedicina")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Plataforma integral con control de hato, alertas inteligentes y consultoría veterinaria.</h4>", unsafe_allow_html=True)
    st.markdown("<small style='color: #666;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- PANEL IZQUIERDO (SIDEBAR): SOLO PARÁMETROS DE PRODUCCIÓN E INFORMACIÓN DEL HATO ---
st.sidebar.markdown("## 🧬 Parámetros del Hato & Producción")

raza = st.sidebar.selectbox("Ajuste Racial / Genético", ["Holstein-Friesian", "Jersey", "Pardo Suizo", "Cruza Zebuína / Lechera"])
paridad = st.sidebar.selectbox("Paridad", ["Multípara (2+ lactancias)", "Primípara (1er parto)"])
estado_productivo = st.sidebar.selectbox("Estado Fisiológico", [
    "Lactación Temprana (1-60 DIM)", 
    "Lactación Media (61-200 DIM)", 
    "Lactación Tardía (201-305 DIM)"
])

if "Temprana" in estado_productivo:
    dim = st.sidebar.slider("Días en Leche (DIM)", 5, 60, 30, 1)
elif "Media" in estado_productivo:
    dim = st.sidebar.slider("Días en Leche (DIM)", 61, 200, 120, 5)
else:
    dim = st.sidebar.slider("Días en Leche (DIM)", 201, 305, 250, 5)

peso_vivo = st.sidebar.number_input("Peso Vivo Base (kg)", min_value=350.0, max_value=900.0, value=650.0, step=10.0)
bcs = st.sidebar.slider("Condición Corporal (BCS 1-5)", 2.25, 4.0, 3.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌡️ Clima y Entorno")
temp_amb = st.sidebar.slider("Temperatura Ambiental (°C)", -5, 42, 22, 1)
humedad_rel = st.sidebar.slider("Humedad Relativa (%)", 20, 100, 50, 5)
ith = (1.8 * temp_amb + 32) - ((0.55 - 0.0055 * humedad_rel) * (1.8 * temp_amb - 26))

st.sidebar.markdown("---")
st.sidebar.markdown("### 🥛 Metas de Producción")
prod_def = 35.0 if "Holstein" in raza else 24.0
prod_leche = st.sidebar.slider("Leche Total Actual (kg/día)", 10.0, 60.0, prod_def, 0.5)

grasa_def = 3.7 if "Holstein" in raza else 4.8
proteina_def = 3.2 if "Holstein" in raza else 3.8

pct_grasa = st.sidebar.slider("Grasa en Leche (%)", 2.8, 6.0, grasa_def, 0.1)
pct_proteina = st.sidebar.slider("Proteína Verd. en Leche (%)", 2.6, 4.5, proteina_def, 0.1)

fcm_35 = (0.4324 * prod_leche) + (16.216 * (prod_leche * (pct_grasa / 100.0)))
ecm = (0.327 * prod_leche) + (12.95 * (prod_leche * (pct_grasa / 100.0))) + (7.2 * (prod_leche * (pct_proteina / 100.0)))

coef_mantenimiento = 0.080 if "Holstein" in raza else 0.092
nel_mantenimiento = coef_mantenimiento * (peso_vivo ** 0.75)

factor_estres_cms = 1.0
factor_estres_energetico = 1.0
if ith > 72:
    factor_estres_cms = max(0.75, 1.0 - ((ith - 72) * 0.012))
    factor_estres_energetico = 1.0 + ((ith - 72) * 0.008)

factor_raza_cms = 1.0 if "Holstein" in raza else 0.84
cms_base_nasem = ((0.022 * peso_vivo) + (0.38 * fcm_35)) * factor_raza_cms
factor_dim_curva = 1 - np.exp(-0.04 * dim) if dim < 50 else 1.0
cms_estimado_calc = round(cms_base_nasem * factor_dim_curva * factor_estres_cms, 2)
cms_estimado_nasem = max(5.0, min(cms_estimado_calc, 35.0))

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Requerimientos Nutricionales")
cms_req = st.sidebar.number_input("CMS Objetivo (kg MS/día)", min_value=5.0, max_value=35.0, value=cms_estimado_nasem, step=0.5)
nel_req = st.sidebar.slider("Energía Neta Lactancia (NEL Mcal/kg MS)", 1.50, 1.85, round(1.68 * factor_estres_energetico, 2), 0.01)

mp_calc = int(ecm * 70 + (nel_mantenimiento * 90))
mp_seguro = max(1000, min(mp_calc, 4200))
mp_req_g = st.sidebar.number_input("Proteína Metabolizable (PM g/día)", min_value=1000, max_value=4500, value=mp_seguro, step=50)

rdp_min_pct = st.sidebar.slider("RDP (% en MS)", 6.0, 12.0, 9.0, 0.2)
rup_min_pct = st.sidebar.slider("RUP (% en MS)", 3.0, 8.0, 4.5, 0.2)
pendf_min = st.sidebar.slider("peNDF Mínima (% en MS)", 14.0, 24.0, 18.0, 0.5)
starch_max = st.sidebar.slider("Almidón Máximo (% MS - Prev. SARA)", 20.0, 32.0, 27.0, 0.5)
ee_max = st.sidebar.slider("Grasa Total / EE Máxima (% MS)", 3.5, 7.0, 6.0, 0.5)

# --- CUERPO PRINCIPAL ORGANIZADO EN PESTAÑAS (TABS) ---
tab_form, tab_inv, tab_alert, tab_fin, tab_vision, tab_telemed = st.tabs([
    "🌾 Formulación TMR", 
    "🐄 Inventario Hato (SINIGA)", 
    "🔔 Alertas & Notificaciones AI",
    "📊 Finanzas & EBITDA", 
    "📷 Visión AI (Peso)", 
    "🩺 Telemedicina"
])

# Variables IoT globales
iot_ph_rumen = 6.2
iot_mixer_error_pct = 1.5
iot_status_str = "Activo (IoT MQTT)"

with tab_form:
    st.subheader("🌾 Matriz Nutricional e Insumos Disponibles")
    st.caption("Configura los costos y límites de inclusión para la optimización lineal de la ración.")
    
    datos_base = {
        "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS Maíz", "Melasa Caña", "Salvado Trigo", "Grasa Sobrepaso", "Carbonato Calcio"],
        "Disponible": [True, True, True, True, True, True, True, True, True, True],
        "Costo": [2.10, 4.20, 5.50, 4.90, 9.90, 7.20, 3.60, 4.60, 25.00, 1.80],
        "MS %": [35.0, 88.0, 88.0, 88.0, 89.0, 90.0, 75.0, 88.0, 99.0, 99.0],
        "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68, 5.20, 0.00],
        "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0, 0.0, 0.0],
        "RDP": [5.5, 13.0, 3.5, 4.0, 28.0, 10.0, 4.0, 12.0, 0.0, 0.0],
        "RUP": [3.0, 5.0, 6.0, 6.5, 17.0, 18.0, 0.5, 4.0, 0.0, 0.0],
        "PC": [8.5, 18.0, 9.0, 10.0, 48.0, 28.0, 4.5, 16.0, 0.0, 0.0],
        "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0, 0.0, 0.0],
        "peNDF": [32.0, 36.0, 2.0, 3.0, 2.0, 8.0, 0.0, 10.0, 0.0, 0.0],
        "Almidon": [28.0, 2.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0, 0.0, 0.0],
        "EE": [3.2, 2.1, 3.8, 3.1, 1.5, 9.5, 0.1, 4.0, 99.0, 0.0],
        "Ca": [0.25, 1.40, 0.03, 0.04, 0.35, 0.15, 0.90, 0.12, 0.00, 38.0],
        "P": [0.20, 0.25, 0.28, 0.29, 0.65, 0.75, 0.10, 0.95, 0.00, 0.02],
        "Min_Inclusion": [3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "Max_Inclusion": [25.0, 16.0, 15.0, 12.0, 12.0, 8.0, 4.0, 6.0, 1.5, 0.8]
    }

    df_ingredientes = pd.DataFrame(datos_base)
    editable_df = st.data_editor(df_ingredientes, num_rows="fixed")
    
    st.markdown("---")
    if st.button("🚀 Ejecutar Optimización Lineal (PuLP)"):
        try:
            prob = pulp.LpProblem("LecherIA_Precision_Diet", pulp.LpMinimize)
            variables = {}
            for idx, row in editable_df.iterrows():
                ing = str(row["Ingrediente"])
                is_available = bool(row["Disponible"])
                min_inc = float(row["Min_Inclusion"]) if is_available else 0.0
                max_inc = float(row["Max_Inclusion"]) if is_available else 0.0
                
                variables[ing] = pulp.LpVariable(f"x_{ing.replace(' ', '_')}", min_inc, max_inc, pulp.LpContinuous)
                
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["Costo"]) for idx, row in editable_df.iterrows()])
            effective_pendf = pendf_min + (1.5 if iot_ph_rumen < 5.9 else 0.0)
            
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req), "CMS_Total"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req), "Min_NEL"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g), "Min_MP"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RDP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rdp_min_pct) / 100.0) * float(cms_req), "Min_RDP"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RUP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rup_min_pct) / 100.0) * float(cms_req), "Min_RUP"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["peNDF"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(effective_pendf) / 100.0) * float(cms_req), "Min_peNDF"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req), "Max_Starch"
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["EE"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(ee_max) / 100.0) * float(cms_req), "Max_EE"
            
            prob.solve()
            
            if prob.status == 1:
                st.success("✅ ¡Dieta Bio-Optimizada con éxito!")
                resultados = []
                costo_alimento = 0
                for idx, row in editable_df.iterrows():
                    ing = str(row["Ingrediente"])
                    cantidad = variables[ing].varValue
                    if cantidad and cantidad > 0.001:
                        costo_parcial = cantidad * float(row["Costo"])
                        costo_alimento += costo_parcial
                        ms_pct = float(row["MS %"])
                        base_fresca_vaca = cantidad / (ms_pct / 100.0)
                        resultados.append({
                            "Ingrediente": ing,
                            "MS %": ms_pct,
                            "Inclusión (kg MS)": round(cantidad, 2),
                            "% en la Dieta (MS)": round((cantidad / cms_req) * 100, 2),
                            "Base Fresca (kg/vaca)": round(base_fresca_vaca, 2),
                            "Costo Parcial (MXN)": round(costo_parcial, 2)
                        })
                        
                st.dataframe(pd.DataFrame(resultados), use_container_width=True)
                st.info(f"💰 **Costo Total de Alimento:** ${costo_alimento:.2f} MXN / vaca / día")
            else:
                st.warning("⚠️ No se encontró solución factible con los límites actuales.")
        except Exception as e:
            st.error(f"Error en la optimización: {e}")

with tab_inv:
    st.subheader("🐄 Inventario del Hato Organizado por SINIGA y Arete Interno")
    st.caption("Clasificación oficial por etapa productiva. El hato se ordena automáticamente por número SINIGA y arete interno.")
    
    # Ordenar estrictamente el DataFrame por SINIGA y Arete Interno
    df_sorted = st.session_state.df_hato.sort_values(by=["SINIGA", "Arete Interno"]).reset_index(drop=True)
    
    # Editor interactivo para agregar o modificar vacas
    st.markdown("### 📋 Registro y Actualización del Hato")
    df_editado = st.data_editor(df_sorted, num_rows="dynamic", use_container_width=True)
    st.session_state.df_hato = df_editado
    
    st.markdown("---")
    st.markdown("### 📊 Resumen por Etapa Productiva")
    
    if not df_editado.empty and "Etapa Productiva" in df_editado.columns:
        conteo_etapas = df_editado["Etapa Productiva"].value_counts().reset_index()
        conteo_etapas.columns = ["Etapa Productiva", "Cantidad de Animales"]
        st.dataframe(conteo_etapas, use_container_width=True)

with tab_alert:
    st.subheader("🔔 Centro de Notificaciones Inteligentes & Alertas al Productor")
    st.caption("Sistema automatizado de monitoreo para secado, transiciones críticas y salud del hato lechero.")
    
    # Motor inteligente de alertas basado en el inventario actual
    alertas_generadas = []
    
    for idx, row in st.session_state.df_hato.iterrows():
        siniga = row.get("SINIGA", "S/N")
        arete = row.get("Arete Interno", "S/N")
        etapa = row.get("Etapa Productiva", "")
        dim = row.get("DIM / Edad (días)", 0)
        gestacion = row.get("Días Gestación", 0)
        salud = row.get("Estado Salud", "")
        
        # 1. Alerta de Secado (Vacas en producción con alta gestación o DIM avanzado)
        if etapa == "En producción" and (dim >= 220 or gestacion >= 210):
            alertas_generadas.append({
                "tipo": "🚨 SECADO REQUERIDO",
                "prioridade": "ALTA",
                "mensaje": f"Vaca Arete #{arete} (SINIGA: {siniga}) ha alcanzado {dim} DIM / {gestacion} días de gestación. Debe secarse e iniciar traslado al corral de vacas secas."
            })
            
        # 2. Alerta de Transición (Riesgo metabólico / cetosis)
        elif etapa == "En transición" or "CETOSIS" in str(salud).upper():
            alertas_generadas.append({
                "tipo": "⚠️ ALERTA SANITARIA / TRANSICIÓN",
                "prioridade": "MEDIA",
                "mensaje": f"Vaca Arete #{arete} (SINIGA: {siniga}) requiere monitoreo estricto de cetosis y consumo de materia seca (POST-PARTO)."
            })
            
        # 3. Alerta de Inseminación
        elif etapa == "Para inseminar" and dim >= 50:
            alertas_generadas.append({
                "tipo": " Reproductive 🧬 CELO / INSEMINACIÓN",
                "prioridade": "MEDIA",
                "mensaje": f"Vaca Arete #{arete} (SINIGA: {siniga}) lista en periodo voluntario de espera ({dim} DIM). Programar detección de celo o sincronización."
            })

    # Mostrar simulación de notificaciones en el teléfono del productor
    st.markdown("### 📱 Bandeja de Notificaciones Push (Simulador Móvil)")
    
    if alertas_generadas:
        for alerta in alertas_generadas:
            color_borde = "#D32F2F" if alerta["prioridade"] == "ALTA" else "#F57C00"
            bg_color = "#FFEBEE" if alerta["prioridade"] == "ALTA" else "#FFF3E0"
            
            st.markdown(
                f"""
                <div style="
                    background-color: {bg_color};
                    border-left: 6px solid {color_borde};
                    padding: 14px 18px;
                    border-radius: 8px;
                    margin-bottom: 12px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                ">
                    <div style="font-weight: bold; color: {color_borde}; font-size: 14px;">{alerta['tipo']}</div>
                    <div style="font-size: 13px; color: #333; margin-top: 4px;">{alerta['mensaje']}</div>
                    <div style="font-size: 10px; color: #777; margin-top: 6px; text-align: right;">Enviado vía SMS / Push Notifier • Hato Lecher-IA Pro</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.success("✅ No hay alertas críticas pendientes en el hato. Todos los animales se encuentran en parámetros normales.")

with tab_fin:
    st.subheader("📊 Estructura Financiera, EBITDA y Proyecciones")
    
    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        tam_corral = st.number_input("Tamaño del Corral / Hato (Vacas)", 1, 2000, 100, 10)
        precio_leche_base = st.number_input("Precio Base Leche (MXN / L)", 5.0, 20.0, 10.50, 0.10)
        bonif_solidos = st.number_input("Bonificación Sólidos (MXN / L)", 0.0, 3.0, 0.40, 0.05)
        precio_leche_total = precio_leche_base + bonif_solidos
    with col_fin2:
        st.markdown("**Costos Operativos (MXN/vaca/día):**")
        costo_mano_obra = st.number_input("Mano de Obra y Salarios", 0.0, 100.0, 18.0, 1.0)
        costo_salud_vet = st.number_input("Salud, Semen y Veterinaria", 0.0, 100.0, 8.5, 0.5)
        costo_energia_serv = st.number_input("Energía, Diésel y Servicios", 0.0, 100.0, 12.0, 1.0)
        costos_fijos_admin = st.number_input("Costos Fijos y Depreciaciones", 0.0, 200.0, 15.0, 1.0)
        ingresos_extras = st.number_input("Ingresos Extras Subproductos", 0.0, 50.0, 4.0, 0.5)

    st.markdown("---")
    st.subheader(f"📈 Proyección a 305 Días — {raza}")
    dias_lactancia = np.arange(1, 306)
    a_factor = prod_leche / ((dim ** 0.2) * np.exp(-0.003 * dim))
    produccion_predicha = a_factor * (dias_lactancia ** 0.2) * np.exp(-0.003 * dias_lactancia)
    
    df_curvas = pd.DataFrame({
        "Día de Lactancia": dias_lactancia,
        "Producción Leche Estimada (L/día)": np.round(produccion_predicha, 2),
        "Ingreso Leche ($ MXN)": np.round(produccion_predicha * precio_leche_total, 2)
    }).set_index("Día de Lactancia")
    
    st.line_chart(df_curvas)

with tab_vision:
    st.subheader("📷 Visión Artificial: Estimación Zoométrica de Peso")
    st.caption("Sube una fotografía lateral del bovino para calcular su peso vivo automáticamente mediante OpenCV.")
    
    foto_bovino = st.file_uploader("Fotografía Lateral del Bovino (.jpg / .png)", type=["jpg", "jpeg", "png"])
    peso_fotografia_calculado = peso_vivo
    
    if foto_bovino is not None:
        image = Image.open(foto_bovino)
        st.image(image, caption="Bovino Analizado por IA", width=400)
        
        img_np = np.array(image)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            factor_escala = h / max(1, w)
            peso_fotografia_calculado = round(float(w * h * 0.0018 * (1.15 if factor_escala < 0.6 else 0.95)), 1)
            peso_fotografia_calculado = max(350.0, min(peso_fotografia_calculado, 900.0))
            st.success(f"🎯 **Peso Estimado por Visión AI:** `{peso_fotografia_calculado} kg`")
        else:
            st.warning("⚠️ No se detectó contorno claro.")
    else:
        peso_fotografia_calculado = st.slider("Peso Vivo Calibrado por Fotografía (kg)", 350.0, 850.0, peso_vivo, 10.0)

with tab_telemed:
    st.subheader("🩺 Clínica Virtual y Telemedicina Bovina")
    st.caption("Agenda una consultoría técnica especializada de **30 minutos** con el **Dr. Alejandro Castañeda Correa**.")
    
    col_tel1, col_tel2 = st.columns([1.2, 1.8])
    
    with col_tel1:
        with st.expander("📅 Agendar Cita y Pago ($475.00 MXN)", expanded=not st.session_state.cita_pagada):
            nombre_productor = st.text_input("Productor / Establo", value="Ganadería Zacatecas")
            fecha_cita = st.date_input("Fecha de Consulta", min_value=datetime.today().date())
            hora_cita = st.time_input("Hora Preferida", value=datetime.strptime("10:00", "%H:%M").time())
            motivo_consulta = st.text_area("Motivo de Consulta", "Revisión de ración TMR y alertas de hato.")
            
            st.markdown("💳 **Costo:** **$475.00 MXN** (30 min)")
            metodo_pago = st.selectbox("Método de Pago", ["Tarjeta (Stripe)", "Transferencia SPEI", "PayPal"])
            
            if st.button("💳 Pagar $475 MXN y Confirmar"):
                st.session_state.cita_pagada = True
                st.session_state.detalles_cita = {
                    "productor": nombre_productor,
                    "fecha": str(fecha_cita),
                    "hora": str(hora_cita),
                    "motivo": motivo_consulta
                }
                st.success("✅ ¡Cita confirmada y pagada exitosamente!")
                
    with col_tel2:
        if st.session_state.cita_pagada:
            st.success(f"🟢 **Cita Activa para:** {st.session_state.detalles_cita.get('productor')} ({st.session_state.detalles_cita.get('fecha')} - {st.session_state.detalles_cita.get('hora')})")
            if st.button("🎥 Abrir Sala de Videollamada (30 min)"):
                st.session_state.ver_videollamada = not st.session_state.ver_videollamada
        else:
            st.info("💡 Agenda y paga tu consulta para habilitar el acceso a la sala de video.")

    if st.session_state.ver_videollamada and st.session_state.cita_pagada:
        st.markdown("---")
        st.markdown("### 🎥 Sala de Videollamada en Directo")
        room_id = f"LecherIA_Consultoria_{st.session_state.detalles_cita.get('fecha').replace('-', '')}"
        jitsi_html = f"""
            <iframe src="https://meet.jit.si/{room_id}#config.prejoinPageEnabled=false" 
                    height="550px" 
                    width="100%" 
                    style="border: 2px solid #137547; border-radius: 12px;" 
                    allow="camera; microphone; display-capture; autoplay">
            </iframe>
        """
        components.html(jitsi_html, height=580)

# --- 6. PIE DE PÁGINA INSTITUCIONAL ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        <strong>Lecher-IA Pro</strong> &bull; Sistema de Visión AI, Inventario SINIGA, Alertas & Telemedicina<br>
        Designed and engineered by <strong>Dr. Alejandro Castañeda Correa</strong>.
    </div>
    """, 
    unsafe_allow_html=True
)
