-- Compuerta de publicación (se ejecuta sobre el candidato). Falla si al agregar se pierde o duplica población: la suma de fexp del hecho debe igualar la de los microdatos.
with micro as (
    select periodo, count(*) as encuestados, sum(factor_expansion) as poblacion
    from {{ ref('stg_enemdu__personas') }}
    group by periodo
),

hecho as (
    select periodo, sum(encuestados) as encuestados, sum(poblacion) as poblacion
    from {{ ref('aud_fct_mercado_laboral') }}
    group by periodo
)

select m.periodo, m.encuestados, h.encuestados as encuestados_hecho, m.poblacion, h.poblacion as poblacion_hecho
from micro m
full outer join hecho h using (periodo)
where m.encuestados is distinct from h.encuestados
   or abs(coalesce(m.poblacion, 0) - coalesce(h.poblacion, 0)) > 0.5
