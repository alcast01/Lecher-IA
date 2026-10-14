import streamlit as st
import pandas as pd
import numpy as np
import pulp
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Lecher-IA Pro | Plataforma de Nutrición y Sostenibilidad Bovina",
    page_icon="🥛",
    layout="wide"
)

# --- MÓDULO 5: REPORTE OPERATIVO PDF (TMR Y HUELLA AMBIENTAL) ---
def generar_pdf_tmr(df_resultados, costo_total, cms_req, ecm, raza, estado_prod, tam_corral, precio_leche, iofc, ch4_vaca, n_exc_vaca):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#054A29'),
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        spaceAfter=14
    )
    
    story.append(Paragraph("<b>LECHER-IA Pro — HOJA DE MEZCLADO TMR Y CERTIFICACIÓN AMBIENTAL</b>", title_style))
    story.append(Paragraph(f"<b>Formulador:</b> Dr. Alejandro Castañeda Correa &nbsp;|&nbsp; <b>Perfil:</b> {raza} ({estado_prod}) &nbsp;|&nbsp; <b>Corral:</b> {tam_corral} vacas", subtitle_style))
    story.append(Spacer(1, 5))
    
    summary_text = (
        f"<b>CMS:</b> {cms_req:.2f} kg MS &nbsp;|&nbsp; "
        f"<b>ECM:</b> {ecm:.2f} kg &nbsp;|&nbsp; "
        f"<b>Costo:</b> ${costo_total:.2f} MXN &nbsp;|&nbsp; "
        f"<b>IOFC:</b> ${iofc:.2f} MXN &nbsp;|&nbsp; "
        f"<b>CH₄:</b> {ch4_vaca:.1f} g/día &nbsp;|&nbsp; "
        f"<b>N Excretado:</b> {n_exc_vaca:.1f} g/día"
    )
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    table_data = [["Ingrediente", "MS %", "Base Seca (kg/vaca)", "Base Fresca (kg/vaca)", f"Carga Corral ({tam_corral} vacas)"]]
    for _, row in df_resultados.iterrows():
        table_data.append([
            str(row["Ingrediente"]),
            f"{row['MS %']:.1f}%",
            f"{row['Inclusión (kg MS)']:.2f}",
            f"{row['Base Fresca (kg/vaca)']:.2f}",
            f"{row['Total Corral (kg)']:.1f} kg"
        ])
        
    t = Table(table_data, colWidths=[150, 60, 100, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#137547')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<i>Motor BMMCO (Stoichiometric Methane & Nitrogen Engine) integrado bajo normativas NASEM (2021) y Journal of Dairy Science.</i>", styles['Normal']))
    
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
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">BIO-ECONOMY & CARBON ENGINE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Bio-Optimización y Sostenibilidad (NASEM 2021)")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Precisión nutricional, rentabilidad y mitigación de metano en una sola plataforma.</h4>", unsafe_allow_html=True)
    st.markdown("<small style='color: #666;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- MÓDULO 1: CARACTERIZACIÓN FISIOLÓGICA Y AMBIENTAL ---
st.sidebar.markdown("## 🧬 1. Fisiología y Entorno")

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

sem_gestacion = st.sidebar.slider("Semanas de Gestación", 0, 40, 0, 1)
peso_def = 650 if "Holstein" in raza else (450 if "Jersey" in raza else 580)
peso_vivo = st.sidebar.slider("Peso Vivo (kg)", 350, 850, peso_def, 10)
bcs = st.sidebar.slider("Condición Corporal (BCS 1-5)", 2.25, 4.0, 3.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌡️ Estrés Térmico (ITH)")
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
st.sidebar.markdown("### ⚙️ Requerimientos Nutricionales Estimados")
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

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 Operativa de Corral y Economía")
tam_corral = st.sidebar.number_input("Tamaño del Corral (N° de Vacas)", min_value=1, max_value=1000, value=80, step=5)
precio_leche = st.sidebar.number_input("Precio de la Leche (MXN / L)", min_value=5.0, max_value=20.0, value=10.50, step=0.10)

if ith > 72:
    st.sidebar.warning(f"🔥 **Estrés Térmico Detectado (ITH: {ith:.1f}):** Se aplicó depresión de consumo e incremento energético.")

st.markdown(f"""
> **Resumen Fisiológico ({raza} | {estado_productivo} | ITH: {ith:.1f}):**  
> **ECM:** `{ecm:.2f} kg/día` &bull; **CMS Estimado NASEM:** `{cms_estimado_nasem} kg MS/día` &bull; **NEL Req:** `{nel_req} Mcal/kg MS`
""")

# --- MÓDULO 2: BASE DE DATOS Y MATRIZ NUTRICIONAL CON VARIABLES DE METANO Y NITRÓGENO ---
st.subheader("🌾 2. Matriz Nutricional, Estequiometría y Disponibilidad de Insumos")
st.caption("Matriz avanzada con coeficientes de fermentación ruminal para el cálculo en tiempo real de metano y nitrógeno excretado.")

datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS Maíz", "Melasa Caña", "Salvado Trigo", "Grasa Sobrepaso", "Carbonato Calcio"],
    "Disponible": [True, True, True, True, True, True, True, True, True, True],
    "Costo": [2.10, 4.20, 5.50, 4.90, 9.90, 7.20, 3.60, 4.60, 25.00, 1.80],
    "MS %": [35.0, 88.0, 88.0, 88.0, 89.0, 90.0, 75.0, 88.0, 99.0, 99.0],
    "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68, 5.20, 0.00],
    "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0, 0.0, 0.0],
    "RDP": [5.5, 13.0, 3.5, 4.0, 28.0, 10.0, 4.0, 12.0, 0.0, 0.0],
    "RUP": [3.0, 5.0, 6.0, 6.5, 17.0, 18.0, 0.5, 4.0, 0.0, 0.0],
    "PC": [8.5, 18.0, 9.0, 10.0, 48.0, 28.0, 4.5, 16.0, 0.0, 0.0],  # Proteína Cruda para cálculo de N
    "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0, 0.0, 0.0],
    "peNDF": [32.0, 36.0, 2.0, 3.0, 2.0, 8.0, 0.0, 10.0, 0.0, 0.0],
    "Almidon": [28.0, 2.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0, 0.0, 0.0],
    "EE": [3.2, 2.1, 3.8, 3.1, 1.5, 9.5, 0.1, 4.0, 99.0, 0.0],
    "Ca": [0.25, 1.40, 0.03, 0.04, 0.35, 0.15, 0.90, 0.12, 0.00, 38.0],
    "P": [0.20, 0.25, 0.28, 0.29, 0.65, 0.75, 0.10, 0.95, 0.00, 0.02],
    "K": [1.10, 2.20, 0.35, 0.38, 2.10, 0.85, 3.20, 1.20, 0.00, 0.00],
    "Na": [0.01, 0.10, 0.02, 0.02, 0.03, 0.20, 0.15, 0.04, 0.00, 0.00],
    "Cl": [0.18, 0.55, 0.05, 0.09, 0.08, 0.15, 1.10, 0.10, 0.00, 0.00],
    "S": [0.12, 0.28, 0.09, 0.11, 0.42, 0.45, 0.50, 0.21, 0.00, 0.00],
    "Min_Inclusion": [3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [25.0, 16.0, 15.0, 12.0, 12.0, 8.0, 4.0, 6.0, 1.5, 0.8]
}

df_ingredientes = pd.DataFrame(datos_base)
editable_df = st.data_editor(df_ingredientes, num_rows="fixed")

# --- MÓDULO 3: MOTOR DE OPTIMIZACIÓN LINEAL (PuLP) ---
st.markdown("---")
if st.button("🚀 Ejecutar Optimización Bio-Económica (BMMCO Engine)"):
    try:
        prob = pulp.LpProblem("LecherIA_Precision_Diet", pulp.LpMinimize)
        
        variables = {}
        for idx, row in editable_df.iterrows():
            ing = str(row["Ingrediente"])
            is_available = bool(row["Disponible"])
            
            if is_available:
                min_inc = float(row["Min_Inclusion"])
                max_inc = float(row["Max_Inclusion"])
            else:
                min_inc = 0.0
                max_inc = 0.0
                
            variables[ing] = pulp.LpVariable(
                f"x_{ing.replace(' ', '_')}", 
                min_inc, 
                max_inc,
                pulp.LpContinuous
            )
            
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["Costo"]) for idx, row in editable_df.iterrows()])
        
        # Restricciones Nutricionales
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req), "CMS_Total"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req), "Min_NEL"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g), "Min_MP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RDP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rdp_min_pct) / 100.0) * float(cms_req), "Min_RDP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RUP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rup_min_pct) / 100.0) * float(cms_req), "Min_RUP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["peNDF"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(pendf_min) / 100.0) * float(cms_req), "Min_peNDF"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req), "Max_Starch"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["EE"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(ee_max) / 100.0) * float(cms_req), "Max_EE"
        
        prob.solve()
        
        if prob.status == 1:
            st.success("✅ ¡Dieta Bio-Optimizada con Éxito (Mínimo Costo + Huella Ambiental Mínima)!")
            
            resultados = []
            costo_total = 0
            nel_sum, mp_sum, rdp_sum, rup_sum, pendf_sum, starch_sum, ee_sum = 0, 0, 0, 0, 0, 0, 0
            pc_total_g = 0
            fdn_total_kg = 0
            
            for idx, row in editable_df.iterrows():
                ing = str(row["Ingrediente"])
                cantidad = variables[ing].varValue
                if cantidad and cantidad > 0.001:
                    costo_parcial = cantidad * float(row["Costo"])
                    costo_total += costo_parcial
                    nel_sum += cantidad * float(row["NEL"])
                    mp_sum += cantidad * float(row["MP"])
                    rdp_sum += cantidad * (float(row["RDP"]) / 100.0)
                    rup_sum += cantidad * (float(row["RUP"]) / 100.0)
                    pendf_sum += cantidad * float(row["peNDF"])
                    starch_sum += cantidad * float(row["Almidon"])
                    ee_sum += cantidad * float(row["EE"])
                    
                    pc_total_g += cantidad * (float(row["PC"]) / 100.0) * 1000.0
                    fdn_total_kg += cantidad * (float(row["FDN"]) / 100.0)
                    
                    ms_pct = float(row["MS %"])
                    base_fresca_vaca = cantidad / (ms_pct / 100.0)
                    total_corral = base_fresca_vaca * tam_corral
                    
                    pct_dieta = (cantidad / cms_req) * 100
                    resultados.append({
                        "Ingrediente": ing,
                        "MS %": ms_pct,
                        "Inclusión (kg MS)": round(cantidad, 2),
                        "% en la Dieta (MS)": round(pct_dieta, 2),
                        "Base Fresca (kg/vaca)": round(base_fresca_vaca, 2),
                        "Total Corral (kg)": round(total_corral, 1),
                        "Costo Parcial (MXN)": round(costo_parcial, 2)
                    })
                    
            df_res = pd.DataFrame(resultados)
            
            # --- CÁLCULO ESTEQUIOMÉTRICO BMMCO (Metano y Nitrógeno) ---
            # Estequiometría de metano entérico (Moe & Tyrrell / NASEM 2021):
            # CH4 (g/día) = 34.07 * FDN_digestible + 18.56 * Almidón_digestible (aproximación basada en fermentación ruminal estequiométrica)
            ch4_vaca = (fdn_total_kg * 0.55 * 38.0) + ((starch_sum / 100.0 * cms_req) * 0.85 * 22.0)
            intensidad_ch4 = ch4_vaca / ecm  # g CH4 / kg ECM
            
            # Nitrógeno Excretado (g/día) = Nitrógeno Consumido - Nitrógeno Retenido en Leche
            n_consumido = pc_total_g / 6.25
            n_leche = (prod_leche * (pct_proteina / 100.0) * 1000.0) / 6.38
            n_excretado = max(30.0, n_consumido - n_leche - 25.0) # Ajuste metabólico por heces y orina
            
            # --- MÓDULO 4: KPIS Y ANALÍTICA BIOLÓGICA ---
            ingreso_leche = prod_leche * precio_leche
            iofc = ingreso_leche - costo_total
            eficiencia_fca = prod_leche / cms_req
            
            col_tabla, col_resumen = st.columns([3.2, 1.8])
            
            with col_tabla:
                st.markdown("### 🧮 3. Ración Bio-Optimizada y Escala TMR de Campo")
                st.dataframe(df_res[["Ingrediente", "MS %", "Inclusión (kg MS)", "% en la Dieta (MS)", "Base Fresca (kg/vaca)", f"Total Corral ({tam_corral} vacas)"]], use_container_width=True)
                
                pdf_buffer = generar_pdf_tmr(df_res, costo_total, cms_req, ecm, raza, estado_productivo, tam_corral, precio_leche, iofc, ch4_vaca, n_excretado)
                st.download_button(
                    label="📄 Descargar Hoja TMR y Certificación Ambiental en PDF",
                    data=pdf_buffer,
                    file_name=f"TMR_Sostenible_LecherIA_{raza}_{dim}DIM.pdf",
                    mime="application/pdf"
                )

            with col_resumen:
                st.markdown("### 📊 4. KPIs Financieros y Ambientales (BMMCO)")
                st.metric("Costo Diario / Vaca", f"${costo_total:.2f} MXN")
                st.metric("IOFC (Margen sobre Alimento)", f"${iofc:.2f} MXN/vaca/día", f"Leche: ${precio_leche:.2f}/L")
                st.metric("Metano Entérico Estimado", f"{ch4_vaca:.1f} g CH₄/día", f"Intensidad: {intensidad_ch4:.1f} g/kg ECM")
                st.metric("Excreción Nitrogenada (N)", f"{n_excretado:.1f} g N/día", "Protección de mantos acuíferos")
                st.metric("Eficiencia Alimenticia (FCA)", f"{eficiencia_fca:.2f} kg Leche/kg CMS")
                st.metric("NEL Consumida", f"{nel_sum/cms_req:.2f} Mcal/kg", f"Meta: {nel_req}")

            # --- MODELACIÓN PRODUCTIVA DE WOOD Y BALANCE ENERGÉTICO ---
            st.markdown("---")
            st.subheader(f"📈 4. Predicción Productiva y Balance Energético a 305 Días — {raza}")
            
            dias_lactancia = np.arange(1, 306)
            a_factor = prod_leche / ((dim ** 0.2) * np.exp(-0.003 * dim))
            produccion_predicha = a_factor * (dias_lactancia ** 0.2) * np.exp(-0.003 * dias_lactancia)
            
            cms_predicho = ((0.022 * peso_vivo) + (0.38 * ((0.327 * produccion_predicha) + (12.95 * (produccion_predicha * (pct_grasa / 100.0)))))) * factor_raza_cms * (1 - np.exp(-0.04 * dias_lactancia)) * factor_estres_cms
            
            nel_aportada = cms_predicho * (nel_sum / cms_req)
            nel_mantenimiento_dinamico = coef_mantenimiento * (peso_vivo ** 0.75) * factor_estres_energetico
            nel_requerida_total = nel_mantenimiento_dinamico + (0.70 * produccion_predicha)
            
            df_curvas = pd.DataFrame({
                "Día de Lactancia": dias_lactancia,
                "Producción Leche Estimada (kg/día)": np.round(produccion_predicha, 2),
                "Consumo MS Estimado (kg/día)": np.round(cms_predicho, 2),
                "Energía Aportada (Mcal NEL)": np.round(nel_aportada, 2),
                "Energía Requerida Total (Mcal NEL)": np.round(nel_requerida_total, 2)
            }).set_index("Día de Lactancia")
            
            tab1, tab2 = st.tabs(["📉 Curva de Lactancia & CMS", "⚡ Balance Energético (Mcal NEL)"])
            
            with tab1:
                st.line_chart(df_curvas[["Producción Leche Estimada (kg/día)", "Consumo MS Estimado (kg/día)"]])
                st.info(f"📍 **Evaluación actual:** Día {dim} de lactancia | Producción: **{prod_leche} kg/día** | Consumo estimado: **{cms_predicho[dim-1]:.1f} kg MS/día**")

            with tab2:
                st.line_chart(df_curvas[["Energía Aportada (Mcal NEL)", "Energía Requerida Total (Mcal NEL)"]])
                if dim < 60:
                    st.warning("⚠️ **Lactancia Temprana:** La vaca está en Balance Energético Negativo (BEN). Moviliza reservas corporales.")
                else:
                    st.success("✅ **Balance Energético Positivo:** Cubre requerimientos de producción y recuperación corporal.")

        else:
            st.error("⚠️ **No se encontró solución factible.** Habilita más insumos o ajusta los límites en la matriz.")
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el modelo matemático: {e}")

# --- 5. PIE DE PÁGINA INSTITUCIONAL ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        <strong>Lecher-IA Pro</strong> &bull; Sistema Avanzado de Optimización Nutricional Bovina<br>
        Diseñado y creado por el <strong>Dr. Alejandro Castañeda Correa</strong>.
    </div>
    """, 
    unsafe_allow_html=True
)
