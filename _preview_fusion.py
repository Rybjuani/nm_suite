"""
_preview_fusion.py — Fusión de identidades visuales: NeuroMood Suite + neuromood.com.ar
Simula la UI real de la suite con el tema fusionado.
Lanzar: python _preview_fusion.py
No modifica ningún archivo del proyecto.

CRITERIO ARTÍSTICO:
  Dark → profundidad del nuevo sistema, tinte azul del actual, teal mejorado, +violeta secundario
  Light → blanco médico del nuevo sistema, teal como acento (reemplaza carbón), leve calidez en base
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import customtkinter as ctk
import tkinter as tk
from datetime import datetime

# ─── PALETAS FUSIONADAS ────────────────────────────────────────────────────────

_FUSION_DARK = {
    # Fondos — nueva profundidad + tinte azul del actual
    "bg_primary":   "#080d1a",  # nuevo depth, azul navy actual → punto medio
    "bg_secondary": "#0c1525",  # barras, header
    "bg_surface":   "#0f1c2e",  # cards — mantiene el tinte azul navy del actual
    "bg_input":     "#0f1c2e",
    "bg_elevated":  "#162437",  # elementos elevados, inputs activos
    "bg_hover":     "#1e3249",  # hover — más suave que el actual #1A3050
    "bg_list_item": "#162437",
    # Acentos — teal de la nueva identidad (más orgánico que el actual)
    "accent":       "#00d4c8",  # ↑ nuevo — bioluminiscente vs. cyan plano actual
    "accent_hover": "#00bdb2",
    "accent_subtle":"#041a1f",
    # Violeta secundario — totalmente nuevo, ausente en el actual
    "violet":       "#7c5bf2",  # ↑ nuevo — da profundidad sin reemplazar el teal
    "violet_muted": "#1a1535",
    # Texto — nuevo sistema (más sofisticado que blanco puro)
    "text_primary": "#f0f4ff",  # ↑ nuevo — azul-blanco suave vs. #FFFFFF actual
    "text_secondary":"#a8b8cc", # ≈ blend
    "text_tertiary": "#5a7090", # ≈ blend (entre #8BA4BE actual y nuevo muted)
    "text_on_accent":"#03080f",
    # Bordes
    "border":       "#162437",  # ≈ actual pero con el nuevo depth
    "border_accent":"#00453e",
    # Estados
    "success":      "#12c97a",  # ≈ blend — vibrante como el actual, más refinado
    "warning":      "#f59e0b",  # ↑ nuevo
    "error":        "#e8505b",  # → actual — bien calibrado
    "info":         "#3b82f6",  # ↑ nuevo
    "progress_track":"#162437",
    "progress_fill":"#00d4c8",
}

_FUSION_LIGHT = {
    # Fondos — blanco médico del nuevo, +1 grado de calidez (salud mental ≠ laboratorio)
    "bg_primary":   "#f5f7fb",  # ≈ blend — más cálido que #f8fafc puro del nuevo
    "bg_secondary": "#eaeff7",  # barras
    "bg_surface":   "#ffffff",  # ↑ nuevo — papel limpio vs. crema Notion del actual
    "bg_input":     "#ffffff",
    "bg_elevated":  "#f0f4fb",  # elevado
    "bg_hover":     "#e4eaf4",
    "bg_list_item": "#ffffff",
    # Acentos — teal profundo del nuevo (reemplaza carbón del actual: error de marca)
    "accent":       "#0891b2",  # ↑ nuevo — el carbón #404040 rompía la identidad visual
    "accent_hover": "#0e7490",
    "accent_subtle":"#e0f4f9",
    # Violeta secundario
    "violet":       "#7c3aed",  # ↑ nuevo
    "violet_muted": "#ede8fb",
    # Texto — nuevo sistema (más preciso que Notion #191919)
    "text_primary": "#0f172a",  # ↑ nuevo
    "text_secondary":"#334155", # ↑ nuevo
    "text_tertiary": "#64748b", # ↑ nuevo
    "text_on_accent":"#ffffff",
    # Bordes
    "border":       "#dde5ef",
    "border_accent":"#9dd1e2",
    # Estados — mix: precisión del nuevo, suavidad del actual para contexto de salud mental
    "success":      "#0d9e74",  # ≈ blend
    "warning":      "#c87c40",  # → actual — calibrado para fondos cálidos
    "error":        "#d46868",  # → actual — más suave para salud mental
    "info":         "#2563eb",  # ↑ nuevo
    "progress_track":"#dde5ef",
    "progress_fill":"#0891b2",
}

# Paletas actuales (para comparación)
_ACTUAL_DARK = {
    "bg_primary":"#0B1928","bg_secondary":"#0D2137","bg_surface":"#112740",
    "bg_input":"#112740","bg_elevated":"#112740","bg_hover":"#1A3050","bg_list_item":"#1A3050",
    "accent":"#1EC8D4","accent_hover":"#2EDDE9","accent_subtle":"#0F3040","violet":"#1EC8D4","violet_muted":"#0F3040",
    "text_primary":"#FFFFFF","text_secondary":"#E8EEF4","text_tertiary":"#8BA4BE","text_on_accent":"#FFFFFF",
    "border":"#1A3050","border_accent":"#1EC8D4",
    "success":"#22D47E","warning":"#F0A500","error":"#E8505B","info":"#1EC8D4",
    "progress_track":"#1A3050","progress_fill":"#1EC8D4",
}
_ACTUAL_LIGHT = {
    "bg_primary":"#E3E2DE","bg_secondary":"#D8D7D3","bg_surface":"#F7F7F5",
    "bg_input":"#FFFFFF","bg_elevated":"#FFFFFF","bg_hover":"#C0BFBC","bg_list_item":"#FFFFFF",
    "accent":"#404040","accent_hover":"#5C5C5C","accent_subtle":"#DDDCDA","violet":"#404040","violet_muted":"#DDDCDA",
    "text_primary":"#191919","text_secondary":"#4A4A4A","text_tertiary":"#6B6B6B","text_on_accent":"#FFFFFF",
    "border":"#CBCAC7","border_accent":"#404040",
    "success":"#5A9E82","warning":"#C87C40","error":"#D46868","info":"#4A7EA5",
    "progress_track":"#CBCAC7","progress_fill":"#404040",
}

_NOTAS = {
    "accent_dark":  "Teal #00d4c8 — más orgánico que el\ncyan plano actual #1EC8D4",
    "violet":       "Violeta #7c5bf2 — acento secundario\nnuevo. El actual es monocromático",
    "bg_dark":      "Base #080d1a — equilibrio entre\nprofundidad nueva y legibilidad actual",
    "text_dark":    "#f0f4ff — azul-blanco suave.\nMás sofisticado que blanco puro",
    "accent_light": "Teal #0891b2 — reemplaza el carbón\n#404040 que rompe la identidad visual",
    "bg_light":     "#f5f7fb — +1°C vs. nuevo puro.\nCalidez necesaria en salud mental",
    "surface_light":"#ffffff papel limpio —\nmejor que la crema Notion actual",
    "success_dark": "#12c97a — vibrante como el actual\npero más refinado que #22D47E",
}


# ─── VENTANA PRINCIPAL ─────────────────────────────────────────────────────────

class PreviewFusion(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._modo = "dark"
        self._ver_notas = False
        self._ver_actual = False
        self.title("NeuroMood · Preview — Fusión de Identidades Visuales")
        w, h = 980, 720
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")
        self.minsize(880, 640)
        self._build()

    def _c(self):
        if self._ver_actual:
            return _ACTUAL_DARK if self._modo == "dark" else _ACTUAL_LIGHT
        return _FUSION_DARK if self._modo == "dark" else _FUSION_LIGHT

    def _rebuild(self):
        ctk.set_appearance_mode(self._modo)
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        c = self._c()
        ctk.set_appearance_mode(self._modo)
        self.configure(fg_color=c["bg_primary"])

        # ── Barra de control superior ─────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=44, corner_radius=0)
        ctrl.pack(fill="x")
        ctrl.pack_propagate(False)

        ctk.CTkLabel(ctrl, text="PREVIEW — FUSIÓN DE TEMAS",
            font=("Segoe UI", 9, "bold"), text_color=c["text_tertiary"]
        ).pack(side="left", padx=14)

        # Toggle notas
        nota_color = c["violet"] if self._ver_notas else c["bg_elevated"]
        nota_tc    = "#ffffff"   if self._ver_notas else c["text_tertiary"]
        ctk.CTkButton(ctrl, text="💬 Notas de diseño", width=136, height=28,
            fg_color=nota_color, hover_color=c["violet"] if not self._ver_notas else c["accent_hover"],
            text_color=nota_tc, corner_radius=6,
            font=("Segoe UI", 10),
            command=lambda: (setattr(self,"_ver_notas",not self._ver_notas), self._rebuild())
        ).pack(side="right", padx=(0,6), pady=8)

        # Toggle actual
        act_color = c["warning"] if self._ver_actual else c["bg_elevated"]
        act_tc    = "#050911"   if self._ver_actual else c["text_tertiary"]
        ctk.CTkButton(ctrl, text="⟷ Ver actual", width=106, height=28,
            fg_color=act_color, hover_color=c["bg_hover"],
            text_color=act_tc, corner_radius=6,
            font=("Segoe UI", 10),
            command=lambda: (setattr(self,"_ver_actual",not self._ver_actual), self._rebuild())
        ).pack(side="right", padx=(0,4), pady=8)

        # Toggle dark/light
        modo_lbl = "☀  Light" if self._modo == "dark" else "☾  Dark"
        ctk.CTkButton(ctrl, text=modo_lbl, width=86, height=28,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color=c["text_on_accent"], corner_radius=6,
            font=("Segoe UI", 10, "bold"),
            command=lambda: (setattr(self,"_modo","light" if self._modo=="dark" else "dark"), self._rebuild())
        ).pack(side="right", padx=(0,4), pady=8)

        etq = "FUSION" if not self._ver_actual else "ACTUAL"
        etq_col = c["accent"] if not self._ver_actual else c["warning"]
        ctk.CTkLabel(ctrl, text=etq, font=("Segoe UI", 9, "bold"), text_color=etq_col
        ).pack(side="right", padx=8)

        # ── Header de la app (simula HeaderFrame) ─────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=62, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="Checklist de Rutina",
            font=("Segoe UI", 17, "bold"), text_color=c["text_primary"]
        ).pack(side="left", padx=20, pady=8)
        ctk.CTkLabel(hdr, text="Estructura tu día para mejorar tu bienestar",
            font=("Segoe UI", 11), text_color=c["text_tertiary"]
        ).pack(side="left", padx=0)
        ctk.CTkButton(hdr, text="☀" if self._modo=="dark" else "☾", width=36, height=36,
            fg_color=c["bg_elevated"], hover_color=c["bg_hover"],
            text_color=c["text_secondary"], corner_radius=8, font=("Segoe UI",14)
        ).pack(side="right", padx=16)

        if self._ver_notas and self._modo == "dark":
            self._nota_overlay(hdr, _NOTAS["bg_dark"], anchor="sw")

        # ── Área principal ────────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=14)

        # Columna izquierda (checklist)
        col_izq = ctk.CTkFrame(main, fg_color="transparent")
        col_izq.pack(side="left", fill="both", expand=True, padx=(0,10))

        # Columna derecha (stats)
        col_der = ctk.CTkFrame(main, fg_color="transparent", width=268)
        col_der.pack(side="right", fill="y")
        col_der.pack_propagate(False)

        self._build_checklist(col_izq, c)
        self._build_stats(col_der, c)

        # ── Barra inferior ────────────────────────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=38, corner_radius=0)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)
        ctk.CTkLabel(bot, text="neuromood.com.ar",
            font=("Segoe UI", 10), text_color=c["text_tertiary"]
        ).pack(side="left", padx=16)
        ctk.CTkButton(bot, text="Acerca de", width=78, height=26,
            fg_color=c["bg_elevated"], hover_color=c["bg_hover"],
            text_color=c["text_tertiary"], corner_radius=6, font=("Segoe UI",10)
        ).pack(side="right", padx=10, pady=6)

        # ── Panel de notas (bottom) ───────────────────────────────────────────
        if self._ver_notas:
            self._build_notas_panel(c)

    def _nota_overlay(self, widget, texto, anchor="ne"):
        """Mini tooltip adherido a un widget — solo en modo notas."""
        tip = ctk.CTkLabel(widget, text=texto, font=("Segoe UI", 8),
            fg_color=_FUSION_DARK["violet"] if self._modo=="dark" else _FUSION_LIGHT["violet"],
            text_color="#ffffff", corner_radius=6, justify="left"
        )
        tip.place(relx=0.98, rely=0.5, anchor="e", x=-4)

    # ── Checklist ─────────────────────────────────────────────────────────────

    def _build_checklist(self, parent, c):
        # Tabs de sección
        tabs = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        tabs.pack(fill="x", pady=(0,10))
        tabs.pack_propagate(False)

        for i, (clave, nombre) in enumerate([("manana","Mañana"),("tarde","Tarde"),("noche","Noche")]):
            activa = (i == 0)
            ctk.CTkButton(tabs, text=nombre, height=34,
                fg_color=c["accent"] if activa else c["bg_hover"],
                hover_color=c["accent_hover"] if activa else c["bg_elevated"],
                text_color=c["text_on_accent"] if activa else c["text_secondary"],
                corner_radius=8, font=("Segoe UI", 12, "bold" if activa else "normal"),
                width=90
            ).pack(side="left", padx=(0,6))

        if self._ver_notas and self._modo == "light":
            ctk.CTkLabel(tabs, text=_NOTAS["accent_light"],
                fg_color=_FUSION_LIGHT["violet"], text_color="#fff",
                font=("Segoe UI",8), corner_radius=6, justify="left"
            ).pack(side="right", padx=4)

        # Card con tareas
        card = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=12,
            border_width=1, border_color=c["border"])
        card.pack(fill="both", expand=True)

        _CAT = {"Logro":"#3A6EA5","Placer":"#3A8E5A","Autocuidado":"#7A4EA5","Social":"#C07030"}
        tareas = [
            ("Meditación guiada 10 min",    True,  "Autocuidado"),
            ("Registro de ánimo",            True,  "Autocuidado"),
            ("Salir a caminar 20 min",       False, "Logro"),
            ("Llamar a un amigo",            False, "Social"),
            ("Leer 15 minutos",              False, "Placer"),
            ("Preparar el almuerzo",         True,  "Logro"),
            ("Ejercicio de respiración",     False, "Autocuidado"),
        ]
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
            scrollbar_button_hover_color=c["accent"]
        )
        scroll.pack(fill="both", expand=True, padx=12, pady=(8,12))

        for desc, completada, cat in tareas:
            fila = ctk.CTkFrame(scroll, fg_color=c["bg_list_item"], corner_radius=8)
            fila.pack(fill="x", pady=3)
            _cb_fg = c["success"] if self._modo == "light" else c["accent"]
            ctk.CTkCheckBox(fila, text=desc,
                variable=ctk.BooleanVar(value=completada),
                font=("Segoe UI", 12),
                text_color=c["success"] if completada else c["text_primary"],
                fg_color=_cb_fg, hover_color=c["accent_hover"],
                border_color=c["border"], checkmark_color=c["text_on_accent"],
            ).pack(side="left", padx=10, pady=9)
            ctk.CTkLabel(fila, text=cat, width=82, height=18,
                fg_color=_CAT.get(cat,"#3A6EA5"), corner_radius=4,
                text_color="#FFFFFF", font=("Segoe UI",9)
            ).pack(side="left", padx=(0,4))
            ctk.CTkButton(fila, text="✕", width=28, height=26,
                fg_color="transparent", hover_color=c["error"],
                text_color=c["text_tertiary"], corner_radius=6, font=("Segoe UI",11,"bold")
            ).pack(side="right", padx=6)

        if self._ver_notas:
            ctk.CTkLabel(card,
                text=_NOTAS["text_dark"] if self._modo=="dark" else _NOTAS["surface_light"],
                fg_color=_FUSION_DARK["violet"] if self._modo=="dark" else _FUSION_LIGHT["violet"],
                text_color="#fff", font=("Segoe UI",8), corner_radius=6, justify="left"
            ).place(relx=0.99, rely=0.99, anchor="se", x=-8, y=-8)

    # ── Panel stats (derecho) ──────────────────────────────────────────────────

    def _build_stats(self, parent, c):
        # Tabs Hoy / Stats / Propuestas
        tab_bar = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        tab_bar.pack(fill="x", pady=(0,8))
        tab_bar.pack_propagate(False)
        for i, lbl in enumerate(["Hoy","Estadísticas","Propuestas"]):
            activa = (i == 0)
            ctk.CTkButton(tab_bar, text=lbl, height=30,
                fg_color=c["accent"] if activa else c["bg_hover"],
                hover_color=c["accent_hover"],
                text_color=c["text_on_accent"] if activa else c["text_secondary"],
                corner_radius=7, font=("Segoe UI", 10, "bold" if activa else "normal")
            ).pack(side="left", padx=(0,3), fill="y")

        # Card progreso circular
        card_prog = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=12,
            border_width=1, border_color=c["border"])
        card_prog.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(card_prog, text="Progreso de hoy",
            font=("Segoe UI",13,"bold"), text_color=c["text_primary"]
        ).pack(anchor="w", padx=16, pady=(14,6))

        canvas = tk.Canvas(card_prog, bg=c["bg_surface"], highlightthickness=0, width=148, height=148)
        canvas.pack(pady=(0,6))
        self._draw_circle(canvas, 0.71, c)

        ctk.CTkLabel(card_prog, text="Seguimiento: 4 días",
            font=("Segoe UI",11,"bold"), text_color=c["accent"]
        ).pack(pady=(0,14))

        if self._ver_notas and self._modo == "dark":
            ctk.CTkLabel(card_prog,
                text=_NOTAS["accent_dark"],
                fg_color=c["violet"], text_color="#fff",
                font=("Segoe UI",8), corner_radius=6, justify="left"
            ).place(relx=0.99, rely=0.01, anchor="ne", x=-6, y=6)

        # Card por categoría
        card_cat = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=12,
            border_width=1, border_color=c["border"])
        card_cat.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(card_cat, text="Por categoría",
            font=("Segoe UI",11,"bold"), text_color=c["text_primary"]
        ).pack(anchor="w", padx=14, pady=(12,4))

        cat_canvas = tk.Canvas(card_cat, bg=c["bg_surface"], highlightthickness=0, height=80)
        cat_canvas.pack(fill="x", padx=14, pady=(0,12))
        cat_canvas.bind("<Configure>", lambda e: self._draw_cat(cat_canvas, c))
        self._draw_cat(cat_canvas, c)

        # Card badges + estados
        card_estados = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=12,
            border_width=1, border_color=c["border"])
        card_estados.pack(fill="x")

        ctk.CTkLabel(card_estados, text="Badges & estados",
            font=("Segoe UI",11,"bold"), text_color=c["text_primary"]
        ).pack(anchor="w", padx=14, pady=(12,6))

        row_b = ctk.CTkFrame(card_estados, fg_color="transparent")
        row_b.pack(anchor="w", padx=14, pady=(0,6))
        badges = [
            ("Logro",   "#3A6EA5", "#1a2e4a" if self._modo=="dark" else "#dce8f5"),
            ("Violeta", c["violet"], c["violet_muted"]),
            ("Éxito",   c["success"], "#0a2d20" if self._modo=="dark" else "#d1fae5"),
        ]
        for lbl, tc, bg in badges:
            ctk.CTkLabel(row_b, text=lbl, fg_color=bg, corner_radius=100,
                font=("Segoe UI",9,"bold"), text_color=tc
            ).pack(side="left", padx=(0,6), ipadx=9, ipady=3)

        row_b2 = ctk.CTkFrame(card_estados, fg_color="transparent")
        row_b2.pack(anchor="w", padx=14, pady=(0,10))
        badges2 = [
            ("Advertencia", c["warning"], "#2d1800" if self._modo=="dark" else "#fef3c7"),
            ("Error",       c["error"],   "#2d0808" if self._modo=="dark" else "#fee2e2"),
        ]
        for lbl, tc, bg in badges2:
            ctk.CTkLabel(row_b2, text=lbl, fg_color=bg, corner_radius=100,
                font=("Segoe UI",9,"bold"), text_color=tc
            ).pack(side="left", padx=(0,6), ipadx=9, ipady=3)

        if self._ver_notas and self._modo == "dark":
            ctk.CTkLabel(card_estados,
                text=_NOTAS["violet"],
                fg_color=c["violet"], text_color="#fff",
                font=("Segoe UI",8), corner_radius=6, justify="left"
            ).place(relx=0.99, rely=0.01, anchor="ne", x=-6, y=6)
        elif self._ver_notas and self._modo == "light":
            ctk.CTkLabel(card_estados,
                text=_NOTAS["bg_light"],
                fg_color=c["violet"], text_color="#fff",
                font=("Segoe UI",8), corner_radius=6, justify="left"
            ).place(relx=0.99, rely=0.01, anchor="ne", x=-6, y=6)

    # ── Canvas helpers ─────────────────────────────────────────────────────────

    def _draw_circle(self, canvas, pct, c):
        canvas.delete("all")
        bg = c["bg_surface"]
        cx, cy, r, gx = 74, 74, 56, 10
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=c["progress_track"], width=gx)
        if pct > 0:
            ext = pct * 360
            col = c["progress_fill"] if pct < 1 else c["success"]
            if pct >= 1:
                canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=col, width=gx)
            else:
                canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                    start=90, extent=-ext, outline=col, width=gx, style="arc")
        canvas.create_text(cx, cy,   text=f"{int(pct*100)}%",
            fill=c["text_primary"], font=("Segoe UI",17,"bold"))
        canvas.create_text(cx, cy+18, text="5/7 tareas",
            fill=c["text_tertiary"], font=("Segoe UI",9))

    def _draw_cat(self, canvas, c):
        canvas.delete("all")
        cats = [
            ("Logro",       "#3A6EA5", 0.85),
            ("Placer",      "#3A8E5A", 0.50),
            ("Autocuidado", "#7A4EA5", 1.00),
            ("Social",      "#C07030", 0.20),
        ]
        w = canvas.winfo_width() or 230
        row_h, y_pad = 14, 4
        for i, (cat, col, pct) in enumerate(cats):
            y = y_pad + i*(row_h + y_pad)
            canvas.create_text(4, y+row_h//2, text=cat, anchor="w",
                fill=c["text_tertiary"], font=("Segoe UI",8))
            bx, bw = 78, w - 78 - 30
            canvas.create_rectangle(bx, y+2, bx+bw, y+row_h-2,
                fill=c["progress_track"], outline="")
            if pct > 0:
                canvas.create_rectangle(bx, y+2, bx+max(bw*pct,3), y+row_h-2,
                    fill=col, outline="")
            canvas.create_text(w-2, y+row_h//2, text=f"{int(pct*100)}%",
                anchor="e", fill=c["text_tertiary"], font=("Segoe UI",8))

    # ── Panel de notas de diseño ───────────────────────────────────────────────

    def _build_notas_panel(self, c):
        panel = ctk.CTkFrame(self, fg_color=c["bg_elevated"], corner_radius=0,
            border_width=1, border_color=c["border"])
        panel.pack(fill="x", side="bottom", before=self.winfo_children()[-1])

        ctk.CTkLabel(panel,
            text="NOTAS DE FUSIÓN  —  ↑ nuevo identidad  ·  ≈ blend  ·  → actual conservado",
            font=("Segoe UI",9,"bold"), text_color=c["violet"]
        ).pack(anchor="w", padx=14, pady=(8,4))

        if self._modo == "dark":
            items = [
                ("↑", "Teal: #00d4c8",        "bioluminiscente vs. cyan plano #1EC8D4 actual"),
                ("↑", "Violeta: #7c5bf2",      "acento secundario nuevo — el actual es monocromático"),
                ("↑", "Base: #080d1a",         "más profundidad, mismo tinte azul del actual"),
                ("↑", "Text: #f0f4ff",         "azul-blanco suave — más sofisticado que blanco puro"),
                ("≈", "Success: #12c97a",      "vibrante como el actual, más refinado que #22D47E"),
                ("→", "Error: #e8505b",        "se conserva — bien calibrado en el actual"),
            ]
        else:
            items = [
                ("↑", "Accent: #0891b2",       "teal profundo — el carbón #404040 actual rompía la identidad"),
                ("↑", "Violeta: #7c3aed",      "acento secundario nuevo — ausente en el actual"),
                ("↑", "Surface: #ffffff",      "papel puro — más limpio que la crema Notion actual"),
                ("≈", "Base: #f5f7fb",         "+1°C de calidez vs. nuevo puro — salud mental ≠ laboratorio"),
                ("≈", "Text: #0f172a",         "más preciso que Notion #191919"),
                ("→", "Warning: #c87c40",      "se conserva — calibrado para fondos cálidos"),
            ]

        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0,10))
        for icon, titulo, detalle in items:
            item_c = c["accent"] if icon == "↑" else c["violet"] if icon == "≈" else c["text_tertiary"]
            f = ctk.CTkFrame(row, fg_color=c["bg_surface"], corner_radius=8,
                border_width=1, border_color=c["border"])
            f.pack(side="left", padx=(0,8))
            ctk.CTkLabel(f, text=f"{icon} {titulo}",
                font=("Segoe UI",9,"bold"), text_color=item_c
            ).pack(anchor="w", padx=10, pady=(6,0))
            ctk.CTkLabel(f, text=detalle, font=("Segoe UI",8),
                text_color=c["text_tertiary"], wraplength=130, justify="left"
            ).pack(anchor="w", padx=10, pady=(0,7))


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    PreviewFusion().mainloop()
