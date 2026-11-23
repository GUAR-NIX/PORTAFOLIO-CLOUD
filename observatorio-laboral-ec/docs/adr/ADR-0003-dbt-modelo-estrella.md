# ADR-0003 · Transformación con dbt y modelo estrella

**Estado:** aceptada · **Fecha:** 2026-11-23

## Contexto
Los microdatos llegan con nombres de variables codificados y cambian entre periodos. Los consumidores (BI, ML, API)
necesitan tablas estables, documentadas y probadas.

## Decisión
- **dbt** sobre PostgreSQL, en tres capas:
  - `staging`: limpieza y renombrado 1:1 con la fuente;
  - `intermediate`: armonización entre periodos y reglas de clasificación (condición de actividad, informalidad);
  - `marts`: **modelo estrella**, con hechos de la persona encuestada y dimensiones de tiempo, territorio y persona.
- Cada modelo lleva **tests** (claves, valores aceptados, rangos) y descripción; la documentación de dbt se publica.

## Consecuencias
- Las reglas de negocio (qué es «empleo adecuado», «informal») quedan escritas en SQL versionado y revisable.
- BI y ML leen solo de `marts`: si cambia la fuente, solo se toca `staging`.
