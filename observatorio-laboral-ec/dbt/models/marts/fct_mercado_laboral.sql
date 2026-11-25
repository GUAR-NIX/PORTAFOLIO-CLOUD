{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='periodo',
    on_schema_change='append_new_columns'
) }}
-- Hecho publicado: copia del candidato ya auditado (models/audit). Solo cambian los periodos recalculados, en una
-- transacción: quien esté leyendo ve la versión anterior o la nueva, nunca una mezcla.
{{ compuerta() }}
select a.*
from {{ ref('aud_fct_mercado_laboral') }} a
{% if is_incremental() and ya_tiene_columnas(this, ['cargado_utc', 'version_logica']) %}
where a.periodo in (
    select c.periodo
    from (select distinct periodo, cargado_utc, version_logica from {{ ref('aud_fct_mercado_laboral') }}) c
    where not exists (
        select 1 from {{ this }} t
        where t.periodo = c.periodo and t.cargado_utc = c.cargado_utc and t.version_logica = c.version_logica
    )
)
{% endif %}
