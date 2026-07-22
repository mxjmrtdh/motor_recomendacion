import sqlite3
import os
import pickle
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import precision_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def reentrenar_pipeline():
    print("=== [MLOPS PIPELINE] Iniciando ciclo de re-entrenamiento automático ===")
    
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            oi.product_id,
            oi.price,
            p.product_category_name,
            COUNT(oi.order_id) OVER(PARTITION BY oi.product_id) as popularidad_producto
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("[ERROR] Base de datos inaccesible.")
        return

    # Preparar mapeo y datos
    df['categoria_codificada'] = df['product_category_name'].astype('category').cat.codes
    umbral_popularidad = df['popularidad_producto'].median()
    df['compro'] = (df['popularidad_producto'] > umbral_popularidad).astype(int)

    # Variables (Sin Data Leakage)
    X = df[['price', 'categoria_codificada']]
    y = df['compro']

    # Entrenar modelo actualizado
    modelo = DecisionTreeClassifier(max_depth=5, random_state=42)
    modelo.fit(X, y)

    # Exportar atomicamente a la carpeta models
    modelo_path = os.path.join(MODELS_DIR, "modelo_final.pkl")
    mapping_path = os.path.join(MODELS_DIR, "mapeo_categorias.pkl")

    with open(modelo_path, "wb") as f:
        pickle.dump(modelo, f)
        
    mapeo_categorias = dict(zip(df['product_category_name'], df['categoria_codificada']))
    with open(mapping_path, "wb") as f:
        pickle.dump(mapeo_categorias, f)

    print(f"=== [MLOPS PIPELINE] Modelo re-entrenado y publicado exitosamente en {MODELS_DIR} ===")

if __name__ == "__main__":
    reentrenar_pipeline()