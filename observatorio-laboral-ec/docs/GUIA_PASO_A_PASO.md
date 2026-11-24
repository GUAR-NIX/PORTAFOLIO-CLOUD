# Guía paso a paso

Registro de lo hecho en cada fase: qué, por qué, problemas encontrados y cómo se resolvieron, con evidencias.
[Volver al README](../README.es.md)

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

### Carga en PostgreSQL (Neon)

4. **Base de datos.** Proyecto gratuito en **Neon** (PostgreSQL 18.7, AWS us-east-2), conexión directa (sin
   *pooler*) y SSL obligatorio. Las credenciales viven solo en `.env`, que git ignora.
5. **Cargador** [`carga.py`](../src/observatorio/carga.py) (`python -m observatorio.carga`): esquema `raw`; cada
   periodo se reemplaza en una transacción (borrar + insertar), así que recargar no duplica; `raw.cargas` registra
   periodo, filas y fecha. En PostgreSQL usa **COPY** (carga masiva nativa); en los tests, SQLite en memoria.
6. **Verificación dentro de la base** ([`verificar_carga.py`](../scripts/verificar_carga.py)): volumen, coherencia
   con `raw.cargas`, duplicados y las tasas oficiales calculadas **en SQL**.

| Medida | Valor |
|---|---|
| Filas cargadas | **1.158.484** (41 periodos) en 71 s |
| Duplicados tras recargar un mes | **0** |
| Coherencia con `raw.cargas` | Sí |
| Tasas en SQL frente al INEC (5 meses × 4 tasas) | **20 de 20 iguales** |
| Espacio en Neon | 227 MB de 512 MB gratuitos |

**Incidencias**
- *Límite de parámetros*: el primer intento insertaba bloques de 5.000 filas × 18 columnas (90.000 parámetros) y
  PostgreSQL admite como máximo 65.535 por consulta. La transacción se deshizo sola (nada quedó a medias) y se
  cambió a `COPY`, más rápido y sin ese límite.
- *Espacio*: la tabla cruda ocupa el 44 % de la capa gratuita; las tablas de dbt deberán ser agregadas o vistas.

## Fase 3 · Modelado con dbt (2026-11-23)

**Objetivo:** convertir la tabla cruda en un modelo estrella documentado y probado, del que lean BI, ML y la API.

| Capa | Modelo | Materialización | Qué hace |
|---|---|---|---|
| seeds | `condicion_actividad`, `catalogos`, `provincias`, `tasas_oficiales_inec` | tabla | Etiquetas oficiales (del `.sav`), división territorial y cifras del INEC para el test |
| staging | `stg_enemdu__personas` | vista | Nombres y tipos; código de ciudad de 6 dígitos; códigos especiales del ingreso |
| intermediate | `int_personas_clasificadas` | vista | Indicadores 0/1 de la sintaxis oficial y grupo de edad |
| marts | `fct_mercado_laboral` | tabla | Hecho agregado: mes × sexo × área × provincia × edad × instrucción, con **poblaciones** (no tasas) |
| marts | `indicadores_nacionales`, `dim_periodo`, `dim_provincia` | tabla | Tasas nacionales mensuales y dimensiones |

Ejecución: `.\scripts\dbt.ps1 build` (carga las credenciales de `.env` solo en ese proceso).

**Tests (40, todos en verde):** claves únicas y no nulas, valores aceptados, integridad referencial, longitud del código
de ciudad, identidades contables (PEA = empleo + desempleo; empleo = suma de sus categorías; PET = PEA + PEI) y dos
tests de negocio:
- `assert_poblacion_conservada`: al agregar no se pierde ni se duplica población (suma del factor de expansión igual a
  la de los microdatos, mes a mes);
- `assert_tasas_iguales_al_inec`: las tasas del mart, redondeadas como las publica el INEC, son iguales a las oficiales.

| Medida | Valor |
|---|---|
| `dbt build` | 4 seeds, 6 modelos, 30 tests de datos: 40/40 OK en 40 s |
| Hecho `fct_mercado_laboral` | 73.630 filas, 13 MB (frente a 227 MB de la tabla cruda) |
| Base de datos completa en Neon | 248 MB de 512 MB |

**Decisiones**
- El hecho guarda **poblaciones expandidas y no tasas**: sumar o promediar tasas da resultados incorrectos; con
  poblaciones, cualquier tasa se recalcula bien a cualquier nivel (provincia, sexo, edad…).
- Staging e intermediate son **vistas**: no ocupan espacio en la capa gratuita y reflejan siempre la tabla cruda.

**Incidencias**
- *Ciudad con 5 dígitos*: el INEC publica `ciudad` como número en los 41 meses, y las provincias 01–09 pierden el cero
  inicial (`10150` es Azuay, `010150`, no Imbabura). Se detectó al comparar la distribución de provincias; `upm`, que
  sí conserva los ceros, confirmó la corrección `lpad(ciudad, 6, '0')`. Un test vigila la longitud.
- *Códigos especiales del ingreso*: el `.sav` oficial define `999999` = «No informa» y `-1` = «Gasta más de lo que
  gana» (5.052 casos). Ambos pasan a nulo, y el motivo se guarda en otra columna, para no distorsionar promedios.
- *Doble redondeo*: el mart guardaba las tasas con 2 decimales y el test las redondeaba a 1. En abril de 2026 el
  subempleo real es 19,549 %: 19,55 → 19,6, cuando el INEC publica 19,5. **El propio test lo detectó.** Ahora el mart
  guarda la precisión completa y solo se redondea al mostrar.
- *YAML*: una descripción con «fuente:» sin comillas rompía el archivo; se entrecomilló.

## Fase 4 · Orquestación y calidad (2026-11-23)

**Objetivo:** que el pipeline se ejecute solo, sin intervención, y avise si algo falla.

Workflow [`observatorio-laboral-ec-pipeline.yml`](../../.github/workflows/observatorio-laboral-ec-pipeline.yml):
cada **lunes a las 08:00 de Ecuador** (y bajo demanda con *Run workflow*):

1. **Ingesta** `--hasta actual`: descubre sola los meses que el INEC vaya publicando (los no publicados cuentan
   como «no publicado», no como error).
2. **Carga** `--solo-faltantes`: consulta `raw.cargas` y solo carga los meses nuevos.
3. **`dbt build`**: seeds, modelos y los 40 tests (incluida la comparación con el INEC).
4. **`dbt source freshness`**: aviso si no se carga nada en 45 días y error a los 75 (el INEC publica cada mes).
5. **Resumen** con las tasas de los últimos 6 meses en la página del run.

Si un paso falla, el run queda en rojo y GitHub avisa por correo al dueño del repositorio. Las credenciales de Neon
son *secrets* del repositorio (`NEON_PGHOST`, `NEON_PGDATABASE`, `NEON_PGUSER`, `NEON_PGPASSWORD`); un paso inicial
falla con un mensaje claro si falta alguno.

**Prueba local de la misma secuencia contra Neon:** ingesta 41 meses + 6 no publicados, 0 errores; carga 0 periodos
nuevos (41 ya estaban); `dbt build` 40/40; frescura PASS; resumen generado.

**Primera ejecución en GitHub Actions (run #3, manual): en verde** en 1 min 43 s.

| Paso | Resultado | Tiempo |
|---|---|---|
| Comprobar secrets | OK | 0 s |
| Ingesta de los meses publicados | OK | 35 s |
| Carga en Neon (solo meses nuevos) | OK | 4 s |
| `dbt build` (40 tests) | OK | 25 s |
| Frescura de los datos | OK | 6 s |
| Resumen del run | OK | 2 s |

**Incidencias**
- *Run #1, «Falta el secret NEON_PGHOST»*: los secrets no se habían guardado. El paso de comprobación paró el
  pipeline con un mensaje claro en vez de un error de conexión confuso, que es justo para lo que se añadió.
- *Run #2, «password authentication failed»*: GitHub llegaba a Neon (servidor y usuario correctos), pero el valor
  del secret de la contraseña no coincidía con el que funciona en local. Se actualizó el secret. Las líneas
  «Network is unreachable» del log son ruido: los servidores de GitHub no tienen IPv6 y psycopg prueba después IPv4.
- *Aviso «Node.js 20 is deprecated»*: se actualizaron `actions/checkout` a v5 y `actions/setup-python` a v6, que ya
  funcionan con Node 24.

## Fase 5 · Análisis y BI (2026-11-24)

**Capa para BI.** Vista `marts.bi_mercado_laboral`: el hecho con etiquetas legibles (sexo, área, provincia, región,
nivel de instrucción), con un test que garantiza que ninguna fila queda «Sin dato». Medidas DAX, diseño de las 4
páginas y campos de Looker Studio en [bi/README.md](../bi/README.md).

**Representatividad.** La ENEMDU mensual es representativa a nivel nacional, no por provincia (Morona Santiago: 297
encuestados en mayo de 2026). Las cifras provinciales del tablero acumulan 12 meses.

**Usuario de solo lectura (`bi_lector`).** Power BI y Looker no usan la cuenta dueña. Permisos en
[`permisos_bi.sql`](../scripts/permisos_bi.sql), aplicados y verificados con
[`aplicar_permisos_bi.py`](../scripts/aplicar_permisos_bi.py): 8 de 8 comprobaciones (lee `marts`; no inserta, no
borra, no ve `raw`, no crea objetos, sin atributos de administración ni grupos).

**Incidencia: un usuario «de solo lectura» que podía escribir.** El primer `bi_lector` se creó desde la consola de
Neon. La verificación mostró que podía insertar y ver `raw`: Neon hace miembros de `neon_superuser` a los roles
creados en la consola, y la cuenta dueña no puede quitárselo (`permission denied to revoke role`). Se retiraron los
permisos, se borró el rol y se creó con `CREATE ROLE … LOGIN PASSWORD` desde el SQL Editor, que nace sin privilegios.
La contraseña se generó con `secrets` de Python (28 caracteres) y se guardó fuera del repositorio.

**Informe de Power BI** ([`bi/observatorio_laboral.pbix`](../bi/observatorio_laboral.pbix), exportado a
[PDF](../bi/observatorio_laboral.pdf)). Conexión PostgreSQL a Neon en modo Importar con `bi_lector`; el navegador
solo muestra las tablas de `marts`, lo que confirma los permisos. Se importan `bi_mercado_laboral` e
`indicadores_nacionales`. Cuatro páginas: Resumen, Brechas, Territorio y Calidad (capturas en
[bi/README.md](../bi/README.md)).

- *Error «el nombre ya se usa para una columna»*: una medida llamada `PEA` choca con la columna `pea` (Power BI no
  distingue mayúsculas). Se renombraron a `Total PEA`, `Total PET`, `Total empleo` y `Total encuestados`.
- *Tasas en la tabla de Calidad*: las columnas de `indicadores_nacionales` ya son tasas, así que se quitó la fila de
  totales (sumar tasas no tiene sentido) y se formatearon a 1 decimal, como publica el INEC.
- Comprobación cruzada: la tarjeta «Desempleo último mes» (3,1 %) y la tabla de Calidad dan el mismo valor desde dos
  caminos distintos (medida DAX sobre el hecho y tasa calculada en dbt).

**Tablero público en Data Studio** (antes Looker Studio):
[enlace](https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0). Conector PostgreSQL a Neon con
`bi_lector`, SSL con el certificado raíz *ISRG Root X1* y consulta personalizada sobre `marts.bi_mercado_laboral`;
seis campos calculados (suma ÷ suma), tarjetas, serie mensual y filtros de periodo, sexo y área. Compartido como
«cualquiera con el enlace puede ver» (no listado). Detalles e incidencias en [bi/README.md](../bi/README.md).

- *Error 400 invalid_scope* al autorizar Data Studio desde un navegador integrado: Google solo concede ese permiso
  en navegadores normales; se hizo desde Chrome.
- *«No hay tablas»* al conectar: el conector solo lista el esquema `public`; se usó una consulta personalizada.
- *Serie con picos hasta cero*: la fecha estaba como día; se cambió a «Año-mes».

**Fase 5 cerrada.**

## Fase 6 · ML: probabilidad de informalidad (2026-11-24)

**Pregunta.** Dado el perfil de una persona ocupada, ¿qué probabilidad tiene de trabajar en el sector informal?
Decisiones en [ADR-0005](adr/ADR-0005-modelo-informalidad.md); resultados en la
[ficha del modelo](../reports/modelo_informalidad/README.md).

**Dataset** ([`modelo_informalidad.py`](../src/observatorio/modelo_informalidad.py)). Desde los Parquet mensuales de la
ingesta: ocupados de 15 años o más (`condact` 1-6) con factor de expansión positivo; objetivo `secemp == 2`.
Variables con etiquetas legibles: edad, sexo, estado civil, nivel de instrucción, área, provincia (nombre desde el
seed de dbt), rama de actividad (CIIU) y ocupación. 559.089 filas en 41 meses. **El ingreso no entra**: es
consecuencia de la informalidad y sería una fuga de información.

**Validación temporal.** Entrenamiento ene-2023 → may-2025; validación jun → nov 2025 (parada temprana); prueba
dic-2025 → may-2026, evaluada una sola vez. Una partición aleatoria mezclaría meses y hogares que la encuesta visita
varias veces, y daría métricas optimistas.

**Modelos** ([`entrenar_informalidad.py`](../scripts/entrenar_informalidad.py), ~10 s):

| Modelo (prueba, ponderado) | AUC-ROC | Brier | Log loss |
|---|---|---|---|
| Tasa media (sin modelo) | 0,500 | 0,248 | 0,690 |
| Regresión logística + splines de edad | 0,881 | 0,139 | 0,429 |
| **LightGBM** (602 árboles) | **0,910** | **0,120** | **0,375** |

**Calibración.** La informalidad estimada por mes sigue a la observada (mayo 2026: 52,95 % frente a 52,84 % en los
microdatos), y la curva de calibración está pegada a la diagonal.

**Explicación (SHAP).** Rama de actividad > ocupación > provincia > instrucción > edad > sexo > área > estado
civil. La educación superior y las ocupaciones directivas o administrativas empujan hacia la formalidad; no tener
instrucción, las ocupaciones elementales y la agricultura, hacia la informalidad. La edad tiene forma de U.

**Equidad.** AUC 0,897 en hombres y 0,927 en mujeres; 0,888 urbano y 0,910 rural; en todos los grupos la tasa
estimada queda a menos de 1 punto de la observada.

**Incidencias y aprendizajes**
- *«Hogares como empleadores» con efecto muy negativo*: no es que el trabajo doméstico sea formal; la ENEMDU lo
  clasifica aparte (`secemp = 3`) y por definición no cuenta como sector informal. Queda anotado en la ficha.
- *Aviso de LightGBM 4.7* (`eval_set` obsoleto): se pasó a `eval_X` / `eval_y`.
- *CI*: los tests de métricas necesitan scikit-learn, así que se añadió a `requirements-dev.txt`; LightGBM y SHAP
  viven en `requirements-ml.txt` para que el pipeline semanal no los instale.
- El modelo (`models/*.joblib`, 3,8 MB) no se versiona: se regenera con el script. Sí se versionan métricas y figuras.

## Fase 7 · ML: pronóstico del desempleo (2026-11-24)

**Pregunta.** ¿Cuánto será el desempleo (y la informalidad) en los próximos 3 meses, y con qué incertidumbre?
Decisiones en [ADR-0006](adr/ADR-0006-pronostico-desempleo.md); resultados en
[reports/pronostico](../reports/pronostico/README.md).

**Serie.** 41 meses calculados desde los microdatos con `indicadores.tasas` (la misma función validada contra el
INEC en la Fase 1).

**Backtesting con origen móvil** ([`pronostico.py`](../src/observatorio/pronostico.py)). 12 orígenes: en cada uno el
modelo solo ve los meses anteriores y pronostica 1, 2 y 3 meses. Un test comprueba que cada modelo recibe solo el
pasado (24, 25, 26… meses) y nunca el valor que tiene que predecir.

| Modelo | Desempleo · MAE (pp) | Informalidad · MAE (pp) |
|---|---|---|
| **Media de 3 meses** | **0,242** | **1,392** |
| Último valor | 0,326 | 1,835 |
| Suavizado exponencial | 0,336 | 1,488 |
| SARIMA | 0,380 | 6,168 |
| Mismo mes del año anterior | 0,406 | 1,691 |

**Conclusión honesta.** Gana el modelo más simple. La serie tiene mucho ruido muestral (de 2,69 % en diciembre de
2024 a 3,82 % en enero de 2025) y solo 41 meses: suavizar vale más que modelar estacionalidad. Pronóstico
junio-agosto de 2026: desempleo 3,03 % (intervalo 80 %: 2,58–3,47) e informalidad 54,97 % (52,75–57,18).

**Incidencias y aprendizajes**
- *SARIMA inestable en la informalidad* (MAE 6,2 pp): con pocos datos, un modelo con más parámetros puede ser mucho
  peor que uno ingenuo. Sin backtesting no se habría notado.
- *Intervalos*: se usan los cuantiles de los errores reales del backtest en vez de suponer normalidad; con 12
  errores por horizonte son orientativos y no siempre crecen con el horizonte.
- Holt-Winters con tendencia y estacionalidad se descartó de entrada: con 41 meses, estimar 12 efectos mensuales
  más la tendencia sobreajusta.

## Fase 8 · MLOps: MLflow, API y Docker (2026-11-24)

Decisiones en [ADR-0007](adr/ADR-0007-mlops-api-docker.md); uso de la API en [api/README.md](../api/README.md).

**MLflow.** `entrenar_informalidad.py` registra cada entrenamiento (parámetros, métricas de prueba de los tres
modelos e informe) en `mlruns/mlflow.db`. El modelo se versiona con el último mes de datos: `lgbm-202605`.

**API FastAPI** ([`api.py`](../src/observatorio/api.py)). `/salud`, `/opciones` y `/prediccion`. Comprobado con el
modelo real: una vendedora de 28 años, bachiller, de Guayas → 42 % de probabilidad de informalidad (suben la
provincia, la rama y el sexo; bajan la edad, el área urbana y la instrucción). El mismo perfil como profesional
con educación superior en la enseñanza en Pichincha → 12 %. Una provincia inexistente → 422 con la lista válida.

**Tests** ([`test_api.py`](../tests/test_api.py)). Con un modelo sintético guardado en una carpeta temporal: no
necesitan microdatos. Comprueban respuestas, explicaciones, el orden lógico (rural y educación básica → más
informal) y los errores 422. Total del proyecto: 38 tests.

**Docker** ([`api/Dockerfile`](../api/Dockerfile)). `python:3.12-slim` + `libgomp1` (LightGBM), solo la API y el
modelo, usuario sin privilegios y *healthcheck*. Dependencias mínimas en `requirements-api.txt`.

**CI del modelo** (`.github/workflows/observatorio-laboral-ec-modelo.yml`): ingesta con caché → entrenamiento →
puerta de calidad (AUC ≥ 0,88, mejor que la logística, calibración < 1,5 pp) → tests de la API → `docker build` →
prueba de humo del contenedor con `curl` → modelo e informe como artefacto. No usa secretos.

**Incidencias y aprendizajes**
- *MLflow 3 rechaza el almacén en carpetas* («filesystem tracking backend is in maintenance mode»): se pasó a
  SQLite (`sqlite:///mlruns/mlflow.db`), que además necesita `alembic`.
- *Docker no arranca en este equipo* (sin WSL2): la imagen se construye y prueba en GitHub Actions.
- *SHAP en producción sin `shap`*: LightGBM calcula las contribuciones exactas con `pred_contrib=True`.
- *La API no depende de la configuración de la base de datos*: se separó de `config.py` para que la imagen no
  necesite `python-dotenv` ni conexión a Neon.

## Fase 9 · Producto: app pública (2026-11-24)

**App Streamlit** ([`app/app.py`](../app/app.py), detalle en [app/README.md](../app/README.md)) con tres pestañas:
simulador de informalidad por perfil (probabilidad, comparación con el promedio nacional y gráfico de factores
SHAP), pronóstico a 3 meses con intervalo y tabla del backtesting, y ficha del modelo.

- La lógica de predicción se movió a [`prediccion.py`](../src/observatorio/prediccion.py): la API y la app usan
  exactamente el mismo código (los 38 tests siguen en verde tras el cambio).
- Gráficos con Plotly y la paleta validada para daltonismo (azul observado/baja, naranja pronóstico, rojo sube),
  con *tooltips* y leyenda.
- Probada en el navegador: las tres pestañas cargan; el perfil de ejemplo da 42 % frente al 54 % nacional.
- Para publicarla sin microdatos, se versiona una copia del modelo en `app/modelo/` (4 MB) y la app lee los
  resultados del pronóstico ya versionados en `reports/`.

**Incidencias**
- *Aviso de Streamlit 1.67* (`use_container_width` obsoleto): se cambió a `width="stretch"`.
- *Puntos sobre el área del intervalo*: Plotly añade marcadores por defecto en series cortas; se fijó
  `mode="lines"` en la banda.

**Publicada** en Streamlit Community Cloud: <https://observatorio-laboral-ec.streamlit.app> (repositorio
`GUAR-NIX/PORTAFOLIO-CLOUD`, rama `main`, archivo `observatorio-laboral-ec/app/app.py`, Python 3.12, sin secretos:
la app no se conecta a la base de datos). Primer arranque: unos 2 minutos instalando dependencias.

**Primera ejecución del workflow del modelo en la nube: en verde** (ingesta de 41 meses, entrenamiento, puerta de
calidad, tests de la API, `docker build` y prueba de humo del contenedor).

## Fase 10 · Monitorización de deriva (2026-11-24)

Decisiones en [ADR-0008](adr/ADR-0008-monitoreo-deriva.md); resultados en
[reports/monitoreo](../reports/monitoreo/README.md).

**Qué hace** ([`monitoreo.py`](../src/observatorio/monitoreo.py), [`monitorear_deriva.py`](../scripts/monitorear_deriva.py)):
para cada mes calcula el PSI de cada variable frente al entrenamiento (ponderado por el factor de expansión), el
AUC del modelo y el sesgo de calibración; marca «estable / vigilar / deriva» y «ok / reentrenar». Con
`--resumen-markdown` escribe una tabla para el resumen de GitHub Actions; el pipeline semanal lo ejecuta tras dbt.

**Resultado:** sin deriva en los 12 meses posteriores al entrenamiento (PSI máximo 0,04–0,10, siempre en la
provincia) y AUC entre 0,90 y 0,92.

**Incidencias y aprendizajes**
- *Falsa alarma en abril de 2026*: con la calibración de un solo mes, la diferencia de 1,9 puntos pedía
  reentrenar; marzo y mayo coincidían. Se cambió la regla a la media móvil de 3 meses y se añadió un test que
  comprueba que un mes ruidoso no la dispara.
- *La provincia siempre lidera el PSI*: no es deriva, es la falta de representatividad mensual por provincia
  (la misma razón por la que el tablero acumula 12 meses).
- 45 tests en total (7 nuevos del monitor, incluido uno que simula un cambio de composición urbano/rural y
  comprueba que se detecta como deriva).


## Fase 11 · Publicación (2026-11-24)

- **README del proyecto**: insignias de los tres workflows (CI, pipeline semanal, modelo y API), tabla «En vivo» con
  la app, el tablero, Power BI y la guía, y un resumen en cifras.
- **Arquitectura corregida** para reflejar lo construido: el modelo y el pronóstico leen los Parquet de la ingesta, el
  monitor de deriva es propio (PSI ponderado) y no se usaron datos del Banco Central (se documentó por qué en
  ADR-0001). Se quitaron las carpetas vacías `ml/`, `monitoring/` y `notebooks/` de la estructura inicial.
- **README del portafolio**: el observatorio pasa a proyecto destacado, primero en la tabla, con sus enlaces en vivo.
- **Perfil de GitHub (GUAR-NIX)**: el observatorio aparece como proyecto principal con los enlaces a la app y al
  tablero.

**Resultado final:** 11 fases, 8 ADR, 45 tests de Python, 40 tests de dbt, tres workflows en verde, una app y un
tablero públicos, a coste cero.
