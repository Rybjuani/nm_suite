"""respiracion.py — Módulo de respiración guiada (4-7-8)."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, get_gradient
from shared.components import draw_gradient_arc, draw_glow_arc, interpolate_color, BotonGradiente
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual


TECNICA = "4-7-8"
FASES = [
    ("Inhala ↑", 4),
    ("Mantén",   7),
    ("Exhala ↓", 8),
]
CICLO_TOTAL = sum(f[1] for f in FASES)  # 19 s por ciclo

PRESETS = [
    ("3 min", 3),
    ("5 min", 5),
    ("10 min", 10),
]

_CANVAS_SIZE = 260
_ARC_RADIUS  = 108
_ARC_WIDTH   = 10
_PAD         = _CANVAS_SIZE // 2 - _ARC_RADIUS


class ModuloRespiracion(NMModule):
    MODULE_TITLE = "Respiración"
    MODULE_ICON = "🌬️"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font

        self._running = False
        self._paused = False
        self._elapsed_ms = 0
        self._session_ms = 0      # cronómetro acumulado total
        self._duration_min = 5
        self._ciclos = 0
        self._timer_id = None
        self._phase_idx = 0
        self._phase_ms = 0

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True,
                     padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

        # ── Preset pills ──────────────────────────────────────
        pill_frame = ctk.CTkFrame(content, fg_color="transparent")
        pill_frame.pack(pady=(0, 16))

        self._pill_btns = []
        for label, mins in PRESETS:
            btn = ctk.CTkButton(
                pill_frame, text=label, width=76, height=34,
                corner_radius=17,
                fg_color=c["bg_surface"],
                hover_color=c["bg_elevated"],
                text_color=c["text_primary"],
                font=(font, TYPOGRAPHY["size_body"]),
                command=lambda m=mins: self._select_preset(m),
            )
            btn.pack(side="left", padx=4)
            self._pill_btns.append((btn, mins))
        self._highlight_preset(5)

        # ── Canvas circular ───────────────────────────────────
        self._canvas = ctk.CTkCanvas(
            content,
            width=_CANVAS_SIZE, height=_CANVAS_SIZE,
            bg=c["bg_primary"], highlightthickness=0,
        )
        self._canvas.pack(pady=(0, 4))
        self._draw_idle_circle()

        # Cronómetro de sesión
        self._session_lbl = ctk.CTkLabel(
            content, text="",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        )
        self._session_lbl.pack(pady=(0, 8))

        # ── Step-cards de las fases ───────────────────────────
        steps_frame = ctk.CTkFrame(content, fg_color="transparent")
        steps_frame.pack(fill="x", pady=(0, 16))
        steps_frame.columnconfigure((0, 1, 2), weight=1)

        self._step_cards = []
        step_data = [
            ("Inhala ↑", "4 s"),
            ("Mantén",   "7 s"),
            ("Exhala ↓", "8 s"),
        ]
        for i, (fase_label, secs_label) in enumerate(step_data):
            card = ctk.CTkFrame(
                steps_frame,
                fg_color=c["bg_surface"],
                corner_radius=LAYOUT["radius_card"],
                border_width=1,
                border_color=c.get("border_card", c["border"]),
            )
            card.grid(row=0, column=i, padx=4, sticky="ew")
            ctk.CTkLabel(
                card, text=fase_label,
                font=(font, TYPOGRAPHY["size_small"], "bold"),
                text_color=c["text_secondary"],
            ).pack(pady=(8, 2))
            ctk.CTkLabel(
                card, text=secs_label,
                font=(font, TYPOGRAPHY["size_caption"]),
                text_color=c["text_tertiary"],
            ).pack(pady=(0, 8))
            self._step_cards.append(card)

        # ── Controls ──────────────────────────────────────────
        ctrl_frame = ctk.CTkFrame(content, fg_color="transparent")
        ctrl_frame.pack()

        self._btn_start = ctk.CTkButton(
            ctrl_frame, text="Iniciar", width=100, height=40,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            corner_radius=LAYOUT["radius_button"],
            command=self._start,
        )
        self._btn_start.pack(side="left", padx=4)

        self._btn_pause = ctk.CTkButton(
            ctrl_frame, text="Pausa", width=100, height=40,
            fg_color=c["bg_surface"], hover_color=c["bg_elevated"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_button"],
            command=self._pause,
        )
        self._btn_pause.pack(side="left", padx=4)

        self._btn_stop = ctk.CTkButton(
            ctrl_frame, text="Detener", width=100, height=40,
            fg_color=c["error"], hover_color=c["error"],
            text_color="#ffffff",
            font=(font, TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_button"],
            command=self._stop,
        )
        self._btn_stop.pack(side="left", padx=4)

    # ── Step-cards highlight ──────────────────────────────────
    def _highlight_step(self, idx: int):
        c = self._c
        grad = get_gradient(self.modo)
        t = idx / max(len(FASES) - 1, 1)
        phase_color = interpolate_color(grad[0], grad[1], t)
        for i, card in enumerate(self._step_cards):
            if i == idx:
                card.configure(border_color=phase_color, border_width=2,
                               fg_color=c["bg_elevated"])
            else:
                card.configure(border_color=c["border"], border_width=1,
                               fg_color=c["bg_surface"])

    def _reset_step_cards(self):
        c = self._c
        for card in self._step_cards:
            card.configure(border_color=c["border"], border_width=1,
                           fg_color=c["bg_surface"])

    # ── Presets ──────────────────────────────────────────────
    def _select_preset(self, mins: int):
        if self._running:
            return
        self._duration_min = mins
        self._highlight_preset(mins)

    def _highlight_preset(self, selected: int):
        c = self._c
        for btn, mins in self._pill_btns:
            if mins == selected:
                btn.configure(fg_color=c["accent"], text_color=c["text_on_accent"])
            else:
                btn.configure(fg_color=c["bg_surface"], text_color=c["text_primary"])

    # ── Drawing ──────────────────────────────────────────────
    def _draw_idle_circle(self):
        c = self._c
        s = _CANVAS_SIZE
        cx = cy = s // 2
        r = _ARC_RADIUS
        self._canvas.delete("all")
        self._canvas.configure(bg=c["bg_primary"])
        # Track ring
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=c["progress_track"], width=_ARC_WIDTH,
        )
        # Center dot
        self._canvas.create_text(
            cx, cy, text="●",
            fill=c["accent"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h1"]),
        )

    def _draw_phase_arc(self, progress: float):
        c = self._c
        s = _CANVAS_SIZE
        cx = cy = s // 2
        r = _ARC_RADIUS
        grad = get_gradient(self.modo)
        extent = max(progress * 360, 2)

        self._canvas.delete("all")
        self._canvas.configure(bg=c["bg_primary"])

        # Track ring
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=c["progress_track"], width=_ARC_WIDTH,
        )

        # Glow (debe dibujarse antes del arco principal)
        draw_glow_arc(
            self._canvas, cx, cy, r,
            start_deg=90, extent_deg=-extent,
            glow_color=grad[0], bg_color=c["bg_primary"],
            tag="glow_arc",
        )

        # Gradiente teal → violeta
        draw_gradient_arc(
            self._canvas, cx, cy, r,
            width=_ARC_WIDTH,
            start_deg=90, extent_deg=-extent,
            color_a=grad[0], color_b=grad[1],
            tag="gradient_arc",
        )

        # Texto central: segundos restantes en la fase
        phase_name, phase_dur = FASES[self._phase_idx]
        secs_left = max(0, phase_dur - int(self._phase_ms / 1000))
        self._canvas.create_text(
            cx, cy - 10, text=str(secs_left),
            fill=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h1"] + 10, "bold"),
            tags="center_text",
        )
        self._canvas.create_text(
            cx, cy + 20, text=phase_name,
            fill=c["text_tertiary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
            tags="center_text",
        )

    # ── Controls ─────────────────────────────────────────────
    def _start(self):
        if self._running and self._paused:
            self._paused = False
            self._btn_pause.configure(text="Pausa")
            self._tick()
            return
        if self._running:
            return
        self._running = True
        self._paused = False
        self._elapsed_ms = 0
        self._session_ms = 0
        self._ciclos = 0
        self._phase_idx = 0
        self._phase_ms = 0
        self._btn_start.configure(text="Reanudar")
        self._tick()

    def _pause(self):
        if not self._running:
            return
        self._paused = True
        self._btn_pause.configure(text="Pausado")
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _stop(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        if self._running and self._ciclos > 0:
            self._save_session()
        self._running = False
        self._paused = False
        self._btn_start.configure(text="Iniciar")
        self._btn_pause.configure(text="Pausa")
        self._draw_idle_circle()
        self._session_lbl.configure(text="")
        self._reset_step_cards()

    # ── Timer loop ───────────────────────────────────────────
    def _tick(self):
        if not self._running or self._paused:
            return
        total_ms = self._duration_min * 60 * 1000
        interval = 100

        if self._elapsed_ms >= total_ms:
            self._finish()
            return

        phase_name, phase_dur = FASES[self._phase_idx]
        phase_dur_ms = phase_dur * 1000
        progress = self._phase_ms / phase_dur_ms
        self._draw_phase_arc(progress)
        self._highlight_step(self._phase_idx)

        # Cronómetro de sesión
        self._session_ms += interval
        s_total = self._session_ms // 1000
        self._session_lbl.configure(
            text=f"Sesión  {s_total // 60:02d}:{s_total % 60:02d}"
            f"   ·   Ciclos: {self._ciclos}"
        )

        self._phase_ms += interval
        self._elapsed_ms += interval

        if self._phase_ms >= phase_dur_ms:
            self._phase_ms = 0
            self._phase_idx += 1
            if self._phase_idx >= len(FASES):
                self._phase_idx = 0
                self._ciclos += 1

        self._timer_id = self.after(interval, self._tick)

    def _finish(self):
        self._running = False
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._save_session()
        c = self._c
        self._draw_idle_circle()
        self._reset_step_cards()
        self._session_lbl.configure(
            text=f"✓ Sesión completa · {self._ciclos} ciclos",
        )
        try:
            import winsound
            winsound.Beep(800, 300)
        except Exception:
            pass
        self._btn_start.configure(text="Iniciar")

    def _save_session(self):
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO respiracion (fecha, hora, tecnica, duracion_minutos, ciclos) "
                "VALUES (?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), TECNICA,
                 round(self._elapsed_ms / 60000, 1), self._ciclos),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def on_leave(self):
        self._stop()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM respiracion WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} sesión{'es' if n > 1 else ''} ✔"
        except Exception:
            pass
        return ""
