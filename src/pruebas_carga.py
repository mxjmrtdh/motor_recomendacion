import requests
import time
import sqlite3
import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
LOGS_PATH = os.path.join(BASE_DIR, "logs.csv")
API_URL = "http://127.0.0.1:8000"

def ejecutar_pruebas_estres(num_peticiones=100):
    print(f"=== [DÍA 6: PRUEBAS DE ESTRÉS] Iniciando {num_peticiones} peticiones hacia la API ===")
    
    # Obtener muestra de IDs de productos reales
    if not os.path.exists(DB_PATH):
        print("[ERROR] Base de datos olist.db no encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM products LIMIT 50")
    productos = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not productos:
        print("[ERROR] No se encontraron productos en la base de datos.")
        return

    # Preparar el archivo CSV de logs
    encabezados = ["timestamp", "product_id", "status_code", "latencia_ms", "estrategia"]
    
    with open(LOGS_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(encabezados)

        print(f"[ESTRÉS] Registrando métricas en {LOGS_PATH}...")
        
        for i in range(num_peticiones):
            p_id = productos[i % len(productos)]
            t_inicio = time.time()
            timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            try:
                res = requests.get(f"{API_URL}/recomendar/{p_id}?limite=5", timeout=5)
                latencia = round((time.time() - t_inicio) * 1000, 2)
                
                if res.status_code == 200:
                    data = res.json()
                    estrategia = data.get("estrategia", "DESCONOCIDA")
                    writer.writerow([timestamp_actual, p_id, res.status_code, latencia, estrategia])
                else:
                    writer.writerow([timestamp_actual, p_id, res.status_code, latencia, "ERROR_HTTP"])
            
            except Exception as e:
                latencia = round((time.time() - t_inicio) * 1000, 2)
                writer.writerow([timestamp_actual, p_id, 500, latencia, "FALLO_CONEXION"])

            if (i + 1) % 20 == 0:
                print(f"  -> Completadas {i + 1}/{num_peticiones} peticiones...")

    print(f"\n✅ [ÉXITO] Pruebas de estrés finalizadas. Archivo '{LOGS_PATH}' generado correctamente.")

if __name__ == "__main__":
    ejecutar_pruebas_estres()