"""Fase 10 · Monitorización de deriva de datos y del desempeño del modelo, mes a mes.

- **Deriva de datos**: PSI (Population Stability Index) de cada variable frente al periodo de entrenamiento,
  con proporciones ponderadas por el factor de expansión (lo que cambia es la población, no la muestra).
  Reglas habituales: PSI < 0,1 estable · 0,1-0,2 vigilar · > 0,2 deriva.
- **Desempeño**: AUC ponderado y diferencia entre la informalidad estimada y la observada en cada mes.
  Umbrales alineados con la puerta de calidad del CI (ADR-0007): AUC ≥ 0,88 y calibración < 1,5 puntos,
  esta última sobre la media móvil de 3 meses para no confundir ruido muestral con descalibración.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

UMBRAL_VIGILAR, UMBRAL_DERIVA = 0.1, 0.2
AUC_MINIMO, CALIBRACION_MAXIMA_PP = 0.88, 1.5
EPS = 1e-4  # evita log(0) cuando una categoría no aparece en uno de los dos periodos


def psi(referencia: pd.Series, actual: pd.Series) -> float:
    """PSI entre dos distribuciones de proporciones indexadas por categoría (o intervalo)."""
    idx = referencia.index.union(actual.index)
    r = referencia.reindex(idx, fill_value=0).to_numpy(dtype=float) + EPS
    a = actual.reindex(idx, fill_value=0).to_numpy(dtype=float) + EPS
    r, a = r / r.sum(), a / a.sum()
    return float(np.sum((a - r) * np.log(a / r)))


def proporciones(valores: pd.Series, pesos: pd.Series) -> pd.Series:
    """Proporción ponderada de cada valor (categoría o intervalo)."""
    t = pd.Series(pesos.to_numpy(), index=valores.astype("string").fillna("Sin dato").to_numpy())
    return t.groupby(level=0).sum() / t.sum()


def cortes_edad(edad_referencia: pd.Series, n: int = 10) -> np.ndarray:
    """Cortes por deciles de la referencia; los extremos abiertos cubren valores nuevos."""
    q = np.unique(np.quantile(edad_referencia.dropna(), np.linspace(0, 1, n + 1)[1:-1]))
    return np.r_[-np.inf, q, np.inf]


def estado(valor_psi: float) -> str:
    if valor_psi > UMBRAL_DERIVA:
        return "deriva"
    return "vigilar" if valor_psi > UMBRAL_VIGILAR else "estable"


def deriva_por_mes(df: pd.DataFrame, referencia: pd.DataFrame, categoricas: list[str],
                   peso: str = "fexp") -> pd.DataFrame:
    """PSI de cada variable (y la edad por deciles) para cada mes frente a la referencia."""
    cortes = cortes_edad(referencia["edad"])
    ref = {c: proporciones(referencia[c], referencia[peso]) for c in categoricas}
    ref["edad"] = proporciones(pd.cut(referencia["edad"], cortes), referencia[peso])
    filas = []
    for periodo, g in df.groupby("periodo", observed=True):
        fila = {"periodo": str(periodo)}
        for c in categoricas:
            fila[c] = psi(ref[c], proporciones(g[c], g[peso]))
        fila["edad"] = psi(ref["edad"], proporciones(pd.cut(g["edad"], cortes), g[peso]))
        filas.append(fila)
    out = pd.DataFrame(filas).sort_values("periodo").reset_index(drop=True)
    variables = [*categoricas, "edad"]
    out["psi_maximo"] = out[variables].max(axis=1)
    out["variable_mas_derivada"] = out[variables].idxmax(axis=1)
    out["estado_datos"] = out["psi_maximo"].map(estado)
    return out


def alerta_desempeno(auc: float, sesgo_3m_pp: float) -> str:
    """`sesgo_3m_pp`: media móvil de 3 meses de (estimada − observada).

    Un solo mes puede desviarse ~2 puntos por ruido muestral; una desviación sostenida es la que indica que el
    modelo se descalibró."""
    if auc < AUC_MINIMO or abs(sesgo_3m_pp) >= CALIBRACION_MAXIMA_PP:
        return "reentrenar"
    return "ok"


def sesgo_movil(estimada_pct: pd.Series, observada_pct: pd.Series, ventana: int = 3) -> pd.Series:
    return (estimada_pct - observada_pct).rolling(ventana, min_periods=1).mean()
