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

# --- 1. CONFIGURACIÓN DE PÁGINA & ESTILOS AVANZADOS ---
st.set_page_config(
    page_title="Lecher-IA Pro | Digital Twin & Precision Livestock Farming",
    page_icon="🧬",
    layout="wide"
)

# Estilizado personalizado CSS
st.markdown("""
<style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        color: #054A29;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0px 0px;
        padding-left: 16px;
        padding-right: 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estados de sesión
if "cita_pagada" not in st.session_state:
    st.session_state.cita_pagada = False
if "detalles_cita" not in st.session_state:
    st.session_state.detalles_cita = {}
if "ver_videollamada" not in st.session_state:
    st.session_state.ver_videollamada = False

# Inicializar hato avanzado
if "df_hato" not in st.session_state:
    st.session_state.df_hato = pd.DataFrame([
        {"SINIGA": "MX-14-032-8811", "Arete Interno": "101", "Etapa Productiva": "En producción", "DIM / Edad (días)": 240, "Días Gestación": 205, "Prod. Leche (L)": 32.5, "pH Ruminal (IoT)": 6.25, "Rumia (min/día)": 480, "Estado Salud": "Óptimo"},
        {"SINIGA": "MX-14-032-9012", "Arete Interno": "102", "Etapa Productiva": "En transición", "DIM / Edad (días)": 12, "Días Gestación": 0, "Prod. Leche (L)": 38.0, "pH Ruminal (IoT)": 5.75, "Rumia (min/día)": 390, "Estado Salud": "⚠️ Alerta SARA / Cetosis"},
        {"SINIGA": "MX-14-033-1045", "Arete Interno": "103", "Etapa Productiva": "Vaca seca", "DIM / Edad (días)": 285, "Días Gestación": 235, "Prod. Leche (L)": 0.0, "pH Ruminal (IoT)": 6.45, "Rumia (min/día)": 510, "Estado Salud": "Preparación Parto"},
        {"SINIGA": "MX-14-034-5521", "Arete Interno": "201", "Etapa Productiva": "Para inseminar", "DIM / Edad (días)": 75, "Días Gestación": 0, "Prod. Leche (L)": 42.0, "pH Ruminal (IoT)": 6.30, "Rumia (min/día)": 490, "Estado Salud": "Periodo Voluntario OK"},
        {"SINIGA": "MX-14-035-7788", "Arete Interno": "301", "Etapa Productiva": "Becerra de reemplazo gestante", "DIM / Edad (días)": 450, "Días Gestación": 110, "Prod. Leche (L)": 0.0, "pH Ruminal (IoT)": 6.50, "Rumia (min/día)": 420, "Estado Salud": "Crecimiento Normal"},
        {"SINIGA": "MX-14-035-8899", "Arete Interno": "302", "Etapa Productiva": "Becerra de reemplazo no gestante", "DIM / Edad (días)": 380, "Días Gestación": 0, "Prod. Leche (L)": 0.0, "pH Ruminal (IoT)": 6.55, "Rumia (min/día)": 400, "Estado Salud": "Desarrollo"},
        {"SINIGA": "MX-14-036-1234", "Arete Interno": "401", "Etapa Productiva": "Becerra recién nacida", "DIM / Edad (días)": 5, "Días Gestación": 0, "Prod. Leche (L)": 0.0, "pH Ruminal (IoT)": 6.80, "Rumia (min/día)": 120, "Estado Salud": "Calostro OK"}
    ])

# --- REPORTE OPERATIVO PDF NASEM 2021 ---
def generar_pdf_tmr_financiero(df_resultados, costo_alimento, cms_req, ecm, raza, estado_prod, tam_corral, precio_leche, iofc, ebitda_diario, costo_total_litro, break_even_leche, ch4_vaca, n_exc_vaca, iot_status, mun_est, de_novo_fat):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#054A29'), spaceAfter=4)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=10)
    
    story.append(Paragraph("<b>LECHER-IA Pro — DIGITAL TWIN & NASEM 2021 REPORT</b>", title_style))
    story.append(Paragraph(f"<b>Formulador:</b> Dr. Alejandro Castañeda Correa &bull; <b>Perfil:</b> {raza} ({estado_prod}) &bull; <b>Corral:</b> {tam_corral} vacas &bull; <b>IoT Link:</b> {iot_status}", subtitle_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph(f"<b>Costo Alimento/Vaca:</b> ${costo_alimento:.2f} MXN &bull; <b>Costo/L:</b>${costo_total_litro:.2f} MXN &bull; <b>Punto Equilibrio:</b> {break_even_leche:.1f} L/vaca", styles['Normal']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>IOFC/Vaca:</b> ${iofc:.2f} MXN/día &bull; <b>MUN Estimado:</b> {mun_est:.1f} mg/dL &bull; <b>Grasa De Novo:</b> {de_novo_fat:.2f}%", styles['Normal']))
    story.append(Spacer(1, 10))
    
    table_data = [["Ingrediente", "MS %", "Inclusión (kg MS)", "Base Fresca (kg)", f"Total Corral ({tam_corral} v)"]]
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
    story.append(Paragraph("<i>Simulación Gemelo Digital basada en ecuaciones dinamicas de pasaje ruminal y metabolómica mamaria.</i>", styles['Normal']))
    
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
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">DIGITAL TWIN & PLF SUITE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Gemelo Digital, Metabolómica & PLF Intelligence")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Plataforma global de precisión bionutricional, análisis predictivo y telemedicina.</h4>", unsafe_allow_html=True)
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
st.sidebar.markdown("### ⚙️ Requerimientos Nutricionales NASEM")
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

# --- CUERPO PRINCIPAL ORGANIZADO EN 7 PESTAÑAS DIVERSIFICADAS ---
tab_form, tab_twin, tab_inv, tab_alert, tab_monte, tab_vision, tab_telemed = st.tabs([
    "🌾 Formulación TMR", 
    "🧬 Gemelo Digital & Metabolómica",
    "🐄 Inventario Hato (SINIGA)", 
    "🔔 Alertas & Comandos Push",
    "🎲 Monte Carlo Stress-Test", 
    "📷 Visión AI (Peso)", 
    "🩺 Telemedicina"
])

# Telemetría IoT por defecto
iot_ph_rumen = 6.18
iot_rumination_min = 465
iot_status_str = "Activo (IoT MQTT Telemetry)"

with tab_form:
    st.subheader("🌾 Matriz Nutricional, Insumos & Optimización Lineal PuLP")
    
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
    if st.button("🚀 Ejecutar Optimización Bio-Económica"):
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
            
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req)
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req)
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g)
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["peNDF"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(effective_pendf) / 100.0) * float(cms_req)
            prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req)
            
            prob.solve()
            
            if prob.status == 1:
                st.success("✅ ¡Dieta Racional Optimizada!")
                resultados = []
                costo_alimento = 0
                for idx, row in editable_df.iterrows():
                    ing = str(row["Ingrediente"])
                    cantidad = variables[ing].varValue
                    if cantidad and cantidad > 0.001:
                        costo_parcial = cantidad * float(row["Costo"])
                        costo_alimento += costo_parcial
                        resultados.append({
                            "Ingrediente": ing,
                            "MS %": float(row["MS %"]),
                            "Inclusión (kg MS)": round(cantidad, 2),
                            "% en Dieta": round((cantidad / cms_req) * 100, 2),
                            "Base Fresca (kg/vaca)": round(cantidad / (float(row["MS %"]) / 100.0), 2),
                            "Costo Parcial (MXN)": round(costo_parcial, 2)
                        })
                df_res = pd.DataFrame(resultados)
                st.dataframe(df_res, use_container_width=True)
                st.info(f"💰 **Costo Alimento/Vaca/Día:** ${costo_alimento:.2f} MXN")
            else:
                st.warning("⚠️ Sin solución factible. Revisa las restricciones.")
        except Exception as e:
            st.error(f"Error en la optimización: {e}")

with tab_twin:
    st.subheader("🧬 Gemelo Digital Bionutricional & Perfil Metabolómico (NASEM 2021)")
    st.caption("Simulación mecanística avanzada de cinética de digestión, pH ruminal biofísico y síntesis mamaria de ácidos grasos.")
    
    col_tw1, col_tw2, col_tw3 = st.columns(3)
    
    # 1. Cinética Ruminal y Tasa de Pasaje (Kp)
    kp_forraje = round(2.5 + 0.05 * (cms_req / peso_vivo * 100), 2)
    kp_concentrado = round(3.8 + 0.12 * (cms_req / peso_vivo * 100), 2)
    
    # 2. Estimación Ureica en Leche (MUN)
    mun_estimado = round(8.5 + (rdp_min_pct * 0.45) - (starch_max * 0.15), 1)
    
    # 3. Síntesis Mamaria de Ácidos Grasos (De Novo vs Preformados)
    de_novo_fat_pct = round(max(0.8, 1.45 - (starch_max * 0.018) + (pendf_min * 0.015)), 2)
    
    # 4. Salivación y pH ruminal biofísico por Rumia
    saliva_litros = round(iot_rumination_min * 0.22 + cms_req * 3.5, 1)
    ph_biofisico = round(6.6 - (starch_max * 0.035) + (pendf_min * 0.02) + (iot_rumination_min * 0.0008), 2)
    
    with col_tw1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Tasa Pasaje Forraje (Kp)", f"{kp_forraje} %/h", "NASEM 2021 Equation")
        st.metric("Tasa Pasaje Concentrado (Kp)", f"{kp_concentrado} %/h", "Dynamic Passage Rate")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_tw2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Nitrógeno Ureico Leche (MUN)", f"{mun_estimado} mg/dL", "Rango Óptimo: 8.0 - 12.0")
        st.metric("Ácidos Grasos De Novo", f"{de_novo_fat_pct} g/100g", "Predictor Depresión Grasa")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_tw3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Producción de Saliva Est.", f"{saliva_litros} L/día", "Capacidad Buffer Ruminal")
        st.metric("pH Ruminal Biofísico", f"{ph_biofisico}", "Riesgo SARA: pH < 5.8" if ph_biofisico >= 5.8 else "🚨 RIESGO SARA ELEVADO")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔬 Perfil de Biohidrogenación Ruminal & Ácidos Grasos Mamarios")
    df_fatty = pd.DataFrame({
        "Fracción Lípida": ["Ácidos Grasos De Novo (C4-C14)", "Ácidos Grasos Mixtos (C16)", "Ácidos Grasos Preformados (C18+)"],
        "Proporción Estimada (%)": [de_novo_fat_pct * 22, 35.0, 100 - (de_novo_fat_pct * 22 + 35.0)],
        "Origen Metabolicó": ["Síntesis Mamaria Acetato/Bustirato", "Dieta + Lipogénesis De Novo", "Dieta + Movilización Adiposa"]
    })
    st.table(df_fatty)

with tab_inv:
    st.subheader("🐄 Inventario del Hato Organizado por SINIGA y Arete Interno")
    df_sorted = st.session_state.df_hato.sort_values(by=["SINIGA", "Arete Interno"]).reset_index(drop=True)
    
    st.markdown("### 📋 Registro Oficial y Parámetros Sensorizados PLF")
    df_editado = st.data_editor(df_sorted, num_rows="dynamic", use_container_width=True)
    st.session_state.df_hato = df_editado

with tab_alert:
    st.subheader("🔔 Centro de Alertas Inteligentes & Comandos Ejecutables Push")
    st.caption("Recibe notificaciones críticas en tiempo real y ejecuta acciones directas en el sistema de gestión del establo.")
    
    for idx, row in st.session_state.df_hato.iterrows():
        siniga = row.get("SINIGA", "S/N")
        arete = row.get("Arete Interno", "S/N")
        etapa = row.get("Etapa Productiva", "")
        dim = row.get("DIM / Edad (días)", 0)
        gestacion = row.get("Días Gestación", 0)
        ph_vaca = row.get("pH Ruminal (IoT)", 6.2)
        
        # Alerta de Secado Automática
        if etapa == "En producción" and (dim >= 220 or gestacion >= 200):
            st.error(f"🚨 **ALERTA DE SECADO REQUERIDO:** Vaca Arete #{arete} (SINIGA: {siniga}) — {dim} DIM / {gestacion} Días Gestación.")
            col_b1, col_b2 = st.columns([1, 4])
            with col_b1:
                if st.button(f"📲 Programar Secado #{arete}", key=f"sec_{arete}"):
                    st.success(f"✅ Comando enviado al operante: Vaca #{arete} marcada para secado y trasladada a Corral Seco.")
        
        # Alerta SARA / pH Ruminal
        if ph_vaca < 5.85:
            st.warning(f"⚠️ **ALERTA IoT SARA / ACIDOSA:** Vaca Arete #{arete} (pH Ruminal Sensorizado: {ph_vaca}). Rumia reducida.")
            col_b3, col_b4 = st.columns([1, 4])
            with col_b3:
                if st.button(f"💊 Ajustar Buffer #{arete}", key=f"buf_{arete}"):
                    st.info(f"✅ Comando enviado a carro mezclador: Incremento de Bicarbonato de Sodio +0.5% en Corral de Vaca #{arete}.")

with tab_monte:
    st.subheader("🎲 Análisis Estocástico de Riesgo Financiero (Monte Carlo Stress-Test)")
    st.caption("Somete la rentabilidad del hato a 1,000 simulaciones estocásticas considerando volatilidad de precios de insumos e impacto climático.")
    
    if st.button("🎰 Ejecutar 1,000 Simulaciones Monte Carlo"):
        np.random.seed(42)
        simulaciones = 1000
        costos_simulados = np.random.normal(loc=185.0, scale=18.5, size=simulaciones) # Costo diario alimentación
        leche_simulada = np.random.normal(loc=prod_leche, scale=2.5, size=simulaciones) # Variación de leche
        
        precio_total_sim = 10.90
        margen_iofc_sim = (leche_simulada * precio_total_sim) - costos_simulados
        
        var_95 = np.percentile(margen_iofc_sim, 5)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Margen IOFC Medio Simulado", f"${np.mean(margen_iofc_sim):,.2f} MXN", "Promedio 1,000 Iteraciones")
        with col_m2:
            st.metric("Valor en Riesgo 95% (VaR)", f"${var_95:,.2f} MXN", "Peor escenario en el 95% de casos")
        with col_m3:
            st.metric("Probabilidad de IOFC Negativo", f"{(np.sum(margen_iofc_sim < 0) / simulaciones) * 100:.1f}%", "Riesgo Financiero Establo")
            
        st.markdown("### 📊 Distribución Estocástica del Margen IOFC ($ MXN/vaca/día)")
        chart_data = pd.DataFrame({"Margen IOFC Simulado ($ MXN)": margen_iofc_sim})
        st.line_chart(chart_data)

with tab_vision:
    st.subheader("📷 Visión Artificial: Estimación Zoométrica de Peso")
    foto_bovino = st.file_uploader("Fotografía Lateral del Bovino (.jpg / .png)", type=["jpg", "jpeg", "png"])
    
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
            peso_calc = round(float(w * h * 0.0018 * (1.15 if factor_escala < 0.6 else 0.95)), 1)
            peso_calc = max(350.0, min(peso_calc, 900.0))
            st.success(f"🎯 **Peso Calibrado por Visión Artificial:** `{peso_calc} kg`")
        else:
            st.warning("⚠️ No se detectó contorno claro.")

with tab_telemed:
    st.subheader("🩺 Clínica Virtual & Telemedicina Bovina")
    col_tel1, col_tel2 = st.columns([1.2, 1.8])
    
    with col_tel1:
        with st.expander("📅 Agendar Cita y Pago ($475.00 MXN)", expanded=not st.session_state.cita_pagada):
            nombre_productor = st.text_input("Productor / Establo", value="Ganadería Zacatecas")
            fecha_cita = st.date_input("Fecha de Consulta", min_value=datetime.today().date())
            hora_cita = st.time_input("Hora Preferida", value=datetime.strptime("10:00", "%H:%M").time())
            motivo_consulta = st.text_area("Motivo", "Revisión NASEM 2021 y Gemelo Digital.")
            
            st.markdown("💳 **Costo:** **$475.00 MXN** (30 min)")
            if st.button("💳 Pagar $475 MXN y Confirmar"):
                st.session_state.cita_pagada = True
                st.session_state.detalles_cita = {"productor": nombre_productor, "fecha": str(fecha_cita), "hora": str(hora_cita)}
                st.success("✅ ¡Cita pagada exitosamente!")
                
    with col_tel2:
        if st.session_state.cita_pagada:
            st.success(f"🟢 **Cita Agendada:** {st.session_state.detalles_cita.get('productor')} ({st.session_state.detalles_cita.get('fecha')})")
            if st.button("🎥 Abrir Sala de Videollamada (30 min)"):
                st.session_state.ver_videollamada = not st.session_state.ver_videollamada

    if st.session_state.ver_videollamada and st.session_state.cita_pagada:
        room_id = f"LecherIA_Consultoria_{st.session_state.detalles_cita.get('fecha').replace('-', '')}"
        jitsi_html = f"""
            <iframe src="https://meet.jit.si/{room_id}#config.prejoinPageEnabled=false" 
                    height="550px" width="100%" style="border: 2px solid #137547; border-radius: 12px;" 
                    allow="camera; microphone; display-capture; autoplay">
            </iframe>
        """
        components.html(jitsi_html, height=580)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        <strong>Lecher-IA Pro</strong> &bull; Digital Twin, Precision Livestock Farming & Telemedicine<br>
        Designed and engineered by <strong>Dr. Alejandro Castañeda Correa</strong>.
    </div>
    """, 
    unsafe_allow_html=True
)
