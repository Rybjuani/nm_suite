"""Entrega de callbacks desde hilos worker al hilo GUI de Qt.

Reemplaza el antipatrón `QTimer.singleShot(0, fn)` invocado **desde un hilo
worker** (sin event loop propio): ese timer vive en el hilo que lo crea, por lo
que nunca dispara y el callback jamás llega a la UI. Acá un ``QObject`` con
afinidad al hilo GUI recibe la llamada vía señal; emitir esa señal desde
cualquier hilo encola la ejecución de ``fn`` en el hilo GUI (conexión queued).
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class _GuiInvoker(QObject):
    _invoke = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        # Conexión por defecto (AutoConnection): si se emite desde otro hilo que
        # el de afinidad del objeto, Qt la resuelve como Queued y ejecuta el slot
        # en el hilo GUI.
        self._invoke.connect(self._call)

    def _call(self, fn) -> None:
        try:
            fn()
        except Exception:  # defensivo: un callback no debe tumbar el hilo GUI
            logger.exception("run_on_gui: el callback en el hilo GUI falló")


_invoker: _GuiInvoker | None = None


def init_gui_invoker() -> None:
    """Crea el invoker en el hilo GUI. Llamar desde ``main()`` tras crear el
    ``QApplication`` para fijar la afinidad correcta de forma determinista."""
    global _invoker
    if _invoker is None:
        _invoker = _GuiInvoker()


def run_on_gui(fn) -> None:
    """Ejecuta ``fn`` en el hilo GUI de Qt. Seguro de llamar desde cualquier hilo.

    Si no hay ``QApplication`` (entornos headless/tests) ejecuta ``fn`` inline.
    """
    global _invoker
    app = QApplication.instance()
    if app is None:
        fn()
        return
    if _invoker is None:
        _invoker = _GuiInvoker()
    # Garantizar afinidad al hilo GUI aunque el invoker se haya creado en otro hilo.
    if _invoker.thread() is not app.thread():
        _invoker.moveToThread(app.thread())
    _invoker._invoke.emit(fn)
