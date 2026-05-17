"""
app/modules/registro_tcc_qt.py — Registro TCC v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > TCC):

  Header        eyebrow + NMTCCStepper (4 pasos)
  2-col main    LEFT: QStackedWidget con 4 pages:
                       1. Situación (textarea + counter X/500)
                       2. Emoción   (grid 4×2 _EmotionTile + NMHeatBar
                                     intensidad fría→caliente)
                       3. Pensamiento (textarea + counter +
                                       distorsiones detectadas + tip glow)
                       4. Respuesta  (textarea)
                RIGHT: _ResumenCard con datos acumulados
  Nav           NMButtonOutline ghost "Anterior" + NMButton gradient
                "Siguiente"/"Guardar"
  Footer        _RegistrosPreviosTable con últimos 5 registros

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _KWORDS, _DISTORTION_CATEGORY, _DISTORTION_ICON, _detect_distortions(),
  _save_current_step_data(), _next_step(), _prev_step(), _guardar(),
  _has_registros_hoy(), get_card_status(), schema DB ``pensamientos``.
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer
from PyQt6 import sip
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QTextEdit, QLineEdit, QFrame, QScrollArea, QSizePolicy,
    QStackedWidget,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMToast, ThemeManager,
        NMCard, NMIcon, NMTCCStepper, NMHeatBar,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_lineedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMToast, ThemeManager,
        NMCard, NMIcon, NMTCCStepper, NMHeatBar,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qfont_mono,
        v3c, V3_SP, V3_RD,
        stylesheet_textedit, stylesheet_lineedit, stylesheet_scrollarea,
        PAD_CONTAINER,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled


# ── Lógica de distorsiones (preservada exacta) ───────────────────────────────

_KWORDS = {
    "Catastrofización":       ["siempre", "nunca", "todo", "nada", "horrible", "terrible", "insoportable"],
    "Lectura mental":         ["seguro que piensa", "piensan que", "creen que", "deben pensar"],
    "Filtro mental":          ["solo", "únicamente", "nada más"],
    "Etiquetado":             ["soy un", "soy una", "es un", "es una"],
    "Debería":                ["debería", "tendría que", "tengo que"],
    "Personalización":        ["por mi culpa", "es culpa mía", "yo causé"],
    "Sobregeneralización":    ["todos", "nadie", "siempre", "nunca", "cada vez"],
    "Descalificación":        ["no cuenta", "fue suerte", "no importa"],
    "Pensamiento dicotómico": ["o todo o nada", "blanco o negro", "perfecto o fracaso"],
    "Magnificación":          ["es lo peor", "arruiné", "destruí"],
}

_DISTORTION_CATEGORY = {
    "Catastrofización":       "cat",
    "Magnificación":          "cat",
    "Personalización":        "cat",
    "Debería":                "cat",
    "Pensamiento dicotómico": "todo",
    "Sobregeneralización":    "todo",
    "Etiquetado":             "todo",
    "Filtro mental":          "min",
    "Descalificación":        "min",
    "Lectura mental":         "min",
}

# v3: iconos SVG en lugar de emoji Unicode
_DISTORTION_ICON = {"cat": "flame", "todo": "warning", "min": "chart"}

_STEP_NAMES = ["Situación", "Emoción", "Pensamiento", "Respuesta"]

# Grid 4×2 de emociones según README v3
_EMOTIONS_GRID = [
    # (label, icon_v3, color_token)
    ("Ansiedad",  "bolt",    "warning"),
    ("Tristeza",  "water",   "info"),
    ("Enojo",     "flame",   "danger"),
    ("Miedo",     "thought", "violet"),
    ("Culpa",     "heart",   "warning"),
    ("Vergüenza", "user",    "violet"),
    ("Soledad",   "moon",    "info"),
    ("Otro",      "dots",    "text2"),
]


# ── _EmotionTile ─────────────────────────────────────────────────────────────

class _EmotionTile(NMCard):
    """Tile clickeable v3: icono + label. Activa = glow + border accent."""

    def __init__(self, label: str, icon_name: str, color_token: str,
                 modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=True, glow=False)
        self._label_text = label
        self._icon_name = icon_name
        self._color_token = color_token
        self._selected = False
        self.setMinimumHeight(96)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["md"],
                                V3_SP["md"], V3_SP["md"])
        lay.setSpacing(V3_SP["xs"] + 2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon = NMIcon(self._icon_name, size=28,
                            color_key=self._color_token, modo=self._modo)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self._lbl = QLabel(self._label_text)
        self._lbl.setFont(qfont("size_small",
                                 weight=TYPOGRAPHY["weight_semibold"]))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._lbl)
        self._apply_tile_styles()

    def set_selected(self, selected: bool):
        if selected != self._selected:
            self._selected = selected
            # set_glow toma el accent del tile como halo color
            if selected:
                self.set_accent(v3c(self._color_token, self._modo).name())
            self.set_glow(selected)
            self._apply_tile_styles()

    def is_selected(self) -> bool:
        return self._selected

    def label_text(self) -> str:
        return self._label_text

    def _apply_tile_styles(self):
        color = (v3c(self._color_token, self._modo).name() if self._selected
                 else v3c("text", self._modo).name())
        self._lbl.setStyleSheet(f"color: {color}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._apply_tile_styles()


# ── _ResumenCard (sidebar lateral derecha) ──────────────────────────────────

class _ResumenCard(NMCard):
    """Card lateral que muestra los pasos completados del wizard."""

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["sm"])

        self._eyebrow = QLabel("RESUMEN")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)

        self._rows: dict[str, tuple[QLabel, QLabel]] = {}
        for key, title in (
            ("situacion",    "Situación"),
            ("emocion",      "Emoción"),
            ("intensidad",   "Intensidad"),
            ("pensamiento",  "Pensamiento"),
            ("distorsiones", "Distorsiones"),
            ("respuesta",    "Respuesta"),
        ):
            row = QVBoxLayout()
            row.setSpacing(0)
            t_lbl = QLabel(title.upper())
            t_lbl.setFont(qfont("size_caption_xs",
                                 weight=TYPOGRAPHY["weight_semibold"]))
            row.addWidget(t_lbl)
            v_lbl = QLabel("—")
            v_lbl.setFont(qfont("size_small"))
            v_lbl.setWordWrap(True)
            row.addWidget(v_lbl)
            self._rows[key] = (t_lbl, v_lbl)
            wrap = QWidget()
            wrap.setLayout(row)
            lay.addWidget(wrap)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(1)
            lay.addWidget(sep)
            self._rows[key + "_sep"] = (sep,)
        lay.addStretch()
        self._apply_resumen_styles()

    def update_data(self, data: dict):
        """Refresca cada fila con los datos actuales del wizard."""
        situacion = data.get("situacion") or "—"
        emocion = data.get("emocion") or "—"
        intensidad = data.get("intensidad", 5)
        pensamiento = data.get("pensamiento") or "—"
        distorsiones = data.get("distorsiones") or "Ninguna detectada"
        respuesta = data.get("respuesta") or "—"
        # Truncar snippets largos
        def _snip(text, n=80):
            t = text.strip()
            return t if len(t) <= n else t[:n - 1] + "…"
        self._rows["situacion"][1].setText(_snip(situacion, 90))
        self._rows["emocion"][1].setText(emocion)
        self._rows["intensidad"][1].setText(f"{intensidad}/10")
        self._rows["pensamiento"][1].setText(_snip(pensamiento, 90))
        self._rows["distorsiones"][1].setText(_snip(distorsiones, 100))
        self._rows["respuesta"][1].setText(_snip(respuesta, 90))

    def _apply_resumen_styles(self):
        c_eye = v3c("text3", self._modo).name()
        c_val = v3c("text", self._modo).name()
        c_sep = v3c("borderSoft", self._modo).name()
        self._eyebrow.setStyleSheet(
            f"color: {c_eye}; background: transparent;")
        for key, refs in self._rows.items():
            if key.endswith("_sep"):
                refs[0].setStyleSheet(f"background-color: {c_sep};")
            else:
                title_lbl, value_lbl = refs
                title_lbl.setStyleSheet(
                    f"color: {c_eye}; background: transparent;")
                value_lbl.setStyleSheet(
                    f"color: {c_val}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_resumen_styles()


# ── _TipCard (card glow con tip terapéutico) ────────────────────────────────

class _TipCard(NMCard):
    """Card glow con tip terapéutico v3 (página de Pensamiento)."""

    def __init__(self, text: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=True)
        self._tip_text = text
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"],
                                V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])
        self._icon = NMIcon("bulb", size=24, color_key="teal",
                            modo=self._modo)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(2)
        self._eyebrow = QLabel("TIP TERAPÉUTICO")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        col.addWidget(self._eyebrow)
        self._text_lbl = QLabel(self._tip_text)
        self._text_lbl.setFont(qfont("size_small"))
        self._text_lbl.setWordWrap(True)
        col.addWidget(self._text_lbl)
        lay.addLayout(col, stretch=1)
        self._apply_tip_styles()

    def _apply_tip_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._text_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._apply_tip_styles()


# ── ModuloRegistroTCC v3 ────────────────────────────────────────────────────

class ModuloRegistroTCC(NMModule):
    MODULE_TITLE = "Registro TCC"
    MODULE_ICON  = "registro_tcc"

    def build_ui(self):
        self._step = 0
        self._data = {
            "situacion": "", "emocion": "", "intensidad": 5,
            "pensamiento": "", "distorsiones": "", "respuesta": "",
        }
        self._emotion_tiles: list[_EmotionTile] = []

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        outer.addWidget(scroll)
        self._scroll = scroll

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["lg"],
                                V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["lg"])

        # 1. Eyebrow + Stepper
        self._eyebrow = QLabel("REGISTRO TCC")
        self._eyebrow.setFont(qfont("size_caption_xs",
                                     weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._eyebrow)

        self._stepper = NMTCCStepper(_STEP_NAMES, modo=self._modo)
        lay.addWidget(self._stepper)

        # 2. Main 2-col: LEFT stack + RIGHT resumen
        main_row = QHBoxLayout()
        main_row.setSpacing(V3_SP["lg"])

        # LEFT: stack de pasos en una NMCard
        steps_card = NMCard(modo=self._modo, clickable=False)
        steps_card.setMinimumWidth(520)
        sc_lay = QVBoxLayout(steps_card)
        sc_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"],
                                   V3_SP["lg"], V3_SP["lg"])
        sc_lay.setSpacing(V3_SP["md"])
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sc_lay.addWidget(self._stack)

        self._pages: list[QWidget] = []
        self._build_page_situacion()
        self._build_page_emocion()
        self._build_page_pensamiento()
        self._build_page_respuesta()

        # Error label
        self._error_lbl = QLabel("")
        self._error_lbl.setFont(qfont("size_small",
                                       weight=TYPOGRAPHY["weight_semibold"]))
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sc_lay.addWidget(self._error_lbl)

        # Nav (Anterior ghost + Siguiente/Guardar gradient)
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(V3_SP["sm"])
        self._btn_prev = NMButton("Anterior", parent=self._content,
                                   modo=self._modo, variant="ghost",
                                   size="md", width=120)
        self._btn_prev.clicked.connect(self._prev_step)
        nav_layout.addWidget(self._btn_prev)
        nav_layout.addStretch()
        self._btn_next = NMButton("Siguiente", parent=self._content,
                                   modo=self._modo, variant="gradient",
                                   size="md", width=160)
        self._btn_next.clicked.connect(self._next_step)
        nav_layout.addWidget(self._btn_next)
        sc_lay.addLayout(nav_layout)

        main_row.addWidget(steps_card, stretch=2)

        # RIGHT: ResumenCard
        self._resumen = _ResumenCard(modo=self._modo)
        self._resumen.setMinimumWidth(260)
        self._resumen.setMaximumWidth(320)
        main_row.addWidget(self._resumen, stretch=1)

        lay.addLayout(main_row)

        # 3. Footer: Registros previos
        prev_section_lbl = QLabel("REGISTROS PREVIOS")
        prev_section_lbl.setFont(qfont("size_caption_xs",
                                        weight=TYPOGRAPHY["weight_semibold"]))
        prev_section_lbl.setContentsMargins(0, V3_SP["sm"], 0, 0)
        lay.addWidget(prev_section_lbl)
        self._prev_section_lbl = prev_section_lbl

        self._prev_card = NMCard(modo=self._modo, clickable=False)
        self._prev_lay = QVBoxLayout(self._prev_card)
        self._prev_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"],
                                            V3_SP["lg"], V3_SP["md"])
        self._prev_lay.setSpacing(V3_SP["xs"] + 2)
        lay.addWidget(self._prev_card)
        self._cargar_registros_previos()

        self._apply_text_styles()
        self._show_step()
        self._resumen.update_data(self._data)

    def _apply_text_styles(self):
        c = v3c("text3", self._modo).name()
        self._eyebrow.setStyleSheet(
            f"color: {c}; background: transparent;")
        self._prev_section_lbl.setStyleSheet(
            f"color: {c}; background: transparent;")
        self._error_lbl.setStyleSheet(
            f"color: {v3c('warning', self._modo).name()}; "
            f"background: transparent;")

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_txt_situacion"):
            self._txt_situacion.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_txt_pensamiento"):
            self._txt_pensamiento.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_txt_respuesta"):
            self._txt_respuesta.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_scroll"):
            self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        self.update()

    # ── Page builders ────────────────────────────────────────────────────────

    def _make_page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(V3_SP["sm"])
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        return page, layout

    def _make_title(self, text: str, subtitle: str = "") -> list[QLabel]:
        widgets = []
        h = QLabel(text)
        h.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_bold"]))
        h.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        widgets.append(h)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(qfont("size_small"))
            sub.setWordWrap(True)
            sub.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; "
                f"background: transparent;")
            widgets.append(sub)
        return widgets

    def _build_page_situacion(self):
        page, layout = self._make_page()
        for lbl in self._make_title(
                "¿Qué pasó?",
                "Describí brevemente la situación que desencadenó el malestar."):
            layout.addWidget(lbl)

        self._txt_situacion = QTextEdit()
        self._txt_situacion.setMinimumHeight(140)
        self._txt_situacion.setStyleSheet(stylesheet_textedit(self._modo))
        self._txt_situacion.textChanged.connect(self._update_situacion_count)
        layout.addWidget(self._txt_situacion)

        self._situacion_count_lbl = QLabel("0 / 500")
        self._situacion_count_lbl.setFont(qfont_mono(10, bold=False))
        self._situacion_count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._situacion_count_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        layout.addWidget(self._situacion_count_lbl)
        layout.addStretch()
        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_emocion(self):
        page, layout = self._make_page()
        for lbl in self._make_title("¿Qué sentiste?"):
            layout.addWidget(lbl)

        # Grid 4×2 de _EmotionTile
        grid = QGridLayout()
        grid.setSpacing(V3_SP["sm"])
        for i, (label, icon_name, color_token) in enumerate(_EMOTIONS_GRID):
            tile = _EmotionTile(label, icon_name, color_token,
                                 modo=self._modo)
            tile.clicked.connect(lambda l=label: self._on_emotion_picked(l))
            r, c = divmod(i, 4)
            grid.addWidget(tile, r, c)
            self._emotion_tiles.append(tile)
        layout.addLayout(grid)

        # Intensidad: header + NMHeatBar
        self._lbl_intensidad_header = QLabel(
            f"Intensidad: {self._data['intensidad']}/10")
        self._lbl_intensidad_header.setFont(qfont("size_small",
                                                   weight=TYPOGRAPHY["weight_semibold"]))
        self._lbl_intensidad_header.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;")
        self._lbl_intensidad_header.setContentsMargins(0, V3_SP["md"], 0, 0)
        layout.addWidget(self._lbl_intensidad_header)

        self._heat_bar = NMHeatBar(
            value=int(self._data["intensidad"] * 10),
            modo=self._modo, parent=page)
        self._heat_bar.value_changed.connect(self._on_intensidad_heat)
        layout.addWidget(self._heat_bar)
        layout.addStretch()
        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_pensamiento(self):
        page, layout = self._make_page()
        for lbl in self._make_title(
                "Pensamiento automático",
                "¿Qué pensaste en ese momento? Escribilo tal como apareció."):
            layout.addWidget(lbl)

        self._txt_pensamiento = QTextEdit()
        self._txt_pensamiento.setMinimumHeight(110)
        self._txt_pensamiento.setStyleSheet(stylesheet_textedit(self._modo))
        self._txt_pensamiento.textChanged.connect(lambda: self._detect_distortions(None))
        self._txt_pensamiento.textChanged.connect(self._update_pensamiento_count)
        layout.addWidget(self._txt_pensamiento)

        self._pensamiento_count_lbl = QLabel("0 / 500")
        self._pensamiento_count_lbl.setFont(qfont_mono(10, bold=False))
        self._pensamiento_count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._pensamiento_count_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        layout.addWidget(self._pensamiento_count_lbl)

        self._dist_eyebrow = QLabel("POSIBLES DISTORSIONES DETECTADAS")
        self._dist_eyebrow.setFont(qfont("size_caption_xs",
                                          weight=TYPOGRAPHY["weight_semibold"]))
        self._dist_eyebrow.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; "
            f"background: transparent;")
        self._dist_eyebrow.setContentsMargins(0, V3_SP["sm"], 0, 0)
        layout.addWidget(self._dist_eyebrow)

        self._distortion_frame = QWidget()
        self._distortion_frame.setStyleSheet("background: transparent;")
        self._distortion_layout = QHBoxLayout(self._distortion_frame)
        self._distortion_layout.setContentsMargins(0, 0, 0, 0)
        self._distortion_layout.setSpacing(V3_SP["xs"] + 2)
        self._distortion_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._distortion_frame)

        # Tip terapéutico (card glow)
        tip = _TipCard(
            "Los pensamientos no son hechos. Preguntate: "
            "¿qué evidencia tengo? ¿qué le diría a un amigo en esta situación?",
            modo=self._modo)
        layout.addWidget(tip)
        self._tip_card = tip
        layout.addStretch()

        self._detect_distortions(None)
        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_respuesta(self):
        page, layout = self._make_page()
        for lbl in self._make_title(
                "Respuesta alternativa",
                "¿Cómo podrías pensar de manera más equilibrada y compasiva?"):
            layout.addWidget(lbl)

        self._txt_respuesta = QTextEdit()
        self._txt_respuesta.setMinimumHeight(140)
        self._txt_respuesta.setStyleSheet(stylesheet_textedit(self._modo))
        layout.addWidget(self._txt_respuesta)
        layout.addStretch()
        self._stack.addWidget(page)
        self._pages.append(page)

    # ── emotion tile picker ──────────────────────────────────────────────────

    def _on_emotion_picked(self, label: str):
        self._data["emocion"] = label
        for tile in self._emotion_tiles:
            tile.set_selected(tile.label_text() == label)
        self._resumen.update_data(self._data)

    # ── char counters ────────────────────────────────────────────────────────

    def _update_situacion_count(self):
        try:
            if sip.isdeleted(self._situacion_count_lbl):
                return
            n = len(self._txt_situacion.toPlainText())
        except Exception:
            return
        col = (v3c("warning", self._modo).name() if n > 500
               else v3c("text3", self._modo).name())
        self._situacion_count_lbl.setText(f"{n} / 500")
        self._situacion_count_lbl.setStyleSheet(
            f"color: {col}; background: transparent;")

    def _update_pensamiento_count(self):
        try:
            if sip.isdeleted(self._pensamiento_count_lbl):
                return
            n = len(self._txt_pensamiento.toPlainText())
        except Exception:
            return
        col = (v3c("warning", self._modo).name() if n > 500
               else v3c("text3", self._modo).name())
        self._pensamiento_count_lbl.setText(f"{n} / 500")
        self._pensamiento_count_lbl.setStyleSheet(
            f"color: {col}; background: transparent;")

    # ── distortion detection (lógica preservada exacta) ──────────────────────

    def _detect_distortions(self, _event):
        _log.debug(f"Detecting distortions, modo={getattr(self, '_modo', 'N/A')}")
        text = ""
        try:
            text = self._txt_pensamiento.toPlainText().strip().lower()
        except Exception:
            text = self._data.get("pensamiento", "").lower()

        found = []
        for distortion, keywords in _KWORDS.items():
            for kw in keywords:
                if kw in text:
                    found.append(distortion)
                    break

        # Clear old chips
        while self._distortion_layout.count():
            item = self._distortion_layout.takeAt(0)
            w = item.widget()
            if w:
                self._distortion_layout.removeWidget(w)
                w.deleteLater()

        cat_colors = {
            "cat":  v3c("danger",  self._modo).name(),
            "todo": v3c("violet",  self._modo).name(),
            "min":  v3c("warning", self._modo).name(),
        }
        if found:
            for d in found:
                cat = _DISTORTION_CATEGORY.get(d, "min")
                fg = cat_colors.get(cat, v3c("warning", self._modo).name())
                # Chip: icon + label
                chip_widget = QWidget()
                chip_widget.setStyleSheet("background: transparent;")
                chip_lay = QHBoxLayout(chip_widget)
                chip_lay.setContentsMargins(V3_SP["sm"], 2, V3_SP["sm"], 2)
                chip_lay.setSpacing(V3_SP["xs"])
                icon_name = _DISTORTION_ICON.get(cat, "info")
                icon = NMIcon(icon_name, size=14, color=fg, modo=self._modo)
                chip_lay.addWidget(icon)
                label = QLabel(d)
                label.setFont(qfont("size_caption",
                                     weight=TYPOGRAPHY["weight_semibold"]))
                label.setStyleSheet(
                    f"color: {fg}; background: transparent;")
                chip_lay.addWidget(label)
                # Wrap in styled frame
                wrapper = QFrame()
                wrapper.setObjectName("DistortionChip")
                wlay = QVBoxLayout(wrapper)
                wlay.setContentsMargins(0, 0, 0, 0)
                wlay.addWidget(chip_widget)
                # Convert hex fg → rgba for soft bg
                qc = QColor(fg)
                bg_rgba = f"rgba({qc.red()},{qc.green()},{qc.blue()},36)"
                wrapper.setStyleSheet(
                    f"QFrame#DistortionChip {{ background: {bg_rgba}; "
                    f"border: 1px solid {fg}; border-radius: 10px; }}")
                self._distortion_layout.addWidget(wrapper)
        else:
            none_lbl = QLabel("Ninguna detectada aún")
            none_lbl.setFont(qfont("size_small"))
            none_lbl.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            self._distortion_layout.addWidget(none_lbl)

        self._data["distorsiones"] = ", ".join(found)
        if hasattr(self, "_resumen"):
            self._resumen.update_data(self._data)

    # ── intensidad ───────────────────────────────────────────────────────────

    def _on_intensidad_heat(self, value: int):
        self._on_intensidad(round(value / 10))

    def _on_intensidad(self, value: int):
        self._data["intensidad"] = value
        try:
            self._lbl_intensidad_header.setText(f"Intensidad: {value}/10")
        except Exception:
            _log.exception("Operation failed")
        if hasattr(self, "_resumen"):
            self._resumen.update_data(self._data)

    # ── step navigation ──────────────────────────────────────────────────────

    def _update_progress(self):
        if hasattr(self, "_stepper"):
            self._stepper.set_step(self._step)

    def _show_step(self):
        try:
            self._update_progress()
            if 0 <= self._step < len(self._pages):
                self._stack.setCurrentWidget(self._pages[self._step])
            self._btn_prev.setEnabled(self._step > 0)
            if self._step == 3:
                self._btn_next.setText("Guardar")
            else:
                self._btn_next.setText("Siguiente")
        except Exception as e:
            _log.error(f"Error in _show_step: {e}")
            import traceback
            traceback.print_exc()

    def _save_current_step_data(self):
        if self._step == 0:
            try:
                self._data["situacion"] = self._txt_situacion.toPlainText().strip()
            except Exception:
                pass
        elif self._step == 1:
            # La emoción se actualiza vía _on_emotion_picked; nada extra
            pass
        elif self._step == 2:
            try:
                self._data["pensamiento"] = self._txt_pensamiento.toPlainText().strip()
            except Exception:
                pass
            try:
                self._detect_distortions(None)
            except Exception as e:
                _log.warning(f"Distortion detection failed: {e}")
        elif self._step == 3:
            try:
                self._data["respuesta"] = self._txt_respuesta.toPlainText().strip()
            except Exception:
                pass
        if hasattr(self, "_resumen"):
            self._resumen.update_data(self._data)

    def _next_step(self):
        try:
            self._save_current_step_data()

            # Validación por paso (preservada)
            campo_requerido = {
                0: ("situacion",   "Describí la situación para continuar."),
                1: ("emocion",     "Seleccioná la emoción que sentiste."),
                2: ("pensamiento", "Escribí el pensamiento automático."),
            }
            if self._step in campo_requerido:
                campo, hint = campo_requerido[self._step]
                if not self._data.get(campo, "").strip():
                    self._error_lbl.setText(hint)
                    return
                self._error_lbl.setText("")

            if self._step == 3:
                self._guardar()
                return

            self._step += 1
            self._show_step()
        except Exception as e:
            _log.error(f"Error in _next_step: {e}")
            import traceback
            traceback.print_exc()

    def _prev_step(self):
        self._save_current_step_data()
        if self._step > 0:
            self._step -= 1
            self._show_step()

    # ── Guardar (lógica preservada exacta) ───────────────────────────────────

    def _guardar(self):
        self._save_current_step_data()
        d = self._data
        if not d["situacion"] or not d["pensamiento"]:
            self._error_lbl.setText("Faltan campos obligatorios (situación + pensamiento).")
            QTimer.singleShot(2500, lambda: self._error_lbl.setText("")
                              if not sip.isdeleted(self) else None)
            return

        try:
            conn = obtener_conexion()
            conn.execute(
                "INSERT INTO pensamientos "
                "(fecha, hora, situacion, emocion, intensidad, pensamiento, "
                "respuesta_alternativa, distorsiones) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fecha_hoy(), hora_actual(),
                 d["situacion"], d["emocion"], d["intensidad"],
                 d["pensamiento"], d["respuesta"], d["distorsiones"]),
            )
            conn.commit()
            conn.close()
        except Exception:
            NMToast.display(self.window(),
                            "Error al guardar el registro",
                            variant="error")
            return

        if hasattr(self._btn_next, "play_success"):
            self._btn_next.play_success()
        self._show_success_page()
        self._cargar_registros_previos()
        QTimer.singleShot(3000, lambda: self._reset()
                          if not sip.isdeleted(self) else None)

    def _show_success_page(self):
        success = QWidget()
        success.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(success)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(V3_SP["sm"])
        check_icon = NMIcon("check", size=64, color_key="success",
                             modo=self._modo)
        layout.addWidget(check_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl = QLabel("Registro guardado")
        title_lbl.setFont(qfont("size_h2",
                                 weight=TYPOGRAPHY["weight_bold"]))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"background: transparent;")
        layout.addWidget(title_lbl)
        sub_lbl = QLabel("Buen trabajo al identificar y cuestionar el pensamiento.")
        sub_lbl.setFont(qfont("size_body"))
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;")
        layout.addWidget(sub_lbl)
        self._stack.addWidget(success)
        self._stack.setCurrentWidget(success)
        self._btn_prev.setEnabled(False)
        self._btn_next.setEnabled(False)

    def _reset(self):
        self._step = 0
        self._data = {
            "situacion": "", "emocion": "", "intensidad": 5,
            "pensamiento": "", "distorsiones": "", "respuesta": "",
        }
        try:
            self._txt_situacion.clear()
            for tile in self._emotion_tiles:
                tile.set_selected(False)
            self._txt_pensamiento.clear()
            self._txt_respuesta.clear()
            if hasattr(self, "_heat_bar"):
                self._heat_bar.set_value(50)
        except Exception:
            _log.exception("Operation failed")

        self._btn_next.setEnabled(True)
        self._btn_prev.setEnabled(True)
        self._error_lbl.setText("")
        self._show_step()
        self._resumen.update_data(self._data)

    # ── Registros previos (footer) ───────────────────────────────────────────

    def _load_recent_records(self, limit: int = 5):
        if visual_qa_enabled():
            return [
                ("2026-05-17", "10:30:00", "Reunión con mi jefe",
                 "Ansiedad", 7, "Catastrofización"),
                ("2026-05-16", "20:15:00", "Discusión con mi pareja",
                 "Tristeza", 6, "Personalización"),
                ("2026-05-15", "08:00:00", "Llegué tarde al trabajo",
                 "Culpa", 5, "Debería"),
            ]
        try:
            conn = obtener_conexion()
            rows = conn.execute(
                "SELECT fecha, hora, situacion, emocion, intensidad, distorsiones "
                "FROM pensamientos ORDER BY fecha DESC, hora DESC LIMIT ?",
                (limit,)
            ).fetchall()
            conn.close()
            out = []
            for r in rows:
                if hasattr(r, "keys"):
                    out.append((r["fecha"], r["hora"], r["situacion"] or "",
                                r["emocion"] or "", int(r["intensidad"] or 0),
                                r["distorsiones"] or ""))
                else:
                    out.append((r[0], r[1], r[2] or "", r[3] or "",
                                int(r[4] or 0), r[5] or ""))
            return out
        except Exception:
            _log.exception("Error cargando registros TCC previos")
            return []

    def _cargar_registros_previos(self):
        # Clear
        while self._prev_lay.count():
            item = self._prev_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        records = self._load_recent_records(5)
        if not records:
            empty = QLabel("Aún no hay registros previos.")
            empty.setFont(qfont("size_small"))
            empty.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            self._prev_lay.addWidget(empty)
            return
        for fecha, hora, situacion, emocion, intensidad, distorsiones in records:
            row = QHBoxLayout()
            row.setSpacing(V3_SP["md"])
            # Fecha mono
            date_lbl = QLabel(self._format_date(fecha, hora))
            date_lbl.setFont(qfont_mono(10, bold=False))
            date_lbl.setStyleSheet(
                f"color: {v3c('text3', self._modo).name()}; "
                f"background: transparent;")
            date_lbl.setFixedWidth(110)
            row.addWidget(date_lbl)
            # Situación (snippet)
            snippet = situacion if len(situacion) <= 60 else situacion[:59] + "…"
            sit_lbl = QLabel(snippet)
            sit_lbl.setFont(qfont("size_small"))
            sit_lbl.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; "
                f"background: transparent;")
            row.addWidget(sit_lbl, stretch=1)
            # Emoción chip
            emo_lbl = QLabel(emocion or "—")
            emo_lbl.setFont(qfont("size_caption",
                                   weight=TYPOGRAPHY["weight_semibold"]))
            emo_lbl.setContentsMargins(V3_SP["sm"], 2, V3_SP["sm"], 2)
            emo_color = v3c("teal", self._modo).name()
            qc = QColor(emo_color)
            emo_lbl.setStyleSheet(
                f"color: {emo_color}; "
                f"background: rgba({qc.red()},{qc.green()},{qc.blue()},36); "
                f"border-radius: 8px;")
            row.addWidget(emo_lbl)
            # Intensidad
            int_lbl = QLabel(f"{intensidad}/10")
            int_lbl.setFont(qfont_mono(10, bold=False))
            int_lbl.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; "
                f"background: transparent;")
            int_lbl.setFixedWidth(48)
            row.addWidget(int_lbl)
            wrap = QWidget()
            wrap.setLayout(row)
            self._prev_lay.addWidget(wrap)

    def _format_date(self, fecha: str, hora: str) -> str:
        try:
            import datetime as dt
            d = dt.datetime.strptime(fecha, "%Y-%m-%d").date()
            today = dt.date.today()
            if d == today:
                return f"Hoy · {hora[:5]}"
            if d == today - dt.timedelta(days=1):
                return f"Ayer · {hora[:5]}"
            return f"{d.strftime('%d/%m')} · {hora[:5]}"
        except Exception:
            return f"{fecha} {hora[:5]}"

    # ── Hooks ────────────────────────────────────────────────────────────────

    def _has_registros_hoy(self) -> bool:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) as n FROM pensamientos WHERE fecha = ?",
                (fecha_hoy(),),
            ).fetchone()
            conn.close()
            return bool(row and row[0] > 0)
        except Exception:
            _log.exception("Operation failed")
            return False

    def on_enter(self):
        """Resetea el wizard al volver al módulo."""
        self._reset()
        self._cargar_registros_previos()

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) as n FROM pensamientos WHERE fecha = ?",
                (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} registro{'s' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
