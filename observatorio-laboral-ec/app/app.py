"""Fase 9 · App pública del Observatorio laboral del Ecuador.

Ejecutar en local (desde observatorio-laboral-ec/):  streamlit run app/app.py
Usa el modelo de la Fase 6 (observatorio.prediccion) y los resultados del pronóstico de la Fase 7.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from observatorio import prediccion as pred  # noqa: E402

PRONOSTICO = RAIZ / "reports" / "pronostico"
METRICAS = RAIZ / "reports" / "modelo_informalidad" / "metricas.json"
TABLERO = "https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0"
REPO = "https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/tree/main/observatorio-laboral-ec"

# Paleta validada (skill dataviz, modo claro): azul = observado / baja, naranja = pronóstico, rojo = sube.
AZUL, NARANJA, ROJO = "#2a78d6", "#eb6834", "#e34948"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#e1e0d9"
NOMBRES = {"edad": "Edad", "sexo": "Sexo", "estado_civil": "Estado civil",
           "nivel_instruccion": "Nivel de instrucción", "area": "Área", "provincia": "Provincia",
           "rama": "Rama de actividad", "ocupacion": "Ocupación"}

st.set_page_config(page_title="Observatorio laboral del Ecuador", page_icon="📊", layout="wide")


@st.cache_resource
def modelo() -> dict:
    return pred.artefacto()


def estilo(fig: go.Figure, alto: int) -> go.Figure:
    fig.update_layout(
        height=alto, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=TINTA_2, size=13),
        hoverlabel=dict(bgcolor="white", font_color=TINTA), showlegend=False,
    )
    fig.update_xaxes(gridcolor=REJILLA, zeroline=False, linecolor="#c3c2b7")
    fig.update_yaxes(gridcolor=REJILLA, zeroline=False, linecolor="#c3c2b7")
    return fig


def grafico_factores(contrib: pd.Series, perfil: dict) -> go.Figure:
    c = contrib.sort_values()
    etiquetas = [f"{NOMBRES[v]}: {perfil[v]}" for v in c.index]
    colores = [ROJO if x > 0 else AZUL for x in c.to_numpy()]
    fig = go.Figure(go.Bar(
        x=c.to_numpy(), y=etiquetas, orientation="h", marker=dict(color=colores, cornerradius=4),
        hovertemplate="%{y}<br>Efecto: %{x:+.2f} (log-odds)<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#898781", line_width=1)
    fig.update_xaxes(title_text="← baja la probabilidad · sube la probabilidad →")
    return estilo(fig, 360)


def grafico_pronostico(columna: str, titulo_eje: str) -> go.Figure:
    serie = pd.read_csv(PRONOSTICO / "serie_mensual.csv")
    futuro = pd.read_csv(PRONOSTICO / f"pronostico_{columna}.csv")
    x_obs = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()
    x_fut = pd.PeriodIndex(futuro["periodo"], freq="M").to_timestamp()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x_fut) + list(x_fut[::-1]),
                             y=list(futuro["superior"]) + list(futuro["inferior"][::-1]),
                             mode="lines", fill="toself", fillcolor="rgba(235,104,52,0.18)",
                             line=dict(width=0),
                             hoverinfo="skip", name="Intervalo 80 %"))
    fig.add_trace(go.Scatter(x=x_obs, y=serie[columna], mode="lines+markers", name="Observado",
                             line=dict(color=AZUL, width=2), marker=dict(size=5),
                             hovertemplate="%{x|%b %Y}: %{y:.2f} %<extra>Observado</extra>"))
    fig.add_trace(go.Scatter(x=x_fut, y=futuro["pronostico"], mode="lines+markers", name="Pronóstico",
                             line=dict(color=NARANJA, width=2, dash="dash"), marker=dict(size=8),
                             customdata=futuro[["inferior", "superior"]],
                             hovertemplate="%{x|%b %Y}: %{y:.2f} % (80 %: %{customdata[0]:.2f}–"
                                           "%{customdata[1]:.2f})<extra>Pronóstico</extra>"))
    fig.update_yaxes(title_text=titulo_eje, ticksuffix=" %")
    fig = estilo(fig, 380)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0))
    return fig


st.title("📊 Observatorio laboral del Ecuador")
st.caption("Microdatos de la ENEMDU (INEC) · enero 2023 – mayo 2026 · "
           f"[código y metodología]({REPO}) · [tablero público]({TABLERO})")

a = modelo()
op = pred.opciones(a)
simulador, pronostico, acerca = st.tabs(
    ["🧮 Simulador de informalidad", "📈 Pronóstico", "ℹ️ Sobre el modelo"]
)

with simulador:
    st.markdown("Describe a una **persona ocupada** y el modelo estima la probabilidad de que trabaje en el "
                "**sector informal** (definición oficial del INEC), con los factores que más pesan.")
    izq, der = st.columns([1, 1.4], gap="large")
    with izq:
        def eleccion(campo: str, defecto: str) -> str:
            valores = op[campo]
            return st.selectbox(NOMBRES[campo], valores,
                                index=valores.index(defecto) if defecto in valores else 0)

        perfil = {
            "edad": st.slider("Edad", 15, 90, 28),
            "sexo": eleccion("sexo", "Mujer"),
            "estado_civil": eleccion("estado_civil", "Soltero(a)"),
            "nivel_instruccion": eleccion("nivel_instruccion", "Educación media/bachillerato"),
            "area": eleccion("area", "Urbana"),
            "provincia": eleccion("provincia", "Guayas"),
            "rama": eleccion("rama", "Comercio"),
            "ocupacion": eleccion("ocupacion", "Trabajadores de servicios y vendedores"),
        }
    with der:
        prob, contrib = pred.predecir(perfil, a)
        ref = a.get("tasa_referencia") or 0.54
        k1, k2 = st.columns(2)
        k1.metric("Probabilidad de informalidad", f"{prob:.0%}",
                  delta=f"{(prob - ref) * 100:+.0f} pts vs. promedio nacional", delta_color="inverse")
        k2.metric("Promedio nacional (dic-2025 a may-2026)", f"{ref:.0%}")
        st.markdown("**¿Qué sube o baja la probabilidad de este perfil?** (valores SHAP del modelo)")
        st.plotly_chart(grafico_factores(contrib, perfil), width="stretch",
                        config={"displayModeBar": False})
        st.caption("El modelo describe patrones de la encuesta; no explica causas ni sirve para decidir "
                   "sobre personas concretas. El trabajo doméstico remunerado es una categoría aparte en "
                   "la ENEMDU.")

with pronostico:
    st.markdown("Pronóstico a 3 meses con el modelo que ganó un **backtesting de origen móvil** (12 cortes, "
                "sin ver el futuro): la **media de los últimos 3 meses**.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Desempleo")
        st.plotly_chart(grafico_pronostico("tasa_desempleo", "Tasa de desempleo"), width="stretch",
                        config={"displayModeBar": False})
    with c2:
        st.subheader("Informalidad")
        st.plotly_chart(grafico_pronostico("tasa_empleo_sector_informal", "Tasa de informalidad"),
                        width="stretch", config={"displayModeBar": False})
    errores = json.loads((PRONOSTICO / "resumen.json").read_text(encoding="utf-8"))["series"]
    tabla = pd.DataFrame({s: v["mae_medio_pp"] for s, v in errores.items()})
    tabla.columns = ["Desempleo", "Informalidad"]
    tabla.index = tabla.index.map({"ingenuo": "Último valor", "estacional_ingenuo": "Mismo mes año anterior",
                                   "media_movil_3": "Media de 3 meses", "ets": "Suavizado exponencial",
                                   "sarima": "SARIMA"})
    st.markdown("**Error medio del backtesting (puntos porcentuales; menor es mejor)**")
    st.dataframe(tabla.round(3), width="stretch")

with acerca:
    m = json.loads(METRICAS.read_text(encoding="utf-8"))
    p = m["prueba"]
    filas = f"{m['datos']['filas']:,}".replace(",", ".")
    ref_m, log_m, lgb_m = p["referencia_tasa_media"], p["regresion_logistica"], p["lightgbm"]
    st.markdown(f"""
**Modelo:** LightGBM ({m['lgbm_iteraciones']} árboles) entrenado con {filas} personas ocupadas
de la ENEMDU, evaluado en 6 meses que nunca vio (diciembre 2025 – mayo 2026), con métricas ponderadas por el
factor de expansión.

| Modelo | AUC-ROC | Brier |
|---|---|---|
| Sin modelo (tasa media) | {ref_m['auc_roc']:.3f} | {ref_m['brier']:.3f} |
| Regresión logística | {log_m['auc_roc']:.3f} | {log_m['brier']:.3f} |
| **LightGBM** | **{lgb_m['auc_roc']:.3f}** | **{lgb_m['brier']:.3f}** |

Funciona igual de bien para mujeres y hombres, y para el área urbana y rural. Más detalle en la
[ficha del modelo]({REPO}/reports/modelo_informalidad).

**Privacidad:** los microdatos del INEC son anónimos y públicos; esta app no guarda lo que escribes.
""")
    st.caption(f"Versión del modelo: {a.get('version', '—')}")
