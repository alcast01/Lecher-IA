import streamlit as st
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import pandas as pd

# 1. Configuración de la página con ícono en la pestaña del navegador
st.set_page_config(
    page_title="LactiDiete MX | Optimizador de Dietas Lecheras",
    page_icon="🐄",
    layout="wide"
)

# --- 2. ENCABEZADO Y LOGOTIPO ---
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    # Muestra un distintivo visual estilo badge/logo con HTML/CSS
    st.markdown(
        """
        <div style="background-color: #2E7D32; padding: 15px; border-radius: 12px; text-align: center; color: white;">
            <span style="font-size: 45px;">🐄🥛</span><br>
            <strong style="font-size: 14px; letter-spacing: 1px;">LACTI-DIETA</strong><br>
            <span style="font-size: 10px; opacity: 0.8;">NUTRICIÓN BOVINA</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("LactiDieta MX — Formulación de Mínimo Costo")
    st.markdown("**Sistema inteligente de optimización de raciones para vacas lecheras en producción.**")

st.markdown("---")

# --- BARRA LATERAL (SIDEBAR) CON LOGO MINIMALISTA ---
st.sidebar.markdown(
    """
    <div style="text-align: center; padding-bottom: 10px;">
        <span style="font-size: 30px;">🐮🌾</span>
        <h3 style="margin: 0; color: #2E7D32;">LactiDieta Pro</h3>
        <small>Formulación Ganado Lechero</small>
    </div>
    <hr style="margin-top: 5px; margin-bottom: 15px;">
    """,
    unsafe_allow_html=True
)

st.sidebar.header("⚙️ Requerimientos Nutricionales")
cms_req = st.sidebar.slider("Consumo de Materia Seca (kg MS)", 15.0, 25.0, 21.0, 0.5)
nel_req = st.sidebar.slider("Energía Neta de Lactancia Mínima (Mcal/kg MS)", 1.4, 1.8, 1.65, 0.01)
pc_req = st.sidebar.slider("Proteína Cruda Mínima (%)", 12.0, 20.0, 16.0, 0.5)
fdn_min = st.sidebar.slider("Fibra Detergente Neutra Mínima (%)", 25.0, 38.0, 30.0, 0.5)

# --- DATOS BASE DE INGREDIENTES ---
datos_base = {
    "Ingrediente": ["Silo de Maíz", "Heno de Alfalfa", "Maíz Molido", "Sorgo Grano", "Pasta de Soya", "DDGS de Maíz", "Melasa de Caña", "Salvado de Trigo"],
    "Costo": [2.00, 4.00, 5.40, 4.80, 9.80, 7.00, 3.50, 4.50],
    "NEL": [1.60, 1.40, 2.10, 2.00, 2.02, 1.95, 1.75, 1.65],
    "PC": [8.5, 18.0, 9.5, 10.5, 45.0, 28.0, 4.5, 16.0],
    "FDN": [45.0, 42.0, 10.0, 13.0, 14.0, 40.0, 1.0, 40.0],
    "Min_Inclusion": [5.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "Max_Inclusion": [15.0, 10.0, 8.0, 8.0, 4.0, 4.0, 2.0, 5.0]
}

df_ingredientes = pd.DataFrame(datos_base)

st.subheader("📋 Tabla de Ingredientes y Precios (Editables)")
editable_df = st.data_editor(df_ingredientes, num_rows="dynamic")

if st.button("🚀 Optimizar Dieta al Menor Costo"):
    prob = LpProblem("Balance_Dietas_Lecheras", LpMinimize)
    
    ingredientes = editable_df["Ingrediente"].tolist()
    variables = {}
    for idx, row in editable_df.iterrows():
        ing = row["Ingrediente"]
        variables[ing] = LpVariable(f"x_{ing.replace(' ', '_')}", lowBound=row["Min_Inclusion"], upBound=row["Max_Inclusion"])
        
    prob += lpSum([variables[row["Ingrediente"]] * row["Costo"] for idx, row in editable_df.iterrows()])
    
    # Restricciones
    prob += lpSum([variables[row["Ingrediente"]] for idx, row in editable_df.iterrows()]) == cms_req, "CMS_Total"
    prob += lpSum([variables[row["Ingrediente"]] * row["NEL"] for idx, row in editable_df.iterrows()]) >= nel_req * cms_req, "Min_NEL"
    prob += lpSum([variables[row["Ingrediente"]] * (row["PC"] / 100.0) for idx, row in editable_df.iterrows()]) >= (pc_req / 100.0) * cms_req, "Min_PC"
    prob += lpSum([variables[row["Ingrediente"]] * (row["FDN"] / 100.0) for idx, row in editable_df.iterrows()]) >= (fdn_min / 100.0) * cms_req, "Min_FDN"
    
    prob.solve()
    
    if LpStatus[prob.status] == 'Optimal':
        st.success("✅ ¡Dieta optimizada con éxito!")
        
        resultados = []
        costo_total = 0
        nel_total = 0
        pc_total = 0
        fdn_total = 0
        
        for idx, row in editable_df.iterrows():
            ing = row["Ingrediente"]
            cantidad = variables[ing].varValue
            if cantidad > 0.001:
                costo_parcial = cantidad * row["Costo"]
                costo_total += costo_parcial
                nel_total += cantidad * row["NEL"]
                pc_total += cantidad * (row["PC"] / 100.0)
                fdn_total += cantidad * (row["FDN"] / 100.0)
                resultados.append({
                    "Ingrediente": ing,
                    "Cantidad (kg MS)": round(cantidad, 2),
                    "Costo Parcial (MXN)": round(costo_parcial, 2)
                })
                
        df_res = pd.DataFrame(resultados)
        st.dataframe(df_res, use_container_width=True)
        
        st.metric(label="Costo Total Diario de la Ración por Vaca", value=f"${costo_total:.2f} MXN")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("NEL Promedio", f"{nel_total/cms_req:.2f} Mcal/kg", f"Meta: {nel_req}")
        col2.metric("Proteína Cruda", f"{(pc_total/cms_req)*100:.2f}%", f"Meta: {pc_req}%")
        col3.metric("FDN Total", f"{(fdn_total/cms_req)*100:.2f}%", f"Meta: {fdn_min}%")
    else:
        st.error("⚠️ No se encontró una solución factible con los límites y requerimientos actuales.")
