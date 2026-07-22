#!/bin/sh

# 1. Iniciar la API de FastAPI en segundo plano (puerto 8000)
echo "🚀 Iniciando API FastAPI en http://0.0.0.0:8000..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# 2. Esperar 3 segundos para que la API cargue los artefactos en RAM
sleep 3

# 3. Iniciar el Dashboard de Streamlit en primer plano (puerto 8501)
echo "📊 Iniciando Dashboard de Streamlit en http://0.0.0.0:8501..."
streamlit run src/app_dashboard.py --server.port=8501 --server.address=0.0.0.0