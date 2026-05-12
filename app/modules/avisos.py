"""avisos.py — Gestión de recordatorios / avisos."""
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.db import obtener_conexion


DIAS_LABELS = ["L", "M", "X", "J", "V", "S", "D"]
DIAS_FULL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class ModuloAvisos(NMModule):
    MODULE_TITLE = "Avisos"
    MODULE_ICON = "🔔"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font

        # Top bar with "Nuevo" button
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(12, 0))

        ctk.CTkLabel(
            top, text="Tus recordatorios",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(side="left")

        self._btn_nuevo = ctk.CTkButton(
            top, text="+ Nuevo aviso", width=120, height=34,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"),
            corner_radius=LAYOUT["radius_button"],
            command=self._show_form,
        )
        self._btn_nuevo.pack(side="right")

        # Banner informativo sobre funcionamiento en background
        banner = ctk.CTkFrame(self, fg_color=c["bg_elevated"], corner_radius=8)
        banner.pack(fill="x", padx=24, pady=(8, 0))
        ctk.CTkLabel(
            banner,
            text="🔔  Los avisos funcionan aunque cierres la app — se minimiza a la bandeja del sistema.",
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["accent"],
            wraplength=460, justify="left",
        ).pack(padx=12, pady=8, anchor="w")

        # Form container (hidden by default)
        self._form_frame = ctk.CTkFrame(self, fg_color=c["bg_surface"], corner_radius=LAYOUT["radius_card"])
        self._form_visible = False

        # Scrollable list
        self._list = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        self._list.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        self._load_reminders()
        self._build_opciones()

    # ── Load reminders ───────────────────────────────────────
    def _load_reminders(self):
        c, font = self._c, self._font

        for w in self._list.winfo_children():
            w.destroy()

        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT id, hora, mensaje, dias, activo FROM recordatorios ORDER BY hora"
            ).fetchall()
            conn.close()
        except Exception:
            rows = []

        if not rows:
            ctk.CTkLabel(
                self._list, text="No hay avisos configurados",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"],
            ).pack(pady=40)
            return

        for row in rows:
            self._build_reminder_card(row)

    def _build_reminder_card(self, row):
        c, font = self._c, self._font
        rec_id = row["id"]
        activo = bool(row["activo"])

        card = ctk.CTkFrame(self._list, fg_color=c["bg_surface"],
                            corner_radius=LAYOUT["radius_card"],
                            border_width=1, border_color=c.get("border_card", c["border"]))
        card.pack(fill="x", pady=(0, LAYOUT["gap_elements"]))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        # Top row: hora + toggle
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row, text=row["hora"],
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"] if activo else c["text_tertiary"],
        ).pack(side="left")

        # Active toggle
        toggle_var = ctk.BooleanVar(value=activo)
        toggle = ctk.CTkSwitch(
            top_row, text="",
            variable=toggle_var,
            width=44, height=22,
            fg_color=c["bg_elevated"],
            progress_color=c["accent"],
            button_color=c["text_primary"],
            command=lambda rid=rec_id, v=toggle_var: self._toggle_active(rid, v),
        )
        toggle.pack(side="right")

        # Delete button
        btn_del = ctk.CTkButton(
            top_row, text="✕", width=28, height=28,
            fg_color="transparent", hover_color=c["error"],
            text_color=c["text_tertiary"],
            font=(font, TYPOGRAPHY["size_small"]),
            corner_radius=14,
            command=lambda rid=rec_id, cd=card: self._delete_reminder(rid, cd),
        )
        btn_del.pack(side="right", padx=(0, 8))

        # Message
        ctk.CTkLabel(
            inner, text=row["mensaje"],
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_primary"] if activo else c["text_tertiary"],
            wraplength=280, justify="left", anchor="w",
        ).pack(fill="x", pady=(6, 4))

        # Days display
        dias_str = row["dias"] if row["dias"] else "1,2,3,4,5,6,7"
        dias_activos = set(dias_str.split(","))
        days_frame = ctk.CTkFrame(inner, fg_color="transparent")
        days_frame.pack(anchor="w")

        for i, lbl in enumerate(DIAS_LABELS, start=1):
            is_active = str(i) in dias_activos
            day_lbl = ctk.CTkLabel(
                days_frame, text=lbl, width=24, height=24,
                font=(font, TYPOGRAPHY["size_caption"], "bold"),
                fg_color=c["accent"] if is_active else c["bg_elevated"],
                text_color=c["text_on_accent"] if is_active else c["text_tertiary"],
                corner_radius=12,
            )
            day_lbl.pack(side="left", padx=1)

    # ── Toggle active ────────────────────────────────────────
    def _toggle_active(self, rec_id: int, var: ctk.BooleanVar):
        try:
            conn = obtener_conexion()
            conn.execute(
                "UPDATE recordatorios SET activo = ? WHERE id = ?",
                (1 if var.get() else 0, rec_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Delete reminder ──────────────────────────────────────
    def _delete_reminder(self, rec_id: int, card_widget):
        try:
            conn = obtener_conexion()
            conn.execute("DELETE FROM recordatorios WHERE id = ?", (rec_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        card_widget.destroy()

    # ── New reminder form ────────────────────────────────────
    def _show_form(self):
        if self._form_visible:
            self._hide_form()
            return

        c, font = self._c, self._font
        self._form_visible = True
        self._form_frame.pack(fill="x", padx=24, pady=(8, 0), before=self._list)

        # Clear previous form contents
        for w in self._form_frame.winfo_children():
            w.destroy()

        inner = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        # Hour input
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row1, text="Hora:",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self._entry_hora = ctk.CTkEntry(
            row1, width=70, height=34,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="HH:MM",
        )
        self._entry_hora.pack(side="left")

        # Days checkboxes
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row2, text="Días:",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self._day_vars = []
        for i, lbl in enumerate(DIAS_LABELS):
            var = ctk.BooleanVar(value=True)
            self._day_vars.append(var)
            cb = ctk.CTkCheckBox(
                row2, text=lbl, variable=var,
                width=36, height=24,
                font=(font, TYPOGRAPHY["size_caption"]),
                fg_color=c["accent"],
                hover_color=c["accent_hover"],
                border_color=c["border"],
                checkmark_color=c["text_on_accent"],
                text_color=c["text_primary"],
                corner_radius=4,
            )
            cb.pack(side="left", padx=2)

        # Message
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row3, text="Mensaje:",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        self._entry_mensaje = ctk.CTkEntry(
            row3, height=34,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_body"]),
            placeholder_text="Ej: Tomar medicación",
        )
        self._entry_mensaje.pack(fill="x")

        # Buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_row, text="Cancelar", width=90, height=34,
            fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_small"]),
            corner_radius=6,
            command=self._hide_form,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Guardar", width=90, height=34,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"],
            font=(font, TYPOGRAPHY["size_small"], "bold"),
            corner_radius=6,
            command=self._save_reminder,
        ).pack(side="left")

    def _hide_form(self):
        self._form_visible = False
        self._form_frame.pack_forget()
        for w in self._form_frame.winfo_children():
            w.destroy()

    def _save_reminder(self):
        hora = self._entry_hora.get().strip()
        mensaje = self._entry_mensaje.get().strip()

        # Validate hour format
        if not hora or not mensaje:
            return
        if ":" not in hora:
            return
        parts = hora.split(":")
        try:
            h, m = int(parts[0]), int(parts[1])
            if h < 0 or h > 23 or m < 0 or m > 59:
                return
            hora = f"{h:02d}:{m:02d}"
        except (ValueError, IndexError):
            return

        # Build days string
        dias = ",".join(str(i + 1) for i, v in enumerate(self._day_vars) if v.get())
        if not dias:
            dias = "1,2,3,4,5,6,7"

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO recordatorios (hora, mensaje, dias, activo) VALUES (?, ?, ?, 1)",
                (hora, mensaje, dias),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        self._hide_form()
        self._load_reminders()

    # ── Opciones del sistema ─────────────────────────────────
    def _build_opciones(self):
        c, font = self._c, self._font

        frame = ctk.CTkFrame(self, fg_color=c["bg_surface"], corner_radius=LAYOUT["radius_card"])
        frame.pack(fill="x", padx=24, pady=(0, 16))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="Opciones",
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color=c["text_secondary"],
        ).pack(anchor="w", pady=(0, 8))

        # Horario de silencio
        sil_row = ctk.CTkFrame(inner, fg_color="transparent")
        sil_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            sil_row, text="🔕  Silencio:",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_primary"],
        ).pack(side="left", padx=(0, 8))

        sil_ini, sil_fin = self._leer_silencio()

        self._entry_sil_ini = ctk.CTkEntry(
            sil_row, width=62, height=30,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_small"]),
            placeholder_text="22:00",
        )
        self._entry_sil_ini.pack(side="left", padx=(0, 4))
        if sil_ini:
            self._entry_sil_ini.insert(0, sil_ini)

        ctk.CTkLabel(sil_row, text="→", font=(font, TYPOGRAPHY["size_small"]),
                     text_color=c["text_tertiary"]).pack(side="left", padx=2)

        self._entry_sil_fin = ctk.CTkEntry(
            sil_row, width=62, height=30,
            fg_color=c["bg_input"], text_color=c["text_primary"],
            border_color=c["border"], border_width=1, corner_radius=6,
            font=(font, TYPOGRAPHY["size_small"]),
            placeholder_text="08:00",
        )
        self._entry_sil_fin.pack(side="left", padx=(0, 8))
        if sil_fin:
            self._entry_sil_fin.insert(0, sil_fin)

        ctk.CTkButton(
            sil_row, text="Aplicar", width=68, height=30,
            fg_color=c["bg_elevated"], hover_color=c["accent"],
            text_color=c["text_primary"],
            font=(font, TYPOGRAPHY["size_small"]),
            corner_radius=6,
            command=self._guardar_silencio,
        ).pack(side="left")

        # Arranque con Windows
        win_row = ctk.CTkFrame(inner, fg_color="transparent")
        win_row.pack(fill="x")

        ctk.CTkLabel(
            win_row, text="🪟  Iniciar con Windows",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_primary"],
        ).pack(side="left")

        autostart_var = ctk.BooleanVar(value=self._get_autostart())
        ctk.CTkSwitch(
            win_row, text="", variable=autostart_var,
            width=44, height=22,
            fg_color=c["bg_elevated"],
            progress_color=c["accent"],
            button_color=c["text_primary"],
            command=lambda: self._set_autostart(autostart_var.get()),
        ).pack(side="right")

    def _leer_silencio(self):
        try:
            conn = obtener_conexion()
            ini = conn.execute("SELECT valor FROM config WHERE clave='silencio_inicio'").fetchone()
            fin = conn.execute("SELECT valor FROM config WHERE clave='silencio_fin'").fetchone()
            conn.close()
            return (
                (ini[0] if isinstance(ini, tuple) else ini["valor"]) if ini else "",
                (fin[0] if isinstance(fin, tuple) else fin["valor"]) if fin else "",
            )
        except Exception:
            return "", ""

    def _guardar_silencio(self):
        ini = self._entry_sil_ini.get().strip()
        fin = self._entry_sil_fin.get().strip()
        for val in (ini, fin):
            if val and (":" not in val):
                return
        try:
            conn = obtener_conexion()
            for clave, valor in (("silencio_inicio", ini), ("silencio_fin", fin)):
                if valor:
                    conn.execute(
                        "INSERT INTO config (clave, valor) VALUES (?, ?) "
                        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
                        (clave, valor),
                    )
                else:
                    conn.execute("DELETE FROM config WHERE clave=?", (clave,))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _get_autostart(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, "NeuroMood")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _set_autostart(self, activar: bool):
        try:
            import winreg, sys
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE,
            )
            if activar:
                exe = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
                winreg.SetValueEx(key, "NeuroMood", 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, "NeuroMood")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def on_enter(self):
        self._load_reminders()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM recordatorios WHERE activo = 1"
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                return f"{row[0]} activo{'s' if row[0] > 1 else ''}"
        except Exception:
            pass
        return ""
