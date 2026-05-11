"""
_preview_neuromood.py — Preview interactivo de la nueva identidad visual NeuroMood.
Fuente: dark-theme-tests.md + white-theme-tests.md
Lanzar:  python _preview_neuromood.py
No modifica ningún archivo del proyecto.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
import tkinter as tk

# ── Paletas ───────────────────────────────────────────────────────────────────

_DARK = {
    "bg_base":        "#050911",
    "bg_surface":     "#0e1421",
    "bg_elevated":    "#141c2e",
    "bg_overlay":     "#1a2340",
    "accent":         "#00d4c8",
    "accent_dim":     "#00b8ad",
    "accent_muted":   "#0a2830",   # rgba(0,212,200,0.12) sobre #050911
    "violet":         "#7c5bf2",
    "violet_muted":   "#1a1535",
    "amber":          "#f59e0b",
    "text_primary":   "#f0f4ff",
    "text_secondary": "#a8b5cc",   # rgba(240,244,255,0.72) aprox.
    "text_muted":     "#647080",   # rgba(240,244,255,0.45) aprox.
    "border":         "#1a2340",   # rgba(255,255,255,0.10) aprox.
    "border_accent":  "#00503d",   # rgba(0,212,200,0.35) aprox.
    "success":        "#10b981",
    "warning":        "#f59e0b",
    "error":          "#ef4444",
    "info":           "#3b82f6",
    "on_accent":      "#050911",
}

_LIGHT = {
    "bg_base":        "#f8fafc",
    "bg_surface":     "#f1f5f9",
    "bg_elevated":    "#e8eef6",
    "bg_overlay":     "#dde6f0",
    "accent":         "#0891b2",
    "accent_dim":     "#0e7490",
    "accent_muted":   "#e0f2f7",   # rgba(8,145,178,0.10) sobre #f8fafc
    "violet":         "#7c3aed",
    "violet_muted":   "#ede8fb",
    "amber":          "#d97706",
    "text_primary":   "#0f172a",
    "text_secondary": "#334155",
    "text_muted":     "#64748b",
    "border":         "#dde3ed",   # rgba(15,23,42,0.10) aprox.
    "border_accent":  "#a5d4e1",   # rgba(8,145,178,0.40) aprox.
    "success":        "#059669",
    "warning":        "#d97706",
    "error":          "#dc2626",
    "info":           "#2563eb",
    "on_accent":      "#ffffff",
}


# ── App ───────────────────────────────────────────────────────────────────────

class PreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._modo = "dark"
        self.title("NeuroMood · Preview — Nueva Identidad Visual")
        w, h = 900, 700
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.minsize(820, 600)
        self._construir()

    def _c(self):
        return _DARK if self._modo == "dark" else _LIGHT

    def _toggle(self):
        self._modo = "light" if self._modo == "dark" else "dark"
        ctk.set_appearance_mode(self._modo)
        for w in self.winfo_children():
            w.destroy()
        self._construir()

    def _construir(self):
        c = self._c()
        ctk.set_appearance_mode(self._modo)
        self.configure(fg_color=c["bg_base"])

        # ── Navbar ────────────────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=c["bg_surface"], height=56, corner_radius=0)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkLabel(
            nav, text="NeuroMood",
            font=("Segoe UI", 18, "bold"),
            text_color=c["accent"]
        ).pack(side="left", padx=20)

        _lbl_sec = lambda t, parent=nav: ctk.CTkLabel(
            parent, text=t, font=("Segoe UI", 11, "normal"),
            text_color=c["text_muted"]
        ).pack(side="left", padx=14)
        _lbl_sec("Servicios")
        _lbl_sec("Instalaciones")
        _lbl_sec("Contacto")

        modo_label = "☀ Light" if self._modo == "dark" else "☾ Dark"
        ctk.CTkButton(
            nav, text=modo_label, width=88, height=32,
            fg_color=c["accent"], hover_color=c["accent_dim"],
            text_color=c["on_accent"], corner_radius=8,
            font=("Segoe UI", 11, "bold"),
            command=self._toggle
        ).pack(side="right", padx=16, pady=12)

        ctk.CTkButton(
            nav, text="Contactar", width=88, height=32,
            fg_color="transparent", hover_color=c["bg_elevated"],
            text_color=c["text_secondary"], corner_radius=8,
            border_width=1, border_color=c["border"],
            font=("Segoe UI", 11),
        ).pack(side="right", padx=(0, 8), pady=12)

        # ── Scroll principal ──────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=c["bg_base"],
            scrollbar_button_color=c["bg_elevated"],
            scrollbar_button_hover_color=c["accent"]
        )
        scroll.pack(fill="both", expand=True)

        pad = 28

        # ── HERO ─────────────────────────────────────────────────────────────
        hero = ctk.CTkFrame(scroll, fg_color=c["bg_elevated"], corner_radius=16)
        hero.pack(fill="x", padx=pad, pady=(pad, 0))

        ctk.CTkLabel(
            hero,
            text="PSIQUIATRÍA INTERVENCIONISTA",
            font=("Segoe UI", 10, "bold"),
            text_color=c["accent"]
        ).pack(anchor="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            hero,
            text="Tecnología al servicio\nde la salud mental",
            font=("Segoe UI", 28, "bold"),
            text_color=c["text_primary"],
            justify="left"
        ).pack(anchor="w", padx=24)

        ctk.CTkLabel(
            hero,
            text="Tratamientos de neuromodulación avanzada para depresión,\nansiedad y trastornos del ánimo refractarios.",
            font=("Segoe UI", 13),
            text_color=c["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=24, pady=(6, 0))

        f_hero_btns = ctk.CTkFrame(hero, fg_color="transparent")
        f_hero_btns.pack(anchor="w", padx=24, pady=(16, 20))

        ctk.CTkButton(
            f_hero_btns, text="Reservar consulta", width=148, height=38,
            fg_color=c["accent"], hover_color=c["accent_dim"],
            text_color=c["on_accent"], corner_radius=8,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            f_hero_btns, text="Conocer más", width=120, height=38,
            fg_color="transparent", hover_color=c["bg_overlay"],
            text_color=c["text_primary"], corner_radius=8,
            border_width=1, border_color=c["border"],
            font=("Segoe UI", 12)
        ).pack(side="left")

        # ── SECCIÓN LABEL ─────────────────────────────────────────────────────
        def _section_label(text):
            ctk.CTkLabel(
                scroll, text=text,
                font=("Segoe UI", 10, "bold"),
                text_color=c["accent"]
            ).pack(anchor="w", padx=pad, pady=(22, 6))

        # ── PALETA DE COLORES ────────────────────────────────────────────────
        _section_label("PALETA DE COLORES")
        f_pal = ctk.CTkFrame(scroll, fg_color="transparent")
        f_pal.pack(fill="x", padx=pad)

        swatches = [
            ("Base",      c["bg_base"]),
            ("Surface",   c["bg_surface"]),
            ("Elevated",  c["bg_elevated"]),
            ("Accent",    c["accent"]),
            ("Violet",    c["violet"]),
            ("Amber",     c["amber"]),
            ("Success",   c["success"]),
            ("Error",     c["error"]),
        ]
        for nombre, color in swatches:
            col = ctk.CTkFrame(f_pal, fg_color="transparent", width=90)
            col.pack(side="left", padx=(0, 8))
            col.pack_propagate(False)
            ctk.CTkFrame(
                col, fg_color=color, height=44, corner_radius=8,
                border_width=1, border_color=c["border"]
            ).pack(fill="x")
            ctk.CTkLabel(
                col, text=nombre, font=("Segoe UI", 9),
                text_color=c["text_muted"]
            ).pack()
            ctk.CTkLabel(
                col, text=color, font=("Segoe UI", 8),
                text_color=c["text_muted"]
            ).pack()

        # ── TIPOGRAFÍA ────────────────────────────────────────────────────────
        _section_label("TIPOGRAFÍA")
        f_tipo = ctk.CTkFrame(scroll, fg_color=c["bg_surface"], corner_radius=12)
        f_tipo.pack(fill="x", padx=pad)

        tipos = [
            ("Display / H1",  26, "bold",   c["text_primary"],   "Neuromodulación avanzada"),
            ("H2",            20, "bold",   c["text_primary"],   "Tratamientos clínicos"),
            ("H3 / Subtítulo",15, "bold",   c["text_secondary"], "Psiquiatría Intervencionista"),
            ("Body",          13, "normal", c["text_secondary"], "Cuerpo de texto estándar para descripciones clínicas."),
            ("Caption / Label",10,"normal", c["text_muted"],     "ETIQUETA DE SECCIÓN · 10px"),
        ]
        for lbl, sz, wt, col_t, sample in tipos:
            row = ctk.CTkFrame(f_tipo, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(
                row, text=lbl, width=130, anchor="w",
                font=("Segoe UI", 10), text_color=c["text_muted"]
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=sample, anchor="w",
                font=("Segoe UI", sz, wt), text_color=col_t
            ).pack(side="left")

        ctk.CTkFrame(f_tipo, fg_color="transparent", height=8).pack()

        # ── BOTONES ───────────────────────────────────────────────────────────
        _section_label("BOTONES")
        f_btns = ctk.CTkFrame(scroll, fg_color=c["bg_surface"], corner_radius=12)
        f_btns.pack(fill="x", padx=pad)
        f_btns_inner = ctk.CTkFrame(f_btns, fg_color="transparent")
        f_btns_inner.pack(padx=16, pady=14, anchor="w")

        botones = [
            ("Primary",         c["accent"],       c["accent_dim"],   c["on_accent"], c["accent"],       0),
            ("Primary Violet",  c["violet"],        "#6245d6",         "#ffffff",      c["violet"],       0),
            ("Ghost",           c["bg_surface"],    c["bg_elevated"],  c["text_primary"], c["border"],   1),
            ("Outline Accent",  c["bg_surface"],    c["accent_muted"], c["accent"],   c["accent"],        1),
            ("Disabled",        c["bg_elevated"],   c["bg_elevated"],  c["text_muted"], c["bg_elevated"], 0),
        ]
        for lbl, fg, hv, tc, bc, bw in botones:
            ctk.CTkButton(
                f_btns_inner, text=lbl, width=130, height=36,
                fg_color=fg, hover_color=hv, text_color=tc,
                corner_radius=8, border_width=bw, border_color=bc,
                font=("Segoe UI", 11, "bold" if bw == 0 else "normal")
            ).pack(side="left", padx=(0, 10))

        # ── CARDS ─────────────────────────────────────────────────────────────
        _section_label("CARDS DE SERVICIO")
        f_cards = ctk.CTkFrame(scroll, fg_color="transparent")
        f_cards.pack(fill="x", padx=pad)

        servicios = [
            ("⚡", "Estimulación TMS",   c["accent"],  "Terapia magnética transcraneal no invasiva para depresión refractaria."),
            ("🧠", "Neurofeedback",       c["violet"],  "Entrenamiento cerebral mediante señales EEG en tiempo real."),
            ("💊", "Psicofarmacología",   c["amber"],   "Optimización de esquemas farmacológicos complejos y refractarios."),
            ("✦",  "Evaluación Integral", c["info"],    "Diagnóstico profundo mediante escalas validadas y neuroimagen."),
        ]
        for icono, titulo, icon_color, desc in servicios:
            card = ctk.CTkFrame(
                f_cards, fg_color=c["bg_surface"], corner_radius=14,
                border_width=1, border_color=c["border"]
            )
            card.pack(side="left", fill="y", padx=(0, 12), ipadx=6, ipady=6)

            icon_bg = ctk.CTkFrame(card, fg_color=c["bg_elevated"], width=44, height=44, corner_radius=10)
            icon_bg.pack(anchor="w", padx=14, pady=(14, 6))
            icon_bg.pack_propagate(False)
            ctk.CTkLabel(icon_bg, text=icono, font=("Segoe UI", 18), text_color=icon_color).pack(expand=True)

            ctk.CTkLabel(
                card, text=titulo, anchor="w",
                font=("Segoe UI", 12, "bold"), text_color=c["text_primary"]
            ).pack(anchor="w", padx=14)
            ctk.CTkLabel(
                card, text=desc, anchor="w", wraplength=160, justify="left",
                font=("Segoe UI", 10), text_color=c["text_muted"]
            ).pack(anchor="w", padx=14, pady=(4, 14))

        # ── BADGES ───────────────────────────────────────────────────────────
        _section_label("BADGES / TAGS")
        f_badges = ctk.CTkFrame(scroll, fg_color="transparent")
        f_badges.pack(anchor="w", padx=pad)

        badges = [
            ("TEAL",    c["accent"],  c["accent_muted"],  c["accent"]),
            ("VIOLET",  c["violet"],  c["violet_muted"],  c["violet"]),
            ("SUCCESS", c["success"], "#0a2d20" if self._modo == "dark" else "#d1fae5", c["success"]),
            ("WARNING", c["warning"], "#2d1f00" if self._modo == "dark" else "#fef3c7", c["warning"]),
            ("ERROR",   c["error"],   "#2d0a0a" if self._modo == "dark" else "#fee2e2", c["error"]),
        ]
        for lbl, tc, bg, _border in badges:
            ctk.CTkLabel(
                f_badges, text=lbl,
                fg_color=bg, corner_radius=100,
                font=("Segoe UI", 9, "bold"), text_color=tc
            ).pack(side="left", padx=(0, 8), ipadx=10, ipady=4)

        # ── INPUTS ───────────────────────────────────────────────────────────
        _section_label("FORMULARIO")
        f_form = ctk.CTkFrame(scroll, fg_color=c["bg_surface"], corner_radius=12)
        f_form.pack(fill="x", padx=pad)
        f_form_inner = ctk.CTkFrame(f_form, fg_color="transparent")
        f_form_inner.pack(fill="x", padx=16, pady=14)

        for lbl_t, ph in [("NOMBRE", "Ej. Juan García"), ("CORREO", "juan@email.com"), ("CONSULTA", "Describe tu motivo...")]:
            ctk.CTkLabel(
                f_form_inner, text=lbl_t, anchor="w",
                font=("Segoe UI", 9, "bold"), text_color=c["text_muted"]
            ).pack(anchor="w", pady=(0, 2))
            ctk.CTkEntry(
                f_form_inner, placeholder_text=ph, height=36,
                fg_color=c["bg_elevated"], border_color=c["border"],
                border_width=1, text_color=c["text_primary"],
                placeholder_text_color=c["text_muted"],
                corner_radius=8, font=("Segoe UI", 12)
            ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            f_form_inner, text="Enviar consulta", height=38,
            fg_color=c["accent"], hover_color=c["accent_dim"],
            text_color=c["on_accent"], corner_radius=8,
            font=("Segoe UI", 12, "bold")
        ).pack(fill="x")

        # ── FOOTER ────────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(scroll, fg_color=c["bg_surface"], corner_radius=0)
        footer.pack(fill="x", pady=(pad, 0))

        ctk.CTkLabel(
            footer,
            text="NeuroMood — Psiquiatría Intervencionista & Neuromodulación · neuromood.com.ar",
            font=("Segoe UI", 10), text_color=c["text_muted"]
        ).pack(pady=14)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    PreviewApp().mainloop()
