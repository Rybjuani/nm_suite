"""
app/modules/registro_tcc_qt.py — Registro TCC v3 (PyQt6)

Estructura según design_handoff_neuromood_v3 (Suite > TCC):

  Header        eyebrow + NMStepper (4 pasos)
  2-col main    LEFT: QStackedWidget con 4 pages:
                       1. Situación (textarea + counter X/500)
                       2. Emoción   (grid 4×2 _EmotionTile + NMHeatBar
                                     intensidad fría→caliente)
                       3. Pensamiento (textarea + counter +
                                       distorsiones detectadas + tip glow)
                       4. Respuesta  (textarea)
                RIGHT: _ResumenCard con datos acumulados
  Nav           NMButton secondary "Anterior" (botón real, no texto suelto) +
                NMButton gradient "Siguiente"/"Guardar" (CTA final distinguible)
  Footer        _RegistrosPreviosTable con últimos 5 registros

LÓGICA DE NEGOCIO PRESERVADA EXACTA:
  _KWORDS, _DISTORTION_CATEGORY, _DISTORTION_ICON, _detect_distortions(),
  _save_current_step_data(), _next_step(), _prev_step(), _guardar(),
  _has_registros_hoy(), get_card_status(), schema DB ``pensamientos``.
"""

import os
import sys
import json
from shared.crash_log import redact
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6 import sip
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QStackedWidget,
    QScrollArea,
)

try:
    from shared.components import (
        NMModule,
        NMButton,
        NMButtonOutline,
        NMToast,
        ThemeManager,
        NMCard,
        NMIcon,
        NMStepper,
        NMHeatBar,
        NMTextArea,
        NMInput,
    )
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        V3_RD,
        stylesheet_textedit,
        stylesheet_lineedit,
        stylesheet_scrollarea,
        PAD_CONTAINER,
        eyebrow_font,
        eyebrow_style,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, conexion
    from shared.identidad import obtener_patient_id
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMModule,
        NMButton,
        NMToast,
        NMCard,
        NMIcon,
        NMStepper,
        NMHeatBar,
        NMTextArea,
        NMInput,
    )
    from shared.theme_qt import (
        C,
        qfont,
        qfont_mono,
        v3c,
        V3_SP,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.db import obtener_conexion, conexion
    from shared.identidad import obtener_patient_id
    from shared.utils import fecha_hoy, hora_actual
    from shared.visual_qa import visual_qa_enabled

from shared.remote_config import t


# ── Lógica de distorsiones (preservada exacta) ───────────────────────────────

_KWORDS = {
    "Catastrofización": [
        "siempre",
        "nunca",
        "todo",
        "nada",
        "horrible",
        "terrible",
        "insoportable",
    ],
    "Lectura mental": ["seguro que piensa", "piensan que", "creen que", "deben pensar"],
    "Filtro mental": ["solo", "únicamente", "nada más"],
    "Etiquetado": ["soy un", "soy una", "es un", "es una"],
    "Debería": ["debería", "tendría que", "tengo que"],
    "Personalización": ["por mi culpa", "es culpa mía", "yo causé"],
    "Sobregeneralización": ["todos", "nadie", "siempre", "nunca", "cada vez"],
    "Descalificación": ["no cuenta", "fue suerte", "no importa"],
    "Pensamiento dicotómico": ["o todo o nada", "blanco o negro", "perfecto o fracaso"],
    "Magnificación": ["es lo peor", "arruiné", "destruí"],
}

_DISTORTION_CATEGORY = {
    "Catastrofización": "cat",
    "Magnificación": "cat",
    "Personalización": "cat",
    "Debería": "cat",
    "Pensamiento dicotómico": "todo",
    "Sobregeneralización": "todo",
    "Etiquetado": "todo",
    "Filtro mental": "min",
    "Descalificación": "min",
    "Lectura mental": "min",
}

# v3: iconos SVG en lugar de emoji Unicode
_DISTORTION_ICON = {"cat": "flame", "todo": "warning", "min": "chart"}

# Grid 4×2 de emociones según README v3
_EMOTIONS_GRID = [
    # (label, icon_v3, color_token)
    ("Ansiedad", "bolt", "warning"),
    ("Tristeza", "water", "info"),
    ("Enojo", "flame", "danger"),
    ("Miedo", "thought", "violet"),
    ("Culpa", "heart", "warning"),
    ("Vergüenza", "user", "violet"),
    ("Soledad", "moon", "info"),
    ("Otro", "dots", "text2"),
]

DEFAULT_TCC_TEMPLATE = {
    "steps": [
        {
            "order": 0,
            "title": "Situación",
            # Mockup l.1223: subtítulo del card = prompt del paso.
            "prompt": "¿Qué pasó? Describí el momento de forma concreta y objetiva.",
            "hint": "",
            "required": True,
        },
        {
            "order": 1,
            "title": "Emoción",
            # Mockup l.1230.
            "prompt": "¿Qué sentiste? Elegí la emoción más intensa y su nivel.",
            "hint": "",
            "required": True,
        },
        {
            "order": 2,
            "title": "Pensamiento automático",  # mockup l.1241: título completo del card
            "stepper_label": "Pensamiento",  # mockup stepper: label corto
            # Mockup l.1241.
            "prompt": "¿Qué pensaste en ese momento? Escribilo tal como apareció.",
            "hint": "",
            "required": True,
        },
        {
            "order": 3,
            "title": "Respuesta",
            # Mockup l.1260.
            "prompt": "Reformulá el pensamiento de forma más equilibrada y realista.",
            "hint": "",
            "required": False,
        },
    ],
    "emotions": [
        {"label": label, "icon": icon, "color_token": color}
        for label, icon, color in _EMOTIONS_GRID
    ],
    "distortions": [
        {
            "label": label,
            "keywords": keywords,
            "category": _DISTORTION_CATEGORY.get(label, "min"),
            "icon": _DISTORTION_ICON.get(_DISTORTION_CATEGORY.get(label, "min"), "chart"),
        }
        for label, keywords in _KWORDS.items()
    ],
    "tip_text": (
        "Los pensamientos no son hechos. Preguntate: "
        "¿qué evidencia tengo? ¿qué le diría a un amigo en esta situación?"
    ),
}


def _json_list(value, fallback):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return fallback
    return value if isinstance(value, list) and value else fallback


def _normalize_steps(value):
    steps = []
    for order, item in enumerate(_json_list(value, DEFAULT_TCC_TEMPLATE["steps"])):
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("label") or "").strip()
            if not title:
                continue
            default = DEFAULT_TCC_TEMPLATE["steps"][min(order, 3)]
            steps.append(
                {
                    "order": int(item.get("order", order)),
                    "title": title,
                    "prompt": item.get("prompt") or default["prompt"],
                    "hint": item.get("hint") or default["hint"],
                    "required": bool(item.get("required", order < 3)),
                }
            )
        else:
            title = str(item).strip()
            if title:
                default = DEFAULT_TCC_TEMPLATE["steps"][min(order, 3)]
                steps.append({**default, "order": order, "title": title})
    steps = sorted(steps, key=lambda row: row.get("order", 0))
    return steps[:4] if len(steps) >= 4 else DEFAULT_TCC_TEMPLATE["steps"]


def _normalize_emotions(value):
    emotions = []
    for item in _json_list(value, DEFAULT_TCC_TEMPLATE["emotions"]):
        if isinstance(item, dict):
            label = str(item.get("label") or item.get("title") or "").strip()
            if label:
                emotions.append(
                    {
                        "label": label,
                        "icon": item.get("icon") or "dots",
                        "color_token": item.get("color_token") or item.get("color") or "text2",
                    }
                )
        else:
            label = str(item).strip()
            if label:
                emotions.append({"label": label, "icon": "dots", "color_token": "text2"})
    return emotions or DEFAULT_TCC_TEMPLATE["emotions"]


def _normalize_distortions(value):
    distortions = []
    for item in _json_list(value, DEFAULT_TCC_TEMPLATE["distortions"]):
        if isinstance(item, dict):
            label = str(item.get("label") or item.get("title") or "").strip()
            keywords = item.get("keywords") or []
            if isinstance(keywords, str):
                keywords = [keywords]
            keywords = [str(kw).lower() for kw in keywords if str(kw).strip()]
            if label:
                category = item.get("category") or _DISTORTION_CATEGORY.get(label, "min")
                distortions.append(
                    {
                        "label": label,
                        "keywords": keywords or [label.lower()],
                        "category": category,
                        "icon": item.get("icon") or _DISTORTION_ICON.get(category, "chart"),
                    }
                )
        else:
            label = str(item).strip()
            if label:
                distortions.append(
                    {
                        "label": label,
                        "keywords": [label.lower()],
                        "category": _DISTORTION_CATEGORY.get(label, "min"),
                        "icon": _DISTORTION_ICON.get(
                            _DISTORTION_CATEGORY.get(label, "min"), "chart"
                        ),
                    }
                )
    return distortions or DEFAULT_TCC_TEMPLATE["distortions"]


def _load_tcc_template_config():
    patient_scope = ""
    try:
        pid = obtener_patient_id()
        patient_scope = f"patient:{pid}" if pid else ""
    except Exception:
        patient_scope = ""
    scopes = [scope for scope in (patient_scope, "global") if scope]
    try:
        conn = obtener_conexion()
        rows = conn.execute(
            "SELECT scope, steps, emotions, distortions, tip_text "
            "FROM tcc_templates_cache WHERE scope IN ({}) "
            "ORDER BY CASE scope {} ELSE 2 END, version DESC, fetched_at DESC".format(
                ",".join("?" for _ in scopes),
                " ".join(f"WHEN ? THEN {idx}" for idx, _ in enumerate(scopes)),
            ),
            (*scopes, *scopes),
        ).fetchall()
        conn.close()
    except Exception:
        return DEFAULT_TCC_TEMPLATE
    if not rows:
        return DEFAULT_TCC_TEMPLATE
    row = rows[0]
    return {
        "steps": _normalize_steps(row["steps"]),
        "emotions": _normalize_emotions(row["emotions"]),
        "distortions": _normalize_distortions(row["distortions"]),
        "tip_text": row["tip_text"] or DEFAULT_TCC_TEMPLATE["tip_text"],
    }


def _set_placeholder_palette(pal, color: QColor):
    """Devuelve una copia de `pal` con el color de placeholderText seteado.

    2026-06 round 4: el placeholder nativo de QLineEdit no se renderiza en
    la plataforma offscreen de Qt con el color por defecto; forzamos el
    role QPalette.PlaceholderText para que sea visible en la captura sin
    alterar el text() del campo.
    """
    from PyQt6.QtGui import QPalette
    pal.setColor(QPalette.ColorRole.PlaceholderText, color)
    return pal


# ── _EmotionTile ─────────────────────────────────────────────────────────────


class _EmotionTile(NMCard):
    """Tile clickeable v3: icono + label. Activa = glow + border accent."""

    def __init__(self, label: str, icon_name: str, color_token: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=True, glow=False)
        self._label_text = label
        self._icon_name = icon_name
        self._color_token = color_token
        self._selected = False
        self.setMinimumHeight(68)
        self.setMaximumHeight(74)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["sm"], V3_SP["sm"], V3_SP["sm"], V3_SP["sm"])
        lay.setSpacing(5)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon = NMIcon(self._icon_name, size=20, color_key=self._color_token, modo=self._modo)
        self._icon.setFixedSize(22, 22)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)
        self._lbl = QLabel(self._label_text)
        self._lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setMinimumHeight(18)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addWidget(self._lbl)
        self._apply_tile_styles()

    def set_selected(self, selected: bool):
        if selected != self._selected:
            self._selected = selected
            self.set_glow(False)
            self.set_active(selected)
            self._apply_tile_styles()

    def is_selected(self) -> bool:
        return self._selected

    def label_text(self) -> str:
        return self._label_text

    def _apply_tile_styles(self):
        color = (
            v3c(self._color_token, self._modo).name()
            if self._selected
            else v3c("text", self._modo).name()
        )
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
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        lay.setSpacing(V3_SP["sm"])

        self._eyebrow = QLabel("Resumen")
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)

        self._rows: dict[str, tuple[QLabel, QLabel]] = {}
        for key, title in (
            ("situacion", "Situación"),
            ("emocion", "Emoción"),
            ("intensidad", "Intensidad"),
            ("pensamiento", "Pensamiento"),
            ("distorsiones", "Distorsiones"),
            ("respuesta", "Respuesta"),
        ):
            row = QVBoxLayout()
            row.setSpacing(0)
            t_lbl = QLabel(title)
            t_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
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
        intensidad = data.get("intensidad")
        pensamiento = data.get("pensamiento") or "—"
        distorsiones = data.get("distorsiones") or "Ninguna detectada"
        respuesta = data.get("respuesta") or "—"

        # Truncar snippets largos
        def _snip(text, n=80):
            t = text.strip()
            return t if len(t) <= n else t[: n - 1] + "…"

        self._rows["situacion"][1].setText(_snip(situacion, 90))
        self._rows["emocion"][1].setText(emocion)
        # Mostrar intensidad en escala 0-100 (mockup TCC línea 1235: "Intensidad (0–100)").
        # Persistencia interna: 0-10; visualización: 0-100.
        intensidad_txt = f"{int(intensidad * 10)}/100" if intensidad is not None else "—"
        self._rows["intensidad"][1].setText(intensidad_txt)
        self._rows["pensamiento"][1].setText(_snip(pensamiento, 90))
        self._rows["distorsiones"][1].setText(_snip(distorsiones, 100))
        self._rows["respuesta"][1].setText(_snip(respuesta, 90))

    def _apply_resumen_styles(self):
        c_eye = v3c("ink_secondary", self._modo).name()
        c_val = v3c("text", self._modo).name()
        c_sep = C("borderSoft", self._modo)
        self._eyebrow.setStyleSheet(
            f"color: {c_eye}; background: transparent;"
        )
        for key, refs in self._rows.items():
            if key.endswith("_sep"):
                refs[0].setStyleSheet(f"background-color: {c_sep};")
            else:
                title_lbl, value_lbl = refs
                title_lbl.setStyleSheet(f"color: {c_eye}; background: transparent;")
                value_lbl.setStyleSheet(f"color: {c_val}; background: transparent;")

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        self._apply_resumen_styles()


# ── _TipCard (card glow con tip terapéutico) ────────────────────────────────


class _TipCard(NMCard):
    """Card gold-soft con tip terapéutico, como el mockup de Pensamiento."""

    def __init__(self, text: str, modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._tip_text = text
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])
        self._icon = NMIcon("bulb", size=24, color_key="gold", modo=self._modo)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(2)
        self._eyebrow = QLabel(t("text.module.registro.tip_eyebrow", "Tip terapéutico"))
        self._eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))  # mockup: sin uppercase
        col.addWidget(self._eyebrow)
        self._text_lbl = QLabel(self._tip_text)
        self._text_lbl.setFont(qfont("size_small"))
        self._text_lbl.setWordWrap(True)
        col.addWidget(self._text_lbl)
        lay.addLayout(col, stretch=1)
        self._apply_tip_styles()

    def _apply_tip_styles(self):
        self._eyebrow.setStyleSheet(
            f"color: {v3c('gold', self._modo).name()}; "
            f"background: transparent;"
        )
        self._text_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        r = V3_RD["card"]
        p.setBrush(QBrush(v3c("goldSoft", self._modo)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)
        p.setBrush(Qt.BrushStyle.NoBrush)
        border = v3c("gold", self._modo, alpha=44)
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), r, r)
        p.end()

    def _apply_theme(self, modo: str):
        super()._apply_theme(modo)
        if self._icon is not None:
            self._icon._modo = self._modo
            self._icon._render()
        self._apply_tip_styles()


def _persistir_pensamiento(d: dict, intensidad: int) -> None:
    """Persiste un registro TCC en la tabla ``pensamientos`` (guardado REAL).

    Seam testeable extraído de ``_guardar`` (Fase 11). El modo QA visual salta
    deliberadamente este INSERT (sólo muestra la página de éxito), así que el
    guardado real quedaba sin cubrir por la evidencia. Tenerlo como función a
    nivel de módulo permite verificar persistencia, constraints (intensidad
    BETWEEN 0 AND 10) y manejo de errores con una SQLite temporal y QA
    desactivado, sin instanciar la UI ni tocar ``nm_data.db``. Cualquier
    excepción se propaga al caller (``_guardar`` la traduce en toast de error).
    """
    with conexion() as conn:
        conn.execute(
            "INSERT INTO pensamientos "
            "(fecha, hora, situacion, emocion, intensidad, pensamiento, "
            "respuesta_alternativa, distorsiones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fecha_hoy(),
                hora_actual(),
                d["situacion"],
                d["emocion"],
                intensidad,
                d["pensamiento"],
                d["respuesta"],
                d["distorsiones"],
            ),
        )


# ── ModuloRegistroTCC v3 ────────────────────────────────────────────────────


class ModuloRegistroTCC(NMModule):
    MODULE_TITLE = "Registro TCC"
    MODULE_ICON = "registro_tcc"

    def build_ui(self):
        self._tcc_template = _load_tcc_template_config()
        self._step_defs = self._tcc_template["steps"]
        self._emotion_defs = self._tcc_template["emotions"]
        self._distortion_defs = self._tcc_template["distortions"]
        self._distortion_by_label = {item["label"]: item for item in self._distortion_defs}
        self._step = 0
        self._data = {
            "situacion": "",
            "emocion": "",
            "intensidad": None,
            "pensamiento": "",
            "distorsiones": "",
            "respuesta": "",
        }
        self._emotion_tiles: list[_EmotionTile] = []
        self._distortions_timer = QTimer()
        self._distortions_timer.setSingleShot(True)
        self._distortions_timer.timeout.connect(lambda: self._detect_distortions(None))

        outer = QVBoxLayout(self._content)
        outer.setContentsMargins(0, 0, 0, 0)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        outer.addWidget(body)

        lay = QVBoxLayout(body)
        lay.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], V3_SP["sm"])
        lay.setSpacing(V3_SP["xs"])

        # 1. Eyebrow + Stepper
        self._eyebrow = QLabel(t("text.module.registro.eyebrow", "Registro TCC"))
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)
        self._eyebrow.hide()  # BL-07: título de módulo ahora en la titlebar

        self._stepper = NMStepper(
            [step.get("stepper_label", step["title"]) for step in self._step_defs], modo=self._modo
        )
        lay.addWidget(self._stepper)

        # 2. Main responsive grid: LEFT stack + RIGHT resumen
        self._main_grid = QGridLayout()
        self._main_grid.setContentsMargins(0, 0, 0, 0)
        self._main_grid.setHorizontalSpacing(V3_SP["md"])
        self._main_grid.setVerticalSpacing(V3_SP["md"])

        # LEFT: stack with one active step page. The stepper above carries
        # progression, so the card stays compact at the 960x600 contract.
        steps_card = NMCard(modo=self._modo, clickable=False)
        steps_card.setMinimumWidth(480)  # Slightly more compact
        # Altura acotada: los campos largos scrollean en su QTextEdit, sin
        # convertir el paso completo en una caja vacía de media pantalla.
        steps_card.setMinimumHeight(318)
        steps_card.setMaximumHeight(352)
        steps_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sc_lay = QVBoxLayout(steps_card)
        sc_lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        sc_lay.setSpacing(V3_SP["sm"])

        self._stack = QStackedWidget()
        self._stack.setMaximumHeight(244)
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._success_page: QWidget | None = None
        sc_lay.addWidget(self._stack, stretch=0)

        self._step_headers = []
        self._pages: list[QWidget] = []
        self._build_page_situacion()
        self._build_page_emocion()
        self._build_page_pensamiento()
        self._build_page_respuesta()
        for page in self._pages:
            self._stack.addWidget(page)

        # Error label
        self._error_lbl = QLabel("")
        self._error_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sc_lay.addWidget(self._error_lbl)

        # Nav (Anterior secondary real + Siguiente/Guardar gradient).
        # Antes "Anterior" era variant="ghost": sin borde ni fondo se leía como
        # texto suelto, no como botón (Fase 8). Ahora secondary → borde visible
        # y jerarquía clara frente al CTA primario de la derecha.
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(V3_SP["sm"])
        self._btn_prev = NMButton(
            t("text.module.registro.prev_btn", "Anterior"),
            parent=self._content, modo=self._modo, variant="secondary", size="sm",
            width=112,
        )
        self._btn_prev.clicked.connect(self._prev_step)
        nav_layout.addWidget(self._btn_prev)
        nav_layout.addStretch()
        self._btn_next = NMButton(
            t("text.module.registro.next_btn", "Siguiente"),
            parent=self._content,
            modo=self._modo,
            variant="gradient",
            size="sm",
            width=140,
        )
        self._btn_next.clicked.connect(self._next_step)
        nav_layout.addWidget(self._btn_next)
        sc_lay.addLayout(nav_layout)

        self._steps_card = steps_card
        self._main_grid.addWidget(self._steps_card, 0, 0)

        # RIGHT: Asistente IA (fijo 280px)
        self._resumen = _ResumenCard(modo=self._modo)
        self._resumen.setFixedWidth(280)
        self._main_grid.addWidget(self._resumen, 0, 1)

        lay.addLayout(self._main_grid)
        self._relayout_main_grid()

        self._apply_text_styles()
        self._show_step()
        self._resumen.update_data(self._data)

    def _relayout_main_grid(self):
        if not hasattr(self, "_main_grid"):
            return
        self._main_grid.removeWidget(self._steps_card)
        self._main_grid.removeWidget(self._resumen)
        w = self.width()
        if w >= 1000:
            self._steps_card.setMinimumWidth(480)
            self._resumen.setFixedWidth(280)
            self._main_grid.addWidget(self._steps_card, 0, 0)
            self._main_grid.addWidget(self._resumen, 0, 1)
            self._main_grid.setColumnStretch(0, 1)
            self._main_grid.setColumnStretch(1, 0)
        else:
            self._steps_card.setMinimumWidth(0)
            self._resumen.setFixedWidth(0)
            self._main_grid.addWidget(self._steps_card, 0, 0)
            self._resumen.hide()
            self._main_grid.setColumnStretch(0, 1)
            self._main_grid.setColumnStretch(1, 0)
            return
        self._resumen.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_main_grid()

    def _apply_text_styles(self):
        c = v3c("ink_secondary", self._modo).name()
        self._eyebrow.setStyleSheet(f"color: {c}; background: transparent;")
        self._error_lbl.setStyleSheet(
            f"color: {v3c('warning', self._modo).name()}; background: transparent;"
        )

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_txt_situacion"):
            self._txt_situacion._apply_theme(self._modo)
        if hasattr(self, "_txt_pensamiento"):
            self._txt_pensamiento._apply_theme(self._modo)
        if hasattr(self, "_txt_respuesta"):
            self._txt_respuesta._apply_theme(self._modo)
        if hasattr(self, "_eyebrow"):
            self._apply_text_styles()
        if hasattr(self, "_show_step"):
            self._show_step()
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
        # Handoff §5: newsreader for clinical titles
        try:
            from shared.theme_qt import v3_font as _v3_font

            h.setFont(_v3_font("size_h3", weight=600, serif=True))
        except Exception:
            h.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))

        h.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        widgets.append(h)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(qfont("size_small"))
            sub.setWordWrap(True)
            sub.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; background: transparent;")
            widgets.append(sub)
        return widgets

    def _step_name(self, index: int, fallback: str) -> str:
        """Nombre del paso (mockup l.1222: 'Situación'/'Emoción'/'Pensamiento'/'Respuesta').

        Es lo que el mockup usa como h2 del card. Antes se usaba el prompt
        ('¿Qué pasó?') como título — ahora el prompt pasa a ser el subtítulo
        (mockup l.1223).
        """
        try:
            return self._step_defs[index].get("title") or fallback
        except Exception:
            return fallback

    def _step_prompt(self, index: int, fallback: str) -> str:
        try:
            return self._step_defs[index].get("prompt") or fallback
        except Exception:
            return fallback

    def _step_hint(self, index: int, fallback: str = "") -> str:
        try:
            return self._step_defs[index].get("hint") or fallback
        except Exception:
            return fallback

    def _build_page_situacion(self):
        page, layout = self._make_page()
        # Add internal margins for indentation
        layout.setContentsMargins(12, 8, 12, 8)
        for lbl in self._make_title(
            # Mockup l.1222-1223: titulo = nombre del paso, subtitulo = pregunta.
            self._step_name(0, "Situación"),
            self._step_prompt(0, "¿Qué pasó? Describí el momento de forma concreta y objetiva."),
        ):
            layout.addWidget(lbl)

        self._txt_situacion = NMTextArea(
            t("text.module.registro.situation_placeholder", "Ej: En la reunión me preguntaron por el reporte y no supe qué responder…"),
            modo=self._modo,
            min_height=120,
        )
        # Mockup l.1224: textarea rows=5 (~110–120px) — antes 156 ocupaba
        # casi toda la card y empujaba el contador 0/500 al borde inferior
        # (apenas visible). 120 le da aire al contador y matchea el mockup.
        self._txt_situacion.setMaximumHeight(120)
        self._txt_situacion.textChanged.connect(self._update_situacion_count)
        layout.addWidget(self._txt_situacion, stretch=0)

        self._situacion_count_lbl = QLabel("0 / 500")
        self._situacion_count_lbl.setFont(qfont("size_caption_xs"))
        self._situacion_count_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)  # mockup: left-aligned
        self._situacion_count_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        layout.addWidget(self._situacion_count_lbl)
        self._pages.append(page)

    def _build_page_emocion(self):
        page, layout = self._make_page()
        layout.setContentsMargins(12, 8, 12, 8)
        for lbl in self._make_title(
            self._step_name(1, "Emoción"),
            self._step_prompt(1, "¿Qué sentiste? Elegí la emoción más intensa y su nivel."),
        ):
            layout.addWidget(lbl)

        # Grid 4×2 de _EmotionTile. La celda de "Otro" usa un QStackedWidget
        # para que el campo de texto se "abra sobre" el tile (misma geometría
        # exacta, sin huecos) cuando el paciente selecciona esa emoción. La pila
        # tiene dos páginas: [0] tile, [1] input; al elegir "Otro" se hace raise
        # al input, que ocupa la celda del tile sin moverse a una fila aparte.
        # (2026-06: setColumnStretch(1,1,1,1) + sizePolicy Expanding en los tiles
        # para que las 4 columnas tengan ancho uniforme — antes el QStackedWidget
        # del "Otro" estiraba su columna y Miedo (mismo ancho de label) la
        # acompañaba, rompiendo la grilla 4×2.)
        grid = QGridLayout()
        grid.setSpacing(V3_SP["sm"])
        for c in range(4):
            grid.setColumnStretch(c, 1)
        self._otro_stack = None
        for i, emotion in enumerate(self._emotion_defs):
            label = emotion["label"]
            icon_name = emotion.get("icon") or "dots"
            color_token = emotion.get("color_token") or "text2"
            tile = _EmotionTile(label, icon_name, color_token, modo=self._modo)
            tile.clicked.connect(lambda lbl=label: self._on_emotion_picked(lbl))
            # Expanding horizontal para que el grid distribuya el ancho 1/4
            # por columna sin importar el sizeHint del label interno.
            tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            r, c = divmod(i, 4)
            if label == "Otro":
                # Pila con tile (página 0) + input (página 1) que aparece
                # al seleccionar "Otro" ocupando TODA la celda del tile
                # (mismo width/height). El input se expande verticalmente
                # para llenar la celda completa, y el placeholder canónico
                # queda visible y centrado.
                # 2026-06 round 4: el input usa setPlaceholderText (campo
                # realmente vacio, text()==""). El placeholder se hace
                # visible via palette PlaceholderText role + ink_secondary.
                stack = QStackedWidget()
                stack.setObjectName("OtroTileStack")
                stack.setStyleSheet("background: transparent;")
                stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                stack.addWidget(tile)  # index 0: tile visible por defecto
                self._custom_emotion_input = NMInput("", modo=self._modo)
                self._custom_emotion_input.setMaxLength(12)
                self._custom_emotion_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Expanding vertical para que el input llene toda la celda
                # del tile (72px) en vez de quedarse en 36px centrado.
                # Sobreescribir maxHeight del NMInput (default 36px) para que
                # crezca con la celda.
                self._custom_emotion_input.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                self._custom_emotion_input.setMinimumHeight(0)
                self._custom_emotion_input.setMaximumHeight(16777215)
                # 2026-06 round 4: placeholder nativo (campo realmente vacio,
                # text()=="" siempre). El placeholder se hace visible via
                # setPlaceholderText + palette color (placeholderText role).
                self._custom_emotion_input.textChanged.connect(
                    self._on_custom_emotion_changed
                )
                otro_placeholder = t(
                    "text.module.registro.other_emotion_placeholder",
                    "Nombrá tu emoción…",
                )
                self._custom_emotion_input.setPlaceholderText("Nombrá tu emoción…")
                if otro_placeholder != "Nombrá tu emoción…":
                    self._custom_emotion_input.setPlaceholderText(otro_placeholder)
                # Palette: color tenue para el placeholder (placeholderText role).
                _ink2_c = QColor(v3c("ink_secondary", self._modo).name())
                self._custom_emotion_input.setPalette(
                    _set_placeholder_palette(self._custom_emotion_input.palette(), _ink2_c)
                )
                stack.addWidget(self._custom_emotion_input)  # index 1: input
                grid.addWidget(stack, r, c)
                self._otro_stack = stack
            else:
                grid.addWidget(tile, r, c)
            self._emotion_tiles.append(tile)
        layout.addLayout(grid)

        # Intensidad: header + NMHeatBar.
        # Mockup TCC línea 1235-1236:
        #   <div class="field-lbl">Intensidad <span>(0–100)</span></div>
        #   <input type="range" min="0" max="100" value="70"
        #     style="background:linear-gradient(90deg,var(--brand),var(--accent));">
        # Slider visual 0–100 con gradiente brand→accent (NO arcoíris genérico).
        # Internamente se persiste intensidad 0-10 (div por 10 en _on_intensidad_heat).
        _intens_init = self._data.get("intensidad")
        _intens_val = _intens_init if _intens_init is not None else 5
        _intens_visual = int(_intens_val * 10)  # 0-10 → 0-100 visual
        _intens_lbl = f"Intensidad: {_intens_visual} (0–100)"
        self._lbl_intensidad_header = QLabel(_intens_lbl)
        self._lbl_intensidad_header.setFont(
            qfont("size_small", weight=TYPOGRAPHY["weight_semibold"])
        )
        self._lbl_intensidad_header.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        self._lbl_intensidad_header.setContentsMargins(0, V3_SP["md"], 0, 0)
        layout.addWidget(self._lbl_intensidad_header)

        self._heat_bar = NMHeatBar(
            value=int((_intens_init or 5) * 10),
            modo=self._modo,
            gradient="brand_accent",  # mockup TCC: linear-gradient(90deg, brand, accent)
            value_max=100,            # mockup TCC: min=0 max=100 (escala visual)
            parent=page,
        )
        self._heat_bar.value_changed.connect(self._on_intensidad_heat)
        heat_row = QHBoxLayout()
        heat_row.setContentsMargins(0, 0, 0, 0)
        heat_row.addStretch(1)
        self._heat_bar.setMaximumWidth(720)
        heat_row.addWidget(self._heat_bar, stretch=1)
        heat_row.addStretch(1)
        layout.addLayout(heat_row)
        layout.addStretch()
        self._pages.append(page)

    def _build_page_pensamiento(self):
        page, layout = self._make_page()
        layout.setContentsMargins(12, 8, 12, 8)
        for lbl in self._make_title(
            self._step_name(2, "Pensamiento"),
            self._step_prompt(2, "¿Qué pensaste en ese momento? Escribilo tal como apareció."),
        ):
            layout.addWidget(lbl)

        self._txt_pensamiento = NMTextArea(
            t("text.module.registro.thought_placeholder", "Escribi el pensamiento automatico"),
            modo=self._modo,
            min_height=96,
        )
        self._txt_pensamiento.setMaximumHeight(132)
        self._txt_pensamiento.textChanged.connect(self._on_pensamiento_changed)
        layout.addWidget(self._txt_pensamiento, stretch=0)

        # QHBoxLayout for 2 columns below the textarea
        two_cols = QHBoxLayout()
        two_cols.setSpacing(V3_SP["md"])

        # Left column (counter + distortions)
        left_col = QVBoxLayout()
        left_col.setSpacing(V3_SP["xs"])
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._pensamiento_count_lbl = QLabel("0 / 500")
        self._pensamiento_count_lbl.setFont(qfont("size_caption_xs"))
        self._pensamiento_count_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._pensamiento_count_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        left_col.addWidget(self._pensamiento_count_lbl)

        self._dist_eyebrow = QLabel(
            t("text.module.registro.distortions_eyebrow", "Posibles distorsiones detectadas")
        )
        self._dist_eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))  # mockup: sin uppercase
        self._dist_eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; "
            f"background: transparent;"
        )
        self._dist_eyebrow.setContentsMargins(0, 4, 0, 0)
        left_col.addWidget(self._dist_eyebrow)

        self._distortion_frame = QWidget()
        self._distortion_frame.setStyleSheet("background: transparent;")
        self._distortion_layout = QHBoxLayout(self._distortion_frame)
        self._distortion_layout.setContentsMargins(0, 0, 0, 0)
        self._distortion_layout.setSpacing(V3_SP["xs"] + 2)
        self._distortion_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_col.addWidget(self._distortion_frame)

        two_cols.addLayout(left_col, stretch=1)

        # Right column (Tip terapéutico)
        right_col = QVBoxLayout()
        right_col.setSpacing(0)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        tip = _TipCard(
            self._tcc_template.get("tip_text") or DEFAULT_TCC_TEMPLATE["tip_text"], modo=self._modo
        )
        # Mínimo y no fijo (auditoría v1.0): el tip viene del Hub (texto libre)
        # y con wordwrap a 2-3 líneas la altura fija lo recortaba contra el
        # borde inferior de la card.
        tip.setMinimumHeight(68)
        right_col.addWidget(tip)
        self._tip_card = tip

        two_cols.addLayout(right_col, stretch=1)
        layout.addLayout(two_cols)

        self._detect_distortions(None)
        self._pages.append(page)

    def _build_page_respuesta(self):
        page, layout = self._make_page()
        layout.setContentsMargins(12, 8, 12, 8)
        for lbl in self._make_title(
            self._step_name(3, "Respuesta"),
            self._step_prompt(3, "Reformulá el pensamiento de forma más equilibrada y realista."),
        ):
            layout.addWidget(lbl)

        self._txt_respuesta = NMTextArea(
            t("text.module.registro.response_placeholder", "Escribi una respuesta alternativa"),
            modo=self._modo,
            min_height=120,
        )
        # Mockup l.1235: textarea rows=5 (~110–120px) — mismo fix que
        # _txt_situacion para no aplastar el contador al borde de la card.
        self._txt_respuesta.setMaximumHeight(120)
        layout.addWidget(self._txt_respuesta, stretch=0)
        self._pages.append(page)

    # ── emotion tile picker ──────────────────────────────────────────────────

    def _on_emotion_picked(self, label: str):
        self._data["emocion"] = label
        for tile in self._emotion_tiles:
            tile.set_selected(tile.label_text() == label)
        
        is_otro = (label == "Otro")
        # "Otro" se "abre sobre" el tile: la celda de la grilla es un
        # QStackedWidget con la tile y el input. Cambiar la página activa
        # muestra el input exactamente en la misma posición que el tile.
        otro_stack = getattr(self, "_otro_stack", None)
        if otro_stack is not None:
            otro_stack.setCurrentIndex(1 if is_otro else 0)
        if hasattr(self, "_custom_emotion_input"):
            if is_otro:
                custom_text = self._custom_emotion_input.text().strip()
                if custom_text:
                    self._data["emocion"] = custom_text
                else:
                    self._data["emocion"] = "Otro"
                # 2026-06 round 4: NO setFocus() automatico — mantiene el
                # placeholder visible (el cursor lo ocultaria en la
                # plataforma offscreen). El usuario puede hacer click para
                # escribir.
            else:
                self._custom_emotion_input.clear()

        if hasattr(self, "_error_lbl"):
            self._error_lbl.setText("")
        self._resumen.update_data(self._data)
        self._refresh_nav_state()

    def _on_custom_emotion_changed(self, text: str):
        cleaned = text.strip()
        # 2026-06 round 4: el input Otro usa setPlaceholderText (no setText),
        # por lo que text() nunca contiene el placeholder — la rama del round 3 ya
        # no es necesaria. Campo vacio = "Otro" como emocion.
        self._data["emocion"] = cleaned if cleaned else "Otro"
        self._resumen.update_data(self._data)
        self._refresh_nav_state()

    # ── char counters ────────────────────────────────────────────────────────

    def _on_pensamiento_changed(self):
        self._update_pensamiento_count()
        self._distortions_timer.start(300)

    def _update_situacion_count(self):
        try:
            if sip.isdeleted(self._situacion_count_lbl):
                return
            n = len(self._txt_situacion.toPlainText())
        except Exception:
            return
        col = (
            v3c("warning", self._modo).name()
            if n > 500
            else v3c("ink_secondary", self._modo).name()
        )
        self._situacion_count_lbl.setText(f"{n} / 500")
        self._situacion_count_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._refresh_nav_state()

    def _update_pensamiento_count(self):
        try:
            if sip.isdeleted(self._pensamiento_count_lbl):
                return
            n = len(self._txt_pensamiento.toPlainText())
        except Exception:
            return
        col = (
            v3c("warning", self._modo).name()
            if n > 500
            else v3c("ink_secondary", self._modo).name()
        )
        self._pensamiento_count_lbl.setText(f"{n} / 500")
        self._pensamiento_count_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._refresh_nav_state()

    # ── distortion detection (lógica preservada exacta) ──────────────────────

    def _detect_distortions(self, _event):
        _log.debug(f"Detecting distortions, modo={getattr(self, '_modo', 'N/A')}")
        text = ""
        try:
            text = self._txt_pensamiento.toPlainText().strip().lower()
        except Exception:
            text = self._data.get("pensamiento", "").lower()

        found = []
        for distortion in self._distortion_defs:
            label = distortion.get("label", "")
            for kw in distortion.get("keywords") or []:
                if kw in text:
                    found.append(label)
                    break

        # Clear old chips
        while self._distortion_layout.count():
            item = self._distortion_layout.takeAt(0)
            w = item.widget()
            if w:
                self._distortion_layout.removeWidget(w)
                w.deleteLater()

        if found:
            for d in found:
                meta = self._distortion_by_label.get(d, {})
                cat = meta.get("category") or _DISTORTION_CATEGORY.get(d, "min")
                fg = v3c("rose", self._modo).name()
                # Chip: icon + label
                chip_widget = QWidget()
                chip_widget.setStyleSheet("background: transparent;")
                chip_lay = QHBoxLayout(chip_widget)
                chip_lay.setContentsMargins(V3_SP["sm"], 2, V3_SP["sm"], 2)
                chip_lay.setSpacing(V3_SP["xs"])
                icon_name = meta.get("icon") or _DISTORTION_ICON.get(cat, "info")
                icon = NMIcon(icon_name, size=14, color=fg, modo=self._modo)
                chip_lay.addWidget(icon)
                label = QLabel(d)
                label.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
                label.setStyleSheet(f"color: {fg}; background: transparent;")
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
                    f"border: none; border-radius: 999px; }}"
                )
                self._distortion_layout.addWidget(wrapper)
        else:
            none_lbl = QLabel(t("text.module.registro.no_distortions", "Ninguna detectada aún"))
            none_lbl.setFont(qfont("size_small"))
            none_lbl.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
            self._distortion_layout.addWidget(none_lbl)

        self._data["distorsiones"] = ", ".join(found)
        if hasattr(self, "_resumen"):
            self._resumen.update_data(self._data)

    # ── intensidad ───────────────────────────────────────────────────────────

    def _on_intensidad_heat(self, value: int):
        self._on_intensidad(round(value / 10))

    def _on_intensidad(self, value: int):
        # value viene en escala 0-10 (div por 10 en _on_intensidad_heat).
        # Persistimos 0-10, pero el label muestra el valor visual 0-100
        # (mockup TCC línea 1235: "Intensidad (0–100)").
        self._data["intensidad"] = value
        try:
            visual_value = int(value * 10)  # 0-10 → 0-100
            self._lbl_intensidad_header.setText(f"Intensidad: {visual_value} (0–100)")
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
            if hasattr(self, "_stack") and self._stack and self._pages:
                stack_h = {0: 244, 1: 284, 2: 288, 3: 244}.get(self._step, 260)
                card_h = {0: 324, 1: 364, 2: 372, 3: 324}.get(self._step, 342)
                self._stack.setMaximumHeight(stack_h)
                if hasattr(self, "_steps_card"):
                    self._steps_card.setMinimumHeight(min(card_h, 352))
                    self._steps_card.setMaximumHeight(min(card_h, 372))
                self._stack.setCurrentWidget(self._pages[self._step])

            for i, page in enumerate(self._pages):
                # Header styling
                if i < len(self._step_headers):
                    hdr, title_lbl, status_lbl = self._step_headers[i]
                    if self._step == i:
                        hdr.set_accent(v3c("primary", self._modo).name())
                        hdr.set_glow(True)
                        title_lbl.setStyleSheet(
                            f"color: {v3c('primary', self._modo).name()}; background: transparent;"
                        )
                    else:
                        hdr.set_accent(None)
                        hdr.set_glow(False)
                        title_lbl.setStyleSheet(
                            f"color: {v3c('text', self._modo).name()}; background: transparent;"
                        )

                    # Status text
                    if i < self._step:
                        status_lbl.setText("Completado ✔")
                        status_lbl.setStyleSheet(
                            f"color: {v3c('success', self._modo).name()}; background: transparent;"
                        )
                    elif i == self._step:
                        status_lbl.setText("Activo")
                        status_lbl.setStyleSheet(
                            f"color: {v3c('primary', self._modo).name()}; background: transparent;"
                        )
                    else:
                        status_lbl.setText("Pendiente")
                        status_lbl.setStyleSheet(
                            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
                        )

            self._btn_prev.setEnabled(self._step > 0)
            if self._step == 3:
                self._btn_next.setText(t("text.module.registro.save_btn", "Guardar registro"))
            else:
                self._btn_next.setText(t("text.module.registro.next_btn", "Siguiente"))
            # 2026-06 round 4: el input Otro usa setPlaceholderText (no setText),
            # por lo que no necesita re-set tras _reset() — el placeholder es
            # siempre canónico y text() permanece vacio.
            self._refresh_nav_state()
        except Exception as e:
            _log.error(redact(f"Error in _show_step: {e}"))
            import traceback

            traceback.print_exc()

    def _current_required_value(self) -> str:
        if self._step == 0:
            try:
                return self._txt_situacion.toPlainText().strip()
            except Exception:
                return self._data.get("situacion", "").strip()
        if self._step == 1:
            return self._data.get("emocion", "").strip()
        if self._step == 2:
            try:
                return self._txt_pensamiento.toPlainText().strip()
            except Exception:
                return self._data.get("pensamiento", "").strip()
        return "ok"

    def _can_advance(self) -> bool:
        if self._step in (0, 1, 2):
            return bool(self._current_required_value())
        return True

    def _refresh_nav_state(self) -> None:
        if not hasattr(self, "_btn_next"):
            return
        if self._success_page is not None and self._stack.currentWidget() is self._success_page:
            self._btn_next.setEnabled(False)
            return
        self._btn_next.setEnabled(self._can_advance())

    def _on_header_clicked(self, step_idx: int):
        if not isinstance(step_idx, int) or step_idx < 0 or step_idx >= len(self._pages):
            return
        self._save_current_step_data()

        # If moving forward, run validation for current step
        if step_idx > self._step:
            campo_requerido = {
                0: ("situacion", "Describí la situación para continuar."),
                1: ("emocion", "Seleccioná la emoción que sentiste."),
                2: ("pensamiento", "Escribí el pensamiento automático."),
            }
            for s in range(self._step, step_idx):
                if s in campo_requerido:
                    campo, hint = campo_requerido[s]
                    if not self._data.get(campo, "").strip():
                        self._error_lbl.setText(hint)
                        return
            self._error_lbl.setText("")

        self._step = step_idx
        self._show_step()

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
                0: ("situacion", "Describí la situación para continuar."),
                1: ("emocion", "Seleccioná la emoción que sentiste."),
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
            _log.error(redact(f"Error in _next_step: {e}"))
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
            QTimer.singleShot(
                2500, lambda: self._error_lbl.setText("") if not sip.isdeleted(self) else None
            )
            return

        # intensidad es NOT NULL CHECK(0..10) en la DB; si el usuario no movió el
        # heatbar queda None y el INSERT fallaba. El control arranca en 5/10, así
        # que ese es el valor por defecto cuando no se declaró intensidad.
        intensidad = d["intensidad"] if d.get("intensidad") is not None else 5

        # Éxito determinista en modo QA visual (Fase 8): la evidencia de la
        # página de éxito no debe depender de un INSERT real (que ante un fallo
        # dispararía el toast de error y arruinaría la captura) ni ensuciar la DB
        # con registros de captura. Producción conserva el INSERT + toast ante un
        # fallo genuino de guardado.
        if visual_qa_enabled():
            self._show_success_page()
            QTimer.singleShot(3000, lambda: self._reset() if not sip.isdeleted(self) else None)
            return

        try:
            _persistir_pensamiento(d, intensidad)
        except Exception:
            _log.exception("Error guardando registro TCC")
            NMToast.display(self.window(), "Error al guardar el registro", variant="error")
            return

        try:
            from shared.sync import sync_inmediato_background

            sync_inmediato_background()
        except Exception:
            pass

        # Sin animación de "éxito" sobre el botón Guardar: se sentía tosca y no
        # coincidía con la interacción normal de Siguiente/Anterior (pedido
        # owner). El feedback de guardado es la página de éxito, no un efecto en
        # el botón. (El "destello verde" reportado antes era el resaltador del
        # lector de pantalla sobre widgets huérfanos, no este botón.)
        self._show_success_page()
        QTimer.singleShot(3000, lambda: self._reset() if not sip.isdeleted(self) else None)

    def _show_success_page(self):
        if self._success_page is not None:
            old = self._success_page
            self._stack.removeWidget(old)
            old.deleteLater()
            self._success_page = None
        success = QWidget()
        success.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(success)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(V3_SP["sm"])
        check_icon = NMIcon("check", size=64, color_key="success", modo=self._modo)
        layout.addWidget(check_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl = QLabel(t("text.module.registro.success_title", "Registro guardado"))
        title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        layout.addWidget(title_lbl)
        sub_lbl = QLabel(
            t(
                "text.module.registro.success_subtitle",
                "Buen trabajo al identificar y cuestionar el pensamiento.",
            )
        )
        sub_lbl.setFont(qfont("size_body"))
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        layout.addWidget(sub_lbl)
        self._stack.addWidget(success)
        self._success_page = success
        self._stack.setCurrentWidget(success)
        # Anclar el foco (y al lector de pantalla) en la confirmación: sin
        # esto, tras recargar "registros previos" el navegador de
        # accesibilidad podía aterrizar en widgets transitorios y dibujar su
        # resaltado con geometría arbitraria (el "destello" reportado).
        success.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        success.setAccessibleName("Registro guardado")
        success.setFocus(Qt.FocusReason.OtherFocusReason)
        self._btn_prev.setEnabled(False)
        self._btn_next.setEnabled(False)

    def _reset(self):
        if self._success_page is not None:
            old = self._success_page
            self._stack.removeWidget(old)
            old.deleteLater()
            self._success_page = None
        self._step = 0
        self._data = {
            "situacion": "",
            "emocion": "",
            "intensidad": None,
            "pensamiento": "",
            "distorsiones": "",
            "respuesta": "",
        }
        try:
            self._txt_situacion.clear()
            for tile in self._emotion_tiles:
                tile.set_selected(False)
            if hasattr(self, "_custom_emotion_input"):
                self._custom_emotion_input.clear()
                self._custom_emotion_input.setVisible(False)
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

    def get_card_status(self) -> str:
        try:
            conn = obtener_conexion()
            row = conn.execute(
                "SELECT COUNT(*) as n FROM pensamientos WHERE fecha = ?", (fecha_hoy(),)
            ).fetchone()
            conn.close()
            if row and row[0] > 0:
                n = row[0]
                return f"{n} registro{'s' if n > 1 else ''}"
        except Exception:
            _log.exception("Operation failed")
        return ""
