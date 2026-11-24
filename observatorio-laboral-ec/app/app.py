"""Fase 9 · App pública del Observatorio laboral del Ecuador (español e inglés).

Ejecutar en local (desde observatorio-laboral-ec/):  streamlit run app/app.py
Usa el modelo de la Fase 6 (observatorio.prediccion) y los resultados del pronóstico de la Fase 7.
El idioma se elige en la app o con el enlace: ?lang=es / ?lang=en
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / "src"), str(Path(__file__).resolve().parent)]
from textos import IDIOMAS, TEXTOS, categoria, decimales, miles  # noqa: E402

from observatorio import prediccion as pred  # noqa: E402

PRONOSTICO = RAIZ / "reports" / "pronostico"
METRICAS = RAIZ / "reports" / "modelo_informalidad" / "metricas.json"
TABLERO = "https://datastudio.google.com/reporting/a932a4c2-ecc6-4148-afd1-df75157ebdb0"
REPO = "https://github.com/GUAR-NIX/PORTAFOLIO-CLOUD/tree/main/observatorio-laboral-ec"

# Paleta validada (skill dataviz, modo claro): azul = observado / baja, naranja = pronóstico, rojo = sube.
AZUL, NARANJA, ROJO = "#2a78d6", "#eb6834", "#e34948"
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#e1e0d9"
PERFIL_INICIAL = {"sexo": "Mujer", "estado_civil": "Soltero(a)",
                  "nivel_instruccion": "Educación media/bachillerato", "area": "Urbana",
                  "provincia": "Guayas", "rama": "Comercio",
                  "ocupacion": "Trabajadores de servicios y vendedores"}

st.set_page_config(page_title="Observatorio laboral del Ecuador · Labor Observatory", page_icon="📊",
                   layout="wide")


@st.cache_resource
def modelo() -> dict:
    return pred.artefacto()


def elegir_idioma() -> str:
    pedido = st.query_params.get("lang", "es")
    inicial = pedido if pedido in IDIOMAS else "es"
    elegido = st.segmented_control("Idioma / Language", list(IDIOMAS), default=inicial,
                                   format_func=IDIOMAS.get, label_visibility="collapsed")
    elegido = elegido or inicial
    if st.query_params.get("lang") != elegido:
        st.query_params["lang"] = elegido
    return elegido


def estilo(fig: go.Figure, alto: int) -> go.Figure:
    fig.update_layout(
        height=alto, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="#fcfcfb", paper_bgcolor="#fcfcfb",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=TINTA_2, size=13),
        hoverlabel=dict(bgcolor="white", font_color=TINTA), showlegend=False,
    )
    fig.update_xaxes(gridcolor=REJILLA, zeroline=False, linecolor="#c3c2b7")
    fig.update_yaxes(gridcolor=REJILLA, zeroline=False, linecolor="#c3c2b7")
    return fig


def grafico_factores(contrib: pd.Series, perfil: dict, t: dict, idioma: str) -> go.Figure:
    c = contrib.sort_values()
    etiquetas = [f"{t['variables'][v]}: {categoria(str(perfil[v]), idioma)}" for v in c.index]
    colores = [ROJO if x > 0 else AZUL for x in c.to_numpy()]
    fig = go.Figure(go.Bar(
        x=c.to_numpy(), y=etiquetas, orientation="h", marker=dict(color=colores, cornerradius=4),
        hovertemplate="%{y}<br>" + t["efecto"] + ": %{x:+.2f} (log-odds)<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#898781", line_width=1)
    fig.update_xaxes(title_text=t["eje_factores"])
    return estilo(fig, 360)


def grafico_pronostico(columna: str, titulo_eje: str, t: dict) -> go.Figure:
    serie = pd.read_csv(PRONOSTICO / "serie_mensual.csv")
    futuro = pd.read_csv(PRONOSTICO / f"pronostico_{columna}.csv")
    x_obs = pd.PeriodIndex(serie["periodo"], freq="M").to_timestamp()
    x_fut = pd.PeriodIndex(futuro["periodo"], freq="M").to_timestamp()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(x_fut) + list(x_fut[::-1]),
                             y=list(futuro["superior"]) + list(futuro["inferior"][::-1]),
                             mode="lines", fill="toself", fillcolor="rgba(235,104,52,0.18)",
                             line=dict(width=0), hoverinfo="skip", name=t["intervalo"]))
    fig.add_trace(go.Scatter(x=x_obs, y=serie[columna], mode="lines+markers", name=t["observado"],
                             line=dict(color=AZUL, width=2), marker=dict(size=5),
                             hovertemplate="%{x|%Y-%m}: %{y:.2f} %<extra>" + t["observado"] + "</extra>"))
    fig.add_trace(go.Scatter(x=x_fut, y=futuro["pronostico"], mode="lines+markers", name=t["pronostico"],
                             line=dict(color=NARANJA, width=2, dash="dash"), marker=dict(size=8),
                             customdata=futuro[["inferior", "superior"]],
                             hovertemplate="%{x|%Y-%m}: %{y:.2f} % (80 %: %{customdata[0]:.2f}–"
                                           "%{customdata[1]:.2f})<extra>" + t["pronostico"] + "</extra>"))
    fig.update_yaxes(title_text=titulo_eje, ticksuffix=" %")
    fig = estilo(fig, 380)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0))
    return fig


idioma = elegir_idioma()
t = TEXTOS[idioma]
st.title(f"📊 {t['titulo']}")
st.caption(t["subtitulo"].format(repo=REPO, tablero=TABLERO))

a = modelo()
op = pred.opciones(a)
simulador, pronostico, acerca = st.tabs(t["pestanas"])

with simulador:
    st.markdown(t["intro"])
    izq, der = st.columns([1, 1.4], gap="large")
    with izq:
        perfil: dict = {"edad": st.slider(t["variables"]["edad"], 15, 90, 28, key="edad")}
        for campo, defecto in PERFIL_INICIAL.items():
            valores = op[campo]
            perfil[campo] = st.selectbox(
                t["variables"][campo], valores, key=campo,
                index=valores.index(defecto) if defecto in valores else 0,
                format_func=lambda v: categoria(v, idioma),
            )
    with der:
        prob, contrib = pred.predecir(perfil, a)
        ref = a.get("tasa_referencia") or 0.54
        k1, k2 = st.columns(2)
        k1.metric(t["probabilidad"], f"{prob:.0%}", delta=t["delta"].format(d=(prob - ref) * 100),
                  delta_color="inverse")
        k2.metric(t["promedio"], f"{ref:.0%}")
        st.markdown(t["que_sube"])
        st.plotly_chart(grafico_factores(contrib, perfil, t, idioma), width="stretch",
                        config={"displayModeBar": False})
        st.caption(t["aviso"])

with pronostico:
    st.markdown(t["pronostico_intro"])
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t["desempleo"])
        st.plotly_chart(grafico_pronostico("tasa_desempleo", t["eje_desempleo"], t), width="stretch",
                        config={"displayModeBar": False})
    with c2:
        st.subheader(t["informalidad"])
        st.plotly_chart(grafico_pronostico("tasa_empleo_sector_informal", t["eje_informalidad"], t),
                        width="stretch", config={"displayModeBar": False})
    errores = json.loads((PRONOSTICO / "resumen.json").read_text(encoding="utf-8"))["series"]
    tabla = pd.DataFrame({s: v["mae_medio_pp"] for s, v in errores.items()})
    tabla.columns = [t["desempleo"], t["informalidad"]]
    tabla.index = tabla.index.map(t["modelos"])
    st.markdown(t["errores"])
    st.dataframe(tabla.round(3), width="stretch")

with acerca:
    m = json.loads(METRICAS.read_text(encoding="utf-8"))
    r, lo, g = (m["prueba"][k] for k in ("referencia_tasa_media", "regresion_logistica", "lightgbm"))
    st.markdown(t["acerca"].format(
        arboles=m["lgbm_iteraciones"], total=miles(m["datos"]["filas"], idioma),
        entren=miles(m["datos"]["particion"]["entrenamiento"]["filas"], idioma), repo=REPO,
        r_auc=decimales(r["auc_roc"], idioma), r_brier=decimales(r["brier"], idioma),
        l_auc=decimales(lo["auc_roc"], idioma), l_brier=decimales(lo["brier"], idioma),
        g_auc=decimales(g["auc_roc"], idioma), g_brier=decimales(g["brier"], idioma),
    ))
    st.caption(t["version"].format(v=a.get("version", "—")))
