"""Adaptive desktop layout helpers for NeuroMood Qt windows and panels."""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import (
    Qt,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    pyqtSignal,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shared.theme_qt import C, V3_SP, eyebrow_font, nm_icon, qfont, v3c


DEFAULT_WINDOW_SIZE = QSize(960, 600)
WINDOW_SAFE_MARGIN = 24
_TRANSIENT_QT_GHOST_TITLES: set[str] = {"Suite", "NeuroMood Hub"}
_TRANSIENT_QT_GHOST_MAX_WIDTH = 260
_TRANSIENT_QT_GHOST_MAX_HEIGHT = 180
_TRANSIENT_QT_WINDOW_GUARD_HOOK = None
_TRANSIENT_QT_WINDOW_GUARD_CALLBACK = None

# ── Breakpoints por SUPERFICIE (ancho del contenedor, no de la pantalla) ──────
# Contrato 960×600: ninguna vista interna puede mantener 2/3 columnas fijas a
# anchos chicos. Estas constantes definen cuándo una superficie debe pasar de
# columnas a apilado/colapso. Las consume `NMResponsiveColumns` y las vistas que
# deciden mostrar/ocultar paneles auxiliares (preview, filtros) por ancho real.
BP_STACK = 720      # < BP_STACK  → apilar columnas verticalmente
BP_AUX_PANEL = 1040  # < BP_AUX_PANEL → ocultar panel auxiliar (preview) o mandarlo a tab/colapso


def surface_width_class(width: int) -> str:
    """Clasifica el ancho de una superficie en 'stack' | 'compact' | 'wide'.

    'stack'   = una sola columna (apilar todo).
    'compact' = columnas principales, sin paneles auxiliares (preview/filtros).
    'wide'    = layout completo (columnas + auxiliares).
    """
    if width < BP_STACK:
        return "stack"
    if width < BP_AUX_PANEL:
        return "compact"
    return "wide"


def configure_adaptive_window(
    window: QWidget,
    *,
    default_size: QSize = DEFAULT_WINDOW_SIZE,
    min_size: QSize = DEFAULT_WINDOW_SIZE,
    margin: int = WINDOW_SAFE_MARGIN,
) -> bool:
    """Apply NeuroMood's 960x600 desktop contract and center the window.

    Returns True when the screen is smaller than the standard contract and the
    caller should prefer compact layout density.
    """
    screen = QApplication.primaryScreen()
    available = screen.availableGeometry() if screen else None
    target = QSize(default_size)
    compact = False

    if available is not None:
        target_w = min(default_size.width(), max(320, available.width() - margin * 2))
        target_h = min(default_size.height(), max(360, available.height() - margin * 2))
        target = QSize(target_w, target_h)
        compact = target_w < default_size.width() or target_h < default_size.height()

    effective_min = QSize(
        min(min_size.width(), target.width()),
        min(min_size.height(), target.height()),
    )
    window.setMinimumSize(effective_min)
    window.setProperty("nm_compact", compact)
    window.resize(target)

    if available is not None:
        x = available.x() + max(0, (available.width() - window.width()) // 2)
        y = available.y() + max(0, (available.height() - window.height()) // 2)
        window.move(x, y)
    return compact


def _is_transient_qt_ghost_window(
    title: str,
    class_name: str,
    width: int,
    height: int,
) -> bool:
    """Detect the known black Qt helper flash without touching real app windows."""
    if width <= 0 or height <= 0:
        return False
    if width > _TRANSIENT_QT_GHOST_MAX_WIDTH or height > _TRANSIENT_QT_GHOST_MAX_HEIGHT:
        return False

    normalized_title = (title or "").strip()
    if normalized_title not in _TRANSIENT_QT_GHOST_TITLES:
        return False

    normalized_class = class_name or ""
    return normalized_class.startswith("Qt") and "QWindow" in normalized_class


def install_transient_qt_window_guard(app_name: str | None = None) -> bool:
    """Hide the tiny transient Qt top-level windows seen as black flashes on Windows.

    Win32 evidence for the Suite/Hub bug is a same-process ``Qt*QWindow*`` window
    with title ``Suite`` or ``NeuroMood Hub`` and a tiny visible rect (~136x54).
    The hook is process-local, best-effort, and leaves normal main windows and
    dialogs alone by requiring that exact small-window signature.
    """
    global _TRANSIENT_QT_WINDOW_GUARD_CALLBACK
    global _TRANSIENT_QT_WINDOW_GUARD_HOOK

    if app_name:
        _TRANSIENT_QT_GHOST_TITLES.add(app_name.strip())
    if _TRANSIENT_QT_WINDOW_GUARD_HOOK is not None:
        return True
    if sys.platform != "win32" or os.environ.get("NM_DISABLE_TRANSIENT_WINDOW_GUARD") == "1":
        return False

    try:
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        EVENT_OBJECT_SHOW = 0x8002
        OBJID_WINDOW = 0
        SW_HIDE = 0
        WINEVENT_OUTOFCONTEXT = 0x0000
        WinEventProc = ctypes.WINFUNCTYPE(
            None,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
        )

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        def _text(hwnd) -> str:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, len(buf))
            return buf.value

        def _class_name(hwnd) -> str:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buf, len(buf))
            return buf.value

        def _rect(hwnd) -> tuple[int, int]:
            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return 0, 0
            return rect.right - rect.left, rect.bottom - rect.top

        def _on_window_event(
            _hook,
            _event,
            hwnd,
            id_object,
            id_child,
            _event_thread,
            _event_time,
        ):
            if not hwnd or id_object != OBJID_WINDOW or id_child != 0:
                return
            try:
                width, height = _rect(hwnd)
                if _is_transient_qt_ghost_window(_text(hwnd), _class_name(hwnd), width, height):
                    user32.ShowWindow(hwnd, SW_HIDE)
            except Exception:
                return

        callback = WinEventProc(_on_window_event)
        hook = user32.SetWinEventHook(
            EVENT_OBJECT_SHOW,
            EVENT_OBJECT_SHOW,
            0,
            callback,
            os.getpid(),
            0,
            WINEVENT_OUTOFCONTEXT,
        )
        if not hook:
            return False
        _TRANSIENT_QT_WINDOW_GUARD_CALLBACK = callback
        _TRANSIENT_QT_WINDOW_GUARD_HOOK = hook
        return True
    except Exception:
        return False


def apply_child_window_chrome(
    window: QWidget,
    title: str,
    modo: str = "dark_hybrid",
    *,
    show_theme_toggle: bool = False,
    show_maximize: bool = True,
):
    """Aplica el chrome NeuroMood a una ventana hija top-level (editores/diálogos).

    Espejo del patrón de las ventanas main de Suite/Hub (`hub/main_qt.py`): pone la
    ventana en modo frameless (`FramelessWindowHint | Window`) y reemplaza la
    titlebar nativa del SO por una `NMWindowChrome` (cerebro + título + min/max/close),
    insertada como primer widget del layout de la ventana. Devuelve la barra.

    El import de `NMWindowChrome` es local para evitar un ciclo de import entre
    `shared.components_qt` y este módulo. No se hardcodean colores: el chrome usa tokens.
    """
    from shared.components import NMWindowChrome  # import local: evita ciclo

    window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
    chrome = NMWindowChrome(
        title=title,
        modo=modo,
        show_theme_toggle=show_theme_toggle,
        show_maximize=show_maximize,
        parent=window,
    )
    layout = window.layout()
    if layout is not None:
        layout.insertWidget(0, chrome)
    # Flags ya definitivos: pedir esquinas redondeadas nativas (Win11; no-op Win10).
    apply_native_rounded_corners(window)
    return chrome


def apply_native_rounded_corners(window) -> None:
    """Esquinas redondeadas NATIVAS de la ventana vía DWM (Windows 11+).

    En Windows 11 (build >= 22000) el compositor redondea la ventana top-level
    (incluidas las frameless nuestras) con su sombra nativa — look premium sin
    costo de render. En Windows 10 no existe API soportada (SetWindowRgn
    serrucha sin antialiasing y la ventana translúcida pierde la sombra y
    sufre esquinas negras — ya descartado en los modales): no-op silencioso.

    Llamar DESPUÉS de que los window flags estén definitivos (cambiar flags
    recrea la ventana nativa y descarta el atributo).
    """
    try:
        import ctypes
        import ctypes.wintypes
        import sys as _sys

        if _sys.platform != "win32" or _sys.getwindowsversion().build < 22000:
            return
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        pref = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.wintypes.HWND(int(window.winId())),
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(pref),
            ctypes.sizeof(pref),
        )
    except Exception:
        pass


def window_edge_radius(win11: int = 22) -> int:
    """Radio de borde para un frame que ES el borde de una ventana frameless.

    En Windows 11 el compositor redondea la ventana top-level (DWM, ver
    apply_native_rounded_corners) → el frame acompaña con `win11`. En Windows 10
    no hay API soportada y la ventana frameless queda cuadrada; si el frame de
    raíz pintara un border-radius, se vería una card redondeada flotando dentro
    de una ventana de puntas rectas (feedback owner: "en Win10 no se ven bien").
    Por eso en Win10 devuelve 0. Aplica solo a frames de BORDE de ventana, no a
    las cards internas (que por ADN siempre van redondeadas).
    """
    try:
        import sys as _sys

        if _sys.platform == "win32" and _sys.getwindowsversion().build >= 22000:
            return win11
    except Exception:
        pass
    return 0


class NMCollapsiblePanel(QFrame):
    """Premium collapsible panel with a stable NeuroMood header."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        *,
        modo: str = "dark_hybrid",
        icon: str | None = None,
        status: str = "",
        expanded: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = modo
        self._expanded = bool(expanded)
        self._title_text = title
        self._icon_key = icon
        self.setObjectName("NMCollapsiblePanel")
        # La política vertical la fija _apply_state según el estado: colapsado
        # NO debe expandirse (absorbía el sobrante del layout padre y quedaba
        # una card vacía gigante con el header flotando, p.ej. REGISTROS
        # PREVIOS del TCC a ventana amplia).

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["sm"], V3_SP["sm"], V3_SP["sm"], V3_SP["sm"])
        root.setSpacing(V3_SP["sm"])

        self._header = QPushButton()
        self._header.setObjectName("NMCollapsibleHeader")
        self._header.setCheckable(True)
        self._header.setChecked(self._expanded)
        # Sin foco persistente: el click dejaba el anillo de foco global
        # pintado sobre todo el header (resplandor gigante — owner v1.0).
        self._header.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._header.clicked.connect(self.set_expanded)
        header_lay = QHBoxLayout(self._header)
        header_lay.setContentsMargins(V3_SP["sm"], 0, V3_SP["sm"], 0)
        header_lay.setSpacing(V3_SP["sm"])

        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        header_lay.addWidget(self._icon)

        self._title = QLabel(title)
        self._title.setFont(eyebrow_font())
        header_lay.addWidget(self._title, stretch=1)

        self._status = QLabel(status)
        self._status.setFont(qfont("size_caption"))
        header_lay.addWidget(self._status)

        self._chevron = QLabel()
        self._chevron.setFont(qfont("size_caption"))
        header_lay.addWidget(self._chevron)
        root.addWidget(self._header)

        self._body = QWidget()
        self._body.setObjectName("NMCollapsibleBody")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(V3_SP["sm"])
        root.addWidget(self._body, stretch=1)

        self._animation = QPropertyAnimation(self._body, b"maximumHeight", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._apply_state(animated=False)
        self.apply_theme(modo)

    def content_layout(self) -> QVBoxLayout:
        return self._body_lay

    def set_content(self, widget: QWidget) -> None:
        while self._body_lay.count():
            item = self._body_lay.takeAt(0)
            old = item.widget()
            if old is not None:
                old.setParent(None)
        self._body_lay.addWidget(widget)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self._apply_state(animated=True)
        self.toggled.emit(self._expanded)

    def is_expanded(self) -> bool:
        return self._expanded

    def apply_theme(self, modo: str) -> None:
        self._modo = modo
        text = v3c("text", modo).name()
        muted = v3c("text2", modo).name()
        surface = v3c("surface", modo).name()
        border = C("borderSoft", modo)
        hover = v3c("bgAlt", modo).name()
        self.setStyleSheet(
            f"QFrame#NMCollapsiblePanel {{ background: {surface}; "
            f"border: 1px solid {border}; border-radius: 14px; }}"
            f"QPushButton#NMCollapsibleHeader {{ background: transparent; "
            f"border: none; min-height: 34px; text-align: left; }}"
            f"QPushButton#NMCollapsibleHeader:hover {{ background: {hover}; "
            f"border-radius: 10px; }}"
            f"QWidget#NMCollapsibleBody {{ background: transparent; }}"
        )
        self._title.setStyleSheet(f"color: {text}; background: transparent;")
        self._status.setStyleSheet(f"color: {muted}; background: transparent;")
        self._chevron.setStyleSheet(f"color: {muted}; background: transparent;")
        if self._icon_key:
            icon = nm_icon(self._icon_key, text, 18)
            self._icon.setPixmap(icon.pixmap(18, 18) if isinstance(icon, QIcon) else icon)
        else:
            self._icon.clear()

    def _apply_state(self, *, animated: bool) -> None:
        self._header.setChecked(self._expanded)
        self._chevron.setText("▾" if self._expanded else "▸")
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding if self._expanded else QSizePolicy.Policy.Fixed,
        )
        self.updateGeometry()
        if not animated:
            self._body.setVisible(self._expanded)
            self._body.setMaximumHeight(0 if not self._expanded else 16777215)
            return
        self._animation.stop()
        if self._expanded:
            self._body.setMaximumHeight(0)
            self._body.setVisible(True)
            hint = max(self._body.sizeHint().height(), 80)
            self._animation.setStartValue(0)
            self._animation.setEndValue(hint)
            self._animation.start()
        else:
            self._animation.setStartValue(self._body.height())
            self._animation.setEndValue(0)
            self._animation.finished.connect(self._on_collapse_done)
            self._animation.start()

    def _on_collapse_done(self) -> None:
        self._animation.finished.disconnect(self._on_collapse_done)
        if not self._expanded:
            self._body.setVisible(False)


class NMSegmentedPanel(QWidget):
    """Compact tab surface for equivalent subpanels."""

    def __init__(self, *, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        self._buttons: list[QPushButton] = []
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(V3_SP["sm"])
        self._nav = QHBoxLayout()
        self._nav.setSpacing(V3_SP["xs"])
        root.addLayout(self._nav)
        self._stack = QStackedWidget()
        root.addWidget(self._stack, stretch=1)
        self.apply_theme(modo)

    def add_panel(self, title: str, widget: QWidget) -> None:
        index = self._stack.addWidget(widget)
        btn = QPushButton(title)
        btn.setCheckable(True)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda _=False, i=index: self._stack.setCurrentIndex(i))
        self._group.addButton(btn)
        self._nav.addWidget(btn)
        self._buttons.append(btn)
        if index == 0:
            btn.setChecked(True)
        self.apply_theme(self._modo)

    def apply_theme(self, modo: str) -> None:
        self._modo = modo
        text = v3c("text", modo).name()
        muted = v3c("text2", modo).name()
        primary = v3c("primary", modo).name()
        soft = v3c("bgAlt", modo).name()
        for btn in self._buttons:
            btn.setFont(qfont("size_caption", weight=500))
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {muted}; "
                f"border: 1px solid transparent; border-radius: 16px; "
                f"padding: 4px 12px; min-height: 32px; }}"
                f"QPushButton:hover {{ background: {soft}; color: {text}; }}"
                f"QPushButton:checked {{ background: {soft}; color: {primary}; "
                f"border-color: {primary}; }}"
            )


class NMSplitPanel(QFrame):
    """Plegable side/bottom panel with predictable collapsed size."""

    def __init__(
        self,
        title: str,
        *,
        modo: str = "dark_hybrid",
        expanded_width: int = 280,
        collapsed_width: int = 48,
        parent=None,
    ):
        super().__init__(parent)
        self._expanded_width = expanded_width
        self._collapsed_width = collapsed_width
        self._expanded = True
        self._title_text = title
        self._modo = modo
        self.setObjectName("NMSplitPanel")
        self.setMinimumWidth(collapsed_width)
        self.setMaximumWidth(expanded_width)

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["sm"], V3_SP["sm"], V3_SP["sm"], V3_SP["sm"])
        root.setSpacing(V3_SP["sm"])
        self._toggle = QToolButton()
        self._toggle.setText(title)
        self._toggle.clicked.connect(lambda: self.set_expanded(not self._expanded))
        root.addWidget(self._toggle)
        self._body = QWidget()
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(V3_SP["sm"])
        root.addWidget(self._body, stretch=1)
        self.apply_theme(modo)

    def content_layout(self) -> QVBoxLayout:
        return self._body_lay

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self._body.setVisible(self._expanded)
        self.setMaximumWidth(self._expanded_width if self._expanded else self._collapsed_width)
        self._toggle.setText(self._title_text if self._expanded else self._title_text[:1])

    def apply_theme(self, modo: str) -> None:
        self._modo = modo
        self.setStyleSheet(
            f"QFrame#NMSplitPanel {{ background: {v3c('surface', modo).name()}; "
            f"border: 1px solid {C('border', modo)}; border-radius: 14px; }}"
        )


# Alias: NMPanelTabs es un NMSegmentedPanel con nombre semántico para contextos
# donde el énfasis es en tabs de navegación (no en paneles colapsables).
NMPanelTabs = NMSegmentedPanel


class NMResponsiveColumns(QWidget):
    """Contenedor que alterna entre fila (columnas) y columna (apiladas) según su
    ancho REAL, en vez de min/max widths fijos que se solapan a 960×600.

    Implementado con un único ``QBoxLayout`` cuyo ``direction`` cambia en
    ``resizeEvent`` (idioma Qt limpio: no se reconstruye el layout). Cada columna
    conserva su ``stretch``, que aplica tanto en horizontal como en vertical.

    Uso típico (Banco):
        cont = NMResponsiveColumns(stack_below=BP_STACK)
        cont.add_column(form_widget, stretch=0)   # arriba al apilar
        cont.add_column(banco_widget, stretch=1)  # abajo/expande
    """

    reflowed = pyqtSignal(bool)  # True cuando pasa a apilado (vertical)

    def __init__(self, *, stack_below: int = BP_STACK, spacing: int | None = None, parent=None):
        super().__init__(parent)
        self._stack_below = int(stack_below)
        self._stacked: bool | None = None
        self._lay = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(V3_SP["md"] if spacing is None else spacing)

    def add_column(self, widget: QWidget, *, stretch: int = 0) -> None:
        self._lay.addWidget(widget, stretch)

    def is_stacked(self) -> bool:
        return bool(self._stacked)

    def resizeEvent(self, e):  # noqa: N802 (Qt override)
        super().resizeEvent(e)
        stacked = e.size().width() < self._stack_below
        if stacked != self._stacked:
            self._stacked = stacked
            self._lay.setDirection(
                QBoxLayout.Direction.TopToBottom
                if stacked
                else QBoxLayout.Direction.LeftToRight
            )
            self.reflowed.emit(stacked)
