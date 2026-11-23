import pytest

from observatorio import config


def test_url_se_construye_desde_el_entorno(monkeypatch):
    entorno = {"PGHOST": "h", "PGPORT": "6543", "PGDATABASE": "b", "PGUSER": "u", "PGPASSWORD": "p"}
    for k, v in entorno.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("PGSSLMODE", "require")
    c = config.config_bd()
    assert c.url == "postgresql+psycopg://u:p@h:6543/b?sslmode=require"


def test_falla_con_mensaje_claro_si_falta_la_contrasena(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    for k in ("PGHOST", "PGDATABASE", "PGUSER"):
        monkeypatch.setenv(k, "x")
    monkeypatch.delenv("PGPASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="PGPASSWORD"):
        config.config_bd()
