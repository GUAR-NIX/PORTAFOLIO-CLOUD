{#-
  Escribir-auditar-publicar: todo modelo de `marts` depende de los modelos auditados y de lo que usan sus tests.
  Con `dbt build`, si un test de error falla aguas arriba, dbt OMITE los modelos que dependen de él: los marts
  publicados se quedan como estaban. Las semillas se listan porque dbt solo encadena un test con un modelo cuando
  todos los padres del test son ancestros de ese modelo.
-#}
{% macro compuerta() -%}
-- publicación condicionada a: {{ ref('aud_fct_mercado_laboral') }}, {{ ref('aud_indicadores_nacionales') }},
--   {{ ref('tasas_oficiales_inec') }}, {{ ref('provincias') }}, {{ ref('catalogos') }}, {{ ref('condicion_actividad') }}
{%- endmacro %}
