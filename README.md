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
python -m pip install -e lib                 # paquete app.comercial / app.config / app.db.mongo

python pipeline/importar_m5.py         # CSV de M5 → MongoDB
python pipeline/entrenar_m5.py --variantes   # cortes de desarrollo
python pipeline/entrenar_m5.py         # modelo final en cortes reservados
python pipeline/pronosticar_m5.py      # 28 días por serie
python pipeline/agregar_m5.py          # agregados para la interfaz
```

`python -m pip install -e lib` instala el paquete de dominio (`lib/pyproject.toml`)
en el entorno activo, de modo que las etapas de `pipeline/` importan
`app.comercial`, `app.config` y `app.db.mongo` sin depender del directorio de
trabajo ni de `PYTHONPATH`. El `pyproject.toml` de la raíz añade `lib` a
`pythonpath` para que `python -m pytest` funcione aunque no se haya instalado.
Solo se declaran `pydantic-settings` y `pymongo`: el resto del pipeline
(`numpy`, `pandas`, `lightgbm`) se instala con `requirements.txt`.

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
lib/pyproject.toml        Paquete instalable del dominio (`pip install -e lib`)
lib/app/comercial/        Paquete de modelado (mismo espacio de nombres del backend)
lib/app/config.py         Configuración con rutas al clon y datos bajo `data/`
lib/app/db/mongo.py       Conexión, colecciones M5 y reintentos de lectura
app/index.html            Host de desarrollo (`npm run dev`)
app/src/main.tsx          Monta la aplicación completa en el navegador
app/src/mount.tsx         Entrada de la librería `mount`/`unmount` del build
app/dist/                 Artefacto del build (`app.js` + `app.css`), ignorado por Git
tests/test_pipeline.py    Contratos estáticos del método
tests/test_comercial.py   Prueba real de `app.comercial.fuentes` (sin entrenar)
docs/                     Metodología, datos y arquitectura
```

La interfaz **no** calcula el modelo: consume la API del portafolio
(`portfolio-api`). El corazón de este repositorio es el pipeline.

```bash
cd app
npm ci
npm run dev      # host de desarrollo: index.html + src/main.tsx
npm run build    # librería ESM en app/dist (app.js + app.css), dentro del repo
```

`app/src/ui/Segmentado.tsx` es el selector segmentado vendorizado: ya no se
importa desde el Atlas vial ni se escribe en `../../dist`. El build de librería
(`src/mount.tsx`) sigue produciendo `mount`/`unmount` para el portafolio, y el
host de desarrollo (`src/main.tsx`) monta la misma aplicación para revisarla en el
navegador contra la API.

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -e lib
python -m pytest
```

Ocho pruebas de contrato estático, sin importar el paquete `comercial` (analizan
el código con `ast`): horizonte de 28 días, herencia del horizonte en el modelo,
existencia y compilación de las cuatro etapas, declaración del protocolo de
variantes y ausencia de rutas absolutas.

`tests/test_comercial.py` añade **ocho pruebas reales** sobre `app.comercial.fuentes`,
el módulo puro que declara archivos, columnas y aritmética de días: cobertura leída
de la cabecera `d_N`, rechazo de cabeceras inválidas, idempotencia de la versión,
semanas de lunes a domingo, conversión `d_N` ↔ fecha real, SHA-256 del manifiesto y
archivos esperados. **No es un entrenamiento ni una ejecución del pipeline**: no
lee los CSV de M5, no usa MongoDB y no importa LightGBM.

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
