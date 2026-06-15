"""Fase 11 — guards de regresión para los cambios visuales de F9/F10.

Estos cambios son de comportamiento de la UI (variantes de botón, métrica
mostrada, visibilidad condicional) cuya evidencia primaria son las capturas
inspeccionadas. Estos tests bloquean la INTENCIÓN sobre el código fuente:
son estables y atrapan una reversión accidental sin instanciar toda la UI.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_respiracion_sin_bpm_biometrico_simulado():
    """F9: la métrica falsa de pulso (BPM simulado RSA) fue reemplazada por
    Ciclos (conteo real)."""
    src = _src("app/modules/respiracion_qt.py")
    assert "Simular arritmia" not in src, "quedó el comentario de la simulación de pulso"
    assert 'QLabel("BPM")' not in src, "la card sigue rotulando BPM"
    assert 'QLabel("Ciclos")' in src
    assert "_ciclos_value_lbl" in src
    # el valor mostrado es el conteo real de ciclos, no un número simulado
    assert "self._ciclos_value_lbl.setText(str(self._ciclos))" in src


def test_actividades_hice_jerarquia_equivalente():
    """F10: 'Hice' dejó de ser variant=primary; mismo peso que 'No pude'."""
    src = _src("app/modules/actividades_qt.py")
    assert 'NMButton("Hice", variant="secondary"' in src
    assert 'NMButton("No pude", variant="secondary"' in src
    assert 'NMButton("Hice", variant="primary"' not in src


def test_avisos_sin_duplicacion_completado_hecho():
    """F10: las filas completadas ocultan el botón 'Hecho' (sólo queda el badge
    'Completado'); el ancho se conserva para no desalinear la columna."""
    src = _src("app/modules/avisos_qt.py")
    assert "setRetainSizeWhenHidden(True)" in src
    assert "self._btn_done.setVisible(False)" in src
    # ya no se re-rotula el botón a "Hecho" en la rama completada
    assert not re.search(r'self\._btn_done\.setText\("Hecho"\)', src)


def test_tcc_anterior_secondary_y_guardado_real_seam():
    """F8/F11: 'Anterior' es un botón secondary real y el guardado real vive en
    un seam (`_persistir_pensamiento`) que `_guardar` invoca."""
    src = _src("app/modules/registro_tcc_qt.py")
    assert '"Anterior", parent=self._content, modo=self._modo, variant="secondary"' in src
    assert 'variant="ghost"' not in src.split('"Anterior"')[1][:120]
    assert "def _persistir_pensamiento(" in src
    assert "_persistir_pensamiento(d, intensidad)" in src
