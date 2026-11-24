"""Predicción y explicación con el modelo de informalidad; la usan la API (Fase 8) y la app (Fase 9).

No depende de FastAPI ni de Streamlit: solo del artefacto guardado por scripts/entrenar_informalidad.py.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
RUTAS_CANDIDATAS = [
    RAIZ / "models" / "informalidad_lgbm.joblib",        # el que genera el entrenamiento local
    RAIZ / "app" / "modelo" / "informalidad_lgbm.joblib",  # copia publicada para la app en la nube
]


class ValoresNoValidos(ValueError):
    """Alguna categoría no existe en el modelo; `errores` lleva lo recibido y los valores válidos."""

    def __init__(self, errores: dict):
        super().__init__(f"Valores no válidos: {', '.join(errores)}")
        self.errores = errores


def ruta_modelo() -> Path:
    if os.environ.get("MODELO_RUTA"):
        return Path(os.environ["MODELO_RUTA"])
    for r in RUTAS_CANDIDATAS:
        if r.exists():
            return r
    return RUTAS_CANDIDATAS[0]


@lru_cache(maxsize=4)
def cargar(ruta: str) -> dict:
    p = Path(ruta)
    if not p.exists():
        raise FileNotFoundError(f"No existe el modelo en {p}. Entrénalo con scripts/entrenar_informalidad.py")
    return joblib.load(p)


def artefacto() -> dict:
    return cargar(str(ruta_modelo()))


def opciones(a: dict) -> dict[str, list[str]]:
    return {c: [str(v) for v in a["categorias"][c] if str(v) != "Sin dato"] for c in a["categoricas"]}


def a_dataframe(perfil: dict, a: dict) -> pd.DataFrame:
    errores = {}
    for c in a["categoricas"]:
        validas = [str(v) for v in a["categorias"][c]]
        if perfil.get(c) not in validas:
            errores[c] = {"recibido": perfil.get(c), "validos": [v for v in validas if v != "Sin dato"]}
    if errores:
        raise ValoresNoValidos(errores)
    fila = pd.DataFrame([{v: perfil[v] for v in a["variables"]}])
    for c in a["categoricas"]:
        fila[c] = pd.Categorical(fila[c], categories=a["categorias"][c])
    fila["edad"] = fila["edad"].astype("float64")
    return fila


def predecir(perfil: dict, a: dict | None = None) -> tuple[float, pd.Series]:
    """Probabilidad de informalidad y contribución SHAP (log-odds) de cada variable."""
    a = artefacto() if a is None else a
    X = a_dataframe(perfil, a)
    modelo = a["modelo"]
    prob = float(modelo.predict_proba(X)[0, 1])
    contrib = np.asarray(modelo.booster_.predict(X, pred_contrib=True))[0, :-1]  # el último es el sesgo
    return prob, pd.Series(contrib, index=a["variables"], dtype=float)
