{#- Test genérico propio: la expresión se cumple en todas las filas del modelo. -#}
{% test expression_is_true(model, expression) %}
select *
from {{ model }}
where not ({{ expression }})
{% endtest %}
