"""
app/modules/timer_qt.py — Timer de enfoque v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > Timer):

  Header        eyebrow + nombre de actividad
  2-col main    LEFT: BIG NMFocusArc (MM:SS)
                       + chip "Sesión en curso" / "Lista para empezar"
                       + 3 NMPlayButton (refresh / play|pause / skip)
                       + chips de duración y modo

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
        NMButtonOutline,
        NMInput,
        NMToast,
        NMCard,
        NMPlayButton,
        NMFocusArc,
        NMRingPulse,
        NMEmptyState,
    )
    from shared.theme_qt import (
        qfont,
        v3c,
        V3_SP,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, leer_config, conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButtonOutline,
        NMInput,
        NMToast,
        NMCard,
        NMPlayButton,
        NMFocusArc,
        NMRingPulse,
    )
    from shared.theme_qt import (
        qfont,
        v3c,
        V3_SP,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.visual_qa import visual_qa_enabled

from shared.remote_config import t


def _duration_chip_label(secs: int) -> str:
    minutes = max(1, int(round(secs / 60)))
    return f"{minutes} min"


def _preset_from_row(row) -> tuple[str, int, str, str] | None:
    """Separa descripción y categoría del preset remoto."""
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
    categoria = ""
    if isinstance(payload, dict):
        secs = payload.get("duracion_seg") or payload.get("duration_sec") or payload.get("seconds")
        name = payload.get("name") or payload.get("nombre") or name
        description = (
            payload.get("description")
            or payload.get("descripcion")
            or ""
        )
        categoria = payload.get("categoria") or ""
    elif isinstance(payload, (int, float)):
        secs = payload

    try:
        secs = int(secs)
    except (TypeError, ValueError):
        return None
    if secs <= 0:
        return None
    return (
        str(name or f"{secs // 60} min"),
        secs,
        str(description or ""),
        str(categoria or ""),
    )


def _load_presets() -> list[tuple[str, int, str, str]]:
    """Actividades temporizadas asignadas por el profesional desde el Hub.

    NO hay presets locales por defecto: si el profesional no asignó ninguna se
    devuelve [] y el módulo muestra el estado vacío (el paciente solo puede
    iniciar actividades asignadas). En modo demostración (fixtures QA aislados)
    se devuelven ejemplos simulados que NO provienen de la DB ni se guardan.

    Regla clínica 2026-06: la interfaz operativa del Timer SOLO aparece con
    asignaciones `patient:<id>` (lo que el profesional configuró para ESTE
    paciente) o con fixtures QA aislados (visual_qa). Nunca con presets
    globales o predeterminados — el paciente no puede temporizar nada que
    su profesional no le haya asignado explícitamente.
    """
    from shared.visual_qa import visual_qa_enabled
    if visual_qa_enabled():
        return [
            ("Lectura", 25 * 60, "", "Foco"),
            ("Pausa activa", 5 * 60, "", "Descanso"),
            ("Trabajo profundo", 45 * 60, "", "Foco"),
        ]
    try:
        patient_id = leer_config("patient_id", "").strip()
    except Exception:
        patient_id = ""
    # Solo `patient:<id>`. Sin fallback a "global" ni a defaults locales.
    if not patient_id:
        return []
    scopes = [f"patient:{patient_id}"]

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
        self._current_categoria = ""
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
        # 2026-06: spacing 8→12, margins top 4→12 para dar respiro al ring
        # ampliado. El bloque operativo ahora llena la card sin huecos
        # verticales.
        cent_lay.setContentsMargins(0, 12, 0, 12)
        cent_lay.setSpacing(12)
        cent_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cent_lay = cent_lay  # para el helper QA _timer_force_empty

        # Stretch superior de balance: los dos addStretch del empty-state (abajo)
        # empujaban el bloque operativo (ring+controles+presets) hacia arriba,
        # dejando el tercio inferior vacío. Este stretch lo equilibra y centra el
        # contenido en modo operativo (el empty-state sigue centrado por los suyos).
        cent_lay.addStretch(1)

        # Canvas: bigring 230×230 (mockup canónico línea 207), con inner core
        # 200×200 + número central 46px font-display (mockup línea 861:
        # <div class="h-serif" id="tmNum" style="font-size:46px;">). El CSS base
        # pide 52px (.bigring .num), pero el Timer overridea inline a 46px.
        self._canvas = NMFocusArc(size=230, modo=self._modo, num_size=46)
        self._canvas.set_data(0.0, self._format_time(self._remaining_sec))
        cent_lay.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

        # State chip
        self._state_chip = QLabel(t("text.module.timer.ready_state", "Lista para empezar"))
        self._state_chip.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._state_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_chip.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
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

        # Input Actividad (envuelto en un container para poder ocultarlo
        # en el empty state). 2026-06: agrupado en _input_container.
        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # Nombre de la actividad asignada (solo-lectura). El paciente NO puede
        # crear ni escribir su propia actividad: refleja la actividad asignada
        # seleccionada (chip). Sin asignación → placeholder invitando a pedirla.
        # (2026-06: ancho fijo removido → el input se expande con el card
        # hasta un máximo razonable. Antes 320px rígido dejaba el campo
        # flotando en cards anchos sin aprovechar el espacio.)
        self._ent_actividad = NMInput(
            t(
                "text.module.timer.activity_placeholder",
                "Pedile a tu profesional que te asigne una actividad",
            ),
            modo=self._modo,
        )
        self._ent_actividad.setMinimumWidth(280)
        self._ent_actividad.setMaximumWidth(420)
        self._ent_actividad.setReadOnly(True)
        input_row.addWidget(self._ent_actividad)
        self._input_container = QWidget()
        self._input_container.setStyleSheet("background: transparent;")
        input_container_lay = QHBoxLayout(self._input_container)
        input_container_lay.setContentsMargins(0, 0, 0, 0)
        input_container_lay.addLayout(input_row)
        cent_lay.addWidget(self._input_container)
        self._input_container.hide()

        # Chips de duración + modo, separados como en el mockup. La actividad
        # seleccionada sigue escribiéndose en _ent_actividad para preservar la
        # persistencia existente.
        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        chips_row.setSpacing(6)
        self._duration_chip_btns: list[tuple[NMButtonOutline, int]] = []
        duration_seconds = sorted({secs for _, secs, *_ in self._presets})
        for secs in duration_seconds[:8]:
            btn = NMButtonOutline(_duration_chip_label(secs), modo=self._modo, toggleable=False, size="sm")
            btn.setFixedHeight(32)
            btn.setMinimumWidth(64)
            btn.clicked.connect(lambda _, s=secs: self._select_duration(s))
            chips_row.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._duration_chip_btns.append((btn, secs))
        self._duration_chip_container = QWidget()
        self._duration_chip_container.setStyleSheet("background: transparent;")
        duration_chip_container_lay = QHBoxLayout(self._duration_chip_container)
        duration_chip_container_lay.setContentsMargins(0, 0, 0, 0)
        duration_chip_container_lay.addLayout(chips_row)
        cent_lay.addWidget(self._duration_chip_container)

        mode_chips_row = QHBoxLayout()
        mode_chips_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        mode_chips_row.setSpacing(8)
        self._chip_btns: list[tuple[NMButtonOutline, int]] = []
        for label, secs, description, categoria in self._presets[:8]:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=False, size="sm")
            btn.setFixedHeight(34)
            btn.setMinimumWidth(max(76, min(150, 20 + len(label) * 9)))
            if description:
                btn.setToolTip(description)
            btn.clicked.connect(
                lambda _, n=label, s=secs, c=categoria: self._select_preset(n, s, c)
            )
            mode_chips_row.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            self._chip_btns.append((btn, secs))
        self._chip_container = QWidget()
        self._chip_container.setStyleSheet("background: transparent;")
        chip_container_lay = QHBoxLayout(self._chip_container)
        chip_container_lay.setContentsMargins(0, 0, 0, 0)
        chip_container_lay.addLayout(mode_chips_row)
        cent_lay.addWidget(self._chip_container)

        # 2026-06: siempre crear el _empty_state canónico (oculto por
        # defecto) para que el helper QA `_timer_force_empty` pueda
        # mostrarlo sin recrear todo el módulo. Reemplaza al _empty_lbl
        # QLabel improvisado — usa el widget NMEmptyState de la librería
        # compartida (icono en chip 64×64, título display-m serif, subtítulo
        # body, sin CTAs operativos).
        # (2026-06 round 3: compactado y centrado como un solo bloque
        # siguiendo el patrón del empty de Recordatorios — addStretch(1)
        # antes y después para centrarlo verticalmente en el espacio
        # disponible, sin stretch en el NMEmptyState para que tome su
        # sizeHint compacto.)
        self._empty_state = NMEmptyState(
            "timer",
            t("text.module.timer.empty_title", "Sin actividades asignadas"),
            t(
                "text.module.timer.empty_desc",
                "Pedile a tu profesional que te asigne una "
                "actividad temporizada para poder empezar.",
            ),
            parent=cent_container,
        )
        self._empty_state.hide()
        cent_lay.addWidget(self._empty_state)
        cent_lay.addStretch(1)

        if self._has_activity:
            # Seleccionar la actividad asignada inicial con su categoría.
            init_preset = next(
                (preset for preset in self._presets if preset[1] == self._total_sec),
                self._presets[0],
            )
            self._ent_actividad.setText(init_preset[0])
            self._current_categoria = init_preset[3]
            self._highlight_preset(self._total_sec, init_preset[0])
        else:
            # Sin actividad asignada (regla clínica 2026-06): el paciente ve
            # el mensaje de empty state, los controles quedan deshabilitados
            # y no hay presets/chips. El input muestra el placeholder
            # invitando a pedir una actividad.
            self._btn_play.setEnabled(False)
            self._btn_skip.setEnabled(False)
            self._state_chip.setText(t("text.module.timer.empty_title", "Sin actividades asignadas"))
            # Ocultar ring, controles, input y chips — solo el empty state.
            # (2026-06 round 3: setMaximumSize(0,0) en los items ocultos para
            # que NO contribuyan al sizeHint del layout — sin esto, el
            # NMEmptyState quedaba estirado en lugar de compacto.)
            for w in (self._canvas, self._state_chip,
                      self._input_container, self._duration_chip_container, self._chip_container):
                w.setMaximumSize(0, 0)
                w.hide()
            self._btn_reset.setEnabled(False)
            # Ocultar también la fila de controles (reset/play/skip) — buscar
            # el QHBoxLayout de controles por inspección.
            for i in range(cent_lay.count()):
                item = cent_lay.itemAt(i)
                if item and item.layout() and not item.widget():
                    ctrl_row_layout = item.layout()
                    for j in range(ctrl_row_layout.count()):
                        w = ctrl_row_layout.itemAt(j).widget()
                        if w:
                            w.setMaximumSize(0, 0)
                            w.hide()
                    break
            # Mostrar el empty state canónico (icono + título + subtítulo).
            self._empty_state.show()

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
        color = v3c("primary", self._modo).name()
        qc = QColor(color)
        bg = f"rgba({qc.red()},{qc.green()},{qc.blue()},24)"
        self._state_chip.setStyleSheet(
            f"color: {color}; background: {bg}; border-radius: 10px; "
            f"padding: 4px 12px; font-weight: 600;"
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

    def _select_duration(self, secs: int):
        if self._running:
            return
        preset = next((preset for preset in self._presets if preset[1] == secs), None)
        if preset is None:
            return
        name, seconds, _description, categoria = preset
        self._select_preset(name, seconds, categoria)

    def _select_preset(self, name: str, secs: int, categoria: str = ""):
        if self._running:
            return
        self._total_sec = secs
        self._remaining_sec = secs
        self._ent_actividad.setText(name)
        self._current_categoria = categoria
        self._highlight_preset(secs, name)
        self._update_canvas()

    def _highlight_preset(self, selected: int, selected_name: str = ""):
        for btn, secs in getattr(self, "_duration_chip_btns", []):
            btn.set_active(secs == selected)
        for btn, secs in self._chip_btns:
            if selected_name:
                btn.set_active(btn.text() == selected_name)
            else:
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
            state = t("text.module.timer.empty_title", "Sin actividades asignadas")
        elif self._running and not self._paused:
            state = t("text.module.timer.running_state", "Sesión en curso")
        elif self._paused:
            state = t("text.module.timer.paused_state", "En pausa")
        else:
            state = t("text.module.timer.ready_state", "Lista para empezar")

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
                    (
                        fecha_hoy(),
                        hora_actual(),
                        nombre,
                        self._current_categoria,
                        self._total_sec,
                        duracion,
                    ),
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
