r"""Integración: dbt incremental + escribir-auditar-publicar sobre un PostgreSQL vacío y datos sintéticos.

Solo se ejecuta con DBT_PRUEBAS=1 y una base desechable (en CI, un servicio de PostgreSQL). Se niega a tocar
una base que no sea local. Las cifras «oficiales» del seed salen de `observatorio.indicadores` (Python),
así que la compuerta compara dos implementaciones independientes: Python y SQL.

    DBT_PRUEBAS=1 PGHOST=localhost PGUSER=ci PGPASSWORD=ci PGDATABASE=prueba \
        pytest tests/test_dbt_incremental.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.skipif(os.getenv("DBT_PRUEBAS") != "1", reason="necesita DBT_PRUEBAS=1 y PostgreSQL")

RAIZ = Path(__file__).resolve().parents[1]
MESES = ["202601", "202602"]
NUEVO = "202603"
MARTS = ["fct_mercado_laboral", "indicadores_nacionales", "dim_periodo"]


def personas(periodo: str, semilla: int, n: int = 600) -> pd.DataFrame:
    """Personas inventadas y coherentes con los tests de dbt (no son microdatos del INEC)."""
    rng = np.random.default_rng(semilla)
    edad = rng.integers(5, 85, n)
    condact = np.where(edad >= 15, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9], n), 0)
    empleo = (condact >= 1) & (condact <= 6)
    return pd.DataFrame({
        "periodo": periodo,
        "id_vivienda": [f"v{i // 4}" for i in range(n)],
        "id_hogar": [f"h{i // 4}" for i in range(n)],
        "id_persona": [f"{periodo}{i:06d}" for i in range(n)],
        "upm": [f"{i // 40:06d}" for i in range(n)],
        "estrato": 1,
        "fexp": rng.uniform(50, 400, n).round(3),
        "area": rng.integers(1, 3, n),
        "ciudad": rng.choice(["170150", "90150", "10150"], n),   # sin el cero inicial, como el INEC
        "p02": rng.integers(1, 3, n),
        "p03": edad,
        "p06": 6,
        "nnivins": rng.integers(1, 6, n),
        "condact": condact,
        "secemp": np.where(empleo, rng.integers(1, 5, n), np.nan),
        "ingrl": np.where(empleo, rng.integers(100, 1500, n).astype(float), np.nan),
        "rama1": np.where(empleo, 7.0, np.nan),
        "grupo1": np.where(empleo, 5.0, np.nan),
    })


class Entorno:
    def __init__(self, tmp: Path):
        from sqlalchemy import create_engine

        from observatorio.config import config_bd

        cfg = config_bd()
        if cfg.host not in {"localhost", "127.0.0.1"}:
            pytest.fail(f"esta prueba solo se ejecuta en una base local, no en {cfg.host}")
        self.engine = create_engine(cfg.url)
        self.dbt_dir = tmp / "dbt"
        ignorar = shutil.ignore_patterns("target", "logs", ".user.yml")
        shutil.copytree(RAIZ / "dbt", self.dbt_dir, ignore=ignorar)
        self.datos = tmp / "personas"
        self.datos.mkdir()
        self.df: dict[str, pd.DataFrame] = {}
        self.sql("drop schema if exists raw, staging, intermediate, audit, marts, seeds cascade")

    def sql(self, consulta: str) -> list:
        from sqlalchemy import text

        with self.engine.begin() as con:
            r = con.execute(text(consulta))
            return r.fetchall() if r.returns_rows else []

    def cargar(self, periodo: str, df: pd.DataFrame) -> None:
        from observatorio.carga import cargar_periodo, preparar

        self.df[periodo] = df
        archivo = self.datos / f"personas_{periodo}.parquet"
        df.to_parquet(archivo, index=False)
        preparar(self.engine)
        cargar_periodo(self.engine, archivo)

    def oficiales(self, error: float = 0.0) -> None:
        """Escribe el seed de tasas oficiales desde Python; `error` simula una cifra que no cuadra."""
        from observatorio.indicadores import tasas

        claves = ["tasa_participacion_global", "tasa_empleo_adecuado", "tasa_subempleo", "tasa_desempleo"]
        filas = [{"periodo": p, **{k: round(tasas(d)[k] + error, 1) for k in claves}, "fuente": "sintética"}
                 for p, d in self.df.items()]
        pd.DataFrame(filas).to_csv(self.dbt_dir / "seeds/tasas_oficiales_inec.csv", index=False)

    def build(self) -> tuple[int, dict[str, dict]]:
        """Ejecuta `dbt build`. Devuelve (código, resultado por nodo)."""
        exe = Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt")
        p = subprocess.run([str(exe), "build", "--profiles-dir", "."], cwd=self.dbt_dir, capture_output=True,
                           text=True, encoding="utf-8")
        ruta = self.dbt_dir / "target/run_results.json"
        assert ruta.exists(), p.stdout[-3000:]
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return p.returncode, {r["unique_id"].split(".")[2]: r for r in datos["results"]}

    def foto(self) -> dict[str, list]:
        """Contenido completo de lo publicado, para comprobar que no cambia ni una fila."""
        md5 = "select md5(string_agg(x::text, '|' order by x::text)) from marts.{} x"
        return {t: self.sql(md5.format(t)) for t in MARTS}

    def versiones(self, periodo: str) -> list:
        """xmin: identifica la transacción que escribió las filas. Si no cambia, no se reescribieron."""
        return self.sql(
            f"select distinct xmin::text from marts.fct_mercado_laboral where periodo = '{periodo}'"
        )


@pytest.fixture
def e(tmp_path):
    ent = Entorno(tmp_path)
    for i, m in enumerate(MESES):
        ent.cargar(m, personas(m, i))
    ent.oficiales()
    codigo, r = ent.build()
    assert codigo == 0, {k: v["message"] for k, v in r.items() if v["status"] not in ("success", "pass")}
    yield ent
    ent.engine.dispose()


def filas(r: dict, nodo: str) -> int:
    return r[nodo]["adapter_response"]["rows_affected"]


def test_sin_cambios_no_recalcula_nada(e):
    antes = e.foto()
    codigo, r = e.build()
    assert codigo == 0
    assert filas(r, "aud_fct_mercado_laboral") == 0
    assert filas(r, "fct_mercado_laboral") == 0
    assert e.foto() == antes


def test_un_mes_nuevo_no_reescribe_los_anteriores(e):
    antes = e.versiones(MESES[0])
    e.cargar(NUEVO, personas(NUEVO, 9))
    e.oficiales()
    codigo, r = e.build()
    assert codigo == 0
    esperadas = e.sql(f"select count(*) from audit.aud_fct_mercado_laboral where periodo = '{NUEVO}'")[0][0]
    assert filas(r, "fct_mercado_laboral") == esperadas > 0
    assert e.versiones(MESES[0]) == antes
    assert e.sql("select count(*) from marts.indicadores_nacionales")[0][0] == 3


def test_una_revision_del_inec_reemplaza_el_mes_sin_duplicar(e):
    otro = e.versiones(MESES[0])
    e.cargar(MESES[1], personas(MESES[1], 77))
    e.oficiales()
    codigo, _ = e.build()
    assert codigo == 0
    esperado = float(e.df[MESES[1]]["fexp"].sum())
    suma = "select sum(poblacion) from marts.fct_mercado_laboral where periodo = '{}'"
    obtenido = e.sql(suma.format(MESES[1]))[0][0]
    assert obtenido == pytest.approx(esperado)
    assert e.versiones(MESES[0]) == otro


def test_un_dato_invalido_no_cambia_lo_publicado(e):
    antes = e.foto()
    malo = personas(NUEVO, 5)
    malo.loc[3, "condact"] = 42
    e.cargar(NUEVO, malo)
    codigo, r = e.build()
    assert codigo == 1
    assert all(r[t]["status"] == "skipped" for t in MARTS)
    assert e.foto() == antes


def test_personas_duplicadas_no_cambian_lo_publicado(e):
    antes = e.foto()
    d = personas(NUEVO, 6)
    e.cargar(NUEVO, pd.concat([d, d.head(5)], ignore_index=True))
    codigo, r = e.build()
    assert codigo == 1
    assert all(r[t]["status"] == "skipped" for t in MARTS)
    assert e.foto() == antes


def test_tasa_que_no_cuadra_bloquea_y_al_corregir_se_publica(e):
    antes = e.foto()
    e.cargar(NUEVO, personas(NUEVO, 7))
    e.oficiales(error=0.5)
    codigo, r = e.build()
    assert codigo == 1
    assert r["assert_tasas_iguales_al_inec"]["status"] == "fail"
    assert all(r[t]["status"] == "skipped" for t in MARTS)
    assert e.foto() == antes, "el candidato rechazado llegó a lo publicado"
    candidatos = e.sql(f"select count(*) from audit.aud_fct_mercado_laboral where periodo = '{NUEVO}'")[0][0]
    assert candidatos > 0, "el candidato debe quedar en audit para investigarlo"

    e.oficiales()
    codigo, _ = e.build()
    assert codigo == 0
    assert e.foto() != antes
    publicado = e.sql(f"select count(*) from marts.fct_mercado_laboral where periodo = '{NUEVO}'")[0][0]
    assert publicado == candidatos


def test_cambiar_la_logica_recalcula_todos_los_meses(e):
    modelo = e.dbt_dir / "models/intermediate/int_personas_clasificadas.sql"
    sql = modelo.read_text(encoding="utf-8")
    assert "then '15-24'" in sql
    modelo.write_text(sql.replace("then '15-24'", "then 'De 15 a 24'"), encoding="utf-8")
    codigo, r = e.build()
    assert codigo == 0
    total = e.sql("select count(*) from marts.fct_mercado_laboral")[0][0]
    assert filas(r, "fct_mercado_laboral") == total
    assert e.sql("select count(*) from marts.fct_mercado_laboral where grupo_edad = '15-24'")[0][0] == 0


def test_migra_una_tabla_antigua_sin_recarga_completa(e):
    antes = e.foto()["indicadores_nacionales"]
    e.sql("drop view marts.bi_mercado_laboral")
    e.sql("alter table marts.fct_mercado_laboral drop column cargado_utc, drop column version_logica")
    codigo, _ = e.build()
    assert codigo == 0
    assert e.foto()["indicadores_nacionales"] == antes
    assert e.sql("select count(*) from marts.fct_mercado_laboral where version_logica is null")[0][0] == 0
