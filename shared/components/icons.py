"""Icon, avatar and section-header display primitives."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import V3_SP, eyebrow_font, nm_icon, norm_modo, qfont, v3c

try:
    from shared.icons_svg import has_icon as _has_v3_icon, nm_svg_pixmap as _nm_svg_pixmap
except ImportError:
    try:
        from icons_svg import has_icon as _has_v3_icon, nm_svg_pixmap as _nm_svg_pixmap  # type: ignore
    except ImportError:
        _nm_svg_pixmap = None
        _has_v3_icon = lambda _n: False  # noqa: E731


def _tm() -> ThemeManager:
    return ThemeManager.instance()


class NMIcon(QLabel):
    """Widget de icono SVG v3.

    Args:
        name:      nombre del icono (``shared.icons_svg.available_icons()``).
        size:      lado del icono en px.
        color:     hex literal (estático).
        color_key: clave de la paleta v3 (``'text'``, ``'text2'``, ``'ink_secondary'``,
                   ``'teal'``, ``'violet'``, ``'danger'``…). Si se pasa, el
                   icono se re-renderiza automáticamente en cada theme change
                   y ``color`` se ignora.
        modo:      override de tema (None = sigue ThemeManager).

    Si el nombre no está en el catálogo v3, cae a QtAwesome vía
    :func:`shared.theme_qt.nm_icon` (compat durante migración).
    """

    def __init__(
        self,
        name: str,
        size: int = 24,
        color: str | None = None,
        color_key: str | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._name = name
        self._size = size
        self._color = color
        self._color_key = color_key
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._render()
        if color_key is not None:
            _tm().theme_changed.connect(self._apply_theme)

    # ── API ───────────────────────────────────────────────────────────────────

    def set_name(self, name: str):
        if name != self._name:
            self._name = name
            self._render()

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self.setFixedSize(size, size)
            self._render()

    def set_color(self, color: str):
        """Color hex estático (desactiva tracking de theme)."""
        self._color = color
        self._color_key = None
        try:
            _tm().theme_changed.disconnect(self._apply_theme)
        except (RuntimeError, TypeError):
            pass
        self._render()

    def set_color_key(self, key: str):
        """Color seguido a través de la paleta v3 (theme-aware)."""
        if self._color_key is None and key is not None:
            _tm().theme_changed.connect(self._apply_theme)
        self._color_key = key
        self._render()

    # ── render ───────────────────────────────────────────────────────────────

    def _resolve_color(self) -> str:
        if self._color_key is not None:
            return v3c(self._color_key, self._modo).name()
        if self._color:
            return self._color
        return v3c("text", self._modo).name()

    def _render(self):
        col = self._resolve_color()
        pix = None
        if _nm_svg_pixmap is not None and _has_v3_icon(self._name):
            pix = _nm_svg_pixmap(self._name, col, self._size)
        if pix is None or pix.isNull():
            # Fallback QtAwesome via nm_icon compatibility
            icon = nm_icon(self._name, col, self._size)
            pix = icon.pixmap(self._size, self._size)
        self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()


class NMSectionHeader(QWidget):
    """Encabezado de sección: eyebrow (caption all-caps suave) + título +
    opcional botón de acción a la derecha.

    Uso:
        h = NMSectionHeader("Última semana", "Tu progreso emocional")
        h.action_clicked.connect(self._on_view_all)
        h.set_action("Ver todo")
    """

    action_clicked = pyqtSignal()

    def __init__(self, eyebrow: str = "", title: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMSectionHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["xs"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._eyebrow = QLabel(eyebrow or "")
        # eyebrow_font = 11px tracked + AllUppercase (mockup `.eyebrow`), en vez
        # del caption_xs sin tracking ni mayúsculas que se usaba antes.
        self._eyebrow.setFont(eyebrow_font())
        top.addWidget(self._eyebrow)
        top.addStretch()
        self._action_btn: QPushButton | None = None
        lay.addLayout(top)

        title_row = QHBoxLayout()
        title_row.setSpacing(V3_SP["md"])
        self._title = QLabel(title or "")
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title.setWordWrap(True)
        title_row.addWidget(self._title, stretch=1)
        lay.addLayout(title_row)
        self._title_row = title_row

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_eyebrow(self, text: str):
        self._eyebrow.setText(text or "")
        self._eyebrow.setVisible(bool(text))

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_action(self, label: str | None):
        """Muestra/oculta el botón de acción a la derecha del título."""
        if not label:
            if self._action_btn is not None:
                self._action_btn.setParent(None)
                self._action_btn.deleteLater()
                self._action_btn = None
            return
        if self._action_btn is None:
            self._action_btn = QPushButton(label)
            self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._action_btn.setFlat(True)
            self._action_btn.clicked.connect(self.action_clicked.emit)
            self._title_row.addWidget(self._action_btn)
        else:
            self._action_btn.setText(label)
        self._style_action()

    def _style_action(self):
        if self._action_btn is None:
            return
        c = v3c("accent", self._modo).name()
        self._action_btn.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._action_btn.setStyleSheet(
            f"QPushButton {{ color: {c}; background: transparent; border: none; "
            f"padding: 4px 8px; }}"
            f"QPushButton:hover {{ color: {v3c('cyan', self._modo).name()}; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        eyebrow_col = v3c("text2", self._modo).name()
        title_col = v3c("text", self._modo).name()
        self._eyebrow.setStyleSheet(
            f"color: {eyebrow_col}; background: transparent;"
        )
        self._title.setStyleSheet(f"color: {title_col}; background: transparent;")
        self._style_action()


class NMAvatar(QWidget):
    """Avatar con iniciales (fallback) o QPixmap.

    Soporta dos modos de forma según el radio:
      - radius=None (default): círculo perfecto (avatar de paciente 40×40 r12
        en el mockup línea 247 → en realidad usa r12 para 40px size, NO es
        círculo perfecto; mantenemos círculo para compatibilidad histórica).
      - radius=N: rounded square con esquinas de radio N (ej: hero del Hub
        Detalle usa avatar 52×52 r15 según mockup).

    Uso:
        av = NMAvatar(initials="AM", size=44)  # círculo
        av = NMAvatar(initials="AM", size=52, radius=15)  # rounded square r15
        av.set_pixmap(QPixmap("foto.png"))
    """

    def __init__(
        self,
        initials: str = "",
        pixmap: QPixmap | None = None,
        size: int = 40,
        color_seed: str | None = None,
        modo: str = None,
        radius: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._initials = (initials or "?").strip().upper()[:2]
        self._pix = pixmap
        self._seed = color_seed or self._initials
        self._radius = radius  # None = círculo perfecto, int = rounded square
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_initials(self, text: str):
        self._initials = (text or "?").strip().upper()[:2]
        self._seed = text or self._initials
        self.update()

    def set_pixmap(self, pix: QPixmap | None):
        self._pix = pix
        self.update()

    def _seed_color_pair(self) -> tuple[QColor, QColor]:
        # Color determinístico desde el seed — gradiente entre accent y warm
        h = sum(ord(c) for c in self._seed) % 360
        # Mezclamos los dos acentos del tema según hash
        a = v3c("accent", self._modo)
        b = v3c("warm", self._modo)
        t = (h % 100) / 100.0
        # interp simple
        r = int(a.red() * (1 - t) + b.red() * t)
        g = int(a.green() * (1 - t) + b.green() * t)
        bl = int(a.blue() * (1 - t) + b.blue() * t)
        c1 = QColor(r, g, bl)
        c2 = QColor(min(255, r + 30), min(255, g + 30), min(255, bl + 30))
        return c1, c2

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        d = self.width()
        rect = QRectF(0, 0, d, d)
        # Path de clip según _radius: círculo (None) o rounded square (int)
        path = QPainterPath()
        if self._radius is None:
            path.addEllipse(rect)
        else:
            path.addRoundedRect(rect, self._radius, self._radius)
        if self._pix and not self._pix.isNull():
            # Clip según path y pintar pixmap
            p.setClipPath(path)
            scaled = self._pix.scaled(
                d,
                d,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.drawPixmap(0, 0, scaled)
        else:
            c1, c2 = self._seed_color_pair()
            grad = QLinearGradient(0, 0, d, d)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(1.0, c2)
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
            # Iniciales centradas en blanco
            p.setPen(QColor("#ffffff"))
            font_pt = max(10, int(d * 0.40))
            p.setFont(qfont(font_pt, weight=TYPOGRAPHY["weight_semibold"]))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._initials)
        # Borde sutil
        p.setClipping(False)
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        if self._radius is None:
            p.drawEllipse(QRectF(0.5, 0.5, d - 1, d - 1))
        else:
            p.drawRoundedRect(QRectF(0.5, 0.5, d - 1, d - 1), self._radius, self._radius)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()
