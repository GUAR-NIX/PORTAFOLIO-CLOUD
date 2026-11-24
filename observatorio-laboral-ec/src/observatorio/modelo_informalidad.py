"""Fase 6 · Modelo de probabilidad de informalidad laboral (ENEMDU, INEC).

Pregunta: dado el perfil de una persona ocupada, ¿qué probabilidad tiene de trabajar en el sector informal?

Decisiones (detalle en docs/adr/ADR-0005-modelo-informalidad.md):
- Población: personas de 15 años o más con empleo (`condact` 1-6), igual que el denominador oficial del INEC.
- Objetivo: `secemp == 2` (sector informal), la misma definición de la tasa oficial de informalidad.
- Variables: solo características de la persona y de su trabajo. El ingreso queda fuera: es una
  consecuencia de la informalidad, no una causa, y usarlo inflaría las métricas (fuga de información).
- Validación temporal: entrenamiento, validación y prueba son meses distintos y consecutivos; la prueba
  son los últimos 6 meses y solo se usa una vez, al final.
- Métricas ponderadas por el factor de expansión (`fexp`): miden el desempeño sobre la población, no
  sobre la muestra.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

OBJETIVO = "informal"
PESO = "fexp"
NUMERICAS = ["edad"]
CATEGORICAS = ["sexo", "estado_civil", "nivel_instruccion", "area", "provincia", "rama", "ocupacion"]
VARIABLES = NUMERICAS + CATEGORICAS

# Etiquetas legibles (diccionario de la ENEMDU) para las explicaciones.
SEXO = {1: "Hombre", 2: "Mujer"}
AREA = {1: "Urbana", 2: "Rural"}
ESTADO_CIVIL = {1: "Casado(a)", 2: "Separado(a)", 3: "Divorciado(a)", 4: "Viudo(a)",
                5: "Unión libre", 6: "Soltero(a)"}
NIVEL = {1: "Ninguno", 2: "Centro de alfabetización", 3: "Educación básica",
         4: "Educación media/bachillerato", 5: "Superior"}
OCUPACION = {1: "Directores y gerentes", 2: "Profesionales científicos e intelectuales",
             3: "Técnicos y profesionales de nivel medio", 4: "Personal de apoyo administrativo",
             5: "Trabajadores de servicios y vendedores",
             6: "Agricultores y trabajadores agropecuarios calificados",
             7: "Oficiales, operarios y artesanos", 8: "Operadores de instalaciones y máquinas",
             9: "Ocupaciones elementales", 10: "Fuerzas armadas"}
RAMA = {1: "Agricultura, ganadería y pesca", 2: "Minas y canteras", 3: "Manufactura",
        4: "Electricidad y gas", 5: "Agua y saneamiento", 6: "Construcción", 7: "Comercio",
        8: "Transporte y almacenamiento", 9: "Alojamiento y comidas", 10: "Información y comunicación",
        11: "Actividades financieras", 12: "Actividades inmobiliarias", 13: "Actividades profesionales",
        14: "Servicios administrativos y de apoyo", 15: "Administración pública y defensa", 16: "Enseñanza",
        17: "Salud y asistencia social", 18: "Artes y entretenimiento", 19: "Otros servicios",
        20: "Hogares como empleadores", 21: "Organizaciones extraterritoriales"}
SEEDS_PROVINCIAS = Path(__file__).resolve().parents[2] / "dbt" / "seeds" / "provincias.csv"


def nombres_provincias(ruta: Path = SEEDS_PROVINCIAS) -> dict[str, str]:
    """Código de dos dígitos → nombre, desde el seed de dbt (una sola fuente de verdad)."""
    if not ruta.exists():
        return {}
    s = pd.read_csv(ruta, dtype=str)
    cod = next(c for c in s.columns if "cod" in c.lower())
    nom = next(c for c in s.columns if c.lower() in {"provincia", "nombre"})
    return dict(zip(s[cod].str.zfill(2), s[nom], strict=True))


@dataclass(frozen=True)
class Particion:
    """Cortes temporales (periodos AAAAMM, inclusivos)."""

    fin_entrenamiento: str = "202505"
    fin_validacion: str = "202511"


def construir_dataset(personas: pd.DataFrame, provincias: dict[str, str] | None = None) -> pd.DataFrame:
    """Filtra la población ocupada y construye variables y objetivo a partir de la tabla de personas."""
    provincias = nombres_provincias() if provincias is None else provincias
    df = personas[(personas["p03"] >= 15) & personas["condact"].between(1, 6)].copy()
    df = df[df["fexp"].notna() & (df["fexp"] > 0) & df["secemp"].notna()]
    ciudad = df["ciudad"].astype("string").str.strip().str.zfill(6)
    salida = pd.DataFrame(
        {
            "periodo": df["periodo"].astype("string"),
            "edad": df["p03"].astype("float64"),
            "sexo": df["p02"].map(SEXO),
            "estado_civil": df["p06"].map(ESTADO_CIVIL),
            "nivel_instruccion": df["nnivins"].map(NIVEL),
            "area": df["area"].map(AREA),
            "provincia": ciudad.str[:2].map(lambda c: provincias.get(c, c)),
            "rama": df["rama1"].map(RAMA),
            "ocupacion": df["grupo1"].map(OCUPACION),
            PESO: df["fexp"].astype("float64"),
            OBJETIVO: (df["secemp"] == 2).astype("int8"),
        }
    )
    for c in CATEGORICAS:
        salida[c] = salida[c].astype("string").fillna("Sin dato").astype("category")
    return salida.reset_index(drop=True)


def leer_meses(carpeta: Path) -> pd.DataFrame:
    """Lee todos los Parquet mensuales de personas y construye el dataset de modelado."""
    columnas = ["periodo", "p02", "p03", "p06", "nnivins", "area", "ciudad", "rama1", "grupo1",
                "condact", "secemp", "fexp"]
    archivos = sorted(carpeta.glob("personas_*.parquet"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos personas_*.parquet en {carpeta}")
    provincias = nombres_provincias()
    partes = [construir_dataset(pd.read_parquet(a, columns=columnas), provincias) for a in archivos]
    df = pd.concat(partes, ignore_index=True)
    for c in CATEGORICAS:  # unificar categorías entre meses
        df[c] = df[c].astype("string").astype("category")
    return df


def particionar(df: pd.DataFrame, p: Particion = Particion()) -> dict[str, pd.DataFrame]:
    """Partición temporal: sin mezclar meses entre conjuntos."""
    return {
        "entrenamiento": df[df["periodo"] <= p.fin_entrenamiento],
        "validacion": df[(df["periodo"] > p.fin_entrenamiento) & (df["periodo"] <= p.fin_validacion)],
        "prueba": df[df["periodo"] > p.fin_validacion],
    }


def tasa_ponderada(y: np.ndarray | pd.Series, w: np.ndarray | pd.Series) -> float:
    """Proporción expandida (como el INEC): suma de pesos de los positivos ÷ suma de pesos."""
    y, w = np.asarray(y, dtype=float), np.asarray(w, dtype=float)
    return float((y * w).sum() / w.sum())


def metricas(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> dict[str, float]:
    """Métricas ponderadas por el factor de expansión."""
    from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

    return {
        "auc_roc": float(roc_auc_score(y, p, sample_weight=w)),
        "auc_pr": float(average_precision_score(y, p, sample_weight=w)),
        "brier": float(brier_score_loss(y, p, sample_weight=w)),
        "log_loss": float(log_loss(y, p, sample_weight=w)),
        "tasa_observada_pct": 100 * tasa_ponderada(y, w),
        "tasa_estimada_pct": 100 * tasa_ponderada(p, w),
    }


def metricas_por_grupo(df: pd.DataFrame, p: np.ndarray, grupo: str) -> pd.DataFrame:
    """Desempeño y calibración por subgrupo (equidad): AUC y tasa observada vs. estimada."""
    filas = []
    for valor, idx in df.groupby(grupo, observed=True).groups.items():
        sub = df.loc[idx]
        pp = p[df.index.get_indexer(idx)]
        m = metricas(sub[OBJETIVO].to_numpy(), pp, sub[PESO].to_numpy())
        filas.append({grupo: valor, "n": len(sub), **{k: round(v, 4) for k, v in m.items()}})
    return pd.DataFrame(filas)
