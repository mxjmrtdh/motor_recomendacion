from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import time
import pickle
import os
import pandas as pd

from src.feature_store import FeatureStoreMemoria
from src.database import obtener_detalle_producto_db
from src.motor_bfs import MotorBFS

# Configuración de rutas para los artefactos de IA
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "modelo_final.pkl")
MAPPING_PATH = os.path.join(BASE_DIR, "models", "mapeo_categorias.pkl")

# Variables globales en memoria RAM
modelo_ia = None
mapeo_categorias = None
feature_store = None
motor_bfs = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestor del ciclo de vida del servidor (MLOps)."""
    global modelo_ia, mapeo_categorias, feature_store, motor_bfs
    
    print("\n=== [MÓDULO MLOPS] Cargando artefactos en el arranque de la API ===")
    
    # 1. Cargar Feature Store
    feature_store = FeatureStoreMemoria()
    
    # 2. Cargar Motor BFS
    motor_bfs = MotorBFS()
    
    # 3. Cargar Modelo de IA (.pkl)
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            modelo_ia = pickle.load(f)
        print("[MLOPS] ¡Modelo clasificador (.pkl) cargado con éxito!")
    else:
        print("[MLOPS WARN] No se encontró modelo_final.pkl")

    # 4. Cargar Mapeo de Categorías (.pkl)
    if os.path.exists(MAPPING_PATH):
        with open(MAPPING_PATH, "rb") as f:
            mapeo_categorias = pickle.load(f)
        print("[MLOPS] ¡Mapeo de categorías (.pkl) cargado con éxito!")
    else:
        print("[MLOPS WARN] No se encontró mapeo_categorias.pkl")
        
    print("=== [MÓDULO MLOPS] Servidor listo para inferencias en tiempo real ===\n")
    yield
    print("[MÓDULO MLOPS] Apagando servicios y liberando memoria...")

app = FastAPI(
    title="Motor de Recomendación de Comercio Electrónico (Olist)",
    description="API MLOps para la generación de recomendaciones en tiempo real.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Endpoints ---

@app.get("/")
def check_health():
    estado_modelos = (modelo_ia is not None) and (mapeo_categorias is not None) and (motor_bfs is not None)
    return {
        "estado": "OK",
        "artefactos_ia_cargados": estado_modelos,
        "mensaje": "Servicio de Recomendación de Olist operando correctamente."
    }

@app.get("/usuario/perfil/{customer_id}")
def obtener_perfil_usuario(customer_id: str):
    inicio = time.time()
    perfil = feature_store.obtener_perfil_usuario(customer_id)
    return {
        "customer_id": customer_id,
        "latencia_ms": round((time.time() - inicio) * 1000, 4),
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

# Endpoint Día 5: Recomendación Real con BFS + Re-ranking de IA
@app.get("/recomendar/{product_id}")
def recomendar_productos(product_id: str, limite: int = 5):
    inicio_tiempo = time.time()

    # PASO 1: Generación de Candidatos vía BFS
    candidatos_ids = motor_bfs.buscar_candidatos_bfs(product_id, max_candidatos=50)

    # Si no hay candidatos por BFS (Cold Start), retornamos lista vacía controlada
    if not candidatos_ids:
        return {
            "producto_origen_id": product_id,
            "estrategia": "SIN_CANDIDATOS_BFS",
            "total_recomendaciones": 0,
            "latencia_ms": round((time.time() - inicio_tiempo) * 1000, 2),
            "recomendaciones": []
        }

    # PASO 2: Obtener atributos de los candidatos desde SQLite
    detalles_candidatos = motor_bfs.obtener_detalles_candidatos(candidatos_ids)

    # PASO 3: Re-ranking con el Modelo de IA (.pkl)
    candidatos_evaluados = []
    
    for item in detalles_candidatos:
        cat_nombre = item["category"]
        # Convertir categoría de texto a código numérico usando mapeo_categorias.pkl
        cat_code = mapeo_categorias.get(cat_nombre, -1)
        
        # Preparar DataFrame de entrada para el modelo
        df_input = pd.DataFrame([{
            'price': item['price'],
            'categoria_codificada': cat_code
        }])

        # Predecir probabilidad/score con la IA
        try:
            # Obtener probabilidad de la clase positiva (compro = 1)
            probabilidades = modelo_ia.predict_proba(df_input)
            score = float(probabilidades[0][1]) if probabilidades.shape[1] > 1 else 0.5
        except Exception:
            score = 0.5  # Fallback neutro en caso de error

        candidatos_evaluados.append({
            "product_id": item["product_id"],
            "category": cat_nombre,
            "price": item["price"],
            "score_relevancia": round(score, 4)
        })

    # PASO 4: Ordenar candidatos por el Score de la IA de mayor a menor
    candidatos_ordenados = sorted(
        candidatos_evaluados, 
        key=lambda x: x["score_relevancia"], 
        reverse=True
    )[:limite]

    latencia_total = round((time.time() - inicio_tiempo) * 1000, 2)

    return {
        "producto_origen_id": product_id,
        "estrategia": "BFS_PLUS_IA_RERANKING",
        "total_recomendaciones": len(candidatos_ordenados),
        "latencia_ms": latencia_total,
        "recomendaciones": candidatos_ordenados
    }