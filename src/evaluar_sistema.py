import requests
import time
import sqlite3
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
API_URL = "http://127.0.0.1:8000"

def ejecutar_benchmark_sistema():
    print("=== [DÍA 8: EVALUACIÓN GLOBAL MLOPS] Iniciando pruebas de rendimiento ===")
    
    # 1. Obtener una muestra aleatoria de productos de SQLite para la prueba
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM products LIMIT 50")
    productos_muestra = [row[0] for row in cursor.fetchall()]
    conn.close()

    latencias = []
    estrategias_conteo = {}
    exitos = 0
    fallos = 0

    print(f"[BENCHMARK] Ejecutando 50 peticiones de inferencia sobre la API ({API_URL})...")

    for p_id in productos_muestra:
        t0 = time.time()
        try:
            res = requests.get(f"{API_URL}/recomendar/{p_id}?limite=5", timeout=5)
            latencia = (time.time() - t0) * 1000
            
            if res.status_code == 200:
                exitos += 1
                latencias.append(latencia)
                estrategia = res.json().get("estrategia", "DESCONOCIDA")
                estrategias_conteo[estrategia] = estrategias_conteo.get(estrategia, 0) + 1
            else:
                fallos += 1
        except Exception as e:
            fallos += 1

    # 2. Cálculo de métricas agregadas
    if latencias:
        avg_latencia = np.mean(latencias)
        p95_latencia = np.percentile(latencias, 95)
        p99_latencia = np.percentile(latencias, 99)

        print("\n========================================================")
        print("📊 REPORTE FINAL DE MÉTRICAS MLOPS Y RENDIMIENTO")
        print("========================================================")
        print(f" Total de solicitudes evaluadas : {len(productos_muestra)}")
        print(f" Solicitudes exitosas (HTTP 200) : {exitos}")
        print(f" Solicitudes fallidas            : {fallos}")
        print(f" Tasa de Disponibilidad (Uptime) : {(exitos/len(productos_muestra))*100:.2f}%")
        print("--------------------------------------------------------")
        print(f" Latencia Promedio (Avg)        : {avg_latencia:.2f} ms")
        print(f" Latencia Percentil 95 (P95)    : {p95_latencia:.2f} ms")
        print(f" Latencia Percentil 99 (P99)    : {p99_latencia:.2f} ms")
        print("--------------------------------------------------------")
        print(" Distribution de Estrategias de Recomendación:")
        for est, count in estrategias_conteo.items():
            pct = (count / exitos) * 100
            print(f"   • {est}: {count} ({pct:.1f}%)")
        print("========================================================\n")

if __name__ == "__main__":
    ejecutar_benchmark_sistema()