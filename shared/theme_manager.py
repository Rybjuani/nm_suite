"""Theme change singleton shared by the Qt visual layer."""

from __future__ import annotations

from PyQt6 import sip
from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QObject, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QGraphicsOpacityEffect, QLabel, QWidget

from shared.theme import norm_modo


class ThemeManager(QObject):
    """Singleton that propagates theme changes to registered widgets."""

    theme_changed = pyqtSignal(str)
    TRANSITION_MS = 350
    _inst = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._inst is None or sip.isdeleted(cls._inst):
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self._transitioning = False

    @property
    def modo(self) -> str:
        return self._modo

    def switch_mode(self, new_modo: str, animate: bool = True):
        new_modo = norm_modo(new_modo)
        if new_modo == self._modo or self._transitioning:
            return

        from shared.visual_qa import visual_qa_enabled

        if not animate or visual_qa_enabled() or QApplication.instance() is None:
            self._modo = new_modo
            for widget in QApplication.topLevelWidgets() if QApplication.instance() else []:
                widget.update()
            self.theme_changed.emit(new_modo)
            return

        snapshots: list[tuple[QWidget, QPixmap]] = []
        for win in QApplication.topLevelWidgets():
            if not win.isVisible():
                continue
            if win.isMinimized():
                continue
            if win.size().width() <= 0 or win.size().height() <= 0:
                continue
            try:
                snap = win.grab()
                if not snap.isNull():
                    snapshots.append((win, snap))
            except Exception:
                pass

        overlays: list[QLabel] = []
        for win, snap in snapshots:
            try:
                overlay = QLabel(win)
                overlay.setPixmap(snap)
                overlay.setGeometry(0, 0, win.width(), win.height())
                overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                overlay.setScaledContents(False)
                overlay.show()
                overlay.raise_()
                overlays.append(overlay)
            except Exception:
                pass

        try:
            QApplication.processEvents()
        except Exception:
            pass

        self._modo = new_modo
        self._transitioning = True
        try:
            self.theme_changed.emit(new_modo)
            for widget in QApplication.topLevelWidgets():
                widget.update()
        except Exception:
            pass

        for overlay in overlays:
            self._fade_out_overlay(overlay)

        if not overlays:
            self._transitioning = False
        else:
            QTimer.singleShot(
                self.TRANSITION_MS + 20, lambda: setattr(self, "_transitioning", False)
            )

    def _fade_out_overlay(self, overlay: QLabel):
        try:
            effect = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(effect)
            effect.setOpacity(1.0)
            animation = QPropertyAnimation(effect, b"opacity", overlay)
            animation.setDuration(self.TRANSITION_MS)
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.finished.connect(overlay.deleteLater)
            animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        except Exception:
            overlay.deleteLater()
