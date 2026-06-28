"""
hub/main_qt.py — NeuroMood Hub (PyQt6 entry point)

Layout:
    QMainWindow
    └── NMFadeWidget
        ├── PacientesView
        └── DetallePacienteView (se carga al seleccionar paciente)
"""

import sys
import os
import threading
import logging

_log = logging.getLogger("NeuroMoodHub")

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QDialog,
)
from PyQt6.QtCore import QEvent, QPoint, QRect, Qt, QTimer, QRectF, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon, QPainter, QBrush, QLinearGradient
from PyQt6 import sip

from shared.theme_qt import (
    v3c,
    colors,
    norm_modo,
    qfont,
    app_palette,
    stylesheet_base,
    stylesheet_scrollarea,
    obtener_ruta_recurso,
    aplicar_captionbar_qt,
    ThemeAwareWidgetMixin,
    apply_hub_density,
    HUB_DENSITY_OBJECT_NAME,
    V3_SP,
)
from shared.adaptive_layout_qt import (
    configure_adaptive_window,
    install_transient_qt_window_guard,
    window_edge_radius,
)
from shared.qt_thread import init_gui_invoker
from shared.components import (
    ThemeManager,
    NMFadeWidget,
    NMButton,
    NMButtonOutline,
    NMCard,
    NMToast,
    NMPatientRowPremium,
    NMEmptyState,
    NMWindowChrome,
    NMBadge,
)
from shared.components.patient import (
    _NM_PATIENT_RING_COL_W,
    _NM_PATIENT_ROW_HEIGHT,
    _NM_PATIENT_TREND_COL_W,
    _NM_PATIENT_UNLINK_SIZE,
)
from shared.visual_qa import visual_qa_enabled, hub_patients

_sb_create = None

from shared.config import supabase_url, supabase_key, supabase_hub_key
import pathlib as _pathlib


# ── Hub AppData helpers ───────────────────────────────────────────────────────

def _hub_appdata_dir() -> _pathlib.Path:
    """Devuelve %APPDATA%/NeuroMoodHub (crea el directorio si no existe)."""
    base = _pathlib.Path(os.environ.get("APPDATA", _pathlib.Path.home() / "AppData" / "Roaming"))
    d = base / "NeuroMoodHub"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _hub_env_path() -> _pathlib.Path:
    return _hub_appdata_dir() / ".env"


def _ensure_hub_env_base() -> None:
    """Garantiza que %APPDATA%/NeuroMoodHub/.env tenga credenciales Supabase.

    Fallback de autogestión: si el instalador no desplegó el .env (versión vieja
    del installer, o primer arranque antes de reinstalar), lo crea leyendo las
    credenciales que shared.config ya encontró (AppData de Suite o raíz en dev).
    Nunca sobreescribe claves existentes. Si existe una clave operativa del Hub,
    la guarda como SUPABASE_HUB_KEY para no contaminar la clave anon de la Suite.
    """
    env_path = _hub_env_path()
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            existing[k.strip()] = v.strip()

    url = supabase_url()
    key = supabase_key()
    hub_key = supabase_hub_key()
    changed = False
    if url and "SUPABASE_URL" not in existing:
        existing["SUPABASE_URL"] = url
        changed = True
    if key and "SUPABASE_KEY" not in existing:
        existing["SUPABASE_KEY"] = key
        changed = True
    if (
        hub_key
        and hub_key != key
        and "SUPABASE_HUB_KEY" not in existing
        and "SUPABASE_SERVICE_ROLE_KEY" not in existing
    ):
        existing["SUPABASE_HUB_KEY"] = hub_key
        changed = True

    if changed or not env_path.exists():
        lines = [f"{k}={v}" for k, v in existing.items() if v]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            from shared import config as _cfg
            _cfg._cache.clear()
        except Exception:
            pass




# ── QSettings · persistencia del tema (handoff Mayo 2026) ────────────────────


def _saved_theme(default: str = "dark_hybrid") -> str:
    """Devuelve el modo guardado para Hub o `default`."""
    try:
        raw = QSettings("NeuroMood", "Hub").value("ui/theme", default, type=str)
    except Exception:
        raw = default
    return norm_modo(raw or default)


def _persist_theme(modo: str) -> None:
    """Guarda el modo del Hub (best-effort)."""
    try:
        QSettings("NeuroMood", "Hub").setValue("ui/theme", norm_modo(modo))
    except Exception:
        pass


def _disconnect_theme_tree(widget: QWidget):
    """Evita callbacks de theme_changed hacia widgets pendientes de deleteLater()."""
    tm = ThemeManager.instance()
    for obj in [widget, *widget.findChildren(QWidget)]:
        for slot_name in ("_apply_theme", "apply_theme", "_on_theme"):
            slot = getattr(obj, slot_name, None)
            if slot is None:
                continue
            try:
                tm.theme_changed.disconnect(slot)
            except (RuntimeError, TypeError):
                pass


def _apply_theme_tree(widget: QWidget, modo: str):
    """Aplica tema solo a widgets vivos, sin usar el signal global."""
    for obj in [widget, *widget.findChildren(QWidget)]:
        if sip.isdeleted(obj):
            continue
        for slot_name in ("_apply_theme", "apply_theme", "_on_theme"):
            slot = getattr(obj, slot_name, None)
            if slot is None:
                continue
            try:
                slot(modo)
            except Exception:
                pass
            break


def _get_sb():
    """Crea y devuelve un cliente Supabase para el Hub.

    Los profesionales acceden libremente — no se requiere sesión ni token.
    El cliente usa la clave configurada en %APPDATA%/NeuroMoodHub/.env.
    """
    global _sb_create
    if _sb_create is None:
        try:
            from supabase import create_client

            _sb_create = create_client
        except ImportError:
            return None, "modulo supabase no instalado"
    url, key = supabase_url(), supabase_hub_key()
    if not url or not key:
        return None, "credenciales no configuradas (.env)"
    try:
        client = _sb_create(url, key)
    except Exception as e:
        return None, str(e)[:60]
    return client, None


# ── Desvinculación local (fallback) ───────────────────────────────────────────
# La X "Quitar del Hub" escribe patients.unlinked=true en Supabase, pero si esa
# columna todavía no existe (db/patients_email_unlink.sql sin correr) el update
# fallaba y la fila NUNCA desaparecía → "la X no funciona". Guardamos además los
# patient_id quitados en la config local del Hub para ocultarlos siempre, exista
# o no la columna remota. (El intento remoto se mantiene best-effort.)
_HUB_UNLINKED_CFG_KEY = "hub_unlinked_patients"


def _load_local_unlinked() -> set[str]:
    try:
        import json
        from shared.db import leer_config

        raw = leer_config(_HUB_UNLINKED_CFG_KEY, "")
        return set(json.loads(raw)) if raw else set()
    except Exception:
        return set()


def _add_local_unlinked(pid: str) -> None:
    if not pid:
        return
    try:
        import json
        from shared.db import guardar_config

        s = _load_local_unlinked()
        s.add(pid)
        guardar_config(_HUB_UNLINKED_CFG_KEY, json.dumps(sorted(s)))
    except Exception:
        _log.debug("No se pudo persistir el unlink local de %s", pid)


# ── PacientesView ─────────────────────────────────────────────────────────────


class PacientesView(QWidget):
    """Hub > Pacientes Dashboard v3.

    Layout:
      Header: eyebrow "PACIENTES" + título "Pacientes (N)"
      Search NMCard: NMInput + 4 filter pills (Todos/Activos/Sin registros/
        Sin sincronización reciente)
      NMCard tabla: NMPatientRow × N con avatar + nombre + adherencia ring

    Filtros — criterios neutrales descriptivos (decisión 7 — sin semáforos
    clínicos sobre uso de la app):
      - Todos: sin filtro.
      - Activos: pacientes no marcados como inactivos/desvinculados.
      - Sin registros: pacientes con evidencia explícita de cero registros.
      - Sin sincronización reciente: `last_sync_date` de hace más de 7 días
        (o nunca sincronizado). Reemplaza al antiguo filtro interpretativo
        basado en umbral de adherencia (prompt F0.1.B).
    """

    def __init__(
        self,
        modo: str,
        pacientes: list,
        on_select,
        on_refresh,
        on_global_texts=None,
        sb=None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._pacientes = pacientes
        self._on_select = on_select
        self._on_refresh = on_refresh
        self._on_global_texts = on_global_texts
        self._sb = sb
        self._rows_limit: int = 40
        self._patient_row_widgets: list[QWidget] = []
        self._setup()

    def _setup(self):
        from shared.theme_qt import v3c, V3_SP, V3_RD
        from shared.theme import TYPOGRAPHY as _TY

        self._v3c = v3c
        self._sp = V3_SP
        self._rd = V3_RD
        self._ty = _TY

        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        # Fit-first 960x600: márgenes compactos para que las 5 filas de pacientes
        # quepan completas en el primer viewport sin fila cortada al pie. El
        # alto se redistribuye al table_card (stretch=1) → más filas visibles
        # sin fila cortada al pie.
        layout.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], 0)
        layout.setSpacing(V3_SP["xs"])

        # (Antes había un NMPageHeader plegado a la titlebar que se ocultaba
        # pero seguía ocupando 640x480 en el layout → vaciío superior en
        # Pacientes. Eliminado: la titlebar ya muestra "NeuroMood Hub /
        # Pacientes" y la barra "Lista activa" del roster hace de header.)

        # 2. Tabla NMCard con NMPatientRow × N
        table_card = NMCard(modo=self._modo, clickable=False, glow=False)
        tc_lay = QVBoxLayout(table_card)
        tc_lay.setContentsMargins(V3_SP["sm"], V3_SP["xs"], V3_SP["sm"], V3_SP["xs"])
        tc_lay.setSpacing(2)
        self._table_card = table_card

        roster_meta = QHBoxLayout()
        roster_meta.setContentsMargins(2, 0, 2, 0)
        roster_meta.setSpacing(V3_SP["sm"])
        self._table_title = QLabel("Lista activa")
        self._table_title.setFont(qfont("size_h1", weight=_TY["weight_semibold"]))
        self._table_title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        roster_meta.addWidget(self._table_title)
        # Mockup l.1388: class='badge brand' → tone='brand'. Mapea al mismo
        # render que 'info' (ambos → _BADGE_TONE_TO_KEY["primary"]), pero
        # el spec del mockup declara explícitamente `brand` (no el alias
        # interno `info`).
        self._results_badge = NMBadge("0 pacientes", tone="brand", modo=self._modo)
        roster_meta.addWidget(self._results_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._table_hint = QLabel("Mail, ánimo de 7 días y uso por paciente")
        self._table_hint.setFont(qfont("size_caption_xs"))
        self._table_hint.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        roster_meta.addWidget(self._table_hint, alignment=Qt.AlignmentFlag.AlignVCenter)
        if callable(self._on_global_texts):
            self._texts_btn = NMButtonOutline(
                "Textos globales",
                size="sm",
                modo=self._modo,
                icon_name="list",  # mockup: outline con ≡
            )
            self._texts_btn.clicked.connect(self._on_global_texts)
            roster_meta.addStretch()
            roster_meta.addWidget(self._texts_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        else:
            roster_meta.addStretch()
        tc_lay.addLayout(roster_meta)

        self._table_header = table_header = QWidget()
        # Sin border-bottom: un border-bottom sin selector se PROPAGABA a cada
        # QLabel hijo dibujando un subrayado bajo cada encabezado (el "subrayado
        # doble" que reaparecía al cambiar de tema). La separación con la primera
        # fila se da con margen/espaciado, no con una línea dura (ADN §7).
        table_header.setStyleSheet("background: transparent;")
        th_lay = QHBoxLayout(table_header)
        th_lay.setContentsMargins(94, 0, 14, V3_SP["md"])
        # Spacing 12 = al de NMPatientRowPremium: con sm(6) las columnas Mail /
        # Ánimo 7d / Uso no caían sobre sus datos (desalineadas).
        th_lay.setSpacing(12)
        # Sin jerga ni abreviaturas técnicas (informe owner v1.0): la columna
        # central muestra email/vínculo (no un "diagnóstico"), y "TEND./ADHER."
        # no le dicen nada a un profesional no técnico.
        for text, stretch in (
            ("Paciente", 3),
            ("Mail", 2),
            ("Ánimo 7d", 0),  # Sparkline area (60px)
            ("Uso", 0),  # Ring area
        ):
            lbl = QLabel(text.upper())
            lbl.setFont(qfont("size_caption_xs", weight=_TY["weight_semibold"]))
            is_metric = stretch == 0
            lbl.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; "
                "background: transparent;"
            )
            if is_metric:
                # Ancho coherente con las columnas de la fila (sparkline / ring),
                # texto centrado sobre su columna.
                lbl.setFixedWidth(
                    _NM_PATIENT_TREND_COL_W if "Ánimo" in text else _NM_PATIENT_RING_COL_W
                )
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                th_lay.addWidget(lbl)
            else:
                th_lay.addWidget(lbl, stretch=stretch)
        # Columna de la X de desvincular, sin título.
        th_lay.addSpacing(_NM_PATIENT_UNLINK_SIZE)
        tc_lay.addWidget(table_header)

        self._rows_scroll = QScrollArea()
        self._rows_scroll.setWidgetResizable(True)
        self._rows_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._rows_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._rows_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._rows_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        self._rows_scroll.verticalScrollBar().valueChanged.connect(
            lambda _value: self._queue_row_control_visibility_refresh()
        )
        self._rows_scroll.viewport().installEventFilter(self)
        self._rows_w = QWidget()
        self._rows_w.setStyleSheet("background: transparent;")
        self._table_lay = QVBoxLayout(self._rows_w)
        self._table_lay.setContentsMargins(0, 0, 0, V3_SP["xs"])
        self._table_lay.setSpacing(2)
        self._table_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._rows_scroll.setWidget(self._rows_w)
        tc_lay.addWidget(self._rows_scroll)
        layout.addWidget(table_card, 0, Qt.AlignmentFlag.AlignTop)
        layout.addStretch(1)

        self._render_rows()

    def _render_rows(self):
        # Limpiar contenido previo
        while self._table_lay.count():
            item = self._table_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._patient_row_widgets = []

        rows = list(self._pacientes)
        self._update_roster_meta(rows)
        self._sync_table_card_height(rows)

        if not rows:
            self._table_header.hide()
            empty = NMEmptyState(
                "users",
                "Sin pacientes vinculados",
                "Cuando un paciente complete el alta desde la Suite, aparecerá acá automáticamente.",
                parent=self._table_card,
            )
            self._table_lay.addWidget(empty)
            self._queue_row_control_visibility_refresh()
            return

        # Hay filas: el header de columnas vuelve a tener sentido.
        self._table_header.show()
        rows_pendientes = max(0, len(rows) - self._rows_limit)
        rows = rows[: self._rows_limit]
        for p in rows:
            nombre = p.get("patient_name") or "-"
            pid = p.get("patient_id", "")
            email = (p.get("email") or "").strip()
            last_session = p.get("last_session") or ("hace 2 días" if visual_qa_enabled() else "")
            # Sin IDs técnicos como contenido principal (informe owner v1.0):
            # la fila describe el vínculo; el ID completo vive en el tooltip.
            # El EMAIL declarado en el alta es el dato principal de la columna
            # Seguimiento: distingue pacientes homónimos (caso real: dos
            # "Juan Cruz" con cuentas distintas).
            _sync_ok = bool(p.get("last_sync_date"))
            if email:
                subtitle = email
            elif visual_qa_enabled():
                subtitle = "Programa activo - seguimiento semanal"
            else:
                subtitle = (
                    "Paciente vinculado · sincronizado"
                    if _sync_ok
                    else "Paciente vinculado · sin sincronizar aún"
                )
            last_activity = f"Último registro: {last_session}" if last_session else "Sin registros"
            next_session = p.get("next_session") or (
                "Próxima: vie 16:00" if visual_qa_enabled() else ""
            )
            sync_state = "ok" if p.get("last_sync_date") or visual_qa_enabled() else "stale"
            _qa_mood = [6, 6, 7, 7, 7, 8, 8] if visual_qa_enabled() else None
            mood_data = p.get("mood_data_7d") or _qa_mood
            pct_val = p.get("adherence")
            try:
                pct = float(pct_val) if pct_val is not None else None
            except (TypeError, ValueError):
                pct = None
            row = NMPatientRowPremium(
                nombre,
                patient_id=pid,
                subtitle=subtitle,
                last_activity=last_activity,
                next_session=next_session,
                tags=["Hub", "Activo"] if visual_qa_enabled() else ["Hub"],
                sync_state=sync_state,
                pct=pct,
                mood_data=mood_data,
                selected=False,
                modo=self._modo,
                on_unlink=lambda _checked=False, _pid=pid, _n=nombre, _e=email: self._confirm_unlink(
                    _pid, _n, _e
                ),
            )
            _tip = f"ID del paciente: {pid}"
            if email:
                _tip = f"{email}\n{_tip}"
            row.setToolTip(_tip)
            row.clicked.connect(lambda _pid=pid, _n=nombre: self._on_select(_pid, _n))
            self._table_lay.addWidget(row)
            self._patient_row_widgets.append(row)

        if rows_pendientes:
            btn_more = NMButton(
                f"Mostrar más ({rows_pendientes} restantes)",
                variant="ghost",
                size="sm",
                modo=self._modo,
                width=220,
            )

            def _load_more():
                self._rows_limit += 40
                self._render_rows()

            btn_more.clicked.connect(_load_more)
            _more_wrap = QWidget()
            _more_wrap.setStyleSheet("background: transparent;")
            _ml = QHBoxLayout(_more_wrap)
            _ml.setContentsMargins(0, V3_SP["xs"], 0, V3_SP["xs"])
            _ml.addStretch()
            _ml.addWidget(btn_more)
            _ml.addStretch()
            self._table_lay.addWidget(_more_wrap)
        self._queue_row_control_visibility_refresh()
        return

    def eventFilter(self, obj, event) -> bool:
        if (
            hasattr(self, "_rows_scroll")
            and obj is self._rows_scroll.viewport()
            and event.type()
            in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Move)
        ):
            self._queue_row_control_visibility_refresh()
        return super().eventFilter(obj, event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._queue_row_control_visibility_refresh()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._queue_row_control_visibility_refresh()

    def _queue_row_control_visibility_refresh(self) -> None:
        if hasattr(self, "_rows_scroll"):
            QTimer.singleShot(0, self._refresh_row_control_visibility)

    def _refresh_row_control_visibility(self) -> None:
        if not hasattr(self, "_rows_scroll") or not hasattr(self, "_rows_w"):
            return
        viewport = self._rows_scroll.viewport()
        view_rect = QRect(viewport.rect())
        view_rect.moveTopLeft(self._rows_w.mapFrom(viewport, QPoint(0, 0)))
        top = view_rect.top()
        bottom = view_rect.bottom()
        live_rows: list[QWidget] = []
        for row in self._patient_row_widgets:
            if sip.isdeleted(row):
                continue
            live_rows.append(row)
            row_rect = row.geometry()
            row_fully_inside = row_rect.top() >= top and row_rect.bottom() <= bottom
            setter = getattr(row, "set_action_controls_visible", None)
            if callable(setter):
                setter(row.isVisible() and row_fully_inside)
        self._patient_row_widgets = live_rows

    def _confirm_unlink(self, pid: str, nombre: str, email: str = ""):
        """Confirma y desvincula al paciente del Hub (patients.unlinked=true).

        Decisión owner v1.0: los datos NO se borran (la fila queda oculta);
        la Suite del paciente detecta el flag y deja de sincronizar (queda
        offline-only). Si el paciente retoma, crea una cuenta nueva.
        """
        from shared.components import NMButtonOutline, NMDialogScaffold

        dialog = QDialog(self.window())
        dialog.setWindowTitle("Quitar paciente")
        dialog.setModal(True)
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        _bc = v3c("borderStrong" if is_dark else "border", self._modo)
        dialog.setStyleSheet(
            f"QDialog {{ background: {card_bg}; border: 1px solid "
            f"rgba({_bc.red()},{_bc.green()},{_bc.blue()},{_bc.alpha()}); "
            f"border-radius: {window_edge_radius()}px; }}"
        )
        dialog.setFixedWidth(420)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        scaffold = NMDialogScaffold(
            title=f"Quitar a {nombre} del Hub",
            eyebrow="Pacientes",
            modo=self._modo,
            parent=dialog,
        )
        root.addWidget(scaffold)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["lg"])
        bl.setSpacing(V3_SP["md"])

        quien = f"{nombre} ({email})" if email else nombre
        msg = QLabel(
            f"{quien} va a dejar de aparecer en tu lista de pacientes y su "
            "aplicación dejará de sincronizar con el Hub.\n\n"
            "Sus registros no se borran. El paciente puede seguir usando la "
            "Suite sin conexión; si retoma el tratamiento, deberá crear una "
            "cuenta nueva."
        )
        msg.setWordWrap(True)
        msg.setFont(qfont("size_small"))
        msg.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        bl.addWidget(msg)

        btns = QHBoxLayout()
        btns.setSpacing(V3_SP["sm"])
        btns.addStretch()
        btn_cancel = NMButtonOutline("Cancelar", modo=self._modo)
        btn_cancel.setFixedSize(100, 34)
        btn_cancel.clicked.connect(dialog.reject)
        btns.addWidget(btn_cancel)
        btn_ok = NMButton("Quitar del Hub", modo=self._modo, size="sm", width=130)
        btn_ok.clicked.connect(dialog.accept)
        btns.addWidget(btn_ok)
        bl.addLayout(btns)

        scaffold.set_body(body)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if visual_qa_enabled():
            NMToast.display(self.window(), f"{nombre} quitado del Hub", variant="success")
            return

        # 1) Ocultar SIEMPRE de forma local y de inmediato: así la fila
        #    desaparece exista o no la columna remota patients.unlinked y haya o
        #    no conexión (antes, sin la columna, la X no hacía nada visible).
        _add_local_unlinked(pid)
        self._pacientes = [
            p for p in self._pacientes if (p.get("patient_id") or "") != pid
        ]
        self._render_rows()

        # 2) Best-effort en la nube: si la columna existe, además marca el flag
        #    para que la Suite del paciente deje de sincronizar. Si no existe o
        #    no hay conexión, el hide local ya alcanzó para el Hub.
        if self._sb:
            try:
                self._sb.table("patients").update({"unlinked": True}).eq(
                    "patient_id", pid
                ).execute()
            except Exception:
                _log.debug("unlink remoto omitido (columna ausente o sin conexión)")

        NMToast.display(self.window(), f"{nombre} quitado del Hub", variant="success")
        if callable(self._on_refresh):
            self._on_refresh()

    def _update_roster_meta(self, rows: list[dict]) -> None:
        visible = len(rows)
        suffix = "s" if visible != 1 else ""
        self._results_badge.setText(f"{visible} paciente{suffix}")
        self._table_hint.setText("Mail, ánimo de 7 días y uso por paciente")

    def _sync_table_card_height(self, rows: list[dict]) -> None:
        if not hasattr(self, "_table_card"):
            return
        if not rows:
            self._table_card.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
            )
            self._table_card.setMinimumHeight(520)
            self._table_card.setMaximumHeight(520)
            return
        visible = min(len(rows), self._rows_limit)
        # Overhead real: roster_meta ~34 + col-header ~26 + tc_margins 8 + spacing 4
        # + table_lay_bottom 4 + row_gaps (n-1)*2 = 76 + 2*(n-1) ~80-90. Buffer 20.
        target_h = min(520, max(252, 108 + visible * _NM_PATIENT_ROW_HEIGHT))
        self._table_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        self._table_card.setMinimumHeight(target_h)
        self._table_card.setMaximumHeight(target_h)
        # Scrollbar solo cuando las filas superan la capacidad del card máximo.
        max_rows_no_scroll = (520 - 108) // _NM_PATIENT_ROW_HEIGHT  # 5 rows
        scroll_policy = (
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            if visible <= max_rows_no_scroll
            else Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._rows_scroll.setVerticalScrollBarPolicy(scroll_policy)

    def _patient_tags(self, p: dict) -> list[str]:
        tags = []
        if p.get("last_mood") is not None:
            tags.append(f"Ánimo {p.get('last_mood')}/10")
        if p.get("last_session"):
            tags.append("En seguimiento")
        if not p.get("last_sync_date"):
            tags.append("Sync pendiente")
        return tags or ["Sin datos recientes"]

    def _last_activity_label(self, p: dict) -> str:
        if visual_qa_enabled():
            return f"Última actividad: {p.get('last_session', 'hace 2 dias')}"
        raw = p.get("last_sync_date") or p.get("last_session")
        return f"Última actividad: {raw}" if raw else "Última actividad: sin registros"

    def _next_session_label(self, p: dict) -> str:
        raw = p.get("next_session")
        return f"Próxima: {raw}" if raw else "Próxima: sin agendar"

    def _apply_theme(self, modo: str):
        from shared.theme_qt import v3c, stylesheet_scrollarea
        self._modo = norm_modo(modo)
        if hasattr(self, "_table_title"):
            self._table_title.setStyleSheet(
                f"color: {v3c('text', self._modo).name()}; background: transparent;"
            )
        if hasattr(self, "_table_hint"):
            self._table_hint.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
        if hasattr(self, "_table_header"):
            # Sin border-bottom (ver _setup): evitar el subrayado doble que
            # reaparecía al togglear el tema. Solo fondo transparente.
            self._table_header.setStyleSheet("background: transparent;")
            for child in self._table_header.findChildren(QLabel):
                child.setStyleSheet(
                    f"color: {v3c('ink_secondary', self._modo).name()}; "
                    "background: transparent;"
                )
        if hasattr(self, "_rows_scroll"):
            self._rows_scroll.setStyleSheet(stylesheet_scrollarea(self._modo))



class _ShellWidget(QWidget):
    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = modo

    def set_shell_modo(self, modo: str):
        self._modo = modo
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        rect = QRectF(self.rect())
        is_dark = "dark" in norm_modo(self._modo)
        from shared.theme_qt import v3c

        # Hub background: professional, calm, structured (no blobs)
        # Deep navy linear gradient in dark mode, clean warm ivory/stone in light mode
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectMode)
        if is_dark:
            bg_top = v3c("bgAlt", self._modo)
            bg_bot = v3c("bg", self._modo)
        else:
            # M3 F0 (B4): light invierte la dirección (bg→bgAlt) como el Suite
            # (paint_shell_background). Antes usaba bgAlt→bg igual que dark = bug.
            bg_top = v3c("bg", self._modo)
            bg_bot = v3c("bgAlt", self._modo)
        grad.setColorAt(0.0, bg_top)
        grad.setColorAt(1.0, bg_bot)
        p.fillRect(rect, QBrush(grad))
        p.end()


class NeuroMoodHub(ThemeAwareWidgetMixin, QMainWindow):
    _patients_loaded_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._patients_loaded_signal.connect(self._on_pacientes_loaded)
        # Restaurar tema persistido (handoff Mayo 2026 — QSettings).
        self._modo = _saved_theme("dark_hybrid")
        self._sb = None
        self._pacientes: list = []
        self._paciente_id: str | None = None
        self._paciente_nombre: str = ""
        qa_start_view = os.environ.get("NM_VISUAL_QA_HUB_VIEW", "").strip().lower()
        # Pantalla inicial = Inicio (decisión owner v1.0: "Dashboard debería
        # llamarse Inicio si funciona como pantalla inicial").
        self._current_view = (
            qa_start_view
            if visual_qa_enabled()
            and qa_start_view in {"pacientes"}
            else "pacientes"
        )

        ThemeManager.instance().switch_mode(self._modo)

        # ── Ventana frameless (handoff WindowChrome) ───────────────────────────
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle("NeuroMood Hub")
        # Handoff §3 (Hub density): objectName scoped permite que el QSS
        # aditivo de apply_hub_density() sólo afecte a este QMainWindow.
        self.setObjectName(HUB_DENSITY_OBJECT_NAME)
        self._center()
        self._apply_icon()
        self._apply_initial_style()
        self._build_ui()
        # Aplicar densidad reducida del Hub (botones 36 px / inputs 32 px).
        # Helper en shared/theme_qt.py · QSS scoped a #HubMain · no toca
        # QApplication global ni paleta ni tokens.
        apply_hub_density(self)

        # ── Sombra DWM (frameless necesita restaurar sombra nativa) ───────────
        QTimer.singleShot(
            120,
            lambda: self._apply_dwm_shadow() if not sip.isdeleted(self) else None,
        )
        QTimer.singleShot(350, self._init_connection)
        self._connect_theme()

    # ── Ventana ───────────────────────────────────────────────────────────────

    def _center(self):
        configure_adaptive_window(self)

    def _apply_icon(self):
        try:
            from shared.assets import obtener_ruta_asset, APP_ICON

            ico = obtener_ruta_asset(APP_ICON)
        except ImportError:
            ico = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

    def _apply_initial_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    def _apply_style(self):
        QApplication.instance().setPalette(app_palette(self._modo))
        QApplication.instance().setStyleSheet(stylesheet_base(self._modo))

    # ── Build ─────────────────────────────────────────────────────────────────

    # Título de cada vista del Hub plegado a la titlebar (en vez de un
    # NMPageHeader grande por vista). El brand "NeuroMood Hub" queda como
    # prefijo y el subtítulo refleja la sección activa: "NeuroMood Hub / Pacientes".
    _VIEW_TITLES = {
        "pacientes": "Pacientes",
        "textos_globales": "Textos globales de Suite",
    }

    def _view_title(self, view_id: str) -> str:
        return self._VIEW_TITLES.get(view_id, "")

    def _build_ui(self):
        central = _ShellWidget(modo=self._modo)
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── Chrome Hub: titlebar canónico del mockup. ────────────────────────
        self._chrome = NMWindowChrome(
            title="NeuroMood Hub",
            subtitle=self._view_title(self._current_view),
            modo=self._modo,
            show_theme_toggle=True,
            parent=central,
        )
        outer_layout.addWidget(self._chrome)

        # ── Área de contenido ─────────────────────────────────────────────────
        # Layout vertical único: chrome + stack. Antes había un QWidget
        # intermedio vacío (`right`) que se llevaba el 50% del alto del
        # content area (Qt divide a partes iguales cuando no hay stretch)
        # y dejaba un vacío superior compartido entre Pacientes y Detalle de
        # ~150-200 px. Stack directo sobre el layout del content con stretch=1
        # → el contenido empieza debajo de la titlebar y el alto recuperado
        # se redistribuye a Pacientes (más filas visibles) y Plan Terapéutico
        # (más alto para el form + lista).
        content = QWidget(central)
        content.setObjectName("NMHubShellContent")
        content.setStyleSheet(self._shell_content_qss(self._modo))
        self._content_widget = content
        outer_layout.addWidget(content, 1)
        rl = QVBoxLayout(content)
        # Sin margen derecho/inferior: el content widget pinta `surface`
        # (#191F2E) y un margen asimétrico (0,0,12,8) dejaba ese surface al
        # descubierto SOLO a la derecha (12px) y abajo (8px) — la vista oscura
        # no llegaba al borde —, produciendo el "marco azul" der/inf que NO está
        # en el mockup (.window: borde uniforme). El aire lateral ya lo aportan
        # los márgenes `lg` simétricos de cada vista; el stack debe llenar el
        # content de borde a borde para no exponer surface.
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self._chrome.theme_toggle.connect(self._toggle_theme)

        # Label de estado oculto en Hub para evitar ruido en header.
        # Parented a self y siempre oculto: es state-holder (la representación
        # visible real de conexión es _sync_orb). Antes se creaba sin parent y
        # _on_nav/_back_to_dashboard le hacían .show() → se volvía ventana
        # top-level fantasma (82x16 en 0,0) que NO cerraba con el Hub (BL-04).
        # (_lbl_ia_status eliminado junto con la vista global de IA.)
        self._lbl_status = QLabel("", self)
        self._lbl_status.hide()

        self._stack = NMFadeWidget(content)
        rl.addWidget(self._stack, 1)

        # Vistas iniciales
        self._refresh_all_views()

    def _refresh_all_views(self, force_recreate: bool = False):
        """Recrea o actualiza todas las vistas con los datos actuales."""
        if not hasattr(self, "_views_cache"):
            self._views_cache = {}

        if force_recreate:
            while self._stack.count():
                w = self._stack.widget(0)
                self._stack.removeWidget(w)
                _disconnect_theme_tree(w)
                w.deleteLater()
            self._views_cache.clear()

        # Pacientes
        if "pacientes" not in self._views_cache or sip.isdeleted(self._views_cache["pacientes"]):
            self._view_pacientes = PacientesView(
                self._modo,
                self._pacientes,
                on_select=self._select_patient,
                on_refresh=self._cargar_pacientes,
                on_global_texts=self._open_global_texts,
                sb=self._sb,
                parent=self._stack,
            )
            self._views_cache["pacientes"] = self._view_pacientes
            self._stack.addWidget(self._view_pacientes)
        else:
            self._view_pacientes._pacientes = self._pacientes
            if hasattr(self._view_pacientes, "_render_rows"):
                self._view_pacientes._render_rows()

        # ── TextosGlobalesSuiteView se construye LAZY ────────────────────────
        # Auditoría performance: construir esta vista al abrir el Hub costaba
        # ~454ms (158 _TextEntryRow × ~3ms c/u + apply_theme + apply_filters).
        # Es una pantalla de configuración que el profesional abre bajo demanda,
        # no en cada arranque. Se construye en `_ensure_textos_globales_view()`
        # la primera vez que se navega a ella (ver `_open_global_texts`).
        # El cache sigue siendo la fuente de verdad: si la vista ya existe y
        # está viva, se le actualiza el cliente Supabase (comportamiento
        # idéntico al eager previo).
        tg = self._views_cache.get("textos_globales")
        if tg is not None and not sip.isdeleted(tg) and hasattr(tg, "set_supabase_client"):
            tg.set_supabase_client(self._sb)

        # Si el profesional estaba dentro de una ficha cuando llegó la carga
        # asíncrona de pacientes, NO patearlo a Inicio: el force_recreate
        # destruyó la DetallePacienteView → reabrirla con los datos frescos.
        # (Bug real: abrir un paciente con _cargar_pacientes en vuelo
        # devolvía al Dashboard al completarse el fetch.)
        if self._current_view == "detalle" and self._paciente_id:
            self._select_patient(self._paciente_id, self._paciente_nombre)
            return

        views = self._nav_views()
        target = views.get(self._current_view, self._view_pacientes)
        self._stack.setCurrentWidget(target)

    def _ensure_textos_globales_view(self):
        """Construye `TextosGlobalesSuiteView` on-demand (lazy load).

        Antes `_refresh_all_views` la construía al abrir el Hub, costando
        ~454ms en mediciones de performance (158 filas + apply_theme). Al
        diferirla a la primera navegación, el arranque del Hub baja de
        ~795ms a ~340ms en offscreen QA. Idempotente: si ya existe y está
        viva, la devuelve; si fue deleteada, la reconstruye.
        """
        existing = self._views_cache.get("textos_globales")
        if existing is not None and not sip.isdeleted(existing):
            return existing
        from hub.config_global_texts import TextosGlobalesSuiteView

        view = TextosGlobalesSuiteView(
            modo=self._modo,
            sb=self._sb,
            parent=self._stack,
        )
        self._views_cache["textos_globales"] = view
        self._view_textos_globales = view
        self._stack.addWidget(view)
        # Aplicar tema actual a la nueva vista (puede haber cambiado desde
        # el arranque).
        try:
            _apply_theme_tree(view, self._modo)
        except Exception:
            pass
        return view

    def _nav_views(self) -> dict:
        views = {
            "pacientes": self._view_pacientes,
        }
        # Lazy: solo exponer textos_globales si ya fue construida.
        tg = self._views_cache.get("textos_globales")
        if tg is not None and not sip.isdeleted(tg):
            views["textos_globales"] = tg
        return views

    # ── Navegación ────────────────────────────────────────────────────────────

    def _on_nav(self, item_id: str):
        self._current_view = item_id
        views = self._nav_views()
        if item_id in views:
            self._stack.setCurrentWidget(views[item_id])
            if hasattr(self, "_chrome"):
                self._chrome.set_subtitle(self._view_title(item_id))

    def _select_patient(self, pid: str, nombre: str):
        self._paciente_id = pid
        self._paciente_nombre = nombre
        # (Las ex-vistas globales Presets/Textos/IA ya no existen: todo lo
        # por-paciente vive dentro del detalle → Plan terapéutico / IA.)

        # Cargar vista de detalle
        from hub.pacientes_qt import DetallePacienteView

        # Anti-acumulación (BL-04): quitar cualquier DetallePacienteView previo del
        # stack antes de agregar el nuevo. Sin esto, cada _select_patient deja una
        # vista de detalle huérfana en el stack (crece sin límite y produce la
        # "superposición progresiva al navegar ida/vuelta").
        i = 0
        while i < self._stack.count():
            w = self._stack.widget(i)
            if isinstance(w, DetallePacienteView):
                self._stack.removeWidget(w)
                _disconnect_theme_tree(w)
                w.deleteLater()
            else:
                i += 1

        detalle = DetallePacienteView(
            modo=self._modo,
            sb=self._sb,
            paciente_id=pid,
            paciente_nombre=nombre,
        )
        detalle.back_requested.connect(self._back_to_pacientes)

        self._stack.addWidget(detalle)
        self._stack.setCurrentWidget(detalle)
        self._current_view = "detalle"
        if hasattr(self, "_chrome"):
            self._chrome.set_module_context(
                (nombre or "")[:24], None, self._back_to_pacientes
            )

        self._lbl_status.hide()
        self._lbl_status.setText(nombre[:24])
        self._lbl_status.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )

    def _open_global_texts(self):
        self._current_view = "textos_globales"
        view = self._ensure_textos_globales_view()
        if view is None:
            return
        if hasattr(view, "set_supabase_client"):
            view.set_supabase_client(self._sb)
        self._stack.setCurrentWidget(view)
        if hasattr(self, "_chrome"):
            self._chrome.set_module_context(
                "Textos globales de Suite", None, self._back_to_pacientes
            )



    def _back_to_pacientes(self):
        self._current_view = "pacientes"
        self._stack.setCurrentWidget(self._view_pacientes)
        if hasattr(self, "_chrome"):
            self._chrome.clear_module_context()

    # ── Conexión (lógica preservada exacta) ───────────────────────────────────

    def _init_connection(self):
        if visual_qa_enabled():
            self._activate_visual_qa_hub()
            return
        self._sb, motivo = _get_sb()
        colors(self._modo)
        if self._sb:
            # Verificar conexión real. Un error de RLS / permiso denegado /
            # JWT significa que Supabase RESPONDIÓ → estamos conectados, solo
            # que el rol anon no tiene acceso a esa tabla (config de RLS).
            # Solo un error de red real (DNS/timeout/refused) es "sin conexión".
            _verify_err = None
            _connected = False
            try:
                self._sb.table("patients").select("patient_id", count="exact").execute()
                _connected = True
            except Exception as _e:
                _msg = str(_e).lower()
                _rls_markers = (
                    "permission denied", "42501", "row-level", "rls",
                    "policy", "jwt", "not authorized", "401", "403",
                )
                if any(m in _msg for m in _rls_markers):
                    _connected = True  # Supabase respondió; RLS bloqueó la tabla
                else:
                    _verify_err = str(_e)[:60]
            if _connected:
                self._lbl_status.setText("● Conectado")
                self._lbl_status.setStyleSheet(
                    f"color: {v3c('success', self._modo).name()}; background: transparent;"
                )
                self._cargar_pacientes()
                return
            self._sb = None
        _detail = motivo or _verify_err or "verificación fallida"
        self._lbl_status.setText(f"● Sin conexión: {_detail}")
        self._lbl_status.setStyleSheet(
            f"color: {v3c('error', self._modo).name()}; background: transparent;"
        )
    def _cargar_pacientes(self):
        if visual_qa_enabled():
            self._on_pacientes_loaded(hub_patients())
            return
        if not self._sb:
            return

        def _fetch():
            try:
                # Orden estable por nombre. SIN dedupe-por-nombre en UI por
                # decisión explícita (informe owner v1.0 frente 5: no ocultar
                # duplicados sin entender el origen — se migran con
                # db/patients_dedupe.sql). El email distingue homónimos y
                # unlinked filtra pacientes quitados por el profesional
                # (db/patients_email_unlink.sql).
                try:
                    res = (
                        self._sb.table("patients")
                        .select("patient_id,patient_name,email,unlinked,last_sync_date")
                        .order("patient_name")
                        .execute()
                    )
                    pats = [p for p in (res.data or []) if not p.get("unlinked")]
                except Exception:
                    # Schema viejo sin email/unlinked: select compatible.
                    res = (
                        self._sb.table("patients")
                        .select("patient_id,patient_name")
                        .order("patient_name")
                        .execute()
                    )
                    pats = res.data or []
            except Exception:
                pats = []
            self._patients_loaded_signal.emit(pats)

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_pacientes_loaded(self, pats: list):
        # Ocultar también los desvinculados localmente (fallback cuando la
        # columna remota patients.unlinked no existe todavía).
        hidden = _load_local_unlinked()
        self._pacientes = [p for p in pats if (p.get("patient_id") or "") not in hidden]
        self._refresh_all_views(force_recreate=True)

    def _activate_visual_qa_hub(self):
        colors(self._modo)
        self._sb = None
        self._pacientes = hub_patients()
        if self._pacientes:
            self._paciente_id = self._pacientes[0]["patient_id"]
            self._paciente_nombre = self._pacientes[0]["patient_name"]
        if hasattr(self, "_chrome"):
            self._chrome.set_subtitle(self._view_title(self._current_view))
        self._lbl_status.setText("● Demo visual")
        self._lbl_status.setStyleSheet(
            f"color: {v3c('teal', self._modo).name()}; background: transparent;"
        )
        self._refresh_all_views(force_recreate=True)

    def _reconnect(self):
        if visual_qa_enabled():
            self._activate_visual_qa_hub()
            NMToast.display(self, "Demo visual recargado", variant="success", duration_ms=1600)
            return
        self._sb, motivo = _get_sb()
        colors(self._modo)
        if self._sb:
            try:
                res = self._sb.table("patients").select("patient_id", count="exact").execute()
                if hasattr(res, "data"):
                    self._lbl_status.setText("● Conectado")
                    self._lbl_status.setStyleSheet(
                        f"color: {v3c('success', self._modo).name()}; background: transparent;"
                    )
                    self._cargar_pacientes()
                    NMToast.display(
                        self, "Conexión restablecida", variant="success", duration_ms=2000
                    )
                    return
            except Exception:
                pass
            self._sb = None
        self._lbl_status.setText(f"● Error: {motivo or 'verificación fallida'}")
        self._lbl_status.setStyleSheet(
            f"color: {v3c('error', self._modo).name()}; background: transparent;"
        )
        NMToast.display(
            self, f"No se pudo conectar: {motivo or 'verificación fallida'}", variant="error"
        )

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        new_mode = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        # M3 F0/F2: usar switch_mode para hacer un crossfade suave sin recreación destructiva
        ThemeManager.instance().switch_mode(new_mode)
        _persist_theme(new_mode)
        QTimer.singleShot(
            50,
            lambda: aplicar_captionbar_qt(self, self._modo) if not sip.isdeleted(self) else None,
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
        cw = self.centralWidget()
        if isinstance(cw, _ShellWidget):
            cw.set_shell_modo(self._modo)
        if hasattr(self, "_chrome"):
            self._chrome._apply_theme(self._modo)
        if hasattr(self, "_header"):
            self._header._apply_theme(self._modo)
        # Re-aplicar QSS del content widget con el surface del modo actual
        # (el QSS incluye el hex literal, hay que refrescarlo en cada switch).
        if hasattr(self, "_content_widget"):
            self._content_widget.setStyleSheet(self._shell_content_qss(self._modo))
        # M3 F2: propagar el cambio de tema de forma no destructiva a todas las vistas
        if hasattr(self, "_views_cache"):
            for name, w in self._views_cache.items():
                if w and not sip.isdeleted(w):
                    _apply_theme_tree(w, self._modo)

    @staticmethod
    def _shell_content_qss(modo: str) -> str:
        """QSS para el content widget: pinta surface (mockup .window bg)."""
        surf_hex = v3c("surface", modo).name()
        return f"QWidget#NMHubShellContent {{ background-color: {surf_hex}; }}"

    # ── DWM shadow + resize handles (frameless) ───────────────────────────────

    def _apply_dwm_shadow(self):
        pass

    def nativeEvent_disabled(self, event_type, message):
        """Maneja WM_NCHITTEST para resize handles en ventana frameless.

        DESHABILITADO (ses.19): Gemini lo había renombrado a `nativeEvent` (M3),
        habilitándolo como override real → el Hub CRASHEA nativamente al abrir
        onscreen (el probe offscreen no lo detecta: no entrega mensajes nativos).
        Restaurado a `_disabled` (estado conocido-funcional; el Suite también lo
        tiene disabled). El resize por bordes se reimplementará con test onscreen.
        """
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            try:
                import ctypes
                import ctypes.wintypes

                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084:  # WM_NCHITTEST
                    BORDER = 8
                    x = ctypes.c_short(msg.lParam & 0xFFFF).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                    geo = self.geometry()
                    lx, ly = geo.x(), geo.y()
                    rx, ry = geo.right(), geo.bottom()
                    on_l = x < lx + BORDER
                    on_r = x > rx - BORDER
                    on_t = y < ly + BORDER
                    on_b = y > ry - BORDER
                    if on_t and on_l:
                        return True, 13  # HTTOPLEFT
                    if on_t and on_r:
                        return True, 14  # HTTOPRIGHT
                    if on_b and on_l:
                        return True, 16  # HTBOTTOMLEFT
                    if on_b and on_r:
                        return True, 17  # HTBOTTOMRIGHT
                    if on_t:
                        return True, 12  # HTTOP
                    if on_b:
                        return True, 15  # HTBOTTOM
                    if on_l:
                        return True, 10  # HTLEFT
                    if on_r:
                        return True, 11  # HTRIGHT
            except Exception:
                pass
        return super().nativeEvent(event_type, message)

    def closeEvent(self, event):
        # BL-02: arrastrar el cierre a las ventanas hijas top-level (editores del
        # Hub) para que no queden huérfanas al cerrar la main window. Se cierran las
        # ventanas cuyo parent es esta main (editores, diálogos), no la main misma.
        try:
            for child in QApplication.topLevelWidgets():
                if child is not self and child.parent() is self and child.isVisible():
                    child.close()
        except Exception:
            pass
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    from shared.crash_log import setup as _crash_setup

    _crash_setup("hub")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood Hub")
    app.setOrganizationName("NeuroMood")
    install_transient_qt_window_guard(app.applicationName())
    # Invoker para entregar callbacks de hilos worker (IA, PDF) al hilo GUI.
    init_gui_invoker()
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente

    # ── Instancia única (paridad con el Suite) ─────────────────────────────
    # Doble click del profesional sobre el acceso directo no debe abrir un
    # segundo Hub: si ya hay una instancia, le pedimos que se muestre y
    # salimos. Se omite en QA/smoke (corren en paralelo).
    _single_server = None
    if not (
        visual_qa_enabled()
        or os.environ.get("NM_QA_SMOKE") == "1"
        or os.environ.get("NM_TEST_FORCE_CLOSE") == "1"
    ):
        try:
            from PyQt6.QtNetwork import QLocalServer, QLocalSocket

            _SINGLETON = "NeuroMoodHub_singleton"
            _probe = QLocalSocket()
            _probe.connectToServer(_SINGLETON)
            if _probe.waitForConnected(300):
                _probe.write(b"activate")
                _probe.flush()
                _probe.waitForBytesWritten(300)
                _probe.disconnectFromServer()
                sys.exit(0)
            _probe.abort()
            QLocalServer.removeServer(_SINGLETON)  # limpia un named-pipe stale
            _single_server = QLocalServer()
            if not _single_server.listen(_SINGLETON):
                _single_server = None
        except Exception:
            _single_server = None

    # Cargar fuentes del handoff (Newsreader, Manrope, JetBrains Mono).
    try:
        from shared.fonts import load_fonts

        load_fonts()
    except Exception:
        pass

    # ── Garantizar AppData Hub con credenciales base ──────────────────────
    # Los profesionales acceden libremente — no se requiere login.
    # _ensure_hub_env_base() crea %APPDATA%\NeuroMoodHub\.env si falta
    # (fallback de autogestión cuando el installer no lo desplegó).
    if not visual_qa_enabled():
        _ensure_hub_env_base()

    window = NeuroMoodHub()
    window.show()
    # Esquinas redondeadas nativas (Win11; no-op Win10) — flags ya definitivos.
    from shared.adaptive_layout_qt import apply_native_rounded_corners

    apply_native_rounded_corners(window)

    # Si somos la instancia primaria, atender pedidos de "mostrate" de
    # instancias nuevas (en vez de dejarlas abrir otro proceso).
    if _single_server is not None:

        def _on_second_instance():
            sock = _single_server.nextPendingConnection()
            if sock is not None:
                sock.readAll()
                sock.disconnectFromServer()
            window.showNormal()
            window.raise_()
            window.activateWindow()

        _single_server.newConnection.connect(_on_second_instance)
        window._single_server = _single_server  # mantener viva la referencia

    # ── Hook de QA Smoke (Fase 2) ──────────────────────────────────────────
    if os.environ.get("NM_QA_SMOKE") == "1":
        print("QA Smoke Test: programando cierre automático en 3 segundos.")
        QTimer.singleShot(3000, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
