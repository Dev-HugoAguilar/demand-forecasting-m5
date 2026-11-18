# M5 Demand Forecasting

**Pipeline de pronóstico a 28 días** sobre el desafío M5 de Walmart: un modelo
global de LightGBM condicionado al horizonte, con un protocolo temporal explícito
—cortes de desarrollo para elegir variantes por WAPE y cortes reservados para la
evaluación final— y backtesting en ventanas completas de 28 días.

[![Pruebas](https://github.com/Dev-HugoAguilar/demand-forecasting-m5/actions/workflows/tests.yml/badge.svg)](https://github.com/Dev-HugoAguilar/demand-forecasting-m5/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Datos](https://img.shields.io/badge/datos%20M5-no%20redistribuidos-b7791f)](#estado-de-ejecución)

> **Estado de ejecución.** Este repositorio contiene el **pipeline completo**, no
> un cuaderno listo para correr. Ejecutarlo requiere los CSV de M5, una instancia
> de MongoDB y un sistema Unix (el paquete usa `resource`). Lo que sí se verifica
> en cada *push*: que los módulos compilen, que las etapas existan, que el
> horizonte sea 28 y que no se publiquen credenciales. Ver
> [`docs/DATOS.md`](docs/DATOS.md).

---

## Qué demuestra

- **Horizonte como invariante**: `DIAS_HORIZONTE = 28` vive en un solo lugar, el
  modelo lo hereda y una prueba falla si alguien lo cambia en silencio.
- **Selección sin fuga temporal**: las variantes compiten por WAPE en cortes de
  desarrollo; el modelo final se evalúa en cortes **reservados** que no
  participaron en la elección.
- **Evaluación por horizonte**: el error se reporta día 1 a 28 porque no es
  estable dentro de la ventana; un agregado único ocultaría el deterioro del tramo
  largo.
- **Ventanas completas**: si una ventana de 28 días no cabe en el calendario
  disponible se descarta, no se trunca.
- **Recorte declarado**: las predicciones negativas se llevan a cero, también al
  evaluar, y el efecto se documenta.

## Pipeline

```bash
git clone https://github.com/Dev-HugoAguilar/demand-forecasting-m5.git
cd demand-forecasting-m5
python -m pip install -r requirements.txt

python pipeline/importar_m5.py         # CSV de M5 → MongoDB
python pipeline/entrenar_m5.py --variantes   # cortes de desarrollo
python pipeline/entrenar_m5.py         # modelo final en cortes reservados
python pipeline/pronosticar_m5.py      # 28 días por serie
python pipeline/agregar_m5.py          # agregados para la interfaz
```

![Pantalla de modelado](docs/cover.jpg)

### Etapas

| Script | Función |
|---|---|
| `importar_m5.py` | Ingesta de las tablas del concurso y exportación compacta. |
| `entrenar_m5.py` | Variantes por corte, selección por WAPE y modelo final. |
| `pronosticar_m5.py` | Pronóstico a 28 días sobre el último origen disponible. |
| `agregar_m5.py` | Agregados que consume la interfaz. |
| `inventario_m5.py` | Inventario de series y cobertura de datos. |
| `derivar_planificacion.py` | Planificación a partir de los agregados. |
| `demo_sintetica_m5.py` | Demostración sin datos del concurso. |

## Modelo

| Decisión | Elección |
|---|---|
| Familia | LightGBM global, condicionado al horizonte |
| Objetivo | Se comparó con `tweedie` en una muestra y se conservó el mejor |
| Referencia | Baseline estacional semanal |
| Variables | Rezagos, medias y desviaciones por ventana, medias por día de semana |
| Precio | Último precio conocido de la semana para toda la ventana |
| Métricas | WAPE (selección), MAE, sesgo y número de ventanas |

Detalle completo en [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md).

## Estructura

```text
pipeline/                 Etapas ejecutables del pronóstico
lib/app/comercial/        Paquete de modelado (mismo espacio de nombres del backend)
app/                      Interfaz React + TypeScript (capa de visualización)
tests/test_pipeline.py    Contratos estáticos del método
docs/                     Metodología, datos y arquitectura
```

La interfaz **no** calcula el modelo: consume la API del portafolio
(`portfolio-api`). Se incluye como fuente para no perder la capa de visualización;
requiere `npm ci` y la API en ejecución. El corazón de este repositorio es el
pipeline.

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Ocho pruebas de contrato estático, sin importar el paquete `comercial` (depende de
MongoDB y de `resource`): horizonte de 28 días, herencia del horizonte en el
modelo, existencia y compilación de las cuatro etapas, declaración del protocolo
de variantes y ausencia de rutas absolutas.

## Datos y atribución

**M5 Forecasting — Accuracy** (Walmart, Kaggle). Los CSV no se redistribuyen y los
agregados derivados no se versionan. Condiciones y unidades en
[`docs/DATOS.md`](docs/DATOS.md). Este repositorio no incluye un archivo `LICENSE`
propio: se respetan los términos del concurso.

## Límites

- El WAPE de un corte no promete desempeño en otro periodo.
- WAPE pondera por volumen: las series pequeñas pesan poco aunque su error
  relativo sea alto.
- Superar al baseline semanal no implica haber capturado estructura causal.
- El recorte a cero mejora el error pero enmascara un problema de especificación.
- No hay servicio desplegado ni datos públicos para reproducir las cifras.

## Contribuir y seguridad

Convenciones en [`CONTRIBUTING.md`](CONTRIBUTING.md). Para reportar un problema,
usa los avisos privados de [`SECURITY.md`](SECURITY.md).
