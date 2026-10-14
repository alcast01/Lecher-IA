import streamlit as st
import pulp
from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="LactiDieta Pro | NASEM & JDS Standard",
    page_icon="🐄",
    layout="wide"
)

# --- ENCABEZADO, LOGOTIPO Y SLOGAN ---
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
    st.markdown("**Eslogan:** *Optimizando la precisión ruminal y la rentabilidad lechera a través de la ciencia.*")
    st.markdown("<small style='color: #555;'>Diseñada y creada por el <b>Dr. Alejandro Castañeda Correa</b>.</small>", unsafe_allow_html=True)

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
mp_req_g = st.sidebar.slider("Proteína Metabolizable (PM en gramos)", 1500, 3000, 2100, 50)
forage_fdn_min = st.sidebar.slider("FDN de Forraje Mínima (% en MS)", 15.0, 28.0, 20.0, 0.5)
starch_max = st.sidebar.slider("Almidón Máximo (% en MS - Prev. SARA)", 20.0, 35.0, 26.0, 0.5)
ee_max = st.sidebar.slider("Extracto Etéreo / Grasa Máxima (% MS)", 4.0, 8.0, 6.0, 0.5)

# --- BASE DE DATOS CIENTÍFICA DE INGREDIENTES ---
datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS de Maíz", "Melasa de Caña", "Salvado de Trigo"],
    "Costo": [2.00, 4.00, 5.40, 4.80, 9.80, 7.00, 3.50, 4.50],
    "NEL": [1.62, 1.42, 2.15, 2.02, 2.05, 1.98, 1.78, 1.68],       
    "MP": [62.0, 115.0, 75.0, 70.0, 310.0, 190.0, 25.0, 110.0],   
    "FDN": [42.0, 40.0, 9.5, 12.0, 13.0, 39.0, 1.0, 39.0],         
    "Forage_FDN": [42.0, 38.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],     
    "Almidon": [28.0, 3.0, 72.0, 68.0, 1.5, 5.0, 0.0, 20.0],        
    "EE": [3.0, 2.0, 3.8, 3.1, 1.8, 9.0, 0.2, 4.2],               
    "Min_Inclusion": [5.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [16.0, 10.0, 10.0, 8.0, 5.0, 4.0, 2.0, 5.0]
}

df_ingredientes = pd.DataFrame(datos_base)

st.subheader("📋 Matriz de Ingredientes y Perfil Nutricional (JDS / NASEM)")
editable_df = st.data_editor(df_ingredientes, num_rows="fixed")

if st.button("🚀 Ejecutar Optimización Avanzada"):
    try:
        prob = LpProblem("Balance_Dietas_Avanzado", LpMinimize)
        
        variables = {}
        for idx, row in editable_df.iterrows():
            ing = str(row["Ingrediente"])
            variables[ing] = LpVariable(f"x_{ing.replace(' ', '_')}", lowBound=float(row["Min_Inclusion"]), upBound=float(row["Max_Inclusion"]))
            
        # Función Objetivo: Minimizar Costo Total
        prob += lpSum([variables[str(row["Ingrediente"])] * float(row["Costo"]) for idx, row in editable_df.iterrows()])
        
        # Restricciones Lineales
        prob += lpSum([variables[str(row["Ingrediente"])] for idx, row in editable_df.iterrows()]) == float(cms_req), "CMS_Total"
        prob += lpSum([variables[str(row["Ingrediente"])] * float(row["NEL"]) for idx, row in editable_df.iterrows()]) >= float(nel_req) * float(cms_req), "Min_NEL"
        prob += lpSum([variables[str(row["Ingrediente"])] * float(row["MP"]) for idx, row in editable_df.iterrows()]) >= float(mp_req_g), "Min_MP"
        prob += lpSum([variables[str(row["Ingrediente"])] * (float(row["Forage_FDN"]) / 100.0) for idx, row in editable_df.iterrows()]) >= (float(forage_fdn_min) / 100.0) * float(cms_req), "Min_Forage_FDN"
        prob += lpSum([variables[str(row["Ingrediente"])] * (float(row["Almidon"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(starch_max) / 100.0) * float(cms_req), "Max_Starch"
        prob += lpSum([variables[str(row["Ingrediente"])] * (float(row["EE"]) / 100.0) for idx, row in editable_df.iterrows()]) <= (float(ee_max) / 100.0) * float(cms_req), "Max_EE"
        
        # Resolver el modelo
        prob.solve()
        
        # Validación de estado con la nueva sintaxis compatible de PuLP
        if prob.status == pulp.LpStatusOptimal:
            st.success("✅ ¡Dieta formulada exitosamente bajo estándares científicos rigurosos!")
            
            resultados = []
            costo_total = 0
            nel_sum = 0
            mp_sum = 0
            forage_fdn_sum = 0
            starch_sum = 0
            ee_sum = 0
            
            for idx, row in editable_df.iterrows():
                ing = str(row["Ingrediente"])
                cantidad = variables[ing].varValue
                if cantidad and cantidad > 0.001:
                    costo_parcial = cantidad * float(row["Costo"])
                    costo_total += costo_parcial
                    nel_sum += cantidad * float(row["NEL"])
                    mp_sum += cantidad * float(row["MP"])
                    forage_fdn_sum += cantidad * float(row["Forage_FDN"])
                    starch_sum += cantidad * float(row["Almidon"])
                    ee_sum += cantidad * float(row["EE"])
                    
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
            st.warning("⚠️ No se encontró solución factible con los requerimientos actuales. Intenta ajustar los valores de la barra lateral o los límites de inclusión de los ingredientes.")
            
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el modelo matemático: {e}")

# Pie de página con créditos institucionales
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 12px;'>LactiDieta Pro &bull; Desarrollado por el Dr. Alejandro Castañeda Correa para la Nutrición Bovina Avanzada.</p>", unsafe_allow_html=True)
