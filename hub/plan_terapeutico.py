"""
hub/plan_terapeutico.py — Tab "Plan terapéutico" del detalle de paciente.

Lugar canónico ÚNICO de la configuración por paciente (informe owner v1.0,
frente 7): temporizador, recordatorios, rutina, activación, plantillas TCC y
textos personalizados. Reemplaza a la vista global "Presets" (que pedía elegir
paciente con un selector aparte): acá el paciente ya es la ficha activa.

Las clases de sub-tabs vienen de hub/editors/presets_editor.py (vista
eliminada en la reestructura); reciben (sb, pid, modo) sin cambios de lógica.
"""

import logging
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QTabWidget,
    QFrame,
    QScrollArea,
    QSizePolicy,
)

from shared.components import NMButton, NMButtonOutline, NMCard, NMInput, NMToast, nm_confirm
from shared.theme_qt import (
    norm_modo,
    qfont,
    qcolor_to_rgba_css,
    stylesheet_combobox,
    stylesheet_scrollarea,
    stylesheet_tabwidget_segmented,
    v3c,
    V3_SP,
    eyebrow_font,
)
from shared.theme import TYPOGRAPHY

_log = logging.getLogger(__name__)


def _section_title(text: str, modo: str) -> QLabel:
    """Título de panel consistente (semibold + color de texto del tema) —
    antes eran QLabel crudos con estilo por defecto, distintos entre tabs."""
    lbl = QLabel(text)
    lbl.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
    lbl.setStyleSheet(f"color: {v3c('text', norm_modo(modo)).name()}; background: transparent;")
    return lbl


def _section_header_row(text: str, modo: str, reset_btn: QWidget | None = None) -> QHBoxLayout:
    """Fila de título de panel + botón 'Restablecer por defecto' a la derecha."""
    row = QHBoxLayout()
    # Aire debajo del título/reset: sin esto el botón "Restablecer por defecto"
    # quedaba pegado al contenido (texto de "sin ítems propios" o la lista).
    # Aplica con y sin ítems propios en todos los paneles (timer/rutina/
    # recordatorios/activación).
    row.setContentsMargins(0, 0, 0, 10)
    row.setSpacing(8)
    row.addWidget(_section_title(text, modo))
    row.addStretch()
    if reset_btn is not None:
        row.addWidget(reset_btn)
    return row


def _make_reset_button(owner: QWidget, modo: str, mensaje: str, on_confirm) -> NMButtonOutline:
    """Botón 'Restablecer por defecto' con confirmación (patrón único para
    todos los configurables Hub→Suite — pedido owner v1.0: el profesional
    puede arrepentirse de un preset/texto y volver al estado de fábrica)."""
    btn = NMButtonOutline("Restablecer por defecto", modo=modo, size="sm")
    btn.setFixedHeight(28)
    btn.clicked.connect(
        lambda: nm_confirm(owner, "Restablecer por defecto", mensaje, on_confirm, modo=modo)
    )
    return btn


def _empty_hint_label(text: str, modo: str) -> QWidget:
    """Estado vacío calmo del Plan: compacto y anclado bajo el encabezado.

    Antes (v0): un QLabel suelto arriba-izquierda dejaba el panel viéndose
    "roto". Fase 5 lo centró (h+v) con minHeight 220 — pero a 960×600 el panel
    derecho hereda la altura del formulario (muy alto) y el mensaje quedaba
    flotando en el centro de un panel enorme y vacío. Ahora es una banda
    compacta (≤132px, vertical=Maximum para no estirarse a todo el panel)
    centrada en horizontal y anclada arriba (la lista usa AlignTop): se lee como
    "lista vacía" sin reservar un vacío gigante.
    """
    modo = norm_modo(modo)
    wrap = QWidget()
    wrap.setStyleSheet("background: transparent;")
    # Expanding horizontal → el texto centra sobre todo el ancho del panel.
    # Maximum vertical + maxHeight → no se estira para llenar el panel alto.
    wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    wrap.setMinimumHeight(96)
    wrap.setMaximumHeight(132)
    wl = QVBoxLayout(wrap)
    wl.setContentsMargins(V3_SP["lg"], V3_SP["xl"], V3_SP["lg"], V3_SP["lg"])
    wl.setSpacing(0)
    wl.addStretch()
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setFont(qfont("size_small"))
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"color: {v3c('ink_secondary', modo).name()}; background: transparent;"
    )
    wl.addWidget(lbl)
    wl.addStretch()
    return wrap


def _tab_scroll_wrap(body: QWidget, modo: str) -> QScrollArea:
    """Scroll-calmo vertical para los subtabs del Plan: a 960×600 el contenido
    bajo hero+tabs+subtabs tiene ~380px — sin esto Qt comprime bajo mínimo y
    los widgets se pintan encimados (patrón conocido)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet(stylesheet_scrollarea(modo))
    body.setStyleSheet("background: transparent;")
    scroll.setWidget(body)
    return scroll


def _wheel_passthrough(inner: QScrollArea) -> None:
    """Evita que un scroll interno (solapa anidada dentro del scroll de página)
    'robe' la rueda del mouse. Solo scrollea con wheel cuando el foco está
    DENTRO de la solapa (interacción directa); en caso contrario deja pasar el
    evento para que continúe el scroll de la pantalla (pedido owner: la rueda no
    debe quedar capturada al pasar por encima de la solapa sin interactuar)."""

    def _wheel(ev, _inner=inner):
        from PyQt6.QtWidgets import QApplication

        fw = QApplication.focusWidget()
        if fw is not None and (fw is _inner or _inner.isAncestorOf(fw)):
            QScrollArea.wheelEvent(_inner, ev)
        else:
            ev.ignore()

    inner.wheelEvent = _wheel


class PlanTerapeuticoTab(QWidget):
    """Contenedor del Plan terapéutico: sub-tabs por módulo del Suite."""

    def __init__(self, modo: str, sb, pid: str, nombre: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = pid
        self._nombre = nombre
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, V3_SP["sm"], 0, 0)
        lay.setSpacing(0)

        self._tabs = QTabWidget()
        # Subnivel bajo tabs underline: segmento ADN (tablero 05) para no
        # duplicar el subrayado del nivel superior.
        # Override compacto solo para estas tabs: los 4 nombres completos de los
        # módulos Suite son largos; con menos padding/fuente entran los 4 en una
        # fila a 960 sin scroll ni tabs cortadas (ADN).
        self._tabs.setStyleSheet(
            stylesheet_tabwidget_segmented(self._modo)
            + "QTabBar::tab { padding: 3px 7px; font-size: 10px; }"
        )
        self._tabs.setDocumentMode(True)

        # Reorganización owner v1.0: SOLO los 4 módulos asignables por
        # paciente. "Pensamientos" (editor de plantilla TCC) y "Textos"
        # per-paciente fueron DEMOLIDOS — los textos son globales y viven en
        # Personalización (un botón por módulo).
        # Nombres EXACTOS de los módulos de la Suite (pedido owner): el
        # profesional ve el mismo nombre que el paciente, sin ambigüedad sobre
        # qué módulo está configurando.
        self._tabs.addTab(
            _PresetRecordatoriosTab(self._sb, self._pid, self._modo, self),
            "Recordatorios de Bienestar",
        )
        self._tabs.addTab(
            _PresetTimerTab(self._sb, self._pid, self._modo, self),
            "Temporizador de Actividades",
        )
        self._tabs.addTab(
            _PresetRutinaTab(self._sb, self._pid, self._modo, self),
            "Checklist de Rutina Diaria",
        )
        self._tabs.addTab(
            _PresetActivacionTab(self._sb, self._pid, self._modo, self),
            "Asistente de Activación Conductual",
        )
        lay.addWidget(self._tabs)

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        # Override compacto solo para estas tabs: los 4 nombres completos de los
        # módulos Suite son largos; con menos padding/fuente entran los 4 en una
        # fila a 960 sin scroll ni tabs cortadas (ADN).
        self._tabs.setStyleSheet(
            stylesheet_tabwidget_segmented(self._modo)
            + "QTabBar::tab { padding: 3px 7px; font-size: 10px; }"
        )
        for i in range(self._tabs.count()):
            w = self._tabs.widget(i)
            if hasattr(w, "apply_theme"):
                w.apply_theme(modo)


# ── Subtab 1: Temporizador ───────────────────────────────────────────────────

class _PresetTimerTab(QWidget):
    def __init__(self, sb, pid: str, modo: str, parent=None):
        super().__init__(parent)
        self._sb = sb
        self._pid = pid
        self._modo = modo
        self._editing_id = None
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(12)
        outer.addWidget(_tab_scroll_wrap(body, self._modo))

        # Form (Left)
        form_card = NMCard(modo=self._modo, clickable=False)
        form_lay = QVBoxLayout(form_card)
        form_lay.setContentsMargins(12, 12, 12, 12)
        form_lay.setSpacing(8)

        # Sin jerga de developer ("preset") cara al profesional.

        self._ent_name = NMInput("Nombre (ej: Pomodoro)", modo=self._modo)
        self._ent_name.setMaxLength(24)
        self._ent_secs = NMInput("Minutos (1–180)", modo=self._modo)
        self._ent_secs.setMaxLength(3)
        self._ent_cat = NMInput("Categoría (ej: Estudio)", modo=self._modo)
        self._ent_cat.setMaxLength(20)

        form_lay.addWidget(self._ent_name)
        form_lay.addWidget(self._ent_secs)
        form_lay.addWidget(self._ent_cat)

        btn_row = QHBoxLayout()
        self._save_btn = NMButton("Agregar actividad", modo=self._modo, width=140, height=32, size="sm")
        self._save_btn.clicked.connect(self._save_preset)
        self._cancel_btn = NMButtonOutline("Cancelar", modo=self._modo)
        self._cancel_btn.setFixedHeight(32)
        self._cancel_btn.setMinimumWidth(90)
        self._cancel_btn.clicked.connect(self._cancel_edit)
        self._cancel_btn.hide()

        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        form_lay.addLayout(btn_row)

        ia_row = QHBoxLayout()
        self._ia_btn = NMButtonOutline("Completar con IA", modo=self._modo, size="sm")
        self._ia_btn.setFixedHeight(32)
        self._ia_btn.clicked.connect(self._autofill_with_ia)
        ia_row.addWidget(self._ia_btn)
        ia_row.addStretch()
        form_lay.addLayout(ia_row)
        form_lay.addStretch()

        lay.addWidget(form_card, 1)

        # List (Right)
        list_card = NMCard(modo=self._modo, clickable=False)
        list_lay = QVBoxLayout(list_card)
        list_lay.setContentsMargins(10, 10, 10, 10)

        list_lay.addLayout(_section_header_row(
            "Actividades del paciente",
            self._modo,
            _make_reset_button(
                self,
                self._modo,
                "Se eliminarán todos los temporizadores propios de este paciente. "
                "Su Suite volverá a mostrar los temporizadores por defecto.",
                self._reset_defaults,
            ),
        ))

        # Scroll Area for presets
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            stylesheet_scrollarea(self._modo)
        )
        _wheel_passthrough(scroll)
        self._list_w = QWidget()
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(6)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_w)
        list_lay.addWidget(scroll, 1)

        lay.addWidget(list_card, 2)
        self._load_presets()

    def _autofill_with_ia(self):
        self._ia_btn.setEnabled(False)
        self._ia_btn.setText("Generando…")
        from hub.ia_asistente import generar_asignacion
        from shared.qt_thread import run_on_gui

        def on_ok(txt: str):
            run_on_gui(lambda: self._on_ia_success(txt))

        def on_err(msg: str):
            run_on_gui(lambda: self._on_ia_failure(msg))

        generar_asignacion("timer", {}, "", on_ok, on_err, patient_id=self._pid)

    def _on_ia_success(self, text: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        vals = {}
        for line in text.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                vals[k.strip().lower()] = v.strip()
        if vals.get("nombre"):
            self._ent_name.setText(vals["nombre"][:24])
        if vals.get("minutos"):
            self._ent_secs.setText(vals["minutos"][:3])
        if vals.get("categoria"):
            self._ent_cat.setText(vals["categoria"][:20])
        NMToast.display(self.window(), "Temporizador sugerido por la IA", variant="success")

    def _on_ia_failure(self, msg: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")

    def _empty_hint(self, text: str) -> QWidget:
        return _empty_hint_label(text, self._modo)

    def _load_presets(self):
        # Clear
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._sb:
            # Sin conexión el panel quedaba en blanco absoluto: dar contexto.
            self._list_lay.addWidget(
                self._empty_hint("Este paciente todavía no tiene temporizadores propios.")
            )
            return

        try:
            res = (
                self._sb.table("timer_presets_remote")
                .select("id,scope,name,duracion_seg,categoria,activo")
                .eq("scope", f"patient:{self._pid}")
                .order("name")
                .execute()
            )
            rows = res.data or []
            if not rows:
                self._list_lay.addWidget(
                    self._empty_hint(
                        "Este paciente todavía no tiene temporizadores propios. "
                        "Agregá uno desde el panel izquierdo."
                    )
                )
                return

            for row in rows:
                row_w = QFrame()
                # 6.2: borderSoft rgba — preservar alpha.
                row_w.setStyleSheet(
                    f"background: {v3c('surface', self._modo).name()}; "
                    f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                    "border-radius: 6px; padding: 4px;"
                )
                # Fila con aire: los botones a 24px pegados se veían
                # "apretados y feos" (informe owner v1.0, Presets).
                row_lay = QHBoxLayout(row_w)
                row_lay.setContentsMargins(10, 6, 10, 6)
                row_lay.setSpacing(8)

                name = row.get("name", "")
                mins = int(row.get("duracion_seg", 0)) // 60
                cat = row.get("categoria", "")

                lbl = QLabel(f"{name} ({mins} min) · {cat}")
                lbl.setFont(qfont("size_small"))
                lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
                row_lay.addWidget(lbl, 1)

                btn_edit = NMButtonOutline("Editar", modo=self._modo)
                btn_edit.setFixedHeight(28)
                btn_edit.setMinimumWidth(60)
                btn_edit.clicked.connect(lambda _, r=row: self._edit(r))
                row_lay.addWidget(btn_edit)

                btn_del = NMButtonOutline("✕", modo=self._modo)
                btn_del.setFixedSize(28, 28)
                btn_del.clicked.connect(lambda _, rid=row["id"]: self._delete(rid))
                row_lay.addWidget(btn_del)

                self._list_lay.addWidget(row_w)
        except Exception:
            _log.exception("Error al cargar presets de timer")

    def _save_preset(self):
        name = self._ent_name.text().strip()
        dur_str = self._ent_secs.text().strip()
        cat = self._ent_cat.text().strip() or "Timer"

        if not name or not dur_str:
            NMToast.display(self.window(), "Completá nombre y duración", variant="error")
            return

        if len(name) > 30:
            NMToast.display(self.window(), "Nombre muy largo (máx 30)", variant="error")
            return

        try:
            dur_mins = int(dur_str)
            if not (1 <= dur_mins <= 180):
                raise ValueError
            dur_seg = dur_mins * 60
        except ValueError:
            NMToast.display(self.window(), "Duración debe ser entre 1 y 180 min", variant="error")
            return

        try:
            payload = {
                "scope": f"patient:{self._pid}",
                "name": name,
                "duracion_seg": dur_seg,
                "categoria": cat,
                "activo": True,
            }
            if self._editing_id:
                self._sb.table("timer_presets_remote").update(payload).eq("id", self._editing_id).execute()
                NMToast.display(self.window(), "Temporizador actualizado", variant="success")
            else:
                self._sb.table("timer_presets_remote").insert(payload).execute()
                NMToast.display(self.window(), "Temporizador agregado", variant="success")

            self._cancel_edit()
            self._load_presets()
        except Exception as e:
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")

    def _edit(self, row: dict):
        self._editing_id = row["id"]
        self._ent_name.setText(row.get("name", ""))
        self._ent_secs.setText(str(int(row.get("duracion_seg", 0)) // 60))
        self._ent_cat.setText(row.get("categoria", ""))
        self._save_btn.setText("Guardar")
        self._cancel_btn.show()

    def _cancel_edit(self):
        self._editing_id = None
        self._ent_name.clear()
        self._ent_secs.clear()
        self._ent_cat.clear()
        self._save_btn.setText("Agregar actividad")
        self._cancel_btn.hide()

    def _delete(self, rid: int):
        try:
            self._sb.table("timer_presets_remote").delete().eq("id", rid).execute()
            self._load_presets()
        except Exception:
            _log.exception("Error deleting timer preset")

    def _reset_defaults(self):
        if not self._sb:
            NMToast.display(self.window(), "Sin conexión: no hay nada que restablecer.", variant="info")
            return
        try:
            self._sb.table("timer_presets_remote").delete().eq(
                "scope", f"patient:{self._pid}"
            ).execute()
            self._cancel_edit()
            self._load_presets()
            NMToast.display(
                self.window(), "Temporizadores restablecidos por defecto.", variant="success"
            )
        except Exception as e:
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")


# ── Subtab 2: Recordatorios ───────────────────────────────────────────────────

class _PresetRecordatoriosTab(QWidget):
    """Tab unificado de Recordatorios de Bienestar.

    Combina mensaje y hora en un unico formulario: hora + mensaje
    se asignan juntos con un solo boton 'Agregar recordatorio'.
    """

    def __init__(self, sb, pid: str, modo: str, parent=None):
        super().__init__(parent)
        self._sb = sb
        self._pid = pid
        self._modo = modo
        self._ia_btn = None
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(12)
        outer.addWidget(_tab_scroll_wrap(body, self._modo))

        # Form card (Left)
        form_card = NMCard(modo=self._modo, clickable=False)
        form_lay = QVBoxLayout(form_card)
        form_lay.setContentsMargins(12, 12, 12, 12)
        form_lay.setSpacing(8)


        self._ent_hora = NMInput("Hora (HH:MM, ej: 08:30)", modo=self._modo)
        self._ent_hora.setMaxLength(5)
        self._ent_msg = NMInput("Mensaje del recordatorio (máx 150)", modo=self._modo)
        self._ent_msg.setMaxLength(150)
        form_lay.addWidget(self._ent_hora)
        form_lay.addWidget(self._ent_msg)

        btn_row = QHBoxLayout()
        self._save_btn = NMButton(
            "Agregar recordatorio", modo=self._modo, width=180, height=32, size="sm"
        )
        self._save_btn.clicked.connect(self._save_recordatorio)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        form_lay.addLayout(btn_row)

        ia_row = QHBoxLayout()
        self._ia_btn = NMButtonOutline("Completar con IA", modo=self._modo, size="sm")
        self._ia_btn.setFixedHeight(32)
        self._ia_btn.clicked.connect(self._autofill_with_ia)
        ia_row.addWidget(self._ia_btn)
        ia_row.addStretch()
        form_lay.addLayout(ia_row)
        form_lay.addStretch()

        lay.addWidget(form_card, 1)

        # List card (Right)
        list_card = NMCard(modo=self._modo, clickable=False)
        list_lay = QVBoxLayout(list_card)
        list_lay.setContentsMargins(10, 10, 10, 10)

        list_lay.addLayout(_section_header_row(
            "Recordatorios del paciente",
            self._modo,
            _make_reset_button(
                self,
                self._modo,
                "Se eliminarán todos los recordatorios asignados a este paciente. "
                "Su Suite quedará sin alertas del profesional.",
                self._reset_recordatorios,
            ),
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        _wheel_passthrough(scroll)
        self._list_w = QWidget()
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(4)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_w)
        list_lay.addWidget(scroll, 1)

        lay.addWidget(list_card, 2)
        self._load_recordatorios()

    def _load_recordatorios(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._sb:
            self._list_lay.addWidget(
                _empty_hint_label("Sin recordatorios asignados aún.", self._modo)
            )
            return
        try:
            res = (
                self._sb.table("assigned_reminders")
                .select("id,hora,mensaje,activa")
                .eq("patient_id", self._pid)
                .order("hora")
                .execute()
            )
            rows = res.data or []
            if not rows:
                self._list_lay.addWidget(
                    _empty_hint_label("Sin recordatorios asignados aún.", self._modo)
                )
                return
            for r in rows:
                w = QFrame()
                w.setStyleSheet(
                    f"background: {v3c('surface', self._modo).name()}; "
                    f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                    "border-radius: 6px; padding: 4px;"
                )
                wl = QHBoxLayout(w)
                wl.setContentsMargins(10, 6, 10, 6)
                wl.setSpacing(8)

                lbl = QLabel(f"{r.get('hora')} · {r.get('mensaje')}")
                lbl.setFont(qfont("size_caption"))
                lbl.setWordWrap(True)
                lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
                wl.addWidget(lbl, 1)

                btn_del = NMButtonOutline("✕", modo=self._modo)
                btn_del.setFixedSize(28, 28)
                btn_del.clicked.connect(lambda _, rid=r["id"]: self._delete_recordatorio(rid))
                wl.addWidget(btn_del)

                self._list_lay.addWidget(w)
        except Exception:
            _log.exception("Error al cargar recordatorios")

    def _save_recordatorio(self):
        hora = self._ent_hora.text().strip()
        msg = self._ent_msg.text().strip()
        if not hora or not msg:
            NMToast.display(self.window(), "Completá la hora y el mensaje", variant="error")
            return
        if not re.match(r"^\d{2}:\d{2}$", hora):
            NMToast.display(
                self.window(), "Formato de hora incorrecto (debe ser HH:MM)", variant="error"
            )
            return
        if len(msg) > 150:
            NMToast.display(self.window(), "Mensaje muy largo (máx 150)", variant="error")
            return
        try:
            self._sb.table("assigned_reminders").insert({
                "patient_id": self._pid,
                "hora": hora,
                "mensaje": msg,
                "dias": "1,2,3,4,5,6,7",
                "activa": True,
            }).execute()
            self._ent_hora.clear()
            self._ent_msg.clear()
            self._load_recordatorios()
            NMToast.display(self.window(), "Recordatorio agregado", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:50], variant="error")

    def _delete_recordatorio(self, rid: int):
        try:
            self._sb.table("assigned_reminders").delete().eq("id", rid).execute()
            self._load_recordatorios()
        except Exception:
            pass

    def _reset_recordatorios(self):
        if not self._sb:
            NMToast.display(
                self.window(), "Sin conexión: no hay nada que restablecer.", variant="info"
            )
            return
        try:
            self._sb.table("assigned_reminders").delete().eq(
                "patient_id", self._pid
            ).execute()
            try:
                self._sb.table("support_messages").delete().eq(
                    "scope", f"patient:{self._pid}"
                ).execute()
            except Exception:
                pass
            self._load_recordatorios()
            NMToast.display(
                self.window(), "Recordatorios restablecidos por defecto.", variant="success"
            )
        except Exception as e:
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")

    def _autofill_with_ia(self):
        if self._ia_btn:
            self._ia_btn.setEnabled(False)
            self._ia_btn.setText("Generando…")
        from hub.ia_asistente import generar_asignacion
        from shared.qt_thread import run_on_gui

        def on_ok(txt: str):
            run_on_gui(lambda: self._on_ia_success(txt))

        def on_err(msg: str):
            run_on_gui(lambda: self._on_ia_failure(msg))

        generar_asignacion("avisos", {}, "", on_ok, on_err, patient_id=self._pid)

    def _on_ia_success(self, text: str):
        if self._ia_btn:
            self._ia_btn.setEnabled(True)
            self._ia_btn.setText("Completar con IA")
        vals = {}
        for line in text.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                vals[k.strip().lower()] = v.strip()
        if vals.get("hora"):
            self._ent_hora.setText(vals["hora"][:5])
        if vals.get("mensaje"):
            self._ent_msg.setText(vals["mensaje"][:150])
        NMToast.display(self.window(), "Recordatorio sugerido por la IA", variant="success")

    def _on_ia_failure(self, msg: str):
        if self._ia_btn:
            self._ia_btn.setEnabled(True)
            self._ia_btn.setText("Completar con IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")


# ── Subtab 3: Routine/Checklist ───────────────────────────────────────────────

class _PresetRutinaTab(QWidget):
    def __init__(self, sb, pid: str, modo: str, parent=None):
        super().__init__(parent)
        self._sb = sb
        self._pid = pid
        self._modo = modo
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(12)
        outer.addWidget(_tab_scroll_wrap(body, self._modo))

        # Form (Left)
        form_card = NMCard(modo=self._modo, clickable=False)
        form_lay = QVBoxLayout(form_card)
        form_lay.setContentsMargins(12, 12, 12, 12)
        form_lay.setSpacing(8)


        self._ent_task = NMInput("Descripción de la tarea (máx 100)", modo=self._modo)
        self._ent_task.setMaxLength(100)
        self._combo_sec = QComboBox()
        self._combo_sec.setStyleSheet(stylesheet_combobox(self._modo))
        for key, val in (("manana", "Mañana"), ("tarde", "Tarde"), ("noche", "Noche")):
            self._combo_sec.addItem(val, key)

        form_lay.addWidget(self._ent_task)
        form_lay.addWidget(self._combo_sec)

        self._save_btn = NMButton("Asignar tarea", modo=self._modo, width=130, height=32, size="sm")
        self._save_btn.clicked.connect(self._save_task)
        form_lay.addWidget(self._save_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        ia_row = QHBoxLayout()
        self._ia_btn = NMButtonOutline("Completar con IA", modo=self._modo, size="sm")
        self._ia_btn.setFixedHeight(32)
        self._ia_btn.clicked.connect(self._autofill_with_ia)
        ia_row.addWidget(self._ia_btn)
        ia_row.addStretch()
        form_lay.addLayout(ia_row)
        form_lay.addStretch()

        lay.addWidget(form_card, 1)

        # List (Right)
        list_card = NMCard(modo=self._modo, clickable=False)
        list_lay = QVBoxLayout(list_card)
        list_lay.setContentsMargins(10, 10, 10, 10)

        list_lay.addLayout(_section_header_row(
            "Tareas del paciente",
            self._modo,
            _make_reset_button(
                self,
                self._modo,
                "Se eliminarán las tareas de rutina asignadas a este paciente. "
                "Su Suite volverá a la rutina por defecto.",
                self._reset_defaults,
            ),
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            stylesheet_scrollarea(self._modo)
        )
        _wheel_passthrough(scroll)
        self._list_w = QWidget()
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(4)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_w)
        list_lay.addWidget(scroll, 1)

        lay.addWidget(list_card, 2)
        self._load_tasks()

    def _autofill_with_ia(self):
        self._ia_btn.setEnabled(False)
        self._ia_btn.setText("Generando…")
        from hub.ia_asistente import generar_asignacion
        from shared.qt_thread import run_on_gui

        def on_ok(txt: str):
            run_on_gui(lambda: self._on_ia_success(txt))

        def on_err(msg: str):
            run_on_gui(lambda: self._on_ia_failure(msg))

        generar_asignacion("rutina", {}, "", on_ok, on_err, patient_id=self._pid)

    def _on_ia_success(self, text: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        vals = {}
        for line in text.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                vals[k.strip().lower()] = v.strip()
        if vals.get("tarea"):
            self._ent_task.setText(vals["tarea"][:100])
        if vals.get("seccion"):
            sec_map = {"manana": 0, "mañana": 0, "tarde": 1, "noche": 2}
            idx = sec_map.get(vals["seccion"].lower(), 0)
            self._combo_sec.setCurrentIndex(idx)
        NMToast.display(self.window(), "Tarea sugerida por la IA", variant="success")

    def _on_ia_failure(self, msg: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")

    def _load_tasks(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._sb:
            self._list_lay.addWidget(
                _empty_hint_label("Sin tareas asignadas aún.", self._modo)
            )
            return
        try:
            res = (
                self._sb.table("assigned_tasks")
                .select("id,descripcion,seccion,activa")
                .eq("patient_id", self._pid)
                .execute()
            )
            rows = res.data or []
            if not rows:
                self._list_lay.addWidget(_empty_hint_label("Sin tareas asignadas aún.", self._modo))
                return

            # Group by section for readability
            sections_map = {"manana": "Mañana", "tarde": "Tarde", "noche": "Noche"}
            for sec_key, sec_name in sections_map.items():
                sec_tasks = [r for r in rows if r.get("seccion") == sec_key]
                if not sec_tasks:
                    continue

                header = QLabel(sec_name)
                header.setFont(eyebrow_font())
                header.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; margin-top: 8px;")
                self._list_lay.addWidget(header)

                for r in sec_tasks:
                    w = QFrame()
                    w.setStyleSheet(f"background: {v3c('surface', self._modo).name()}; border-radius: 4px; padding: 4px;")
                    wl = QHBoxLayout(w)
                    wl.setContentsMargins(8, 2, 8, 2)

                    lbl = QLabel(r.get("descripcion"))
                    lbl.setFont(qfont("size_small"))
                    lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
                    wl.addWidget(lbl, 1)

                    btn_del = NMButtonOutline("✕", modo=self._modo)
                    btn_del.setFixedSize(28, 28)
                    btn_del.clicked.connect(lambda _, rid=r["id"]: self._delete_task(rid))
                    wl.addWidget(btn_del)

                    self._list_lay.addWidget(w)
        except Exception:
            _log.exception("Error al cargar tareas de rutina")

    def _save_task(self):
        desc = self._ent_task.text().strip()
        sec = self._combo_sec.currentData()
        if not desc:
            return
        if len(desc) > 100:
            NMToast.display(self.window(), "Descripción muy larga (máx 100)", variant="error")
            return
        try:
            self._sb.table("assigned_tasks").insert({
                "patient_id": self._pid,
                "descripcion": desc,
                "seccion": sec,
                "activa": True,
            }).execute()
            self._ent_task.clear()
            self._load_tasks()
            NMToast.display(self.window(), "Tarea de rutina asignada", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:50], variant="error")

    def _delete_task(self, rid: int):
        try:
            self._sb.table("assigned_tasks").delete().eq("id", rid).execute()
            self._load_tasks()
        except Exception:
            pass

    def _reset_defaults(self):
        if not self._sb:
            NMToast.display(self.window(), "Sin conexión: no hay nada que restablecer.", variant="info")
            return
        try:
            self._sb.table("assigned_tasks").delete().eq("patient_id", self._pid).execute()
            self._load_tasks()
            NMToast.display(
                self.window(), "Rutina restablecida por defecto.", variant="success"
            )
        except Exception as e:
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")


# ── Subtab 4: Activación Conductual ───────────────────────────────────────────

class _PresetActivacionTab(QWidget):
    def __init__(self, sb, pid: str, modo: str, parent=None):
        super().__init__(parent)
        self._sb = sb
        self._pid = pid
        self._modo = modo
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        body = QWidget()
        lay = QHBoxLayout(body)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(12)
        outer.addWidget(_tab_scroll_wrap(body, self._modo))

        # Form (Left)
        form_card = NMCard(modo=self._modo, clickable=False)
        form_lay = QVBoxLayout(form_card)
        form_lay.setContentsMargins(12, 12, 12, 12)
        form_lay.setSpacing(8)


        self._ent_name = NMInput("Nombre (ej: Caminata corta, máx 50)", modo=self._modo)
        self._ent_name.setMaxLength(50)
        self._ent_desc = NMInput("Descripción (ej: 15 min de aire fresco)", modo=self._modo)
        self._ent_desc.setMaxLength(120)

        self._combo_cat = QComboBox()
        self._combo_cat.setStyleSheet(stylesheet_combobox(self._modo))
        for cat in ("Autocuidado", "Física", "Cognitiva", "Placer", "Social", "Maestría"):
            self._combo_cat.addItem(cat, cat)

        # Rango de ánimo (1-10) — items cortos ("Mín: N"): el texto largo
        # inflaba el ancho mínimo de la columna y recortaba la card derecha.
        range_lbl = QLabel("Rango de ánimo en el que se sugiere")
        range_lbl.setFont(qfont("size_caption"))
        range_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        range_lay = QHBoxLayout()
        self._combo_min = QComboBox()
        self._combo_min.setStyleSheet(stylesheet_combobox(self._modo))
        self._combo_max = QComboBox()
        self._combo_max.setStyleSheet(stylesheet_combobox(self._modo))
        for i in range(1, 11):
            self._combo_min.addItem(f"Mín: {i}", i)
            self._combo_max.addItem(f"Máx: {i}", i)
        self._combo_max.setCurrentIndex(9)  # default max = 10
        range_lay.addWidget(self._combo_min)
        range_lay.addWidget(self._combo_max)
        range_lay.addStretch()

        form_lay.addWidget(self._ent_name)
        form_lay.addWidget(self._ent_desc)
        form_lay.addWidget(self._combo_cat)
        form_lay.addWidget(range_lbl)
        form_lay.addLayout(range_lay)

        self._save_btn = NMButton(
            "Agregar actividad", modo=self._modo, width=150, height=32, size="sm"
        )
        self._save_btn.clicked.connect(self._save_activity)
        form_lay.addWidget(self._save_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # IA Assist Button
        ia_row = QHBoxLayout()
        self._ia_btn = NMButtonOutline("Completar con IA", modo=self._modo, size="sm")
        self._ia_btn.setFixedHeight(32)
        self._ia_btn.clicked.connect(self._autofill_with_ia)
        ia_row.addWidget(self._ia_btn)
        ia_row.addStretch()
        form_lay.addLayout(ia_row)

        form_lay.addStretch()

        lay.addWidget(form_card, 1)

        # List (Right)
        list_card = NMCard(modo=self._modo, clickable=False)
        list_lay = QVBoxLayout(list_card)
        list_lay.setContentsMargins(10, 10, 10, 10)

        list_lay.addLayout(_section_header_row(
            "Actividades del paciente",
            self._modo,
            _make_reset_button(
                self,
                self._modo,
                "Se eliminarán las actividades personalizadas de este paciente. "
                "Su Suite volverá a sugerir las actividades por defecto.",
                self._reset_defaults,
            ),
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            stylesheet_scrollarea(self._modo)
        )
        _wheel_passthrough(scroll)
        self._list_w = QWidget()
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(4)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_w)
        list_lay.addWidget(scroll, 1)

        lay.addWidget(list_card, 2)
        self._load_activities()

    def _load_activities(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._sb:
            self._list_lay.addWidget(
                _empty_hint_label("Sin actividades personalizadas aún.", self._modo)
            )
            return
        try:
            res = (
                self._sb.table("patient_activities")
                .select("id,nombre,descripcion,categoria,animo_min,animo_max")
                .eq("patient_id", self._pid)
                .execute()
            )
            rows = res.data or []
            if not rows:
                self._list_lay.addWidget(_empty_hint_label("Sin actividades personalizadas aún.", self._modo))
                return
            for r in rows:
                w = QFrame()
                w.setStyleSheet(f"background: {v3c('surface', self._modo).name()}; border-radius: 4px; padding: 4px;")
                wl = QHBoxLayout(w)
                wl.setContentsMargins(8, 2, 8, 2)

                name = r.get("nombre")
                desc = r.get("descripcion", "")
                cat = r.get("categoria", "")
                amin = r.get("animo_min", 1)
                amax = r.get("animo_max", 10)

                info = QLabel(f"<b>{name}</b> ({cat}) · Rango: {amin}-{amax}<br/><font color='gray'>{desc}</font>")
                info.setFont(qfont("size_small"))
                info.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
                wl.addWidget(info, 1)

                btn_del = NMButtonOutline("✕", modo=self._modo)
                btn_del.setFixedSize(28, 28)
                btn_del.clicked.connect(lambda _, rid=r["id"]: self._delete_activity(rid))
                wl.addWidget(btn_del)

                self._list_lay.addWidget(w)
        except Exception:
            _log.exception("Error al cargar actividades")

    def _save_activity(self):
        name = self._ent_name.text().strip()
        desc = self._ent_desc.text().strip()
        cat = self._combo_cat.currentText()
        amin = self._combo_min.currentData()
        amax = self._combo_max.currentData()

        if not name:
            return
        if len(name) > 50:
            NMToast.display(self.window(), "Nombre muy largo (máx 50)", variant="error")
            return
        if len(desc) > 150:
            NMToast.display(self.window(), "Descripción muy larga (máx 150)", variant="error")
            return
        if amin > amax:
            NMToast.display(self.window(), "Ánimo mínimo no puede ser mayor al máximo", variant="error")
            return

        try:
            self._sb.table("patient_activities").insert({
                "patient_id": self._pid,
                "nombre": name,
                "descripcion": desc,
                "categoria": cat,
                "animo_min": amin,
                "animo_max": amax,
                "activa": True,
            }).execute()
            self._ent_name.clear()
            self._ent_desc.clear()
            self._load_activities()
            NMToast.display(self.window(), "Actividad agregada al catálogo", variant="success")
        except Exception as e:
            NMToast.display(self.window(), str(e)[:50], variant="error")

    def _delete_activity(self, rid: int):
        try:
            self._sb.table("patient_activities").delete().eq("id", rid).execute()
            self._load_activities()
        except Exception:
            pass

    def _reset_defaults(self):
        if not self._sb:
            NMToast.display(self.window(), "Sin conexión: no hay nada que restablecer.", variant="info")
            return
        try:
            self._sb.table("patient_activities").delete().eq("patient_id", self._pid).execute()
            self._load_activities()
            NMToast.display(
                self.window(), "Actividades restablecidas por defecto.", variant="success"
            )
        except Exception as e:
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")

    def _autofill_with_ia(self):
        name = self._ent_name.text().strip()
        if not name:
            NMToast.display(self.window(), "Escribí el nombre primero para que la IA sugiera la descripción.", variant="info")
            return
        self._ia_btn.setEnabled(False)
        self._ia_btn.setText("Generando…")

        # Async run via ia_asistente
        from hub.ia_asistente import autocompletar_actividad
        from shared.qt_thread import run_on_gui

        def on_ok(txt: str):
            run_on_gui(lambda: self._on_ia_success(txt))

        def on_err(msg: str):
            run_on_gui(lambda: self._on_ia_failure(msg))

        autocompletar_actividad(name, on_ok, on_err, patient_id=self._pid)

    def _on_ia_success(self, text: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        self._ent_desc.setText(text[:150])
        NMToast.display(self.window(), "Descripción sugerida por la IA", variant="success")

    def _on_ia_failure(self, msg: str):
        self._ia_btn.setEnabled(True)
        self._ia_btn.setText("Completar con IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")
