# ruff: noqa: E501  (textos largos: partirlos no los hace más legibles)
"""Textos de la app en español e inglés.

El modelo trabaja siempre con las categorías originales en español; aquí solo se traduce lo que se muestra.
"""

from __future__ import annotations

IDIOMAS = {"es": "Español", "en": "English"}

TEXTOS = {
    "es": {
        "titulo": "Observatorio laboral del Ecuador",
        "subtitulo": "Microdatos de la ENEMDU (INEC) · enero 2023 – mayo 2026 · "
                     "[código y metodología]({repo}) · [tablero público]({tablero})",
        "idioma": "Idioma",
        "pestanas": ["🧮 Simulador de informalidad", "📈 Pronóstico", "ℹ️ Sobre el modelo"],
        "intro": "Describe a una **persona ocupada** y el modelo estima la probabilidad de que trabaje en el "
                 "**sector informal** (definición oficial del INEC), con los factores que más pesan.",
        "variables": {"edad": "Edad", "sexo": "Sexo", "estado_civil": "Estado civil",
                      "nivel_instruccion": "Nivel de instrucción", "area": "Área", "provincia": "Provincia",
                      "rama": "Rama de actividad", "ocupacion": "Ocupación"},
        "probabilidad": "Probabilidad de informalidad",
        "delta": "{d:+.0f} pts vs. promedio nacional",
        "promedio": "Promedio nacional (dic-2025 a may-2026)",
        "que_sube": "**¿Qué sube o baja la probabilidad de este perfil?** (valores SHAP del modelo)",
        "eje_factores": "← baja la probabilidad · sube la probabilidad →",
        "efecto": "Efecto",
        "aviso": "El modelo describe patrones de la encuesta; no explica causas ni sirve para decidir sobre "
                 "personas concretas. El trabajo doméstico remunerado es una categoría aparte en la ENEMDU.",
        "pronostico_intro": "Pronóstico a 3 meses con el modelo que ganó un **backtesting de origen móvil** "
                            "(12 cortes, sin ver el futuro): la **media de los últimos 3 meses**.",
        "desempleo": "Desempleo", "informalidad": "Informalidad",
        "eje_desempleo": "Tasa de desempleo", "eje_informalidad": "Tasa de informalidad",
        "intervalo": "Intervalo 80 %", "observado": "Observado", "pronostico": "Pronóstico",
        "errores": "**Error medio del backtesting (puntos porcentuales; menor es mejor)**",
        "modelos": {"ingenuo": "Último valor", "estacional_ingenuo": "Mismo mes año anterior",
                    "media_movil_3": "Media de 3 meses", "ets": "Suavizado exponencial", "sarima": "SARIMA"},
        "acerca": """
**Modelo:** LightGBM ({arboles} árboles) sobre {total} personas ocupadas de la ENEMDU ({entren} para entrenar),
evaluado en 6 meses que nunca vio (diciembre 2025 – mayo 2026), con métricas ponderadas por el factor de
expansión.

| Modelo | AUC-ROC | Brier |
|---|---|---|
| Sin modelo (tasa media) | {r_auc} | {r_brier} |
| Regresión logística | {l_auc} | {l_brier} |
| **LightGBM** | **{g_auc}** | **{g_brier}** |

No funciona peor para las mujeres ni para el área rural (AUC entre 0,89 y 0,93 por grupo). Más detalle en la
[ficha del modelo]({repo}/reports/modelo_informalidad).

**Privacidad:** los microdatos del INEC son anónimos y públicos; esta app no guarda lo que escribes.
""",
        "version": "Versión del modelo: {v}",
    },
    "en": {
        "titulo": "Ecuador Labor Observatory",
        "subtitulo": "ENEMDU microdata (INEC, Ecuador) · January 2023 – May 2026 · "
                     "[code and methodology]({repo}) · [public dashboard (Spanish)]({tablero})",
        "idioma": "Language",
        "pestanas": ["🧮 Informality simulator", "📈 Forecast", "ℹ️ About the model"],
        "intro": "Describe an **employed person** and the model estimates the probability that they work in the "
                 "**informal sector** (INEC's official definition), with the factors that matter most.",
        "variables": {"edad": "Age", "sexo": "Sex", "estado_civil": "Marital status",
                      "nivel_instruccion": "Education level", "area": "Area", "provincia": "Province",
                      "rama": "Industry", "ocupacion": "Occupation"},
        "probabilidad": "Probability of informality",
        "delta": "{d:+.0f} pts vs. national average",
        "promedio": "National average (Dec 2025 – May 2026)",
        "que_sube": "**What raises or lowers the probability for this profile?** (the model's SHAP values)",
        "eje_factores": "← lowers the probability · raises the probability →",
        "efecto": "Effect",
        "aviso": "The model describes patterns in the survey; it does not explain causes and must not be used to "
                 "make decisions about specific people. Paid domestic work is a separate category in ENEMDU.",
        "pronostico_intro": "3-month forecast with the model that won a **rolling-origin backtest** (12 cut-offs, "
                            "never seeing the future): the **mean of the last 3 months**.",
        "desempleo": "Unemployment", "informalidad": "Informality",
        "eje_desempleo": "Unemployment rate", "eje_informalidad": "Informality rate",
        "intervalo": "80% interval", "observado": "Observed", "pronostico": "Forecast",
        "errores": "**Mean backtest error (percentage points; lower is better)**",
        "modelos": {"ingenuo": "Last value", "estacional_ingenuo": "Same month last year",
                    "media_movil_3": "3-month mean", "ets": "Exponential smoothing", "sarima": "SARIMA"},
        "acerca": """
**Model:** LightGBM ({arboles} trees) on {total} employed people from ENEMDU ({entren} for training), evaluated on
6 months it had never seen (December 2025 – May 2026), with metrics weighted by the survey expansion factor.

| Model | AUC-ROC | Brier |
|---|---|---|
| No model (mean rate) | {r_auc} | {r_brier} |
| Logistic regression | {l_auc} | {l_brier} |
| **LightGBM** | **{g_auc}** | **{g_brier}** |

It does not perform worse for women or for rural areas (AUC between 0.89 and 0.93 by group). More detail in the
[model card (Spanish)]({repo}/reports/modelo_informalidad).

**Privacy:** INEC's microdata are anonymous and public; this app does not store what you enter.
""",
        "version": "Model version: {v}",
    },
}

# Categorías del modelo (en español) → inglés. Las provincias no se traducen.
CATEGORIAS_EN = {
    "Hombre": "Male", "Mujer": "Female", "Urbana": "Urban", "Rural": "Rural",
    "Casado(a)": "Married", "Separado(a)": "Separated", "Divorciado(a)": "Divorced", "Viudo(a)": "Widowed",
    "Unión libre": "Cohabiting", "Soltero(a)": "Single",
    "Ninguno": "None", "Centro de alfabetización": "Literacy center", "Educación básica": "Basic education",
    "Educación media/bachillerato": "Secondary / high school", "Superior": "Higher education",
    "Directores y gerentes": "Managers",
    "Profesionales científicos e intelectuales": "Professionals",
    "Técnicos y profesionales de nivel medio": "Technicians and associate professionals",
    "Personal de apoyo administrativo": "Clerical support workers",
    "Trabajadores de servicios y vendedores": "Service and sales workers",
    "Agricultores y trabajadores agropecuarios calificados": "Skilled agricultural workers",
    "Oficiales, operarios y artesanos": "Craft and related trades workers",
    "Operadores de instalaciones y máquinas": "Plant and machine operators",
    "Ocupaciones elementales": "Elementary occupations", "Fuerzas armadas": "Armed forces",
    "Agricultura, ganadería y pesca": "Agriculture, livestock and fishing",
    "Minas y canteras": "Mining and quarrying", "Manufactura": "Manufacturing",
    "Electricidad y gas": "Electricity and gas", "Agua y saneamiento": "Water and sanitation",
    "Construcción": "Construction", "Comercio": "Trade (wholesale and retail)",
    "Transporte y almacenamiento": "Transport and storage",
    "Alojamiento y comidas": "Accommodation and food services",
    "Información y comunicación": "Information and communication",
    "Actividades financieras": "Financial activities", "Actividades inmobiliarias": "Real estate",
    "Actividades profesionales": "Professional activities",
    "Servicios administrativos y de apoyo": "Administrative and support services",
    "Administración pública y defensa": "Public administration and defense", "Enseñanza": "Education",
    "Salud y asistencia social": "Health and social work",
    "Artes y entretenimiento": "Arts and entertainment", "Otros servicios": "Other services",
    "Hogares como empleadores": "Households as employers",
    "Organizaciones extraterritoriales": "Extraterritorial organizations",
}


def categoria(valor: str, idioma: str) -> str:
    """Texto que se muestra para una categoría; si no tiene traducción, la original."""
    return CATEGORIAS_EN.get(valor, valor) if idioma == "en" else valor


def miles(n: int, idioma: str) -> str:
    return f"{n:,}" if idioma == "en" else f"{n:,}".replace(",", ".")


def decimales(x: float, idioma: str, n: int = 3) -> str:
    return f"{x:.{n}f}" if idioma == "en" else f"{x:.{n}f}".replace(".", ",")
