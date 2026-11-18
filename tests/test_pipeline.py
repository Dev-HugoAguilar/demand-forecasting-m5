"""Contratos estáticos del pipeline M5.

Estas pruebas no importan ``app.comercial``: ese paquete depende de MongoDB y de
``resource`` (solo Unix) y no se puede ejecutar sin datos ni infraestructura. En
su lugar se analiza el código con ``ast`` para fijar los invariantes que la
metodología documenta y que un cambio descuidado podría romper en silencio.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
COMERCIAL = RAIZ / "lib" / "app" / "comercial"
PIPELINE = RAIZ / "pipeline"


def valor_asignado(archivo: Path, nombre: str):
    """Devuelve el literal asignado a ``nombre`` en el módulo."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign):
            for objetivo in nodo.targets:
                if isinstance(objetivo, ast.Name) and objetivo.id == nombre:
                    return ast.literal_eval(nodo.value)
    raise AssertionError(f"no se encontró la asignación de {nombre} en {archivo.name}")


def test_horizonte_del_desafio_es_28_dias() -> None:
    fuentes = COMERCIAL / "fuentes.py"
    assert fuentes.exists(), "falta el módulo de fuentes"
    assert valor_asignado(fuentes, "DIAS_HORIZONTE") == 28


def test_modelo_deriva_su_horizonte_de_fuentes() -> None:
    """El modelo no debe redefinir el horizonte: lo hereda de ``fuentes``."""
    texto = (COMERCIAL / "modelo.py").read_text(encoding="utf-8")
    assert "DIAS_HORIZONTE" in texto
    assert "HORIZONTE = fuentes.DIAS_HORIZONTE" in texto


@pytest.mark.parametrize(
    "etapa",
    ["importar_m5.py", "entrenar_m5.py", "pronosticar_m5.py", "agregar_m5.py"],
)
def test_etapas_del_pipeline_existen_y_compilan(etapa: str) -> None:
    archivo = PIPELINE / etapa
    assert archivo.exists(), f"falta la etapa {etapa}"
    codigo = archivo.read_text(encoding="utf-8")
    compile(codigo, str(archivo), "exec")
    assert "argparse" in codigo, "cada etapa se ejecuta desde la línea de comandos"


def test_el_entrenamiento_documenta_su_protocolo() -> None:
    texto = (PIPELINE / "entrenar_m5.py").read_text(encoding="utf-8")
    # El protocolo se declara en el propio script: cortes de desarrollo y
    # evaluación final separados, y selección por WAPE.
    assert "--variantes" in texto
    assert "wape" in texto.lower()


def test_los_fuentes_no_contienen_rutas_absolutas() -> None:
    for archivo in list(COMERCIAL.glob("*.py")) + list(PIPELINE.glob("*.py")):
        codigo = archivo.read_text(encoding="utf-8")
        assert "D:\\" not in codigo and "C:\\Users" not in codigo, archivo.name
