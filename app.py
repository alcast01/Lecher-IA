import streamlit as st
import pandas as pd
import numpy as np
import pulp

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Lecher-IA Pro | Precisión Nutricional",
    page_icon="🥛",
    layout="wide"
)

# --- 2. ENCABEZADO Y BRANDING DE VANGUARDIA ---
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
            <div style="font-size: 9px; font-weight: 500; opacity: 0.85; letter-spacing: 0.8px;">NUTRICIÓN DE PRECISIÓN</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("Lecher-IA Pro — Modelo Nutricional Avanzado (NASEM 2021)")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Precisión nutricional que rinde en la tanqueta.</h4>", unsafe_allow_html=True)
    st.markdown("<small style='color: #666;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- 3. BARRA LATERAL: PARÁMETROS FISIOLÓGICOS, RAZA Y CLIMA (NASEM) ---
st.sidebar.markdown("### 🧬 Genética y Fisiología del Animal")
raza = st.sidebar.selectbox("Raza Bovina", ["Holstein-Friesian", "Jersey"])
paridad = st.sidebar.selectbox("Número de Lactancia (Paridad)", ["Multípara (2+ lactancias)", "Primípara (1er parto)"])
estado_productivo = st.sidebar.selectbox("Estado Fisiológico / Productivo", [
    "Lactación Temprana (1-60 DIM)", 
    "Lactación Media (61-200 DIM)", 
    "Lactación Tardía (201-305 DIM)"
])

# Rango DIM automático según el estado seleccionado
if "Temprana" in estado_productivo:
    dim = st.sidebar.slider("Días en Leche (DIM)", 5, 60, 30, 1)
elif "Media" in estado_productivo:
    dim = st.sidebar.slider("Días en Leche (DIM)", 61, 200, 120, 5)
else:
    dim = st.sidebar.slider("Días en Leche (DIM)", 201, 305, 250, 5)

# Peso y Condición Corporal con valores predeterminados según raza
peso_def = 650 if raza == "Holstein-Friesian" else 450
peso_vivo = st.sidebar.slider("Peso Vivo (kg)", 350, 850, peso_def, 10)
bcs = st.sidebar.slider("Condición Corporal (BCS 1-5)", 2.25, 4.0, 3.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌡️ Clima y Entorno")
temp_amb = st.sidebar.slider("Temperatura Ambiental (°C)", -10, 42, 22, 1)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🥛 Metas de Producción y Leche")
prod_def = 35.0 if raza == "Holstein-Friesian" else 24.0
prod_leche = st.sidebar.slider("Leche Total Actual (kg/día)", 10.0, 60.0, prod_def, 0.5)

# Ajuste porcentual de grasa y proteína según raza estándar NASEM
grasa_def = 3.7 if raza == "Holstein-Friesian" else 4.8
proteina_def = 3.2 if raza == "Holstein-Friesian" else 3.8

pct_grasa = st.sidebar.slider("Grasa en Leche (%)", 2.8, 6.0, grasa_def, 0.1)
pct_proteina = st.sidebar.slider("Proteína Verd. en Leche (%)", 2.6, 4.5, proteina_def, 0.1)

# --- AJUSTES MATEMÁTICOS NASEM POR RAZA Y CLIMA ---
# Coeficiente de mantenimiento energético (Mcal NEL / kg BW^0.75): Jersey requiere ~15% más por unidad metabólica
coef_mantenimiento = 0.080 if raza == "Holstein-Friesian" else 0.092
nel_mantenimiento = coef_mantenimiento * (peso_vivo ** 0.75)

# Factor de estrés térmico por temperatura ambiental (°C)
# Si T > 25°C, hay depresión de consumo (CMS) y aumento de costo energético por termorregulación
factor_estres_cms = 1.0
factor_estres_energetico = 1.0
if temp_amb > 25:
    grados_estres = temp_amb - 25
    factor_estres_cms = max(0.80, 1.0 - (grados_estres * 0.015)) # Depresión de hasta 20% en calor extremo
    factor_estres_energetico = 1.0 + (grados_estres * 0.007)      # Incremento de requerimiento por frecuencia respiratoria

# Cálculos Metabólicos NASEM (2021)
fcm_35 = (0.4324 * prod_leche) + (16.216 * (prod_leche * (pct_grasa / 100.0)))
ecm = (0.327 * prod_leche) + (12.95 * (prod_leche * (pct_grasa / 100.0))) + (7.2 * (prod_leche * (pct_proteina / 100.0)))

# Estimación Dinámica del Consumo de Materia Seca (CMS) ajustada por Raza y Estrés Térmico
factor_raza_cms = 1.0 if raza == "Holstein-Friesian" else 0.82 # Jersey consume menor volumen relativo pero mayor densidad
cms_base_nasem = ((0.022 * peso_vivo) + (0.38 * fcm_35)) * factor_raza_cms
factor_dim_curva = 1 - np.exp(-0.04 * dim) if dim < 50 else 1.0
cms_estimado_nasem = round(cms_base_nasem * factor_dim_curva * factor_estres_cms, 2)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Requerimientos Nutricionales Estimados")
cms_req = st.sidebar.number_input("CMS Objetivo (kg MS/día)", min_value=8.0, max_value=35.0, value=cms_estimado_nasem, step=0.5)

# Densidad energética ajustada por estrés térmico
nel_req_base = 1.45 + (ecm * 0.012)
nel_req = st.sidebar.slider("Energía Neta Lactancia (NEL Mcal/kg MS)", 1.45, 1.95, round(nel_req_base * factor_estres_energetico, 2), 0.01)

mp_req_g = st.sidebar.number_input("Proteína Metabolizable (PM g/día)", min_value=1000, max_value=3500, value=int(ecm * 75 + (nel_mantenimiento * 100)), step=50)

rdp_min_pct = st.sidebar.slider("Proteína Degradable Rumen (RDP % en MS)", 8.0, 13.0, 10.0, 0.2)
rup_min_pct = st.sidebar.slider("Proteína Sobrepasante (RUP % en MS)", 4.0, 9.0, 6.0, 0.2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Restricciones Ruminales y Minerales")
pendf_min = st.sidebar.slider("peNDF Mínima (% en MS)", 16.0, 26.0, 20.0, 0.5)
starch_max = st.sidebar.slider("Almidón Máximo (% MS - Prev. SARA)", 18.0, 32.0, 24.0, 0.5)
ee_max = st.sidebar.slider("Grasa Total / EE Máxima (% MS)", 3.5, 7.0, 5.5, 0.5)
ca_min = st.sidebar.slider("Calcio Mínimo (Ca % MS)", 0.50, 1.00, 0.70, 0.05)
p_min = st.sidebar.slider("Fósforo Mínimo (P % MS)", 0.30, 0.55, 0.38, 0.02)

# Alerta de Estrés Térmico en Interfaz
if temp_amb > 28:
    st.sidebar.error(f"⚠️ **Alerta de Estrés Térmico ({temp_amb}°C):** Se aplicó corrección por depresión de consumo y mayor requerimiento energético.")

st.markdown(f"""
> **Resumen del Perfil Fisiológico ({raza} | {estado_productivo}):**  
> **ECM (Leche Corregida):** `{ecm:.2f} kg/día` &bull; **CMS Estimado NASEM:** `{cms_estimado_nasem} kg MS/día` &bull; **NEL Objetivo:** `{nel_req} Mcal/kg MS`
""")

# --- 4. BASE DE DATOS EXTENDIDA CON COLUMNA "Disponible" ---
datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS Maíz", "Melasa Caña", "Salvado Trigo", "Grasa Sobrepaso", "Carbonato Calcio"],
    "Disponible": [True, True, True, True, True, True, True, True, True, True],
    "Costo": [2.10, 4.20, 5.50, 4.90, 9.90, 7.20, 3.60, 4.60, 25.00, 1.80],
    "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68, 5.20, 0.00],        # Mcal/kg MS
    "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0, 0.0, 0.0],       # g/kg MS
    "RDP": [5.5, 13.0, 3.5, 4.0, 28.0, 10.0, 4.0, 12.0, 0.0, 0.0],              # % en MS
    "RUP": [3.0, 5.0, 6.0, 6.5, 17.0, 18.0, 0.5, 4.0, 0.0, 0.0],               # % en MS
    "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0, 0.0, 0.0],            # % en MS
    "peNDF": [32.0, 36.0, 2.0, 3.0, 2.0, 8.0, 0.0, 10.0, 0.0, 0.0],              # % en MS
    "Almidon": [28.0, 2.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0, 0.0, 0.0],          # % en MS
    "EE": [3.2, 2.1, 3.8, 3.1, 1.5, 9.5, 0.1, 4.0, 99.0, 0.0],                 # % en MS
    "Ca": [0.25, 1.40, 0.03, 0.04, 0.35, 0.15, 0.90, 0.12, 0.00, 38.0],          # % en MS
    "P": [0.20, 0.25, 0.28, 0.29, 0.65, 0.75, 0.10, 0.95, 0.00, 0.02],           # % en MS
    "Min_Inclusion": [4.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [18.0, 12.0, 10.0, 8.0, 6.0, 4.0, 2.0, 4.0, 0.8, 0.3]
}

df_ingredientes = pd.DataFrame(datos_base)

st.subheader("📋 Matriz Nutricional y Disponibilidad de Ingredientes")
st.caption("Marca o desmarca la columna **'Disponible'** según el inventario actual de tu establo. Modifica precios o límites cuando lo requieras.")
editable_df = st.data_editor(df_ingredientes, num_rows="fixed")

# --- 5. MOTOR DE OPTIMIZACIÓN LINEAL (PuLP) ---
if st.button("🚀 Ejecutar Optimización Avanzada de Dietas"):
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
            
        # Función Objetivo: Minimizar Costo Total Diario
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["Costo"]) for idx, row in editable_df.iterrows()])
        
        # RESTRICCIONES NUTRICIONALES Y METABÓLICAS RIGUROSAS
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req), "CMS_Total"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req), "Min_NEL"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g), "Min_MP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RDP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rdp_min_pct) / 100.0) * float(cms_req), "Min_RDP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["RUP"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(rup_min_pct) / 100.0) * float(cms_req), "Min_RUP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["peNDF"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(pendf_min) / 100.0) * float(cms_req), "Min_peNDF"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req), "Max_Starch"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["EE"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(ee_max) / 100.0) * float(cms_req), "Max_EE"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Ca"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(ca_min) / 100.0) * float(cms_req), "Min_Ca"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["P"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(p_min) / 100.0) * float(cms_req), "Min_P"
        
        # Resolver el modelo
        prob.solve()
        
        # Estado de la solución
        if prob.status == 1:
            st.success("✅ ¡Dieta optimizada exitosamente considerando los parámetros raciales, ambientales y de inventario!")
            
            resultados = []
            costo_total = 0
            nel_sum, mp_sum, rdp_sum, rup_sum, pendf_sum, starch_sum, ee_sum, ca_sum, p_sum = 0, 0, 0, 0, 0, 0, 0, 0, 0
            
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
                    ca_sum += cantidad * float(row["Ca"])
                    p_sum += cantidad * float(row["P"])
                    
                    pct_dieta = (cantidad / cms_req) * 100
                    resultados.append({
                        "Ingrediente": ing,
                        "Inclusión (kg MS)": round(cantidad, 2),
                        "% en la Dieta (MS)": round(pct_dieta, 2),
                        "Costo Parcial (MXN)": round(costo_parcial, 2)
                    })
                    
            df_res = pd.DataFrame(resultados)
            
            col_tabla, col_resumen = st.columns([3, 2])
            
            with col_tabla:
                st.markdown("### 🥗 Ración Optimizada al Mínimo Costo")
                st.dataframe(df_res, use_container_width=True)
                st.metric(label="💰 Costo Mínimo Total Diario por Vaca", value=f"${costo_total:.2f} MXN")

            with col_resumen:
                st.markdown("### 📊 Perfil Nutricional Alcanzado")
                st.metric("NEL Consumida", f"{nel_sum/cms_req:.2f} Mcal/kg", f"Meta: {nel_req}")
                st.metric("Proteína Metabolizable", f"{mp_sum:.0f} g/día", f"Meta: {mp_req_g} g")
                st.metric("RDP / RUP (% MS)", f"{(rdp_sum/cms_req)*100:.1f}% / {(rup_sum/cms_req)*100:.1f}%", f"Metas: {rdp_min_pct}% / {rup_min_pct}%")
                st.metric("Fibra Efectiva (peNDF)", f"{(pendf_sum/cms_req)*100:.1f}%", f"Mín: {pendf_min}%")
                st.metric("Almidón Ruminal", f"{(starch_sum/cms_req)*100:.1f}%", f"Máx: {starch_max}%")
                st.metric("Grasa Total (EE)", f"{(ee_sum/cms_req)*100:.1f}%", f"Máx: {ee_max}%")
                st.metric("Calcio (Ca) / Fósforo (P)", f"{(ca_sum/cms_req)*100:.2f}% / {(p_sum/cms_req)*100:.2f}%", f"Metas: {ca_min}% / {p_min}%")

            # --- 6. MODELACIÓN Y GRÁFICAS DE PREDICCIÓN PRODUCTIVA ---
            st.markdown("---")
            st.subheader(f"📈 Predicción del Comportamiento Productivo — {raza} ({estado_productivo})")
            
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
                st.markdown("**Trayectoria esperada de producción láctea y consumo de materia seca a 305 días:**")
                st.line_chart(df_curvas[["Producción Leche Estimada (kg/día)", "Consumo MS Estimado (kg/día)"]])
                st.info(f"📍 **Punto de evaluación actual:** Día {dim} de lactancia | Producción: **{prod_leche} kg/día** | Consumo estimado: **{cms_predicho[dim-1]:.1f} kg MS/día**")

            with tab2:
                st.markdown("**Comparación del Aporte Energético vs. Requerimiento Total:**")
                st.line_chart(df_curvas[["Energía Aportada (Mcal NEL)", "Energía Requerida Total (Mcal NEL)"]])
                
                if dim < 60:
                    st.warning("⚠️ **Atención (Lactancia Temprana / Transición):** La vaca se encuentra en fase de Balance Energético Negativo (BEN). Movilizará reservas corporales de grasa para sostener el pico de lactancia.")
                else:
                    st.success("✅ **Fase de Balance Energético Positivo:** El consumo de materia seca satisface los requerimientos para producción y recuperación de condición corporal.")

        else:
            st.warning("⚠️ No se encontró solución factible. Es posible que hayas desactivado ingredientes clave y las restricciones nutricionales no se puedan cumplir. Vuelve a habilitar ingredientes necesarios en la tabla o ajusta los límites.")
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el modelo matemático: {e}")

# --- 7. PIE DE PÁGINA E INSTITUCIONAL ---
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
