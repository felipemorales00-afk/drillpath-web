import streamlit as st
import ezdxf
import io
import math
import pandas as pd

# 1. Configuración de la interfaz
st.set_page_config(page_title="DrillPath AI", page_icon="🏗️", layout="wide")
st.title("🏗️ DrillPath AI: Ingeniería HDD de Precisión")

# 2. Panel lateral de parámetros
with st.sidebar:
    st.header("Configuración del Proyecto")
    proyecto = st.text_input("Nombre del Proyecto", "Cruce ADIF")
    longitud_nominal = st.number_input("Longitud teórica (m)", value=350.0)
    diametro_tubo_mm = st.number_input("Diámetro Tubería (mm)", value=355.0)
    diametro_reamer = st.number_input("Diámetro Escariador (m)", value=0.5)
    prof_diseno = st.number_input("Profundidad de Perforación (m)", value=15.0)
    suelo = st.selectbox("Tipo de Suelo", ["Arcillas", "Arenas", "Gravas"])
    sg_lodo = st.slider("Densidad Lodo (SG)", 1.0, 1.8, 1.2)
    densidad_suelo = st.number_input("Densidad Suelo (g/cm³)", value=1.8)

# 3. Lógica de Cálculos
def calcular_ingenieria(L, D_tubo, D_reamer, prof, suelo, sg, dens_suelo):
    D_m = D_tubo / 1000
    # Factores de fricción estimados
    k_suelo = {"Arcillas": 20, "Arenas": 14, "Gravas": 24}
    pullback = (L * D_m * k_suelo.get(suelo, 18)) / 100
    
    # Volumen de detritos
    rop_est = {"Arcillas": 8, "Arenas": 5, "Gravas": 3}.get(suelo, 5)
    vol_anular = (math.pi * (D_reamer/2)**2 * L) - (math.pi * (D_m/2)**2 * L)
    detritos = vol_anular * (1 + (1/rop_est))
    
    # Presión MAP y Flotabilidad
    map_p = prof * 0.15
    buoyancy = (math.pi * (D_m/2)**2) * L * sg * 1000 - (L * 50)
    
    return pullback, detritos, buoyancy, map_p

p_back, v_det, b_force, m_pres = calcular_ingenieria(longitud_nominal, diametro_tubo_mm, diametro_reamer, prof_diseno, suelo, sg_lodo, densidad_suelo)

# 4. Cuadro de mando (Métricas)
st.subheader("📊 Análisis de Ingeniería")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pullback Est.", f"{p_back:.2f} Tn")
col2.metric("Vol. Detritos", f"{v_det:.2f} m³")
col3.metric("Flotabilidad", f"{b_force:.0f} kg")
col4.metric("Límite MAP", f"{m_pres:.2f} Bar")

# 5. Función para generar el archivo DXF
def crear_archivo_dxf(puntos_suelo, profundidad):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Dibujar Terreno (Rojo)
    msp.add_lwpolyline(puntos_suelo, dxfattribs={'color': 1})
    
    # Dibujar Perforación (Cian)
    x_i, y_i = puntos_suelo[0]
    x_f, y_f = puntos_suelo[-1]
    y_suelo_min = min([p[1] for p in puntos_suelo])
    
    # Curva simple de 3 puntos (Inicio, Centro bajo, Fin)
    puntos_curva = [
        (x_i, y_i),
        ((x_i + x_f) / 2, y_suelo_min - profundidad),
        (x_f, y_f)
    ]
    msp.add_spline(puntos_curva, dxfattribs={'color': 4})
    
    # Guardar en memoria
    buf = io.BytesIO()
    doc.write(buf, fmt="bin")
    buf.seek(0)
    return buf

# 6. Sección de carga de datos
st.divider()
st.subheader("💾 Topografía y Diseño de Perfil")
archivo = st.file_uploader("Cargar TOPO ADIF.csv", type=["csv", "xlsx"])

if archivo:
    try:
        if archivo.name.endswith('.xlsx'):
            df = pd.read_excel(archivo)
        else:
            # Detección automática de separador (coma o punto y coma)
            df = pd.read_csv(archivo, sep=None, engine='python')
        
        if df.shape[1] >= 2:
            # Limpiar datos: convertir a número y manejar comas decimales
            x_data = pd.to_numeric(df.iloc[:,0].astype(str).str.replace(',','.'), errors='coerce')
            y_data = pd.to_numeric(df.iloc[:,1].astype(str).str.replace(',','.'), errors='coerce')
            
            # Quitar filas vacías
            df_clean = pd.DataFrame({'x': x_data, 'y': y_data}).dropna()
            
            # Normalizar para que el primer punto sea 0,0
            pts = list(zip(df_clean['x'] - df_clean['x'].iloc[0], df_clean['y'] - df_clean['y'].iloc[0]))
            
            # Generar y descargar
            dxf_output = crear_archivo_dxf(pts, prof_diseno)
            st.download_button("📥 Descargar Diseño Final (.DXF)", data=dxf_output, file_name="diseno_perfil_hdd.dxf")
            st.success("Plano generado con éxito.")
        else:
            st.error("El archivo necesita 2 columnas de datos.")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando archivo de topografía...")
