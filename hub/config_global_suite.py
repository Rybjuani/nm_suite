"""
hub/config_global_suite.py — Vista "Configuración global de Suite" del Hub.

Reemplaza por completo a la antigua "Personalización". Muestra un CLON real,
navegable y de solo-lectura de la Suite del paciente (onboarding + Home + los 8
módulos enteros, en sus estados vacíos y con datos de demostración), con la misma
estructura, apariencia y navegación que la Suite instalada.

Única edición permitida: los TEXTOS globales configurables. Cualquier otra
interacción es inerte (no escribe registros, no sincroniza datos de paciente, no
modifica estados clínicos). Los cambios se guardan con "Guardar cambios"
(scope='global' en `hub_config`, claves `text.ovr.*`) y se sincronizan a la Suite
de todos los pacientes; "Restaurar por defecto" revierte a los textos originales.

Estados de demostración:
    - Los estados "con datos" usan los fixtures de `shared.visual_qa`
      (NM_VISUAL_QA) → tareas/recordatorios/temporizadores/actividades simulados
      SIN tocar la base de datos. Son solo de previsualización: no se guardan, no
      se sincronizan, no se vuelven contenido real. Solo los TEXTOS configurados
      sobre esos estados se guardan globalmente.
    - Los datos simulados (nombres de tareas, mensajes de recordatorio, etc.) NO
      se ofrecen como editables (son datos individuales del paciente, no textos
      globales); solo los textos estáticos de UI son editables.

Robustez:
    - Cada pantalla/estado se construye UNA vez y se cachea en un QStackedWidget;
      no se destruyen mientras el menú está abierto (destruir un módulo vivo con
      timers a mitad de transición segfaultea).
    - Las vistas se instancian contra una SQLite temporal vacía (NEUROMOOD_TEST_DB).
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import re
import tempfile
from contextlib import contextmanager
from functools import lru_cache

from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from shared.components import (
    NMButton,
    NMButtonOutline,
    NMInput,
    NMTextArea,
    NMToast,
    nm_confirm,
)
from shared.theme import TYPOGRAPHY
from shared.theme_qt import (
    V3_SP,
    _clinical_scrollbar_qss,
    nm_icon,
    norm_modo,
    qcolor_to_rgba_css,
    qfont,
    qfont_mono,
    v3c,
)
from shared.text_overrides import PREFIX, TextSite, collect_texts

_log = logging.getLogger(__name__)

_BRAND_DEFAULT = "NeuroMood Suite"

# Módulos reales de la Suite (mismo registry que app/main_qt.py).
_MODULE_MAP = {
    "animo": ("app.modules.animo_qt", "ModuloAnimo"),
    "respiracion": ("app.modules.respiracion_qt", "ModuloRespiracion"),
    "registro": ("app.modules.registro_tcc_qt", "ModuloRegistroTCC"),
    "rutina": ("app.modules.rutina_qt", "ModuloRutina"),
    "actividades": ("app.modules.actividades_qt", "ModuloActividades"),
    "timer": ("app.modules.timer_qt", "ModuloTimer"),
    "avisos": ("app.modules.avisos_qt", "ModuloAvisos"),
    "dbt": ("app.modules.dbt_qt", "ModuloDBT"),
}

# Rail de pantallas: secciones (header) + estados. Cada estado:
# (label, screen_id, qa)  — qa=True usa fixtures de demostración (con datos).
_RAIL: list[dict] = [
    {"header": "Acceso"},
    {"label": "Primer arranque", "screen": "onboarding", "qa": False},
    {"header": "Inicio"},
    {"label": "Home · con datos", "screen": "home", "qa": True},
    {"label": "Home · vacío", "screen": "home", "qa": False},
    {"header": "Módulos"},
    {"label": "Termómetro · con datos", "screen": "animo", "qa": True},
    {"label": "Termómetro · vacío", "screen": "animo", "qa": False},
    {"label": "Respiración · con sesiones", "screen": "respiracion", "qa": True},
    {"label": "Respiración · vacío", "screen": "respiracion", "qa": False},
    {"label": "Registro TCC", "screen": "registro", "qa": False},
    {"label": "Rutina · con tareas", "screen": "rutina", "qa": True},
    {"label": "Rutina · vacío", "screen": "rutina", "qa": False},
    {"label": "Activación · con actividades", "screen": "actividades", "qa": True},
    {"label": "Activación · vacío", "screen": "actividades", "qa": False},
    {"label": "Temporizador · con sesiones", "screen": "timer", "qa": True},
    {"label": "Temporizador · vacío", "screen": "timer", "qa": False},
    {"label": "Recordatorios · activos", "screen": "avisos", "qa": True},
    {"label": "Recordatorios · vacío", "screen": "avisos", "qa": False},
    {"label": "Habilidades DBT · con datos", "screen": "dbt", "qa": True},
    {"label": "Habilidades DBT · vacío", "screen": "dbt", "qa": False},
]

_ICONS = {
    "onboarding": "user", "home": "home", "animo": "mood", "respiracion": "leaf",
    "registro": "brain", "rutina": "routine", "actividades": "run", "timer": "timer",
    "avisos": "bell", "dbt": "spark",
}

# Patrones de texto DINÁMICO (datos, no UI editable): contadores, porcentajes,
# horas, "N de M", fechas. Estos no son textos globales configurables.
_DATA_RE = re.compile(
    r"^\s*("
    r"\d+\s*/\s*\d+"            # 3/5
    r"|\d+\s*%.*"               # 60% ...
    r"|\d+\s+de\s+\d+.*"        # 6 de 10 ...
    r"|\d{1,2}:\d{2}"           # 08:00
    r"|[\d\s.,:%/+\-]+"         # solo números/símbolos
    r")\s*$",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _fixture_data_strings() -> frozenset[str]:
    """Strings de datos simulados (no editables: son datos individuales)."""
    out: set[str] = set()
    try:
        from shared import visual_qa as vq
        for sec in vq.routine_sections().values():
            for it in sec:
                out.add(str(it.get("descripcion", "")).strip())
        for r in vq.reminder_rows():
            out.add(str(r.get("mensaje", "")).strip())
        for a in vq.activity_suggestions():
            out.add(str(a.get("nombre", "")).strip())
            out.add(str(a.get("descripcion", "")).strip())
        for s in vq.timer_sessions():
            out.add(str(s).strip())
        out.add(vq.qa_patient_name().strip())
        out.add(vq.qa_patient_name().title().strip())
    except Exception as exc:
        _log.debug("fixture strings: %s", exc)
    out.discard("")
    return frozenset(out)


def _is_data_text(txt: str) -> bool:
    t = (txt or "").strip()
    if not t:
        return True
    if t in _fixture_data_strings():
        return True
    if _DATA_RE.match(t):
        return True
    return False


def _compute_max_len(widget: QWidget, default: str, kind: str) -> int:
    """Tope de caracteres por ubicación real: lo que entra en el ancho del
    componente × las líneas permitidas (evita cortes/desbordes)."""
    text = default or ""
    nl = text.count("\n")
    multiline = isinstance(widget, (QTextEdit, QPlainTextEdit)) or nl > 0
    w = 0
    try:
        w = widget.width()
        if w <= 1:
            w = widget.sizeHint().width()
    except Exception:
        pass
    if w <= 1:
        w = 220
    try:
        avg = QFontMetrics(widget.font()).averageCharWidth() or 7
    except Exception:
        avg = 7
    per_line = max(6, int((w - 12) / max(4, avg)))
    if multiline:
        lines = max(nl + 1, 3)
        cap, lo, hi = per_line * lines, 24, 400
    else:
        cap, lo, hi = per_line, 8, 140
    limit = min(max(cap, len(text) + 4), hi)
    return max(lo, limit, len(text))


class _CloneDB:
    """SQLite temporal y vacía para instanciar las vistas reales sin tocar datos."""

    def __init__(self):
        self._dir = tempfile.mkdtemp(prefix="nm_hub_clone_db_")
        self._path = os.path.join(self._dir, "clone.db")
        self._ready = False

    def ensure(self):
        if self._ready:
            return
        with self.active(qa=False):
            try:
                from shared.db import inicializar_tablas
                inicializar_tablas()
            except Exception as exc:
                _log.debug("CloneDB init: %s", exc)
        self._ready = True

    @contextmanager
    def active(self, qa: bool):
        prev_db = os.environ.get("NEUROMOOD_TEST_DB")
        prev_qa = os.environ.get("NM_VISUAL_QA")
        os.environ["NEUROMOOD_TEST_DB"] = self._path
        if qa:
            os.environ["NM_VISUAL_QA"] = "1"
        else:
            os.environ.pop("NM_VISUAL_QA", None)
        try:
            yield
        finally:
            for var, prev in (("NEUROMOOD_TEST_DB", prev_db), ("NM_VISUAL_QA", prev_qa)):
                if prev is None:
                    os.environ.pop(var, None)
                else:
                    os.environ[var] = prev


class ConfigGlobalSuiteView(QWidget):
    """Clon navegable, read-only y editable (solo textos) de la Suite."""

    def __init__(self, modo: str, sb, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._clonedb = _CloneDB()

        self._saved: dict[str, str] = {}
        self._pending: dict[str, str] = {}
        self._default_by_key: dict[str, str] = {}
        self._sites_by_key: dict[str, list[TextSite]] = {}
        self._inert_ids: set[int] = set()

        self._screen_pane: dict[tuple[str, bool], QWidget] = {}
        self._suite_frames: list[QFrame] = []
        self._scrolls: list[QScrollArea] = []
        self._current_sites: list[TextSite] = []
        self._editing_key: str | None = None
        self._row_entry: dict[int, dict] = {}

        self._load_saved()
        self._setup()

    # ── Carga / persistencia (hub_config) ──────────────────────────────────────

    def _load_saved(self):
        self._saved = {}
        if not self._sb:
            return
        try:
            res = (
                self._sb.table("hub_config")
                .select("key,value")
                .eq("scope", "global")
                .like("key", PREFIX + "%")
                .execute()
            )
            for row in res.data or []:
                val = row.get("value")
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                self._saved[row["key"]] = str(val or "")
        except Exception:
            _log.exception("Error al cargar textos globales (hub_config)")

    def _effective(self) -> dict[str, str]:
        eff = dict(self._saved)
        eff.update(self._pending)
        return eff

    # ── Setup UI ────────────────────────────────────────────────────────────────

    def _setup(self):
        self.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["xs"])
        root.setSpacing(V3_SP["xs"])

        # Encabezado compacto: una línea (eyebrow + hint) + acciones a la derecha.
        header = QHBoxLayout()
        header.setSpacing(V3_SP["md"])
        htxt = QVBoxLayout()
        htxt.setSpacing(0)
        self._eyebrow = QLabel("Configuración global de Suite · clon read-only")
        self._eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        htxt.addWidget(self._eyebrow)
        self._hint = QLabel(
            "Clic en cualquier texto para editarlo. Solo se guardan textos; ninguna "
            "otra interacción genera registros."
        )
        self._hint.setFont(qfont("size_caption_xs"))
        htxt.addWidget(self._hint)
        header.addLayout(htxt, stretch=1)
        self._restore_btn = NMButtonOutline("Restaurar por defecto", modo=self._modo, size="sm")
        self._restore_btn.clicked.connect(self._ask_restore_all)
        header.addWidget(self._restore_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._save_btn = NMButton("Guardar cambios", modo=self._modo, size="sm", width=150)
        self._save_btn.clicked.connect(self._save_changes)
        header.addWidget(self._save_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(V3_SP["md"])

        self._rail = QListWidget()
        self._rail.setFixedWidth(208)
        self._rail.setIconSize(QSize(16, 16))
        self._rail.setStyleSheet(self._rail_style())
        self._rail.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._build_rail()
        self._rail.currentRowChanged.connect(self._on_rail_changed)
        body.addWidget(self._rail)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        body.addWidget(self._stack, stretch=1)

        root.addLayout(body, stretch=1)

        self._edit_card = self._build_edit_card()
        self._edit_card.setVisible(False)
        root.addWidget(self._edit_card)

        self._apply_text_styles()
        # Primera pantalla seleccionable (Primer arranque).
        for r in range(self._rail.count()):
            if self._rail.item(r).flags() & Qt.ItemFlag.ItemIsSelectable:
                self._rail.setCurrentRow(r)
                break

    def _build_rail(self):
        self._rail.clear()
        self._row_entry = {}
        for entry in _RAIL:
            if "header" in entry:
                it = QListWidgetItem(entry["header"].upper())
                it.setFlags(Qt.ItemFlag.NoItemFlags)
                f = qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
                it.setFont(f)
                it.setForeground(v3c("ink_secondary", self._modo))
                self._rail.addItem(it)
            else:
                it = QListWidgetItem(entry["label"])
                try:
                    it.setIcon(nm_icon(_ICONS.get(entry["screen"], "home"),
                                       v3c("ink_secondary", self._modo), size=15))
                except Exception:
                    pass
                self._rail.addItem(it)
                self._row_entry[self._rail.row(it)] = entry

    def _rail_style(self) -> str:
        sel_bg = qcolor_to_rgba_css(v3c("accentSoft", self._modo))
        hover_bg = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        return (
            f"QListWidget {{ background: {v3c('surface', self._modo).name()}; "
            f"color: {v3c('text', self._modo).name()}; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
            "border-radius: 12px; padding: 5px; outline: none; }}"
            "QListWidget::item { padding: 6px 7px; border-radius: 7px; margin: 1px 0; }"
            f"QListWidget::item:hover {{ background: {hover_bg}; }}"
            f"QListWidget::item:selected {{ background: {sel_bg}; "
            f"color: {v3c('text', self._modo).name()}; }}"
            + _clinical_scrollbar_qss(self._modo)
        )

    def _scroll_style(self) -> str:
        return (
            "QScrollArea { background: transparent; border: none; }"
            + _clinical_scrollbar_qss(self._modo)
        )

    def _apply_text_styles(self):
        ink2 = v3c("ink_secondary", self._modo).name()
        self._eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._hint.setStyleSheet(f"color: {ink2}; background: transparent;")

    # ── Barra de edición ────────────────────────────────────────────────────────

    def _build_edit_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("EditCard")
        card.setStyleSheet(
            f"QFrame#EditCard {{ background: {v3c('surface', self._modo).name()}; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('border', self._modo))}; "
            "border-radius: 12px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        lay.setSpacing(V3_SP["xs"])

        top = QHBoxLayout()
        self._edit_ctx = QLabel("Editar texto")
        self._edit_ctx.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._edit_ctx.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        top.addWidget(self._edit_ctx, stretch=1)
        self._edit_counter = QLabel("0/0")
        self._edit_counter.setFont(qfont_mono(10))
        self._edit_counter.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        top.addWidget(self._edit_counter, alignment=Qt.AlignmentFlag.AlignRight)
        lay.addLayout(top)

        self._edit_input = NMInput("Texto…", modo=self._modo)
        self._edit_input.textChanged.connect(self._on_edit_text_changed)
        self._edit_input.returnPressed.connect(self._apply_edit)
        lay.addWidget(self._edit_input)

        self._edit_area = NMTextArea("Texto…", modo=self._modo, min_height=54)
        self._edit_area.textChanged.connect(lambda: self._on_edit_text_changed(self._edit_area.toPlainText()))
        self._edit_area.setVisible(False)
        lay.addWidget(self._edit_area)

        btns = QHBoxLayout()
        btns.setSpacing(V3_SP["sm"])
        self._edit_reset_btn = NMButtonOutline("Restablecer este texto", modo=self._modo, size="sm")
        self._edit_reset_btn.clicked.connect(self._reset_current_text)
        btns.addWidget(self._edit_reset_btn)
        btns.addStretch(1)
        self._edit_cancel_btn = NMButtonOutline("Cancelar", modo=self._modo, size="sm")
        self._edit_cancel_btn.clicked.connect(self._close_edit)
        btns.addWidget(self._edit_cancel_btn)
        self._edit_apply_btn = NMButton("Aplicar", modo=self._modo, size="sm", width=110)
        self._edit_apply_btn.clicked.connect(self._apply_edit)
        btns.addWidget(self._edit_apply_btn)
        lay.addLayout(btns)
        return card

    # ── Navegación (cacheada) ───────────────────────────────────────────────────

    def _on_rail_changed(self, row: int):
        entry = self._row_entry.get(row)
        if entry is None:
            return
        self._close_edit()
        self._show_screen(entry["screen"], entry.get("qa", False))

    def select_screen(self, screen_id: str, qa: bool | None = None):
        """API para QA: selecciona la primera fila de ese screen (qa opcional)."""
        for row, entry in self._row_entry.items():
            if entry["screen"] == screen_id and (qa is None or entry.get("qa", False) == qa):
                self._rail.setCurrentRow(row)
                return

    def _show_screen(self, screen: str, qa: bool):
        cache_key = (screen, qa)
        if cache_key in self._screen_pane:
            self._stack.setCurrentWidget(self._screen_pane[cache_key])
            self._current_sites = [s for s in self._iter_all_sites() if s.scope in (screen, "chrome")]
            return

        try:
            self._clonedb.ensure()
            with self._clonedb.active(qa=qa):
                view = self._build_screen(screen)
        except Exception as exc:
            _log.exception("Error al construir pantalla %s (qa=%s)", screen, qa)
            view = self._error_placeholder(screen, exc)

        frame = self._wrap_in_suite_frame(view)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(self._scroll_style())
        scroll.setWidget(frame)
        self._scrolls.append(scroll)
        self._stack.addWidget(scroll)
        self._screen_pane[cache_key] = scroll

        # Registrar textos: chrome (barra de título) + la vista (scope=screen).
        self._register_texts(frame.findChild(QFrame, "SuiteTitlebar"), "chrome")
        self._register_texts(view, screen)
        self._current_sites = [s for s in self._iter_all_sites() if s.scope in (screen, "chrome")]
        self._stack.setCurrentWidget(scroll)

    def _iter_all_sites(self):
        for sites in self._sites_by_key.values():
            yield from sites

    def _build_screen(self, screen: str) -> QWidget:
        if screen == "home":
            from app.home_qt import HomeView
            from shared.visual_qa import visual_qa_enabled, module_status, qa_patient_name
            name = qa_patient_name().title() if visual_qa_enabled() else "Paciente"
            status_fn = (lambda mid="": module_status(mid)) if visual_qa_enabled() else (lambda *a, **k: "")
            return HomeView(
                modo=self._modo,
                on_module_open=lambda *_a, **_k: None,
                get_status_fn=status_fn,
                username=name,
            )
        if screen == "onboarding":
            from app.onboarding_qt import OnboardingDialog
            dlg = OnboardingDialog()
            dlg.setWindowFlags(Qt.WindowType.Widget)
            dlg.setModal(False)
            return dlg
        if screen in _MODULE_MAP:
            mod_path, cls_name = _MODULE_MAP[screen]
            module = importlib.import_module(mod_path)
            cls = getattr(module, cls_name)
            inst = cls(modo=self._modo, show_header=False)
            if hasattr(inst, "on_enter"):
                try:
                    inst.on_enter()
                except Exception:
                    _log.debug("on_enter() falló en clon %s", screen)
            return inst
        return self._error_placeholder(screen, RuntimeError("pantalla desconocida"))

    def _wrap_in_suite_frame(self, view: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SuiteFrame")
        frame.setStyleSheet(self._frame_style())
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(0)
        lay.addWidget(self._build_titlebar())
        lay.addWidget(view, stretch=1)
        self._suite_frames.append(frame)
        return frame

    def _build_titlebar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("SuiteTitlebar")
        bar.setFixedHeight(30)
        bar.setStyleSheet(
            f"QFrame#SuiteTitlebar {{ background: {v3c('surface', self._modo).name()}; "
            f"border-top-left-radius: 13px; border-top-right-radius: 13px; "
            f"border-bottom: 1px solid {qcolor_to_rgba_css(v3c('border', self._modo))}; }}"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 10, 0)
        lay.setSpacing(7)
        brand = QLabel(_BRAND_DEFAULT)
        brand.setObjectName("SuiteBrand")
        brand.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        brand.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        lay.addWidget(brand, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch(1)
        dot_css = qcolor_to_rgba_css(v3c("borderStrong", self._modo))
        for _ in range(3):
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {dot_css}; border-radius: 4px;")
            lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        return bar

    def _frame_style(self) -> str:
        return (
            f"QFrame#SuiteFrame {{ background: {v3c('bg', self._modo).name()}; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('border', self._modo))}; "
            "border-radius: 14px; }}"
        )

    def _error_placeholder(self, screen: str, exc: Exception) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["xl"])
        lbl = QLabel(f"No se pudo cargar «{screen}».\n{str(exc)[:120]}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {v3c('danger', self._modo).name()}; background: transparent;")
        lay.addWidget(lbl)
        return w

    # ── Registro de textos editables + read-only ─────────────────────────────────

    def _register_texts(self, root: QWidget, scope: str):
        if root is None:
            return
        sites = collect_texts(root, scope)
        eff = self._effective()
        registered_ids: set[int] = set()
        for site in sites:
            # No ofrecer DATOS simulados (tareas/recordatorios/etc.) como editables.
            if _is_data_text(site.default):
                continue
            self._sites_by_key.setdefault(site.key, []).append(site)
            self._default_by_key[site.key] = site.default
            registered_ids.add(id(site.widget))
            val = eff.get(site.key)
            try:
                if val is not None and val != site.default:
                    if site.kind == "text":
                        site.widget.setText(val)
                    else:
                        site.widget.setPlaceholderText(val)
                site.widget.setCursor(Qt.CursorShape.PointingHandCursor)
                site.widget.setToolTip("Clic para editar este texto global")
                site.widget.installEventFilter(self)
            except RuntimeError:
                continue

        # Read-only: cualquier control interactivo que NO sea un texto editable
        # queda inerte (sus clics se consumen → no escribe registros ni cambia
        # estados clínicos).
        try:
            controls = root.findChildren(
                (QAbstractButton, QLineEdit, QTextEdit, QPlainTextEdit, QSlider,
                 QComboBox, QAbstractSpinBox)
            )
        except RuntimeError:
            controls = []
        for c in controls:
            if id(c) in registered_ids:
                continue
            self._inert_ids.add(id(c))
            try:
                c.installEventFilter(self)
            except RuntimeError:
                continue

    def eventFilter(self, obj, event):  # noqa: N802 (Qt override)
        et = event.type()
        if et in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick,
                  QEvent.Type.MouseButtonRelease):
            key = self._key_for_widget(obj)
            if key is not None:
                if et == QEvent.Type.MouseButtonPress:
                    self._begin_edit(key)
                return True  # consumir → no dispara la acción del widget
            if id(obj) in self._inert_ids:
                return True  # control inerte → sin efecto (read-only)
        return super().eventFilter(obj, event)

    def _key_for_widget(self, widget) -> str | None:
        for key, sites in self._sites_by_key.items():
            for site in sites:
                if site.widget is widget:
                    return key
        return None

    # ── Edición de un texto ─────────────────────────────────────────────────────

    def _begin_edit(self, key: str):
        sites = self._sites_by_key.get(key) or []
        if not sites:
            return
        self._editing_key = key
        default = self._default_by_key.get(key, "")
        current = self._effective().get(key, default)
        site = sites[0]
        max_len = _compute_max_len(site.widget, default, site.kind)
        multiline = isinstance(site.widget, (QTextEdit, QPlainTextEdit)) or "\n" in default or max_len > 80

        ctx = default if len(default) <= 48 else default[:45] + "…"
        self._edit_ctx.setText(f"Editar: «{ctx}»  ·  {site.scope}")
        self._edit_max = max_len

        self._edit_input.blockSignals(True)
        self._edit_area.blockSignals(True)
        if multiline:
            self._edit_input.setVisible(False)
            self._edit_area.setVisible(True)
            self._edit_area._max_length = max_len
            self._edit_area.setPlainText(current)
            self._active_editor = self._edit_area
        else:
            self._edit_area.setVisible(False)
            self._edit_input.setVisible(True)
            self._edit_input.setMaxLength(max_len)
            self._edit_input.setText(current)
            self._active_editor = self._edit_input
        self._edit_input.blockSignals(False)
        self._edit_area.blockSignals(False)
        self._update_edit_counter(len(current))
        self._edit_card.setVisible(True)
        self._active_editor.setFocus()

    def _current_edit_text(self) -> str:
        if self._edit_area.isVisible():
            return self._edit_area.toPlainText()
        return self._edit_input.text()

    def _on_edit_text_changed(self, _txt=None):
        self._update_edit_counter(len(self._current_edit_text()))

    def _update_edit_counter(self, length: int):
        over = length > getattr(self, "_edit_max", 220)
        col = v3c("danger" if over else "ink_secondary", self._modo).name()
        self._edit_counter.setText(f"{length}/{getattr(self, '_edit_max', 0)}")
        self._edit_counter.setStyleSheet(f"color: {col}; background: transparent;")
        self._edit_apply_btn.setEnabled(not over)

    def _apply_edit(self):
        if self._editing_key is None:
            return
        key = self._editing_key
        default = self._default_by_key.get(key, "")
        text = self._current_edit_text()
        if len(text) > getattr(self, "_edit_max", 220):
            return
        if text == "" or text == default:
            if key in self._saved:
                self._pending[key] = ""
            else:
                self._pending.pop(key, None)
            effective = default
        else:
            self._pending[key] = text
            effective = text
        self._update_sites_text(key, effective)
        self._close_edit()
        NMToast.display(
            self.window(),
            "Texto actualizado · usá «Guardar cambios» para sincronizar.",
            variant="info",
        )

    def _reset_current_text(self):
        if self._editing_key is None:
            return
        key = self._editing_key
        default = self._default_by_key.get(key, "")
        if key in self._saved:
            self._pending[key] = ""
        else:
            self._pending.pop(key, None)
        self._update_sites_text(key, default)
        self._close_edit()

    def _update_sites_text(self, key: str, value: str):
        for site in self._sites_by_key.get(key, []):
            try:
                if site.kind == "text":
                    site.widget.setText(value)
                else:
                    site.widget.setPlaceholderText(value)
            except RuntimeError:
                continue

    def _close_edit(self):
        self._editing_key = None
        self._edit_card.setVisible(False)

    # ── Guardar / Restaurar ──────────────────────────────────────────────────────

    def _save_changes(self):
        if not self._pending:
            NMToast.display(self.window(), "No hay cambios pendientes.", variant="info")
            return
        if not self._sb:
            NMToast.display(self.window(), "Sin conexión: no se puede guardar.", variant="error")
            return
        try:
            for key, value in list(self._pending.items()):
                default = self._default_by_key.get(key, "")
                if value == "" or value == default:
                    self._delete_value(key)
                    self._saved.pop(key, None)
                else:
                    self._upsert_value(key, value)
                    self._saved[key] = value
            self._pending.clear()
            NMToast.display(
                self.window(),
                "Cambios guardados · se sincronizan con la Suite de todos los pacientes.",
                variant="success",
            )
        except Exception as exc:
            _log.exception("Error al guardar textos globales")
            NMToast.display(self.window(), f"Error al guardar: {str(exc)[:50]}", variant="error")

    def _ask_restore_all(self):
        nm_confirm(
            self,
            "Restaurar textos por defecto",
            "Se quitarán TODOS los textos personalizados y la Suite de todos los "
            "pacientes volverá a los textos originales de NeuroMood.\n\n"
            "Los avances, registros, tareas, actividades y recordatorios "
            "individuales no se modifican.",
            self._restore_all,
            modo=self._modo,
        )

    def _restore_all(self):
        try:
            if self._sb:
                self._sb.table("hub_config").delete().eq("scope", "global").like(
                    "key", PREFIX + "%"
                ).execute()
            self._saved.clear()
            self._pending.clear()
            self._close_edit()
            for key, default in self._default_by_key.items():
                self._update_sites_text(key, default)
            NMToast.display(
                self.window(),
                "Textos restaurados a los valores por defecto de NeuroMood.",
                variant="success",
            )
        except Exception as exc:
            _log.exception("Error al restaurar textos globales")
            NMToast.display(self.window(), f"Error: {str(exc)[:50]}", variant="error")

    def _upsert_value(self, key: str, value: str):
        self._sb.table("hub_config").upsert(
            {"scope": "global", "key": key, "value": json.dumps(value)},
            on_conflict="scope,key",
        ).execute()

    def _delete_value(self, key: str):
        self._sb.table("hub_config").delete().eq("scope", "global").eq("key", key).execute()

    # ── QA ──────────────────────────────────────────────────────────────────────

    def _qa_begin_first_edit(self):
        # Preferir un texto que no sea de la barra de título para evidencia clara.
        for s in self._current_sites:
            if s.scope != "chrome":
                self._begin_edit(s.key)
                return
        if self._current_sites:
            self._begin_edit(self._current_sites[0].key)

    # ── Tema ──────────────────────────────────────────────────────────────────

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_text_styles()
        self._build_rail()
        self._rail.setStyleSheet(self._rail_style())
        for sc in self._scrolls:
            try:
                sc.setStyleSheet(self._scroll_style())
            except RuntimeError:
                pass
        for fr in self._suite_frames:
            try:
                fr.setStyleSheet(self._frame_style())
                tb = fr.findChild(QFrame, "SuiteTitlebar")
                if tb is not None:
                    tb.setStyleSheet(
                        f"QFrame#SuiteTitlebar {{ background: {v3c('surface', self._modo).name()}; "
                        f"border-top-left-radius: 13px; border-top-right-radius: 13px; "
                        f"border-bottom: 1px solid {qcolor_to_rgba_css(v3c('border', self._modo))}; }}"
                    )
            except RuntimeError:
                pass
        # Las vistas embebidas se re-tematizan vía ThemeManager.theme_changed.
