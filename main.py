import streamlit as st
import ezdxf
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="DrillPath AI", page_icon="🏗️", layout="wide")

st.title("🏗️ DrillPath AI: Ingeniería HDD de Precisión")
st.sidebar.header("Parámetros del Proyecto")

# --- ENTRADA DE DATOS ---
with st.sidebar:
    proyecto = st.text_input("Nombre del Proyecto", "Cruce Río Ebro")
    longitud = st.number_input("Longitud del tramo (m)", min_value=1.0, value=150.0)
    diametro = st.number_input("Diámetro tubería (mm)", min_value=10.0, value=250.0)
    suelo = st.selectbox("Tipo de Suelo", ["Arcilla", "Arena", "Roca", "Grava"])
    prof_max = st.number_input("Profundidad Máxima (m)", value=5.0)

# --- LÓGICA DE CÁLCULO ---
st.subheader("📊 Análisis de Viabilidad Técnica")
col1, col2, col3 = st.columns(3)

# Simulación de cálculo
friccion = {"Arcilla": 0.3, "Arena": 0.5, "Roca": 0.8, "Grava": 0.6}
tension = longitud * (diametro / 20) * friccion[suelo]

with col1:
    st.metric("Tensión de Pullback", f"{round(tension, 2)} kg")
with col2:
    status = "✅ SEGURO" if tension < 5000 else "⚠️ ALERTA"
    st.metric("Estado de Seguridad", status)
with col3:
    st.metric("Lodo Estimado", f"{round(longitud * 0.15, 2)} m³")

# --- GENERACIÓN DE AUTOCAD ---
def create_dxf():
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (longitud, 0)], dxfattribs={'color': 3})
    msp.add_spline([(0, 0), (longitud/2, -prof_max), (longitud, 0)], dxfattribs={'color': 1})
    
    # Usamos un buffer binario
    out = io.BytesIO()
    # Escribimos explícitamente en formato binario
    doc.write(out, fmt="bin")
    # Movemos el puntero al principio para que Streamlit pueda leerlo
    out.seek(0)
    return out 

    

st.divider()
st.subheader("💾 Entregables de Consultoría")

# Botón de descarga
dxf_file = create_dxf()
st.download_button(
    label="📥 Descargar Perfil en AutoCAD (.DXF)",
    data=dxf_file,
    file_name=f"{proyecto}_perfil.dxf",
    mime="application/dxf"
)

st.info("Próxima actualización: Integración de IA para lectura de informes geotécnicos PDF.")




