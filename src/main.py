from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import time
import pickle
import os

from src.feature_store import FeatureStoreMemoria
from src.database import obtener_detalle_producto_db

# Configuración de rutas para los artefactos de IA
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_final.pkl")
MAPPING_PATH = os.path.join(BASE_DIR, "models", "mapeo_categorias.pkl")

# Variables globales donde residirán los artefactos en RAM
modelo_ia = None
mapeo_categorias = None
feature_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor del ciclo de vida del servidor (MLOps).
    Carga los modelos e infraestructura en memoria RAM antes de recibir peticiones.
    """
    global modelo_ia, mapeo_categorias, feature_store
    
    print("\n=== [MÓDULO MLOPS] Cargando artefactos en el arranque de la API ===")
    
    # 1. Cargar Feature Store
    feature_store = FeatureStoreMemoria()
    
    # 2. Cargar Modelo de IA (.pkl)
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            modelo_ia = pickle.load(f)
        print("[MLOPS] ¡Modelo clasificador (.pkl) cargado con éxito en RAM!")
    else:
        print("[MLOPS WARN] No se encontró modelo_final.pkl en models/")

    # 3. Cargar Mapeo de Categorías (.pkl)
    if os.path.exists(MAPPING_PATH):
        with open(MAPPING_PATH, "rb") as f:
            mapeo_categorias = pickle.load(f)
        print("[MLOPS] ¡Mapeo de categorías (.pkl) cargado con éxito en RAM!")
    else:
        print("[MLOPS WARN] No se encontró mapeo_categorias.pkl en models/")
        
    print("=== [MÓDULO MLOPS] Servidor listo para inferencias en tiempo real ===\n")
    
    yield  # El servidor se mantiene ejecutando y respondiendo peticiones
    
    # Limpieza al apagar el servidor si fuera necesario
    print("[MÓDULO MLOPS] Apagando servicios y liberando memoria...")

# Inicialización de la aplicación
app = FastAPI(
    title="Motor de Recomendación de Comercio Electrónico (Olist)",
    description="API MLOps para la generación de recomendaciones en tiempo real.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Endpoints del Día 1, 2 y 3 ---

@app.get("/")
def check_health():
    # Verificamos si los artefactos de IA están cargados correctamente
    estado_modelos = (modelo_ia is not None) and (mapeo_categorias is not None)
    return {
        "estado": "OK",
        "artefactos_ia_cargados": estado_modelos,
        "mensaje": "Servicio de Recomendación de Olist operando correctamente."
    }

@app.get("/usuario/perfil/{customer_id}")
def obtener_perfil_usuario(customer_id: str):
    inicio = time.time()
    perfil = feature_store.obtener_perfil_usuario(customer_id)
    latencia_ms = round((time.time() - inicio) * 1000, 4)
    return {
        "customer_id": customer_id,
        "latencia_ms": latencia_ms,
        "perfil_features": perfil
    }

@app.get("/producto/{product_id}")
def obtener_producto(product_id: str):
    inicio = time.time()
    detalle = obtener_detalle_producto_db(product_id)
    if not detalle:
        raise HTTPException(
            status_code=404, 
            detail=f"El producto con ID '{product_id}' no existe en la base de datos."
        )
    detalle["latencia_ms"] = round((time.time() - inicio) * 1000, 2)
    return detalle

# Endpoint MOCK (Aún no integrado con el motor real, corresponde al Día 5)
@app.get("/recomendar/{product_id}")
def recomendar_productos_mock(product_id: str, limite: int = 5):
    inicio = time.time()
    recomendaciones_simuladas = [
        {"product_id": f"prod_simulado_{i}", "score_relevancia": round(0.95 - (i * 0.1), 2)}
        for i in range(1, limite + 1)
    ]
    return {
        "producto_origen_id": product_id,
        "total_recomendaciones": len(recomendaciones_simuladas),
        "latencia_ms": round((time.time() - inicio) * 1000, 2),
        "recomendaciones": recomendaciones_simuladas
    }