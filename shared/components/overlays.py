"""State/overlay widgets: empty states, error states, tooltips."""

from __future__ import annotations

from PyQt6.QtCore import (
    QAbstractAnimation,
    QPoint,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.theme_manager import ThemeManager
from shared.theme import TYPOGRAPHY
from shared.theme_qt import (
    C,
    ThemeAwareWidgetMixin,
    V3_RD,
    V3_SP,
    colors,
    nm_icon,
    norm_modo,
    qcolor_to_rgba_css,
    qfont,
    sp,
    v3_font,
    v3c,
)
from shared.components.buttons import NMButton


def _tm() -> ThemeManager:
    return ThemeManager.instance()


_NM_EMPTY_ICON_CHIP_SIZE = 64
_NM_EMPTY_ICON_CHIP_RADIUS = 18
_NM_EMPTY_ICON_SIZE = 30
_NM_EMPTY_TITLE_SIZE = 20
# Mockup `.empty p { max-width: 34ch }` (neuromood-mockup.html l.312). En
# Segoe UI 13.5px (default FONT_SANS de la app) el glyph "0" mide 10px →
# 34ch ≈ 340px. Antes pineado a 300px (<ch) y el body wrapeaba a 4 líneas
# en lugar de las 3 del spec. Ancho fijo para que el subtítulo wordwrap
# respete heightForWidth (ver nota en __init__).
_NM_EMPTY_SUBTITLE_WIDTH = 340


class NMEmptyState(ThemeAwareWidgetMixin, QWidget):
    """Widget de estado vacío con icono, título y subtítulo (runtime spec §2.11).

    Icono 30px dentro de chip PRIMARY_SOFT 64×64 r18.
    Título serif 20/600. Subtítulo body MUTE.
    Acepta hasta 2 CTAs opcionales (``cta_primary`` / ``cta_secondary``).
    """

    cta_primary_clicked = pyqtSignal()
    cta_secondary_clicked = pyqtSignal()

    def __init__(
        self,
        icon_key: str,
        title: str,
        subtitle: str,
        cta_primary: str = "",
        cta_secondary: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._icon_key = icon_key
        self._modo = norm_modo(_tm().modo)

        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        # Mockup canónico .empty (línea 306-307): padding 50px vertical × 24px horizontal.
        # Antes: sp("xl")=16 uniforme (tight).
        layout.setContentsMargins(24, 50, 24, 50)
        layout.setSpacing(V3_SP["md"])
        # Sin alignment a nivel layout: comprimía los QLabel wordwrap a su
        # sizeHint mínimo (título pisando el ícono, subtítulo recortado). Los
        # labels toman el ancho completo y centran su propio texto; el chip se
        # centra con alignment por-widget.

        # Chip contenedor del icono (64×64, PRIMARY_SOFT bg, r18)
        self._icon_chip = QFrame()
        self._icon_chip.setFixedSize(_NM_EMPTY_ICON_CHIP_SIZE, _NM_EMPTY_ICON_CHIP_SIZE)
        self._icon_chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chip_lay = QHBoxLayout(self._icon_chip)
        chip_lay.setContentsMargins(0, 0, 0, 0)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(_NM_EMPTY_ICON_SIZE, _NM_EMPTY_ICON_SIZE)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        chip_lay.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(V3_SP["sm"])

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(
            v3_font(_NM_EMPTY_TITLE_SIZE, "weight_semibold", serif=True)
        )
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel(subtitle)
        # Mockup línea 312: .empty p { font-size: 13.5px; color: ink-2; max-width: 34ch; line-height: 1.5 }
        # size_body=14 NO es canónico; pasamos 13.5 como setPointSizeFloat (QFont admite float).
        sub_font = v3_font("size_body", weight=TYPOGRAPHY["weight_regular"])
        sub_font.setPointSizeF(13.5)
        self._subtitle_lbl.setFont(sub_font)
        # Un QLabel wordwrap añadido a un QVBoxLayout CON alignment colapsa a su
        # sizeHint de una línea (Qt no llama heightForWidth en items alineados):
        # el subtítulo largo quedaba recortado a la primera línea ("Tu terapeuta…").
        # Fix: ancho fijo (34ch del mockup) + centrado vía HBox con stretches, así
        # heightForWidth produce la altura multi-línea real y el texto no se corta.
        self._subtitle_lbl.setFixedWidth(_NM_EMPTY_SUBTITLE_WIDTH)
        self._subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self._subtitle_lbl.setWordWrap(True)
        self._subtitle_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        _sub_row = QHBoxLayout()
        _sub_row.setContentsMargins(0, 0, 0, 0)
        _sub_row.addStretch(1)
        _sub_row.addWidget(self._subtitle_lbl)
        _sub_row.addStretch(1)
        layout.addLayout(_sub_row)

        # CTAs opcionales
        if cta_primary or cta_secondary:
            btn_row = QWidget()
            btn_row.setStyleSheet("background: transparent;")
            btn_row_lay = QHBoxLayout(btn_row)
            btn_row_lay.setContentsMargins(0, V3_SP["sm"], 0, V3_SP["sm"])
            btn_row_lay.setSpacing(V3_SP["sm"])
            btn_row_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if cta_primary:
                self._btn_primary = NMButton(
                    cta_primary, variant="gradient", size="sm", width=140, modo=self._modo
                )
                self._btn_primary.clicked.connect(self.cta_primary_clicked.emit)
                btn_row_lay.addWidget(self._btn_primary)
            if cta_secondary:
                self._btn_secondary = NMButton(
                    cta_secondary, variant="ghost", size="sm", width=120, modo=self._modo
                )
                self._btn_secondary.clicked.connect(self.cta_secondary_clicked.emit)
                btn_row_lay.addWidget(self._btn_secondary)
            layout.addWidget(btn_row)

        self._apply_theme(self._modo)
        self._connect_theme()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        # Chip: brand-soft del mockup (primarySoft) con r18.
        bg_css = qcolor_to_rgba_css(v3c("primarySoft", self._modo))
        self._icon_chip.setStyleSheet(
            f"QFrame {{ background-color: {bg_css}; "
            f"border-radius: {_NM_EMPTY_ICON_CHIP_RADIUS}px; }}"
        )
        icon_col = v3c("primary", self._modo)
        self._icon_lbl.setPixmap(
            nm_icon(self._icon_key, icon_col, size=_NM_EMPTY_ICON_SIZE).pixmap(
                _NM_EMPTY_ICON_SIZE, _NM_EMPTY_ICON_SIZE
            )
        )
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(
            f"color: {C('mute', self._modo)}; background: transparent;"
        )


class NMTooltip(QWidget):
    """Tooltip flotante con tema NM (alternativa al QToolTip nativo para casos
    que necesitan mayor control visual o autohide programable).

    Uso:
        tip = NMTooltip.show_for(parent_widget, "Texto del tooltip", duration_ms=2000)
    """

    @classmethod
    def show_for(
        cls, anchor: QWidget, text: str, duration_ms: int = 2500, modo: str = None
    ) -> "NMTooltip":
        tip = cls(text, modo=modo or _tm().modo, parent=anchor.window())
        # Posicionar arriba del anchor centrado
        pt = anchor.mapToGlobal(QPoint(anchor.width() // 2, 0))
        pt = tip.parent().mapFromGlobal(pt) if tip.parent() else pt
        tip.adjustSize()
        x = pt.x() - tip.width() // 2
        y = pt.y() - tip.height() - 8
        tip.move(max(8, x), max(8, y))
        tip.show()
        QTimer.singleShot(duration_ms, tip.fade_out)
        return tip

    def __init__(self, text: str = "", modo: str = None, parent=None):
        # Child overlay con parent real, sin window flags: un tooltip con
        # Qt.ToolTip era una ventana top-level que el lector de pantalla
        # resaltaba como mini ventana (informe user feedback, frente 2).
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        self._label = QLabel(text or "")
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(280)
        lay.addWidget(self._label)
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_text(self, text: str):
        self._label.setText(text or "")
        self.adjustSize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        is_dark = "dark" in self._modo
        bg = v3c("elevatedSolid" if is_dark else "elevated", self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.drawRoundedRect(rect, V3_RD["sm"], V3_RD["sm"])
        p.end()

    def _set_opacity(self, value):
        self._opacity = float(value)
        # El QLabel hijo pinta aparte: su color acompaña el fade vía alpha.
        c = v3c("text", self._modo)
        self._label.setStyleSheet(
            f"color: rgba({c.red()},{c.green()},{c.blue()},{int(255 * self._opacity)}); "
            "background: transparent;"
        )
        self.update()

    def fade_out(self, duration_ms: int = 200):
        # painter opacity, no QGraphicsOpacityEffect (efectos anidados).
        anim = QVariantAnimation(self)
        anim.setDuration(duration_ms)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.valueChanged.connect(self._set_opacity)
        anim.finished.connect(self.deleteLater)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self.update()


# ── NMErrorState ─────────────────────────────────────────────────────────────


class NMErrorState(QWidget):
    """Estado de error: icono + título + mensaje + opcional botón retry.

    Uso:
        err = NMErrorState("No se pudo cargar", "Verificá tu conexión.")
        err.retry_requested.connect(self._reload)
        err.set_retry("Reintentar")
    """

    retry_requested = pyqtSignal()

    def __init__(
        self, title: str = "Ocurrió un error", message: str = "", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["sm"])
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Chip contenedor del icono (64×64, DANGER_SOFT bg, r18)
        self._icon_chip = QFrame()
        self._icon_chip.setFixedSize(64, 64)
        self._icon_chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chip_lay = QHBoxLayout(self._icon_chip)
        chip_lay.setContentsMargins(8, 8, 8, 8)
        self._icon_lbl = QLabel("")
        self._icon_lbl.setFixedSize(48, 48)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        chip_lay.addWidget(self._icon_lbl)
        lay.addWidget(self._icon_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel(title or "")
        self._title.setFont(v3_font("size_display_m", "weight_medium"))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)
        lay.addWidget(self._title)

        self._msg = QLabel(message or "")
        self._msg.setFont(qfont("size_small"))
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg.setWordWrap(True)
        self._msg.setMaximumWidth(420)
        lay.addWidget(self._msg, alignment=Qt.AlignmentFlag.AlignCenter)

        self._retry_btn = QPushButton("")
        self._retry_btn.setVisible(False)
        self._retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._retry_btn.clicked.connect(self.retry_requested.emit)
        lay.addWidget(self._retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_message(self, text: str):
        self._msg.setText(text or "")

    def set_retry(self, label: str | None):
        if not label:
            self._retry_btn.setVisible(False)
            return
        self._retry_btn.setText(label)
        self._retry_btn.setVisible(True)
        self._style_retry()

    def _render_icon(self):
        try:
            from shared.icons_svg import nm_svg_pixmap, has_icon
        except ImportError:
            return
        col = v3c("danger", self._modo).name()
        name = "warning" if has_icon("warning") else "info"
        pix = nm_svg_pixmap(name, col, 40)
        if pix is not None and not pix.isNull():
            self._icon_lbl.setPixmap(pix)

    def _style_retry(self):
        accent = v3c("accent", self._modo).name()
        self._retry_btn.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._retry_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {accent}; "
            f"border: 1px solid {accent}; border-radius: 10px; "
            f"padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {qcolor_to_rgba_css(v3c('accentSoft', self._modo))}; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._msg.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        # Chip DANGER_SOFT
        danger_c = v3c("danger", self._modo)
        danger_c.setAlphaF(0.10)
        bg_css = f"rgba({danger_c.red()},{danger_c.green()},{danger_c.blue()},25)"
        if hasattr(self, "_icon_chip"):
            self._icon_chip.setStyleSheet(
                f"QFrame {{ background-color: {bg_css}; border-radius: 12px; }}"
            )
        self._render_icon()
        self._style_retry()
