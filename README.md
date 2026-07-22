# motor_recomendacion
Este es un proyecto de recomendación de productos considerando MLOps

# Version de python es 3.13.7

# Actualizar pip, setuptools y wheel
python -m pip install --upgrade pip setuptools wheel

# para instalar lo necesario ejecutar, activar el entorno virtual y ejecutar
pip install -r requirements.txt

# Probar el servidor web
uvicorn src.main:app --reload
## para la validación Interactiva (Swagger UI)
## Abre cualquier navegador web (Chrome, Firefox, Edge). Ingresa a esta dirección: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Para probar los candidatos
### aca2eb7d00ea1a7b8ebd4e68314663af

# para correr el proyecto con docker se tiene que ejecutar lo siguiente:
## Construir la imagen
docker build -t motor-recomendacion-olist .

## Ejecutar el contenedor mapeando ambos puertos
docker run -d -p 8000:8000 -p 8501:8501 --name olist_app motor-recomendacion-olist

## las rutas a consultar son
API / Swagger UI: http://localhost:8000/docs
Dashboard Interactivos: http://localhost:8501