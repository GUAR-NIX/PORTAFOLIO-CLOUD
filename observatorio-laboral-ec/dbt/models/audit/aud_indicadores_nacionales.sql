{{ config(materialized='view') }}
-- Tasas candidatas: se comparan con las cifras oficiales del INEC ANTES de publicar.
{{ indicadores_desde_hecho(ref('aud_fct_mercado_laboral')) }}
