"""
hub/main_qt.py — Hub Profesional NeuroMood (PyQt6 entry point)

Layout:
    QMainWindow
    ├── NMSidebar (200px, izquierda)
    └── área derecha
        ├── NMHeader (56px)
        └── NMFadeWidget
            ├── DashboardView
            ├── PacientesView
            ├── DetallePacienteView (se carga al seleccionar paciente)
            └── ConfigView

Toda la lógica de conexión Supabase preservada exacta.
"""

import sys
import os
import threading

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QScrollArea, QGridLayout, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPointF
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QBrush, QRadialGradient
from PyQt6 import sip

from shared.theme_qt import (
    C, colors, norm_modo, qcolor, qfont, interpolate_color, SessionColor,
    get_gradient, gradient_colors, app_palette, stylesheet_base, stylesheet_scrollarea,
    obtener_ruta_recurso, aplicar_captionbar_qt,
    RADIUS_CARD, RADIUS_BUTTON, PAD_CONTAINER, PAD_CARD, GAP_CARDS,
    ThemeAwareWidgetMixin, HUB_ICONS, nm_icon,
)
from shared.components_qt import (
    ThemeManager, NMSidebar, NMHeader, NMFadeWidget,
    NMButton, NMButtonOutline, NMCard, NMToast, NMSkeleton,
)

_sb_create = None

from shared.config import supabase_url, supabase_key

_NAV_ITEMS = [
    ("dashboard", "fa5s.chart-bar", "Dashboard"),
    ("pacientes", "pacientes", "Pacientes"),
    ("config", "configuracion", "Config"),
]


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
    global _sb_create
    if _sb_create is None:
        try:
            from supabase import create_client
            _sb_create = create_client
        except ImportError:
            return None, "modulo supabase no instalado"
    url, key = supabase_url(), supabase_key()
    if not url or not key:
        return None, "credenciales no configuradas (.env)"
    try:
        return _sb_create(url, key), None
    except Exception as e:
        return None, str(e)[:60]


# ── Mini indicador de ánimo ───────────────────────────────────────────────────

class _AnimoIndicator(QWidget):
    """Círculo de 14px con color semántico del último ánimo registrado."""

    _COLORS = {
        range(1, 4):  "error",
        range(4, 7):  "warning",
        range(7, 11): "success",
    }

    def __init__(self, puntaje: int | None, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        self._puntaje = puntaje
        self.setFixedSize(14, 14)
        self._update_color()
        self.setStyleSheet("background: transparent;")
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _update_color(self):
        modo = norm_modo(self._modo)
        self._color = C("text_tertiary", modo)
        if self._puntaje is not None:
            for r, key in self._COLORS.items():
                if self._puntaje in r:
                    self._color = C(key, modo)
                    break

    def apply_theme(self, modo: str):
        self._modo = modo
        self._update_color()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 12, 12)
        p.end()


# ── DashboardView ─────────────────────────────────────────────────────────────

class DashboardView(ThemeAwareWidgetMixin, QWidget):
    def __init__(self, modo: str, pacientes: list, sb,
                 on_select_patient, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._pacientes = pacientes
        self._sb = sb
        self._on_select = on_select_patient
        self._setup()
        self._connect_theme()

    def paintEvent(self, event):
        """Aura radial dinámica de fondo."""
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        sc = SessionColor.instance()
        grad = QRadialGradient(w * 0.2, h * 0.5, w * 0.85)
        grad.setColorAt(0, sc.aura_qcolor(self._modo))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRect(self.rect())
        p.end()

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_CARDS)

        # Título
        n = len(self._pacientes)
        title = QLabel(
            f"Dashboard  —  {n} paciente{'s' if n != 1 else ''}"
        )
        title.setFont(qfont("size_h2", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(title)

        if not self._pacientes:
            empty = QLabel(
                "Sin pacientes registrados.\n"
                "Usá la sección Pacientes para vincular."
            )
            empty.setFont(qfont("size_body"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            layout.addWidget(empty)
            # Skeleton loaders mientras carga
            sk_grid = QGridLayout()
            sk_grid.setSpacing(GAP_CARDS)
            for col in range(3):
                sk_grid.setColumnStretch(col, 1)
            for i in range(3):
                sk = NMSkeleton(width=200, height=120, radius=RADIUS_CARD, modo=self._modo)
                sk_grid.addWidget(sk, i // 3, i % 3)
            layout.addLayout(sk_grid)
            layout.addStretch()
            return

        # Grid de cards 3 columnas
        grid = QGridLayout()
        grid.setSpacing(GAP_CARDS)
        for col in range(3):
            grid.setColumnStretch(col, 1)

        grad = gradient_colors(self._modo)

        for i, p in enumerate(self._pacientes):
            nombre = p.get("patient_name") or p.get("patient_id", "—")
            pid = p.get("patient_id", "")
            t = (i % 3) / 2
            card_accent = interpolate_color(grad[0], grad[-1], t)

            card = NMCard(accent_color=card_accent, clickable=True, modo=self._modo)
            card.setMinimumHeight(120)
            card.clicked.connect(
                lambda checked=False, _pid=pid, _n=nombre:
                    self._on_select(_pid, _n)
            )

            inner = QVBoxLayout()
            inner.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
            inner.setSpacing(4)

            # Fila top: nombre + indicador ánimo
            top_row = QHBoxLayout()
            name_lbl = QLabel(nombre)
            name_lbl.setFont(qfont("size_body", bold=True))
            name_lbl.setStyleSheet(
                f"color: {c['text_primary']}; background: transparent;"
            )
            name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(name_lbl)
            top_row.addStretch()

            # Indicador de animo (ultimo puntaje si existe en los datos)
            puntaje = p.get("last_mood") if "last_mood" in p else None
            ind = _AnimoIndicator(puntaje, self._modo)
            ind.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            top_row.addWidget(ind)
            inner.addLayout(top_row)

            # ID truncado
            id_lbl = QLabel(f"ID: {pid[:14]}…" if len(pid) > 14 else pid)
            id_lbl.setFont(qfont("size_caption"))
            id_lbl.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )
            id_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(id_lbl)

            inner.addStretch()

            btn = NMButton("Ver detalle", modo=self._modo, width=100, height=30)
            btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            inner.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)

            # Montar inner en card
            card_inner = QWidget(card)
            card_inner.setStyleSheet("background: transparent;")
            card_inner.setLayout(inner)
            card_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.addWidget(card_inner)

            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")


# ── PacientesView ─────────────────────────────────────────────────────────────

class PacientesView(QWidget):
    def __init__(self, modo: str, pacientes: list, on_select, on_refresh, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._pacientes = pacientes
        self._on_select = on_select
        self._on_refresh = on_refresh
        self._setup()

    def _setup(self):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_CARDS)

        # Título + refresh
        top = QHBoxLayout()
        title = QLabel("Pacientes vinculados")
        title.setFont(qfont("size_h2", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        top.addWidget(title)
        top.addStretch()
        btn_ref = NMButtonOutline("↻ Actualizar", modo=self._modo)
        btn_ref.setFixedSize(120, 32)
        btn_ref.clicked.connect(self._on_refresh)
        top.addWidget(btn_ref)
        layout.addLayout(top)

        # Lista
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        lst = QVBoxLayout(container)
        lst.setContentsMargins(0, 0, 0, 0)
        lst.setSpacing(6)
        lst.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        if not self._pacientes:
            empty = QLabel("No hay pacientes vinculados.")
            empty.setFont(qfont("size_body"))
            empty.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            lst.addWidget(empty)
            return

        for p in self._pacientes:
            nombre = p.get("patient_name") or "—"
            pid = p.get("patient_id", "")

            row = NMCard(clickable=False, modo=self._modo)
            row.setMinimumHeight(46)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 0, 12, 0)

            nl = QLabel(nombre)
            nl.setFont(qfont("size_body"))
            nl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            rl.addWidget(nl)

            idl = QLabel(pid[:16])
            idl.setFont(qfont("size_caption"))
            idl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            rl.addWidget(idl)
            rl.addStretch()

            btn = NMButton("Ver detalle", modo=self._modo, width=100, height=28)
            btn.clicked.connect(
                lambda checked=False, _pid=pid, _n=nombre:
                    self._on_select(_pid, _n)
            )
            rl.addWidget(btn)
            lst.addWidget(row)


# ── ConfigView ────────────────────────────────────────────────────────────────

class ConfigView(QWidget):
    def __init__(self, modo: str, on_toggle_theme, on_reconnect, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._setup(on_toggle_theme, on_reconnect)

    def _setup(self, on_toggle_theme, on_reconnect):
        c = colors(self._modo)
        self.setStyleSheet(f"background: {c['bg_primary']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, PAD_CONTAINER,
                                   PAD_CONTAINER, PAD_CONTAINER)
        layout.setSpacing(GAP_CARDS)

        title = QLabel("Configuración")
        title.setFont(qfont("size_h2", bold=True))
        title.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(title)

        def _card(titulo: str, btn_text: str, callback) -> NMCard:
            card = NMCard(clickable=False, modo=self._modo)
            card.setMinimumHeight(52)
            fl = QHBoxLayout(card)
            fl.setContentsMargins(PAD_CARD, 10, PAD_CARD, 10)
            fl.setSpacing(8)
            lbl = QLabel(titulo)
            lbl.setFont(qfont("size_body", bold=True))
            lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            fl.addWidget(lbl)
            fl.addStretch()
            btn = NMButtonOutline(btn_text, modo=self._modo)
            btn.setFixedSize(130, 32)
            btn.clicked.connect(callback)
            fl.addWidget(btn)
            return card

        layout.addWidget(_card("Base de datos", "Reconectar", on_reconnect))
        layout.addStretch()


# ── HubProfesional ────────────────────────────────────────────────────────────

class HubProfesional(ThemeAwareWidgetMixin, QMainWindow):

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self._sb = None
        self._pacientes: list = []
        self._paciente_id: str | None = None
        self._paciente_nombre: str = ""
        self._current_view = "dashboard"

        ThemeManager.instance().switch_mode(self._modo)

        self.setWindowTitle("NeuroMood Hub Pro")
        self.setMinimumSize(QSize(900, 560))
        self.resize(QSize(1100, 680))
        self._center()
        self._apply_icon()
        self._apply_initial_style()
        self._build_ui()

        QTimer.singleShot(120, lambda: aplicar_captionbar_qt(self, self._modo))
        QTimer.singleShot(350, self._init_connection)
        self._connect_theme()

    # ── Ventana ───────────────────────────────────────────────────────────────

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        target_w = min(1100, int(screen.width() * 0.75))
        target_h = min(720, int(screen.height() * 0.82))
        if target_w < self.minimumWidth():
            target_w = self.minimumWidth()
        if target_h < self.minimumHeight():
            target_h = self.minimumHeight()
        self.resize(QSize(target_w, target_h))
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def _apply_icon(self):
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

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = NMSidebar(central, modo=self._modo)
        self._sidebar.add_logo()
        self._sidebar.add_header("NeuroMood Hub Pro")
        for iid, icon_key, label in _NAV_ITEMS:
            self._sidebar.add_item(iid, nm_icon(icon_key, C("accent", self._modo), size=18), label)
        self._sidebar.add_spacer()
        self._sidebar.add_separator()
        self._sidebar.add_label("Sin paciente")
        self._sidebar.nav_changed.connect(self._on_nav)
        main_layout.addWidget(self._sidebar)

        # Área derecha
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        main_layout.addWidget(right)

        # Header
        self._header = NMHeader(right, modo=self._modo)
        self._header.theme_toggle.connect(self._toggle_theme)
        rl.addWidget(self._header)

        # Status label en header
        c = colors(self._modo)
        self._lbl_status = QLabel("Conectando…")
        self._lbl_status.setFont(qfont("size_caption"))
        self._lbl_status.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent;"
        )
        # Insertar en el header layout
        header_layout = self._header.layout()
        if header_layout:
            header_layout.insertWidget(1, self._lbl_status)

        # Stack
        self._stack = NMFadeWidget(right)
        rl.addWidget(self._stack)

        # Vistas iniciales
        self._refresh_all_views()

    def _refresh_all_views(self):
        """Recrea todas las vistas con los datos actuales."""
        # Limpiar stack
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            _disconnect_theme_tree(w)
            w.deleteLater()

        self._view_dashboard = DashboardView(
            self._modo, self._pacientes, self._sb,
            on_select_patient=self._select_patient,
        )
        self._view_pacientes = PacientesView(
            self._modo, self._pacientes,
            on_select=self._select_patient,
            on_refresh=self._cargar_pacientes,
        )
        self._view_config = ConfigView(
            self._modo,
            on_toggle_theme=self._toggle_theme,
            on_reconnect=self._reconnect,
        )

        self._stack.addWidget(self._view_dashboard)
        self._stack.addWidget(self._view_pacientes)
        self._stack.addWidget(self._view_config)

        views = {
            "dashboard": self._view_dashboard,
            "pacientes":  self._view_pacientes,
            "config":     self._view_config,
        }
        target = views.get(self._current_view, self._view_dashboard)
        self._stack.setCurrentWidget(target)
        self._sidebar.set_active(self._current_view)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _on_nav(self, item_id: str):
        self._current_view = item_id
        views = {
            "dashboard": self._view_dashboard,
            "pacientes":  self._view_pacientes,
            "config":     self._view_config,
        }
        if item_id in views:
            self._stack.setCurrentWidget(views[item_id])

    def _select_patient(self, pid: str, nombre: str):
        self._paciente_id = pid
        self._paciente_nombre = nombre

        # Cargar vista de detalle
        from hub.pacientes_qt import DetallePacienteView
        detalle = DetallePacienteView(
            modo=self._modo, sb=self._sb,
            paciente_id=pid, paciente_nombre=nombre,
        )
        detalle.back_requested.connect(self._back_to_dashboard)

        self._stack.addWidget(detalle)
        self._stack.setCurrentWidget(detalle)
        self._current_view = "detalle"

        self._header.set_back_action(self._back_to_dashboard)
        self._lbl_status.setText(f"📋  {nombre[:24]}")
        self._lbl_status.setStyleSheet(
            f"color: {C('text_primary', self._modo)}; background: transparent;"
        )

    def _back_to_dashboard(self):
        self._current_view = "dashboard"
        self._stack.setCurrentWidget(self._view_dashboard)
        self._sidebar.set_active("dashboard")
        self._header.set_back_action(None)

    # ── Conexión (lógica preservada exacta) ───────────────────────────────────

    def _init_connection(self):
        self._sb, motivo = _get_sb()
        c = colors(self._modo)
        if self._sb:
            # Verificar conexión real
            try:
                res = self._sb.table("patients").select("patient_id", count="exact").execute()
                if hasattr(res, 'data'):
                    self._lbl_status.setText("● Conectado")
                    self._lbl_status.setStyleSheet(
                        f"color: {c['success']}; background: transparent;"
                    )
                    self._cargar_pacientes()
                    return
            except Exception:
                pass
            self._sb = None
        self._lbl_status.setText(f"● Sin conexión: {motivo or 'verificación fallida'}")
        self._lbl_status.setStyleSheet(
            f"color: {c['error']}; background: transparent;"
        )

    def _cargar_pacientes(self):
        if not self._sb:
            return

        def _fetch():
            try:
                res = (self._sb.table("patients")
                       .select("patient_id,patient_name")
                       .execute())
                pats = res.data or []
            except Exception:
                pats = []
            # Volver al hilo principal
            QTimer.singleShot(0, lambda p=pats: self._on_pacientes_loaded(p) if not sip.isdeleted(self) else None)

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_pacientes_loaded(self, pats: list):
        self._pacientes = pats
        self._refresh_all_views()

    def _reconnect(self):
        self._sb, motivo = _get_sb()
        c = colors(self._modo)
        if self._sb:
            try:
                res = self._sb.table("patients").select("patient_id", count="exact").execute()
                if hasattr(res, 'data'):
                    self._lbl_status.setText("● Conectado")
                    self._lbl_status.setStyleSheet(
                        f"color: {c['success']}; background: transparent;"
                    )
                    self._cargar_pacientes()
                    NMToast.show(self, "Conexión restablecida", variant="success", duration_ms=2000)
                    return
            except Exception:
                pass
            self._sb = None
        self._lbl_status.setText(f"● Error: {motivo or 'verificación fallida'}")
        self._lbl_status.setStyleSheet(
            f"color: {c['error']}; background: transparent;"
        )
        NMToast.show(self, f"No se pudo conectar: {motivo or 'verificación fallida'}", variant="error")

    # ── Tema ──────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._modo = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        ThemeManager.instance()._modo = self._modo
        self._apply_theme(self._modo)
        QTimer.singleShot(50, lambda: aplicar_captionbar_qt(self, self._modo))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
        if hasattr(self, "_sidebar"):
            self._sidebar._apply_theme(self._modo)
        if hasattr(self, "_header"):
            self._header._apply_theme(self._modo)
        if hasattr(self, "_lbl_status"):
            c = colors(self._modo)
            self._lbl_status.setStyleSheet(
                f"color: {c['text_tertiary']}; background: transparent;"
            )

    def closeEvent(self, event):
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood Hub")
    # AA_UseHighDpiPixmaps fue eliminado en PyQt6 6.x — DPI se maneja automáticamente
    window = HubProfesional()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
