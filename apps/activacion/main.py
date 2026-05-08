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
import random

try:
    import numpy as np
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SONIDO_DISPONIBLE = True
except Exception:
    SONIDO_DISPONIBLE = False

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    BadgeLabel, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual, fecha_legible


# Energía 0-3: activación mínima — bajo umbral conductual
ACTIVIDADES_BAJA = [
    "Permanecé en posición cómoda y realizá 5 ciclos de respiración diafragmática lenta",
    "Identificá 3 objetos en la habitación y describí mentalmente su forma, color y textura",
    "Tomá un vaso de agua despacio. El acto de hidratarse es una conducta de autocuidado básico",
    "Soltá la mandíbula, los hombros y las manos. Escaneá brevemente tensión corporal",
    "Escribí en papel una sola oración sobre cómo te sentís en este momento, sin editar",
    "Abrí una ventana o salí al exterior 2 minutos. El cambio sensorial reduce la rumiación",
    "Dúchate con agua tibia — la estimulación sensoriomotora activa el sistema nervioso",
    "Escuchá una canción completa sin hacer otra cosa al mismo tiempo",
    "Movilizá suavemente cuello, hombros y muñecas durante 3 minutos",
    "Tomá una infusión caliente. La rutina sensorial contribuye a la regulación emocional",
    "Ordená un único objeto fuera de lugar. Las conductas de bajo costo generan sensación de control",
    "Escribí una sola cosa concreta que hayas hecho hoy, sin minimizarla",
]

# Energía 4-6: activación moderada — conductas con mayor demanda
ACTIVIDADES_MEDIA = [
    "Salí a caminar 15 minutos a ritmo moderado, preferentemente sin pantallas",
    "Realizá una práctica de relajación muscular progresiva de Jacobson durante 10 minutos",
    "Escribí en un registro personal sin corrección durante 10 minutos sobre lo que te preocupa",
    "Preparate una comida sencilla prestando atención al proceso — no al resultado",
    "Realizá una secuencia de estiramiento muscular de 10 minutos con música tranquila",
    "Enviá un mensaje breve a alguien de confianza. El contacto social reduce el aislamiento",
    "Leé material de tu interés durante 20 minutos sin otras tareas en paralelo",
    "Organizá un espacio pequeño del entorno. El orden físico impacta en el estado mental",
    "Hacé una lista de 3 actividades placenteras que hayas postergado y agendá una para esta semana",
    "Escuchá un podcast o audio de tema de tu interés mientras realizás una tarea manual simple",
    "Realizá una meditación guiada de 10 minutos orientada a la observación del pensamiento",
    "Realizá una actividad expresiva sin objetivo de resultado: dibujo, escritura libre, color",
]

# Energía 7-10: activación alta — conductas con mayor demanda cognitiva y social
ACTIVIDADES_ALTA = [
    "Realizá ejercicio físico aeróbico de intensidad moderada durante 30 minutos",
    "Retomá una actividad o proyecto personal que hayas suspendido sin fecha de retorno",
    "Planificá y cocinás una receta nueva. El aprendizaje activo genera bienestar sostenido",
    "Contactá a alguien de tu red social y proponé un encuentro concreto con fecha y lugar",
    "Visitá un espacio cultural o natural diferente a tu rutina habitual",
    "Inscribite o asistí a una clase, taller o actividad grupal nueva",
    "Trabajá en un proyecto propio durante al menos 45 minutos sin interrupciones",
    "Realizá una caminata larga en entorno natural o urbano diferente al habitual",
    "Resolvé una tarea postergada de mediana complejidad de principio a fin",
    "Realizá ejercicio físico de alta intensidad: carrera, natación, deporte grupal",
    "Escribí un texto elaborado sobre algo que te importe: reflexión, carta, proyecto",
    "Dedicá tiempo a una habilidad específica que querés desarrollar: idioma, instrumento, técnica",
]

MENSAJES_REFUERZO = [
    "Completar esta actividad es evidencia de capacidad de acción. Registralo.",
    "La activación conductual funciona porque actuás antes de sentirte listo. Lo hiciste.",
    "Este es exactamente el tipo de acción que genera cambio a lo largo del tiempo.",
    "Tomaste una decisión activa sobre tu bienestar. Eso tiene valor terapéutico real.",
    "Cada actividad completada fortalece el patrón de activación. Seguí.",
    "Lo que acabás de hacer es parte del trabajo. No es menor.",
    "La conducta precede al estado de ánimo. Acabás de demostrarlo.",
    "Este registro queda como evidencia de tu proceso. Bien hecho.",
]


class ActivacionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"
        self.actividades_propuestas = []
        self._energia_val = 5

        self.title("NeuroMood · Asistente de Activación")
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
            titulo="Asistente de Activación",
            subtitulo="Activación conductual — actividades adaptadas a tu energía",
            modo=self.modo,
            on_toggle_modo=self._toggle_modo
        )
        self.header.pack(fill="x")

        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=LAYOUT["padding_container"],
                       pady=LAYOUT["padding_container"])

        col_izq = ctk.CTkFrame(contenido, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=300)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_sliders(col_izq)
        self._construir_propuestas(col_izq)
        self._construir_historial(col_der)

        barra_inferior = ctk.CTkFrame(self, fg_color=colores["bg_secondary"], height=40, corner_radius=0)
        barra_inferior.pack(fill="x", side="bottom")
        barra_inferior.pack_propagate(False)

        BotonSecundario(
            barra_inferior, text="Acerca de", modo=self.modo, width=100, height=30,
            command=lambda: mostrar_acerca_de(self, self.modo)
        ).pack(side="right", padx=12, pady=5)

    def _construir_sliders(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            card, text="¿Cómo estás ahora?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 12), anchor="w")

        energia_frame = ctk.CTkFrame(card, fg_color="transparent")
        energia_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        ctk.CTkLabel(
            energia_frame, text="Energía:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"], width=80
        ).pack(side="left")

        ctk.CTkLabel(energia_frame, text="0", text_color=colores["text_tertiary"],
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side="left")

        ctk.CTkLabel(energia_frame, text="10", text_color=colores["text_tertiary"],
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side="right")

        self.slider_energia = ctk.CTkSlider(
            energia_frame, from_=0, to=10, number_of_steps=10,
            progress_color=colores["accent"],
            button_color=colores["accent"],
            button_hover_color=colores["accent_hover"],
            fg_color=colores["progress_track"],
            command=self._on_energia
        )
        self.slider_energia.set(self._energia_val)
        self.slider_energia.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_energia = ctk.CTkLabel(
            energia_frame, text=str(self._energia_val),
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            text_color=colores["accent"], width=30
        )
        self.lbl_energia.pack(side="right", padx=(8, 0))

        BotonPrimario(
            card, text="Proponé actividades", modo=self.modo,
            command=self._generar_propuestas
        ).pack(padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]), fill="x")

    def _construir_propuestas(self, parent):
        colores = COLORS[self.modo]

        self.card_propuestas = CardFrame(parent, modo=self.modo)
        self.card_propuestas.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.card_propuestas, text="Actividades sugeridas",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8), anchor="w")

        self.frame_propuestas = ctk.CTkScrollableFrame(
            self.card_propuestas, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_propuestas.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                                   pady=(0, LAYOUT["padding_card"]))

        if not self.actividades_propuestas:
            ctk.CTkLabel(
                self.frame_propuestas,
                text="Ajustá el nivel de energía\ny presioná el botón para ver sugerencias.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"],
                justify="center"
            ).pack(expand=True, pady=20)
        else:
            for actividad in self.actividades_propuestas:
                self._crear_card_actividad(actividad)

    def _crear_card_actividad(self, actividad: str):
        colores = COLORS[self.modo]

        frame = ctk.CTkFrame(
            self.frame_propuestas,
            fg_color=colores["bg_hover"],
            corner_radius=LAYOUT["radius_card"],
            border_color=colores["border"],
            border_width=LAYOUT["border_width"]
        )
        frame.pack(fill="x", pady=4)
        frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text=actividad,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_primary"],
            wraplength=380, justify="left", anchor="w"
        ).grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=(4, 12), pady=8, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Hecha", height=28, width=80,
            fg_color=colores["success"],
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            command=lambda a=actividad: self._registrar_resultado(a, "hecha")
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Intentada", height=28, width=80,
            fg_color=colores["warning"],
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            command=lambda a=actividad: self._registrar_resultado(a, "intentada")
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            btn_frame, text="No pude", height=28, width=80,
            fg_color=colores["error"],
            text_color=colores["text_on_accent"],
            corner_radius=LAYOUT["radius_button"],
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            command=lambda a=actividad: self._registrar_resultado(a, "no_pude")
        ).pack()

    def _construir_historial(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Historial de logros",
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
            "SELECT fecha, hora, actividad, resultado, energia, animo FROM activacion ORDER BY fecha DESC, hora DESC LIMIT 15"
        ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_historial, text="Sin actividades registradas",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        color_resultado = {
            "hecha": colores["success"],
            "intentada": colores["warning"],
            "no_pude": colores["error"],
        }
        texto_resultado = {
            "hecha": "✓ Hecha",
            "intentada": "~ Intentada",
            "no_pude": "✗ No pude",
        }

        for reg in registros:
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=2)

            color = color_resultado.get(reg["resultado"], colores["text_tertiary"])
            texto = texto_resultado.get(reg["resultado"], reg["resultado"])

            encabezado = ctk.CTkFrame(fila, fg_color="transparent")
            encabezado.pack(fill="x", padx=8, pady=(6, 2))

            ctk.CTkLabel(
                encabezado, text=texto,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
                text_color=color
            ).pack(side="left")

            ctk.CTkLabel(
                encabezado,
                text=f"{fecha_legible(reg['fecha'])} · Energía: {reg['energia']}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(side="right")

            lbl_act = ctk.CTkLabel(
                fila, text=reg["actividad"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_primary"],
                wraplength=240, justify="left", anchor="w"
            )
            lbl_act.pack(padx=8, pady=(0, 6), fill="x", anchor="w")
            _wrap_state = {"last": 0}
            def _on_fila_resize(e, _l=lbl_act, _s=_wrap_state):
                nw = max(1, e.width - 20)
                if nw != _s["last"]:
                    _s["last"] = nw
                    _l.configure(wraplength=nw)
            fila.bind("<Configure>", _on_fila_resize)

    def _on_energia(self, val):
        self._energia_val = max(0, int(round(val)))
        self.lbl_energia.configure(text=str(self._energia_val))

    def _generar_propuestas(self):
        if self._energia_val <= 3:
            pool = ACTIVIDADES_BAJA
        elif self._energia_val <= 6:
            pool = ACTIVIDADES_MEDIA
        else:
            pool = ACTIVIDADES_ALTA

        self.actividades_propuestas = random.sample(pool, min(3, len(pool)))
        self._refrescar_propuestas()

    def _refrescar_propuestas(self):
        for widget in self.frame_propuestas.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        if not self.actividades_propuestas:
            ctk.CTkLabel(
                self.frame_propuestas,
                text="Ajustá el nivel de energía\ny presioná el botón para ver sugerencias.",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"],
                justify="center"
            ).pack(expand=True, pady=20)
        else:
            for actividad in self.actividades_propuestas:
                self._crear_card_actividad(actividad)

    def _reproducir_resultado(self, resultado: str):
        if not SONIDO_DISPONIBLE:
            return
        try:
            sr = 44100
            if resultado == "hecha":
                # Acorde mayor breve — Do + Mi + Sol
                freqs, dur = [523.25, 659.25, 783.99], 0.22
            elif resultado == "intentada":
                # Intervalo neutro
                freqs, dur = [440.0, 523.25], 0.18
            else:
                # Nota grave corta
                freqs, dur = [311.13], 0.15
            t = np.linspace(0, dur, int(sr * dur), False)
            onda = sum(np.sin(2 * np.pi * f * t) * (0.2 / len(freqs)) for f in freqs)
            fade = int(sr * 0.02)
            onda[:fade] *= np.linspace(0, 1, fade)
            onda[-fade:] *= np.linspace(1, 0, fade)
            pcm = (onda * 32767).astype(np.int16)
            stereo = np.column_stack((pcm, pcm))
            pygame.sndarray.make_sound(stereo).play()
        except Exception:
            pass

    def _registrar_resultado(self, actividad: str, resultado: str):
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), self._energia_val, self._energia_val, actividad, resultado)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        self._reproducir_resultado(resultado)

        if actividad in self.actividades_propuestas:
            self.actividades_propuestas.remove(actividad)

        self._refrescar_propuestas()
        self._cargar_historial()

    def _toggle_modo(self):
        estado = self.state()
        self.modo = "light" if self.modo == "dark" else "dark"
        hwnd = _freeze_window(self)
        self._construir_ui()
        self.update_idletasks()
        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self, self.modo)
        if estado == "zoomed":
            self.state("zoomed")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = ActivacionApp()
    app.mainloop()
