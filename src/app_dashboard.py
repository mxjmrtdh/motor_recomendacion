import streamlit as st
import requests
import pandas as pd

# Configuración básica de la página
st.set_page_config(
    page_title="Monitor de Recomendaciones - Olist",
    page_icon="🛍️",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

st.title("🛍️ Dashboard de Monitoreo MLOps - Motor de Recomendaciones")
st.markdown("Sistema de recomendación en tiempo real integrando **BFS (Grafos) + Modelo Clasificador (.pkl) + Feature Store**.")

# Sidebar de Estado del Servidor
st.sidebar.header("⚙️ Estado de la API")
try:
    res_health = requests.get(f"{API_URL}/", timeout=2)
    if res_health.status_code == 200:
        st.sidebar.success("API Conectada (HTTP 200)")
        datos_health = res_health.json()
        st.sidebar.json(datos_health)
    else:
        st.sidebar.error("Error al conectar con la API")
except Exception:
    st.sidebar.error("⚠️ La API de FastAPI no está ejecutándose en http://127.0.0.1:8000")

# Contenido Principal - Tabs
tab1, tab2 = st.tabs(["🎯 Generar Recomendaciones", "👤 Consultar Feature Store (Usuarios)"])

# TAB 1: RECOMENDADOR
with tab1:
    st.subheader("Probar Inferencia en Vivo")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # ID de ejemplo predeterminado
        product_input = st.text_input(
            "Ingrese el ID del Producto Origen:", 
            value="aca2eb7d00ea1a7b8ebd4e68314663af"
        )
    with col2:
        limite_input = st.slider("Cantidad de Recomendaciones:", min_value=1, max_value=10, value=5)

    if st.button("🚀 Obtener Recomendaciones", type="primary"):
        with st.spinner("Consultando API y ejecutando Re-ranking de IA..."):
            try:
                response = requests.get(f"{API_URL}/recomendar/{product_input}?limite={limite_input}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Métricas clave en tarjetas
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Latencia Total", f"{data['latencia_ms']} ms")
                    m2.metric("Estrategia Aplicada", data['estrategia'])
                    m3.metric("Total Recomendados", data['total_recomendaciones'])
                    
                    st.divider()
                    
                    # Tabla de recomendaciones
                    if data['recomendaciones']:
                        df_recom = pd.DataFrame(data['recomendaciones'])
                        st.write("### 📋 Productos Recomendados por el Modelo")
                        st.dataframe(
                            df_recom, 
                            column_config={
                                "product_id": "ID del Producto",
                                "category": "Categoría",
                                "price": st.column_config.NumberColumn("Precio ($)", format="%.2f"),
                                "score_relevancia": st.column_config.ProgressColumn(
                                    "Score de Relevancia IA", min_value=0.0, max_value=1.0, format="%.4f"
                                )
                            },
                            use_container_width=True
                        )
                    else:
                        st.warning("No se encontraron recomendaciones para este producto.")
                else:
                    st.error(f"Error en la API: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"No se pudo conectar con la API: {e}")

# TAB 2: FEATURE STORE
with tab2:
    st.subheader("Inspeccionar Pérfil de Usuario en RAM (Feature Store)")
    customer_input = st.text_input(
        "Ingrese el ID del Cliente (customer_id):", 
        value="06b009f7d0738513a4220706a782e33b"
    )
    
    if st.button("🔍 Consultar Feature Store"):
        try:
            res_user = requests.get(f"{API_URL}/usuario/perfil/{customer_input}")
            if res_user.status_code == 200:
                user_data = res_user.json()
                st.metric("Latencia de Lectura RAM O(1)", f"{user_data['latencia_ms']} ms")
                st.write("**Variables Precalculadas en RAM:**")
                st.json(user_data['perfil_features'])
            else:
                st.error("Error al obtener perfil de usuario.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")