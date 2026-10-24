import streamlit as st
import requests
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# Configuración inicial de la página
st.set_page_config(page_title="Viajes Majo Aleja", page_icon="🌍", layout="wide")

# Clases de soporte para la lógica del negocio
class ConversorDivisas:
    def __init__(self):
        self.tasas = {"EUR": 1.0, "USD": 1.09, "JPY": 162.50, "GBP": 0.86, "MXN": 18.50}
    
    def convertir(self, cantidad_eur, divisa_destino):
        tasa = self.tasas.get(divisa_destino, 1.0)
        return cantidad_eur * tasa

class FiltroSeguridad:
    def __init__(self):
        self.seguridad = {
            "japon": "Bajo Riesgo", "tokyo": "Bajo Riesgo", "kyoto": "Bajo Riesgo",
            "francia": "Bajo Riesgo", "paris": "Bajo Riesgo",
            "islandia": "Bajo Riesgo", "reykjavik": "Bajo Riesgo",
            "españa": "Bajo Riesgo", "madrid": "Bajo Riesgo", "barcelona": "Bajo Riesgo",
            "estados unidos": "Riesgo Medio", "new york": "Riesgo Medio"
        }
    
    def obtener_riesgo(self, destino):
        return self.seguridad.get(destino.lower(), "Bajo Riesgo")

# Título de la aplicación con la nueva marca
st.title("🌍 Viajes Majo Aleja")
st.subheader("Tu comparador inteligente de viajes seguros y optimizados por clima")

# Menú lateral para la configuración del usuario
with st.sidebar:
    st.header("⚙️ Configuración del Viaje")
    origen = st.text_input("Ciudad de Origen", "Madrid")
    destino = st.text_input("Ciudad de Destino", "Tokyo")
    presupuesto = st.number_input("Presupuesto Máximo (EUR)", min_value=100, value=1500)
    
    conversor = ConversorDivisas()
    divisa_seleccionada = st.selectbox("Moneda de Visualización", list(conversor.tasas.keys()))
    tasa_actual = conversor.tasas[divisa_seleccionada]

# Lógica para obtener coordenadas y clima real mediante API gratuita
def obtener_datos_viaje(ciudad_destino):
    try:
        url_geo = f"https://open-meteo.com{ciudad_destino}&count=1&language=es&format=json"
        res_geo = requests.get(url_geo).json()
        
        if not res_geo.get("results"):
            return None
        
        lat = res_geo["results"][0]["latitude"]
        lon = res_geo["results"][0]["longitude"]
        
        url_clima = f"https://open-meteo.com{lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,rain_sum&timezone=auto"
        res_clima = requests.get(url_clima).json()
        
        return res_clima
    except:
        return None

datos_clima = obtener_datos_viaje(destino)

if datos_clima:
    temp_max_promedio = np.mean(datos_clima["daily"]["temperature_2m_max"])
    lluvia_total = np.sum(datos_clima["daily"]["rain_sum"])
    
    seguridad_motor = FiltroSeguridad()
    nivel_riesgo = seguridad_motor.obtener_riesgo(destino)
    
    dias = [f"Día {i}" for i in range(1, 31)]
    base_vuelo = 400
    base_hotel = 80
    
    precios_vuelo = [base_vuelo + int(50 * np.sin(i/2)) + int(30 * np.cos(i/3)) for i in range(1, 31)]
    precios_hotel = [base_hotel + int(15 * np.sin(i/2)) for i in range(1, 31)]
    precios_totales_eur = [v + (h * 5) for v, h in zip(precios_vuelo, precios_hotel)]
    
    precios_totales_mostrar = [conversor.convertir(p, divisa_seleccionada) for p in precios_totales_eur]
    
    df_precios = pd.DataFrame({"Día": dias, f"Precio Total ({divisa_seleccionada})": precios_totales_mostrar})
    
    indice_optimo = np.argmin(precios_totales_eur)
    dia_optimo = dias[indice_optimo]
    precio_optimo_eur = precios_totales_eur[indice_optimo]
    precio_optimo_mostrar = precios_totales_mostrar[indice_optimo]
    
    equipaje = ["Pasaporte y documentos", "Cargadores y adaptadores"]
    if temp_max_promedio < 15:
        equipaje.append("Ropa de abrigo pesada y chaqueta térmica")
    else:
        equipaje.append("Ropa ligera y cómoda")
        
    if lluvia_total > 2.0:
        equipaje.append("Paraguas y calzado impermeable")
    else:
        equipaje.append("Gafas de sol")

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperatura Máx Promedio", f"{temp_max_promedio:.1f} °C")
    col2.metric("Nivel de Seguridad", nivel_riesgo)
    col3.metric(f"Mejor Precio ({divisa_seleccionada})", f"{precio_optimo_mostrar:.2f} {divisa_seleccionada}")
    
    st.subheader(f"📈 Curva de Precios Estimada para el Mes ({divisa_seleccionada})")
    st.line_chart(df_precios.set_index("Día"))
    
    st.subheader("🎒 Lista de Equipaje Recomendada (Según Clima Real)")
    for item in equipaje:
        st.write(f"- {item}")
        
    def generar_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Informe Oficial de Viaje - Viajes Majo Aleja", styles["Title"]))
        story.append(Spacer(1, 12))
        
        datos = [
            ["Concepto", "Detalle"],
            ["Origen", origen],
            ["Destino", destino],
            ["Seguridad del Destino", nivel_riesgo],
            ["Clima Promedio", f"{temp_max_promedio:.1f} °C"],
            [f"Precio Óptimo ({divisa_seleccionada})", f"{precio_optimo_mostrar:.2f} {divisa_seleccionada}"],
            ["Día Recomendado para Viajar", dia_optimo]
        ]
        
        tabla = Table(datos)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.blue),
            ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        story.append(tabla)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Equipaje Recomendado:", styles["Heading2"]))
        for item in equipaje:
            story.append(Paragraph(f"• {item}", styles["Normal"]))
            
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def generar_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_precios.to_excel(writer, index=False, sheet_name="Curva de Precios")
            df_resumen = pd.DataFrame({
                "Parámetro": ["Origen", "Destino", "Día Óptimo", "Precio Total Estancia", "Moneda"],
                "Valor": [origen, destino, dia_optimo, precio_optimo_mostrar, divisa_seleccionada]
            })
            df_resumen.to_excel(writer, index=False, sheet_name="Resumen del Viaje")
        return output.getvalue()
        
    st.subheader("📥 Exportar Datos")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(label="📄 Descargar Itinerario en PDF", data=generar_pdf(), file_name="Viajes_Majo_Aleja_Reporte.pdf", mime="application/pdf")
    with c2:
        st.download_button(label="📊 Descargar Matriz de Precios en Excel", data=generar_excel(), file_name="Viajes_Majo_Aleja_Precios.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.error("No se han podido obtener datos climatológicos del destino seleccionado. Por favor, revisa la ortografía de la ciudad.")

