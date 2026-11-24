# BI · Power BI y Looker Studio

Los dos tableros leen de **`marts.bi_mercado_laboral`** (vista con etiquetas legibles) y de
**`marts.indicadores_nacionales`**, en Neon, con un **usuario de solo lectura** (`bi_lector`).

## Regla de oro: poblaciones, no tasas
La vista trae **poblaciones expandidas** (suma del factor de expansión). Las tasas se calculan siempre como
**suma ÷ suma** dentro de la herramienta. Nunca se promedian tasas: el promedio de tasas de provincias o meses da un
resultado incorrecto.

## Representatividad (importante)
La ENEMDU mensual es representativa **a nivel nacional**. Por provincia, un solo mes tiene muy pocos encuestados
(Morona Santiago: 297 en mayo de 2026), así que **las cifras provinciales se calculan acumulando 12 meses**
(unos 6.000 encuestados por provincia) y el tablero lo indica. Para sexo y área (urbana/rural) basta un mes.

## Medidas DAX (Power BI)

Tabla `bi_mercado_laboral` (importada desde PostgreSQL):

```dax
PEA = SUM ( bi_mercado_laboral[pea] )
PET = SUM ( bi_mercado_laboral[pet] )
Empleo = SUM ( bi_mercado_laboral[empleo] )

Tasa de participación global = DIVIDE ( [PEA], [PET] )
Tasa de empleo adecuado = DIVIDE ( SUM ( bi_mercado_laboral[empleo_adecuado] ), [PEA] )
Tasa de subempleo = DIVIDE ( SUM ( bi_mercado_laboral[subempleo] ), [PEA] )
Tasa de desempleo = DIVIDE ( SUM ( bi_mercado_laboral[desempleo] ), [PEA] )
Tasa de informalidad = DIVIDE ( SUM ( bi_mercado_laboral[empleo_informal] ), [Empleo] )
Ingreso laboral medio = DIVIDE ( SUM ( bi_mercado_laboral[ingreso_laboral_total] ),
                                 SUM ( bi_mercado_laboral[empleo_con_ingreso] ) )
Encuestados = SUM ( bi_mercado_laboral[encuestados] )

-- Último mes con datos y variación interanual (puntos porcentuales)
Último periodo = MAX ( bi_mercado_laboral[fecha] )
Desempleo último mes =
    VAR fin = [Último periodo]
    RETURN CALCULATE ( [Tasa de desempleo], bi_mercado_laboral[fecha] = fin )
Desempleo hace un año =
    VAR fin = [Último periodo]
    RETURN CALCULATE ( [Tasa de desempleo], bi_mercado_laboral[fecha] = EDATE ( fin, -12 ) )
Variación interanual desempleo (pp) = ( [Desempleo último mes] - [Desempleo hace un año] ) * 100

-- Provincias: acumulado de los últimos 12 meses (representatividad)
Informalidad 12 meses =
    VAR fin = [Último periodo]
    RETURN CALCULATE ( [Tasa de informalidad],
        bi_mercado_laboral[fecha] > EDATE ( fin, -12 ), bi_mercado_laboral[fecha] <= fin )
Desempleo 12 meses =
    VAR fin = [Último periodo]
    RETURN CALCULATE ( [Tasa de desempleo],
        bi_mercado_laboral[fecha] > EDATE ( fin, -12 ), bi_mercado_laboral[fecha] <= fin )
```

Formato: las tasas en **Porcentaje con 1 decimal** (como publica el INEC); el ingreso en **Moneda, 0 decimales**.

## Páginas del informe

| Página | Visuales |
|---|---|
| **1 · Resumen** | 4 tarjetas (participación, empleo adecuado, subempleo, desempleo del último mes) con la variación interanual; línea de las 4 tasas en los 41 meses; nota de fuente y fecha de corte |
| **2 · Brechas** | Columnas agrupadas por sexo y por área (desempleo, empleo adecuado, informalidad); ingreso medio por sexo y nivel de instrucción; segmentadores de periodo, región y grupo de edad |
| **3 · Territorio** | Mapa coroplético o barras por provincia con **informalidad 12 meses** y **desempleo 12 meses**; tabla con encuestados acumulados; aviso de representatividad |
| **4 · Calidad de los datos** | Tabla de `indicadores_nacionales` frente a las cifras oficiales del INEC; encuestados por mes; texto: «40 tests de dbt en cada ejecución del pipeline» |

## Looker Studio (versión pública)
Fuente de datos: conector **PostgreSQL** → host de Neon, base `neondb`, usuario `bi_lector`, **SSL activado**, tabla
`marts.bi_mercado_laboral`. Campos calculados:

```
Tasa de desempleo      = SUM(desempleo) / SUM(pea)
Tasa de empleo adecuado = SUM(empleo_adecuado) / SUM(pea)
Tasa de subempleo      = SUM(subempleo) / SUM(pea)
Tasa de informalidad   = SUM(empleo_informal) / SUM(empleo)
Tasa de participación  = SUM(pea) / SUM(pet)
```
Tipo: **Porcentaje**. Una página con tarjetas, serie temporal y filtros de sexo, área y región.
