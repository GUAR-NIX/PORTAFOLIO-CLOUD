"""Verifica la carga en PostgreSQL: volumen, coherencia con raw.cargas, duplicados y tasas oficiales en SQL.

Uso: python scripts/verificar_carga.py
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, text

from observatorio.config import config_bd

OFICIALES = {
    "202505": (65.4, 35.2, 20.9, 4.1),
    "202602": (64.2, 37.1, 17.7, 3.1),
    "202603": (64.4, 32.1, 19.6, 2.9),
    "202604": (65.3, 34.3, 19.5, 3.1),
    "202605": (65.9, 36.6, 18.3, 3.1),
}

TASAS_SQL = """
with b as (
  select periodo, fexp, condact from raw.enemdu_personas where p03 >= 15
)
select periodo,
  round((100 * sum(fexp) filter (where condact between 1 and 8) / sum(fexp))::numeric, 1) as tpg,
  round((100 * sum(fexp) filter (where condact = 1)
         / sum(fexp) filter (where condact between 1 and 8))::numeric, 1) as adecuado,
  round((100 * sum(fexp) filter (where condact between 2 and 3)
         / sum(fexp) filter (where condact between 1 and 8))::numeric, 1) as subempleo,
  round((100 * sum(fexp) filter (where condact between 7 and 8)
         / sum(fexp) filter (where condact between 1 and 8))::numeric, 1) as desempleo
from b where periodo = any(:periodos) group by periodo order by periodo
"""


def main() -> int:
    e = create_engine(config_bd().url)
    ok = True
    with e.connect() as con:
        def uno(sql: str, **p):
            return con.execute(text(sql), p).scalar()

        filas = uno("select count(*) from raw.enemdu_personas")
        periodos = uno("select count(distinct periodo) from raw.enemdu_personas")
        control = uno("select sum(filas) from raw.cargas")
        dups = uno("select count(*) - count(distinct (periodo, id_persona)) from raw.enemdu_personas")
        tam = uno("select pg_size_pretty(pg_total_relation_size('raw.enemdu_personas'))")
        print(f"Filas: {filas:,} · periodos: {periodos} · tamaño en la base: {tam}")
        print(f"Coherencia con raw.cargas: {'sí' if control == filas else 'NO'} · duplicados: {dups}")
        ok &= control == filas and dups == 0

        print("\nTasas calculadas en SQL frente a las oficiales del INEC:")
        res = con.execute(text(TASAS_SQL), {"periodos": list(OFICIALES)}).fetchall()
        for periodo, *calc in res:
            oficial = OFICIALES[periodo]
            igual = all(float(c) == o for c, o in zip(calc, oficial, strict=True))
            ok &= igual
            marca = 'OK' if igual else 'DIFERENCIA'
            print(f"  {periodo}: {tuple(float(c) for c in calc)}  INEC {oficial}  {marca}")
    print("\nResultado:", "carga verificada" if ok else "HAY PROBLEMAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
