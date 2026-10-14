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

# --- 2. ENCABEZADO, LOGOTIPO Y BRANDING RENOVADO ---
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
    st.title("Lecher-IA Pro")
    st.markdown("<h4 style='color: #2A9D8F; margin-top: -15px; font-weight: 600;'>Precisión nutricional que rinde en la tanqueta.</h4>", unsafe_allow_html=True)
    st.markdown("<small style='color: #666;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

st.markdown("---")

# --- 3. BARRA LATERAL: MECANISMO DE CÁLCULO DINÁMICO DEL ANIMAL ---
st.sidebar.markdown("### 🧬 Parámetros Fisiológicos")
paridad = st.sidebar.selectbox("Paridad", ["Multípara (2+ lactancias)", "Primípara (1er parto)"])
dim = st.sidebar.slider("Días en Leche (DIM)", 5, 305, 90, 5)
peso_vivo = st.sidebar.slider("Peso Vivo (kg)", 450, 800, 650, 10)
bcs = st.sidebar.slider("Condición Corporal (BCS 1-5)", 2.25, 4.0, 3.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🥛 Metas de Producción y Leche")
prod_leche = st.sidebar.slider("Leche Total Actual (kg/día)", 15.0, 60.0, 35.0, 0.5)
pct_grasa = st.sidebar.slider("Grasa en Leche (%)", 2.8, 5.0, 3.7, 0.1)
pct_proteina = st.sidebar.slider("Proteína Verd. en Leche (%)", 2.6, 4.0, 3.2, 0.1)

# Cálculo de Leche Corregida por Energía (ECM / FCM NASEM)
fcm_35 = (0.4324 * prod_leche) + (16.216 * (prod_leche * (pct_grasa / 100.0)))
ecm = (0.327 * prod_leche) + (12.95 * (prod_leche * (pct_grasa / 100.0))) + (7.2 * (prod_leche * (pct_proteina / 100.0)))

# Estimación automática de CMS según NASEM (2021)
cms_estimado_nasem = round((0.022 * peso_vivo) + (0.38 * fcm_35), 2)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Ajuste Manual de Requerimientos")
cms_req = st.sidebar.number_input("CMS Objetivo (kg MS/día)", min_value=12.0, max_value=35.0, value=cms_estimado_nasem, step=0.5)
nel_req = st.sidebar.slider("Energía Neta Lactancia (NEL Mcal/kg MS)", 1.45, 1.85, 1.68, 0.01)
mp_req_g = st.sidebar.number_input("Proteína Metabolizable (PM g/día)", min_value=1200, max_value=3500, value=int(ecm * 72 + 500), step=50)

# Restricciones ruminales avanzadas
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Restricciones Ruminales y Salud")
pendf_min = st.sidebar.slider("peNDF Mínima (% en MS)", 16.0, 26.0, 20.0, 0.5)
starch_max = st.sidebar.slider("Almidón Máximo (% MS - Prev. SARA)", 18.0, 32.0, 25.0, 0.5)
ee_max = st.sidebar.slider("Grasa Total / EE Máxima (% MS)", 3.5, 7.0, 5.5, 0.5)
ca_min = st.sidebar.slider("Calcio Mínimo (Ca % MS)", 0.50, 1.00, 0.70, 0.05)
p_min = st.sidebar.slider("Fósforo Mínimo (P % MS)", 0.30, 0.55, 0.38, 0.02)

st.markdown(f"""
> **Resumen del Perfil Fisiológico:**  
> **ECM (Leche Corregida):** `{ecm:.2f} kg/día` &bull; **CMS Estimado NASEM:** `{cms_estimado_nasem} kg MS/día` &bull; **Densidad Energética:** `{nel_req} Mcal/kg MS`
""")

# --- 4. BASE DE DATOS EXTENDIDA DE INGREDIENTES ---
datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS Maíz", "Melasa Caña", "Salvado Trigo", "Grasa Sobrepaso", "Carbonato Calcio"],
    "Costo": [2.10, 4.20, 5.50, 4.90, 9.90, 7.20, 3.60, 4.60, 25.00, 1.80],
    "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68, 5.20, 0.00],        # Mcal/kg MS
    "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0, 0.0, 0.0],       # g/kg MS
    "RDP": [5.5, 13.0, 3.5, 4.0, 28.0, 10.0, 4.0, 12.0, 0.0, 0.0],              # % MS
    "RUP": [3.0, 5.0, 6.0, 6.5, 17.0, 18.0, 0.5, 4.0, 0.0, 0.0],               # % MS
    "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0, 0.0, 0.0],            # % MS
    "peNDF": [32.0, 36.0, 2.0, 3.0, 2.0, 8.0, 0.0, 10.0, 0.0, 0.0],              # % MS
    "Almidon": [28.0, 2.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0, 0.0, 0.0],          # % MS
    "EE": [3.2, 2.1, 3.8, 3.1, 1.5, 9.5, 0.1, 4.0, 99.0, 0.0],                 # % MS
    "Ca": [0.25, 1.40, 0.03, 0.04, 0.35, 0.15, 0.90, 0.12, 0.00, 38.0],          # % MS
    "P": [0.20, 0.25, 0.28, 0.29, 0.65, 0.75, 0.10, 0.95, 0.00, 0.02],           # % MS
    "Min_Inclusion": [4.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [18.0, 12.0, 10.0, 8.0, 6.0, 4.0, 2.0, 4.0, 0.8, 0.3]
}

df_ingredientes = pd.DataFrame(datos_base)

st.subheader("📋 Matriz Nutricional Completa de Ingredientes")
st.caption("Puedes modificar precios, aportes nutricionales y límites de inclusión directamente en la tabla.")
editable_df = st.data_editor(df_ingredientes, num_rows="fixed")

# --- 5. MOTOR DE OPTIMIZACIÓN LINEAL (PuLP) ---
if st.button("🚀 Ejecutar Optimización Avanzada de Dietas"):
    try:
        prob = pulp.LpProblem("LecherIA_Precision_Diet", pulp.LpMinimize)
        
        variables = {}
        for idx, row in editable_df.iterrows():
            ing = str(row["Ingrediente"])
            variables[ing] = pulp.LpVariable(
                f"x_{ing.replace(' ', '_')}", 
                lowBound=float(row["Min_Inclusion"]), 
                upBound=float(row["Max_Inclusion"])
            )
            
        # Función Objetivo: Minimizar Costo Total Diario
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["Costo"]) for idx, row in editable_df.iterrows()])
        
        # RESTRICCIONES NUTRICIONALES Y METABÓLICAS
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req), "CMS_Total"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req), "Min_NEL"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g), "Min_MP"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["peNDF"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(pendf_min) / 100.0) * float(cms_req), "Min_peNDF"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req), "Max_Starch"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["EE"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(ee_max) / 100.0) * float(cms_req), "Max_EE"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["Ca"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(ca_min) / 100.0) * float(cms_req), "Min_Ca"
        prob += pulp.lpSum([variables[str(row["Ingrediente"])] * (float(row["P"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(p_min) / 100.0) * float(cms_req), "Min_P"
        
        # Resolver el modelo
        prob.solve()
        
        # Estado de la solución
        if prob.status == 1:
            st.success("✅ ¡Dieta optimizada exitosamente bajo criterios científicos de alta precisión!")
            
            resultados = []
            costo_total = 0
            nel_sum, mp_sum, pendf_sum, starch_sum, ee_sum, ca_sum, p_sum = 0, 0, 0, 0, 0, 0, 0
            
            for idx, row in editable_df.iterrows():
                ing = str(row["Ingrediente"])
                cantidad = variables[ing].varValue
                if cantidad and cantidad > 0.001:
                    costo_parcial = cantidad * float(row["Costo"])
                    costo_total += costo_parcial
                    nel_sum += cantidad * float(row["NEL"])
                    mp_sum += cantidad * float(row["MP"])
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
                st.markdown("### 🥗 Ración Optimizada (Base Seca)")
                st.dataframe(df_res, use_container_width=True)
                st.metric(label="💰 Costo Total Diario por Vaca", value=f"${costo_total:.2f} MXN")

            with col_resumen:
                st.markdown("### 📊 Perfil Nutricional Alcanzado")
                st.metric("NEL Consumida", f"{nel_sum/cms_req:.2f} Mcal/kg", f"Meta: {nel_req}")
                st.metric("Proteína Metabolizable", f"{mp_sum:.0f} g/día", f"Meta: {mp_req_g} g")
                st.metric("Fibra Efectiva (peNDF)", f"{(pendf_sum/cms_req)*100:.1f}%", f"Mín: {pendf_min}%")
                st.metric("Almidón Ruminal", f"{(starch_sum/cms_req)*100:.1f}%", f"Máx: {starch_max}%")
                st.metric("Grasa Total (EE)", f"{(ee_sum/cms_req)*100:.1f}%", f"Máx: {ee_max}%")
                st.metric("Calcio (Ca) / Fósforo (P)", f"{(ca_sum/cms_req)*100:.2f}% / {(p_sum/cms_req)*100:.2f}%", f"Metas: {ca_min}% / {p_min}%")

            # --- 6. MODELACIÓN Y GRÁFICAS DE PREDICCIÓN PRODUCTIVA ---
            st.markdown("---")
            st.subheader("📈 Predicción del Comportamiento Productivo y Balance Energético (Modelo de Wood)")
            
            # Generar curva de 305 días de lactancia
            dias_lactancia = np.arange(1, 306)
            
            # Parámetros del modelo de Wood
            a_factor = prod_leche / ((dim ** 0.2) * np.exp(-0.003 * dim))
            produccion_predicha = a_factor * (dias_lactancia ** 0.2) * np.exp(-0.003 * dias_lactancia)
            
            # Estimación del CMS a lo largo de la lactancia
            cms_predicho = (0.022 * peso_vivo) + (0.38 * ((0.327 * produccion_predicha) + (12.95 * (produccion_predicha * (pct_grasa / 100.0)))))
            factor_depresion = 1 - np.exp(-0.04 * dias_lactancia)
            cms_predicho = cms_predicho * factor_depresion
            
            # Aporte y Requerimiento de Energía
            nel_aportada = cms_predicho * (nel_sum / cms_req)
            nel_mantenimiento = 0.08 * (peso_vivo ** 0.75)
            nel_requerida_total = nel_mantenimiento + (0.70 * produccion_predicha)
            
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
                    st.warning("⚠️ **Atención (Lactancia Temprana):** La vaca se encuentra en fase de Balance Energético Negativo (BEN). Movilizará reservas corporales de grasa para sostener el pico de lactancia.")
                else:
                    st.success("✅ **Fase de Balance Energético Positivo:** El consumo de materia seca satisface los requerimientos para producción y recuperación de condición corporal.")

        else:
            st.warning("⚠️ No se encontró solución factible. Las restricciones nutricionales son aplicadas estrictamente. Intenta ampliar los rangos de inclusión de los ingredientes o ajustar los límites de la barra lateral.")
            
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
