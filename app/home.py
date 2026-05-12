"""home.py — Vista Home con 7 cards adaptativas para la plataforma paciente."""
import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, get_gradient
from shared.components import interpolate_color


MODULES_CONFIG = [
    {"id": "animo",       "icon": "🎭", "title": "Ánimo",       "desc": "Registrá tu estado emocional"},
    {"id": "respiracion", "icon": "🌬️", "title": "Respirar",    "desc": "Ejercicios de respiración guiada"},
    {"id": "registro",    "icon": "📝", "title": "Registro",    "desc": "Pensamientos automáticos (TCC)"},
    {"id": "rutina",      "icon": "✅", "title": "Rutina",      "desc": "Tareas del día"},
    {"id": "actividades", "icon": "⚡", "title": "Actividades", "desc": "Sugerencias según tu ánimo"},
    {"id": "timer",       "icon": "⏱️", "title": "Timer",       "desc": "Temporizador de actividades"},
    {"id": "avisos",      "icon": "🔔", "title": "Avisos",      "desc": "Recordatorios personalizados"},
]


class HomeView(ctk.CTkFrame):
    def __init__(self, master, modo: str, on_module_open, get_status_fn=None):
        super().__init__(master, fg_color="transparent")
        self.modo = modo
        self._on_module_open = on_module_open
        self._get_status = get_status_fn or (lambda mid: "")
        self._cards = {}
        self._badge_refs = {}   # module_id -> (badge_container_frame, top_row)
        self._build()

    def _build(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=c["bg_surface"],
        )
        self._scroll.pack(fill="both", expand=True, padx=16, pady=16)

        self._scroll.columnconfigure(0, weight=1)
        self._scroll.columnconfigure(1, weight=1)
        self._scroll.columnconfigure(2, weight=1)

        for idx, mod in enumerate(MODULES_CONFIG):
            is_banner = (idx == len(MODULES_CONFIG) - 1 and len(MODULES_CONFIG) % 3 != 0)
            row = idx // 3
            col = idx % 3

            if is_banner:
                colspan = 3 - (len(MODULES_CONFIG) - 1) % 3 + 1
                card = self._create_card(mod, c, font, banner=True)
                card.grid(row=row, column=0, columnspan=3, sticky="nsew",
                          padx=6, pady=6)
            else:
                card = self._create_card(mod, c, font)
                card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

            self._cards[mod["id"]] = card

        for row_idx in range((len(MODULES_CONFIG) + 2) // 3):
            self._scroll.rowconfigure(row_idx, weight=1)

    def _create_card(self, mod, c, font, banner=False):
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=c["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_width=1,
            border_color=c["border"],
        )
        min_h = 80 if banner else 120
        card.configure(height=min_h)

        card.bind("<Enter>", lambda e, w=card: w.configure(
            border_color=c["accent"], fg_color=c.get("bg_elevated", c["bg_surface"])))
        card.bind("<Leave>", lambda e, w=card: w.configure(
            border_color=c["border"], fg_color=c["bg_surface"]))
        card.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)
        inner.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        # Dot de color del gradiente (posición en el gradiente según índice del módulo)
        module_idx = next((i for i, m in enumerate(MODULES_CONFIG) if m["id"] == mod["id"]), 0)
        t = module_idx / max(len(MODULES_CONFIG) - 1, 1)
        grad = get_gradient(self.modo)
        dot_color = interpolate_color(grad[0], grad[1], t)
        dot_canvas = ctk.CTkCanvas(
            top_row, width=10, height=10,
            bg=c["bg_surface"], highlightthickness=0,
        )
        dot_canvas.pack(side="left", padx=(0, 6))
        dot_canvas.create_oval(1, 1, 9, 9, fill=dot_color, outline="")
        dot_canvas.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        icon_lbl = ctk.CTkLabel(
            top_row, text=mod["icon"],
            font=(font, 22),
            text_color=c["text_primary"],
        )
        icon_lbl.pack(side="left")
        icon_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        # Badge de status — guardamos la top_row para poder recrearlo al refrescar
        self._badge_refs[mod["id"]] = top_row
        status = self._get_status(mod["id"])
        if status:
            self._render_badge(top_row, status, c, font)

        title_lbl = ctk.CTkLabel(
            inner, text=mod["title"],
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
            anchor="w",
        )
        title_lbl.pack(fill="x", pady=(6, 2))
        title_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        desc_lbl = ctk.CTkLabel(
            inner, text=mod["desc"],
            font=(font, TYPOGRAPHY["size_small"]),
            text_color=c["text_tertiary"],
            anchor="w",
        )
        desc_lbl.pack(fill="x")
        desc_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        return card

    def _render_badge(self, top_row, status: str, c: dict, font: str):
        badge = ctk.CTkFrame(
            top_row,
            fg_color=c.get("accent_glow", c["bg_elevated"]),
            corner_radius=8,
        )
        badge.pack(side="right", padx=(4, 0))
        ctk.CTkLabel(
            badge, text=status,
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["accent"],
        ).pack(padx=8, pady=3)

    def refresh_statuses(self):
        self.after(0, self._do_refresh_statuses)

    def _do_refresh_statuses(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for mod in MODULES_CONFIG:
            mid = mod["id"]
            top_row = self._badge_refs.get(mid)
            if top_row is None:
                continue
            for child in list(top_row.winfo_children()):
                if isinstance(child, ctk.CTkFrame):
                    child.destroy()
            status = self._get_status(mid)
            if status:
                self._render_badge(top_row, status, c, font)

    def set_modo(self, modo: str):
        self.modo = modo
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._cards.clear()
        self._build()
