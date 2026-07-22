import os
import sqlite3
import pandas as pd

# Configuración de rutas relativas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "olist.db")

def crear_base_de_datos():
    print("=== Iniciando la creación de la Base de Datos SQLite ===")
    
    # 1. Conectar a SQLite (si el archivo no existe, se crea automáticamente)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 2. Cargar los archivos CSV esenciales usando Pandas
        print("Cargando archivos CSV...")
        df_orders = pd.read_csv(os.path.join(DATA_DIR, "olist_orders_dataset.csv"))
        df_items = pd.read_csv(os.path.join(DATA_DIR, "olist_order_items_dataset.csv"))
        df_products = pd.read_csv(os.path.join(DATA_DIR, "olist_products_dataset.csv"))
        
        # 3. Limpieza y filtrado básico para optimizar espacio local
        # Nos quedamos solo con las columnas necesarias para el Grafo y la IA
        df_orders = df_orders[['order_id', 'customer_id']]
        df_items = df_items[['order_id', 'product_id', 'price']]
        df_products = df_products[['product_id', 'product_category_name']]
        
        # Llenar categorías nulas con un valor por defecto para evitar fallos de Cold Start
        df_products['product_category_name'] = df_products['product_category_name'].fillna('sin_categoria')
        
        # 4. Migrar los DataFrames a tablas de SQLite
        print("Migrando datos a tablas SQLite...")
        df_orders.to_sql("orders", conn, if_exists="replace", index=False)
        df_items.to_sql("order_items", conn, if_exists="replace", index=False)
        df_products.to_sql("products", conn, if_exists="replace", index=False)
        
        # 5. CREACIÓN DE ÍNDICES (Crucial para el rendimiento y la latencia del BFS)
        print("Creando índices optimizados para las búsquedas del BFS...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_id ON orders(order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id);")
        
        conn.commit()
        print(f"\n¡Éxito! Base de datos creada y guardada en: {DB_PATH}")
        
        # Verificación rápida imprimiendo el conteo de registros
        cursor.execute("SELECT COUNT(*) FROM order_items;")
        total_items = cursor.fetchone()[0]
        print(f"Total de registros de co-compra listos en producción simulada: {total_items}")
        
    except FileNotFoundError as e:
        print(f"\n[ERROR]: No se encontró alguno de los archivos CSV en la carpeta 'data/'.")
        print(f"Detalle: {e}")
    except Exception as e:
        print(f"\n[ERROR INESPERADO]: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    crear_base_de_datos()