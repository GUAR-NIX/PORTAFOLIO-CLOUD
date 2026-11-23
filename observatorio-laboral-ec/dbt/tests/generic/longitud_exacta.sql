{#- Test genérico propio: todos los valores no nulos tienen exactamente `longitud` caracteres. -#}
{% test longitud_exacta(model, column_name, longitud) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and length({{ column_name }}) <> {{ longitud }}
{% endtest %}
