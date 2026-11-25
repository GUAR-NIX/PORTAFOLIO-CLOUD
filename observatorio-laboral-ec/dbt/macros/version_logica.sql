{#-
  Huella del código que calcula el hecho. Si cambia la lógica de staging, de intermediate o del propio hecho, la
  huella cambia y TODOS los periodos se recalculan solos: no hace falta acordarse de --full-refresh.
  Se normalizan los finales de línea: la huella es la misma en Windows y en GitHub Actions.
-#}
{% macro version_logica() -%}
    {%- if execute -%}
        {%- set huellas = [] -%}
        {%- for nombre in ['stg_enemdu__personas', 'int_personas_clasificadas', 'aud_fct_mercado_laboral'] -%}
            {%- do huellas.append(graph.nodes['model.observatorio.' ~ nombre].raw_code | replace('\r\n', '\n') | trim) -%}
        {%- endfor -%}
        {{- local_md5(huellas | join('-')) -}}
    {%- else -%}
        {{- 'sin-ejecutar' -}}
    {%- endif -%}
{%- endmacro %}
