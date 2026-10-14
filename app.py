import streamlit as st
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="LactiDieta Pro | NASEM & JDS Standard",
    page_icon="🐄",
    layout="wide"
)

# --- ENCABEZADO Y LOGOTIPO CIENTÍFICO ---
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    st.markdown(
        """
        <div style="background-color: #1B5E20; padding: 15px; border-radius: 12px; text-align: center; color: white;">
            <span style="font-size: 40px;">🔬🐄</span><br>
            <strong style="font-size: 13px;">JDS & NASEM</strong><br>
            <span style="font-size: 9px; opacity: 0.9;">BIO-NUTRICIÓN LECHERA</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("LactiDieta Pro — Modelo Lineal Avanzado (JDS / NASEM)")
    st.markdown("**Sistema de optimización con restricciones metabólicas, proteicas (RDP/RUP), fibra efectiva y límites de almidón.**")

st.markdown("---")

# --- BARRA LATERAL: PARÁMETROS FISIOLÓGICOS Y NUTRICIONALES ---
st.sidebar.markdown("### 🧬 Parámetros del Animal (JDS)")
paridad = st.sidebar.selectbox("Paridad", ["Multípara (2+ lactancias)", "Primípara (1er parto)"])
dim = st.sidebar.slider("Días en Leche (DIM)", 10, 305, 120)
peso_vivo = st.sidebar.slider("Peso Vivo (kg)", 500, 750, 650, 10)
produccion_leche = st.sidebar.slider("Producción Leche 3.5% Grasa (kg/día)", 20, 55, 35, 1)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Requerimientos Metabólicos")
cms_req = st.sidebar.slider("Consumo Materia Seca Objetivo (CMS kg)", 18.0, 28.0, 22.5, 0.5)
nel_req = st.sidebar.slider("Energía Neta Lactancia (NEL Mcal/kg MS)", 1.50, 1.85, 1.70, 0.01)
mp_req_g = st.sidebar.slider("Proteína Metabolizable (PM en gramos)", 1800, 3200, 2400, 50)
forage_fdn_min = st.sidebar.slider("FDN de Forraje Mínima (% en MS)", 18.0, 28.0, 21.0, 0.5)
starch_max = st.sidebar.slider("Almidón Máximo (% en MS - Prev. SARA)", 20.0, 32.0, 26.0, 0.5)
ee_max = st.sidebar.slider("Extracto Etéreo / Grasa Máxima (% MS)", 4.0, 7.0, 6.0, 0.5)

# --- BASE DE DATOS CIENTÍFICA DE INGREDIENTES ---
datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS de Maíz", "Melasa de Caña", "Salvado de Trigo"],
    "Costo": [2.00, 4.00, 5.40, 4.80, 9.80, 7.00, 3.50, 4.50],
    "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68],       # Mcal/kg MS
    "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0],   # g/kg MS (Proteína Metabolizable)
    "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0],         # % FDN
    "Forage_FDN": [42.0, 38.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],     # % Aporta como FDN de Forraje
    "Almidon": [28.0, 3.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0],        # % Almidón
    "EE": [3.0, 2.0, 3.8, 3.1, 1.8, 9.0, 0.2, 4.2],               # % Extracto Etéreo (Grasa)
    "Min_Inclusion": [5.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [16.0, 10.0, 10.0, 8.0, 5.0, 4.0, 2.0, 5.0]
}

df_ingredientes = pd.DataFrame(datos_base)

st.subheader("📋 Matriz de Ingredientes y Perfil Nutricional (JDS / NASEM)")
editable_df = st.data_editor(df_ingredientes, num_rows="dynamic")

if st.button("🚀 Ejecutar Optimización Avanzada"):
    prob = LpProblem("Balance_Dietas_Avanzado", LpMinimize)
    
    variables = {}
    for idx, row in editable_df.iterrows():
        ing = row["Ingrediente"]
        variables[ing] = LpVariable(f"x_{ing.replace(' ', '_')}", lowBound=row["Min_Inclusion"], upBound=row["Max_Inclusion"])
        
    # Función Objetivo: Minimizar Costo Total
    prob += lpSum([variables[row["Ingrediente"]] * row["Costo"] for idx, row in editable_df.iterrows()])
    
    # 1. Restricción de Consumo de Materia Seca (CMS)
    prob += lpSum([variables[row["Ingrediente"]] for idx, row in editable_df.iterrows()]) == cms_req, "CMS_Total"
    
    # 2. Requerimiento de Energía Neta de Lactancia (NEL)
    prob += lpSum([variables[row["Ingrediente"]] * row["NEL"] for idx, row in editable_df.iterrows()]) >= nel_req * cms_req, "Min_NEL"
    
    # 3. Requerimiento de Proteína Metabolizable (PM en gramos)
    prob += lpSum([variables[row["Ingrediente"]] * row["MP"] for idx, row in editable_df.iterrows()]) >= mp_req_g, "Min_MP"
    
    # 4. Fibra Detergente Neutra de Forraje (Salud ruminal / peNDF)
    prob += lpSum([variables[row["Ingrediente"]] * (row["Forage_FDN"] / 100.0) for idx, row in editable_df.iterrows()]) >= (forage_fdn_min / 100.0) * cms_req, "Min_Forage_FDN"
    
    # 5. Límite superior de Almidón (Prevención de Acidosis SARA)
    prob += lpSum([variables[row["Ingrediente"]] * (row["Almidon"] / 100.0) for idx, row in editable_df.iterrows()]) <= (starch_max / 100.0) * cms_req, "Max_Starch"
    
    # 6. Límite superior de Extracto Etéreo / Grasa (Digestibilidad de fibra)
    prob += lpSum([variables[row["Ingrediente"]] * (row["EE"] / 100.0) for idx, row in editable_df.iterrows()]) <= (ee_max / 100.0) * cms_req, "Max_EE"
    
    # Resolver
    prob.solve()
    
    if LpStatus[prob.status] == 'Optimal':
        st.success("✅ ¡Dieta formulada exitosamente bajo estándares científicos rigurosos!")
        
        resultados = []
        costo_total = 0
        nel_sum = 0
        mp_sum = 0
        forage_fdn_sum = 0
        starch_sum = 0
        ee_sum = 0
        
        for idx, row in editable_df.iterrows():
            ing = row["Ingrediente"]
            cantidad = variables[ing].varValue
            if cantidad > 0.001:
                costo_parcial = cantidad * row["Costo"]
                costo_total += costo_parcial
                nel_sum += cantidad * row["NEL"]
                mp_sum += cantidad * row["MP"]
                forage_fdn_sum += cantidad * row["Forage_FDN"]
                starch_sum += cantidad * row["Almidon"]
                ee_sum += cantidad * row["EE"]
                
                resultados.append({
                    "Ingrediente": ing,
                    "Cantidad (kg MS)": round(cantidad, 2),
                    "Costo Parcial (MXN)": round(costo_parcial, 2)
                })
                
        df_res = pd.DataFrame(resultados)
        st.dataframe(df_res, use_container_width=True)
        
        st.metric(label="Costo Total Diario por Vaca", value=f"${costo_total:.2f} MXN")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("NEL Consumida", f"{nel_sum/cms_req:.2f} Mcal/kg", f"Meta: {nel_req}")
        col2.metric("PM Total", f"{mp_sum:.0f} g", f"Meta: {mp_req_g} g")
        col3.metric("Almidón en Dieta", f"{(starch_sum/cms_req)*100:.1f}%", f"Máx: {starch_max}%")
        col4.metric("FDN de Forraje", f"{(forage_fdn_sum/cms_req)*100:.1f}%", f"Mín: {forage_fdn_min}%")
        
    else:
        st.error("⚠️ No se encontró solución factible. Las restricciones cruzadas (por ejemplo, exigir mucha fibra de forraje con un límite bajo de ingredientes) son estrictas. Intenta ajustar los rangos de inclusión.")
