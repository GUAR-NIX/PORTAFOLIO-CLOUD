"""Calcula la serie mensual de indicadores desde los Parquet procesados y la compara con las cifras oficiales.

Uso: python scripts/serie_indicadores.py
"""

from __future__ import annotations

import sys

import pandas as pd

from observatorio.config import DATOS_PROCESADOS
from observatorio.indicadores import tasas

# Cifras publicadas por el INEC («Estadísticas laborales», indicadores nacionales; % de la PEA salvo la TPG).
OFICIALES = {
    "202505": (65.4, 35.2, 20.9, 4.1),
    "202602": (64.2, 37.1, 17.7, 3.1),
    "202603": (64.4, 32.1, 19.6, 2.9),
    "202604": (65.3, 34.3, 19.5, 3.1),
    "202605": (65.9, 36.6, 18.3, 3.1),
}
CAMPOS = ["tasa_participacion_global", "tasa_empleo_adecuado", "tasa_subempleo", "tasa_desempleo"]


def serie() -> pd.DataFrame:
    df = pd.read_parquet(DATOS_PROCESADOS / "personas")
    filas = []
    for periodo, g in df.groupby("periodo", observed=True):
        filas.append({"periodo": str(periodo), "encuestados": len(g), **tasas(g)})
    return pd.DataFrame(filas).sort_values("periodo").reset_index(drop=True)


def main() -> int:
    s = serie()
    pd.set_option("display.width", 160)
    print(s.round(2).to_string(index=False))
    print("\nComparación con las cifras oficiales (redondeo a un decimal, como publica el INEC):")
    ok = True
    for periodo, oficial in OFICIALES.items():
        fila = s[s["periodo"] == periodo].iloc[0]
        difs = [round(fila[c], 1) - o for c, o in zip(CAMPOS, oficial, strict=True)]
        cumple = all(abs(d) < 0.1 + 1e-9 for d in difs)
        ok &= cumple
        marca = "OK" if cumple else "DIFERENCIA"
        print(f"  {periodo}: " + "  ".join(f"{d:+.1f}" for d in difs) + f"   {marca}")
    total = len(OFICIALES)
    print("\nResultado:", f"{total} de {total} meses coinciden" if ok else "hay diferencias")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
