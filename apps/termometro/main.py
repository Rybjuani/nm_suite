import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    AreaTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual, fecha_legible, color_por_puntaje


class TermometroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()

        self.modo = "dark"
        self.puntaje_actual = 5
        self._nota_temp = ""

        self.title("NeuroMood · Termómetro Emocional")
        w, h = 960, 720
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(900, 680)
        self.configure(fg_color=COLORS[self.modo]["bg_primary"])

        try:
            self.iconbitmap(obtener_icono_solido())
        except Exception:
            pass

        self._centrar_ventana()
        self._construir_ui()

    def _centrar_ventana(self):
        self._prev_state = "zoomed"
        self.after(50, lambda: self.state("zoomed"))
        self.bind("<Configure>", self._on_configure_centrar)

    def _on_configure_centrar(self, event):
        if event.widget is not self:
            return
        estado = self.state()
        if self._prev_state == "zoomed" and estado == "normal":
            self.after(20, self._recentrar)
        self._prev_state = estado

    def _recentrar(self):
        if self.state() != "normal":
            return
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _construir_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        self.configure(fg_color=colores["bg_primary"])

        self.header = HeaderFrame(
            self,
            titulo="Termómetro Emocional",
            subtitulo="Registrá tu estado de ánimo diario",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        columna_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        columna_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        columna_der = ctk.CTkFrame(contenido, fg_color="transparent")
        columna_der.pack(side="right", fill="both", expand=True, padx=(12, 0))

        self._construir_termometro(columna_izq)
        self._construir_registro(columna_izq)
        self._construir_historial(columna_der)

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

    def _construir_termometro(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="¿Cómo te sentís hoy?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8))

        self.EMOJIS = ["😭", "😢", "😞", "😔", "😕", "😐", "🙂", "😊", "😄", "😁", "🤩"]

        emoji_frame = ctk.CTkFrame(card, fg_color="transparent")
        emoji_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=12)

        self.emoji_labels = []
        for i, emoji in enumerate(self.EMOJIS):
            lbl = ctk.CTkLabel(
                emoji_frame, text=emoji,
                font=(TYPOGRAPHY["font_family"], 20),
                width=36, height=36
            )
            lbl.pack(side="left", expand=True)
            self.emoji_labels.append(lbl)

        self._actualizar_emojis()

        self.lbl_puntaje = ctk.CTkLabel(
            card, text="5 — Regular",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=color_por_puntaje(5, self.modo)
        )
        self.lbl_puntaje.pack(pady=(4, 8))

        slider_frame = ctk.CTkFrame(card, fg_color="transparent")
        slider_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        ctk.CTkLabel(
            slider_frame, text="0", font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(side="left")

        ctk.CTkLabel(
            slider_frame, text="10", font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(side="right")

        self.slider = ctk.CTkSlider(
            slider_frame, from_=0, to=10, number_of_steps=10,
            progress_color=colores["accent"],
            button_color=colores["accent"],
            button_hover_color=colores["accent_hover"],
            fg_color=colores["progress_track"],
            command=self._on_slider_change
        )
        self.slider.set(5)
        self.slider.pack(side="left", fill="x", expand=True, padx=8)

    def _construir_registro(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Nota (opcional)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        self.txt_nota = AreaTexto(card, modo=self.modo, height=60)
        self.txt_nota.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))
        if self._nota_temp:
            self.txt_nota.insert("1.0", self._nota_temp)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        BotonPrimario(
            btn_frame, text="Registrar estado", modo=self.modo,
            command=self._registrar
        ).pack(side="left")

    def _construir_historial(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Historial de registros",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        self.frame_registros = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_registros.pack(fill="both", expand=True,
                                   padx=LAYOUT["padding_card"],
                                   pady=(0, LAYOUT["padding_card"]))

        self._actualizar_historial()
        self._verificar_alerta()

    _EMOJI_GRAD = [
        "#E74C3C", "#E96134", "#EC762C", "#EF8C24", "#F0A500",
        "#EAB800", "#C0C030", "#7CBD50", "#3AAE70", "#2BBF7A", "#22D47E",
    ]

    def _actualizar_emojis(self):
        colores = COLORS[self.modo]
        for i, lbl in enumerate(self.emoji_labels):
            if i == self.puntaje_actual:
                lbl.configure(
                    font=(TYPOGRAPHY["font_family"], 36),
                    text_color=self._EMOJI_GRAD[i]
                )
            else:
                lbl.configure(
                    font=(TYPOGRAPHY["font_family"], 20),
                    text_color=colores["text_tertiary"]
                )

    def _on_slider_change(self, valor):
        self.puntaje_actual = max(0, int(round(valor)))
        etiqueta = self._etiqueta_puntaje(self.puntaje_actual)
        color = color_por_puntaje(self.puntaje_actual, self.modo)
        self.lbl_puntaje.configure(
            text=f"{self.puntaje_actual} — {etiqueta}",
            text_color=color
        )
        self._actualizar_emojis()

    def _etiqueta_puntaje(self, p: int) -> str:
        if p == 0:
            return "Pésimo"
        elif p <= 2:
            return "Muy mal"
        elif p <= 4:
            return "Mal"
        elif p <= 6:
            return "Regular"
        elif p <= 8:
            return "Bien"
        else:
            return "Muy bien"

    def _registrar(self):
        nota = self.txt_nota.get("1.0", "end").strip()[:200]
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO termometro (fecha, hora, puntaje, nota) VALUES (?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self.puntaje_actual, nota)
            )
            conn.commit()
            conn.close()
            self.txt_nota.delete("1.0", "end")
            self._actualizar_historial()
            self._verificar_alerta()
            self._mostrar_confirmacion()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el registro.\n{e}")

    def _mostrar_confirmacion(self):
        colores = COLORS[self.modo]
        self.lbl_confirmacion = ctk.CTkLabel(
            self, text="✓ Registro guardado",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["success"],
            fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_button"],
            padx=16, pady=8
        )
        self.lbl_confirmacion.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, lambda: self.lbl_confirmacion.place_forget()
                   if hasattr(self, 'lbl_confirmacion') else None)

    def _actualizar_historial(self):
        for widget in self.frame_registros.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        conn = obtener_conexion()
        registros = conn.execute(
            "SELECT fecha, hora, puntaje, nota FROM termometro ORDER BY fecha DESC, hora DESC"
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_registros, text="Sin registros aún",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for reg in registros:
            etiqueta = self._etiqueta_puntaje(reg["puntaje"])
            color = color_por_puntaje(reg["puntaje"], self.modo)
            emoji = self.EMOJIS[reg["puntaje"]]

            fila = ctk.CTkFrame(self.frame_registros, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            inner = ctk.CTkFrame(fila, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=6)

            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x")

            ctk.CTkLabel(
                top, text=emoji,
                font=(TYPOGRAPHY["font_family"], 18),
                text_color=color
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                top, text=f"{reg['puntaje']}  {etiqueta}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                text_color=color
            ).pack(side="left")

            ctk.CTkLabel(
                top, text=f"{fecha_legible(reg['fecha'])} · {reg['hora'][:5]}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right")

            if reg["nota"]:
                ctk.CTkLabel(
                    inner,
                    text=reg["nota"][:80] + ("…" if len(reg["nota"]) > 80 else ""),
                    font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                    text_color=colores["text_secondary"],
                    anchor="w"
                ).pack(anchor="w", pady=(2, 0))

    def _verificar_alerta(self):
        conn = obtener_conexion()
        hoy = datetime.now().date()
        ultimos_3 = []
        for i in range(3):
            dia = (hoy - timedelta(days=i)).isoformat()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (dia,)
            ).fetchone()
            if row:
                ultimos_3.append(row["puntaje"])
        conn.close()

        if len(ultimos_3) == 3 and all(p <= 3 for p in ultimos_3):
            self._mostrar_alerta_apoyo()

    def _mostrar_alerta_apoyo(self):
        colores = COLORS[self.modo]
        alerta = ctk.CTkFrame(
            self, fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_color=colores["warning"],
            border_width=2
        )
        alerta.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            alerta, text="💛",
            font=(TYPOGRAPHY["font_family"], 28)
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            alerta, text="Notamos que tus últimos días fueron difíciles",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=24)

        ctk.CTkLabel(
            alerta,
            text="Recordá que no estás solo/a. Si necesitás hablar,\ncontactá a tu equipo terapéutico.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"],
            justify="center"
        ).pack(padx=24, pady=8)

        BotonPrimario(
            alerta, text="Entendido", modo=self.modo, width=120,
            command=alerta.destroy
        ).pack(pady=(8, 20))

    def _toggle_modo(self):
        estado = self.state()
        self._nota_temp = self.txt_nota.get("1.0", "end").strip() if hasattr(self, 'txt_nota') else ""
        self.modo = "light" if self.modo == "dark" else "dark"
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.slider.set(self.puntaje_actual)
        self._on_slider_change(self.puntaje_actual)
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = TermometroApp()
    app.mainloop()
