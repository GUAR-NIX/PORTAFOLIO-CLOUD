🇪🇸 **Español** · 🇺🇸 [English](README.md)

# 📊 Observatorio laboral del Ecuador · ENEMDU → dbt → ML → Power BI

[![CI](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec.yml/badge.svg)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec.yml)
[![Pipeline semanal](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec-pipeline.yml/badge.svg)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec-pipeline.yml)
[![Modelo y API](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec-modelo.yml/badge.svg)](https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/actions/workflows/observatorio-laboral-ec-modelo.yml)

De los **microdatos de la encuesta de empleo del INEC (ENEMDU)** a un **modelo desplegado públicamente** y un **dashboard público**:
ingesta automatizada, data warehouse con dbt sobre PostgreSQL, indicadores oficiales reproducidos con factores de
expansión, modelos de machine learning explicables, API, app web y monitorización. Coste cero y todo medido.

## 🔗 En vivo

| | Enlace | Qué hay |
|---|---|---|
| 🧮 **App** | **[observatorio-laboral-ec.streamlit.app](https://observatorio-laboral-ec.streamlit.app)** | Simulador de informalidad por perfil, con explicación de cada predicción, y pronóstico a 3 meses |
| 📈 **Tablero** | **[Data Studio](https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0)** | Indicadores mensuales con filtros de periodo, sexo y área, leídos en vivo de PostgreSQL |
| 📄 **Power BI** | [Capturas y PDF](bi/README.md) | Informe de 4 páginas: resumen, brechas, territorio y calidad de los datos |
| 📘 **Guía** | [Paso a paso](docs/GUIA_PASO_A_PASO.md) | Cada fase con sus decisiones, errores y cómo se resolvieron |

## En cifras

| | |
|---|---|
| Datos | 41 meses de microdatos · 1,16 M de registros de personas · 559.089 de ocupados en el modelo |
| Calidad | 20 de 20 tasas oficiales del INEC reproducidas al décimo (5 meses) · 40 tests de dbt · 50 tests de Python |
| Modelo | AUC **0,910** en meses no vistos · tasa estimada a 0,4 puntos de la observada · AUC de 0,89 a 0,93 por sexo y área |
| Pronóstico | Error medio **0,24 puntos** en el desempleo, 26 % mejor que la referencia |
| Operación | Pipeline semanal · CI con puerta de calidad · Docker · monitor de deriva · coste 0 USD |

## Resultados

**Las tasas oficiales del INEC se reproducen desde los microdatos** (mayo de 2026, 27.369 personas encuestadas que
representan a 19,09 millones de habitantes), aplicando la sintaxis oficial y el factor de expansión:

| Indicador | Calculado | INEC | Diferencia |
|---|---|---|---|
| Tasa de participación global | 65,90 % | 65,9 % | 0,00 |
| Tasa de empleo adecuado | 36,60 % | 36,6 % | 0,00 |
| Tasa de subempleo | 18,32 % | 18,3 % | +0,02 |
| Tasa de desempleo | 3,06 % | 3,1 % | −0,04 |

Es la base de todo lo demás: si un indicador no coincide con el oficial, nada construido encima es fiable.

**Serie histórica automatizada:** la ingesta descarga y procesa **41 meses** (enero de 2023 a mayo de 2026) en 19 s;
la segunda ejecución no descarga nada (idempotente, con manifiesto SHA-256). Los **5 meses** con cifra oficial
publicada coinciden en las 4 tasas con diferencia 0,0.

**En la nube:** 1.158.484 filas cargadas en PostgreSQL (Neon) con `COPY` en 71 s, carga idempotente y verificada
dentro de la base: 0 duplicados y las tasas calculadas en SQL iguales a las del INEC (20 de 20).

**Modelo estrella con dbt:** staging → intermediate → marts, con un hecho agregado de 73.630 filas (13 MB) y
**40/40 tests en verde**, entre ellos uno que compara las tasas del mart con las oficiales del INEC. Ese test detectó
un error real de doble redondeo antes de que llegara a ningún dashboard.

**Pipeline automático:** cada lunes, GitHub Actions descarga los meses que el INEC haya publicado, los carga en Neon,
ejecuta `dbt build` con los 40 tests, comprueba la frescura y publica un resumen con las últimas tasas. Primera ejecución en verde en la nube: **1 min 43 s**.
Cálculo: [`indicadores.py`](src/observatorio/indicadores.py) · validación: [`validar_tasas_oficiales.py`](scripts/validar_tasas_oficiales.py) ·
variables: [diccionario](docs/datos/diccionario.md).

**BI:** informe de Power BI de 4 páginas ([capturas y PDF](bi/README.md)) y
**[tablero público en vivo en Data Studio](https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0)**,
ambos con un usuario de base de datos de solo lectura.

**Machine learning · probabilidad de informalidad:** LightGBM sobre 559.089 ocupados (398.378 para entrenar), evaluado en 6 meses
que nunca vio: **AUC 0,910** (regresión logística: 0,881) y **bien calibrado**: en mayo de 2026 estima 52,95 % de
informalidad frente al 52,84 % observado en los microdatos. Con SHAP: la rama de actividad y la ocupación pesan más que
todo lo demás, la educación superior protege y la edad tiene forma de U. No funciona peor para las mujeres ni para el
área rural. → [Ficha del modelo](reports/modelo_informalidad/README.md)

**Pronóstico con backtesting:** 12 orígenes móviles sin mirar el futuro. Gana la media de 3 meses (error de **0,24
puntos** en el desempleo, 26 % mejor que repetir el último valor); SARIMA, más complejo, queda peor. Pronóstico para
junio-agosto de 2026: **3,0 % de desempleo** (intervalo 80 %: 2,6–3,5). → [Resultados](reports/pronostico/README.md)

**MLOps:** el modelo se sirve con una **API FastAPI** que explica cada predicción (los 3 factores que más suben o
bajan la probabilidad), empaquetada en una imagen **Docker** mínima. Un workflow reentrena desde los datos del INEC,
aplica una **puerta de calidad** (falla si el modelo no alcanza los umbrales mínimos), prueba la API y el contenedor;
los experimentos quedan en **MLflow**. → [API](api/README.md)

**Producto y monitorización:** **[app pública en Streamlit](https://observatorio-laboral-ec.streamlit.app)** con
un simulador por perfil y el pronóstico; y un
monitor semanal de deriva (PSI ponderado) y desempeño: **sin deriva** en los 12 meses posteriores al
entrenamiento y AUC entre 0,90 y 0,92. → [Monitor](reports/monitoreo/README.md)

## Arquitectura

```mermaid
flowchart LR
  INEC["INEC · ENEMDU<br/>microdatos"] --> ING["Ingesta Python<br/>Parquet"]
  ING --> PG[("PostgreSQL<br/>Neon")]
  PG --> DBT["dbt<br/>staging → marts<br/>40 tests"]
  DBT --> BI["Power BI<br/>Data Studio"]
  ING --> ML1["LightGBM + SHAP<br/>informalidad"]
  ING --> ML2["Pronóstico<br/>backtesting"]
  ML1 --> MLF["MLflow"]
  ML1 --> API["API FastAPI<br/>Docker"]
  ML1 & ML2 --> APP["App Streamlit<br/>pública"]
  ML1 -.-> MON["Monitor de deriva<br/>PSI ponderado"]
  GHA["GitHub Actions<br/>semanal + CI"] -.-> ING & DBT & MON
```

## Fases

| Fase | Contenido | Estado |
|---|---|---|
| 0 · Base | Estructura, decisiones de arquitectura, entorno, CI | ✅ |
| 1 · Comprensión de los datos | Fuentes, diccionario, factores de expansión, tasas oficiales reproducidas | ✅ |
| 2 · Ingesta | Descarga automática e idempotente de 41 meses; carga en PostgreSQL (Neon) | ✅ |
| 3 · Modelado (dbt) | staging → intermediate → marts (modelo estrella), 40 tests | ✅ |
| 4 · Calidad y orquestación | Pipeline semanal en GitHub Actions: ingesta → carga → dbt → frescura | ✅ |
| 5 · Análisis y BI | KPIs del mercado laboral en Power BI ([informe y capturas](bi/README.md)) y [tablero público en Data Studio](https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0) | ✅ |
| 6 · ML: informalidad | LightGBM explicable (SHAP), validación temporal y equidad · [ficha del modelo](reports/modelo_informalidad/README.md) | ✅ |
| 7 · ML: pronóstico | Desempleo e informalidad a 3 meses con *backtesting* de origen móvil · [resultados](reports/pronostico/README.md) | ✅ |
| 8 · MLOps | MLflow, [API FastAPI](api/README.md) en Docker, CI que reentrena con puerta de calidad | ✅ |
| 9 · Producto | **[App pública](https://observatorio-laboral-ec.streamlit.app)** con simulador por perfil y pronóstico ([detalle](app/README.md)) | ✅ |
| 10 · Monitorización | [PSI ponderado y desempeño mensual](reports/monitoreo/README.md) en el pipeline semanal | ✅ |
| 11 · Publicación | README con enlaces en vivo, guía completa y proyecto destacado en el perfil | ✅ |

## Decisiones técnicas

| ADR | Decisión |
|---|---|
| [0001](docs/adr/ADR-0001-alcance-y-fuentes.md) | Microdatos de la ENEMDU con factores de expansión; validar contra las tasas oficiales del INEC (< 0,1 puntos) |
| [0002](docs/adr/ADR-0002-nube-gratuita.md) | Nube gratuita real: Neon (PostgreSQL), GitHub Actions, Streamlit Community Cloud, MLflow |
| [0003](docs/adr/ADR-0003-dbt-modelo-estrella.md) | dbt en tres capas y modelo estrella; BI y ML solo leen `marts` |
| [0004](docs/adr/ADR-0004-bi-power-bi-y-looker.md) | Power BI (mercado ecuatoriano) + Looker Studio (enlace público) |
| [0005](docs/adr/ADR-0005-modelo-informalidad.md) | Modelo de informalidad: definiciones del INEC, sin ingreso (fuga), validación temporal, pesos de expansión |
| [0006](docs/adr/ADR-0006-pronostico-desempleo.md) | Pronóstico: backtesting de origen móvil contra referencias ingenuas; intervalos empíricos |
| [0007](docs/adr/ADR-0007-mlops-api-docker.md) | MLOps: MLflow, API FastAPI en Docker mínimo y CI que reentrena con puerta de calidad |
| [0008](docs/adr/ADR-0008-monitoreo-deriva.md) | Monitor de deriva: PSI ponderado por el diseño muestral y calibración con media móvil de 3 meses |

## Cómo reproducirlo

```bash
cd observatorio-laboral-ec
python -m venv .venv && source .venv/bin/activate      # en Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env                                   # y ajusta la conexión a PostgreSQL
pytest
python -m observatorio.ingesta --desde 2023-01 --hasta actual   # microdatos (PYTHONPATH=src)
pip install -r requirements-ml.txt && python scripts/entrenar_informalidad.py   # modelo, ~10 s
python scripts/pronosticar_indicadores.py                                       # pronóstico y backtesting
```

## Estructura

```
src/observatorio/   Código Python: indicadores oficiales, ingesta, carga, modelo, pronóstico, monitor, API
scripts/            Validación contra el INEC, entrenamiento, pronóstico, monitor de deriva, permisos de BI
dbt/                Transformaciones SQL (staging → intermediate → marts) y tests de datos
reports/            Fichas, métricas y figuras del modelo, del pronóstico y del monitor
api/  app/          Dockerfile de la API y app pública en Streamlit
bi/                 Informe de Power BI, PDF y capturas
docs/               ADR, fuentes, diccionario de datos y guía paso a paso
tests/              Tests de Python (50)
```

## Fuente de datos y licencia

Código bajo [MIT](LICENSE). Datos: **INEC**, Encuesta Nacional de Empleo, Desempleo y Subempleo (ENEMDU). Conservan
los términos de uso de su publicador y no se redistribuyen en este repositorio: el proyecto los descarga desde la
fuente oficial. El modelo publicado en `app/modelo/` no contiene microdatos, solo los árboles entrenados.
