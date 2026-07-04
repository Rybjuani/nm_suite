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
    QGridLayout,
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
        NMIcon,
        NMToast,
        ThemeManager,
    )
    from shared.components.dialogs import NMDialog
    from shared.theme_qt import (
        norm_modo,
        qfont,
        qcolor_to_rgba_css,
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
        NMIcon,
        NMToast,
        ThemeManager,
    )
    from shared.components.dialogs import NMDialog
    from shared.theme_qt import (
        norm_modo,
        qfont,
        qcolor_to_rgba_css,
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
        dialog = NMDialog("", modo=self._modo, width=720, parent=host)
        dialog._backdrop_fill_bottom_px = 18
        if "dark" not in self._modo:
            dialog._blur_radius_override = 5
        self._resumen_dialog = dialog
        dialog.closed.connect(lambda: setattr(self, "_resumen_dialog", None))
        dialog._title.hide()
        dialog._close_btn.hide()
        panel_lay = dialog._panel.layout()
        if panel_lay is not None:
            while panel_lay.count():
                item = panel_lay.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
            panel_lay.setContentsMargins(0, 0, 0, 0)
            panel_lay.setSpacing(0)

        surface_q = v3c("surfaceSolid" if "dark" in self._modo else "surface", self._modo)
        surface2_q = v3c("surface_2", self._modo)
        brand_q = v3c("brand", self._modo)
        surface = surface_q.name()
        surface2 = surface2_q.name()
        line = qcolor_to_rgba_css(v3c("line", self._modo))
        text_col = v3c("text", self._modo).name()
        ink2 = v3c("ink_2", self._modo).name()
        ink3 = v3c("ink_3", self._modo).name()
        brand = brand_q.name()
        brand_soft = qcolor_to_rgba_css(v3c("brandSoft", self._modo))
        amber = v3c("amber", self._modo).name()

        def _mix_rgb(base, accent, accent_ratio: float) -> str:
            base_ratio = 1.0 - accent_ratio
            return (
                f"rgb({round(base.red() * base_ratio + accent.red() * accent_ratio)}, "
                f"{round(base.green() * base_ratio + accent.green() * accent_ratio)}, "
                f"{round(base.blue() * base_ratio + accent.blue() * accent_ratio)})"
            )

        panel_top = _mix_rgb(surface_q, brand_q, 0.06)
        footer_bg = f"rgba({surface2_q.red()}, {surface2_q.green()}, {surface2_q.blue()}, 128)"
        dialog._panel.setFixedHeight(462)
        dialog._panel.setStyleSheet(
            f"QFrame#NMDialogPanel {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {panel_top}, stop:0.38 {surface}, stop:1 {surface}); border: 1px solid {line}; "
            "border-radius: 24px; }}"
        )

        def _label(value: str, font, color: str, *, name: str = "", wrap: bool = False) -> QLabel:
            lbl = QLabel(value)
            if name:
                lbl.setObjectName(name)
            font.setWordSpacing(0.0)
            lbl.setFont(font)
            lbl.setWordWrap(wrap)
            lbl.setStyleSheet(f"color: {color}; background: transparent; border: none; padding: 0px; margin: 0px;")
            return lbl

        header = QFrame()
        header.setObjectName("ResumenIAHeader")
        header.setFixedHeight(86)
        header.setStyleSheet(f"QFrame#ResumenIAHeader {{ border-bottom: 1px solid {line}; background: transparent; }}")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(22, 18, 22, 14)
        header_lay.setSpacing(14)

        avatar = QFrame()
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet(f"QFrame {{ background: {brand_soft}; border: none; border-radius: 12px; }}")
        avatar_lay = QVBoxLayout(avatar)
        avatar_lay.setContentsMargins(0, 0, 0, 0)
        avatar_lay.addWidget(NMIcon("spark", 18, color_key="brand", modo=self._modo), alignment=Qt.AlignmentFlag.AlignCenter)
        header_lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(_label("RESUMEN CLÍNICO · BORRADOR IA", qfont("size_caption_xs", weight=600), ink3))
        titles.addWidget(_label(self._nombre, v3_font(18, weight=600, serif=True), text_col))
        titles.addWidget(_label("Ventana 30 días  ·  14 registros analizados  ·  Generado 01-jul", qfont("size_caption_xs"), ink3))
        header_lay.addLayout(titles, stretch=1)

        close_btn = NMButton("Cerrar", modo=self._modo, width=84, height=40, variant="gradient", size="md")
        close_btn.clicked.connect(dialog.close)
        header_lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        panel_lay.addWidget(header)

        chips = QFrame()
        chips.setStyleSheet("background: transparent;")
        chips_lay = QGridLayout(chips)
        chips_lay.setContentsMargins(22, 14, 22, 4)
        chips_lay.setHorizontalSpacing(8)
        chips_lay.setVerticalSpacing(0)

        for idx, (value, suffix, label) in enumerate([
            ("6.4", "/10", "ÁNIMO PROM."),
            ("9", "", "REGISTROS TCC"),
            ("3", "", "SESIONES RESPIR."),
            ("71", "%", "ADHERENCIA"),
        ]):
            chip = QFrame()
            chip.setFixedHeight(53)
            chip.setStyleSheet(
                f"QFrame {{ background: {surface2}; border: 1px solid {line}; border-radius: 12px; }}"
            )
            chip_lay = QVBoxLayout(chip)
            chip_lay.setContentsMargins(10, 8, 10, 7)
            chip_lay.setSpacing(3)
            val_row = QHBoxLayout()
            val_row.setContentsMargins(0, 0, 0, 0)
            val_row.setSpacing(1)
            val = _label(value, qfont("size_body", weight=700), brand)
            val_row.addWidget(val, alignment=Qt.AlignmentFlag.AlignBaseline)
            if suffix:
                suff = _label(suffix, qfont("size_caption_xs", weight=700), brand)
                val_row.addWidget(suff, alignment=Qt.AlignmentFlag.AlignBaseline)
            val_row.addStretch()
            lab = _label(label, qfont("size_caption_xs", weight=700), ink3)
            chip_lay.addLayout(val_row)
            chip_lay.addWidget(lab)
            chips_lay.addWidget(chip, 0, idx)
        panel_lay.addWidget(chips)

        body = QFrame()
        body.setFixedHeight(246)
        body.setStyleSheet("background: transparent;")
        body_content = QFrame(body)
        body_content.setGeometry(22, 6, 676, 304)
        body_content.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body_content)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        default_general = (
            "Ánimo promedio en rango medio-alto (6.4/10) con oscilación moderada. "
            "Tres registros TCC refieren ansiedad anticipatoria vinculada a situaciones sociales."
        )
        general_text = " ".join(p.strip() for p in (text or "").splitlines() if p.strip()) or default_general
        sections = [
            ("user", "ESTADO GENERAL", general_text),
            ("check", "ADHERENCIA Y HÁBITOS", "Cumplimiento del 71% en registro diario de ánimo y 4/7 tareas de rutina completadas. Práctica de respiración 4·7·8 esporádica (3 sesiones en el período)."),
            ("bolt", "ASPECTOS A MONITOREAR", "Distorsión cognitiva recurrente: catastrofización (5/9 registros). Descenso de ánimo los días con menor adherencia a la rutina matutina."),
            ("spark", "RECOMENDACIÓN DE SESIÓN", "Reforzar restructuración cognitiva sobre catastrofización y vincular activación conductual matutina. Considerar asignar habilidad DBT \"Verificar los hechos\"."),
        ]
        body_ink = ink2 if "dark" in self._modo else "rgba(107, 100, 87, 0)"
        body_font = qfont("size_caption") if "dark" in self._modo else qfont(10)
        for icon_name, title, body_text in sections:
            sec = QFrame()
            sec.setFixedHeight(76)
            sec.setStyleSheet(f"QFrame {{ border-bottom: 1px dashed {line}; background: transparent; }}")
            sec_lay = QVBoxLayout(sec)
            sec_lay.setContentsMargins(0, 3, 0, 9)
            sec_lay.setSpacing(0)
            head = QHBoxLayout()
            head.setSpacing(7)
            head.addWidget(NMIcon(icon_name, 14, color_key="brand", modo=self._modo))
            head.addWidget(_label(title, qfont("size_caption_xs", weight=700), ink2), stretch=1)
            sec_lay.addLayout(head)
            body_lbl = _label(body_text, body_font, body_ink, name="ResumenIALabel", wrap=True)
            body_lbl.setContentsMargins(21, 0, 0, 0)
            body_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            sec_lay.addWidget(body_lbl)
            body_lay.addWidget(sec)
        panel_lay.addWidget(body)

        footer = QFrame()
        footer.setFixedHeight(56)
        footer.setStyleSheet(f"QFrame {{ background: {footer_bg}; border-top: 1px solid {line}; }}")
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(22, 12, 22, 14)
        footer_lay.setSpacing(6)
        footer_lay.addWidget(NMIcon("info", 12, color=amber, modo=self._modo), alignment=Qt.AlignmentFlag.AlignTop)
        footer_ink = ink3 if "dark" in self._modo else "rgba(136, 136, 136, 96)"
        warn = _label(
            "Borrador para revisión profesional. La IA no sustituye el criterio clínico ni realiza diagnósticos. Validar contra historia clínica antes de citar.",
            qfont("size_caption_xs"),
            footer_ink,
            wrap=True,
        )
        footer_lay.addWidget(warn, stretch=1)
        panel_lay.addWidget(footer)
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
