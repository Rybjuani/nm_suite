"""Core component primitives shared by Suite and Hub."""

from __future__ import annotations

from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget

from shared.theme_manager import ThemeManager
from shared.theme_qt import norm_modo, v3c


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


class NMFadeWidget(QStackedWidget):
    """
    QStackedWidget con transición "fade-through-background" entre páginas.

    setCurrentWidget() override: switch instantáneo + velo del color de fondo
    del tema que se desvanece en ~160ms. El cross-blend anterior (snapshot de
    la vista vieja desvaneciéndose SOBRE la nueva) mostraba AMBAS vistas
    superpuestas durante toda la animación — el "titileo fantasma" que el
    user feedback grabó en video (informe v1.0 final). Con el velo nunca conviven dos
    contenidos: la vista nueva emerge del fondo, calma y sin doble exposición.
    """

    def __init__(self, parent=None, duration: int = 160):
        super().__init__(parent)
        self._duration = duration
        self._animating = False
        self._snapshot: QWidget | None = None
        self._fade_anim: QPropertyAnimation | None = None

    def setCurrentWidget(self, widget: QWidget):
        if widget is self.currentWidget():
            return
        if self._animating and self._fade_anim is not None:
            # Navegación rápida durante el velo: cortar la animación en curso
            # (stop() emite finished → limpieza única) y conmutar igual;
            # descartar el click dejaba la nav "muerta" durante 160ms.
            self._fade_anim.stop()
        self._fade_to(widget)

    def _fade_to(self, target: QWidget):
        current = self.currentWidget()
        super().setCurrentWidget(target)
        if current is None:
            self._animating = False
            return

        self._animating = True
        modo = norm_modo(_tm().modo)
        scrim = QWidget(self)
        scrim.setStyleSheet(f"background: {v3c('bg', modo).name()};")
        scrim.setGeometry(0, 0, self.width(), self.height())
        scrim.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        scrim.show()
        scrim.raise_()
        self._snapshot = scrim

        eff = QGraphicsOpacityEffect(scrim)
        scrim.setGraphicsEffect(eff)

        fade_out = QPropertyAnimation(eff, b"opacity", self)
        fade_out.setDuration(self._duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_out_done():
            scrim.deleteLater()
            self._snapshot = None
            self._animating = False
            self._fade_anim = None

        fade_out.finished.connect(_on_out_done)
        self._fade_anim = fade_out
        fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._snapshot:
            self._snapshot.setGeometry(0, 0, self.width(), self.height())
