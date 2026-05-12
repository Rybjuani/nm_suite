"""animo.py — Módulo Ánimo: slider + emoji + nota + registrar."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY
from shared.components import interpolate_color
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual


EMOJIS = {1: "😞", 2: "😔", 3: "😟", 4: "😐", 5: "🙂",
           6: "😊", 7: "😄", 8: "😁", 9: "🤩", 10: "🌟"}

COLORES_PUNTAJE = {
    1: "#E96134", 2: "#EC762C", 3: "#EF8C24",
    4: "#F0A500", 5: "#EAB800", 6: "#C0C030", 7: "#7CBD50",
    8: "#3AAE70", 9: "#2BBF7A", 10: "#22D47E",
}


class ModuloAnimo(NMModule):
    MODULE_TITLE = "Ánimo"
    MODULE_ICON = "🎭"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self.puntaje = 5
        self._ok_after_id = None

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(
            content, text="¿Cómo te sentís?",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(pady=(0, 20))

        self._emoji_lbl = ctk.CTkLabel(
            content, text=EMOJIS[5],
            font=(font, 72),
        )
        self._emoji_lbl.pack(pady=(0, 8))

        self._valor_lbl = ctk.CTkLabel(
            content, text="5 / 10",
            font=(font, TYPOGRAPHY["size_h1"], "bold"),
            text_color=COLORES_PUNTAJE[5],
        )
        self._valor_lbl.pack(pady=(0, 16))

        self._slider = ctk.CTkSlider(
            content, from_=1, to=10, number_of_steps=9,
            width=320, height=22,
            progress_color=COLORES_PUNTAJE[5],
            button_color=c["text_primary"],
            fg_color=c["bg_surface"],
            command=self._on_slider,
        )
        self._slider.set(5)
        self._slider.pack(pady=(0, 6))

        # Pista de gradiente rojo→verde debajo del slider
        grad_canvas = ctk.CTkCanvas(
            content, width=320, height=8,
            bg=c["bg_primary"], highlightthickness=0,
        )
        grad_canvas.pack(pady=(0, 4))
        steps = 40
        w_step = 320 / steps
        for i in range(steps):
            t = i / (steps - 1)
            color = interpolate_color("#E96134", "#22D47E", t)
            x0 = int(i * w_step)
            x1 = int((i + 1) * w_step) + 1
            grad_canvas.create_rectangle(x0, 0, x1, 8, fill=color, outline="")

        # Etiquetas extremos del slider
        extremos = ctk.CTkFrame(content, fg_color="transparent")
        extremos.pack(fill="x", pady=(0, 20))
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
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self._txt_nota = ctk.CTkTextbox(
            content, height=80, width=340,
            fg_color=c["bg_input"],
            text_color=c["text_primary"],
            border_color=c["border"],
            border_width=1,
            corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._txt_nota.pack(pady=(0, 20))

        btn = ctk.CTkButton(
            content, text="Registrar",
            fg_color=c["accent"],
            hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            height=42, width=180,
            corner_radius=8,
            command=self._registrar,
        )
        btn.pack(pady=(0, 12))

        # Burbuja de confirmación (oculta por defecto)
        self._ok_bubble = ctk.CTkFrame(
            content,
            fg_color=c["success"],
            corner_radius=20,
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
        self._emoji_lbl.configure(text=EMOJIS.get(v, "🙂"))
        self._valor_lbl.configure(text=f"{v} / 10", text_color=COLORES_PUNTAJE.get(v, "#1EC8D4"))
        self._slider.configure(progress_color=COLORES_PUNTAJE.get(v, "#1EC8D4"))

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
        if hasattr(self, "_ok_after_id") and self._ok_after_id:
            self.after_cancel(self._ok_after_id)
        self._ok_bubble.pack(pady=(0, 4))
        self._ok_after_id = self.after(2200, self._ocultar_ok)

    def _ocultar_ok(self):
        self._ok_after_id = None
        self._ok_bubble.pack_forget()

    def on_leave(self):
        if hasattr(self, "_ok_after_id") and self._ok_after_id:
            self.after_cancel(self._ok_after_id)
            self._ok_after_id = None

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                return f"{row[0]}/10 ✔"
        except Exception:
            pass
        return ""
