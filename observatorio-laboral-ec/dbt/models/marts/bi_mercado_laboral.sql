{{ config(materialized='view') }}
-- Vista para BI (Power BI y Looker Studio): el hecho con etiquetas legibles en lugar de códigos.
-- Es una vista (0 bytes): las herramientas de BI agregan las poblaciones y calculan las tasas con sus medidas.
with f as (
    select * from {{ ref('fct_mercado_laboral') }}
),

cat as (
    select variable, codigo, etiqueta from {{ ref('catalogos') }}
)

select
    f.periodo,
    p.fecha_periodo                                  as fecha,
    p.anio,
    p.mes,
    p.nombre_mes,
    coalesce(sx.etiqueta, 'Sin dato')                as sexo,
    coalesce(ar.etiqueta, 'Sin dato')                as area,
    coalesce(pr.provincia, 'Sin dato')               as provincia,
    coalesce(pr.region, 'Sin dato')                  as region,
    f.grupo_edad,
    coalesce(ni.etiqueta, 'Sin dato')                as nivel_instruccion,
    f.encuestados,
    f.poblacion,
    f.pet,
    f.pea,
    f.empleo,
    f.empleo_adecuado,
    f.subempleo,
    f.otro_empleo_no_pleno,
    f.empleo_no_remunerado,
    f.empleo_no_clasificado,
    f.desempleo,
    f.pei,
    f.empleo_informal,
    f.ingreso_laboral_total,
    f.empleo_con_ingreso
from f
join {{ ref('dim_periodo') }} p using (periodo)
left join {{ ref('dim_provincia') }} pr using (provincia_cod)
left join cat sx on sx.variable = 'sexo' and sx.codigo = f.sexo_cod
left join cat ar on ar.variable = 'area' and ar.codigo = f.area_cod
left join cat ni on ni.variable = 'nivel_instruccion' and ni.codigo = f.nivel_instruccion_cod
