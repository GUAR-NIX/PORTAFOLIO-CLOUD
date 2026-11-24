"""Fase 8 · API que sirve el modelo de probabilidad de informalidad.

Ejecutar en local:  uvicorn observatorio.api:app --reload      (con PYTHONPATH=src)
Documentación interactiva: http://127.0.0.1:8000/docs

Decisiones:
- El modelo se carga una vez al arrancar desde `MODELO_RUTA` (por defecto models/informalidad_lgbm.joblib).
- Las categorías válidas salen del propio artefacto: si llega un valor que el modelo no vio al entrenar, se
  responde 422 con la lista de valores permitidos, en lugar de predecir algo sin sentido.
- La explicación usa las contribuciones nativas de LightGBM (`pred_contrib`), que son valores SHAP exactos
  para árboles: la imagen de producción no necesita la librería `shap`.
- La lógica vive en `observatorio.prediccion`, compartida con la app; la API no guarda los perfiles.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from observatorio import prediccion as pred

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


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    pred.artefacto()  # falla al arrancar, no en la primera petición, si el modelo no está
    yield


app = FastAPI(
    title="Observatorio laboral del Ecuador · API de informalidad",
    description="Probabilidad de que una persona ocupada trabaje en el sector informal (ENEMDU, INEC).",
    version=VERSION_API,
    lifespan=ciclo_de_vida,
)


@app.get("/salud")
def salud() -> dict:
    a = pred.artefacto()
    return {"estado": "ok", "version_api": VERSION_API, "version_modelo": a.get("version", "sin versión")}


@app.get("/opciones")
def opciones() -> dict[str, list[str]]:
    return pred.opciones(pred.artefacto())


@app.post("/prediccion", response_model=Prediccion)
def prediccion(perfil: Perfil) -> Prediccion:
    a = pred.artefacto()
    datos = perfil.model_dump()
    try:
        prob, contrib = pred.predecir(datos, a)
    except pred.ValoresNoValidos as e:
        raise HTTPException(status_code=422, detail={"valores_no_validos": e.errores}) from e
    factores = [Factor(variable=v, valor=str(datos[v]), efecto=round(float(e), 3))
                for v, e in contrib.items()]
    suben = sorted((f for f in factores if f.efecto > 0), key=lambda f: -f.efecto)[:3]
    bajan = sorted((f for f in factores if f.efecto < 0), key=lambda f: f.efecto)[:3]
    return Prediccion(
        probabilidad_informal=round(prob, 4),
        tasa_nacional_referencia=a.get("tasa_referencia"),
        factores_que_suben=suben,
        factores_que_bajan=bajan,
        version_modelo=a.get("version", "sin versión"),
    )
