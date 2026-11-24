# ADR-0002 · Infraestructura en nube gratuita

**Estado:** aceptada · **Fecha:** 2026-11-23

## Contexto
El portafolio necesita enlaces que se abran en el navegador (sin clonar nada) y una ejecución automática real, con coste
cero y sin riesgo de cargos inesperados.

## Decisión
| Pieza | Servicio | Motivo |
|---|---|---|
| Base de datos (producción) | **Neon** (PostgreSQL gestionado, capa gratuita) | PostgreSQL estándar, compatible con dbt; sin tarjeta |
| Base de datos (desarrollo) | PostgreSQL 16 en **Docker** (`docker-compose.yml`) | Igual que producción y sin depender de Internet |
| Orquestación | **GitHub Actions** programado | Gratis en repositorios públicos; el historial de ejecuciones es evidencia |
| API del modelo y app | **Streamlit Community Cloud** (app publicada); la API se entrega como imagen Docker probada en CI | Enlace público gratuito |
| Experimentos | **MLflow** | Estándar del sector; registro de modelos |

Alternativas descartadas: AWS con capa gratuita (riesgo de cargos y más superficie de configuración) y ejecutarlo en un
laboratorio propio (sin enlace público).

## Consecuencias
- Límite de almacenamiento de la capa gratuita (~0,5 GB): en producción se cargan datos procesados, no todo el crudo.
- Los secretos (cadena de conexión de Neon, tokens) viven en los *secrets* de GitHub y en `.env` local, nunca en git.
