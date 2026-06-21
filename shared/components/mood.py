"""Mood-related UI components: emoji, picker, slider, V3 mood slider."""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    QPointF,
    QRectF,
    QEasingCurve,
    QPropertyAnimation,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY, get_mood
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    C,
    V3_RD,
    V3_SP,
    norm_modo,
    qfont,
    qfont_mono,
    v3c,
    v3_font,
    qcolor_to_rgba_css,
    sp,
    stylesheet_slider,
)


def _tm() -> ThemeManager:
    return ThemeManager.instance()


try:
    from shared.icons_svg import nm_mood_pixmap as _nm_mood_pixmap
except ImportError:
    try:
        from icons_svg import nm_mood_pixmap as _nm_mood_pixmap  # type: ignore
    except ImportError:
        _nm_mood_pixmap = None


# ── NMMoodEmoji ───────────────────────────────────────────────────────────────


class NMMoodEmoji(QLabel):
    """Emoji de mood v3 — 10 niveles, SVG line-style.

    Spec del README (sección "Mood emoji system"):
      - Círculo de línea del color ``palette[lv]['to']``, sin relleno.
      - Ojos (2 círculos), boca curva (path varía con nivel).
      - Cejas inclinadas en niveles 1-3 y 9-10.
      - Lágrimas en 1-2, blush en 7-10, sparkles en 9-10 (+ corona en 10).
      - Halo radial opcional detrás (más fuerte en dark: 0.22 vs 0.15).

    El emoji es **100% SVG inline** — no usa Apple Color Emoji ni Unicode,
    coherente con el lenguaje visual del resto de iconos v3.

    Args:
        level: 1-10 (se clampa).
        size:  lado en px.
        glow:  halo radial detrás (default True).
        modo:  override de tema; afecta intensidad del halo.
    """

    def __init__(
        self, level: int = 5, size: int = 64, glow: bool = True, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._size = size
        self._glow = bool(glow)
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._render()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API ──────────────────────────────────────────────────────────────────

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level:
            self._level = lv
            self._render()

    def level(self) -> int:
        return self._level

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self.setFixedSize(size, size)
            self._render()

    def set_glow(self, glow: bool):
        if bool(glow) != self._glow:
            self._glow = bool(glow)
            self._render()

    # ── render ───────────────────────────────────────────────────────────────

    def _render(self):
        if _nm_mood_pixmap is None:
            return
        is_dark = "dark" in self._modo
        pix = _nm_mood_pixmap(self._level, self._size, glow=self._glow, is_dark=is_dark)
        if pix is not None and not pix.isNull():
            self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()


# ── NMEmojiPicker ─────────────────────────────────────────────────────────────


class NMEmojiPicker(QWidget):
    """5 botones circulares de emoji para selección de estado de ánimo (1-10).

    Emite picked(int) con el puntaje seleccionado. Las etiquetas aparecen
    debajo de la fila de botones, no sobre ellos.
    """

    picked = pyqtSignal(int)

    _CHIPS = [
        ("\U0001f61e", "Muy bajo", 1),
        ("\U0001f615", "Bajo", 3),
        ("\U0001f610", "Neutro", 5),
        ("\U0001f642", "Bien", 7),
        ("\U0001f604", "Excelente", 9),
    ]

    _BTN_SIZE = 48

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected: int | None = None
        self._btns: list[QPushButton] = []
        self._labels: list[QLabel] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(sp("sm"))

        for i, (emoji, label, score) in enumerate(self._CHIPS):
            btn = QPushButton(emoji)
            btn.setFixedSize(self._BTN_SIZE, self._BTN_SIZE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i, sc=score: self._select(idx, sc))
            btn_row.addWidget(btn)
            self._btns.append(btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        lbl_row = QHBoxLayout()
        lbl_row.setContentsMargins(0, 0, 0, 0)
        lbl_row.setSpacing(sp("sm"))

        for _, label, _ in self._CHIPS:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(self._BTN_SIZE)
            lbl_row.addWidget(lbl)
            self._labels.append(lbl)

        lbl_row.addStretch()
        outer.addLayout(lbl_row)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _select(self, idx: int, score: int):
        self._selected = idx
        self._apply_theme(self._modo)
        self.picked.emit(score)

    def selected_score(self) -> int | None:
        return self._CHIPS[self._selected][2] if self._selected is not None else None

    def set_score(self, score: int):
        for i, (_, _, sc) in enumerate(self._CHIPS):
            if score <= sc + 1:
                self._selected = i
                break
        self._apply_theme(self._modo)

    def reset(self):
        self._selected = None
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        from shared.theme_qt import colors
        teal = C("teal", self._modo)
        border = C("border", self._modo)
        bg_el = C("bg_elevated", self._modo)
        bg_ov = C("bg_overlay", self._modo)
        txt_s = C("text_secondary", self._modo)
        r = self._BTN_SIZE // 2

        for i, (btn, lbl) in enumerate(zip(self._btns, self._labels)):
            is_sel = i == self._selected
            if is_sel:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: 2px solid {teal};
                        border-radius: {r}px;
                        font-size: 18px;
                    }}
                    QPushButton:hover {{ background: {bg_ov}; }}
                """)
                lbl.setStyleSheet(
                    f"color: {teal}; font-weight: 500; font-size: {TYPOGRAPHY['size_caption']}px;"
                )
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg_el};
                        border: 1px solid {border};
                        border-radius: {r}px;
                        font-size: 17px;
                    }}
                    QPushButton:hover {{
                        background: {bg_ov};
                        border-color: {teal};
                    }}
                """)
                lbl.setStyleSheet(f"color: {txt_s}; font-size: {TYPOGRAPHY['size_caption']}px;")


# ── NMMoodSlider ──────────────────────────────────────────────────────────────


class NMMoodSlider(QFrame):
    """Slider de estado de ánimo 1-10 con empty state inicial (F1.6).

    Estado INICIAL (null):
    - Track neutral (sin fill de color)
    - Thumb oculto / transparente
    - Display "-- /10"
    - Label "Sin registro"
    - Helper "¿Cómo te sientes hoy?"

    PRIMERA INTERACCIÓN:
    - Revela thumb con opacity 1
    - Track fill usa MOOD_PALETTE según valor seleccionado
    - Display muestra valor numérico (ej: "7 /10")

    Signals:
        value_changed(int): emitido cuando se selecciona valor 1-10
        cleared():          emitido cuando se limpia el slider al estado null
    """

    value_changed = pyqtSignal(int)
    cleared = pyqtSignal()

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._has_value = False  # null state por defecto
        self.setObjectName("NMMoodSlider")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Layout principal ──
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["sm"])

        # ── Label de estado ──
        self._state_label = QLabel("Sin registro")
        self._state_label.setFont(v3_font("size_caption", weight=TYPOGRAPHY["weight_medium"]))
        lay.addWidget(self._state_label)

        # ── Slider row ──
        slider_row = QHBoxLayout()
        slider_row.setSpacing(V3_SP["md"])
        slider_row.setContentsMargins(0, 0, 0, 0)

        # QSlider: range 1-10, sin setValue() al inicio → null state
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 10)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(1)
        self._slider.setObjectName("MoodSliderInternal")
        self._slider.valueChanged.connect(self._on_value_changed)
        self._slider.sliderPressed.connect(self._on_first_interaction)
        slider_row.addWidget(self._slider, stretch=1)

        # Display numérico
        self._display = QLabel("-- /10")
        self._display.setFont(v3_font("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
        self._display.setMinimumWidth(60)
        self._display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self._display)

        lay.addLayout(slider_row)

        # ── Helper text ──
        self._helper = QLabel("¿Cómo te sientes hoy?")
        self._helper.setFont(v3_font("size_caption_xs", weight=TYPOGRAPHY["weight_regular"]))
        lay.addWidget(self._helper)

        # Opacity effect para transición suave del thumb
        self._opacity_effect = QGraphicsOpacityEffect(self._slider)
        self._opacity_effect.setOpacity(0.0)  # thumb oculto en estado null
        self._slider.setGraphicsEffect(self._opacity_effect)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _on_first_interaction(self):
        """Primera interacción con el slider: revela thumb progresivamente."""
        if not self._has_value:
            self._has_value = True
            self._animate_thumb_reveal()

    def _animate_thumb_reveal(self):
        """Transición suave de opacity 0 → 1 para el thumb."""
        self._thumb_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._thumb_anim.setDuration(180)
        self._thumb_anim.setStartValue(0.0)
        self._thumb_anim.setEndValue(1.0)
        self._thumb_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._thumb_anim.start()
        self._thumb_anim.finished.connect(self._update_stylesheet)

    def _on_value_changed(self, value: int):
        """Handler interno de valueChanged del QSlider."""
        if self._slider.hasMouse():
            self._apply_theme(self._modo)
        self.value_changed.emit(value)

    def _update_stylesheet(self):
        """Refresca el QSS del slider tras animación."""
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)

        # Colores del tema
        text_primary = v3c("text", self._modo)
        text_secondary = v3c("text2", self._modo)
        self._slider.setStyleSheet(stylesheet_slider(self._modo))

        # Label de estado
        self._state_label.setStyleSheet(f"color: {text_secondary.name()}; background: transparent;")
        self._display.setStyleSheet(f"color: {text_primary.name()}; background: transparent;")
        self._helper.setStyleSheet(
            f"color: {text_secondary.name()}; background: transparent; opacity: 0.7;"
        )

    def set_value(self, value: int | None):
        """Establece el valor del slider (1-10) o None para estado vacío."""
        if value is None:
            self._has_value = False
            self._slider.setValue(1)  # reset al mínimo internamente
            self._opacity_effect.setOpacity(0.0)
            self._display.setText("-- /10")
            self._state_label.setText("Sin registro")
            self._apply_theme(self._modo)
        else:
            clamped = max(1, min(10, int(value)))
            self._slider.setValue(clamped)
            if not self._has_value:
                self._has_value = True
                self._opacity_effect.setOpacity(1.0)
            self._display.setText(f"{clamped} /10")
            self._state_label.setText(get_mood(clamped)["name"])
            self._apply_theme(self._modo)

    def get_value(self) -> int | None:
        """Devuelve el valor actual (1-10) o None si está vacío."""
        return self._slider.value() if self._has_value else None

    def clear(self):
        """Limpia el slider al estado null inicial."""
        self._has_value = False
        self._slider.setValue(1)
        self._opacity_effect.setOpacity(0.0)
        self._display.setText("-- /10")
        self._state_label.setText("Sin registro")
        self._apply_theme(self._modo)
        self.cleared.emit()


# ── _MoodPickWidget / _MoodPickLabel / _MoodNumRow / _MoodTrackBar ─────────────


class _MoodPickWidget(QWidget):
    """Widget interno que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, value: int, parent=None):
        super().__init__(parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


class _MoodPickLabel(QLabel):
    """QLabel que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, text: str, value: int, parent=None):
        super().__init__(text, parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


# ── _MoodTrackBar (subcomponente del V3MoodSlider) ───────────────────────────


class _MoodNumRow(QWidget):
    """Fila de números 0-10 posicionados EXACTAMENTE bajo los slots del track.

    Usa la misma fórmula que ``_MoodTrackBar._slot_positions`` (margen 16 +
    i/10 del ancho útil). Con el layout anterior de stretches, el centro de
    cada número quedaba ~10px corrido del dot real del slider (informe user feedback
    v1.0, módulo Ánimo).

    Parámetro ``show_zero`` (2026-06): si es False, se omite la label del 0
    y los números 1-10 se reposicionan para quedar bajo los dots 1-10
    (fórmula ``(i+1)/10`` en vez de ``i/10``). Usado en el módulo Ánimo
    para mostrar la escala clínica 1-10 sin el tick 0.
    """

    def __init__(self, labels: list[QLabel], parent=None, show_zero: bool = True):
        super().__init__(parent)
        self._labels = labels
        self._show_zero = bool(show_zero)
        self.setFixedHeight(20)
        for lbl in labels:
            lbl.setParent(self)
            lbl.setFixedSize(24, 20)

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        margin = 16
        span = max(0, self.width() - 2 * margin)
        for i, lbl in enumerate(self._labels):
            if self._show_zero:
                x = margin + (i / 10) * span
            else:
                # Sin tick 0: los números 1-10 se posicionan bajo los dots 1-10
                x = margin + ((i + 1) / 10) * span
            lbl.move(int(x - lbl.width() / 2), 0)


class _MoodTrackBar(QWidget):
    """Track horizontal con gradient arcoíris emocional + 10 dots clickeables.

    El gradient NO varía con el theme (paleta emocional fija, ver README v3).
    El dot activo: 16x16 blanco con border 3px del color del nivel + halo.
    Dots inactivos: 6x6 semi-transparentes.
    """

    level_clicked = pyqtSignal(int)

    # 6-stop arcoíris canónico del mockup (neuromood-mockup.html línea 200):
    #   linear-gradient(90deg, #7b8a99, #6b8fa8, #5faa86, #86b15f, #c99a3d, #b24e3d)
    # PAleta emocional neutral (slate→teal→olive→amber→terracotta), NO saturada con
    # lavanda/rosa. Coincide con el slider arcoíris del mockup para Ánimo y TCC.
    _RAINBOW_STOPS = (
        ("#7b8a99", 0.00),
        ("#6b8fa8", 0.20),
        ("#5faa86", 0.40),
        ("#86b15f", 0.60),
        ("#c99a3d", 0.80),
        ("#b24e3d", 1.00),
    )

    def __init__(self, level: int = 5, parent=None, unset: bool = False):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        # Muesca 0 (feedback user feedback): el thumb arranca ESTACIONADO en un
        # 0 visual que NO es un valor registrable — al primer click/drag se
        # mueve a 1-10 y deja de estar unset. El 0 no responde a clicks.
        self._unset = bool(unset)
        self.setFixedHeight(56)
        self.setMinimumWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level or self._unset:
            self._level = lv
            self._unset = False
            self.update()

    def level(self) -> int:
        return self._level

    def set_unset(self, unset: bool = True):
        self._unset = bool(unset)
        self.update()

    def is_unset(self) -> bool:
        return self._unset

    def _slot_positions(self) -> list[float]:
        """11 slots equiespaciados: índice 0 = muesca de estacionamiento,
        índices 1-10 = niveles registrables."""
        margin_x = 16
        w = self.width() - 2 * margin_x
        return [margin_x + (i / 10) * w for i in range(11)]

    def _dot_positions(self) -> list[float]:
        return self._slot_positions()[1:]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        bar_y = h // 2 - 4
        bar_h = 8
        margin_x = 16
        bar_w = self.width() - 2 * margin_x
        bar_rect = QRectF(margin_x, bar_y, bar_w, bar_h)

        # Track con gradient rainbow (opacity .85 según JSX)
        grad = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
        for hex_c, pos in self._RAINBOW_STOPS:
            grad.setColorAt(pos, QColor(hex_c))
        path = QPainterPath()
        path.addRoundedRect(bar_rect, bar_h / 2, bar_h / 2)
        p.setOpacity(0.85)
        p.fillPath(path, QBrush(grad))
        p.setOpacity(1.0)

        # Muesca 0 (estacionamiento): anillo neutro sutil; el thumb descansa
        # acá mientras el paciente no eligió valor. Theme-aware: en light el
        # anillo blanco-sobre-card-clara era INVISIBLE (informe user feedback) —
        # se delinea con slate oscuro.
        _is_dark = "dark" in norm_modo(_tm().modo)
        slot0_x = self._slot_positions()[0]
        center_y = h / 2
        if self._unset:
            if _is_dark:
                ring = QColor(255, 255, 255, 120)
                halo = QColor(255, 255, 255, 18)
            else:
                ring = QColor(71, 85, 105, 150)
                halo = QColor(71, 85, 105, 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(QPointF(slot0_x, center_y), 9, 9)
            p.setBrush(QBrush(QColor("#ffffff")))
            p.setPen(QPen(ring, 2))
            p.drawEllipse(QPointF(slot0_x, center_y), 5.5, 5.5)
        else:
            _parked = (
                QColor(255, 255, 255, 110) if _is_dark else QColor(71, 85, 105, 110)
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_parked))
            p.drawEllipse(QPointF(slot0_x, center_y), 2.5, 2.5)

        # Dots (10)
        positions = self._dot_positions()
        for i, x in enumerate(positions):
            n = i + 1
            if n == self._level and not self._unset:
                brand = v3c("brand", _tm().modo)
                halo = QColor(v3c("brandSoft", _tm().modo))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(halo))
                p.drawEllipse(QPointF(x, center_y), 14, 14)
                # Mockup range thumb: 22x22, blanco/surface, borde brand 3px.
                p.setBrush(QBrush(QColor("#ffffff")))
                p.setPen(QPen(brand, 3))
                p.drawEllipse(QPointF(x, center_y), 11, 11)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 180)))
                p.drawEllipse(QPointF(x, center_y), 3, 3)
        p.end()

    def _level_at_x(self, x: float) -> int:
        # Solo niveles 1-10: la muesca 0 es inerte (no registrable).
        positions = self._dot_positions()
        return min(range(10), key=lambda i: abs(positions[i] - x)) + 1

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
            self.level_clicked.emit(n)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
                self.level_clicked.emit(n)
        super().mouseMoveEvent(event)


# ── V3MoodSlider ─────────────────────────────────────────────────────────────


class V3MoodSlider(QWidget):
    """Slider de mood 1-10 v3 (Suite > Mood Tracker > Slashbar 1-10).

    Composición:
      • Header: título + subtítulo + cluster derecho (eyebrow "HOY", nombre del
        nivel grande en color, "n/10" mono, emoji 104px con glow).
      • Slashbar gradient arcoíris emocional con 10 dots clickeables.
      • Fila de números 1-10 (mono); el activo coloreado del nivel.
      • Range descriptors (3 columnas: izq/centro/der).
      • Panel inferior con 10 mini emojis preview; el activo escala 1.18 + glow.

    Signal:
        level_changed(int)  emitido cada vez que cambia el nivel.
    """

    level_changed = pyqtSignal(int)

    def __init__(
        self,
        level: int = 5,
        title: str = "¿Cómo te sientes hoy?",
        subtitle: str = "Deslizá para encontrar el número que mejor describe tu estado.",
        modo: str = None,
        parent=None,
        compact: bool = False,
        unset: bool = False,
        show_zero: bool = True,
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self._unset = bool(unset)
        self._show_zero = bool(show_zero)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(V3_SP["xs"] if compact else V3_SP["lg"])

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(V3_SP["lg"])

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setFont(qfont("size_small"))
        self._subtitle_lbl.setWordWrap(True)
        title_col.addWidget(self._title_lbl)
        title_col.addWidget(self._subtitle_lbl)
        title_col.addStretch()
        header.addLayout(title_col, stretch=1)

        right = QHBoxLayout()
        right.setSpacing(V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._eyebrow_lbl = QLabel("Hoy")
        self._eyebrow_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl = QLabel("—" if self._unset else get_mood(self._level)["name"])
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl.setFont(qfont("size_display", weight=TYPOGRAPHY["weight_semibold"]))
        self._numeric_lbl = QLabel("—/10" if self._unset else f"{self._level}/10")
        self._numeric_lbl.setFont(qfont_mono(12, bold=False))
        self._numeric_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._numeric_lbl)
        text_col.addStretch()
        right.addLayout(text_col)

        self._emoji_big = NMMoodEmoji(level=self._level, size=104, glow=True, modo=self._modo)
        right.addWidget(self._emoji_big, alignment=Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(right)
        root.addLayout(header)

        # ── Slashbar ──────────────────────────────────────────────────────────
        self._track = _MoodTrackBar(level=self._level, unset=self._unset)
        self._track.level_clicked.connect(self._on_level_clicked)
        root.addWidget(self._track)

        # ── Fila de números 0-10 (el 0 es la muesca de estacionamiento; no
        # registra valor — feedback user feedback). _MoodNumRow los posiciona
        # con la MISMA fórmula del track: cada número queda centrado bajo su
        # dot real (antes el layout de stretches los corría ~10px).
        # (2026-06: si show_zero=False, se omite la label del 0 y los
        # números 1-10 se reposicionan para llenar el track 1-10.)
        self._num_labels: list[_MoodPickLabel] = []
        if self._show_zero:
            self._zero_lbl = QLabel("0")
            self._zero_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._zero_lbl.setFont(qfont_mono(10))
            num_row = _MoodNumRow(
                [self._zero_lbl, *[self._make_num_label(n) for n in range(1, 11)]],
                show_zero=True,
            )
        else:
            # Sin tick 0: solo los 10 números 1-10, reposicionados.
            self._zero_lbl = None
            num_row = _MoodNumRow(
                [self._make_num_label(n) for n in range(1, 11)],
                show_zero=False,
            )
        root.addWidget(num_row)

        # ── Range descriptors ─────────────────────────────────────────────────
        desc_row = QHBoxLayout()
        desc_row.setContentsMargins(0, V3_SP["sm"], 0, 0)
        d_left = QLabel("Necesito apoyo")
        d_mid = QLabel("En el medio")
        d_mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_right = QLabel("Me siento pleno")
        d_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        for d in (d_left, d_mid, d_right):
            d.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        desc_row.addWidget(d_left, 1)
        desc_row.addWidget(d_mid, 1)
        desc_row.addWidget(d_right, 1)
        self._desc_labels = (d_left, d_mid, d_right)
        root.addLayout(desc_row)

        # ── Panel inferior con 10 mini emojis ─────────────────────────────────
        self._preview_panel = QFrame()
        self._preview_panel.setObjectName("MoodPreviewPanel")
        prow = QHBoxLayout(self._preview_panel)
        prow.setContentsMargins(14, 16, 14, 16)
        prow.setSpacing(0)
        self._preview_cells: list[tuple[_MoodPickWidget, NMMoodEmoji, QLabel, int]] = []
        for n in range(1, 11):
            cell = _MoodPickWidget(n)
            cell.setFixedWidth(40)
            col = QVBoxLayout(cell)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(2)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            is_active = n == self._level and not self._unset
            emoji = NMMoodEmoji(
                level=n, size=(38 if is_active else 32), glow=is_active, modo=self._modo
            )
            num_lbl = QLabel(str(n))
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setFont(qfont_mono(9, bold=is_active))
            col.addWidget(emoji, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(num_lbl)
            cell.picked.connect(self._on_level_clicked)
            self._preview_cells.append((cell, emoji, num_lbl, n))
            prow.addWidget(cell)
            if n < 10:
                prow.addStretch()
        root.addWidget(self._preview_panel)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

        if compact:
            self._subtitle_lbl.hide()
            self._emoji_big.hide()
            d_left.hide()
            d_mid.hide()
            d_right.hide()
            self._preview_panel.hide()
            self._title_lbl.hide()
            self._eyebrow_lbl.hide()
            self._name_lbl.hide()
            self._numeric_lbl.hide()

    # ── API pública ──────────────────────────────────────────────────────────

    def level(self) -> int:
        return self._level

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv == self._level and not self._unset:
            return
        self._level = lv
        self._unset = False
        self._track.set_level(lv)
        self._emoji_big.set_level(lv)
        self._name_lbl.setText(get_mood(lv)["name"])
        self._numeric_lbl.setText(f"{lv}/10")
        self._refresh_styles()
        self.level_changed.emit(lv)

    def set_subtitle(self, text: str):
        self._subtitle_lbl.setText(text or "")

    def _on_level_clicked(self, n):
        self.set_level(int(n))

    def _make_num_label(self, n: int) -> "_MoodPickLabel":
        """Crea un _MoodPickLabel para el número n (1-10). Usado por _setup_ui
        para construir la fila de números, tanto con show_zero=True (11
        labels) como con show_zero=False (10 labels)."""
        lbl = _MoodPickLabel(str(n), n)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.picked.connect(self._on_level_clicked)
        return lbl

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._refresh_styles()

    def _refresh_styles(self):
        is_dark = "dark" in self._modo
        c_text = v3c("text", self._modo).name()
        c_text2 = v3c("text2", self._modo).name()
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        c_text4 = v3c("text4", self._modo).name()
        elev_key = "elevatedSolid" if is_dark else "elevated"
        c_elev = v3c(elev_key, self._modo).name()
        c_border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        lv_color = get_mood(self._level)["to"]

        self._title_lbl.setStyleSheet(f"color: {c_text}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        self._eyebrow_lbl.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {lv_color}; background: transparent;")
        self._numeric_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        for d in self._desc_labels:
            d.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        if hasattr(self, "_zero_lbl") and self._zero_lbl is not None:
            self._zero_lbl.setStyleSheet(f"color: {c_text4}; background: transparent;")
        for lbl in self._num_labels:
            active = lbl._value == self._level and not self._unset
            col = get_mood(lbl._value)["to"] if active else c_ink_secondary
            lbl.setFont(qfont_mono(11, bold=active))
            lbl.setStyleSheet(f"color: {col}; background: transparent;")
        for cell, emoji, num_lbl, n in self._preview_cells:
            active = n == self._level and not self._unset
            col = get_mood(n)["to"] if active else c_text4
            num_lbl.setFont(qfont_mono(9, bold=active))
            num_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._preview_panel.setStyleSheet(
            f"#MoodPreviewPanel {{ background: {c_elev}; "
            f"border: 1px solid {c_border}; border-radius: {V3_RD['lg']}px; }}"
        )
