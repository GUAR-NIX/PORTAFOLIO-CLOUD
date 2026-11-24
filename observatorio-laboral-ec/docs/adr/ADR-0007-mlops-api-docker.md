# ADR-0007 · MLOps: MLflow, API FastAPI en Docker y CI del modelo

**Estado:** aceptada · **Fecha:** 2026-11-24

## Contexto
Un modelo en un notebook no es un producto. Hay que poder reentrenarlo de forma reproducible, saber qué versión
está sirviendo, detectar uno por debajo de los umbrales y exponerlo a otras aplicaciones (la app de la Fase 9).

## Decisión
- **Registro de experimentos con MLflow** (backend SQLite en `mlruns/`, no versionado): parámetros, métricas de
  prueba de los tres modelos e informe completo como artefacto. MLflow 3 ya no admite el almacén en carpetas.
- **Versión del modelo = último mes de datos** (`lgbm-202605`): se lee en `/salud` y en cada respuesta.
- **API con FastAPI** (`src/observatorio/api.py`): `GET /salud`, `GET /opciones`, `POST /prediccion`. Valida las
  categorías contra las que vio el modelo (422 con los valores permitidos) y explica cada predicción con las
  contribuciones nativas de LightGBM (SHAP exacto para árboles) sin instalar `shap` en producción.
- **Imagen Docker mínima** (`api/Dockerfile`): `python:3.12-slim`, solo la API y el modelo, usuario sin
  privilegios, *healthcheck*. Dependencias en `requirements-api.txt`.
- **CI del modelo** (`.github/workflows/observatorio-laboral-ec-modelo.yml`): ingesta desde el INEC (con caché),
  reentrenamiento, **puerta de calidad** (AUC ≥ 0,88, mejor que la regresión logística y calibración a menos de
  1,5 puntos), tests de la API, construcción de la imagen y prueba de humo del contenedor. El modelo y su informe
  se guardan como artefacto del workflow.
- Los tests de la API usan un **modelo sintético**: no necesitan los microdatos y corren en segundos.

## Consecuencias
- Docker no se ejecuta en el equipo de desarrollo (sin WSL2); la imagen se construye y prueba en GitHub Actions.
- El despliegue público de la API (por ejemplo, en Hugging Face Spaces) queda para la Fase 9 junto con la app.
