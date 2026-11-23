"""Ingesta de los microdatos mensuales de la ENEMDU (datos abiertos del INEC).

Diseño:
- **Idempotente**: un mes ya descargado e íntegro (mismo SHA-256 del manifiesto) no se vuelve a descargar.
- **Verificable**: `data/raw/manifiesto.json` guarda URL, tamaño, SHA-256 y fecha de cada archivo.
- **Robusta**: descarga a un archivo temporal y solo lo da por bueno si es un ZIP con la tabla de personas
  (el servidor puede devolver una página de error con código 200).
- **Tolerante a cambios de esquema**: si un mes no trae alguna columna, se crea vacía y se avisa.

Uso:
    python -m observatorio.ingesta --desde 2023-01 --hasta 2026-05
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from observatorio.config import DATOS_CRUDOS, DATOS_PROCESADOS

log = logging.getLogger("ingesta")

URL_BASE = "https://www.ecuadorencifras.gob.ec/documentos/web-inec/EMPLEO"
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]

# Columnas de personas que usa el proyecto: identificación, diseño muestral, perfil y mercado laboral.
COLUMNAS = [
    "periodo", "id_vivienda", "id_hogar", "id_persona", "upm", "estrato", "fexp",
    "area", "ciudad", "p02", "p03", "p06", "nnivins",
    "condact", "secemp", "ingrl", "rama1", "grupo1",
]
TEXTO = {"periodo", "id_vivienda", "id_hogar", "id_persona", "upm", "ciudad"}


@dataclass(frozen=True)
class Mes:
    anio: int
    mes: int

    @classmethod
    def actual(cls) -> Mes:
        hoy = datetime.now(UTC)
        return cls(hoy.year, hoy.month)

    @classmethod
    def desde_texto(cls, texto: str) -> Mes:
        if texto == "actual":
            return cls.actual()
        anio, mes = texto.split("-")
        m = cls(int(anio), int(mes))
        if not 1 <= m.mes <= 12:
            raise ValueError(f"Mes no válido: {texto}")
        return m

    @property
    def clave(self) -> str:
        return f"{self.anio}{self.mes:02d}"

    def siguiente(self) -> Mes:
        return Mes(self.anio + self.mes // 12, self.mes % 12 + 1)

    def __le__(self, otro: Mes) -> bool:
        return (self.anio, self.mes) <= (otro.anio, otro.mes)


def rango(desde: Mes, hasta: Mes) -> list[Mes]:
    meses, m = [], desde
    while m <= hasta:
        meses.append(m)
        m = m.siguiente()
    return meses


def url_mes(m: Mes) -> str:
    """URL del ZIP de datos abiertos (CSV). Patrón válido de forma continua desde enero de 2023."""
    carpeta = f"{MESES[m.mes - 1]}_{m.anio}"
    return f"{URL_BASE}/{m.anio}/{carpeta}/2_BDD_DATOS_ABIERTOS_ENEMDU_{m.anio}_{m.mes:02d}_CSV.zip"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _miembro_personas(z: zipfile.ZipFile) -> str:
    nombres = [n for n in z.namelist() if "persona" in n.lower() and n.lower().endswith(".csv")]
    if not nombres:
        raise ValueError("el ZIP no contiene la tabla de personas")
    return nombres[0]


def es_zip_valido(ruta: Path) -> bool:
    if not zipfile.is_zipfile(ruta):
        return False
    with zipfile.ZipFile(ruta) as z:
        try:
            _miembro_personas(z)
        except ValueError:
            return False
        return z.testzip() is None


class Manifiesto:
    def __init__(self, ruta: Path):
        self.ruta = ruta
        self.datos: dict = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}

    def get(self, clave: str) -> dict | None:
        return self.datos.get(clave)

    def registrar(self, clave: str, entrada: dict) -> None:
        self.datos[clave] = entrada
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.datos, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        tmp.replace(self.ruta)


def descargar_mes(m: Mes, destino: Path, manifiesto: Manifiesto, sesion: requests.Session) -> Path:
    """Descarga el ZIP de un mes si no está ya descargado e íntegro. Devuelve la ruta local."""
    archivo = destino / f"enemdu_{m.clave}_csv.zip"
    previo = manifiesto.get(m.clave)
    if archivo.exists() and previo and sha256(archivo) == previo["sha256"]:
        log.info("%s ya descargado (sin cambios)", m.clave)
        return archivo

    url = url_mes(m)
    destino.mkdir(parents=True, exist_ok=True)
    tmp = archivo.with_suffix(".part")
    with sesion.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for bloque in r.iter_content(1 << 20):
                f.write(bloque)
    if not es_zip_valido(tmp):
        tmp.unlink(missing_ok=True)
        raise ValueError(f"{m.clave}: la respuesta no es un ZIP válido con la tabla de personas ({url})")
    tmp.replace(archivo)
    manifiesto.registrar(m.clave, {
        "url": url,
        "bytes": archivo.stat().st_size,
        "sha256": sha256(archivo),
        "descargado_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    })
    log.info("%s descargado (%.1f MB)", m.clave, archivo.stat().st_size / 1e6)
    return archivo


def leer_personas_zip(archivo: Path) -> pd.DataFrame:
    """Lee la tabla de personas directamente del ZIP y normaliza el esquema a COLUMNAS."""
    with zipfile.ZipFile(archivo) as z, z.open(_miembro_personas(z)) as f:
        crudo = f.read()
    df = pd.read_csv(
        io.BytesIO(crudo), sep=";", decimal=",", na_values=[" ", ""], low_memory=False,
        dtype={c: "string" for c in TEXTO},
    )
    df.columns = [c.strip().lower() for c in df.columns]
    faltan = [c for c in COLUMNAS if c not in df.columns]
    if faltan:
        log.warning("%s: columnas ausentes, se crean vacías: %s", archivo.name, ", ".join(faltan))
        for c in faltan:
            df[c] = pd.NA
    df = df[COLUMNAS].copy()
    # Esquema fijo para todos los meses: códigos como texto y el resto numérico (lo no convertible, vacío).
    for c in COLUMNAS:
        if c in TEXTO:
            df[c] = df[c].astype("string").str.strip()
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    return df


def procesar_mes(archivo: Path, m: Mes, salida: Path) -> Path:
    """Escribe el mes en Parquet (un archivo por periodo); reescribirlo da el mismo resultado."""
    df = leer_personas_zip(archivo)
    df["periodo"] = m.clave
    destino = salida / f"personas_{m.clave}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(destino, index=False)
    return destino


def ejecutar(
    desde: Mes, hasta: Mes, crudos: Path = DATOS_CRUDOS, procesados: Path = DATOS_PROCESADOS
) -> dict:
    manifiesto = Manifiesto(crudos / "manifiesto.json")
    resumen = {"ok": [], "no_publicado": [], "error": []}
    with requests.Session() as sesion:
        sesion.headers["User-Agent"] = "observatorio-laboral-ec (portafolio de datos)"
        for m in rango(desde, hasta):
            try:
                archivo = descargar_mes(m, crudos / "enemdu", manifiesto, sesion)
                procesar_mes(archivo, m, procesados / "personas")
                resumen["ok"].append(m.clave)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    log.info("%s aún no está publicado", m.clave)
                    resumen["no_publicado"].append(m.clave)
                else:
                    log.error("%s: %s", m.clave, e)
                    resumen["error"].append(m.clave)
            except ValueError as e:
                log.error("%s", e)
                resumen["error"].append(m.clave)
    return resumen


def main() -> None:
    p = argparse.ArgumentParser(description="Descarga y procesa los microdatos mensuales de la ENEMDU.")
    p.add_argument("--desde", default="2023-01", help="AAAA-MM (por defecto 2023-01)")
    p.add_argument("--hasta", default="actual", help="AAAA-MM o «actual» (por defecto: el mes en curso)")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    r = ejecutar(Mes.desde_texto(a.desde), Mes.desde_texto(a.hasta))
    print(json.dumps({k: len(v) for k, v in r.items()}), "| errores:", r["error"] or "ninguno")
    raise SystemExit(1 if r["error"] else 0)


if __name__ == "__main__":
    main()
