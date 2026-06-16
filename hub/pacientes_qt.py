"""
hub/pacientes_qt.py — Vista detallada de paciente (PyQt6)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

try:
    from shared.components import (
        NMCard,
        NMAvatar,
        NMBadge,
        NMElidedLabel,
        ThemeManager,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
    )
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
        NMBadge,
        NMElidedLabel,
        ThemeManager,
    )
    from shared.theme_qt import (
        norm_modo,
        qfont,
        v3_font,
        v3c,
    )
    from shared.theme import TYPOGRAPHY

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

        chips_col = QVBoxLayout()
        chips_col.setContentsMargins(0, 0, 0, 0)
        chips_col.setSpacing(6)

        self._chip_row = QHBoxLayout()
        self._chip_row.setContentsMargins(0, 0, 0, 0)
        self._chip_row.setSpacing(10)
        # Si el hero se queda sin ancho, los chips NO deben comprimirse unos
        # contra otros: el stretch inicial absorbe y los empuja a la derecha.
        self._chip_row.addStretch()
        # 5.1: lenguaje neutral — "Riesgo bajo" afirma una verdad clínica que el
        # demo no valida. "Sin alerta activa" describe el estado de la app
        # (no se generaron alertas), no diagnostica al paciente. "5d racha"
        # se mantiene como señal operativa (cuántos días lleva registrando),
        # no como juicio clínico.
        self._chip_semana = NMBadge("Semana 12", tone="patient", modo=self._modo)
        self._chip_riesgo = NMBadge("Sin alerta activa", tone="neutral", modo=self._modo)
        # "racha" no se usa en Argentina (feedback owner) → "progreso".
        self._chip_racha = NMBadge("Progreso 5d", tone="completed", modo=self._modo)
        self._chip_row.addWidget(self._chip_semana)
        self._chip_row.addWidget(self._chip_riesgo)
        self._chip_row.addWidget(self._chip_racha)
        chips_col.addLayout(self._chip_row)
        # ("Vista activa en NeuroMood Hub" eliminado: redundante y ocupaba
        # espacio — informe owner v1.0, detalle de paciente.)

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

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("background: transparent;")
        ink1 = v3c("text", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._lbl_eyebrow.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._lbl_name.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._lbl_meta.setStyleSheet(f"color: {ink2}; background: transparent;")
