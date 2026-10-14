import streamlit as st
import pandas as pd
import numpy as np
import pulp
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Lecher-IA Pro | Plataforma IoT & Bio-Económica Bovina",
    page_icon="🥛",
    layout="wide"
)

# --- MÓDULO 5: REPORTE OPERATIVO, FINANCIERO E IOT EN PDF ---
def generar_pdf_tmr_financiero(df_resultados, costo_alimento, cms_req, ecm, raza, estado_prod, tam_corral, precio_leche, iofc, ebitda_diario, costo_total_litro, break_even_leche, ch4_vaca, n_exc_vaca, iot_status):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#054A29'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        spaceAfter=10
    )
    
    story.append(Paragraph("<b>LECHER-IA Pro — REPORTE FINANCIERO, TMR & TELEMETRÍA PLF</b>", title_style))
    story.append(Paragraph(f"<b>Formulador:</b> Dr. Alejandro Castañeda Correa &nbsp;|&nbsp; <b>Perfil:</b> {raza} ({estado_prod}) &nbsp;|&nbsp; <b>Corral:</b> {tam_corral} vacas &nbsp;|&nbsp; <b>IoT Link:</b> {iot_status}", subtitle_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph(f"<b>Costo Alimento/Vaca:</b> ${costo_alimento:.2f} MXN &nbsp;|&nbsp; <b>Costo Total/L:</b> ${costo_total_litro:.2f} MXN &nbsp;|&nbsp; <b>Punto Equilibrio:</b> {break_even_leche:.1f} L/vaca", styles['Normal']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<b>IOFC/Vaca:</b> ${iofc:.2f} MXN/día &nbsp;|&nbsp; <b>EBITDA Corral/Mes:</b> ${ebitda_diario * tam_corral * 30.5:,.2f} MXN &nbsp;|&nbsp; <b>Huella CH₄:</b> {ch4_vaca:.1f} g/día", styles['Normal']))
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
    story.append(Paragraph("<i>Optimización bio-económica integrada con telemetría de precisión (Aretes IoT, Bolos Ruminales, Podómetros y Carro Mezclador).</i>", styles['Normal']))
    
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
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">PLF & IoT PRECISION SUITE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Plataforma IoT y Telemetría Ganadera")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Integración inteligente con aretes, bolos, podómetros y carros mezcladores.</h4>", unsafe_allow_html=True)
    st.markdown("<small style='color: #666;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- MÓDULO IOT / PLF: TELEMETRÍA Y DISPOSITIVOS INTELIGENTES ---
st.sidebar.markdown("## 📡 0. Conectividad IoT & PLF")
conectar_iot = st.sidebar.checkbox("Habilitar Telemetría Inteligente en Vivo", value=True)

if conectar_iot:
    tipo_fuente_iot = st.sidebar.selectbox("Origen de Datos IoT", [
        "Simulación Automática de Hato (IoT Mock API)", 
        "Carga Manual de CSV / Telemetría", 
        "Webhooks / MQTT en Tiempo Real"
    ])
    
    if tipo_fuente_iot == "Simulación Automática de Hato (IoT Mock API)":
        st.sidebar.success("🟢 **Broker MQTT Conectado:** Recibiendo flujos de 80 aretes/bolos.")
        iot_ph_rumen = st.sidebar.slider("pH Ruminal Promedio (Bolos IoT)", 5.6, 6.8, 6.2, 0.05)
        iot_actividad_alerta = st.sidebar.slider("Índice Actividad Estral (Podómetros)", 80, 250, 110, 5)
        iot_mixer_error_pct = st.sidebar.slider("Error de Carga Carro Mezclador (%)", 0.0, 10.0, 1.5, 0.5)
        iot_status_str = "Activo (MQTT Mock API)"
        
        if iot_ph_rumen < 5.8:
            st.sidebar.error("⚠️ **ALERTA SARA (Bolos IoT):** ¡pH ruminal crítico (< 5.8)! Se recomienda incrementar peNDF.")
        if iot_actividad_alerta > 180:
            st.sidebar.info("🔥 **ALERTA DE CELO (Podómetros):** Alta actividad detectada en corral.")
            
    else:
        uploaded_iot = st.sidebar.file_uploader("Subir Archivo de Sensores (.csv)", type=["csv"])
        if uploaded_iot is not None:
            df_iot_user = pd.read_csv(uploaded_iot)
            st.sidebar.success(f"📂 Archivo IoT cargado: {len(df_iot_user)} registros leídos.")
            iot_ph_rumen = 6.2
            iot_mixer_error_pct = 1.0
            iot_status_str = "Archivo CSV Externo"
        else:
            iot_ph_rumen = 6.2
            iot_mixer_error_pct = 1.0
            iot_status_str = "Sin archivo conectado"
else:
    iot_ph_rumen = 6.2
    iot_mixer_error_pct = 0.0
    iot_status_str = "Desactivado"

# --- MÓDULO 1: CARACTERIZACIÓN FISIOLÓGICA Y AMBIENTAL ---
st.sidebar.markdown("---")
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

peso_def = 650 if "Holstein" in raza else (450 if "Jersey" in raza else 580)
peso_vivo = st.sidebar.slider("Peso Vivo (kg)", 350, 850, peso_def, 10)
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

# --- MÓDULO FINANCIERO Y ESTRUCTURA DE COSTOS DEL ESTABLO ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 💵 5. Estructura Financiera del Establo")

tam_corral = st.sidebar.number_input("Tamaño del Corral / Hato (Vacas)", min_value=1, max_value=2000, value=100, step=10)
precio_leche_base = st.sidebar.number_input("Precio Base Leche (MXN / L)", min_value=5.0, max_value=20.0, value=10.50, step=0.10)
bonif_solidos = st.sidebar.number_input("Bonificación Sólidos (MXN / L)", min_value=0.00, max_value=3.00, value=0.40, step=0.05)
precio_leche_total = precio_leche_base + bonif_solidos

st.sidebar.markdown("**Costos Operativos (MXN/vaca/día):**")
costo_mano_obra = st.sidebar.number_input("Mano de Obra y Salarios", min_value=0.0, max_value=100.0, value=18.0, step=1.0)
costo_salud_vet = st.sidebar.number_input("Salud, Semen y Veterinaria", min_value=0.0, max_value=100.0, value=8.5, step=0.5)
costo_energia_serv = st.sidebar.number_input("Energía, Diésel y Servicios", min_value=0.0, max_value=100.0, value=12.0, step=1.0)
costos_fijos_admin = st.sidebar.number_input("Costos Fijos y Depreciaciones", min_value=0.0, max_value=200.0, value=15.0, step=1.0)
ingresos_extras_subproductos = st.sidebar.number_input("Ingresos Extras (MXN/vaca/día)", min_value=0.0, max_value=50.0, value=4.0, step=0.5)

# --- MÓDULO 2: BASE DE DATOS Y MATRIZ NUTRICIONAL ---
st.subheader("🌾 2. Matriz Nutricional, Telemetría IoT y Disponibilidad de Insumos")
st.caption("Matriz de insumos integrada con monitoreo en tiempo real por bolos ruminales y básculas de carro mezclador.")

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

# --- MÓDULO 3: MOTOR DE OPTIMIZACIÓN LINEAL (PuLP) ---
st.markdown("---")
if st.button("🚀 Ejecutar Optimización con Telemetría PLF e IoT"):
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
            st.success("✅ ¡Dieta Bio-Optimizada con Sincronización IoT y Telemetría PLF!")
            
            resultados = []
            costo_alimento = 0
            nel_sum, mp_sum, rdp_sum, rup_sum, pendf_sum, starch_sum, ee_sum = 0, 0, 0, 0, 0, 0, 0
            pc_total_g = 0
            fdn_total_kg = 0
            
            for idx, row in editable_df.iterrows():
                ing = str(row["Ingrediente"])
                cantidad = variables[ing].varValue
                if cantidad and cantidad > 0.001:
                    costo_parcial = cantidad * float(row["Costo"])
                    costo_alimento += costo_parcial
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
                    
                    # Ajuste de carga en base al error del carro mezclador IoT
                    factor_mixer = 1.0 + (iot_mixer_error_pct / 100.0)
                    total_corral_iot = base_fresca_vaca * tam_corral * factor_mixer
                    
                    pct_dieta = (cantidad / cms_req) * 100
                    resultados.append({
                        "Ingrediente": ing,
                        "MS %": ms_pct,
                        "Inclusión (kg MS)": round(cantidad, 2),
                        "% en la Dieta (MS)": round(pct_dieta, 2),
                        "Base Fresca (kg/vaca)": round(base_fresca_vaca, 2),
                        "Total Corral (kg)": round(total_corral_iot, 1),
                        "Costo Parcial (MXN)": round(costo_parcial, 2)
                    })
                    
            df_res = pd.DataFrame(resultados)
            
            # --- CÁLCULOS FINANCIEROS Y P&L ---
            costo_opex_no_alimento = costo_mano_obra + costo_salud_vet + costo_energia_serv + costos_fijos_admin
            costo_total_diario_vaca = costo_alimento + costo_opex_no_alimento
            
            ingreso_leche_vaca = prod_leche * precio_leche_total
            ingreso_total_vaca = ingreso_leche_vaca + ingresos_extras_subproductos
            
            iofc = ingreso_leche_vaca - costo_alimento
            ebitda_vaca_dia = ingreso_total_vaca - costo_total_diario_vaca
            ebitda_corral_mes = ebitda_vaca_dia * tam_corral * 30.5
            
            costo_por_litro = costo_total_diario_vaca / prod_leche
            margen_neto_pct = (ebitda_vaca_dia / ingreso_total_vaca) * 100
            break_even_leche = (costo_total_diario_vaca - ingresos_extras_subproductos) / precio_leche_total
            
            # --- CÁLCULO ESTEQUIOMÉTRICO BMMCO ---
            ch4_vaca = (fdn_total_kg * 0.55 * 38.0) + ((starch_sum / 100.0 * cms_req) * 0.85 * 22.0)
            intensidad_ch4 = ch4_vaca / ecm
            n_consumido = pc_total_g / 6.25
            n_leche = (prod_leche * (pct_proteina / 100.0) * 1000.0) / 6.38
            n_excretado = max(30.0, n_consumido - n_leche - 25.0)
            
            col_tabla, col_resumen = st.columns([3.2, 1.8])
            
            with col_tabla:
                st.markdown("### 🧮 3. Ración Optimizada y Hoja TMR con Telemetría Carro Mezclador")
                st.dataframe(
                    df_res[["Ingrediente", "MS %", "Inclusión (kg MS)", "% en la Dieta (MS)", "Base Fresca (kg/vaca)", "Total Corral (kg)"]], 
                    use_container_width=True
                )
                
                pdf_buffer = generar_pdf_tmr_financiero(
                    df_res, costo_alimento, cms_req, ecm, raza, estado_productivo, 
                    tam_corral, precio_leche_total, iofc, ebitda_vaca_dia, 
                    costo_por_litro, break_even_leche, ch4_vaca, n_excretado, iot_status_str
                )
                
                st.download_button(
                    label="📄 Descargar Reporte Financiero y TMR IoT en PDF",
                    data=pdf_buffer,
                    file_name=f"Reporte_PLF_IoT_LecherIA_{raza}_{dim}DIM.pdf",
                    mime="application/pdf"
                )

            with col_resumen:
                st.markdown("### 📊 4. Telemetría IoT & Estado Financiero (P&L)")
                st.metric("pH Ruminal (Bolos IoT)", f"{iot_ph_rumen:.2f}", "Rango óptimo: > 6.0" if iot_ph_rumen>=6.0 else "⚠️ Riesgo SARA")
                st.metric("Costo Alimento / Vaca", f"${costo_alimento:.2f} MXN", f"{(costo_alimento/costo_total_diario_vaca)*100:.1f}% del total")
                st.metric("EBITDA Mensual del Corral", f"${ebitda_corral_mes:,.2f} MXN", f"Margen Neto: {margen_neto_pct:.1f}%")
                st.metric("Punto de Equilibrio (Leche)", f"{break_even_leche:.2f} L/vaca/día", f"Actual: {prod_leche:.1f} L")
                st.metric("Metano Entérico (CH₄)", f"{ch4_vaca:.1f} g CH₄/día", f"Intensidad: {intensidad_ch4:.1f} g/kg ECM")

            # --- MODELACIÓN PRODUCTIVA Y TRAYECTORIA ---
            st.markdown("---")
            st.subheader(f"📈 5. Proyección Productiva y Económica a 305 Días — {raza}")
            
            dias_lactancia = np.arange(1, 306)
            a_factor = prod_leche / ((dim ** 0.2) * np.exp(-0.003 * dim))
            produccion_predicha = a_factor * (dias_lactancia ** 0.2) * np.exp(-0.003 * dias_lactancia)
            
            cms_predicho = ((0.022 * peso_vivo) + (0.38 * ((0.327 * produccion_predicha) + (12.95 * (produccion_predicha * (pct_grasa / 100.0)))))) * factor_raza_cms * (1 - np.exp(-0.04 * dias_lactancia)) * factor_estres_cms
            
            ingreso_predicho = produccion_predicha * precio_leche_total
            costo_alimento_predicho = cms_predicho * (costo_alimento / cms_req)
            iofc_predicho = ingreso_predicho - costo_alimento_predicho
            
            df_curvas = pd.DataFrame({
                "Día de Lactancia": dias_lactancia,
                "Producción Leche Estimada (L/día)": np.round(produccion_predicha, 2),
                "Ingreso Leche ($ MXN)": np.round(ingreso_predicho, 2),
                "Costo Alimento ($ MXN)": np.round(costo_alimento_predicho, 2),
                "IOFC Margen ($ MXN)": np.round(iofc_predicho, 2)
            }).set_index("Día de Lactancia")
            
            tab1, tab2 = st.tabs(["📉 Curva de Lactancia & Ingresos", "💰 Trayectoria del Margen IOFC ($)"])
            
            with tab1:
                st.line_chart(df_curvas[["Producción Leche Estimada (L/día)", "Ingreso Leche ($ MXN)"]])
                st.info(f"📍 **Evaluación actual:** Día {dim} | Producción: **{prod_leche} L/día** | pH ruminal IoT: **{iot_ph_rumen:.2f}**")

            with tab2:
                st.line_chart(df_curvas[["IOFC Margen ($ MXN)", "Costo Alimento ($ MXN)"]])
                st.success(f"✅ **Margen Acumulado Estimado a 305 Días:** **${df_curvas['IOFC Margen ($ MXN)'].sum():,.2f} MXN** por vaca.")

        else:
            st.error("⚠️ **No se encontró solución factible.** Habilita más insumos o ajusta los límites en la matriz.")
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el modelo matemático: {e}")

# --- 6. PIE DE PÁGINA INSTITUCIONAL ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        <strong>Lecher-IA Pro</strong> &bull; Sistema de Precisión IoT, Nutrición y Finanzas Bovina<br>
        Diseñado y creado por el <strong>Dr. Alejandro Castañeda Correa</strong>.
    </div>
    """, 
    unsafe_allow_html=True
)
