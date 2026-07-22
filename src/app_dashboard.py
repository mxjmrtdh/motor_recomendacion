import streamlit as st
import requests
import pandas as pd
import sqlite3
import os
import time

# Configuración básica de la página
st.set_page_config(
    page_title="Sistema MLOps & Motor de Recomendaciones - Olist",
    page_icon="🛍️",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
LOGS_PATH = os.path.join(BASE_DIR, "logs.csv")
API_URL = "http://127.0.0.1:8000"

# --- Funciones Auxiliares de Carga de Datos Muestra ---
@st.cache_data
def obtener_muestra_productos():
    """Consulta SQLite para obtener 15 IDs de productos reales para la muestra."""
    if not os.path.exists(DB_PATH):
        return ["aca2eb7d00ea1a7b8ebd4e68314663af", "999eb05a1d84700284f4672bc175f123"]
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT p.product_id, p.product_category_name, COUNT(oi.order_id) as ventas
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id
            ORDER BY ventas DESC
            LIMIT 15
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Crear etiquetas legibles: "ID_CORTO - Categoria (X ventas)"
        opciones = []
        for _, row in df.iterrows():
            cat = row['product_category_name'] or 'sin_categoria'
            label = f"{row['product_id']} | ({cat}, {row['ventas']} ventas)"
            opciones.append((row['product_id'], label))
        return opciones
    except Exception:
        return [("aca2eb7d00ea1a7b8ebd4e68314663af", "aca2eb7d00ea1a7b8ebd4e68314663af")]

@st.cache_data
def obtener_muestra_clientes():
    """Consulta SQLite para obtener 15 IDs de clientes para el Feature Store."""
    if not os.path.exists(DB_PATH):
        return ["06b009f7d0738513a4220706a782e33b"]
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT DISTINCT customer_id FROM orders LIMIT 15"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df['customer_id'].tolist()
    except Exception:
        return ["06b009f7d0738513a4220706a782e33b"]


# Carga inicial de datos de muestra
muestra_productos = obtener_muestra_productos()
muestra_clientes = obtener_muestra_clientes()


# --- Interfaz Principal ---
st.title("🛍️ Portal de Control MLOps - Motor de Recomendaciones Olist")
st.markdown("Plataforma interactiva para inferencia en tiempo real, monitoreo de latencias en `logs.csv` y consulta de Feature Store.")

# Sidebar de Estado del Servidor
st.sidebar.header("⚙️ Estado del Servidor FastAPI")
try:
    res_health = requests.get(f"{API_URL}/", timeout=2)
    if res_health.status_code == 200:
        st.sidebar.success("API Conectada (HTTP 200)")
        st.sidebar.json(res_health.json())
    else:
        st.sidebar.error("Error al conectar con la API")
except Exception:
    st.sidebar.error("⚠️ La API no está ejecutándose en http://127.0.0.1:8000")


# Definición de Pestañas (Tabs)
tab1, tab2, tab3 = st.tabs([
    "🎯 Probar Inferencia en Vivo", 
    "📊 Monitoreo de Latencias (logs.csv)", 
    "👤 Feature Store (Usuarios)"
])

# ==============================================================================
# TAB 1: PROBAR INFERENCIA EN VIVO
# ==============================================================================
with tab1:
    st.subheader("Generar Recomendaciones en Tiempo Real")
    st.caption("Seleccione un producto de la lista desplegable de muestra o ingrese uno manualmente para evaluar el modelo.")
    
    col_sel, col_lim = st.columns([3, 1])
    
    # Mapeo para el selector desplegable
    opciones_prod_labels = [item[1] for item in muestra_productos] + ["-- Ingresar ID Manualmente --"]
    
    with col_sel:
        seleccion_prod = st.selectbox(
            "Seleccione un Producto Muestra (ID | Categoría | Ventas):",
            options=opciones_prod_labels
        )
        
        # Lógica si elige ingresar manualmente
        if seleccion_prod == "-- Ingresar ID Manualmente --":
            product_input = st.text_input("Ingrese el Product ID personalizado:", value="aca2eb7d00ea1a7b8ebd4e68314663af")
        else:
            # Extraer el ID real de la tupla seleccionada
            idx = opciones_prod_labels.index(seleccion_prod)
            product_input = muestra_productos[idx][0]
            st.info(f"🔑 **ID de Producto Activo:** `{product_input}`")

    with col_lim:
        limite_input = st.slider("Cantidad a recomendar:", min_value=1, max_value=10, value=5)

    if st.button("🚀 Obtener Recomendaciones", type="primary"):
        with st.spinner("Consultando API y ejecutando Re-ranking de IA..."):
            try:
                response = requests.get(f"{API_URL}/recomendar/{product_input}?limite={limite_input}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Latencia de Respuesta", f"{data['latencia_ms']} ms")
                    m2.metric("Estrategia Aplicada", data['estrategia'])
                    m3.metric("Total Recomendados", data['total_recomendaciones'])
                    
                    st.divider()
                    
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

# ==============================================================================
# TAB 2: MONITOREO MLOPS EN TIEMPO REAL (LOGS.CSV)
# ==============================================================================
with tab2:
    st.subheader("Monitoreo de Operaciones, Latencia P95 y Métricas MLOps")
    
    col_ref, col_btn = st.columns([3, 1])
    with col_ref:
        st.caption("Lectura continua del archivo `logs.csv` generado por la API.")
    with col_btn:
        if st.button("🔄 Actualizar Logs Ahora"):
            st.rerun()

    def cargar_logs():
        if not os.path.exists(LOGS_PATH):
            return pd.DataFrame()
        try:
            df = pd.read_csv(LOGS_PATH)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception:
            return pd.DataFrame()

    df_logs = cargar_logs()

    if df_logs.empty:
        st.info("ℹ️ No se encontraron registros en `logs.csv`. Genera peticiones en la Tab 1 o ejecuta `python src/pruebas_carga.py`.")
    else:
        # KPIs del Sistema
        total_peticiones = len(df_logs)
        latencia_promedio = df_logs['latencia_ms'].mean()
        latencia_p95 = df_logs['latencia_ms'].quantile(0.95)
        tasa_exito = (len(df_logs[df_logs['status_code'] == 200]) / total_peticiones) * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Peticiones Registradas", total_peticiones)
        k2.metric("Latencia Promedio", f"{latencia_promedio:.2f} ms")
        k3.metric("Latencia P95", f"{latencia_p95:.2f} ms")
        k4.metric("Tasa de Disponibilidad (Uptime)", f"{tasa_exito:.1f}%")

        st.divider()

        # Gráficos
        g1, g2 = st.columns(2)

        with g1:
            st.write("#### 📈 Evolución de Latencia por Petición (ms)")
            st.line_chart(df_logs.set_index('timestamp')['latencia_ms'])

        with g2:
            st.write("#### 🎯 Distribución de Estrategias de Recomendación")
            conteo_estrategias = df_logs['estrategia'].value_counts()
            st.bar_chart(conteo_estrategias)

        st.divider()

        # Tabla de Logs
        st.write("#### 📋 Registro Detallado de Eventos en `logs.csv` (Últimas 20 Peticiones)")
        st.dataframe(
            df_logs.sort_values(by="timestamp", ascending=False).head(20),
            use_container_width=True
        )

# ==============================================================================
# TAB 3: FEATURE STORE (PERFILES DE USUARIO)
# ==============================================================================
with tab3:
    st.subheader("Consultar Perfil de Usuario en RAM (Feature Store)")
    st.caption("Seleccione un Customer ID de la muestra o ingrese uno manualmente para consultar sus métricas precalculadas en memoria.")
    
    col_cust, col_btn_cust = st.columns([3, 1])
    
    opciones_cust = muestra_clientes + ["-- Ingresar ID Manualmente --"]
    
    with col_cust:
        seleccion_cust = st.selectbox(
            "Seleccione un Cliente Muestra (Customer ID):",
            options=opciones_cust
        )
        
        if seleccion_cust == "-- Ingresar ID Manualmente --":
            customer_input = st.text_input("Ingrese el Customer ID personalizado:", value="06b009f7d0738513a4220706a782e33b")
        else:
            customer_input = seleccion_cust
            st.info(f"🔑 **ID de Cliente Activo:** `{customer_input}`")

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