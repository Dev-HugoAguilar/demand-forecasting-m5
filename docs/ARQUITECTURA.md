# Arquitectura del repositorio

## Capas

```text
pipeline/                  Etapas ejecutables (CLI con argparse)
  importar_m5.py           CSV de M5 → MongoDB (crudo y compacto)
  entrenar_m5.py           Entrenamiento por cortes, variantes y modelo final
  pronosticar_m5.py        Pronóstico a 28 días sobre el último origen
  agregar_m5.py            Agregados que consume la interfaz
  inventario_m5.py         Inventario de series y cobertura
  derivar_planificacion.py Planificación a partir de los agregados
  demo_sintetica_m5.py     Demostración sin datos del concurso

lib/app/comercial/         Paquete de modelado (espacio de nombres del backend)
  fuentes.py               Rutas, cortes y DIAS_HORIZONTE
  ingesta.py               Lectura y normalización de las fuentes
  modelo.py                Features, LightGBM por horizonte, evaluación
  forecast.py              Pronóstico y armado de la salida
  derivados.py             Derivaciones para la interfaz
  inventario.py            Inventario de series
  precios.py               Precios y manifiesto vigente
  esquema.py               Contratos de documentos
  conexion.py              Acceso a MongoDB

app/                       Interfaz React + TypeScript (capa de visualización)
docs/                      Metodología, datos y esta arquitectura
```

## Por qué el paquete replica `app.comercial`

`lib/app/comercial` conserva el mismo espacio de nombres que el backend del
portafolio. Sincronizar un cambio entre ambos es una copia directa de archivo,
revisable en un `diff`. Las etapas de `pipeline/` se copian igual desde
`backend/scripts/`. No renombres el paquete sin actualizar los dos lados.

## Flujo de datos

```text
CSV de M5 ──importar_m5.py──▶ MongoDB (crudo + compacto)
                                  │
                    entrenar_m5.py│  cortes de desarrollo ──▶ variantes ──▶ WAPE
                                  │  cortes reservados   ──▶ modelo final
                                  ▼
                    MongoDB M5_EVALUACION / M5_PRONOSTICOS
                                  │
                   pronosticar_m5.py ──▶ 28 días por serie
                                  │
                     agregar_m5.py ──▶ M5_AGREGADOS
                                  │
                            API HTTP (portfolio-api) ──▶ app/ (React)
```

La interfaz consume la API; no calcula el modelo ni lee MongoDB directamente.

## Interfaz (`app/`)

Aplicación React + TypeScript construida con Vite. Sus pantallas cubren modelado,
pronóstico, planificación, precios, estacionalidad, evaluación, comparación,
detalle de artículo y auditoría temporal.

```bash
cd app
npm ci
npm run dev     # requiere la API en ejecución
```

No se incluye `node_modules` ni artefactos de compilación. La aplicación no forma
parte de la verificación automática del repositorio: su dependencia es la API, que
vive en `portfolio-api`.

## Contrato con la API

| Recurso | Uso en la interfaz |
|---|---|
| Salud y metadatos | Estado del servicio y versión del esquema |
| Agregados por ventana | Series y matrices de las pantallas |
| Pronóstico | Banda, horizonte y métricas por corte |
| Evaluación | Comparación de variantes y ventanas |
| Exportación | Descargas CSV de las tablas visibles |

## No objetivos

- No reentrena en el navegador ni sirve el modelo desde el cliente.
- No publica los datos del concurso ni agregados derivados.
- No sustituye un sistema de planificación: es un prototipo de método.
