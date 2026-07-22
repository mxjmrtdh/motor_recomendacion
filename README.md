# 🛍️ Motor de Recomendación e-Commerce (Dataset Olist)

Sistema de recomendación en tiempo real de alta disponibilidad y baja latencia, construido con arquitectura basada en **Grafos (BFS) + Re-ranking de IA (Árboles de Decisión) + Feature Store en RAM + Monitoreo MLOps**.

---

## 🏛️ Arquitectura del Sistema

El flujo de inferencia opera en un pipeline en cascada diseñado para garantizar respuestas sub-50ms y alta relevancia:

```text
 1. Solicitud HTTP (`product_id`)
         │
         ▼
 2. Algoritmo BFS (Grafos de Co-compra) ──► Genera Candidatos (Nivel 2)
         │                                       │
         │ (Si no hay candidatos)                ▼
         └──► Fallback Cold Start ────────► Re-ranking de IA (.pkl)
              (Popularidad/Categoría)            │
                                                 ▼
 5. Registro en logs.csv ◄──────────── Respuesta JSON + Score IA
 ```

## 🧩 Componentes Principales
 * Engine BFS (motor_bfs.py): Algoritmo de exploración de grafos de 2 niveles cargado en memoria RAM para extraer productos co-comprados
 * Modelo IA Clasificador (modelo_final.pkl): Árbol de decisión optimizado mediante GridSearchCV que asigna un score_relevancia de compra a cada candidato.
 * Feature Store (feature_store.py): Estructura en RAM con HashMap de respuesta $O(1)$ para métricas históricas de clientes.
 * Cold Start Strategy (cold_start.py): Sistema de contingencia por popularidad de categoría ante productos sin historial de ventas.
 * API REST (main.py): Desarrollada en FastAPI con gestión de ciclo de vida asíncrono (lifespan).
 * Dashboard MLOps (app_dashboard.py): Interfaz interactiva construida en Streamlit para pruebas de inferencia en vivo, inspección de logs.csv y métricas de latencia ($P_{95}$).

 ## 🚀 Despliegue Rápido con Docker (Recomendado)
Sigue estos pasos para desplegar la arquitectura completa (API FastAPI + Dashboard Streamlit) en un solo contenedor autónomo.

1. Construir la Imagen de Docker
Abre tu terminal en la raíz del proyecto y ejecuta:  
docker build -t motor-recomendacion-olist .
2. Ejecutar el Contenedor
Arranca el servicio exponiendo los puertos de la API (8000) y del Dashboard (8501):  
docker run -d -p 8000:8000 -p 8501:8501 --name app_olist motor-recomendacion-olist  
¡Listo! Accede a las interfaces desde tu navegador:

* 📊 Dashboard MLOps (Streamlit): http://localhost:8501
* 📖 Documentación Interactiva Swagger (FastAPI): http://localhost:8000/docs

## 💻 Ejecución Local Manual (Sin Docker)
Si prefieres ejecutar el entorno de desarrollo localmente:

1. Crear e Iniciar el Entorno Virtual  
python -m venv venv
* En Windows:  
venv\Scripts\activate
* En Linux/macOS:  
source venv/bin/activate
2. Instalar Dependencias  
pip install -r requirements.txt


3. Iniciar Servicios (2 Terminales)  
* Terminal 1 — API Backend:  
uvicorn src.main:app --reload --port 8000
* Terminal 2 — Dashboard MLOps:  
streamlit run src/app_dashboard.py --server.port 8501

## ⚙️ Pipelines de MLOps y Utilidades
### Pipeline de Re-entrenamiento Automatizado y Data Drift  
Evalúa la desviación de distribuciones de datos (KS-test) y re-entrena el modelo optimizando hiperparámetros:  
python src/pipeline_entrenamiento.py  
### Pruebas de Carga y Estrés (Generación de logs.csv)
Ejecuta solicitudes masivas a la API para registrar latencias de respuesta y evaluar el percentil $P_{95}$:  
python src/pruebas_carga.py

# 📋 Estructura del Repositorio
```text
motor_recomendacion/
├── data/                         # CSVs originales del dataset Olist
│   ├── olist_order_items_dataset.csv
│   ├── olist_orders_dataset.csv
│   └── olist_products_dataset.csv
│
├── models/
│   ├── modelo_final.pkl          # Modelo optimizado por GridSearchCV
│   └── mapeo_categorias.pkl      # Mapeo numérico de categorías
│
├── src/
│   ├── crear_db.py               # Generador de la base de datos SQLite (olist.db)
│   ├── entrenar_ia.py            # Entrenamiento del modelo baseline inicial
│   ├── database.py               # Conector a SQLite
│   ├── feature_store.py          # Feature Store en RAM O(1)
│   ├── motor_bfs.py              # Algoritmo de Grafos de Co-compra
│   ├── cold_start.py             # Respaldo por Popularidad/Categoría
│   ├── pipeline_entrenamiento.py # Pipeline MLOps, GridSearchCV & Data Drift Test
│   ├── main.py                   # API REST en FastAPI
│   ├── app_dashboard.py          # Dashboard MLOps interactivo en Streamlit
│   ├── pruebas_carga.py          # Generador de peticiones de estrés (logs.csv)
│   └── evaluar_sistema.py        # Benchmark global de latencia P95 y disponibilidad
│
├── olist.db                      # Base de datos relacional SQLite
├── Dockerfile                    # Configuración de empaquetado Docker
├── docker-compose.yml            # (Opcional) Orquestación de contenedores
├── entrypoint.sh                 # Script supervisor de servicios (API + UI)
├── requirements.txt              # Dependencias unificadas del proyecto
├── logs.csv                      # Registro histórico de peticiones y latencias
└── README.md                     # Documentación técnica completa
```