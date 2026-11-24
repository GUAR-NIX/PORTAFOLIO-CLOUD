"""Fase 8 · API que sirve el modelo de probabilidad de informalidad.

Ejecutar en local:  uvicorn observatorio.api:app --reload      (con PYTHONPATH=src)
Documentación interactiva: http://127.0.0.1:8000/docs

Decisiones:
- El modelo se carga una vez al arrancar desde `MODELO_RUTA` (por defecto models/informalidad_lgbm.joblib).
- Las categorías válidas salen del propio artefacto: si llega un valor que el modelo no vio al entrenar, se
  responde 422 con la lista de valores permitidos, en lugar de predecir algo sin sentido.
- La explicación usa las contribuciones nativas de LightGBM (`pred_contrib`), que son valores SHAP exactos
  para árboles: la imagen de producción no necesita la librería `shap`.
- La API no guarda los perfiles que recibe.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Sin depender de observatorio.config: la imagen de la API no necesita la configuración de la base de datos.
RUTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "models" / "informalidad_lgbm.joblib"
VERSION_API = "1.0.0"


class Perfil(BaseModel):
    """Perfil de una persona ocupada. Los valores válidos de cada campo están en GET /opciones."""

    edad: int = Field(ge=15, le=99, examples=[28])
    sexo: str = Field(examples=["Mujer"])
    estado_civil: str = Field(examples=["Soltero(a)"])
    nivel_instruccion: str = Field(examples=["Educación media/bachillerato"])
    area: str = Field(examples=["Urbana"])
    provincia: str = Field(examples=["Guayas"])
    rama: str = Field(examples=["Comercio"])
    ocupacion: str = Field(examples=["Trabajadores de servicios y vendedores"])


class Factor(BaseModel):
    variable: str
    valor: str
    efecto: float = Field(description="Contribución SHAP (log-odds); positiva = más informalidad")


class Prediccion(BaseModel):
    probabilidad_informal: float = Field(ge=0, le=1)
    tasa_nacional_referencia: float | None = None
    factores_que_suben: list[Factor]
    factores_que_bajan: list[Factor]
    version_modelo: str


@lru_cache(maxsize=1)
def cargar(ruta: str) -> dict:
    p = Path(ruta)
    if not p.exists():
        raise FileNotFoundError(f"No existe el modelo en {p}. Entrénalo con scripts/entrenar_informalidad.py")
    return joblib.load(p)


def artefacto() -> dict:
    return cargar(os.environ.get("MODELO_RUTA", str(RUTA_POR_DEFECTO)))


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    artefacto()  # falla al arrancar, no en la primera petición, si el modelo no está
    yield


app = FastAPI(
    title="Observatorio laboral del Ecuador · API de informalidad",
    description="Probabilidad de que una persona ocupada trabaje en el sector informal (ENEMDU, INEC).",
    version=VERSION_API,
    lifespan=ciclo_de_vida,
)


@app.get("/salud")
def salud() -> dict:
    a = artefacto()
    return {"estado": "ok", "version_api": VERSION_API, "version_modelo": a.get("version", "sin versión")}


@app.get("/opciones")
def opciones() -> dict[str, list[str]]:
    a = artefacto()
    return {c: [str(v) for v in a["categorias"][c] if str(v) != "Sin dato"] for c in a["categoricas"]}


def _a_dataframe(perfil: Perfil, a: dict) -> pd.DataFrame:
    datos = perfil.model_dump()
    errores = {}
    for c in a["categoricas"]:
        validas = [str(v) for v in a["categorias"][c]]
        if datos[c] not in validas:
            errores[c] = {"recibido": datos[c], "validos": [v for v in validas if v != "Sin dato"]}
    if errores:
        raise HTTPException(status_code=422, detail={"valores_no_validos": errores})
    fila = pd.DataFrame([{v: datos[v] for v in a["variables"]}])
    for c in a["categoricas"]:
        fila[c] = pd.Categorical(fila[c], categories=a["categorias"][c])
    fila["edad"] = fila["edad"].astype("float64")
    return fila


@app.post("/prediccion", response_model=Prediccion)
def prediccion(perfil: Perfil) -> Prediccion:
    a = artefacto()
    X = _a_dataframe(perfil, a)
    modelo = a["modelo"]
    prob = float(modelo.predict_proba(X)[0, 1])
    contrib = np.asarray(modelo.booster_.predict(X, pred_contrib=True))[0, :-1]  # el último es el sesgo
    datos = perfil.model_dump()
    factores = [Factor(variable=v, valor=str(datos[v]), efecto=round(float(e), 3))
                for v, e in zip(a["variables"], contrib, strict=True)]
    suben = sorted((f for f in factores if f.efecto > 0), key=lambda f: -f.efecto)[:3]
    bajan = sorted((f for f in factores if f.efecto < 0), key=lambda f: f.efecto)[:3]
    return Prediccion(
        probabilidad_informal=round(prob, 4),
        tasa_nacional_referencia=a.get("tasa_referencia"),
        factores_que_suben=suben,
        factores_que_bajan=bajan,
        version_modelo=a.get("version", "sin versión"),
    )
