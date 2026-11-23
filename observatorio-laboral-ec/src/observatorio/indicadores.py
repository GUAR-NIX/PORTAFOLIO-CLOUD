"""Indicadores del mercado laboral calculados como en la sintaxis oficial del INEC.

Fuente de las definiciones: «00 Indicadores de Mercado Laboral.sps» (INEC, febrero de 2021), basada en la
«Nota metodológica para la medición del empleo en Ecuador». Todos los indicadores usan el factor de expansión
(`fexp`): una media sin ponderar no es un indicador oficial.

Condición de actividad (`condact`):
    1 empleo adecuado · 2 subempleo por horas · 3 subempleo por ingresos · 4 otro empleo no pleno
    5 empleo no remunerado · 6 empleo no clasificado · 7 desempleo abierto · 8 desempleo oculto · 9 inactivo
Sector del empleo (`secemp`): 1 formal · 2 informal · 3 doméstico · 4 no clasificado.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

COLUMNAS_CLAVE = ["p03", "condact", "secemp", "fexp"]


def leer_personas(ruta: str | Path, columnas: list[str] | None = None) -> pd.DataFrame:
    """Lee la tabla de personas de los datos abiertos de la ENEMDU.

    Formato del INEC: CSV con «;», coma decimal y vacíos escritos como un espacio.
    """
    return pd.read_csv(
        ruta,
        sep=";",
        decimal=",",
        na_values=[" ", ""],
        usecols=columnas,
        low_memory=False,
    )


def _suma(peso: pd.Series, mascara: pd.Series) -> float:
    return float(peso[mascara.fillna(False)].sum())


def poblaciones(df: pd.DataFrame) -> dict[str, float]:
    """Poblaciones expandidas (número de personas que representa la muestra)."""
    w = df["fexp"]
    pet = df["p03"] >= 15
    ca = df["condact"].where(pet)          # menores de 15 no tienen condición de actividad
    empleo = ca.between(1, 6)
    return {
        "poblacion_total": float(w.sum()),
        "pet": _suma(w, pet),
        "pea": _suma(w, ca.between(1, 8)),
        "empleo": _suma(w, empleo),
        "empleo_adecuado": _suma(w, ca == 1),
        "subempleo": _suma(w, ca.between(2, 3)),
        "otro_no_pleno": _suma(w, ca == 4),
        "no_remunerado": _suma(w, ca == 5),
        "desempleo": _suma(w, ca.between(7, 8)),
        "pei": _suma(w, ca == 9),
        "empleo_informal": _suma(w, empleo & (df["secemp"] == 2)),
    }


def tasas(df: pd.DataFrame) -> dict[str, float]:
    """Tasas oficiales en porcentaje.

    Participación sobre la PET; empleo, subempleo y desempleo sobre la PEA; informalidad sobre el empleo.
    """
    p = poblaciones(df)
    pea = p["pea"]
    return {
        "tasa_participacion_global": 100 * pea / p["pet"],
        "tasa_empleo_adecuado": 100 * p["empleo_adecuado"] / pea,
        "tasa_subempleo": 100 * p["subempleo"] / pea,
        "tasa_otro_empleo_no_pleno": 100 * p["otro_no_pleno"] / pea,
        "tasa_empleo_no_remunerado": 100 * p["no_remunerado"] / pea,
        "tasa_desempleo": 100 * p["desempleo"] / pea,
        "tasa_empleo_sector_informal": 100 * p["empleo_informal"] / p["empleo"],
    }
