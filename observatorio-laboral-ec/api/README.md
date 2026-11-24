# API del modelo de informalidad

Sirve el modelo de la [Fase 6](../reports/modelo_informalidad/README.md). Código:
[`src/observatorio/api.py`](../src/observatorio/api.py) · decisiones: [ADR-0007](../docs/adr/ADR-0007-mlops-api-docker.md).

| Ruta | Qué devuelve |
|---|---|
| `GET /salud` | Estado y versión del modelo (`lgbm-AAAAMM`, último mes de datos) |
| `GET /opciones` | Valores válidos de cada variable |
| `POST /prediccion` | Probabilidad de informalidad y los 3 factores que más la suben y la bajan (SHAP) |
| `GET /docs` | Documentación interactiva (Swagger) |

## Ejemplo
```json
POST /prediccion
{"edad": 28, "sexo": "Mujer", "estado_civil": "Soltero(a)",
 "nivel_instruccion": "Educación media/bachillerato", "area": "Urbana", "provincia": "Guayas",
 "rama": "Comercio", "ocupacion": "Trabajadores de servicios y vendedores"}
```
```json
{"probabilidad_informal": 0.4199, "tasa_nacional_referencia": 0.5422,
 "factores_que_suben": [{"variable": "provincia", "valor": "Guayas", "efecto": 0.329},
                        {"variable": "rama", "valor": "Comercio", "efecto": 0.264},
                        {"variable": "sexo", "valor": "Mujer", "efecto": 0.198}],
 "factores_que_bajan": [{"variable": "edad", "valor": "28", "efecto": -0.297},
                        {"variable": "area", "valor": "Urbana", "efecto": -0.133},
                        {"variable": "nivel_instruccion", "valor": "Educación media/bachillerato", "efecto": -0.126}],
 "version_modelo": "lgbm-202605"}
```
El mismo perfil con educación superior, trabajando como profesional en la enseñanza en Pichincha: **12,4 %**.
Una categoría desconocida (por ejemplo, `"provincia": "Narnia"`) responde **422** con la lista de valores válidos.

## Ejecutar
```powershell
# En local (requiere el modelo: python scripts/entrenar_informalidad.py)
pip install -r requirements-api.txt
$env:PYTHONPATH = "src"; uvicorn observatorio.api:app --reload      # http://127.0.0.1:8000/docs

# Con Docker (desde observatorio-laboral-ec/)
docker build -f api/Dockerfile -t observatorio-api .
docker run -p 8000:8000 observatorio-api
```
La imagen se construye y se prueba en cada cambio del modelo o de la API con el workflow
[`observatorio-laboral-ec-modelo.yml`](../../.github/workflows/observatorio-laboral-ec-modelo.yml).
