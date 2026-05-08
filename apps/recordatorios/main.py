import sys
import os

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from datetime import datetime
import threading
import time
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas, guardar_config, leer_config
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    mostrar_mensaje, NMToplevel, aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import hora_actual

try:
    import pystray
    from PIL import Image
    TRAY_DISPONIBLE = True
except ImportError:
    TRAY_DISPONIBLE = False

try:
    import numpy as np
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False


def _generar_tono(frecuencia: float, duracion: float, volumen: float = 0.25) -> "pygame.mixer.Sound | None":
    if not SONIDO_DISPONIBLE:
        return None
    try:
        sr = 44100
        t = np.linspace(0, duracion, int(sr * duracion), False)
        onda = np.sin(2 * np.pi * frecuencia * t) * volumen
        fade = int(sr * min(0.02, duracion / 4))
        onda[:fade] *= np.linspace(0, 1, fade)
        onda[-fade:] *= np.linspace(1, 0, fade)
        pcm = (onda * 32767).astype(np.int16)
        stereo = np.column_stack((pcm, pcm))
        return pygame.sndarray.make_sound(stereo)
    except Exception:
        return None


def _reproducir_check():
    s = _generar_tono(1046.5, 0.12)  # Do6 — breve y limpio
    if s:
        s.play()


def _reproducir_alarma():
    if not SONIDO_DISPONIBLE:
        return
    try:
        sr = 44100
        dur = 0.18
        t = np.linspace(0, dur, int(sr * dur), False)
        onda = (np.sin(2 * np.pi * 784 * t) * 0.18 + np.sin(2 * np.pi * 988 * t) * 0.12)
        fade = int(sr * 0.02)
        onda[:fade] *= np.linspace(0, 1, fade)
        onda[-fade:] *= np.linspace(1, 0, fade)
        pcm = (onda * 32767).astype(np.int16)
        stereo = np.column_stack((pcm, pcm))
        s = pygame.sndarray.make_sound(stereo)
        s.play()
    except Exception:
        pass


class RecordatoriosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"
        self.hilo_activo = True
        self.pausado = False
        self.silencio_inicio = leer_config("silencio_inicio", "23:00")
        self.silencio_fin = leer_config("silencio_fin", "07:00")
        self.tray_icon = None
        self._hora_temp = ""
        self._mensaje_temp = ""
        self._dias_temp = {i: True for i in range(1, 8)}

        self.title("NeuroMood · Recordatorios de Bienestar")
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
        self._iniciar_monitor()

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

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
            titulo="Recordatorios de Bienestar",
            subtitulo="Reforzá hábitos saludables con recordatorios personalizados",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=320)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_lista(col_izq)
        self._construir_formulario(col_der)
        self._construir_config_silencio(col_der)

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        estado_texto = "⏸ Pausado" if self.pausado else "▶ Activo"
        self.lbl_estado = ctk.CTkLabel(
            barra_inferior, text=estado_texto,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["warning"] if self.pausado else colores["success"]
        )
        self.lbl_estado.pack(side="left", padx=12, pady=5)

        BotonSecundario(
            barra_inferior, text="Pausar todo" if not self.pausado else "Reanudar",
            modo=self.modo, width=100, height=30,
            command=self._toggle_pausa
        ).pack(side="left", padx=4, pady=5)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

    def _construir_lista(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Recordatorios activos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        self.frame_lista = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_lista.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                              pady=(0, LAYOUT["padding_card"]))

        self._cargar_recordatorios()

    def _cargar_recordatorios(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        conn = obtener_conexion()
        recordatorios = conn.execute(
            "SELECT id, hora, mensaje, dias, activo FROM recordatorios ORDER BY hora"
        ).fetchall()
        conn.close()

        if not recordatorios:
            ctk.CTkLabel(
                self.frame_lista, text="No hay recordatorios configurados",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        dias_nombres = {1: "Lu", 2: "Ma", 3: "Mi", 4: "Ju", 5: "Vi", 6: "Sá", 7: "Do"}

        for rec in recordatorios:
            fila = ctk.CTkFrame(self.frame_lista, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=3)

            info_frame = ctk.CTkFrame(fila, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                info_frame, text=rec["hora"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                text_color=colores["accent"] if rec["activo"] else colores["text_tertiary"]
            ).pack(side="left", padx=(0, 12))

            ctk.CTkLabel(
                info_frame, text=rec["mensaje"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"] if rec["activo"] else colores["text_tertiary"]
            ).pack(side="left")

            dias_lista = rec["dias"].split(",")
            dias_texto = " ".join(dias_nombres.get(int(d), "") for d in dias_lista if d.strip())
            ctk.CTkLabel(
                info_frame, text=dias_texto,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right", padx=8)

            btn_frame = ctk.CTkFrame(fila, fg_color="transparent")
            btn_frame.pack(side="right", padx=8)

            rec_id = rec["id"]
            activo = rec["activo"]

            sw_var = ctk.BooleanVar(value=bool(activo))
            ctk.CTkSwitch(
                btn_frame,
                text="",
                variable=sw_var,
                width=48, height=24,
                button_color="#FFFFFF",
                button_hover_color=colores["text_secondary"],
                progress_color=colores["success"],
                fg_color=colores["progress_track"],
                command=lambda rid=rec_id, act=activo: self._toggle_activo(rid, act)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                btn_frame,
                text="Activo" if activo else "Pausado",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["success"] if activo else colores["text_tertiary"],
                width=52, anchor="w"
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btn_frame,
                text="✕",
                width=28, height=28,
                fg_color="transparent",
                hover_color=colores["error"],
                text_color=colores["text_tertiary"],
                corner_radius=LAYOUT["radius_button"],
                command=lambda rid=rec_id: self._eliminar_recordatorio(rid)
            ).pack(side="left", padx=2)

    def _construir_formulario(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="Nuevo recordatorio",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        ctk.CTkLabel(
            card, text="Hora (HH:MM)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w")

        self.entry_hora = InputTexto(card, modo=self.modo, placeholder_text="08:00")
        self.entry_hora.pack(fill="x", padx=LAYOUT["padding_card"], pady=(2, 8))
        if self._hora_temp:
            self.entry_hora.insert(0, self._hora_temp)

        ctk.CTkLabel(
            card, text="Mensaje",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w")

        self.entry_mensaje = InputTexto(card, modo=self.modo, placeholder_text="Tomá agua 💧")
        self.entry_mensaje.pack(fill="x", padx=LAYOUT["padding_card"], pady=(2, 8))
        if self._mensaje_temp:
            self.entry_mensaje.insert(0, self._mensaje_temp)

        ctk.CTkLabel(
            card, text="Días activos",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w")

        dias_frame = ctk.CTkFrame(card, fg_color="transparent")
        dias_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(2, 12))

        self.dias_vars = {}
        dias_nombres = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
        for i, nombre in enumerate(dias_nombres, 1):
            var = ctk.BooleanVar(value=self._dias_temp.get(i, True))
            self.dias_vars[i] = var
            ctk.CTkCheckBox(
                dias_frame, text=nombre, variable=var,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"],
                fg_color=colores["accent"],
                hover_color=colores["accent_hover"],
                border_color=colores["border"],
                checkmark_color=colores["text_on_accent"],
                width=40
            ).pack(side="left", padx=2)

        BotonPrimario(
            card, text="Agregar recordatorio", modo=self.modo,
            command=self._agregar_recordatorio
        ).pack(padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]), fill="x")

    def _construir_config_silencio(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x")

        ctk.CTkLabel(
            card, text="Modo silencio",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        frame_horas = ctk.CTkFrame(card, fg_color="transparent")
        frame_horas.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        ctk.CTkLabel(
            frame_horas, text="Desde:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(side="left")

        self.entry_silencio_inicio = InputTexto(frame_horas, modo=self.modo, width=70)
        self.entry_silencio_inicio.insert(0, self.silencio_inicio)
        self.entry_silencio_inicio.pack(side="left", padx=(4, 12))

        ctk.CTkLabel(
            frame_horas, text="Hasta:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_secondary"]
        ).pack(side="left")

        self.entry_silencio_fin = InputTexto(frame_horas, modo=self.modo, width=70)
        self.entry_silencio_fin.insert(0, self.silencio_fin)
        self.entry_silencio_fin.pack(side="left", padx=4)

        BotonSecundario(
            card, text="Guardar horario", modo=self.modo, width=140,
            command=self._guardar_silencio
        ).pack(padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

    def _agregar_recordatorio(self):
        hora = self.entry_hora.get().strip()
        mensaje = self.entry_mensaje.get().strip()

        if not hora or not mensaje:
            mostrar_mensaje(self, "Faltan datos", "Completá la hora y el mensaje.", tipo="warning", modo=self.modo)
            return

        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            mostrar_mensaje(self, "Hora inválida", "Usá el formato HH:MM (ej: 08:30)", tipo="warning", modo=self.modo)
            return

        dias_activos = [str(d) for d, var in self.dias_vars.items() if var.get()]
        if not dias_activos:
            mostrar_mensaje(self, "Sin días", "Seleccioná al menos un día.", tipo="warning", modo=self.modo)
            return

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO recordatorios (hora, mensaje, dias, activo) VALUES (?, ?, ?, 1)",
                (hora, mensaje, ",".join(dias_activos))
            )
            conn.commit()
            conn.close()
            self.entry_hora.delete(0, "end")
            self.entry_mensaje.delete(0, "end")
            self._cargar_recordatorios()
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo guardar.\n{e}", tipo="error", modo=self.modo)

    def _toggle_activo(self, rec_id, activo_actual):
        nuevo_activo = 0 if activo_actual else 1
        rec_hora = None
        rec_mensaje = None
        conn = obtener_conexion()
        conn.execute("UPDATE recordatorios SET activo = ? WHERE id = ?",
                     (nuevo_activo, rec_id))
        conn.commit()
        if nuevo_activo == 1:
            rec = conn.execute("SELECT hora, mensaje FROM recordatorios WHERE id = ?", (rec_id,)).fetchone()
            if rec:
                rec_hora = rec["hora"]
                rec_mensaje = rec["mensaje"]
        conn.close()
        if nuevo_activo == 1 and rec_hora and not self.pausado and not self._en_silencio():
            minuto_actual = datetime.now().strftime("%H:%M")
            if rec_hora == minuto_actual:
                self.after(0, lambda m=rec_mensaje: (self._mostrar_popup(m), _reproducir_alarma()))
        if not activo_actual:
            _reproducir_check()
        self._cargar_recordatorios()

    def _eliminar_recordatorio(self, rec_id):
        conn = obtener_conexion()
        conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
        conn.commit()
        conn.close()
        self._cargar_recordatorios()

    def _guardar_silencio(self):
        inicio = self.entry_silencio_inicio.get().strip()
        fin = self.entry_silencio_fin.get().strip()
        try:
            datetime.strptime(inicio, "%H:%M")
            datetime.strptime(fin, "%H:%M")
        except ValueError:
            mostrar_mensaje(self, "Formato inválido", "Usá HH:MM para ambas horas.", tipo="warning", modo=self.modo)
            return
        self.silencio_inicio = inicio
        self.silencio_fin = fin
        guardar_config("silencio_inicio", inicio)
        guardar_config("silencio_fin", fin)
        colores = COLORS[self.modo]
        lbl_ok = ctk.CTkLabel(
            self, text="✓ Horario guardado",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["success"],
            fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_button"],
            padx=16, pady=8
        )
        lbl_ok.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, lbl_ok.place_forget)

    def _en_silencio(self) -> bool:
        ahora = datetime.now().strftime("%H:%M")
        inicio = self.silencio_inicio
        fin = self.silencio_fin
        if inicio <= fin:
            return inicio <= ahora <= fin
        else:
            return ahora >= inicio or ahora <= fin

    def _toggle_pausa(self):
        self.pausado = not self.pausado
        self._construir_ui()

    def _iniciar_monitor(self):
        self.ultimo_minuto_notificado = ""

        def monitor():
            while self.hilo_activo:
                time.sleep(1)
                if self.pausado or self._en_silencio():
                    continue

                ahora = datetime.now()
                minuto_actual = ahora.strftime("%H:%M")
                dia_semana = ahora.isoweekday()

                if minuto_actual == self.ultimo_minuto_notificado:
                    continue

                conn = obtener_conexion()
                recordatorios = conn.execute(
                    "SELECT mensaje, dias FROM recordatorios WHERE hora = ? AND activo = 1",
                    (minuto_actual,)
                ).fetchall()
                conn.close()

                for rec in recordatorios:
                    if str(dia_semana) not in rec["dias"].split(","):
                        continue
                    self.ultimo_minuto_notificado = minuto_actual
                    self.after(0, lambda m=rec["mensaje"]: (self._mostrar_popup(m), _reproducir_alarma()))

        hilo = threading.Thread(target=monitor, daemon=True)
        hilo.start()

    def _mostrar_popup(self, mensaje):
        colores = COLORS[self.modo]
        popup = NMToplevel(self, modo=self.modo)
        popup.title("Recordatorio")
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
            frame, text="🔔 Recordatorio",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["accent"]
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            frame, text=mensaje,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"],
            wraplength=320
        ).pack(pady=(0, 16))

        BotonPrimario(
            frame, text="Entendido", modo=self.modo, width=120,
            command=popup.destroy
        ).pack()

    def _toggle_modo(self):
        estado = self.state()
        self._hora_temp = self.entry_hora.get().strip() if hasattr(self, 'entry_hora') else ""
        self._mensaje_temp = self.entry_mensaje.get().strip() if hasattr(self, 'entry_mensaje') else ""
        if hasattr(self, 'dias_vars'):
            self._dias_temp = {i: v.get() for i, v in self.dias_vars.items()}
        if hasattr(self, 'entry_silencio_inicio'):
            val = self.entry_silencio_inicio.get().strip()
            if val:
                self.silencio_inicio = val
        if hasattr(self, 'entry_silencio_fin'):
            val = self.entry_silencio_fin.get().strip()
            if val:
                self.silencio_fin = val
        self.modo = "light" if self.modo == "dark" else "dark"
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")

    def _al_cerrar(self):
        self.hilo_activo = False
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = RecordatoriosApp()
    app.mainloop()
