select provincia_cod, provincia, region
from {{ ref('provincias') }}
