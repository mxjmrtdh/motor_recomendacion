import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "olist.db")

class FeatureStoreMemoria:
    """
    Simulación de Feature Store en RAM para la recuperación de perfiles de usuario.
    Permite lecturas en O(1) evitando consultas costosas a disco en tiempo de inferencia.
    """
    def __init__(self):
        self._cache_usuarios = {}
        self.inicializar_cache()

    def inicializar_cache(self):
        print("[FEATURE STORE] Cargando perfiles de usuario en caché RAM...")
        if not os.path.exists(DB_PATH):
            print("[FEATURE STORE WARN] No se encontró olist.db. La caché estará vacía.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Agrupamos el historial del usuario para tener sus variables precalculadas
        query = """
            SELECT 
                o.customer_id,
                COUNT(o.order_id) as total_compras,
                MIN(oi.price) as precio_min,
                MAX(oi.price) as precio_max,
                AVG(oi.price) as ticket_promedio
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.customer_id
        """
        try:
            cursor.execute(query)
            filas = cursor.fetchall()
            for row in filas:
                cust_id, total, p_min, p_max, ticket = row
                self._cache_usuarios[cust_id] = {
                    "total_compras": total,
                    "precio_minimo": round(p_min, 2) if p_min else 0.0,
                    "precio_maximo": round(p_max, 2) if p_max else 0.0,
                    "ticket_promedio": round(ticket, 2) if ticket else 0.0
                }
            print(f"[FEATURE STORE] ¡Éxito! {len(self._cache_usuarios)} perfiles cargados en RAM.")
        except Exception as e:
            print(f"[FEATURE STORE ERROR] Fallo al cargar caché: {e}")
        finally:
            conn.close()

    def obtener_perfil_usuario(self, customer_id: str) -> dict:
        """Recupera en O(1) las características del usuario. Maneja Cold Start si no existe."""
        if customer_id in self._cache_usuarios:
            return self._cache_usuarios[customer_id]
        
        # Perfil por defecto en caso de Usuario Nuevo (Cold Start)
        return {
            "total_compras": 0,
            "precio_minimo": 0.0,
            "precio_maximo": 0.0,
            "ticket_promedio": 0.0,
            "es_usuario_nuevo": True
        }