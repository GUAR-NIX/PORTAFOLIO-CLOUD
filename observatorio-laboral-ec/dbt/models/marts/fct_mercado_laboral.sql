-- Hechos agregados: una fila por mes × sexo × área × provincia × grupo de edad × nivel de instrucción.
-- Guarda poblaciones expandidas (sumas de fexp) y no tasas: así cualquier tasa se recalcula bien a cualquier nivel
-- (sumar tasas daría resultados erróneos). Agregar en vez de copiar personas ahorra espacio en la capa gratuita.
with p as (
    select * from {{ ref('int_personas_clasificadas') }}
)

select
    periodo,
    sexo_cod,
    area_cod,
    provincia_cod,
    grupo_edad,
    nivel_instruccion_cod,
    count(*)                                                        as encuestados,
    sum(factor_expansion)                                           as poblacion,
    sum(factor_expansion * ind_pet)                                 as pet,
    sum(factor_expansion * ind_pea)                                 as pea,
    sum(factor_expansion * ind_empleo)                              as empleo,
    sum(factor_expansion * ind_empleo_adecuado)                     as empleo_adecuado,
    sum(factor_expansion * ind_subempleo)                           as subempleo,
    sum(factor_expansion * ind_otro_no_pleno)                       as otro_empleo_no_pleno,
    sum(factor_expansion * ind_no_remunerado)                       as empleo_no_remunerado,
    sum(factor_expansion * ind_no_clasificado)                      as empleo_no_clasificado,
    sum(factor_expansion * ind_desempleo)                           as desempleo,
    sum(factor_expansion * ind_pei)                                 as pei,
    sum(factor_expansion * ind_empleo_informal)                     as empleo_informal,
    -- Ingreso laboral de las personas con empleo (para promedios ponderados: suma / población con ingreso).
    sum(factor_expansion * ingreso_laboral)
        filter (where ind_empleo = 1 and ingreso_laboral is not null) as ingreso_laboral_total,
    sum(factor_expansion)
        filter (where ind_empleo = 1 and ingreso_laboral is not null) as empleo_con_ingreso
from p
group by 1, 2, 3, 4, 5, 6
