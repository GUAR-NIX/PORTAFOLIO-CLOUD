-- Indicadores nacionales mensuales (en %), calculados desde las poblaciones expandidas del hecho.
-- Las tasas se guardan con toda su precisión: redondear aquí y otra vez al mostrar produce errores de doble
-- redondeo (abril de 2026: subempleo 19,549 % → 19,55 → 19,6, cuando el INEC publica 19,5).
{{ compuerta() }}
{{ indicadores_desde_hecho(ref('fct_mercado_laboral')) }}
