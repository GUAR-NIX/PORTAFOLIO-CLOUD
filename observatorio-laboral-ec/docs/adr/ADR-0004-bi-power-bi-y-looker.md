# ADR-0004 · BI con Power BI y Looker Studio

**Estado:** aceptada · **Fecha:** 2026-11-23

## Contexto
Power BI es la herramienta de BI más pedida en las ofertas de analista en Ecuador, pero «Publicar en la web» exige una
cuenta laboral o educativa. El portafolio necesita además un enlace público que se abra sin instalar nada.

## Decisión
- **Power BI Desktop**: informe principal (modelo de datos, medidas DAX, páginas por tema). Se versiona el `.pbix` y se
  publica un PDF con capturas.
- **Looker Studio**: versión pública del tablero, conectada a las tablas `marts`.
- Ambos usan las mismas definiciones de KPI que dbt (una sola fuente de verdad).

## Consecuencias
- Hay que mantener dos tableros: se limitan a los KPI principales para que no diverjan.
