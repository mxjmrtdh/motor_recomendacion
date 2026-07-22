from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

from src.feature_store import FeatureStoreMemoria
from src.database import obtener_detalle_producto_db

app = FastAPI(
    title="Motor de Recomendación de Comercio Electrónico (Olist)",
    description="API MLOps para la generación de recomendaciones en tiempo real.",
    version="1.0.0"
)

# Carga global del Feature Store
feature_store = FeatureStoreMemoria()

# --- Esquemas Pydantic (Validación y Contrato) ---
class ProductoResponse(BaseModel):
    product_id: str
    category: str
    price: float
    total_ventas: int
    latencia_ms: float

# --- Endpoints ---

@app.get("/")
def check_health():
    return {
        "estado": "OK",
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

# Endpoint Día 3: Consulta Directa a SQLite
@app.get("/producto/{product_id}", response_model=ProductoResponse)
def obtener_producto(product_id: str):
    inicio = time.time()
    detalle = obtener_detalle_producto_db(product_id)
    
    if not detalle:
        raise HTTPException(
            status_code=404, 
            detail=f"El producto con ID '{product_id}' no existe en la base de datos."
        )
    
    latencia_ms = round((time.time() - inicio) * 1000, 2)
    detalle["latencia_ms"] = latencia_ms
    return detalle

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