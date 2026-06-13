"""
app/modules/timer_qt.py — Timer de enfoque v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Timer):

  Header        eyebrow + nombre de actividad
  2-col main    LEFT: BIG NMFocusArc (340, stroke 14, mono MM:SS)
                       + chip "Sesión en curso" / "Listo para empezar"
                       + 3 NMPlayButton (refresh / play|pause / skip)
                RIGHT rail: NMCard "DETALLES DE SESIÓN" con NMInput +
                            chips preset (5/10/25/45/custom)
                            NMCard "SESIONES DE HOY" con lista del día

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  PRESETS, _tick() (1s), _save_session() (INSERT INTO actividades_temporizador),
  _finish() con NMRingPulse + auto-restore window + toast,
  on_leave() guarda si elapsed ≥ 30s, get_card_status().
"""

import os
import sys
import logging
import json
import sqlite3
import math
import struct
import tempfile
import wave

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer
from PyQt6 import sip
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QScrollArea,
)

try:
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMButtonOutline,
        NMInput,
        NMToast,
        ThemeManager,
        NMCard,
        NMIcon,
        NMPlayButton,
        NMFocusArc,
        NMRingPulse,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        V3_RD,
        stylesheet_lineedit,
        stylesheet_scrollarea,
        PAD_CONTAINER,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled, timer_sessions
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule,
        NMButton,
        NMButtonOutline,
        NMInput,
        NMToast,
        NMCard,
        NMIcon,
        NMPlayButton,
        NMFocusArc,
        NMRingPulse,
    )
    from shared.theme_qt import (
        C,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        stylesheet_lineedit,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.visual_qa import visual_qa_enabled, timer_sessions

from shared.remote_config import t


# ── Presets (preservados) ────────────────────────────────────────────────────

PRESETS = [
    ("5 min", 5 * 60),
    ("10 min", 10 * 60),
    ("25 min", 25 * 60),
    ("45 min", 45 * 60),
]


def _parse_bool_config(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("0", "false", "no", "off"):
        return False
    if text in ("1", "true", "yes", "on"):
        return True
    return default


def _preset_from_row(row) -> tuple[str, int, str] | None:
    try:
        name = row["name"] if hasattr(row, "keys") else row[0]
        payload_raw = row["payload"] if hasattr(row, "keys") else row[1]
        payload = json.loads(payload_raw or "{}")
    except Exception:
        return None

    if isinstance(payload, dict) and payload.get("activo") is False:
        return None
    if isinstance(payload, dict) and payload.get("active") is False:
        return None

    secs = None
    description = ""
    if isinstance(payload, dict):
        secs = payload.get("duracion_seg") or payload.get("duration_sec") or payload.get("seconds")
        name = payload.get("name") or payload.get("nombre") or name
        description = (
            payload.get("description")
            or payload.get("descripcion")
            or payload.get("categoria")
            or ""
        )
    elif isinstance(payload, (int, float)):
        secs = payload

    try:
        secs = int(secs)
    except (TypeError, ValueError):
        return None
    if secs <= 0:
        return None
    return str(name or f"{secs // 60} min"), secs, str(description or "")


def _load_presets() -> list[tuple[str, int, str]]:
    try:
        patient_id = leer_config("patient_id", "").strip()
    except Exception:
        patient_id = ""
    scopes = []
    if patient_id:
        scopes.append(f"patient:{patient_id}")
    scopes.append("global")

    conn = None
    try:
        conn = obtener_conexion()
        for scope in scopes:
            rows = conn.execute(
                "SELECT name, payload FROM timer_presets_cache WHERE scope = ? ORDER BY id",
                (scope,),
            ).fetchall()
            presets = []
            for row in rows:
                preset = _preset_from_row(row)
                if preset:
                    presets.append(preset)
            if presets:
                return presets
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc).lower():
            _log.warning("No se pudieron cargar presets remotos del timer: %s", exc)
    except Exception as exc:
        _log.warning("No se pudieron cargar presets remotos del timer: %s", exc)
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    return [(name, secs, "") for name, secs in PRESETS]


def _manual_timer_enabled() -> bool:
    try:
        return _parse_bool_config(leer_config("perm_temporizador_manual", "1"))
    except Exception:
        return True


# ── Soft-alarm chime ─────────────────────────────────────────────────────────
# Generamos un chime corto (3 tonos con envelope ADSR) en memoria la primera vez
# que se necesita. Sin assets externos: el WAV se cachea en %TEMP% para reuso.
# Suficientemente suave para no asustar, pero perceptible al finalizar el timer.

_SOFT_ALARM_PATH = os.path.join(tempfile.gettempdir(), "nm_soft_alarm.wav")


def _ensure_soft_alarm_wav() -> str | None:
    """Genera (una sola vez) un WAV corto y suave. Devuelve la ruta al archivo."""
    try:
        if os.path.exists(_SOFT_ALARM_PATH) and os.path.getsize(_SOFT_ALARM_PATH) > 1024:
            return _SOFT_ALARM_PATH
    except Exception:
        pass
    try:
        sample_rate = 22050
        # Tres tonos suaves: A4, C#5, E5 — total ~1.2s
        notes = [(440.0, 0.30), (554.37, 0.30), (659.25, 0.40)]
        attack = 0.04
        release = 0.12
        frames = bytearray()
        for freq, dur in notes:
            n_samples = int(sample_rate * dur)
            for i in range(n_samples):
                t = i / sample_rate
                # ADSR: attack rápido, sustain, release suave
                if t < attack:
                    env = t / attack
                elif t > dur - release:
                    env = max(0.0, (dur - t) / release)
                else:
                    env = 1.0
                # Mezcla de seno + 2da armónica muy baja → timbre cálido
                sample = (
                    0.6 * math.sin(2 * math.pi * freq * t)
                    + 0.15 * math.sin(2 * math.pi * freq * 2 * t)
                )
                frames.extend(struct.pack("<h", int(sample * env * 0.55 * 32767)))
        with wave.open(_SOFT_ALARM_PATH, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(bytes(frames))
        return _SOFT_ALARM_PATH
    except Exception:
        _log.debug("No se pudo generar el WAV del chime suave")
        return None


def _play_soft_alarm() -> None:
    """Reproduce el chime suave (no-op si no es Windows o si falla)."""
    try:
        if sys.platform != "win32":
            return
        path = _ensure_soft_alarm_wav()
        if not path:
            return
        import winsound

        # SND_ASYNC: no bloquea el hilo de UI. SND_FILENAME: usa el archivo.
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        _log.debug("No se pudo reproducir el chime suave")


# ── _SessionsListCard ───────────────────────────────────────────────────────


class _SessionsListCard(NMCard):
    """Card v3 con lista de sesiones del día (tabla compacta)."""

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(
            V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"]
        )  # compact R5A: era xl/xl
        lay.setSpacing(V3_SP["sm"])  # compact R5A: era V3_SP["md"]=10
        self._eyebrow = QLabel("Sesiones de hoy")
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)
        # Patrón "Registros previos" de TCC (informe owner v1.0): los
        # registros acumulados scrollean DENTRO de la card — con 3+ sesiones
        # el contenido desbordaba el tope de la card y comprimía/pisaba el
        # temporizador principal.
        self._items_scroll = QScrollArea()
        self._items_scroll.setWidgetResizable(True)
        self._items_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._items_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._items_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        _items_body = QWidget()
        _items_body.setStyleSheet("background: transparent;")
        self._items_layout = QVBoxLayout(_items_body)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(V3_SP["xs"])
        self._items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._items_scroll.setWidget(_items_body)
        lay.addWidget(self._items_scroll, stretch=1)
        self._apply_sess_styles()

    def set_sessions(self, items: list[str]):
        """Cada item es 'nombre · MM:SS' (formato preservado por compat)."""
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            w = child.widget()
            if w:
                w.deleteLater()
        if not items:
            empty = QLabel(t("text.module.timer.empty_state", "Sin sesiones todavía hoy."))
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            self._items_layout.addWidget(empty)
            return
        for text in items:
            # Parse "nombre · MM:SS" → mostrar nombre + chip de duración
            parts = text.split("·")
            nombre = parts[0].strip() if parts else text
            duracion = parts[1].strip() if len(parts) > 1 else ""
            row = QHBoxLayout()
            row.setSpacing(V3_SP["sm"])
            icon = NMIcon("timer", size=16, color_key="teal", modo=self._modo)
            row.addWidget(icon)
            name_lbl = QLabel(nombre)
            name_lbl.setFont(qfont("size_small"))
            name_lbl.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
            row.addWidget(name_lbl, stretch=1)
            if duracion:
                dur_lbl = QLabel(duracion)
                dur_lbl.setFont(qfont_mono(10, bold=False))
                dur_lbl.setStyleSheet(
                    f"color: {v3c('teal', self._modo).name()}; background: transparent;"
                )
                row.addWidget(dur_lbl)
            wrap = QWidget()
            wrap.setLayout(row)
            self._items_layout.addWidget(wrap)

    def _apply_sess_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )

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
        self._presets = _load_presets()
        initial_secs = next(
            (secs for _, secs, *_ in self._presets if secs == 25 * 60),
            self._presets[0][1],
        )
        self._total_sec = initial_secs
        self._remaining_sec = initial_secs
        self._timer_id: QTimer | None = None
        self._custom_mode = False
        self._last_10s_blink = False
        self._manual_timer_enabled = _manual_timer_enabled()

        outer = QVBoxLayout(self._content)
        # Aire inferior md: con sm la card SESIONES DE HOY quedaba pegada al
        # borde de la ventana ("no respira").
        outer.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        outer.setSpacing(V3_SP["sm"])

        # 1. Eyebrow
        self._eyebrow = QLabel(t("text.module.timer.eyebrow", "Timer de enfoque"))
        self._eyebrow.setFont(eyebrow_font())

        # Card principal del temporizador, equivalente al panel 6 columnas del mockup.
        timer_card = NMCard(modo=self._modo, clickable=False, glow=False)
        timer_card.setMinimumHeight(300)
        timer_card_lay = QVBoxLayout(timer_card)
        timer_card_lay.setContentsMargins(V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["xs"])
        timer_card_lay.setSpacing(V3_SP["xs"])
        timer_card_lay.addWidget(self._eyebrow)
        self._eyebrow.hide()  # BL-07: título de módulo ahora en la titlebar

        # Centered container
        cent_container = QWidget()
        cent_container.setStyleSheet("background: transparent;")
        cent_lay = QVBoxLayout(cent_container)
        cent_lay.setContentsMargins(0, 4, 0, 4)
        cent_lay.setSpacing(8)
        cent_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Canvas: ring reducido a 180px. A 210 el bloque (ring+chip+controles+
        # input+presets) medía ~414px y a 960x600 la card sólo da ~360-390 → el
        # centrado desbordaba y RECORTABA el ring arriba y la fila OK abajo. 180
        # hace caber todo sin comprimir los controles (pedido owner).
        self._canvas = NMFocusArc(size=180, modo=self._modo)
        self._canvas.set_data(0.0, self._format_time(self._remaining_sec))
        cent_lay.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

        # State chip
        self._state_chip = QLabel("Listo para empezar")
        self._state_chip.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        self._state_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_chip.setContentsMargins(V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["xs"])
        cent_lay.addWidget(self._state_chip, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Controls
        ctrl_row = QHBoxLayout()
        ctrl_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ctrl_row.setSpacing(V3_SP["md"])

        self._btn_reset = NMPlayButton(icon_name="refresh", size="md", modo=self._modo)
        self._btn_reset.clicked.connect(self._stop)
        ctrl_row.addWidget(self._btn_reset)

        self._btn_play = NMPlayButton(icon_name="play", size="lg", modo=self._modo)
        self._btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_row.addWidget(self._btn_play)

        self._btn_skip = NMPlayButton(icon_name="skip", size="md", modo=self._modo)
        self._btn_skip.clicked.connect(self._finish)
        ctrl_row.addWidget(self._btn_skip)

        cent_lay.addLayout(ctrl_row)

        # Input Actividad
        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._ent_actividad = NMInput("¿En qué vas a trabajar?", modo=self._modo)
        self._ent_actividad.setFixedWidth(320)
        if visual_qa_enabled():
            self._ent_actividad.setText("Deep Work Session")
        input_row.addWidget(self._ent_actividad)
        cent_lay.addLayout(input_row)

        # Preset chips row (pill-row, up to 8 chips horizontales)
        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        chips_row.setSpacing(6)
        # stretch=1 explícito: addStretch() (factor 0) repartía el espacio
        # libre EN PARTES IGUALES con _custom_widget (Preferred) y a 1920px
        # los chips quedaban huérfanos a un lado y min/OK desparramados.
        chips_row.addStretch(1)
        self._chip_btns: list[tuple[NMButtonOutline, int]] = []
        for label, secs, description in self._presets[:8]:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=False, size="sm")
            btn.setFixedSize(76, 28)
            if description:
                btn.setToolTip(description)
            btn.clicked.connect(lambda _, s=secs: self._select_preset(s))
            chips_row.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._chip_btns.append((btn, secs))

        # Custom input inline
        self._custom_widget = QWidget()
        self._custom_widget.setVisible(self._manual_timer_enabled)
        self._custom_widget.setEnabled(self._manual_timer_enabled)
        # Altura fija = chips (28): sin esto el QWidget se estiraba vertical y el
        # campo "min" quedaba más alto que los presets/OK (desalineado).
        self._custom_widget.setFixedHeight(28)
        cw_row = QHBoxLayout(self._custom_widget)
        cw_row.setContentsMargins(0, 0, 0, 0)
        cw_row.setSpacing(4)
        cw_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._entry_custom = QLineEdit()
        self._entry_custom.setPlaceholderText("min")
        self._entry_custom.setFixedSize(64, 28)
        self._entry_custom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._entry_custom.setStyleSheet(self._pill_input_style())
        cw_row.addWidget(self._entry_custom)

        # Ancho 56 (era 36): a 36px el OK era mucho más angosto que cualquier
        # otro botón y rompía el target de clic (S11). Mantiene el alto 28 de la
        # fila compacta y queda alineado con el input "min" (64) contiguo.
        btn_ok = NMButton("OK", modo=self._modo, variant="gradient", size="sm", width=56)
        btn_ok.setFixedSize(56, 28)
        btn_ok.clicked.connect(self._apply_custom)
        cw_row.addWidget(btn_ok)

        chips_row.addSpacing(8)
        chips_row.addWidget(self._custom_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        chips_row.addStretch(1)
        cent_lay.addLayout(chips_row)

        self._highlight_preset(self._total_sec)

        timer_card_lay.addWidget(cent_container, stretch=1)
        outer.addWidget(timer_card, stretch=1)
        self._timer_card = timer_card

        # SESIONES DE HOY card
        self._sessions_card = _SessionsListCard(modo=self._modo)
        self._sessions_card.setMinimumHeight(88)
        self._sessions_card.setMaximumHeight(136)
        outer.addWidget(self._sessions_card)

        self._apply_text_styles()
        self._update_canvas()
        self._load_quick_history()

        # Ring pulse — overlay de finalización de sesión
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)

    def _relayout_main_grid(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _pill_input_style(self) -> str:
        """CSS para que el input de minutos custom tenga aspecto de pill (igual que los presets)."""
        border = C("border", self._modo)
        text = v3c("text", self._modo).name()
        ph = v3c("ink_secondary", self._modo).name()
        prim = v3c("primary", self._modo).name()
        return (
            f"QLineEdit {{ background: transparent; border: 1px solid {border}; "
            f"border-radius: 12px; color: {text}; padding: 0 12px; "
            f"font-size: {TYPOGRAPHY['size_body']}px; }}"
            f"QLineEdit::placeholder {{ color: {ph}; }}"
            f"QLineEdit:focus {{ border-color: {prim}; }}"
        )

    def _apply_text_styles(self):
        c = v3c("ink_secondary", self._modo).name()
        if hasattr(self, "_eyebrow"):
            self._eyebrow.setStyleSheet(
                f"color: {c}; background: transparent;"
            )
        self._apply_state_chip_style()

    def _apply_state_chip_style(self):
        is_active = self._running and not self._paused
        if is_active:
            color = v3c("teal", self._modo).name()
            # Soft background for active state (handoff §4.4)
            qc = QColor(color)
            bg = f"rgba({qc.red()},{qc.green()},{qc.blue()},28)"
            self._state_chip.setStyleSheet(
                f"color: {color}; background: {bg}; border-radius: 10px; "
                f"padding: 4px 14px; font-weight: 500;"
            )
        else:
            color = v3c("ink_secondary", self._modo).name()
            self._state_chip.setStyleSheet(
                f"color: {color}; background: transparent; padding: 4px 0;"
            )

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_canvas"):
            self._canvas._apply_theme(self._modo)
        if hasattr(self, "_entry_custom"):
            self._entry_custom.setStyleSheet(self._pill_input_style())
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
        self._custom_widget.setVisible(self._manual_timer_enabled)
        self._highlight_preset(secs)
        self._update_canvas()

    def _highlight_preset(self, selected: int):
        for btn, secs in self._chip_btns:
            btn.set_active(secs == selected and not self._custom_mode)

    def _apply_custom(self):
        if not self._manual_timer_enabled:
            return
        try:
            mins = int(self._entry_custom.text().strip())
            mins = max(1, min(120, mins))
            self._total_sec = mins * 60
            self._remaining_sec = self._total_sec
            self._custom_mode = True
            self._highlight_preset(self._total_sec)
            self._update_canvas()
        except ValueError:
            pass
        self._custom_widget.setVisible(self._manual_timer_enabled)

    # ── Display ──────────────────────────────────────────────────────────────

    def _format_time(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _update_canvas(self):
        # NMFocusArc usa progress 0-1 (cuánto LLEVA, no cuánto queda)
        if self._total_sec > 0:
            progress = (self._total_sec - self._remaining_sec) / self._total_sec
        else:
            progress = 0.0
        state = (
            "Sesión en curso"
            if (self._running and not self._paused)
            else ("Pausado" if self._paused else "Listo para empezar")
        )

        # Handoff §5.5: focus timer digits in Newsreader display
        time_str = self._format_time(self._remaining_sec)
        self._canvas.set_data(progress, time_str)

        # Force a cleaner font for the canvas text if supported
        try:
            from shared.theme_qt import v3_font

            self._canvas.setFont(v3_font(48, weight=600, serif=True))
        except Exception:
            pass

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
        if hasattr(self, "_ring_pulse"):
            self._ring_pulse.launch()
        # Alarma suave: chime breve que no asusta. No bloquea UI (winsound async).
        _play_soft_alarm()

        nombre = self._ent_actividad.text().strip() or "Sin nombre"
        top = self.window()
        if top and top.isMinimized():
            top.showNormal()
        if top:
            top.raise_()
            top.activateWindow()
        NMToast.display(
            top, f'Tiempo para "{nombre}" finalizado', variant="success", duration_ms=4000
        )

        QTimer.singleShot(
            4000, lambda: self._reset_after_finish() if not sip.isdeleted(self) else None
        )

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
        nombre = self._ent_actividad.text().strip() or (
            self._format_time(self._total_sec) + " timer"
        )
        try:
            with conexion() as conn:
                conn.execute(
                    "INSERT INTO actividades_temporizador "
                    "(fecha, hora, nombre, categoria, duracion_config, duracion_real) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (fecha_hoy(), hora_actual(), nombre, "Timer", self._total_sec, duracion),
                )
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
                (fecha_hoy(),),
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

    def on_enter(self):
        pass

    def on_leave(self):
        if self._running:
            elapsed = self._total_sec - self._remaining_sec
            self._stop()
            msg = (
                "Sesión guardada"
                if elapsed >= 30
                else "Timer detenido — menos de 30 s, no se guardó"
            )
            NMToast.display(self.window(), msg, variant="warning")

    def get_card_status(self) -> str:
        if visual_qa_enabled():
            return "2 sesiones"
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha=?", (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
