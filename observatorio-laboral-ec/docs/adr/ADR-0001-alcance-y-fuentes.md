# ADR-0001 · Alcance y fuentes de datos

**Estado:** aceptada · **Fecha:** 2026-11-23

## Contexto
El proyecto debe demostrar, en un solo repositorio, las competencias de ingeniería de datos, ciencia de datos, ML/MLOps
y análisis. Necesita datos reales, públicos, con interés social y con suficiente riqueza (microdatos, no solo agregados).

## Decisión
- Fuente principal: **Encuesta Nacional de Empleo, Desempleo y Subempleo (ENEMDU)** del INEC, a nivel de **microdatos**
  (una fila por persona), con sus **factores de expansión**.
- Fuente complementaria: indicadores macroeconómicos del **Banco Central del Ecuador** (inflación, PIB) para el pronóstico.
- Criterio de calidad: los indicadores calculados deben **reproducir las tasas oficiales publicadas por el INEC** con una
  diferencia menor a 0,1 puntos porcentuales antes de usarse en BI o ML.

## Consecuencias
- Los cálculos deben usar siempre el factor de expansión; una media sin ponderar no es un indicador oficial.
- El formato de los microdatos puede cambiar entre periodos: hacen falta contratos de datos y tests por periodo.
- Los datos no se redistribuyen en el repositorio: se descargan de la fuente con la ingesta (ver `.gitignore`).
