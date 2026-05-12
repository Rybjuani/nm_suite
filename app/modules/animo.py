"""animo.py — Módulo Ánimo: slider + emoji + nota + registrar."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.components import interpolate_color, BotonGradiente
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual

# Escala rojo→verde para 10 puntos — referencia: refs ZVpLC, LdbzV
COLORES_PUNTAJE = {
    1: "#ef4444", 2: "#f97316", 3: "#fb923c",
    4: "#fbbf24", 5: "#facc15", 6: "#a3e635", 7: "#4ade80",
    8: "#22d3ee", 9: "#06b6d4", 10: "#00d4c8",
}

EMOJIS = {1: "😞", 2: "😔", 3: "😟", 4: "😐", 5: "🙂",
          6: "😊", 7: "😄", 8: "😁", 9: "🤩", 10: "🌟"}


class ModuloAnimo(NMModule):
    MODULE_TITLE = "Ánimo"
    MODULE_ICON = "🎭"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self.puntaje = 5
        self._ok_after_id = None

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True,
                     padx=LAYOUT["padding_container"],
                     pady=LAYOUT["padding_container"])

        ctk.CTkLabel(
            content, text="¿Cómo te sentís hoy?",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(pady=(0, 16))

        # Emoji grande — usa token en vez de 72 hardcoded
        self._emoji_lbl = ctk.CTkLabel(
            content, text=EMOJIS[5],
            font=(font, TYPOGRAPHY["size_emoji"]),
        )
        self._emoji_lbl.pack(pady=(0, 6))

        self._valor_lbl = ctk.CTkLabel(
            content, text="5 / 10",
            font=(font, TYPOGRAPHY["size_h1"], "bold"),
            text_color=COLORES_PUNTAJE[5],
        )
        self._valor_lbl.pack(pady=(0, 14))

        self._slider = ctk.CTkSlider(
            content, from_=1, to=10, number_of_steps=9,
            width=320, height=22,
            progress_color=COLORES_PUNTAJE[5],
            button_color="#ffffff",
            button_hover_color="#e0e0e0",
            fg_color=c["progress_track"],
            command=self._on_slider,
        )
        self._slider.set(5)
        self._slider.pack(pady=(0, 4))

        # Pista gradiente rojo→verde (valores canónicos del tema)
        grad_canvas = ctk.CTkCanvas(
            content, width=320, height=6,
            bg=c["bg_primary"], highlightthickness=0,
        )
        grad_canvas.pack(pady=(0, 2))
        steps = 40
        w_step = 320 / steps
        for i in range(steps):
            t = i / (steps - 1)
            color = interpolate_color("#ef4444", "#00d4c8", t)
            x0 = int(i * w_step)
            x1 = int((i + 1) * w_step) + 1
            grad_canvas.create_rectangle(x0, 0, x1, 6, fill=color, outline="")

        extremos = ctk.CTkFrame(content, fg_color="transparent")
        extremos.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(
            extremos, text="Muy mal",
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"],
        ).pack(side="left")
        ctk.CTkLabel(
            extremos, text="Excelente",
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"],
        ).pack(side="right")

        ctk.CTkLabel(
            content, text="Nota (opcional)",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self._txt_nota = ctk.CTkTextbox(
            content, height=76, width=340,
            fg_color=c["bg_input"],
            text_color=c["text_primary"],
            border_color=c["border"],
            border_width=1,
            corner_radius=LAYOUT["radius_input"],
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._txt_nota.pack(pady=(0, 16))

        # Botón con gradiente — acción principal
        BotonGradiente(
            content, text="Registrar ánimo",
            command=self._registrar,
            modo=self.modo,
            width=200, height=44,
        ).pack(pady=(0, 10))

        # Burbuja de confirmación
        self._ok_bubble = ctk.CTkFrame(
            content, fg_color=c["success"],
            corner_radius=LAYOUT["radius_pill"],
        )
        self._ok_lbl = ctk.CTkLabel(
            self._ok_bubble, text="✓  Registrado",
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color="#ffffff",
        )
        self._ok_lbl.pack(padx=20, pady=8)

    def _on_slider(self, value):
        v = int(round(value))
        self.puntaje = v
        color = COLORES_PUNTAJE.get(v, COLORS.get(self.modo, COLORS["dark_hybrid"])["accent"])
        self._emoji_lbl.configure(text=EMOJIS.get(v, "🙂"))
        self._valor_lbl.configure(text=f"{v} / 10", text_color=color)
        self._slider.configure(progress_color=color)

    def _registrar(self):
        nota = self._txt_nota.get("1.0", "end").strip()[:200]
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO termometro (fecha, hora, puntaje, nota) VALUES (?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self.puntaje, nota),
            )
            conn.commit()
            conn.close()
            self._txt_nota.delete("1.0", "end")
            try:
                from shared.sync import sync_inmediato_background
                sync_inmediato_background()
            except Exception:
                pass
            self._mostrar_ok()
        except Exception:
            pass

    def _mostrar_ok(self):
        if self._ok_after_id:
            self.after_cancel(self._ok_after_id)
        self._ok_bubble.pack(pady=(0, 4))
        self._ok_after_id = self.after(2200, self._ocultar_ok)

    def _ocultar_ok(self):
        self._ok_after_id = None
        self._ok_bubble.pack_forget()

    def on_leave(self):
        if self._ok_after_id:
            self.after_cancel(self._ok_after_id)
            self._ok_after_id = None

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha=? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                return f"{row[0]}/10 ✔"
        except Exception:
            pass
        return ""
