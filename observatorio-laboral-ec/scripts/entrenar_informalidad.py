"""Entrena y evalúa el modelo de probabilidad de informalidad (Fase 6).

Uso: python scripts/entrenar_informalidad.py

Salidas:
- reports/modelo_informalidad/  → métricas (JSON/CSV) y figuras que se versionan en git.
- models/informalidad_lgbm.joblib → el modelo entrenado (no se versiona; se regenera con este script).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from sklearn.calibration import calibration_curve  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, SplineTransformer  # noqa: E402

from observatorio.config import DATOS_PROCESADOS, RAIZ  # noqa: E402
from observatorio.modelo_informalidad import (  # noqa: E402
    CATEGORICAS,
    NUMERICAS,
    OBJETIVO,
    PESO,
    VARIABLES,
    Particion,
    leer_meses,
    metricas,
    metricas_por_grupo,
    particionar,
    tasa_ponderada,
)

SEMILLA = 42
SALIDA = RAIZ / "reports" / "modelo_informalidad"
MODELOS = RAIZ / "models"
NOMBRES = {
    "edad": "Edad", "sexo": "Sexo", "estado_civil": "Estado civil",
    "nivel_instruccion": "Nivel de instrucción", "area": "Área", "provincia": "Provincia",
    "rama": "Rama de actividad", "ocupacion": "Ocupación",
}


def pesos(w: pd.Series) -> np.ndarray:
    """Factor de expansión normalizado a media 1 (mismo peso relativo, escala estable para el optimizador)."""
    return (w / w.mean()).to_numpy()


def entrenar_logistica(tr: pd.DataFrame) -> Pipeline:
    prep = ColumnTransformer([
        ("num", SplineTransformer(n_knots=5, degree=3), NUMERICAS),  # la edad no tiene efecto lineal
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), CATEGORICAS),
    ])
    modelo = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=2000, C=1.0))])
    modelo.fit(tr[VARIABLES], tr[OBJETIVO], clf__sample_weight=pesos(tr[PESO]))
    return modelo


def entrenar_lgbm(tr: pd.DataFrame, va: pd.DataFrame) -> lgb.LGBMClassifier:
    modelo = lgb.LGBMClassifier(
        n_estimators=3000, learning_rate=0.03, num_leaves=63, min_child_samples=200,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
        cat_smooth=20, random_state=SEMILLA, verbose=-1,
    )
    modelo.fit(
        tr[VARIABLES], tr[OBJETIVO], sample_weight=pesos(tr[PESO]),
        eval_X=(va[VARIABLES],), eval_y=(va[OBJETIVO],), eval_sample_weight=[pesos(va[PESO])],
        eval_metric="binary_logloss", categorical_feature=CATEGORICAS,
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    return modelo


def figura_tasa_mensual(te: pd.DataFrame, p: np.ndarray, ruta: Path) -> pd.DataFrame:
    filas = []
    for periodo, idx in te.groupby("periodo").groups.items():
        sub = te.loc[idx]
        filas.append({
            "periodo": periodo,
            "tasa_observada_pct": 100 * tasa_ponderada(sub[OBJETIVO], sub[PESO]),
            "tasa_estimada_pct": 100 * tasa_ponderada(p[te.index.get_indexer(idx)], sub[PESO]),
        })
    t = pd.DataFrame(filas).sort_values("periodo")
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(t["periodo"], t["tasa_observada_pct"], "o-", label="Observada (microdatos, como el INEC)")
    ax.plot(t["periodo"], t["tasa_estimada_pct"], "s--", label="Estimada por el modelo")
    ax.set_ylabel("Informalidad (%)")
    ax.set_title("Meses de prueba: informalidad observada vs. estimada")
    ax.set_ylim(40, 65)
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return t


def figura_calibracion(y: np.ndarray, p: np.ndarray, w: np.ndarray, ruta: Path) -> None:
    rng = np.random.default_rng(SEMILLA)
    idx = rng.choice(len(y), size=len(y), p=w / w.sum())  # remuestreo por peso: calibración poblacional
    frac, media = calibration_curve(y[idx], p[idx], n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    ax.plot([0, 1], [0, 1], ":", color="grey", label="Calibración perfecta")
    ax.plot(media, frac, "o-", label="LightGBM")
    ax.set_xlabel("Probabilidad predicha")
    ax.set_ylabel("Proporción observada de informales")
    ax.set_title("Calibración (meses de prueba)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def explicar(modelo: lgb.LGBMClassifier, te: pd.DataFrame, ruta_dir: Path) -> dict:
    """SHAP sobre una muestra de la prueba: importancia global y efecto medio de cada categoría."""
    muestra = te.sample(n=min(6000, len(te)), random_state=SEMILLA)
    X = muestra[VARIABLES]
    valores = shap.TreeExplainer(modelo).shap_values(X)
    if isinstance(valores, list):  # versiones antiguas devuelven [clase0, clase1]
        valores = valores[1]
    sv = pd.DataFrame(valores, columns=VARIABLES, index=X.index)

    importancia = sv.abs().mean().sort_values()
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.barh([NOMBRES[c] for c in importancia.index], importancia.to_numpy(), color="#2b6cb0")
    ax.set_xlabel("Impacto medio |SHAP| (log-odds)")
    ax.set_title("¿Qué pesa más al estimar la informalidad?")
    fig.tight_layout()
    fig.savefig(ruta_dir / "shap_importancia.png", dpi=150)
    plt.close(fig)

    efectos = {}
    for var in ["nivel_instruccion", "ocupacion", "rama", "area"]:
        e = sv[var].groupby(X[var], observed=True).agg(["mean", "size"])
        e = e[e["size"] >= 30].sort_values("mean")
        efectos[var] = {str(k): round(float(v), 3) for k, v in e["mean"].items()}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, var in zip(axes, ["nivel_instruccion", "ocupacion"], strict=True):
        e = pd.Series(efectos[var])
        colores = ["#c53030" if v > 0 else "#2f855a" for v in e.to_numpy()]
        ax.barh(e.index, e.to_numpy(), color=colores)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_title(f"Efecto de «{NOMBRES[var]}»")
        ax.set_xlabel("SHAP medio (→ más informal)")
        ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    fig.savefig(ruta_dir / "shap_categorias.png", dpi=150)
    plt.close(fig)

    edad = pd.DataFrame({"edad": X["edad"], "shap": sv["edad"]}).groupby("edad")["shap"].mean()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.plot(edad.index, edad.rolling(5, center=True, min_periods=1).mean().to_numpy(), color="#2b6cb0")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Edad")
    ax.set_ylabel("SHAP medio (→ más informal)")
    ax.set_title("Efecto de la edad (con todo lo demás igual)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ruta_dir / "shap_edad.png", dpi=150)
    plt.close(fig)

    return {"importancia_media_abs_shap": {k: round(float(v), 4) for k, v in importancia[::-1].items()},
            "efecto_medio_por_categoria": efectos}


def main() -> None:
    inicio = time.time()
    SALIDA.mkdir(parents=True, exist_ok=True)
    MODELOS.mkdir(parents=True, exist_ok=True)

    df = leer_meses(DATOS_PROCESADOS / "personas")
    partes = particionar(df, Particion())
    tr, va, te = partes["entrenamiento"], partes["validacion"], partes["prueba"]
    te = te.reset_index(drop=True)
    print({k: f"{len(v):,} filas, {v['periodo'].nunique()} meses" for k, v in partes.items()})

    logit = entrenar_logistica(tr)
    lgbm = entrenar_lgbm(tr, va)

    y, w = te[OBJETIVO].to_numpy(), te[PESO].to_numpy()
    p_logit = logit.predict_proba(te[VARIABLES])[:, 1]
    p_lgbm = lgbm.predict_proba(te[VARIABLES])[:, 1]
    base = np.full(len(te), tasa_ponderada(tr[OBJETIVO], tr[PESO]))  # «predecir la tasa media»

    resultados = {
        "datos": {
            "meses": int(df["periodo"].nunique()),
            "filas": int(len(df)),
            "particion": {
                k: {"filas": int(len(v)), "desde": str(v["periodo"].min()), "hasta": str(v["periodo"].max())}
                for k, v in partes.items()
            },
        },
        "variables": VARIABLES,
        "lgbm_iteraciones": int(lgbm.best_iteration_),
        "prueba": {
            "referencia_tasa_media": metricas(y, base, w),
            "regresion_logistica": metricas(y, p_logit, w),
            "lightgbm": metricas(y, p_lgbm, w),
        },
    }

    por_grupo = pd.concat(
        [metricas_por_grupo(te, p_lgbm, g).rename(columns={g: "grupo"}).assign(variable=g)
         for g in ["sexo", "area"]],
        ignore_index=True,
    )[["variable", "grupo", "n", "auc_roc", "brier", "tasa_observada_pct", "tasa_estimada_pct"]]
    por_grupo.to_csv(SALIDA / "equidad_por_grupo.csv", index=False)

    mensual = figura_tasa_mensual(te, p_lgbm, SALIDA / "tasa_mensual_prueba.png")
    mensual.round(2).to_csv(SALIDA / "tasa_mensual_prueba.csv", index=False)
    figura_calibracion(y, p_lgbm, w, SALIDA / "calibracion.png")
    resultados["explicacion"] = explicar(lgbm, te, SALIDA)
    resultados["segundos"] = round(time.time() - inicio, 1)

    texto = json.dumps(resultados, indent=2, ensure_ascii=False)
    (SALIDA / "metricas.json").write_text(texto, encoding="utf-8")
    joblib.dump({"modelo": lgbm, "variables": VARIABLES, "categoricas": CATEGORICAS,
                 "categorias": {c: list(df[c].cat.categories) for c in CATEGORICAS}},
                MODELOS / "informalidad_lgbm.joblib")

    for nombre, m in resultados["prueba"].items():
        print(f"{nombre:24s}", {k: round(v, 4) for k, v in m.items()})
    print(por_grupo.to_string(index=False))
    print(mensual.round(2).to_string(index=False))
    print(f"listo en {resultados['segundos']} s")


if __name__ == "__main__":
    main()
