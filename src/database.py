import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")

def obtener_conexion_db():
    """Crea y retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder a los campos por nombre de columna
    return conn

def obtener_detalle_producto_db(product_id: str) -> dict | None:
    """
    Consulta en SQLite la categoría, precio e historial de ventas de un producto.
    Retorna None si el producto no existe en la DB.
    """
    if not os.path.exists(DB_PATH):
        return None

    conn = obtener_conexion_db()
    cursor = conn.cursor()

    query = """
        SELECT 
            p.product_id,
            p.product_category_name,
            AVG(oi.price) as precio_promedio,
            COUNT(oi.order_id) as total_ventas
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        WHERE p.product_id = ?
        GROUP BY p.product_id
    """
    
    try:
        cursor.execute(query, (product_id,))
        fila = cursor.fetchone()
        
        if fila and fila["product_id"]:
            return {
                "product_id": fila["product_id"],
                "category": fila["product_category_name"] or "sin_categoria",
                "price": round(fila["precio_promedio"], 2) if fila["precio_promedio"] else 0.0,
                "total_ventas": fila["total_ventas"]
            }
        return None
    except Exception as e:
        print(f"[DATABASE ERROR] Error al consultar producto {product_id}: {e}")
        return None
    finally:
        conn.close()