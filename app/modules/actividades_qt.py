"""
app/modules/actividades_qt.py — Sugerencias de actividades según el ánimo (PyQt6)

LÓGICA PRESERVADA EXACTA:
  _FALLBACK_ACTIVIDADES, _get_last_mood(), _get_activities(),
  _register_result(), get_card_status()
"""

import os
import sys
import random
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QSizePolicy,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMToast,
        ThemeManager, h_spacer, NMEmptyState,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD,
        stylesheet_scrollarea,
    )
    from shared.theme import CATEGORY_COLORS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMCard, NMToast,
        ThemeManager, h_spacer, NMEmptyState,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS, RADIUS_CARD,
        stylesheet_scrollarea,
    )
    from shared.theme import CATEGORY_COLORS
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual


# ── Fallback activities (preservado exacto) ───────────────────────────────────

_FALLBACK_ACTIVIDADES = [
    {"nombre": "Caminata corta",    "descripcion": "Salí 10 minutos a caminar sin destino fijo.",          "categoria": "Física"},
    {"nombre": "Escuchar música",   "descripcion": "Elegí una canción que te guste y escuchala con atención.", "categoria": "Placer"},
    {"nombre": "Orden breve",       "descripcion": "Ordená un cajón o superficie pequeña.",                 "categoria": "Maestría"},
    {"nombre": "Respiración",       "descripcion": "3 minutos de respiración consciente.",                  "categoria": "Autocuidado"},
    {"nombre": "Contacto social",   "descripcion": "Mandá un mensaje breve a alguien.",                     "categoria": "Social"},
    {"nombre": "Hidratación",       "descripcion": "Tomá un vaso de agua.",                                 "categoria": "Autocuidado"},
]


# ── Result button (NMButtonOutline wrapper with feedback) ─────────────────────


# ── ModuloActividades ─────────────────────────────────────────────────────────

class ModuloActividades(NMModule):
    MODULE_TITLE = "Actividades"
    MODULE_ICON  = "🎯"

    def build_ui(self):
        c = colors(self._modo)

        # ── Root layout ───────────────────────────────────────────────────────
        root = QVBoxLayout(self._content)
        root.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                PAD_CONTAINER, PAD_CONTAINER)
        root.setSpacing(sp("sm"))

        # ── Scroll area ───────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, sp("sm"), 0)
        self._scroll_layout.setSpacing(GAP_CARDS)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._scroll_content)
        root.addWidget(self._scroll)

        self._load_suggestions()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self.update()

    # ── Load suggestions ──────────────────────────────────────────────────────

    def _load_suggestions(self):
        # Clear scroll content
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get last mood
        animo = self._get_last_mood()

        if animo is None:
            self._show_no_mood()
            return

        # Mood banner
        c = colors(self._modo)
        mood_frame = QFrame()
        mood_frame.setObjectName("MoodBanner")
        mood_frame.setStyleSheet(f"""
            QFrame#MoodBanner {{
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
        """)
        mood_layout = QHBoxLayout(mood_frame)
        mood_layout.setContentsMargins(sp("md"), sp("sm") + sp("xs") // 2, sp("md"), sp("sm") + sp("xs") // 2)
        mood_lbl = QLabel(f"Tu último ánimo registrado: {animo}/10")
        mood_lbl.setFont(qfont("size_body"))
        mood_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        mood_layout.addWidget(mood_lbl)
        self._scroll_layout.addWidget(mood_frame)

        # Suggestions
        actividades = self._get_activities(animo)

        if not actividades:
            self._scroll_layout.addWidget(NMEmptyState(
                "fa5s.running",
                "Sin sugerencias",
                "Completá un registro de ánimo primero.",
                self._scroll_content,
            ))
            return

        title_lbl = QLabel("Sugerencias para vos")
        title_lbl.setFont(qfont("size_h3", bold=True))
        title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._scroll_layout.addWidget(title_lbl)

        for act in actividades[:3]:
            self._build_activity_card(act)

    def _show_no_mood(self):
        self._scroll_layout.addWidget(NMEmptyState(
            "fa5s.running",
            "Sin sugerencias",
            "Completá un registro de ánimo primero.",
            self._scroll_content,
        ))

    def _build_activity_card(self, act: dict):
        c = colors(self._modo)
        cat = act.get("categoria", "Autocuidado")
        cat_color = CATEGORY_COLORS.get(cat, c["accent"])

        # Use NMCard with accent_color for the left bar
        card = NMCard(
            parent=self._scroll_content,
            accent_color=cat_color,
            clickable=False,
            modo=self._modo,
        )
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(
            sp("md"),
            sp("sm") + sp("xs") // 2,
            sp("sm") + sp("xs"),
            sp("sm") + sp("xs") // 2,
        )
        card_layout.setSpacing(sp("sm") + sp("xs"))

        # Inner content
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(sp("xs"))

        # Category label
        cat_lbl = QLabel(cat)
        cat_lbl.setFont(qfont("size_caption"))
        cat_lbl.setStyleSheet(f"color: {cat_color}; background: transparent;")
        inner_layout.addWidget(cat_lbl)

        # Title
        name_lbl = QLabel(act.get("nombre", ""))
        name_lbl.setFont(qfont("size_body", bold=True))
        name_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        inner_layout.addWidget(name_lbl)

        # Description
        desc = act.get("descripcion", "")
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(qfont("size_small"))
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
            inner_layout.addWidget(desc_lbl)

        # Result buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(sp("sm") - sp("xs") // 2)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        nombre = act.get("nombre", "Actividad")
        results = [
            ("Hecha",     "hecha",     c["success"]),
            ("Intentada", "intentada", c["warning"]),
            ("No pude",   "no_pude",   c["error"]),
        ]
        self._result_btns: list[NMButtonOutline] = []
        for label, resultado, _hover_color in results:
            btn = NMButtonOutline(label, modo=self._modo)
            btn.setFixedHeight(30)
            btn.setMinimumWidth(76)
            btn.clicked.connect(
                lambda checked=False, n=nombre, r=resultado, cd=card:
                    self._register_result(n, r, cd)
            )
            btn_row.addWidget(btn)
            self._result_btns.append(btn)

        inner_layout.addLayout(btn_row)
        card_layout.addWidget(inner)

        self._scroll_layout.addWidget(card)

    # ── _register_result (lógica preservada exacta) ───────────────────────────

    def _register_result(self, nombre: str, resultado: str, card_widget: NMCard):
        c = colors(self._modo)
        animo = self._get_last_mood()
        if animo is None:
            # Bloqueo sin ánimo — NMToast info en lugar de mostrar_mensaje
            top = self.window()
            NMToast.show(
                top,
                "Registrá tu ánimo primero para asociar esta actividad a tu estado actual.",
                variant="info",
                duration_ms=3000,
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
            _log.exception("Operation failed")

        # Visual feedback: cambiar borde de la NMCard al color del resultado
        color_map = {
            "hecha":     c["success"],
            "intentada": c["warning"],
            "no_pude":   c["error"],
        }
        card_widget.set_accent(color_map.get(resultado, c["accent"]))
        if hasattr(card_widget, "play_success"):
            card_widget.play_success()

        # Deshabilitar botones tras selección
        for btn in getattr(self, "_result_btns", []):
            btn.setEnabled(False)
        self._result_btns = []

        # Toast de confirmación
        labels = {"hecha": "Hecha ✓", "intentada": "Intentada", "no_pude": "No se pudo"}
        NMToast.show(
            self.window(),
            f"Actividad \"{nombre}\": {labels.get(resultado, resultado)}",
            variant="success" if resultado == "hecha" else "info",
            duration_ms=2000,
        )

    # ── Data access (lógica preservada exacta) ────────────────────────────────

    def _get_last_mood(self):
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT puntaje FROM termometro "
                "WHERE fecha = ? ORDER BY hora DESC LIMIT 1",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row:
                return row[0] if isinstance(row, tuple) else row["puntaje"]
        except Exception:
            _log.exception("Operation failed")
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
            _log.exception("Operation failed")

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

    # ── Hooks ─────────────────────────────────────────────────────────────────

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
                n = row[0]
                return f"{n} actividad{'es' if n > 1 else ''} ✔"
        except Exception:
            _log.exception("Operation failed")
        return ""
