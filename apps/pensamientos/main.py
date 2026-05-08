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
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion, inicializar_tablas
from shared.components import (
    HeaderFrame, CardFrame, BotonPrimario, BotonSecundario,
    InputTexto, AreaTexto, mostrar_acerca_de, obtener_ruta_recurso, obtener_icono_solido,
    mostrar_mensaje, NMToplevel, aplicar_captionbar_flush, _freeze_window, _unfreeze_window
)
from shared.utils import fecha_hoy, hora_actual, fecha_legible


DISTORSIONES = [
    "Exagerar lo negativo",
    "Ver todo en extremos",
    "Anticipar lo peor",
    "Adivinar lo que otros piensan",
    "Ignorar lo bueno",
    "Exigirme demasiado",
    "Ponerme una etiqueta negativa",
    "Quedarme solo con lo malo",
]


class PensamientosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        inicializar_tablas()
        self.modo = "dark"
        self.paso_actual = 1
        self._filtro_buscar = ""

        self.title("NeuroMood · Registro de Pensamientos")
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
            titulo="Registro de Pensamientos",
            subtitulo="Identificá y cuestioná pensamientos automáticos",
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

        col_der = ctk.CTkFrame(contenido, fg_color="transparent", width=320)
        col_der.pack(side="right", fill="both", padx=(12, 0))

        self._construir_formulario(col_izq)
        self._construir_historial(col_der)

    def _construir_formulario(self, parent):
        colores = COLORS[self.modo]

        progress_frame = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        progress_frame.pack(fill="x", pady=(0, 8))
        progress_frame.pack_propagate(False)

        pasos = ["Situación", "Emoción", "Pensamiento", "Respuesta alternativa"]
        for i, paso in enumerate(pasos, 1):
            color = colores["accent"] if i <= self.paso_actual else colores["progress_track"]
            ctk.CTkFrame(
                progress_frame, fg_color=color, corner_radius=4,
                height=6, width=80
            ).pack(side="left", padx=2, pady=12, fill="x", expand=True)

        ctk.CTkLabel(
            parent, text=f"Paso {self.paso_actual} de 4",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 4))

        self.card_form = CardFrame(parent, modo=self.modo)
        self.card_form.pack(fill="both", expand=True)

        if self.paso_actual == 1:
            self._paso_situacion()
        elif self.paso_actual == 2:
            self._paso_emocion()
        elif self.paso_actual == 3:
            self._paso_pensamiento()
        elif self.paso_actual == 4:
            self._paso_respuesta()

    def _paso_situacion(self):
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            self.card_form, text="¿Qué estaba pasando?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        ctk.CTkLabel(
            self.card_form, text="Describí la situación que desencadenó el pensamiento",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 8))

        self.txt_situacion = AreaTexto(self.card_form, modo=self.modo, height=150)
        self.txt_situacion.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        if hasattr(self, '_datos') and self._datos.get("situacion"):
            self.txt_situacion.insert("1.0", self._datos["situacion"])

        btn_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        BotonPrimario(
            btn_frame, text="Siguiente →", modo=self.modo,
            command=self._siguiente_paso
        ).pack(side="right")

    def _paso_emocion(self):
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            self.card_form, text="¿Qué sentiste?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        ctk.CTkLabel(
            self.card_form, text="Nombrá la emoción que experimentaste",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 8))

        self.entry_emocion = InputTexto(self.card_form, modo=self.modo, placeholder_text="Ej: Ansiedad, tristeza, enojo...")
        self.entry_emocion.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 16))

        if hasattr(self, '_datos') and self._datos.get("emocion"):
            self.entry_emocion.insert(0, self._datos["emocion"])

        ctk.CTkLabel(
            self.card_form, text="Intensidad (0-10)",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w")

        slider_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        slider_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(4, 8))

        ctk.CTkLabel(slider_frame, text="0", text_color=colores["text_tertiary"],
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side="left")

        ctk.CTkLabel(slider_frame, text="10", text_color=colores["text_tertiary"],
                     font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"])).pack(side="right")

        self.intensidad_val = 5
        if hasattr(self, '_datos') and self._datos.get("intensidad"):
            self.intensidad_val = self._datos["intensidad"]

        self.slider_intensidad = ctk.CTkSlider(
            slider_frame, from_=0, to=10, number_of_steps=10,
            progress_color=colores["accent"],
            button_color=colores["accent"],
            button_hover_color=colores["accent_hover"],
            fg_color=colores["progress_track"],
            command=self._on_intensidad
        )
        self.slider_intensidad.set(self.intensidad_val)
        self.slider_intensidad.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_intensidad = ctk.CTkLabel(
            self.card_form, text=str(self.intensidad_val),
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=colores["accent"]
        )
        self.lbl_intensidad.pack(pady=(0, 12))

        ctk.CTkLabel(
            self.card_form, text="Distorsiones cognitivas detectadas:",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            text_color=colores["text_secondary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(8, 4))

        dist_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        dist_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        self.distorsion_vars = {}
        for i, dist in enumerate(DISTORSIONES):
            var = ctk.BooleanVar(value=False)
            if hasattr(self, '_datos') and dist in self._datos.get("distorsiones_list", []):
                var.set(True)
            self.distorsion_vars[dist] = var
            ctk.CTkCheckBox(
                dist_frame, text=dist, variable=var,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"],
                fg_color=colores["accent"],
                hover_color=colores["accent_hover"],
                border_color=colores["border"],
                checkmark_color=colores["text_on_accent"]
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=2)

        btn_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        BotonSecundario(
            btn_frame, text="← Anterior", modo=self.modo,
            command=self._paso_anterior
        ).pack(side="left")

        BotonPrimario(
            btn_frame, text="Siguiente →", modo=self.modo,
            command=self._siguiente_paso
        ).pack(side="right")

    def _paso_pensamiento(self):
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            self.card_form, text="¿Qué pensaste en ese momento?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        ctk.CTkLabel(
            self.card_form, text="El pensamiento automático que apareció",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 8))

        self.txt_pensamiento = AreaTexto(self.card_form, modo=self.modo, height=150)
        self.txt_pensamiento.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        if hasattr(self, '_datos') and self._datos.get("pensamiento"):
            self.txt_pensamiento.insert("1.0", self._datos["pensamiento"])

        btn_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        BotonSecundario(
            btn_frame, text="← Anterior", modo=self.modo,
            command=self._paso_anterior
        ).pack(side="left")

        BotonPrimario(
            btn_frame, text="Siguiente →", modo=self.modo,
            command=self._siguiente_paso
        ).pack(side="right")

    def _paso_respuesta(self):
        colores = COLORS[self.modo]

        ctk.CTkLabel(
            self.card_form, text="¿Hay otra manera de verlo?",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 4), anchor="w")

        ctk.CTkLabel(
            self.card_form, text="Intentá formular una respuesta alternativa más equilibrada",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(padx=LAYOUT["padding_card"], anchor="w", pady=(0, 8))

        self.txt_respuesta = AreaTexto(self.card_form, modo=self.modo, height=150)
        self.txt_respuesta.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, 12))

        if hasattr(self, '_datos') and self._datos.get("respuesta"):
            self.txt_respuesta.insert("1.0", self._datos["respuesta"])

        btn_frame = ctk.CTkFrame(self.card_form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(0, LAYOUT["padding_card"]))

        BotonSecundario(
            btn_frame, text="← Anterior", modo=self.modo,
            command=self._paso_anterior
        ).pack(side="left")

        BotonPrimario(
            btn_frame, text="Guardar registro", modo=self.modo,
            command=self._guardar
        ).pack(side="right")

    def _on_intensidad(self, val):
        self.intensidad_val = max(0, int(round(val)))
        self.lbl_intensidad.configure(text=str(self.intensidad_val))

    def _siguiente_paso(self):
        self._guardar_datos_paso()
        if self.paso_actual < 4:
            self.paso_actual += 1
            estado = self.state()
            hwnd = _freeze_window(self)
            self._construir_ui()
            self.update_idletasks()
            _unfreeze_window(hwnd)
            if estado == "zoomed":
                self.state("zoomed")

    def _paso_anterior(self):
        self._guardar_datos_paso()
        if self.paso_actual > 1:
            self.paso_actual -= 1
            estado = self.state()
            hwnd = _freeze_window(self)
            self._construir_ui()
            self.update_idletasks()
            _unfreeze_window(hwnd)
            if estado == "zoomed":
                self.state("zoomed")

    def _guardar_datos_paso(self):
        if not hasattr(self, '_datos'):
            self._datos = {}

        if self.paso_actual == 1 and hasattr(self, 'txt_situacion'):
            self._datos["situacion"] = self.txt_situacion.get("1.0", "end").strip()
        elif self.paso_actual == 2:
            if hasattr(self, 'entry_emocion'):
                self._datos["emocion"] = self.entry_emocion.get().strip()
            self._datos["intensidad"] = self.intensidad_val
            if hasattr(self, 'distorsion_vars'):
                self._datos["distorsiones_list"] = [d for d, v in self.distorsion_vars.items() if v.get()]
        elif self.paso_actual == 3 and hasattr(self, 'txt_pensamiento'):
            self._datos["pensamiento"] = self.txt_pensamiento.get("1.0", "end").strip()
        elif self.paso_actual == 4 and hasattr(self, 'txt_respuesta'):
            self._datos["respuesta"] = self.txt_respuesta.get("1.0", "end").strip()

    def _guardar(self):
        self._guardar_datos_paso()

        situacion = self._datos.get("situacion", "")
        emocion = self._datos.get("emocion", "")
        intensidad = self._datos.get("intensidad", 5)
        pensamiento = self._datos.get("pensamiento", "")
        respuesta = self._datos.get("respuesta", "")
        distorsiones = ",".join(self._datos.get("distorsiones_list", []))

        if not situacion or not emocion or not pensamiento:
            mostrar_mensaje(self, "Faltan datos", "Completá al menos la situación, emoción y pensamiento.", tipo="info", modo=self.modo)
            return

        try:
            conn = obtener_conexion()
            conn.execute(
                """INSERT INTO pensamientos (fecha, hora, situacion, emocion, intensidad, pensamiento, respuesta_alternativa, distorsiones)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (fecha_hoy(), hora_actual(), situacion, emocion, intensidad, pensamiento, respuesta, distorsiones)
            )
            conn.commit()
            conn.close()

            self._datos = {}
            self.paso_actual = 1
            estado = self.state()
            hwnd = _freeze_window(self)
            self._construir_ui()
            self.update_idletasks()
            _unfreeze_window(hwnd)
            if estado == "zoomed":
                self.state("zoomed")
        except Exception as e:
            mostrar_mensaje(self, "Error", f"No se pudo guardar.\n{e}", tipo="error", modo=self.modo)

    def _construir_historial(self, parent):
        colores = COLORS[self.modo]

        card = CardFrame(parent, modo=self.modo)
        card.pack(fill="both", expand=True)

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=LAYOUT["padding_card"], pady=(LAYOUT["padding_card"], 8))

        ctk.CTkLabel(
            header_frame, text="Historial",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=colores["text_primary"]
        ).pack(side="left")

        self.entry_buscar = InputTexto(
            header_frame, modo=self.modo, width=140,
            placeholder_text="Buscar..."
        )
        self.entry_buscar.pack(side="right")
        if self._filtro_buscar:
            self.entry_buscar.insert(0, self._filtro_buscar)
        self.entry_buscar.bind("<Return>", lambda e: self._buscar())
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._buscar())

        self.frame_historial = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=colores["bg_hover"],
            scrollbar_button_hover_color=colores["accent"]
        )
        self.frame_historial.pack(fill="both", expand=True, padx=LAYOUT["padding_card"],
                                  pady=(0, LAYOUT["padding_card"]))

        self._cargar_historial(self._filtro_buscar)

    def _cargar_historial(self, filtro: str = ""):
        for widget in self.frame_historial.winfo_children():
            widget.destroy()

        colores = COLORS[self.modo]
        conn = obtener_conexion()

        if filtro:
            registros = conn.execute(
                """SELECT fecha, hora, situacion, emocion, intensidad, pensamiento, respuesta_alternativa, distorsiones
                   FROM pensamientos
                   WHERE situacion LIKE ? OR emocion LIKE ? OR pensamiento LIKE ? OR fecha LIKE ?
                   ORDER BY fecha DESC, hora DESC LIMIT 20""",
                (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%", f"%{filtro}%")
            ).fetchall()
        else:
            registros = conn.execute(
                """SELECT fecha, hora, situacion, emocion, intensidad, pensamiento, respuesta_alternativa, distorsiones
                   FROM pensamientos ORDER BY fecha DESC, hora DESC LIMIT 20"""
            ).fetchall()
        conn.close()

        if not registros:
            ctk.CTkLabel(
                self.frame_historial, text="Sin registros",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_tertiary"]
            ).pack(pady=20)
            return

        for reg in registros:
            fila = ctk.CTkFrame(self.frame_historial, fg_color=colores["bg_hover"],
                                corner_radius=LAYOUT["radius_button"])
            fila.pack(fill="x", pady=3)

            ctk.CTkLabel(
                fila, text=f"{fecha_legible(reg['fecha'])} · {reg['hora'][:5]}",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                text_color=colores["text_tertiary"]
            ).pack(padx=12, pady=(8, 0), anchor="w")

            ctk.CTkLabel(
                fila, text=f"{reg['emocion']} ({reg['intensidad']}/10)",
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                text_color=colores["accent"]
            ).pack(padx=12, anchor="w")

            ctk.CTkLabel(
                fila, text=reg["situacion"][:120] + ("..." if len(reg["situacion"]) > 120 else ""),
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
                text_color=colores["text_secondary"],
                anchor="w", wraplength=280, justify="left"
            ).pack(fill="x", padx=12, pady=(0, 4), anchor="w")

            ctk.CTkButton(
                fila, text="Ver completo", width=90, height=24,
                fg_color="transparent",
                hover_color=colores["bg_hover"],
                text_color=colores["accent"],
                border_width=1,
                border_color=colores["accent"],
                corner_radius=LAYOUT["radius_button"],
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
                command=lambda r=dict(reg): self._mostrar_detalle(r)
            ).pack(side="right", padx=(0, 12), pady=(0, 8))

    def _mostrar_detalle(self, reg):
        colores = COLORS[self.modo]
        win = NMToplevel(self, modo=self.modo)
        win.title("Detalle del registro")
        _w, _h = 520, 560
        _sw = win.winfo_screenwidth()
        _sh = win.winfo_screenheight()
        _x = (_sw - _w) // 2
        _y = (_sh - _h) // 2
        win.geometry(f"{_w}x{_h}+{_x}+{_y}")
        win.configure(fg_color=colores["bg_primary"])
        win.grab_set()
        win.after(10, win.focus_force)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll,
            text=f"{reg.get('fecha', '')} · {str(reg.get('hora', ''))[:5]}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w", pady=(0, 8))

        dist_raw = reg.get("distorsiones", "") or ""
        dist_txt = ", ".join(d.strip() for d in dist_raw.split(",") if d.strip()) or "—"
        campos = [
            ("Emoción", f"{reg.get('emocion', '')}  ({reg.get('intensidad', '')}/10)"),
            ("Situación", reg.get("situacion", "")),
            ("Pensamiento", reg.get("pensamiento", "")),
            ("Respuesta alternativa", reg.get("respuesta_alternativa", "") or "—"),
            ("Distorsiones", dist_txt),
        ]
        for titulo, texto in campos:
            ctk.CTkLabel(
                scroll, text=titulo,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                text_color=colores["accent"]
            ).pack(anchor="w", pady=(8, 2))
            ctk.CTkLabel(
                scroll, text=texto,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                text_color=colores["text_primary"],
                wraplength=460, justify="left", anchor="w"
            ).pack(anchor="w", fill="x")

        BotonPrimario(
            win, text="Cerrar", modo=self.modo, width=100,
            command=win.destroy
        ).pack(pady=(0, 16))

    def _buscar(self):
        self._filtro_buscar = self.entry_buscar.get().strip()
        self._cargar_historial(self._filtro_buscar)

    def _toggle_modo(self):
        estado = self.state()
        self._guardar_datos_paso()
        self._filtro_buscar = self.entry_buscar.get().strip() if hasattr(self, 'entry_buscar') else ""
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
    app = PensamientosApp()
    app.mainloop()
