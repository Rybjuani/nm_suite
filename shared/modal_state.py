"""Registro global de modales activos sobre una ventana.

Permite que un overlay de ventana (p.ej. el corner-shadow de `app/main_qt.py`)
se desactive mientras haya un modal visible: un modal se captura recortado a
SU PROPIO content bbox, mucho más chico que el de la ventana completa —
pintar la esquina de la VENTANA durante esa captura infla el bbox detectado
del modal y rompe su contrato (ver VISUAL_REPAIR_HANDOFF, regresión
dbt-practice-* de 2026-07-06).

Los widgets modales (``NMDialog``, ``NMDialogScaffold``,
``_PracticeModalScrim``) reportan su visibilidad vía ``modal_shown``/
``modal_hidden`` desde sus propios ``showEvent``/``hideEvent`` — no hace
falta que cada call-site individual lo invoque.
"""

from __future__ import annotations

_active_modal_count = 0


def modal_shown(widget=None) -> None:
    global _active_modal_count
    _active_modal_count += 1
    _refresh_overlay(widget)


def modal_hidden(widget=None) -> None:
    global _active_modal_count
    _active_modal_count = max(0, _active_modal_count - 1)
    _refresh_overlay(widget)


def any_modal_active() -> bool:
    return _active_modal_count > 0


def _refresh_overlay(widget) -> None:
    """Fuerza el repaint del corner-overlay de la ventana de ``widget``.

    El overlay solo evalúa ``any_modal_active()`` dentro de su propio
    ``paintEvent`` — sin este empujón, mostrar/ocultar un modal no dispara
    por sí solo un repaint de un sibling ya pintado que no cambió de
    geometría.
    """
    if widget is None:
        return
    try:
        win = widget.window()
        overlay = getattr(win, "_corner_overlay", None)
        if overlay is not None:
            overlay.update()
    except RuntimeError:
        pass  # widget o ventana ya destruidos (C++ object deleted)
