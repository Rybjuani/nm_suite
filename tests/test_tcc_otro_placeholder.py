"""Test permanente: el input "Otro" del Registro TCC usa setPlaceholderText
(campo realmente vacio, text()=="") y la emocion se mantiene en "Otro" hasta
que el usuario escribe algo distinto.

2026-06 round 4: este test blinda la correccion que reemplazo setText("¿Cual?")
por setPlaceholderText("¿Cual?") + palette PlaceholderText role.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

# Forzar plataforma offscreen antes de importar PyQt6.
# Movido a tests/conftest.py (se aplica a todos los tests).


def _get_qapp():
    """Retorna la QApplication activa creada por el fixture `qapp` de pytest-qt.

    Mantenida como helper para los calls `_get_qapp().processEvents()` dispersos
    en este test. No crea una QApplication propia: si no hay instancia activa,
    retorna None (el fixture `qapp` debe haberse inicializado antes via el
    fixture `tcc_modulo` o similar).
    """
    from PyQt6.QtWidgets import QApplication

    return QApplication.instance()


@pytest.fixture
def tcc_modulo(qapp):
    """Construye un ModuloRegistroTCC aislado, ya en el step de emocion
    con un texto de situacion valido (asi _next_step avanza al step 1).
    """
    from PyQt6.QtCore import QSize

    from shared.fonts import load_fonts
    from shared.theme_qt import stylesheet_base
    from app.modules.registro_tcc_qt import ModuloRegistroTCC

    load_fonts()
    qapp.setStyleSheet(stylesheet_base("dark_hybrid"))

    mod = ModuloRegistroTCC(modo="dark_hybrid", show_header=False)
    mod.resize(QSize(960, 600))
    mod.show()
    for _ in range(20):
        qapp.processEvents()

    mod._txt_situacion.setPlainText("Estaba en una reunion y me senti incomodo")
    mod._next_step()
    for _ in range(20):
        qapp.processEvents()
        time.sleep(0.01)

    yield mod

    mod.close()
    mod.deleteLater()
    qapp.processEvents()


def _click_tile_otro(mod) -> None:
    for tile in mod._emotion_tiles:
        if getattr(tile, "_label_text", None) == "Otro":
            tile.clicked.emit()
            return
    raise AssertionError("No se encontro el tile 'Otro' en _emotion_tiles")


def test_input_otro_placeholder_vacio_al_seleccionar(tcc_modulo):
    """Al seleccionar 'Otro': text()=='', placeholderText()=='¿Cual?',
    _data['emocion']=='Otro'. El placeholder NO es contenido."""
    mod = tcc_modulo
    inp = mod._custom_emotion_input

    _click_tile_otro(mod)
    for _ in range(10):
        _get_qapp().processEvents()

    assert inp.text() == "", (
        f"El input Otro debe estar vacio, pero text()={inp.text()!r}. "
        "El placeholder NO debe ser contenido."
    )
    assert inp.placeholderText() == "¿Cuál?", (
        f"placeholderText debe ser '¿Cual?', got {inp.placeholderText()!r}"
    )
    assert mod._data["emocion"] == "Otro", (
        f"_data['emocion'] debe ser 'Otro' cuando el campo esta vacio, "
        f"got {mod._data['emocion']!r}"
    )


def test_input_otro_emocion_se_actualiza_al_tipear(tcc_modulo):
    """Hasta que el usuario escribe, la emocion permanece en 'Otro'. Cuando
    escribe, _data['emocion'] refleja el texto tipeado."""
    mod = tcc_modulo
    inp = mod._custom_emotion_input

    _click_tile_otro(mod)
    for _ in range(10):
        _get_qapp().processEvents()

    # Pre-tipeo: emocion = "Otro"
    assert mod._data["emocion"] == "Otro"

    # El usuario escribe "Frustracion" (sin acento para evitar encoding issues)
    inp.setText("Frustracion")
    for _ in range(10):
        _get_qapp().processEvents()

    assert inp.text() == "Frustracion"
    assert mod._data["emocion"] == "Frustracion", (
        f"Tras tipear, emocion debe ser 'Frustracion', got {mod._data['emocion']!r}"
    )

    # Si borra el texto, vuelve a "Otro"
    inp.clear()
    for _ in range(10):
        _get_qapp().processEvents()

    assert inp.text() == ""
    assert mod._data["emocion"] == "Otro", (
        f"Tras clear(), emocion debe volver a 'Otro', got {mod._data['emocion']!r}"
    )


def test_input_otro_no_settext_como_contenido(tcc_modulo):
    """Estructural: el modulo NO debe llamar setText('¿Cual?') en ningun
    punto — solo setPlaceholderText. Esto blinda contra regresiones que
    conviertan el placeholder en contenido (rompiendo text()=='')."""
    import inspect
    from app.modules import registro_tcc_qt as tcc_mod

    src = inspect.getsource(tcc_mod)
    forbidden = 'setText("¿Cuál?")'
    assert forbidden not in src, (
        f"Encontrado {forbidden!r} en registro_tcc_qt — el placeholder debe "
        "usarse via setPlaceholderText, nunca como contenido."
    )
    # Y debe estar el setPlaceholderText
    assert 'setPlaceholderText("¿Cuál?")' in src, (
        "Falta setPlaceholderText('¿Cual?') en registro_tcc_qt"
    )
