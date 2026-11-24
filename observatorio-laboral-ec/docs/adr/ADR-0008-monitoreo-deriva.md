# ADR-0008 · Monitorización de deriva con PSI y desempeño mensual

**Estado:** aceptada · **Fecha:** 2026-11-24

## Contexto
El INEC publica un mes nuevo cada cierto tiempo y el pipeline lo carga solo. Hay que saber, sin revisar a mano,
si la población cambió lo suficiente como para que el modelo de informalidad deje de ser fiable.

## Decisión
- **PSI por variable**, con proporciones ponderadas por el factor de expansión, frente al periodo de entrenamiento;
  la edad se agrupa por deciles de la referencia. Umbrales estándar: 0,1 (vigilar) y 0,2 (deriva).
- **Desempeño mensual**: AUC ponderado y sesgo de calibración. La alerta de calibración usa la **media móvil de 3
  meses** porque un mes aislado puede desviarse ~2 puntos solo por ruido muestral.
- Umbrales iguales a los de la puerta de calidad del CI (ADR-0007), para que monitor y CI hablen el mismo idioma.
- Implementación propia en lugar de Evidently: son ~80 líneas, sin dependencias nuevas, y el PSI ponderado por el
  diseño muestral no viene de serie en esas herramientas.
- Se ejecuta en el **pipeline semanal** con `continue-on-error`: informa en el resumen de GitHub Actions, pero un
  fallo del monitor no detiene la carga de datos.

## Consecuencias
- La provincia muestra siempre el PSI más alto por la falta de representatividad mensual; se documenta para no
  confundirla con un cambio real.
- El monitor usa la copia publicada del modelo (`app/modelo/`); si se reentrena, hay que actualizarla.
