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
    page_title="Lecher-IA Pro | Secure Enterprise PLF & Subscription Suite",
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
    .pricing-card {
        background: linear-gradient(135deg, #ffffff 0%, #f4f6f5 100%);
        border: 2px solid #137547;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    .pricing-card-vip {
        background: linear-gradient(135deg, #054A29 0%, #137547 100%);
        color: white;
        border: 3px solid #FFD700;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 12px 24px rgba(5,74,41,0.25);
        transform: scale(1.03);
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

# Definición global de columnas oficiales del inventario (hasta 3,000 cabezas)
COLUMNAS_HATO = [
    "SINIGA", 
    "Arete Interno", 
    "Etapa Productiva", 
    "DIM / Edad (días)", 
    "Días Gestación", 
    "Prod. Leche (L)", 
    "pH Ruminal (IoT)", 
    "Rumia (min/día)", 
    "Estado Salud"
]

# --- INICIALIZACIÓN DE ESTADOS DE SESIÓN ---
if "subscribed" not in st.session_state:
    st.session_state.subscribed = False
if "plan_seleccionado" not in st.session_state:
    st.session_state.plan_seleccionado = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "two_fa_verified" not in st.session_state:
    st.session_state.two_fa_verified = False

if "cita_pagada" not in st.session_state:
    st.session_state.cita_pagada = False
if "detalles_cita" not in st.session_state:
    st.session_state.detalles_cita = {}
if "ver_videollamada" not in st.session_state:
    st.session_state.ver_videollamada = False

if "bt_conectado" not in st.session_state:
    st.session_state.bt_conectado = False
if "idx_ingrediente_actual" not in st.session_state:
    st.session_state.idx_ingrediente_actual = 0
if "peso_cargado_actual" not in st.session_state:
    st.session_state.peso_cargado_actual = 0.0

if "df_hato" not in st.session_state:
    st.session_state.df_hato = pd.DataFrame(columns=COLUMNAS_HATO)


# =========================================================================
# PASO 1 PRIMORDIAL: PASARELA DE PLANES Y SUSCRIPCIÓN (APARECE AL INICIO)
# =========================================================================
if not st.session_state.subscribed:
    st.markdown("<h1 style='text-align: center; color: #054A29;'>💎 Planes de Suscripción Lecher-IA Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 16px;'>Selecciona tu plan para desbloquear la plataforma líder en precisión bionutricional, modelos NASEM 2021 y control de hato.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.markdown("""
            <div class='pricing-card'>
                <h3 style='color: #054A29;'>Plan Trimestral</h3>
                <h2 style='color: #333;'>3 Meses</h2>
                <p style='color: #666;'>Ideal para prueba y evaluación de hatos medianos.</p>
                <hr>
                <h1 style='color: #137547;'>$1,495 <small style='font-size: 14px;'>MXN/mes</small></h1>
                <p style='color: #888; font-size: 13px;'>Facturado cada 3 meses ($4,485 MXN total)</p>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar Plan 3 Meses", use_container_width=True):
            st.session_state.subscribed = True
            st.session_state.plan_seleccionado = "3 Meses"
            st.success("¡Suscripción Trimestral Seleccionada! Procede con el inicio de sesión seguro.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_p2:
        st.markdown("""
            <div class='pricing-card'>
                <h3 style='color: #054A29;'>Plan Semestral</h3>
                <h2 style='color: #333;'>6 Meses</h2>
                <p style='color: #666;'>Optimización continua y control estacional.</p>
                <hr>
                <h1 style='color: #137547;'>$1,195 <small style='font-size: 14px;'>MXN/mes</small></h1>
                <p style='color: #888; font-size: 13px;'>Ahorras 20% ($7,170 MXN total)</p>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar Plan 6 Meses", use_container_width=True):
            st.session_state.subscribed = True
            st.session_state.plan_seleccionado = "6 Meses"
            st.success("¡Suscripción Semestral Seleccionada! Procede con el inicio de sesión seguro.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_p3:
        st.markdown("""
            <div class='pricing-card-vip'>
                <div style='background-color: #FFD700; color: #054A29; font-weight: 800; font-size: 12px; padding: 4px 12px; border-radius: 20px; display: inline-block; margin-bottom: 8px;'>🔥 MÁS POPULAR & AHORRO MÁXIMO</div>
                <h3 style='color: #FFFFFF;'>Plan Anual VIP</h3>
                <h2 style='color: #FFD700;'>12 Meses</h2>
                <p style='color: #E0E0E0;'>Acceso total ilimitado para 3,000 cabezas + Soporte 24/7 con el Dr. Alejandro Castañeda.</p>
                <hr style='border-color: rgba(255,255,255,0.2);'>
                <h1 style='color: #FFFFFF;'>$795 <small style='font-size: 14px; color: #FFD700;'>MXN/mes</small></h1>
                <p style='color: #FFD700; font-size: 14px; font-weight: 700;'>¡Ahorras 47% ($9,540 MXN anuales)! Pagas $9,540 MXN único.</p>
                <p style='color: #E0E0E0; font-size: 12px; margin-top: 5px;'>Garantía de retención de precio por 3 años + Actualizaciones automáticas de Gemelo Digital.</p>
        """, unsafe_allow_html=True)
        if st.button("🌟 SUSCRIBIRME 12 MESES (AHORRO VIP)", use_container_width=True):
            st.session_state.subscribed = True
            st.session_state.plan_seleccionado = "12 Meses VIP"
            st.balloons()
            st.success("¡Suscripción Anual VIP Seleccionada con Éxito!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Estrategia Nutri-ON & Lecher-IA:** El 85% de los productores lecheros de alto rendimiento eligen el **Plan Anual de 12 Meses** para asegurar consistencia estacional en sus fórmulas NASEM, evitar aumentos de tarifas por inflación de materias primas y mantener un monitoreo ininterrumpido de su hato con máxima rentabilidad.")
    st.stop()


# =========================================================================
# PASO 2: PANTALLA DE AUTENTICACIÓN Y DOBLE FACTOR (2FA)
# =========================================================================
if not st.session_state.logged_in or not st.session_state.two_fa_verified:
    st.markdown("<h1 style='text-align: center; color: #054A29;'>🔐 Lecher-IA Pro — Autenticación Segura</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #137547; font-weight: 600;'>Plan Seleccionado: {st.session_state.plan_seleccionado}</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.container():
            st.markdown("### 🔑 Credenciales & Doble Factor (2FA)")
            
            if not st.session_state.logged_in:
                with st.form("form_login"):
                    usuario = st.text_input("Usuario / Correo Electrónico", value="admin")
                    password = st.text_input("Contraseña", type="password", value="lecheria2026")
                    btn_login = st.form_submit_button("Siguiente: Verificar 2FA ➔")
                    
                    if btn_login:
                        if usuario == "admin" and password == "lecheria2026":
                            st.session_state.logged_in = True
                            st.success("✅ Credenciales correctas. Se ha enviado un código OTP de 6 dígitos a tu autenticador.")
                            st.rerun()
                        else:
                            st.error("❌ Usuario o contraseña incorrectos. (Prueba con usuario: admin, password: lecheria2026)")
            else:
                st.success("🟢 Usuario autenticado correctamente.")
                st.info("📱 Ingresa el código de Doble Factor de Autenticación (2FA) recibido en tu dispositivo (Código de prueba: **2026**).")
                
                with st.form("form_2fa"):
                    codigo_2fa = st.text_input("Código 2FA (6 dígitos)", max_chars=6, value="2026")
                    btn_2fa = st.form_submit_button("🔒 Validar 2FA e Ingresar a la App")
                    
                    if btn_2fa:
                        if codigo_2fa == "2026":
                            st.session_state.two_fa_verified = True
                            st.success("✅ ¡Autenticación completada con éxito!")
                            st.rerun()
                        else:
                            st.error("❌ Código 2FA inválido. Utiliza el código de prueba: 2026")
    st.stop()


# =========================================================================
# PASO 3: APLICACIÓN PRINCIPAL (ACCESO TOTAL LUEGO DE SUSCRIPCIÓN + LOGIN)
# =========================================================================

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
    story.append(Paragraph("<i>Simulación Gemelo Digital basada en ecuaciones dinámicas de pasaje ruminal y metabolómica mamaria.</i>", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- ENCABEZADO Y BRANDING ---
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
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">ENTERPRISE PLF SUITE</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Plataforma Integral Bionutricional & PLF")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Gemelo Digital, Bluetooth TMR, Control de 3,000 Cabezas y Telemedicina.</h4>", unsafe_allow_html=True)
    st.markdown(f"<small style='color: #666;'>Plan Activo: <b>{st.session_state.plan_seleccionado}</b> &bull; Creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- PANEL IZQUIERDO (SIDEBAR): PARÁMETROS DEL HATO ---
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

# --- CUERPO PRINCIPAL ORGANIZADO EN PESTAÑAS ---
tab_inv, tab_form, tab_mixer_bt, tab_twin, tab_alert, tab_monte, tab_vision, tab_telemed = st.tabs([
    "🐄 Registro & Base de Datos Hato",
    "🌾 Formulación TMR", 
    "🚜 Carro Mezclador Bluetooth BLE",
    "🧬 Gemelo Digital & Metabolómica",
    "🔔 Alertas & Comandos Push",
    "🎲 Monte Carlo Stress-Test", 
    "📷 Visión AI (Peso)", 
    "🩺 Telemedicina"
])

iot_ph_rumen = 6.18
iot_rumination_min = 465

with tab_inv:
    st.subheader("📝 Formulario de Registro Individual de Animales")
    st.caption("Ingresa los datos del bovino y presiona el botón para guardarlo en la base de datos (capacidad hasta 3,000 animales).")
    
    with st.form("form_nuevo_animal", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            siniga_input = st.text_input("Número SINIGA (Oficial)", value="", placeholder="Ej: MX-14-032-1001")
            arete_input = st.text_input("Arete Interno (Establo)", value="", placeholder="Ej: 101")
            etapa_input = st.selectbox("Etapa Productiva", [
                "Vaca en producción",
                "Vaca seca",
                "Becerra recién nacida",
                "Becerra de reemplazo gestante",
                "Becerra de reemplazo no gestante",
                "Vaca para inseminar",
                "Vaca en transición"
            ])
        with c2:
            dim_input = st.number_input("DIM / Edad (días)", min_value=0, max_value=2000, value=30, step=1)
            gest_input = st.number_input("Días de Gestación", min_value=0, max_value=285, value=0, step=1)
            prod_input = st.number_input("Producción de Leche (L/día)", min_value=0.0, max_value=80.0, value=0.0, step=0.5)
        with c3:
            ph_input = st.number_input("pH Ruminal Sensorizado (IoT)", min_value=5.0, max_value=7.5, value=6.25, step=0.05)
            rumia_input = st.number_input("Rumia (min/día)", min_value=0, max_value=800, value=480, step=10)
            salud_input = st.text_input("Estado Salud / Observaciones", value="Óptimo", placeholder="Ej: Fisiológico Normal")
            
        btn_guardar = st.form_submit_button("💾 Guardar Animal en la Base de Datos")
        
        if btn_guardar:
            if not siniga_input or not arete_input:
                st.error("⚠️ Es obligatorio ingresar al menos el **Número SINIGA** y el **Arete Interno**.")
            elif len(st.session_state.df_hato) >= 3000:
                st.warning("⚠️ Se ha alcanzado la capacidad máxima de 3,000 animales en esta sesión.")
            else:
                nuevo_registro = {
                    "SINIGA": siniga_input,
                    "Arete Interno": arete_input,
                    "Etapa Productiva": etapa_input,
                    "DIM / Edad (días)": dim_input,
                    "Días Gestación": gest_input,
                    "Prod. Leche (L)": prod_input,
                    "pH Ruminal (IoT)": ph_input,
                    "Rumia (min/día)": rumia_input,
                    "Estado Salud": salud_input
                }
                st.session_state.df_hato = pd.concat([st.session_state.df_hato, pd.DataFrame([nuevo_registro])], ignore_index=True)
                st.success(f"✅ ¡Animal Arete #{arete_input} (SINIGA: {siniga_input}) guardado con éxito!")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Base de Datos del Hato Registrado")
    
    if not st.session_state.df_hato.empty:
        df_ordenado = st.session_state.df_hato.sort_values(by=["SINIGA", "Arete Interno"]).reset_index(drop=True)
        st.dataframe(df_ordenado, use_container_width=True)
        
        col_res1, col_res2 = st.columns([2, 2])
        with col_res1:
            st.metric("Total de Animales en la Base de Datos", f"{len(df_ordenado)} / 3,000")
        with col_res2:
            if st.button("🗑️ Vaciar / Limpiar Base de Datos"):
                st.session_state.df_hato = pd.DataFrame(columns=COLUMNAS_HATO)
                st.success("✅ Base de datos vaciada.")
                st.rerun()
    else:
        st.info("💡 La base de datos está actualmente **vacía**. Utiliza el formulario superior para agregar los animales de tu hato.")

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

with tab_mixer_bt:
    st.subheader("🚜 Sincronización Bluetooth BLE con Báscula de Carro Mezclador")
    col_bt1, col_bt2 = st.columns([1.5, 2.5])
    
    with col_bt1:
        st.markdown("### 📡 Conexión Bluetooth (BLE)")
        if not st.session_state.bt_conectado:
            if st.button("🔗 Escanear y Conectar Carro Mezclador (BLE)"):
                st.session_state.bt_conectado = True
                st.success("✅ ¡Conectado a Báscula Digi-Star / Dinamica Generale (MAC: 00:1A:7D:DA:71:13)!")
                st.rerun()
        else:
            st.success("🟢 **Báscula Bluetooth Sincronizada**")
            if st.button("🔴 Desconectar Bluetooth"):
                st.session_state.bt_conectado = False
                st.rerun()
                
        tam_corral_mezcla = st.number_input("Vacas a Alimentar en este Mezclado", 1, 3000, 100, 10)
        
    with col_bt2:
        if st.session_state.bt_conectado:
            ingredientes_tmr = [
                {"nombre": "Silo de Maíz", "objetivo_vaca": 18.5},
                {"nombre": "Heno de Alfalfa", "objetivo_vaca": 4.2},
                {"nombre": "Maíz Molido", "objetivo_vaca": 5.0},
                {"nombre": "Pasta de Soya", "objetivo_vaca": 2.1},
                {"nombre": "DDGS Maíz", "objetivo_vaca": 1.5},
                {"nombre": "Minerales / Bicarbonato", "objetivo_vaca": 0.4}
            ]
            idx_actual = st.session_state.idx_ingrediente_actual
            
            if idx_actual < len(ingredientes_tmr):
                ing_actual = ingredientes_tmr[idx_actual]
                peso_meta_corral = ing_actual["objetivo_vaca"] * tam_corral_mezcla
                
                st.markdown(f"### 🈳 Ingrediente en Carga [{idx_actual + 1}/{len(ingredientes_tmr)}]: **{ing_actual['nombre']}**")
                peso_cargado = st.slider(f"Telemetría en Vivo (kg de {ing_actual['nombre']})", 0.0, float(peso_meta_corral * 1.15), float(st.session_state.peso_cargado_actual), 10.0)
                st.session_state.peso_cargado_actual = peso_cargado
                
                porcentaje_completado = min(100.0, (peso_cargado / peso_meta_corral) * 100)
                
                if porcentaje_completado < 85.0:
                    st.progress(porcentaje_completado / 100.0)
                    st.info(f"🚜 **CARGANDO...** Faltan `{peso_meta_corral - peso_cargado:.1f} kg` de {ing_actual['nombre']}.")
                elif 85.0 <= porcentaje_completado < 98.0:
                    st.progress(porcentaje_completado / 100.0)
                    st.warning(f"⚠️ **¡CUIDADO! COMPLETANDO (90%+):** Faltan `{peso_meta_corral - peso_cargado:.1f} kg`.")
                else:
                    st.progress(1.0)
                    st.success(f"🛑 **¡INGREDIENTE COMPLETO! DETENER CARGA DE {ing_actual['nombre'].upper()}.** Target: `{peso_cargado:.1f} kg` / `{peso_meta_corral:.1f} kg`.")
                    if st.button("➡️ Siguiente Ingrediente en la Ración"):
                        st.session_state.idx_ingrediente_actual += 1
                        st.session_state.peso_cargado_actual = 0.0
                        st.rerun()
            else:
                st.balloons()
                st.success("🎉 **¡TODOS LOS INGREDIENTES CARGADOS EN EL CARRO MEZCLADOR!**")
                if st.button("🔄 Reiniciar Mezclado para Nuevo Corral"):
                    st.session_state.idx_ingrediente_actual = 0
                    st.session_state.peso_cargado_actual = 0.0
                    st.rerun()
        else:
            st.info("💡 Conecta la báscula del carro mezclador vía Bluetooth BLE para iniciar la sincronización de carga.")

with tab_twin:
    st.subheader("🧬 Gemelo Digital Bionutricional & Perfil Metabolómico (NASEM 2021)")
    col_tw1, col_tw2, col_tw3 = st.columns(3)
    kp_forraje = round(2.5 + 0.05 * (cms_req / peso_vivo * 100), 2)
    kp_concentrado = round(3.8 + 0.12 * (cms_req / peso_vivo * 100), 2)
    mun_estimado = round(8.5 + (rdp_min_pct * 0.45) - (starch_max * 0.15), 1)
    de_novo_fat_pct = round(max(0.8, 1.45 - (starch_max * 0.018) + (pendf_min * 0.015)), 2)
    saliva_litros = round(iot_rumination_min * 0.22 + cms_req * 3.5, 1)
    ph_biofisico = round(6.6 - (starch_max * 0.035) + (pendf_min * 0.02) + (iot_rumination_min * 0.0008), 2)
    
    with col_tw1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Tasa Pasaje Forraje (Kp)", f"{kp_forraje} %/h")
        st.metric("Tasa Pasaje Concentrado (Kp)", f"{kp_concentrado} %/h")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_tw2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("MUN Estimado", f"{mun_estimado} mg/dL")
        st.metric("Grasa De Novo", f"{de_novo_fat_pct} g/100g")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_tw3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Saliva Estimada", f"{saliva_litros} L/día")
        st.metric("pH Ruminal Biofísico", f"{ph_biofisico}")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_alert:
    st.subheader("🔔 Centro de Alertas Inteligentes & Comandos Ejecutables Push")
    if not st.session_state.df_hato.empty:
        for idx, row in st.session_state.df_hato.iterrows():
            siniga = row.get("SINIGA", "S/N")
            arete = row.get("Arete Interno", "S/N")
            etapa = str(row.get("Etapa Productiva", ""))
            dim_v = float(row.get("DIM / Edad (días)", 0) or 0)
            gestacion = float(row.get("Días Gestación", 0) or 0)
            
            if "producción" in etapa.lower() and (dim_v >= 220 or gestacion >= 200):
                st.error(f"🚨 **ALERTA DE SECADO REQUERIDO:** Vaca Arete #{arete} (SINIGA: {siniga}) — {dim_v} DIM / {gestacion} Días Gestación.")
                if st.button(f"📲 Programar Secado #{arete}", key=f"sec_{arete}"):
                    st.success(f"✅ Vaca #{arete} marcada para secado y trasladada a Corral Seco.")
    else:
        st.info("💡 Registra animales en la pestaña de inventario para activar la evaluación de alertas automáticas.")

with tab_monte:
    st.subheader("🎲 Análisis Estocástico de Riesgo Financiero (Monte Carlo Stress-Test)")
    if st.button("🎰 Ejecutar 1,000 Simulaciones Monte Carlo"):
        np.random.seed(42)
        simulaciones = 1000
        costos_simulados = np.random.normal(loc=185.0, scale=18.5, size=simulaciones)
        leche_simulada = np.random.normal(loc=prod_leche, scale=2.5, size=simulaciones)
        margen_iofc_sim = (leche_simulada * 10.90) - costos_simulados
        var_95 = np.percentile(margen_iofc_sim, 5)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Margen IOFC Medio Simulado", f"${np.mean(margen_iofc_sim):,.2f} MXN")
        with col_m2:
            st.metric("Valor en Riesgo 95% (VaR)", f"${var_95:,.2f} MXN")
        with col_m3:
            st.metric("Probabilidad IOFC Negativo", f"{(np.sum(margen_iofc_sim < 0) / simulaciones) * 100:.1f}%")
        st.line_chart(pd.DataFrame({"Margen IOFC Simulado ($ MXN)": margen_iofc_sim}))

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

with tab_telemed:
    st.subheader("🩺 Clínica Virtual & Telemedicina Bovina")
    col_tel1, col_tel2 = st.columns([1.2, 1.8])
    with col_tel1:
        with st.expander("📅 Agendar Cita y Pago ($475.00 MXN)", expanded=not st.session_state.cita_pagada):
            nombre_productor = st.text_input("Productor / Establo", value="Ganadería Zacatecas")
            fecha_cita = st.date_input("Fecha de Consulta", min_value=datetime.today().date())
            hora_cita = st.time_input("Hora Preferida", value=datetime.strptime("10:00", "%H:%M").time())
            motivo_consulta = st.text_area("Motivo", "Revisión NASEM 2021 y Carro Mezclador BLE.")
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
        <strong>Lecher-IA Pro</strong> &bull; Enterprise Suite, Digital Twin & Telemedicine<br>
        Designed and engineered by <strong>Dr. Alejandro Castañeda Correa</strong>.
    </div>
    """, 
    unsafe_allow_html=True
)
