from fastapi import FastAPI, HTTPException
import time

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="Motor de Recomendación de Comercio Electrónico (Olist)",
    description="API MLOps para la generación de recomendaciones en tiempo real combinando BFS y IA.",
    version="1.0.0"
)

# Endpoint de salud del sistema (Health Check)
@app.get("/")
def check_health():
    return {
        "estado": "OK",
        "mensaje": "Servicio de Recomendación de Olist operando correctamente.",
        "version": "1.0.0"
    }

# Endpoint MOCK (Contrato de Interfaz del Día 1)
@app.get("/recomendar/{product_id}")
def recomendar_productos_mock(product_id: str, limite: int = 5):
    """
    Simulación de la respuesta de recomendación (Mock) para validar el contrato.
    Recibe el ID de un producto consultado y devuelve una lista ficticia.
    """
    inicio_tiempo = time.time()
    
    # Respuesta simulada (Estructura acordada con el equipo)
    recomendaciones_simuladas = [
        {"product_id": f"prod_simulado_{i}", "score_relevancia": round(0.95 - (i * 0.1), 2), "price": 49.90 + (i * 10)}
        for i in range(1, limite + 1)
    ]
    
    latencia_ms = round((time.time() - inicio_tiempo) * 1000, 2)
    
    return {
        "producto_origen_id": product_id,
        "metodo": "MOCK_PRUEBA_DIA_1",
        "total_recomendaciones": len(recomendaciones_simuladas),
        "latencia_ms": latencia_ms,
        "recomendaciones": recomendaciones_simuladas
    }