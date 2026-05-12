"""main.py — Hub Profesional NeuroMood (entry point terapeuta)."""
import sys
import os
import threading

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
from shared.components import ThemeManager, aplicar_captionbar, mostrar_mensaje
from shared.config import supabase_url, supabase_key

try:
    from supabase import create_client as _sb_create
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False


def _get_sb():
    if not _SUPABASE_OK:
        return None, "módulo supabase no instalado"
    url, key = supabase_url(), supabase_key()
    if not url or not key:
        return None, "credenciales no configuradas (.env)"
    try:
        return _sb_create(url, key), None
    except Exception as e:
        return None, str(e)[:60]


NAV_ITEMS = [
    {"id": "dashboard",  "icon": "📊", "label": "Dashboard"},
    {"id": "pacientes",  "icon": "👥", "label": "Pacientes"},
    {"id": "config",     "icon": "⚙️",  "label": "Config"},
]


class HubProfesional(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        ctk.set_appearance_mode("dark")
        self.tm = ThemeManager(self, self._modo)

        self.title("NeuroMood · Hub Profesional")
        self.geometry("1100x680")
        self.minsize(900, 560)
        c = COLORS[self._modo]
        self.configure(fg_color=c["bg_primary"])

        self._center(1100, 680)
        self._apply_icon()
        self.after(100, lambda: aplicar_captionbar(self, self._modo))

        self._sb = None
        self._pacientes: list = []
        self._paciente_id: str | None = None
        self._paciente_nombre: str = ""
        self._current_view = "dashboard"
        self._detalle_frame = None   # DetallePaciente activo

        self._build()
        self.after(300, self._init_connection)

    # ── Init ─────────────────────────────────────────────────────────────────

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_icon(self):
        try:
            icon = os.path.join(_base, "NM_icon.ico")
            if os.path.exists(icon):
                self.iconbitmap(icon)
        except Exception:
            pass

    def _init_connection(self):
        self._sb, motivo = _get_sb()
        c = COLORS[self._modo]
        if self._sb:
            self._lbl_status.configure(text="● Conectado",
                                       text_color=c["success"])
            self._cargar_pacientes()
        else:
            self._lbl_status.configure(text=f"● Sin conexión: {motivo}",
                                       text_color=c["error"])

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        c = COLORS[self._modo]
        font = TYPOGRAPHY["font_family"]

        # Header con separador
        header = ctk.CTkFrame(self, fg_color=c["bg_secondary"],
                              height=LAYOUT["header_height"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Hub Profesional",
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color=c["accent"],
        ).pack(side="left", padx=16)

        self._lbl_status = ctk.CTkLabel(
            header, text="Conectando…",
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"],
        )
        self._lbl_status.pack(side="left", padx=8)

        ctk.CTkButton(
            header, text="↻", width=34, height=34,
            fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
            text_color=c["text_secondary"],
            corner_radius=LAYOUT["radius_button"],
            font=(font, TYPOGRAPHY["size_body"]),
            command=self._reconnect,
        ).pack(side="right", padx=6)

        ctk.CTkButton(
            header, text="☀" if "dark" in self._modo else "☾",
            width=34, height=34,
            fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
            text_color=c["text_secondary"],
            corner_radius=LAYOUT["radius_button"],
            font=(font, TYPOGRAPHY["size_body"]),
            command=self._toggle_theme,
        ).pack(side="right", padx=(0, 2))

        ctk.CTkFrame(header, height=1, fg_color=c.get("border_card", c["border"]),
                     corner_radius=0).pack(fill="x", side="bottom")

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Nav lateral
        self._nav = ctk.CTkFrame(body, fg_color=c["bg_secondary"],
                                 width=180, corner_radius=0)
        self._nav.pack(side="left", fill="y")
        self._nav.pack_propagate(False)
        self._build_nav(c, font)

        # Content
        self._content = ctk.CTkFrame(body, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True)

        self._show_view("dashboard")

    def _build_nav(self, c, font):
        self._nav_btns: dict = {}

        # Logo/marca en la nav
        ctk.CTkLabel(
            self._nav, text="NeuroMood",
            font=(font, TYPOGRAPHY["size_small"], "bold"),
            text_color=c["accent"],
        ).pack(padx=16, pady=(16, 4), anchor="w")
        ctk.CTkLabel(
            self._nav, text="Hub Profesional",
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"],
        ).pack(padx=16, pady=(0, 12), anchor="w")
        ctk.CTkFrame(self._nav, height=1, fg_color=c.get("border_card", c["border"])).pack(
            fill="x", padx=12, pady=(0, 8))

        for item in NAV_ITEMS:
            is_active = item["id"] == "dashboard"
            btn = ctk.CTkButton(
                self._nav,
                text=f"  {item['icon']}  {item['label']}",
                anchor="w", height=40, width=160,
                fg_color=c["bg_elevated"] if is_active else "transparent",
                hover_color=c["bg_elevated"],
                text_color=c["text_primary"] if is_active else c["text_secondary"],
                corner_radius=LAYOUT["radius_button"],
                border_width=0,
                font=(font, TYPOGRAPHY["size_small"], "bold" if is_active else "normal"),
                command=lambda vid=item["id"]: self._show_view(vid),
            )
            btn.pack(padx=8, pady=2, fill="x")
            self._nav_btns[item["id"]] = btn

        ctk.CTkFrame(self._nav, fg_color=c.get("border_card", c["border"]), height=1).pack(
            fill="x", padx=12, pady=12)
        self._lbl_pac_sel = ctk.CTkLabel(
            self._nav, text="Sin paciente seleccionado",
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"], wraplength=150,
        )
        self._lbl_pac_sel.pack(padx=14, anchor="w")

    # ── Routing ──────────────────────────────────────────────────────────────

    def _show_view(self, view_id: str):
        c = COLORS[self._modo]
        self._current_view = view_id
        font = TYPOGRAPHY["font_family"]
        for vid, btn in self._nav_btns.items():
            if vid == view_id:
                btn.configure(fg_color=c["bg_elevated"],
                              text_color=c["text_primary"],
                              font=(font, TYPOGRAPHY["size_small"], "bold"))
            else:
                btn.configure(fg_color="transparent",
                              text_color=c["text_secondary"],
                              font=(font, TYPOGRAPHY["size_small"], "normal"))

        for w in self._content.winfo_children():
            w.destroy()
        self._detalle_frame = None

        {
            "dashboard": self._view_dashboard,
            "pacientes": self._view_pacientes,
            "config":    self._view_config,
        }.get(view_id, self._view_dashboard)()

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _view_dashboard(self):
        c = COLORS[self._modo]
        font = TYPOGRAPHY["font_family"]

        scroll = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            scroll,
            text=f"Dashboard  —  {len(self._pacientes)} paciente{'s' if len(self._pacientes) != 1 else ''}",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 16))

        if not self._pacientes:
            ctk.CTkLabel(
                scroll,
                text="Sin pacientes registrados.\nUsá la sección Pacientes para vincular.",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"], justify="center",
            ).pack(pady=30)
            return

        # Grid de cards
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        from shared.components import interpolate_color
        from shared.theme import get_gradient
        grad = get_gradient(self._modo)

        for i, p in enumerate(self._pacientes):
            nombre = p.get("patient_name") or p.get("patient_id", "—")
            pid = p.get("patient_id", "")
            t = (i % 3) / 2
            card_accent = interpolate_color(grad[0], grad[1], t)

            card = ctk.CTkFrame(
                grid, fg_color=c["bg_surface"],
                corner_radius=LAYOUT["radius_card"],
                border_width=1,
                border_color=c.get("border_card", c["border"]),
            )
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)

            # Barra de color superior
            top_bar = ctk.CTkCanvas(card, height=4, highlightthickness=0, bg=card_accent)
            top_bar.pack(fill="x")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True,
                       padx=LAYOUT["padding_card"] - 6, pady=10)

            ctk.CTkLabel(
                inner, text=nombre,
                font=(font, TYPOGRAPHY["size_body"], "bold"),
                text_color=c["text_primary"],
            ).pack(anchor="w")
            ctk.CTkLabel(
                inner, text=f"ID: {pid[:14]}…" if len(pid) > 14 else pid,
                font=(font, TYPOGRAPHY["size_caption"]),
                text_color=c["text_tertiary"],
            ).pack(anchor="w", pady=(2, 8))

            ctk.CTkButton(
                inner, text="Ver detalle", height=28, width=100,
                fg_color=c["accent"], hover_color=c["accent_hover"],
                text_color=c["text_on_accent"],
                font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
                command=lambda p_id=pid, p_n=nombre: self._abrir_detalle(p_id, p_n),
            ).pack(anchor="w")

    # ── Detalle paciente ──────────────────────────────────────────────────────

    def _abrir_detalle(self, pid: str, nombre: str):
        self._paciente_id = pid
        self._paciente_nombre = nombre
        self._lbl_pac_sel.configure(text=f"📋  {nombre}")

        for w in self._content.winfo_children():
            w.destroy()

        from hub.pacientes import DetallePaciente
        self._detalle_frame = DetallePaciente(
            self._content, self._modo, self._sb, pid, nombre,
        )
        self._detalle_frame.pack(fill="both", expand=True)

        # Marcar nav como ninguno activo (estamos en un sub-view)
        for btn in self._nav_btns.values():
            btn.configure(fg_color="transparent",
                          text_color=COLORS[self._modo]["text_secondary"])

    # ── Pacientes ─────────────────────────────────────────────────────────────

    def _view_pacientes(self):
        c = COLORS[self._modo]
        font = TYPOGRAPHY["font_family"]

        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=16)

        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            top, text="Pacientes vinculados",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            top, text="↻ Actualizar", height=32, width=120,
            fg_color=c["bg_surface"], hover_color=c["bg_elevated"],
            text_color=c["text_secondary"],
            border_width=1, border_color=c["border"],
            font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
            command=self._cargar_pacientes,
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(
            frame, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        scroll.pack(fill="both", expand=True)

        if not self._pacientes:
            ctk.CTkLabel(
                scroll, text="No hay pacientes vinculados.",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"],
            ).pack(pady=20)
            return

        for p in self._pacientes:
            nombre = p.get("patient_name") or "—"
            pid = p.get("patient_id", "")
            row = ctk.CTkFrame(scroll, fg_color=c["bg_surface"],
                               corner_radius=8, height=46)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=nombre,
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_primary"],
            ).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(
                row, text=pid[:16],
                font=(font, TYPOGRAPHY["size_caption"]),
                text_color=c["text_tertiary"],
            ).pack(side="left", padx=8)

            ctk.CTkButton(
                row, text="Ver detalle", height=28, width=100,
                fg_color=c["accent"], hover_color=c["accent_hover"],
                text_color=c["text_on_accent"],
                font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
                command=lambda p_id=pid, p_n=nombre: self._abrir_detalle(p_id, p_n),
            ).pack(side="right", padx=12, pady=8)

    # ── Config ────────────────────────────────────────────────────────────────

    def _view_config(self):
        c = COLORS[self._modo]
        font = TYPOGRAPHY["font_family"]

        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            frame, text="Configuración",
            font=(font, TYPOGRAPHY["size_h2"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 16))

        # Tema
        card_t = ctk.CTkFrame(frame, fg_color=c["bg_surface"], corner_radius=8)
        card_t.pack(fill="x", pady=(0, 8))
        inner_t = ctk.CTkFrame(card_t, fg_color="transparent")
        inner_t.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(inner_t, text="Tema visual",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(side="left")
        ctk.CTkButton(
            inner_t, text="Cambiar tema", height=30, width=120,
            fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
            text_color=c["text_secondary"],
            font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
            border_width=1, border_color=c["border"],
            command=self._toggle_theme,
        ).pack(side="right")

        # Info conexión
        card_c = ctk.CTkFrame(frame, fg_color=c["bg_surface"], corner_radius=8)
        card_c.pack(fill="x", pady=(0, 8))
        inner_c = ctk.CTkFrame(card_c, fg_color="transparent")
        inner_c.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(inner_c, text="Conexión Supabase",
                     font=(font, TYPOGRAPHY["size_body"], "bold"),
                     text_color=c["text_primary"]).pack(side="left")
        ctk.CTkButton(
            inner_c, text="Reconectar", height=30, width=110,
            fg_color=c["bg_elevated"], hover_color=c["bg_overlay"],
            text_color=c["text_secondary"],
            font=(font, TYPOGRAPHY["size_small"]), corner_radius=6,
            border_width=1, border_color=c["border"],
            command=self._reconnect,
        ).pack(side="right")

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _cargar_pacientes(self):
        if not self._sb:
            return

        def _fetch():
            try:
                res = (self._sb.table("patients")
                       .select("patient_id,patient_name")
                       .execute())
                pats = res.data or []
            except Exception:
                pats = []
            self.after(0, lambda: self._on_pacientes_loaded(pats))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_pacientes_loaded(self, pats: list):
        self._pacientes = pats
        if self._current_view == "dashboard":
            self._show_view("dashboard")
        elif self._current_view == "pacientes":
            self._show_view("pacientes")

    def _reconnect(self):
        self._sb, motivo = _get_sb()
        c = COLORS[self._modo]
        if self._sb:
            self._lbl_status.configure(text="● Conectado",
                                       text_color=c["success"])
            self._cargar_pacientes()
        else:
            self._lbl_status.configure(text=f"● Error: {motivo}",
                                       text_color=c["error"])

    def _toggle_theme(self):
        if "dark" in self._modo:
            self._modo = "light_hybrid"
            ctk.set_appearance_mode("light")
        else:
            self._modo = "dark_hybrid"
            ctk.set_appearance_mode("dark")
        c = COLORS[self._modo]
        self.configure(fg_color=c["bg_primary"])
        self.tm.switch_mode(self._modo)
        self.after(50, lambda: aplicar_captionbar(self, self._modo))
        self._rebuild_ui()

    def _rebuild_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self._nav_btns = {}
        self._build()
        self._show_view(self._current_view)


def main():
    app = HubProfesional()
    app.mainloop()


if __name__ == "__main__":
    main()
