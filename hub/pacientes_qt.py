"""
hub/pacientes_qt.py — Vista detallada de paciente (PyQt6)
"""

import logging
from datetime import datetime, timedelta

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

_log = logging.getLogger("NeuroMoodHub.Pacientes")

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
        self._btn_exportar_pdf = NMButton(
            "Exportar PDF", variant="secondary", size="sm", modo=self._modo, width=120
        )
        self._btn_exportar_pdf.clicked.connect(self._on_exportar_pdf)
        ia_row.addWidget(self._btn_exportar_pdf)
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

    def _set_exportar_pdf_busy(self, busy: bool):
        self._btn_exportar_pdf.setEnabled(not busy)
        self._btn_exportar_pdf.setText("Exportando..." if busy else "Exportar PDF")

    def _on_exportar_pdf(self):
        self._set_exportar_pdf_busy(True)
        try:
            from hub.exportar import exportar_pdf
        except ImportError:
            self._set_exportar_pdf_busy(False)
            NMToast.display(self.window(), "Exportación PDF no disponible", variant="error")
            return

        datos = self._fetch_patient_data()

        def on_done(ruta: str):
            self._set_exportar_pdf_busy(False)
            NMToast.display(self.window(), f"PDF generado: {ruta}", variant="success")

        def on_error(msg: str):
            self._set_exportar_pdf_busy(False)
            NMToast.display(self.window(), f"No se pudo exportar PDF: {msg[:60]}", variant="error")

        exportar_pdf(
            self._nombre,
            self._pid,
            datos,
            on_done=on_done,
            on_error=on_error,
        )

    def _fetch_patient_data(self) -> dict:
        """Trae registros reales de los 8 modulos Suite desde Supabase.

        S0-1 (auditoria profunda): corrige 4 referencias a tablas inexistentes
        que hacian que el fetch devolviera siempre listas vacias para
        animo, TCC, activacion conductual y DBT. Los `except: pass` silenciaban
        el error.

        Tablas reales (ver db/supabase_schema.sql y db/dbt_practice_records.sql):
          - mood_records           (era "animo_registros")
          - breathing_sessions     (ya era correcta)
          - thought_records        (era "tcc_registros")
          - checklist_completions  (ya era correcta)
          - activation_results     (era "activacion_registros")
          - timer_sessions         (ya era correcta)
          - assigned_reminders     (ya era correcta — programacion del profesional)
          - dbt_practice_records   (era "dbt_registros")
          - reminder_logs          (RB-3: telemetria de avisos disparados al paciente)

        Campos: trae los campos textuales reales de cada tabla (no solo
        id+fecha) para que el prompt de IA y el PDF puedan usarlos. Esto es
        tecnicamente S1-1, pero se incluye aca porque estamos reescribiendo
        las queries de todas formas.
        """
        datos: dict = {
            "animo": [], "respiracion": [], "tcc": [], "checklist": [],
            "actividades": [], "timer": [], "recordatorios": [], "dbt": [],
            "avisos_disparados": [],
        }
        if not self._sb:
            return datos

        fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        def _fetch(key: str, table: str, columns: str, limit: int = 30) -> None:
            """Una query por modulo. Loguea errores en vez de silenciarlos."""
            try:
                r = (
                    self._sb.table(table)
                    .select(columns)
                    .eq("patient_id", self._pid)
                    .gte("fecha", fecha_desde)
                    .order("fecha", desc=True)
                    .limit(limit)
                    .execute()
                )
                datos[key] = r.data or []
            except Exception as exc:
                _log.warning(
                    "_fetch_patient_data: fallo fetch tabla=%s key=%s pid=%s: %s",
                    table, key, self._pid, exc,
                )

        # 1) Ánimo: escala única 1-10. No pedir campos que este módulo no captura.
        _fetch("animo", "mood_records",
               "fecha,hora,puntaje,nota", limit=30)

        # 2) Respiracion - tabla real: breathing_sessions (ya era correcta)
        _fetch("respiracion", "breathing_sessions",
               "fecha,hora,tecnica,duracion_minutos,ciclos", limit=30)

        # 3) TCC - tabla real: thought_records (era "tcc_registros").
        # RA-6: NO se pide `reflexion_ia` porque el módulo TCC actual no la
        # captura (no hay widget). Pedirla traería el default del schema
        # Supabase (NULL) — el Hub no la necesita.
        _fetch("tcc", "thought_records",
               "fecha,hora,situacion,emocion,intensidad,pensamiento,"
               "respuesta_alternativa,distorsiones", limit=20)

        # 4) Rutina (checklist) - tabla real: checklist_completions (ya era correcta)
        _fetch("checklist", "checklist_completions",
               "fecha,descripcion,categoria,origen", limit=30)

        # 5) Actividades - tabla real: activation_results (era "activacion_registros").
        # RA-1 (reauditoría UI-first): NO se pide `energia` porque el módulo
        # Actividades no la captura. Pedirla traería el default del schema
        # Supabase (NULL) — el Hub no la necesita para mostrar registros.
        _fetch("actividades", "activation_results",
               "fecha,hora,animo,actividad,resultado", limit=20)

        # 6) Timer - tabla real: timer_sessions (ya era correcta)
        _fetch("timer", "timer_sessions",
               "fecha,hora,nombre,categoria,duracion_config,duracion_real,notas", limit=20)

        # 7) Recordatorios asignados - tabla real: assigned_reminders (ya era correcta).
        # NOTA: assigned_reminders es la programacion que el profesional definió
        # para el paciente. La telemetría real de avisos disparados al paciente
        # se consulta de reminder_logs (ver fetch #9 / RB-3). No mezclar.
        try:
            r = (
                self._sb.table("assigned_reminders")
                .select("id,hora,mensaje,dias,activa,completado_en")
                .eq("patient_id", self._pid)
                .order("hora", desc=False)
                .limit(50)  # RC-3/S0-1: limit explicito (regresion congelada por test_rc3_limit_assigned_reminders)
                .execute()
            )
            datos["recordatorios"] = r.data or []
        except Exception as exc:
            _log.warning(
                "_fetch_patient_data: fallo fetch assigned_reminders pid=%s: %s",
                self._pid, exc,
            )

        # 8) DBT - tabla real: dbt_practice_records (era "dbt_registros")
        _fetch("dbt", "dbt_practice_records",
               "fecha,hora,skill_id,skill_version,familia,necesidad,"
               "malestar_antes,malestar_despues,resultado,duracion_seg,nota",
               limit=20)

        # 9) Telemetría de avisos disparados - tabla real: reminder_logs (RB-3).
        # Distinto de assigned_reminders: aqui se registra cada vez que un aviso
        # se disparo efectivamente al paciente (auditoria / adherencia real).
        # Columnas verificadas en db/supabase_schema.sql:82-90.
        _fetch("avisos_disparados", "reminder_logs",
               "fecha,hora,mensaje,cerrado", limit=50)

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
