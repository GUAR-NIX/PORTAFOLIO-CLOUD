-- Compuerta de publicación (se ejecuta sobre el candidato). Falla si alguna tasa, redondeada a un decimal como publica el INEC, difiere de la cifra oficial.
select
    o.periodo,
    i.tasa_participacion_global, o.tasa_participacion_global as oficial_tpg,
    i.tasa_empleo_adecuado,      o.tasa_empleo_adecuado      as oficial_adecuado,
    i.tasa_subempleo,            o.tasa_subempleo            as oficial_subempleo,
    i.tasa_desempleo,            o.tasa_desempleo            as oficial_desempleo
from {{ ref('tasas_oficiales_inec') }} o
left join {{ ref('aud_indicadores_nacionales') }} i using (periodo)
where i.periodo is null
   or round(i.tasa_participacion_global::numeric, 1) <> o.tasa_participacion_global::numeric
   or round(i.tasa_empleo_adecuado::numeric, 1)      <> o.tasa_empleo_adecuado::numeric
   or round(i.tasa_subempleo::numeric, 1)            <> o.tasa_subempleo::numeric
   or round(i.tasa_desempleo::numeric, 1)            <> o.tasa_desempleo::numeric
