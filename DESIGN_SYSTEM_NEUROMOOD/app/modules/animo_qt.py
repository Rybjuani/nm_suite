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
import random
import logging

_log = logging.getLogger(__name__)

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
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMEmojiPicker, NMWaveChart, NMStreakBadge,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color, qcolor_to_rgba_css,
        get_gradient, stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMToast, ThemeManager,
        NMEmojiPicker, NMWaveChart, NMStreakBadge,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qcolor, qfont, interpolate_color, qcolor_to_rgba_css,
        get_gradient, stylesheet_textedit, stylesheet_scrollarea,
        PAD_CONTAINER, GAP_ELEMENTS, RADIUS_CARD, RADIUS_PILL,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual

# ── Tokens de negocio (preservados) ──────────────────────────────────────────

COLORES_PUNTAJE = {
    1: "#ef4444", 2: "#f97316", 3: "#fb923c",
    4: "#fbbf24", 5: "#facc15", 6: "#a3e635", 7: "#4ade80",
    8: "#22d3ee", 9: "#06b6d4", 10: "#14b8a6",
}

EMOJIS = {
    1: "😞", 2: "😔", 3: "😟", 4: "😐", 5: "🙂",
    6: "😊", 7: "😄", 8: "😁", 9: "🤩", 10: "🌟",
}


# ── EmojiLabel con bounce ─────────────────────────────────────────────────────

class _MoodParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -2)
        self.alpha = 255
        self.radius = random.uniform(3, 6)
        self.color = QColor(color)


class MoodCelebration(QWidget):
    """Overlay de particulas que se muestra brevemente sobre el modulo de animo."""

    def __init__(self, parent, modo="dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._particles = []
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.hide()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def launch(self, origin_x: int, origin_y: int):
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        c = colors(self._modo)
        colors_pool = [c["accent"], c["teal"], c["violet"], c["cyan"]]
        self._particles = [
            _MoodParticle(origin_x, origin_y, random.choice(colors_pool))
            for _ in range(28)
        ]
        self.raise_()
        self.show()
        self._timer.start()

    def _tick(self):
        alive = []
        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.3
            p.alpha = max(0, p.alpha - 6)
            if p.alpha > 0:
                alive.append(p)
        self._particles = alive
        self.update()
        if not alive:
            self._timer.stop()
            self.hide()

    def stop(self):
        self._timer.stop()
        self._particles = []
        self.hide()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for part in self._particles:
            col = QColor(part.color)
            col.setAlpha(part.alpha)
            painter.setBrush(col)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(part.x - part.radius),
                int(part.y - part.radius),
                int(part.radius * 2),
                int(part.radius * 2),
            )
        painter.end()

    def _apply_theme(self, modo):
        self._modo = norm_modo(modo)


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
    MODULE_ICON = "animo"

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

        # ── Selector emoji (chips) ────────────────────────────────────────────
        self._emoji_picker = NMEmojiPicker(self._modo)
        self._emoji_picker.set_score(5)
        self._emoji_picker.picked.connect(self._on_picker)
        layout.addWidget(self._emoji_picker, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Streak badge ──────────────────────────────────────────────────────
        self._streak = NMStreakBadge(self._load_streak(), self._modo)
        layout.addWidget(self._streak, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── Nota ──────────────────────────────────────────────────────────────
        nota_lbl = QLabel("Nota (opcional)")
        nota_lbl.setFont(qfont("size_body", bold=True))
        nota_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(nota_lbl)

        self._txt_nota = QTextEdit()
        self._txt_nota.setMinimumHeight(60)
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
        hist_lbl.setFont(qfont("size_body", bold=True))
        hist_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(hist_lbl)

        self._hist_scroll = QScrollArea()
        self._hist_scroll.setMinimumHeight(168)
        self._hist_scroll.setWidgetResizable(True)
        self._hist_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._hist_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._hist_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        self._hist_container = QWidget()
        self._hist_container.setStyleSheet("background: transparent;")
        self._hist_row = QHBoxLayout(self._hist_container)
        self._hist_row.setContentsMargins(0, 4, 0, 4)
        self._hist_row.setSpacing(6)
        self._hist_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._hist_scroll.setWidget(self._hist_container)
        layout.addWidget(self._hist_scroll)

        self._cargar_historial()

        # ── Gráfico de ánimo (dual-serie) ─────────────────────────────────────
        chart_lbl = QLabel("Ánimo de la semana")
        chart_lbl.setFont(qfont("size_body", bold=True))
        chart_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(chart_lbl)

        self._wave_chart = NMWaveChart(self._modo)
        layout.addWidget(self._wave_chart)

        self._cargar_grafico()
        self._celebration = MoodCelebration(self._content, self._modo)

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_txt_nota"):
            self._txt_nota.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_hist_scroll"):
            self._hist_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_emoji_picker"):
            self._emoji_picker._apply_theme(self._modo)
        if hasattr(self, "_streak"):
            self._streak._apply_theme(self._modo)
        if hasattr(self, "_wave_chart"):
            self._wave_chart._apply_theme(self._modo)
        self._cargar_historial()
        self.update()

    # ── Picker ────────────────────────────────────────────────────────────────

    def _on_picker(self, score: int):
        """Recibe el puntaje del NMEmojiPicker y actualiza el estado."""
        self._on_slider(score)

    def _load_streak(self) -> int:
        """Días consecutivos con registro de ánimo."""
        try:
            import datetime as dt
            con = obtener_conexion()
            rows = [r[0] for r in con.execute(
                "SELECT DISTINCT date(fecha) FROM termometro ORDER BY date(fecha) DESC LIMIT 30"
            ).fetchall()]
            today = dt.date.today()
            streak = 0
            for i, d_str in enumerate(rows):
                if str(today - dt.timedelta(days=i)) == d_str:
                    streak += 1
                else:
                    break
            return streak
        except Exception:
            _log.exception("Error calculando streak")
            return 0

    def _cargar_grafico(self):
        """Carga datos de las últimas 2 semanas en el NMWaveChart."""
        if not hasattr(self, "_wave_chart"):
            return
        try:
            import datetime as dt
            con = obtener_conexion()
            today = dt.date.today()
            current_data: list[float | None] = []
            prev_data:    list[float | None] = []
            for offset in range(6, -1, -1):
                day = today - dt.timedelta(days=offset)
                row = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?",
                    (str(day),)
                ).fetchone()
                current_data.append(float(row[0]) if row and row[0] is not None else None)
                day_prev = day - dt.timedelta(days=7)
                row2 = con.execute(
                    "SELECT AVG(puntaje) FROM termometro WHERE date(fecha)=?",
                    (str(day_prev),)
                ).fetchone()
                prev_data.append(float(row2[0]) if row2 and row2[0] is not None else None)
            self._wave_chart.set_data(current_data, prev_data)
        except Exception:
            _log.exception("Error cargando gráfico de ánimo")

    # ── Slider (reutilizado por picker) ───────────────────────────────────────

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
            self._cargar_grafico()
            if hasattr(self, "_streak"):
                self._streak.set_days(self._load_streak())
            if hasattr(self._btn_reg, "play_success"):
                self._btn_reg.play_success()
            # Buscar ventana principal para mostrar toast
            top = self.window()
            NMToast.display(top, f"Ánimo {self.puntaje}/10 registrado ✔",
                         variant="success")
            if self.puntaje >= 7 and hasattr(self, "_celebration"):
                origin = self._btn_reg.mapTo(
                    self,
                    self._btn_reg.rect().center(),
                )
                self._celebration.launch(origin.x(), origin.y())
        except Exception:
            _log.exception("Operation failed")

    # ── Historial ─────────────────────────────────────────────────────────────

    def _cargar_historial(self):
        # Limpiar chips anteriores
        while self._hist_row.count():
            item = self._hist_row.takeAt(0)
            w = item.widget()
            if w:
                self._hist_row.removeWidget(w)
                w.deleteLater()

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
            self._hist_row.addStretch()
            empty = QLabel("Todavia no hay registros de hoy.")
            empty.setFont(qfont("size_body"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumWidth(260)
            empty.setStyleSheet(f"color: {C('text_tertiary', self._modo)}; background: transparent;")
            self._hist_row.addWidget(empty)
            self._hist_row.addStretch()
            return

        for row in rows:
            hora = row["hora"] if hasattr(row, "keys") else row[0]
            puntaje = row["puntaje"] if hasattr(row, "keys") else row[1]
            chip_color = COLORES_PUNTAJE.get(puntaje, C("accent", self._modo))
            fill = QColor(chip_color)
            fill.setAlpha(26 if "dark" in self._modo else 20)
            emoji = EMOJIS.get(puntaje, "🙂")
            hora_short = str(hora)[:5]

            chip = QLabel(f"{emoji} {puntaje}  {hora_short}")
            chip.setFont(qfont("size_caption"))
            chip.setStyleSheet(f"""
                QLabel {{
                    color: {chip_color};
                    background: {qcolor_to_rgba_css(fill)};
                    border: 1px solid {chip_color};
                    border-radius: {RADIUS_PILL}px;
                    padding: 4px 10px;
                }}
            """)
            self._hist_row.addWidget(chip)

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def on_enter(self):
        self._cargar_historial()
        self._cargar_grafico()
        if hasattr(self, "_streak"):
            self._streak.set_days(self._load_streak())

    def on_leave(self):
        if hasattr(self, "_celebration"):
            self._celebration.stop()

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
                return f"{p}/10"
        except Exception:
            _log.exception("Operation failed")
        return ""
