import numpy as np
import pandas as pd
import pytest

from observatorio.pronostico import (
    backtest,
    estacional_ingenuo,
    ingenuo,
    intervalos,
    media_movil,
    resumen,
)


def serie(valores) -> pd.Series:
    return pd.Series(valores, index=pd.period_range("2023-01", periods=len(valores), freq="M"), dtype=float)


def test_modelos_ingenuos():
    y = np.arange(1, 25, dtype=float)  # 24 meses: 1..24
    assert ingenuo(y, 3).tolist() == [24, 24, 24]
    assert estacional_ingenuo(y, 3).tolist() == [13, 14, 15]  # mismo mes del año anterior
    assert media_movil(y, 2).tolist() == [23, 23]


def test_backtest_no_usa_el_futuro():
    vistos = []

    def espia(y, h):
        vistos.append(len(y))
        return np.repeat(y[-1], h)

    y = serie(np.arange(30))
    bt = backtest(y, {"espia": espia}, horizonte=2, origenes=5)
    # 5 orígenes, cada uno solo ve el pasado: 24, 25, ..., 28 meses
    assert vistos == [24, 25, 26, 27, 28]
    # el pronóstico de cada fila es el último valor visto, nunca el real
    assert (bt["fecha"] > bt["origen"]).all()
    assert len(bt) == 5 * 2


def test_error_cero_en_serie_constante():
    bt = backtest(serie([3.0] * 30), {"ingenuo": ingenuo}, horizonte=3, origenes=6)
    r = resumen(bt)
    assert r["mae"].abs().max() == pytest.approx(0)


def test_resumen_y_intervalos():
    y = serie(np.r_[np.zeros(20), np.arange(10)])
    bt = backtest(y, {"ingenuo": ingenuo}, horizonte=2, origenes=4)
    r = resumen(bt)
    assert set(r["horizonte"]) == {1, 2}
    semi = intervalos(bt, "ingenuo", 0.8)
    assert semi[2] >= semi[1] > 0  # en una tendencia, el error crece con el horizonte


def test_serie_corta_falla_con_claridad():
    with pytest.raises(ValueError):
        backtest(serie(np.arange(15)), {"ingenuo": ingenuo}, horizonte=3, origenes=12)
