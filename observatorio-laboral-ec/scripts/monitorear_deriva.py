"""Informe mensual de deriva de datos y desempeño del modelo de informalidad (Fase 10).

Uso: python scripts/monitorear_deriva.py [--resumen-markdown]
Necesita los Parquet de la ingesta y el modelo (models/ o la copia publicada en app/modelo/).
Salidas en reports/monitoreo/; con --resumen-markdown imprime una tabla para el resumen de GitHub Actions.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from observatorio.config import DATOS_PROCESADOS, RAIZ
from observatorio.modelo_informalidad import CATEGORICAS, OBJETIVO, PESO, VARIABLES, Particion, leer_meses
from observatorio.monitoreo import alerta_desempeno, deriva_por_mes, sesgo_movil
from observatorio.prediccion import artefacto

SALIDA = RAIZ / "reports" / "monitoreo"


def desempeno_por_mes(df: pd.DataFrame, a: dict) -> pd.DataFrame:
    from sklearn.metrics import roc_auc_score

    X = df[VARIABLES].copy()
    for c in CATEGORICAS:  # mismas categorías que vio el modelo; lo nuevo queda como desconocido
        X[c] = pd.Categorical(X[c].astype("string"), categories=a["categorias"][c])
    p = a["modelo"].predict_proba(X)[:, 1]
    filas = []
    for periodo, idx in df.groupby("periodo", observed=True).groups.items():
        sub, pp = df.loc[idx], p[df.index.get_indexer(idx)]
        w, y = sub[PESO].to_numpy(), sub[OBJETIVO].to_numpy()
        obs, est = 100 * np.average(y, weights=w), 100 * np.average(pp, weights=w)
        auc = float(roc_auc_score(y, pp, sample_weight=w))
        filas.append({"periodo": str(periodo), "auc": auc,
                      "tasa_observada_pct": obs, "tasa_estimada_pct": est})
    t = pd.DataFrame(filas).sort_values("periodo").reset_index(drop=True)
    t["sesgo_3m_pp"] = sesgo_movil(t["tasa_estimada_pct"], t["tasa_observada_pct"])
    t["alerta_modelo"] = [alerta_desempeno(a, s) for a, s in zip(t["auc"], t["sesgo_3m_pp"], strict=True)]
    return t


def figura(t: pd.DataFrame, fin_entrenamiento: str, ruta) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = pd.PeriodIndex(t["periodo"], freq="M").to_timestamp()
    corte = pd.Period(fin_entrenamiento, freq="M").to_timestamp()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
    a1.plot(x, t["psi_maximo"], "o-", ms=3, color="#2a78d6", label="PSI máximo entre variables")
    a1.axhline(0.1, ls=":", color="#898781")
    a1.axhline(0.2, ls="--", color="#e34948", label="Umbral de deriva (0,2)")
    a1.set_ylabel("PSI")
    a1.set_title("Deriva de datos frente al periodo de entrenamiento")
    a1.legend(frameon=False, fontsize=8)
    a2.plot(x, t["auc"], "o-", ms=3, color="#2a78d6", label="AUC mensual")
    a2.axhline(0.88, ls="--", color="#e34948", label="Mínimo aceptable (0,88)")
    a2.set_ylabel("AUC")
    a2.set_title("Desempeño del modelo mes a mes")
    a2.legend(frameon=False, fontsize=8, loc="lower left")
    for ax in (a1, a2):
        ax.axvspan(x.min(), corte, color="#e1e0d9", alpha=0.5, lw=0)
        ax.grid(alpha=0.3)
    a1.text(x.min(), a1.get_ylim()[1] * 0.92, " entrenamiento", fontsize=8, color="#52514e", va="top")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumen-markdown", action="store_true")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    df = leer_meses(DATOS_PROCESADOS / "personas")
    part = Particion()
    referencia = df[df["periodo"] <= part.fin_entrenamiento]
    a = artefacto()

    t = deriva_por_mes(df, referencia, CATEGORICAS).merge(desempeno_por_mes(df, a), on="periodo")
    t["en_entrenamiento"] = t["periodo"] <= part.fin_entrenamiento
    t.round(4).to_csv(SALIDA / "deriva_mensual.csv", index=False)
    figura(t, part.fin_entrenamiento, SALIDA / "deriva_mensual.png")

    fuera = t[~t["en_entrenamiento"]]
    ultimo = t.iloc[-1]
    resumen = {
        "version_modelo": a.get("version"),
        "ultimo_mes": ultimo["periodo"],
        "estado_datos_ultimo_mes": ultimo["estado_datos"],
        "psi_maximo_ultimo_mes": round(float(ultimo["psi_maximo"]), 4),
        "variable_mas_derivada": ultimo["variable_mas_derivada"],
        "auc_ultimo_mes": round(float(ultimo["auc"]), 4),
        "alerta_modelo_ultimo_mes": ultimo["alerta_modelo"],
        "meses_fuera_de_entrenamiento": len(fuera),
        "meses_con_deriva": int((fuera["estado_datos"] == "deriva").sum()),
        "meses_con_alerta_modelo": int((fuera["alerta_modelo"] == "reentrenar").sum()),
    }
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.resumen_markdown:
        print("## Monitor del modelo de informalidad\n")
        print(f"Modelo `{resumen['version_modelo']}` · último mes `{resumen['ultimo_mes']}`: datos "
              f"**{resumen['estado_datos_ultimo_mes']}** (PSI máx. {resumen['psi_maximo_ultimo_mes']:.3f}, "
              f"`{resumen['variable_mas_derivada']}`), modelo **{resumen['alerta_modelo_ultimo_mes']}** "
              f"(AUC {resumen['auc_ultimo_mes']:.3f}).\n")
        print("| Mes | PSI máx. | Variable | Datos | AUC | Observada | Estimada | Modelo |")
        print("|---|---|---|---|---|---|---|---|")
        for _, r in fuera.tail(6).iterrows():
            print(f"| {r['periodo']} | {r['psi_maximo']:.3f} | {r['variable_mas_derivada']} | "
                  f"{r['estado_datos']} | {r['auc']:.3f} | {r['tasa_observada_pct']:.1f} % | "
                  f"{r['tasa_estimada_pct']:.1f} % | {r['alerta_modelo']} |")
    else:
        print(t.round(3).to_string(index=False))
        print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
