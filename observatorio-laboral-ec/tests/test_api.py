"""Tests de la API con un modelo sintético: no necesitan los microdatos ni el modelo real."""

import joblib
import numpy as np
import pandas as pd
import pytest

lgb = pytest.importorskip("lightgbm")
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from observatorio import api  # noqa: E402
from observatorio.modelo_informalidad import CATEGORICAS, VARIABLES  # noqa: E402

CATEGORIAS = {
    "sexo": ["Hombre", "Mujer"],
    "estado_civil": ["Casado(a)", "Soltero(a)"],
    "nivel_instruccion": ["Educación básica", "Superior"],
    "area": ["Rural", "Urbana"],
    "provincia": ["Guayas", "Pichincha"],
    "rama": ["Agricultura, ganadería y pesca", "Enseñanza"],
    "ocupacion": ["Ocupaciones elementales", "Profesionales científicos e intelectuales"],
}
PERFIL = {"edad": 30, "sexo": "Mujer", "estado_civil": "Soltero(a)", "nivel_instruccion": "Superior",
          "area": "Urbana", "provincia": "Pichincha", "rama": "Enseñanza",
          "ocupacion": "Profesionales científicos e intelectuales"}


@pytest.fixture(scope="module")
def cliente(tmp_path_factory):
    rng = np.random.default_rng(0)
    n = 2000
    X = pd.DataFrame({"edad": rng.integers(15, 80, n).astype(float),
                      **{c: rng.choice(CATEGORIAS[c], n) for c in CATEGORICAS}})[VARIABLES]
    for c in CATEGORICAS:
        X[c] = pd.Categorical(X[c], categories=CATEGORIAS[c])
    # informalidad sintética: rural y educación básica la suben
    logit = -1 + 2 * (X["area"] == "Rural") + 1.5 * (X["nivel_instruccion"] == "Educación básica")
    y = (rng.random(n) < 1 / (1 + np.exp(-logit.astype(float)))).astype(int)
    modelo = lgb.LGBMClassifier(n_estimators=30, verbose=-1).fit(X, y)
    ruta = tmp_path_factory.mktemp("modelo") / "m.joblib"
    joblib.dump({"modelo": modelo, "variables": VARIABLES, "categoricas": CATEGORICAS,
                 "categorias": CATEGORIAS, "version": "test", "tasa_referencia": 0.5}, ruta)
    mp = pytest.MonkeyPatch()
    mp.setenv("MODELO_RUTA", str(ruta))
    api.cargar.cache_clear()
    with TestClient(api.app) as c:
        yield c
    api.cargar.cache_clear()
    mp.undo()


def test_salud(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json()["version_modelo"] == "test"


def test_opciones(cliente):
    assert cliente.get("/opciones").json()["provincia"] == ["Guayas", "Pichincha"]


def test_prediccion_y_explicacion(cliente):
    r = cliente.post("/prediccion", json=PERFIL)
    assert r.status_code == 200
    d = r.json()
    assert 0 <= d["probabilidad_informal"] <= 1
    assert len(d["factores_que_suben"]) <= 3 and len(d["factores_que_bajan"]) <= 3
    assert all(f["efecto"] > 0 for f in d["factores_que_suben"])


def test_perfil_rural_basico_es_mas_informal(cliente):
    urbano = cliente.post("/prediccion", json=PERFIL).json()["probabilidad_informal"]
    rural = cliente.post("/prediccion", json=dict(PERFIL, area="Rural",
                                                  nivel_instruccion="Educación básica")).json()
    assert rural["probabilidad_informal"] > urbano


def test_categoria_desconocida_da_422_con_valores_validos(cliente):
    r = cliente.post("/prediccion", json=dict(PERFIL, provincia="Narnia"))
    assert r.status_code == 422
    assert r.json()["detail"]["valores_no_validos"]["provincia"]["validos"] == ["Guayas", "Pichincha"]


def test_edad_fuera_de_rango_da_422(cliente):
    assert cliente.post("/prediccion", json=dict(PERFIL, edad=12)).status_code == 422
