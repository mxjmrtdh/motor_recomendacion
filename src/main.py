from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
from src.feature_store import FeatureStoreMemoria

app = FastAPI(
    title="Motor de Recomendación de Comercio Electrónico (Olist)",
    description="API MLOps para la generación de recomendaciones en tiempo real.",
    version="1.0.0"
)

# Carga global del Feature Store en RAM
feature_store = FeatureStoreMemoria()

@app.get("/")
def check_health():
    return {
        "estado": "OK",
        "mensaje": "Servicio de Recomendación de Olist operando correctamente."
    }

# Endpoint para consultar el perfil en caché (Día 2)
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