"""Configuración leída del entorno: archivo .env en local y secretos de GitHub en CI.

Nunca hay credenciales en el código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
DATOS_CRUDOS = RAIZ / "data" / "raw"
DATOS_PROCESADOS = RAIZ / "data" / "processed"


@dataclass(frozen=True)
class ConfigBD:
    host: str
    puerto: int
    base: str
    usuario: str
    contrasena: str
    sslmode: str = "disable"

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.usuario}:{self.contrasena}@{self.host}:{self.puerto}/{self.base}"
            f"?sslmode={self.sslmode}"
        )


def config_bd() -> ConfigBD:
    """Lee la conexión a PostgreSQL. Falla con un mensaje claro si falta alguna variable."""
    load_dotenv(RAIZ / ".env")
    faltan = [v for v in ("PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD") if not os.getenv(v)]
    if faltan:
        raise RuntimeError(f"Faltan variables de entorno: {', '.join(faltan)} (copia .env.example como .env)")
    return ConfigBD(
        host=os.environ["PGHOST"],
        puerto=int(os.getenv("PGPORT", "5432")),
        base=os.environ["PGDATABASE"],
        usuario=os.environ["PGUSER"],
        contrasena=os.environ["PGPASSWORD"],
        sslmode=os.getenv("PGSSLMODE", "disable"),
    )
