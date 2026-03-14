import streamlit as st
import ezdxf
import io
import math
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="DrillPath AI", page_icon="🏗️", layout="wide")

st.title("🏗️ DrillPath AI: Ingeniería HDD de Precisión")

# --- 1. ENTRADA DE DATOS (SIDEBAR) ---
with st.sidebar:
    st.header("Parámetros del Proyecto")
    proyecto = st.text_input("Nombre del Proyecto", "Cruce Río Ebro")
    longitud = st.number_input("Longitud del tramo (m)", value=352.68)
    diametro_tubo_mm = st.number_input("Diámetro Tubería (mm)", value=355.0)
    diametro_reamer = st.number_input("Diámetro Escariador (m)", value=0.5)
    prof_max = st.number_input("Profundidad Máxima (m)", value=5.0)
    suelo = st.selectbox("Tipo de Suelo", ["Arcillas", "Arenas", "Gravas"])
    sg_lodo = st.slider("Densidad Lodo (SG)", 1.0, 1.8, 1.2)
    densidad_suelo = st.number_input("Densidad Suelo (g/cm³)", value=1.8)

# --- 2. MOTOR DE CÁLCULO ---
def ejecutar_calculos_hdd(L, D_tubo, D_reamer, prof, suelo, sg, dens_suelo):
    D_tubo_m = D_tubo / 1000
    rop_base = {"Arcillas": 8.0, "Arenas": 5.0, "Gravas": 3.0}
    rop = rop_base.get(suelo, 5.0) / (dens_suelo / 1.5)
    factor_lodos = 1.0 + (1 / rop)
    
    vol_interno = math.pi * (D_tubo_m/2)**2 * L
    vol_anular = (math.pi * (D_reamer/2)**2 * L) - vol_interno
    vol_detritos = vol_anular * factor_lodos
    
    fuerza_bf = (math.pi * (D_tubo_m/2)**2) * L * sg * 1000
    peso_tubo = L * 50 
    flotabilidad_neta = fuerza_bf - peso_tubo
    
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

archivo_subido = st.file_uploader("Cargar perfil topográfico (Excel o CSV)", type=["xlsx", "csv"])

def create_dxf(puntos):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline(puntos, dxfattribs={'color': 1})
    out = io.BytesIO()
    doc.write(out, fmt="bin")
    out.seek(0)
    return out

if archivo_subido:
    try:
        if archivo_subido.name.endswith('.xlsx'):
            df = pd.read_excel(archivo_subido)
        else:
            # Forzamos separador ';' porque es lo que detectamos en tu archivo
            df = pd.read_csv(archivo_subido, sep=';', engine='python')
        
        # Si el archivo leyó solo una columna, re-intentamos con coma
        if df.shape[1] < 2:
            archivo_subido.seek(0)
            df = pd.read_csv(archivo_subido, sep=',', engine='python')

        if df.shape[1] >= 2:
            st.success("¡Archivo cargado correctamente!")
            
            # Limpieza de datos (por si hay comas como decimales)
            x_raw = pd.to_numeric(df.iloc[:, 0].astype(str).str.replace(',', '.'), errors='coerce')
            y_raw = pd.to_numeric(df.iloc[:, 1].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Quitar filas con errores (NaN)
            validos = ~(x_raw.isna() | y_raw.isna())
            x_raw, y_raw = x_raw[validos], y_raw[validos]

            # Normalización para AutoCAD (Restamos el primer punto para empezar en 0,0)
            puntos_topo = list(zip(x_raw - x_raw.iloc[0], y_raw - y_raw.iloc[0]))
            
            archivo_dxf = create_dxf(puntos_topo)
            st.download_button("📥 Descargar Perfil Real (.DXF)", data=archivo_dxf, file_name=f"{proyecto}_perfil.dxf", mime="application/dxf")
            
            st.write("Vista previa de los datos procesados:")
            st.dataframe(df.head())
        else:
            st.error("El archivo no tiene suficientes columnas. Revisa que los datos estén separados por comas o punto y coma.")
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("Sube un archivo de topografía para generar el perfil real.")





