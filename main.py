import streamlit as st
import ezdxf
import io
import math
import pandas as pd

# Configuración
st.set_page_config(page_title="DrillPath AI", page_icon="🏗️", layout="wide")
st.title("🏗️ DrillPath AI: Ingeniería HDD de Precisión")

# --- 1. ENTRADA DE DATOS ---
with st.sidebar:
    st.header("Parámetros del Proyecto")
    proyecto = st.text_input("Nombre del Proyecto", "Cruce Río Ebro")
    longitud = st.number_input("Longitud (m)", value=352.68)
    diametro_tubo_mm = st.number_input("Diámetro Tubería (mm)", value=355.0)
    diametro_reamer = st.number_input("Diámetro Escariador (m)", value=0.5)
    prof_max = st.number_input("Profundidad Máxima (m)", value=5.0)
    suelo = st.selectbox("Tipo de Suelo", ["Arcillas", "Arenas", "Gravas"])
    sg_lodo = st.slider("Densidad Lodo (SG)", 1.0, 1.8, 1.2)
    densidad_suelo = st.number_input("Densidad Suelo (g/cm³)", value=1.8)

# --- 2. MOTOR DE CÁLCULO (Lógica de Ingeniería) ---
def ejecutar_calculos_hdd(L, D_tubo, D_reamer, prof, suelo, sg, dens_suelo):
    D_tubo_m = D_tubo / 1000
    # ROP y Secuencia lógica
    rop_base = {"Arcillas": 8.0, "Arenas": 5.0, "Gravas": 3.0}
    rop = rop_base.get(suelo, 5.0) / (dens_suelo / 1.5)
    factor_lodos = 1.0 + (1 / rop)
    
    # Volúmenes
    vol_interno = math.pi * (D_tubo_m/2)**2 * L
    vol_anular = (math.pi * (D_reamer/2)**2 * L) - vol_interno
    vol_detritos = vol_anular * factor_lodos
    
    # Flotabilidad
    fuerza_bf = (math.pi * (D_tubo_m/2)**2) * L * sg * 1000
    peso_tubo = L * 50 
    flotabilidad_neta = fuerza_bf - peso_tubo
    
    # Pullback y MAP
    k_valores = {"Arcillas": 20, "Arenas": 14, "Gravas": 24}
    pullback = (L * D_tubo_m * k_valores.get(suelo, 18)) / 100
    map_presion = prof * 0.15 
    caudal = (D_reamer * 1000) * 0.8
    
    return locals()

res = ejecutar_calculos_hdd(longitud, diametro_tubo_mm, diametro_reamer, prof_max, suelo, sg_lodo, densidad_suelo)

# --- 3. INTERFAZ DE RESULTADOS ---
st.subheader("📊 Análisis de Ingeniería HDD")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pullback", f"{res['pullback']:.2f} Tn")
c2.metric("Vol. Detritos", f"{res['vol_detritos']:.2f} m³")
c3.metric("Flotabilidad Neta", f"{res['flotabilidad_neta']:.0f} kg")
c4.metric("MAP (Límite)", f"{res['map_presion']:.2f} Bar")

# --- 4. CARGA DE TOPOGRAFÍA Y DXF ---
st.divider()
st.subheader("💾 Entregables y Perfil Real")
uploaded_file = st.file_uploader("Cargar perfil topográfico (Excel con 2 columnas: Distancia, Cota)", type=["xlsx", "csv"])

def create_dxf(puntos):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline(puntos, dxfattribs={'color': 1})
    out = io.BytesIO()
    doc.write(out, fmt="bin")
    out.seek(0)
    return out

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    puntos_topo = list(zip(df.iloc[:, 0], df.iloc[:, 1]))
    
    dxf_file = create_dxf(puntos_topo)
    st.download_button("📥 Descargar Perfil Real (.DXF)", data=dxf_file, file_name=f"{proyecto}_perfil.dxf", mime="application/dxf")
    st.success("Perfil cargado y listo para exportar.")
else:
    st.info("Sube un archivo de topografía para generar el perfil real.")





