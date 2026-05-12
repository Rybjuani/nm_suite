"""timer.py — Temporizador con presets y cuenta regresiva circular."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, get_gradient
from shared.components import draw_gradient_arc, draw_glow_arc
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual


PRESETS = [
    ("5 min", 5 * 60),
    ("10 min", 10 * 60),
    ("15 min", 15 * 60),
    ("20 min", 20 * 60),
]


class ModuloTimer(NMModule):
    MODULE_TITLE = "Temporizador"
    MODULE_ICON = "⏱️"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font

        self._running = False
        self._paused = False
        self._total_sec = 300  # default 5 min
        self._remaining_sec = 300
        self._timer_id = None
        self._custom_mode = False

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=32, pady=20)

        # Preset chips
        chip_frame = ctk.CTkFrame(content, fg_color="transparent")
        chip_frame.pack(pady=(0, 16))

        self._chip_btns = []
        for label, secs in PRESETS:
            btn = ctk.CTkButton(
                chip_frame, text=label, width=68, height=32,
                corner_radius=16,
                fg_color=c["bg_surface"],
                hover_color=c["bg_elevated"],
                text_color=c["text_primary"],
                font=(font, TYPOGRAPHY["size_small"]),
                command=lambda s=secs: self._select_preset(s),
            )
            btn.pack(side="left", padx=3)
            self._chip_btns.append((btn, secs))

        # Custom chip
        self._btn_custom = ctk.CTkButton(
            chip_frame, text="Otro", width=56, height=32,
            corner_radius=16,
            fg_color=c["bg_surface"],
            hover_color=c["bg_elevated"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_small"]),
            command=self._show_custom_input,
        )
        self._btn_custom.pack(side="left", padx=3)

        # Custom input (hidden by default)
        self._custom_frame = ctk.CTkFrame(content, fg_color="transparent")
        self._entry_custom = ctk.CTkEntry(
            self._custom_frame, width=80, height=34,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="min",
        )
        self._entry_custom.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            self._custom_frame, text="OK", width=40, height=34,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"),
            corner_radius=6,
            command=self._apply_custom,
        ).pack(side="left")

        self._highlight_preset(300)

        # Circular countdown display (canvas)
        canvas_size = 240
        self._canvas = ctk.CTkCanvas(
            content, width=canvas_size, height=canvas_size,
            bg=c["bg_primary"], highlightthickness=0,
        )
        self._canvas.pack(pady=(8, 12))
        self._canvas_size = canvas_size
        self._draw_timer()

        # Time label (large)
        self._time_lbl = ctk.CTkLabel(
            content, text=self._format_time(self._remaining_sec),
            font=(font, TYPOGRAPHY["size_h1"], "bold"),
            text_color=c["text_primary"],
        )
        self._time_lbl.pack(pady=(0, 16))

        # Controls
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
            fg_color=c["error"], hover_color="#c0392b",
            text_color="#ffffff",
            font=(font, TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_button"],
            command=self._stop,
        )
        self._btn_stop.pack(side="left", padx=4)

    # ── Presets ──────────────────────────────────────────────
    def _select_preset(self, secs: int):
        if self._running:
            return
        self._total_sec = secs
        self._remaining_sec = secs
        self._custom_mode = False
        self._custom_frame.pack_forget()
        self._highlight_preset(secs)
        self._update_display()

    def _highlight_preset(self, selected: int):
        c = self._c
        for btn, secs in self._chip_btns:
            if secs == selected and not self._custom_mode:
                btn.configure(fg_color=c["accent"], text_color=c["text_on_accent"])
            else:
                btn.configure(fg_color=c["bg_surface"], text_color=c["text_primary"])
        if self._custom_mode:
            self._btn_custom.configure(fg_color=c["accent"], text_color=c["text_on_accent"])
        else:
            self._btn_custom.configure(fg_color=c["bg_surface"], text_color=c["text_primary"])

    def _show_custom_input(self):
        if self._running:
            return
        self._custom_mode = True
        self._custom_frame.pack(pady=(0, 8))
        self._highlight_preset(-1)
        self._entry_custom.focus_set()

    def _apply_custom(self):
        try:
            mins = int(self._entry_custom.get().strip())
            if mins < 1:
                mins = 1
            if mins > 120:
                mins = 120
            self._total_sec = mins * 60
            self._remaining_sec = self._total_sec
            self._update_display()
        except ValueError:
            pass
        self._custom_frame.pack_forget()

    # ── Display ──────────────────────────────────────────────
    def _format_time(self, secs: int) -> str:
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    def _draw_timer(self):
        c = self._c
        s = self._canvas_size
        pad = 20
        r = s // 2 - pad
        cx = cy = s // 2
        self._canvas.delete("all")
        self._canvas.configure(bg=c["bg_primary"])

        # Background ring
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=c["progress_track"], width=10,
        )

        if self._total_sec > 0:
            progress = self._remaining_sec / self._total_sec
        else:
            progress = 1.0
        extent = max(progress * 360, 2)

        if self._remaining_sec > 0:
            grad = get_gradient(self.modo)
            draw_glow_arc(
                self._canvas, cx, cy, r,
                start_deg=90, extent_deg=-extent,
                glow_color=grad[0], bg_color=c["bg_primary"],
                tag="glow_arc",
            )
            draw_gradient_arc(
                self._canvas, cx, cy, r,
                width=10,
                start_deg=90, extent_deg=-extent,
                color_a=grad[0], color_b=grad[1],
                tag="gradient_arc",
            )
        else:
            # Arco success al completar
            self._canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=-360,
                outline=c["success"], width=10, style="arc",
            )

    def _update_display(self):
        self._time_lbl.configure(text=self._format_time(self._remaining_sec))
        self._draw_timer()

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
        self._remaining_sec = self._total_sec
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
        was_running = self._running
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._running = False
        self._paused = False
        # Record partial session if meaningful (>= 30 sec elapsed)
        elapsed = self._total_sec - self._remaining_sec
        if was_running and elapsed >= 30:
            self._save_session(elapsed)
        self._remaining_sec = self._total_sec
        self._btn_start.configure(text="Iniciar")
        self._btn_pause.configure(text="Pausa")
        self._update_display()

    # ── Timer loop ───────────────────────────────────────────
    def _tick(self):
        if not self._running or self._paused:
            return
        if self._remaining_sec <= 0:
            self._finish()
            return
        self._remaining_sec -= 1
        self._update_display()
        self._timer_id = self.after(1000, self._tick)

    def _finish(self):
        if not self._running:
            return
        self._running = False
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._save_session(self._total_sec)
        self._btn_start.configure(text="Iniciar")
        self._btn_pause.configure(text="Pausa")
        self._update_display()

        c = self._c
        self._time_lbl.configure(text="¡Tiempo! ✓", text_color=c["success"])
        self.after(3000, lambda: self._time_lbl.configure(
            text=self._format_time(self._total_sec), text_color=c["text_primary"]
        ))

        try:
            import winsound
            winsound.Beep(1000, 400)
            self.after(500, lambda: winsound.Beep(1000, 400))
        except Exception:
            pass

    def _save_session(self, duracion: int):
        nombre = self._format_time(self._total_sec) + " timer"
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
        except Exception:
            pass

    def on_leave(self):
        if self._running:
            self._stop()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM actividades_temporizador WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                return f"{row[0]} sesión{'es' if row[0] > 1 else ''} ✔"
        except Exception:
            pass
        return ""
