import sqlite3
import os
import pickle
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def evaluar_data_drift(df_referencia, df_nuevo, umbral_p_value=0.05):
    """
    Simula y evalúa la desviación de datos (Data Drift) entre un conjunto de 
    referencia (histórico) y datos 'nuevos' simulados.
    
    Utiliza la prueba Kolmogorov-Smirnov (KS-test) para la variable continua 'price'.
    """
    print("\n--- [EVALUACIÓN DE DATA DRIFT] ---")
    
    # 1. Simulación de datos "nuevos" con ligera alteración (por ejemplo, inflación o cambio de oferta)
    # Tomamos una muestra y simulamos un incremento del 15% en precios para forzar el análisis de Drift
    df_simulado_nuevo = df_nuevo.copy()
    df_simulado_nuevo['price'] = df_simulado_nuevo['price'] * np.random.uniform(1.10, 1.25, size=len(df_simulado_nuevo))
    
    # 2. Prueba estadística Kolmogorov-Smirnov sobre la feature 'price'
    stat, p_value = ks_2samp(df_referencia['price'], df_simulado_nuevo['price'])
    
    print(f"P-Value de la prueba KS ('price'): {p_value:.6f}")
    
    if p_value < umbral_p_value:
        print("⚠️ [ALERTA DATA DRIFT DETECTADO]: La distribución de precios ha cambiado significativamente.")
        print("   -> Se justifica la ejecución del Re-entrenamiento del modelo.")
        return True
    else:
        print("✅ [SIN DATA DRIFT]: Las distribuciones se mantienen estables.")
        return False

def ejecutar_pipeline_entrenamiento():
    print("=== [MÓDULO MLOPS - DÍA 7] Pipeline de Entrenamiento & Data Drift ===")
    
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

    # Preprocesamiento de variables
    df['categoria_codificada'] = df['product_category_name'].astype('category').cat.codes
    umbral_popularidad = df['popularidad_producto'].median()
    df['compro'] = (df['popularidad_producto'] > umbral_popularidad).astype(int)

    # División simulada: Muestra histórica (80%) vs Muestra "Nueva" entrante (20%)
    df_historico = df.sample(frac=0.8, random_state=42)
    df_nuevo = df.drop(df_historico.index)

    # Evaluar Data Drift
    drift_detectado = evaluar_data_drift(df_historico, df_nuevo)

    # Entrenamiento y Optimización de Hiperparámetros con GridSearch
    X = df[['price', 'categoria_codificada']]
    y = df['compro']

    param_grid = {
        'max_depth': [3, 5, 8, 12],
        'min_samples_split': [2, 5, 10],
        'criterion': ['gini', 'entropy']
    }

    modelo_base = DecisionTreeClassifier(random_state=42)
    
    print("\n[OPTIMIZACIÓN] Ejecutando GridSearchCV para re-entrenar el modelo...")
    grid_search = GridSearchCV(
        estimator=modelo_base, 
        param_grid=param_grid, 
        cv=3, 
        scoring='accuracy', 
        n_jobs=-1
    )
    grid_search.fit(X, y)

    mejor_modelo = grid_search.best_estimator_
    print(f"[ÉXITO] Mejores Hiperparámetros: {grid_search.best_params_}")
    print(f"[MÉTRICA OPTIMIZADA] Mejor Precisión Cross-Validation: {grid_search.best_score_:.4f}")

    # Guardar artefactos (.pkl)
    os.makedirs(MODELS_DIR, exist_ok=True)
    modelo_path = os.path.join(MODELS_DIR, "modelo_final.pkl")
    mapping_path = os.path.join(MODELS_DIR, "mapeo_categorias.pkl")

    with open(modelo_path, "wb") as f:
        pickle.dump(mejor_modelo, f)
        
    mapeo_categorias = dict(zip(df['product_category_name'], df['categoria_codificada']))
    with open(mapping_path, "wb") as f:
        pickle.dump(mapeo_categorias, f)

    print(f"\n=== [MÓDULO MLOPS] Artefactos actualizados exitosamente en {MODELS_DIR} ===")

if __name__ == "__main__":
    ejecutar_pipeline_entrenamiento()