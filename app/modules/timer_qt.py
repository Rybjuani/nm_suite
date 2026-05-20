"""
app/modules/timer_qt.py — Timer de enfoque v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Timer):

  Header        eyebrow + nombre de actividad
  2-col main    LEFT: BIG NMFocusArc (340, stroke 14, mono MM:SS)
                       + chip "Sesión en curso" / "Lista para empezar"
                       + 3 NMPlayButton (refresh / play|pause / skip)
                RIGHT rail: NMCard "DETALLES DE SESIÓN" con NMInput +
                            chips preset (5/10/25/45/custom)
                            NMCard "SESIONES DE HOY" con lista del día

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  PRESETS, _tick() (1s), _save_session() (INSERT INTO actividades_temporizador),
  _finish() con winsound.Beep doble + auto-restore window + toast,
  on_leave() guarda si elapsed ≥ 30s, get_card_status().
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer
from PyQt6 import sip
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QFrame, QScrollArea,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMInput, NMToast, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMFocusArc,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_lineedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled, timer_sessions
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMInput, NMToast, ThemeManager,
        NMCard, NMIcon, NMPlayButton, NMFocusArc,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_lineedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled, timer_sessions


# ── Presets (preservados) ────────────────────────────────────────────────────

PRESETS = [
    ("5 min",  5 * 60),
    ("10 min", 10 * 60),
    ("25 min", 25 * 60),
    ("45 min", 45 * 60),
]


# ── _SessionsListCard ───────────────────────────────────────────────────────

class _SessionsListCard(NMCard):
    """Card v3 con lista de sesiones del día (tabla compacta)."""

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["md"])
        self._eyebrow = QLabel("SESIONES DE HOY")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)
        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(V3_SP["xs"])
        lay.addLayout(self._items_layout)
        lay.addStretch()
        self._apply_sess_styles()

    def set_sessions(self, items: list[str]):
        """Cada item es 'nombre · MM:SS' (formato preservado por compat)."""
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            w = child.widget()
            if w:
                w.deleteLater()
        if not items:
            empty = QLabel("Sin sesiones todavía hoy.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            self._items_layout.addWidget(empty)
            return
        for text in items:
            # Parse "nombre · MM:SS" → mostrar nombre + chip de duración
            parts = text.split("·")
            nombre = parts[0].strip() if parts else text
            duracion = parts[1].strip() if len(parts) > 1 else ""
            row = QHBoxLayout()
            row.setSpacing(V3_SP["sm"])
            icon = NMIcon("timer", size=16, color_key="teal",
                           modo=self._modo)
            row.addWidget(icon)
            name_lbl = QLabel(nombre)
            name_lbl.setFont(qfont("size_small"))
            name_lbl.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; "
                f"background: transparent;")
            row.addWidget(name_lbl, stretch=1)
            if duracion:
                dur_lbl = QLabel(duracion)
                dur_lbl.setFont(qfont_mono(10, bold=False))
                dur_lbl.setStyleSheet(
                    f"color: {v3c('teal', self._modo).name()}; "
                    f"background: transparent;")
                row.addWidget(dur_lbl)
            wrap = QWidget()
            wrap.setLayout(row)
            self._items_layout.addWidget(wrap)

    def _apply_sess_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_sess_styles()


# ── ModuloTimer v3 ──────────────────────────────────────────────────────────

class ModuloTimer(NMModule):
    MODULE_TITLE = "Timer"
    MODULE_ICON = "timer"

    def build_ui(self):
        # Estado preservado exacto
        self._running = False
        self._paused = False
        self._total_sec = 25 * 60
        self._remaining_sec = 25 * 60
        self._timer_id: QTimer | None = None
        self._custom_mode = False
        self._last_10s_blink = False

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(scroll)
        self._scroll = scroll

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        # 1. Eyebrow
        self._eyebrow = QLabel("TIMER DE ENFOQUE")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)

        # 2. Main 2-col
        main_row = QHBoxLayout()
        main_row.setSpacing(V3_SP["xl"])

        # ── LEFT col ─────────────────────────────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(V3_SP["lg"])
        left_col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # BIG ring (360)
        self._canvas = NMFocusArc(size=360, modo=self._modo)
        self._canvas.set_data(0.0, "25:00", "Lista para empezar")
        left_col.addWidget(self._canvas,
                            alignment=Qt.AlignmentFlag.AlignHCenter)

        # Chip "Sesión en curso" / estado
        self._state_chip = QLabel("Lista para empezar")
        self._state_chip.setFont(qfont("size_body",
                                        weight=TYPOGRAPHY["weight_semibold"]))
        self._state_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_chip.setContentsMargins(V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["xs"])
        left_col.addWidget(self._state_chip,
                            alignment=Qt.AlignmentFlag.AlignHCenter)

        # 3 NMPlayButton (refresh / play|pause / skip)
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ctrl_row.setSpacing(V3_SP["xl"])

        self._btn_reset = NMPlayButton(icon_name="refresh", size="md",
                                        modo=self._modo)
        self._btn_reset.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_reset)

        self._btn_play = NMPlayButton(icon_name="play", size="lg",
                                       modo=self._modo)
        self._btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_row.addWidget(self._btn_play)

        self._btn_skip = NMPlayButton(icon_name="skip", size="md",
                                       modo=self._modo)
        self._btn_skip.clicked.connect(self._finish)
        ctrl_row.addWidget(self._btn_skip)

        left_col.addLayout(ctrl_row)
        main_row.addLayout(left_col, stretch=2)

        # ── RIGHT rail ───────────────────────────────────────────────────────
        right_rail = QVBoxLayout()
        right_rail.setSpacing(V3_SP["xl"])
        right_rail.setAlignment(Qt.AlignmentFlag.AlignTop)

        # DETALLES DE SESIÓN card
        details_card = NMCard(modo=self._modo, clickable=False)
        details_lay = QVBoxLayout(details_card)
        details_lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"],
                                        V3_SP["xl"], V3_SP["xl"])
        details_lay.setSpacing(V3_SP["md"])
        self._details_eyebrow = QLabel("DETALLES DE SESIÓN")
        self._details_eyebrow.setFont(qfont("size_caption_xs",
                                             weight=TYPOGRAPHY["weight_semibold"]))
        details_lay.addWidget(self._details_eyebrow)

        self._activity_lbl = QLabel("Actividad")
        self._activity_lbl.setFont(qfont("size_small"))
        details_lay.addWidget(self._activity_lbl)

        self._ent_actividad = NMInput("¿En qué vas a trabajar?",
                                       modo=self._modo)
        if visual_qa_enabled():
            self._ent_actividad.setText("Deep Work Session")
        details_lay.addWidget(self._ent_actividad)

        self._duration_lbl = QLabel("Duración")
        self._duration_lbl.setFont(qfont("size_small"))
        self._duration_lbl.setContentsMargins(0, V3_SP["sm"], 0, 0)
        details_lay.addWidget(self._duration_lbl)

        # Preset chips (NMButtonOutline toggleables)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(V3_SP["sm"])
        self._chip_btns: list[tuple[NMButtonOutline, int]] = []
        for label, secs in PRESETS:
            btn = NMButtonOutline(label, modo=self._modo,
                                   toggleable=False, size="sm")
            btn.setFixedSize(76, 32)
            btn.clicked.connect(lambda _, s=secs: self._select_preset(s))
            chips_row.addWidget(btn)
            self._chip_btns.append((btn, secs))
        details_lay.addLayout(chips_row)
        self._highlight_preset(25 * 60)

        # Custom input (hidden by default)
        self._custom_widget = QWidget()
        self._custom_widget.setVisible(False)
        cw_row = QHBoxLayout(self._custom_widget)
        cw_row.setContentsMargins(0, V3_SP["sm"], 0, 0)
        cw_row.setSpacing(V3_SP["sm"])
        self._entry_custom = QLineEdit()
        self._entry_custom.setPlaceholderText("minutos")
        self._entry_custom.setFixedSize(90, 32)
        self._entry_custom.setStyleSheet(stylesheet_lineedit(self._modo))
        cw_row.addWidget(self._entry_custom)
        btn_ok = NMButton("OK", modo=self._modo, variant="secondary",
                          size="sm", width=54)
        btn_ok.clicked.connect(self._apply_custom)
        cw_row.addWidget(btn_ok)
        details_lay.addWidget(self._custom_widget)
        right_rail.addWidget(details_card)
        self._details_card = details_card

        # SESIONES DE HOY card
        self._sessions_card = _SessionsListCard(modo=self._modo)
        right_rail.addWidget(self._sessions_card)

        right_rail.addStretch()
        main_row.addLayout(right_rail, stretch=1)
        lay.addLayout(main_row)

        self._apply_text_styles()
        self._update_canvas()
        self._load_quick_history()

    def _apply_text_styles(self):
        c = v3c("text3", self._modo).name()
        for lbl in (self._eyebrow, self._details_eyebrow):
            lbl.setStyleSheet(f"color: {c}; background: transparent;")
        for lbl in (self._activity_lbl, self._duration_lbl):
            lbl.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; "
                f"background: transparent;")
        self._apply_state_chip_style()

    def _apply_state_chip_style(self):
        is_active = self._running and not self._paused
        if is_active:
            color = v3c("teal", self._modo).name()
            qc = QColor(color)
            bg = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
            self._state_chip.setStyleSheet(
                f"color: {color}; background: {bg}; border-radius: 12px;")
        else:
            color = v3c("text3", self._modo).name()
            self._state_chip.setStyleSheet(
                f"color: {color}; background: transparent;")

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_canvas"):
            self._canvas._apply_theme(self._modo)
        if hasattr(self, "_entry_custom"):
            self._entry_custom.setStyleSheet(stylesheet_lineedit(self._modo))
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        self.update()

    # ── Presets ──────────────────────────────────────────────────────────────

    def _select_preset(self, secs: int):
        if self._running:
            return
        self._total_sec = secs
        self._remaining_sec = secs
        self._custom_mode = False
        self._custom_widget.setVisible(False)
        self._highlight_preset(secs)
        self._update_canvas()

    def _highlight_preset(self, selected: int):
        for btn, secs in self._chip_btns:
            btn.set_active(secs == selected and not self._custom_mode)

    def _apply_custom(self):
        try:
            mins = int(self._entry_custom.text().strip())
            mins = max(1, min(120, mins))
            self._total_sec = mins * 60
            self._remaining_sec = self._total_sec
            self._update_canvas()
        except ValueError:
            pass
        self._custom_widget.setVisible(False)

    # ── Display ──────────────────────────────────────────────────────────────

    def _format_time(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _update_canvas(self):
        # NMFocusArc usa progress 0-1 (cuánto LLEVA, no cuánto queda)
        if self._total_sec > 0:
            progress = (self._total_sec - self._remaining_sec) / self._total_sec
        else:
            progress = 0.0
        state = "Sesión en curso" if (self._running and not self._paused) \
            else ("Pausado" if self._paused
                  else "Lista para empezar")
        self._canvas.set_data(progress,
                               self._format_time(self._remaining_sec),
                               state)
        self._state_chip.setText(state)
        self._apply_state_chip_style()

    # ── Controles ────────────────────────────────────────────────────────────

    def _toggle_play_pause(self):
        """Toggle único: play / pause / resume."""
        if not self._running:
            self._start()
        elif self._paused:
            # resume
            self._paused = False
            self._btn_play.set_icon("pause")
            self._canvas.start_pulse()
            self._tick()
            self._update_canvas()
        else:
            # pause
            self._pause()

    def _start(self):
        if self._running and not self._paused:
            return
        self._running = True
        self._paused = False
        self._remaining_sec = self._total_sec
        self._last_10s_blink = False
        self._btn_play.set_icon("pause")
        self._canvas.reset()
        self._canvas.start_pulse()
        self._tick()
        self._update_canvas()

    def _pause(self):
        if not self._running:
            return
        self._paused = True
        self._btn_play.set_icon("play")
        self._canvas.stop_pulse()
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._update_canvas()

    def _stop(self):
        was_running = self._running
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._canvas.stop_pulse()
        self._canvas.stop_blink()
        elapsed = self._total_sec - self._remaining_sec
        if was_running and elapsed >= 30:
            self._save_session(elapsed)
        self._running = False
        self._paused = False
        self._remaining_sec = self._total_sec
        self._btn_play.set_icon("play")
        self._canvas.reset()
        self._update_canvas()
        self._load_quick_history()

    # ── Tick (1s interval — preservado) ─────────────────────────────────────

    def _tick(self):
        if not self._running or self._paused:
            return
        if self._remaining_sec <= 0:
            self._finish()
            return

        self._remaining_sec -= 1
        self._update_canvas()

        if self._remaining_sec <= 10 and not self._last_10s_blink:
            self._last_10s_blink = True
            self._canvas.start_blink()

        if self._timer_id is None:
            self._timer_id = QTimer(self)
            self._timer_id.timeout.connect(self._tick)
        self._timer_id.start(1000)

    def _finish(self):
        self._running = False
        if self._timer_id:
            self._timer_id.stop()
            self._timer_id = None
        self._save_session(self._total_sec)
        self._btn_play.set_icon("play")
        self._canvas.show_finish()
        try:
            import winsound
            winsound.Beep(1000, 400)
            QTimer.singleShot(500, lambda: winsound.Beep(1000, 400))
        except Exception:
            _log.exception("Operation failed")

        nombre = self._ent_actividad.text().strip() or "Sin nombre"
        top = self.window()
        if top and top.isMinimized():
            top.showNormal()
        if top:
            top.raise_()
            top.activateWindow()
        NMToast.display(top,
                         f"Tiempo para \"{nombre}\" finalizado",
                         variant="success", duration_ms=4000)

        QTimer.singleShot(4000, lambda: self._reset_after_finish()
                          if not sip.isdeleted(self) else None)

    def _reset_after_finish(self):
        self._canvas.reset()
        self._remaining_sec = self._total_sec
        self._update_canvas()
        self._load_quick_history()

    # ── DB (preservado exacto) ───────────────────────────────────────────────

    def _save_session(self, duracion: int):
        if visual_qa_enabled():
            if hasattr(self._btn_play, "play_success"):
                # NMPlayButton no tiene play_success, ignorar gracefully
                pass
            return
        nombre = self._ent_actividad.text().strip() or \
            (self._format_time(self._total_sec) + " timer")
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO actividades_temporizador "
                "(fecha, hora, nombre, categoria, duracion_config, duracion_real) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), nombre, "Timer",
                 self._total_sec, duracion),
            )
            conn.commit()
            conn.close()
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception:
                pass
        except Exception:
            _log.exception("Operation failed")

    def _load_quick_history(self):
        if visual_qa_enabled():
            self._sessions_card.set_sessions(timer_sessions())
            return
        sessions = []
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, duracion_real FROM actividades_temporizador "
                "WHERE fecha = ? ORDER BY rowid DESC LIMIT 6",
                (fecha_hoy(),)
            ).fetchall()
            conn.close()
            for row in rows:
                if hasattr(row, "keys"):
                    name = row["nombre"]
                    dr = row["duracion_real"]
                else:
                    name = row[0]
                    dr = row[1]
                mins = dr // 60
                secs = dr % 60
                sessions.append(f"{name} · {mins:02d}:{secs:02d}")
            self._sessions_card.set_sessions(sessions)
        except Exception:
            _log.exception("Operation failed")

    def on_leave(self):
        if self._running:
            elapsed = self._total_sec - self._remaining_sec
            self._stop()
            msg = ("Sesión guardada" if elapsed >= 30
                   else "Timer detenido — menos de 30 s, no se guardó")
            NMToast.display(self.window(), msg, variant="warning")

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "2 sesiones"
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
