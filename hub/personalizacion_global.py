"""
hub/personalizacion_global.py — Vista "Personalización" del Hub.

Reorganización owner v1.0 (2026-06-12): acá se setean SOLAMENTE los textos
de la Suite a nivel GLOBAL, un botón por módulo. Nada asignable vive acá:
el asignado de recordatorios/temporizador/rutina/activación es POR PACIENTE
y vive en su ficha → "Plan terapéutico".

Demolido sin fallback (decisión owner): presets de temporizador globales,
mensajes de apoyo globales y banco de actividades global.
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
)

from shared.components_qt import (
    NMButtonOutline,
    NMCard,
    NMListRow,
)
from shared.theme import TYPOGRAPHY
from shared.theme_qt import (
    V3_SP,
    norm_modo,
    qfont,
    v3c,
)

_log = logging.getLogger(__name__)


# (id, nombre de módulo, categoría en TEXT_KEYS, icono svg)
_MODULOS_TEXTOS = [
    ("animo", "Termómetro Emocional", "Termómetro Emocional", "mood"),
    ("avisos", "Recordatorios de Bienestar", "Recordatorios de Bienestar", "bell"),
    ("timer", "Temporizador de Actividades", "Temporizador", "timer"),
    ("registro", "Registro de Pensamientos (TCC)", "Registro TCC", "brain"),
    ("respiracion", "Guía de Respiración Animada", "Guía de Respiración", "leaf"),
    ("rutina", "Checklist de Rutina Diaria", "Checklist de Rutina", "routine"),
    ("evolucion", "Visualizador de Evolución Anímica", "Evolución Anímica", "chart"),
    ("actividades", "Asistente de Activación Conductual", "Activación Conductual", "run"),
]


class PersonalizacionGlobalView(QWidget):
    """Para todos los pacientes: textos de la Suite, un botón por módulo.

    page 0 = lista de módulos (NMListRow); page 1 = editor de textos del
    módulo elegido, con encabezado "Volver". Sin sub-columna fija vacía.
    """

    def __init__(self, modo: str, sb, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._editor = None
        self._setup()

    def _setup(self):
        self.setStyleSheet("background: transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["sm"])
        root.setSpacing(V3_SP["sm"])

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        root.addWidget(self._stack, stretch=1)

        # ── Página 0: lista de módulos ───────────────────────────────────────
        lista_page = QWidget()
        lista_page.setStyleSheet("background: transparent;")
        lp = QVBoxLayout(lista_page)
        lp.setContentsMargins(0, 0, 0, 0)
        lp.setSpacing(V3_SP["sm"])

        self._eyebrow = QLabel("Para todos los pacientes")
        self._eyebrow.setFont(
            qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
        )
        lp.addWidget(self._eyebrow)

        self._hint = QLabel(
            "Textos que la Suite muestra a todos los pacientes. "
            "Lo asignable por paciente vive en su Plan terapéutico."
        )
        self._hint.setWordWrap(True)
        self._hint.setFont(qfont("size_caption"))
        lp.addWidget(self._hint)

        card = NMCard(modo=self._modo, clickable=False, glow=False)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, V3_SP["xs"], 0, V3_SP["xs"])
        cl.setSpacing(0)
        self._rows = []
        for i, (mid, nombre, _categoria, icono) in enumerate(_MODULOS_TEXTOS):
            row = NMListRow(
                icon=icono,
                title=nombre,
                subtitle="Editar textos",
                modo=self._modo,
                divider=(i < len(_MODULOS_TEXTOS) - 1),
                clickable=True,
            )
            row.clicked.connect(lambda _mid=mid: self._open_editor(_mid))
            cl.addWidget(row)
            self._rows.append(row)
        lp.addWidget(card)
        lp.addStretch()
        self._stack.addWidget(lista_page)

        # ── Página 1: editor del módulo elegido ──────────────────────────────
        self._editor_page = QWidget()
        self._editor_page.setStyleSheet("background: transparent;")
        ep = QVBoxLayout(self._editor_page)
        ep.setContentsMargins(0, 0, 0, 0)
        ep.setSpacing(V3_SP["xs"])

        head = QHBoxLayout()
        head.setSpacing(V3_SP["sm"])
        self._btn_back = NMButtonOutline("‹ Volver", modo=self._modo, size="sm")
        self._btn_back.setFixedHeight(30)
        self._btn_back.clicked.connect(self._back_to_list)
        head.addWidget(self._btn_back)
        self._editor_title = QLabel("")
        self._editor_title.setFont(
            qfont("size_small", weight=TYPOGRAPHY["weight_semibold"])
        )
        head.addWidget(self._editor_title, stretch=1)
        ep.addLayout(head)

        self._editor_slot = QVBoxLayout()
        self._editor_slot.setContentsMargins(0, 0, 0, 0)
        ep.addLayout(self._editor_slot, stretch=1)
        self._stack.addWidget(self._editor_page)

        self._apply_text_styles()

    def _open_editor(self, module_id: str):
        from hub.editors.text_overrides_editor import TextOverridesEditor

        entry = next((m for m in _MODULOS_TEXTOS if m[0] == module_id), None)
        if entry is None:
            return
        _mid, nombre, categoria, _icono = entry

        if self._editor is not None:
            self._editor_slot.removeWidget(self._editor)
            self._editor.hide()
            self._editor.deleteLater()
            self._editor = None

        self._editor = TextOverridesEditor(
            self._sb, modo=self._modo, fixed_category=categoria
        )
        self._editor_slot.addWidget(self._editor)
        self._editor_title.setText(f"{nombre} · Textos")
        self._stack.setCurrentIndex(1)

    def _back_to_list(self):
        self._stack.setCurrentIndex(0)

    def _apply_text_styles(self):
        ink2 = v3c("ink_secondary", self._modo).name()
        self._eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._hint.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._editor_title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_text_styles()
        for row in self._rows:
            if hasattr(row, "_apply_theme"):
                row._apply_theme(self._modo)
        if self._editor is not None and hasattr(self._editor, "apply_theme"):
            self._editor.apply_theme(self._modo)
