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
    QFrame,
    QSizePolicy,
)

try:
    from shared.components import (
        NMCard,
        NMAvatar,
        NMButton,
        NMButtonOutline,
        NMElidedLabel,
        NMToast,
        ThemeManager,
    )
    from shared.components.dialogs import NMDialog
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
        V3_SP,
    )
    from shared.qt_thread import run_on_gui
    from shared.theme import TYPOGRAPHY
except ImportError:
    import os
    import sys
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.components import (
        NMCard,
        NMAvatar,
        NMButton,
        NMElidedLabel,
        NMToast,
        ThemeManager,
    )
    from shared.components.dialogs import NMDialog
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
        V3_SP,
    )
    from shared.qt_thread import run_on_gui
    from shared.theme import TYPOGRAPHY


def _detail_screen_qss(modo: str, *, bottom_edge: bool = False) -> str:
    surface = v3c("surface", modo).name()
    if not bottom_edge:
        return f"background-color: {surface};"
    border = v3c("borderSoft", modo).name()
    return (
        f"background-color: {surface};"
        f"border-bottom: 1px solid {border};"
    )


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
        self.setStyleSheet(
            f"#DetallePacienteView {{ background-color: {v3c('surface', self._modo).name()}; }}"
        )

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
        self._top_card = top
        top.setMinimumHeight(64)
        tl = QHBoxLayout(top)
        tl.setContentsMargins(18, 10, 18, 10)
        tl.setSpacing(14)

        initials = "".join(w[0] for w in (self._nombre or "?").split()[:2]).upper()
        # Mockup canónico hero del Hub Detalle (líneas 254-256): avatar 52×52 r15
        # (rounded square, no círculo). Antes: 40×40 círculo.
        self._avatar = NMAvatar(
            initials=initials or "P",
            size=52,
            radius=15,
            color_seed=self._pid or self._nombre,
            modo=self._modo,
        )
        tl.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._lbl_eyebrow = QLabel("Paciente".upper())
        self._lbl_eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        text_col.addWidget(self._lbl_eyebrow)

        # NMElidedLabel: a 960px el hero no tiene ancho para nombre + subtítulo
        # + 3 chips; los labels ceden con "…" en vez de empujar los chips a
        # geometrías bajo-mínimo (Qt los superpone físicamente en ese caso).
        self._lbl_name = NMElidedLabel(self._nombre)
        self._lbl_name.setFont(v3_font("size_h1", weight=600, serif=True))
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
        self._ia_row = ia_row
        ia_row.setContentsMargins(0, 4, 0, 0)
        ia_row.addStretch()
        self._btn_exportar_pdf = NMButton(
            "Exportar PDF", modo=self._modo,
            icon_name="download",  # mockup: primary filled, icono descarga
        )
        self._btn_exportar_pdf.clicked.connect(self._on_exportar_pdf)
        ia_row.addWidget(self._btn_exportar_pdf)
        self._btn_resumen_ia = NMButtonOutline(
            "Resumen IA", modo=self._modo,
            icon_name="sparkle",  # mockup: outline
        )
        self._btn_resumen_ia.clicked.connect(self._on_resumen_ia)
        ia_row.addWidget(self._btn_resumen_ia)
        chips_col.addLayout(ia_row)

        tl.addLayout(chips_col)
        self._top_wrap = QWidget()
        self._top_wrap.setStyleSheet(_detail_screen_qss(self._modo))
        top_lay = QVBoxLayout(self._top_wrap)
        top_lay.setContentsMargins(24, 24, 24, 8)
        top_lay.setSpacing(0)
        top_lay.addWidget(top)
        layout.addWidget(self._top_wrap)

        from hub.plan_terapeutico import PlanTerapeuticoTab

        self._tab_plan = PlanTerapeuticoTab(self._modo, self._sb, self._pid, self._nombre)
        self._plan_header_compact = False
        self._tab_plan._tabs.currentChanged.connect(self._sync_plan_header_density)
        self._sync_plan_header_density(self._tab_plan._tabs.currentIndex())

        self._plan_wrap = QWidget()
        self._plan_wrap.setStyleSheet(_detail_screen_qss(self._modo, bottom_edge=True))
        plan_lay = QVBoxLayout(self._plan_wrap)
        plan_lay.setContentsMargins(24, 0, 24, 0)
        plan_lay.setSpacing(0)
        plan_lay.addWidget(self._tab_plan)
        layout.addWidget(self._plan_wrap, stretch=1)

    def _sync_plan_header_density(self, index: int) -> None:
        compact = index == 3
        if compact == self._plan_header_compact:
            return
        self._plan_header_compact = compact
        if compact:
            self._top_card._padding_margins = (20, 15, 20, 15)
            self._top_card._lift_enabled = "dark" in self._modo
            self._ia_row.setContentsMargins(0, 0, 0, 0)
            self._btn_exportar_pdf.setFixedSize(144, 36)
            self._btn_resumen_ia.setFixedSize(132, 36)
        else:
            self._top_card._padding_margins = (20, 20, 20, 20)
            self._top_card._lift_enabled = True
            self._ia_row.setContentsMargins(0, 4, 0, 0)
            for btn in (self._btn_exportar_pdf, self._btn_resumen_ia):
                btn.setMinimumSize(0, 0)
                btn.setMaximumSize(16777215, 16777215)
        self._top_card._queue_padding_sync()
        self._top_card.updateGeometry()

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

        host = self.window() or self
        dialog = NMDialog("", modo=self._modo, width=560, parent=host)
        self._resumen_dialog = dialog
        dialog.closed.connect(lambda: setattr(self, "_resumen_dialog", None))
        dialog._title.hide()
        dialog._close_btn.hide()
        panel_lay = dialog._panel.layout()
        if panel_lay is not None:
            while panel_lay.count():
                panel_lay.takeAt(0)
            panel_lay.setContentsMargins(
                V3_SP["lg"], V3_SP["xs"], V3_SP["lg"], V3_SP["sm"]
            )
            panel_lay.setSpacing(V3_SP["xs"])

        # 2026-06-24: mockup Resumen IA — eyebrow UPPERCASE del nombre del
        # paciente sobre el título del diálogo. Antes era title-case en
        # color gris secundario sin uppercase.
        patient_lbl = QLabel(self._nombre.upper())
        patient_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        patient_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        panel_lay.addWidget(patient_lbl)

        title_lbl = QLabel("Resumen IA")
        title_lbl.setFont(v3_font(21, weight=600, serif=True))
        title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        panel_lay.addWidget(title_lbl)

        for paragraph in [p.strip() for p in (text or "").split("\n\n") if p.strip()]:
            lbl = QLabel(paragraph)
            lbl.setObjectName("ResumenIALabel")
            lbl.setWordWrap(True)
            lbl.setFont(qfont("size_body"))
            lbl.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; "
                "background: transparent; line-height: 1.6;"
            )
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            panel_lay.addWidget(lbl)
        panel_lay.addStretch(1)
        panel_lay.addLayout(dialog._footer_row)

        # 2026-06-24: mockup Resumen IA — botón "Cerrar" filled green (primary),
        # no ghost. Antes era texto estilo ghost.
        dialog.add_footer_button("Cerrar", role="primary", callback=dialog.close)
        dialog._panel.setFixedHeight(220)
        dialog.show_centered()

    def _on_resumen_ia_error(self, msg: str):
        self._btn_resumen_ia.setEnabled(True)
        self._btn_resumen_ia.setText("Resumen IA")
        NMToast.display(self.window(), f"IA no disponible: {msg[:40]}", variant="error")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(
            f"#DetallePacienteView {{ background-color: {v3c('surface', self._modo).name()}; }}"
        )
        if hasattr(self, "_top_wrap"):
            self._top_wrap.setStyleSheet(_detail_screen_qss(self._modo))
        if hasattr(self, "_plan_wrap"):
            self._plan_wrap.setStyleSheet(_detail_screen_qss(self._modo, bottom_edge=True))
        ink1 = v3c("text", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._lbl_eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._lbl_name.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._lbl_meta.setStyleSheet(f"color: {ink2}; background: transparent;")
