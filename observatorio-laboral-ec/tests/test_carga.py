"""Tests del cargador sobre SQLite en memoria (misma lógica SQLAlchemy, sin necesitar un servidor)."""

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from observatorio.carga import ejecutar
from observatorio.ingesta import COLUMNAS


def parquet_mes(carpeta, periodo: str, filas: int):
    df = pd.DataFrame({c: [None] * filas for c in COLUMNAS})
    df["periodo"] = periodo
    df["id_persona"] = [f"{periodo}-{i}" for i in range(filas)]
    df["fexp"] = 100.0
    ruta = carpeta / f"personas_{periodo}.parquet"
    df.to_parquet(ruta, index=False)
    return ruta


@pytest.fixture
def motor():
    return create_engine("sqlite://")


def contar(motor, sql):
    with motor.connect() as c:
        return c.execute(text(sql)).scalar()


def test_carga_todos_los_periodos(tmp_path, motor):
    parquet_mes(tmp_path, "202604", 3)
    parquet_mes(tmp_path, "202605", 2)
    r = ejecutar(motor, tmp_path, esquema=None)
    assert r == [("202604", 3), ("202605", 2)]
    assert contar(motor, "select count(*) from enemdu_personas") == 5
    assert contar(motor, "select sum(filas) from cargas") == 5


def test_recargar_no_duplica(tmp_path, motor):
    parquet_mes(tmp_path, "202605", 2)
    ejecutar(motor, tmp_path, esquema=None)
    ejecutar(motor, tmp_path, esquema=None)
    assert contar(motor, "select count(*) from enemdu_personas") == 2
    assert contar(motor, "select count(*) from cargas") == 1


def test_recarga_reemplaza_un_periodo_corregido(tmp_path, motor):
    parquet_mes(tmp_path, "202605", 2)
    ejecutar(motor, tmp_path, esquema=None)
    parquet_mes(tmp_path, "202605", 4)  # el INEC republica el mes con más registros
    ejecutar(motor, tmp_path, solo="202605", esquema=None)
    assert contar(motor, "select count(*) from enemdu_personas where periodo = '202605'") == 4


def test_sin_datos_procesados_da_un_error_claro(tmp_path, motor):
    with pytest.raises(FileNotFoundError, match="ingesta"):
        ejecutar(motor, tmp_path, esquema=None)
