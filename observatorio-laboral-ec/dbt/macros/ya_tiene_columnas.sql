{#- true si la relación existe y tiene todas las columnas: permite migrar una tabla antigua sin --full-refresh. -#}
{% macro ya_tiene_columnas(relacion, columnas) -%}
    {%- set existentes = adapter.get_columns_in_relation(relacion) | map(attribute='name') | map('lower') | list -%}
    {%- set ns = namespace(ok=true) -%}
    {%- for c in columnas if c not in existentes -%}{%- set ns.ok = false -%}{%- endfor -%}
    {{- return(ns.ok) -}}
{%- endmacro %}
