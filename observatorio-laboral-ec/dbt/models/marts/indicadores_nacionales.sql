-- Indicadores nacionales mensuales (en %), calculados desde las poblaciones expandidas del hecho.
-- Las tasas se guardan con toda su precisión: redondear aquí y otra vez al mostrar produce errores de doble
-- redondeo (abril de 2026: subempleo 19,549 % → 19,55 → 19,6, cuando el INEC publica 19,5).
with mes as (
    select
        periodo,
        sum(encuestados)            as encuestados,
        sum(poblacion)              as poblacion,
        sum(pet)                    as pet,
        sum(pea)                    as pea,
        sum(empleo)                 as empleo,
        sum(empleo_adecuado)        as empleo_adecuado,
        sum(subempleo)              as subempleo,
        sum(otro_empleo_no_pleno)   as otro_empleo_no_pleno,
        sum(empleo_no_remunerado)   as empleo_no_remunerado,
        sum(desempleo)              as desempleo,
        sum(empleo_informal)        as empleo_informal,
        sum(ingreso_laboral_total)  as ingreso_laboral_total,
        sum(empleo_con_ingreso)     as empleo_con_ingreso
    from {{ ref('fct_mercado_laboral') }}
    group by periodo
)

select
    m.periodo,
    d.fecha_periodo,
    m.encuestados,
    round(m.poblacion::numeric)                                                as poblacion,
    round(m.pet::numeric)                                                      as pet,
    round(m.pea::numeric)                                                      as pea,
    100 * m.pea / m.pet                                     as tasa_participacion_global,
    100 * m.empleo_adecuado / m.pea                         as tasa_empleo_adecuado,
    100 * m.subempleo / m.pea                               as tasa_subempleo,
    100 * m.otro_empleo_no_pleno / m.pea                    as tasa_otro_empleo_no_pleno,
    100 * m.empleo_no_remunerado / m.pea                    as tasa_empleo_no_remunerado,
    100 * m.desempleo / m.pea                               as tasa_desempleo,
    100 * m.empleo_informal / m.empleo                      as tasa_empleo_sector_informal,
    m.ingreso_laboral_total / m.empleo_con_ingreso          as ingreso_laboral_medio
from mes m
join {{ ref('dim_periodo') }} d using (periodo)
