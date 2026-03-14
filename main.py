import streamlit as st
import ezdxf
import io
import math
import pandas as pd

st.set_page_config(page_title="DrillPath AI", layout="wide")
st.title("🏗️ DrillPath AI: Ingeniería HDD")

with st.sidebar:
    st.header("Parámetros")
    proyecto = st.text_input("Proyecto", "Cruce ADIF")
    longitud = st.number_input("Longitud (m)", value=350.0)
    prof_diseno = st.number_input("Profundidad (m)", value=15.0)
    suelo = st.selectbox("Suelo", ["Arcillas", "Arenas", "Gravas"])

k_suelo = {"Arcillas": 20, "Arenas": 14, "Gravas": 24}
p_back = (longitud * 0.355 * k_suelo.get(suelo, 18)) / 100

st.subheader("📊 Resultados")
st.metric("Pullback Estimado", f"{p_back:.2f} Tn")

def crear_dxf(puntos, prof):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline(puntos, dxfattribs={'color': 1})
    xi, yi = puntos[0]
    xf, yf = puntos[-1]
    ymin = min([p[1] for p in puntos])
    curva = [(xi, yi), ((xi+xf)/2, ymin-prof), (xf, yf)]
    msp.add_spline(curva, dxfattribs={'color': 4})
    buf = io.BytesIO()
    doc.write(buf, fmt="bin")
    buf.seek(0)
    return buf

st.divider()
archivo = st.file_uploader("Subir TOPO ADIF.csv", type=["csv", "xlsx"])

if archivo:
    try:
        if archivo.name.endswith('.xlsx'):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo, sep=None, engine='python')
        x = pd.to_numeric(df.iloc[:,0].astype(str).str.replace(',','.'), errors='coerce')
        y = pd.to_numeric(df.iloc[:,1].astype(str).str.replace(',','.'), errors='coerce')
        df_c = pd.DataFrame({'x': x, 'y': y}).dropna()
        pts = list(zip(df_c['x'] - df_c['x'].iloc[0], df_c['y'] - df_c['y'].iloc[0]))
        dxf = crear_dxf(pts, prof_diseno)
        st.download_button("📥 Descargar DXF", data=dxf, file_name="perfil.dxf")
        st.success("¡Plano listo!")
    except Exception as e:
        st.error(f"Error: {e}")
