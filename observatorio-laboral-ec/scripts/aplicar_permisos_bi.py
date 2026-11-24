"""Aplica scripts/permisos_bi.sql con la cuenta dueña y verifica que `bi_lector` sea de solo lectura.

Uso: python scripts/aplicar_permisos_bi.py
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, text

from observatorio.config import RAIZ, config_bd

VERIFICAR = """
select
  has_table_privilege('bi_lector', 'marts.bi_mercado_laboral', 'SELECT')        as lee_bi_mercado_laboral,
  has_table_privilege('bi_lector', 'marts.indicadores_nacionales', 'SELECT')    as lee_indicadores_nacionales,
  not has_table_privilege('bi_lector', 'marts.fct_mercado_laboral', 'INSERT')   as no_puede_insertar,
  not has_table_privilege('bi_lector', 'marts.fct_mercado_laboral', 'DELETE')   as no_puede_borrar,
  not has_schema_privilege('bi_lector', 'raw', 'USAGE')                         as no_ve_raw,
  not has_schema_privilege('bi_lector', 'marts', 'CREATE')                      as no_crea_en_marts,
  (select not (rolsuper or rolcreatedb or rolcreaterole or rolbypassrls)
     from pg_roles where rolname = 'bi_lector')                                 as sin_atributos_admin,
  (select count(*) = 0 from pg_auth_members where member = 'bi_lector'::regrole) as sin_grupos
"""


def main() -> int:
    sql = (RAIZ / "scripts" / "permisos_bi.sql").read_text(encoding="utf-8")
    sin_comentarios = "\n".join(linea for linea in sql.splitlines() if not linea.strip().startswith("--"))
    sentencias = [s.strip() for s in sin_comentarios.split(";") if s.strip()]
    e = create_engine(config_bd().url)
    with e.begin() as con:
        for s in sentencias:
            con.execute(text(s))
    print(f"{len(sentencias)} sentencias aplicadas\n")
    with e.connect() as con:
        r = con.execute(text(VERIFICAR)).mappings().one()
    for k, v in r.items():
        print(f"  {'OK ' if v else 'MAL'} {k}")
    ok = all(r.values())
    print("\nResultado:", "bi_lector es de solo lectura sobre marts" if ok else "REVISAR PERMISOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
