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
