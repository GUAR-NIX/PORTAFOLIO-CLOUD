# ADR-0009 · dbt incremental y publicación auditada (escribir-auditar-publicar)

**Estado:** aceptada · **Fecha:** 2026-11-24

## Contexto
Cada ejecución reconstruía los marts completos y los probaba **después** de reemplazarlos. `dbt build` terminaba en rojo
si algo fallaba, pero la tabla mala ya estaba publicada y los tableros la leían. Además, recalcular los 41 meses para
añadir uno no escala.

## Decisión
- **Capa `audit`**: `aud_fct_mercado_laboral` (candidato del hecho) y `aud_indicadores_nacionales` (tasas candidatas). Los
  tests de contenido, la población conservada y la comparación con el INEC se ejecutan aquí.
- **Compuerta**: todos los modelos de `marts` dependen de la capa `audit` (macro `compuerta`). Si un test de error falla,
  `dbt build` **omite** los marts y lo publicado queda como estaba. El candidato rechazado se conserva para investigarlo.
- **Incremental por periodo** (`delete+insert`). Un mes se recalcula si es nuevo, si se volvió a cargar (`cargado_utc`) o si
  cambió la lógica (`version_logica`, huella del código de staging, intermediate y el hecho).
- **Migración sin recarga**: si la tabla publicada es la antigua, sin esas columnas, se reescribe entera una vez.
- `raw.cargas.cargado_utc` guarda microsegundos: con segundos, dos cargas seguidas podían confundirse.

## Alternativas consideradas
- **Filtro por el último periodo** (`periodo > max(periodo)`): más simple, pero no detecta que el INEC revise un mes.
- **`--full-refresh` manual al cambiar la lógica**: depende de acordarse.
- **Esquema azul/verde con renombrado**: publicación atómica de todo, pero obliga a rehacer permisos y vistas.
- **Instantáneas o ramas de la base (Neon)**: válido, pero ata la solución al proveedor.

## Consecuencias
- Medido con los datos reales (1.158.484 filas, PostgreSQL 18 local, mediana de 3): construir el candidato pasa de 3,58 s
  (completo) a 0,91 s (un mes) y 0,16 s (sin cambios). `dbt build` completo: 7,0 s, 4,1 s y 3,4 s. **El tiempo total lo dominan
  los tests**, que siguen leyendo toda la tabla cruda; el ahorro importa más cuando haya más meses. La ganancia principal es
  de seguridad, no de velocidad.
- Resultado idéntico al anterior: 0 filas de diferencia en el hecho, la dimensión de tiempo y los indicadores.
- La capa `audit` ocupa 18 MB más. `bi_lector` no puede verla.
- **Límite**: cada tabla se publica en su transacción, no todas a la vez. Durante un instante el hecho puede estar más al día
  que los indicadores.
- **Límite**: las semillas y las dimensiones pequeñas se reconstruyen en cada ejecución.
- 8 pruebas de integración en CI, sobre PostgreSQL y con datos sintéticos, comprueban la compuerta y el incremental.
