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

**Incidencias**
- *Menores de 15 con `condact`*: el código 0 identifica a los menores; el cálculo filtra además por edad (`p03` ≥ 15)
  y hay un test que lo comprueba aunque el dato venga mal marcado.
