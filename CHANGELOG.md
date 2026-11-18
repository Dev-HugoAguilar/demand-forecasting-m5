# Historial de cambios

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
las versiones usan [Versionado Semántico](https://semver.org/lang/es/).

## [1.0.0] — 2026-11-26

### Añadido

- Primera publicación como repositorio independiente.
- Pipeline de pronóstico a 28 días con etapas separadas de importación,
  entrenamiento, pronóstico y agregación.
- Modelo global de LightGBM condicionado al horizonte, con comparación de objetivo
  frente a `tweedie` y baseline estacional semanal.
- Protocolo temporal: cortes de desarrollo para elegir variantes por WAPE y cortes
  reservados para la evaluación final.
- Evaluación por horizonte con WAPE, MAE, sesgo y número de ventanas; backtesting
  en ventanas completas de 28 días.
- Ocho pruebas de contrato estático que fijan el horizonte, las etapas y la
  ausencia de rutas absolutas.
- Capa de visualización React + TypeScript incluida como fuente.
- Documentación de metodología, datos, arquitectura y límites.

### Nota

Los CSV de M5 no se redistribuyen. El pipeline requiere MongoDB y un sistema Unix;
el repositorio declara ese estado en lugar de prometer una ejecución que no puede
ofrecer.
