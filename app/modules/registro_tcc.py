"""registro_tcc.py — Registro de pensamientos TCC (wizard 4 pasos)."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual


_KWORDS = {
    "Catastrofización": ["siempre", "nunca", "todo", "nada", "horrible", "terrible", "insoportable"],
    "Lectura mental": ["seguro que piensa", "piensan que", "creen que", "deben pensar"],
    "Filtro mental": ["solo", "únicamente", "nada más"],
    "Etiquetado": ["soy un", "soy una", "es un", "es una"],
    "Debería": ["debería", "tendría que", "tengo que"],
    "Personalización": ["por mi culpa", "es culpa mía", "yo causé"],
    "Sobregeneralización": ["todos", "nadie", "siempre", "nunca", "cada vez"],
    "Descalificación": ["no cuenta", "fue suerte", "no importa"],
    "Pensamiento dicotómico": ["o todo o nada", "blanco o negro", "perfecto o fracaso"],
    "Magnificación": ["es lo peor", "arruiné", "destruí"],
}


class ModuloRegistroTCC(NMModule):
    MODULE_TITLE = "Registro TCC"
    MODULE_ICON = "📝"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font
        self._step = 0
        self._data = {"situacion": "", "emocion": "", "intensidad": 5,
                      "pensamiento": "", "distorsiones": "", "respuesta": ""}

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=32, pady=16)

        # Progress indicator — pills
        self._progress_frame = ctk.CTkFrame(self._content, fg_color="transparent", height=36)
        self._progress_frame.pack(fill="x", pady=(0, 16))
        self._progress_frame.pack_propagate(False)
        self._step_pills = []  # (pill_frame, inner_label)
        steps = ["Situación", "Emoción", "Pensamiento", "Respuesta"]
        for i, name in enumerate(steps):
            pill = ctk.CTkFrame(
                self._progress_frame,
                fg_color=c["border"],
                corner_radius=14,
            )
            pill.pack(side="left", padx=4)
            lbl = ctk.CTkLabel(
                pill, text=f"{i+1}  {name}",
                font=(font, TYPOGRAPHY["size_small"]),
                text_color=c["text_tertiary"],
            )
            lbl.pack(padx=10, pady=5)
            self._step_pills.append((pill, lbl))

        # Step container
        self._step_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frame.pack(fill="both", expand=True)

        # Navigation buttons
        nav = ctk.CTkFrame(self._content, fg_color="transparent")
        nav.pack(fill="x", pady=(12, 0))

        self._btn_prev = ctk.CTkButton(
            nav, text="← Anterior", width=110, height=38,
            fg_color=c["bg_surface"], hover_color=c["bg_elevated"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_body"]),
            corner_radius=LAYOUT["radius_button"],
            command=self._prev_step,
        )
        self._btn_prev.pack(side="left")

        self._btn_next = ctk.CTkButton(
            nav, text="Siguiente →", width=110, height=38,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            corner_radius=LAYOUT["radius_button"],
            command=self._next_step,
        )
        self._btn_next.pack(side="right")

        self._show_step()

    # ── Step rendering ───────────────────────────────────────
    def _clear_step(self):
        for w in self._step_frame.winfo_children():
            w.destroy()

    def _update_progress(self):
        c = self._c
        for i, (pill, lbl) in enumerate(self._step_pills):
            if i == self._step:
                pill.configure(fg_color=c["accent"])
                lbl.configure(text_color=c["text_on_accent"])
            elif i < self._step:
                pill.configure(fg_color=c["success"])
                lbl.configure(text_color="#ffffff")
            else:
                pill.configure(fg_color=c["border"])
                lbl.configure(text_color=c["text_tertiary"])

    def _show_step(self):
        self._clear_step()
        self._update_progress()
        c, font = self._c, self._font

        if self._step == 0:
            self._build_step_situacion()
        elif self._step == 1:
            self._build_step_emocion()
        elif self._step == 2:
            self._build_step_pensamiento()
        elif self._step == 3:
            self._build_step_respuesta()

        # Button states
        self._btn_prev.configure(state="normal" if self._step > 0 else "disabled")
        if self._step == 3:
            self._btn_next.configure(text="Guardar ✓")
        else:
            self._btn_next.configure(text="Siguiente →")

    def _build_step_situacion(self):
        c, font = self._c, self._font
        ctk.CTkLabel(
            self._step_frame, text="¿Qué pasó?",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self._step_frame, text="Describí brevemente la situación que desencadenó el malestar.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 12))

        self._txt_situacion = ctk.CTkTextbox(
            self._step_frame, height=120,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._txt_situacion.pack(fill="x", pady=(0, 8))
        self._txt_situacion.insert("1.0", self._data["situacion"])

    def _build_step_emocion(self):
        c, font = self._c, self._font
        ctk.CTkLabel(
            self._step_frame, text="¿Qué sentiste?",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            self._step_frame, text="Emoción principal",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        self._entry_emocion = ctk.CTkEntry(
            self._step_frame, height=38,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Ej: ansiedad, tristeza, enojo...",
        )
        self._entry_emocion.pack(fill="x", pady=(0, 16))
        if self._data["emocion"]:
            self._entry_emocion.insert(0, self._data["emocion"])

        ctk.CTkLabel(
            self._step_frame, text=f"Intensidad: {self._data['intensidad']}/10",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        self._slider_intensidad = ctk.CTkSlider(
            self._step_frame, from_=0, to=10, number_of_steps=10,
            width=300, height=20,
            progress_color=c["accent"],
            button_color=c["text_primary"],
            fg_color=c["bg_surface"],
            command=self._on_intensidad,
        )
        self._slider_intensidad.set(self._data["intensidad"])
        self._slider_intensidad.pack(pady=(0, 8))

        self._lbl_intensidad = ctk.CTkLabel(
            self._step_frame, text=f"{self._data['intensidad']}/10",
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["accent"],
        )
        self._lbl_intensidad.pack()

    def _build_step_pensamiento(self):
        c, font = self._c, self._font
        ctk.CTkLabel(
            self._step_frame, text="Pensamiento automático",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self._step_frame,
            text="¿Qué pensaste en ese momento? Escribí el pensamiento tal como vino.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 12))

        self._txt_pensamiento = ctk.CTkTextbox(
            self._step_frame, height=90,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._txt_pensamiento.pack(fill="x", pady=(0, 12))
        self._txt_pensamiento.insert("1.0", self._data["pensamiento"])
        self._txt_pensamiento.bind("<KeyRelease>", self._detect_distortions)

        # Distortion suggestions
        ctk.CTkLabel(
            self._step_frame, text="Posibles distorsiones detectadas:",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        ).pack(anchor="w", pady=(0, 4))

        self._distortion_frame = ctk.CTkFrame(self._step_frame, fg_color="transparent")
        self._distortion_frame.pack(fill="x")
        self._detect_distortions(None)

    def _build_step_respuesta(self):
        c, font = self._c, self._font
        ctk.CTkLabel(
            self._step_frame, text="Respuesta alternativa",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self._step_frame,
            text="¿Cómo podrías pensar de manera más equilibrada?",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 12))

        self._txt_respuesta = ctk.CTkTextbox(
            self._step_frame, height=120,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._txt_respuesta.pack(fill="x")
        self._txt_respuesta.insert("1.0", self._data["respuesta"])

    # ── Distortion detection ─────────────────────────────────
    def _detect_distortions(self, _event):
        text = ""
        try:
            text = self._txt_pensamiento.get("1.0", "end").strip().lower()
        except Exception:
            text = self._data.get("pensamiento", "").lower()

        found = []
        for distortion, keywords in _KWORDS.items():
            for kw in keywords:
                if kw in text:
                    found.append(distortion)
                    break

        for w in self._distortion_frame.winfo_children():
            w.destroy()

        c = self._c
        font = self._font
        if found:
            for d in found:
                badge = ctk.CTkLabel(
                    self._distortion_frame, text=f"  {d}  ",
                    font=(font, TYPOGRAPHY["size_small"]),
                    fg_color=c["bg_elevated"],
                    text_color=c["warning"],
                    corner_radius=12,
                )
                badge.pack(side="left", padx=2, pady=2)
        else:
            ctk.CTkLabel(
                self._distortion_frame, text="Ninguna detectada aún",
                font=(font, TYPOGRAPHY["size_small"]),
                text_color=c["text_tertiary"],
            ).pack(anchor="w")

        self._data["distorsiones"] = ", ".join(found)

    # ── Intensity slider ─────────────────────────────────────
    def _on_intensidad(self, value):
        v = int(round(value))
        self._data["intensidad"] = v
        try:
            self._lbl_intensidad.configure(text=f"{v}/10")
        except Exception:
            pass

    # ── Navigation ───────────────────────────────────────────
    def _save_current_step_data(self):
        if self._step == 0:
            self._data["situacion"] = self._txt_situacion.get("1.0", "end").strip()
        elif self._step == 1:
            self._data["emocion"] = self._entry_emocion.get().strip()
        elif self._step == 2:
            self._data["pensamiento"] = self._txt_pensamiento.get("1.0", "end").strip()
            self._detect_distortions(None)
        elif self._step == 3:
            self._data["respuesta"] = self._txt_respuesta.get("1.0", "end").strip()

    def _next_step(self):
        self._save_current_step_data()
        # Validar campo obligatorio del paso actual antes de avanzar
        campo_requerido = {
            0: ("situacion",  "Describí la situación para continuar."),
            1: ("emocion",    "Nombrá la emoción que sentiste."),
            2: ("pensamiento","Escribí el pensamiento automático."),
        }
        if self._step in campo_requerido:
            campo, hint = campo_requerido[self._step]
            if not self._data.get(campo, "").strip():
                self._btn_next.configure(text=hint)
                self.after(2200, lambda: self._btn_next.configure(
                    text="Guardar ✓" if self._step == 3 else "Siguiente →"))
                return
        if self._step == 3:
            self._guardar()
            return
        self._step += 1
        self._show_step()

    def _prev_step(self):
        self._save_current_step_data()
        if self._step > 0:
            self._step -= 1
            self._show_step()

    # ── Save to DB ───────────────────────────────────────────
    def _guardar(self):
        self._save_current_step_data()
        d = self._data
        if not d["situacion"] or not d["pensamiento"]:
            self._btn_next.configure(text="Completá los campos")
            self.after(2000, lambda: self._btn_next.configure(text="Guardar ✓"))
            return

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO pensamientos "
                "(fecha, hora, situacion, emocion, intensidad, pensamiento, "
                "respuesta_alternativa, distorsiones) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(),
                 d["situacion"], d["emocion"], d["intensidad"],
                 d["pensamiento"], d["respuesta"], d["distorsiones"]),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        # Show confirmation
        self._clear_step()
        c = self._c
        font = self._font
        ctk.CTkLabel(
            self._step_frame, text="✓",
            font=(font, 48), text_color=c["success"],
        ).pack(pady=(20, 8))
        ctk.CTkLabel(
            self._step_frame, text="Registro guardado",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(pady=(0, 8))
        ctk.CTkLabel(
            self._step_frame, text="Buen trabajo al identificar y cuestionar el pensamiento.",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack()

        # Reset after delay
        self.after(3000, self._reset)

    def _reset(self):
        self._step = 0
        self._data = {"situacion": "", "emocion": "", "intensidad": 5,
                      "pensamiento": "", "distorsiones": "", "respuesta": ""}
        self._show_step()
        self._btn_next.configure(text="Siguiente →")

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) as n FROM pensamientos WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                return f"{row[0]} registro{'s' if row[0] > 1 else ''} ✔"
        except Exception:
            pass
        return ""
