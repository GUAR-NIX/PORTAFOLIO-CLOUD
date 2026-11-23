# Diccionario de las variables clave (tabla de personas)

Solo las variables que usa el proyecto. Las etiquetas de los valores se tomaron del archivo oficial
`enemdu_persona_2026_05.sav` (versión SPSS de los microdatos), que las incluye; el CSV de datos abiertos no las trae.

| Variable | Descripción | Valores / uso |
|---|---|---|
| `p02` | Sexo | 1 hombre · 2 mujer |
| `p03` | Edad en años cumplidos | PET = 15 años o más |
| `p06` | Estado civil | 1 casado · 2 separado · 3 divorciado · 4 viudo · 5 unión libre · 6 soltero |
| `nnivins` | Nivel de instrucción | 1 ninguno · 2 centro de alfabetización · 3 educación básica · 4 media/bachillerato · 5 superior |
| `area` | Área | 1 urbana · 2 rural |
| `ciudad` | Código de ciudad (DPA) | Los 2 primeros dígitos son la provincia |
| `condact` | **Condición de actividad** | 0 menores de 15 años · 1 empleo adecuado · 2 subempleo por horas · 3 subempleo por ingresos · 4 otro empleo no pleno · 5 empleo no remunerado · 6 empleo no clasificado · 7 desempleo abierto · 8 desempleo oculto · 9 población inactiva |
| `secemp` | **Sector del empleo** | 1 formal · 2 informal · 3 doméstico · 4 no clasificado |
| `ingrl` | Ingreso laboral mensual | Dólares; con códigos especiales que se tratarán en la Fase 3 |
| `rama1`, `grupo1` | Rama de actividad y grupo de ocupación | CIIU / CIUO |
| `fexp` | **Factor de expansión** | Peso de cada persona en la población |
| `upm`, `estrato` | Diseño muestral | Para errores estándar con diseño complejo |
| `periodo` | Periodo | `AAAAMM` |

## Definiciones de los indicadores (sintaxis oficial del INEC)

| Indicador | Numerador | Denominador |
|---|---|---|
| Tasa de participación global | PEA (`condact` 1–8) | PET (`p03` ≥ 15) |
| Tasa de empleo adecuado | `condact` = 1 | PEA |
| Tasa de subempleo | `condact` 2–3 | PEA |
| Tasa de desempleo | `condact` 7–8 | PEA |
| Tasa de empleo en el sector informal | empleo (`condact` 1–6) con `secemp` = 2 | Empleo |

Todas las sumas se ponderan con `fexp`. Implementación: [`src/observatorio/indicadores.py`](../../src/observatorio/indicadores.py).
