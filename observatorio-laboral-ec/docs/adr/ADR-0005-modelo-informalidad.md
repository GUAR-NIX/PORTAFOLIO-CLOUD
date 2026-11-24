# ADR-0005 · Modelo de probabilidad de informalidad

**Estado:** aceptada · **Fecha:** 2026-11-24

## Contexto
La mitad de los ocupados del Ecuador trabaja en el sector informal. La tasa oficial dice *cuántos*; un modelo a
nivel de persona permite estudiar *quiénes* tienen más probabilidad de serlo, y con qué peso influye cada
característica. Hay que evitar los errores típicos: fuga de información, validación aleatoria sobre una encuesta que
se repite mes a mes y métricas que ignoran el diseño muestral.

## Decisión
- **Población y objetivo con las definiciones oficiales del INEC**: ocupados de 15 años o más (`condact` 1-6);
  objetivo `secemp == 2` (sector informal). Así el modelo es comparable con la tasa publicada.
- **Variables**: edad, sexo, estado civil, nivel de instrucción, área, provincia, rama de actividad y ocupación.
  **El ingreso se excluye**: es consecuencia de la informalidad, no causa, e incluirlo inflaría las métricas.
- **Validación temporal**: entrenamiento ene-2023 a may-2025 (29 meses), validación jun-nov 2025 (parada temprana),
  prueba dic-2025 a may-2026, usada una sola vez. Una partición aleatoria mezclaría meses y hogares que la
  encuesta vuelve a visitar.
- **Factor de expansión** como peso de entrenamiento (normalizado a media 1) y en todas las métricas: el desempeño
  se mide sobre la población, no sobre la muestra.
- **Dos modelos**: regresión logística con *splines* de edad (referencia interpretable) y **LightGBM** con variables
  categóricas nativas (modelo principal). Se elige por AUC, *log loss* y calibración en validación.
- **Explicabilidad y equidad**: SHAP (TreeExplainer) para la importancia global y el efecto de cada categoría;
  métricas por sexo y por área para comprobar que el modelo no funciona peor para un grupo.
- **Artefactos**: métricas y figuras en `reports/modelo_informalidad/` (versionadas); el modelo entrenado
  (`models/*.joblib`) no se versiona: se regenera con `scripts/entrenar_informalidad.py` en unos segundos.

## Consecuencias
- Es un modelo **descriptivo/predictivo, no causal**: SHAP explica qué usa el modelo, no qué *causa* la
  informalidad.
- El trabajo doméstico remunerado tiene su propia categoría (`secemp = 3`), que por definición no es «sector
  informal»; por eso «Hogares como empleadores» aparece con un efecto muy negativo.
- La Fase 8 (MLOps) registrará estos experimentos en MLflow y servirá el modelo por API.
