# Fuentes de datos

## ENEMDU · Encuesta Nacional de Empleo, Desempleo y Subempleo (INEC)

Página oficial: <https://www.ecuadorencifras.gob.ec/estadisticas-laborales-enemdu/>

| Archivo (mayo de 2026) | Contenido | Tamaño | SHA-256 (inicio) |
|---|---|---|---|
| `2_BDD_DATOS_ABIERTOS_ENEMDU_2026_05_CSV.zip` | Microdatos en CSV: personas, viviendas y hogares, consumidores; diccionarios y metadatos (.ods) | 1,3 MB | `F6A7D964B3B9` |
| `1_BDD_ENEMDU_2026_05_SPSS.zip` | Los mismos microdatos en SPSS (.sav), **con las etiquetas de los valores** | 4,5 MB | `0FB6D0886374` |
| `202605_Diccionario_de_variables_ENEMDU.zip` | Diccionarios y metadatos de las tres tablas | 0,03 MB | `5A5366883003` |
| `202605_Guia_de_usuario_BDD_ENEMDU.pdf` | Guía de usuario de la base de datos | 4,1 MB | `CFDE9F5EA610` |
| `202102_Sintaxis indicadores_ENEMDU.zip` | Sintaxis SPSS oficial de los indicadores de mercado laboral | 0,01 MB | `F8E19F12EDDE` |

Ruta de descarga: `https://www.ecuadorencifras.gob.ec/documentos/web-inec/EMPLEO/<año>/<Mes>_<año>/…`

### Formato de los CSV
- Separador `;`, **coma decimal** y valores vacíos escritos como un espacio.
- Tabla de personas de mayo de 2026: **27.369 registros, 142 columnas** (11 MB sin comprimir).
- Claves: `id_vivienda`, `id_hogar`, `id_persona`; periodo en `periodo` (`AAAAMM`).
- Diseño muestral: `upm` (unidad primaria de muestreo), `estrato`, `fexp` (factor de expansión).

### Términos de uso
Los datos son públicos y pertenecen al INEC. No se redistribuyen en este repositorio: la ingesta los descarga desde la
fuente oficial.

## Banco Central del Ecuador
Se planteó usar indicadores macroeconómicos (inflación, PIB) en el pronóstico, pero **no se incorporaron**: con 41
meses de serie, el backtesting favorece un modelo simple (ver la actualización de
[ADR-0001](../adr/ADR-0001-alcance-y-fuentes.md)).
