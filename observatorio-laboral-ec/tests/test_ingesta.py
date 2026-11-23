import io
import zipfile

import pandas as pd
import pytest
import requests

from observatorio import ingesta
from observatorio.ingesta import Manifiesto, Mes, descargar_mes, procesar_mes, rango, url_mes

CSV = (
    "area;ciudad;p02;p03;condact;secemp;fexp;periodo;id_persona\n"
    "1;010150;2;30;1;1;102,5;202605;0001\n"
    "2;170150;1;10;0; ;80,25;202605;0002\n"
)


def zip_enemdu(csv: str = CSV) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("enemdu_persona_2026_05.csv", csv)
        z.writestr("enemdu_vivienda_hogar_2026_05.csv", "x;y\n1;2\n")
    return buf.getvalue()


class RespuestaFalsa:
    def __init__(self, contenido: bytes, estado: int = 200):
        self.contenido, self.status_code = contenido, estado

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def iter_content(self, _):
        yield self.contenido


class SesionFalsa:
    def __init__(self, contenido: bytes, estado: int = 200):
        self.contenido, self.estado, self.llamadas = contenido, estado, 0

    def get(self, url, **_):
        self.llamadas += 1
        return RespuestaFalsa(self.contenido, self.estado)


def test_url_sigue_el_patron_del_inec():
    assert url_mes(Mes(2026, 5)) == (
        "https://www.ecuadorencifras.gob.ec/documentos/web-inec/EMPLEO/2026/Mayo_2026/"
        "2_BDD_DATOS_ABIERTOS_ENEMDU_2026_05_CSV.zip"
    )


def test_rango_cruza_el_fin_de_anio():
    assert [m.clave for m in rango(Mes(2024, 11), Mes(2025, 2))] == ["202411", "202412", "202501", "202502"]


def test_mes_no_valido():
    with pytest.raises(ValueError):
        Mes.desde_texto("2025-13")


def test_descarga_idempotente(tmp_path):
    man = Manifiesto(tmp_path / "manifiesto.json")
    sesion = SesionFalsa(zip_enemdu())
    a = descargar_mes(Mes(2026, 5), tmp_path, man, sesion)
    b = descargar_mes(Mes(2026, 5), tmp_path, man, sesion)
    assert a == b and sesion.llamadas == 1          # la segunda vez no descarga
    assert man.get("202605")["sha256"] == ingesta.sha256(a)


def test_rechaza_una_pagina_de_error_aunque_el_codigo_sea_200(tmp_path):
    man = Manifiesto(tmp_path / "manifiesto.json")
    with pytest.raises(ValueError, match="no es un ZIP"):
        descargar_mes(Mes(2026, 5), tmp_path, man, SesionFalsa(b"<html>Error</html>"))
    assert not list(tmp_path.glob("*.zip")) and man.get("202605") is None


def test_404_se_propaga_como_no_publicado(tmp_path):
    with pytest.raises(requests.HTTPError):
        descargar_mes(Mes(2030, 1), tmp_path, Manifiesto(tmp_path / "m.json"), SesionFalsa(b"", 404))


def test_procesar_normaliza_esquema_y_tipos(tmp_path):
    zipf = tmp_path / "mes.zip"
    zipf.write_bytes(zip_enemdu())
    salida = procesar_mes(zipf, Mes(2026, 5), tmp_path / "personas")
    df = pd.read_parquet(salida)
    assert list(df.columns) == ingesta.COLUMNAS               # columnas ausentes creadas vacías
    assert df["fexp"].tolist() == [102.5, 80.25]               # coma decimal
    assert df["ciudad"].tolist() == ["010150", "170150"]       # códigos con ceros a la izquierda
    assert df["secemp"].isna().tolist() == [False, True]       # el espacio es un vacío
    assert (df["periodo"] == "202605").all()
