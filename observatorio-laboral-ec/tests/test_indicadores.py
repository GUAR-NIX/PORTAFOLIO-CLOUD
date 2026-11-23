import pandas as pd
import pytest

from observatorio.indicadores import poblaciones, tasas


def personas() -> pd.DataFrame:
    # Muestra sintética: cada fila representa a `fexp` personas.
    return pd.DataFrame(
        {
            "p03":     [10, 30, 40, 25, 50, 35, 60, 20],
            "condact": [None, 1, 2, 3, 7, 9, 1, 8],
            "secemp":  [None, 1, 2, 2, None, None, 2, None],
            "fexp":    [100, 10, 20, 10, 5, 30, 15, 10],
        }
    )


def test_poblaciones_expandidas():
    p = poblaciones(personas())
    assert p["poblacion_total"] == 200
    assert p["pet"] == 100            # el menor de 15 no cuenta
    assert p["pea"] == 70             # condact 1-8
    assert p["empleo"] == 55          # condact 1-6
    assert p["desempleo"] == 15       # condact 7-8
    assert p["pei"] == 30
    assert p["empleo_informal"] == 45  # empleados con secemp = 2


def test_tasas_oficiales():
    t = tasas(personas())
    assert t["tasa_participacion_global"] == pytest.approx(70.0)
    assert t["tasa_empleo_adecuado"] == pytest.approx(100 * 25 / 70)
    assert t["tasa_subempleo"] == pytest.approx(100 * 30 / 70)
    assert t["tasa_desempleo"] == pytest.approx(100 * 15 / 70)
    assert t["tasa_empleo_sector_informal"] == pytest.approx(100 * 45 / 55)


def test_menor_de_15_no_entra_aunque_tenga_condact():
    df = personas()
    df.loc[0, "condact"] = 7  # dato inconsistente: un niño marcado como desempleado
    assert poblaciones(df)["desempleo"] == 15
