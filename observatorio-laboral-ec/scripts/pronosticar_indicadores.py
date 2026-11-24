"""Backtesting y pronóstico a 3 meses de la tasa de desempleo y de informalidad (Fase 7).

Uso: python scripts/pronosticar_indicadores.py
Salidas en reports/pronostico/: backtest, resumen de errores, pronóstico con intervalos y figuras.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from observatorio.config import DATOS_PROCESADOS, RAIZ  # noqa: E402
from observatorio.indicadores import tasas  # noqa: E402
from observatorio.pronostico import MODELOS, backtest, intervalos, resumen  # noqa: E402

SALIDA = RAIZ / "reports" / "pronostico"
HORIZONTE, ORIGENES, NIVEL = 3, 12, 0.8
SERIES = {"tasa_desempleo": "Tasa de desempleo", "tasa_empleo_sector_informal": "Tasa de informalidad"}
NOMBRES = {"ingenuo": "Último valor", "estacional_ingenuo": "Mismo mes del año anterior",
           "media_movil_3": "Media de 3 meses", "ets": "Suavizado exponencial", "sarima": "SARIMA"}


def serie_mensual() -> pd.DataFrame:
    columnas = ["periodo", "p03", "condact", "secemp", "fexp"]
    df = pd.read_parquet(DATOS_PROCESADOS / "personas", columns=columnas)
    filas = [{"periodo": str(p), **tasas(g)} for p, g in df.groupby("periodo", observed=True)]
    s = pd.DataFrame(filas).sort_values("periodo")
    s.index = pd.PeriodIndex(s.pop("periodo"), freq="M")
    return s


def figura(y: pd.Series, futuro: pd.DataFrame, titulo: str, ruta) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = y.index.to_timestamp()
    ax.plot(x, y.to_numpy(), "o-", ms=3, label="Observado (microdatos ENEMDU)")
    xf = futuro.index.to_timestamp()
    ax.plot(xf, futuro["pronostico"], "s--", color="#c05621", label="Pronóstico")
    ax.fill_between(xf, futuro["inferior"], futuro["superior"], color="#c05621", alpha=0.2,
                    label=f"Intervalo {int(NIVEL * 100)} % (errores del backtest)")
    ax.set_title(titulo)
    ax.set_ylabel("%")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    s = serie_mensual()
    s.round(4).to_csv(SALIDA / "serie_mensual.csv", index_label="periodo")
    informe = {"meses": len(s), "desde": str(s.index.min()), "hasta": str(s.index.max()),
               "horizonte": HORIZONTE, "origenes": ORIGENES, "nivel_intervalo": NIVEL, "series": {}}

    for col, titulo in SERIES.items():
        y = s[col]
        bt = backtest(y, MODELOS, HORIZONTE, ORIGENES)
        r = resumen(bt)
        bt.to_csv(SALIDA / f"backtest_{col}.csv", index=False)
        r.round(4).to_csv(SALIDA / f"errores_{col}.csv", index=False)

        medios = r.groupby("modelo")["mae_medio"].first().sort_values()
        mejor = medios.index[0]
        semi = intervalos(bt, mejor, NIVEL)
        pred = MODELOS[mejor](y.to_numpy(dtype=float), HORIZONTE)
        idx = pd.period_range(y.index[-1] + 1, periods=HORIZONTE, freq="M")
        futuro = pd.DataFrame({"pronostico": pred}, index=idx)
        futuro["inferior"] = [p - semi[h + 1] for h, p in enumerate(pred)]
        futuro["superior"] = [p + semi[h + 1] for h, p in enumerate(pred)]
        futuro.round(3).to_csv(SALIDA / f"pronostico_{col}.csv", index_label="periodo")
        figura(y, futuro, f"{titulo}: pronóstico a {HORIZONTE} meses ({NOMBRES[mejor].lower()})",
               SALIDA / f"pronostico_{col}.png")

        informe["series"][col] = {
            "mae_medio_pp": {m: round(float(v), 3) for m, v in medios.items()},
            "mejor_modelo": mejor,
            "mejora_sobre_ingenuo_pct": round(100 * (1 - medios[mejor] / medios["ingenuo"]), 1),
            "pronostico": {str(p): {k: round(float(v), 2) for k, v in fila.items()}
                           for p, fila in futuro.iterrows()},
        }
        print(f"\n{titulo}: MAE medio (pp) por modelo")
        print(medios.round(3).to_string())
        print(futuro.round(2).to_string())

    (SALIDA / "resumen.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
