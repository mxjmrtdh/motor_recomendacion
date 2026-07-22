import sqlite3
import os
from collections import deque

# Ruta a nuestra base de datos local
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")

class MotorBFS:
    def __init__(self):
        self.grafo_productos_usuarios = {}
        self.grafo_usuarios_productos = {}
        self.cargar_grafos_en_memoria()

    def cargar_grafos_en_memoria(self):
        """Lee SQLite una sola vez y monta las listas de adyacencia en RAM."""
        print("Cargando estructuras de grafos en memoria RAM desde SQLite...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Consultamos las relaciones directas de órdenes y productos
        query = """
            SELECT o.customer_id, oi.product_id 
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        conn.close()

        # Poblar los diccionarios de adyacencia
        for customer_id, product_id in filas:
            if product_id not in self.grafo_productos_usuarios:
                self.grafo_productos_usuarios[product_id] = set()
            if customer_id not in self.grafo_usuarios_productos:
                self.grafo_usuarios_productos[customer_id] = set()
                
            self.grafo_productos_usuarios[product_id].add(customer_id)
            self.grafo_usuarios_productos[customer_id].add(product_id)
            
        print("¡Grafos cargados con éxito en memoria!")

    def buscar_candidatos_bfs(self, producto_origen_id, max_candidatos=50):
        """
        Ejecuta un BFS de exactamente 2 niveles de profundidad para encontrar
        productos relacionados por patrones de co-compra.
        """
        # Si el producto no existe en el historial, devolvemos lista vacía (Activa Cold Start)
        if producto_origen_id not in self.grafo_productos_usuarios:
            return []

        candidatos = set()
        
        # PASO 1: Obtener todos los usuarios que compraron el producto de origen
        usuarios_nivel_1 = self.grafo_productos_usuarios[producto_origen_id]
        
        # PASO 2: Para cada usuario, obtener los otros productos que compró
        for usuario_id in usuarios_nivel_1:
            productos_nivel_2 = self.grafo_usuarios_productos[usuario_id]
            for prod_id in productos_nivel_2:
                if prod_id != producto_origen_id: # No auto-recomendar el mismo producto
                    candidatos.add(prod_id)
                    if len(candidatos) >= max_candidatos:
                        return list(candidatos)
                        
        return list(candidatos)


# Bloque de prueba local para validar que funcione de inmediato
# if __name__ == "__main__":
#     motor = MotorBFS()
    
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
        
#         # CAMBIO: Buscamos el producto que aparezca más veces (el más vendido)
#         query_bestseller = """
#             SELECT product_id, COUNT(*) as ventas 
#             FROM order_items 
#             GROUP BY product_id 
#             ORDER BY ventas DESC 
#             LIMIT 1;
#         """
#         cursor.execute(query_bestseller)
#         resultado = cursor.fetchone()
#         un_producto_bestseller = resultado[0]
#         ventas = resultado[1]
#         conn.close()
        
#         print(f"\nProbando BFS para el BESTSELLER: {un_producto_bestseller} (Vendió {ventas} veces)")
#         candidatos_encontrados = motor.buscar_candidatos_bfs(un_producto_bestseller)
#         print(f"Número de candidatos co-comprados encontrados: {len(candidatos_encontrados)}")
#         if candidatos_encontrados:
#             print(f"Primeros 3 candidatos: {candidatos_encontrados[:3]}")
            
#     except Exception as e:
#         print(f"Error en la prueba: {e}")

# Bloque de prueba local para validar que funcione de inmediato
if __name__ == "__main__":
    motor = MotorBFS()
    
    # Tomamos un ID de producto real existente en el dataset de Olist para probar
    # Nota: Si el dataset cambia, puedes buscar un ID válido directo en la DB.
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id FROM order_items LIMIT 1;")
        un_producto_real = cursor.fetchone()[0]
        conn.close()
        
        print(f"\nProbando BFS para el producto: {un_producto_real}")
        candidatos_encontrados = motor.buscar_candidatos_bfs(un_producto_real)
        print(f"Número de candidatos co-comprados encontrados: {len(candidatos_encontrados)}")
        if candidatos_encontrados:
            print(f"Primeros 3 candidatos: {candidatos_encontrados[:3]}")
            
    except Exception as e:
        print(f"Error en la prueba: {e}. Asegúrate de haber ejecutado 'crear_db.py' antes.")