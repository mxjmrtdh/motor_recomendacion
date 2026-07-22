import sqlite3
import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import precision_score

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Crear carpeta de modelos si no existe (Trazabilidad MLOps local)
os.makedirs(MODELS_DIR, exist_ok=True)

def preparar_datos_y_entrenar():
    print("=== Iniciando Pipeline de Entrenamiento de IA ===")
    
    # 1. Conectar a la base de datos y extraer variables
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
        print("[ERROR]: La base de datos está vacía. Ejecuta primero 'crear_db.py'.")
        return

    print(f"Datos extraídos: {len(df)} registros para entrenamiento.")

    # 2. Ingeniería de Características Simplificada (Feature Engineering)
    # Convertimos las categorías de texto a números usando codificación por etiquetas (Label Encoding)
    df['categoria_codificada'] = df['product_category_name'].astype('category').cat.codes
    
    # Para entrenar un clasificador, necesitamos una variable objetivo (Target)
    # Simularemos que si el producto tiene una popularidad alta (mayor al promedio), es una compra "exitosa" (1), de lo contrario (0)
    umbral_popularidad = df['popularidad_producto'].median()
    df['compro'] = (df['popularidad_producto'] > umbral_popularidad).astype(int)

    # Definir variables de entrada (X) y variable a predecir (y)
    X = df[['price', 'categoria_codificada']]
    y = df['compro']

    # 3. División de datos (Entrenamiento y Validación)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Entrenamiento del Modelo Clasificador
    print("Entrenando el modelo de Árbol de Decisión...")
    modelo = DecisionTreeClassifier(max_depth=5, random_state=42)
    modelo.fit(X_train, y_train)

    # 5. Evaluación del Desempeño (Métricas de Calidad)
    predicciones = modelo.predict(X_test)
    precision = precision_score(y_test, predicciones, zero_division=0)
    print(f"\n[MÉTRICA DE CALIDAD] Precision del modelo en Validación: {precision:.4f}")

    # 6. MLOps Local: Guardar el modelo v1 y sus metadatos
    modelo_path = os.path.join(MODELS_DIR, "modelo_final.pkl")
    mapping_path = os.path.join(MODELS_DIR, "mapeo_categorias.pkl")
    
    # Guardamos el modelo
    with open(modelo_path, "wb") as f:
        pickle.dump(modelo, f)
        
    # Guardamos el mapeo de categorías para que la API pueda convertir texto a número
    mapeo_categorias = dict(zip(df['product_category_name'], df['categoria_codificada']))
    with open(mapping_path, "wb") as f:
        pickle.dump(mapeo_categorias, f)

    print(f"¡Éxito! Modelo y mapeos exportados a la carpeta: {MODELS_DIR}/")

if __name__ == "__main__":
    preparar_datos_y_entrenar()