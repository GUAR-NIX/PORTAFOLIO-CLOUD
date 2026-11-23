select distinct
    periodo,
    fecha_periodo,
    extract(year from fecha_periodo)::int                       as anio,
    extract(month from fecha_periodo)::int                      as mes,
    extract(quarter from fecha_periodo)::int                    as trimestre,
    (array['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre',
           'Noviembre', 'Diciembre'])[extract(month from fecha_periodo)::int] as nombre_mes
from {{ ref('stg_enemdu__personas') }}
