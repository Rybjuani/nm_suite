"""pacientes.py — Vista detallada de paciente con tabs: Registros | Asignar | Banco | IA."""
import threading
import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, CATEGORY_COLORS
from shared.components import mostrar_mensaje


class DetallePaciente(ctk.CTkFrame):
    """Panel derecho del Hub: se monta cuando hay paciente seleccionado."""

    TABS = [
        ("registros",  "Registros"),
        ("asignar",    "Asignar"),
        ("banco",      "Banco"),
        ("ia",         "IA"),
    ]

    def __init__(self, master, modo: str, sb, paciente_id: str, paciente_nombre: str):
        super().__init__(master, fg_color="transparent")
        self._modo = modo
        self._sb = sb
        self._pid = paciente_id
        self._nombre = paciente_nombre
        self._datos_cache: dict = {}
        self._tab_actual = "registros"
        self._build()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]

        # Título
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(12, 0))
        ctk.CTkLabel(
            top, text=f"📋  {self._nombre}",
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
        ).pack(side="left")

        # Tab bar
        tab_bar = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=38, corner_radius=0)
        tab_bar.pack(fill="x", pady=(8, 0))
        tab_bar.pack_propagate(False)

        self._tab_btns: dict = {}
        for tid, label in self.TABS:
            btn = ctk.CTkButton(
                tab_bar, text=label, height=28, width=110,
                fg_color=c["accent"] if tid == self._tab_actual else "transparent",
                hover_color=c["accent"],
                text_color=c["text_on_accent"] if tid == self._tab_actual else c["text_secondary"],
                font=(font, TYPOGRAPHY["size_small"], "bold"),
                corner_radius=6,
                command=lambda t=tid: self._ir_tab(t),
            )
            btn.pack(side="left", padx=4, pady=5)
            self._tab_btns[tid] = btn

        # Contenido del tab
        self._tab_content = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_content.pack(fill="both", expand=True)
        self._cargar_tab("registros")

    def _ir_tab(self, tab_id: str):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        self._tab_actual = tab_id
        for tid, btn in self._tab_btns.items():
            if tid == tab_id:
                btn.configure(fg_color=c["accent"], text_color=c["text_on_accent"])
            else:
                btn.configure(fg_color="transparent", text_color=c["text_secondary"])
        self._cargar_tab(tab_id)

    def _cargar_tab(self, tab_id: str):
        for w in self._tab_content.winfo_children():
            w.destroy()
        getattr(self, f"_tab_{tab_id}")()

    # ── Tab: Registros ────────────────────────────────────────────────────────

    def _tab_registros(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]

        top = ctk.CTkFrame(self._tab_content, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(12, 4))

        ctk.CTkButton(
            top, text="↻ Cargar datos", height=30, width=130,
            fg_color=c["bg_surface"], hover_color=c["bg_elevated"],
            text_color=c["text_secondary"], border_width=1, border_color=c["border"],
            font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
            command=self._cargar_datos_paciente,
        ).pack(side="left")

        self._btn_pdf = ctk.CTkButton(
            top, text="⬇ Exportar PDF", height=30, width=130,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._exportar_pdf,
        )
        self._btn_pdf.pack(side="right")

        self._scroll_reg = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        self._scroll_reg.pack(fill="both", expand=True, padx=20, pady=(4, 12))

        if self._datos_cache:
            self._mostrar_registros(self._datos_cache)
        else:
            ctk.CTkLabel(
                self._scroll_reg, text="Presioná '↻ Cargar datos' para ver los registros.",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"],
            ).pack(pady=30)

    def _cargar_datos_paciente(self):
        if not self._sb or getattr(self, "_cargando_datos", False):
            return
        self._cargando_datos = True
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for w in self._scroll_reg.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._scroll_reg, text="Cargando...",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_tertiary"],
        ).pack(pady=30)

        def _fetch():
            datos = {}
            tablas = {
                "animo":     ("mood_records",          "fecha,hora,puntaje,nota",                       20),
                "resp":      ("breathing_sessions",    "fecha,hora,tecnica,duracion_minutos",            15),
                "pens":      ("thought_records",       "fecha,hora,emocion,intensidad,pensamiento",      15),
                "checklist": ("checklist_completions", "fecha,descripcion,categoria,origen",             30),
                "timer":     ("timer_sessions",        "fecha,hora,nombre,categoria,duracion_real",      15),
                "reclog":    ("reminder_logs",         "fecha,hora,mensaje,cerrado",                     15),
            }
            for clave, (tabla, campos, lim) in tablas.items():
                try:
                    res = (self._sb.table(tabla).select(campos)
                           .eq("patient_id", self._pid)
                           .order("fecha", desc=True).limit(lim).execute())
                    datos[clave] = res.data or []
                except Exception:
                    datos[clave] = []
            self._datos_cache = datos
            self._cargando_datos = False
            self.after(0, lambda: self._mostrar_registros(datos))

        threading.Thread(target=_fetch, daemon=True).start()

    def _mostrar_registros(self, datos: dict):
        for w in self._scroll_reg.winfo_children():
            w.destroy()
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        p = LAYOUT["padding_card"]

        def _card_seccion(titulo, filas, fila_fn):
            card = ctk.CTkFrame(self._scroll_reg, fg_color=c["bg_surface"],
                                corner_radius=LAYOUT["radius_card"])
            card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                card, text=titulo,
                font=(font, TYPOGRAPHY["size_small"], "bold"),
                text_color=c["accent"],
            ).pack(anchor="w", padx=p, pady=(p, 4))
            if not filas:
                ctk.CTkLabel(
                    card, text="Sin registros.",
                    font=(font, TYPOGRAPHY["size_caption"]),
                    text_color=c["text_tertiary"],
                ).pack(anchor="w", padx=p, pady=(0, p))
            else:
                for r in filas:
                    row = ctk.CTkFrame(card, fg_color=c["bg_elevated"], corner_radius=6)
                    row.pack(fill="x", padx=p, pady=1)
                    ctk.CTkLabel(
                        row, text=fila_fn(r),
                        font=(font, TYPOGRAPHY["size_caption"]),
                        text_color=c["text_secondary"], anchor="w",
                    ).pack(padx=8, pady=3, anchor="w")
                ctk.CTkLabel(card, text="").pack(pady=(0, 2))

        # Ánimo con promedio
        animo = datos.get("animo", [])
        puntajes = [r.get("puntaje") for r in animo if r.get("puntaje") is not None]
        prom_label = f"Promedio: {round(sum(puntajes)/len(puntajes),1)}/10  |  {len(animo)} registros" if puntajes else ""
        card_animo = ctk.CTkFrame(self._scroll_reg, fg_color=c["bg_surface"],
                                  corner_radius=LAYOUT["radius_card"])
        card_animo.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(card_animo, text="Registros de ánimo",
                     font=(font, TYPOGRAPHY["size_small"], "bold"),
                     text_color=c["accent"]).pack(anchor="w", padx=p, pady=(p, 2))
        if prom_label:
            ctk.CTkLabel(card_animo, text=prom_label,
                         font=(font, TYPOGRAPHY["size_body"]),
                         text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(0, 4))

        # Botón ver gráfico ánimo
        if animo:
            ctk.CTkButton(
                card_animo, text="Ver gráfico", height=26, width=100,
                fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
                text_color=c["text_secondary"],
                font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
                command=lambda: self._mostrar_grafico_animo(animo),
            ).pack(anchor="w", padx=p, pady=(0, 6))

        for r in animo:
            nota = (r.get("nota") or "")[:50]
            row = ctk.CTkFrame(card_animo, fg_color=c["bg_elevated"], corner_radius=6)
            row.pack(fill="x", padx=p, pady=1)
            ctk.CTkLabel(
                row,
                text=f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                     f"Ánimo: {r.get('puntaje','—')}  {nota}",
                font=(font, TYPOGRAPHY["size_caption"]),
                text_color=c["text_secondary"], anchor="w",
            ).pack(padx=8, pady=3, anchor="w")
        ctk.CTkLabel(card_animo, text="").pack(pady=(0, 2))

        _card_seccion("Sesiones de respiración", datos.get("resp", []),
                      lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                                f"{r.get('tecnica','?')}  ({r.get('duracion_minutos','?')} min)")
        _card_seccion("Registros TCC", datos.get("pens", []),
                      lambda r: f"{r.get('fecha','')[:10]}  —  {r.get('emocion','?')} "
                                f"(int.{r.get('intensidad','?')})  "
                                f"{(r.get('pensamiento') or '')[:60]}")
        _card_seccion("Sesiones de temporizador", datos.get("timer", []),
                      lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                                f"{(r.get('nombre') or 'Sin nombre')[:30]}  "
                                f"{(r.get('duracion_real') or 0) // 60} min")
        _card_seccion("Recordatorios disparados", datos.get("reclog", []),
                      lambda r: f"{r.get('fecha','')[:10]}  {r.get('hora','')[:5]}  —  "
                                f"{(r.get('mensaje') or '')[:60]}")

    def _mostrar_grafico_animo(self, registros: list):
        from hub.visualizacion import grafico_animo
        from shared.components import NMToplevel
        ventana = NMToplevel(self, modo=self._modo)
        ventana.title(f"Ánimo — {self._nombre}")
        ventana.geometry("620x340")
        g = grafico_animo(ventana, registros, self._modo)
        g.pack(fill="both", expand=True, padx=12, pady=12)

    def _exportar_pdf(self):
        if not self._datos_cache:
            mostrar_mensaje(self, "Sin datos",
                            "Cargá los datos del paciente primero.",
                            tipo="info", modo=self._modo)
            return
        self._btn_pdf.configure(state="disabled", text="Generando...")
        from hub.exportar import exportar_pdf
        exportar_pdf(
            self._nombre, self._pid, self._datos_cache,
            on_done=lambda ruta: self.after(0, lambda: self._pdf_ok(ruta)),
            on_error=lambda msg: self.after(0, lambda: self._pdf_error(msg)),
        )

    def _pdf_ok(self, ruta: str):
        self._btn_pdf.configure(state="normal", text="⬇ Exportar PDF")
        mostrar_mensaje(self, "PDF generado", f"Guardado en:\n{ruta}",
                        tipo="info", modo=self._modo)

    def _pdf_error(self, msg: str):
        self._btn_pdf.configure(state="normal", text="⬇ Exportar PDF")
        mostrar_mensaje(self, "Error PDF", msg, tipo="error", modo=self._modo)

    # ── Tab: Asignar ─────────────────────────────────────────────────────────

    def _tab_asignar(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]

        scroll = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        # ── Asignar tarea de rutina ───────────────────────────────────────────
        card_r = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                              corner_radius=LAYOUT["radius_card"])
        card_r.pack(fill="x", pady=(0, 12))
        p = LAYOUT["padding_card"]

        ctk.CTkLabel(card_r, text="Asignar tarea de rutina",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(p, 4))

        inner_r = ctk.CTkFrame(card_r, fg_color="transparent")
        inner_r.pack(fill="x", padx=p, pady=(0, p))

        self._entry_tarea = ctk.CTkEntry(
            inner_r, height=36, fg_color=c["bg_input"],
            text_color=c["text_primary"], border_color=c["border"],
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Descripción de la tarea...",
        )
        self._entry_tarea.pack(fill="x", pady=(0, 8))

        row_r = ctk.CTkFrame(inner_r, fg_color="transparent")
        row_r.pack(fill="x")

        ctk.CTkLabel(row_r, text="Sección:",
                     font=(font, TYPOGRAPHY["size_small"]),
                     text_color=c["text_secondary"]).pack(side="left")
        self._combo_sec = ctk.CTkComboBox(
            row_r, values=["manana", "tarde", "noche"], width=130, height=32,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], button_color=c["accent"],
            font=(font, TYPOGRAPHY["size_small"]),
        )
        self._combo_sec.pack(side="left", padx=12)

        ctk.CTkButton(
            row_r, text="Asignar tarea", height=32, width=120,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._asignar_tarea,
        ).pack(side="right")

        # ── Asignar recordatorio remoto ───────────────────────────────────────
        card_rec = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                                corner_radius=LAYOUT["radius_card"])
        card_rec.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card_rec, text="Enviar recordatorio remoto",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(p, 4))

        inner_rec = ctk.CTkFrame(card_rec, fg_color="transparent")
        inner_rec.pack(fill="x", padx=p, pady=(0, p))

        self._entry_rec_msg = ctk.CTkEntry(
            inner_rec, height=36, fg_color=c["bg_input"],
            text_color=c["text_primary"], border_color=c["border"],
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Mensaje del recordatorio...",
        )
        self._entry_rec_msg.pack(fill="x", pady=(0, 8))

        row_rec = ctk.CTkFrame(inner_rec, fg_color="transparent")
        row_rec.pack(fill="x")

        ctk.CTkLabel(row_rec, text="Hora (HH:MM):",
                     font=(font, TYPOGRAPHY["size_small"]),
                     text_color=c["text_secondary"]).pack(side="left")
        self._entry_rec_hora = ctk.CTkEntry(
            row_rec, width=80, height=32,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], font=(font, TYPOGRAPHY["size_body"]),
        )
        self._entry_rec_hora.pack(side="left", padx=12)

        ctk.CTkButton(
            row_rec, text="Enviar", height=32, width=100,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._asignar_recordatorio,
        ).pack(side="right")

    def _asignar_tarea(self):
        if not self._sb:
            return
        tarea = self._entry_tarea.get().strip()
        seccion = self._combo_sec.get()
        if not tarea:
            return
        try:
            self._sb.table("assigned_tasks").insert({
                "patient_id": self._pid,
                "descripcion": tarea,
                "seccion": seccion,
            }).execute()
            self._entry_tarea.delete(0, "end")
            mostrar_mensaje(self, "Asignada",
                            f"Tarea '{tarea}' asignada al paciente.",
                            tipo="info", modo=self._modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", str(e)[:100],
                            tipo="error", modo=self._modo)

    def _asignar_recordatorio(self):
        if not self._sb:
            return
        msg = self._entry_rec_msg.get().strip()
        hora = self._entry_rec_hora.get().strip()
        if not msg or not hora:
            return
        try:
            self._sb.table("assigned_reminders").insert({
                "patient_id": self._pid,
                "mensaje": msg,
                "hora": hora,
                "dias": "1,2,3,4,5,6,7",
            }).execute()
            self._entry_rec_msg.delete(0, "end")
            self._entry_rec_hora.delete(0, "end")
            mostrar_mensaje(self, "Enviado",
                            "Recordatorio enviado al paciente.",
                            tipo="info", modo=self._modo)
        except Exception as e:
            mostrar_mensaje(self, "Error", str(e)[:100],
                            tipo="error", modo=self._modo)

    # ── Tab: Banco de actividades ─────────────────────────────────────────────

    def _tab_banco(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        categorias = list(CATEGORY_COLORS.keys())
        p = LAYOUT["padding_card"]

        scroll = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(scroll, text="Banco de actividades conductuales",
                     font=(font, TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            scroll,
            text="Las actividades del banco se sincronizan al abrir la app del paciente.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        ).pack(anchor="w", pady=(0, 12))

        # Formulario nueva actividad
        form_card = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                                 corner_radius=LAYOUT["radius_card"])
        form_card.pack(fill="x", pady=(0, 12))

        inner = ctk.CTkFrame(form_card, fg_color="transparent")
        inner.pack(fill="x", padx=p, pady=p)

        ctk.CTkLabel(inner, text="Nueva actividad",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["accent"]).pack(anchor="w", pady=(0, 8))

        self._ent_act_nombre = ctk.CTkEntry(
            inner, height=34, fg_color=c["bg_input"],
            text_color=c["text_primary"], border_color=c["border"],
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Nombre de la actividad...",
        )
        self._ent_act_nombre.pack(fill="x", pady=(0, 6))

        self._ent_act_desc = ctk.CTkEntry(
            inner, height=34, fg_color=c["bg_input"],
            text_color=c["text_primary"], border_color=c["border"],
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Descripción breve (opcional)...",
        )
        self._ent_act_desc.pack(fill="x", pady=(0, 6))

        row_form = ctk.CTkFrame(inner, fg_color="transparent")
        row_form.pack(fill="x")

        ctk.CTkLabel(row_form, text="Categoría:",
                     font=(font, TYPOGRAPHY["size_small"]),
                     text_color=c["text_secondary"]).pack(side="left")
        self._cmb_cat = ctk.CTkComboBox(
            row_form, values=categorias, width=150, height=32,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], button_color=c["accent"],
            font=(font, TYPOGRAPHY["size_small"]),
        )
        self._cmb_cat.set(categorias[0])
        self._cmb_cat.pack(side="left", padx=10)

        ctk.CTkLabel(row_form, text="Ánimo:",
                     font=(font, TYPOGRAPHY["size_small"]),
                     text_color=c["text_secondary"]).pack(side="left")
        self._cmb_animo = ctk.CTkComboBox(
            row_form, values=["1-4 (bajo)", "4-7 (medio)", "7-10 (alto)"],
            width=130, height=32,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], button_color=c["accent"],
            font=(font, TYPOGRAPHY["size_small"]),
        )
        self._cmb_animo.set("4-7 (medio)")
        self._cmb_animo.pack(side="left", padx=10)

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8, 0))

        ctk.CTkButton(
            btn_row, text="✦ IA: completar descripción", height=30, width=200,
            fg_color=c["bg_elevated"], hover_color=c["violet"],
            text_color=c["text_secondary"], border_width=1, border_color=c["border"],
            font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
            command=self._ia_completar_actividad,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Agregar actividad", height=30, width=150,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._agregar_actividad,
        ).pack(side="right")

        # Lista de actividades existentes
        self._scroll_banco = ctk.CTkFrame(scroll, fg_color="transparent")
        self._scroll_banco.pack(fill="x")
        self._cargar_banco()

    def _cargar_banco(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for w in self._scroll_banco.winfo_children():
            w.destroy()

        if not self._sb:
            return
        try:
            res = self._sb.table("activity_bank").select(
                "id,nombre,descripcion,categoria,animo_min,animo_max,activa"
            ).order("categoria").execute()
            rows = res.data or []
        except Exception:
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._scroll_banco, text="El banco está vacío.",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"],
            ).pack(pady=20)
            return

        for r in rows:
            cat = r.get("categoria", "")
            cat_color = CATEGORY_COLORS.get(cat, c["accent"])
            row_frame = ctk.CTkFrame(
                self._scroll_banco, fg_color=c["bg_surface"],
                corner_radius=8, height=44,
            )
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            # Dot de categoría
            dot = ctk.CTkCanvas(row_frame, width=10, height=10,
                                bg=c["bg_surface"], highlightthickness=0)
            dot.pack(side="left", padx=(10, 4))
            dot.create_oval(1, 1, 9, 9, fill=cat_color, outline="")

            ctk.CTkLabel(
                row_frame,
                text=f"{r.get('nombre','')}  ·  [{cat}]  ·  "
                     f"ánimo {r.get('animo_min',0)}-{r.get('animo_max',10)}",
                font=(font, TYPOGRAPHY["size_small"]),
                text_color=c["text_primary"] if r.get("activa", True) else c["text_tertiary"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=4)

            ctk.CTkButton(
                row_frame, text="✕", width=28, height=28,
                fg_color="transparent", hover_color=c["error"],
                text_color=c["text_tertiary"],
                font=(font, TYPOGRAPHY["size_small"]), corner_radius=14,
                command=lambda rid=r["id"]: self._eliminar_actividad(rid),
            ).pack(side="right", padx=6)

    def _animo_rango(self, seleccion: str):
        if "bajo" in seleccion:
            return 1, 4
        elif "alto" in seleccion:
            return 7, 10
        return 4, 7

    def _agregar_actividad(self):
        if not self._sb:
            return
        nombre = self._ent_act_nombre.get().strip()
        if not nombre:
            return
        desc = self._ent_act_desc.get().strip()
        cat = self._cmb_cat.get()
        animo_min, animo_max = self._animo_rango(self._cmb_animo.get())
        try:
            self._sb.table("activity_bank").insert({
                "nombre": nombre,
                "descripcion": desc,
                "categoria": cat,
                "animo_min": animo_min,
                "animo_max": animo_max,
                "activa": True,
            }).execute()
            self._ent_act_nombre.delete(0, "end")
            self._ent_act_desc.delete(0, "end")
            self._cargar_banco()
        except Exception as e:
            mostrar_mensaje(self, "Error", str(e)[:100],
                            tipo="error", modo=self._modo)

    def _eliminar_actividad(self, rid: int):
        if not self._sb:
            return
        try:
            self._sb.table("activity_bank").delete().eq("id", rid).execute()
            self._cargar_banco()
        except Exception as e:
            mostrar_mensaje(self, "Error", str(e)[:100],
                            tipo="error", modo=self._modo)

    def _ia_completar_actividad(self):
        nombre = self._ent_act_nombre.get().strip()
        if not nombre:
            return
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        self._ent_act_desc.delete(0, "end")
        self._ent_act_desc.insert(0, "Generando con IA…")
        self._ent_act_desc.configure(text_color=c["text_tertiary"])

        from hub.ia_asistente import autocompletar_actividad
        autocompletar_actividad(
            nombre,
            on_result=lambda txt: self.after(0, lambda: self._ia_desc_ok(txt)),
            on_error=lambda msg: self.after(0, lambda: self._ia_desc_error(msg)),
        )

    def _ia_desc_ok(self, txt: str):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        self._ent_act_desc.delete(0, "end")
        self._ent_act_desc.insert(0, txt)
        self._ent_act_desc.configure(text_color=c["text_primary"])

    def _ia_desc_error(self, msg: str):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        self._ent_act_desc.delete(0, "end")
        self._ent_act_desc.configure(text_color=c["error"])

    # ── Tab: IA ───────────────────────────────────────────────────────────────

    def _tab_ia(self):
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]

        scroll = ctk.CTkScrollableFrame(
            self._tab_content, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(scroll, text="🤖  Asistente IA",
                     font=(font, TYPOGRAPHY["size_h3"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            scroll,
            text="El terapeuta revisa y aprueba cada sugerencia antes de aplicarla.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        ).pack(anchor="w", pady=(0, 12))

        # ── Resumen de evolución ──────────────────────────────────────────────
        card_res = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                                corner_radius=LAYOUT["radius_card"])
        card_res.pack(fill="x", pady=(0, 12))
        p = LAYOUT["padding_card"]

        ctk.CTkLabel(card_res, text="Resumen de evolución",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(p, 4))

        self._txt_resumen = ctk.CTkTextbox(
            card_res, height=90, fg_color=c["bg_input"],
            text_color=c["text_secondary"],
            border_color=c["border"], border_width=1, corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
            state="disabled",
        )
        self._txt_resumen.pack(fill="x", padx=p, pady=(0, 8))

        self._btn_resumen = ctk.CTkButton(
            card_res, text="Generar resumen", height=32, width=150,
            fg_color=c["violet"], hover_color=c["violet_hover"],
            text_color="#ffffff",
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._generar_resumen,
        )
        self._btn_resumen.pack(anchor="w", padx=p, pady=(0, p))

        # ── Sugerencias de acción ─────────────────────────────────────────────
        card_sug = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                                corner_radius=LAYOUT["radius_card"])
        card_sug.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card_sug, text="Sugerencias de acción",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(p, 4))

        self._frame_sugerencias = ctk.CTkFrame(card_sug, fg_color="transparent")
        self._frame_sugerencias.pack(fill="x", padx=p, pady=(0, 4))

        ctk.CTkLabel(
            self._frame_sugerencias, text="Presioná 'Generar sugerencias' para obtener acciones.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        ).pack(anchor="w")

        self._btn_sugerencias = ctk.CTkButton(
            card_sug, text="Generar sugerencias", height=32, width=170,
            fg_color=c["violet"], hover_color=c["violet_hover"],
            text_color="#ffffff",
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._generar_sugerencias,
        )
        self._btn_sugerencias.pack(anchor="w", padx=p, pady=(0, p))

        # ── Generar tarea personalizada ───────────────────────────────────────
        card_tarea = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                                  corner_radius=LAYOUT["radius_card"])
        card_tarea.pack(fill="x")

        ctk.CTkLabel(card_tarea, text="Generar tarea personalizada",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(anchor="w", padx=p, pady=(p, 4))

        self._ent_contexto = ctk.CTkEntry(
            card_tarea, height=34, fg_color=c["bg_input"],
            text_color=c["text_primary"], border_color=c["border"],
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Ej: paciente con ansiedad leve, mejoró en respiración...",
        )
        self._ent_contexto.pack(fill="x", padx=p, pady=(0, 8))

        row_tarea = ctk.CTkFrame(card_tarea, fg_color="transparent")
        row_tarea.pack(fill="x", padx=p, pady=(0, p))

        self._lbl_tarea_gen = ctk.CTkLabel(
            row_tarea, text="",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["accent"], wraplength=320, justify="left",
        )
        self._lbl_tarea_gen.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row_tarea, text="Generar", height=32, width=90,
            fg_color=c["violet"], hover_color=c["violet_hover"],
            text_color="#ffffff",
            font=(font, TYPOGRAPHY["size_small"], "bold"), corner_radius=6,
            command=self._generar_tarea,
        ).pack(side="right")

    def _generar_resumen(self):
        if not self._datos_cache:
            mostrar_mensaje(self, "Sin datos",
                            "Cargá los registros del paciente primero.",
                            tipo="info", modo=self._modo)
            return
        self._btn_resumen.configure(state="disabled", text="Generando…")
        self._txt_resumen.configure(state="normal")
        self._txt_resumen.delete("1.0", "end")
        self._txt_resumen.insert("1.0", "Consultando IA…")
        self._txt_resumen.configure(state="disabled")

        from hub.ia_asistente import resumir_evolucion
        resumir_evolucion(
            self._datos_cache, self._nombre,
            on_result=lambda txt: self.after(0, lambda: self._resumen_ok(txt)),
            on_error=lambda msg: self.after(0, lambda: self._resumen_error(msg)),
        )

    def _resumen_ok(self, txt: str):
        self._btn_resumen.configure(state="normal", text="Generar resumen")
        self._txt_resumen.configure(state="normal")
        self._txt_resumen.delete("1.0", "end")
        self._txt_resumen.insert("1.0", txt)
        self._txt_resumen.configure(state="disabled")

    def _resumen_error(self, msg: str):
        self._btn_resumen.configure(state="normal", text="Generar resumen")
        self._txt_resumen.configure(state="normal")
        self._txt_resumen.delete("1.0", "end")
        self._txt_resumen.insert("1.0", f"Error: {msg}")
        self._txt_resumen.configure(state="disabled")

    def _generar_sugerencias(self):
        if not self._datos_cache:
            mostrar_mensaje(self, "Sin datos",
                            "Cargá los registros del paciente primero.",
                            tipo="info", modo=self._modo)
            return
        self._btn_sugerencias.configure(state="disabled", text="Generando…")

        from hub.ia_asistente import sugerir_acciones
        sugerir_acciones(
            self._datos_cache, self._nombre,
            on_result=lambda txt: self.after(0, lambda: self._sugerencias_ok(txt)),
            on_error=lambda msg: self.after(0, lambda: self._sugerencias_error(msg)),
        )

    def _sugerencias_ok(self, txt: str):
        self._btn_sugerencias.configure(state="normal", text="Generar sugerencias")
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for w in self._frame_sugerencias.winfo_children():
            w.destroy()

        for linea in txt.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            fila = ctk.CTkFrame(self._frame_sugerencias, fg_color=c["bg_elevated"],
                                corner_radius=8)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(
                fila, text=linea,
                font=(font, TYPOGRAPHY["size_small"]),
                text_color=c["text_primary"], anchor="w", wraplength=380,
            ).pack(side="left", padx=8, pady=6, fill="x", expand=True)
            ctk.CTkButton(
                fila, text="Aplicar", width=70, height=26,
                fg_color=c["success"], hover_color="#0a7a5a",
                text_color="#ffffff",
                font=(font, TYPOGRAPHY["size_caption"], "bold"), corner_radius=6,
                command=lambda l=linea: self._aplicar_sugerencia(l),
            ).pack(side="right", padx=6)

    def _sugerencias_error(self, msg: str):
        self._btn_sugerencias.configure(state="normal", text="Generar sugerencias")
        c = COLORS.get(self._modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for w in self._frame_sugerencias.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._frame_sugerencias, text=f"Error: {msg}",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["error"],
        ).pack(anchor="w")

    def _aplicar_sugerencia(self, linea: str):
        mostrar_mensaje(self, "Sugerencia",
                        f"Sugerencia copiada al portapapeles:\n\n{linea}",
                        tipo="info", modo=self._modo)
        try:
            self.clipboard_clear()
            self.clipboard_append(linea)
        except Exception:
            pass

    def _generar_tarea(self):
        contexto = self._ent_contexto.get().strip()
        if not contexto:
            return
        self._lbl_tarea_gen.configure(text="Generando…")
        from hub.ia_asistente import generar_tarea
        generar_tarea(
            contexto,
            on_result=lambda txt: self.after(0, lambda: self._lbl_tarea_gen.configure(text=txt)),
            on_error=lambda msg: self.after(0, lambda: self._lbl_tarea_gen.configure(
                text=f"Error: {msg}")),
        )
