"""La app en inglés no puede quedarse a medias: mismas claves y todas las categorías del modelo traducidas."""

import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import textos  # noqa: E402

from observatorio import modelo_informalidad as mi  # noqa: E402


def campos(plantilla: str) -> set[str]:
    return {c for _, c, _, _ in string.Formatter().parse(plantilla) if c}


def test_los_dos_idiomas_tienen_las_mismas_claves():
    es, en = textos.TEXTOS["es"], textos.TEXTOS["en"]
    assert es.keys() == en.keys()
    for clave in ("variables", "modelos"):
        assert es[clave].keys() == en[clave].keys()
    assert len(es["pestanas"]) == len(en["pestanas"])


def test_las_plantillas_usan_los_mismos_campos():
    es, en = textos.TEXTOS["es"], textos.TEXTOS["en"]
    for clave, valor in es.items():
        if isinstance(valor, str):
            assert campos(valor) == campos(en[clave]), clave


def test_todas_las_categorias_del_modelo_tienen_traduccion():
    for catalogo in (mi.SEXO, mi.AREA, mi.ESTADO_CIVIL, mi.NIVEL, mi.OCUPACION, mi.RAMA):
        faltan = [v for v in catalogo.values() if v not in textos.CATEGORIAS_EN]
        assert not faltan


def test_el_espanol_no_se_altera_y_lo_desconocido_se_muestra_igual():
    assert textos.categoria("Mujer", "es") == "Mujer"
    assert textos.categoria("Mujer", "en") == "Female"
    assert textos.categoria("Guayas", "en") == "Guayas"


def test_formatos_de_numero_por_idioma():
    assert textos.miles(559089, "es") == "559.089" and textos.miles(559089, "en") == "559,089"
    assert textos.decimales(0.9101, "es") == "0,910" and textos.decimales(0.9101, "en") == "0.910"
