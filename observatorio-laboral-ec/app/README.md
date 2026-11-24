# App pública · Observatorio laboral del Ecuador

**👉 [observatorio-laboral-ec.streamlit.app](https://observatorio-laboral-ec.streamlit.app)** (Streamlit Community
Cloud, se redespliega sola con cada push a `main`).

App en Streamlit con tres pestañas:

1. **Simulador de informalidad**: describes a una persona ocupada (edad, sexo, estado civil, instrucción, área,
   provincia, rama y ocupación) y ves la probabilidad de que trabaje en el sector informal, comparada con el promedio
   nacional, y qué variables la suben o la bajan (valores SHAP del modelo de la
   [Fase 6](../reports/modelo_informalidad/README.md)).
2. **Pronóstico**: desempleo e informalidad a 3 meses con su intervalo y la tabla de errores del backtesting
   ([Fase 7](../reports/pronostico/README.md)).
3. **Sobre el modelo**: métricas, equidad, versión y privacidad.

La lógica de predicción es la misma que usa la API ([`prediccion.py`](../src/observatorio/prediccion.py)).

## Ejecutar en local
```powershell
pip install -r app/requirements.txt
streamlit run app/app.py        # desde observatorio-laboral-ec/ → http://localhost:8501
```

## Publicar en Streamlit Community Cloud (gratis)
1. Entrar en <https://share.streamlit.io> con la cuenta de GitHub.
2. **Create app** → repositorio `GUAR-NIX/PORTAFOLIO-CLOUD`, rama `main`, archivo
   `observatorio-laboral-ec/app/app.py`.
3. Streamlit instala `app/requirements.txt` y usa la copia del modelo en `app/modelo/`.

`app/modelo/informalidad_lgbm.joblib` es una copia publicada del modelo (4 MB) para que la app funcione en la nube
sin los microdatos. Para actualizarla: reentrenar con `scripts/entrenar_informalidad.py` y copiar el archivo.

## Diseño
Paleta validada para daltonismo: azul para lo observado y los factores que bajan la probabilidad, naranja para
el pronóstico, rojo para los factores que la suben; cada gráfico lleva texto y leyenda, nunca solo color.
