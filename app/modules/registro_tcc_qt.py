"""
app/modules/registro_tcc_qt.py — Registro de pensamientos TCC (PyQt6)

LÓGICA PRESERVADA EXACTA:
  _KWORDS, _save_current_step_data(), _next_step() con validación por paso,
  _guardar(), _detect_distortions(), get_card_status()
"""

import os
import sys
import logging

_log = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QTimer
from PyQt6 import sip
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QTextEdit, QLineEdit, QFrame, QScrollArea, QSizePolicy,
    QStackedWidget, QPushButton,
)

try:
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMToast, ThemeManager,
        h_spacer, NMEmptyState,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_PILL, RADIUS_BADGE,
        stylesheet_textedit, stylesheet_slider, stylesheet_lineedit,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components_qt import (
        NMModule, NMButton, NMButtonOutline, NMToast, ThemeManager,
        h_spacer, NMEmptyState,
    )
    from shared.theme_qt import (
        C, colors, norm_modo, qfont, qcolor,
        sp,
        PAD_CONTAINER, GAP_CARDS, GAP_ELEMENTS,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_PILL, RADIUS_BADGE,
        stylesheet_textedit, stylesheet_slider, stylesheet_lineedit,
    )
    from shared.db import obtener_conexion
    from shared.utils import fecha_hoy, hora_actual


# ── Distorsiones cognitivas (preservado exacto) ───────────────────────────────

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

_STEP_NAMES = ["Situación", "Emoción", "Pensamiento", "Respuesta"]


# ── Pill widget para indicador de progreso ────────────────────────────────────

class _StepPill(QFrame):
    """Píldora redondeada para indicar el paso activo/completado/pendiente."""

    def __init__(self, index: int, name: str, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._index = index
        self._name = name
        self._state = "pending"  # "pending" | "active" | "done"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            sp("sm") + sp("xs"),
            sp("sm") - sp("xs") // 2,
            sp("sm") + sp("xs"),
            sp("sm") - sp("xs") // 2,
        )

        self._lbl = QLabel(f"{index + 1}  {name}")
        self._lbl.setFont(qfont("size_small"))
        layout.addWidget(self._lbl)

        self._apply_state()

    def set_state(self, state: str):
        """state: 'pending' | 'active' | 'done'"""
        self._state = state
        self._apply_state()

    def _apply_state(self):
        c = colors(self._modo)
        r = RADIUS_PILL
        if self._state == "active":
            bg = c["accent"]
            text_color = c["text_on_accent"]
        elif self._state == "done":
            bg = c["success"]
            text_color = "#ffffff"
        else:
            bg = c.get("border_card", c["border"])
            text_color = c["text_tertiary"]

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: {r}px;
                border: none;
            }}
        """)
        self._lbl.setStyleSheet(f"color: {text_color}; background: transparent;")

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_state()


# ── ModuloRegistroTCC ─────────────────────────────────────────────────────────

class ModuloRegistroTCC(NMModule):
    MODULE_TITLE = "Registro TCC"
    MODULE_ICON  = "registro_tcc"

    def build_ui(self):
        self._step = 0
        self._data = {
            "situacion": "", "emocion": "", "intensidad": 5,
            "pensamiento": "", "distorsiones": "", "respuesta": "",
        }

        c = colors(self._modo)

        # ── Root layout ───────────────────────────────────────────────────────
        root = QVBoxLayout(self._content)
        root.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                PAD_CONTAINER, PAD_CONTAINER)
        root.setSpacing(sp("sm") + sp("xs"))

        # ── Pills row ─────────────────────────────────────────────────────────
        if not self._has_registros_hoy():
            root.addWidget(NMEmptyState(
                "fa5s.brain",
                "Sin registros aún",
                "Anotá un pensamiento cuando estés listo.",
                self._content,
            ))

        pills_row = QHBoxLayout()
        pills_row.setSpacing(sp("sm") - sp("xs") // 2)
        pills_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._pills: list[_StepPill] = []
        for i, name in enumerate(_STEP_NAMES):
            pill = _StepPill(i, name, self._content, self._modo)
            pills_row.addWidget(pill)
            self._pills.append(pill)
        pills_row.addStretch()
        root.addLayout(pills_row)

        # ── Step container (QStackedWidget) ───────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self._stack)

        # Build all 4 step pages
        self._pages: list[QWidget] = []
        self._build_page_situacion()
        self._build_page_emocion()
        self._build_page_pensamiento()
        self._build_page_respuesta()

        # ── Navigation buttons ────────────────────────────────────────────────
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(sp("sm"))

        self._btn_prev = NMButtonOutline("← Anterior", parent=self._content, modo=self._modo)
        self._btn_prev.setFixedHeight(38)
        self._btn_prev.setMinimumWidth(110)
        self._btn_prev.clicked.connect(self._prev_step)
        nav_layout.addWidget(self._btn_prev)

        nav_layout.addStretch()

        self._btn_next = NMButton("Siguiente →", parent=self._content,
                                   modo=self._modo, width=110, height=38)
        self._btn_next.clicked.connect(self._next_step)
        nav_layout.addWidget(self._btn_next)

        # Error label (compartido entre pasos)
        self._error_lbl = QLabel("")
        self._error_lbl.setFont(qfont("size_small"))
        self._error_lbl.setStyleSheet(
            f"color: {C('warning', self._modo)}; background: transparent; font-weight: bold;"
        )
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._error_lbl)

        root.addLayout(nav_layout)

        self._show_step()

    def _on_theme(self, modo: str) -> None:
        super()._on_theme(modo)
        if hasattr(self, "_txt_situacion"):
            self._txt_situacion.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_txt_pensamiento"):
            self._txt_pensamiento.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_txt_respuesta"):
            self._txt_respuesta.setStyleSheet(stylesheet_textedit(self._modo))
        if hasattr(self, "_error_lbl"):
            self._error_lbl.setStyleSheet(
                f"color: {C('warning', self._modo)}; background: transparent; font-weight: bold;"
            )
        for child in self.findChildren(QFrame):
            if hasattr(child, "apply_theme"):
                child.apply_theme(self._modo)
        self.update()

    # ── Page builders ─────────────────────────────────────────────────────────

    def _make_page(self) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(sp("sm"))
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        return page, layout

    def _make_title(self, text: str, subtitle: str = "") -> list[QLabel]:
        c = colors(self._modo)
        widgets = []
        h = QLabel(text)
        h.setFont(qfont("size_h2", bold=True))
        h.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        widgets.append(h)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(qfont("size_small"))
            sub.setWordWrap(True)
            sub.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
            widgets.append(sub)
        return widgets

    def _build_page_situacion(self):
        page, layout = self._make_page()
        c = colors(self._modo)

        for lbl in self._make_title(
            "¿Qué pasó?",
            "Describí brevemente la situación que desencadenó el malestar."
        ):
            layout.addWidget(lbl)

        self._txt_situacion = QTextEdit()
        self._txt_situacion.setMinimumHeight(100)
        self._txt_situacion.setStyleSheet(stylesheet_textedit(self._modo))
        layout.addWidget(self._txt_situacion)
        layout.addStretch()

        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_emocion(self):
        page, layout = self._make_page()
        c = colors(self._modo)

        for lbl in self._make_title("¿Qué sentiste?"):
            layout.addWidget(lbl)

        lbl_emo = QLabel("Emoción principal")
        lbl_emo.setFont(qfont("size_body"))
        lbl_emo.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(lbl_emo)

        self._entry_emocion = QLineEdit()
        self._entry_emocion.setMinimumHeight(36)
        self._entry_emocion.setPlaceholderText("Ej: ansiedad, tristeza, enojo...")
        self._entry_emocion.setStyleSheet(stylesheet_lineedit(self._modo))
        layout.addWidget(self._entry_emocion)

        lbl_int = QLabel(f"Intensidad: {self._data['intensidad']}/10")
        lbl_int.setFont(qfont("size_body"))
        lbl_int.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(lbl_int)
        self._lbl_intensidad_header = lbl_int

        self._slider_intensidad = QSlider(Qt.Orientation.Horizontal)
        self._slider_intensidad.setRange(0, 10)
        self._slider_intensidad.setValue(self._data["intensidad"])
        self._slider_intensidad.setFixedHeight(28)
        self._slider_intensidad.setStyleSheet(stylesheet_slider(self._modo))
        self._slider_intensidad.valueChanged.connect(self._on_intensidad)
        layout.addWidget(self._slider_intensidad)

        self._lbl_intensidad = QLabel(f"{self._data['intensidad']}/10")
        self._lbl_intensidad.setFont(qfont("size_h3", bold=True))
        self._lbl_intensidad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_intensidad.setStyleSheet(
            f"color: {c['accent']}; background: transparent;"
        )
        layout.addWidget(self._lbl_intensidad)
        layout.addStretch()

        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_pensamiento(self):
        page, layout = self._make_page()
        c = colors(self._modo)

        for lbl in self._make_title(
            "Pensamiento automático",
            "¿Qué pensaste en ese momento? Escribí el pensamiento tal como vino."
        ):
            layout.addWidget(lbl)

        self._txt_pensamiento = QTextEdit()
        self._txt_pensamiento.setMinimumHeight(80)
        self._txt_pensamiento.setStyleSheet(stylesheet_textedit(self._modo))
        self._txt_pensamiento.textChanged.connect(lambda: self._detect_distortions(None))
        layout.addWidget(self._txt_pensamiento)

        lbl_dist = QLabel("Posibles distorsiones detectadas:")
        lbl_dist.setFont(qfont("size_small"))
        lbl_dist.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        layout.addWidget(lbl_dist)

        # Distortion chips container
        self._distortion_frame = QWidget()
        self._distortion_frame.setStyleSheet("background: transparent;")
        self._distortion_layout = QHBoxLayout(self._distortion_frame)
        self._distortion_layout.setContentsMargins(0, 0, 0, 0)
        self._distortion_layout.setSpacing(sp("xs"))
        self._distortion_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._distortion_frame)
        layout.addStretch()

        self._detect_distortions(None)

        self._stack.addWidget(page)
        self._pages.append(page)

    def _build_page_respuesta(self):
        page, layout = self._make_page()
        c = colors(self._modo)

        for lbl in self._make_title(
            "Respuesta alternativa",
            "¿Cómo podrías pensar de manera más equilibrada?"
        ):
            layout.addWidget(lbl)

        self._txt_respuesta = QTextEdit()
        self._txt_respuesta.setMinimumHeight(100)
        self._txt_respuesta.setStyleSheet(stylesheet_textedit(self._modo))
        layout.addWidget(self._txt_respuesta)
        layout.addStretch()

        self._stack.addWidget(page)
        self._pages.append(page)

    # ── Distortion detection (lógica preservada exacta) ───────────────────────

    def _detect_distortions(self, _event):
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

        c = colors(self._modo)
        if found:
            for d in found:
                badge = QLabel(f"  {d}  ")
                badge.setFont(qfont("size_small"))
                badge.setStyleSheet(f"""
                    QLabel {{
                        color: {c['warning']};
                        background-color: {c['bg_elevated']};
                        border-radius: {RADIUS_BADGE}px;
                        padding: {sp('xs')}px {sp('sm')}px;
                    }}
                """)
                self._distortion_layout.addWidget(badge)
        else:
            none_lbl = QLabel("Ninguna detectada aún")
            none_lbl.setFont(qfont("size_small"))
            none_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            self._distortion_layout.addWidget(none_lbl)

        self._data["distorsiones"] = ", ".join(found)

    # ── Intensity slider ──────────────────────────────────────────────────────

    def _on_intensidad(self, value: int):
        self._data["intensidad"] = value
        try:
            self._lbl_intensidad.setText(f"{value}/10")
            self._lbl_intensidad_header.setText(f"Intensidad: {value}/10")
        except Exception:
            _log.exception("Operation failed")

    # ── Step progress indicator ───────────────────────────────────────────────

    def _update_progress(self):
        for i, pill in enumerate(self._pills):
            if i == self._step:
                pill.set_state("active")
            elif i < self._step:
                pill.set_state("done")
            else:
                pill.set_state("pending")

    def _show_step(self):
        self._update_progress()
        if 0 <= self._step < len(self._pages):
            self._stack.setCurrentWidget(self._pages[self._step])

        # Button states
        self._btn_prev.setEnabled(self._step > 0)
        if self._step == 3:
            self._btn_next.setText("Guardar ✓")
        else:
            self._btn_next.setText("Siguiente →")

    # ── Navigation (lógica de validación preservada exacta) ───────────────────

    def _save_current_step_data(self):
        if self._step == 0:
            try:
                self._data["situacion"] = self._txt_situacion.toPlainText().strip()
            except Exception:
                pass
        elif self._step == 1:
            try:
                self._data["emocion"] = self._entry_emocion.text().strip()
            except Exception:
                pass
        elif self._step == 2:
            try:
                self._data["pensamiento"] = self._txt_pensamiento.toPlainText().strip()
            except Exception:
                pass
            self._detect_distortions(None)
        elif self._step == 3:
            try:
                self._data["respuesta"] = self._txt_respuesta.toPlainText().strip()
            except Exception:
                pass

    def _next_step(self):
        self._save_current_step_data()

        # Validación por paso (preservada exacta)
        campo_requerido = {
            0: ("situacion",   "Describí la situación para continuar."),
            1: ("emocion",     "Nombrá la emoción que sentiste."),
            2: ("pensamiento", "Escribí el pensamiento automático."),
        }
        if self._step in campo_requerido:
            campo, hint = campo_requerido[self._step]
            if not self._data.get(campo, "").strip():
                # Mostrar error en label dedicado, no en el texto del botón
                self._error_lbl.setText(hint)
                return
            self._error_lbl.setText("")

        if self._step == 3:
            self._guardar()
            return

        self._step += 1
        self._show_step()

    def _prev_step(self):
        self._save_current_step_data()
        if self._step > 0:
            self._step -= 1
            self._show_step()

    # ── Save to DB (_guardar lógica preservada exacta) ────────────────────────

    def _guardar(self):
        self._save_current_step_data()
        d = self._data
        if not d["situacion"] or not d["pensamiento"]:
            self._btn_next.setText("Completá los campos")
            QTimer.singleShot(2000, lambda: self._btn_next.setText("Guardar ✓") if not sip.isdeleted(self._btn_next) else None)
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
            NMToast.display(self.window(), "Error al guardar el registro", variant="error")
            return

        # Show success state in the step page
        if hasattr(self._btn_next, "play_success"):
            self._btn_next.play_success()
        self._show_success_page()
        QTimer.singleShot(3000, lambda: self._reset() if not sip.isdeleted(self) else None)

    def _show_success_page(self):
        c = colors(self._modo)

        # Replace current step page content with a confirmation widget
        success = QWidget()
        success.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(success)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(sp("sm"))

        check_lbl = QLabel("✓")
        check_lbl.setFont(qfont(48, bold=True))
        check_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_lbl.setStyleSheet(f"color: {c['success']}; background: transparent;")
        layout.addWidget(check_lbl)

        title_lbl = QLabel("Registro guardado")
        title_lbl.setFont(qfont("size_h2", bold=True))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("Buen trabajo al identificar y cuestionar el pensamiento.")
        sub_lbl.setFont(qfont("size_body"))
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
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
        # Restore text fields
        try:
            self._txt_situacion.clear()
            self._entry_emocion.clear()
            self._txt_pensamiento.clear()
            self._txt_respuesta.clear()
            self._slider_intensidad.setValue(5)
        except Exception:
            _log.exception("Operation failed")

        self._btn_next.setEnabled(True)
        self._btn_prev.setEnabled(True)
        self._show_step()

    # ── Hooks ─────────────────────────────────────────────────────────────────

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
