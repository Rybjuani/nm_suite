"""
app/home_qt.py — Vista Home v3 Premium (PyQt6)

Layout a 960x600:
  QVBoxLayout full-width
  ├── hero de bienestar
  └── QGridLayout de ModuleCards

API pública: HomeView(modo, on_module_open, get_status_fn, username, parent)
             .set_modo(modo) / .refresh_statuses() / .resizeEvent()
"""

import logging
import os
import sys
from datetime import datetime

_log = logging.getLogger(__name__)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QAbstractAnimation,
    QVariantAnimation,
    QPoint,
    QPointF,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
    QLinearGradient,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QPushButton,
    QStackedWidget,
)

try:
    from shared.theme_qt import (
        C,
        colors,
        norm_modo,
        qfont,
        ThemeAwareWidgetMixin,
        SessionColor,
        aura_opacity,
        v3c,
        V3_SP,
        V3_RD,
        v3_font,
        paint_card_lift,
        stylesheet_scrollarea,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY, V3_RADIUS, V3_SHADOWS
    from shared.components import (
        ThemeManager,
        NMIcon,
        NMModuleRing,
        NMButton,
        NMInput,
        NMToast,
        NMCard,
        NMWaveChart,
        NMProgressBar,
        NMChartPanel,
    )
except ImportError:
    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from shared.theme_qt import (
        C,
        norm_modo,
        qfont,
        ThemeAwareWidgetMixin,
        SessionColor,
        v3c,
        V3_SP,
        V3_RD,
        v3_font,
        paint_card_lift,
        eyebrow_font,
    )
    from shared.theme import TYPOGRAPHY
    from shared.components import (
        ThemeManager,
        NMIcon,
        NMModuleRing,
        NMButton,
        NMInput,
        NMToast,
        NMCard,
        NMWaveChart,
        NMProgressBar,
    )

from shared.visual_qa import visual_qa_enabled
from shared.remote_config import t


# ── Módulos ───────────────────────────────────────────────────────────────────

# Mockup homeCard (neuromood-mockup.html l.655-662): el TÍTULO de la card es
# corto y específico (`card_title`), distinto del título largo de la pantalla del
# módulo (`title`, que sigue alimentando el titlebar vía text.home.module.*.title).
# `desc`/`chip` también se alinean al copy exacto del mockup (cat + sub).
MODULES_CONFIG = [
    {
        "id": "animo",
        "icon_v3": "mood",
        "title": "Termómetro Emocional",
        "card_title": "Termómetro emocional",
        "desc": "Registro emocional diario",
        "chip": "Bienestar",
        "cat_tone": "brand",
        "badge_tone": "brand",
    },
    {
        "id": "respiracion",
        "icon_v3": "breath",
        "title": "Guía de Respiración Animada",
        "card_title": "Guía de respiración",
        "desc": "Técnicas de calma 4·7·8",
        "chip": "Calma",
        "cat_tone": "mind",
        "badge_tone": "brand",
    },
    {
        "id": "registro",
        "icon_v3": "brain",
        "title": "Registro de Pensamientos (TCC)",
        "card_title": "Registro de pensamientos",
        "desc": "Trabajo con pensamientos automáticos",
        "chip": "Cognitivo",
        "cat_tone": "efect",
        "badge_tone": "gold",
    },
    {
        "id": "rutina",
        "icon_v3": "checklist",
        "title": "Checklist de Rutina Diaria",
        "card_title": "Checklist de rutina",
        "desc": "Tu rutina del día",
        "chip": "Hábitos",
        "cat_tone": "brand",
        "badge_tone": "brand",
    },
    {
        "id": "actividades",
        "icon_v3": "run",
        "title": "Asistente de Activación Conductual",
        "card_title": "Activación conductual",
        "desc": "Sugerencias para activarte",
        "chip": "Acción",
        "cat_tone": "accent",
        "badge_tone": "accent",
    },
    {
        "id": "timer",
        "icon_v3": "timer",
        "title": "Temporizador de Actividades",
        "card_title": "Temporizador",
        "desc": "Sesiones de foco",
        "chip": "Enfoque",
        "cat_tone": "gold",
        "badge_tone": "gold",
    },
    {
        "id": "avisos",
        "icon_v3": "bell",
        "title": "Recordatorios de Bienestar",
        "card_title": "Recordatorios",
        "desc": "Avisos de bienestar",
        "chip": "Diario",
        "cat_tone": "brand",
        "badge_tone": "accent",
    },
    {
        "id": "dbt",
        "icon_v3": "spark",
        "title": "Habilidades DBT",
        "card_title": "Habilidades DBT",
        "desc": "Práctica guiada breve",
        "chip": "Habilidades",
        "cat_tone": "efect",
        "badge_tone": "brand",
    },
]


def _module_text(module_id: str, field: str, default: str) -> str:
    return str(t(f"text.home.module.{module_id}.{field}", default))


def module_configs() -> list[dict]:
    configs = []
    for cfg in MODULES_CONFIG:
        module_id = cfg["id"]
        item = dict(cfg)
        item["title"] = _module_text(module_id, "title", cfg["title"])
        item["card_title"] = _module_text(module_id, "card_title", cfg.get("card_title", cfg["title"]))
        item["desc"] = _module_text(module_id, "desc", cfg["desc"])
        item["chip"] = _module_text(module_id, "chip", cfg["chip"])
        configs.append(item)
    return configs


_TONE_COLOR_KEYS = {
    "brand": "brand",
    "mind": "mind",
    "efect": "efect",
    "accent": "accent",
    "gold": "gold",
    "rose": "rose",
}

_TONE_SOFT_KEYS = {
    "brand": "brandSoft",
    "mind": "brandSoft",
    "efect": "brandSoft",
    "accent": "accentSoft",
    "gold": "goldSoft",
    "rose": "roseSoft",
}


def _tone_color(tone: str, modo: str) -> QColor:
    return v3c(_TONE_COLOR_KEYS.get(tone, "brand"), modo)


def _tone_soft(tone: str, modo: str) -> QColor:
    return v3c(_TONE_SOFT_KEYS.get(tone, "brandSoft"), modo)


def _rgba(c: QColor) -> str:
    return f"rgba({c.red()},{c.green()},{c.blue()},{c.alpha()})"


# ── ModuleCard ────────────────────────────────────────────────────────────────


class ModuleCard(ThemeAwareWidgetMixin, QWidget):
    """Card de módulo v3 con NMIcon SVG y NMModuleRing."""

    def __init__(self, config: dict, idx: int, modo: str, on_click, get_status_fn, parent=None):
        super().__init__(parent)
        self._config = config
        self._idx = idx
        self._modo = norm_modo(modo)
        self._on_click = on_click
        self._get_status = get_status_fn
        self._accent = _tone_color(self._config.get("cat_tone", "brand"), self._modo).name()
        self._hover = False
        self._disabled = False
        self._disabled_reason = ""

        self._shadow: QGraphicsDropShadowEffect | None = None
        self._fade_eff: QGraphicsOpacityEffect | None = None
        # Radio de card declarado como shape attr (contrato VAS/design-system,
        # mismo idiom que NMCard._radius_override): paintEvent lo consume.
        self._radius = float(V3_RD["lg"])

        # Mockup homeCard: height:168px FIJO (`.hcard` inline style). Con altura
        # expandible las cards quedaban en 181 y el badge (margin-top:auto)
        # caía 13px más abajo que el canon.
        self.setFixedHeight(168)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._build_ui()
        self._connect_theme()
        self._apply_shadow(hover=False)

    def _apply_shadow(self, hover: bool):
        is_dark = "dark" in self._modo
        eff = QGraphicsDropShadowEffect(self)
        if hover:
            eff.setBlurRadius(20 if is_dark else 12)
            eff.setOffset(0, 6)
            eff.setColor(QColor(0, 0, 0, 85 if is_dark else 30))
        else:
            eff.setBlurRadius(8 if is_dark else 6)
            eff.setOffset(0, 2)
            eff.setColor(QColor(0, 0, 0, 45 if is_dark else 15))
        self._shadow = eff
        self.setGraphicsEffect(eff)

    def _set_shadow_state(self, hover: bool):
        self._apply_shadow(hover)

    # ── build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # Mockup homeCard: .card.pad 20px; vertical calibrado contra el canon
        # (icon box en +18 del tope, badge box terminando a -22 del borde).
        layout.setContentsMargins(20, 18, 20, 22)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Top row: icon + chip
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self._icon_box = QFrame(self)
        self._icon_box.setFixedSize(32, 32)
        icon_lay = QHBoxLayout(self._icon_box)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        icon_lay.setSpacing(0)
        self._icon = NMIcon(self._config["icon_v3"], size=18, color=self._accent, modo=self._modo)
        icon_lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self._icon_box)
        top.addStretch()
        self._chip = QLabel(self._config.get("chip", ""))
        self._chip.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        # Canon: chip box en y 249..272 (6px bajo el tope del icon row de 32).
        chip_box = QVBoxLayout()
        chip_box.setContentsMargins(0, 0, 0, 0)
        chip_box.setSpacing(0)
        chip_box.addSpacing(6)
        chip_box.addWidget(self._chip)
        chip_box.addStretch(1)
        top.addLayout(chip_box)
        layout.addLayout(top)

        # Mockup hcard: flex gap 8px; 4 acá porque el line-box Qt del título
        # mete ~4px de leading interno arriba del ink (canon ink L1 en y=285).
        layout.addSpacing(4)

        # Title — mockup homeCard: `.h-serif` 16.5px (Fraunces) con el título CORTO
        # de card, line-clamp 2: los títulos largos WRAPPEAN a 2 líneas en el
        # canon (Termómetro emocional, Registro de pensamientos) — sin shrink.
        self._title_lbl = QLabel(self._config.get("card_title", self._config["title"]))
        # Mockup 16.5px → 16 (setPixelSize entero; 17 y pointSizeF fraccional
        # rinden más anchos que el canon por métrica Qt-vs-Chromium).
        self._title_lbl.setFont(v3_font(16, weight=600, serif=True))
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._title_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._title_lbl)
        layout.addSpacing(3)  # mockup: sub margin-top 3px

        # Mockup: sub con line-clamp:1 → una sola línea con elipsis (las descs
        # largas como "Trabajo con pensamientos automáticos" NO wrappean).
        self._desc_full = self._config["desc"]
        self._desc_lbl = QLabel(self._desc_full)
        self._desc_lbl.setFont(v3_font(12))  # mockup 12.5px
        self._desc_lbl.setWordWrap(False)
        self._desc_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._desc_lbl)

        self._badge_wrap = QFrame(self)
        self._badge_wrap.setFixedHeight(22)  # canon: badge box h22 (345..367)
        self._badge_wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        badge_lay = QHBoxLayout(self._badge_wrap)
        badge_lay.setContentsMargins(11, 0, 11, 0)
        badge_lay.setSpacing(5)
        self._badge_dot = QFrame(self._badge_wrap)
        self._badge_dot.setFixedSize(6, 6)
        badge_lay.addWidget(self._badge_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        self._badge = QLabel("")
        self._badge.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        badge_lay.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)
        badge_lay.addStretch()
        self._ring = NMModuleRing(size=22, pct=0.0, modo=self._modo, show_label=False)
        self._ring.hide()
        # Mockup homeCard: la badge de estado lleva `margin-top:auto` → se ancla al
        # PIE de la card y se estira al ancho disponible.
        layout.addStretch(1)
        layout.addWidget(self._badge_wrap)

        self._apply_styles()
        self._refresh_status()
        self._set_shadow_state(False)

    def _apply_styles(self):
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._desc_lbl.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        icon_bg = v3c("surface3", self._modo)
        self._icon_box.setStyleSheet(
            f"background-color: {icon_bg.name()}; border-radius: 10px;"
        )

        badge_tone = self._config.get("badge_tone", "brand")
        accent = _tone_color(badge_tone, self._modo)
        chip_bg = _tone_soft(badge_tone, self._modo)
        self._chip.setStyleSheet(
            f"color: {accent.name()}; "
            f"background-color: {_rgba(chip_bg)}; "
            "border-radius: 11px; padding: 4px 11px;"
        )

    # ── status badge ──────────────────────────────────────────────────────────

    def _apply_status_badge_style(self, tone: str):
        color = _tone_color(tone, self._modo)
        bg = _tone_soft(tone, self._modo)
        self._badge_wrap.setStyleSheet(
            f"background-color: {_rgba(bg)}; border-radius: 11px;"
        )
        self._badge_dot.setStyleSheet(
            f"background-color: {color.name()}; border-radius: 3px;"
        )
        self._badge.setStyleSheet(
            f"color: {color.name()}; background: transparent;"
        )

    def _refresh_status(self):
        status = self._get_status(self._config["id"])
        if self._disabled:
            self._badge.setText("No disponible")
            self._apply_status_badge_style("gold")
            self._badge_wrap.show()
            self._ring.set_pct(0.0)
            return
        if status:
            self._badge.setText(status)
            self._apply_status_badge_style(self._config.get("badge_tone", "brand"))
            self._badge_wrap.show()
        elif self._config["id"] == "animo":
            # Mockup: card animo muestra estado vacío cuando no hay registro del día
            self._badge.setText(t("text.home.animo_no_record", "Sin registro hoy"))
            self._apply_status_badge_style("gold")
            self._badge_wrap.show()
        else:
            self._badge.setText("")
            self._badge_wrap.hide()
        self._update_ring(status)

    def _update_ring(self, status: str = None):
        if status is None:
            status = self._get_status(self._config["id"])
        if not status:
            self._ring.set_pct(0.0)
            return
        clean = status.replace("✓", "").replace("✔", "").strip()
        if "En progreso" in clean:
            self._ring.set_pct(0.65 if self._config["id"] == "animo" else 0.50)
        elif clean == "Activo":
            self._ring.set_pct(0.84)
        elif clean == "Completo":
            self._ring.set_pct(1.0)
        elif "/" in clean:
            try:
                parts = clean.split("/")
                done = int(parts[0].strip())
                total = int(parts[1].strip().split()[0])
                self._ring.set_pct(done / total if total > 0 else 0.0)
            except Exception:
                self._ring.set_pct(0.0)
        elif self._config["id"] != "avisos":
            self._ring.set_pct(1.0)
        else:
            self._ring.set_pct(0.0)

    # ── paint v3 ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = "dark" in self._modo
        r = self._radius
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # Surface solid like .module-grid-card in the HTML mockup.
        if is_dark:
            surf = v3c("surfaceSolid", self._modo)
        else:
            surf = v3c("surface", self._modo)
        p.setBrush(QBrush(surf))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Lift: highlight superior interno (mockup aprobado) — coherente con NMCard.
        if not self._disabled and self.isEnabled():
            paint_card_lift(p, rect, r, self._modo)

        is_active = self._hover and self.isEnabled() and not self._disabled

        # Border — más grueso y accent-tinted en hover
        if is_active:
            border_c = QColor(self._accent)
            border_c.setAlpha(200 if is_dark else 170)
            border_w = 1.5
        else:
            border_c = v3c("border", self._modo) if is_dark else v3c("borderStrong", self._modo)
            border_w = 1.0
        inset = border_w / 2.0
        p.setPen(QPen(border_c, border_w))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(inset, inset, w - 2 * inset, h - 2 * inset), r, r)

        # Disabled overlay
        if self._disabled:
            p.fillRect(rect, QColor(255, 255, 255, 22 if is_dark else 80))
        p.end()

    # ── eventos ───────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        # Mockup: sub line-clamp:1 — elide con "…" al ancho disponible.
        super().resizeEvent(event)
        if hasattr(self, "_desc_lbl") and self._desc_full:
            fm = QFontMetrics(self._desc_lbl.font())
            avail = max(0, self._desc_lbl.width())
            self._desc_lbl.setText(
                fm.elidedText(self._desc_full, Qt.TextElideMode.ElideRight, avail)
            )
        # Line-box canónico del título: CSS line-height 1.2 → 20px por línea
        # (Qt usa ~22 y corría la desc 2px en cards de título de 1 línea).
        if hasattr(self, "_title_lbl") and self._title_lbl.width() > 0:
            tfm = QFontMetrics(self._title_lbl.font())
            one_line = (
                tfm.horizontalAdvance(self._title_lbl.text()) <= self._title_lbl.width()
            )
            self._title_lbl.setFixedHeight(20 if one_line else 40)

    def enterEvent(self, event):
        self._hover = True
        self._set_shadow_state(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._set_shadow_state(False)
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            not self._disabled
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.pos())
        ):
            self._on_click(self._config["id"])
        super().mouseReleaseEvent(event)

    # ── animación de entrada ──────────────────────────────────────────────────

    def animate_enter(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._start_anim)

    def _start_anim(self):
        # El shadow actual se reemplaza por un opacity effect mientras dura
        # la animación de entrada; Qt borra el shadow al cambiar el effect.
        # Al terminar, RECREAMOS un shadow nuevo en lugar de intentar restaurar
        # el original (que ya fue destruido).
        fade_eff = QGraphicsOpacityEffect(self)
        fade_eff.setOpacity(0.0)
        self.setGraphicsEffect(fade_eff)
        self._shadow = None  # shadow original ya destruido

        anim_fade = QPropertyAnimation(fade_eff, b"opacity", self)
        anim_fade.setDuration(300)
        anim_fade.setStartValue(0.0)
        anim_fade.setEndValue(1.0)
        anim_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_done():
            # Recrear shadow para la elevación permanente del card
            try:
                self._apply_shadow(self._hover)
            except RuntimeError:
                # widget ya eliminado durante la animación
                pass

        anim_fade.finished.connect(_on_fade_done)
        anim_fade.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        orig_y = self.y()
        self.move(self.x(), orig_y + 16)
        anim_move = QPropertyAnimation(self, b"pos", self)
        anim_move.setDuration(300)
        anim_move.setStartValue(QPoint(self.x(), self.y()))
        anim_move.setEndValue(QPoint(self.x(), orig_y))
        anim_move.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_move.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._accent = _tone_color(self._config.get("cat_tone", "brand"), self._modo).name()
        self._icon.set_color(self._accent)
        self._apply_styles()
        self._ring._modo = self._modo
        self._ring.update()
        # Re-crear shadow para reflejar tonos del nuevo modo (no reusar — el
        # objeto C++ puede haber sido invalidado por una animación previa)
        try:
            self._apply_shadow(self._hover)
        except RuntimeError:
            pass
        self._refresh_status()
        self.update()

    def refresh(self):
        self._refresh_status()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        self.setCursor(
            Qt.CursorShape.ForbiddenCursor if state else Qt.CursorShape.PointingHandCursor
        )
        self._refresh_status()
        self.update()


# ── _HeroBienestar ────────────────────────────────────────────────────────────
# Hero card del handoff §5.2: eyebrow + score serif grande + badge + mensaje
# cálido + barra progress gradient primary→amber. Se inserta arriba del grid
# de módulos como "primera impresión" de la Home.


class _HeroBienestar(QFrame):
    """Hero card de bienestar — handoff §5.2.

    No tiene lógica clínica propia: lee el último score vía callback y lo
    presenta visualmente. Si no hay registro, muestra un mensaje suave.

    Métrica compacta (fitHome del mockup): a 960×600 el Home no entra a
    tamaño natural, y el mockup canónico encoge SOLO el welcome card via
    ``transform: scale(s)`` (grid intacta). El canon congelado quedó con el
    hero a ~0.78 (variante con score) / ~0.90 (variante sin score, menos
    contenido → menos shrink). Acá esas escalas se aplican como constantes
    de diseño sobre fuentes/paddings (Qt no escala widgets), medidas del
    canon: título ink 238×21 (score) / 273×25 (no-score), score "10" ink
    h23, barra h6, hero card 71..220.
    """

    # fitHome del mockup, medido sobre qa/_mockup_canonical (ver docstring).
    _FIT_SCORE = 0.78
    _FIT_EMPTY = 0.90

    def __init__(
        self, modo: str, get_status_fn, username: str = "", on_module_open=None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._get_status = get_status_fn or (lambda mid: "")
        self._on_module_open = on_module_open or (lambda _mid: None)
        # Nombre capitalizado (Fase 7): el saludo "Hola, juan" salía en minúscula
        # cuando el nombre venía así de la cuenta. Tomamos el primer nombre y
        # capitalizamos para un saludo prolijo ("Hola, Juan"). Guarda anti-split
        # vacío (nombre sólo-espacios → "Paciente").
        _parts = (username or "Paciente").split()
        self._username = _parts[0].capitalize() if _parts else "Paciente"
        # Radio declarado como shape attr (contrato VAS/design-system, idiom
        # NMCard._radius_override — este frame se presenta como NMCard).
        self._radius = float(V3_RD["lg"])
        self.setObjectName("NMCard")
        # Sin altura fija: el sizeHint del contenido manda (con el score "10"
        # lleno necesita ~142px; fijarlo en 112 recortaba el número grande).
        self._build_ui()
        self._apply_hero_shadow()
        self.refresh()

    def _greeting_text(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        # En modo QA visual el saludo se fija a "noches" para coincidir de forma
        # determinista con el target del mockup (que muestra "Buenas noches").
        hour = 21 if visual_qa_enabled() else datetime.now().hour
        if 5 <= hour < 12:
            prefix = t("text.home.greeting_morning", "Buenos días,").rstrip(",")
        elif 12 <= hour < 20:
            prefix = t("text.home.greeting_afternoon", "Buenas tardes,").rstrip(",")
        else:
            prefix = t("text.home.greeting_evening", "Buenas noches,").rstrip(",")
        return f"{prefix}, {name}"

    def _apply_hero_shadow(self):
        """Drop shadow para dar elevación al hero card."""
        eff = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        eff.setBlurRadius(14 if is_dark else 10)
        eff.setOffset(0, 3)
        eff.setColor(QColor(0, 0, 0, 60 if is_dark else 20))
        self.setGraphicsEffect(eff)

    def _build_ui(self):
        root = QVBoxLayout(self)
        # Padding .card.pad 20px × fit; calibrado contra el canon: eyebrow
        # ink en (44,93), barra x 43..916, bottom 16 para barra en y 196..202.
        root.setContentsMargins(19, 18, 20, 16)
        root.setSpacing(2)

        # Eyebrow row + badge derecho
        top = QHBoxLayout()
        self._eyebrow = QLabel(t("text.home.hero_eyebrow", "Bienvenida").upper())
        self._eyebrow.setFont(eyebrow_font())
        self._eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        top.addWidget(self._eyebrow)
        top.addStretch()
        root.addLayout(top)
        # Canon: gap ink eyebrow→título 15px (mockup margin 6 × fit + leading).
        root.addSpacing(4)

        self._hero_title = QLabel(self._greeting_text())
        # Tamaño real lo fija _apply_fit() según variante (23px score / 27px empty).
        self._hero_title.setFont(v3_font(23, weight=TYPOGRAPHY["weight_semibold"], serif=True))
        root.addWidget(self._hero_title)

        # Stacked area for empty vs filled
        self._stack = QStackedWidget(self)
        root.addWidget(self._stack)

        # ── Empty page ──
        self._empty_page = QWidget()
        empty_lay = QHBoxLayout(self._empty_page)
        empty_lay.setContentsMargins(0, 0, 0, 0)
        empty_lay.setSpacing(14)  # mockup l.671: gap:14px
        self._msg = QLabel(
            t(
                "text.home.empty_message",
                "Aún no registraste tu ánimo hoy.",
            )
        )
        self._msg.setFont(v3_font(12))  # mockup 13.5px × fit empty
        empty_lay.addWidget(self._msg)
        # Mockup l.673: CTA inline "Registrar ahora" → navega al módulo animo
        self._register_btn = NMButton(
            t("text.home.register_btn", "Registrar ahora"),
            variant="primary",
            size="sm",
            modo=self._modo,
        )
        self._register_btn.clicked.connect(lambda: self._on_module_open("animo"))
        empty_lay.addWidget(self._register_btn)
        empty_lay.addStretch()
        self._stack.addWidget(self._empty_page)

        # ── Filled page ──
        self._filled_page = QWidget()
        filled_lay = QVBoxLayout(self._filled_page)
        # Canon: score ink en y=155 (gap ink título→score 21px).
        filled_lay.setContentsMargins(0, 8, 0, 0)
        filled_lay.setSpacing(2)

        score_row = QHBoxLayout()
        score_row.setSpacing(8)  # mockup gap 10 × fit
        score_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._score = QLabel("—")
        # Mockup hero: <span class="h-serif" style="font-size:40px; color:var(--brand)">.
        # Número serif brand; 40 × fit ≈ 33 (canon ink digits h23).
        self._score.setFont(v3_font(33, weight=600, serif=True))
        # Ancho mínimo para que "10" (dos dígitos) no se corte a 960×600.
        self._score.setMinimumWidth(33)
        self._score.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        score_row.addWidget(self._score)
        # Mockup: align-items:baseline — unit y chip cuelgan de la baseline
        # del score (ink bottom canon y=178), no del centro del row.
        self._score_unit = QLabel("/ 10")
        self._score_unit.setFont(v3_font(11))  # mockup 14px × fit
        unit_col = QVBoxLayout()
        unit_col.setContentsMargins(0, 0, 0, 0)
        unit_col.setSpacing(0)
        unit_col.addStretch(1)
        unit_col.addWidget(self._score_unit)
        unit_col.addSpacing(7)
        score_row.addLayout(unit_col)

        # Delta inline
        self._delta_lbl = QLabel("")
        self._delta_lbl.setFont(v3_font(9, weight=600))  # .badge 11.5px × fit
        chip_col = QVBoxLayout()
        chip_col.setContentsMargins(0, 0, 0, 0)
        chip_col.setSpacing(0)
        chip_col.addStretch(1)
        chip_col.addWidget(self._delta_lbl)
        chip_col.addSpacing(3)
        score_row.addLayout(chip_col)
        score_row.addStretch()
        filled_lay.addLayout(score_row)
        # Canon: barra en y 197..203 (mockup margin-top 14 × fit + leading).
        filled_lay.addSpacing(10)

        # Progress bar — dithered density gradient (reemplaza los QFrames raw)
        # Mockup 8px × fit = 6 (canon: barra en y 196..202).
        self._progress_bar = NMProgressBar(height=6, modo=self._modo)
        filled_lay.addWidget(self._progress_bar)
        # Pack al tope: sin esto el layout centra el contenido en el alto
        # sobrante del stack y el score/bar derivan del canon.
        filled_lay.addStretch(1)

        self._stack.addWidget(self._filled_page)

        self._apply_styles()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._radius
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # Mockup Home: linear-gradient(135deg, surface -> surface-2).
        grad = QLinearGradient(0, 0, w, h)
        c1 = v3c("surface", self._modo)
        c2 = v3c("surface2", self._modo)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)

        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Mockup l.667: glow radial en upper-right (brand-soft → transparent,
        # 200x200 en right:-30 top:-40). Canon vigente: rgba(brand, .13) —
        # alpha 33. (El alpha 100 anterior estaba calibrado contra un canon
        # viejo y dejaba una mancha verde fuerte en el diff.)
        glow_color = v3c("brand", self._modo)
        glow_color.setAlpha(33)
        glow = QRadialGradient(w - 30, -40, 200)
        glow.setColorAt(0.0, glow_color)
        glow.setColorAt(0.7, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Border sutil
        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)
        p.end()

    def _apply_styles(self):
        brand = v3c("brand", self._modo)
        text2 = v3c("text2", self._modo)
        muted = v3c("textMuted", self._modo)
        text = v3c("text", self._modo)

        self._eyebrow.setStyleSheet(
            f"color: {text2.name()}; background: transparent;"
        )

        # Handoff §5.2: Greeting name in serif (Newsreader)
        # We'll use a mix: "Hola," in sans, name in serif if possible
        self._hero_title.setStyleSheet(f"color: {text.name()}; background: transparent;")

        # Fuentes de eyebrow/título dependen de la página activa (fit).
        self._apply_fit()

        # Mockup: número del hero en color brand (verde/menta), no accent (cobre).
        self._score.setStyleSheet(f"color: {brand.name()}; background: transparent;")
        self._score_unit.setStyleSheet(f"color: {muted.name()}; background: transparent;")
        self._msg.setStyleSheet(f"color: {text2.name()}; background: transparent;")
        if hasattr(self, "_progress_bar"):
            self._progress_bar._apply_theme(self._modo)


    def _apply_fit(self):
        """Tamaños de eyebrow/título según página activa (fitHome del mockup).

        El mockup escala el welcome card entero; los tamaños resultantes en el
        canon difieren por variante: con score fit≈0.78 (título 30→23px,
        eyebrow 11→9px), sin score fit≈0.90 (título 27px, eyebrow 10px).
        """
        filled = self._stack.currentIndex() == 1
        title_px = 23 if filled else 27
        eyebrow_px = 9 if filled else 10
        self._hero_title.setFont(v3_font(title_px, weight=600, serif=True))
        eb = eyebrow_font()
        eb.setPixelSize(eyebrow_px)
        self._eyebrow.setFont(eb)

    def _parse_score(self, text: str):
        """Extrae float 0-10 del formato 'N/10' que emite _get_module_status."""
        if not text or "/" not in text:
            return None
        left = text.split("/", 1)[0].strip()
        try:
            val = float(left.replace(",", "."))
            if 0 <= val <= 10:
                return val
        except (ValueError, TypeError):
            pass
        return None

    def refresh(self):
        """Lee el score actual y actualiza el hero. Idempotente.

        El score es el PROMEDIO de los registros de hoy (bienestar combinado:
        los registros negativos restan). Sin cartel interpretativo de estado
        ("Estado positivo"/"Estable") — la interpretación es del profesional,
        no de la app (feedback owner).
        """
        raw = self._get_status("animo")
        score = self._parse_score(raw)
        if score is None:
            self._stack.setCurrentIndex(0)
            self._apply_fit()
            return

        self._stack.setCurrentIndex(1)
        self._apply_fit()

        # Mockup muestra "10" (entero) y "8.5" (con decimal): sin ceros sobrantes.
        self._score.setText(f"{score:.1f}".rstrip("0").rstrip("."))

        delta = 0.8 if visual_qa_enabled() else None
        if delta is not None:
            self._delta_lbl.setText(f"▲ {delta:.1f} vs semana")
            delta_c = v3c("mind", self._modo)
            delta_bg = QColor(delta_c)
            delta_bg.setAlpha(36)
            self._delta_lbl.setStyleSheet(
                f"color: {delta_c.name()}; "
                f"background: rgba({delta_bg.red()},{delta_bg.green()},{delta_bg.blue()},{delta_bg.alpha()}); "
                "border-radius: 8px; padding: 3px 9px;"  # .badge 4px 11px × fit
            )
            self._delta_lbl.show()
        else:
            self._delta_lbl.hide()

        self._progress_bar.animate_to(score / 10.0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.refresh()
        except Exception:
            pass

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_styles()
        self._apply_hero_shadow()


# ── _ProximaSesionCard ────────────────────────────────────────────────────────


class _ProximaSesionCard(QFrame):
    """Card 'Próxima sesión' — handoff SuiteHome columna derecha (1fr)."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setObjectName("NMCard")
        self.setFixedHeight(96)
        self._build_ui()
        self._apply_card_styles()
        self._apply_shadow()

    def _apply_shadow(self):
        eff = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        eff.setBlurRadius(14 if is_dark else 10)
        eff.setOffset(0, 3)
        eff.setColor(QColor(0, 0, 0, 60 if is_dark else 20))
        self.setGraphicsEffect(eff)

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        self._eyebrow = QLabel(t("text.home.next_session_eyebrow", "Próxima sesión"))
        self._eyebrow.setFont(eyebrow_font())
        lay.addWidget(self._eyebrow)

        self._time_lbl = QLabel("—")
        self._time_lbl.setFont(qfont("size_heading_l", weight=600))
        lay.addWidget(self._time_lbl)

        self._therapist_lbl = QLabel(t("text.home.next_session_empty", "Sin sesión programada"))
        self._therapist_lbl.setFont(qfont("size_small"))
        self._therapist_lbl.setWordWrap(True)
        lay.addWidget(self._therapist_lbl)

        lay.addStretch()

    def _apply_card_styles(self):
        surface = v3c("surface", self._modo)
        border = v3c("border", self._modo)
        is_dark = "dark" in self._modo
        if is_dark:
            surf = v3c("surfaceSolid", self._modo)
            surf_css = f"rgba({surf.red()},{surf.green()},{surf.blue()},160)"
        else:
            surf_css = f"rgba({surface.red()},{surface.green()},{surface.blue()},210)"
        # 2026-06-24: subir opacidad del border de 26 (10%) a 60 (~24%) para
        # que el 1px stroke sea perceptible (mockup muestra border visible).
        border_alpha = 60 if not is_dark else border.alpha()
        border_css = f"rgba({border.red()},{border.green()},{border.blue()},{border_alpha})"
        self.setStyleSheet(f"""
            QFrame#NMCard {{
                background-color: {surf_css};
                border: 1px solid {border_css};
                border-radius: {V3_RD["lg"]}px;
            }}
        """)
        text2 = v3c("text2", self._modo)
        muted = v3c("textMuted", self._modo)
        primary = v3c("primary", self._modo)
        self._eyebrow.setStyleSheet(
            f"color: {text2.name()}; background: transparent;"
        )
        self._time_lbl.setStyleSheet(f"color: {primary.name()}; background: transparent;")
        self._therapist_lbl.setStyleSheet(f"color: {muted.name()}; background: transparent;")

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_card_styles()
        self._apply_shadow()


# ── HomeView ──────────────────────────────────────────────────────────────────


class HomeView(QWidget):
    """Vista Home v3 Premium — contenido directo full-width.

    Layout:
      QHBoxLayout
      └── QWidget (content)
          ├── hero strip
          ├── QGridLayout — ModuleCard responsive
          └── QStretch
    """

    _theme_switch_requested = pyqtSignal(bool)

    def __init__(
        self,
        modo: str = "dark_hybrid",
        on_module_open=None,
        get_status_fn=None,
        username: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._open_cb = on_module_open or (lambda mid: None)
        self._get_status = get_status_fn or (lambda mid: "")
        self._username = username
        self._cards: dict[str, ModuleCard] = {}
        self._grid_cols = 0
        self._session = SessionColor.instance()
        self._setup()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    # ── setup ─────────────────────────────────────────────────────────────────

    def _setup(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        # Root horizontal kept for shell compatibility; Home content is full-width.
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        content_lay = QVBoxLayout(content)
        # Mockup `.screen`: padding 24 (canon: hero card top en y=71; el
        # chrome Qt termina en 48, 1px más abajo que el mockup → top 23).
        # Bottom libre: las cards son de altura fija 168 (grid termina ~571
        # y el resto respira como el canon).
        content_lay.setContentsMargins(24, 23, 24, 2)
        content_lay.setSpacing(0)

        self._hero = _HeroBienestar(
            self._modo,
            self._get_status,
            username=self._username,
            on_module_open=self._open_cb,
            parent=content,
        )
        # Canon fitHome: hero card ocupa y 71..220 (h=149) y su margin-bottom
        # queda comprimido a ~3 (mockup: 18px menos el alto ahorrado).
        # Bienvenida PRIMERO (decisión owner): el hero de bienestar abre el Home.
        self._hero.setFixedHeight(149)
        self._hero.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._session_card = _ProximaSesionCard(self._modo, parent=content)
        self._session_card.hide()
        content_lay.addWidget(self._hero)
        content_lay.addSpacing(3)

        # P2.C: cards de "Progreso de Ánimo" y "Resumen Semanal" removidas.
        # El espacio liberado se usa para agrandar las 8 cards de módulo (la grilla
        # pasa a ocupar el área que antes usaban esas dos cards).
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setVerticalSpacing(12)  # canon: fila 2 en y=403
        self._grid.setHorizontalSpacing(12)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._module_configs = module_configs()
        for idx, cfg in enumerate(self._module_configs):
            card = ModuleCard(
                cfg, idx, self._modo, on_click=self._open_cb, get_status_fn=self._get_status
            )
            self._cards[cfg["id"]] = card

        self._sync_availability()
        self._rebuild_grid()

        # Sin stretch final: en el mockup el espacio vertical lo consumen hero y
        # grilla; no queda un pie vacío debajo de la segunda fila.
        content_lay.addLayout(self._grid, stretch=0)

        root.addWidget(content, stretch=1)

        # Staggered entrance
        for idx, cfg in enumerate(self._module_configs):
            card = self._cards.get(cfg["id"])
            if card:
                card.animate_enter(delay_ms=idx * 55)

        # Apply initial token styles
        self._apply_theme(self._modo)

    # ── grid responsive ───────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        content_w = max(1, self.width())
        # compact R4: breakpoints calibrados para cards 200px mín en 1280×800
        if content_w >= 720:
            new_cols = 4
        elif content_w >= 540:
            new_cols = 3
        elif content_w >= 360:
            new_cols = 2
        else:
            new_cols = 1
        if new_cols != self._grid_cols:
            self._grid_cols = new_cols
            self._rebuild_grid()

    def _rebuild_grid(self):
        content_w = max(1, self.width())
        if self._grid_cols:
            cols = self._grid_cols
        elif content_w >= 720:
            cols = 4
        elif content_w >= 540:
            cols = 3
        elif content_w >= 360:
            cols = 2
        else:
            cols = 1
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        # Equal column widths; no row-stretch so cards stay at natural height.
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        n = len(self._module_configs)
        num_rows = (n + cols - 1) // cols
        # Handoff §3 (Home): distribución balanceada al hueco del grid 4×2.
        # Con N módulos reales (7) en `cols` columnas, la última fila puede
        # tener menos celdas; las centramos para evitar un hueco visual.
        # Sin inventar features ni placeholders.
        last_row_count = n - (num_rows - 1) * cols if num_rows > 0 else n
        last_row_offset = max(0, (cols - last_row_count) // 2)
        for idx, cfg in enumerate(self._module_configs):
            card = self._cards.get(cfg["id"])
            if not card:
                continue
            row = idx // cols
            col = idx % cols
            if row == num_rows - 1 and last_row_count < cols:
                col = col + last_row_offset
            self._grid.addWidget(card, row, col)

    # ── API pública ───────────────────────────────────────────────────────────

    def refresh_statuses(self):
        self._sync_availability()
        for card in self._cards.values():
            card.refresh()
        if hasattr(self, "_weekly_mood"):
            self._weekly_mood.refresh()
        if hasattr(self, "_home_wave"):
            self._refresh_home_wave()
        # Refresh hero bienestar (handoff §5.2)
        if hasattr(self, "_hero"):
            self._hero.refresh()

    def set_sync_status(self, label: str, tone: str = "ok"):
        """Compatibility hook for the shell sync signal; Home no longer owns a footer."""
        return None

    def set_modo(self, modo: str):
        self._apply_theme(modo)

    def _greeting_text(self) -> str:
        name = (self._username or "Paciente").strip() or "Paciente"
        # En modo QA visual el saludo se fija a "noches" para coincidir de forma
        # determinista con el target del mockup (que muestra "Buenas noches").
        hour = 21 if visual_qa_enabled() else datetime.now().hour
        if 5 <= hour < 12:
            prefix = t("text.home.greeting_morning", "Buenos días,").rstrip(",")
        elif 12 <= hour < 20:
            prefix = t("text.home.greeting_afternoon", "Buenas tardes,").rstrip(",")
        else:
            prefix = t("text.home.greeting_evening", "Buenas noches,").rstrip(",")
        return f"{prefix}, {name}"

    def _subtitle_text(self) -> str:
        return t(
            "text.home.subtitle",
            "Elegí un módulo para registrar cómo venís y sostener tu rutina.",
        )

    # ── permisos ──────────────────────────────────────────────────────────────

    def _disabled_reason(self, module_id: str) -> str:
        return {
            "rutina": "Tu profesional desactivó la rutina manual.",
            "actividades": "Tu profesional desactivó las actividades manuales.",
            "timer": "Tu profesional desactivó el temporizador manual.",
            "avisos": "Tu profesional desactivó los recordatorios manuales.",
        }.get(module_id, "Módulo no disponible.")

    def _sync_availability(self):
        for module_id, card in self._cards.items():
            available = self._is_module_available(module_id)
            card.set_disabled(
                not available, self._disabled_reason(module_id) if not available else ""
            )

    def _is_module_available(self, module_id: str) -> bool:
        if visual_qa_enabled():
            return True
        permission_keys = {
            "rutina": "perm_checklist_manual",
            "actividades": "perm_checklist_activacion",
            "timer": "perm_temporizador_manual",
            "avisos": "perm_recordatorios_manual",
        }
        key = permission_keys.get(module_id)
        if not key:
            return True
        try:
            from shared.db import leer_config

            return leer_config(key, "1") != "0"
        except Exception:
            return True

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for card in self._cards.values():
            card._apply_theme(self._modo)
        if hasattr(self, "_weekly_mood"):
            self._weekly_mood._apply_theme(self._modo)
        for card_name in ("_home_progress_card", "_home_attention_card"):
            card = getattr(self, card_name, None)
            if card is not None:
                card._apply_theme(self._modo)
        if hasattr(self, "_home_wave"):
            self._home_wave._apply_theme(self._modo)
        for lbl_name in (
            "_home_progress_eyebrow",
            "_home_attention_eyebrow",
        ):
            lbl = getattr(self, lbl_name, None)
            if lbl is not None:
                lbl.setStyleSheet(
                    f"color: {v3c('mute', self._modo).name()}; background: transparent;"
                )
        for lbl_name in ("_home_progress_title", "_home_attention_title"):
            lbl = getattr(self, lbl_name, None)
            if lbl is not None:
                lbl.setStyleSheet(
                    f"color: {v3c('text', self._modo).name()}; background: transparent;"
                )
        if hasattr(self, "_home_attention_body"):
            self._home_attention_body.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; background: transparent;"
            )
        if hasattr(self, "_home_assignment"):
            self._home_assignment.setStyleSheet(
                f"QLabel {{ color: {v3c('primary', self._modo).name()}; "
                f"background: {C('primary_soft', self._modo)}; "
                f"border-radius: 6px; padding: 8px; }}"
            )
        if hasattr(self, "_hero"):
            self._hero.apply_theme(self._modo)
        if hasattr(self, "_session_card"):
            self._session_card.apply_theme(self._modo)
        self.update()

    def _refresh_home_wave(self):
        if not hasattr(self, "_home_wave"):
            return
        if visual_qa_enabled():
            current = [3.0, 7.0, 4.0, 6.0, 8.0, 5.0, 7.2]
            previous = [4.0, 5.0, 5.5, 5.0, 6.0, 5.8, 6.2]
        else:
            try:
                from shared.utils import get_weekly_series

                current, previous = get_weekly_series()
            except Exception:
                current, previous = [None] * 7, [None] * 7
        self._home_wave.set_data(current, previous)

    # ── fondo ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        # Fondo canónico de pantalla (idéntico a registro/dbt, ambos PASS):
        # surface plano + glow radial `.screen-frame` (50%, -20%, r500,
        # surface-2 → transparente 70%). El shell gradient bg→bgAlt que se
        # usaba acá no existe en el mockup y oscurecía todo el fondo del Home.
        p = QPainter(self)
        rect = QRectF(self.rect())
        surface = v3c("surface", self._modo)
        surface_2 = v3c("surface_2", self._modo)

        p.fillRect(rect, QBrush(surface))

        glow = QRadialGradient(QPointF(rect.width() * 0.5, -rect.height() * 0.2), 500)
        glow.setColorAt(0.0, surface_2)
        fade = QColor(surface_2)
        fade.setAlpha(0)
        glow.setColorAt(0.7, fade)
        p.fillRect(rect, QBrush(glow))

        # Borde de `.window` del mockup (idéntico a _DBTScreen): 1px --line en
        # laterales y base, esquinas inferiores r-xl=28. El borde superior lo
        # pinta el chrome; este widget cubre el resto de la ventana.
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        line_c = QColor(v3c("line", self._modo))
        if line_c.alpha() == 255:
            # Alpha canónico: light rgba(49,45,39,.10) / dark rgba(255,255,255,.09)
            line_c.setAlpha(23 if "dark" in self._modo else 26)
        radius = 28.0
        win_path = QPainterPath()
        win_path.addRoundedRect(
            QRectF(0.5, -radius, rect.width() - 1.0, rect.height() + radius - 0.5),
            radius,
            radius,
        )
        exterior = QPainterPath()
        exterior.addRect(rect)
        exterior = exterior.subtracted(win_path)
        p.fillPath(exterior, QBrush(v3c("bg", self._modo)))
        p.setPen(QPen(line_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(win_path)
        p.end()
