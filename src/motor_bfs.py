import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")

class MotorBFS:
    def __init__(self):
        self.grafo_productos_usuarios = {}
        self.grafo_usuarios_productos = {}
        self.cargar_grafos_en_memoria()

    def cargar_grafos_en_memoria(self):
        """Lee SQLite una sola vez al levantar el sistema y monta las listas de adyacencia en RAM."""
        print("[MÓDULO BFS] Cargando estructuras de grafos en memoria RAM...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT o.customer_id, oi.product_id 
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        conn.close()

        for customer_id, product_id in filas:
            if product_id not in self.grafo_productos_usuarios:
                self.grafo_productos_usuarios[product_id] = set()
            if customer_id not in self.grafo_usuarios_productos:
                self.grafo_usuarios_productos[customer_id] = set()
                
            self.grafo_productos_usuarios[product_id].add(customer_id)
            self.grafo_usuarios_productos[customer_id].add(product_id)
            
        print("[MÓDULO BFS] ¡Grafos cargados con éxito en memoria!")

    def buscar_candidatos_bfs(self, producto_origen_id, max_candidatos=50):
        """
        Ejecuta un BFS de exactamente 2 niveles de profundidad para encontrar
        productos relacionados por patrones de co-compra.
        """
        if producto_origen_id not in self.grafo_productos_usuarios:
            return []

        candidatos = set()
        usuarios_nivel_1 = self.grafo_productos_usuarios[producto_origen_id]
        
        for usuario_id in usuarios_nivel_1:
            productos_nivel_2 = self.grafo_usuarios_productos[usuario_id]
            for prod_id in productos_nivel_2:
                if prod_id != producto_origen_id:
                    candidatos.add(prod_id)
                    if len(candidatos) >= max_candidatos:
                        return list(candidatos)
                        
        return list(candidatos)

    def obtener_detalles_candidatos(self, lista_product_ids):
        """
        Dado un listado de IDs, consulta en SQLite sus precios y categorías.
        Esto facilita el formateo de las características para la API y la IA.
        """
        if not lista_product_ids:
            return []

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(lista_product_ids))
        query = f"""
            SELECT oi.product_id, oi.price, p.product_category_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.product_id IN ({placeholders})
            GROUP BY oi.product_id
        """
        cursor.execute(query, lista_product_ids)
        resultados = cursor.fetchall()
        conn.close()
        
        return [
            {"product_id": r[0], "price": r[1], "category": r[2]}
            for r in resultados
        ]