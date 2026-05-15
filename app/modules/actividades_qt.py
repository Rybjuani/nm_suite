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
        NMModule, NMButton, NMButtonOutline, NMCard, NMToast, NMSegmentedChoice,
        ThemeManager, h_spacer, NMEmptyState, NMMoodContextHeader, NMCategoryFilter,
        NMActivityCard,
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
        NMModule, NMButton, NMButtonOutline, NMCard, NMToast, NMSegmentedChoice,
        ThemeManager, h_spacer, NMEmptyState, NMMoodContextHeader, NMCategoryFilter,
        NMActivityCard,
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
    MODULE_ICON  = "actividades"

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
            w = item.widget()
            if w:
                self._scroll_layout.removeWidget(w)
                w.deleteLater()

        # Reset stored state
        self._all_activities: list[dict] = []
        self._cards_widget = None

        # Get last mood
        animo = self._get_last_mood()

        if animo is None:
            self._show_no_mood()
            return

        # Mood context header (premium banner)
        self._mood_header = NMMoodContextHeader(
            score=animo, modo=self._modo, parent=self._scroll_content
        )
        self._scroll_layout.addWidget(self._mood_header)

        # Load all activities for this mood
        self._all_activities = self._get_activities(animo)

        if not self._all_activities:
            self._scroll_layout.addWidget(NMEmptyState(
                "fa5s.running",
                "Sin sugerencias",
                "Completá un registro de ánimo primero.",
                self._scroll_content,
            ))
            return

        # Category filter chips — derived from loaded activities
        cats = sorted({act.get("categoria", "Autocuidado") for act in self._all_activities})
        self._cat_filter = NMCategoryFilter(
            cats, modo=self._modo, parent=self._scroll_content
        )
        self._cat_filter.filter_changed.connect(self._on_category_filter)
        self._scroll_layout.addWidget(self._cat_filter)

        # Cards container widget (rebuilt when filter changes)
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(GAP_CARDS)
        self._scroll_layout.addWidget(self._cards_widget)

        self._rebuild_cards("")

    def _on_category_filter(self, cat: str):
        self._rebuild_cards(cat)

    def _rebuild_cards(self, cat: str):
        """Clear and repopulate activity cards, optionally filtered by category."""
        if not hasattr(self, "_cards_layout") or self._cards_widget is None:
            return
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            w = item.widget()
            if w:
                self._cards_layout.removeWidget(w)
                w.deleteLater()

        activities = self._all_activities
        if cat:
            activities = [a for a in activities if a.get("categoria", "") == cat]

        if not activities:
            self._cards_layout.addWidget(NMEmptyState(
                "fa5s.running",
                "Sin actividades",
                f"No hay actividades en la categoría \"{cat}\".",
                self._cards_widget,
            ))
            return

        for act in activities:
            self._build_activity_card(act)

    def _show_no_mood(self):
        self._scroll_layout.addWidget(NMEmptyState(
            "fa5s.running",
            "Sin sugerencias",
            "Completá un registro de ánimo primero.",
            self._scroll_content,
        ))

    def _build_activity_card(self, act: dict):
        cat = act.get("categoria", "Autocuidado")
        nombre = act.get("nombre", "Actividad")
        card = NMActivityCard(
            nombre,
            act.get("descripcion", ""),
            category=cat,
            modo=self._modo,
            parent=self._scroll_content,
        )
        card.completed.connect(
            lambda n=nombre, cd=card: self._register_result(n, "hecha", cd, None)
        )
        card.skipped.connect(
            lambda n=nombre, cd=card: self._register_result(n, "no_pude", cd, None)
        )

        target = getattr(self, "_cards_layout", self._scroll_layout)
        target.addWidget(card)

    # ── _register_result (lógica preservada exacta) ───────────────────────────

    def _register_result(self, nombre: str, resultado: str, card_widget,
                         seg: NMSegmentedChoice | None):
        c = colors(self._modo)
        animo = self._get_last_mood()
        if animo is None:
            # Bloqueo sin ánimo — NMToast info en lugar de mostrar_mensaje
            top = self.window()
            NMToast.display(
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
        if hasattr(card_widget, "set_accent"):
            card_widget.set_accent(color_map.get(resultado, c["accent"]))
        if hasattr(card_widget, "play_success"):
            card_widget.play_success()

        # Deshabilitar botones tras selección
        if seg is not None:
            for btn in seg._btns.values():
                btn.setEnabled(False)
        elif hasattr(card_widget, "set_completed") and resultado == "hecha":
            card_widget.set_completed(True)

        # Toast de confirmación
        labels = {"hecha": "Hecha ✓", "intentada": "Intentada", "no_pude": "No se pudo"}
        NMToast.display(
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
                "ORDER BY RANDOM() LIMIT 9",
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
        return pool[:]  # return all matching; NMCategoryFilter handles display

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
                return f"{n} actividad{'es' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
