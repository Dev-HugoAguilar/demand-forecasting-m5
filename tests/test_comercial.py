"""Prueba real de la lógica del paquete ``comercial``.

A diferencia de ``tests/test_pipeline.py`` —contratos **estáticos** que analizan
el código con ``ast``— esta prueba **importa** ``app.comercial.fuentes`` y
comprueba cálculos concretos: la aritmética de días 1-based de M5, las ventanas
de lunes a domingo del tablero, la regla de idempotencia de la versión y el
SHA-256 del manifiesto.

No es un entrenamiento ni una ejecución del pipeline: no se leen los CSV del
concurso (M5 no se redistribuye), no se usa MongoDB y no se toca LightGBM. Solo
se ejercita el módulo puro que declara archivos, columnas y aritmética de días.

Requiere el paquete instalado: ``python -m pip install -e lib``.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.comercial import fuentes


def test_horizonte_y_constantes_del_desafio() -> None:
    """El horizonte de 28 días y el patrón de 7 días son la base del baseline."""
    assert fuentes.DIAS_HORIZONTE == 28
    assert fuentes.DIAS_SEMANA_PATRON == 7
    assert fuentes.TAMANO_BLOQUE == 196


def test_cuenta_dias_ventas_desde_la_cabecera() -> None:
    """Las columnas ``d_N`` de la cabecera definen la cobertura observada."""
    cabecera = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id", "d_1", "d_2", "d_3"]
    assert fuentes.cuenta_dias_ventas(cabecera) == 3


def test_cuenta_dias_ventas_rechaza_cabeceras_invalidas() -> None:
    with pytest.raises(ValueError, match="no tiene columnas d_N"):
        fuentes.cuenta_dias_ventas(["id", "item_id"])
    with pytest.raises(ValueError, match="no son consecutivas"):
        fuentes.cuenta_dias_ventas(["id", "d_1", "d_3"])


def test_crear_version_es_estable_y_sensible_a_los_hashes() -> None:
    """Mismo contenido ⇒ misma versión; cambiar un hash ⇒ otra versión."""
    hash_ventas = "a" * 64
    hash_calendario = "b" * 64
    esperada = "m5-0a8ba7b434ba"
    assert fuentes.crear_version("sales_train_evaluation.csv", 1941, hash_ventas, hash_calendario) == esperada
    # Idempotente: repetir la importación no crea una versión nueva.
    assert fuentes.crear_version(
        "sales_train_evaluation.csv", 1941, hash_ventas, hash_calendario
    ) == esperada
    # Un archivo distinto produce una versión distinta.
    assert fuentes.crear_version(
        "sales_train_validation.csv", 1941, hash_ventas, hash_calendario
    ) != esperada
    # Un calendario distinto también.
    assert fuentes.crear_version(
        "sales_train_evaluation.csv", 1941, hash_ventas, "c" * 64
    ) != esperada
    assert esperada.startswith("m5-") and len(esperada) == len("m5-") + 12


def test_semana_comercial_va_de_lunes_a_domingo() -> None:
    """Las semanas del tablero no usan la semana de competición (sábado)."""
    miercoles = date(2026, 1, 7)
    assert fuentes.inicio_semana(miercoles) == date(2026, 1, 5)
    assert fuentes.fin_semana(miercoles) == date(2026, 1, 11)
    # Un lunes es su propio inicio y el domingo cierra la misma semana.
    assert fuentes.inicio_semana(date(2026, 1, 5)) == date(2026, 1, 5)
    assert fuentes.fin_semana(date(2026, 1, 11)) == date(2026, 1, 11)


def test_conversion_entre_dia_y_fecha_real() -> None:
    """``d_1`` es 1-based y se traduce con el calendario importado."""
    fechas = {1: date(2011, 1, 29), 2: date(2011, 1, 30)}
    assert fuentes.dia_a_fecha(fechas, 2) == date(2011, 1, 30)
    assert fuentes.fecha_a_dia(fechas, date(2011, 1, 29)) == 1
    # Fuera de la cobertura: error explícito al mapear y ``None`` al buscar.
    assert fuentes.fecha_a_dia(fechas, date(2011, 2, 1)) is None
    with pytest.raises(ValueError, match="no cubre d_5"):
        fuentes.dia_a_fecha(fechas, 5)


def test_hash_archivo_vectores_conocidos(tmp_path) -> None:
    vacio = tmp_path / "vacio.csv"
    vacio.write_bytes(b"")
    assert fuentes.hash_archivo(vacio) == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

    contenido = tmp_path / "muestra.csv"
    contenido.write_bytes(b"abc")
    assert fuentes.hash_archivo(contenido) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_archivos_esperados_y_su_obligatoriedad() -> None:
    """El importador acepta evaluación o validación, nunca las dos mezcladas."""
    esperados = fuentes.archivos_esperados()
    assert [archivo.nombre for archivo in esperados] == [
        "sales_train_evaluation.csv",
        "calendar.csv",
        "sell_prices.csv",
    ]
    assert [archivo.obligatorio for archivo in esperados] == [True, True, False]

    solo_validacion = fuentes.archivos_esperados(solo_validacion=True)
    assert solo_validacion[0].nombre == "sales_train_validation.csv"
    assert solo_validacion[0].obligatorio is True
