# ADR-0006 · Pronóstico del desempleo con *backtesting*

**Estado:** aceptada · **Fecha:** 2026-11-24

## Contexto
La serie mensual comparable de la ENEMDU empieza en enero de 2023: 41 meses. La tasa de desempleo mensual tiene
mucho ruido muestral (saltos de más de 1 punto de un mes a otro, como de 2,7 % a 3,8 % entre diciembre de 2024 y
enero de 2025); con tan pocos datos, los modelos complejos tienden a sobreajustar ese ruido. Un pronóstico solo es creíble si se demuestra, sin mirar el futuro, que supera a las
referencias ingenuas.

## Decisión
- La serie se calcula desde los microdatos con la metodología oficial (`indicadores.tasas`).
- **Backtesting con origen móvil**: 12 orígenes (último mes visto de marzo de 2025 a febrero de 2026; pronósticos
  de abril de 2025 a mayo de 2026), horizonte de 1 a 3 meses; en cada origen el modelo solo ve el pasado.
- Candidatos: último valor, mismo mes del año anterior, media de 3 meses, suavizado exponencial simple y
  SARIMA(1,0,0)(1,0,0)₁₂. Métrica principal: **MAE en puntos porcentuales**, promedio de los 3 horizontes.
- Se publica el **modelo que gane el backtest**, aunque sea el más simple.
- **Intervalos de predicción empíricos** (cuantil 80 % del error absoluto del backtest por horizonte), sin suponer
  normalidad.

## Consecuencias
- Gana la media de 3 meses (MAE 0,24 pp en desempleo; 26 % mejor que repetir el último valor): con 41 meses, suavizar
  el ruido muestral vale más que modelar estacionalidad. Se revisará cuando haya más historia.
- Los intervalos se estiman con 12 errores por horizonte: son orientativos.
- El modelo se elige y se mide en el mismo backtest, así que el error del ganador es algo optimista: la comprobación
  independiente llegará cuando el INEC publique junio-agosto de 2026.
- SARIMA es inestable en la informalidad (MAE 6,2 pp): por eso no se usa sin compararlo antes.
