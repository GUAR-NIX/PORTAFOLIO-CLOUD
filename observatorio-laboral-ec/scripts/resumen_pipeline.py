"""Resumen en Markdown de la última ejecución del pipeline (para el resumen del run en GitHub Actions).

Uso: python scripts/resumen_pipeline.py >> "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

from sqlalchemy import create_engine, text

from observatorio.config import config_bd

ULTIMOS = """
select periodo, encuestados, tasa_participacion_global, tasa_empleo_adecuado, tasa_subempleo, tasa_desempleo,
       tasa_empleo_sector_informal
from marts.indicadores_nacionales order by periodo desc limit 6
"""
CABECERA = ["Periodo", "Encuestados", "Participación", "Empleo adecuado", "Subempleo", "Desempleo",
            "Informalidad"]


def main() -> None:
    with create_engine(config_bd().url).connect() as con:
        filas = con.execute(text(ULTIMOS)).fetchall()
        meses, personas = con.execute(text("select count(*), sum(filas) from raw.cargas")).one()
        ultima = con.execute(text("select max(cargado_utc) from raw.cargas")).scalar()
    print("## 📊 Observatorio laboral del Ecuador · ejecución del pipeline\n")
    print(f"**Datos cargados:** {meses} meses · {personas:,} personas encuestadas · última carga {ultima}\n")
    print("| " + " | ".join(CABECERA) + " |")
    print("|---|" + "---:|" * (len(CABECERA) - 1))
    for periodo, n, *tasas in filas:
        celdas = [f"{periodo[:4]}-{periodo[4:]}", f"{n:,}", *(f"{t:.1f} %" for t in tasas)]
        print("| " + " | ".join(celdas) + " |")
    print("\nTasas sobre la PEA (participación sobre la PET; informalidad sobre el empleo).")
    print("Fuente: INEC, ENEMDU.")


if __name__ == "__main__":
    main()
