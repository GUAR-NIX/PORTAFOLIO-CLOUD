import numpy as np
import pandas as pd
import pytest

from observatorio.monitoreo import alerta_desempeno, deriva_por_mes, estado, proporciones, psi, sesgo_movil


def test_psi_cero_si_no_cambia_y_crece_con_el_cambio():
    r = pd.Series({"a": 0.5, "b": 0.5})
    assert psi(r, r) == pytest.approx(0, abs=1e-9)
    leve = psi(r, pd.Series({"a": 0.55, "b": 0.45}))
    fuerte = psi(r, pd.Series({"a": 0.9, "b": 0.1}))
    assert 0 < leve < 0.1 < 0.2 < fuerte


def test_psi_tolera_categorias_nuevas_o_ausentes():
    assert np.isfinite(psi(pd.Series({"a": 1.0}), pd.Series({"a": 0.5, "b": 0.5})))


def test_proporciones_ponderadas():
    p = proporciones(pd.Series(["x", "y", "x"]), pd.Series([1.0, 2.0, 1.0]))
    assert p["x"] == pytest.approx(0.5) and p["y"] == pytest.approx(0.5)


def test_estados_por_umbral():
    assert [estado(v) for v in (0.05, 0.15, 0.3)] == ["estable", "vigilar", "deriva"]


def test_alerta_usa_auc_y_sesgo_sostenido():
    assert alerta_desempeno(0.91, 0.3) == "ok"
    assert alerta_desempeno(0.85, 0.0) == "reentrenar"
    assert alerta_desempeno(0.91, -1.6) == "reentrenar"


def test_un_mes_ruidoso_no_dispara_el_sesgo_movil():
    est = pd.Series([54.0, 54.0, 52.0])
    obs = pd.Series([54.0, 54.0, 54.0])  # solo el último mes se desvía 2 puntos
    assert abs(sesgo_movil(est, obs).iloc[-1]) < 1.5


def test_deriva_por_mes_detecta_un_cambio_de_composicion():
    rng = np.random.default_rng(1)
    n = 3000
    base = pd.DataFrame({"periodo": "202401", "edad": rng.integers(15, 80, n).astype(float),
                         "area": rng.choice(["Urbana", "Rural"], n, p=[0.7, 0.3]), "fexp": 1.0})
    cambio = base.assign(periodo="202402", area=rng.choice(["Urbana", "Rural"], n, p=[0.3, 0.7]))
    t = deriva_por_mes(pd.concat([base, cambio], ignore_index=True), base, ["area"])
    assert t.loc[t["periodo"] == "202401", "estado_datos"].item() == "estable"
    assert t.loc[t["periodo"] == "202402", "estado_datos"].item() == "deriva"
    assert t.loc[t["periodo"] == "202402", "variable_mas_derivada"].item() == "area"
