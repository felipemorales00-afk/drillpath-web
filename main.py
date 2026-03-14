
import streamlit as st
import ezdxf
import io
import math
import pandas as pd

# 1. Configuración de la página
st.set_page_config(page_title="DrillPath AI", page_icon="🏗️", layout="wide")

st.title("🏗️ DrillPath AI: Ingeniería HDD de Precisión")

# 2. Parámetros en la barra lateral
with st.sidebar:
    st.header("Parámetros del Proyecto")
    proyecto = st.text_input("Nombre del Proyecto", "Cruce ADIF")
    longitud_nominal = st.number_input("Longitud teórica (m)", value=352.68)
    diametro_tubo_mm = st.number_input("Diámetro Tubería (mm)", value=355.0)
    diametro_reamer = st.number_input("Diámetro Escariador (m)", value=0.5)
    prof_diseno = st.number_input("Profundidad de Perforación (m)", value=15.0)
    suelo = st.selectbox("Tipo de Suelo", ["Arcillas", "Arenas", "Gravas"])
    sg_lodo = st.slider("Densidad Lodo (SG)", 1.0, 1.8, 1.2)
    densidad_suelo = st.number_input("Densidad Suelo (g/cm³)", value=1.8)

# 3. Cálculos de Ingeniería
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
    
    return locals()

res = ejecutar_calculos_hdd(longitud_nominal, diametro_tubo_mm, diametro_reamer, prof_diseno, suelo, sg_lodo, densidad_suelo)

# 4. Mostrar Resultados
st.subheader("📊 Análisis de Ingeniería HDD")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pullback", f"{res['pullback']:.2f} Tn")
c2.metric("Vol. Detritos", f"{res['vol_detritos']:.2f} m³")
c3.metric("Flotabilidad Neta", f"{res['flotabilidad_neta']:.0f} kg")
c4.metric("MAP (Límite)", f"{res['map_presion']:.2f} Bar")

# 5. Generación de Archivo DXF
def generar_dxf(puntos_topo, prof_perforacion):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Dibujar Terreno (Rojo)
    msp.add_lwpolyline(puntos_topo, dxfattribs={'color': 1})
    
    # Dibujar Perforación (Cian)
    x_ini, y_ini = puntos_topo[0]
    x_fin, y_fin = puntos_topo[-1]
    y_min_t = min([p[1] for p in puntos_topo])
    
    puntos_perfo = [
        (x_ini, y_ini),
        ((x_ini + x_fin) / 2, y_min_t - prof_perforacion),
        (x_fin, y_fin)
    ]
    msp.add_spline(puntos_perfo, dxfattribs={'color': 4})
    
    output = io.BytesIO()
    doc.write(output, fmt="bin")
    output.seek(0)
    return output

# 6. Carga de Archivos
st.divider()
st.subheader("💾 Carga de Topografía y Exportación")
archivo = st.file_uploader("Sube tu archivo TOPO ADIF.csv", type=["csv", "xlsx"])

if archivo:
    try:
        # Leer archivo con detección de separador
        if archivo.name.endswith('.xlsx'):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo, sep=None, engine='python')
        
        if df.shape[1] >= 2:
            # Convertir coordenadas y limpiar comas decimales
            x = pd.to_numeric(df.iloc[:, 0].astype(str).str.replace(',', '.'), errors='coerce')
            y = pd.to_numeric(df.iloc[:, 1].astype(str).str.replace(',', '.'), errors='coerce')
            validos = ~(x.isna() | y.isna())
            x, y = x[validos], y[validos]

            # Normalizar para que empiece en 0,0
            puntos = list(zip(x - x.iloc[0], y - y.iloc[0]))
            
            dxf_data = generar_dxf(puntos, prof_diseno)
            
            st.download_button("📥 Descargar DXF Final", data=dxf_data, file_name="perfil_hdd.dxf")
            st.success("¡Todo listo! Ya puedes descargar el archivo.")
        else:
            st.error("El archivo necesita 2 columnas.")
    except Exception as e:
        st.error(f"Error: {e}")
