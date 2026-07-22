import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")

def obtener_populares_por_categoria(categoria: str = None, limite: int = 5) -> list:
    """
    Estrategia de Fallback (Cold Start):
    Devuelve los productos más vendidos de la misma categoría. Si no hay categoría,
    devuelve los productos más populares globales del e-commerce.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if categoria and categoria != "sin_categoria":
        query = """
            SELECT 
                p.product_id,
                p.product_category_name,
                AVG(oi.price) as price,
                COUNT(oi.order_id) as popularidad
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            WHERE p.product_category_name = ?
            GROUP BY p.product_id
            ORDER BY popularidad DESC
            LIMIT ?
        """
        cursor.execute(query, (categoria, limite))
    else:
        query = """
            SELECT 
                p.product_id,
                p.product_category_name,
                AVG(oi.price) as price,
                COUNT(oi.order_id) as popularidad
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id
            ORDER BY popularidad DESC
            LIMIT ?
        """
        cursor.execute(query, (limite,))

    resultados = cursor.fetchall()
    conn.close()

    return [
        {
            "product_id": r[0],
            "category": r[1] or "desconocido",
            "price": round(r[2], 2) if r[2] else 0.0,
            "score_relevancia": 0.5000  # Score base neutro para productos populares
        }
        for r in resultados
    ]