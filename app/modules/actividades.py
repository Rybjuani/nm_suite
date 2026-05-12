"""actividades.py — Sugerencias de actividades según el ánimo."""
import random
import customtkinter as ctk
from shared.base_module import NMModule
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, CATEGORY_COLORS
from shared.db import obtener_conexion
from shared.utils import fecha_hoy, hora_actual


# Fallback suggestions when no DB activities are configured
_FALLBACK_ACTIVIDADES = [
    {"nombre": "Caminata corta", "descripcion": "Salí 10 minutos a caminar sin destino fijo.", "categoria": "Física"},
    {"nombre": "Escuchar música", "descripcion": "Elegí una canción que te guste y escuchala con atención.", "categoria": "Placer"},
    {"nombre": "Orden breve", "descripcion": "Ordená un cajón o superficie pequeña.", "categoria": "Maestría"},
    {"nombre": "Respiración", "descripcion": "3 minutos de respiración consciente.", "categoria": "Autocuidado"},
    {"nombre": "Contacto social", "descripcion": "Mandá un mensaje breve a alguien.", "categoria": "Social"},
    {"nombre": "Hidratación", "descripcion": "Tomá un vaso de agua.", "categoria": "Autocuidado"},
]


class ModuloActividades(NMModule):
    MODULE_TITLE = "Actividades"
    MODULE_ICON = "🎯"

    def build_ui(self):
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        font = TYPOGRAPHY["font_family"]
        self._c = c
        self._font = font

        self._content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=c["bg_elevated"],
        )
        self._content.pack(fill="both", expand=True, padx=24, pady=16)

        self._load_suggestions()

    def _load_suggestions(self):
        c, font = self._c, self._font

        # Clear content
        for w in self._content.winfo_children():
            w.destroy()

        # Get last mood
        animo = self._get_last_mood()

        if animo is None:
            self._show_no_mood()
            return

        # Mood display
        mood_frame = ctk.CTkFrame(self._content, fg_color=c["bg_surface"], corner_radius=10)
        mood_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            mood_frame, text=f"Tu último ánimo registrado: {animo}/10",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
        ).pack(padx=16, pady=10)

        # Get activity suggestions
        actividades = self._get_activities(animo)

        if not actividades:
            ctk.CTkLabel(
                self._content, text="No hay actividades disponibles.",
                font=(font, TYPOGRAPHY["size_body"]),
                text_color=c["text_tertiary"],
            ).pack(pady=20)
            return

        ctk.CTkLabel(
            self._content, text="Sugerencias para vos",
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        # Show 2-3 suggestion cards
        for act in actividades[:3]:
            self._build_activity_card(act)

    def _show_no_mood(self):
        c, font = self._c, self._font
        ctk.CTkLabel(
            self._content, text="Sin registro de ánimo hoy",
            font=(font, TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
        ).pack(pady=(40, 8))
        ctk.CTkLabel(
            self._content,
            text="Registrá tu ánimo en el módulo correspondiente\npara recibir sugerencias personalizadas.",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_secondary"],
            justify="center",
        ).pack(pady=(0, 20))

        # Show generic suggestions
        ctk.CTkLabel(
            self._content, text="Mientras tanto, algunas ideas generales:",
            font=(font, TYPOGRAPHY["size_body"]),
            text_color=c["text_tertiary"],
        ).pack(anchor="w", pady=(20, 12))

        generics = random.sample(_FALLBACK_ACTIVIDADES, min(3, len(_FALLBACK_ACTIVIDADES)))
        for act in generics:
            self._build_activity_card(act)

    def _build_activity_card(self, act: dict):
        c, font = self._c, self._font
        cat = act.get("categoria", "Autocuidado")
        cat_color = CATEGORY_COLORS.get(cat, c["accent"])

        card = ctk.CTkFrame(self._content, fg_color=c["bg_surface"], corner_radius=LAYOUT["radius_card"])
        card.pack(fill="x", pady=(0, LAYOUT["gap_cards"]))

        # Color accent bar (simulated with a thin label)
        accent_bar = ctk.CTkFrame(card, fg_color=cat_color, width=4, corner_radius=2)
        accent_bar.pack(side="left", fill="y", padx=(0, 0), pady=8)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Category badge
        ctk.CTkLabel(
            inner, text=cat,
            font=(font, TYPOGRAPHY["size_caption"]),
            text_color=cat_color,
        ).pack(anchor="w")

        # Title
        ctk.CTkLabel(
            inner, text=act.get("nombre", ""),
            font=(font, TYPOGRAPHY["size_body"], "bold"),
            text_color=c["text_primary"],
        ).pack(anchor="w", pady=(2, 2))

        # Description
        desc = act.get("descripcion", "")
        if desc:
            ctk.CTkLabel(
                inner, text=desc,
                font=(font, TYPOGRAPHY["size_small"]),
                text_color=c["text_secondary"],
                wraplength=300, justify="left",
            ).pack(anchor="w", pady=(0, 8))

        # Result buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(anchor="w")

        nombre = act.get("nombre", "Actividad")
        results = [
            ("Hecha", "hecha", c["success"]),
            ("Intentada", "intentada", c["warning"]),
            ("No pude", "no_pude", c["error"]),
        ]
        for label, resultado, color in results:
            btn = ctk.CTkButton(
                btn_frame, text=label, width=80, height=30,
                fg_color=c["bg_elevated"], hover_color=color,
                text_color=c["text_primary"],
                font=(font, TYPOGRAPHY["size_small"]),
                corner_radius=6,
                command=lambda n=nombre, r=resultado, cd=card: self._register_result(n, r, cd),
            )
            btn.pack(side="left", padx=(0, 6))

    def _register_result(self, nombre: str, resultado: str, card_widget):
        c = self._c
        animo = self._get_last_mood()
        if animo is None:
            # Sin ánimo real no se puede asociar la actividad a un estado significativo
            from shared.components import mostrar_mensaje
            mostrar_mensaje(
                self, "Registrá tu ánimo primero",
                "Para asociar esta actividad a tu estado actual,\n"
                "registrá tu ánimo en el módulo Ánimo antes de continuar.",
                tipo="info", modo=self.modo,
            )
            return
        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO activacion (fecha, hora, energia, animo, actividad, resultado) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(), animo, animo, nombre, resultado),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        # Visual feedback
        color_map = {"hecha": c["success"], "intentada": c["warning"], "no_pude": c["error"]}
        try:
            card_widget.configure(border_color=color_map.get(resultado, c["accent"]), border_width=2)
        except Exception:
            pass

    # ── Data access ──────────────────────────────────────────
    def _get_last_mood(self):
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass
        return None

    def _get_activities(self, animo: int) -> list:
        """Get activities from DB matching mood range, fallback to defaults."""
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT nombre, descripcion, categoria FROM activacion_actividades "
                "WHERE activa = 1 AND animo_min <= ? AND animo_max >= ? "
                "ORDER BY RANDOM() LIMIT 3",
                (animo, animo),
            ).fetchall()
            conn.close()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            pass

        # Fallback: filter by mood level heuristic
        if animo <= 3:
            pool = [a for a in _FALLBACK_ACTIVIDADES if a["categoria"] in ("Autocuidado", "Placer")]
        elif animo <= 6:
            pool = _FALLBACK_ACTIVIDADES[:]
        else:
            pool = [a for a in _FALLBACK_ACTIVIDADES if a["categoria"] in ("Física", "Maestría", "Social")]

        if not pool:
            pool = _FALLBACK_ACTIVIDADES
        return random.sample(pool, min(3, len(pool)))

    def on_enter(self):
        self._load_suggestions()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) FROM activacion WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                return f"{row[0]} actividad{'es' if row[0] > 1 else ''} ✔"
        except Exception:
            pass
        return ""
