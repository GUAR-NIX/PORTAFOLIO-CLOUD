-- Reglas de negocio de la sintaxis oficial del INEC («00 Indicadores de Mercado Laboral.sps»):
-- PET = 15 años o más; PEA = condact 1-8; empleo = 1-6; adecuado = 1; subempleo = 2-3; desempleo = 7-8;
-- PEI = 9; sector informal = empleo con secemp = 2. Cada indicador es 0/1 para poder sumarlo ponderado.
with personas as (
    select * from {{ ref('stg_enemdu__personas') }}
),

clasificadas as (
    select
        *,
        (edad >= 15)                                           as es_pet,
        case
            when edad < 15 then 'Menor de 15'
            when edad < 25 then '15-24'
            when edad < 35 then '25-34'
            when edad < 45 then '35-44'
            when edad < 65 then '45-64'
            else '65 y más'
        end                                                    as grupo_edad
    from personas
)

select
    *,
    case when es_pet then 1 else 0 end                                         as ind_pet,
    case when es_pet and condact between 1 and 8 then 1 else 0 end             as ind_pea,
    case when es_pet and condact between 1 and 6 then 1 else 0 end             as ind_empleo,
    case when es_pet and condact = 1 then 1 else 0 end                         as ind_empleo_adecuado,
    case when es_pet and condact between 2 and 3 then 1 else 0 end             as ind_subempleo,
    case when es_pet and condact = 4 then 1 else 0 end                         as ind_otro_no_pleno,
    case when es_pet and condact = 5 then 1 else 0 end                         as ind_no_remunerado,
    case when es_pet and condact = 6 then 1 else 0 end                         as ind_no_clasificado,
    case when es_pet and condact between 7 and 8 then 1 else 0 end             as ind_desempleo,
    case when es_pet and condact = 9 then 1 else 0 end                         as ind_pei,
    case when es_pet and condact between 1 and 6 and sector_empleo_cod = 2
         then 1 else 0 end                                                     as ind_empleo_informal
from clasificadas
