# 1. Imagen base ligera de Python
FROM python:3.10-slim

# 2. Configurar el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar la estructura completa del proyecto al contenedor
COPY . .

# 5. Dar permisos de ejecución al script de inicio
RUN chmod +x entrypoint.sh

# 6. Exponer los puertos de FastAPI (8000) y Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# 7. Ejecutar ambos servicios mediante el script supervisor
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]