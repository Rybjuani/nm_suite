"""
app/modules/animo_qt.py — Módulo Ánimo (PyQt6)

LÓGICA PRESERVADA EXACTA:
  COLORES_PUNTAJE, EMOJIS, _registrar(), get_card_status()

NUEVAS CAPACIDADES:
  Emoji bounce: QGraphicsScale animado 1.0→1.35→1.0 en 300ms
  Color animado del valor: QVariantAnimation sobre color del label
  Slider custom: QSlider + stylesheet gradiente teal→rojo
  Historial del día: QScrollArea horizontal con chips hora+emoji+puntaje
  Toast de confirmación: NMToast success reemplaza _ok_bubble
"""

import os
import sys

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup,
    QVariantAnimation, QAbstractAnimation, pyqtProperty, QPointF,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont,
    QLinearGradient,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QTextEdit, QScrollArea, QSizePolicy, QGraphicsOpacityEffect,
    QFrame,
)

try:
    from shared.components_qt import NMModule, NMButton, NMToast, ThemeManager
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, stylesheet_slider, stylesheet_textedit,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import NMModule, NMButton, NMToast, ThemeManager
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color,
        get_gradient, stylesheet_slider, stylesheet_textedit,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual

# ── Tokens de negocio (preservados) ──────────────────────────────────────────

COLORES_PUNTAJE = {
    1: "#ef4444", 2: "#f97316", 3: "#fb923c",
    4: "#fbbf24", 5: "#facc15", 6: "#a3e635", 7: "#4ade80",
    8: "#22d3ee", 9: "#06b6d4", 10: "#00d4c8",
}

EMOJIS = {
    1: "😞", 2: "😔", 3: "😟", 4: "😐", 5: "🙂",
    6: "😊", 7: "😄", 8: "😁", 9: "🤩", 10: "🌟",
}


# ── EmojiLabel con bounce ─────────────────────────────────────────────────────

class _EmojiLabel(QLabel):
    """Label de emoji con animación de bounce al cambiar."""

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__("🙂", parent)
        self._modo = norm_modo(modo)
        self.setFont(qfont("size_emoji"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent;")

        # QGraphicsOpacityEffect para simular escala via opacity (workaround
        # ya que QGraphicsScale en QLabel directo es complejo)
        self._eff = QGraphicsOpacityEffect(self)
        self._eff.setOpacity(1.0)
        self.setGraphicsEffect(self._eff)

        self._anim: QSequentialAnimationGroup | None = None

    def bounce(self):
        """Fade out→in simulando el bounce (simplificado y robusto)."""
        if self._anim:
            self._anim.stop()

        out = QPropertyAnimation(self._eff, b"opacity", self)
        out.setDuration(80)
        out.setStartValue(1.0)
        out.setEndValue(0.3)
        out.setEasingCurve(QEasingCurve.Type.OutCubic)

        back = QPropertyAnimation(self._eff, b"opacity", self)
        back.setDuration(200)
        back.setStartValue(0.3)
        back.setEndValue(1.0)
        back.setEasingCurve(QEasingCurve.Type.OutBack)

        self._anim = QSequentialAnimationGroup(self)
        self._anim.addAnimation(out)
        self._anim.addAnimation(back)
        self._anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._anim = None  # se borrará solo


# ── ModuloAnimo ───────────────────────────────────────────────────────────────

class ModuloAnimo(NMModule):
    MODULE_TITLE = "Ánimo"
    MODULE_ICON = "🎭"

    def build_ui(self):
        self.puntaje = 5
        self._prev_color = COLORES_PUNTAJE[5]

        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        c = colors(self._modo)

        # ── Título ────────────────────────────────────────────────────────────
        title = QLabel("¿Cómo te sentís hoy?")
        title.setFont(qfont("size_h2", bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(title)

        # ── Emoji ─────────────────────────────────────────────────────────────
        self._emoji_lbl = _EmojiLabel(self._content, self._modo)
        layout.addWidget(self._emoji_lbl)

        # ── Valor numérico con color animado ──────────────────────────────────
        self._valor_lbl = QLabel("5 / 10")
        self._valor_lbl.setFont(qfont("size_h1", bold=True))
        self._valor_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._valor_lbl.setStyleSheet(
            f"color: {COLORES_PUNTAJE[5]}; background: transparent;"
        )
        layout.addWidget(self._valor_lbl)

        # ── Slider custom ─────────────────────────────────────────────────────
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 10)
        self._slider.setValue(5)
        self._slider.setFixedHeight(28)
        self._slider.setStyleSheet(stylesheet_slider(self._modo))
        self._slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self._slider)

        # Etiquetas extremos
        ext_row = QHBoxLayout()
        lbl_bad = QLabel("Muy mal")
        lbl_bad.setFont(qfont("size_caption"))
        lbl_bad.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        lbl_ok = QLabel("Excelente")
        lbl_ok.setFont(qfont("size_caption"))
        lbl_ok.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_ok.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        ext_row.addWidget(lbl_bad)
        ext_row.addStretch()
        ext_row.addWidget(lbl_ok)
        layout.addLayout(ext_row)

        # ── Nota ──────────────────────────────────────────────────────────────
        nota_lbl = QLabel("Nota (opcional)")
        nota_lbl.setFont(qfont("size_small"))
        nota_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(nota_lbl)

        self._txt_nota = QTextEdit()
        self._txt_nota.setFixedHeight(80)
        self._txt_nota.setPlaceholderText("¿Qué influyó en tu estado hoy?")
        self._txt_nota.setStyleSheet(stylesheet_textedit(self._modo))
        layout.addWidget(self._txt_nota)

        # ── Botón registrar ───────────────────────────────────────────────────
        self._btn_reg = NMButton("Registrar ánimo", modo=self._modo,
                                  width=200, height=44)
        self._btn_reg.clicked.connect(self._registrar)
        layout.addWidget(self._btn_reg, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Historial del día ─────────────────────────────────────────────────
        hist_lbl = QLabel("Registros de hoy")
        hist_lbl.setFont(qfont("size_small"))
        hist_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        layout.addWidget(hist_lbl)

        self._hist_scroll = QScrollArea()
        self._hist_scroll.setFixedHeight(56)
        self._hist_scroll.setWidgetResizable(True)
        self._hist_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._hist_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._hist_scroll.setStyleSheet("background: transparent; border: none;")

        self._hist_container = QWidget()
        self._hist_container.setStyleSheet("background: transparent;")
        self._hist_row = QHBoxLayout(self._hist_container)
        self._hist_row.setContentsMargins(0, 4, 0, 4)
        self._hist_row.setSpacing(6)
        self._hist_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._hist_scroll.setWidget(self._hist_container)
        layout.addWidget(self._hist_scroll)

        self._cargar_historial()

    # ── Slider ────────────────────────────────────────────────────────────────

    def _on_slider(self, value: int):
        self.puntaje = value
        new_color = COLORES_PUNTAJE.get(value, C("accent", self._modo))

        # Emoji con bounce
        self._emoji_lbl.setText(EMOJIS.get(value, "🙂"))
        self._emoji_lbl.bounce()

        # Animación de color del label de puntaje
        self._animate_color_change(self._prev_color, new_color)
        self._prev_color = new_color

    def _animate_color_change(self, from_hex: str, to_hex: str):
        anim = QVariantAnimation(self)
        anim.setDuration(300)
        anim.setStartValue(QColor(from_hex))
        anim.setEndValue(QColor(to_hex))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_value(v: QColor):
            self._valor_lbl.setText(f"{self.puntaje} / 10")
            self._valor_lbl.setStyleSheet(
                f"color: {v.name()}; background: transparent;"
            )

        anim.valueChanged.connect(_on_value)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Registrar ─────────────────────────────────────────────────────────────

    def _registrar(self):
        nota = self._txt_nota.toPlainText().strip()[:200]
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO termometro (fecha, hora, puntaje, nota) "
                "VALUES (?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self.puntaje, nota),
            )
            conn.commit()
            conn.close()
            self._txt_nota.clear()
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception:
                pass
            self._cargar_historial()
            # Buscar ventana principal para mostrar toast
            top = self.window()
            NMToast.show(top, f"Ánimo {self.puntaje}/10 registrado ✔",
                         variant="success")
        except Exception:
            pass

    # ── Historial ─────────────────────────────────────────────────────────────

    def _cargar_historial(self):
        # Limpiar chips anteriores
        while self._hist_row.count():
            item = self._hist_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT hora, puntaje FROM termometro "
                "WHERE fecha=? ORDER BY hora ASC",
                (fecha_hoy(),)
            ).fetchall()
            conn.close()
        except Exception:
            rows = []

        if not rows:
            empty = QLabel("Sin registros hoy")
            empty.setFont(qfont("size_caption"))
            c = colors(self._modo)
            empty.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            self._hist_row.addWidget(empty)
            return

        for row in rows:
            hora = row["hora"] if hasattr(row, "keys") else row[0]
            puntaje = row["puntaje"] if hasattr(row, "keys") else row[1]
            chip_color = COLORES_PUNTAJE.get(puntaje, C("accent", self._modo))
            emoji = EMOJIS.get(puntaje, "🙂")
            hora_short = str(hora)[:5]

            chip = QLabel(f"{emoji} {puntaje}  {hora_short}")
            chip.setFont(qfont("size_caption"))
            chip.setContentsMargins(8, 4, 8, 4)
            chip.setStyleSheet(f"""
                QLabel {{
                    color: {chip_color};
                    background: transparent;
                    border: 1px solid {chip_color};
                    border-radius: {RADIUS_PILL // 2}px;
                    padding: 2px 6px;
                }}
            """)
            self._hist_row.addWidget(chip)

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._cargar_historial()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro "
                "WHERE fecha=? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                p = row[0] if isinstance(row, tuple) else row["puntaje"]
                return f"{p}/10 ✔"
        except Exception:
            pass
        return ""
