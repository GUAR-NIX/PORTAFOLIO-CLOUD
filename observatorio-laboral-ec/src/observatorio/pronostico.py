"""Fase 7 · Pronóstico de indicadores mensuales (desempleo e informalidad) con *backtesting*.

Decisiones (detalle en docs/adr/ADR-0006-pronostico-desempleo.md):
- La serie sale de los microdatos con la metodología oficial (`indicadores.tasas`), no de cifras copiadas.
- Evaluación con **origen móvil**: en cada origen el modelo solo ve los meses anteriores y pronostica 1..H
  meses adelante. Nunca se usa información del futuro.
- Siempre se compara contra referencias ingenuas (último valor, mismo mes del año anterior): un modelo que no
  las supera no aporta nada.
- Intervalos de predicción **empíricos**: cuantiles de los errores absolutos del backtest para cada horizonte,
  en lugar de suponer errores normales.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable

import numpy as np
import pandas as pd

Modelo = Callable[[np.ndarray, int], np.ndarray]


def ingenuo(y: np.ndarray, h: int) -> np.ndarray:
    """Último valor observado."""
    return np.repeat(y[-1], h)


def estacional_ingenuo(y: np.ndarray, h: int, m: int = 12) -> np.ndarray:
    """Mismo mes del año anterior."""
    return np.array([y[len(y) - m + (i % m)] for i in range(h)])


def media_movil(y: np.ndarray, h: int, k: int = 3) -> np.ndarray:
    """Media de los últimos k meses."""
    return np.repeat(y[-k:].mean(), h)


def ets(y: np.ndarray, h: int) -> np.ndarray:
    """Suavizado exponencial simple (nivel); con pocos datos, tendencia y estacionalidad sobreajustan."""
    from statsmodels.tsa.holtwinters import SimpleExpSmoothing

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.asarray(SimpleExpSmoothing(y, initialization_method="estimated").fit().forecast(h))


def sarima(y: np.ndarray, h: int) -> np.ndarray:
    """SARIMA(1,0,0)(1,0,0)12 con constante: memoria de corto plazo y del mismo mes del año anterior."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo = SARIMAX(y, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12), trend="c",
                         enforce_stationarity=True)
        return np.asarray(modelo.fit(disp=False).forecast(h))


MODELOS: dict[str, Modelo] = {
    "ingenuo": ingenuo,
    "estacional_ingenuo": estacional_ingenuo,
    "media_movil_3": media_movil,
    "ets": ets,
    "sarima": sarima,
}


def backtest(
    y: pd.Series, modelos: dict[str, Modelo], horizonte: int = 3, origenes: int = 12
) -> pd.DataFrame:
    """Origen móvil: para cada uno de los últimos `origenes` cortes, ajusta con el pasado y pronostica.

    Devuelve una fila por (modelo, origen, horizonte) con el pronóstico, el valor real y el error.
    """
    valores = y.to_numpy(dtype=float)
    n = len(valores)
    primer_corte = n - origenes - horizonte + 1
    if primer_corte < 13:
        raise ValueError("Serie demasiado corta para el backtest pedido")
    filas = []
    for corte in range(primer_corte, n - horizonte + 1):  # se ajusta con valores[:corte]
        pasado = valores[:corte]
        for nombre, f in modelos.items():
            pred = f(pasado, horizonte)
            for k in range(horizonte):
                real = valores[corte + k]
                filas.append({
                    "modelo": nombre, "origen": y.index[corte - 1], "horizonte": k + 1,
                    "fecha": y.index[corte + k], "pronostico": float(pred[k]), "real": float(real),
                    "error": float(pred[k] - real),
                })
    return pd.DataFrame(filas)


def resumen(bt: pd.DataFrame) -> pd.DataFrame:
    """MAE y RMSE (puntos porcentuales) por modelo y horizonte, más el promedio de horizontes."""
    g = bt.assign(abs=bt["error"].abs(), sq=bt["error"] ** 2).groupby(["modelo", "horizonte"])
    r = g.agg(mae=("abs", "mean"), rmse=("sq", lambda s: float(np.sqrt(s.mean()))), n=("abs", "size"))
    r = r.reset_index()
    total = r.groupby("modelo")[["mae", "rmse"]].mean().rename(columns=lambda c: f"{c}_medio")
    return r.merge(total, on="modelo").sort_values(["mae_medio", "horizonte"]).reset_index(drop=True)


def intervalos(bt: pd.DataFrame, modelo: str, nivel: float = 0.8) -> dict[int, float]:
    """Semiamplitud del intervalo por horizonte: cuantil `nivel` del error absoluto del backtest."""
    sub = bt[bt["modelo"] == modelo]
    return {int(h): float(np.quantile(e.abs(), nivel)) for h, e in sub.groupby("horizonte")["error"]}
