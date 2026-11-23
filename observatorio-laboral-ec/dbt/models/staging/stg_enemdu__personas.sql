-- Limpieza 1:1 con la fuente: nombres legibles, tipos y códigos normalizados. Sin reglas de negocio.
with fuente as (
    select * from {{ source('raw', 'enemdu_personas') }}
)

select
    periodo,
    to_date(periodo || '01', 'YYYYMMDD')                  as fecha_periodo,
    id_persona,
    id_hogar,
    id_vivienda,
    upm,
    estrato::int                                          as estrato,
    fexp                                                  as factor_expansion,
    -- El INEC publica `ciudad` como número: las provincias 01-09 pierden el cero inicial (10150 = 010150).
    lpad(ciudad, 6, '0')                                  as ciudad_cod,
    left(lpad(ciudad, 6, '0'), 2)                         as provincia_cod,
    area::int                                             as area_cod,
    p02::int                                              as sexo_cod,
    p03::int                                              as edad,
    p06::int                                              as estado_civil_cod,
    nnivins::int                                          as nivel_instruccion_cod,
    condact::int                                          as condact,
    secemp::int                                           as sector_empleo_cod,
    -- Ingreso laboral: códigos especiales del .sav oficial (999999 «No informa», -1 «Gasta más de lo que gana»).
    case when ingrl in (999999, -1) then null else ingrl end as ingreso_laboral,
    case ingrl
        when 999999 then 'no informa'
        when -1 then 'gasta más de lo que gana'
    end                                                   as ingreso_laboral_codigo_especial,
    rama1::int                                            as rama_actividad_cod,
    grupo1::int                                           as grupo_ocupacion_cod
from fuente
