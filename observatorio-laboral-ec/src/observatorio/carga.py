"""Carga de los Parquet procesados en PostgreSQL (esquema `raw`), de forma idempotente.

Cada periodo se reemplaza dentro de una transacción (borrar + insertar): ejecutar la carga dos veces deja la
base exactamente igual. La tabla `raw.cargas` registra qué se cargó, cuántas filas y cuándo.

Uso:
    python -m observatorio.carga                 # carga todos los periodos procesados
    python -m observatorio.carga --solo 202605   # uno concreto
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, create_engine, text

from observatorio.config import DATOS_PROCESADOS, config_bd
from observatorio.ingesta import COLUMNAS

log = logging.getLogger("carga")

TABLA = "enemdu_personas"
TABLA_CARGAS = "cargas"


def _nombre(esquema: str | None, tabla: str) -> str:
    return f"{esquema}.{tabla}" if esquema else tabla


def preparar(engine: Engine, esquema: str | None = "raw") -> None:
    """Crea el esquema y la tabla de control si no existen."""
    with engine.begin() as con:
        if esquema:
            con.execute(text(f"CREATE SCHEMA IF NOT EXISTS {esquema}"))
        con.execute(text(
            f"CREATE TABLE IF NOT EXISTS {_nombre(esquema, TABLA_CARGAS)} ("
            "periodo VARCHAR(6) PRIMARY KEY, filas INTEGER NOT NULL, cargado_utc VARCHAR(32) NOT NULL)"
        ))


def cargar_periodo(engine: Engine, archivo: Path, esquema: str | None = "raw") -> tuple[str, int]:
    """Reemplaza un periodo completo en una sola transacción. Devuelve (periodo, filas)."""
    df = pd.read_parquet(archivo, columns=COLUMNAS)
    periodos = df["periodo"].unique().tolist()
    if len(periodos) != 1:
        raise ValueError(f"{archivo.name}: se esperaba un único periodo y hay {periodos}")
    periodo = str(periodos[0])
    tabla = _nombre(esquema, TABLA)
    with engine.begin() as con:
        existe = con.dialect.has_table(con, TABLA, schema=esquema)
        if existe:
            con.execute(text(f"DELETE FROM {tabla} WHERE periodo = :p"), {"p": periodo})
        df.to_sql(TABLA, con, schema=esquema, if_exists="append", index=False, chunksize=5000, method="multi")
        control = _nombre(esquema, TABLA_CARGAS)
        con.execute(text(f"DELETE FROM {control} WHERE periodo = :p"), {"p": periodo})
        con.execute(
            text(f"INSERT INTO {control} (periodo, filas, cargado_utc) VALUES (:p, :n, :t)"),
            {"p": periodo, "n": len(df), "t": datetime.now(UTC).isoformat(timespec="seconds")},
        )
    log.info("%s cargado (%s filas)", periodo, f"{len(df):,}")
    return periodo, len(df)


def ejecutar(engine: Engine, carpeta: Path, solo: str | None = None, esquema: str | None = "raw") -> list:
    preparar(engine, esquema)
    archivos = sorted(carpeta.glob("personas_*.parquet"))
    if solo:
        archivos = [a for a in archivos if a.stem.endswith(solo)]
    if not archivos:
        raise FileNotFoundError(f"No hay Parquet en {carpeta}: ejecuta antes la ingesta")
    return [cargar_periodo(engine, a, esquema) for a in archivos]


def main() -> None:
    p = argparse.ArgumentParser(description="Carga los microdatos procesados en PostgreSQL (esquema raw).")
    p.add_argument("--solo", help="periodo AAAAMM")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    engine = create_engine(config_bd().url, pool_pre_ping=True)
    resultado = ejecutar(engine, DATOS_PROCESADOS / "personas", a.solo)
    total = sum(n for _, n in resultado)
    print(f"{len(resultado)} periodos cargados · {total:,} filas")


if __name__ == "__main__":
    main()
