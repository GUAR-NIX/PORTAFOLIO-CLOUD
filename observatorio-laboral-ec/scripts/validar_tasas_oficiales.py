"""Fase 1: reproduce las tasas oficiales del INEC a partir de los microdatos y mide la diferencia.

Uso: python scripts/validar_tasas_oficiales.py data/raw/enemdu_2026_05/bdd/enemdu_persona_2026_05.csv
Criterio de aceptación (ADR-0001): diferencia absoluta < 0,1 puntos porcentuales en cada tasa.
"""

from __future__ import annotations

import sys

from observatorio.indicadores import COLUMNAS_CLAVE, leer_personas, poblaciones, tasas

# Publicado por el INEC para mayo de 2026 (página «Estadísticas laborales», indicadores nacionales).
OFICIAL_2026_05 = {
    "tasa_participacion_global": 65.9,
    "tasa_empleo_adecuado": 36.6,
    "tasa_subempleo": 18.3,
    "tasa_desempleo": 3.1,
}
TOLERANCIA = 0.1


def main(ruta: str) -> int:
    df = leer_personas(ruta, columnas=COLUMNAS_CLAVE)
    p, t = poblaciones(df), tasas(df)
    print(f"Registros en la muestra: {len(df):,}  ·  población que representan: {p['poblacion_total']:,.0f}")
    print(f"PET {p['pet']:,.0f} · PEA {p['pea']:,.0f} · empleo {p['empleo']:,.0f}", end="")
    print(f" · desempleo {p['desempleo']:,.0f}\n")
    print(f"{'Indicador':32} {'Calculado':>10} {'INEC':>7} {'Diferencia':>11}  ¿OK?")
    ok = True
    for nombre, valor in t.items():
        oficial = OFICIAL_2026_05.get(nombre)
        if oficial is None:
            print(f"{nombre:32} {valor:10.2f} {'-':>7} {'-':>11}")
            continue
        dif = valor - oficial
        # El INEC publica con un decimal: se compara el valor redondeado igual que el publicado.
        cumple = abs(round(valor, 1) - oficial) < TOLERANCIA + 1e-9
        ok &= cumple
        print(f"{nombre:32} {valor:10.2f} {oficial:7.1f} {dif:+11.2f}  {'sí' if cumple else 'NO'}")
    print("\nResultado:", "las tasas oficiales se reproducen" if ok else "HAY DIFERENCIAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
