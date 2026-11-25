-- Sale del hecho publicado (no de los microdatos): solo hay meses que pasaron la auditoría.
{{ compuerta() }}
with meses as (
    select distinct periodo, to_date(periodo || '01', 'YYYYMMDD') as fecha_periodo
    from {{ ref('fct_mercado_laboral') }}
)

select
    periodo,
    fecha_periodo,
    extract(year from fecha_periodo)::int                       as anio,
    extract(month from fecha_periodo)::int                      as mes,
    extract(quarter from fecha_periodo)::int                    as trimestre,
    (array['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre',
           'Noviembre', 'Diciembre'])[extract(month from fecha_periodo)::int] as nombre_mes
from meses
