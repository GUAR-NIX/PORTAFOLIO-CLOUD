# Guía paso a paso

Registro de lo hecho en cada fase: qué, por qué, problemas encontrados y cómo se resolvieron, con evidencias.
[Volver al README](../README.md)

## Fase 0 · Base (2026-11-23)

- Estructura del repositorio por capas: ingesta (`src/`), transformación (`dbt/`), modelos (`ml/`), servicio
  (`api/`, `app/`), monitorización y BI, documentación.
- Decisiones de arquitectura: ADR-0001 a ADR-0004.
- Configuración solo por variables de entorno (`.env` local, *secrets* en CI); `.env.example` como plantilla.
- PostgreSQL 16 local con Docker, expuesto solo en `127.0.0.1`.
- Datos excluidos de git: se regeneran con la ingesta y se respetan los términos de la fuente.
- Entorno: Python 3.12 en `.venv`; pandas 3.1, dbt-core 1.12.7 + dbt-postgres. `pip check` sin conflictos.
- CI en GitHub Actions: ruff, pytest y `dbt parse` (sin conexión a base de datos ni secretos).
- Verificación local: ruff sin errores, 2/2 tests, `dbt parse` correcto.

**Incidencias**
- *dbt instaló una beta (1.13.0b1)*: `dbt-postgres` no limita la versión de dbt-core. Se fijó
  `dbt-core>=1.10,<1.13` y quedó la estable 1.12.7.
- *Docker Desktop no arranca* («Docker Desktop is unable to start»): la plataforma de virtualización que usa (WSL2) no
  está disponible en este equipo. Para desarrollo se usará PostgreSQL 18 nativo (ya instalado); `docker-compose.yml` se
  mantiene como alternativa documentada.
- *Integración en el portafolio*: el proyecto pasó a ser una carpeta de PORTAFOLIO-CLOUD, con su propio workflow
  (`.github/workflows/observatorio-laboral-ec.yml`) que solo se ejecuta cuando cambia esta carpeta. CI en verde.

## Fase 1 · Comprensión de los datos (2026-11-23)

**Objetivo:** entender los microdatos y demostrar que se calculan igual que el INEC antes de construir nada encima.

1. **Fuentes.** En la página oficial de estadísticas laborales del INEC están, para mayo de 2026, los microdatos en CSV
   (datos abiertos) y en SPSS, el diccionario, la guía de usuario y la **sintaxis oficial** de los indicadores
   ([fuentes.md](datos/fuentes.md)).
2. **Formato.** CSV con `;`, coma decimal y vacíos escritos como un espacio. Tabla de personas: 27.369 registros y
   142 columnas, con el diseño muestral (`upm`, `estrato`) y el factor de expansión (`fexp`).
3. **Definiciones.** Se tradujo a Python la sintaxis SPSS oficial (`00 Indicadores de Mercado Laboral.sps`):
   PET = 15 años o más; PEA = `condact` 1–8; empleo adecuado = 1; subempleo = 2–3; desempleo = 7–8; informalidad =
   empleo con `secemp` = 2 ([diccionario.md](datos/diccionario.md), [`indicadores.py`](../src/observatorio/indicadores.py)).
4. **Etiquetas.** El CSV no trae las etiquetas de los valores; se leyeron del `.sav` oficial con `pyreadstat`.

**Resultado: las tasas oficiales se reproducen** (`scripts/validar_tasas_oficiales.py`):

| Indicador (mayo de 2026) | Calculado | INEC | Diferencia |
|---|---|---|---|
| Tasa de participación global | 65,90 % | 65,9 % | 0,00 |
| Tasa de empleo adecuado | 36,60 % | 36,6 % | 0,00 |
| Tasa de subempleo | 18,32 % | 18,3 % | +0,02 |
| Tasa de desempleo | 3,06 % | 3,1 % | −0,04 |

Las 27.369 personas encuestadas representan a 19,09 millones de habitantes (PET 13,57 millones; PEA 8,94 millones).
La tasa de empleo en el sector informal es del 52,84 % del empleo.

**Incidencias (Fase 1)**
- *Menores de 15 con `condact`*: el código 0 identifica a los menores; el cálculo filtra además por edad (`p03` ≥ 15)
  y hay un test que lo comprueba aunque el dato venga mal marcado.

## Fase 2 · Ingesta automática (2026-11-23)

**Objetivo:** construir la serie histórica mensual de forma reproducible, sin pasos manuales.

1. **Patrón de URLs.** Se probó mes a mes la ruta de los datos abiertos del INEC: el patrón
   `EMPLEO/<año>/<Mes>_<año>/2_BDD_DATOS_ABIERTOS_ENEMDU_<año>_<mm>_CSV.zip` funciona de forma continua desde
   **enero de 2023** (en 2022 el INEC usaba otros nombres). Junio de 2026 aún no está publicado.
2. **Módulo** [`ingesta.py`](../src/observatorio/ingesta.py) (`python -m observatorio.ingesta --desde 2023-01 --hasta 2026-05`):
   - *idempotente*: si un mes ya está descargado y su SHA-256 coincide con el manifiesto, no se descarga otra vez;
   - *verificable*: `data/raw/manifiesto.json` guarda URL, tamaño, SHA-256 y fecha de cada archivo;
   - *robusto*: descarga a un temporal y solo lo acepta si es un ZIP íntegro con la tabla de personas; un 404 se
     registra como «no publicado», no como error;
   - *esquema fijo*: 18 columnas con tipos explícitos (códigos como texto para conservar los ceros a la izquierda);
     si un mes no trae alguna columna, se crea vacía y se avisa.
3. **Tests** con una sesión HTTP falsa (sin depender de Internet): idempotencia, rechazo de una página de error
   servida con código 200, 404, cambio de año, coma decimal, ceros a la izquierda y vacíos.

**Resultado**

| Medida | Valor |
|---|---|
| Meses descargados y procesados | **41** (enero de 2023 a mayo de 2026), 0 errores |
| Tiempo de la primera ejecución | 19 s (57,7 MB) |
| Segunda ejecución | 6 s, **0 descargas** (idempotente) |
| Meses comparados con la cifra oficial del INEC | **5 de 5 coinciden** en las 4 tasas (diferencia 0,0) |

La serie completa (`scripts/serie_indicadores.py`) muestra, por ejemplo, el desempleo entre el 2,6 % y el 4,2 % y la
informalidad entre el 51 % y el 58 % del empleo en estos 41 meses.

**Incidencias**
- *Particiones de Parquet*: se guardó primero cada mes en una carpeta `periodo=AAAAMM` con una columna `periodo`
  dentro del archivo, y pyarrow no podía unir ambas. Se pasó a un archivo por mes (`personas_AAAAMM.parquet`) con
  tipos fijos, para que todos los meses tengan exactamente el mismo esquema.

**Pendiente de la fase:** cargar los Parquet en PostgreSQL (necesita crear la base de datos; ver ADR-0002).
