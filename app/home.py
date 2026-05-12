"""home.py — Vista Home con 7 cards adaptativas para la plataforma paciente."""
import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, get_gradient
from shared.components import interpolate_color


MODULES_CONFIG = [
    {"id": "animo",       "icon": "🎭", "title": "Ánimo",
     "desc": "Registrá tu estado emocional · 1 min"},
    {"id": "respiracion", "icon": "🌬️", "title": "Respirar",
     "desc": "Respiración guiada 4-7-8 · 3/5/10 min"},
    {"id": "registro",    "icon": "📝", "title": "Registro TCC",
     "desc": "Pensamientos automáticos · 4 pasos"},
    {"id": "rutina",      "icon": "✅", "title": "Rutina",
     "desc": "Tareas del día · Mañana/Tarde/Noche"},
    {"id": "actividades", "icon": "⚡", "title": "Actividades",
     "desc": "Sugerencias según tu ánimo actual"},
    {"id": "timer",       "icon": "⏱️", "title": "Timer",
     "desc": "Temporizador de actividades"},
    {"id": "avisos",      "icon": "🔔", "title": "Avisos",
     "desc": "Recordatorios · funcionan en background"},
]

# Colores de acento por módulo (escala gradiente teal→violeta)
def _dot_color(idx: int, modo: str) -> str:
    grad = get_gradient(modo)
    t = idx / max(len(MODULES_CONFIG) - 1, 1)
    return interpolate_color(grad[0], grad[1], t)


class HomeView(ctk.CTkFrame):
    def __init__(self, master, modo: str, on_module_open, get_status_fn=None):
        super().__init__(master, fg_color="transparent")
        self.modo = modo
        self._on_module_open = on_module_open
        self._get_status = get_status_fn or (lambda mid: "")
        self._cards = {}
        self._badge_refs = {}
        self._build()

    def _build(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        gap = LAYOUT["gap_cards"]

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
            scrollbar_button_hover_color=c["accent"],
        )
        self._scroll.pack(fill="both", expand=True, padx=14, pady=14)

        self._scroll.columnconfigure(0, weight=1)
        self._scroll.columnconfigure(1, weight=1)
        self._scroll.columnconfigure(2, weight=1)

        for idx, mod in enumerate(MODULES_CONFIG):
            is_banner = (idx == len(MODULES_CONFIG) - 1 and len(MODULES_CONFIG) % 3 != 0)
            row = idx // 3
            col = idx % 3
            card = self._create_card(mod, c, font, idx, banner=is_banner)
            if is_banner:
                card.grid(row=row, column=0, columnspan=3, sticky="nsew",
                          padx=5, pady=5)
            else:
                card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            self._cards[mod["id"]] = card

        for row_idx in range((len(MODULES_CONFIG) + 2) // 3):
            self._scroll.rowconfigure(row_idx, weight=1)

    def _create_card(self, mod, c, font, idx: int, banner=False):
        dot_c = _dot_color(idx, self.modo)

        # Card con borde_card sutil y radius más generoso
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=c["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_width=1,
            border_color=c.get("border_card", c["border"]),
        )
        min_h = 76 if banner else 116
        card.configure(height=min_h)

        # Hover: borde accent + fondo elevado
        card.bind("<Enter>", lambda e, w=card, dc=dot_c: w.configure(
            border_color=dc,
            border_width=2,
            fg_color=c["bg_elevated"]))
        card.bind("<Leave>", lambda e, w=card: w.configure(
            border_color=c.get("border_card", c["border"]),
            border_width=1,
            fg_color=c["bg_surface"]))
        card.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True,
                   padx=LAYOUT["padding_card"] - 4,
                   pady=10)
        inner.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        # Barra de color vertical izquierda (3 px, color del gradiente)
        accent_bar = ctk.CTkCanvas(
            card, width=4, highlightthickness=0, bg=dot_c,
        )
        accent_bar.place(x=0, y=0, relheight=1.0)
        accent_bar.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        # Icono emoji — usa token size_emoji_sm
        icon_lbl = ctk.CTkLabel(
            top_row, text=mod["icon"],
            font=(font, TYPOGRAPHY["size_emoji_sm"]),
            text_color=c["text_primary"],
        )
        icon_lbl.pack(side="left", padx=(8, 4))
        icon_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        # Badge de status
        self._badge_refs[mod["id"]] = top_row
        status = self._get_status(mod["id"])
        if status:
            self._render_badge(top_row, status, c, font, dot_c)

        title_lbl = ctk.CTkLabel(
            inner, text=mod["title"],
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
            anchor="w",
        )
        title_lbl.pack(fill="x", pady=(6, 1), padx=(8, 0))
        title_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        desc_lbl = ctk.CTkLabel(
            inner, text=mod["desc"],
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=c["text_tertiary"],
            anchor="w",
        )
        desc_lbl.pack(fill="x", padx=(8, 0))
        desc_lbl.bind("<Button-1>", lambda e, mid=mod["id"]: self._on_module_open(mid))

        return card

    def _render_badge(self, top_row, status: str, c: dict, font: str,
                      dot_color: str = None):
        accent = dot_color or c["accent"]
        bg = interpolate_color(accent, c["bg_surface"], 0.75) if dot_color else c.get("accent_glow", c["bg_elevated"])
        badge = ctk.CTkFrame(
            top_row,
            fg_color=bg,
            corner_radius=LAYOUT["radius_badge"],
        )
        badge.pack(side="right", padx=(4, 0))
        ctk.CTkLabel(
            badge, text=status,
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=accent,
        ).pack(padx=8, pady=3)

    def refresh_statuses(self):
        self.after(0, self._do_refresh_statuses)

    def _do_refresh_statuses(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        for idx, mod in enumerate(MODULES_CONFIG):
            mid = mod["id"]
            top_row = self._badge_refs.get(mid)
            if top_row is None:
                continue
            for child in list(top_row.winfo_children()):
                if isinstance(child, ctk.CTkFrame):
                    child.destroy()
            status = self._get_status(mid)
            if status:
                self._render_badge(top_row, status, c, font, _dot_color(idx, self.modo))

    def set_modo(self, modo: str):
        self.modo = modo
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._cards.clear()
        self._badge_refs.clear()
        self._build()
