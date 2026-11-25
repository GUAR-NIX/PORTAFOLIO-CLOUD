-- Después de publicar: lo publicado debe ser exactamente el candidato auditado, mes a mes.
with a as (
    select periodo, cargado_utc, version_logica, count(*) as filas, sum(poblacion) as poblacion
    from {{ ref('aud_fct_mercado_laboral') }}
    group by 1, 2, 3
),

f as (
    select periodo, cargado_utc, version_logica, count(*) as filas, sum(poblacion) as poblacion
    from {{ ref('fct_mercado_laboral') }}
    group by 1, 2, 3
)

select periodo, a.filas, f.filas as filas_publicadas
from a
full outer join f using (periodo, cargado_utc, version_logica)
where a.filas is distinct from f.filas
   or abs(coalesce(a.poblacion, 0) - coalesce(f.poblacion, 0)) > 0.5
