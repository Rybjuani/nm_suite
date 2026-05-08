import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math
import time as _time_mod

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual


TECNICA_478 = {"inhalar": 4, "retener": 7, "exhalar": 8}


class RespiracionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"

        self.duracion_sesion = 180
        self.corriendo = False
        self.ciclos_completados = 0
        self.fase_actual = ""
        self.segundos_fase_restantes = 0
        self.tiempo_total_transcurrido = 0
        self.timer_id = None
        self._tiempo_inicio_real = 0

        self.title("NeuroMood · Guía de Respiración")
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
            titulo="Guía de Respiración",
            subtitulo="Regulación del sistema nervioso autónomo",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=280)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_circulo(col_izq)
        self._construir_controles(col_der)
        self._construir_historial(col_der)

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

    def _construir_circulo(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                         pady=LAYOUT["padding_card"])
        self.canvas.bind("<Configure>", lambda e: self._dibujar_circulo(0.5) if not self.corriendo else None)

        self.lbl_instruccion = ctk.CTkLabel(
            card, text="Presioná Iniciar para comenzar",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=colores["text_primary"]
        )
        self.lbl_instruccion.pack(pady=(0, 8))

        self.lbl_ciclos = ctk.CTkLabel(
            card, text="Ciclos: 0",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["accent"]
        )
        self.lbl_ciclos.pack(pady=(0, 4))

        self.lbl_tiempo_sesion = ctk.CTkLabel(
            card, text="",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_tertiary"]
        )
        self.lbl_tiempo_sesion.pack(pady=(0, LAYOUT["padding_card"]))

    def _construir_controles(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Técnica 4-7-8",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        ctk.CTkLabel(
            card, text="Inhalá 4s · Retené 7s · Exhalá 8s",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            card, text="Duración",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(0, 4), anchor="w")

        dur_frame = ctk.CTkFrame(card, fg_color="transparent")
        dur_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        for texto, seg in [("3'", 180), ("5'", 300), ("10'", 600), ("Libre", 0)]:
            es_activa = seg == self.duracion_sesion
            ctk.CTkButton(
                dur_frame, text=texto, width=55, height=34,
                fg_color=colores["accent"] if es_activa else colores["bg_hover"],
                hover_color=colores["accent_hover"],
                text_color=colores["text_on_accent"] if es_activa else colores["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                command=lambda s=seg: self._set_duracion(s)
            ).pack(side="left", padx=2)

        self.btn_iniciar = BotonPrimario(
            card, text="Iniciar", modo=self.modo,
            command=self._toggle_sesion
        )
        self.btn_iniciar.pack(fill="x", padx=LAYOUT["padding_card"],
                              pady=(0, LAYOUT["padding_card"]))

    def _construir_historial(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Sesiones recientes",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        self.frame_historial = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_historial.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                                  pady=(0, LAYOUT["padding_card"]))

        self._cargar_historial()

    def _cargar_historial(self):
        for widget in self.frame_historial.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        conn = obtener_conexion()
        sesiones = conn.execute(
            "SELECT fecha, hora, tecnica, duracion_minutos, ciclos FROM respiracion ORDER BY fecha DESC, hora DESC LIMIT 10"
        ).fetchall()
        conn.close()

        for ses in sesiones:
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            ctk.CTkLabel(
                fila, text=f"{ses['tecnica']} · {ses['ciclos']} ciclos",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_primary"]
            ).pack(padx=8, pady=(4, 0), anchor="w")

            ctk.CTkLabel(
                fila, text=f"{ses['fecha']} · {int(ses['duracion_minutos'])} min",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(padx=8, pady=(0, 4), anchor="w")

    def _dibujar_circulo(self, escala: float):
        canvas = self.canvas
        canvas.delete("all")
        colores = COLORS[self.modo]

        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 400
        cx, cy = w // 2, h // 2

        radio_max = min(w, h) // 2 - 40
        radio_min = radio_max * 0.4
        radio = radio_min + (radio_max - radio_min) * escala

        canvas.create_oval(
            cx - radio_max - 5, cy - radio_max - 5,
            cx + radio_max + 5, cy + radio_max + 5,
            outline=colores["border"], width=1, dash=(4, 4)
        )

        for i in range(3):
            offset = i * 8
            alpha_approx = 0.3 - i * 0.1
            canvas.create_oval(
                cx - radio - offset, cy - radio - offset,
                cx + radio + offset, cy + radio + offset,
                outline=colores["accent"], width=1
            )

        canvas.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            fill=colores["bg_primary"], outline=colores["accent"], width=3
        )

        if self.fase_actual:
            canvas.create_text(
                cx, cy - 14, text=self.fase_actual,
                fill=colores["accent"],
                font=(TYPOGRAPHY["font_family"], 16, "bold")
            )
            canvas.create_text(
                cx, cy + 18, text=f"{self.segundos_fase_restantes}s",
                fill=colores["text_primary"],
                font=(TYPOGRAPHY["font_family"], 28, "bold")
            )

    def _set_duracion(self, segundos):
        if not self.corriendo:
            self.duracion_sesion = segundos
            self._construir_ui()

    def _toggle_sesion(self):
        if self.corriendo:
            self._detener()
        else:
            self._iniciar_sesion()

    def _iniciar_sesion(self):
        self.corriendo = True
        self.ciclos_completados = 0
        self.tiempo_total_transcurrido = 0
        self._tiempo_inicio_real = _time_mod.time()
        self._detener_al_terminar_ciclo = False
        self.btn_iniciar.configure(text="Detener", fg_color=COLORS[self.modo]["error"])
        self._ejecutar_ciclo()

    def _detener(self):
        self.corriendo = False
        self._detener_al_terminar_ciclo = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

        self.btn_iniciar.configure(text="Iniciar", fg_color=COLORS[self.modo]["accent"])
        self._guardar_sesion()
        self._mostrar_finalizado()

    def _ejecutar_ciclo(self):
        if not self.corriendo:
            return

        fases = [
            ("Inhalá...", TECNICA_478["inhalar"]),
            ("Retené...", TECNICA_478["retener"]),
            ("Exhalá...", TECNICA_478["exhalar"]),
        ]

        self._ejecutar_fases(fases, 0)

    def _ejecutar_fases(self, fases, indice):
        if not self.corriendo:
            return

        if indice >= len(fases):
            if self._detener_al_terminar_ciclo:
                self._detener_al_terminar_ciclo = False
                self.ciclos_completados += 1
                self.lbl_ciclos.configure(text=f"Ciclos: {self.ciclos_completados}")
                self._detener()
                return
            self.ciclos_completados += 1
            self.lbl_ciclos.configure(text=f"Ciclos: {self.ciclos_completados}")
            self._ejecutar_ciclo()
            return

        if self.duracion_sesion > 0 and not self._detener_al_terminar_ciclo:
            elapsed = _time_mod.time() - self._tiempo_inicio_real
            if elapsed >= self.duracion_sesion:
                if indice < 2:
                    self._detener()
                    return
                else:
                    self._detener_al_terminar_ciclo = True

        texto, duracion = fases[indice]
        self.fase_actual = texto.replace("...", "")
        self.lbl_instruccion.configure(text=texto)

        es_inhalar = "Inhal" in texto
        es_exhalar = "Exhal" in texto

        self._animar_fase(duracion, es_inhalar, es_exhalar, fases, indice)

    def _animar_fase(self, duracion_seg, es_inhalar, es_exhalar, fases, indice):
        total_frames = duracion_seg * 20
        frame_actual = [0]

        def animar():
            if not self.corriendo:
                return

            progreso = frame_actual[0] / max(total_frames, 1)
            self.segundos_fase_restantes = duracion_seg - (frame_actual[0] // 20)

            if es_inhalar:
                escala = 0.3 + progreso * 0.7
            elif es_exhalar:
                escala = 1.0 - progreso * 0.7
            else:
                escala = 0.5 + math.sin(progreso * math.pi * 2) * 0.1

            self._dibujar_circulo(escala)

            if hasattr(self, 'lbl_tiempo_sesion') and self.corriendo:
                elapsed = _time_mod.time() - self._tiempo_inicio_real
                if self.duracion_sesion > 0:
                    restante = max(0, self.duracion_sesion - elapsed)
                    mm, ss = int(restante) // 60, int(restante) % 60
                    self.lbl_tiempo_sesion.configure(text=f"⏱ {mm:02d}:{ss:02d} restantes")
                else:
                    mm, ss = int(elapsed) // 60, int(elapsed) % 60
                    self.lbl_tiempo_sesion.configure(text=f"⏱ {mm:02d}:{ss:02d} transcurridos")

            frame_actual[0] += 1
            if frame_actual[0] >= total_frames:
                self.tiempo_total_transcurrido += duracion_seg
                self._ejecutar_fases(fases, indice + 1)
            else:
                self.timer_id = self.after(50, animar)

        animar()

    def _guardar_sesion(self):
        if self.ciclos_completados == 0:
            return

        duracion_min = round(self.tiempo_total_transcurrido / 60, 1)
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO respiracion (fecha, hora, tecnica, duracion_minutos, ciclos) VALUES (?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), "4-7-8", duracion_min, self.ciclos_completados)
            )
            conn.commit()
            conn.close()
            self._cargar_historial()
        except Exception:
            pass

    def _mostrar_finalizado(self):
        colores = COLORS[self.modo]

        self.fase_actual = ""
        self._dibujar_circulo(0.5)
        if hasattr(self, 'lbl_tiempo_sesion'):
            self.lbl_tiempo_sesion.configure(text="")

        self.lbl_instruccion.configure(text=f"✓ Sesión completada — {self.ciclos_completados} ciclos")

        duracion_min = round(self.tiempo_total_transcurrido / 60, 1)
        mm = int(self.tiempo_total_transcurrido) // 60
        ss = int(self.tiempo_total_transcurrido) % 60
        tiempo_str = f"{mm}:{ss:02d} min" if mm > 0 else f"{ss}s"

        popup = ctk.CTkFrame(
            self, fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_modal"],
            border_color=colores["accent"],
            border_width=LAYOUT["border_accent_width"]
        )
        popup.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            popup, text="Completado",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["accent"]
        ).pack(padx=32, pady=(24, 12))

        ctk.CTkLabel(
            popup, text=f"{self.ciclos_completados} ciclos · {tiempo_str}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"]
        ).pack(padx=32, pady=(0, 4))

        ctk.CTkLabel(
            popup, text="Técnica 4-7-8",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=32)

        BotonPrimario(
            popup, text="Continuar", modo=self.modo, width=120,
            command=popup.destroy
        ).pack(pady=(16, 24))

    def _toggle_modo(self):
        estado = self.state()
        self.modo = "light" if self.modo == "dark" else "dark"
        hwnd = _freeze_window(self)
        self._construir_ui()
        if self.corriendo:
            self.btn_iniciar.configure(text="Detener", fg_color=COLORS[self.modo]["error"])
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = RespiracionApp()
    app.mainloop()
