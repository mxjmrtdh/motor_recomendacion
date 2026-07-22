import sqlite3
import os
import pickle
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def reentrenar_y_optimizar_pipeline():
    print("=== [MÓDULO MLOPS - DÍA 7] Re-entrenamiento y Optimización de Hiperparámetros ===")
    
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

    # Preparación de variables categóricas y objetivo (Sin Data Leakage)
    df['categoria_codificada'] = df['product_category_name'].astype('category').cat.codes
    umbral_popularidad = df['popularidad_producto'].median()
    df['compro'] = (df['popularidad_producto'] > umbral_popularidad).astype(int)

    X = df[['price', 'categoria_codificada']]
    y = df['compro']

    # 🎯 DÍA 7: Búsqueda de Hiperparámetros Óptimos (Grid Search Cross-Validation)
    param_grid = {
        'max_depth': [3, 5, 8, 12],
        'min_samples_split': [2, 5, 10],
        'criterion': ['gini', 'entropy']
    }

    modelo_base = DecisionTreeClassifier(random_state=42)
    
    print("[OPTIMIZACIÓN] Evaluando combinaciones de hiperparámetros con Cross-Validation...")
    grid_search = GridSearchCV(
        estimator=modelo_base, 
        param_grid=param_grid, 
        cv=3, 
        scoring='accuracy', 
        n_jobs=-1
    )
    grid_search.fit(X, y)

    mejor_modelo = grid_search.best_estimator_
    print(f"[ÉXITO] Mejores Hiperparámetros encontrados: {grid_search.best_params_}")
    print(f"[MÉTRICA OPTIMIZADA] Mejor Precisión (CV): {grid_search.best_score_:.4f}")

    # Exportación atómica de los artefactos
    os.makedirs(MODELS_DIR, exist_ok=True)
    modelo_path = os.path.join(MODELS_DIR, "modelo_final.pkl")
    mapping_path = os.path.join(MODELS_DIR, "mapeo_categorias.pkl")

    with open(modelo_path, "wb") as f:
        pickle.dump(mejor_modelo, f)
        
    mapeo_categorias = dict(zip(df['product_category_name'], df['categoria_codificada']))
    with open(mapping_path, "wb") as f:
        pickle.dump(mapeo_categorias, f)

    print(f"=== [MÓDULO MLOPS] Modelo final optimizado y publicado en {MODELS_DIR} ===\n")

if __name__ == "__main__":
    reentrenar_y_optimizar_pipeline()