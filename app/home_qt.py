"""
app/home_qt.py — Vista Home v3 Premium (PyQt6)

Layout a 960x600:
  QVBoxLayout full-width
  ├── hero de bienestar
  └── QGridLayout de ModuleCards

API pública: HomeView(modo, on_module_open, get_status_fn, username, parent)
             .set_modo(modo) / .refresh_statuses() / .resizeEvent()
"""

import logging
import os
import sys
from datetime import datetime

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QAbstractAnimation,
    QVariantAnimation,
    QPoint,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QDialog,
    QScrollArea,
    QPushButton,
    QStackedWidget,
)

try:
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        interpolate_color,
        gradient_colors,
        ThemeAwareWidgetMixin,
        SessionColor,
        aura_opacity,
        v3c,
        V3_SP,
        V3_RD,
        v3_font,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY, V3_RADIUS, V3_SHADOWS
    from shared.components import (
        ThemeManager,
        NMIcon,
        NMModuleRing,
        NMButton,
        NMToggle,
        NMSettingsSection,
        NMInput,
        NMToast,
        NMCard,
        NMWaveChart,
        NMProgressBar,
        NMChartPanel,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C,
        norm_modo,
        qfont,
        interpolate_color,
        gradient_colors,
        ThemeAwareWidgetMixin,
        SessionColor,
        v3c,
        V3_SP,
        V3_RD,
        v3_font,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.components import (
        ThemeManager,
        NMIcon,
        NMModuleRing,
        NMButton,
        NMToggle,
        NMSettingsSection,
        NMInput,
        NMToast,
        NMCard,
        NMWaveChart,
        NMProgressBar,
    )

from shared.visual_qa import visual_qa_enabled
from shared.remote_config import t


# ── Módulos ───────────────────────────────────────────────────────────────────

MODULES_CONFIG = [
    {
        "id": "animo",
        "icon_v3": "mood",
        "title": "Termómetro Emocional",
        "desc": "Registro emocional diario",
        "chip": "Bienestar",
    },
    {
        "id": "respiracion",
        "icon_v3": "breath",
        "title": "Guía de Respiración Animada",
        "desc": "Técnicas de calma 4-7-8",
        "chip": "Calma",
    },
    {
        "id": "registro",
        "icon_v3": "brain",
        "title": "Registro de Pensamientos (TCC)",
        "desc": "Pensamientos automáticos",
        "chip": "Cognitivo",
    },
    {
        "id": "rutina",
        "icon_v3": "routine",
        "title": "Checklist de Rutina Diaria",
        "desc": "Checklist del día",
        "chip": "Hábitos",
    },
    {
        "id": "actividades",
        "icon_v3": "run",
        "title": "Asistente de Activación Conductual",
        "desc": "Activación conductual",
        "chip": "Acción",
    },
    {
        "id": "timer",
        "icon_v3": "timer",
        "title": "Temporizador de Actividades",
        "desc": "Sesiones de enfoque",
        "chip": "Focus",
    },
    {
        "id": "avisos",
        "icon_v3": "bell",
        "title": "Recordatorios de Bienestar",
        "desc": "Recordatorios del día",
        "chip": "Diario",
    },
    {
        "id": "dbt",
        "icon_v3": "spark",
        "title": "Habilidades DBT",
        "desc": "Práctica guiada breve",
        "chip": "Habilidades",
    },
]


def _dot_color(idx: int, modo: str) -> str:
    """Color degradado teal→violet según posición del módulo."""
    grad = gradient_colors(norm_modo(modo))
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[-1], t)


# ── _SettingsPanel ────────────────────────────────────────────────────────────────


class _SettingsPanel(QWidget):
    """
    Panel de ajustes de Home (F3.B) — overlay modal centrado.

    Secciones:
      1. Inicio con Windows — NMToggle → _get_autostart/_set_autostart
         de avisos_daemon (NO reimplementado aquí).
      2. Modo privacidad:
           - Toggle “Pedir PIN al abrir” → privacy_lock_enabled.
           - Botón “Configurar / cambiar PIN” → mini-dialog interno.
      3. Apariencia — dark / light toggle (reutiliza ThemeManager).
    """

    def __init__(self, parent: QWidget, modo: str, on_theme_switch=None):
        # Overlay HIJO del Home (no QDialog top-level translúcido). El enfoque
        # anterior (Dialog frameless + WA_TranslucentBackground) pintaba el fondo
        # en NEGRO en light (feedback P0). Como widget hijo, el scrim se pinta
        # theme-aware en paintEvent y nunca hay ventana negra.
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._on_theme_switch = on_theme_switch

        # Tamaño fijo 380px de ancho, alto = contenido. El fade se hace animando
        # el alpha del scrim en paintEvent (NO QGraphicsOpacityEffect sobre el
        # overlay: anidar efectos con los drop-shadow de las secciones hijas
        # deja el subtree en blanco — bug clásico de Qt con effects anidados).
        self._panel_w = 380
        self._scrim_alpha = 1.0
        self._build_ui()
        self._apply_panel_theme()
        ThemeManager.instance().theme_changed.connect(self._on_theme_changed)

    def showEvent(self, event):
        # Sincronizar geometría con el padre al mostrarse (la geometría pasada a
        # show_panel puede quedar stale si el Home aún no terminó su layout) y
        # seguir sus resizes mientras el overlay esté visible.
        par = self.parentWidget()
        if par is not None:
            par.installEventFilter(self)
            self.setGeometry(par.rect())
            self._center_card()
        super().showEvent(event)

    def hideEvent(self, event):
        par = self.parentWidget()
        if par is not None:
            par.removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, obj, ev):
        if (
            obj is self.parentWidget()
            and ev.type() == QEvent.Type.Resize
            and self.isVisible()
        ):
            self.setGeometry(obj.rect())
            self._center_card()
        return super().eventFilter(obj, ev)

    def paintEvent(self, event):
        # Scrim theme-aware sobre el Home: en dark negro translúcido; en light la
        # tinta profunda del tema a baja alpha (nunca negro pleno).
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if "dark" in self._modo:
            scrim = QColor(0, 0, 0, 110)
        else:
            ink = v3c("text", self._modo)
            scrim = QColor(ink.red(), ink.green(), ink.blue(), 70)
        scrim.setAlpha(int(scrim.alpha() * max(0.0, min(1.0, self._scrim_alpha))))
        p.fillRect(self.rect(), scrim)
        p.end()

    # ── construcción ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # El card flota sobre un overlay translúcido y se centra manualmente en
        # show_panel (sin layout raíz). Antes era un drawer de altura completa
        # anclado a la derecha; ahora es un modal compacto centrado.
        self._card = QFrame(self)
        self._card.setObjectName("SettingsCard")
        self._card.setFixedWidth(self._panel_w)
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # Header del panel
        header = QWidget(self._card)
        header.setStyleSheet("background: transparent;")
        header.setFixedHeight(52)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(V3_SP["lg"], 0, V3_SP["sm"], 0)
        h_lay.setSpacing(V3_SP["sm"])

        title_lbl = QLabel("Ajustes")
        title_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        self._header_title = title_lbl
        h_lay.addWidget(title_lbl)
        h_lay.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._animate_close)
        self._close_btn = close_btn
        h_lay.addWidget(close_btn)
        card_lay.addWidget(header)

        # Separador
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        card_lay.addWidget(self._sep)

        # Cuerpo compacto (sólo 2 secciones → sin scroll).
        body = QWidget(self._card)
        body.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        body_lay.setSpacing(V3_SP["md"])
        card_lay.addWidget(body)

        # ── 1. Inicio con Windows ──────────────────────────────────────────
        sec_win = NMSettingsSection("Inicio con Windows", modo=self._modo)
        try:
            from app.avisos_daemon import _get_autostart, _set_autostart

            self._autostart_enabled = True
        except Exception:
            self._autostart_enabled = False

        self._autostart_toggle = NMToggle(modo=self._modo)
        if self._autostart_enabled:
            self._autostart_toggle.setChecked(_get_autostart())
            # P2.I: cuando el usuario toca el toggle, marcamos autostart como
            # "ya seteado por el usuario" para que el default no lo vuelva a
            # forzar en próximos arranques.
            self._autostart_toggle.toggled.connect(self._on_autostart_toggled)
        else:
            self._autostart_toggle.setEnabled(False)
            self._autostart_toggle.setToolTip("No disponible en esta plataforma")
        sec_win.add_row("Iniciar con Windows", self._autostart_toggle)
        body_lay.addWidget(sec_win)
        self._sec_win = sec_win

        # ── 2. Modo privacidad ────────────────────────────────────────────
        sec_priv = NMSettingsSection("Privacidad", modo=self._modo)

        try:
            from app.privacy_lock_qt import (
                is_lock_enabled,
                set_lock_enabled,
                set_pin,
            )

            self._privacy_available = True
            self._is_lock_enabled = is_lock_enabled
            self._set_lock_enabled = set_lock_enabled
            self._set_pin_fn = set_pin
        except Exception:
            self._privacy_available = False

        self._privacy_toggle = NMToggle(modo=self._modo)
        if self._privacy_available:
            self._privacy_toggle.setChecked(self._is_lock_enabled())
            self._privacy_toggle.toggled.connect(self._on_privacy_toggled)
        else:
            self._privacy_toggle.setEnabled(False)

        sec_priv.add_row("Pedir PIN al abrir", self._privacy_toggle)

        pin_btn = NMButton(
            "Configurar / cambiar PIN",
            modo=self._modo,
            variant="secondary",
            size="sm",
            width=220,
        )
        pin_btn.clicked.connect(self._show_pin_setup)
        self._pin_btn = pin_btn

        pin_row_w = QWidget()
        pin_row_w.setStyleSheet("background: transparent;")
        pin_row_lay = QHBoxLayout(pin_row_w)
        pin_row_lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        # Centrado horizontal (pedido owner): stretch a ambos lados del botón
        # de ancho fijo, en vez de quedar pegado a la izquierda.
        pin_row_lay.addStretch()
        pin_row_lay.addWidget(pin_btn)
        pin_row_lay.addStretch()
        sec_priv._rows.addWidget(pin_row_w)

        body_lay.addWidget(sec_priv)
        self._sec_priv = sec_priv

        # Identidad del producto, discreta al pie del panel.
        from shared.version import NM_VERSION

        self._version_lbl = QLabel(f"NeuroMood Suite · versión {NM_VERSION}")
        self._version_lbl.setFont(qfont("size_caption"))
        self._version_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        body_lay.addSpacing(V3_SP["xs"])
        body_lay.addWidget(self._version_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        # La sección "Apariencia" (Modo claro) se eliminó: el toggle de tema ya
        # vive en la titlebar (chrome.show_theme_toggle), era un duplicado.

    # ── autostart (P2.I) ─────────────────────────────────────────────────────

    def _on_autostart_toggled(self, checked: bool):
        """Aplica el toggle y marca autostart como 'seteado por el usuario' para
        que el default del primer arranque no lo vuelva a forzar."""
        try:
            from app.avisos_daemon import _set_autostart

            _set_autostart(bool(checked))
        except Exception:
            _log.exception("No se pudo aplicar toggle de autostart")
        try:
            from shared.db import conexion

            with conexion() as conn:
                conn.execute(
                    "INSERT INTO config (clave, valor) VALUES ('nm_autostart_user_set', '1') "
                    "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor"
                )
        except Exception:
            pass

    # ── animación ────────────────────────────────────────────────────────────

    def show_panel(self, parent_rect):
        """Overlay sobre la ventana del Home + modal compacto centrado con fade."""
        self.setGeometry(parent_rect)

        # Refresca estado autostart en cada apertura
        if self._autostart_enabled:
            try:
                from app.avisos_daemon import _get_autostart

                was = self._autostart_toggle.blockSignals(True)
                self._autostart_toggle.setChecked(_get_autostart())
                self._autostart_toggle.blockSignals(was)
            except Exception:
                pass

        # Refresca estado privacy lock
        if self._privacy_available:
            was = self._privacy_toggle.blockSignals(True)
            self._privacy_toggle.setChecked(self._is_lock_enabled())
            self._privacy_toggle.blockSignals(was)

        self.show()
        self.raise_()
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self._center_card()

        # Fade-in del scrim (el card aparece de inmediato; calma sin parpadeo).
        self._scrim_alpha = 0.0
        anim = QVariantAnimation(self)
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(self._set_scrim_alpha)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._open_anim = anim

    def _center_card(self):
        """Centra el card compacto (alto = contenido) sobre el overlay."""
        self._card.adjustSize()
        ch = self._card.sizeHint().height()
        max_h = max(120, self.height() - 48)
        ch = min(ch, max_h)
        self._card.setFixedHeight(ch)
        x = (self.width() - self._panel_w) // 2
        y = (self.height() - ch) // 2
        self._card.move(max(0, x), max(0, y))

    def _set_scrim_alpha(self, value):
        self._scrim_alpha = float(value)
        self.update()

    def _animate_close(self):
        """Fade-out del scrim y cierra."""
        anim = QVariantAnimation(self)
        anim.setDuration(130)
        anim.setStartValue(self._scrim_alpha)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.valueChanged.connect(self._set_scrim_alpha)
        anim.finished.connect(self.hide)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._close_anim = anim

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._animate_close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Click fuera del panel (en el overlay) cierra el panel."""
        if not self._card.geometry().contains(event.pos()):
            self._animate_close()
        else:
            super().mousePressEvent(event)

    # ── acciones ────────────────────────────────────────────────────────────

    def _on_privacy_toggled(self, checked: bool):
        if not self._privacy_available:
            return
        if checked:
            # No permitir activar el lock si todavía no hay PIN configurado.
            # Si el usuario activa sin PIN y cierra la app, quedará bloqueado
            # sin PIN que ingresar.
            try:
                from shared.db import leer_config as _lr
                existing_hash = _lr("privacy_pin_hash", "")
            except Exception:
                existing_hash = ""
            if not existing_hash:
                # Revertir el toggle antes de abrir el setup
                self._privacy_toggle.blockSignals(True)
                self._privacy_toggle.setChecked(False)
                self._privacy_toggle.blockSignals(False)
                # Abrir setup de PIN
                self._show_pin_setup()
                # Si el setup fue exitoso, activar el lock
                try:
                    from shared.db import leer_config as _lr2
                    new_hash = _lr2("privacy_pin_hash", "")
                except Exception:
                    new_hash = ""
                if new_hash:
                    self._set_lock_enabled(True)
                    self._privacy_toggle.blockSignals(True)
                    self._privacy_toggle.setChecked(True)
                    self._privacy_toggle.blockSignals(False)
                # Si no se configuró PIN (canceló), toggle queda en OFF
                return
        self._set_lock_enabled(checked)

    def _show_pin_setup(self):
        """Mini-dialog para ingresar / cambiar PIN."""
        if not self._privacy_available:
            return
        dlg = _PINSetupDialog(self.window(), self._modo)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pin = dlg.pin_value()
            if pin:
                self._set_pin_fn(pin)
                win = self.parent() or self
                NMToast.display(
                    win, "✅ PIN configurado correctamente.", variant="success", duration_ms=2000
                )

    # ── tema ──────────────────────────────────────────────────────────────

    def _on_theme_changed(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_panel_theme()

    def _apply_panel_theme(self):
        is_dark = "dark" in self._modo
        if is_dark:
            card_bg = v3c("surfaceSolid", self._modo).name()
            border = C("borderStrong", self._modo)
            title_col = v3c("text", self._modo).name()
            sep_col = C("borderSoft", self._modo)
            close_col = v3c("ink_secondary", self._modo).name()
        else:
            card_bg = v3c("surface", self._modo).name()
            border = C("border", self._modo)
            title_col = v3c("text", self._modo).name()
            sep_col = C("border", self._modo)
            close_col = v3c("ink_secondary", self._modo).name()

        self._card.setStyleSheet(
            f"#SettingsCard {{ background: {card_bg}; border: 1px solid {border}; "
            "border-radius: 22px; }"
        )
        self._header_title.setStyleSheet(f"color: {title_col}; background: transparent;")
        # Handoff §5: newsreader for clinical titles
        try:
            from shared.theme_qt import v3_font

            self._header_title.setFont(v3_font("size_h3", weight=600, serif=True))
        except Exception:
            pass

        self._sep.setStyleSheet(f"background: {sep_col};")
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 12px; color: {close_col}; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; "
            f"color: {v3c('text', self._modo).name()}; }}"
        )
        if hasattr(self, "_version_lbl"):
            self._version_lbl.setStyleSheet(
                f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
            )
        # El scrim del overlay se pinta theme-aware en paintEvent (no stylesheet
        # rgba negro). Forzar repaint por si cambió el tema con el panel abierto.
        self.update()


# ── _PINSetupDialog ───────────────────────────────────────────────────────────────


class _PINSetupDialog(QDialog):
    """Mini-dialog para ingresar y confirmar nuevo PIN."""

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        # Frameless + fondo opaco theme-aware: antes era un QDialog con titlebar
        # nativa y los controles flotaban sobre lienzo desnudo (en light el fondo
        # se veía negro/nativo, feedback P0/P1). Opaco (sin WA_TranslucentBackground)
        # para evitar el artefacto de esquinas negras del overlay translúcido.
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self._modo = norm_modo(modo)
        self._pin = ""
        self.setWindowTitle("Configurar PIN")
        self.setMinimumWidth(360)
        self._build()
        from shared.adaptive_layout_qt import apply_native_rounded_corners

        apply_native_rounded_corners(self)

    def _build(self):
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("borderStrong" if is_dark else "border", self._modo)
        from shared.adaptive_layout_qt import window_edge_radius

        self.setStyleSheet(
            f"_PINSetupDialog {{ background: {card_bg}; border: 1px solid {border}; "
            f"border-radius: {window_edge_radius()}px; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"], V3_SP["xl"], V3_SP["lg"])
        lay.setSpacing(V3_SP["md"])

        # Header: título + cerrar (no hay titlebar nativa).
        head = QHBoxLayout()
        title = QLabel("Nuevo PIN de privacidad")
        title.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        title.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        head.addWidget(title)
        head.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"border-radius: 12px; padding: 0px; "
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"}}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; "
            f"color: {v3c('text', self._modo).name()}; }}"
        )
        head.addWidget(close_btn)
        lay.addLayout(head)

        sub = QLabel("Ingresá un PIN de 4 a 6 dígitos.")
        sub.setFont(qfont("size_small"))
        sub.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()}; background: transparent;")
        lay.addWidget(sub)

        # Campo corto (4-6 dígitos): ancho acotado + alineación izquierda para que
        # el input no se estire a todo el diálogo (input gigante) — BL-03.
        self._pin_input = NMInput("PIN nuevo", modo=self._modo)
        self._pin_input.setEchoMode(NMInput.EchoMode.Password)
        self._pin_input.setMaxLength(6)
        self._pin_input.textChanged.connect(self._refresh_submit_state)
        lay.addWidget(self._pin_input)

        self._confirm_input = NMInput("Confirmar PIN", modo=self._modo)
        self._confirm_input.setEchoMode(NMInput.EchoMode.Password)
        self._confirm_input.setMaxLength(6)
        self._confirm_input.textChanged.connect(self._refresh_submit_state)
        lay.addWidget(self._confirm_input)

        self._err_lbl = QLabel("")
        self._err_lbl.setFont(qfont("size_small"))
        self._err_lbl.setStyleSheet(
            f"color: {v3c('danger', self._modo).name()}; background: transparent;"
        )
        self._err_lbl.setWordWrap(True)
        lay.addWidget(self._err_lbl)

        btn_row = QHBoxLayout()
        btn_cancel = NMButton("Cancelar", variant="secondary", size="md", modo=self._modo, width=110)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        self._btn_ok = NMButton("Guardar PIN", variant="primary", size="md", modo=self._modo, width=152)
        self._btn_ok.clicked.connect(self._on_accept)
        self._btn_ok.setEnabled(False)
        btn_row.addWidget(self._btn_ok)
        lay.addLayout(btn_row)

    def _refresh_submit_state(self):
        p1 = self._pin_input.text().strip()
        p2 = self._confirm_input.text().strip()
        self._btn_ok.setEnabled(bool(p1 and p2 and len(p1) >= 4))
        if self._err_lbl.text():
            self._err_lbl.setText("")

    def _on_accept(self):
        p1 = self._pin_input.text().strip()
        p2 = self._confirm_input.text().strip()
        if len(p1) < 4:
            self._err_lbl.setText("El PIN debe tener al menos 4 dígitos.")
            return
        if not p1.isdigit():
            self._err_lbl.setText("El PIN solo puede contener números.")
            return
        if p1 != p2:
            self._err_lbl.setText("Los PINes no coinciden.")
            return
        self._pin = p1
        self.accept()

    def pin_value(self) -> str:
        return self._pin

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()

    def center_on_parent(self):
        parent = self.parentWidget()
        if parent:
            self.adjustSize()
            parent_rect = parent.rect()
            parent_global_pos = parent.mapToGlobal(parent_rect.topLeft())
            x = parent_global_pos.x() + (parent_rect.width() - self.width()) // 2
            y = parent_global_pos.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)


# ── ModuleCard ────────────────────────────────────────────────────────────────


class ModuleCard(ThemeAwareWidgetMixin, QWidget):
    """Card de módulo v3 con NMIcon SVG y NMModuleRing."""

    def __init__(self, config: dict, idx: int, modo: str, on_click, get_status_fn, parent=None):
        super().__init__(parent)
        self._config = config
        self._idx = idx
        self._modo = norm_modo(modo)
        self._on_click = on_click
        self._get_status = get_status_fn
        self._accent = _dot_color(idx, modo)
        self._hover = False
        self._disabled = False
        self._disabled_reason = ""

        self._shadow: QGraphicsDropShadowEffect | None = None
        self._fade_eff: QGraphicsOpacityEffect | None = None

        # M2 P2-C: al quitar las cards "Progreso de Ánimo" y "Resumen Semanal",
        # las 8 cards de módulo se agrandan para ocupar el espacio liberado y
        # ganar presencia (más premium), sin solapar títulos de 2 líneas.
        # Altura elástica acotada: con alturas FIJAS en todos los items, el
        # QVBoxLayout del Home repartía el sobrante como huecos entre items
        # (voids proporcionales al agrandar la ventana). El chip de estado
        # queda anclado abajo por el stretch interno. Tope 288 (era 256): el
        # alto que liberó el hero compacto lo absorben estas cards.
        self.setMinimumHeight(150)
        self.setMaximumHeight(288)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._build_ui()
        self._connect_theme()
        self._apply_shadow(hover=False)

    def _apply_shadow(self, hover: bool):
        is_dark = "dark" in self._modo
        eff = QGraphicsDropShadowEffect(self)
        if hover:
            eff.setBlurRadius(20 if is_dark else 12)
            eff.setOffset(0, 6)
            eff.setColor(QColor(0, 0, 0, 85 if is_dark else 30))
        else:
            eff.setBlurRadius(8 if is_dark else 6)
            eff.setOffset(0, 2)
            eff.setColor(QColor(0, 0, 0, 45 if is_dark else 15))
        self._shadow = eff
        self.setGraphicsEffect(eff)

    def _set_shadow_state(self, hover: bool):
        self._apply_shadow(hover)

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)  # Premium: 20px padding
        layout.setSpacing(0)

        # Top row: icon + chip
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(4)
        self._icon = NMIcon(self._config["icon_v3"], size=18, color=self._accent, modo=self._modo)
        top.addWidget(self._icon)
        top.addStretch()
        self._chip = QLabel(self._config.get("chip", ""))
        self._chip.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._chip.setContentsMargins(5, 1, 5, 1)
        top.addWidget(self._chip)
        layout.addLayout(top)

        layout.addSpacing(6)

        # Title (reference cockpit clinical: cleaner sans)
        self._title_lbl = QLabel(self._config["title"])
        self._title_lbl.setFont(qfont("size_small", weight=600))
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(self._config["desc"])
        self._desc_lbl.setFont(qfont("size_caption_xs"))
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

        # Bottom row: badge + ring (size 22)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(4)
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._badge.setContentsMargins(6, 2, 6, 2)
        bottom.addWidget(self._badge)
        bottom.addStretch()
        self._ring = NMModuleRing(size=22, pct=0.0, modo=self._modo, show_label=False)
        self._ring.hide()
        bottom.addWidget(self._ring)
        layout.addLayout(bottom)

        self._apply_styles()
        self._refresh_status()
        self._set_shadow_state(False)

    def _apply_styles(self):
        is_dark = "dark" in self._modo
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        # Chip bg: warm tint in light, purple tint in dark.
        accent = v3c("accent", self._modo)
        if is_dark:
            chip_bg = v3c("accentSoft", self._modo)
        else:
            # Warm sand tint instead of cold mint — more coherent with ivory palette
            chip_bg = v3c("accentSoft", self._modo)
        self._chip.setStyleSheet(
            f"color: {accent.name()}; "
            f"background-color: rgba({chip_bg.red()},{chip_bg.green()},{chip_bg.blue()},{chip_bg.alpha()}); "
            f"border-radius: 6px;"
        )

    # ── status badge ──────────────────────────────────────────────────────────

    def _pill_style(self, color_hex: str, alpha_bg: float = 0.14) -> str:
        c = QColor(color_hex)
        a = int(alpha_bg * 255)
        return (
            f"color: {color_hex}; "
            f"background-color: rgba({c.red()},{c.green()},{c.blue()},{a}); "
            f"border-radius: 8px; padding: 2px 6px;"
        )

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        if self._disabled:
            self._badge.setText("No disponible")
            self._badge.setStyleSheet(self._pill_style(C("warning", self._modo)))
            self._ring.set_pct(0.0)
            return
        if status:
            mid = self._config["id"]
            low = status.lower()
            if "completo" in low:
                color = C("success", self._modo)
            elif "progreso" in low or "listos" in low or "/" in status:
                color = C("warning", self._modo)
            elif mid == "avisos":
                color = C("warning", self._modo)
            elif mid == "timer":
                color = C("accent", self._modo)
            elif mid == "rutina":
                color = (
                    C("success", self._modo)
                    if status.startswith("✓")
                    else C("warning", self._modo)
                    if "/" in status
                    else C("teal", self._modo)
                )
            else:
                color = C("teal", self._modo)
            self._badge.setText(status)
            self._badge.setStyleSheet(self._pill_style(color))
        else:
            self._badge.setText("")
            self._badge.setStyleSheet("background: transparent;")
        self._update_ring(status)

    def _update_ring(self, status: str = None):
        if status is None:
            status = self._get_status(self._config["id"])
        if not status:
            self._ring.set_pct(0.0)
            return
        clean = status.replace("✓", "").replace("✔", "").strip()
        if "En progreso" in clean:
            self._ring.set_pct(0.65 if self._config["id"] == "animo" else 0.50)
        elif clean == "Activo":
            self._ring.set_pct(0.84)
        elif clean == "Completo":
            self._ring.set_pct(1.0)
        elif "/" in clean:
            try:
                parts = clean.split("/")
                done = int(parts[0].strip())
                total = int(parts[1].strip().split()[0])
                self._ring.set_pct(done / total if total > 0 else 0.0)
            except Exception:
                self._ring.set_pct(0.0)
        elif self._config["id"] != "avisos":
            self._ring.set_pct(1.0)
        else:
            self._ring.set_pct(0.0)

    # ── paint v3 ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = "dark" in self._modo
        r = float(V3_RD["lg"])
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # Surface solid like .module-grid-card in the HTML mockup.
        if is_dark:
            surf = v3c("surfaceSolid", self._modo)
        else:
            surf = v3c("surface", self._modo)
        p.setBrush(QBrush(surf))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        is_active = self._hover and self.isEnabled() and not self._disabled

        # Border — más grueso y accent-tinted en hover
        if is_active:
            border_c = QColor(self._accent)
            border_c.setAlpha(200 if is_dark else 170)
            border_w = 1.5
        else:
            border_c = v3c("border", self._modo) if is_dark else v3c("borderStrong", self._modo)
            border_w = 1.0
        inset = border_w / 2.0
        p.setPen(QPen(border_c, border_w))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(inset, inset, w - 2 * inset, h - 2 * inset), r, r)

        # Disabled overlay
        if self._disabled:
            p.fillRect(rect, QColor(255, 255, 255, 22 if is_dark else 80))
        p.end()

    # ── eventos ───────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hover = True
        self._set_shadow_state(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._set_shadow_state(False)
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            not self._disabled
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.pos())
        ):
            self._on_click(self._config["id"])
        super().mouseReleaseEvent(event)

    # ── animación de entrada ──────────────────────────────────────────────────

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        # El shadow actual se reemplaza por un opacity effect mientras dura
        # la animación de entrada; Qt borra el shadow al cambiar el effect.
        # Al terminar, RECREAMOS un shadow nuevo en lugar de intentar restaurar
        # el original (que ya fue destruido).
        fade_eff = QGraphicsOpacityEffect(self)
        fade_eff.setOpacity(0.0)
        self.setGraphicsEffect(fade_eff)
        self._shadow = None  # shadow original ya destruido

        anim_fade = QPropertyAnimation(fade_eff, b"opacity", self)
        anim_fade.setDuration(300)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_done():
            # Recrear shadow para la elevación permanente del card
            try:
                self._apply_shadow(self._hover)
            except RuntimeError:
                # widget ya eliminado durante la animación
                pass

        anim_fade.finished.connect(_on_fade_done)
        anim_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        orig_y = self.y()
        self.move(self.x(), orig_y + 16)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(300)
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _dot_color(self._idx, self._modo)
        self._icon._color = self._accent
        self._icon._render()
        self._apply_styles()
        self._ring._modo = self._modo
        self._ring.update()
        # Re-crear shadow para reflejar tonos del nuevo modo (no reusar — el
        # objeto C++ puede haber sido invalidado por una animación previa)
        try:
            self._apply_shadow(self._hover)
        except RuntimeError:
            pass
        self._refresh_status()
        self.update()

    def refresh(self):
        self._refresh_status()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        self.setCursor(
            Qt.CursorShape.ForbiddenCursor if state else Qt.CursorShape.PointingHandCursor
        )
        self._refresh_status()
        self.update()


# ── _HeroBienestar ────────────────────────────────────────────────────────────
# Hero card del handoff §5.2: eyebrow + score serif grande + badge + mensaje
# cálido + barra progress gradient primary→amber. Se inserta arriba del grid
# de módulos como "primera impresión" de la Home.


class _HeroBienestar(QFrame):
    """Hero card de bienestar — handoff §5.2.

    No tiene lógica clínica propia: lee el último score vía callback y lo
    presenta visualmente. Si no hay registro, muestra un mensaje suave.
    """

    def __init__(
        self, modo: str, get_status_fn, on_registrar_click, username: str = "", parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._get_status = get_status_fn or (lambda mid: "")
        self._on_registrar_click = on_registrar_click
        # Nombre capitalizado (Fase 7): el saludo "Hola, juan" salía en minúscula
        # cuando el nombre venía así de la cuenta. Tomamos el primer nombre y
        # capitalizamos para un saludo prolijo ("Hola, Juan"). Guarda anti-split
        # vacío (nombre sólo-espacios → "Paciente").
        _parts = (username or "Paciente").split()
        self._username = _parts[0].capitalize() if _parts else "Paciente"
        self.setObjectName("NMCard")
        # Sin altura fija: el sizeHint del contenido manda (con el score "10"
        # lleno necesita ~142px; fijarlo en 112 recortaba el número grande).
        self._build_ui()
        self._apply_hero_shadow()
        self.refresh()

    def _apply_hero_shadow(self):
        """Drop shadow para dar elevación al hero card."""
        eff = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        eff.setBlurRadius(14 if is_dark else 10)
        eff.setOffset(0, 3)
        eff.setColor(QColor(0, 0, 0, 60 if is_dark else 20))
        self.setGraphicsEffect(eff)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(4)

        # Eyebrow row + badge derecho
        top = QHBoxLayout()
        self._eyebrow = QLabel("Bienvenida")
        self._eyebrow.setFont(eyebrow_font())
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        top.addWidget(self._eyebrow)
        top.addStretch()
        # Lazy import para evitar circular dependency en arranque
        try:
            from shared.components import NMBadge

            self._badge = NMBadge("Sin registro hoy", tone="neutral", modo=self._modo)
        except Exception:
            self._badge = QLabel("Sin registro hoy")
            self._badge.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        top.addWidget(self._badge)
        root.addLayout(top)

        self._hero_title = QLabel(f"Hola, {self._username}")
        self._hero_title.setFont(qfont("size_h1", weight=TYPOGRAPHY["weight_semibold"]))
        root.addWidget(self._hero_title)

        # Stacked area for empty vs filled
        self._stack = QStackedWidget(self)
        root.addWidget(self._stack)

        # ── Empty page ──
        self._empty_page = QWidget()
        empty_lay = QHBoxLayout(self._empty_page)
        empty_lay.setContentsMargins(0, 0, 0, 0)
        self._msg = QLabel(
            "Aquí tienes tu espacio personal. Arriba están tus módulos recomendados."
        )
        self._msg.setFont(qfont("size_small"))
        empty_lay.addWidget(self._msg)
        empty_lay.addStretch()

        self._btn_registrar = NMButton(
            "Registrar", variant="ghost", size="sm", modo=self._modo, width=90
        )
        self._btn_registrar.clicked.connect(self._on_registrar_click)
        empty_lay.addWidget(self._btn_registrar)
        self._stack.addWidget(self._empty_page)

        # ── Filled page ──
        self._filled_page = QWidget()
        filled_lay = QVBoxLayout(self._filled_page)
        filled_lay.setContentsMargins(0, 0, 0, 0)
        filled_lay.setSpacing(2)

        score_row = QHBoxLayout()
        score_row.setSpacing(4)
        score_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._score = QLabel("—")
        # Display M (26pt): sin el cartel de estado el hero se achica y el
        # espacio ganado lo absorben las cards de módulo (feedback owner).
        self._score.setFont(qfont("size_display_m", weight=TYPOGRAPHY["weight_medium"]))
        # Ancho mínimo para que "10" (dos dígitos) no se corte a 960×600.
        self._score.setMinimumWidth(40)
        self._score.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        score_row.addWidget(self._score)
        self._score_unit = QLabel("/ 10")
        self._score_unit.setFont(qfont("size_small"))
        score_row.addWidget(self._score_unit)

        # Delta inline
        self._delta_lbl = QLabel("")
        self._delta_lbl.setFont(qfont("size_small", bold=True))
        score_row.addWidget(self._delta_lbl)
        score_row.addStretch()
        filled_lay.addLayout(score_row)

        # Progress bar — dithered density gradient (reemplaza los QFrames raw)
        self._progress_bar = NMProgressBar(height=4, modo=self._modo)
        filled_lay.addWidget(self._progress_bar)

        self._stack.addWidget(self._filled_page)

        self._apply_styles()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(V3_RD["lg"])
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # Handoff §5.2: linear-gradient(135deg, var(--primary-soft), var(--surface))
        grad = QLinearGradient(0, 0, w, h)
        c1 = v3c("primary_soft", self._modo)
        c2 = v3c("surface", self._modo)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)

        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Border sutil
        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)
        p.end()

    def _apply_styles(self):
        accent = v3c("accent", self._modo)
        text2 = v3c("text2", self._modo)
        muted = v3c("textMuted", self._modo)
        text = v3c("text", self._modo)

        self._eyebrow.setStyleSheet(
            f"color: {text2.name()}; background: transparent;"
        )

        # Handoff §5.2: Greeting name in serif (Newsreader)
        # We'll use a mix: "Hola," in sans, name in serif if possible
        self._hero_title.setStyleSheet(f"color: {text.name()}; background: transparent;")

        # Try to use Newsreader for name
        from shared.theme_qt import v3_font

        self._hero_title.setFont(v3_font("size_h1", weight=600, serif=True))

        self._score.setStyleSheet(f"color: {accent.name()}; background: transparent;")
        self._score_unit.setStyleSheet(f"color: {muted.name()}; background: transparent;")
        self._msg.setStyleSheet(f"color: {text2.name()}; background: transparent;")


    def _parse_score(self, text: str):
        """Extrae float 0-10 del formato 'N/10' que emite _get_module_status."""
        if not text or "/" not in text:
            return None
        left = text.split("/", 1)[0].strip()
        try:
            val = float(left.replace(",", "."))
            if 0 <= val <= 10:
                return val
        except (ValueError, TypeError):
            pass
        return None

    def refresh(self):
        """Lee el score actual y actualiza el hero. Idempotente.

        El score es el PROMEDIO de los registros de hoy (bienestar combinado:
        los registros negativos restan). Sin cartel interpretativo de estado
        ("Estado positivo"/"Estable") — la interpretación es del profesional,
        no de la app (feedback owner).
        """
        raw = self._get_status("animo")
        score = self._parse_score(raw)
        if score is None:
            self._stack.setCurrentIndex(0)
            self._badge.show()
            try:
                self._badge.set_tone("neutral")
                self._badge.setText("Sin registro hoy")
            except Exception:
                pass
            return

        self._stack.setCurrentIndex(1)
        self._badge.hide()

        if score == int(score):
            self._score.setText(str(int(score)))
        else:
            self._score.setText(f"{score:.1f}".replace(".", ","))

        delta = 0.8 if visual_qa_enabled() else None
        if delta is not None:
            self._delta_lbl.setText(f"  ↑ {delta:.1f}")
            self._delta_lbl.setStyleSheet(
                f"color: {v3c('teal', self._modo).name()}; background: transparent;"
            )
            self._delta_lbl.show()
        else:
            self._delta_lbl.hide()

        self._progress_bar.animate_to(score / 10.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.refresh()
        except Exception:
            pass

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_styles()
        self._apply_hero_shadow()
        try:
            self._badge._apply_theme(self._modo)
        except Exception:
            pass


# ── _ProximaSesionCard ────────────────────────────────────────────────────────


class _ProximaSesionCard(QFrame):
    """Card 'Próxima sesión' — handoff SuiteHome columna derecha (1fr)."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setObjectName("NMCard")
        self.setFixedHeight(96)
        self._build_ui()
        self._apply_card_styles()
        self._apply_shadow()

    def _apply_shadow(self):
        eff = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        eff.setBlurRadius(14 if is_dark else 10)
        eff.setOffset(0, 3)
        eff.setColor(QColor(0, 0, 0, 60 if is_dark else 20))
        self.setGraphicsEffect(eff)

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        self._eyebrow = QLabel("Próxima sesión")
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)

        self._time_lbl = QLabel("—")
        self._time_lbl.setFont(qfont("size_heading_l", weight=600))
        lay.addWidget(self._time_lbl)

        self._therapist_lbl = QLabel("Sin sesión programada")
        self._therapist_lbl.setFont(qfont("size_small"))
        self._therapist_lbl.setWordWrap(True)
        lay.addWidget(self._therapist_lbl)

        lay.addStretch()

    def _apply_card_styles(self):
        surface = v3c("surface", self._modo)
        border = v3c("border", self._modo)
        is_dark = "dark" in self._modo
        if is_dark:
            surf = v3c("surfaceSolid", self._modo)
            surf_css = f"rgba({surf.red()},{surf.green()},{surf.blue()},160)"
        else:
            surf_css = f"rgba({surface.red()},{surface.green()},{surface.blue()},210)"
        border_css = f"rgba({border.red()},{border.green()},{border.blue()},{border.alpha()})"
        self.setStyleSheet(f"""
            QFrame#NMCard {{
                background-color: {surf_css};
                border: 1px solid {border_css};
                border-radius: {V3_RD["lg"]}px;
            }}
        """)
        text2 = v3c("text2", self._modo)
        muted = v3c("textMuted", self._modo)
        primary = v3c("primary", self._modo)
        self._eyebrow.setStyleSheet(
            f"color: {text2.name()}; background: transparent;"
        )
        self._time_lbl.setStyleSheet(f"color: {primary.name()}; background: transparent;")
        self._therapist_lbl.setStyleSheet(f"color: {muted.name()}; background: transparent;")

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_card_styles()
        self._apply_shadow()


# ── HomeView ──────────────────────────────────────────────────────────────────


class HomeView(QWidget):
    """Vista Home v3 Premium — contenido directo full-width.

    Layout:
      QHBoxLayout
      └── QWidget (content)
          ├── hero strip
          ├── QGridLayout — ModuleCard responsive
          └── QStretch
    """

    _theme_switch_requested = pyqtSignal(bool)

    def __init__(
        self,
        modo: str = "dark_hybrid",
        on_module_open=None,
        get_status_fn=None,
        username: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._open_cb = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._username = username
        self._cards: dict[str, ModuleCard] = {}
        self._grid_cols = 0
        self._session = SessionColor.instance()
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    # ── setup ─────────────────────────────────────────────────────────────────

    def _setup(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        # Root horizontal kept for shell compatibility; Home content is full-width.
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        content_lay = QVBoxLayout(content)
        # Márgenes verticales recortados: liberan altura para que la fila inferior
        # (chart + Resumen Semanal, stretch=1) no quede comprimida a 960×600 (BL-03).
        content_lay.setContentsMargins(24, 14, 24, 12)
        content_lay.setSpacing(0)

        self._hero = _HeroBienestar(
            self._modo,
            self._get_status,
            on_registrar_click=lambda: self._open_cb("animo"),
            username=self._username,
            parent=content,
        )
        # Hero compacto (score Display M + sin cartel de estado): tope 148 —
        # el alto liberado lo absorben las cards de módulo (feedback owner).
        # Bienvenida PRIMERO (decisión owner): el hero de bienestar abre el Home.
        self._hero.setMaximumHeight(148)
        self._hero.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._session_card = _ProximaSesionCard(self._modo, parent=content)
        self._session_card.hide()
        content_lay.addWidget(self._hero, stretch=1)
        content_lay.addSpacing(V3_SP["sm"])

        # El eyebrow "TUS MÓDULOS" y la tuerca se eliminaron del Home: la tuerca
        # vive ahora en la titlebar (chrome → settings_clicked); las cards de
        # módulo no necesitan rótulo. _SettingsPanel se crea lazy al primer open.
        self._settings_panel: _SettingsPanel | None = None

        # P2.C: cards de "Progreso de Ánimo" y "Resumen Semanal" removidas.
        # El espacio liberado se usa para agrandar las 8 cards de módulo (la grilla
        # pasa a ocupar el área que antes usaban esas dos cards).
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setVerticalSpacing(12)  # Premium: 12px gap
        self._grid.setHorizontalSpacing(12)  # Premium: 12px gap

        for idx, cfg in enumerate(MODULES_CONFIG):
            card = ModuleCard(
                cfg, idx, self._modo, on_click=self._open_cb, get_status_fn=self._get_status
            )
            self._cards[cfg["id"]] = card

        self._sync_availability()
        self._rebuild_grid()

        # SIN stretch final (feedback owner v1.0 r3): hero y cards absorben
        # TODO el alto disponible (máximos 192/256 cubren de sobra el contrato
        # 960×600 e incluso 1366×768) — el pie queda lleno, no "con resto".
        content_lay.addLayout(self._grid, stretch=3)

        root.addWidget(content, stretch=1)

        # Staggered entrance
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 55)

        # Apply initial token styles
        self._apply_theme(self._modo)

    # ── grid responsive ───────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        content_w = max(1, self.width())
        # compact R4: breakpoints calibrados para cards 200px mín en 1280×800
        if content_w >= 720:
            new_cols = 4
        elif content_w >= 540:
            new_cols = 3
        elif content_w >= 360:
            new_cols = 2
        else:
            new_cols = 1
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._rebuild_grid()

    def _rebuild_grid(self):
        content_w = max(1, self.width())
        if self._grid_cols:
            cols = self._grid_cols
        elif content_w >= 720:
            cols = 4
        elif content_w >= 540:
            cols = 3
        elif content_w >= 360:
            cols = 2
        else:
            cols = 1
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        # Equal column widths; no row-stretch so cards stay at natural height.
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        n = len(MODULES_CONFIG)
        num_rows = (n + cols - 1) // cols
        # Handoff §3 (Home): distribución balanceada al hueco del grid 4×2.
        # Con N módulos reales (7) en `cols` columnas, la última fila puede
        # tener menos celdas; las centramos para evitar un hueco visual.
        # Sin inventar features ni placeholders.
        last_row_count = n - (num_rows - 1) * cols if num_rows > 0 else n
        last_row_offset = max(0, (cols - last_row_count) // 2)
        for idx, cfg in enumerate(MODULES_CONFIG):
            card = self._cards.get(cfg["id"])
            if not card:
                continue
            row = idx // cols
            col = idx % cols
            if row == num_rows - 1 and last_row_count < cols:
                col = col + last_row_offset
            self._grid.addWidget(card, row, col)

    # ── API pública ───────────────────────────────────────────────────────────

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()
        if hasattr(self, "_weekly_mood"):
            self._weekly_mood.refresh()
        if hasattr(self, "_home_wave"):
            self._refresh_home_wave()
        # Refresh hero bienestar (handoff §5.2)
        if hasattr(self, "_hero"):
            self._hero.refresh()

    def set_sync_status(self, label: str, tone: str = "ok"):
        """Compatibility hook for the shell sync signal; Home no longer owns a footer."""
        return None

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    # ── Ajustes ──────────────────────────────────────────────────────────────

    def _open_settings(self):
        """Abre (o cierra si ya está visible) el panel de ajustes.

        El overlay es HIJO de la VENTANA (no del Home): la tuerca de la
        titlebar debe funcionar también con un módulo abierto — antes el
        panel quedaba dentro del Home oculto en el stack y no se veía
        (feedback owner v1.0).
        """
        host = self.window() or self
        if self._settings_panel is None:
            self._settings_panel = _SettingsPanel(
                parent=host,
                modo=self._modo,
                on_theme_switch=self._theme_switch_requested.emit,
            )
        if self._settings_panel.isVisible():
            self._settings_panel._animate_close()
        else:
            self._settings_panel.show_panel(host.rect())

    def _greeting_text(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        hour = datetime.now().hour
        if 5 <= hour < 12:
            prefix = t("text.home.greeting_morning", "Buenos días,").rstrip(",")
        elif 12 <= hour < 20:
            prefix = t("text.home.greeting_afternoon", "Buenas tardes,").rstrip(",")
        else:
            prefix = t("text.home.greeting_evening", "Buenas noches,").rstrip(",")
        return f"{prefix}, {name}"

    def _subtitle_text(self) -> str:
        return t(
            "text.home.subtitle",
            "Elegí un módulo para registrar cómo venís y sostener tu rutina.",
        )

    # ── permisos ──────────────────────────────────────────────────────────────

    def _disabled_reason(self, module_id: str) -> str:
        return {
            "rutina": "Tu profesional desactivó la rutina manual.",
            "actividades": "Tu profesional desactivó las actividades manuales.",
            "timer": "Tu profesional desactivó el temporizador manual.",
            "avisos": "Tu profesional desactivó los recordatorios manuales.",
        }.get(module_id, "Módulo no disponible.")

    def _sync_availability(self):
        for module_id, card in self._cards.items():
            available = self._is_module_available(module_id)
            card.set_disabled(
                not available, self._disabled_reason(module_id) if not available else ""
            )

    def _is_module_available(self, module_id: str) -> bool:
        if visual_qa_enabled():
            return True
        permission_keys = {
            "rutina": "perm_checklist_manual",
            "actividades": "perm_checklist_activacion",
            "timer": "perm_temporizador_manual",
            "avisos": "perm_recordatorios_manual",
        }
        key = permission_keys.get(module_id)
        if not key:
            return True
        try:
            from shared.db import leer_config

            return leer_config(key, "1") != "0"
        except Exception:
            return True

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        if hasattr(self, "_weekly_mood"):
            self._weekly_mood._apply_theme(self._modo)
        for card_name in ("_home_progress_card", "_home_attention_card"):
            card = getattr(self, card_name, None)
            if card is not None:
                card._apply_theme(self._modo)
        if hasattr(self, "_home_wave"):
            self._home_wave._apply_theme(self._modo)
        for lbl_name in (
            "_home_progress_eyebrow",
            "_home_attention_eyebrow",
        ):
            lbl = getattr(self, lbl_name, None)
            if lbl is not None:
                lbl.setStyleSheet(
                    f"color: {v3c('mute', self._modo).name()}; background: transparent;"
                )
        for lbl_name in ("_home_progress_title", "_home_attention_title"):
            lbl = getattr(self, lbl_name, None)
            if lbl is not None:
                lbl.setStyleSheet(
                    f"color: {v3c('text', self._modo).name()}; background: transparent;"
                )
        if hasattr(self, "_home_attention_body"):
            self._home_attention_body.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; background: transparent;"
            )
        if hasattr(self, "_home_assignment"):
            self._home_assignment.setStyleSheet(
                f"QLabel {{ color: {v3c('primary', self._modo).name()}; "
                f"background: {C('primary_soft', self._modo)}; "
                f"border-radius: 6px; padding: 8px; }}"
            )
        if hasattr(self, "_hero"):
            self._hero.apply_theme(self._modo)
        if hasattr(self, "_session_card"):
            self._session_card.apply_theme(self._modo)
        self.update()

    def _refresh_home_wave(self):
        if not hasattr(self, "_home_wave"):
            return
        if visual_qa_enabled():
            current = [3.0, 7.0, 4.0, 6.0, 8.0, 5.0, 7.2]
            previous = [4.0, 5.0, 5.5, 5.0, 6.0, 5.8, 6.2]
        else:
            try:
                from shared.utils import get_weekly_series

                current, previous = get_weekly_series()
            except Exception:
                current, previous = [None] * 7, [None] * 7
        self._home_wave.set_data(current, previous)

    # ── fondo ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        from shared.theme_qt import paint_shell_background

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_shell_background(p, QRectF(self.rect()), self._modo)
        p.end()
