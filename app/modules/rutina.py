"""rutina.py — Checklist de rutina diaria (Mañana / Tarde / Noche)."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion
from shared.utils import fecha_hoy


SECCIONES = [
    ("manana", "Mañana", "🌅"),
    ("tarde", "Tarde", "☀️"),
    ("noche", "Noche", "🌙"),
]


class ModuloRutina(NMModule):
    MODULE_TITLE = "Rutina"
    MODULE_ICON = "✅"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        self._scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # Badge summary
        self._badge_lbl = ctk.CTkLabel(
            self._scroll, text="",
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color=c["accent"],
        )
        self._badge_lbl.pack(anchor="w", pady=(0, 12))

        # Section containers
        self._section_frames = {}
        self._section_bodies = {}
        self._section_collapsed = {}
        self._task_vars = {}  # tarea_id -> BooleanVar

        for key, label, icon in SECCIONES:
            self._build_section(key, label, icon)

        self._load_tasks()
        self._build_nota_dia()

    def _build_section(self, key: str, label: str, icon: str):
        c, font = self._c, self._font
        self._section_collapsed[key] = False

        frame = ctk.CTkFrame(self._scroll, fg_color=c["bg_surface"], corner_radius=LAYOUT["radius_card"])
        frame.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))
        self._section_frames[key] = frame

        # Header (clickable to collapse)
        header = ctk.CTkFrame(frame, fg_color="transparent", height=44)
        header.pack(fill="x", padx=12, pady=(8, 0))
        header.pack_propagate(False)

        title_btn = ctk.CTkButton(
            header, text=f"{icon}  {label}", width=160, height=36,
            fg_color="transparent", hover_color=c["bg_elevated"],
            text_color=c["text_primary"], anchor="w",
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            command=lambda k=key: self._toggle_section(k),
        )
        title_btn.pack(side="left")

        # Count label
        count_lbl = ctk.CTkLabel(
            header, text="",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
        )
        count_lbl.pack(side="left", padx=8)

        # Add button
        add_btn = ctk.CTkButton(
            header, text="+", width=32, height=32,
            fg_color=c["bg_elevated"], hover_color=c["accent"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            corner_radius=16,
            command=lambda k=key: self._show_add_form(k),
        )
        add_btn.pack(side="right")

        # Progress bar de la sección (4px, debajo del header)
        prog = ctk.CTkProgressBar(
            frame, height=4,
            progress_color=c["accent"],
            fg_color=c["progress_track"],
            corner_radius=2,
        )
        prog.set(0)
        prog.pack(fill="x", padx=12, pady=(2, 0))

        # Body (task list)
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(4, 12))
        self._section_bodies[key] = body

        # Guardamos referencia a la progress bar por key
        if not hasattr(self, "_section_progs"):
            self._section_progs = {}
        self._section_progs[key] = prog

    def _toggle_section(self, key: str):
        collapsed = self._section_collapsed[key]
        if collapsed:
            self._section_bodies[key].pack(fill="x", padx=12, pady=(4, 12))
        else:
            self._section_bodies[key].pack_forget()
        self._section_collapsed[key] = not collapsed

    # ── Load tasks from DB ───────────────────────────────────
    def _load_tasks(self):
        c, font = self._c, self._font
        self._task_vars.clear()

        # Clear existing task widgets
        for key in self._section_bodies:
            for w in self._section_bodies[key].winfo_children():
                w.destroy()

        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()

            for key, _, _ in SECCIONES:
                tareas = conn.execute(
                    "SELECT id, descripcion FROM checklist_tareas WHERE seccion = ? ORDER BY orden",
                    (key,)
                ).fetchall()

                completadas = set()
                if tareas:
                    ids = [str(t["id"]) for t in tareas]
                    rows = conn.execute(
                        f"SELECT tarea_id FROM checklist_completadas "
                        f"WHERE fecha = ? AND tarea_id IN ({','.join('?' * len(ids))})",
                        [hoy] + [int(i) for i in ids],
                    ).fetchall()
                    completadas = {r["tarea_id"] for r in rows}

                body = self._section_bodies[key]
                for tarea in tareas:
                    tid = tarea["id"]
                    done = tid in completadas
                    var = ctk.BooleanVar(value=done)
                    self._task_vars[tid] = var

                    row_frame = ctk.CTkFrame(body, fg_color="transparent", height=36)
                    row_frame.pack(fill="x", pady=2)
                    row_frame.pack_propagate(False)

                    cb = ctk.CTkCheckBox(
                        row_frame, text=tarea["descripcion"],
                        variable=var,
                        font=(font, TYPOGRAPHY["size_body"]),
                        text_color=c["text_primary"] if not done else c["text_tertiary"],
                        fg_color=c["accent"],
                        hover_color=c["accent_hover"],
                        border_color=c["border"],
                        checkmark_color=c["text_on_accent"],
                        corner_radius=4,
                        command=lambda t=tid, v=var: self._on_check(t, v),
                    )
                    cb.pack(side="left", padx=4)

                # Show section count + progress bar
                header = self._section_frames[key].winfo_children()[0]
                count_lbl = header.winfo_children()[1]
                done_count = sum(1 for t in tareas if t["id"] in completadas)
                total = len(tareas)
                count_lbl.configure(text=f"{done_count}/{total}" if total > 0 else "")
                if hasattr(self, "_section_progs") and key in self._section_progs and total > 0:
                    self._section_progs[key].set(done_count / total)

            conn.close()
        except Exception:
            pass

        self._update_badge()

    def _on_check(self, tarea_id: int, var: ctk.BooleanVar):
        hoy = fecha_hoy()
        try:
            conn = obtener_conexion()
            if var.get():
                conn.execute(
                    "INSERT OR IGNORE INTO checklist_completadas (tarea_id, fecha) VALUES (?, ?)",
                    (tarea_id, hoy),
                )
                self._play_beep()
            else:
                conn.execute(
                    "DELETE FROM checklist_completadas WHERE tarea_id = ? AND fecha = ?",
                    (tarea_id, hoy),
                )
            conn.commit()
            conn.close()
        except Exception:
            pass
        self._update_badge()
        self._update_section_progress()

    def _play_beep(self):
        try:
            import winsound
            winsound.Beep(1200, 80)
        except Exception:
            pass

    def _update_badge(self):
        total = len(self._task_vars)
        done = sum(1 for v in self._task_vars.values() if v.get())
        if total > 0:
            self._badge_lbl.configure(text=f"{done}/{total} completadas")
        else:
            self._badge_lbl.configure(text="Sin tareas configuradas")

    def _update_section_progress(self):
        if not hasattr(self, "_section_progs"):
            return
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            for key, _, _ in SECCIONES:
                if key not in self._section_progs:
                    continue
                tareas = conn.execute(
                    "SELECT id FROM checklist_tareas WHERE seccion = ?", (key,)
                ).fetchall()
                total = len(tareas)
                if total == 0:
                    self._section_progs[key].set(0)
                    continue
                ids = [t["id"] for t in tareas]
                done = conn.execute(
                    f"SELECT COUNT(*) FROM checklist_completadas "
                    f"WHERE fecha = ? AND tarea_id IN ({','.join('?' * len(ids))})",
                    [hoy] + ids,
                ).fetchone()[0]
                self._section_progs[key].set(done / total)
            conn.close()
        except Exception:
            pass

    # ── Add task inline form ─────────────────────────────────
    def _show_add_form(self, seccion: str):
        c, font = self._c, self._font
        body = self._section_bodies[seccion]

        form = ctk.CTkFrame(body, fg_color=c["bg_elevated"], corner_radius=8)
        form.pack(fill="x", pady=(4, 4))

        entry = ctk.CTkEntry(
            form, height=34,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border_accent"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Nueva tarea...",
        )
        entry.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=8)
        entry.focus_set()

        btn_save = ctk.CTkButton(
            form, text="✓", width=34, height=34,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            corner_radius=6,
            command=lambda: self._add_task(seccion, entry.get(), form),
        )
        btn_save.pack(side="right", padx=(0, 8), pady=8)

        entry.bind("<Return>", lambda _: self._add_task(seccion, entry.get(), form))

    def _add_task(self, seccion: str, descripcion: str, form_widget):
        descripcion = descripcion.strip()
        if not descripcion:
            return
        try:
            conn = obtener_conexion()
            max_orden = conn.execute(
                "SELECT COALESCE(MAX(orden), 0) FROM checklist_tareas WHERE seccion = ?",
                (seccion,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO checklist_tareas (seccion, descripcion, orden) VALUES (?, ?, ?)",
                (seccion, descripcion, max_orden + 1),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        form_widget.destroy()
        self._load_tasks()

    def _build_nota_dia(self):
        c, font = self._c, self._font
        frame = ctk.CTkFrame(self._scroll, fg_color=c["bg_surface"], corner_radius=LAYOUT["radius_card"])
        frame.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        ctk.CTkLabel(
            frame, text="📓  Nota del día",
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color=c["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 4))

        self._nota_txt = ctk.CTkTextbox(
            frame, height=80,
            fg_color=c["bg_input"],
            text_color=c["text_primary"],
            border_color=c["border"],
            border_width=1,
            corner_radius=8,
            font=(font, TYPOGRAPHY["size_body"]),
        )
        self._nota_txt.pack(fill="x", padx=14, pady=(0, 4))
        self._nota_txt.bind("<FocusOut>", lambda _: self._guardar_nota())

        # Cargar nota guardada del día
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT nota FROM checklist_notas_dia WHERE fecha = ?", (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0]:
                self._nota_txt.insert("1.0", row[0])
        except Exception:
            pass

        ctk.CTkButton(
            frame, text="Guardar nota", width=110, height=32,
            fg_color=c["bg_elevated"], hover_color=c["accent"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_small"]),
            corner_radius=6,
            command=self._guardar_nota,
        ).pack(anchor="e", padx=14, pady=(0, 12))

    def _guardar_nota(self):
        nota = self._nota_txt.get("1.0", "end").strip()
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO checklist_notas_dia (fecha, nota) VALUES (?, ?) "
                "ON CONFLICT(fecha) DO UPDATE SET nota = excluded.nota",
                (fecha_hoy(), nota),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def on_enter(self):
        self._load_tasks()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            hoy = fecha_hoy()
            total = conn.execute("SELECT COUNT(*) FROM checklist_tareas").fetchone()[0]
            done = conn.execute(
                "SELECT COUNT(*) FROM checklist_completadas WHERE fecha = ?", (hoy,)
            ).fetchone()[0]
            conn.close()
            if total > 0:
                return f"{done}/{total} ✔"
        except Exception:
            pass
        return ""
