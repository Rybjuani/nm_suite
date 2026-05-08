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
import threading

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, BadgeLabel, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    NMToplevel, aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual

try:
    import pystray
    from PIL import Image as PILImage
    TRAY_DISPONIBLE = True
except ImportError:
    TRAY_DISPONIBLE = False

try:
    import pygame
    pygame.mixer.init()
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False


CATEGORIAS = ["Relajación", "Cognitiva", "Física", "Social", "Autocuidado"]


class TemporizadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"
        self._nombre_temp = ""
        self._actividad_texto = ""
        self._nombre_actividad = ""
        self.tray_icon = None

        self.duracion_total = 300
        self.tiempo_restante = 300
        self.corriendo = False
        self.en_pausa = False
        self.timer_id = None
        self.tiempo_inicio = None
        self.categoria_actual = CATEGORIAS[0]

        self.title("NeuroMood · Temporizador de Actividades")
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

        self._estado_ventana = "zoomed"
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
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
        if estado in ("zoomed", "normal"):
            self._estado_ventana = estado
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
            titulo="Temporizador de Actividades",
            subtitulo="Delimitá tus actividades terapéuticas en el tiempo",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=300)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_temporizador(col_izq)
        self._construir_controles(col_izq)
        self._construir_historial_hoy(col_der)

    def _construir_temporizador(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        self.canvas_timer = tk.Canvas(
            card, bg=colores["bg_surface"], highlightthickness=0,
            width=180, height=180
        )
        self.canvas_timer.pack(pady=LAYOUT["padding_card"])

        self.lbl_tiempo = ctk.CTkLabel(
            card, text=self._formatear_tiempo(self.tiempo_restante),
            font=(TYPOGRAPHY["font_family"], 36, "bold"),
            text_color=colores["text_primary"]
        )
        self.lbl_tiempo.pack(pady=(0, 8))

        self.lbl_actividad = ctk.CTkLabel(
            card, text="Sin actividad configurada",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_tertiary"]
        )
        self.lbl_actividad.pack(pady=(0, LAYOUT["padding_card"]))
        if self._actividad_texto and self._actividad_texto != "Sin actividad configurada":
            color = colores["accent"] if self.corriendo else colores["success"]
            self.lbl_actividad.configure(text=self._actividad_texto, text_color=color)

        self._dibujar_arco()

    def _construir_controles(self, parent):
        colores = COLORS[self.modo]
        p = LAYOUT["padding_card"]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x")

        # ── Fila: Actividad ───────────────────────────
        row_act = ctk.CTkFrame(card, fg_color="transparent")
        row_act.pack(fill="x", padx=p, pady=(p, 8))
        ctk.CTkLabel(
            row_act, text="Actividad:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))
        self.entry_nombre = InputTexto(row_act, modo=self.modo, placeholder_text="Nombre de la actividad", height=34)
        self.entry_nombre.pack(side="left", fill="x", expand=True)
        if self._nombre_temp:
            self.entry_nombre.insert(0, self._nombre_temp)

        # ── Fila: Categoría ───────────────────────────
        row_cat = ctk.CTkFrame(card, fg_color="transparent")
        row_cat.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_cat, text="Categoría:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))
        self.combo_categoria = ctk.CTkComboBox(
            row_cat, values=CATEGORIAS,
            fg_color=colores["bg_input"],
            border_color=colores["border"],
            button_color=colores["accent"],
            button_hover_color=colores["accent_hover"],
            dropdown_fg_color=colores["bg_surface"],
            dropdown_hover_color=colores["bg_hover"],
            text_color=colores["text_primary"],
            dropdown_text_color=colores["text_primary"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_input"],
            command=self._on_categoria
        )
        self.combo_categoria.set(self.categoria_actual)
        self.combo_categoria.pack(side="left")

        # ── Fila: Duración ────────────────────────────
        row_dur = ctk.CTkFrame(card, fg_color="transparent")
        row_dur.pack(fill="x", padx=p, pady=(0, 8))
        ctk.CTkLabel(
            row_dur, text="Duración:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"],
            width=72, anchor="w"
        ).pack(side="left", padx=(0, 8))

        presets = [("5'", 300), ("10'", 600), ("15'", 900), ("20'", 1200), ("30'", 1800)]
        self.preset_btns = {}
        for texto, seg in presets:
            selec = (self.duracion_total == seg)
            b = ctk.CTkButton(
                row_dur, text=texto, width=44, height=34,
                fg_color=colores["accent"] if selec else colores["bg_hover"],
                hover_color=colores["accent_hover"],
                text_color=colores["text_on_accent"] if selec else colores["text_primary"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                command=lambda s=seg: self._set_duracion(s)
            )
            b.pack(side="left", padx=2)
            self.preset_btns[seg] = b

        self.entry_custom = InputTexto(row_dur, modo=self.modo, width=50, height=34, placeholder_text="min")
        self.entry_custom.pack(side="left", padx=(8, 4))
        ctk.CTkButton(
            row_dur, text="OK", width=36, height=34,
            fg_color=colores["accent"],
            hover_color=colores["accent_hover"],
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            command=self._set_custom
        ).pack(side="left")

        # ── Separador ─────────────────────────────────
        ctk.CTkFrame(card, fg_color=colores["border"], height=1, corner_radius=0).pack(
            fill="x", padx=p, pady=(8, 0)
        )

        # ── Botones de control ────────────────────────
        frame_btns = ctk.CTkFrame(card, fg_color="transparent")
        frame_btns.pack(fill="x", padx=p, pady=(p // 2, p))

        self.btn_iniciar = BotonPrimario(
            frame_btns, text="Iniciar", modo=self.modo, command=self._iniciar,
            width=100, height=30
        )
        self.btn_iniciar.pack(side="left", padx=(0, 8))

        self.btn_pausar = BotonSecundario(
            frame_btns, text="Pausar", modo=self.modo, command=self._pausar,
            width=100, height=30
        )
        self.btn_pausar.pack(side="left", padx=(0, 8))

        BotonSecundario(
            frame_btns, text="Reiniciar", modo=self.modo, command=self._reiniciar,
            width=100, height=30
        ).pack(side="left")

    def _construir_historial_hoy(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Actividades de hoy",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
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
        registros = conn.execute(
            "SELECT nombre, categoria, hora, duracion_real FROM actividades_temporizador WHERE fecha = ? ORDER BY hora DESC",
            (fecha_hoy(),)
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_historial, text="Sin actividades completadas hoy",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for reg in registros:
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            info = ctk.CTkFrame(fila, fg_color="transparent")
            info.pack(side="left", padx=12, pady=8, fill="x", expand=True)

            ctk.CTkLabel(
                info, text=f"✓ {reg['nombre']}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                info, text=reg["categoria"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(anchor="w")

            minutos = reg["duracion_real"] // 60
            ctk.CTkLabel(
                fila, text=f"{minutos} min",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["accent"]
            ).pack(side="right", padx=12)

            ctk.CTkLabel(
                fila, text=reg["hora"][:5],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right", padx=4)

    def _dibujar_arco(self):
        canvas = self.canvas_timer
        canvas.delete("all")
        colores = COLORS[self.modo]

        w = 180
        h = 180
        cx, cy = w // 2, h // 2
        radio = 70
        grosor = 10

        canvas.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            outline=colores["progress_track"], width=grosor
        )

        if self.duracion_total > 0:
            progreso = self.tiempo_restante / self.duracion_total if self.corriendo or self.tiempo_restante > 0 else 1.0
        else:
            progreso = 0

        if progreso > 0:
            angulo_inicio = 90
            angulo_ext = progreso * 360
            canvas.create_arc(
                cx - radio, cy - radio, cx + radio, cy + radio,
                start=angulo_inicio, extent=angulo_ext,
                outline=colores["accent"], width=grosor, style="arc"
            )

    def _formatear_tiempo(self, segundos: int) -> str:
        m = segundos // 60
        s = segundos % 60
        return f"{m:02d}:{s:02d}"

    def _set_duracion(self, segundos: int):
        if not self.corriendo:
            self.duracion_total = segundos
            self.tiempo_restante = segundos
            self.lbl_tiempo.configure(text=self._formatear_tiempo(segundos))
            self._dibujar_arco()
            if hasattr(self, 'preset_btns'):
                colores = COLORS[self.modo]
                for seg, btn in self.preset_btns.items():
                    if seg == segundos:
                        btn.configure(fg_color=colores["accent"], text_color=colores["text_on_accent"])
                    else:
                        btn.configure(fg_color=colores["bg_hover"], text_color=colores["text_secondary"])

    def _set_custom(self):
        try:
            minutos = int(self.entry_custom.get().strip())
            if 1 <= minutos <= 180:
                self._set_duracion(minutos * 60)
        except ValueError:
            pass

    def _on_categoria(self, valor):
        self.categoria_actual = valor

    def _iniciar(self):
        if self.corriendo:
            return
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            nombre = "Actividad sin nombre"

        self._nombre_actividad = nombre

        colores = COLORS[self.modo]
        self.lbl_actividad.configure(text=nombre, text_color=colores["accent"])

        if self.tiempo_restante <= 0:
            self.tiempo_restante = self.duracion_total

        self.en_pausa = False
        self.btn_pausar.configure(text="Pausar")
        self.tiempo_inicio = datetime.now()
        self.corriendo = True
        self._tick()

    def _pausar(self):
        if self.corriendo:
            self.corriendo = False
            if self.timer_id:
                self.after_cancel(self.timer_id)
                self.timer_id = None
            self.en_pausa = True
            self.btn_pausar.configure(text="Reanudar")
            self.btn_iniciar.configure(state="disabled")
        elif self.en_pausa:
            self.en_pausa = False
            self.corriendo = True
            self.btn_pausar.configure(text="Pausar")
            self.btn_iniciar.configure(state="normal")
            self._tick()

    def _reiniciar(self):
        self.corriendo = False
        self.en_pausa = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.tiempo_restante = self.duracion_total
        self.lbl_tiempo.configure(text=self._formatear_tiempo(self.duracion_total))
        self.btn_pausar.configure(text="Pausar")
        self.btn_iniciar.configure(state="normal")
        colores = COLORS[self.modo]
        self.lbl_actividad.configure(text="Sin actividad configurada", text_color=colores["text_tertiary"])
        self._dibujar_arco()

    def _tick(self):
        if not self.corriendo:
            return

        self.tiempo_restante -= 1
        self.lbl_tiempo.configure(text=self._formatear_tiempo(max(0, self.tiempo_restante)))
        self._dibujar_arco()

        if self.tiempo_restante <= 0:
            self.corriendo = False
            self._finalizar()
            return

        self.timer_id = self.after(1000, self._tick)

    def _finalizar(self):
        nombre = self._nombre_actividad or self.entry_nombre.get().strip()
        duracion_real = self.duracion_total - self.tiempo_restante

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO actividades_temporizador (fecha, hora, nombre, categoria, duracion_config, duracion_real) VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), nombre, self.categoria_actual, self.duracion_total, duracion_real)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        self._cargar_historial()
        self._reproducir_alarma()

        if self.tray_icon is not None:
            self._restaurar_desde_bandeja()
        self._mostrar_finalizado(nombre)

    def _reproducir_alarma(self):
        if not SONIDO_DISPONIBLE:
            return
        try:
            freq = 800
            duracion_ms = 300
            import numpy as np
            sample_rate = 44100
            t = np.linspace(0, duracion_ms / 1000, int(sample_rate * duracion_ms / 1000), False)
            wave = np.sin(2 * math.pi * freq * t) * 0.3
            wave = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
            self.after(500, sound.play)
            self.after(1000, sound.play)
        except Exception:
            pass

    def _mostrar_finalizado(self, nombre: str = ""):
        self._restaurar_ventana()
        colores = COLORS[self.modo]
        if hasattr(self, 'lbl_actividad'):
            self.lbl_actividad.configure(
                text=nombre or "Actividad",
                text_color=colores["success"]
            )

        popup = NMToplevel(self, modo=self.modo)
        popup.title("Actividad completada")
        _w, _h = 380, 200
        _sw = popup.winfo_screenwidth()
        _sh = popup.winfo_screenheight()
        _x = (_sw - _w) // 2
        _y = (_sh - _h) // 2
        popup.geometry(f"{_w}x{_h}+{_x}+{_y}")
        popup.resizable(False, False)
        popup.configure(fg_color=colores["bg_surface"])
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.after(10, lambda: popup.focus_force())

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=LAYOUT["padding_container"],
                   pady=LAYOUT["padding_container"])

        ctk.CTkLabel(
            frame, text="⏰ Actividad completada",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["accent"]
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            frame,
            text=nombre if nombre else "El tiempo de tu actividad ha finalizado.",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"],
            wraplength=320
        ).pack(pady=(0, 16))

        BotonPrimario(
            frame, text="Entendido", modo=self.modo, width=120,
            command=popup.destroy
        ).pack()

    def _al_cerrar(self):
        if self.corriendo:
            self._enviar_a_bandeja()
        else:
            self.destroy()

    def _enviar_a_bandeja(self):
        if not TRAY_DISPONIBLE:
            self.destroy()
            return
        self.withdraw()

        def _crear_imagen():
            try:
                ruta = obtener_ruta_recurso("LOGO.png")
                img = PILImage.open(ruta).convert("RGBA").resize((64, 64), PILImage.LANCZOS)
                return img
            except Exception:
                img = PILImage.new("RGBA", (64, 64), (30, 200, 212, 255))
                return img

        menu = pystray.Menu(
            pystray.MenuItem("Abrir Temporizador", lambda icon, item: self.after(0, self._restaurar_desde_bandeja), default=True),
            pystray.MenuItem("Salir", lambda icon, item: self.after(0, self._salir_desde_bandeja)),
        )
        self.tray_icon = pystray.Icon(
            "NM_Temporizador",
            _crear_imagen(),
            "Temporizador en ejecución",
            menu=menu
        )
        hilo = threading.Thread(target=self.tray_icon.run, daemon=True)
        hilo.start()

    def _restaurar_desde_bandeja(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self._restaurar_ventana()

    def _salir_desde_bandeja(self):
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.destroy()

    def _restaurar_ventana(self):
        self.deiconify()
        estado = getattr(self, "_estado_ventana", "zoomed")
        if estado == "zoomed":
            self.state("zoomed")
        self.lift()
        self.focus_force()

    def _toggle_modo(self):
        estado = self.state()
        self._nombre_temp = self.entry_nombre.get().strip() if hasattr(self, 'entry_nombre') else ""
        self._actividad_texto = self.lbl_actividad.cget("text") if hasattr(self, 'lbl_actividad') else ""
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        was_corriendo = self.corriendo
        self.corriendo = False
        self.modo = "light" if self.modo == "dark" else "dark"
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")
        if was_corriendo:
            self.corriendo = True
            self._tick()
        elif self.en_pausa:
            self.btn_pausar.configure(text="Reanudar")
            self.btn_iniciar.configure(state="disabled")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = TemporizadorApp()
    app.mainloop()
