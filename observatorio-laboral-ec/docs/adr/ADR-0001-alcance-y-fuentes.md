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

## Actualización (2026-11-24)
Los datos del **Banco Central no se incorporaron**. El backtesting de la Fase 7 ([ADR-0006](ADR-0006-pronostico-desempleo.md))
mostró que, con 41 meses, el mejor pronóstico es la media de los últimos 3 meses: el ruido muestral de la serie
mensual domina, y añadir regresores macroeconómicos no tendría datos suficientes para demostrar una mejora.
Queda como posible extensión cuando la serie sea más larga.
