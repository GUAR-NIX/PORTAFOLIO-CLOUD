# Imagen de la API del modelo de informalidad (Fase 8).
# Construir desde observatorio-laboral-ec/:   docker build -f api/Dockerfile -t observatorio-api .
# Requiere el modelo entrenado en models/informalidad_lgbm.joblib (scripts/entrenar_informalidad.py).
FROM python:3.12-slim

# LightGBM necesita OpenMP en tiempo de ejecución
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MODELO_RUTA=/app/models/informalidad_lgbm.joblib

WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Solo el código que la API necesita y el modelo; nada de datos ni secretos
COPY src/observatorio/__init__.py src/observatorio/api.py src/observatorio/prediccion.py src/observatorio/
COPY models/informalidad_lgbm.joblib models/

# Usuario sin privilegios
RUN useradd --create-home --uid 10001 api
USER api

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud')" || exit 1
CMD ["uvicorn", "observatorio.api:app", "--host", "0.0.0.0", "--port", "8000"]
