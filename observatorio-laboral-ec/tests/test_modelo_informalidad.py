import numpy as np
import pandas as pd
import pytest

from observatorio.modelo_informalidad import (
    CATEGORICAS,
    OBJETIVO,
    PESO,
    Particion,
    construir_dataset,
    metricas,
    particionar,
    tasa_ponderada,
)


def personas(**cambios) -> pd.DataFrame:
    base = {
        "periodo": ["202501"] * 6,
        "p02": [1, 2, 1, 2, 1, 2],
        "p03": [30, 45, 14, 70, 25, 40],
        "p06": [1, 6, 6, 4, 5, 1],
        "nnivins": [5, 3, 3, 1, 4, 4],
        "area": [1, 2, 1, 2, 1, 1],
        "ciudad": ["170150", "90150", "10150", "130150", "170150", "90150"],
        "rama1": [16, 1, 7, 1, 7, 3],
        "grupo1": [2, 6, 5, 9, 5, 7],
        "condact": [1, 3, 1, 9, 7, 2],
        "secemp": [1, 2, 2, np.nan, np.nan, 2],
        "fexp": [100.0, 200.0, 50.0, 80.0, 60.0, 0.0],
    }
    base.update(cambios)
    return pd.DataFrame(base)


def test_solo_ocupados_de_15_o_mas_con_peso_positivo():
    df = construir_dataset(personas(), provincias={})
    # fuera: menor de 15, inactivo (condact 9), desempleado (7) y peso 0
    assert len(df) == 2
    assert df[OBJETIVO].tolist() == [0, 1]


def test_objetivo_es_sector_informal_secemp_2():
    p = personas(p03=[30] * 6, condact=[1] * 6, secemp=[1, 2, 3, 4, 2, 1], fexp=[1.0] * 6)
    df = construir_dataset(p, provincias={})
    assert df[OBJETIVO].tolist() == [0, 1, 0, 0, 1, 0]


def test_provincia_desde_ciudad_sin_cero_inicial():
    df = construir_dataset(personas(), provincias={"09": "Guayas", "17": "Pichincha"})
    assert df["provincia"].tolist() == ["Pichincha", "Guayas"]


def test_etiquetas_legibles_y_categoricas():
    df = construir_dataset(personas(), provincias={})
    assert df.loc[0, "nivel_instruccion"] == "Superior"
    assert df.loc[1, "area"] == "Rural"
    assert all(str(df[c].dtype) == "category" for c in CATEGORICAS)


def test_ingreso_no_es_variable():
    df = construir_dataset(personas(), provincias={})
    assert "ingrl" not in df.columns


def test_particion_temporal_sin_mezclar_meses():
    df = pd.DataFrame({"periodo": ["202504", "202505", "202506", "202511", "202512", "202605"]})
    partes = particionar(df, Particion("202505", "202511"))
    assert partes["entrenamiento"]["periodo"].tolist() == ["202504", "202505"]
    assert partes["validacion"]["periodo"].tolist() == ["202506", "202511"]
    assert partes["prueba"]["periodo"].tolist() == ["202512", "202605"]


def test_tasa_ponderada_usa_el_factor_de_expansion():
    assert tasa_ponderada([1, 0], [3, 1]) == pytest.approx(0.75)


def test_metricas_ponderadas():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.4, 0.35, 0.8])
    w = np.ones(4)
    m = metricas(y, p, w)
    assert m["auc_roc"] == pytest.approx(0.75)
    assert m["tasa_observada_pct"] == pytest.approx(50.0)
    assert m["tasa_estimada_pct"] == pytest.approx(41.25)


def test_peso_y_objetivo_presentes():
    df = construir_dataset(personas(), provincias={})
    assert {PESO, OBJETIVO, "periodo"} <= set(df.columns)
