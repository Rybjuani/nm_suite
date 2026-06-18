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
  _tick() (1s), _save_session() (INSERT INTO actividades_temporizador),
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
)

try:
    from shared.components import (
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
    from shared.components import (
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
    """Actividades temporizadas asignadas por el profesional desde el Hub.

    NO hay presets locales por defecto: si el profesional no asignó ninguna se
    devuelve [] y el módulo muestra el estado vacío (el paciente solo puede
    iniciar actividades asignadas). En modo demostración (clon del Hub) se
    devuelven ejemplos simulados que NO provienen de la DB ni se guardan.
    """
    from shared.visual_qa import visual_qa_enabled
    if visual_qa_enabled():
        return [("Lectura", 25 * 60, ""), ("Pausa activa", 5 * 60, ""),
                ("Trabajo profundo", 45 * 60, "")]
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
    # Sin asignaciones del profesional: no hay fallback local de presets.
    return []


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


# ── ModuloTimer v3 ──────────────────────────────────────────────────────────


class ModuloTimer(NMModule):
    MODULE_TITLE = "Timer"
    MODULE_ICON = "timer"

    def build_ui(self):
        # Estado preservado exacto
        self._running = False
        self._paused = False
        self._presets = _load_presets()
        # Solo se puede usar el temporizador si el profesional asignó al menos una
        # actividad (sin asignación → estado vacío, no se puede iniciar).
        self._has_activity = bool(self._presets)
        initial_secs = next(
            (secs for _, secs, *_ in self._presets if secs == 25 * 60),
            self._presets[0][1] if self._presets else 25 * 60,
        )
        self._total_sec = initial_secs
        self._remaining_sec = initial_secs
        self._timer_id: QTimer | None = None
        self._last_10s_blink = False

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
        # El paciente NO puede crear su propia actividad temporizada: las
        # actividades las asigna el profesional desde el Hub. El campo es
        # solo-lectura y muestra el placeholder invitando a pedir
        # actividades a su profesional.
        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Nombre de la actividad asignada (solo-lectura). El paciente NO puede
        # crear ni escribir su propia actividad: refleja la actividad asignada
        # seleccionada (chip). Sin asignación → placeholder invitando a pedirla.
        self._ent_actividad = NMInput("Pedile a tu profesional que te asigne una actividad", modo=self._modo)
        self._ent_actividad.setFixedWidth(320)
        self._ent_actividad.setReadOnly(True)
        input_row.addWidget(self._ent_actividad)
        cent_lay.addLayout(input_row)

        # Preset chips row: una actividad temporizada asignada por chip (nombre +
        # duración). No hay opción de minutos manuales (el paciente no crea).
        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        chips_row.setSpacing(6)
        chips_row.addStretch(1)
        self._chip_btns: list[tuple[NMButtonOutline, int]] = []
        for label, secs, description in self._presets[:8]:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=False, size="sm")
            btn.setFixedSize(76, 28)
            if description:
                btn.setToolTip(description)
            btn.clicked.connect(lambda _, n=label, s=secs: self._select_preset(n, s))
            chips_row.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._chip_btns.append((btn, secs))
        chips_row.addStretch(1)
        cent_lay.addLayout(chips_row)

        if self._has_activity:
            # Seleccionar la actividad asignada inicial (nombre + duración).
            init_name = next(
                (n for n, s, *_ in self._presets if s == self._total_sec),
                self._presets[0][0],
            )
            self._ent_actividad.setText(init_name)
            self._highlight_preset(self._total_sec)
        else:
            # Sin actividad asignada: no se puede iniciar el temporizador.
            self._btn_play.setEnabled(False)
            self._btn_skip.setEnabled(False)

        timer_card_lay.addWidget(cent_container, stretch=1)
        outer.addWidget(timer_card, stretch=1)
        self._timer_card = timer_card

        self._apply_text_styles()
        self._update_canvas()

        # Ring pulse — overlay de finalización de sesión
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)

    def _relayout_main_grid(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)


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
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        self.update()

    # ── Presets ──────────────────────────────────────────────────────────────

    def _select_preset(self, name: str, secs: int):
        if self._running:
            return
        self._total_sec = secs
        self._remaining_sec = secs
        self._ent_actividad.setText(name)
        self._highlight_preset(secs)
        self._update_canvas()

    def _highlight_preset(self, selected: int):
        for btn, secs in self._chip_btns:
            btn.set_active(secs == selected)

    # ── Display ──────────────────────────────────────────────────────────────

    def _format_time(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _update_canvas(self):
        # NMFocusArc usa progress 0-1 (cuánto LLEVA, no cuánto queda)
        if self._total_sec > 0:
            progress = (self._total_sec - self._remaining_sec) / self._total_sec
        else:
            progress = 0.0
        if not getattr(self, "_has_activity", True):
            state = "Sin actividad asignada"
        elif self._running and not self._paused:
            state = "Sesión en curso"
        elif self._paused:
            state = "Pausado"
        else:
            state = "Listo para empezar"

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
        # Sin actividad asignada no se puede iniciar (red de seguridad; el botón
        # ya está deshabilitado en ese estado).
        if not getattr(self, "_has_activity", True):
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

        nombre = self._ent_actividad.text().strip()
        top = self.window()
        if top and top.isMinimized():
            top.showNormal()
        if top:
            top.raise_()
            top.activateWindow()
        msg = f'Tiempo para "{nombre}" finalizado' if nombre else "Tiempo finalizado"
        NMToast.display(top, msg, variant="success", duration_ms=4000)

        QTimer.singleShot(
            4000, lambda: self._reset_after_finish() if not sip.isdeleted(self) else None
        )

    def _reset_after_finish(self):
        self._canvas.reset()
        self._remaining_sec = self._total_sec
        self._update_canvas()

    # ── DB (preservado exacto) ───────────────────────────────────────────────

    def _save_session(self, duracion: int):
        if visual_qa_enabled():
            if hasattr(self._btn_play, "play_success"):
                # NMPlayButton no tiene play_success, ignorar gracefully
                pass
            return
        # Solo se guardan sesiones de una actividad asignada con nombre real:
        # nunca con nombres automáticos ("Sin nombre", "25:00 timer").
        nombre = self._ent_actividad.text().strip()
        if not nombre:
            return
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
