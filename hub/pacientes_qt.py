"""
hub/pacientes_qt.py — Vista detallada de paciente (PyQt6)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDialog,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QTextBrowser,
)

try:
    from shared.components import (
        NMCard,
        NMAvatar,
        NMBadge,
        NMButton,
        NMDialogScaffold,
        NMElidedLabel,
        NMToast,
        ThemeManager,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
        V3_SP,
    )
    from shared.qt_thread import run_on_gui
    from shared.theme import TYPOGRAPHY
    from shared.adaptive_layout_qt import window_edge_radius
except ImportError:
    import os
    import sys
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMCard,
        NMAvatar,
        NMBadge,
        NMButton,
        NMDialogScaffold,
        NMElidedLabel,
        NMToast,
        ThemeManager,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
        V3_SP,
    )
    from shared.qt_thread import run_on_gui
    from shared.theme import TYPOGRAPHY
    from shared.adaptive_layout_qt import window_edge_radius

# ── DetallePacienteView ───────────────────────────────────────────────────────


class DetallePacienteView(QWidget):
    """Panel completo de detalle de paciente con shell premium y tabs clínicas."""

    back_requested = pyqtSignal()

    def __init__(self, modo: str, sb, paciente_id: str, paciente_nombre: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._sb = sb
        self._pid = paciente_id
        self._nombre = paciente_nombre
        self.setObjectName("DetallePacienteView")
        self.setAccessibleName(f"DetallePacienteView patient_id={self._pid}")
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _setup(self):
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # (Se eliminó la NMProgressLine de 2px del tope: al seleccionar un
        # paciente se leía como una línea que separaba la titlebar de la ventana
        # principal — pedido owner.)

        # Patient hero shell — alto reducido: el header lo paga TODA tab y el
        # contenido se recortaba abajo (H12/H21). Menos padding/avatar libera
        # ~18px de viewport para resumen/registros/ia/plan sin perder jerarquía.
        top = NMCard(modo=self._modo, clickable=False, glow=False)
        top.setMinimumHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(18, 10, 18, 10)
        tl.setSpacing(14)

        initials = "".join(w[0] for w in (self._nombre or "?").split()[:2]).upper()
        self._avatar = NMAvatar(
            initials=initials or "P", size=40, color_seed=self._pid or self._nombre, modo=self._modo
        )
        tl.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._lbl_eyebrow = QLabel("Paciente")
        self._lbl_eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        text_col.addWidget(self._lbl_eyebrow)

        # NMElidedLabel: a 960px el hero no tiene ancho para nombre + subtítulo
        # + 3 chips; los labels ceden con "…" en vez de empujar los chips a
        # geometrías bajo-mínimo (Qt los superpone físicamente en ese caso).
        self._lbl_name = NMElidedLabel(self._nombre)
        self._lbl_name.setFont(v3_font("size_h2", weight=600, serif=True))
        text_col.addWidget(self._lbl_name)

        # Texto corto: "del paciente" era redundante (eyebrow PACIENTE + nombre
        # arriba) y a 960px forzaba elisión permanente.
        self._lbl_meta = NMElidedLabel("Seguimiento profesional")
        self._lbl_meta.setAccessibleName(f"Seguimiento profesional del paciente ID {self._pid}")
        self._lbl_meta.setFont(qfont("size_caption"))
        self._lbl_meta.setWordWrap(False)
        text_col.addWidget(self._lbl_meta)

        tl.addLayout(text_col, stretch=1)

        # Las pills de cabecera (Semana / Alerta / Progreso) fueron eliminadas:
        # afirmaban señales clínicas que el seguimiento no valida. El encabezado
        # queda con el perfil + el acceso a Resumen IA.
        chips_col = QVBoxLayout()
        chips_col.setContentsMargins(0, 0, 0, 0)
        chips_col.setSpacing(6)

        ia_row = QHBoxLayout()
        ia_row.setContentsMargins(0, 4, 0, 0)
        ia_row.addStretch()
        self._btn_resumen_ia = NMButton(
            "Resumen IA", variant="ghost", size="sm", modo=self._modo, width=120
        )
        self._btn_resumen_ia.clicked.connect(self._on_resumen_ia)
        ia_row.addWidget(self._btn_resumen_ia)
        chips_col.addLayout(ia_row)

        tl.addLayout(chips_col)
        top_wrap = QWidget()
        top_wrap.setStyleSheet("background: transparent;")
        top_lay = QVBoxLayout(top_wrap)
        top_lay.setContentsMargins(12, 4, 12, 2)
        top_lay.setSpacing(0)
        top_lay.addWidget(top)
        layout.addWidget(top_wrap)

        from hub.plan_terapeutico import PlanTerapeuticoTab

        self._tab_plan = PlanTerapeuticoTab(self._modo, self._sb, self._pid, self._nombre)

        plan_wrap = QWidget()
        plan_wrap.setStyleSheet("background: transparent;")
        plan_lay = QVBoxLayout(plan_wrap)
        plan_lay.setContentsMargins(12, 0, 12, 4)
        plan_lay.setSpacing(0)
        plan_lay.addWidget(self._tab_plan)
        layout.addWidget(plan_wrap, stretch=1)

    def _on_resumen_ia(self):
        self._btn_resumen_ia.setEnabled(False)
        self._btn_resumen_ia.setText("Generando...")
        try:
            from hub.ia_asistente import generar_resumen_paciente
        except ImportError:
            NMToast.display(self.window(), "Modulo IA no disponible", variant="error")
            self._btn_resumen_ia.setEnabled(True)
            self._btn_resumen_ia.setText("Resumen IA")
            return

        datos = self._fetch_patient_data()

        def on_ok(txt: str):
            run_on_gui(lambda: self._show_resumen_dialog(txt))

        def on_err(msg: str):
            run_on_gui(lambda: self._on_resumen_ia_error(msg))

        generar_resumen_paciente(
            datos, self._nombre, on_ok, on_err, patient_id=self._pid
        )

    def _fetch_patient_data(self) -> dict:
        datos: dict = {
            "animo": [], "respiracion": [], "tcc": [], "checklist": [],
            "actividades": [], "timer": [], "recordatorios": [], "dbt": [],
        }
        if not self._sb:
            return datos
        try:
            r = self._sb.table("animo_registros").select("puntaje,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(30).execute()
            datos["animo"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("breathing_sessions").select("id,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(30).execute()
            datos["respiracion"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("tcc_registros").select("id,emocion,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(20).execute()
            datos["tcc"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("checklist_completions").select("id,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(30).execute()
            datos["checklist"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("activacion_registros").select("id,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(20).execute()
            datos["actividades"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("timer_sessions").select("id,duracion,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(20).execute()
            datos["timer"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("assigned_reminders").select("id,hora,mensaje").eq(
                "patient_id", self._pid
            ).execute()
            datos["recordatorios"] = r.data or []
        except Exception:
            pass
        try:
            r = self._sb.table("dbt_registros").select("id,fecha").eq(
                "patient_id", self._pid
            ).order("fecha", desc=True).limit(20).execute()
            datos["dbt"] = r.data or []
        except Exception:
            pass
        return datos

    def _show_resumen_dialog(self, text: str):
        self._btn_resumen_ia.setEnabled(True)
        self._btn_resumen_ia.setText("Resumen IA")

        dialog = QDialog(self.window())
        dialog.setWindowTitle("Resumen IA")
        dialog.setModal(True)
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        _bc = v3c("borderStrong" if is_dark else "border", self._modo)
        try:
            radius = window_edge_radius()
        except Exception:
            radius = 12
        dialog.setStyleSheet(
            f"QDialog {{ background: {card_bg}; border: 1px solid "
            f"rgba({_bc.red()},{_bc.green()},{_bc.blue()},{_bc.alpha()}); "
            f"border-radius: {radius}px; }}"
        )
        dialog.setFixedWidth(480)
        dialog.setMinimumHeight(320)

        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        scaffold = NMDialogScaffold(
            title="Resumen IA",
            eyebrow=self._nombre,
            modo=self._modo,
            parent=dialog,
        )
        root.addWidget(scaffold)

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["lg"])
        bl.setSpacing(V3_SP["sm"])

        tb = QTextBrowser()
        tb.setPlainText(text)
        tb.setReadOnly(True)
        tb.setFrameShape(QFrame.Shape.NoFrame)
        tb.setStyleSheet(
            f"QTextBrowser {{ background: transparent; color: {v3c('text', self._modo).name()}; "
            f"border: none; font-size: 13px; }}"
        )
        tb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bl.addWidget(tb, 1)

        close_row = QHBoxLayout()
        close_row.addStretch()
        btn_close = NMButton("Cerrar", modo=self._modo, size="sm", width=90)
        btn_close.clicked.connect(dialog.accept)
        close_row.addWidget(btn_close)
        bl.addLayout(close_row)

        scaffold.set_body(body)
        dialog.exec()

    def _on_resumen_ia_error(self, msg: str):
        self._btn_resumen_ia.setEnabled(True)
        self._btn_resumen_ia.setText("Resumen IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("background: transparent;")
        ink1 = v3c("text", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._lbl_eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._lbl_name.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._lbl_meta.setStyleSheet(f"color: {ink2}; background: transparent;")
