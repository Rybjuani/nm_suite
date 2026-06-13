"""
shared/components_qt.py
Biblioteca de componentes UI PyQt6 para NeuroMood V3.

Cada componente implementa apply_theme(modo) y se conecta
automáticamente al singleton ThemeManager al instanciarse.

NO importa CustomTkinter. Compatible con contexto frozen.
"""

import sys
import os

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QPoint,
    QRectF,
    QPointF,
    QSize,
    pyqtSignal,
    pyqtProperty,
    QObject,
    QRect,
    QSequentialAnimationGroup,
    QAbstractAnimation,
    QVariantAnimation,
)
from PyQt6 import sip
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPalette,
    QLinearGradient,
    QRadialGradient,
    QPainterPath,
    QFontMetrics,
    QPixmap,
    QPaintEvent,
    QMouseEvent,
    QResizeEvent,
    QEnterEvent,
    QIcon,
    QPolygonF,
    QImage,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QPushButton,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QAbstractButton,
    QToolButton,
    QSizePolicy,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QApplication,
    QScrollArea,
    QTextEdit,
    QLayout,
    QSlider,
    QButtonGroup,
)

try:
    from shared.theme_qt import (
        # Legacy (intacto)
        qcolor,
        qfont,
        qfont_mono,
        linear_gradient,
        rich_gradient,
        linear_gradient_vertical,
        radial_glow,
        noise_overlay,
        gradient_colors,
        conical_arc_gradient,
        ring_color,
        aura_opacity,
        blob_opacity,
        C,
        colors,
        norm_modo,
        interpolate_color,
        blend_color,
        label_style,
        SessionColor,
        nm_icon,
        nm_font,
        sp,
        fx,
        focus_ring_stylesheet,
        ThemeAwareWidgetMixin,
        ANIM,
        EASE_OUT,
        RADIUS_CARD,
        RADIUS_BUTTON,
        RADIUS_INPUT,
        RADIUS_PILL,
        RADIUS_SMALL,
        CHECKBOX_SIZE,
        qcolor_to_rgba_css,
        qcolor_hex,
        shadow_effect,
        PAD_CONTAINER,
        PAD_CARD,
        GAP_CARDS,
        GAP_ELEMENTS,
        HEADER_H,
        FONT_MONO,
        SIZE_TIME_LARGE,
        SIZE_TIME_TIMER,
        RING_GOOD_THRESHOLD,
        RING_MID_THRESHOLD,
        stylesheet_lineedit,
        aplicar_captionbar_qt,
        obtener_ruta_recurso,
        recolorear_logo_light,
        obtener_icono_solido,
        # v3 (nuevos helpers para los sub-pasos 2-8)
        v3c,
        parse_rgba,
        v3_shadow,
        v3_linear_gradient,
        v3_conical_signature,
        v3_font,
        mood_qcolor,
        mood_gradient,
        V3_SP,
        V3_RD,
        pill_radius,
        eyebrow_font,
    )
    from shared.theme import (
        TYPOGRAPHY,
        LAYOUT,
        CATEGORY_COLORS,
        get_gradient,
        # v3
        V3_LIGHT,
        V3_DARK,
        V3_SPACE,
        V3_RADIUS,
        V3_SHADOWS,
        V3_GRADIENTS,
        MOOD_PALETTE,
        get_v3_palette,
        get_mood,
        v3_mode,
        icon_stroke_width,
    )
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme_qt import (
        qfont,
        qfont_mono,
        radial_glow,
        blob_opacity,
        C,
        colors,
        norm_modo,
        interpolate_color,
        blend_color,
        label_style,
        SessionColor,
        nm_icon,
        sp,
        focus_ring_stylesheet,
        ThemeAwareWidgetMixin,
        ANIM,
        EASE_OUT,
        RADIUS_CARD,
        RADIUS_BUTTON,
        RADIUS_INPUT,
        RADIUS_PILL,
        RADIUS_SMALL,
        qcolor_to_rgba_css,
        PAD_CARD,
        HEADER_H,
        SIZE_TIME_LARGE,
        obtener_ruta_recurso,
        recolorear_logo_light,
        v3c,
        v3_shadow,
        v3_linear_gradient,
        v3_font,
        V3_SP,
        V3_RD,
        pill_radius,
        eyebrow_font,
    )
    from theme import (
        TYPOGRAPHY,
        LAYOUT,
        CATEGORY_COLORS,
        V3_LIGHT,
        V3_DARK,
        V3_SHADOWS,
        V3_GRADIENTS,
        get_mood,
        v3_mode,
    )


# ── ThemeManager singleton ────────────────────────────────────────────────────


class ThemeManager(QObject):
    """
    Singleton que propaga cambios de tema a todos los componentes registrados.

    Uso:
        ThemeManager.instance().switch_mode("light_hybrid")          # animado
        ThemeManager.instance().switch_mode("light_hybrid", False)   # instantáneo
        # En cualquier widget:
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    Transición v3 (350ms): por cada ventana top-level visible, toma snapshot del
    estado actual, lo overlay como QLabel, dispara el switch (que re-pinta todo
    bajo el overlay con el tema nuevo), y anima la opacidad del overlay de 1.0
    → 0.0 con OutCubic. Crossfade limpio sin tocar el paint de cada widget.
    """

    theme_changed = pyqtSignal(str)  # emite el nuevo modo

    # Duración de la transición (spec README v3)
    TRANSITION_MS = 350

    _inst = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._inst is None or sip.isdeleted(cls._inst):
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self._transitioning = False  # evita re-entradas durante una animación

    @property
    def modo(self) -> str:
        return self._modo

    def switch_mode(self, new_modo: str, animate: bool = True):
        new_modo = norm_modo(new_modo)
        if new_modo == self._modo or self._transitioning:
            return

        from shared.visual_qa import visual_qa_enabled

        if not animate or visual_qa_enabled() or QApplication.instance() is None:
            # Modo instantáneo (initial load, tests, headless)
            self._modo = new_modo
            for widget in QApplication.topLevelWidgets() if QApplication.instance() else []:
                widget.update()
            self.theme_changed.emit(new_modo)
            return

        # 1. Snapshot de cada ventana top-level visible (antes del switch)
        snapshots: list[tuple[QWidget, QPixmap]] = []
        for win in QApplication.topLevelWidgets():
            if not win.isVisible():
                continue
            if win.isMinimized():
                continue
            if win.size().width() <= 0 or win.size().height() <= 0:
                continue
            try:
                snap = win.grab()
                if not snap.isNull():
                    snapshots.append((win, snap))
            except Exception:
                # No es crítico — seguimos sin overlay para esa ventana
                pass

        # 2. Overlay snapshot ANTES del switch para que cubra el repaint
        overlays: list[QLabel] = []
        for win, snap in snapshots:
            try:
                ov = QLabel(win)
                ov.setPixmap(snap)
                ov.setGeometry(0, 0, win.width(), win.height())
                ov.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                ov.setScaledContents(False)
                ov.show()
                ov.raise_()
                overlays.append(ov)
            except Exception:
                pass

        # 3. Procesar eventos para asegurar que overlays están pintados
        try:
            QApplication.processEvents()
        except Exception:
            pass

        # 4. Switch real (widgets reciben theme_changed y se repintan bajo el overlay)
        self._modo = new_modo
        self._transitioning = True
        try:
            self.theme_changed.emit(new_modo)
            for widget in QApplication.topLevelWidgets():
                widget.update()
        except Exception:
            pass

        # 5. Animar cada overlay: fade out 350ms, luego deleteLater
        for ov in overlays:
            self._fade_out_overlay(ov)

        # Si no había overlays (caso headless), unlock inmediato
        if not overlays:
            self._transitioning = False
        else:
            # Unlock cuando termina la última animación
            QTimer.singleShot(
                self.TRANSITION_MS + 20, lambda: setattr(self, "_transitioning", False)
            )

    def _fade_out_overlay(self, overlay: QLabel):
        """Anima la opacidad del overlay 1.0 → 0.0 en TRANSITION_MS."""
        try:
            eff = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(eff)
            eff.setOpacity(1.0)
            anim = QPropertyAnimation(eff, b"opacity", overlay)
            anim.setDuration(self.TRANSITION_MS)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.finished.connect(overlay.deleteLater)
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        except Exception:
            overlay.deleteLater()


def _tm() -> ThemeManager:
    """Shorthand interno."""
    return ThemeManager.instance()


# ── NMCard ────────────────────────────────────────────────────────────────────


class NMEmptyState(ThemeAwareWidgetMixin, QWidget):
    """Widget de estado vacío con icono, título y subtítulo (handoff §2.11).

    Icono 48px dentro de chip PRIMARY_SOFT 64×64 r18.
    Título en display-m serif. Subtítulo body MUTE.
    Acepta hasta 2 CTAs opcionales (``cta_primary`` / ``cta_secondary``).
    """

    cta_primary_clicked = pyqtSignal()
    cta_secondary_clicked = pyqtSignal()

    def __init__(
        self,
        icon_key: str,
        title: str,
        subtitle: str,
        cta_primary: str = "",
        cta_secondary: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._icon_key = icon_key
        self._modo = norm_modo(_tm().modo)

        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp("xl"), sp("xl"), sp("xl"), sp("xl"))
        layout.setSpacing(V3_SP["md"])
        # Sin alignment a nivel layout: comprimía los QLabel wordwrap a su
        # sizeHint mínimo (título pisando el ícono, subtítulo recortado). Los
        # labels toman el ancho completo y centran su propio texto; el chip se
        # centra con alignment por-widget.

        # Chip contenedor del icono (64×64, PRIMARY_SOFT bg, r18)
        self._icon_chip = QFrame()
        self._icon_chip.setFixedSize(64, 64)
        self._icon_chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chip_lay = QHBoxLayout(self._icon_chip)
        chip_lay.setContentsMargins(8, 8, 8, 8)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(48, 48)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        chip_lay.addWidget(self._icon_lbl)
        layout.addWidget(self._icon_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(V3_SP["sm"])

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(v3_font("size_display_m", "weight_medium", serif=True))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setFont(v3_font("size_body"))
        self._subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_lbl.setWordWrap(True)
        layout.addWidget(self._subtitle_lbl)

        # CTAs opcionales
        if cta_primary or cta_secondary:
            btn_row = QWidget()
            btn_row.setStyleSheet("background: transparent;")
            btn_row_lay = QHBoxLayout(btn_row)
            btn_row_lay.setContentsMargins(0, V3_SP["sm"], 0, V3_SP["sm"])
            btn_row_lay.setSpacing(V3_SP["sm"])
            btn_row_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if cta_primary:
                self._btn_primary = NMButton(
                    cta_primary, variant="gradient", size="sm", width=140, modo=self._modo
                )
                self._btn_primary.clicked.connect(self.cta_primary_clicked.emit)
                btn_row_lay.addWidget(self._btn_primary)
            if cta_secondary:
                self._btn_secondary = NMButton(
                    cta_secondary, variant="ghost", size="sm", width=120, modo=self._modo
                )
                self._btn_secondary.clicked.connect(self.cta_secondary_clicked.emit)
                btn_row_lay.addWidget(self._btn_secondary)
            layout.addWidget(btn_row)

        self._apply_theme(self._modo)
        self._connect_theme()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        # Chip: PRIMARY_SOFT bg con radio moderado
        primary_c = v3c("primary", self._modo)
        primary_c.setAlphaF(0.10)
        bg_css = f"rgba({primary_c.red()},{primary_c.green()},{primary_c.blue()},25)"
        self._icon_chip.setStyleSheet(
            f"QFrame {{ background-color: {bg_css}; border-radius: 12px; }}"
        )
        icon_col = QColor(c["accent"])
        icon_col.setAlphaF(0.8)
        self._icon_lbl.setPixmap(nm_icon(self._icon_key, icon_col, size=48).pixmap(48, 48))
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(
            f"color: {C('mute', self._modo)}; background: transparent;"
        )


class NMCard(QFrame):
    """
    Card v3 — superficie limpia con border ``borderSoft`` y radius 18.

    Spec del README v3:
      - Surface ``v3c("surface")`` (o ``surfaceSolid`` en dark para QSS).
      - Border 1px ``borderSoft`` → cambia a ``borderStrong`` en hover.
      - Sin scale ni desplazamiento horizontal en press (eso es de botones).
      - ``glow=True``: halo teal concéntrico alrededor + (solo dark)
        overlay gradient teal→violet al 10% de opacidad.

    Args:
        accent_color: Hex que tiñe el halo si ``glow=True`` (default = teal).
        clickable:    Cursor pointer + emite ``clicked`` al soltar.
        modo:         Override de tema; ``None`` = sigue ThemeManager.
        disabled:     Opacity 0.45 + cursor forbidden + tooltip reason.
        glow:         Halo + (en dark) overlay gradient translúcido.
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        parent=None,
        accent_color: str = None,
        clickable: bool = True,
        modo: str = None,
        disabled: bool = False,
        disabled_reason: str = "",
        glow: bool = False,
        active: bool = False,
        radius: int | None = None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        # Radio override por instancia (None = V3_RD["card"]). Permite cards
        # de borde recto donde el redondeo lee desprolijo (p.ej. paneles
        # laterales pegados al borde de la ventana).
        self._radius_override = radius
        self._accent = accent_color
        self._base_accent = accent_color
        self._clickable = clickable
        self._glow = glow
        self._active = active
        self._hover = False
        self._disabled = False
        self._disabled_effect: QGraphicsOpacityEffect | None = None
        self._disabled_reason = ""
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._card_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName("NMCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self.set_disabled(disabled, disabled_reason)
        # Aplicar sombra al construir (v3 spec) — antes solo se aplicaba
        # al cambiar tema, dejando la primera render sin sombra (cards planas
        # en light).
        if not disabled:
            self._apply_card_shadow()

        _tm().theme_changed.connect(self._apply_theme)

    # ── sombra v3 (extraída para reutilizar desde init / theme / glow) ──────

    def _apply_card_shadow(self):
        """Crea o refresca QGraphicsDropShadowEffect según modo + glow.

        Spec V3_SHADOWS (shared/theme.py):
          light card:  blur 12, offset (0,4), rgba(15,23,42,13)
          dark  card:  blur 30, offset (0,10), rgba(0,0,0,115)
          light ring:  blur 20, offset (0,4), teal alpha 96  (glow=True)
          dark  glow:  blur 40, offset (0,0),  accent alpha 120 (glow=True)
        """
        if self._disabled:
            return
        if self._card_shadow is None:
            self._card_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if self._glow:
            # Halo accent — reads from V3_SHADOWS ring/glow bucket
            if is_dark:
                s = V3_SHADOWS["dark"]["glow"]
                self._card_shadow.setBlurRadius(s["blur"])
                self._card_shadow.setOffset(*s["offset"])
                sc = v3c("accent", self._modo)
                sc.setAlpha(s["color"][3])  # 46 from token
            else:
                s = V3_SHADOWS["light"]["ring"]
                self._card_shadow.setBlurRadius(s["blur"])
                self._card_shadow.setOffset(*s["offset"])
                sc = v3c("teal", self._modo)
                sc.setAlpha(s["color"][3])  # 76 from token
        else:
            # Standard card shadow — reads from V3_SHADOWS card bucket
            if is_dark:
                s = V3_SHADOWS["dark"]["card"]
                self._card_shadow.setBlurRadius(s["blur"])  # 30
                self._card_shadow.setOffset(*s["offset"])  # (0, 10)
                sc = QColor(*s["color"])  # rgba(0,0,0,115)
            else:
                s = V3_SHADOWS["light"]["card"]
                self._card_shadow.setBlurRadius(s["blur"])  # 12
                self._card_shadow.setOffset(*s["offset"])  # (0, 4)
                sc = QColor(*s["color"])  # rgba(15,23,42,13)
        self._card_shadow.setColor(sc)
        self.setGraphicsEffect(self._card_shadow)

    # ── hover (solo cambia el color del border, sin escalado) ─────────────────

    def enterEvent(self, event: QEnterEvent):
        # F2 ADN Claude: hover NO agranda la sombra (la card no "se levanta");
        # el feedback es el borde (border → borderStrong en paintEvent).
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ── click (v3 no aplica scale a cards en press; solo se emite clicked) ────

    def mouseReleaseEvent(self, event: QMouseEvent):
        if (
            self._clickable
            and not self._disabled
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.pos())
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _animate_press_scale(self, scale: float):
        """Pulso de escala — usado por ``play_success`` (no por hover/click)."""
        base = self.geometry()
        if not base or base.isNull():
            return
        if scale >= 1.0:
            target = base
        else:
            dw = int(base.width() * (1.0 - scale) / 2)
            dh = int(base.height() * (1.0 - scale) / 2)
            target = base.adjusted(dw, dh, -dw, -dh)
        if self._scale_anim:
            try:
                if not sip.isdeleted(self._scale_anim):
                    self._scale_anim.stop()
            except RuntimeError:
                pass
            self._scale_anim = None
        anim = QPropertyAnimation(self, b"geometry", self)
        self._scale_anim = anim
        anim.setDuration(ANIM["fast"])
        anim.setStartValue(self.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(EASE_OUT)
        anim.finished.connect(
            lambda a=anim: setattr(self, "_scale_anim", None)
            if self._scale_anim is a else None
        )
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── paintEvent v3 ─────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = "dark" in self._modo
        r = (
            self._radius_override
            if getattr(self, "_radius_override", None) is not None
            else V3_RD["card"]  # 18px — premium Hub card radius
        )
        w, h = self.width(), self.height()
        rect = QRectF(0, 0, w, h)

        # Superficie sólida del cockpit: card limpia, sin glass ni highlights.
        if not self._disabled and self.isEnabled():
            surf_col = v3c("surfaceSolid" if is_dark else "surface", self._modo)
            p.setBrush(QBrush(surf_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)
        else:
            # Disabled: solid surface for legibility
            surface_key = "surfaceSolid" if is_dark else "surface"
            p.setBrush(QBrush(v3c(surface_key, self._modo)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)

        if self._glow and not self._disabled and self.isEnabled():
            accent = QColor(self._accent or v3c("primary", self._modo).name())
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(accent))
            p.drawRoundedRect(QRectF(0, 12, 3, max(18, h - 24)), 1.5, 1.5)

        # Border: 'primary' if active, 'borderStrong' on hover, else 'border'
        if self._active:
            border_c = v3c("primary", self._modo)
            pen = QPen(border_c, 2)
        elif self._hover and self.isEnabled() and not self._disabled:
            border_c = v3c("borderStrong", self._modo)
            pen = QPen(border_c, 1)
        else:
            border_c = v3c("border", self._modo)
            pen = QPen(border_c, 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.end()

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self._apply_card_shadow()
        self.update()

    def set_active(self, active: bool):
        self._active = bool(active)
        self.update()

    def set_accent(self, hex_color: str | None):
        """En v3 solo afecta el color del halo cuando ``glow=True``."""
        self._accent = hex_color
        self._base_accent = hex_color
        self.update()

    def set_glow(self, enabled: bool):
        self._glow = bool(enabled)
        # Re-aplicar shadow con preset distinto (card → ring/glow)
        self._apply_card_shadow()
        self.update()

    def set_disabled(self, state: bool, reason: str = ""):
        self._disabled = state
        self._disabled_reason = reason
        self.setToolTip(reason if state else "")
        if state:
            if self._disabled_effect is None:
                self._disabled_effect = QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(self._disabled_effect)
            self._disabled_effect.setOpacity(0.45)
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            if self._disabled_effect is not None:
                self._disabled_effect.deleteLater()
                self._disabled_effect = None
            self.setCursor(
                Qt.CursorShape.PointingHandCursor if self._clickable else Qt.CursorShape.ArrowCursor
            )
            # Restaurar sombra (reemplaza el QGraphicsOpacityEffect anterior)
            self._apply_card_shadow()
        self.update()

    def play_success(self):
        """Pulso de escala + flash del halo en success."""
        if self._disabled:
            return
        base = self.geometry()
        if base.isNull():
            return
        prev_accent = self._accent
        prev_glow = self._glow
        self._accent = C("success", self._modo)
        self._glow = True
        self.update()

        target = base.adjusted(
            -int(base.width() * 0.02),
            -int(base.height() * 0.02),
            int(base.width() * 0.02),
            int(base.height() * 0.02),
        )
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
        grow = QPropertyAnimation(self, b"geometry", self)
        grow.setDuration(ANIM["fast"])
        grow.setStartValue(base)
        grow.setEndValue(target)
        grow.setEasingCurve(QEasingCurve.Type.OutElastic)

        shrink = QPropertyAnimation(self, b"geometry", self)
        shrink.setDuration(ANIM["fast"])
        shrink.setStartValue(target)
        shrink.setEndValue(base)
        shrink.setEasingCurve(QEasingCurve.Type.OutElastic)

        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        group.addAnimation(grow)
        group.addAnimation(shrink)

        def _restore():
            self._accent = prev_accent
            self._glow = prev_glow
            self.update()

        group.finished.connect(_restore)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMIconButton ──────────────────────────────────────────────────────────────


class NMIconButton(QToolButton):
    """NMIconButton F1 Polish V2."""

    def __init__(
        self,
        icon_name: str,
        size: str = "default",
        variant: str = "default",
        tooltip: str = "",
        checkable: bool = False,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._icon_name = icon_name
        self._variant = variant
        self._size_str = size

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(checkable)
        if tooltip:
            self.setToolTip(tooltip)

        if size == "sm":
            wh = 28
            self._isize = 16
        else:
            wh = 36
            self._isize = 20

        self.setFixedSize(wh, wh)
        self.setIconSize(QSize(self._isize, self._isize))
        self.setObjectName("NMIconButton")

        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        ic_color = C("ink_primary", self._modo)
        if self._icon_name:
            self.setIcon(nm_icon(self._icon_name, ic_color, size=self._isize))

        if self._variant == "ghost":
            bg = "transparent"
            hov_bg = C("surface2", self._modo)
            bd = "transparent"
        elif self._variant == "tint":
            bg = C("surface2", self._modo)
            hov_bg = C("surface", self._modo)
            bd = C("border", self._modo)
        else:  # default
            bg = C("surface", self._modo)
            hov_bg = C("surface2", self._modo)
            bd = C("border", self._modo)

        r = self.width() // 2
        prim = C("primary", self._modo)

        self.setStyleSheet(f"""
            QToolButton#NMIconButton {{
                background-color: {bg};
                border: 1px solid {bd};
                border-radius: {r}px;
            }}
            QToolButton#NMIconButton:hover {{
                background-color: {hov_bg};
            }}
            QToolButton#NMIconButton:checked {{
                background-color: {prim};
                border: 1px solid {prim};
            }}
        """)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


# ── NMButton ──────────────────────────────────────────────────────────────────

# Controles ADN: compacto/sobrio, sin variante grande por defecto.
_NM_CONTROL_HEIGHT = 36
_NM_CONTROL_COMPACT_HEIGHT = 32
_NM_CONTROL_RADIUS = LAYOUT["radius_input"]
_NM_CONTROL_PILL_RADIUS = _NM_CONTROL_HEIGHT // 2
_NM_CONTROL_FONT = "size_body"
# Texto de botones en negrita (semibold 600, el peso "fuerte" canónico del
# de-negritado): el owner pidió confirmar que TODOS los botones se lean en
# negrita; a 500 (medium) quedaban demasiado livianos.
_NM_CONTROL_WEIGHT = TYPOGRAPHY["weight_semibold"]
_NM_TAB_HEIGHT = 32
_NM_TAB_RADIUS = 16
_NM_TAB_FONT = "size_caption"
_NM_BUTTON_HEIGHT = {
    "sm": _NM_CONTROL_COMPACT_HEIGHT,
    "md": _NM_CONTROL_HEIGHT,
    "lg": _NM_CONTROL_HEIGHT,
}
_NM_BUTTON_FONT = {"sm": "size_caption", "md": _NM_CONTROL_FONT, "lg": _NM_CONTROL_FONT}


class NMButton(QPushButton):
    """
    Botón v3 — pill, 3 variantes (``gradient`` / ``secondary`` / ``ghost``),
    con ``lg`` normalizado a la escala media ADN para evitar gigantismo.

    Comportamiento:
      - Press: scale 0.97 por 100 ms (spec README v3 para botones).
      - Hover: variante ``gradient`` añade glow exterior teal; las otras
        cambian color de fondo y/o border.
      - Ripple blanco al click solo en variante ``gradient``.

    Args:
        text:    label
        parent:  QWidget parent
        modo:    override de tema; ``None`` = sigue ThemeManager
        width:   minWidth (legacy, default 180)
        height:  fixedHeight; ``None`` = derivado de ``size``
        variant: ``"gradient"`` (primary teal→violet) | ``"secondary"``
                 (surface + border) | ``"ghost"`` (transparente)
        size:    ``"sm"`` / ``"md"`` / ``"lg"``
    """

    def __init__(
        self,
        text: str = "",
        parent=None,
        modo: str = None,
        width: int = 180,
        height: int | None = None,
        variant: str = "gradient",
        size: str = "md",
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = (
            variant
            if variant in ("gradient", "secondary", "ghost", "danger", "destructive")
            else "gradient"
        )
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._hover = False
        self._pressed = False
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._base_geom = None
        self._btn_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName(f"NMButton_{self._variant}")
        eff_height = height if height is not None else _NM_BUTTON_HEIGHT[self._size]
        self.setFixedHeight(eff_height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont(_NM_BUTTON_FONT[self._size], weight=_NM_CONTROL_WEIGHT))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        self._apply_btn_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API v3 ────────────────────────────────────────────────────────────────

    def set_variant(self, variant: str):
        if variant in ("gradient", "secondary", "ghost", "danger", "destructive"):
            self._variant = variant
            self.setObjectName(f"NMButton_{self._variant}")
            self._apply_btn_shadow()
            self.update()

    def variant(self) -> str:
        return self._variant

    def set_size(self, size: str):
        if size in ("sm", "md", "lg") and size != self._size:
            self._size = size
            self.setFixedHeight(_NM_BUTTON_HEIGHT[size])
            self.setFont(qfont(_NM_BUTTON_FONT[size], weight=_NM_CONTROL_WEIGHT))
            self.update()

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        r = min(LAYOUT["radius_button"], h // 2)
        w = self.width()
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        is_dark = "dark" in self._modo

        if not self.isEnabled():
            p.setOpacity(0.4)

        if self._variant == "gradient":
            primary = v3c("primary", self._modo)
            p.fillPath(path, QBrush(primary))

            # Pressed: tinte plano (ADN Claude — el ripple radial fue eliminado;
            # alpha 45 compensa el feedback que aportaba la onda).
            if self._pressed and self.isEnabled():
                p.fillPath(path, QBrush(QColor(0, 0, 0, 45)))

            # Hover: soft inner highlight ring (no heavy outer glow)
            if self._hover and not self._pressed and self.isEnabled():
                ring_c = QColor(255, 255, 255, 55 if is_dark else 70)
                p.setPen(QPen(ring_c, 1.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                inset = 1.25
                p.drawRoundedRect(rect.adjusted(inset, inset, -inset, -inset), r, r)

            text_color = v3c("primary_ink", self._modo)

        elif self._variant == "secondary":
            surf_key = "surfaceSolid" if is_dark else "surface"
            elev_key = "elevatedSolid" if is_dark else "elevated"

            if self._pressed and self.isEnabled():
                # Press: one step deeper than hover
                bg_col = v3c(elev_key, self._modo)
                bg_col.setAlpha(230 if is_dark else 255)
                p.fillPath(path, QBrush(bg_col))
            elif self._hover and self.isEnabled():
                p.fillPath(path, QBrush(v3c(elev_key, self._modo)))
            else:
                p.fillPath(path, QBrush(v3c(surf_key, self._modo)))

            border_key = "borderStrong" if (self._hover or self._pressed) else "border"
            border_col = v3c(border_key, self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

            text_color = v3c("text", self._modo)

        elif self._variant in ("danger", "destructive"):
            bg_col = v3c("dangerSoftSolid", self._modo)
            if self._pressed and self.isEnabled():
                bg_col = QColor(blend_color(v3c("danger", self._modo).name(), bg_col.name(), 0.20))
            elif self._hover and self.isEnabled():
                bg_col = QColor(blend_color(v3c("danger", self._modo).name(), bg_col.name(), 0.10))
            p.fillPath(path, QBrush(bg_col))

            border_key = "danger" if (self._hover or self._pressed) else "dangerSoft"
            border_col = v3c(border_key, self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

            text_color = v3c("danger", self._modo)

        else:  # ghost
            if self._pressed and self.isEnabled():
                # Press: slightly deeper tint than hover
                bg_c = v3c("border", self._modo)
                bg_c.setAlpha(90 if is_dark else 100)
                p.fillPath(path, QBrush(bg_c))
            elif self._hover and self.isEnabled():
                bg_col = v3c("borderSoft", self._modo)
                p.fillPath(path, QBrush(bg_col))
            # Text: lift to `text` on hover/press for clear feedback
            text_color = (
                v3c("text", self._modo)
                if (self._hover or self._pressed) and self.isEnabled()
                else v3c("text2", self._modo)
            )

        # Label
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())

        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._pressed = True
            self._animate_press_scale(0.97)
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._pressed:
            self._pressed = False
            self._animate_press_scale(1.0)
            self.update()
        super().mouseReleaseEvent(event)

    def _animate_press_scale(self, scale: float):
        """Scale 0.97 ↔ 1.0 (100ms) — spec README v3 para botones."""
        if scale < 1.0:
            self._base_geom = self.geometry()
        base = self._base_geom or self.geometry()
        if not base or base.isNull():
            return
        if scale >= 1.0:
            target = base
        else:
            dw = int(base.width() * (1.0 - scale) / 2)
            dh = int(base.height() * (1.0 - scale) / 2)
            target = base.adjusted(dw, dh, -dw, -dh)
        if self._scale_anim:
            try:
                if not sip.isdeleted(self._scale_anim):
                    self._scale_anim.stop()
            except RuntimeError:
                pass
            self._scale_anim = None
        anim = QPropertyAnimation(self, b"geometry", self)
        self._scale_anim = anim
        anim.setDuration(100)
        anim.setStartValue(self.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(EASE_OUT)
        anim.finished.connect(
            lambda a=anim: setattr(self, "_scale_anim", None)
            if self._scale_anim is a else None
        )
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        if scale >= 1.0:
            self._base_geom = None

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self._apply_btn_shadow()
        self.update()

    def _apply_btn_shadow(self):
        if not self.isEnabled():
            self._btn_shadow = None
            return
        is_dark = "dark" in self._modo
        if self._btn_shadow is None:
            self._btn_shadow = QGraphicsDropShadowEffect(self)
            self.setGraphicsEffect(self._btn_shadow)
        shadow = self._btn_shadow
        if self._variant == "gradient":
            # Primary CTA: lift discreto. ADN §7.3: en dark la elevación es por
            # contraste sutil — sombra neutra, nunca halo tintado con el acento.
            if is_dark:
                shadow.setBlurRadius(12)
                shadow.setOffset(0, 3)
                sc = QColor(0, 0, 0, 86)
            else:
                shadow.setBlurRadius(10)
                shadow.setOffset(0, 2)
                sc = QColor(0x44, 0x2A, 0x0A, 22)  # warm stone tint — no cold teal on ivory
        elif self._variant == "secondary":
            # Sombra neutra sutil (lift discreto)
            shadow.setBlurRadius(8 if is_dark else 6)
            shadow.setOffset(0, 2 if is_dark else 1)
            sc = QColor(0, 0, 0, 54 if is_dark else 10)
        elif self._variant in ("danger", "destructive"):
            # Subtle danger soft shadow
            shadow.setBlurRadius(8 if is_dark else 5)
            shadow.setOffset(0, 2 if is_dark else 1)
            sc = v3c("danger", self._modo)
            sc.setAlpha(40 if is_dark else 15)
        else:  # ghost
            # Sombra mínima — apenas perceptible
            shadow.setBlurRadius(4 if is_dark else 2)
            shadow.setOffset(0, 1)
            sc = QColor(0, 0, 0, 40 if is_dark else 8)
        shadow.setColor(sc)

    def play_success(self):
        """Pulso de escala."""
        base = self.geometry()
        if base.isNull():
            return
        target = base.adjusted(-2, -2, 2, 2)
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        grow = QPropertyAnimation(self, b"geometry", self)
        grow.setDuration(ANIM["fast"])
        grow.setStartValue(base)
        grow.setEndValue(target)
        grow.setEasingCurve(QEasingCurve.Type.OutElastic)
        shrink = QPropertyAnimation(self, b"geometry", self)
        shrink.setDuration(ANIM["fast"])
        shrink.setStartValue(target)
        shrink.setEndValue(base)
        shrink.setEasingCurve(QEasingCurve.Type.OutElastic)
        group.addAnimation(grow)
        group.addAnimation(shrink)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMButtonOutline ───────────────────────────────────────────────────────────


class NMButtonOutline(QPushButton):
    """Botón pill toggleable v3 — variant ``secondary`` cuando inactivo,
    fill gradient teal→violet cuando activo.

    Si ``toggleable=True`` alterna ``active`` en cada click. Estilo coherente
    con :class:`NMButton` (mismo radius pill, misma tipografía sm).
    """

    def __init__(
        self,
        text: str = "",
        parent=None,
        modo: str = None,
        toggleable: bool = False,
        size: str = "md",
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._hover = False
        self._active = False
        self._toggleable = toggleable
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._success_anim: QSequentialAnimationGroup | None = None

        self.setFont(qfont(_NM_BUTTON_FONT[self._size], weight=_NM_CONTROL_WEIGHT))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setMinimumHeight(_NM_BUTTON_HEIGHT[self._size])
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        _tm().theme_changed.connect(self._apply_theme)

    def setText(self, text: str):
        super().setText(text)
        self.setAccessibleName(text)
        self.update()

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def is_active(self) -> bool:
        return self._active

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        r = min(LAYOUT["radius_button"], h // 2)
        w = self.width()
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        is_dark = "dark" in self._modo

        if not self.isEnabled():
            p.setOpacity(0.4)

        if self._active:
            # Active: primary SÓLIDO + tinta token (F5 ADN Claude — antes
            # gradiente firma 135° con texto #ffffff duro y ring interno).
            p.fillPath(path, QBrush(v3c("primary", self._modo)))
            text_color = v3c("primary_ink", self._modo)

        elif self._hover:
            # Hover: elevated surface + strong border
            elev_key = "elevatedSolid" if is_dark else "elevated"
            p.fillPath(path, QBrush(v3c(elev_key, self._modo)))
            p.setPen(QPen(v3c("borderStrong", self._modo), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
            # Hover: lift text from text2 → text
            text_color = v3c("text", self._modo)

        else:
            # Rest: surface + border
            surf_key = "surfaceSolid" if is_dark else "surface"
            p.fillPath(path, QBrush(v3c(surf_key, self._modo)))
            p.setPen(QPen(v3c("border", self._modo), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)
            text_color = v3c("text2", self._modo)

        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._toggleable:
            self._active = not self._active
            self.update()
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self.update()

    def play_success(self):
        base = self.geometry()
        if base.isNull():
            return
        target = base.adjusted(-2, -2, 2, 2)
        if self._success_anim:
            try:
                if not sip.isdeleted(self._success_anim):
                    self._success_anim.stop()
            except RuntimeError:
                pass
            self._success_anim = None
        group = QSequentialAnimationGroup(self)
        self._success_anim = group
        grow = QPropertyAnimation(self, b"geometry", self)
        grow.setDuration(ANIM["fast"])
        grow.setStartValue(base)
        grow.setEndValue(target)
        grow.setEasingCurve(QEasingCurve.Type.OutElastic)
        shrink = QPropertyAnimation(self, b"geometry", self)
        shrink.setDuration(ANIM["fast"])
        shrink.setStartValue(target)
        shrink.setEndValue(base)
        shrink.setEasingCurve(QEasingCurve.Type.OutElastic)
        group.addAnimation(grow)
        group.addAnimation(shrink)
        group.finished.connect(
            lambda g=group: setattr(self, "_success_anim", None)
            if self._success_anim is g else None
        )
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMInput ───────────────────────────────────────────────────────────────────


class NMInput(QLineEdit):
    """
    QLineEdit estilizado. Focus anima el color del borde border→border_focus en 200ms.
    """

    def __init__(self, placeholder: str = "", parent=None, modo: str = None, max_length: int | None = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._focus_glow: QGraphicsDropShadowEffect | None = None
        self._error_message = ""
        self.setObjectName("NMInput")
        self.setPlaceholderText(placeholder)
        self.setAccessibleName(placeholder)
        # Límite físico opcional (auditoría v1.0): textos sin tope rompen el
        # responsive de la Suite al sincronizar (el Hub inyecta estos textos).
        if max_length is not None:
            self.setMaxLength(int(max_length))
        self.setFont(qfont(_NM_CONTROL_FONT))
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        self.setMaximumHeight(_NM_CONTROL_HEIGHT)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._apply_base_style()

        _tm().theme_changed.connect(self._apply_theme)

    def _apply_base_style(self):
        bg_c = v3c("surface_2", self._modo)
        text_c = v3c("text", self._modo)
        faint_c = v3c("faint", self._modo)
        border_c = v3c("border", self._modo)
        # Foco suave: accent con alpha (no a plena intensidad) — borde fino
        # y calmo, alineado al patrón de Recordatorios (owner v1.0).
        focus_c = v3c("accent", self._modo)  # teal (light) / purple (dark)
        focus_c.setAlpha(160)
        acc_c = v3c("accent", self._modo)
        if self._error_message:
            border_c = v3c("danger", self._modo)
            focus_c = border_c
        r = _NM_CONTROL_RADIUS
        sel_text_c = v3c("primary_ink", self._modo)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_c.name()};
                color: {text_c.name()};
                border: 1px solid {qcolor_to_rgba_css(border_c)};
                border-radius: {r}px;
                padding: 0 12px;
                font-size: {TYPOGRAPHY["size_body"]}px;
                selection-background-color: {acc_c.name()};
                selection-color: {sel_text_c.name()};
            }}
            QLineEdit::placeholder {{
                color: {faint_c.name()};
            }}
            QLineEdit:focus {{
                border: 1px solid {qcolor_to_rgba_css(focus_c)};
                background-color: {bg_c.name()};
            }}
            {focus_ring_stylesheet(self._modo)}
        """)

    def focusInEvent(self, event):
        """Enciende glow suave alrededor del input en el color del accent."""
        super().focusInEvent(event)
        is_dark = "dark" in self._modo
        if self._focus_glow is None:
            self._focus_glow = QGraphicsDropShadowEffect(self)
        self._focus_glow.setBlurRadius(12 if is_dark else 10)
        self._focus_glow.setOffset(0, 0)
        gc = v3c("accent", self._modo)
        # Glow contenido en ambos temas (owner v1.0: el resplandor fuerte se
        # leía duro, no premium).
        gc.setAlpha(70 if is_dark else 50)
        self._focus_glow.setColor(gc)
        self.setGraphicsEffect(self._focus_glow)

    def focusOutEvent(self, event):
        """Apaga glow al perder foco."""
        super().focusOutEvent(event)
        self.setGraphicsEffect(None)
        self._focus_glow = None

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_base_style()

    def set_error(self, message: str = ""):
        """Marca el input en estado error real sin inventar QSS por pantalla."""
        self._error_message = message or "Error"
        self.setToolTip(self._error_message)
        self._apply_base_style()

    def clear_error(self):
        self._error_message = ""
        self.setToolTip("")
        self._apply_base_style()


# ── NMProgressBar ─────────────────────────────────────────────────────────────


class NMProgressBar(QWidget):
    """
    Barra de progreso custom con fill gradiente teal→violet.
    Propiedad animable: value (0.0–1.0).
    """

    def __init__(self, parent=None, height: int = 6, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._value = 0.0
        self._bar_h = height
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _tm().theme_changed.connect(self._apply_theme)

    # value como pyqtProperty para QPropertyAnimation
    def _get_value(self) -> float:
        return self._value

    def _set_value(self, v: float):
        self._value = max(0.0, min(1.0, v))
        self.update()

    value = pyqtProperty(float, _get_value, _set_value)

    def animate_to(self, target: float, duration: int = 400):
        a = QPropertyAnimation(self, b"value", self)
        a.setDuration(duration)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.setEndValue(target)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def set_progress(self, frac: float) -> None:
        """API compatible con NMProgressLine para reemplazos drop-in."""
        self._set_value(frac)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = self._bar_h // 2
        w = self.width()
        h = self.height()
        rect = QRectF(0, 0, w, h)

        # Track
        p.setBrush(QBrush(QColor(c["progress_track"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Fill — barra sólida continua con caps redondeados (ADN Claude).
        # El dithering de puntitos anterior se leía "técnico/punteado" — el
        # owner lo marcó como random design en el informe v1.0 final.
        # F5 ADN Claude: fill `primary` SÓLIDO sobre track neutro (lo lineal
        # va plano; el gradiente firma queda solo en lo circular/identitario).
        # (El shimmer fue eliminado en F2.)
        fill_w = w * self._value
        if fill_w > 0:
            fill_rect = QRectF(0, 0, fill_w, h)
            p.setBrush(QBrush(v3c("primary", self._modo)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(fill_rect, r, r)

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMToggle ──────────────────────────────────────────────────────────────────


class NMToggle(QAbstractButton):
    """
    Toggle switch custom: píldora redondeada con círculo deslizante.
    QPropertyAnimation sobre posición X del círculo en 200ms OutCubic.
    """

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        # v3: track 42×24, thumb 9px (deja 3px margin top/bot)
        self._track_w = 42
        self._track_h = 24
        self._thumb_r = 9
        self._thumb_x = float(self._thumb_r + 3)

        self.setCheckable(True)
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Toggle")

        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.toggled.connect(self._on_toggle)
        _tm().theme_changed.connect(self._apply_theme)

    # thumb_x como pyqtProperty
    def _get_thumb_x(self) -> float:
        return self._thumb_x

    def _set_thumb_x(self, x: float):
        self._thumb_x = x
        self.update()

    thumb_x = pyqtProperty(float, _get_thumb_x, _set_thumb_x)

    def _on_toggle(self, checked: bool):
        target = (self._track_w - self._thumb_r - 3) if checked else (self._thumb_r + 3)
        self._anim.stop()
        self._anim.setStartValue(self._thumb_x)
        self._anim.setEndValue(float(target))
        self._anim.start()

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self._track_h // 2
        track_rect = QRectF(0, 0, self._track_w, self._track_h)
        is_dark = "dark" in self._modo

        # Track
        if self.isChecked():
            # F5 ADN Claude: track `primary` SÓLIDO, sin halo (antes gradiente
            # firma + glow teal alrededor).
            p.setBrush(QBrush(v3c("primary", self._modo)))
        else:
            # Inactivo: text4 en light (#cbd5e1 — spec JSX), borderSolid en dark
            track_col = v3c("text4", self._modo) if not is_dark else v3c("borderSolid", self._modo)
            p.setBrush(QBrush(track_col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(track_rect, r, r)

        # Thumb (knob blanco) — sombra suave solo cuando activo (v3 spec)
        ty = self._track_h / 2
        if self.isChecked():
            shadow_col = QColor(0, 0, 0, 50)
            p.setBrush(QBrush(shadow_col))
            p.drawEllipse(QPointF(self._thumb_x, ty + 1), self._thumb_r, self._thumb_r)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(self._thumb_x, ty), self._thumb_r, self._thumb_r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMToast ───────────────────────────────────────────────────────────────────


class NMToast(QWidget):
    """
    Notificación inline en la esquina inferior derecha de la VENTANA.
    Variantes: 'success', 'error', 'info', 'warning'.

    Es un child overlay con parent real, SIN window flags: nunca crea una
    ventana top-level. (Antes era una ventana Qt.ToolTip|StaysOnTop y el
    lector de pantalla la resaltaba como "mini ventana titilante" fuera de
    la app — informe owner v1.0, frente 2.) El fade usa painter.setOpacity,
    no QGraphicsOpacityEffect: ahora vive bajo ancestros que pueden tener
    drop-shadows y Qt no soporta efectos anidados.
    """

    _VARIANT_KEYS = {
        "success": "success",
        "error": "danger",
        "info": "accent",
        "warning": "warning",
    }

    # Un toast activo por ventana: el nuevo reemplaza al anterior (antes se
    # apilaban superpuestos en la misma esquina).
    _active_by_host: dict = {}

    def __init__(
        self, parent_window: QWidget, message: str, variant: str = "info", duration_ms: int = 2500
    ):
        host = parent_window.window() if parent_window is not None else None
        super().__init__(host)
        self._host = host
        self._variant = variant
        self._message = message
        self._duration = duration_ms
        self._opacity = 0.0
        self._modo = norm_modo(ThemeManager.instance().modo)
        key = self._VARIANT_KEYS.get(variant, self._VARIANT_KEYS["info"])
        self._color = v3c(key, self._modo).name()
        self.setObjectName(f"NMToast_{variant}")
        self.setAccessibleName(f"NMToast {variant}: {message}")
        self.setAccessibleDescription("NeuroMood toast notification")
        # No roba foco ni clicks: el navegador de accesibilidad no debe
        # saltar al toast.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self._setup_ui()

    def _setup_ui(self):
        # Texto auto-pintado en paintEvent (sin QLabel hijo): el fade por
        # painter.setOpacity debe afectar carta y texto por igual.
        self._font = qfont("size_body")
        self._text_color = v3c("text", self._modo)
        # Margen izquierdo ampliado para no solapar la barra de acento (4 px)
        self._margins = (18, 12, 16, 12)
        ml, mt, mr, mb = self._margins
        fm = QFontMetrics(self._font)
        avail = 360 - ml - mr
        text_rect = fm.boundingRect(
            QRect(0, 0, avail, 1000), int(Qt.TextFlag.TextWordWrap), self._message
        )
        w = max(260, min(360, text_rect.width() + ml + mr))
        h = text_rect.height() + mt + mb
        self.setFixedSize(w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        r = 12.0
        accent = QColor(self._color)

        # Fondo y wash adaptativos al tema. Superficie 100% OPACA en ambos
        # temas (feedback owner v1.0: cualquier traslucidez se lee "barata" y
        # el aviso se confunde con el fondo); el color queda en la barra de
        # acento + wash mínimo.
        is_dark = "dark" in self._modo
        wash = QColor(accent)
        wash.setAlpha(12 if is_dark else 18)
        if is_dark:
            base_bg = QColor(v3c("surfaceSolid", self._modo))
        else:
            base_bg = QColor(v3c("surface", self._modo))
        base_bg.setAlpha(255)
        # El wash va ENCIMA del fondo opaco, nunca en su lugar: si el gradiente
        # arranca en el wash solo (alpha ~12), el borde izquierdo del toast
        # queda translúcido y se ve el contenido de atrás (feedback owner).
        wash_grad = QLinearGradient(0, 0, w, 0)
        wash_grad.setColorAt(0.0, wash)
        wash_transparent = QColor(wash)
        wash_transparent.setAlpha(0)
        wash_grad.setColorAt(0.40, wash_transparent)

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setClipPath(clip)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(base_bg))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setBrush(QBrush(wash_grad))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Barra de acento izquierda — 4 px, color sólido
        p.setBrush(QBrush(accent))
        p.drawRect(QRectF(0, 0, 4, h))

        p.setClipping(False)

        # Borde perimetral sutil en ambos temas (paridad dark/light) — apenas
        # más firme que el de las cards para que el aviso se distinga del
        # fondo sin recurrir a sombras.
        border_c = QColor(accent)
        border_c.setAlpha(95)
        p.setPen(QPen(border_c, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), r, r)

        # Texto (auto-pintado para que el fade lo incluya)
        ml, mt, mr, mb = self._margins
        p.setFont(self._font)
        p.setPen(QPen(self._text_color))
        opt = QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        opt.setWrapMode(QTextOption.WrapMode.WordWrap)
        p.drawText(QRectF(ml, mt, w - ml - mr, h - mt - mb), self._message, opt)
        p.end()

    def _set_opacity(self, value):
        self._opacity = float(value)
        self.update()

    def show_toast(self):
        if self._host is None:
            return
        self._replace_previous()
        self._host.installEventFilter(self)
        self._reposition()
        super().show()  # QWidget.show() — evita recursión con classmethod show()
        self.raise_()
        self._announce()

        # Fade in (painter opacity — sin QGraphicsOpacityEffect)
        anim_in = QVariantAnimation(self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.valueChanged.connect(self._set_opacity)
        anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Auto-dismiss
        QTimer.singleShot(
            self._duration,
            lambda: self._dismiss() if not sip.isdeleted(self) else None,
        )

    def eventFilter(self, obj, event):
        if obj is self._host and event.type() == QEvent.Type.Resize:
            self._reposition()
        return False

    def _replace_previous(self):
        prev = NMToast._active_by_host.get(id(self._host))
        if prev is not None and prev is not self and not sip.isdeleted(prev):
            prev._cleanup()
        NMToast._active_by_host[id(self._host)] = self

    def _announce(self):
        # Al no ser ya una ventana, el lector de pantalla no lo anuncia solo:
        # anuncio explícito (Qt >= 6.8; silencioso si no está disponible).
        try:
            from PyQt6.QtGui import QAccessible, QAccessibleAnnouncementEvent

            QAccessible.updateAccessibility(QAccessibleAnnouncementEvent(self, self._message))
        except Exception:
            pass

    def _dismiss(self):
        anim_out = QVariantAnimation(self)
        anim_out.setDuration(200)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_out.valueChanged.connect(self._set_opacity)
        anim_out.finished.connect(self._cleanup)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _cleanup(self):
        if sip.isdeleted(self):
            return
        if self._host is not None and not sip.isdeleted(self._host):
            self._host.removeEventFilter(self)
            if NMToast._active_by_host.get(id(self._host)) is self:
                NMToast._active_by_host.pop(id(self._host), None)
        self.hide()
        self.deleteLater()

    def _reposition(self):
        if self._host is None or sip.isdeleted(self._host):
            return
        margin = 20
        self.adjustSize()
        x = self._host.width() - self.width() - margin
        y = self._host.height() - self.height() - margin
        self.move(max(0, x), max(0, y))

    @classmethod
    def display(
        cls, parent_window: QWidget, message: str, variant: str = "info", duration_ms: int = 2500
    ):
        """Factory: crea y muestra un toast de una línea. None-safe: sin
        ventana host no se muestra nada (nunca un top-level)."""
        if parent_window is None:
            return None
        toast = cls(parent_window, message, variant, duration_ms)
        toast.show_toast()
        return toast


# ── NMSidebar ─────────────────────────────────────────────────────────────────


class _SidebarItem(QWidget):
    """Ítem individual del sidebar."""

    clicked = pyqtSignal(str)

    def __init__(
        self, item_id: str, icon: str | QIcon, label: str, parent=None, modo: str = "dark_hybrid"
    ):
        super().__init__(parent)
        self._id = item_id
        self._icon = icon
        self._icon_pixmap = icon.pixmap(20, 20) if isinstance(icon, QIcon) else None
        self._label = label
        self._modo = norm_modo(modo)
        self._active = False
        self._hover = False
        self._hover_alpha = 0.0
        self._bar_anim_val = 0.0  # 0.0→1.0 para la barra izquierda

        self.setFixedHeight(_NM_CONTROL_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._bar_anim = QPropertyAnimation(self, b"bar_val", self)
        self._bar_anim.setDuration(150)
        self._bar_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim = QPropertyAnimation(self, b"hover_alpha", self)
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_bar_val(self) -> float:
        return self._bar_anim_val

    def _set_bar_val(self, v: float):
        self._bar_anim_val = v
        self.update()

    bar_val = pyqtProperty(float, _get_bar_val, _set_bar_val)

    def _get_hover_alpha(self) -> float:
        return self._hover_alpha

    def _set_hover_alpha(self, v: float):
        self._hover_alpha = max(0.0, min(1.0, v))
        self.update()

    hover_alpha = pyqtProperty(float, _get_hover_alpha, _set_hover_alpha)

    def set_active(self, active: bool):
        self._active = active
        target = 1.0 if active else 0.0
        self._bar_anim.stop()
        self._bar_anim.setStartValue(self._bar_anim_val)
        self._bar_anim.setEndValue(target)
        self._bar_anim.start()

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_alpha)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._id)
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        is_dark = "dark" in self._modo
        r = V3_RD["md"]  # 10px — softer pill than RADIUS_BUTTON

        # ── Active background ──────────────────────────────────────────
        if self._active:
            bg = v3c("primary", self._modo)
            # Light: 12% primary tint on warm cream; Dark: 14% primary tint on navy
            bg.setAlpha(31 if is_dark else 28)
            path = QPainterPath()
            path.addRoundedRect(QRectF(6, 2, w - 12, h - 4), r, r)
            p.fillPath(path, QBrush(bg))

        # ── Hover background ─────────────────────────────────────────
        elif self._hover_alpha > 0:
            # Use border token fill — readable in both light and dark
            hover_bg = v3c("borderSoft", self._modo)
            hover_bg.setAlpha(
                int(hover_bg.alpha() * self._hover_alpha)
                if hover_bg.alpha() > 0
                else int(28 * self._hover_alpha)
            )
            if is_dark:
                # Dark: explicit alpha since borderSoft is rgba
                hover_fill = v3c("border", self._modo)
                hover_fill.setAlpha(int(40 * self._hover_alpha))
            else:
                # Light: warm stone tint, alpha-driven by hover_alpha
                hover_fill = v3c("border", self._modo)
                hover_fill.setAlpha(int(55 * self._hover_alpha))
            path = QPainterPath()
            path.addRoundedRect(QRectF(6, 2, w - 12, h - 4), r, r)
            p.fillPath(path, QBrush(hover_fill))

        # ── Focus ring ──────────────────────────────────────────────
        if self.hasFocus():
            focus_c = v3c("accent", self._modo)
            p.setPen(QPen(focus_c, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(7, 3, w - 14, h - 6), r, r)

        # ── Left active bar (3px, animated) ─────────────────────────────
        if self._bar_anim_val > 0:
            bar_h = int((h - 10) * self._bar_anim_val)
            bar_y = (h - bar_h) // 2
            bar_c = v3c("primary", self._modo)
            bar_path = QPainterPath()
            bar_path.addRoundedRect(QRectF(0, bar_y, 3, bar_h), 1.5, 1.5)
            p.fillPath(bar_path, QBrush(bar_c))

        # ── Icon ────────────────────────────────────────────────────
        # Active: primary color; hover: text; rest: textMuted
        if self._active:
            text_color = v3c("primary", self._modo)
        elif self._hover:
            text_color = v3c("text", self._modo)
        else:
            text_color = v3c("textMuted", self._modo)
        p.setPen(QPen(text_color))

        # Icon zone: x=16, width=28 — nudged 2px right from old x=14
        icon_rect = QRect(16, 0, 28, h)
        if self._icon_pixmap is not None:
            x = icon_rect.x() + (icon_rect.width() - self._icon_pixmap.width()) // 2
            y = icon_rect.y() + (icon_rect.height() - self._icon_pixmap.height()) // 2
            p.drawPixmap(x, y, self._icon_pixmap)
        else:
            font_icon = qfont("size_body")
            font_icon.setFamily("Segoe UI Emoji")
            p.setFont(font_icon)
            p.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon)

        # ── Label ───────────────────────────────────────────────────
        # Active: text (full contrast); hover: text; rest: textMuted
        if self._active:
            label_color = v3c("text", self._modo)
        elif self._hover:
            label_color = v3c("text", self._modo)
        else:
            label_color = v3c("textMuted", self._modo)
        p.setPen(QPen(label_color))

        # weight_semibold for active, weight_normal for rest (no bold jump)
        weight = TYPOGRAPHY["weight_semibold"] if self._active else TYPOGRAPHY["weight_normal"]
        p.setFont(qfont("size_small", weight=weight))
        # Label starts at x=46 (was 44) to match nudged icon zone
        label_rect = QRect(46, 0, w - 50, h)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignVCenter, self._label)

        p.end()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMSidebar(QWidget):
    """
    Sidebar de navegación de 200px. Emite nav_changed(str) al hacer click en un ítem.
    """

    nav_changed = pyqtSignal(str)

    def __init__(self, parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._items: dict[str, _SidebarItem] = {}
        self._active_id: str = ""
        self._theme_labels: list[tuple[QLabel, str]] = []
        self._logo_shadow: QGraphicsDropShadowEffect | None = None
        self._logo_lbl: QLabel | None = None

        self.setFixedWidth(200)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        is_dark = "dark" in self._modo
        # Use V3 sidebar bg token with alpha for glassmorphism
        if is_dark:
            bg = v3c("bgSidebar", self._modo)
            bg.setAlpha(180)
        else:
            bg = QColor(0xF2, 0xED, 0xE2, 210)  # Glassy warm cream
        p.fillRect(self.rect(), QBrush(bg))
        # Subtle glowing glass border on the right
        border_c = v3c("border", self._modo)
        border_c.setAlpha(90 if is_dark else 140)
        p.setPen(QPen(border_c, 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()
        super().paintEvent(event)

    def add_header(self, title: str, subtitle: str = ""):
        """Añade sección de título/logo al tope del sidebar."""
        colors(self._modo)
        w = QWidget()
        w.setObjectName("SidebarHeader")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 6)
        vl.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setFont(qfont("size_small", bold=True))
        lbl_title.setStyleSheet(label_style(self._modo, "accent"))
        self._theme_labels.append((lbl_title, "accent"))
        vl.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setFont(qfont("size_caption"))
            lbl_sub.setStyleSheet(label_style(self._modo, "text_tertiary"))
            self._theme_labels.append((lbl_sub, "text_tertiary"))
            vl.addWidget(lbl_sub)

        self._layout.addWidget(w)
        self._add_separator()

    def add_logo(self, logo_path: str = ""):
        """Inserta logo premium con sombra al tope del sidebar.
        Usa logos-icon-{light,dark}.png segun tema."""
        from PyQt6.QtGui import QPixmap

        w = QWidget()
        w.setObjectName("SidebarLogo")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 4)

        logo_lbl = QLabel()
        try:
            if logo_path:
                path = logo_path
            else:
                icon_name = (
                    "logos-icon-light.png" if "light" in self._modo else "logos-icon-dark.png"
                )
                path = obtener_ruta_recurso(icon_name)
                if not os.path.exists(path):
                    path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    pm = pm.scaled(
                        144,
                        32,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    logo_lbl.setPixmap(pm)
                else:
                    raise FileNotFoundError
            else:
                raise FileNotFoundError
        except Exception:
            logo_lbl.setText("NeuroMood")
            logo_lbl.setStyleSheet(label_style(self._modo, "accent"))
            logo_lbl.setFont(qfont("size_h3", bold=True))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        is_dark = "dark" in self._modo
        shadow = QGraphicsDropShadowEffect(logo_lbl)
        shadow.setBlurRadius(8 if is_dark else 4)
        shadow.setOffset(0, 2)
        if is_dark:
            col = QColor(C("accent", self._modo))
            col.setAlpha(115)
        else:
            col = QColor(15, 23, 42, 26)  # rgba(15,23,42,.10) — spec light logo shadow
        shadow.setColor(col)
        logo_lbl.setGraphicsEffect(shadow)
        self._logo_shadow = shadow
        self._logo_lbl = logo_lbl

        vl.addWidget(logo_lbl)
        self._layout.insertWidget(0, w)

    def add_item(self, item_id: str, icon: str | QIcon, label: str):
        item = _SidebarItem(item_id, icon, label, self, self._modo)
        item.clicked.connect(self._on_item_clicked)
        self._items[item_id] = item
        self._layout.addWidget(item)

    def add_separator(self):
        self._add_separator()

    def _add_separator(self):
        sep = QWidget()
        sep.setFixedHeight(1)
        # Use V3 border token — warm stone in light, violet-tinted in dark
        border_c = v3c("border", self._modo)
        sep.setStyleSheet(
            f"background-color: rgba({border_c.red()},{border_c.green()},{border_c.blue()},90);"
        )
        self._layout.addWidget(sep)

    def add_spacer(self):

        self._layout.addStretch()

    def add_label(self, text: str):
        colors(self._modo)
        lbl = QLabel(text)
        lbl.setFont(qfont("size_caption"))
        lbl.setWordWrap(True)
        lbl.setContentsMargins(14, 4, 14, 4)
        lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._theme_labels.append((lbl, "text_tertiary"))
        self._layout.addWidget(lbl)
        self._status_label = lbl

    def set_active(self, item_id: str):
        for iid, item in self._items.items():
            item.set_active(iid == item_id)
        self._active_id = item_id

    def _on_item_clicked(self, item_id: str):
        self.set_active(item_id)
        self.nav_changed.emit(item_id)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        for item in self._items.values():
            item.apply_theme(modo)
        colors(self._modo)
        # Actualizar labels temáticos y limpiar referencias muertas
        alive = []
        for lbl, color_key in self._theme_labels:
            if not sip.isdeleted(lbl):
                lbl.setStyleSheet(label_style(self._modo, color_key))
                alive.append((lbl, color_key))
        self._theme_labels = alive
        # Actualizar sombra del logo
        if self._logo_shadow is not None:
            if "dark" in self._modo:
                col = QColor(C("accent", self._modo))
                col.setAlpha(115)
            else:
                col = QColor(15, 23, 42, 26)
            self._logo_shadow.setBlurRadius(8 if "dark" in self._modo else 4)
            self._logo_shadow.setColor(col)
        # Recolorear logo en light mode o cargar logos canónicos directos
        if self._logo_lbl is not None:
            try:
                from shared.assets import obtener_ruta_asset, LOGO_LIGHT, LOGO_DARK

                logo_name = LOGO_LIGHT if "light" in self._modo else LOGO_DARK
                path = obtener_ruta_asset(logo_name)
                pm = None
                if os.path.exists(path):
                    pm = QPixmap(path)
                else:
                    path = obtener_ruta_recurso("LOGO.png")
                    if os.path.exists(path):
                        pm = QPixmap(path)
                        if "light" in self._modo:
                            from PIL import Image as PILImage

                            img = PILImage.open(path).convert("RGBA")
                            img = recolorear_logo_light(img)
                            data = img.tobytes("raw", "RGBA")
                            qimg = QImage(
                                data, img.width, img.height, QImage.Format.Format_RGBA8888
                            )
                            pm = QPixmap.fromImage(qimg)
                if pm and not pm.isNull():
                    self._logo_lbl.setPixmap(
                        pm.scaled(
                            144,
                            32,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            except Exception:
                pass
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.minimumHeight() == 1 and w.maximumHeight() == 1:
                border_c = v3c("border", self._modo)
                w.setStyleSheet(
                    f"background-color: rgba({border_c.red()},{border_c.green()},"
                    f"{border_c.blue()},90);"
                )


# ── NMHeader ──────────────────────────────────────────────────────────────────


class NMHeader(QWidget):
    """
    Header de 56px con contexto, nombre de usuario y control dark/light compacto.
    Emite theme_toggle() al hacer click en el control.

    Modos:
      - Normal (default): contexto + username + theme button
      - show_back=True: boton volver + icono + titulo de modulo
      - home_mode=True: greeting + subtitle + streak badge + theme toggle
    """

    theme_toggle = pyqtSignal()

    def __init__(
        self,
        parent=None,
        modo: str = None,
        username: str = "",
        show_back: bool = False,
        module_title: str = "",
        module_icon: str = "",
        home_mode: bool = False,
        greeting: str = "",
        subtitle: str = "",
        streak: int = 0,
        hide_selector: bool = False,
        is_suite: bool = False,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._username = username
        self._show_back = show_back
        self._module_title = module_title
        self._module_icon = module_icon
        self._home_mode = home_mode
        self._greeting = greeting
        self._subtitle_text = subtitle
        self._streak = streak
        self._hide_selector = hide_selector
        self._is_suite = is_suite

        self.setFixedHeight(HEADER_H)
        self._setup_ui()
        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)

        colors(self._modo)

        if self._show_back:
            # Módulo: botón back estilo pill (mockup: .back-btn)
            self._btn_back = QPushButton("← Volver")
            self._btn_back.setFont(qfont("size_caption", bold=True))
            self._btn_back.setFixedHeight(30)
            self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
            self._apply_back_btn_style()
            layout.addWidget(self._btn_back)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent;")
            self._module_icon_lbl = icon_lbl
            self._apply_module_icon()
            layout.addWidget(icon_lbl)

            title_lbl = QLabel(self._module_title)
            title_lbl.setFont(qfont("size_h3", bold=True))
            title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
            self._module_title_lbl = title_lbl
            layout.addWidget(title_lbl)
        else:
            if self._home_mode:
                # Home mode: greeting + subtitle + streak
                left_col = QVBoxLayout()
                left_col.setSpacing(2)
                greet_lbl = QLabel(self._greeting)
                greet_lbl.setFont(qfont("size_h1", bold=True))
                greet_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
                self._greet_lbl = greet_lbl
                left_col.addWidget(greet_lbl)
                sub_lbl = QLabel(self._subtitle_text)
                sub_lbl.setFont(qfont("size_small"))
                sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
                self._sub_lbl = sub_lbl
                left_col.addWidget(sub_lbl)
                layout.addLayout(left_col, stretch=1)
                layout.addSpacing(sp("md"))

                if self._streak > 0:
                    self._streak_badge = NMStreakBadge(self._streak, self._modo)
                    layout.addWidget(self._streak_badge)
            else:
                self._logo_widget = None

                product_is_suite = bool(self._username)

                if not self._is_suite:
                    brand = QWidget(self)
                    brand.setStyleSheet("background: transparent;")
                    brand_l = QHBoxLayout(brand)
                    brand_l.setContentsMargins(0, 0, 0, 0)
                    brand_l.setSpacing(10)
                    self._hud_mark = _ChromeLogoMark(self._modo, brand)
                    self._hud_mark.setFixedSize(24, 24)
                    brand_l.addWidget(self._hud_mark, 0, Qt.AlignmentFlag.AlignVCenter)

                    brand_txt = QVBoxLayout()
                    brand_txt.setSpacing(0)
                    self._brand_name_lbl = QLabel("NeuroMood")
                    self._brand_name_lbl.setFont(
                        qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    self._brand_mode_lbl = QLabel(
                        "Suite" if product_is_suite else "Hub"
                    )
                    self._brand_mode_lbl.setFont(
                        qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    brand_txt.addWidget(self._brand_name_lbl)
                    brand_txt.addWidget(self._brand_mode_lbl)
                    brand_l.addLayout(brand_txt)
                    layout.addWidget(brand, 0, Qt.AlignmentFlag.AlignVCenter)

                    layout.addStretch(1)

                    self._mode_selector = QWidget(self)
                    self._mode_selector.setObjectName("NMModeSelector")
                    selector_l = QHBoxLayout(self._mode_selector)
                    selector_l.setContentsMargins(2, 2, 2, 2)
                    selector_l.setSpacing(0)
                    self._suite_tab_lbl = QLabel("Suite")
                    self._hub_tab_lbl = QLabel("Hub")
                    for tab in (self._suite_tab_lbl, self._hub_tab_lbl):
                        tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        tab.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
                        tab.setMinimumHeight(24)
                        tab.setContentsMargins(12, 3, 12, 3)
                        selector_l.addWidget(tab)
                    self._suite_tab_active = product_is_suite
                    layout.addWidget(self._mode_selector, 0, Qt.AlignmentFlag.AlignCenter)
                    if self._hide_selector:
                        self._mode_selector.hide()

                    layout.addStretch(1)

                    identity = QWidget(self)
                    identity.setStyleSheet("background: transparent;")
                    identity_l = QHBoxLayout(identity)
                    identity_l.setContentsMargins(0, 0, 0, 0)
                    identity_l.setSpacing(10)
                    meta_l = QVBoxLayout()
                    meta_l.setSpacing(0)
                    display_name = self._username or "Dra. Garcia"
                    self._identity_name_lbl = QLabel(display_name)
                    self._identity_name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                    self._identity_name_lbl.setFont(
                        qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    self._identity_role_lbl = QLabel(
                        "Programa Activo" if product_is_suite else "Panel Profesional"
                    )
                    self._identity_role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                    self._identity_role_lbl.setFont(
                        qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    meta_l.addWidget(self._identity_name_lbl)
                    meta_l.addWidget(self._identity_role_lbl)
                    identity_l.addLayout(meta_l)
                    initials = (
                        "".join(part[:1] for part in display_name.split()[:2]).upper() or "NM"
                    )
                    self._identity_avatar_lbl = QLabel(initials)
                    self._identity_avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._identity_avatar_lbl.setFixedSize(28, 28)
                    self._identity_avatar_lbl.setFont(
                        qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"])
                    )
                    identity_l.addWidget(self._identity_avatar_lbl)
                    layout.addWidget(identity, 0, Qt.AlignmentFlag.AlignVCenter)

        if self._show_back or self._home_mode or self._is_suite:
            layout.addStretch()

        self._theme_lbl = QLabel(self._theme_label_text())
        self._theme_lbl.setFont(qfont("size_caption"))
        self._theme_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))
        layout.addWidget(self._theme_lbl)
        self._theme_lbl.hide()  # compact R3: toggle comunica el estado sin label

        # Compact theme button: sidebar/window chrome already carry the brand.
        self._toggle = QPushButton(self)
        self._toggle.setCheckable(True)
        self._toggle.setFixedSize(28, 28)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setAccessibleName("Cambiar tema")
        self._toggle.setChecked("light" in self._modo)
        self._toggle.toggled.connect(lambda _: self.theme_toggle.emit())
        self._apply_theme_button_style()
        layout.addWidget(self._toggle)
        # En Suite el toggle ya vive en NMWindowChrome — ocultarlo aquí evita duplicado
        if self._is_suite:
            self._toggle.hide()
        self._apply_hud_styles()

    def _ensure_context_widgets(self):
        if hasattr(self, "_context_title_lbl"):
            return
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        title_lbl = QLabel("")
        title_lbl.setFont(qfont("size_h3", bold=True))
        title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))

        self._context_icon_lbl = icon_lbl
        self._context_title_lbl = title_lbl
        self._module_icon_lbl = icon_lbl
        self._module_title_lbl = title_lbl

        layout = self.layout()
        if layout:
            insert_at = 1 if hasattr(self, "_btn_back") else 0
            layout.insertWidget(insert_at, icon_lbl)
            layout.insertWidget(insert_at + 1, title_lbl)
        icon_lbl.hide()
        title_lbl.hide()

    def set_context_title(self, title: str = "", icon: str = ""):
        """Activa el header contextual compacto usado por pantallas internas."""
        title = (title or "").strip()
        self._module_title = title
        self._module_icon = icon or ""

        if title:
            self._ensure_context_widgets()
            if hasattr(self, "_logo_widget") and self._logo_widget is not None:
                self._logo_widget.hide()
            if hasattr(self, "_user_lbl") and self._user_lbl is not None:
                self._user_lbl.hide()
            if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
                self._greet_lbl.hide()
            if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
                self._sub_lbl.hide()
            if hasattr(self, "_streak_badge") and self._streak_badge is not None:
                self._streak_badge.hide()
            if hasattr(self, "_mode_selector"):
                self._mode_selector.hide()
            self._context_title_lbl.setText(title)
            self._context_title_lbl.show()
            self._context_icon_lbl.setVisible(bool(icon))
            self._apply_module_icon()
            return

        if hasattr(self, "_context_title_lbl"):
            self._context_title_lbl.hide()
        if hasattr(self, "_context_icon_lbl"):
            self._context_icon_lbl.hide()
        if hasattr(self, "_logo_widget") and self._logo_widget is not None:
            self._logo_widget.show()
        if hasattr(self, "_user_lbl") and self._user_lbl is not None:
            self._user_lbl.show()
        if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
            self._greet_lbl.show()
        if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
            self._sub_lbl.show()
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            self._streak_badge.show()
        if hasattr(self, "_mode_selector") and not self._hide_selector:
            self._mode_selector.show()
        if hasattr(self, "_context_badge_lbl"):
            self._context_badge_lbl.hide()

    def set_context_badge(self, text: str = "", color_key: str = "teal"):
        if getattr(self, "_is_suite", False):
            return
        text = (text or "").strip()
        if not hasattr(self, "_context_badge_lbl"):
            self._context_badge_lbl = QLabel("")
            self._context_badge_lbl.setFont(qfont("size_caption", bold=True))
            self._context_badge_lbl.setContentsMargins(8, 2, 8, 2)
            layout = self.layout()
            if layout:
                layout.insertWidget(max(0, layout.count() - 3), self._context_badge_lbl)
        self._context_badge_key = color_key or "teal"
        self._context_badge_lbl.setText(text)
        self._context_badge_lbl.setVisible(bool(text))
        self._apply_context_badge_style()

    def _apply_context_badge_style(self):
        if not hasattr(self, "_context_badge_lbl"):
            return
        key = getattr(self, "_context_badge_key", "teal")
        fg = C(key, self._modo) if key in colors(self._modo) else C("teal", self._modo)
        bg = _rgba(fg, 0.14)
        self._context_badge_lbl.setStyleSheet(
            f"QLabel {{ color: {fg}; background: {bg}; "
            f"border-radius: {RADIUS_PILL}px; padding: 2px 8px; }}"
        )

    def _theme_label_text(self) -> str:
        return "Claro" if "light" in self._modo else "Oscuro"

    def _apply_theme_button_style(self) -> None:
        if not hasattr(self, "_toggle"):
            return
        c = colors(self._modo)
        icon_key = "moon" if "light" in self._modo else "sun"
        self._toggle.setIcon(nm_icon(icon_key, C("text_secondary", self._modo), size=15))
        self._toggle.setIconSize(QSize(15, 15))
        self._toggle.setToolTip(
            "Cambiar a modo oscuro" if "light" in self._modo else "Cambiar a modo claro"
        )
        self._toggle.setStyleSheet(
            f"QPushButton {{"
            f" background: {c.get('bg_elevated', c['bg_surface'])};"
            f" border: 1px solid {c.get('border_card', c['border'])};"
            f" border-radius: 8px;"
            f" padding: 0px;"
            f"}}"
            f"QPushButton:hover {{"
            f" background: {c.get('bg_hover', c.get('bg_secondary', c['bg_surface']))};"
            f" border-color: {c.get('border_strong', c.get('border', '#ffffff'))};"
            f"}}"
            f"QPushButton:focus {{"
            f" border: 1px solid {C('accent', self._modo)};"
            f"}}"
        )

    def _apply_module_icon(self):
        if not hasattr(self, "_module_icon_lbl"):
            return
        icon_key = self._module_icon or ""
        if not icon_key:
            self._module_icon_lbl.clear()
            return
        try:
            pm = nm_icon(icon_key, C("accent", self._modo), size=22).pixmap(22, 22)
            if not pm.isNull():
                self._module_icon_lbl.setPixmap(pm)
                self._module_icon_lbl.setText("")
                return
        except Exception:
            pass
        self._module_icon_lbl.setText(icon_key)
        self._module_icon_lbl.setFont(qfont("size_body"))

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        # Handoff: top command hud uses bg_canvas background
        p.fillRect(self.rect(), v3c("bg", self._modo))
        # Subtle glass border at bottom
        p.setPen(QPen(v3c("border", self._modo), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()
        super().paintEvent(event)

    def _apply_hud_styles(self):
        if not hasattr(self, "_brand_name_lbl"):
            return
        primary = v3c("primary", self._modo).name()
        primary_ink = v3c("primary_ink", self._modo).name()
        surface2 = v3c("surface_2", self._modo).name()
        text = v3c("text", self._modo).name()
        text2 = v3c("text2", self._modo).name()
        mute = v3c("mute", self._modo).name()
        border = C("border", self._modo)
        self._hud_mark._apply_theme(self._modo)
        self._brand_name_lbl.setStyleSheet(f"color: {text}; background: transparent;")
        self._brand_mode_lbl.setStyleSheet(
            f"color: {mute}; background: transparent; text-transform: uppercase; font-size: 8.5px;"
        )

        selector = self.findChild(QWidget, "NMModeSelector")
        if selector:
            # More subtle selector (pill secondary surface)
            selector.setStyleSheet(
                f"QWidget#NMModeSelector {{ background: {surface2}; "
                f"border: 1px solid {border}; border-radius: 14px; }}"
            )

        suite_active = getattr(self, "_suite_tab_active", False)
        for label, active in (
            (getattr(self, "_suite_tab_lbl", None), suite_active),
            (getattr(self, "_hub_tab_lbl", None), not suite_active),
        ):
            if label is None:
                continue
            # Pill active style
            label.setStyleSheet(
                f"QLabel {{ background: {primary if active else 'transparent'}; "
                f"color: {primary_ink if active else text2}; "
                f"border-radius: 10px; padding: 4px 14px; "
                f"font-size: 11px; font-weight: 500; }}"
            )

        self._identity_name_lbl.setStyleSheet(
            f"color: {text}; background: transparent; font-size: 12px; font-weight: 500;"
        )
        self._identity_role_lbl.setStyleSheet(
            f"color: {mute}; background: transparent; font-size: 9px; text-transform: uppercase;"
        )

        # Identity avatar (ML-like circle)
        self._identity_avatar_lbl.setStyleSheet(
            f"QLabel {{ background: {qcolor_to_rgba_css(v3c('primary_soft', self._modo))}; "
            f"color: {primary}; border: 1px solid {border}; border-radius: 14px; "
            f"font-size: 11.5px; font-weight: 500; }}"
        )

    def _apply_back_btn_style(self):
        """Aplica estilo pill del botón Volver según mockup."""
        if not hasattr(self, "_btn_back"):
            return
        c = colors(self._modo)
        is_dark = "dark" in self._modo
        if is_dark:
            bg = "rgba(255,255,255,0.04)"
            border = "rgba(255,255,255,0.08)"
        else:
            bg = c["bg_elevated"]
            border = c["border"]
        self._btn_back.setStyleSheet(
            f"QPushButton {{ "
            f"color: {C('text_tertiary', self._modo)}; "
            f"background-color: {bg}; "
            f"border: 1px solid {border}; "
            f"border-radius: {RADIUS_SMALL}px; "
            f"padding: 3px 10px; "
            f"font-size: 11px; "
            f"font-weight: 500; "
            f"}} "
            f"QPushButton:hover {{ "
            f"background-color: {c['bg_elevated']}; "
            f"color: {C('text_secondary', self._modo)}; "
            f"}}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        if hasattr(self, "_logo_widget") and self._logo_widget is not None:
            self._logo_widget.set_modo(modo)
        if hasattr(self, "_user_lbl"):
            self._user_lbl.setStyleSheet(label_style(modo, "text_tertiary"))
        if hasattr(self, "_btn_back"):
            self._apply_back_btn_style()
        if hasattr(self, "_module_title_lbl"):
            self._module_title_lbl.setStyleSheet(label_style(modo, "text_primary"))
        self._apply_module_icon()
        self._apply_hud_styles()
        if hasattr(self, "_theme_lbl"):
            self._theme_lbl.setText(self._theme_label_text())
            self._theme_lbl.setStyleSheet(label_style(modo, "text_secondary"))
        self._apply_context_badge_style()
        was_blocked = self._toggle.blockSignals(True)
        self._toggle.setChecked("light" in modo)
        self._toggle.blockSignals(was_blocked)
        self._apply_theme_button_style()

    def _ensure_back_button(self):
        if hasattr(self, "_btn_back"):
            return self._btn_back
        btn = QPushButton("← Volver", self)
        btn.setFont(qfont("size_caption", bold=True))
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = self.layout()
        if layout:
            layout.insertWidget(0, btn)
        self._btn_back = btn
        self._back_btn = btn
        self._apply_back_btn_style()
        return btn

    def set_home_greeting(self, greeting: str = "", subtitle: str = "", streak: int = 0):
        """Actualiza los textos del header en modo home."""
        if hasattr(self, "_greet_lbl") and self._greet_lbl is not None:
            self._greet_lbl.setText(greeting or f"Hola, {self._username}")
        if hasattr(self, "_sub_lbl") and self._sub_lbl is not None:
            self._sub_lbl.setText(subtitle)
        if hasattr(self, "_streak_badge") and self._streak_badge is not None:
            if streak > 0:
                self._streak_badge.show()
            else:
                self._streak_badge.hide()

    def set_back_action(self, callback=None):
        btn = self._ensure_back_button() if callback else getattr(self, "_btn_back", None)
        if not btn:
            return
        try:
            btn.clicked.disconnect()
        except TypeError:
            pass
        if callback:
            btn.clicked.connect(callback)
            btn.show()
        else:
            btn.hide()

    def set_back_callback(self, callback):
        self.set_back_action(callback)

    def set_title_info(self, title: str = "", icon: str = ""):
        self.set_context_title(title, icon)


class _LogoLabel(QWidget):
    """Logo NeuroMood desde assets/LOGO.png con glow animado + sombra premium."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._glow_alpha_value = 0
        self.setFixedHeight(32)
        self._pixmap = None
        self._load_logo()

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setOffset(0, 0)
        col = QColor(C("accent", self._modo))
        col.setAlpha(30)
        self._shadow.setColor(col)
        self.setGraphicsEffect(self._shadow)

        self._breath_anim = QPropertyAnimation(self, b"glow_alpha", self)
        self._breath_anim.setDuration(3000)
        self._breath_anim.setStartValue(0)
        self._breath_anim.setEndValue(60)
        self._breath_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._breath_anim.setLoopCount(-1)
        self._breath_anim.start()

    def _load_logo(self):
        try:
            from shared.assets import obtener_ruta_asset, LOGO_LIGHT, LOGO_DARK

            logo_name = LOGO_LIGHT if "light" in self._modo else LOGO_DARK
            logo_path = obtener_ruta_asset(logo_name)
            if not os.path.exists(logo_path):
                logo_key = "logos-light.png" if "light" in self._modo else "logos-dark.png"
                logo_path = obtener_ruta_recurso(logo_key)
                if not os.path.exists(logo_path):
                    logo_path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(logo_path):
                self._pixmap = QPixmap(logo_path)
                self._pixmap_light = None
        except Exception:
            self._pixmap = None
            self._pixmap_light = None

    def _get_pixmap(self):
        if self._pixmap is None:
            return None
        return self._pixmap

    def _get_glow_alpha(self) -> int:
        return self._glow_alpha_value

    def _set_glow_alpha(self, value: int):
        self._glow_alpha_value = max(0, min(255, int(value)))
        self.update()

    glow_alpha = pyqtProperty(int, _get_glow_alpha, _set_glow_alpha)

    def set_modo(self, modo: str):
        old_modo = self._modo
        self._modo = norm_modo(modo)
        if old_modo != self._modo:
            self._load_logo()
        is_dark = "dark" in self._modo
        if is_dark:
            col = QColor(C("accent", self._modo))
            col.setAlpha(30)
            self._shadow.setBlurRadius(8)
        else:
            col = QColor(15, 23, 42, 26)  # rgba(15,23,42,.10) — spec light logo shadow
            self._shadow.setBlurRadius(4)
        self._shadow.setOffset(0, 2)
        self._shadow.setColor(col)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(140, 32)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Double glow in dark mode: violet radial halo behind logo
        if "dark" in self._modo and self._glow_alpha_value > 0:
            violet_alpha = int(self._glow_alpha_value * 0.6)
            vglow = radial_glow(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.6,
                C("violet", self._modo),
                alpha=violet_alpha,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(vglow))
            p.drawEllipse(
                QPointF(self.width() / 2, self.height() / 2),
                self.width() * 0.5,
                self.height() * 0.8,
            )

        draw_text_fallback = True
        pm = self._get_pixmap()
        if pm and not pm.isNull():
            pm_scaled = pm.scaled(
                140,
                28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            if pm_scaled and not pm_scaled.isNull():
                x = (self.width() - pm_scaled.width()) // 2
                y = (self.height() - pm_scaled.height()) // 2
                p.drawPixmap(x, y, pm_scaled)
                draw_text_fallback = False

        if draw_text_fallback:
            c = colors(self._modo)
            font_bold = qfont("size_body", bold=True)
            p.setFont(font_bold)
            fm = QFontMetrics(font_bold)
            p.setPen(QColor(c["text_primary"]))
            p.drawText(0, fm.ascent() + 4, "Neuro")
            w1 = fm.horizontalAdvance("Neuro")
            p.setPen(QColor(C("accent", self._modo)))
            p.drawText(w1, fm.ascent() + 4, "Mood")

        if self._glow_alpha_value > 0:
            glow = radial_glow(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.7,
                C("accent", self._modo),
                alpha=self._glow_alpha_value,
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(
                QPointF(self.width() / 2, self.height() / 2),
                self.width() * 0.45,
                self.height() * 0.7,
            )
        p.end()


# ── NMFadeWidget ──────────────────────────────────────────────────────────────


class NMFadeWidget(QStackedWidget):
    """
    QStackedWidget con transición "fade-through-background" entre páginas.

    setCurrentWidget() override: switch instantáneo + velo del color de fondo
    del tema que se desvanece en ~160ms. El cross-blend anterior (snapshot de
    la vista vieja desvaneciéndose SOBRE la nueva) mostraba AMBAS vistas
    superpuestas durante toda la animación — el "titileo fantasma" que el
    owner grabó en video (informe v1.0 final). Con el velo nunca conviven dos
    contenidos: la vista nueva emerge del fondo, calma y sin doble exposición.
    """

    def __init__(self, parent=None, duration: int = 160):
        super().__init__(parent)
        self._duration = duration
        self._animating = False
        self._snapshot: QWidget | None = None
        self._fade_anim: QPropertyAnimation | None = None

    def setCurrentWidget(self, widget: QWidget):
        if widget is self.currentWidget():
            return
        if self._animating and self._fade_anim is not None:
            # Navegación rápida durante el velo: cortar la animación en curso
            # (stop() emite finished → limpieza única) y conmutar igual;
            # descartar el click dejaba la nav "muerta" durante 160ms.
            self._fade_anim.stop()
        self._fade_to(widget)

    def _fade_to(self, target: QWidget):
        current = self.currentWidget()
        super().setCurrentWidget(target)
        if current is None:
            self._animating = False
            return

        self._animating = True
        modo = norm_modo(_tm().modo)
        scrim = QWidget(self)
        scrim.setStyleSheet(f"background: {v3c('bg', modo).name()};")
        scrim.setGeometry(0, 0, self.width(), self.height())
        scrim.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        scrim.show()
        scrim.raise_()
        self._snapshot = scrim

        eff = QGraphicsOpacityEffect(scrim)
        scrim.setGraphicsEffect(eff)

        fade_out = QPropertyAnimation(eff, b"opacity", self)
        fade_out.setDuration(self._duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_out_done():
            scrim.deleteLater()
            self._snapshot = None
            self._animating = False
            self._fade_anim = None

        fade_out.finished.connect(_on_out_done)
        self._fade_anim = fade_out
        fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self._snapshot:
            self._snapshot.setGeometry(0, 0, self.width(), self.height())


# ── NMModule (base class Qt) ──────────────────────────────────────────────────


class NMSkeleton(QWidget):
    """
    Rectangulo de carga animado con gradiente deslizante.
    Uso: skeleton = NMSkeleton(parent, width=200, height=16, radius=8)
    """

    def __init__(self, parent=None, width=200, height=16, radius=8, modo=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._radius = radius
        self._pos = 0.0
        self.setFixedSize(width, height)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        _tm().theme_changed.connect(self._apply_theme)

    def _tick(self):
        self._pos = (self._pos + 0.012) % 1.4
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        r = QRectF(self.rect())

        p.setBrush(QColor(c["bg_elevated"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, self._radius, self._radius)

        sx = (self._pos - 0.3) * self.width()
        sw = self.width() * 0.4
        sg = QLinearGradient(sx, 0, sx + sw, 0)
        sg.setColorAt(0.0, QColor(255, 255, 255, 0))
        sg.setColorAt(0.5, QColor(255, 255, 255, 18))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sg))
        p.drawRoundedRect(r, self._radius, self._radius)
        p.end()

    def _apply_theme(self, modo):
        self._modo = norm_modo(modo)
        self.update()


class NMModule(ThemeAwareWidgetMixin, QWidget):
    """
    Clase base para módulos de la plataforma paciente en PyQt6.
    Preserva exactamente el mismo contrato que la versión CTk:
      - MODULE_TITLE, MODULE_ICON
      - build_ui() → raise NotImplementedError
      - get_card_status() → str
      - on_enter(), on_leave() — hooks
    """

    MODULE_TITLE: str = ""
    MODULE_ICON: str = ""

    # Señal que los módulos emiten cuando quieren volver al home
    back_requested = pyqtSignal()

    def __init__(self, parent=None, modo: str = None, show_header: bool = True):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._show_header = show_header
        self._session = SessionColor.instance()

        # Layout vertical: header + contenido
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        if self._show_header:
            self._header = NMHeader(
                self,
                modo=self._modo,
                show_back=True,
                module_title=self.MODULE_TITLE,
                module_icon=self.MODULE_ICON,
            )
            self._header.set_back_callback(self.back_requested.emit)
            self._root_layout.addWidget(self._header)

        # Contenido del modulo (build_ui lo llena) con centrado premium
        self._content = QWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Handoff §2: opaque background para que el stacked widget no
        # muestre contenido anterior a través del módulo activo.
        self._content.setAutoFillBackground(True)
        _surf = v3c("surface", self._modo)
        _pal = QPalette()
        _pal.setColor(QPalette.ColorRole.Window, _surf)
        self._content.setPalette(_pal)
        self._apply_content_bg()

        # Wrapper centrado para pantallas anchas (>1100px el contenido se centra)
        self._content_wrapper = QHBoxLayout()
        self._content_wrapper.setContentsMargins(0, 0, 0, 0)
        self._content_wrapper.addWidget(self._content)
        self._root_layout.addLayout(self._content_wrapper)

        self._connect_theme()
        self.build_ui()

    def _apply_content_bg(self):
        self._content.update()

    def paintEvent(self, event):
        """Aura radial dinámica de fondo."""
        super().paintEvent(event)

    @property
    def modo(self) -> str:
        return self._modo

    def build_ui(self):
        raise NotImplementedError(f"{self.__class__.__name__} debe implementar build_ui()")

    def get_card_status(self) -> str:
        """Estado resumido del módulo para mostrar en la card del home."""
        return ""

    def on_enter(self):
        """Llamado cuando el módulo se hace visible (recargar datos frescos)."""
        pass

    def on_leave(self):
        """Llamado antes de que el módulo sea ocultado (detener timers, etc.)."""
        pass

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_content_bg()

    def _apply_theme(self, modo: str):
        self._on_theme(modo)


# ── NMStatusChip ──────────────────────────────────────────────────────────────


class NMStatusChip(QLabel):
    """Pill pequeña con color semántico y texto. Usa tokens del tema."""

    def __init__(
        self, text: str = "", color_key: str = "success", modo: str = "dark_hybrid", parent=None
    ):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._color_key = color_key
        self.setFont(qfont("size_caption"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(22)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        color_hex = C(self._color_key, self._modo)
        is_dark = "dark" in self._modo
        # Soft semantic bg: use the Soft variant of the color key if available
        soft_key = self._color_key + "Soft"
        soft_c = (
            v3c(soft_key, self._modo) if soft_key in (V3_DARK if is_dark else V3_LIGHT) else None
        )
        if soft_c is not None:
            bg_css = f"rgba({soft_c.red()},{soft_c.green()},{soft_c.blue()},{soft_c.alpha()})"
        else:
            # Fallback: 10% of the semantic color
            fc = QColor(color_hex)
            fc.setAlpha(26)  # ~10%
            bg_css = f"rgba({fc.red()},{fc.green()},{fc.blue()},26)"
        self._pill_r_applied = pill_radius(self, fallback=22)
        self.setStyleSheet(f"""
            NMStatusChip {{
                color: {color_hex};
                background-color: {bg_css};
                border: 1px solid {color_hex};
                border-radius: {self._pill_r_applied}px;
                padding: 2px 10px;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=22) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def set_color(self, color_key: str):
        self._color_key = color_key
        self._apply_style()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


# ── NMSectionCard ─────────────────────────────────────────────────────────────


class NMSectionCard(QFrame):
    """Card con título decorativo. content_widget() devuelve el área para widgets."""

    def __init__(self, title: str = "", icon: str = "", modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._title = title
        self._icon = icon
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._build()
        _tm().theme_changed.connect(self._apply_theme)

    def _build(self):
        c = colors(self._modo)
        self.setStyleSheet(f"""
            NMSectionCard {{
                background-color: {c["bg_surface"]};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get("border_card", c["border"])};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CARD, 12, PAD_CARD, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        if self._icon:
            icon_lbl = QLabel(self._icon)
            icon_lbl.setStyleSheet("background: transparent;")
            header.addWidget(icon_lbl)
        title_lbl = QLabel(self._title)
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(4)
        layout.addWidget(self._content)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(f"""
            NMSectionCard {{
                background-color: {c["bg_surface"]};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get("border_card", c["border"])};
            }}
        """)


# ── NMFormField ────────────────────────────────────────────────────────────────


class NMFormField(QWidget):
    """Label + input en fila horizontal, con espaciado consistente."""

    def __init__(
        self, label: str = "", widget: QWidget = None, modo: str = "dark_hybrid", parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setFont(qfont("size_body"))
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))
        self._label.setMinimumWidth(55)
        layout.addWidget(self._label)

        if widget:
            layout.addWidget(widget, stretch=1)
        layout.addStretch()
        _tm().theme_changed.connect(self._apply_theme)

    def label(self) -> QLabel:
        return self._label

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))


def h_spacer() -> QWidget:
    """Spacer horizontal expandible."""
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return w


# Breakpoints documentados (ancho de viewport)
BREAKPOINTS = {"xs": 640, "sm": 960, "md": 1280, "lg": 1600}


def responsive_columns(
    available_width: int, min_card_width: int = 280, max_columns: int = 3
) -> int:
    """Devuelve el número óptimo de columnas según ancho disponible.

    Breakpoints documentados:
        xs < 640   → 1 columna (móvil / ventana muy pequeña)
        sm < 960   → hasta 2 columnas
        md < 1280  → hasta 3 columnas
        lg < 1600  → hasta max_columns
        xl >= 1600 → max_columns
    """
    if available_width < BREAKPOINTS["xs"]:
        return 1
    if available_width < BREAKPOINTS["sm"]:
        return min(2, max_columns)
    cols = max(1, min(max_columns, available_width // min_card_width))
    return cols


def responsive_breakpoint(width: int) -> str:
    """Devuelve el nombre del breakpoint activo para el ancho dado."""
    if width < BREAKPOINTS["xs"]:
        return "xs"
    if width < BREAKPOINTS["sm"]:
        return "sm"
    if width < BREAKPOINTS["md"]:
        return "md"
    if width < BREAKPOINTS["lg"]:
        return "lg"
    return "xl"


def _rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    a = max(0, min(255, int(alpha * 255)))
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"


# ── Helpers v3 para rings (NMFocusArc / NMModuleRing / NMCycleRing) ──────────


def _ring_stroke(size: int) -> int:
    """Stroke proporcional al tamaño (README v3).

    ≤ 40       → 3-4
    60-100     → 5-8
    ≥ 100      → 10-14   (340 → 14)
    """
    if size <= 40:
        return max(3, round(size * 0.085))
    if size <= 60:
        return 5
    if size <= 80:
        return 6
    if size <= 100:
        return 8
    if size <= 140:
        return 10
    if size <= 200:
        return 12
    return 14


def _color_at_t(stops, t: float) -> QColor:
    """Interpola entre stops ``[(hex, t_pos), …]`` ordenados por t_pos."""
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        h0, t0 = stops[i]
        h1, t1 = stops[i + 1]
        if t0 <= t <= t1:
            local = (t - t0) / max(1e-9, t1 - t0)
            return QColor(interpolate_color(h0, h1, local))
    return QColor(stops[-1][0])


def _paint_v3_arc(
    p: QPainter,
    rect: QRectF,
    start_angle_deg: float,
    span_deg: float,
    pen_width: int,
    modo: str,
    segments: int = 64,
):
    """Pinta un arco con el gradient firma v3 fluyendo a lo largo del arco.

    Implementación segmento-a-segmento con FlatCap (sin spokes intermedios) y
    círculos sólidos en los extremos para simular RoundCap. Funciona en
    cualquier dirección (CW o CCW) sin los líos de QConicalGradient.
    """
    import math

    if abs(span_deg) < 0.1:
        return
    stops = V3_GRADIENTS[v3_mode(modo)]
    direction = 1 if span_deg > 0 else -1
    abs_span = abs(span_deg)

    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(segments):
        t0 = i / segments
        t1 = (i + 1) / segments
        mid_t = (t0 + t1) / 2
        col = _color_at_t(stops, mid_t)
        pen = QPen(col, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        a0 = start_angle_deg + direction * abs_span * t0
        a1 = start_angle_deg + direction * abs_span * t1
        p.drawArc(rect, int(a0 * 16), int((a1 - a0) * 16))

    # Round caps manuales en los extremos del arco
    cx, cy = rect.center().x(), rect.center().y()
    rx, ry = rect.width() / 2, rect.height() / 2
    cap_r = pen_width / 2
    for endpoint_t, color_t in ((0.0, 0.0), (1.0, 1.0)):
        angle = math.radians(start_angle_deg + direction * abs_span * endpoint_t)
        # Qt: y aumenta hacia abajo, ángulo positivo es CCW desde +x
        px = cx + rx * math.cos(angle)
        py = cy - ry * math.sin(angle)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(_color_at_t(stops, color_t)))
        p.drawEllipse(QPointF(px, py), cap_r, cap_r)


# ── NMIcon ───────────────────────────────────────────────────────────────────

try:
    from shared.icons_svg import nm_svg_pixmap as _nm_svg_pixmap, has_icon as _has_v3_icon
except ImportError:
    try:
        from icons_svg import nm_svg_pixmap as _nm_svg_pixmap, has_icon as _has_v3_icon  # type: ignore
    except ImportError:
        _nm_svg_pixmap = None
        _has_v3_icon = lambda _n: False  # noqa: E731


class NMIcon(QLabel):
    """Widget de icono SVG v3.

    Args:
        name:      nombre del icono (``shared.icons_svg.available_icons()``).
        size:      lado del icono en px.
        color:     hex literal (estático).
        color_key: clave de la paleta v3 (``'text'``, ``'text2'``, ``'ink_secondary'``,
                   ``'teal'``, ``'violet'``, ``'danger'``…). Si se pasa, el
                   icono se re-renderiza automáticamente en cada theme change
                   y ``color`` se ignora.
        modo:      override de tema (None = sigue ThemeManager).

    Si el nombre no está en el catálogo v3, cae a QtAwesome vía
    :func:`shared.theme_qt.nm_icon` (compat durante migración).
    """

    def __init__(
        self,
        name: str,
        size: int = 24,
        color: str | None = None,
        color_key: str | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._name = name
        self._size = size
        self._color = color
        self._color_key = color_key
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._render()
        if color_key is not None:
            _tm().theme_changed.connect(self._apply_theme)

    # ── API ───────────────────────────────────────────────────────────────────

    def set_name(self, name: str):
        if name != self._name:
            self._name = name
            self._render()

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self.setFixedSize(size, size)
            self._render()

    def set_color(self, color: str):
        """Color hex estático (desactiva tracking de theme)."""
        self._color = color
        self._color_key = None
        try:
            _tm().theme_changed.disconnect(self._apply_theme)
        except (RuntimeError, TypeError):
            pass
        self._render()

    def set_color_key(self, key: str):
        """Color seguido a través de la paleta v3 (theme-aware)."""
        if self._color_key is None and key is not None:
            _tm().theme_changed.connect(self._apply_theme)
        self._color_key = key
        self._render()

    # ── render ───────────────────────────────────────────────────────────────

    def _resolve_color(self) -> str:
        if self._color_key is not None:
            return v3c(self._color_key, self._modo).name()
        if self._color:
            return self._color
        return v3c("text", self._modo).name()

    def _render(self):
        col = self._resolve_color()
        pix = None
        if _nm_svg_pixmap is not None and _has_v3_icon(self._name):
            pix = _nm_svg_pixmap(self._name, col, self._size)
        if pix is None or pix.isNull():
            # Fallback QtAwesome via nm_icon legacy
            icon = nm_icon(self._name, col, self._size)
            pix = icon.pixmap(self._size, self._size)
        self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()


# ── NMMoodEmoji ───────────────────────────────────────────────────────────────

try:
    from shared.icons_svg import nm_mood_pixmap as _nm_mood_pixmap
except ImportError:
    try:
        from icons_svg import nm_mood_pixmap as _nm_mood_pixmap  # type: ignore
    except ImportError:
        _nm_mood_pixmap = None


class NMMoodEmoji(QLabel):
    """Emoji de mood v3 — 10 niveles, SVG line-style.

    Spec del README (sección "Mood emoji system"):
      - Círculo de línea del color ``palette[lv]['to']``, sin relleno.
      - Ojos (2 círculos), boca curva (path varía con nivel).
      - Cejas inclinadas en niveles 1-3 y 9-10.
      - Lágrimas en 1-2, blush en 7-10, sparkles en 9-10 (+ corona en 10).
      - Halo radial opcional detrás (más fuerte en dark: 0.22 vs 0.15).

    El emoji es **100% SVG inline** — no usa Apple Color Emoji ni Unicode,
    coherente con el lenguaje visual del resto de iconos v3.

    Args:
        level: 1-10 (se clampa).
        size:  lado en px.
        glow:  halo radial detrás (default True).
        modo:  override de tema; afecta intensidad del halo.
    """

    def __init__(
        self, level: int = 5, size: int = 64, glow: bool = True, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._size = size
        self._glow = bool(glow)
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._render()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API ──────────────────────────────────────────────────────────────────

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level:
            self._level = lv
            self._render()

    def level(self) -> int:
        return self._level

    def set_size(self, size: int):
        if size != self._size:
            self._size = size
            self.setFixedSize(size, size)
            self._render()

    def set_glow(self, glow: bool):
        if bool(glow) != self._glow:
            self._glow = bool(glow)
            self._render()

    # ── render ───────────────────────────────────────────────────────────────

    def _render(self):
        if _nm_mood_pixmap is None:
            return
        is_dark = "dark" in self._modo
        pix = _nm_mood_pixmap(self._level, self._size, glow=self._glow, is_dark=is_dark)
        if pix is not None and not pix.isNull():
            self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()


# ── NMSegmentedChoice ─────────────────────────────────────────────────────────


class NMSegmentedChoice(QWidget):
    """Grupo de NMButtonOutline con selección exclusiva. Emite choice_made(str)."""

    choice_made = pyqtSignal(str)

    def __init__(self, choices: list[tuple[str, str]], modo: str = "dark_hybrid", parent=None):
        """
        choices: lista de (label, value). Ej: [("Hecha", "hecha"), ("No pude", "no_pude")]
        """
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._btns: dict[str, NMButtonOutline] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # 4px per F2.2 — reduced from 6px
        for label, value in choices:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=True)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(72)
            btn.clicked.connect(lambda checked=False, v=value, b=btn: self._select(v, b))
            layout.addWidget(btn)
            self._btns[value] = btn
        layout.addStretch()

    def _select(self, value: str, active_btn: NMButtonOutline):
        for v, btn in self._btns.items():
            btn.set_active(btn is active_btn)
        self.choice_made.emit(value)

    def selected(self) -> str:
        for v, btn in self._btns.items():
            if btn.is_active():
                return v
        return ""

    def reset(self):
        for btn in self._btns.values():
            btn.set_active(False)


# ═══════════════════════════════════════════════════════════════════════════════
# NMCustomCheck / NMActivityCard / Timer helpers


class _NMAnimCheckBox(QWidget):
    """Caja 20×20 con checkmark que se dibuja progresivamente (220ms OutCubic).

    Uso interno de NMCustomCheck. No usar directamente.
    """

    # Geometría del checkmark en espacio 20×20
    _P0 = (4.0, 11.0)   # inicio (izquierda)
    _P1 = (8.0, 15.0)   # vértice inferior (punto de quiebre)
    _P2 = (16.0, 5.0)   # final (derecha arriba)

    import math as _math
    _SEG1 = _math.sqrt((_P1[0]-_P0[0])**2 + (_P1[1]-_P0[1])**2)  # ≈ 5.66
    _SEG2 = _math.sqrt((_P2[0]-_P1[0])**2 + (_P2[1]-_P1[1])**2)  # ≈ 12.81
    _TOTAL = _SEG1 + _SEG2
    _T1 = _SEG1 / _TOTAL   # ≈ 0.306 — fracción donde termina el primer trazo

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._checked = False
        self._draw_t = 0.0
        self._anim: QPropertyAnimation | None = None
        self.setFixedSize(20, 20)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_draw_t(self) -> float:
        return self._draw_t

    def _set_draw_t(self, v: float) -> None:
        self._draw_t = max(0.0, min(1.0, v))
        self.update()

    draw_t = pyqtProperty(float, _get_draw_t, _set_draw_t)

    # ── API ───────────────────────────────────────────────────────────────────

    def set_checked_animated(self, checked: bool) -> None:
        """Marcar con animación (uso en interacción del usuario)."""
        self._checked = checked
        if checked:
            self._draw_t = 0.0
            if self._anim:
                try:
                    self._anim.stop()
                except RuntimeError:
                    pass
            a = QPropertyAnimation(self, b"draw_t", self)
            a.setDuration(ANIM["medium"])
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.Type.OutCubic)
            a.finished.connect(lambda: setattr(self, "_anim", None))
            self._anim = a
            a.start()
        else:
            if self._anim:
                try:
                    self._anim.stop()
                except RuntimeError:
                    pass
                self._anim = None
            self._draw_t = 0.0
            self.update()

    def set_checked_instant(self, checked: bool) -> None:
        """Establecer estado sin animación (inicialización programática)."""
        if self._anim:
            try:
                self._anim.stop()
            except RuntimeError:
                pass
            self._anim = None
        self._checked = checked
        self._draw_t = 1.0 if checked else 0.0
        self.update()

    def set_modo(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self.update()

    # ── render ────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        border_col = v3c("teal" if self._checked else "borderStrong", self._modo)
        bg_col = QColor(v3c("teal", self._modo)) if self._checked else QColor(0, 0, 0, 0)

        p.setPen(QPen(border_col, 2.0))
        p.setBrush(QBrush(bg_col))
        p.drawRoundedRect(QRectF(1, 1, 18, 18), 5, 5)

        if self._checked and self._draw_t > 0.001:
            ink = v3c("bg", self._modo)
            # Trazo más grueso en light: el bg del botón es más claro, necesita más peso
            ck_width = 2.0 if "dark" in self._modo else 2.5
            pen = QPen(ink, ck_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            t = self._draw_t
            x0, y0 = self._P0
            x1, y1 = self._P1
            x2, y2 = self._P2

            if t <= self._T1:
                prog = t / max(1e-9, self._T1)
                p.drawLine(QPointF(x0, y0), QPointF(x0 + (x1-x0)*prog, y0 + (y1-y0)*prog))
            else:
                p.drawLine(QPointF(x0, y0), QPointF(x1, y1))
                prog = (t - self._T1) / max(1e-9, 1.0 - self._T1)
                p.drawLine(QPointF(x1, y1), QPointF(x1 + (x2-x1)*prog, y1 + (y2-y1)*prog))

        p.end()


class NMCustomCheck(QWidget):
    """Checklist row matching the HTML `.check-item` / `.cbox` pattern."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        text: str,
        checked: bool = False,
        modo: str = None,
        parent=None,
        strike_on_check: bool = True,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._checked = checked
        self._strike_on_check = strike_on_check
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, V3_SP["sm"], 0, V3_SP["sm"])
        lay.setSpacing(V3_SP["md"])
        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self._box = _NMAnimCheckBox(self._modo)
        lay.addWidget(self._box)
        self.setAccessibleName(text)
        if checked:
            self._box.set_checked_instant(True)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_checked(self, checked: bool):
        self._checked = checked
        self._box.set_checked_instant(checked)
        self._apply_theme(self._modo)

    def is_checked(self) -> bool:
        return self._checked

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self.set_checked(checked)

    def setText(self, text: str):
        self._label.setText(text)

    def text(self) -> str:
        return self._label.text()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._checked = not self._checked
            self._box.set_checked_animated(self._checked)
            self._apply_theme(self._modo)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        try:
            from shared.theme_qt import v3c
            text_col = (
                v3c("ink_secondary", self._modo).name()
                if self._checked
                else v3c("text2", self._modo).name()
            )
        except ImportError:
            text_col = C("text_secondary", self._modo)

        self._box.set_modo(self._modo)
        decoration = "line-through" if self._checked and self._strike_on_check else "none"
        self._label.setStyleSheet(
            f"color: {text_col}; background: transparent; text-decoration: {decoration};"
        )


class NMActivityCard(QFrame):
    """Card de actividad con barra izquierda y acciones exclusivas."""

    completed = pyqtSignal()
    skipped = pyqtSignal()

    def __init__(
        self,
        title: str,
        description: str,
        category: str = "Autocuidado",
        completed: bool = False,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._category = category
        self._completed = completed
        self._accent = CATEGORY_COLORS.get(category, C("accent", self._modo))
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 12, 12)
        lay.setSpacing(5)
        self._name_lbl = QLabel(title)
        self._name_lbl.setFont(qfont("size_small", bold=True))
        lay.addWidget(self._name_lbl)
        self._desc_lbl = QLabel(description)
        self._desc_lbl.setFont(qfont("size_caption"))
        self._desc_lbl.setWordWrap(True)
        lay.addWidget(self._desc_lbl)
        row = QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 0)
        row.setSpacing(6)
        self._yes_btn = QPushButton()
        self._yes_btn.setFixedHeight(24)
        self._yes_btn.clicked.connect(self._complete)
        row.addWidget(self._yes_btn)
        self._no_btn = QPushButton("\u00d7 No es para mi")
        self._no_btn.setFixedHeight(24)
        self._no_btn.clicked.connect(lambda _=False: self.skipped.emit())
        row.addWidget(self._no_btn)
        row.addStretch()
        lay.addLayout(row)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _complete(self):
        self.set_completed(True)
        self.completed.emit()
        # Flash del botón: dim → bright (feedback táctil sin overlay)
        fx = QGraphicsOpacityEffect(self._yes_btn)
        self._yes_btn.setGraphicsEffect(fx)
        a = QPropertyAnimation(fx, b"opacity", self._yes_btn)
        a.setDuration(ANIM["fast"])
        a.setKeyValueAt(0.0, 1.0)
        a.setKeyValueAt(0.35, 0.35)
        a.setKeyValueAt(1.0, 1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.finished.connect(lambda: self._yes_btn.setGraphicsEffect(None)
                           if not sip.isdeleted(self._yes_btn) else None)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def set_completed(self, completed: bool):
        self._completed = completed
        self._apply_theme(self._modo)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS_CARD, RADIUS_CARD)
        p.fillPath(path, QColor(c["bg_surface"]))
        p.setPen(QPen(QColor(c.get("border_card", c["border"])), 1))
        p.drawPath(path)
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, 0, 3, self.height()), 3, 3)
        p.fillPath(bar, QColor(self._accent))
        if self._completed:
            p.fillPath(path, QColor(0, 0, 0, 80 if "dark" in self._modo else 20))
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self._name_lbl.setStyleSheet(label_style(self._modo, "text_primary"))
        self._desc_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._yes_btn.setText("\u2713 Completado" if self._completed else "\u2713 Hice esto")
        self._yes_btn.setStyleSheet(
            f"QPushButton {{ background: {_rgba(self._accent, 0.14)}; color: {self._accent}; "
            f"border: none; border-radius: 8px; padding: 4px 12px; "
            f"font-size: {TYPOGRAPHY['size_caption']}px; font-weight: 500; }}"
        )
        self._no_btn.setVisible(not self._completed)
        self._no_btn.setStyleSheet(
            f"QPushButton {{ background: {c['bg_elevated']}; color: {c['text_tertiary']}; "
            f"border: none; border-radius: 8px; padding: 4px 12px; "
            f"font-size: {TYPOGRAPHY['size_caption']}px; font-weight: 500; }}"
        )
        self.update()


class NMPresetChip(QPushButton):
    """Chip de preset del timer."""

    def __init__(self, text: str, active: bool = False, modo: str = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active = active
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small"))
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_active(self, active: bool):
        self._active = active
        self._apply_theme(self._modo)

    def is_active(self) -> bool:
        return self._active

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        accent_hex = C("accent", self._modo)
        if self._active:
            bg = _rgba(accent_hex, 0.13 if is_dark else 0.10)
            border = _rgba(accent_hex, 0.32 if is_dark else 0.28)
            col = accent_hex
        else:
            bg = "transparent"
            bdr_c = v3c("border", self._modo)
            border = f"rgba({bdr_c.red()},{bdr_c.green()},{bdr_c.blue()},180)"
            col = v3c("text2", self._modo).name()  # was text_tertiary — too dim
        # Hover: elevated surface + full text contrast
        elev_c = v3c("elevated" if not is_dark else "elevatedSolid", self._modo)
        hover_bg = (
            f"rgba({elev_c.red()},{elev_c.green()},{elev_c.blue()},200)"
            if not is_dark
            else elev_c.name()
        )
        text_hex = v3c("text", self._modo).name()
        self._pill_r_applied = pill_radius(self, fallback=30)
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {col}; border: 1px solid {border}; "
            f"border-radius: {self._pill_r_applied}px; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {hover_bg}; color: {text_hex}; }}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=30) != getattr(self, "_pill_r_applied", None):
            self._apply_theme(self._modo)


class NMFocusArc(QWidget):
    """Arco circular de foco con aura, texto central, pulse y blink."""

    def __init__(self, size: int = 160, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct = 0.0
        self._time_text = "25:00"
        self._state_text = "listo"
        # Efectos animados
        self._pulse_intensity = 0.0   # 0..1 — modula aura y glow mientras corre
        self._blink_on = True          # False = frame apagado en los últimos 10s
        self._anim_pulse: QPropertyAnimation | None = None
        self._blink_timer: QTimer | None = None
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_pulse_intensity(self) -> float:
        return self._pulse_intensity

    def _set_pulse_intensity(self, v: float) -> None:
        self._pulse_intensity = max(0.0, min(1.0, v))
        self.update()

    pulse_intensity = pyqtProperty(float, _get_pulse_intensity, _set_pulse_intensity)

    # ── API de datos ──────────────────────────────────────────────────────────

    def set_data(self, pct: float, time_text: str, state_text: str | None = None):
        self._pct = max(0.0, min(1.0, pct))
        self._time_text = time_text
        self.update()

    def update_data(self, progress: float, time_text: str):
        self.set_data(progress, time_text, self._state_text)

    # ── Animaciones de estado ─────────────────────────────────────────────────

    def start_pulse(self):
        """Aura que respira lentamente mientras el timer corre (loop infinito)."""
        self._state_text = "en curso"
        self._blink_on = True
        if self._anim_pulse is not None:
            return
        a = QPropertyAnimation(self, b"pulse_intensity", self)
        a.setDuration(ANIM["pulse"])
        a.setLoopCount(-1)
        a.setKeyValueAt(0.0, 0.15)
        a.setKeyValueAt(0.5, 1.0)
        a.setKeyValueAt(1.0, 0.15)
        a.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim_pulse = a
        a.start()

    def stop_pulse(self):
        """Pausa el timer — congela el pulso en base."""
        self._state_text = "pausado"
        self._stop_pulse_anim()
        self.update()

    def start_blink(self):
        """Parpadeo urgente para los últimos 10 s (coexiste con el pulse)."""
        if self._blink_timer is not None:
            return
        t = QTimer(self)
        t.setInterval(ANIM["blink"])
        t.timeout.connect(self._on_blink_tick)
        self._blink_timer = t
        t.start()

    def stop_blink(self):
        if self._blink_timer is not None:
            self._blink_timer.stop()
            self._blink_timer = None
        self._blink_on = True
        self.update()

    def _on_blink_tick(self) -> None:
        self._blink_on = not self._blink_on
        self.update()

    def show_finish(self):
        self._stop_all_anims()
        self.set_data(1.0, "00:00", "terminado")

    def reset(self):
        self._stop_all_anims()
        self.set_data(0.0, self._time_text, "listo")

    def _stop_pulse_anim(self) -> None:
        if self._anim_pulse is not None:
            try:
                self._anim_pulse.stop()
            except RuntimeError:
                pass
            self._anim_pulse = None
        self._pulse_intensity = 0.0

    def _stop_all_anims(self) -> None:
        self._stop_pulse_anim()
        self.stop_blink()

    # ── paintEvent ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        cx = cy = w / 2
        is_dark = "dark" in self._modo

        # ── Sección arc+aura: opacidad en blink-off (más alto en light para visibilidad)
        p.setOpacity(0.22 if not self._blink_on else 1.0)

        # Aura radial — radio y alpha adaptativos al tema
        base_alpha = 0.18 if is_dark else 0.11
        pulse_boost = 0.10 if is_dark else 0.07   # boost más sutil en light
        aura_alpha = min(1.0, base_alpha + self._pulse_intensity * pulse_boost)
        aura_r = w * (0.42 + self._pulse_intensity * 0.03)
        aura = QRadialGradient(QPointF(cx, cy), aura_r)
        ac = QColor(v3c("teal", self._modo))
        ac.setAlphaF(aura_alpha)
        aura.setColorAt(0.0, ac)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(aura)
        p.drawEllipse(QPointF(cx, cy), aura_r, aura_r)

        # Track sutil
        pen_w = _ring_stroke(w)
        r = w / 2 - pen_w - 1
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        track_col = v3c("borderSoft", self._modo)
        p.setPen(QPen(track_col, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Arco progreso con glow — glow se intensifica con pulse
        if self._pct > 0.001:
            glow_w = pen_w + 6
            glow_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            base_glow = 40 if is_dark else 22
            pulse_glow = 40 if is_dark else 22   # amplitud del pulso también más sutil en light
            glow_col = QColor(v3c("teal", self._modo))
            glow_col.setAlpha(int(base_glow + self._pulse_intensity * pulse_glow))
            p.setPen(QPen(glow_col, glow_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.drawArc(glow_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            if is_dark:
                glow_col2 = QColor(v3c("violet", self._modo))
                glow_col2.setAlpha(int(25 + self._pulse_intensity * 25))
                p.setPen(QPen(glow_col2, glow_w - 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawArc(glow_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            _paint_v3_arc(p, rect, 90.0, -360.0 * self._pct, pen_w, self._modo)

        # ── Tiempo central: siempre 100% opacidad para ser legible ───────────
        p.setOpacity(1.0)
        time_pt = max(16, int(w * 0.15))
        p.setPen(v3c("text", self._modo))
        try:
            from shared.theme_qt import v3_font as _v3_font
            p.setFont(_v3_font(time_pt, weight=TYPOGRAPHY["weight_medium"], serif=True))
        except ImportError:
            p.setFont(qfont_mono(time_pt, bold=True))
        p.drawText(QRectF(0, 0, w, w), Qt.AlignmentFlag.AlignCenter, self._time_text)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


class NMSessionHistory(QWidget):
    """Footer de chips de sesiones de hoy."""

    def __init__(self, title: str = "Sesiones de hoy", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(7)
        self._label = QLabel(title)
        self._label.setFont(qfont("size_caption"))
        lay.addWidget(self._label)
        self._row = QHBoxLayout()
        self._row.setSpacing(6)
        self._row.addStretch()
        lay.addLayout(self._row)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_sessions(self, sessions: list[str]):
        while self._row.count() > 1:
            item = self._row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for text in sessions:
            chip = QLabel(text)
            chip.setFont(qfont("size_caption"))
            chip.setContentsMargins(11, 4, 11, 4)
            chip.setStyleSheet(self._chip_style())
            self._row.insertWidget(self._row.count() - 1, chip)

    def _chip_style(self) -> str:
        c = colors(self._modo)
        return (
            f"QLabel {{ background: {c['bg_elevated']}; color: {c['text_tertiary']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: 10px; padding: 4px 11px; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(f"border-top: 1px solid {C('border', self._modo)};")
        self._label.setStyleSheet(label_style(self._modo, "text_tertiary"))
        for chip in self.findChildren(QLabel):
            if chip is not self._label:
                chip.setStyleSheet(self._chip_style())


# COMPONENTES V3 — Design System Mayo 2026
# ═══════════════════════════════════════════════════════════════════════════════

# ── NMProgressLine ────────────────────────────────────────────────────────────


class NMProgressLine(QWidget):
    """Línea de progreso ultra-fina (2 px, full-width) con gradiente teal→violet.

    Uso: colocar en borde superior del área de contenido de módulos y Hub.
    """

    def __init__(self, total: int = 1, current: int = 0, modo: str = None, parent=None):
        super().__init__(parent)
        self._total = max(1, total)
        self._current = current
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedHeight(2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_progress(self, current: int, total: int = None):
        if total is not None:
            self._total = max(1, total)
        self._current = current
        self.update()

    @property
    def pct(self) -> float:
        return min(1.0, max(0.0, self._current / self._total))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        fill_w = int(w * self.pct)
        # Track: V3 border token — warm stone (light) / dark navy (dark)
        track = v3c("border", self._modo)
        track.setAlpha(80)
        p.fillRect(0, 0, w, h, track)
        if fill_w > 0:
            # F5 ADN Claude: fill `primary` sólido (lo lineal va plano).
            p.fillRect(0, 0, fill_w, h, v3c("primary", self._modo))
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMStreakBadge ─────────────────────────────────────────────────────────────


class NMStreakBadge(QLabel):
    """Pill badge de racha diaria — paleta brand teal, sin emoji.

    Muestra '● N días' con color teal y fondo accent_soft.
    Se oculta automáticamente si days <= 0.
    """

    def __init__(self, days: int = 0, modo: str = None, parent=None):
        super().__init__(parent)
        self._days = days
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(10, 0, 10, 0)
        self._update_text()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_days(self, days: int):
        self._days = days
        self._update_text()
        self._apply_theme(self._modo)

    def _update_text(self):
        if self._days <= 0:
            self.setText("")
            self.hide()
        else:
            suffix = "s" if self._days != 1 else ""
            self.setText(f"●  {self._days} día{suffix}")
            self.show()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        teal = v3c("teal", self._modo)
        bg = v3c("accent_soft", self._modo)
        border_c = QColor(teal)
        border_c.setAlpha(70)
        self._pill_r_applied = pill_radius(self, fallback=22)
        self.setStyleSheet(f"""
            QLabel {{
                color: {teal.name()};
                background-color: {bg.name()};
                border-radius: {self._pill_r_applied}px;
                border: 1px solid rgba({border_c.red()},{border_c.green()},{border_c.blue()},70);
                padding: 1px 10px;
                font-size: {TYPOGRAPHY["size_small"]}px;
                font-weight: 500;
            }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=22) != getattr(self, "_pill_r_applied", None):
            self._apply_theme(self._modo)


# ── NMWelcomeBar ──────────────────────────────────────────────────────────────


class NMWelcomeBar(QWidget):
    """Tarjeta de bienvenida accent: '✨ Bienvenida de vuelta / ¿Empezamos?'.

    Se usa debajo del saludo en HomeView.
    """

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        lay.setSpacing(sp("sm"))

        icon_lbl = QLabel("✨")
        icon_lbl.setFont(qfont("size_h3"))
        icon_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel("Bienvenida de vuelta")
        self._title_lbl.setFont(qfont("size_small", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        text_col.addWidget(self._title_lbl)

        self._sub_lbl = QLabel("Tu última sesión fue ayer. ¿Empezamos?")
        self._sub_lbl.setFont(qfont("size_caption"))
        self._sub_lbl.setStyleSheet("background: transparent;")
        text_col.addWidget(self._sub_lbl)

        lay.addLayout(text_col, stretch=1)

        self._action_lbl = QLabel("Comenzar →")
        self._action_lbl.setFont(qfont("size_caption", bold=True))
        self._action_lbl.setStyleSheet("background: transparent;")
        self._action_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self._action_lbl)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def refresh(self):
        pass

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        accent = C("accent", self._modo)
        c = QColor(accent)
        bg_r, bg_g, bg_b = c.red(), c.green(), c.blue()
        self.setStyleSheet(f"""
            NMWelcomeBar {{
                background-color: rgba({bg_r},{bg_g},{bg_b},20);
                border: 1px solid rgba({bg_r},{bg_g},{bg_b},51);
                border-radius: {RADIUS_INPUT}px;
            }}
        """)
        self._title_lbl.setStyleSheet(f"color: {accent}; background: transparent;")
        self._sub_lbl.setStyleSheet(
            f"color: {C('text_tertiary', self._modo)}; background: transparent;"
        )
        self._action_lbl.setStyleSheet(f"color: {accent}; background: transparent;")


# ── NMEmojiPicker ─────────────────────────────────────────────────────────────


class NMEmojiPicker(QWidget):
    """5 botones circulares de emoji para selección de estado de ánimo (1-10).

    Emite picked(int) con el puntaje seleccionado. Las etiquetas aparecen
    debajo de la fila de botones, no sobre ellos.
    """

    picked = pyqtSignal(int)

    _CHIPS = [
        ("\U0001f61e", "Muy bajo", 1),
        ("\U0001f615", "Bajo", 3),
        ("\U0001f610", "Neutro", 5),
        ("\U0001f642", "Bien", 7),
        ("\U0001f604", "Excelente", 9),
    ]

    _BTN_SIZE = 48

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected: int | None = None
        self._btns: list[QPushButton] = []
        self._labels: list[QLabel] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(sp("sm"))

        for i, (emoji, label, score) in enumerate(self._CHIPS):
            btn = QPushButton(emoji)
            btn.setFixedSize(self._BTN_SIZE, self._BTN_SIZE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i, sc=score: self._select(idx, sc))
            btn_row.addWidget(btn)
            self._btns.append(btn)

        btn_row.addStretch()
        outer.addLayout(btn_row)

        lbl_row = QHBoxLayout()
        lbl_row.setContentsMargins(0, 0, 0, 0)
        lbl_row.setSpacing(sp("sm"))

        for _, label, _ in self._CHIPS:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(self._BTN_SIZE)
            lbl_row.addWidget(lbl)
            self._labels.append(lbl)

        lbl_row.addStretch()
        outer.addLayout(lbl_row)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _select(self, idx: int, score: int):
        self._selected = idx
        self._apply_theme(self._modo)
        self.picked.emit(score)

    def selected_score(self) -> int | None:
        return self._CHIPS[self._selected][2] if self._selected is not None else None

    def set_score(self, score: int):
        for i, (_, _, sc) in enumerate(self._CHIPS):
            if score <= sc + 1:
                self._selected = i
                break
        self._apply_theme(self._modo)

    def reset(self):
        self._selected = None
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        teal = C("teal", self._modo)
        border = C("border", self._modo)
        bg_el = C("bg_elevated", self._modo)
        bg_ov = C("bg_overlay", self._modo)
        txt_s = C("text_secondary", self._modo)
        r = self._BTN_SIZE // 2

        for i, (btn, lbl) in enumerate(zip(self._btns, self._labels)):
            is_sel = i == self._selected
            if is_sel:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: 2px solid {teal};
                        border-radius: {r}px;
                        font-size: 18px;
                    }}
                    QPushButton:hover {{ background: {bg_ov}; }}
                """)
                lbl.setStyleSheet(
                    f"color: {teal}; font-weight: 500; font-size: {TYPOGRAPHY['size_caption']}px;"
                )
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg_el};
                        border: 1px solid {border};
                        border-radius: {r}px;
                        font-size: 17px;
                    }}
                    QPushButton:hover {{
                        background: {bg_ov};
                        border-color: {teal};
                    }}
                """)
                lbl.setStyleSheet(f"color: {txt_s}; font-size: {TYPOGRAPHY['size_caption']}px;")


# ── NMWaveChart ───────────────────────────────────────────────────────────────


class NMWaveChart(QWidget):
    """Gráfico de área dual-serie para el módulo Ánimo.

    Serie teal = principal. Serie secundaria configurable por token
    (`secondary_color_key`, default violet p/ "semana anterior"; el módulo
    Ánimo la usa en danger para la serie NEGATIVA, en paralelo a la positiva).
    `series_labels=(lbl1, lbl2)` pinta una leyenda discreta arriba a la derecha.
    Emite week_changed(int) con offset de semana (0=actual, -1=anterior…).
    """

    week_changed = pyqtSignal(int)

    def __init__(
        self,
        modo: str = None,
        parent=None,
        secondary_color_key: str = "violet",
        series_labels: tuple[str, str] | None = None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._data_current: list[float | None] = [None] * 7
        self._data_previous: list[float | None] = [None] * 7
        self._secondary_color_key = secondary_color_key
        self._series_labels = series_labels
        self._week_offset = 0
        self._hover_idx = -1
        self._labels = ["L", "M", "M", "J", "V", "S", "D"]

        self.setMinimumHeight(140)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_data(self, current: list, previous: list):
        self._data_current = list(current[:7])
        self._data_previous = list(previous[:7])
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        n = len(self._data_current)
        if n < 2:
            return
        ml, mr = 32, 16
        step = (self.width() - ml - mr) / max(1, n - 1)
        idx = round((event.pos().x() - ml) / step)
        idx = max(0, min(n - 1, idx))
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        colors(self._modo)
        ml, mr = 32, 16
        # mt ampliado: la leyenda (●Positivo ●Negativo) y el label "10" del eje
        # vivían pegados al borde superior (y≈1) y se cortaban. Con una banda
        # propia arriba del gridline ya no se recortan. Aplica a todos los usos
        # del chart (pos/neg en Ánimo, semana previa, etc.).
        mt, mb = 34, 28
        cw = w - ml - mr
        ch = h - mt - mb

        teal_hex = C("teal", self._modo)
        violet_hex = C(self._secondary_color_key, self._modo)

        # Faint grid — incluye la línea de base 0 (feedback owner: sin ella la
        # escala quedaba asimétrica respecto de 5 y 10).
        for row in range(0, 5):
            y_grid = mt + ch - (ch * row / 4)
            gc = QColor(v3c("border", self._modo).name())
            gc.setAlpha(35)
            p.setPen(QPen(gc, 1, Qt.PenStyle.DotLine))
            p.drawLine(ml, int(y_grid), w - mr, int(y_grid))

        def _pts(data):
            result = []
            n = len(data)
            for i, v in enumerate(data):
                if v is None:
                    continue
                x = ml + (i / max(1, n - 1)) * cw
                y = mt + ch - (v / 10.0) * ch
                result.append(QPointF(x, y))
            return result

        def _draw_area(pts, color_hex, alpha_fill=50, alpha_line=190):
            if len(pts) < 2:
                return
            bottom_y = mt + ch
            poly_pts = [QPointF(pts[0].x(), bottom_y)]
            poly_pts += pts
            poly_pts.append(QPointF(pts[-1].x(), bottom_y))
            poly = QPolygonF(poly_pts)
            path = QPainterPath()
            path.addPolygon(poly)
            fill_grad = QLinearGradient(0, mt, 0, mt + ch)
            fc = QColor(color_hex)
            fc.setAlpha(alpha_fill)
            ec = QColor(color_hex)
            ec.setAlpha(0)
            fill_grad.setColorAt(0.0, fc)
            fill_grad.setColorAt(1.0, ec)
            p.fillPath(path, QBrush(fill_grad))
            lc = QColor(color_hex)
            lc.setAlpha(alpha_line)
            p.setPen(QPen(lc, 2.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            line_path = QPainterPath()
            line_path.moveTo(pts[0])
            for pt in pts[1:]:
                line_path.lineTo(pt)
            p.drawPath(line_path)

        is_dark = "dark" in self._modo
        # Con leyenda (modo pos/neg) la serie secundaria se dibuja con más
        # presencia: es un dato en paralelo, no un eco de la semana anterior.
        sec_alpha_line = 170 if self._series_labels else 90
        sec_alpha_fill = (38 if is_dark else 30) if self._series_labels else (31 if is_dark else 26)
        prev_pts = _pts(self._data_previous)
        _draw_area(prev_pts, violet_hex, alpha_fill=sec_alpha_fill, alpha_line=sec_alpha_line)

        curr_pts = _pts(self._data_current)
        _draw_area(curr_pts, teal_hex, alpha_fill=64 if is_dark else 46, alpha_line=210)

        # Dots — ambas series cuando hay leyenda (pos/neg en paralelo)
        if self._series_labels:
            p.setBrush(QBrush(QColor(violet_hex)))
            p.setPen(Qt.PenStyle.NoPen)
            for pt in prev_pts:
                p.drawEllipse(pt, 3, 3)
        p.setBrush(QBrush(QColor(teal_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        for i, pt in enumerate(curr_pts):
            r = 5 if i == self._hover_idx else 3
            p.drawEllipse(pt, r, r)

        # Leyenda discreta arriba a la derecha: ● lbl1  ● lbl2
        if self._series_labels:
            p.setFont(qfont("size_caption_xs"))
            fm = p.fontMetrics()
            lbl1, lbl2 = self._series_labels
            seg_gap, dot_r = 10, 3
            x_cursor = w - mr
            for text, hexc in ((lbl2, violet_hex), (lbl1, teal_hex)):
                tw_lbl = fm.horizontalAdvance(text)
                x_cursor -= tw_lbl
                p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
                p.drawText(
                    QRectF(x_cursor, 6, tw_lbl, 14),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    text,
                )
                x_cursor -= dot_r * 2 + 4
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(hexc)))
                p.drawEllipse(QPointF(x_cursor + dot_r, 13), dot_r, dot_r)
                x_cursor -= seg_gap

        # Hover tooltip
        if 0 <= self._hover_idx < len(self._data_current):
            val = self._data_current[self._hover_idx]
            if val is not None:
                n_cur = len(self._data_current)
                pt = QPointF(
                    ml + (self._hover_idx / max(1, n_cur - 1)) * cw,
                    mt + ch - (val / 10.0) * ch,
                )
                is_today = self._hover_idx == len(self._data_current) - 1
                tip_text = f"Hoy: {val:.0f}" if is_today else f"{val:.0f}/10"
                tw, th = 60, 22
                tx = min(pt.x() - tw / 2, w - mr - tw)
                ty = max(float(mt), pt.y() - th - 8)
                tip_bg = QColor(v3c("elevated", self._modo).name())
                tip_bg.setAlpha(220)
                tip_r = QRectF(tx, ty, tw, th)
                tip_path = QPainterPath()
                tip_path.addRoundedRect(tip_r, RADIUS_SMALL, RADIUS_SMALL)
                p.fillPath(tip_path, tip_bg)
                p.setPen(QColor(v3c("text", self._modo).name()))
                p.setFont(qfont("size_small"))
                p.drawText(tip_r, Qt.AlignmentFlag.AlignCenter, tip_text)

        # Y-axis labels — escala completa 10/5/0 (feedback owner v1.0: sin el
        # 0 la escala quedaba coja en todos los diagramas).
        p.setFont(qfont("size_caption_xs"))
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        for y_val in (10, 5, 0):
            y_pos = mt + ch - (y_val / 10.0) * ch
            p.drawText(
                QRectF(0, y_pos - 7, ml - 4, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(y_val),
            )

        # Day labels
        p.setPen(QColor(v3c("ink_secondary", self._modo).name()))
        p.setFont(qfont("size_caption"))
        n = len(self._labels)
        for i, lbl in enumerate(self._labels):
            x = ml + (i / max(1, n - 1)) * cw
            p.drawText(QRectF(x - 12, h - mb + 4, 24, 14), Qt.AlignmentFlag.AlignCenter, lbl)

        p.restore()
        p.end()


# ── NMPhaseChip ───────────────────────────────────────────────────────────────


class NMPhaseChip(QWidget):
    """Fila de 3 chips de fase para la respiración: Inhala / Mantén / Exhala.

    El chip activo se ilumina con fondo teal. Llama a set_phase(key).
    keys: 'inhala' | 'manten' | 'exhala' | None
    """

    _PHASES = [
        ("Inhala ↑ 4s", "inhala"),
        ("Mantén 7s", "manten"),
        ("Exhala ↓ 8s", "exhala"),
    ]

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active: str | None = None
        self._chips: dict[str, QLabel] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(sp("sm"))

        for label, key in self._PHASES:
            chip = QLabel(label)
            chip.setFont(qfont("size_small"))
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chip.setFixedHeight(32)
            chip.setMinimumWidth(90)
            chip.setContentsMargins(12, 0, 12, 0)
            self._chips[key] = chip
            lay.addWidget(chip)

        lay.addStretch()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_phase(self, phase: str | None):
        self._active = phase
        self._apply_theme(self._modo)

    _PHASE_COLOR_KEY = {
        "inhala": "teal",
        "manten": "accent",
        "exhala": "violet",
    }

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for key, chip in self._chips.items():
            active = key == self._active
            phase_color = C(self._PHASE_COLOR_KEY.get(key, "teal"), self._modo)
            if active:
                bg = phase_color
                col = v3c("textOnSolid", self._modo).name()
                border = phase_color
            else:
                # Estado preview: tint suave del color de fase + texto del color
                bg = _rgba(phase_color, 0.12)
                col = phase_color
                border = _rgba(phase_color, 0.25)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_BUTTON}px;
                    font-size: {TYPOGRAPHY["size_small"]}px;
                    font-weight: {"500" if active else "400"};
                }}
            """)


# ── NMCycleRing ───────────────────────────────────────────────────────────────


class NMCycleRing(QWidget):
    """Anillo de trazo pequeño con contador de ciclos de respiración.

    Columna izquierda del módulo Respiración.
    """

    def __init__(self, size: int = 56, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._cycles = 0
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_cycles(self, n: int):
        self._cycles = n
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        s = self._size
        cx, cy = s / 2, s / 2
        pen_w = _ring_stroke(s)
        r_out = s / 2 - pen_w - 1
        rect = QRectF(cx - r_out, cy - r_out, r_out * 2, r_out * 2)

        # Contorno completo con gradient firma v3 (no es progreso — siempre 360°)
        _paint_v3_arc(p, rect, 90.0, -359.99, pen_w, self._modo, segments=80)

        p.setPen(v3c("text", self._modo))
        p.setFont(qfont_mono(max(10, int(s * 0.22)), bold=False))
        # Peso semibold sin usar bold flag: usar v3_font sería ideal pero qfont_mono no
        # acepta weight; pintamos directo con la familia mono y dejamos bold=False
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, str(self._cycles))
        p.restore()
        p.end()


# ── NMCalmBadge ───────────────────────────────────────────────────────────────


class NMCalmBadge(QWidget):
    """Badge decorativo 'Calm ♥ / N BPM' para la columna derecha de Respiración."""

    def __init__(self, bpm: int = 60, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._bpm = bpm
        self._blink_alpha = 255
        self._blink_dir = -1
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(80)
        self._blink_timer.timeout.connect(self._on_blink)
        self._blink_timer.start()
        self.setObjectName("NMCalmBadge")
        # WA_StyledBackground=True para que el QSS bg/border aplique al widget
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(100)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("sm"), sp("md"), sp("sm"), sp("md"))
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._calm_lbl = QLabel("Calm ♥")
        self._calm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._calm_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._calm_lbl)

        self._bpm_lbl = QLabel(str(bpm))
        self._bpm_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bpm_lbl.setFont(qfont_mono(SIZE_TIME_LARGE, bold=True))
        lay.addWidget(self._bpm_lbl)

        self._unit_lbl = QLabel("BPM")
        self._unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit_lbl.setFont(qfont("size_caption"))
        lay.addWidget(self._unit_lbl)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_bpm(self, bpm: int):
        self._bpm = bpm
        self._bpm_lbl.setText(str(bpm))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        violet = C("violet", self._modo)
        # Selector específico #NMCalmBadge para evitar herencia del border a hijos
        # (sin esto, cada QLabel hijo se renderizaba con su propio border = chips
        # fragmentados visualmente)
        self.setStyleSheet(
            f"QWidget#NMCalmBadge {{ background: {v3c('elevated', self._modo).name()}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; }}"
            f"QWidget#NMCalmBadge QLabel {{ background: transparent; border: none; }}"
        )
        self._calm_lbl.setStyleSheet(f"color: {violet};")
        self._bpm_lbl.setStyleSheet(f"color: {violet};")
        self._unit_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )

    def _on_blink(self):
        if sip.isdeleted(self):
            self._blink_timer.stop()
            return
        self._blink_alpha += self._blink_dir * 12
        if self._blink_alpha <= 80:
            self._blink_dir = 1
            self._blink_alpha = 80
        elif self._blink_alpha >= 255:
            self._blink_dir = -1
            self._blink_alpha = 255
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(C("violet", self._modo))
        c.setAlpha(self._blink_alpha)
        p.setBrush(QBrush(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(self.width() - 14, 8, 6, 6))
        p.end()


# ── NMStepper ─────────────────────────────────────────────────────────────────


class NMStepper(QWidget):
    """Stepper horizontal de N pasos con dots de 10px, línea de 2px y labels de 12px 700."""

    def __init__(self, steps: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._steps = steps
        self._current = 0
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_step(self, idx: int):
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        n = len(self._steps)
        if n == 0:
            p.restore()
            p.end()
            return

        w, _h = self.width(), self.height()
        circle_r = 5
        cy = 16
        step_w = w / n

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            # Connector line (2px line)
            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                if i <= self._current:
                    p.setPen(QPen(QColor(v3c("primary", self._modo)), 2))
                else:
                    p.setPen(QPen(QColor(v3c("borderSolid", self._modo)), 2))
                line_gap = 2
                start_x = prev_cx + circle_r + line_gap
                end_x = cx - circle_r - line_gap
                if end_x > start_x:
                    p.drawLine(start_x, cy, end_x, cy)

            # Circle / Dot
            if i <= self._current:
                p.setBrush(QBrush(QColor(v3c("primary", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
            else:
                p.setBrush(QBrush(QColor(v3c("surface2", self._modo))))
                p.setPen(QPen(QColor(v3c("borderSolid", self._modo)), 1))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)

            # Label below dot — elidido a su columna: un paso largo (texto
            # configurable desde el Hub) colisionaba con los vecinos.
            col_txt = (
                v3c("text", self._modo) if i == self._current else v3c("ink_secondary", self._modo)
            )
            p.setPen(QColor(col_txt))
            _f = qfont("size_caption", weight=700)
            p.setFont(_f)
            _fm = QFontMetrics(_f)
            _elided = _fm.elidedText(label, Qt.TextElideMode.ElideRight, int(step_w - 8))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 6, step_w - 8, 20),
                Qt.AlignmentFlag.AlignCenter,
                _elided,
            )

        p.restore()
        p.end()


# ── NMTCCStepper ──────────────────────────────────────────────────────────────


class NMTCCStepper(QWidget):
    """Stepper horizontal de N pasos para el asistente TCC (y cualquier wizard).

    Estado por paso: pasado=verde+check, activo=accent, futuro=gris.
    """

    def __init__(self, steps: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._steps = steps
        self._current = 0
        self.setFixedHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_step(self, idx: int):
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        n = len(self._steps)
        if n == 0:
            p.restore()
            p.end()
            return

        w, _h = self.width(), self.height()
        circle_r = 14
        cy = 22
        step_w = w / n

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            # Connector line — F3+F5 ADN Claude: tramo completado en `primary`
            # SÓLIDO vía token (el gradiente lavanda→ámbar anterior tenía los
            # 6 hex duros acá y "lo lineal va plano"; gradiente queda solo en
            # lo circular/identitario).
            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                if i <= self._current:
                    p.setPen(QPen(QColor(v3c("primary", self._modo)), 2))
                else:
                    p.setPen(QPen(QColor(v3c("borderSoft", self._modo)), 2))
                p.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            # Circle
            circ_rect = QRectF(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
            if i < self._current:
                p.setBrush(QBrush(QColor(v3c("teal", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QPen(QColor(v3c("textOnSolid", self._modo)), 2))
                p.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, "✓")
            elif i == self._current:
                p.setBrush(QBrush(QColor(v3c("accent", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(v3c("textOnSolid", self._modo)))
                p.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(v3c("borderSoft", self._modo)), 2))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(v3c("ink_secondary", self._modo)))
                p.setFont(qfont("size_small"))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Label below circle — elidido a su columna: un paso largo (texto
            # configurable desde el Hub) colisionaba con los vecinos.
            col_txt = (
                v3c("text", self._modo) if i == self._current else v3c("ink_secondary", self._modo)
            )
            p.setPen(QColor(col_txt))
            _f = qfont("size_caption")
            p.setFont(_f)
            _fm = QFontMetrics(_f)
            _elided = _fm.elidedText(label, Qt.TextElideMode.ElideRight, int(step_w - 8))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 4, step_w - 8, 16),
                Qt.AlignmentFlag.AlignCenter,
                _elided,
            )

        p.restore()
        p.end()


# ── NMHeatBar ─────────────────────────────────────────────────────────────────


class NMHeatBar(QWidget):
    """Barra de intensidad con gradiente dinámico frío→tibio→caliente.

    Arrastrar o hacer click mueve el indicador.
    Emite value_changed(int) con valor 0-100.
    """

    value_changed = pyqtSignal(int)

    def __init__(self, value: int = 50, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._value = max(0, min(100, value))
        self._dragging = False
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    @property
    def value(self) -> int:
        return self._value

    def set_value(self, v: int):
        self._value = max(0, min(100, v))
        self.update()

    def _ramp(self) -> tuple[str, str, str]:
        """Rampa frío→tibio→caliente desde TOKENS por modo (F3 ADN: los hex
        web genéricos #3b82f6/#8b5cf6/#ef4444 estaban fuera de la paleta)."""
        cold = C("tcc_heat_cold", self._modo)
        hot = C("tcc_heat_hot", self._modo)
        return cold, blend_color(cold, hot, 0.5), hot

    def _color_at(self, t: float) -> QColor:
        cold, mid, hot = self._ramp()
        if t <= 0.5:
            return QColor(interpolate_color(cold, mid, t * 2))
        return QColor(interpolate_color(mid, hot, (t - 0.5) * 2))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_from_x(event.pos().x())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self._update_from_x(event.pos().x())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def _update_from_x(self, x: int):
        margin = 16
        usable = self.width() - margin * 2
        t = max(0.0, min(1.0, (x - margin) / usable))
        new_v = int(t * 100)
        if new_v != self._value:
            self._value = new_v
            self.update()
            self.value_changed.emit(self._value)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        margin = 16
        gh = 8
        gy = (h - gh) // 2
        gw = w - margin * 2

        groove_rect = QRectF(margin, gy, gw, gh)
        cold, mid, hot = self._ramp()
        grad = QLinearGradient(margin, 0, margin + gw, 0)
        grad.setColorAt(0.0, QColor(cold))
        grad.setColorAt(0.5, QColor(mid))
        grad.setColorAt(1.0, QColor(hot))
        path = QPainterPath()
        path.addRoundedRect(groove_rect, gh / 2, gh / 2)
        p.fillPath(path, grad)

        t = self._value / 100.0
        hx = margin + t * gw
        hc = self._color_at(t)
        p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
        p.setBrush(QBrush(hc))
        p.drawEllipse(QPointF(hx, gy + gh / 2), 10, 10)

        # El valor vive en el QLabel "Intensidad: N/10" (accesible al lector de
        # pantalla y en la misma escala /10). El antiguo caption "N%" pintado acá
        # era texto no accesible y en otra escala → contradicción de la auditoría.

        p.restore()
        p.end()


# ── NMRoutineSection ──────────────────────────────────────────────────────────


class NMRoutineSection(QWidget):
    """Sección colapsable de rutina con cabecera tintada de color semántico.

    section_type: 'morning' | 'afternoon' | 'night'
    Añadir ítems con content_layout().addWidget(…).
    """

    _TINTS = {
        "morning": ("routine_morning_tint", "☀️"),
        "afternoon": ("routine_afternoon_tint", "\U0001f324"),
        "night": ("routine_night_tint", "\U0001f319"),
    }

    def __init__(self, section_type: str, title: str, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._section_type = section_type
        self._collapsed = False
        self.setObjectName("NMRoutineSection")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._main_lay = QVBoxLayout(self)
        self._main_lay.setContentsMargins(0, 0, 0, 0)
        self._main_lay.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setFixedHeight(_NM_CONTROL_HEIGHT)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.mousePressEvent = lambda e: self._toggle()

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(sp("md"), 0, sp("md"), 0)
        h_lay.setSpacing(sp("sm"))

        _, icon = self._TINTS.get(section_type, ("routine_morning_tint", "•"))
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFont(qfont("size_body"))
        self._icon_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._icon_lbl)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_body", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._title_lbl, stretch=1)

        # Mini progress bar inline (60×3px) + label "N/N"
        self._mini_prog = QWidget()
        self._mini_prog.setFixedSize(60, 3)
        self._mini_prog_pct = 0.0
        self._mini_prog.paintEvent = self._paint_mini_prog
        self._mini_prog.setVisible(False)
        h_lay.addWidget(self._mini_prog)

        self._prog_lbl = QLabel("")
        self._prog_lbl.setFont(qfont("size_caption", bold=True))
        self._prog_lbl.setStyleSheet("background: transparent;")
        self._prog_lbl.setVisible(False)
        h_lay.addWidget(self._prog_lbl)

        self._toggle_lbl = QLabel("▼")
        self._toggle_lbl.setFont(qfont("size_caption"))
        self._toggle_lbl.setStyleSheet("background: transparent;")
        h_lay.addWidget(self._toggle_lbl)
        self._main_lay.addWidget(self._header)

        # Content
        self._content = QWidget()
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        self._content_lay.setSpacing(sp("sm"))
        self._main_lay.addWidget(self._content)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def content_layout(self) -> QVBoxLayout:
        return self._content_lay

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._toggle_lbl.setText("▶" if self._collapsed else "▼")

    def set_progress(self, done: int, total: int):
        """Muestra mini-bar inline + label 'N/N' (o 'N/N ✓' si completo) en el header."""
        if total <= 0:
            self._mini_prog.setVisible(False)
            self._prog_lbl.setVisible(False)
            return
        self._mini_prog_pct = max(0.0, min(1.0, done / total))
        complete = done >= total
        self._prog_lbl.setText(f"{done}/{total} ✓" if complete else f"{done}/{total}")
        c = colors(self._modo)
        if complete:
            col = C("success", self._modo) if "success" in c else C("teal", self._modo)
        elif self._mini_prog_pct >= 0.5:
            col = C("warning", self._modo)
        else:
            col = C("text_tertiary", self._modo)
        self._prog_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._mini_prog.setVisible(True)
        self._prog_lbl.setVisible(True)
        self._mini_prog.update()

    def _paint_mini_prog(self, _event):
        p = QPainter(self._mini_prog)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self._mini_prog.width(), self._mini_prog.height()
        c = colors(self._modo)
        # Track
        track_c = QColor(c.get("border_card", c["border"]))
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.fillPath(track_path, track_c)
        # Fill
        if self._mini_prog_pct > 0:
            complete = self._mini_prog_pct >= 1.0
            if complete:
                fill_c = QColor(
                    C("success", self._modo) if "success" in c else C("teal", self._modo)
                )
            elif self._mini_prog_pct >= 0.5:
                fill_c = QColor(C("warning", self._modo))
            else:
                fill_c = QColor(C("teal", self._modo))
            fill_path = QPainterPath()
            fw = w * self._mini_prog_pct
            fill_path.addRoundedRect(QRectF(0, 0, fw, h), h / 2, h / 2)
            p.fillPath(fill_path, fill_c)
        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        tint_key, _ = self._TINTS.get(self._section_type, ("routine_morning_tint", ""))
        tint_hex = C(tint_key, self._modo)
        self.setStyleSheet(
            f"QWidget#NMRoutineSection {{ background: {c['bg_surface']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: {RADIUS_CARD}px; }}"
        )
        self._header.setStyleSheet(
            f"QWidget {{ background: {_rgba(tint_hex, 0.08 if 'light' in self._modo else 0.06)}; "
            f"border: none; border-radius: {RADIUS_CARD}px; }}"
        )
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._toggle_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._content.setStyleSheet(
            f"background: {_rgba('#000000', 0.01 if 'light' in self._modo else 0.02)};"
        )


# ── NMDayNote ─────────────────────────────────────────────────────────────────


class NMDayNote(QWidget):
    """Card de nota del día con estado bloqueado/desbloqueado.

    Bloqueada: ícono de candado + razón de bloqueo.
    Desbloqueada: QTextEdit expandible.
    Emite note_changed(str).
    """

    note_changed = pyqtSignal(str)

    def __init__(self, locked: bool = True, lock_reason: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._locked = locked
        self._last_emitted_text = ""
        self.setObjectName("NMDayNote")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("md"), sp("sm"), sp("md"), sp("sm"))
        lay.setSpacing(sp("sm"))

        # Header
        row = QHBoxLayout()
        row.setSpacing(sp("sm"))
        self._icon_lbl = QLabel()
        self._icon_lbl.setFont(qfont("size_body"))
        self._icon_lbl.setStyleSheet("background: transparent;")
        row.addWidget(self._icon_lbl)
        title_lbl = QLabel("Nota del día")
        title_lbl.setFont(qfont("size_body", bold=True))
        title_lbl.setStyleSheet("background: transparent;")
        row.addWidget(title_lbl, stretch=1)
        self._save_btn = NMButton("Guardar", variant="gradient", size="sm", modo=self._modo, width=88)
        self._save_btn.clicked.connect(self._emit_note_changed)
        row.addWidget(self._save_btn)
        lay.addLayout(row)

        self._locked_lbl = QLabel()
        self._locked_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._locked_lbl.setFont(qfont("size_small"))
        self._locked_lbl.setWordWrap(True)
        lay.addWidget(self._locked_lbl)

        self._textarea = QTextEdit()
        self._textarea.setPlaceholderText("Escribe tu reflexión del día...")
        self._textarea.setFixedHeight(90)
        # note_changed se emite al TERMINAR de editar (focus out), NO por
        # tecla: emitir en textChanged hacía que el consumidor guardara y
        # bloqueara la nota con el PRIMER caracter (feedback owner v1.0).
        self._textarea.installEventFilter(self)
        lay.addWidget(self._textarea)

        self.set_locked(locked, lock_reason)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "_textarea", None) and not self._textarea.isReadOnly():
            if ev.type() == QEvent.Type.FocusOut:
                self._emit_note_changed()
            elif ev.type() == QEvent.Type.KeyPress and ev.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                # Enter CONFIRMA la nota (cierra la edición → FocusOut →
                # guardado); Shift+Enter inserta salto de línea. Antes Enter
                # dejaba la nota en modo edición permanente (informe owner).
                if not (ev.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._textarea.clearFocus()
                    return True
        return super().eventFilter(obj, ev)

    def _emit_note_changed(self):
        text = self._textarea.toPlainText()
        if self._locked or self._textarea.isReadOnly():
            return
        if text == self._last_emitted_text:
            return
        self._last_emitted_text = text
        self.note_changed.emit(text)

    def set_locked(self, locked: bool, reason: str = ""):
        self._locked = locked
        self._locked_lbl.setVisible(locked)
        self._textarea.setVisible(not locked)
        self._textarea.setReadOnly(False)
        self._save_btn.setVisible(not locked)
        self._save_btn.setEnabled(not locked)
        self._icon_lbl.setText("\U0001f512" if locked else "\U0001f4dd")
        if locked:
            self._locked_lbl.setText(reason or "Completa tu rutina del día para desbloquear")

    def set_saved_today(self, text: str):
        """Estado 'nota del día guardada': lectura hasta mañana.

        La nota del día no es un block de notas eterno (decisión owner v1.0):
        al guardarse queda visible pero cerrada; al día siguiente el módulo
        la reabre vacía (la nota se persiste por fecha).
        """
        self._locked = True
        self.set_note(text)
        self._textarea.setVisible(True)
        self._textarea.setReadOnly(True)
        self._icon_lbl.setText("✓")
        self._locked_lbl.clear()
        self._locked_lbl.setVisible(False)
        self._save_btn.setVisible(False)
        self._save_btn.setEnabled(False)

    def is_saved_today(self) -> bool:
        return self._textarea.isReadOnly()

    def set_note(self, text: str):
        self._textarea.blockSignals(True)
        self._textarea.setPlainText(text)
        self._textarea.blockSignals(False)
        self._last_emitted_text = text

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = _rgba(C("accent", self._modo), 0.20 if "light" in self._modo else 0.25)
        bg = _rgba(C("accent", self._modo), 0.04 if "light" in self._modo else 0.06)
        self.setStyleSheet(
            f"QWidget#NMDayNote {{ background: {bg}; border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {border}; }}"
            "QWidget#NMDayNote QLabel { background: transparent; border: none; }"
        )
        self._locked_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._save_btn._apply_theme(self._modo)
        self._textarea.setStyleSheet(
            f"QTextEdit {{ background: {c['bg_input']}; color: {c['text_primary']}; "
            f"border: 1px solid {c['border']}; border-radius: {RADIUS_INPUT}px; "
            f"padding: 6px 10px; font-size: {TYPOGRAPHY['size_body']}px; }}"
        )


# ── NMMoodContextHeader ────────────────────────────────────────────────────────


class NMMoodContextHeader(QWidget):
    """Banner contextual: 'Basado en tu ánimo de hoy (N/10) EMOJI'.

    Se usa en la cabecera del módulo Actividades.
    """

    _SCORE_MAP = [
        (3, "\U0001f61e"),  # <=2  muy bajo
        (5, "\U0001f615"),  # 3-4  bajo
        (7, "\U0001f610"),  # 5-6  neutro
        (9, "\U0001f642"),  # 7-8  bien
        (11, "\U0001f604"),  # 9-10 excelente
    ]

    def __init__(self, score: int = 5, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._score = score
        self.setFixedHeight(_NM_CONTROL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(sp("md"), 0, sp("md"), 0)
        lay.setSpacing(sp("sm"))

        self._emoji_lbl = QLabel()
        self._emoji_lbl.setFont(qfont("size_h3"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._emoji_lbl)

        self._text_lbl = QLabel()
        self._text_lbl.setFont(qfont("size_small"))
        self._text_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._text_lbl, stretch=1)

        self.set_score(score)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _emoji_for(self, score: int) -> str:
        for limit, emoji in self._SCORE_MAP:
            if score < limit:
                return emoji
        return "\U0001f610"

    def set_score(self, score: int):
        self._score = score
        self._emoji_lbl.setText(self._emoji_for(score))
        self._text_lbl.setText(f"Basado en tu ánimo de hoy ({score}/10)")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg = _rgba(C("teal", self._modo), 0.06 if "light" in self._modo else 0.07)
        border = _rgba(C("teal", self._modo), 0.12 if "light" in self._modo else 0.15)
        self.setStyleSheet(
            f"background: {bg}; border-radius: {RADIUS_CARD}px; border: 1px solid {border};"
        )
        self._text_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))


# ── NMCategoryFilter ──────────────────────────────────────────────────────────


class NMCategoryFilter(QWidget):
    """Fila horizontal scrollable de chips de filtro por categoría.

    Emite filter_changed(str): nombre de categoría o "" para "Todas".
    """

    filter_changed = pyqtSignal(str)

    def __init__(self, categories: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected: str | None = None
        self._btns: dict[str, QPushButton] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(40)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(sp("sm"))

        all_btn = QPushButton("Todas")
        all_btn.setFixedHeight(28)
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.clicked.connect(lambda: self._select(""))
        row.addWidget(all_btn)
        self._btns[""] = all_btn

        for cat in categories:
            btn = QPushButton(cat)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, c=cat: self._select(c))
            row.addWidget(btn)
            self._btns[cat] = btn

        row.addStretch()
        scroll.setWidget(container)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _select(self, cat: str):
        self._selected = cat if cat else None
        self._apply_theme(self._modo)
        self.filter_changed.emit(cat)

    def selected(self) -> str:
        return self._selected or ""

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        for cat, btn in self._btns.items():
            is_sel = (self._selected == cat) or (cat == "" and self._selected is None)
            cat_color = (
                CATEGORY_COLORS.get(cat, C("accent", self._modo))
                if cat
                else C("accent", self._modo)
            )
            bg = _rgba(cat_color, 0.20 if is_sel else 0.14)
            border = _rgba(cat_color, 0.25)
            col = cat_color if cat else C("text_secondary", self._modo)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_PILL}px;
                    padding: 3px 12px;
                    font-size: {TYPOGRAPHY["size_caption"]}px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    border-color: {cat_color};
                    background: {_rgba(cat_color, 0.20)};
                }}
            """)


# ── NMAvisoCard ───────────────────────────────────────────────────────────────


class NMAvisoCard(QFrame):
    """Card de recordatorio con hora grande, mensaje y status pill.

    status: 'activo' | 'disparado' | 'expirado'
    """

    STATUS_ACTIVE = "activo"
    STATUS_FIRED = "disparado"
    STATUS_EXPIRED = "expirado"

    def __init__(
        self, time_str: str, message: str, status: str = "activo", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._status = status
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Quitamos border en setStyleSheet; lo dibujamos manualmente para tener accent bar
        self.setAutoFillBackground(False)

        outer = QHBoxLayout(self)
        # Margen izquierdo extra para dejar espacio al accent bar de 3px
        outer.setContentsMargins(sp("md") + 6, sp("sm"), sp("md"), sp("sm"))
        outer.setSpacing(sp("md"))

        # Left: big monospaced time
        self._time_lbl = QLabel(time_str)
        self._time_lbl.setFont(qfont_mono(SIZE_TIME_LARGE, bold=True))
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_lbl.setFixedWidth(88)
        self._time_lbl.setStyleSheet("background: transparent;")
        outer.addWidget(self._time_lbl)

        # Right: message + status pill
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)

        self._msg_lbl = QLabel(message)
        self._msg_lbl.setFont(qfont("size_body"))
        self._msg_lbl.setWordWrap(True)
        self._msg_lbl.setStyleSheet("background: transparent;")
        right.addWidget(self._msg_lbl)

        pill_row = QHBoxLayout()
        pill_row.setSpacing(sp("sm"))
        self._pill = QLabel()
        self._pill.setFixedHeight(20)
        self._pill.setContentsMargins(10, 0, 10, 0)
        self._pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pill.setFont(qfont("size_caption", bold=True))
        pill_row.addWidget(self._pill)
        pill_row.addStretch()
        right.addLayout(pill_row)

        outer.addLayout(right, stretch=1)

        self.set_status(status)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, status: str):
        self._status = status
        self._update_pill()
        self._apply_theme(self._modo)

    def _update_pill(self):
        labels = {
            self.STATUS_ACTIVE: "● Activo",
            self.STATUS_FIRED: "✓ Disparado",
            self.STATUS_EXPIRED: "○ Expirado",
        }
        self._pill.setText(labels.get(self._status, self._status))

    def _status_pill_colors(self) -> tuple[str, str]:
        if self._status == self.STATUS_ACTIVE:
            return C("teal", self._modo), C("text_on_accent", self._modo)
        if self._status == self.STATUS_FIRED:
            return C("violet", self._modo), C("text_on_accent", self._modo)
        return C("bg_elevated", self._modo), C("text_tertiary", self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        # No usamos border/background en setStyleSheet — los pintamos en paintEvent
        # para tener accent bar gradient teal→violet a la izquierda.
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        time_key = "text_primary" if self._status != self.STATUS_EXPIRED else "text_tertiary"
        self._time_lbl.setStyleSheet(f"color: {C(time_key, self._modo)}; background: transparent;")
        msg_key = "text_primary" if self._status != self.STATUS_EXPIRED else "text_tertiary"
        self._msg_lbl.setStyleSheet(label_style(self._modo, msg_key))
        pill_bg, pill_col = self._status_pill_colors()
        self._pill.setStyleSheet(
            f"QLabel {{ background: {pill_bg}; color: {pill_col}; "
            f"border-radius: 10px; font-size: {TYPOGRAPHY['size_caption']}px; "
            f"font-weight: 500; }}"
        )
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self.width(), self.height()
        r = RADIUS_CARD
        c = colors(self._modo)

        # Card background + border
        bg = QColor(c["bg_surface"])
        if self._status == self.STATUS_EXPIRED:
            bg.setAlphaF(0.5)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, bg)

        # Accent bar lateral 3px con gradient teal→violet (gris si expirado)
        if self._status == self.STATUS_EXPIRED:
            bar_top = QColor(c.get("border_card", c["border"]))
            bar_bot = QColor(bar_top)
        else:
            bar_top = QColor(C("teal", self._modo))
            bar_bot = QColor(C("violet", self._modo))
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(0, 0, 3, h), 1.5, 1.5)
        bar_grad = QLinearGradient(0, 0, 0, h)
        bar_grad.setColorAt(0.0, bar_top)
        bar_grad.setColorAt(1.0, bar_bot)
        p.fillPath(bar_path, bar_grad)

        # Border sutil
        border_c = QColor(c.get("border_card", c["border"]))
        p.setPen(QPen(border_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.restore()
        p.end()


# ── NMFeaturedCard ────────────────────────────────────────────────────────────

_PATIENT_AVATAR_PAIRS = [
    ("accent", "teal"),
    ("teal", "violet"),
    ("violet", "accent"),
    ("accent", "violet"),
]


class NMPatientRow(QFrame):
    """Fila de paciente del Hub con avatar e indicador de adherencia."""

    clicked = pyqtSignal()

    def __init__(
        self,
        name: str,
        subtitle: str = "",
        initials: str = "",
        pct: float = 0.0,
        selected: bool = False,
        tags: list[str] | None = None,
        last_activity: str = "",
        next_session: str = "",
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = selected
        self._tags = tags or []
        self._last_activity = last_activity
        self._next_session = next_session
        self._name_hash = sum(ord(c) for c in (name or "?")) % len(_PATIENT_AVATAR_PAIRS)
        self.setObjectName("NMPatientRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(74)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        self._avatar = QLabel(initials or "".join(part[:1] for part in name.split()[:2]).upper())
        self._avatar.setFixedSize(38, 38)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._avatar)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self._name = QLabel(name)
        self._name.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle = QLabel(subtitle)
        self._subtitle.setFont(qfont("size_caption"))
        text_col.addWidget(self._name)
        text_col.addWidget(self._subtitle)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)
        self._tag_labels: list[QLabel] = []
        for tag in self._tags[:3]:
            lbl = QLabel(tag)
            lbl.setFont(qfont("size_caption"))
            lbl.setContentsMargins(7, 2, 7, 2)
            self._tag_labels.append(lbl)
            meta_row.addWidget(lbl)
        self._last_lbl = QLabel(self._last_activity)
        self._last_lbl.setFont(qfont("size_caption"))
        self._next_lbl = QLabel(self._next_session)
        self._next_lbl.setFont(qfont("size_caption"))
        if self._last_activity:
            meta_row.addWidget(self._last_lbl)
        if self._next_session:
            meta_row.addWidget(self._next_lbl)
        meta_row.addStretch()
        text_col.addLayout(meta_row)
        lay.addLayout(text_col, stretch=1)
        # Ring 40px: tamaño suficiente para mostrar "85%" sin recorte
        self._ring = NMModuleRing(size=46, pct=pct, modo=self._modo)
        lay.addWidget(self._ring)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_theme(self._modo)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        if self._selected:
            bg = _rgba(v3c("accent", self._modo).name(), 0.05)
            border = _rgba(v3c("accent", self._modo).name(), 0.30)
        else:
            bg = v3c("elevated", self._modo).name()
            border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        self.setStyleSheet(
            f"QFrame#NMPatientRow {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: 14px; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: 19px; "
            f"border: 1px solid {_rgba('#ffffff', 0.18 if 'dark' in self._modo else 0.35)}; }}"
        )
        self._name.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        meta_col = v3c("ink_secondary", self._modo).name()
        for lbl in (self._last_lbl, self._next_lbl):
            lbl.setStyleSheet(f"color: {meta_col}; background: transparent;")
        accent = v3c("accent", self._modo)
        tag_bg = f"rgba({accent.red()},{accent.green()},{accent.blue()},34)"
        for lbl in self._tag_labels:
            lbl.setStyleSheet(
                f"color: {v3c('accent', self._modo).name()}; "
                f"background: {tag_bg}; border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                "border-radius: 8px;"
            )


class NMSparkline(QWidget):
    """Inline sparkline — polyline for up to N data points (mood 7d, etc.).

    • Fixed size (default 90×28).
    • None / 0 values treated as gaps (segment breaks).
    • Color auto-selects `danger` token when last value drops ≥2 vs first
      (descending trend), otherwise uses `primary` token.
    """

    def __init__(
        self,
        data: list | None = None,
        color: str | None = None,
        w: int = 90,
        h: int = 28,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._data: list = list(data) if data else []
        self._color = color
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedSize(w, h)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        _tm().theme_changed.connect(self._on_theme)

    def set_data(self, data: list, color: str | None = None):
        self._data = list(data)
        if color is not None:
            self._color = color
        self.update()

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event: QPaintEvent):  # noqa: N802
        valid = [(i, float(v)) for i, v in enumerate(self._data) if v is not None and float(v) > 0]
        if len(valid) < 2:
            return

        vals = [v for _, v in valid]
        trend_down = len(vals) >= 2 and (vals[-1] - vals[0]) <= -2
        if self._color:
            stroke = QColor(self._color)
        elif trend_down:
            stroke = v3c("danger", self._modo)
        else:
            stroke = v3c("primary", self._modo)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pw, ph = self.width(), self.height()
        pad = 3
        eff_w = pw - pad * 2
        eff_h = ph - pad * 2
        n_total = max(len(self._data), 1)
        mn, mx = min(vals), max(vals)
        span = (mx - mn) if mx > mn else 1.0

        def _xy(idx: int, val: float) -> tuple:
            x = pad + idx * eff_w / max(n_total - 1, 1)
            y = pad + eff_h - (val - mn) / span * eff_h
            return x, y

        pen = QPen(stroke)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        first = True
        for idx, val in valid:
            x, y = _xy(idx, val)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        painter.drawPath(path)

        last_x, last_y = _xy(valid[-1][0], valid[-1][1])
        dot = QColor(stroke)
        dot.setAlpha(200)
        painter.setBrush(dot)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(last_x, last_y), 2.5, 2.5)
        painter.end()


class NMAreaSparkline(QWidget):
    """Area sparkline grande para la card de animo del Hub Dashboard (capture 03).

    A diferencia de :class:`NMSparkline` (polyline inline 90x28), este pinta:
      - area rellena con gradiente teal que se desvanece hacia abajo;
      - linea con marcadores circulares en cada punto;
      - area suave sin guias tecnicas punteadas;
      - etiquetas de eje X (dias) debajo del grafico.

    Ancho expansible, alto compacto para no romper la politica fit-first.
    """

    def __init__(
        self,
        data: list | None = None,
        labels: list[str] | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._data: list[float] = [float(v) for v in (data or [])]
        self._labels: list[str] = list(labels) if labels else []
        self._modo = norm_modo(modo or _tm().modo)
        self.setMinimumHeight(74)
        self.setMaximumHeight(82)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        _tm().theme_changed.connect(self._on_theme)

    def set_series(self, data: list, labels: list[str] | None = None):
        self._data = [float(v) for v in (data or [])]
        if labels is not None:
            self._labels = list(labels)
        self.update()

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event: QPaintEvent):  # noqa: N802
        if len(self._data) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        stroke = v3c("teal", self._modo)
        axis_c = v3c("mute", self._modo)
        pw, ph = self.width(), self.height()

        axis_h = 16 if self._labels else 0
        pad_x = 4
        top_pad = 6
        plot_h = ph - axis_h - top_pad
        eff_w = pw - pad_x * 2

        vals = self._data
        n = len(vals)
        mn, mx = min(vals), max(vals)
        # Margen vertical para que picos/valles no toquen los bordes.
        span = (mx - mn) if mx > mn else 1.0
        lo = mn - span * 0.25
        hi = mx + span * 0.25
        vspan = hi - lo

        def _xy(idx: int, val: float) -> tuple[float, float]:
            x = pad_x + idx * eff_w / max(n - 1, 1)
            y = top_pad + plot_h - (val - lo) / vspan * plot_h
            return x, y

        pts = [_xy(i, v) for i, v in enumerate(vals)]

        # Area rellena con gradiente que se desvanece hacia la baseline.
        area = QPainterPath()
        area.moveTo(pts[0][0], top_pad + plot_h)
        for x, y in pts:
            area.lineTo(x, y)
        area.lineTo(pts[-1][0], top_pad + plot_h)
        area.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, top_pad + plot_h)
        top_c = QColor(stroke)
        top_c.setAlpha(70)
        bot_c = QColor(stroke)
        bot_c.setAlpha(0)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawPath(area)

        # Linea principal.
        line = QPainterPath()
        line.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            line.lineTo(x, y)
        line_pen = QPen(QColor(stroke))
        line_pen.setWidthF(2.0)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line)

        # Marcadores circulares (relleno = surface, borde = stroke).
        surface_c = QColor(colors(self._modo)["bg_surface"])
        for x, y in pts:
            painter.setPen(QPen(QColor(stroke), 1.6))
            painter.setBrush(surface_c)
            painter.drawEllipse(QPointF(x, y), 3.0, 3.0)

        # Etiquetas de eje X (dias).
        if self._labels:
            painter.setPen(QColor(axis_c))
            f = qfont("size_caption_xs")
            painter.setFont(f)
            label_y = ph - axis_h
            n_lab = len(self._labels)
            for i, lab in enumerate(self._labels):
                cx = pad_x + i * eff_w / max(n_lab - 1, 1)
                painter.drawText(
                    QRectF(cx - 14, label_y, 28, axis_h),
                    Qt.AlignmentFlag.AlignCenter,
                    lab,
                )
        painter.end()


class NMPatientRowPremium(QFrame):
    """Dense Hub patient row with avatar, metadata, chips, sync and ring."""

    clicked = pyqtSignal()

    _SYNC_TO_KEY = {
        "ok": "success",
        "syncing": "warning",
        "stale": "warning",
        "error": "error",
    }

    def __init__(
        self,
        name: str,
        patient_id: str = "",
        subtitle: str = "",
        last_activity: str = "",
        next_session: str = "",
        tags: list[str] | None = None,
        sync_state: str = "ok",
        pct: float = 0.0,
        mood_data: list | None = None,
        selected: bool = False,
        modo: str = None,
        on_unlink=None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = selected
        self._sync_state = sync_state if sync_state in self._SYNC_TO_KEY else "ok"
        self._full_name = name or "-"
        self._full_last_activity = last_activity or patient_id or "Sin registros recientes"
        self._full_subtitle = subtitle or "Sin programa vinculado"
        self._full_next_session = next_session or self._sync_copy()
        self._name_hash = sum(ord(c) for c in (name or "?")) % len(_PATIENT_AVATAR_PAIRS)
        self.setObjectName("NMPatientRowPremium")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(58)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 7, 14, 7)
        lay.setSpacing(12)

        # Status dot
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(10, 10)
        self._status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        # Avatar circular initials (28x28 px)
        initials = "".join(part[:1] for part in (name or "?").split()[:2]).upper()
        self._avatar = QLabel(initials or "P")
        self._avatar.setFixedSize(28, 28)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        # Patient identity column
        patient_col = QVBoxLayout()
        patient_col.setContentsMargins(0, 0, 0, 0)
        patient_col.setSpacing(1)
        self._name = QLabel(self._full_name)
        self._name.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._name.setToolTip(self._full_name)
        self._name.setMinimumWidth(150)
        patient_col.addWidget(self._name)

        self._activity_lbl = QLabel(self._full_last_activity)
        self._activity_lbl.setFont(qfont("size_caption_xs"))
        self._activity_lbl.setToolTip(self._full_last_activity)
        patient_col.addWidget(self._activity_lbl)
        lay.addLayout(patient_col, stretch=3)

        # Program / context column
        program_col = QVBoxLayout()
        program_col.setContentsMargins(0, 0, 0, 0)
        program_col.setSpacing(1)
        self._subtitle_lbl = QLabel(self._full_subtitle)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        self._subtitle_lbl.setToolTip(self._full_subtitle)
        program_col.addWidget(self._subtitle_lbl)

        self._context_lbl = QLabel(self._full_next_session)
        self._context_lbl.setFont(qfont("size_caption_xs"))
        self._context_lbl.setToolTip(self._full_next_session)
        program_col.addWidget(self._context_lbl)
        lay.addLayout(program_col, stretch=2)

        # Sparkline
        self._sparkline = None
        if mood_data:
            self._sparkline = NMSparkline(data=mood_data, modo=self._modo)
            self._sparkline.setFixedSize(64, 22)
            lay.addWidget(self._sparkline, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            lay.addSpacing(64)

        # Adherence ring — en columna fija de 56px para alinear con el header
        # "USO" y dejar aire respecto del borde derecho. 30px: con 26 el
        # porcentaje interior quedaba comprimido contra el anillo.
        self._ring = NMModuleRing(size=30, pct=pct, modo=self._modo)
        _ring_wrap = QWidget()
        _ring_wrap.setFixedWidth(56)
        _ring_wl = QHBoxLayout(_ring_wrap)
        _ring_wl.setContentsMargins(0, 0, 0, 0)
        _ring_wl.addWidget(self._ring, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(_ring_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        # X discreta para quitar al paciente del Hub (decisión owner v1.0:
        # pacientes que dejan el tratamiento no deben acumularse en la lista).
        # Botón hijo: consume su propio click, no dispara el clicked de la fila.
        self._btn_unlink = None
        if on_unlink is not None:
            self._btn_unlink = QToolButton()
            self._btn_unlink.setObjectName("NMRowUnlink")
            self._btn_unlink.setFixedSize(26, 26)
            self._btn_unlink.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_unlink.setToolTip("Quitar paciente del Hub")
            self._btn_unlink.setAccessibleName(f"Quitar a {self._full_name} del Hub")
            self._btn_unlink.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._btn_unlink.clicked.connect(on_unlink)
            lay.addWidget(self._btn_unlink, 0, Qt.AlignmentFlag.AlignVCenter)

        # Legacy widgets created but hidden to avoid crashes
        self._pid = QLabel(patient_id)
        self._subtitle = QLabel(subtitle)
        self._sync = QLabel("Sync")

        self._apply_theme(self._modo)
        QTimer.singleShot(0, self._refresh_name_text)
        QTimer.singleShot(0, self._refresh_activity_text)
        QTimer.singleShot(0, self._refresh_subtitle_text)
        QTimer.singleShot(0, self._refresh_context_text)
        _tm().theme_changed.connect(self._apply_theme)

    def _sync_copy(self) -> str:
        return {
            "ok": "Sincronización reciente",
            "syncing": "Sincronizando",
            "stale": "Sin sincronización reciente",
            "error": "Error de sincronización",
        }.get(self._sync_state, "Sincronización reciente")

    def _chip(self, text: str, tone_key: str) -> QLabel:
        chip = QLabel(text)
        chip.setProperty("tone_key", tone_key)
        chip.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setMinimumHeight(18)
        chip.setContentsMargins(6, 1, 6, 1)
        return chip

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_theme(self._modo)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_name_text()
        self._refresh_activity_text()
        self._refresh_subtitle_text()
        self._refresh_context_text()

    def _fit_label(self, label: QLabel, text: str, minimum: int = 72):
        width = max(minimum, label.width() - 4)
        metrics = QFontMetrics(label.font())
        label.setText(metrics.elidedText(text, Qt.TextElideMode.ElideRight, width))

    def _refresh_subtitle_text(self):
        if hasattr(self, "_subtitle_lbl"):
            self._fit_label(self._subtitle_lbl, self._full_subtitle, minimum=88)

    def _refresh_name_text(self):
        if hasattr(self, "_name"):
            self._fit_label(self._name, self._full_name, minimum=96)

    def _refresh_activity_text(self):
        if hasattr(self, "_activity_lbl"):
            self._fit_label(self._activity_lbl, self._full_last_activity, minimum=110)

    def _refresh_context_text(self):
        if hasattr(self, "_context_lbl"):
            self._fit_label(self._context_lbl, self._full_next_session, minimum=94)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg_key = "surfaceSolid" if is_dark else "surface"
        bg = (
            _rgba(v3c("accent", self._modo).name(), 0.08)
            if self._selected
            else v3c(bg_key, self._modo).name()
        )
        border = (
            _rgba(C("accent", self._modo), 0.38)
            if self._selected
            else qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        )
        hover_bg = _rgba(C("teal", self._modo), 0.07 if is_dark else 0.05)
        self.setStyleSheet(
            f"QFrame#NMPatientRowPremium {{ background: {bg}; border: 1px solid {border}; "
            f"border-left: 3px solid {C('accent', self._modo) if self._selected else border}; "
            f"border-radius: 12px; }}"
            f"QFrame#NMPatientRowPremium:hover {{ background: {hover_bg}; "
            f"border-color: {_rgba(C('teal', self._modo), 0.42)}; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: 12px; "
            f"border: 1px solid {_rgba('#ffffff', 0.22 if is_dark else 0.42)}; }}"
        )
        self._name.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._activity_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._subtitle_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._context_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._pid.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )
        if self._sparkline is not None:
            self._sparkline._on_theme(self._modo)

        if self._btn_unlink is not None:
            _ink = v3c("ink_secondary", self._modo).name()
            self._btn_unlink.setIcon(nm_icon("close", _ink, size=13))
            self._btn_unlink.setIconSize(QSize(13, 13))
            self._btn_unlink.setStyleSheet(
                "QToolButton#NMRowUnlink { background: transparent; border: none; "
                "border-radius: 13px; }"
                f"QToolButton#NMRowUnlink:hover {{ "
                f"background: {_rgba(C('danger', self._modo), 0.14)}; }}"
            )

        # Status dot color based on sync state
        dot_color = v3c(self._SYNC_TO_KEY.get(self._sync_state, "ok"), self._modo).name()
        self._status_dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 5px;"
        )

        for chip in self.findChildren(QLabel):
            tone_key = chip.property("tone_key")
            if not tone_key:
                continue
            col = QColor(C(str(tone_key), self._modo))
            bgc = QColor(col)
            bgc.setAlpha(34 if is_dark else 26)
            brd = QColor(col)
            brd.setAlpha(68 if is_dark else 48)
            chip.setStyleSheet(
                f"color: {col.name()}; background: rgba({bgc.red()},{bgc.green()},{bgc.blue()},{bgc.alpha()}); "
                f"border: 1px solid rgba({brd.red()},{brd.green()},{brd.blue()},{brd.alpha()}); "
                f"border-radius: 10px; padding: 3px 8px;"
            )


class NMSettingsSection(QFrame):
    """Sección de configuración v3 (NMConfigRow del README).

    - Surface card con radius ``V3_RD["lg"]`` (14).
    - Header eyebrow (caption semibold) con separador ``borderSoft``.
    - Filas key-value separadas con line ``borderSoft``.
    - Right slot acepta QWidget arbitrario (NMToggle, NMStatusChip, valor).
    """

    def __init__(self, title: str, modo: str = None, compact: bool = False, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMSettingsSection")
        self._sec_shadow: QGraphicsDropShadowEffect | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._header = QLabel(title)
        self._header.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        if self._compact:
            self._header.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        else:
            self._header.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.addWidget(self._header)
        self._rows = QVBoxLayout()
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(0)
        lay.addLayout(self._rows)
        self._apply_theme(self._modo)
        self._apply_section_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_section_shadow(self):
        """Sombra v3 (idem NMCard) — sin esta queda plana sobre fondo claro."""
        if self._sec_shadow is None:
            self._sec_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._sec_shadow.setBlurRadius(32)
            self._sec_shadow.setOffset(0, 10)
            self._sec_shadow.setColor(QColor(0, 0, 0, 120))
        else:
            self._sec_shadow.setBlurRadius(32)
            self._sec_shadow.setOffset(0, 12)
            self._sec_shadow.setColor(QColor(28, 34, 24, 18))
        self.setGraphicsEffect(self._sec_shadow)

    def paintEvent(self, event):
        """La sección usa superficie sólida QSS; sin brillo decorativo."""
        super().paintEvent(event)

    def add_row(self, label: str, value):
        row = QWidget()
        row.setObjectName("NMSettingsRow")
        lay = QHBoxLayout(row)
        if getattr(self, "_compact", False):
            lay.setContentsMargins(V3_SP["md"], V3_SP["xs"] + 2, V3_SP["md"], V3_SP["xs"] + 2)
        else:
            lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"] + 2, V3_SP["lg"], V3_SP["sm"] + 2)
        left = QLabel(label)
        left.setFont(qfont("size_small"))
        lay.addWidget(left)
        lay.addStretch()
        if isinstance(value, QWidget):
            lay.addWidget(value)
        else:
            right = QLabel(str(value))
            sval = str(value)
            right.setFont(
                qfont_mono(9) if "http" in sval or "..." in sval else qfont("size_caption")
            )
            lay.addWidget(right)
        self._rows.addWidget(row)
        self._apply_theme(self._modo)
        return row

    def add_log(self, html: str):
        log = QLabel(html)
        log.setTextFormat(Qt.TextFormat.RichText)
        log.setFont(qfont_mono(9))
        log.setWordWrap(True)
        if getattr(self, "_compact", False):
            log.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
        else:
            log.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["sm"])
        self._rows.addWidget(log)
        self._apply_theme(self._modo)
        return log

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        surf_key = "surfaceSolid" if is_dark else "surface"
        bg = v3c(surf_key, self._modo).name()
        border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        text_eyebrow = v3c("ink_secondary", self._modo).name()
        text_body = v3c("text2", self._modo).name()
        radius = V3_RD["lg"]
        self.setStyleSheet(
            f"QFrame#NMSettingsSection {{ background: {bg}; "
            f"border: 1px solid {border}; border-radius: {radius}px; }}"
            f"QWidget#NMSettingsRow {{ background: transparent; "
            f"border-top: 1px solid {border}; }}"
        )
        self._header.setStyleSheet(f"color: {text_eyebrow}; background: transparent; ")
        for lbl in self.findChildren(QLabel):
            if lbl is not self._header:
                lbl.setStyleSheet(f"color: {text_body}; background: transparent;")
        # Re-aplicar sombra al cambiar tema
        if getattr(self, "_sec_shadow", None) is not None:
            self._apply_section_shadow()


class NMPanel(QFrame):
    """Panel de configuracion compacto con header y superficie v3."""

    def __init__(
        self, title: str, subtitle: str = "", modo: str = None, compact: bool = False, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMPanel")
        self._panel_shadow: QGraphicsDropShadowEffect | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget(self)
        header.setStyleSheet("background: transparent;")
        header_lay = QVBoxLayout(header)
        if self._compact:
            header_lay.setContentsMargins(12, 10, 12, 6)
        else:
            header_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["sm"])
        header_lay.setSpacing(2)

        self._title = QLabel(title)
        self._title.setFont(
            qfont("size_h3" if self._compact else "size_h2", weight=TYPOGRAPHY["weight_semibold"])
        )
        header_lay.addWidget(self._title)
        self._subtitle = QLabel(subtitle)
        self._subtitle.setWordWrap(True)
        self._subtitle.setFont(qfont("size_caption"))
        if subtitle:
            header_lay.addWidget(self._subtitle)
        root.addWidget(header)

        self._body = QVBoxLayout()
        if self._compact:
            self._body.setContentsMargins(12, 0, 12, 12)
            self._body.setSpacing(8)
        else:
            self._body.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], V3_SP["md"])
            self._body.setSpacing(V3_SP["sm"])
        root.addLayout(self._body)

        self._apply_theme(self._modo)
        self._apply_panel_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    def body_layout(self) -> QVBoxLayout:
        return self._body

    def add_widget(self, widget: QWidget):
        self._body.addWidget(widget)
        return widget

    def _apply_panel_shadow(self):
        if self._panel_shadow is None:
            self._panel_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._panel_shadow.setBlurRadius(32)
            self._panel_shadow.setOffset(0, 10)
            self._panel_shadow.setColor(QColor(0, 0, 0, 120))
        else:
            self._panel_shadow.setBlurRadius(32)
            self._panel_shadow.setOffset(0, 12)
            self._panel_shadow.setColor(QColor(28, 34, 24, 18))
        self.setGraphicsEffect(self._panel_shadow)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        self.setStyleSheet(
            f"QFrame#NMPanel {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: {V3_RD['lg']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        if self._panel_shadow is not None:
            self._apply_panel_shadow()


class NMFormRow(QWidget):
    """Fila label/control para formularios de configuracion."""

    def __init__(
        self,
        label: str,
        value,
        hint: str = "",
        modo: str = None,
        compact: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self.setObjectName("NMFormRow")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["sm"] if self._compact else V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._label = QLabel(label)
        self._label.setFont(
            qfont(
                "size_caption" if self._compact else "size_small",
                weight=TYPOGRAPHY["weight_semibold"],
            )
        )
        text_col.addWidget(self._label)
        self._hint = QLabel(hint)
        self._hint.setWordWrap(True)
        self._hint.setFont(qfont("size_caption"))
        if hint:
            text_col.addWidget(self._hint)
        lay.addLayout(text_col, stretch=1)

        if isinstance(value, QWidget):
            self._value = value
            lay.addWidget(
                value, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        else:
            self._value = QLabel(str(value))
            self._value.setFont(qfont_mono(9) if "http" in str(value) else qfont("size_caption"))
            self._value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(self._value)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("QWidget#NMFormRow { background: transparent; }")
        self._label.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._hint.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        if isinstance(self._value, QLabel):
            self._value.setStyleSheet(
                f"color: {v3c('text2', self._modo).name()}; background: transparent;"
            )


class NMStatusBanner(QFrame):
    """Banner sereno de estado operativo para pantallas de configuracion."""

    _TONES = {
        "ok": ("positive", "Conectado"),
        "syncing": ("patient", "Verificando"),
        "idle": ("neutral", "Pendiente"),
        "error": ("danger", "Revisar conexion"),
    }

    def __init__(
        self,
        title: str,
        detail: str = "",
        tone: str = "idle",
        action: QWidget | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone
        self.setObjectName("NMStatusBanner")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])

        self._dot = NMStatusDot(tone="ok", modo=self._modo, parent=self)
        lay.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(2)
        self._title = QLabel(title)
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._detail = QLabel(detail)
        self._detail.setWordWrap(True)
        self._detail.setFont(qfont("size_caption"))
        text.addWidget(self._title)
        text.addWidget(self._detail)
        lay.addLayout(text, stretch=1)

        self._badge = NMBadge("", tone="patient", modo=self._modo)
        lay.addWidget(self._badge, alignment=Qt.AlignmentFlag.AlignTop)
        if action is not None:
            lay.addWidget(action, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.set_tone(tone)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, title: str, detail: str, tone: str):
        self._title.setText(title)
        self._detail.setText(detail)
        self.set_tone(tone)

    def set_tone(self, tone: str):
        self._tone = tone if tone in self._TONES else "idle"
        dot_tone = (
            "danger" if self._tone == "error" else ("warn" if self._tone == "syncing" else "ok")
        )
        self._dot.set_tone(dot_tone)
        badge_variant, badge_text = self._TONES[self._tone]
        self._badge.setText(badge_text)
        self._badge.set_tone(badge_variant)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg_key = "surface2" if is_dark else "surface2"
        bg = v3c(bg_key, self._modo)
        border = v3c("border", self._modo)
        if self._tone == "error":
            border = v3c("danger", self._modo)
            border.setAlpha(130)
        else:
            border.setAlpha(150)
        self.setStyleSheet(
            f"QFrame#NMStatusBanner {{ background: {bg.name()}; "
            f"border: 1px solid rgba({border.red()},{border.green()},{border.blue()},{border.alpha()}); "
            f"border-radius: {V3_RD['xl']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._detail.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )


class NMAIDisclaimer(QFrame):
    """Disclaimer clínico permanente para todo output de IA (HANDOFF §6).

    Caja warning/amber con icono de escudo + texto fijo. Siempre visible: la IA
    solo genera borradores que requieren validación profesional y no constituyen
    diagnóstico. Componente reutilizable (panel IA del detalle, asistente global).
    """

    _TEXT = (
        "Borrador generado por IA · requiere validación de un profesional. "
        "No constituye diagnóstico."
    )

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMAIDisclaimer")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        lay.setSpacing(V3_SP["sm"])

        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        self._icon.setScaledContents(True)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignTop)

        self._lbl = QLabel(self._TEXT)
        self._lbl.setWordWrap(True)
        self._lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._lbl, stretch=1)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg_color = C("warning_bg", self._modo)
        primary_color = C("primary", self._modo)
        ink_color = C("warning_ink", self._modo)
        self.setStyleSheet(
            f"QFrame#NMAIDisclaimer {{ "
            f"background-color: {bg_color}; "
            f"border: 1px solid {primary_color}; "
            f"border-left: 1px solid {primary_color}; "
            f"border-radius: {V3_RD['lg']}px; }}"
        )
        try:
            self._icon.setPixmap(nm_icon("shield", primary_color, size=18).pixmap(18, 18))
        except Exception:
            self._icon.setText("!")
            self._icon.setStyleSheet(f"color: {primary_color}; background: transparent;")
        self._lbl.setStyleSheet(f"color: {ink_color}; background: transparent;")


class NMAIPanel(QFrame):
    """Panel IA (F1.5) con disclaimer obligatorio en todos los estados (idle/generando/borrador).
    Background warning-bg, Border 1px primary-line (primary).
    """

    def __init__(self, state="idle", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self.setObjectName("NMAIPanel")

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        # Disclaimer - siempre visible
        self._disclaimer = NMAIDisclaimer(modo=self._modo, parent=self)
        lay.addWidget(self._disclaimer)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_state(self, state: str):
        self._state = state
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg_color = C("warning_bg", self._modo)
        primary_color = C("primary", self._modo)
        self.setStyleSheet(
            f"QFrame#NMAIPanel {{ "
            f"background-color: {bg_color}; "
            f"border: 1px solid {primary_color}; "
            f"border-radius: {V3_RD['xl']}px; }}"
        )


class NMMoodSlider(QFrame):
    """Slider de estado de ánimo 1-10 con empty state inicial (F1.6).

    Estado INICIAL (null):
    - Track neutral (sin fill de color)
    - Thumb oculto / transparente
    - Display "-- /10"
    - Label "Sin registro"
    - Helper "¿Cómo te sientes hoy?"

    PRIMERA INTERACCIÓN:
    - Revela thumb con opacity 1
    - Track fill usa MOOD_PALETTE según valor seleccionado
    - Display muestra valor numérico (ej: "7 /10")

    Signals:
        value_changed(int): emitido cuando se selecciona valor 1-10
        cleared():          emitido cuando se limpia el slider al estado null
    """

    value_changed = pyqtSignal(int)
    cleared = pyqtSignal()

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._has_value = False  # null state por defecto
        self.setObjectName("NMMoodSlider")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Layout principal ──
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["sm"])

        # ── Label de estado ──
        self._state_label = QLabel("Sin registro")
        self._state_label.setFont(v3_font("size_caption", weight=TYPOGRAPHY["weight_medium"]))
        lay.addWidget(self._state_label)

        # ── Slider row ──
        slider_row = QHBoxLayout()
        slider_row.setSpacing(V3_SP["md"])
        slider_row.setContentsMargins(0, 0, 0, 0)

        # QSlider: range 1-10, sin setValue() al inicio → null state
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 10)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(1)
        self._slider.setObjectName("MoodSliderInternal")
        self._slider.valueChanged.connect(self._on_value_changed)
        self._slider.sliderPressed.connect(self._on_first_interaction)
        slider_row.addWidget(self._slider, stretch=1)

        # Display numérico
        self._display = QLabel("-- /10")
        self._display.setFont(v3_font("size_heading_m", weight=TYPOGRAPHY["weight_semibold"]))
        self._display.setMinimumWidth(60)
        self._display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self._display)

        lay.addLayout(slider_row)

        # ── Helper text ──
        self._helper = QLabel("¿Cómo te sientes hoy?")
        self._helper.setFont(v3_font("size_caption_xs", weight=TYPOGRAPHY["weight_regular"]))
        lay.addWidget(self._helper)

        # Opacity effect para transición suave del thumb
        self._opacity_effect = QGraphicsOpacityEffect(self._slider)
        self._opacity_effect.setOpacity(0.0)  # thumb oculto en estado null
        self._slider.setGraphicsEffect(self._opacity_effect)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _on_first_interaction(self):
        """Primera interacción con el slider: revela thumb progresivamente."""
        if not self._has_value:
            self._has_value = True
            self._animate_thumb_reveal()

    def _animate_thumb_reveal(self):
        """Transición suave de opacity 0 → 1 para el thumb."""
        self._thumb_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._thumb_anim.setDuration(180)
        self._thumb_anim.setStartValue(0.0)
        self._thumb_anim.setEndValue(1.0)
        self._thumb_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._thumb_anim.start()
        self._thumb_anim.finished.connect(self._update_stylesheet)

    def _on_value_changed(self, value: int):
        """Handler interno de valueChanged del QSlider."""
        if self._slider.hasMouse():
            self._apply_theme(self._modo)
        self.value_changed.emit(value)

    def _update_stylesheet(self):
        """Refresca el QSS del slider tras animación."""
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)

        # Colores del tema
        text_primary = v3c("text", self._modo)
        text_secondary = v3c("text2", self._modo)
        surface = v3c("surface", self._modo)
        surface2 = v3c("surface2", self._modo)
        v3c("line", self._modo)

        # Track neutral (sin fill cuando null)
        track_inactive = QColor(surface2)
        track_inactive.setAlpha(100)

        if self._has_value and self._slider.value() > 0:
            # Track fill con color del mood palette
            mood = get_mood(self._slider.value())
            track_fill = QColor(mood["from"])
            track_fill.setAlpha(180)
            thumb_color = mood["from"]
        else:
            # Estado null: sin fill
            track_fill = QColor(surface2)
            track_fill.setAlpha(0)
            thumb_color = QColor(text_secondary).name()

        # Slider QSS
        self._slider.setStyleSheet(f"""
            QSlider#MoodSliderInternal {{
                background: transparent;
            }}
            QSlider#MoodSliderInternal::groove:horizontal {{
                border: none;
                height: 6px;
                background: rgba({track_inactive.red()},{track_inactive.green()},{track_inactive.blue()},{track_inactive.alpha()});
                border-radius: 3px;
                margin: 10px 0;
            }}
            QSlider#MoodSliderInternal::groove:horizontal::sub-page {{
                background: rgba({track_fill.red()},{track_fill.green()},{track_fill.blue()},{track_fill.alpha()});
                border-radius: 3px;
            }}
            QSlider#MoodSliderInternal::handle:horizontal {{
                background: {thumb_color};
                border: 2px solid {surface};
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }}
        """)

        # Label de estado
        self._state_label.setStyleSheet(f"color: {text_secondary.name()}; background: transparent;")
        self._display.setStyleSheet(f"color: {text_primary.name()}; background: transparent;")
        self._helper.setStyleSheet(
            f"color: {text_secondary.name()}; background: transparent; opacity: 0.7;"
        )

    def set_value(self, value: int | None):
        """Establece el valor del slider (1-10) o None para estado vacío."""
        if value is None:
            self._has_value = False
            self._slider.setValue(1)  # reset al mínimo internamente
            self._opacity_effect.setOpacity(0.0)
            self._display.setText("-- /10")
            self._state_label.setText("Sin registro")
            self._apply_theme(self._modo)
        else:
            clamped = max(1, min(10, int(value)))
            self._slider.setValue(clamped)
            if not self._has_value:
                self._has_value = True
                self._opacity_effect.setOpacity(1.0)
            self._display.setText(f"{clamped} /10")
            self._state_label.setText(get_mood(clamped)["name"])
            self._apply_theme(self._modo)

    def get_value(self) -> int | None:
        """Devuelve el valor actual (1-10) o None si está vacío."""
        return self._slider.value() if self._has_value else None

    def clear(self):
        """Limpia el slider al estado null inicial."""
        self._has_value = False
        self._slider.setValue(1)
        self._opacity_effect.setOpacity(0.0)
        self._display.setText("-- /10")
        self._state_label.setText("Sin registro")
        self._apply_theme(self._modo)
        self.cleared.emit()


# ── NMRingPulse ───────────────────────────────────────────────────────────────


class NMRingPulse(QWidget):
    """Anillo único que se expande desde el centro y se desvanece — 500 ms, 1 pulso.

    Uso:
        self._ring_pulse = NMRingPulse(self._content, modo=self._modo)
        # Al finalizar sesión:
        self._ring_pulse.launch()

    El anillo cubre todo el widget padre (overlay transparente a eventos).
    Dos capas concéntricas: teal principal + violet secundario al 88 % del radio.
    """

    def __init__(self, parent: QWidget, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._t = 0.0          # 0→1: controla radio + alpha simultáneamente
        self._max_r = 1.0      # se calcula en launch() según tamaño del padre
        self._anim: QPropertyAnimation | None = None
        self.hide()
        parent.installEventFilter(self)

    # ── resize tracking ───────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type().name in ("Resize", "Move"):
            self.setGeometry(self.parent().rect())
        return super().eventFilter(obj, event)

    # ── pyqtProperty animable ─────────────────────────────────────────────────

    def _get_t(self) -> float:
        return self._t

    def _set_t(self, v: float) -> None:
        self._t = max(0.0, min(1.0, v))
        self.update()

    pulse_t = pyqtProperty(float, _get_t, _set_t)

    # ── API ───────────────────────────────────────────────────────────────────

    def launch(self) -> None:
        """Dispara el pulso. Idempotente: cancela pulso previo si existía."""
        par = self.parent()
        if par is None:
            return
        self.setGeometry(par.rect())
        w, h = float(par.width()), float(par.height())
        self._max_r = (w ** 2 + h ** 2) ** 0.5 / 2.0
        self._t = 0.0
        self.raise_()
        self.show()

        if self._anim:
            try:
                self._anim.stop()
            except RuntimeError:
                pass
        self._anim = QPropertyAnimation(self, b"pulse_t", self)
        self._anim.setDuration(ANIM["ring"])
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    # ── render ────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        if self._t <= 0 or self._max_r <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        center = QPointF(cx, cy)

        is_dark = "dark" in self._modo
        r = self._t * self._max_r
        # Alpha máximo y grosor de trazo difieren por tema:
        # dark → más dramático sobre bg oscuro; light → más sutil sobre bg claro
        a_max = 210 if is_dark else 155
        a = int(a_max * (1.0 - self._t) ** 1.5)
        stroke_main = 2.5 if is_dark else 2.0
        stroke_sec  = 1.5 if is_dark else 1.0

        # Anillo principal — teal
        teal = QColor(v3c("teal", self._modo))
        teal.setAlpha(a)
        p.setPen(QPen(teal, stroke_main))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(center, r, r)

        # Anillo secundario — violet, al 88 % del radio
        violet = QColor(v3c("violet", self._modo))
        sec_mult = 0.55 if is_dark else 0.45
        violet.setAlpha(int(a * sec_mult))
        p.setPen(QPen(violet, stroke_sec))
        p.drawEllipse(center, r * 0.88, r * 0.88)

        p.end()


class _GradientTextLabel(QWidget):
    """Label que pinta texto con gradiente horizontal izquierda→derecha."""

    def __init__(
        self,
        text: str,
        font,
        color_left: str,
        color_right: str,
        height: int = 28,
        margins=(10, 6, 10, 10),
        parent=None,
    ):
        super().__init__(parent)
        self._text = text
        self._font = font
        self._c1 = QColor(color_left)
        self._c2 = QColor(color_right)
        self.setFixedHeight(height)
        self.setContentsMargins(*margins)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_colors(self, color_left: str, color_right: str):
        self._c1 = QColor(color_left)
        self._c2 = QColor(color_right)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self._font)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, self._c1)
        grad.setColorAt(1.0, self._c2)
        p.setPen(QPen(QBrush(grad), 1))
        r = self.contentsRect()
        p.drawText(r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._text)
        p.end()


class NMHubSidebar(QWidget):
    """Sidebar del Hub con nav vertical y pill activo."""

    nav_clicked = pyqtSignal(str)

    def __init__(
        self,
        items: list[tuple[str, str, str]],
        active: str = "",
        modo: str = None,
        parent=None,
        product: str = "Hub",
        sidebar_width: int = 200,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active = active or (items[0][0] if items else "")
        self._items_tuple = items
        self._product = product.lower()
        self._collapsed = False
        self._buttons: dict[str, QPushButton] = {}
        self._expanded_width = sidebar_width
        self._collapsed_width = 60
        self.setFixedWidth(sidebar_width)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        self._layout = lay
        lay.setContentsMargins(8, 10, 8, 10)
        lay.setSpacing(4)
        self._logo_icon = QLabel()
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._logo_icon.setContentsMargins(12, 10, 12, 10)
        self._logo_icon.setStyleSheet("background: transparent;")
        self._section_title = QLabel(
            "Herramientas" if product.lower() == "suite" else "Panel Profesional"
        )
        self._section_title.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        self._section_title.setContentsMargins(12, 0, 12, 10)
        self._section_title.setStyleSheet("background: transparent;")
        if self._product == "suite":
            self._logo_icon.hide()
            lay.addWidget(self._section_title)
            self._logo_text = self._section_title
        else:
            self._section_title.hide()
            lay.addWidget(self._logo_icon)
            self._logo_text = self._logo_icon
        for key, icon, label in items:
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            try:
                qicon = nm_icon(icon, C("ink_secondary", self._modo), size=16)
                if qicon and not qicon.isNull():
                    btn.setIcon(qicon)
                    btn.setIconSize(QSize(18, 18))
            except Exception:
                pass
            btn.clicked.connect(lambda checked=False, k=key: self._select(k))
            lay.addWidget(btn)
            self._buttons[key] = btn
        lay.addStretch()
        # M3 F4: saludo del profesional en serif (Newsreader) para calidez emocional
        # — el Suite usa serif en los saludos del Home; el Hub debe resonar.
        self._footer = QLabel()
        try:
            self._footer.setFont(v3_font("size_caption", "weight_semibold", serif=True))
        except Exception:
            self._footer.setFont(qfont("size_caption"))
        self._footer.setContentsMargins(10, 10, 10, 4)
        self._footer.setWordWrap(True)
        lay.addWidget(self._footer)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_footer(self, text: str):
        text = (text or "").strip()
        self._footer.setText(text)
        self._footer.setVisible(bool(text) and not self._collapsed)

    def set_collapsed(self, collapsed: bool):
        """Colapsa la sidebar a solo iconos y conserva el isotipo de marca."""
        self._collapsed = bool(collapsed)
        self.setFixedWidth(self._collapsed_width if collapsed else self._expanded_width)
        if self._logo_text is self._logo_icon:
            self._logo_icon.setVisible(True)
        else:
            self._logo_text.setVisible(not collapsed)
        self._footer.setVisible(bool(self._footer.text().strip()) and not collapsed)
        _labels = {item[0]: item[2] for item in self._items_tuple}
        for key, btn in self._buttons.items():
            btn.setText("" if collapsed else f"  {_labels.get(key, '')}")
            btn.setToolTip(_labels.get(key, "") if collapsed else "")
        self._apply_theme(self._modo)

    def set_active(self, key: str):
        self._active = key
        self._apply_theme(self._modo)

    def _select(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo

        if hasattr(self, "_logo_icon") and self._logo_icon.parent() is not None:
            if self._logo_text is self._logo_icon:
                if self._collapsed:
                    from shared.assets import nm_logo_pixmap

                    self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._logo_icon.setContentsMargins(0, 10, 0, 10)
                    self._logo_icon.setFixedHeight(48)
                    self._logo_icon.setPixmap(
                        nm_logo_pixmap(self._modo, tipo="icon", width=30, height=30)
                    )
                    self._logo_icon.show()
                    self._section_title.hide()
                else:
                    from shared.assets import obtener_ruta_asset

                    logo_filename = "logo_dark.png" if is_dark else "logo_light.png"
                    logo_path = obtener_ruta_asset(logo_filename)
                    self._logo_icon.setAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                    self._logo_icon.setContentsMargins(12, 10, 12, 10)
                    self._logo_icon.setFixedHeight(56)
                    if os.path.exists(logo_path):
                        pm = QPixmap(logo_path)
                        self._logo_icon.setPixmap(
                            pm.scaledToWidth(130, Qt.TransformationMode.SmoothTransformation)
                        )
                        self._logo_icon.show()
                        self._section_title.hide()
                    else:
                        self._section_title.setText("NeuroMood Hub")
                        self._section_title.show()
                        self._logo_icon.hide()
            else:
                self._section_title.show()
                self._logo_icon.hide()

        # Sidebar sólida del mockup: bg-sidebar + borde line, sin glass.
        # Separación visual explícita (Rule 7, 8, 9): usamos bg_sidebar para contraste con el fondo
        bg = v3c("bg_sidebar", self._modo)
        bg_css = bg.name()
        border_c = v3c("border", self._modo)
        # BL-08/BL-10: divisor vertical más sutil (antes 180/140 = duro). El
        # contraste bg_sidebar vs fondo ya separa; el borde solo lo acompaña.
        border_alpha = 110 if is_dark else 85
        border_rgba = f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},{border_alpha})"
        self.setStyleSheet(
            f"NMHubSidebar {{ background-color: {bg_css}; border-right: 1px solid {border_rgba}; }}"
        )

        if hasattr(self, "_section_title"):
            self._section_title.setStyleSheet(
                f"color: {v3c('mute', self._modo).name()}; "
                "background: transparent;"
            )

        # ── Footer ───────────────────────────────────────────────────
        ink_secondary_hex = v3c("ink_secondary", self._modo).name()
        self._footer.setStyleSheet(
            f"color: {ink_secondary_hex}; background: transparent; border: none;"
        )

        # ── Nav buttons ────────────────────────────────────────────────
        primary_hex = v3c("primary", self._modo).name()
        primary_ink = v3c("primary_ink", self._modo).name()
        text_hex = v3c("text", self._modo).name()
        text2_hex = v3c("text2", self._modo).name()
        primary_soft = (
            f"rgba({v3c('primary', self._modo).red()},"
            f"{v3c('primary', self._modo).green()},"
            f"{v3c('primary', self._modo).blue()}, 25)"
        )
        font_pt = TYPOGRAPHY["size_small"]

        for key, btn in self._buttons.items():
            active = key == self._active
            btn.setFixedHeight(38)
            align = "center" if self._collapsed else "left"
            padding = "8px 0px" if self._collapsed else "8px 10px"
            radius = 12 if self._collapsed else 8
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  text-align: {align};"
                f"  background: {primary_hex if active else 'transparent'};"
                f"  color: {primary_ink if active else text2_hex};"
                f"  border: none;"
                f"  border-radius: {radius}px;"
                # 10px: con la sidebar angosta (172) el padding 12 cortaba
                # "Personalización" (el label más largo).
                f"  padding: {padding};"
                f"  font-size: {font_pt}px;"
                f"  font-weight: 500;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: {primary_hex if active else primary_soft};"
                f"  color: {primary_ink if active else text_hex};"
                f"}}"
            )
            # Icon: primary_ink when active, text2 at rest
            icon_color = primary_ink if active else text2_hex
            for item in self._items_tuple:
                if item[0] == key:
                    try:
                        qicon = nm_icon(item[1], icon_color, size=16)
                        if qicon and not qicon.isNull():
                            btn.setIcon(qicon)
                            icon_px = 20 if self._collapsed else 18
                            btn.setIconSize(QSize(icon_px, icon_px))
                    except Exception:
                        pass
                    break


class FlowLayout(QLayout):
    """Layout que acomoda los items en filas y los envuelve a la línea siguiente
    cuando no entran en el ancho disponible (patrón estándar de Qt).

    Pensado para grupos de chips/badges que no deben desbordar ni recortarse a
    anchos chicos (regla anti-solape del HANDOFF §3). Implementa
    ``heightForWidth`` para que el contenedor reserve el alto correcto al envolver.
    """

    def __init__(self, parent=None, margin: int = 0, spacing: int = 6):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self._spacing = spacing
        self._items = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only: bool):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        right = rect.right() - m.right()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            w, h = hint.width(), hint.height()
            next_x = x + w
            if next_x > right and line_height > 0:
                x = rect.x() + m.left()
                y = y + line_height + self._spacing
                next_x = x + w
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x + self._spacing
            line_height = max(line_height, h)
        return y + line_height - rect.y() + m.bottom()


class NMFeaturedCard(QFrame):
    """Card principal del Hub Dashboard con blob gradient de fondo.

    Muestra ánimo promedio como número grande + emoji + subtítulo.
    API: set_score(float, str), set_delta(float|None), set_meta(str), set_tags(list[tuple[str,str]])
    """

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(140)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("lg"), sp("md"), sp("lg"), sp("md"))
        lay.setSpacing(sp("xs") if hasattr(sp, "__call__") else 4)

        # Sub-label superior teal uppercase (ej. "Ánimo promedio · semana")
        self._title_lbl = QLabel("Ánimo promedio · semana")
        self._title_lbl.setFont(qfont("size_caption", bold=True))
        self._title_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._title_lbl)

        # Fila: score grande + "/10" + emoji + delta pill
        score_row = QHBoxLayout()
        score_row.setSpacing(sp("sm"))
        self._score_lbl = QLabel("—")
        self._score_lbl.setFont(qfont("size_h1", bold=True))
        self._score_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._score_lbl)

        self._slash_lbl = QLabel("/ 10")
        self._slash_lbl.setFont(qfont("size_small"))
        self._slash_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._slash_lbl)

        self._emoji_lbl = QLabel("\U0001f610")
        self._emoji_lbl.setFont(qfont("size_h2"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        score_row.addWidget(self._emoji_lbl)

        self._delta_lbl = QLabel()
        self._delta_lbl.setFont(qfont("size_caption", bold=True))
        self._delta_lbl.setVisible(False)
        score_row.addWidget(self._delta_lbl)

        score_row.addStretch()
        lay.addLayout(score_row)

        # Meta line: "N semanas en programa · Última sesión: hace X días"
        self._sub_lbl = QLabel()
        self._sub_lbl.setFont(qfont("size_small"))
        self._sub_lbl.setStyleSheet("background: transparent;")
        self._sub_lbl.setVisible(False)
        lay.addWidget(self._sub_lbl)

        # Tags row (pills) — FlowLayout: los chips envuelven en vez de desbordar.
        self._tags_widget = QWidget()
        self._tags_widget.setStyleSheet("background: transparent;")
        _tags_pol = self._tags_widget.sizePolicy()
        _tags_pol.setHeightForWidth(True)
        self._tags_widget.setSizePolicy(_tags_pol)
        self._tags_layout = FlowLayout(
            self._tags_widget, margin=0, spacing=sp("sm") if hasattr(sp, "__call__") else 8
        )  # 8px gap per F3.3
        self._tags_widget.setVisible(False)
        lay.addWidget(self._tags_widget)

        # Sparkline de área (tendencia semanal de ánimo). Va debajo de las
        # métricas para que la línea nunca cruce chips ni labels.
        self._spark = NMAreaSparkline(modo=self._modo)
        self._spark.setVisible(False)
        lay.addWidget(self._spark)

        lay.addStretch()

        self._last_delta = None  # cache para re-aplicar en cambio de tema

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_score(self, score: float, emoji: str = "\U0001f610"):
        self._score_lbl.setText(f"{score:.1f}")
        self._emoji_lbl.setText(emoji)
        self.update()

    def set_delta(self, delta):
        """Muestra pill con delta vs semana anterior. None oculta el pill."""
        self._last_delta = delta
        if delta is None:
            self._delta_lbl.setVisible(False)
            return
        sign = "↑" if delta >= 0 else "↓"
        text = f"{sign} {abs(delta):.1f} vs semana anterior"
        self._delta_lbl.setText(text)
        teal = C("teal", self._modo)
        amber = C("warning", self._modo)
        bg_color = _rgba(teal, 0.14) if delta >= 0 else _rgba(amber, 0.14)
        fg_color = teal if delta >= 0 else amber
        self._delta_lbl.setStyleSheet(
            f"QLabel {{ background: {bg_color}; color: {fg_color}; "
            f"border-radius: 10px; padding: 2px 8px; }}"
        )
        self._delta_lbl.setVisible(True)

    def set_series(self, data, labels=None):
        """Serie semanal de ánimo para el sparkline de área. Lista vacía la oculta."""
        if not data:
            self._spark.setVisible(False)
            return
        self._spark.set_series(data, labels)
        self._spark.setVisible(True)

    def set_meta(self, text: str):
        """Muestra línea gris con meta info (semanas, última sesión)."""
        if not text:
            self._sub_lbl.setVisible(False)
            return
        self._sub_lbl.setText(text)
        self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._sub_lbl.setVisible(True)

    def set_tags(self, tags):
        """tags: list[tuple[str, str]] donde str2 es 'teal'|'violet'|'accent'."""
        # Limpiar tags anteriores
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item is not None and item.widget():
                item.widget().deleteLater()
        if not tags:
            self._tags_widget.setVisible(False)
            return
        color_map = {
            "teal": ("teal", 0.14),
            "violet": ("violet", 0.14),
            "accent": ("accent", 0.14),
        }
        for label_text, color_key in tags[:3]:
            key, alpha = color_map.get(color_key, ("teal", 0.14))
            fg = C(key, self._modo)
            bg = _rgba(fg, alpha)
            chip = QLabel(label_text)
            chip.setFont(qfont("size_caption", bold=True))
            chip.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {fg}; "
                f"border-radius: 10px; padding: 2px 9px; }}"
            )
            self._tags_layout.addWidget(chip)
        self._tags_widget.setVisible(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        r = RADIUS_CARD
        is_dark = "dark" in self._modo
        surf_col = v3c("surfaceSolid" if is_dark else "surface", self._modo)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, surf_col)

        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.restore()
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        teal = C("teal", self._modo)
        self._title_lbl.setStyleSheet(
            f"color: {teal}; background: transparent;"
        )
        self._score_lbl.setStyleSheet(
            f"color: {C('text_primary', self._modo)}; background: transparent;"
        )
        self._slash_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._emoji_lbl.setStyleSheet("background: transparent;")
        if self._sub_lbl.isVisible():
            self._sub_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        # Re-aplicar delta con los nuevos colores de tema
        if hasattr(self, "_last_delta"):
            self.set_delta(self._last_delta)
        self.update()


# ── NMModuleRing ──────────────────────────────────────────────────────────────


class NMModuleRing(QWidget):
    """Arco circular de progreso para cards de módulo del Hub.

    Color semántico: ≥80%→teal, 50-79%→accent, <50%→violet (via ring_color()).

    ``show_label``: si True (default), pinta "NN%" centrado. En tamaños pequeños
    (<32px) el label es ilegible — usar show_label=False y delegar el % a una
    chip/badge externa.
    """

    def __init__(
        self,
        size: int = 56,
        pct: float = 0.0,
        modo: str = None,
        show_label: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct = max(0.0, min(1.0, pct))
        self._size = size
        self._show_label = bool(show_label)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_pct(self, pct: float):
        self._pct = max(0.0, min(1.0, pct))
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        s = self._size
        cx, cy = s / 2, s / 2
        pen_w = _ring_stroke(s)
        r_arc = s / 2 - pen_w - 1
        arc_rect = QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2)

        # (F2 ADN Claude: el glow radial teal detrás del arco fue eliminado —
        # el anillo se sostiene solo con track + arco firma, sin halo.)

        # Track sutil (borderSoft v3 — TODOS los rings usan el mismo lenguaje)
        track_c = v3c("borderSoft", self._modo)
        p.setPen(QPen(track_c, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r_arc, r_arc)

        # Arco progreso con gradient firma v3 (uniforme entre rings)
        if self._pct > 0.001:
            _paint_v3_arc(p, arc_rect, 90.0, -360.0 * self._pct, pen_w, self._modo)

        # Texto centrado (solo si show_label=True; tamaños chicos no lo pintan)
        if self._show_label:
            p.setPen(v3c("text", self._modo))
            p.setFont(qfont_mono(max(9, int(s * 0.20)), bold=False))
            p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, f"{int(self._pct * 100)}%")

        p.restore()
        p.end()


# ── NMChatBubble ──────────────────────────────────────────────────────────────


class NMChatBubble(QWidget):
    """Burbuja de chat v3 (Hub IA).

      - ``side="left"``  → IA       (surface + borderSoft, texto principal).
      - ``side="right"`` → usuario  (gradient firma teal→violet, texto on-accent).

    Soporta ``typing=True``: muestra ``...`` que se actualiza cíclicamente cada
    400ms (placeholder ligero; para una animación con `NMTypingDots` pleno,
    instanciar éste como hijo).
    """

    def __init__(
        self,
        text: str = "",
        side: str = "left",
        modo: str = None,
        typing: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._side = side
        self._typing = bool(typing)
        self._typing_dots_state = 1
        self._original_text = text
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(0)

        if side == "right":
            outer.addStretch()

        self._bubble = QLabel(text)
        self._bubble.setFont(qfont("size_body"))
        self._bubble.setWordWrap(True)
        self._bubble.setMaximumWidth(480)
        # H-08: ensure minimum height for 2-3 lines of text
        self._bubble.setMinimumHeight(52)
        self._bubble.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        self._bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(self._bubble)

        if side == "left":
            outer.addStretch()

        # Timer interno para typing dots
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(400)
        self._typing_timer.timeout.connect(self._tick_typing)
        if self._typing:
            self._typing_timer.start()
            self._refresh_typing_text()

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_text(self, text: str):
        self._original_text = text
        self._typing = False
        if self._typing_timer.isActive():
            self._typing_timer.stop()
        self._bubble.setText(text)

    def set_typing(self, typing: bool):
        """Activa/desactiva el indicador de 'IA escribiendo' (3 dots cíclicos)."""
        self._typing = bool(typing)
        if self._typing:
            self._typing_timer.start()
            self._refresh_typing_text()
        else:
            self._typing_timer.stop()
            self._bubble.setText(self._original_text)

    def _tick_typing(self):
        self._typing_dots_state = (self._typing_dots_state % 3) + 1
        self._refresh_typing_text()

    def _refresh_typing_text(self):
        self._bubble.setText("●" * self._typing_dots_state + "○" * (3 - self._typing_dots_state))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        r = V3_RD["lg"]  # radius 14
        pad = f"padding: {V3_SP['sm']}px {V3_SP['md']}px;"
        fsize = f"font-size: {TYPOGRAPHY['size_body']}px;"
        if self._side == "left":
            # IA — superficie clara con borderSoft, cola en top-left
            surf_key = "surfaceSolid" if is_dark else "surface"
            bg = v3c(surf_key, self._modo).name()
            col = v3c("text", self._modo).name()
            border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
            radii = (
                f"border-top-left-radius: 3px; "
                f"border-top-right-radius: {r}px; "
                f"border-bottom-left-radius: {r}px; "
                f"border-bottom-right-radius: {r}px;"
            )
            self._bubble.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {col}; "
                f"border: 1px solid {border}; {radii} {pad} {fsize} }}"
            )
        else:
            # Usuario — low-opacity primary tint + solid primary border, cola en top-right
            bg_color = v3c("primarySoft", self._modo)
            bg_css = qcolor_to_rgba_css(bg_color)
            border_color = v3c("primary", self._modo).name()
            text_col = v3c("text", self._modo).name()
            radii = (
                f"border-top-left-radius: {r}px; "
                f"border-top-right-radius: 3px; "
                f"border-bottom-left-radius: {r}px; "
                f"border-bottom-right-radius: {r}px;"
            )
            self._bubble.setStyleSheet(
                f"QLabel {{ background: {bg_css}; color: {text_col}; "
                f"border: 1px solid {border_color}; {radii} {pad} {fsize} }}"
            )


# ── NMTypingDots ──────────────────────────────────────────────────────────────


class NMTypingDots(QWidget):
    """Indicador animado de 'IA escribiendo...' (3 puntos secuenciales).

    Llamar a start()/stop() para controlar la animación.
    """

    # Spec README v3: "3 dots con animación translateY(-4px) escalonada
    # (delay 0/0.15/0.3s)" — implementado con phase continuous + sin wave.
    _PERIOD_MS = 1200  # ciclo completo
    _STAGGER_MS = 150  # 0.15s entre dots
    _BOUNCE_PX = 4  # translateY -4px en el pico

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._t_ms = 0
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 fps (suave para anim continua)
        self._timer.timeout.connect(self._tick)
        self._running = False
        self.setFixedSize(48, 24)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def start(self):
        self._running = True
        self._t_ms = 0
        self._timer.start()

    def stop(self):
        self._running = False
        self._timer.stop()
        self.update()

    def _tick(self):
        if sip.isdeleted(self):
            self._timer.stop()
            return
        self._t_ms = (self._t_ms + 33) % self._PERIOD_MS
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        import math

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        dot_r = 4
        gap = 12
        y_c = self.height() / 2
        x_start = dot_r + 2
        base_c = QColor(C("teal", self._modo))
        for i in range(3):
            # Phase shift por dot — 0.15s stagger
            if self._running:
                phase = ((self._t_ms - i * self._STAGGER_MS) % self._PERIOD_MS) / self._PERIOD_MS
                # bounce: pico arriba en phase 0.5, queda abajo en 0/1
                # Usamos curva senoidal solo en la primera mitad del ciclo
                if 0 <= phase < 0.5:
                    bounce = math.sin(phase * math.pi)  # 0→1→0
                else:
                    bounce = 0.0
                offset_y = -self._BOUNCE_PX * bounce
                alpha = 0.4 + 0.6 * bounce  # 0.4 idle, 1.0 peak
            else:
                offset_y = 0.0
                alpha = 0.3
            dc = QColor(base_c)
            dc.setAlphaF(alpha)
            p.setBrush(QBrush(dc))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x_start + i * gap, y_c + offset_y), dot_r, dot_r)
        p.restore()
        p.end()


# ── NMSyncOrb ─────────────────────────────────────────────────────────────────


class NMProviderChip(QWidget):
    """Chip compacto para proveedor/modelo IA activo."""

    def __init__(
        self, text: str = "IA verificando", state: str = "syncing", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)
        self._dot = NMSyncOrb(state=state, size=7, modo=self._modo, parent=self)
        lay.addWidget(self._dot)
        self._label = QLabel(text)
        self._label.setFont(qfont("size_caption"))
        lay.addWidget(self._label)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_status(self, text: str, state: str = "ok"):
        self._state = state
        self._dot.set_state(state)
        self._label.setText(text)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = C("teal", self._modo) if self._state == "ok" else c.get("border_card", c["border"])
        bg = _rgba(C("teal", self._modo), 0.10 if self._state == "ok" else 0.04)
        self.setStyleSheet(
            f"QWidget {{ background: {bg}; border: 1px solid {_rgba(border, 0.35)}; "
            f"border-radius: {RADIUS_PILL}px; }}"
        )
        self._label.setStyleSheet(label_style(self._modo, "text_secondary"))


class NMQuickAction(QPushButton):
    """Boton de sugerencia rapida del panel IA."""

    def __init__(self, text: str, modo: str = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(30)
        self.setFont(qfont("size_caption"))
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c['text_secondary']}; "
            f"border: 1px solid {c.get('border_card', c['border'])}; "
            f"border-radius: {RADIUS_BUTTON}px; padding: 6px 10px; text-align: left; }}"
            f"QPushButton:hover {{ color: {C('teal', self._modo)}; "
            f"border-color: {_rgba(C('teal', self._modo), 0.35)}; "
            f"background: {_rgba(C('teal', self._modo), 0.06)}; }}"
        )


class NMPatientContext(QFrame):
    """Panel lateral de contexto de paciente para IA."""

    def __init__(self, paciente: str = "Sin paciente", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._rows: dict[str, QLabel] = {}
        self.setMinimumWidth(240)
        self.setMaximumWidth(270)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        self._title = QLabel("Contexto")
        self._title.setFont(qfont("size_body", bold=True))
        lay.addWidget(self._title)
        for key, label, value in [
            ("paciente", "Paciente", paciente),
            ("semanas", "Semanas", "12"),
            ("animo", "Ánimo 7d", "7.2/10"),
            ("distorsiones", "Distorsiones", "3"),
            ("progreso", "Progreso", "5d"),
        ]:
            row = QWidget()
            row_l = QVBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(1)
            lbl = QLabel(label)
            lbl.setFont(qfont("size_caption"))
            v = QLabel(value)
            v.setFont(qfont("size_small", bold=True))
            row_l.addWidget(lbl)
            row_l.addWidget(v)
            lay.addWidget(row)
            self._rows[key] = v
        lay.addStretch()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_patient(self, paciente: str):
        if "paciente" in self._rows:
            self._rows["paciente"].setText(paciente or "Sin paciente")

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(
            f"QFrame {{ background: {c['bg_secondary']}; "
            f"border-left: 1px solid {c.get('border_card', c['border'])}; }}"
        )
        self._title.setStyleSheet(label_style(self._modo, "text_primary"))
        for key, lbl in self._rows.items():
            color_key = (
                "teal"
                if key == "animo"
                else ("violet" if key == "distorsiones" else "text_primary")
            )
            lbl.setStyleSheet(label_style(self._modo, color_key))
        for label in self.findChildren(QLabel):
            if label is self._title or label in self._rows.values():
                continue
            label.setStyleSheet(label_style(self._modo, "text_tertiary"))


class NMSyncOrb(QWidget):
    """Orb circular de estado de sincronización con animación de pulso.

    state: 'ok' (verde) | 'error' (rojo) | 'syncing' (ámbar, pulsa).
    """

    def __init__(self, state: str = "ok", size: int = 12, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._state = state
        self._anim_alpha = 255
        self._fade_dir = -1
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._pulse)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.set_state(state)
        _tm().theme_changed.connect(self._apply_theme)

    def set_state(self, state: str):
        self._state = state
        if state == "syncing":
            self._timer.start()
        else:
            self._timer.stop()
            self._anim_alpha = 255
        self.update()

    def _pulse(self):
        if sip.isdeleted(self):
            self._timer.stop()
            return
        self._anim_alpha += self._fade_dir * 14
        if self._anim_alpha <= 70:
            self._fade_dir = 1
        elif self._anim_alpha >= 255:
            self._fade_dir = -1
        self.update()

    def _color(self) -> QColor:
        key = {"ok": "sync_orb_green", "error": "error"}.get(self._state, "warning")
        return QColor(C(key, self._modo))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        c = self._color()

        # Glow halo radial — alpha modulado por pulso (max 100)
        glow = QRadialGradient(cx, cy, cx)
        glow_c = QColor(c)
        glow_c.setAlpha(int(self._anim_alpha * 0.39))  # ~100 en estado estático
        transparent = QColor(c)
        transparent.setAlpha(0)
        glow.setColorAt(0.3, glow_c)
        glow.setColorAt(1.0, transparent)
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(0, 0, w, h))

        # Círculo sólido centrado
        c.setAlpha(self._anim_alpha)
        p.setBrush(QBrush(c))
        m = max(1, w // 4)
        p.drawEllipse(QRectF(m, m, w - m * 2, h - m * 2))

        p.restore()
        p.end()


# ── NMInstallStepper ──────────────────────────────────────────────────────────


class NMInstallStepper(QWidget):
    """Stepper horizontal para instaladores y desinstaladores (3-5 pasos).

    Siempre usa dark mode (instaladores son siempre dark).
    Accent configurable: 'teal' para Suite, 'violet' para NeuroMood Hub.
    """

    def __init__(self, steps: list[str], current: int = 0, accent_key: str = "teal", parent=None):
        super().__init__(parent)
        self._steps = steps
        self._current = current
        self._accent_key = accent_key
        self._modo = "dark_hybrid"
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_step(self, idx: int):
        self._current = max(0, min(len(self._steps) - 1, idx))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        n = len(self._steps)
        if n == 0:
            p.restore()
            p.end()
            return

        w, _h = self.width(), self.height()
        circle_r = 12
        cy = 20
        step_w = w / n
        accent_key = {
            "error": "danger",
            "red": "danger",
            "destructive": "danger",
            "hub": "violet",
            "suite": "teal",
        }.get(self._accent_key, self._accent_key)
        accent = C(accent_key, self._modo)

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                lc = QColor(accent if i <= self._current else C("border", self._modo))
                p.setPen(QPen(lc, 2))
                p.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            circ_rect = QRectF(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
            if i < self._current:
                p.setBrush(QBrush(QColor(accent)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
                p.setFont(qfont("size_caption", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, "✓")
            elif i == self._current:
                p.setBrush(QBrush(QColor(accent)))
                p.setPen(QPen(QColor(C("bg_primary", self._modo)), 2))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_on_accent", self._modo)))
                p.setFont(qfont("size_caption", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(C("border", self._modo)), 1))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_tertiary", self._modo)))
                p.setFont(qfont("size_caption"))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            col = "text_primary" if i == self._current else "text_tertiary"
            p.setPen(QColor(C(col, self._modo)))
            p.setFont(qfont("size_caption"))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 4, step_w - 8, 14),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        p.restore()
        p.end()


# ── NMDataPreserveCard ────────────────────────────────────────────────────────


class NMDataPreserveCard(QWidget):
    """Card de decisión crítica para desinstaladores.

    Muestra ícono de advertencia + título + descripción + toggle switch gradient.
    Emite toggled(bool). Siempre dark mode.
    """

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, description: str, checked: bool = True, parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._checked = checked
        self.setObjectName("NMDataPreserveCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(sp("lg"), sp("md"), sp("lg"), sp("md"))
        lay.setSpacing(sp("sm"))

        # Warning header
        header = QHBoxLayout()
        warn = QLabel("⚠️")
        warn.setFont(qfont("size_h3"))
        warn.setStyleSheet("background: transparent;")
        header.addWidget(warn)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_body", bold=True))
        self._title_lbl.setStyleSheet(
            f"color: {C('warning', self._modo)}; background: transparent;"
        )
        header.addWidget(self._title_lbl, stretch=1)
        lay.addLayout(header)

        self._desc_lbl = QLabel(description)
        self._desc_lbl.setFont(qfont("size_small"))
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._desc_lbl)

        # Toggle row
        toggle_row = QHBoxLayout()
        self._state_lbl = QLabel("Activado" if checked else "Desactivado")
        self._state_lbl.setFont(qfont("size_small", bold=True))
        self._state_lbl.setStyleSheet("background: transparent;")
        toggle_row.addWidget(self._state_lbl, stretch=1)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setFixedSize(52, 28)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)
        toggle_row.addWidget(self._toggle_btn)
        lay.addLayout(toggle_row)

        self._apply_theme(self._modo)

    def _toggle(self):
        self._checked = not self._checked
        self._state_lbl.setText("Activado" if self._checked else "Desactivado")
        self._apply_theme(self._modo)
        self.toggled.emit(self._checked)

    def is_checked(self) -> bool:
        return self._checked

    def _apply_theme(self, modo: str = None):
        c = colors(self._modo)
        self.setStyleSheet(
            f"QWidget#NMDataPreserveCard {{ "
            f"background: {c['bg_surface']}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {C('warning', self._modo)}; }}"
        )
        self._desc_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))
        if self._checked:
            self._toggle_btn.setText("✓")
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {C('teal', self._modo)}, stop:1 {C('accent', self._modo)}); "
                f"color: {C('text_on_accent', self._modo)}; font-weight: 500; "
                f"border-radius: 14px; border: none; min-height: 0px; padding: 0px; }}"
            )
            self._state_lbl.setStyleSheet(
                f"color: {C('teal', self._modo)}; background: transparent;"
            )
        else:
            self._toggle_btn.setText("")
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: {c['bg_elevated']}; "
                f"border-radius: 14px; border: 1px solid {c['border']}; "
                f"min-height: 0px; padding: 0px; }}"
            )
            self._state_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))


# ══════════════════════════════════════════════════════════════════════════════
# V3MoodSlider + NMPlayButton — componentes nuevos v3 (aditivos)
# ══════════════════════════════════════════════════════════════════════════════

# ── helpers privados para clicks tipados ──────────────────────────────────────


class _MoodPickWidget(QWidget):
    """Widget interno que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, value: int, parent=None):
        super().__init__(parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


class _MoodPickLabel(QLabel):
    """QLabel que emite ``picked(int)`` al hacer click izquierdo."""

    picked = pyqtSignal(int)

    def __init__(self, text: str, value: int, parent=None):
        super().__init__(text, parent)
        self._value = value
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(self._value)
        super().mousePressEvent(event)


# ── _MoodTrackBar (subcomponente del V3MoodSlider) ───────────────────────────


class _MoodNumRow(QWidget):
    """Fila de números 0-10 posicionados EXACTAMENTE bajo los slots del track.

    Usa la misma fórmula que ``_MoodTrackBar._slot_positions`` (margen 16 +
    i/10 del ancho útil). Con el layout anterior de stretches, el centro de
    cada número quedaba ~10px corrido del dot real del slider (informe owner
    v1.0, módulo Ánimo).
    """

    def __init__(self, labels: list[QLabel], parent=None):
        super().__init__(parent)
        self._labels = labels
        self.setFixedHeight(20)
        for lbl in labels:
            lbl.setParent(self)
            lbl.setFixedSize(24, 20)

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        margin = 16
        span = max(0, self.width() - 2 * margin)
        for i, lbl in enumerate(self._labels):
            x = margin + (i / 10) * span
            lbl.move(int(x - lbl.width() / 2), 0)


class _MoodTrackBar(QWidget):
    """Track horizontal con gradient arcoíris emocional + 10 dots clickeables.

    El gradient NO varía con el theme (paleta emocional fija, ver README v3).
    El dot activo: 16x16 blanco con border 3px del color del nivel + halo.
    Dots inactivos: 6x6 semi-transparentes.
    """

    level_clicked = pyqtSignal(int)

    # 7-stop rainbow emocional (literal del README v3)
    _RAINBOW_STOPS = (
        ("#5b6cb8", 0.00),
        ("#7ba8e6", 0.22),
        ("#f5d76a", 0.50),
        ("#5dd6a3", 0.70),
        ("#36cfb8", 0.80),
        ("#a78bfa", 0.95),
        ("#ec4899", 1.00),
    )

    def __init__(self, level: int = 5, parent=None, unset: bool = False):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        # Muesca 0 (feedback owner v1.0): el thumb arranca ESTACIONADO en un
        # 0 visual que NO es un valor registrable — al primer click/drag se
        # mueve a 1-10 y deja de estar unset. El 0 no responde a clicks.
        self._unset = bool(unset)
        self.setFixedHeight(56)
        self.setMinimumWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level or self._unset:
            self._level = lv
            self._unset = False
            self.update()

    def level(self) -> int:
        return self._level

    def set_unset(self, unset: bool = True):
        self._unset = bool(unset)
        self.update()

    def is_unset(self) -> bool:
        return self._unset

    def _slot_positions(self) -> list[float]:
        """11 slots equiespaciados: índice 0 = muesca de estacionamiento,
        índices 1-10 = niveles registrables."""
        margin_x = 16
        w = self.width() - 2 * margin_x
        return [margin_x + (i / 10) * w for i in range(11)]

    def _dot_positions(self) -> list[float]:
        return self._slot_positions()[1:]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        bar_y = h // 2 - 4
        bar_h = 8
        margin_x = 16
        bar_w = self.width() - 2 * margin_x
        bar_rect = QRectF(margin_x, bar_y, bar_w, bar_h)

        # Track con gradient rainbow (opacity .85 según JSX)
        grad = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
        for hex_c, pos in self._RAINBOW_STOPS:
            grad.setColorAt(pos, QColor(hex_c))
        path = QPainterPath()
        path.addRoundedRect(bar_rect, bar_h / 2, bar_h / 2)
        p.setOpacity(0.85)
        p.fillPath(path, QBrush(grad))
        p.setOpacity(1.0)

        # Muesca 0 (estacionamiento): anillo neutro sutil; el thumb descansa
        # acá mientras el paciente no eligió valor. Theme-aware: en light el
        # anillo blanco-sobre-card-clara era INVISIBLE (informe owner v1.0) —
        # se delinea con slate oscuro.
        _is_dark = "dark" in norm_modo(_tm().modo)
        slot0_x = self._slot_positions()[0]
        center_y = h / 2
        if self._unset:
            if _is_dark:
                ring = QColor(255, 255, 255, 200)
                halo = QColor(255, 255, 255, 40)
            else:
                ring = QColor(71, 85, 105, 230)
                halo = QColor(71, 85, 105, 36)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(halo))
            p.drawEllipse(QPointF(slot0_x, center_y), 12, 12)
            p.setBrush(QBrush(QColor("#ffffff")))
            p.setPen(QPen(ring, 2))
            p.drawEllipse(QPointF(slot0_x, center_y), 7, 7)
        else:
            _parked = (
                QColor(255, 255, 255, 110) if _is_dark else QColor(71, 85, 105, 110)
            )
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_parked))
            p.drawEllipse(QPointF(slot0_x, center_y), 2.5, 2.5)

        # Dots (10)
        positions = self._dot_positions()
        for i, x in enumerate(positions):
            n = i + 1
            lv_color = get_mood(n)["to"]
            if n == self._level and not self._unset:
                # Halo exterior
                halo = QColor(lv_color)
                halo.setAlpha(64)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(halo))
                p.drawEllipse(QPointF(x, center_y), 14, 14)
                # Halo intermedio
                halo2 = QColor(lv_color)
                halo2.setAlpha(110)
                p.setBrush(QBrush(halo2))
                p.drawEllipse(QPointF(x, center_y), 10, 10)
                # Dot blanco con borde
                p.setBrush(QBrush(QColor("#ffffff")))
                p.setPen(QPen(QColor(lv_color), 3))
                p.drawEllipse(QPointF(x, center_y), 8, 8)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 180)))
                p.drawEllipse(QPointF(x, center_y), 3, 3)
        p.end()

    def _level_at_x(self, x: float) -> int:
        # Solo niveles 1-10: la muesca 0 es inerte (no registrable).
        positions = self._dot_positions()
        return min(range(10), key=lambda i: abs(positions[i] - x)) + 1

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
            self.level_clicked.emit(n)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            x = event.position().x() if hasattr(event, "position") else float(event.pos().x())
            n = self._level_at_x(x)
            if n != self._level or self._unset:
                self.set_level(n)
                self.level_clicked.emit(n)
        super().mouseMoveEvent(event)


# ── V3MoodSlider ─────────────────────────────────────────────────────────────


class V3MoodSlider(QWidget):
    """Slider de mood 1-10 v3 (Suite > Mood Tracker > Slashbar 1-10).

    Composición:
      • Header: título + subtítulo + cluster derecho (eyebrow "HOY", nombre del
        nivel grande en color, "n/10" mono, emoji 104px con glow).
      • Slashbar gradient arcoíris emocional con 10 dots clickeables.
      • Fila de números 1-10 (mono); el activo coloreado del nivel.
      • Range descriptors (3 columnas: izq/centro/der).
      • Panel inferior con 10 mini emojis preview; el activo escala 1.18 + glow.

    Signal:
        level_changed(int)  emitido cada vez que cambia el nivel.
    """

    level_changed = pyqtSignal(int)

    def __init__(
        self,
        level: int = 5,
        title: str = "¿Cómo te sientes hoy?",
        subtitle: str = "Deslizá para encontrar el número que mejor describe tu estado.",
        modo: str = None,
        parent=None,
        compact: bool = False,
        unset: bool = False,
    ):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._modo = norm_modo(modo or _tm().modo)
        self._compact = compact
        self._unset = bool(unset)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(V3_SP["xs"] if compact else V3_SP["lg"])

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(V3_SP["lg"])

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setFont(qfont("size_small"))
        self._subtitle_lbl.setWordWrap(True)
        title_col.addWidget(self._title_lbl)
        title_col.addWidget(self._subtitle_lbl)
        title_col.addStretch()
        header.addLayout(title_col, stretch=1)

        right = QHBoxLayout()
        right.setSpacing(V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._eyebrow_lbl = QLabel("Hoy")
        self._eyebrow_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl = QLabel("—" if self._unset else get_mood(self._level)["name"])
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl.setFont(qfont("size_display", weight=TYPOGRAPHY["weight_semibold"]))
        self._numeric_lbl = QLabel("—/10" if self._unset else f"{self._level}/10")
        self._numeric_lbl.setFont(qfont_mono(12, bold=False))
        self._numeric_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._numeric_lbl)
        text_col.addStretch()
        right.addLayout(text_col)

        self._emoji_big = NMMoodEmoji(level=self._level, size=104, glow=True, modo=self._modo)
        right.addWidget(self._emoji_big, alignment=Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(right)
        root.addLayout(header)

        # ── Slashbar ──────────────────────────────────────────────────────────
        self._track = _MoodTrackBar(level=self._level, unset=self._unset)
        self._track.level_clicked.connect(self._on_level_clicked)
        root.addWidget(self._track)

        # ── Fila de números 0-10 (el 0 es la muesca de estacionamiento; no
        # registra valor — feedback owner v1.0). _MoodNumRow los posiciona
        # con la MISMA fórmula del track: cada número queda centrado bajo su
        # dot real (antes el layout de stretches los corría ~10px).
        self._num_labels: list[_MoodPickLabel] = []
        self._zero_lbl = QLabel("0")
        self._zero_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zero_lbl.setFont(qfont_mono(10))
        for n in range(1, 11):
            lbl = _MoodPickLabel(str(n), n)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.picked.connect(self._on_level_clicked)
            self._num_labels.append(lbl)
        num_row = _MoodNumRow([self._zero_lbl, *self._num_labels])
        root.addWidget(num_row)

        # ── Range descriptors ─────────────────────────────────────────────────
        desc_row = QHBoxLayout()
        desc_row.setContentsMargins(0, V3_SP["sm"], 0, 0)
        d_left = QLabel("Necesito apoyo")
        d_mid = QLabel("En el medio")
        d_mid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_right = QLabel("Me siento pleno")
        d_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        for d in (d_left, d_mid, d_right):
            d.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        desc_row.addWidget(d_left, 1)
        desc_row.addWidget(d_mid, 1)
        desc_row.addWidget(d_right, 1)
        self._desc_labels = (d_left, d_mid, d_right)
        root.addLayout(desc_row)

        # ── Panel inferior con 10 mini emojis ─────────────────────────────────
        self._preview_panel = QFrame()
        self._preview_panel.setObjectName("MoodPreviewPanel")
        prow = QHBoxLayout(self._preview_panel)
        prow.setContentsMargins(14, 16, 14, 16)
        prow.setSpacing(0)
        self._preview_cells: list[tuple[_MoodPickWidget, NMMoodEmoji, QLabel, int]] = []
        for n in range(1, 11):
            cell = _MoodPickWidget(n)
            cell.setFixedWidth(40)
            col = QVBoxLayout(cell)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(2)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            is_active = n == self._level and not self._unset
            emoji = NMMoodEmoji(
                level=n, size=(38 if is_active else 32), glow=is_active, modo=self._modo
            )
            num_lbl = QLabel(str(n))
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setFont(qfont_mono(9, bold=is_active))
            col.addWidget(emoji, alignment=Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(num_lbl)
            cell.picked.connect(self._on_level_clicked)
            self._preview_cells.append((cell, emoji, num_lbl, n))
            prow.addWidget(cell)
            if n < 10:
                prow.addStretch()
        root.addWidget(self._preview_panel)

        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

        if compact:
            self._subtitle_lbl.hide()
            self._emoji_big.hide()
            d_left.hide()
            d_mid.hide()
            d_right.hide()
            self._preview_panel.hide()
            self._title_lbl.hide()
            self._eyebrow_lbl.hide()
            self._name_lbl.hide()
            self._numeric_lbl.hide()

    # ── API pública ──────────────────────────────────────────────────────────

    def level(self) -> int:
        return self._level

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv == self._level and not self._unset:
            return
        self._level = lv
        self._unset = False
        self._track.set_level(lv)
        self._emoji_big.set_level(lv)
        self._name_lbl.setText(get_mood(lv)["name"])
        self._numeric_lbl.setText(f"{lv}/10")
        for cell, emoji, lbl, n in self._preview_cells:
            active = n == lv
            emoji.set_size(38 if active else 32)
            emoji.set_glow(active)
        self._refresh_styles()
        self.level_changed.emit(lv)

    def set_subtitle(self, text: str) -> None:
        """Actualiza el subtítulo (mensaje de cuidado dinámico por nivel)."""
        if hasattr(self, "_subtitle_lbl"):
            self._subtitle_lbl.setText(text)

    # ── internals ────────────────────────────────────────────────────────────

    def _on_level_clicked(self, n: int):
        self.set_level(int(n))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._refresh_styles()

    def _refresh_styles(self):
        is_dark = "dark" in self._modo
        c_text = v3c("text", self._modo).name()
        c_text2 = v3c("text2", self._modo).name()
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        c_text4 = v3c("text4", self._modo).name()
        elev_key = "elevatedSolid" if is_dark else "elevated"
        c_elev = v3c(elev_key, self._modo).name()
        c_border = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        lv_color = get_mood(self._level)["to"]

        self._title_lbl.setStyleSheet(f"color: {c_text}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        self._eyebrow_lbl.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        self._name_lbl.setStyleSheet(f"color: {lv_color}; background: transparent;")
        self._numeric_lbl.setStyleSheet(f"color: {c_text2}; background: transparent;")
        for d in self._desc_labels:
            d.setStyleSheet(f"color: {c_ink_secondary}; background: transparent;")
        if hasattr(self, "_zero_lbl"):
            self._zero_lbl.setStyleSheet(f"color: {c_text4}; background: transparent;")
        for lbl in self._num_labels:
            active = lbl._value == self._level and not self._unset
            col = get_mood(lbl._value)["to"] if active else c_ink_secondary
            lbl.setFont(qfont_mono(11, bold=active))
            lbl.setStyleSheet(f"color: {col}; background: transparent;")
        for cell, emoji, num_lbl, n in self._preview_cells:
            active = n == self._level and not self._unset
            col = get_mood(n)["to"] if active else c_text4
            num_lbl.setFont(qfont_mono(9, bold=active))
            num_lbl.setStyleSheet(f"color: {col}; background: transparent;")
        self._preview_panel.setStyleSheet(
            f"#MoodPreviewPanel {{ background: {c_elev}; "
            f"border: 1px solid {c_border}; border-radius: {V3_RD['lg']}px; }}"
        )


# ── NMPlayButton ─────────────────────────────────────────────────────────────


class NMPlayButton(QPushButton):
    """Botón circular minimal para controles de player (play/pause/stop/skip/refresh).

    Spec README v3:
      - Tamaños sm/md/lg → diámetro 40/48/56.
      - Background ``surface`` (neutro), border ``borderSoft`` sutil,
        sombra suave ``v3_shadow("sm")``.
      - **Sin gradient**, **sin texto**. Solo icono SVG centrado.
      - Hover: fondo ``elevated`` + border ``borderStrong``.

    Args:
        icon_name: nombre del icono SVG v3 ("play"/"pause"/"stop"/"skip"/"refresh").
        size:      "sm" / "md" / "lg".
        modo:      override de tema.
    """

    _SIZE_MAP = {"sm": 40, "md": 48, "lg": 56}

    def __init__(self, icon_name: str = "play", size: str = "md", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._icon_name = icon_name
        self._size_key = size if size in self._SIZE_MAP else "md"
        self._hover = False
        diameter = self._SIZE_MAP[self._size_key]
        self.setFixedSize(diameter, diameter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._disabled = False
        self._card_shadow = None
        self._apply_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API ──────────────────────────────────────────────────────────────────

    def set_icon(self, name: str):
        if name != self._icon_name:
            self._icon_name = name
            self.update()

    def icon_name(self) -> str:
        return self._icon_name

    def set_size(self, size: str):
        if size in self._SIZE_MAP and size != self._size_key:
            self._size_key = size
            d = self._SIZE_MAP[size]
            self.setFixedSize(d, d)
            self.update()

    # ── eventos ──────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ── paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = "dark" in self._modo
        d = self.width()
        rect = QRectF(1, 1, d - 2, d - 2)

        # Background surface (elevated en hover)
        surf_key = (
            "elevatedSolid"
            if (self._hover and is_dark)
            else "elevated"
            if self._hover
            else "surfaceSolid"
            if is_dark
            else "surface"
        )
        bg = v3c(surf_key, self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(rect)

        # Border sutil
        border_key = "borderStrong" if self._hover else "borderSoft"
        p.setPen(QPen(v3c(border_key, self._modo), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.5, 0.5, d - 1, d - 1))

        # Icono SVG centrado
        if _nm_svg_pixmap is not None and _has_v3_icon(self._icon_name):
            icon_size = max(14, int(d * 0.45))
            color = v3c("text", self._modo).name()
            pix = _nm_svg_pixmap(self._icon_name, color, icon_size)
            if pix is not None and not pix.isNull():
                px = (d - icon_size) // 2
                p.drawPixmap(px, px, pix)
        p.end()

    # ── theme ────────────────────────────────────────────────────────────────

    def _apply_shadow(self):
        eff = v3_shadow("sm", self._modo, parent=self)
        self.setGraphicsEffect(eff)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        if not self._disabled and self.isEnabled():
            if self._card_shadow is None:
                self._card_shadow = QGraphicsDropShadowEffect(self)
            is_dark = "dark" in self._modo
            self._card_shadow.setBlurRadius(30 if is_dark else 12)
            self._card_shadow.setOffset(0, 10 if is_dark else 4)
            sc = v3c("teal", self._modo) if is_dark else QColor(15, 23, 42, 13)
            if is_dark:
                sc.setAlpha(115)
            self._card_shadow.setColor(sc)
            self.setGraphicsEffect(self._card_shadow)
        self.update()


# ══════════════════════════════════════════════════════════════════════════════
# Componentes v3 — Redesign 2026 (Sage Linen / Indigo Mist)
# ══════════════════════════════════════════════════════════════════════════════
# Estos wrappers cubren huecos del design system identificados en la auditoría:
# NMDivider, NMSectionHeader, NMAvatar, NMStatCard, NMSearchInput, NMTextArea,
# NMTabs, NMTooltip, NMErrorState, NMDialog/NMModal.
#
# Todos siguen el patrón canónico: aceptan `modo`, registran un slot al
# ThemeManager via _tm().theme_changed, y exponen `_apply_theme(modo)`.
# ══════════════════════════════════════════════════════════════════════════════


# ── NMDivider ────────────────────────────────────────────────────────────────


class NMDivider(QWidget):
    """Separador token-driven. orient='h' o 'v', opacity 0-255.

    Uso:
        layout.addWidget(NMDivider())                  # horizontal sutil
        row.addWidget(NMDivider(orient="v", alpha=80)) # vertical
    """

    def __init__(
        self, orient: str = "h", alpha: int = 60, inset: int = 0, modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._orient = "v" if orient == "v" else "h"
        self._alpha = max(0, min(255, int(alpha)))
        self._inset = max(0, int(inset))
        if self._orient == "h":
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(1)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        _tm().theme_changed.connect(self._apply_theme)

    def paintEvent(self, event):
        p = QPainter(self)
        col = v3c("border", self._modo)
        col.setAlpha(self._alpha)
        p.setPen(QPen(col, 1.0))
        if self._orient == "h":
            y = self.height() // 2
            p.drawLine(self._inset, y, self.width() - self._inset, y)
        else:
            x = self.width() // 2
            p.drawLine(x, self._inset, x, self.height() - self._inset)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMSectionHeader ──────────────────────────────────────────────────────────


class NMSectionHeader(QWidget):
    """Encabezado de sección: eyebrow (caption all-caps suave) + título +
    opcional botón de acción a la derecha.

    Uso:
        h = NMSectionHeader("Última semana", "Tu progreso emocional")
        h.action_clicked.connect(self._on_view_all)
        h.set_action("Ver todo")
    """

    action_clicked = pyqtSignal()

    def __init__(self, eyebrow: str = "", title: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMSectionHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(V3_SP["xs"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._eyebrow = QLabel(eyebrow or "")
        self._eyebrow.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        top.addWidget(self._eyebrow)
        top.addStretch()
        self._action_btn: QPushButton | None = None
        lay.addLayout(top)

        title_row = QHBoxLayout()
        title_row.setSpacing(V3_SP["md"])
        self._title = QLabel(title or "")
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title.setWordWrap(True)
        title_row.addWidget(self._title, stretch=1)
        lay.addLayout(title_row)
        self._title_row = title_row

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_eyebrow(self, text: str):
        self._eyebrow.setText(text or "")
        self._eyebrow.setVisible(bool(text))

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_action(self, label: str | None):
        """Muestra/oculta el botón de acción a la derecha del título."""
        if not label:
            if self._action_btn is not None:
                self._action_btn.setParent(None)
                self._action_btn.deleteLater()
                self._action_btn = None
            return
        if self._action_btn is None:
            self._action_btn = QPushButton(label)
            self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._action_btn.setFlat(True)
            self._action_btn.clicked.connect(self.action_clicked.emit)
            self._title_row.addWidget(self._action_btn)
        else:
            self._action_btn.setText(label)
        self._style_action()

    def _style_action(self):
        if self._action_btn is None:
            return
        c = v3c("accent", self._modo).name()
        self._action_btn.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._action_btn.setStyleSheet(
            f"QPushButton {{ color: {c}; background: transparent; border: none; "
            f"padding: 4px 8px; }}"
            f"QPushButton:hover {{ color: {v3c('cyan', self._modo).name()}; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        eyebrow_col = v3c("text2", self._modo).name()
        title_col = v3c("text", self._modo).name()
        self._eyebrow.setStyleSheet(
            f"color: {eyebrow_col}; background: transparent;"
        )
        self._title.setStyleSheet(f"color: {title_col}; background: transparent;")
        self._style_action()


# ── NMAvatar ─────────────────────────────────────────────────────────────────


class NMAvatar(QWidget):
    """Avatar circular con iniciales (fallback) o QPixmap.

    Uso:
        av = NMAvatar(initials="AM", size=44)
        av.set_pixmap(QPixmap("foto.png"))
    """

    def __init__(
        self,
        initials: str = "",
        pixmap: QPixmap | None = None,
        size: int = 40,
        color_seed: str | None = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._initials = (initials or "?").strip().upper()[:2]
        self._pix = pixmap
        self._seed = color_seed or self._initials
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_initials(self, text: str):
        self._initials = (text or "?").strip().upper()[:2]
        self._seed = text or self._initials
        self.update()

    def set_pixmap(self, pix: QPixmap | None):
        self._pix = pix
        self.update()

    def _seed_color_pair(self) -> tuple[QColor, QColor]:
        # Color determinístico desde el seed — gradiente entre accent y warm
        h = sum(ord(c) for c in self._seed) % 360
        # Mezclamos los dos acentos del tema según hash
        a = v3c("accent", self._modo)
        b = v3c("warm", self._modo)
        t = (h % 100) / 100.0
        # interp simple
        r = int(a.red() * (1 - t) + b.red() * t)
        g = int(a.green() * (1 - t) + b.green() * t)
        bl = int(a.blue() * (1 - t) + b.blue() * t)
        c1 = QColor(r, g, bl)
        c2 = QColor(min(255, r + 30), min(255, g + 30), min(255, bl + 30))
        return c1, c2

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        d = self.width()
        rect = QRectF(0, 0, d, d)
        if self._pix and not self._pix.isNull():
            # Clip circular y pintar pixmap
            path = QPainterPath()
            path.addEllipse(rect)
            p.setClipPath(path)
            scaled = self._pix.scaled(
                d,
                d,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.drawPixmap(0, 0, scaled)
        else:
            c1, c2 = self._seed_color_pair()
            grad = QLinearGradient(0, 0, d, d)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(1.0, c2)
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(rect)
            # Iniciales centradas en blanco
            p.setPen(QColor("#ffffff"))
            font_pt = max(10, int(d * 0.40))
            p.setFont(qfont(font_pt, weight=TYPOGRAPHY["weight_semibold"]))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._initials)
        # Borde sutil
        p.setClipping(False)
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(0.5, 0.5, d - 1, d - 1))
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMStatCard ───────────────────────────────────────────────────────────────


class NMStatCard(QWidget):
    """Card de métrica: label arriba (eyebrow), valor grande, delta opcional.

    Uso:
        c = NMStatCard("PROMEDIO 7 DÍAS", "7.3/10")
        c.set_delta("+0.4", positive=True)
    """

    def __init__(self, label: str = "", value: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(84)
        self.setMinimumWidth(168)  # minmax(168px, 1fr) per F3.3

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["xs"], V3_SP["md"], V3_SP["xs"])
        lay.setSpacing(0)

        self._label = QLabel(label or "")
        self._label.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        lay.addWidget(self._label)

        value_row = QHBoxLayout()
        value_row.setSpacing(V3_SP["xs"])
        self._value = QLabel(value or "—")
        try:
            from shared.theme_qt import v3_font as _v3_font

            self._value.setFont(
                _v3_font("size_h2", weight=TYPOGRAPHY["weight_semibold"], serif=True)
            )
        except ImportError:
            self._value.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        value_row.addWidget(self._value)
        self._delta = QLabel("")
        self._delta.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))

        self._delta.setContentsMargins(6, 2, 6, 2)
        self._delta.setVisible(False)
        value_row.addWidget(self._delta)
        value_row.addStretch()
        lay.addLayout(value_row)
        lay.addStretch()

        _tm().theme_changed.connect(self._apply_theme)
        self._tone_key = None
        self._stat_shadow: QGraphicsDropShadowEffect | None = None
        self._apply_theme(self._modo)
        self._apply_stat_shadow()

    def _apply_stat_shadow(self):
        if self._stat_shadow is None:
            self._stat_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if is_dark:
            self._stat_shadow.setBlurRadius(18)
            self._stat_shadow.setOffset(0, 5)
            self._stat_shadow.setColor(QColor(0, 0, 0, 80))
        else:
            self._stat_shadow.setBlurRadius(10)
            self._stat_shadow.setOffset(0, 3)
            self._stat_shadow.setColor(QColor(28, 34, 24, 14))
        self.setGraphicsEffect(self._stat_shadow)

    def set_value(self, value: str):
        self._value.setText(value or "—")

    def set_label(self, label: str):
        self._label.setText(label or "")

    def set_tone(self, tone_key: str | None):
        """Define un color semántico (primary, accent, danger, etc) para el valor."""
        self._tone_key = tone_key
        self._apply_value_style()

    def set_delta(self, text: str, positive: bool | None = None):
        if not text:
            self._delta.setVisible(False)
            return
        self._delta.setText(text)
        self._delta.setVisible(True)
        self._delta_positive = positive
        self._style_delta()

    def _apply_value_style(self):
        if self._tone_key:
            col = v3c(self._tone_key, self._modo)
        else:
            col = v3c("text", self._modo)
        self._value.setStyleSheet(f"color: {col.name()}; background: transparent;")

    def _style_delta(self):
        pos = getattr(self, "_delta_positive", None)
        if pos is True:
            col = v3c("success", self._modo)
        elif pos is False:
            col = v3c("danger", self._modo)
        else:
            col = v3c("text2", self._modo)
        bg_alpha = 36
        bg = f"rgba({col.red()},{col.green()},{col.blue()},{bg_alpha})"
        self._delta.setStyleSheet(
            f"color: {col.name()}; background: {bg}; border-radius: 6px; padding: 2px 6px;"
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(V3_RD["card"])  # premium Hub radius 18px
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        is_dark = "dark" in self._modo
        surf = v3c("surfaceSolid" if is_dark else "surface", self._modo)
        p.setBrush(QBrush(surf))
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.drawRoundedRect(rect, r, r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; "
            f"background: transparent;"
        )
        self._value.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._style_delta()
        self._apply_value_style()
        if hasattr(self, "_stat_shadow") and self._stat_shadow is not None:
            self._apply_stat_shadow()
        self.update()


# ── NMSearchInput ────────────────────────────────────────────────────────────


class NMSearchInput(QWidget):
    """Input de búsqueda con icono de lupa y botón clear (aparece con texto).

    Uso:
        s = NMSearchInput(placeholder="Buscar paciente…")
        s.text_changed.connect(self._on_search)
        s.text() / s.set_text("foo")
    """

    text_changed = pyqtSignal(str)
    returned = pyqtSignal(str)

    def __init__(self, placeholder: str = "Buscar…", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(_NM_CONTROL_HEIGHT)
        self.setMaximumHeight(_NM_CONTROL_HEIGHT)
        self.setAccessibleName("Buscar")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["sm"], 0, V3_SP["xs"], 0)
        lay.setSpacing(V3_SP["xs"])

        self._icon = QLabel()
        self._icon.setFixedSize(20, 20)
        lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setFrame(False)
        self._edit.setFont(qfont(_NM_CONTROL_FONT))
        # Texto centrado verticalmente: sin margen de texto propio el QLineEdit
        # frameless dejaba el placeholder/valor pegado abajo del campo. Margen 0
        # + alineación VCenter en el layout lo centran de forma estable con
        # cualquier fuente (Manrope cargada vs fallback).
        self._edit.setTextMargins(0, 0, 0, 0)
        self._edit.textChanged.connect(self._on_text_changed)
        self._edit.returnPressed.connect(lambda: self.returned.emit(self._edit.text()))
        lay.addWidget(self._edit, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._clear_btn = QPushButton("")
        self._clear_btn.setFixedSize(22, 22)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setFlat(True)
        self._clear_btn.clicked.connect(lambda: self._edit.setText(""))
        self._clear_btn.setVisible(False)
        lay.addWidget(self._clear_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def text(self) -> str:
        return self._edit.text()

    def set_text(self, value: str):
        self._edit.setText(value or "")

    def set_placeholder(self, value: str):
        self._edit.setPlaceholderText(value or "")

    def _on_text_changed(self, text: str):
        self._clear_btn.setVisible(bool(text))
        self.text_changed.emit(text)

    def _render_icons(self):
        try:
            from shared.icons_svg import nm_svg_pixmap, has_icon
        except ImportError:
            return
        text_col = v3c("ink_secondary", self._modo).name()
        if has_icon("search"):
            pix = nm_svg_pixmap("search", text_col, 18)
            if pix is not None and not pix.isNull():
                self._icon.setPixmap(pix)
        if has_icon("close"):
            pix = nm_svg_pixmap("close", text_col, 14)
            if pix is not None and not pix.isNull():
                self._clear_btn.setIcon(QIcon(pix))
                self._clear_btn.setIconSize(QSize(14, 14))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(_NM_CONTROL_RADIUS)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = v3c("surface_2", self._modo)
        focused = self._edit.hasFocus()
        border = v3c("accent" if focused else "border", self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(border, 1.5 if focused else 1.0))
        p.drawRoundedRect(rect, r, r)
        p.end()

    def focusInEvent(self, event):
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.update()
        super().focusOutEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c_text = v3c("text", self._modo).name()
        c_placeholder = v3c("faint", self._modo).name()
        self._edit.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; "
            f"color: {c_text}; padding: 6px 4px; "
            f"font-size: {TYPOGRAPHY['size_body']}px; }}"
            f"QLineEdit::placeholder {{ color: {c_placeholder}; }}"
        )
        self._clear_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._render_icons()
        # Forzar repintado de border via focus event listener
        self._edit.installEventFilter(self) if not hasattr(self, "_filt") else None
        self._filt = True
        self.update()

    def eventFilter(self, obj, ev):
        if obj is self._edit and ev.type() in (ev.Type.FocusIn, ev.Type.FocusOut):
            self.update()
        return super().eventFilter(obj, ev)


# ── NMTextArea ───────────────────────────────────────────────────────────────


class NMTextArea(QTextEdit):
    """QTextEdit con tema, border focus, placeholder y altura mínima."""

    def __init__(
        self,
        placeholder: str = "",
        modo: str = None,
        min_height: int = 96,
        max_length: int | None = None,
        font_key: str = _NM_CONTROL_FONT,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._max_length = max_length
        # font_key configurable: el contenido generado por IA usa "size_small"
        # (más compacto, pedido owner) sin afectar el resto de los text areas.
        self._font_key = font_key if font_key in TYPOGRAPHY else _NM_CONTROL_FONT
        self.setPlaceholderText(placeholder or "")
        self.setAccessibleName(placeholder or "Text area")
        self.setMinimumHeight(min_height)
        self.setFont(qfont(self._font_key))
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        if max_length is not None:
            # QTextEdit no tiene setMaxLength: tope físico vía textChanged
            # (auditoría v1.0 — pegar texto masivo rompía el responsive de la
            # Suite al sincronizar).
            self.textChanged.connect(self._enforce_max_length)
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def _enforce_max_length(self):
        if self._max_length is None:
            return
        text = self.toPlainText()
        if len(text) <= self._max_length:
            return
        cursor = self.textCursor()
        pos = min(cursor.position(), self._max_length)
        self.blockSignals(True)
        self.setPlainText(text[: self._max_length])
        cursor = self.textCursor()
        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        self.blockSignals(False)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        bg = v3c("surface_2", self._modo).name()
        text_col = v3c("text", self._modo).name()
        placeholder = v3c("faint", self._modo).name()
        border = C("border", self._modo)
        focus_col = v3c("accent", self._modo).name()
        sel_text = v3c("primary_ink", self._modo).name()
        # Foco fino y suave (1px, accent con alpha) — el 1.5px a plena
        # intensidad se leía duro/grueso (informe owner v1.0: alinear al
        # borde verde suave de Recordatorios).
        _focus_soft = QColor(v3c("accent", self._modo))
        _focus_soft.setAlpha(150)
        # Scrollbar canónica (clínica, neutra): un QTextEdit con stylesheet
        # propio pierde el QScrollBar global y caía al nativo de Qt (las "muchas
        # scrollbars que violan el ADN" en el tab IA). La apendamos al QSS.
        from shared.theme_qt import _clinical_scrollbar_qss

        self.setStyleSheet(
            f"QTextEdit {{ background-color: {bg}; color: {text_col}; "
            f"border: 1px solid {border}; border-radius: {_NM_CONTROL_RADIUS}px; "
            f"padding: 8px 12px; font-size: {TYPOGRAPHY[self._font_key]}px; "
            f"selection-background-color: {focus_col}; selection-color: {sel_text}; }}"
            f"QTextEdit:focus {{ border: 1px solid {qcolor_to_rgba_css(_focus_soft)}; }}"
            + _clinical_scrollbar_qss(self._modo)
        )
        # Solo el placeholder en color faint (vía palette). Antes se pintaba el
        # viewport con ese color, lo que también atenuaba el TEXTO escrito y lo
        # dejaba casi ilegible en light. El texto real usa text_col del QSS.
        _pal = self.palette()
        _pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(placeholder))
        self.setPalette(_pal)


# ── NMTabs ───────────────────────────────────────────────────────────────────


class NMTabs(QWidget):
    """Tabs custom (pill o underline). API minimal independiente de QTabWidget.

    Uso:
        t = NMTabs(["Todos", "Activos", "Sin registros"])
        t.changed.connect(self._on_tab)
        t.set_current(0)
    """

    changed = pyqtSignal(int, str)  # index, label

    def __init__(
        self,
        labels: list[str] | None = None,
        variant: str = "pill",  # "pill" | "underline"
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = "pill"
        self._labels = list(labels or [])
        self._current = 0
        self._btns: list[QPushButton] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(V3_SP["xs"])
        self._build_buttons()
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def _build_buttons(self):
        # Limpiar
        for b in self._btns:
            b.setParent(None)
            b.deleteLater()
        self._btns.clear()
        # Crear
        for i, label in enumerate(self._labels):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, idx=i: self.set_current(idx))
            self._lay.addWidget(btn)
            self._btns.append(btn)
        self._lay.addStretch()

    def set_labels(self, labels: list[str]):
        self._labels = list(labels or [])
        self._current = 0
        self._build_buttons()
        self._apply_theme(self._modo)

    def set_current(self, idx: int):
        if not (0 <= idx < len(self._labels)):
            return
        self._current = idx
        for i, b in enumerate(self._btns):
            b.setChecked(i == idx)
        self._style_buttons()
        self.changed.emit(idx, self._labels[idx])

    def current(self) -> int:
        return self._current

    def _style_buttons(self):
        primary = v3c("primary", self._modo).name()
        primary_ink = v3c("primary_ink", self._modo).name()
        text = v3c("text", self._modo).name()
        text_muted = v3c("text2", self._modo).name()
        surface_2 = v3c("surface_2", self._modo).name()
        border = v3c("border", self._modo)
        soft_css = (
            f"rgba({border.red()},{border.green()},"
            f"{border.blue()},{max(border.alpha(), 24)})"
        )
        for i, b in enumerate(self._btns):
            b.setMinimumHeight(_NM_TAB_HEIGHT)
            b.setFont(qfont(_NM_TAB_FONT, weight=_NM_CONTROL_WEIGHT))
            checked = i == self._current
            if checked:
                b.setStyleSheet(
                    f"QPushButton {{ background: {primary}; color: {primary_ink}; "
                    f"border: none; padding: 4px 14px; "
                    f"border-radius: {_NM_TAB_RADIUS - 3}px; }}"
                )
            else:
                b.setStyleSheet(
                    f"QPushButton {{ background: {surface_2}; color: {text_muted}; "
                    f"border: 1px solid {soft_css}; padding: 4px 14px; "
                    f"border-radius: {_NM_TAB_RADIUS - 3}px; }}"
                    f"QPushButton:hover {{ color: {text}; }}"
                )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._style_buttons()


# ── NMTooltip ────────────────────────────────────────────────────────────────


class NMTooltip(QWidget):
    """Tooltip flotante con tema NM (alternativa al QToolTip nativo para casos
    que necesitan mayor control visual o autohide programable).

    Uso:
        tip = NMTooltip.show_for(parent_widget, "Texto del tooltip", duration_ms=2000)
    """

    @classmethod
    def show_for(
        cls, anchor: QWidget, text: str, duration_ms: int = 2500, modo: str = None
    ) -> "NMTooltip":
        tip = cls(text, modo=modo or _tm().modo, parent=anchor.window())
        # Posicionar arriba del anchor centrado
        pt = anchor.mapToGlobal(QPoint(anchor.width() // 2, 0))
        pt = tip.parent().mapFromGlobal(pt) if tip.parent() else pt
        tip.adjustSize()
        x = pt.x() - tip.width() // 2
        y = pt.y() - tip.height() - 8
        tip.move(max(8, x), max(8, y))
        tip.show()
        QTimer.singleShot(duration_ms, tip.fade_out)
        return tip

    def __init__(self, text: str = "", modo: str = None, parent=None):
        # Child overlay con parent real, sin window flags: un tooltip con
        # Qt.ToolTip era una ventana top-level que el lector de pantalla
        # resaltaba como mini ventana (informe owner v1.0, frente 2).
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        self._label = QLabel(text or "")
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(280)
        lay.addWidget(self._label)
        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_text(self, text: str):
        self._label.setText(text or "")
        self.adjustSize()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setOpacity(self._opacity)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        is_dark = "dark" in self._modo
        bg = v3c("elevatedSolid" if is_dark else "elevated", self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(QPen(v3c("border", self._modo), 1.0))
        p.drawRoundedRect(rect, V3_RD["sm"], V3_RD["sm"])
        p.end()

    def _set_opacity(self, value):
        self._opacity = float(value)
        # El QLabel hijo pinta aparte: su color acompaña el fade vía alpha.
        c = v3c("text", self._modo)
        self._label.setStyleSheet(
            f"color: rgba({c.red()},{c.green()},{c.blue()},{int(255 * self._opacity)}); "
            "background: transparent;"
        )
        self.update()

    def fade_out(self, duration_ms: int = 200):
        # painter opacity, no QGraphicsOpacityEffect (efectos anidados).
        anim = QVariantAnimation(self)
        anim.setDuration(duration_ms)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.valueChanged.connect(self._set_opacity)
        anim.finished.connect(self.deleteLater)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._label.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self.update()


# ── NMErrorState ─────────────────────────────────────────────────────────────


class NMErrorState(QWidget):
    """Estado de error: icono + título + mensaje + opcional botón retry.

    Uso:
        err = NMErrorState("No se pudo cargar", "Verificá tu conexión.")
        err.retry_requested.connect(self._reload)
        err.set_retry("Reintentar")
    """

    retry_requested = pyqtSignal()

    def __init__(
        self, title: str = "Ocurrió un error", message: str = "", modo: str = None, parent=None
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["xl"])
        lay.setSpacing(V3_SP["sm"])
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Chip contenedor del icono (64×64, DANGER_SOFT bg, r18)
        self._icon_chip = QFrame()
        self._icon_chip.setFixedSize(64, 64)
        self._icon_chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chip_lay = QHBoxLayout(self._icon_chip)
        chip_lay.setContentsMargins(8, 8, 8, 8)
        self._icon_lbl = QLabel("")
        self._icon_lbl.setFixedSize(48, 48)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        chip_lay.addWidget(self._icon_lbl)
        lay.addWidget(self._icon_chip, alignment=Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel(title or "")
        self._title.setFont(v3_font("size_display_m", "weight_medium"))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)
        lay.addWidget(self._title)

        self._msg = QLabel(message or "")
        self._msg.setFont(qfont("size_small"))
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg.setWordWrap(True)
        self._msg.setMaximumWidth(420)
        lay.addWidget(self._msg, alignment=Qt.AlignmentFlag.AlignCenter)

        self._retry_btn = QPushButton("")
        self._retry_btn.setVisible(False)
        self._retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._retry_btn.clicked.connect(self.retry_requested.emit)
        lay.addWidget(self._retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_message(self, text: str):
        self._msg.setText(text or "")

    def set_retry(self, label: str | None):
        if not label:
            self._retry_btn.setVisible(False)
            return
        self._retry_btn.setText(label)
        self._retry_btn.setVisible(True)
        self._style_retry()

    def _render_icon(self):
        try:
            from shared.icons_svg import nm_svg_pixmap, has_icon
        except ImportError:
            return
        col = v3c("danger", self._modo).name()
        name = "warning" if has_icon("warning") else "info"
        pix = nm_svg_pixmap(name, col, 40)
        if pix is not None and not pix.isNull():
            self._icon_lbl.setPixmap(pix)

    def _style_retry(self):
        accent = v3c("accent", self._modo).name()
        self._retry_btn.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._retry_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {accent}; "
            f"border: 1px solid {accent}; border-radius: 10px; "
            f"padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {qcolor_to_rgba_css(v3c('accentSoft', self._modo))}; }}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._msg.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        # Chip DANGER_SOFT
        danger_c = v3c("danger", self._modo)
        danger_c.setAlphaF(0.10)
        bg_css = f"rgba({danger_c.red()},{danger_c.green()},{danger_c.blue()},25)"
        if hasattr(self, "_icon_chip"):
            self._icon_chip.setStyleSheet(
                f"QFrame {{ background-color: {bg_css}; border-radius: 12px; }}"
            )
        self._render_icon()
        self._style_retry()


# ── NMDialog / NMModal ───────────────────────────────────────────────────────


class NMDialog(QWidget):
    """Modal/Dialog overlay con header, body y footer estandarizados.

    Implementado como overlay sobre la ventana padre (no QDialog nativo) para
    mantener consistencia visual con el shell. Soporta close por click en
    backdrop o tecla Escape.

    Uso:
        dlg = NMDialog(title="Confirmar acción", parent=self)
        dlg.set_body_widget(QLabel("¿Estás seguro?"))
        dlg.add_footer_button("Cancelar", role="secondary",
                              callback=dlg.close)
        dlg.add_footer_button("Eliminar", role="danger",
                              callback=self._do_delete)
        dlg.show_centered()
    """

    closed = pyqtSignal()

    def __init__(self, title: str = "", modo: str = None, width: int = 480, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._dialog_width = width
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Overlay full-cover sobre el padre
        if parent is not None:
            self.setGeometry(parent.rect())

        # Container central
        self._panel = QFrame(self)
        self._panel.setFixedWidth(width)
        self._panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["lg"])
        panel_lay.setSpacing(V3_SP["md"])

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(V3_SP["sm"])
        self._title = QLabel(title or "")
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title.setWordWrap(True)
        header_row.addWidget(self._title, stretch=1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFlat(True)
        self._close_btn.clicked.connect(self.close)
        header_row.addWidget(self._close_btn)
        panel_lay.addLayout(header_row)

        # Body container
        self._body_holder = QVBoxLayout()
        self._body_holder.setSpacing(V3_SP["md"])
        panel_lay.addLayout(self._body_holder, stretch=1)

        # Footer
        self._footer_row = QHBoxLayout()
        self._footer_row.setSpacing(V3_SP["sm"])
        self._footer_row.addStretch()
        panel_lay.addLayout(self._footer_row)
        self._footer_buttons: list[QPushButton] = []

        # Layout root para centrar el panel
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()
        center_row = QHBoxLayout()
        center_row.addStretch()
        center_row.addWidget(self._panel)
        center_row.addStretch()
        root.addLayout(center_row)
        root.addStretch()

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)
        self.hide()

    # ── API ──────────────────────────────────────────────────────────────────

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_body_widget(self, widget: QWidget):
        # Limpiar body actual
        while self._body_holder.count():
            item = self._body_holder.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._body_holder.addWidget(widget)

    def add_footer_button(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        """role: 'primary' | 'secondary' | 'danger' | 'ghost'."""
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(96)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_row.addWidget(btn)
        self._footer_buttons.append(btn)
        self._style_footer()
        return btn

    def show_centered(self):
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.setFocus(Qt.FocusReason.PopupFocusReason)

    # ── Eventos ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Click fuera del panel cierra
        if not self._panel.geometry().contains(event.pos()):
            self.close()
            return
        super().mousePressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Backdrop semitransparente, theme-aware: en light un scrim negro duro se
        # ve roto (feedback). En dark mantenemos negro; en light usamos la tinta
        # profunda del tema a baja alpha para atenuar sin ennegrecer.
        if "dark" in self._modo:
            scrim = QColor(0, 0, 0, 150)
        else:
            ink = v3c("text", self._modo)
            scrim = QColor(ink.red(), ink.green(), ink.blue(), 90)
        p.fillRect(self.rect(), scrim)
        # El panel se pinta como QFrame con su stylesheet
        p.end()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("border", self._modo)
        self._panel.setStyleSheet(
            f"QFrame {{ background-color: {bg}; "
            f"border: 1px solid {border}; border-radius: {V3_RD['xl']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c_ink_secondary}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; "
            f"color: {v3c('text', self._modo).name()}; }}"
        )
        self._style_footer()

    def _style_footer(self):
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_on_acc = v3c("primary_ink", self._modo).name()
        text = v3c("text", self._modo).name()
        text_muted = v3c("text2", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._footer_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if role == "primary":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; }}"
                )
            elif role == "danger":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('warm', self._modo).name()}; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_muted}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:  # secondary
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )


# Alias semántico
NMModal = NMDialog


def nm_confirm(
    parent: QWidget,
    titulo: str,
    mensaje: str,
    on_confirm,
    confirm_text: str = "Restablecer",
    modo: str = None,
) -> NMDialog:
    """Confirmación estándar sobre NMDialog (patrón único del producto).

    La usan todos los "Restablecer por defecto" de los configurables del Hub:
    overlay child de la ventana (sin ventana top-level), Cancelar ghost +
    acción danger. `on_confirm` corre solo si el profesional confirma.
    """
    win = parent.window() if parent is not None else None
    dlg = NMDialog(title=titulo, modo=modo, parent=win)
    body = QLabel(mensaje)
    body.setWordWrap(True)
    body.setFont(qfont("size_small"))
    body.setStyleSheet(
        f"color: {v3c('text2', norm_modo(modo or _tm().modo)).name()}; background: transparent;"
    )
    dlg.set_body_widget(body)
    dlg.add_footer_button("Cancelar", role="ghost", callback=dlg.close)

    def _go():
        dlg.close()
        on_confirm()

    dlg.add_footer_button(confirm_text, role="danger", callback=_go)
    dlg.show_centered()
    return dlg


# ════════════════════════════════════════════════════════════════════════════
# Handoff Full UI Pass — Mayo 2026
# Extensiones MÍNIMAS al catálogo para alinear con
# design_handoff_nm_suite_full_ui/. Sólo se incluyen los componentes que el
# plan declara imprescindibles para Fase 1 y que no existían como tales.
# El resto (NMRing, NMSparkline, NMMoodBars, NMModal, NMToast, NMTabs,
# NMAvatar, NMSwitch, NMProgress) ya está en el catálogo arriba y se reusan
# desde las pantallas — se repintan automáticamente al cambiar la paleta V3.
# ════════════════════════════════════════════════════════════════════════════


# ── NMBadge ──────────────────────────────────────────────────────────────────
# Handoff §4.4: pill 4×10, radius 999, font 12/600, tonos neutral/info/
# positive/warn/danger, icono opcional a la izquierda.
# Implementación: subclase de QLabel themed, mapeando tono → token semántico.

_BADGE_TONE_TO_KEY = {
    "neutral": "text2",  # ink-2: borde y texto
    "info": "accent",  # primary (sage/lavender)
    "positive": "success",
    "completed": "success",  # variante literal de la lámina de componentes
    "patient": "teal",  # identificación de paciente sin inventar semántica clínica
    "warn": "warning",
    "warning": "warning",  # alias
    "danger": "danger",
    "critical": "danger",
}


# ── NMChip ────────────────────────────────────────────────────────────────────


class NMChip(QFrame):
    """NMChip F1 Polish V2."""

    def __init__(
        self,
        text: str,
        variant: str = "default",
        size: str = "default",
        icon_name: str = None,
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = variant
        self._size = size
        self._icon_name = icon_name
        self.setObjectName("NMChip")

        lay = QHBoxLayout(self)
        h_margin = 8 if size == "sm" else 12
        v_margin = 2 if size == "sm" else 4
        lay.setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        lay.setSpacing(4)

        if icon_name:
            self._icon = QLabel()
            self._icon.setFixedSize(14, 14)
            lay.addWidget(self._icon)
        else:
            self._icon = None

        self._label = QLabel()
        font_sz = "size_caption_xs" if size == "sm" else "size_caption"
        font = v3_font(font_sz, weight=TYPOGRAPHY["weight_semibold"])
        self._label.setFont(font)

        fm = QFontMetrics(font)
        max_w = 150
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, max_w)
        self._label.setText(elided)
        if elided != text:
            self.setToolTip(text)

        lay.addWidget(self._label)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        if self._variant in ("default", "tint"):
            color_hex = C("ink_primary", self._modo)
            bg_key = "surface2"
        elif self._variant in ("solid", "info"):
            color_hex = C("primary", self._modo)
            bg_key = "surface"
        elif self._variant in ("success", "warning", "danger", "amber"):
            color_hex = C(self._variant if self._variant != "amber" else "warning", self._modo)
            bg_key = self._variant if self._variant != "amber" else "warning"
        else:
            color_hex = C("ink_primary", self._modo)
            bg_key = "surface2"

        if self._variant in ("success", "warning", "danger", "amber", "info", "tint"):
            bg_base = QColor(color_hex)
            bg_base.setAlpha(36)
            bg_css = f"rgba({bg_base.red()},{bg_base.green()},{bg_base.blue()},{bg_base.alpha()})"
            bd_css = f"rgba({bg_base.red()},{bg_base.green()},{bg_base.blue()},60)"
        else:
            bg_css = C(bg_key, self._modo)
            bd_css = C("border", self._modo)

        self._pill_r_applied = pill_radius(self, fallback=20 if self._size == "sm" else 24)
        self.setStyleSheet(f"""
            QFrame#NMChip {{
                background-color: {bg_css};
                border: 1px solid {bd_css};
                border-radius: {self._pill_r_applied}px;
            }}
            QLabel {{
                color: {color_hex};
                background: transparent;
                border: none;
            }}
        """)

        if self._icon and self._icon_name:
            self._icon.setPixmap(nm_icon(self._icon_name, color_hex, size=14).pixmap(14, 14))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


class NMElidedLabel(QLabel):
    """QLabel de una línea que elide con "…" en vez de empujar el layout.

    Para textos informativos en filas/heros con ancho disputado: no impone
    mínimo horizontal (Ignored) y pinta el texto elidido a su ancho real,
    con tooltip del texto completo cuando recorta. Evita el patrón "el label
    no entra → Qt fuerza geometrías bajo el mínimo → widgets superpuestos".
    """

    def __init__(self, text: str = "", parent=None):
        self._full_text = text
        super().__init__(text, parent)

    # NO usar sizePolicy Ignored: QBoxLayout le asigna slot de ancho 0 al
    # item (aun con minimumWidth explícito) y el widget "salta" a su mínimo
    # pintándose ENCIMA del vecino. Con policy normal + minimumSizeHint chico
    # el layout puede comprimir sin superponer.
    def sizeHint(self):  # noqa: N802 — override de QLabel
        fm = QFontMetrics(self.font())
        base = super().sizeHint()
        return QSize(fm.horizontalAdvance(self._full_text) + 4, base.height())

    def minimumSizeHint(self):  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(24, base.height())

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        self._full_text = text
        super().setText(text)
        self.updateGeometry()
        self._elide()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        self._elide()

    def _elide(self):
        fm = QFontMetrics(self.font())
        avail = max(0, self.width() - 2)
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, avail)
        if super().text() != elided:
            super().setText(elided)
        self.setToolTip(self._full_text if elided != self._full_text else "")


class NMBadge(QLabel):
    """Pill semántica del handoff §4.4.

    Args:
        text:   Etiqueta. Puede incluir un símbolo unicode a la izquierda.
        tone:   ``"neutral"`` / ``"info"`` / ``"completed"`` /
                ``"warning"`` / ``"critical"`` / ``"patient"``.
        modo:   Override; ``None`` = sigue ThemeManager.
        parent: parent widget.

    Para añadir ícono SVG real, usar ``NMIcon`` en un layout horizontal y
    poner el ``NMBadge`` al lado — el handoff acepta rich text via QLabel
    pero la composición externa es más mantenible.
    """

    def __init__(self, text: str = "", tone: str = "neutral", modo: str | None = None, parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone if tone in _BADGE_TONE_TO_KEY else "neutral"
        self.setObjectName("NMBadge")
        self.setFont(v3_font("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(24)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def set_tone(self, tone: str):
        if tone in _BADGE_TONE_TO_KEY:
            self._tone = tone
            self._apply_style()

    def tone(self) -> str:
        return self._tone

    def _apply_style(self):
        key = _BADGE_TONE_TO_KEY[self._tone]
        color_hex = C(key, self._modo)
        # Soft bg: rgba a 14% del color semántico (consistente con handoff §4.4).
        fc = QColor(color_hex)
        fc.setAlpha(36)  # ~14%
        bg_css = f"rgba({fc.red()},{fc.green()},{fc.blue()},{fc.alpha()})"
        border_alpha = QColor(color_hex)
        border_alpha.setAlpha(60)
        border_css = (
            f"rgba({border_alpha.red()},{border_alpha.green()},"
            f"{border_alpha.blue()},{border_alpha.alpha()})"
        )
        self._pill_r_applied = pill_radius(self, fallback=26)
        self.setStyleSheet(f"""
            NMBadge {{
                color: {color_hex};
                background-color: {bg_css};
                border: 1px solid {border_css};
                border-radius: {self._pill_r_applied}px;
                padding: 4px 12px;
                min-height: 24px;
            }}
        """)
        # Una pill nunca debe renderizar texto recortado ni pisarse con su
        # vecina. Medir con QFontMetrics y NO con sizeHint(): el sizeHint del
        # QLabel depende de que el QSS esté "polished", y cuando la pill se
        # re-estila después del primer layout (theme apply) el mínimo crecía
        # tarde — el widget se ensanchaba sin que el QHBoxLayout reposicionara
        # a los hermanos → pills superpuestas (bug real: "Sin alerta activa"
        # pisada por "Progreso 5d" en el hero del detalle del Hub).
        # 26 = padding QSS 12+12 + borde 1+1.
        self._sync_min_width()

    def _sync_min_width(self):
        fm = QFontMetrics(self.font())
        self.setMinimumWidth(fm.horizontalAdvance(self.text()) + 26)
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if pill_radius(self, fallback=26) != getattr(self, "_pill_r_applied", None):
            self._apply_style()

    def setText(self, text: str):  # noqa: N802 — override de QLabel
        super().setText(text)
        self._sync_min_width()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


# ── NMCardSecondary ──────────────────────────────────────────────────────────
# Handoff §4.2: variante "nm-card-2" — surface-2, sin sombra, radius 14.
# Se usa para cards anidadas o secundarias (insets dentro de cards primarias).


class NMCardSecondary(NMCard):
    """Card secundaria del handoff §4.2 (``nm-card-2``).

    Apaga la sombra de la card primaria y conmuta el background a
    ``surface-2`` con radius 14. Mantiene la API de NMCard.
    """

    def __init__(self, parent=None, modo: str | None = None, clickable: bool = False):
        super().__init__(parent=parent, modo=modo, clickable=clickable, glow=False)
        # Apagar sombra heredada (handoff §4.2: "sin sombra")
        try:
            self.setGraphicsEffect(None)
        except Exception:
            pass
        self._card_shadow = None
        self._apply_secondary_style()
        _tm().theme_changed.connect(self._reapply_secondary)

    def _apply_secondary_style(self):
        surf2 = (
            v3c("surface_2", self._modo).name()
            if "surface_2" in (V3_DARK if "dark" in self._modo else V3_LIGHT)
            else C("bg_input", self._modo)
        )
        border = v3c("line", self._modo)
        border_css = f"rgba({border.red()},{border.green()},{border.blue()},{border.alpha()})"
        # Override del stylesheet base de NMCard sin perder focus ring.
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#NMCard {{
                background-color: {surf2};
                border: 1px solid {border_css};
                border-radius: {V3_RD["lg"]}px;
            }}
        """
        )

    def _reapply_secondary(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_secondary_style()


# ── NMSelect ─────────────────────────────────────────────────────────────────
# Handoff §4.3: QComboBox themed (surface-2 bg, border line, radius 14,
# focus = primary). El catálogo previo no exponía un select consistente.

try:
    from PyQt6.QtWidgets import QComboBox as _QComboBox

    class NMSelect(_QComboBox):
        """QComboBox themed según handoff §4.3.

        Lee tokens del tema vía ``stylesheet_combobox`` (theme_qt). Se conecta
        al ThemeManager para repintar al conmutar light/dark.
        """

        def __init__(self, parent=None, modo: str | None = None):
            super().__init__(parent)
            self._modo = norm_modo(modo or _tm().modo)
            self.setMinimumHeight(36)
            self.setFont(qfont("size_body"))
            self._apply_theme(self._modo)
            _tm().theme_changed.connect(self._apply_theme)

        def _apply_theme(self, modo: str):
            self._modo = norm_modo(modo)
            try:
                from shared.theme_qt import stylesheet_combobox
            except ImportError:
                from theme_qt import stylesheet_combobox  # type: ignore
            self.setStyleSheet(stylesheet_combobox(self._modo))
except ImportError:
    # PyQt6 sin QComboBox (no debería pasar) — degradar a alias seguro.
    NMSelect = QLineEdit  # type: ignore


# ── NMStatusDot ──────────────────────────────────────────────────────────────
# Handoff §3 / tokens.css `.nm-status-dot`: punto de estado 8 px con halo
# suave (positive/warn/danger). Sirve para footer de sidebar y barras de
# estado interno. Cubre los tres tonos del handoff usando los keys semánticos
# del tema existente — NO introduce paleta nueva.

_STATUS_DOT_TONE_TO_KEY = {
    "ok": "success",
    "positive": "success",
    "warn": "warning",
    "warning": "warning",
    "danger": "danger",
    "error": "danger",
}


class NMStatusDot(QWidget):
    """Punto de estado con halo suave (handoff §3 + tokens `.nm-status-dot`).

    El punto sólido es de 8 px; el widget total es 16 px para hospedar el
    halo radial al estilo del CSS original. Tonos soportados:
    ``"ok" | "warn" | "danger"`` (alias: ``positive | warning | error``).
    """

    def __init__(self, tone: str = "ok", modo: str | None = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = tone if tone in _STATUS_DOT_TONE_TO_KEY else "ok"
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        _tm().theme_changed.connect(self._apply_theme)

    def set_tone(self, tone: str):
        if tone in _STATUS_DOT_TONE_TO_KEY:
            self._tone = tone
            self.update()

    def tone(self) -> str:
        return self._tone

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, _ev):  # noqa: N802 (Qt API)
        key = _STATUS_DOT_TONE_TO_KEY[self._tone]
        color = QColor(C(key, self._modo))
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        # Halo radial (alpha decreciente) de 14 px
        halo = QRadialGradient(QPointF(cx, cy), 7.0)
        halo_c = QColor(color)
        halo_c.setAlpha(70)
        halo.setColorAt(0.0, halo_c)
        edge = QColor(color)
        edge.setAlpha(0)
        halo.setColorAt(1.0, edge)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(cx, cy), 7.0, 7.0)
        # Punto sólido 8 px
        p.setBrush(QBrush(color))
        p.drawEllipse(QPointF(cx, cy), 4.0, 4.0)
        p.end()


# ── NMWindowChrome ────────────────────────────────────────────────────────────
# Handoff §3 / components.jsx `WindowChrome`:
#   Barra de título custom de 36 px que reemplaza el título nativo del SO.
#   Background bg-1, border-bottom 1px line.
#   Izquierda: logo mark 16×16 (gradiente primary→accent→amber) + título
#   (Manrope 12/600, ink-2) + subtítulo opcional (mute, separado con "—").
#   Derecha: status dot + label opcionales + botones min/max/close (40×28 c/u).
#   Drag: mousePressEvent/mouseMoveEvent mueven la ventana padre.
# ─────────────────────────────────────────────────────────────────────────────


class _ChromeWinBtn(QPushButton):
    """Botón de control de ventana (min / max / close) para NMWindowChrome."""

    def __init__(self, kind: str, modo: str, parent=None):
        super().__init__(parent)
        self._kind = kind  # "min" | "max" | "close"
        self._modo = norm_modo(modo)
        self.setFixedSize(46, 38)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._apply_style()

    def _apply_style(self):
        is_dark = "dark" in self._modo
        hover_bg = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.05)"
        pressed_bg = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.1)"
        if self._kind == "close":
            danger = v3c("danger", self._modo)
            pressed = QColor(
                blend_color(
                    v3c("primary_ink", self._modo).name(),
                    danger.name(),
                    0.18 if is_dark else 0.12,
                )
            )
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background: {danger.name()};
                }}
                QPushButton:pressed {{
                    background: {pressed.name()};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                }}
                QPushButton:hover {{
                    background: {hover_bg};
                }}
                QPushButton:pressed {{
                    background: {pressed_bg};
                }}
            """)

    def paintEvent(self, event):
        p = QPainter(self)
        is_dark = "dark" in self._modo
        hovered = self.underMouse()
        pressed = self.isDown()
        # Fondo hover/pressed pintado ACÁ: este paintEvent custom reemplaza el
        # render por defecto del QPushButton, por lo que el `background` del
        # stylesheet nunca llegaba a dibujarse. En light eso dejaba la X en
        # primary_ink (casi blanco) sobre la superficie clara del chrome → la X
        # "desaparecía" al hover (bug owner). Pintar el fondo restaura el patrón
        # Windows (rojo en close, sutil en min/max) y devuelve el contraste.
        if hovered or pressed:
            if self._kind == "close":
                if pressed:
                    bg = QColor(
                        blend_color(
                            v3c("primary_ink", self._modo).name(),
                            v3c("danger", self._modo).name(),
                            0.18 if is_dark else 0.12,
                        )
                    )
                else:
                    bg = QColor(v3c("danger", self._modo))
            else:
                base = QColor(255, 255, 255) if is_dark else QColor(0, 0, 0)
                if is_dark:
                    base.setAlphaF(0.15 if pressed else 0.10)
                else:
                    base.setAlphaF(0.10 if pressed else 0.05)
                bg = base
            p.fillRect(self.rect(), bg)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        if self._kind == "close" and hovered:
            color = QColor(v3c("primary_ink", self._modo))
        else:
            color = QColor(v3c("text", self._modo))
        pen = QPen(color, 1)
        p.setPen(pen)
        cx = self.width() // 2
        cy = self.height() // 2
        if self._kind == "min":
            p.drawLine(cx - 5, cy, cx + 5, cy)
        elif self._kind == "max":
            p.drawRect(cx - 5, cy - 5, 10, 10)
        elif self._kind == "close":
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.drawLine(cx - 5, cy - 5, cx + 5, cy + 5)
            p.drawLine(cx + 5, cy - 5, cx - 5, cy + 5)
        p.end()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()
        self.update()


class _ChromeLogoMark(QLabel):
    """Logo icon mark que usa el asset real de la marca mediante nm_logo_pixmap."""

    def __init__(self, modo: str, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(20, 20)
        self._apply_theme(self._modo)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        from shared.assets import nm_logo_pixmap

        pm = nm_logo_pixmap(self._modo, tipo="icon", width=20, height=20)
        self.setPixmap(pm)
        self.update()


class NMWindowChrome(QWidget):
    """Barra de título custom 36 px (handoff WindowChrome).

    - Drag a mover: mantiene lógica mousePressEvent/mouseMoveEvent.
    - Doble clic → maximizar/restaurar.
    - Botones min/max/close llaman a window().showMinimized() etc.
    - ThemeManager conectado vía _tm().theme_changed.
    """

    theme_toggle = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(
        self,
        title: str = "NeuroMood",
        subtitle: str = None,
        status: str = None,
        status_label: str = None,
        show_theme_toggle: bool = False,
        show_settings_btn: bool = False,
        show_maximize: bool = True,
        modo: str = "dark_hybrid",
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._title = title
        self._subtitle = subtitle
        self._status = status  # "ok" | "warn" | "danger" | None
        self._status_label = status_label
        self._show_theme_toggle = show_theme_toggle
        self._show_settings_btn = show_settings_btn
        # Ventanas de tamaño fijo (onboarding, diálogos) no deben maximizar:
        # solo "—" minimizar y "✕" cerrar. Maximizar rompería el layout
        # fit-first y no aporta en una card centrada.
        self._show_maximize = show_maximize
        self._drag_pos = None

        self.setFixedHeight(38)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._build_ui()
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(0)

        title_wrap = QWidget(self)
        title_wrap.setStyleSheet("background: transparent;")
        title_l = QHBoxLayout(title_wrap)
        title_l.setContentsMargins(0, 0, 0, 0)
        title_l.setSpacing(7)
        self._mark = _ChromeLogoMark(self._modo, self)
        title_l.addWidget(self._mark, 0, Qt.AlignmentFlag.AlignVCenter)
        self._lbl_title = QLabel(self._title)
        title_l.addWidget(self._lbl_title, 0, Qt.AlignmentFlag.AlignVCenter)
        if self._subtitle:
            self._lbl_sep = QLabel("/")
            title_l.addWidget(self._lbl_sep, 0, Qt.AlignmentFlag.AlignVCenter)
            self._lbl_sub = QLabel(self._subtitle)
            title_l.addWidget(self._lbl_sub, 0, Qt.AlignmentFlag.AlignVCenter)
        self._title_wrap = title_wrap
        lay.addWidget(title_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        # ── Contexto de módulo (Suite, BL-07) ────────────────────────────────
        # Cuando hay un módulo abierto, el back + icono + título viven aquí, en la
        # titlebar, en vez de una banda de 56px aparte. Oculto hasta abrir módulo.
        ctx_wrap = QWidget(self)
        ctx_wrap.setStyleSheet("background: transparent;")
        ctx_l = QHBoxLayout(ctx_wrap)
        ctx_l.setContentsMargins(0, 0, 0, 0)
        ctx_l.setSpacing(8)
        self._ctx_back = QPushButton("←", ctx_wrap)
        self._ctx_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ctx_back.setFixedSize(30, 30)
        self._ctx_back.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._ctx_back.setAccessibleName("Volver")
        self._ctx_back.setToolTip("Volver al inicio")
        self._ctx_back.clicked.connect(self._on_ctx_back)
        ctx_l.addWidget(self._ctx_back, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ctx_icon = QLabel(ctx_wrap)
        self._ctx_icon.setFixedSize(18, 18)
        self._ctx_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ctx_icon.setStyleSheet("background: transparent;")
        ctx_l.addWidget(self._ctx_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self._ctx_title = QLabel("", ctx_wrap)
        ctx_l.addWidget(self._ctx_title, 0, Qt.AlignmentFlag.AlignVCenter)
        ctx_wrap.hide()
        self._ctx_wrap = ctx_wrap
        lay.addWidget(ctx_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addStretch(1)

        # Optional status dot + label (JetBrains Mono 11)
        if self._status is not None:
            self._status_dot = NMStatusDot(tone=self._status, modo=self._modo, parent=self)
            lay.addWidget(self._status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(6)
            self._lbl_status_txt = QLabel(self._status_label or "")
            lay.addWidget(self._lbl_status_txt, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(12)

        if self._show_settings_btn:
            self._btn_settings = QPushButton(self)
            self._btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_settings.setStyleSheet(
                f"QPushButton {{ border: none; "
                "background: transparent; border-radius: 12px; padding: 0px; } "
                f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
            )
            self._btn_settings.setFixedSize(30, 30)
            self._btn_settings.setToolTip("Ajustes")
            self._btn_settings.setAccessibleName("Ajustes")
            # P2.C: usar el engranaje "cog" en vez de "settings" para que no se
            # confunda con el icono de tema (sun/moon) en la titlebar.
            self._btn_settings.setIcon(nm_icon("cog", C("ink_secondary", self._modo), size=14))
            self._btn_settings.setIconSize(QSize(14, 14))
            self._btn_settings.clicked.connect(self.settings_clicked.emit)
            lay.addWidget(self._btn_settings, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(6)

        if self._show_theme_toggle:
            self._btn_theme = QPushButton(self)
            self._btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_theme.setStyleSheet(
                f"QPushButton {{ border: none; "
                "background: transparent; border-radius: 12px; padding: 0px; } "
                f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
            )
            self._btn_theme.setFixedSize(30, 30)
            is_dark = "dark" in self._modo
            icon_name = "sun" if is_dark else "moon"
            self._btn_theme.setIcon(nm_icon(icon_name, C("ink_secondary", self._modo), size=14))
            self._btn_theme.setIconSize(QSize(14, 14))
            self._btn_theme.clicked.connect(self.theme_toggle.emit)
            lay.addWidget(self._btn_theme, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(8)

        # Window controls: min / max / close (standard Windows design)
        win_controls = QWidget(self)
        # Transparente como title_wrap/content: sin esto el wrapper hereda el
        # `QWidget { background-color: bg_primary }` global y pinta una caja más
        # oscura sobre el `surface` del chrome (costura tras min/max/close en dark).
        win_controls.setStyleSheet("background: transparent;")
        win_controls_l = QHBoxLayout(win_controls)
        win_controls_l.setContentsMargins(0, 0, 0, 0)
        win_controls_l.setSpacing(0)

        self._btn_min = _ChromeWinBtn("min", self._modo, self)
        self._btn_max = _ChromeWinBtn("max", self._modo, self) if self._show_maximize else None
        self._btn_close = _ChromeWinBtn("close", self._modo, self)

        self._btn_min.clicked.connect(lambda: self.window().showMinimized())
        if self._btn_max is not None:
            self._btn_max.clicked.connect(self._toggle_maximize)
        self._btn_close.clicked.connect(self.window().close)

        win_controls_l.addWidget(self._btn_min)
        if self._btn_max is not None:
            win_controls_l.addWidget(self._btn_max)
        win_controls_l.addWidget(self._btn_close)
        lay.addWidget(win_controls)

    # ── Drag / maximize ───────────────────────────────────────────────────────

    def _toggle_maximize(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self._drag_pos is not None
            and not self.window().isMaximized()
        ):
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._show_maximize:
            self._toggle_maximize()
        else:
            super().mouseDoubleClickEvent(event)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        # Background: surface, como la barra de ventana del mockup.
        p.fillRect(self.rect(), v3c("surface", self._modo))
        # Border bottom: 1px line
        border_c = v3c("border", self._modo)
        p.setPen(QPen(border_c, 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c_ink2 = v3c("ink_2", self._modo)
        c_mute = v3c("mute", self._modo)
        c_faint = v3c("faint", self._modo)

        title_f = qfont("size_caption", weight=600)
        self._lbl_title.setFont(title_f)
        self._lbl_title.setStyleSheet(f"color: {c_ink2.name()}; background: transparent;")

        # El logo se actualiza internamente en _ChromeLogoMark al aplicar tema
        if hasattr(self, "_mark") and isinstance(self._mark, _ChromeLogoMark):
            self._mark._apply_theme(self._modo)

        if hasattr(self, "_lbl_sep"):
            sep_f = qfont("size_caption")
            self._lbl_sep.setFont(sep_f)
            self._lbl_sep.setStyleSheet(f"color: {c_faint.name()}; background: transparent;")
        if hasattr(self, "_lbl_sub"):
            sub_f = qfont("size_caption")
            self._lbl_sub.setFont(sub_f)
            self._lbl_sub.setStyleSheet(f"color: {c_mute.name()}; background: transparent;")
        if hasattr(self, "_lbl_status_txt"):
            self._lbl_status_txt.setFont(qfont_mono(8))
            self._lbl_status_txt.setStyleSheet(f"color: {c_mute.name()}; background: transparent;")
        if hasattr(self, "_status_dot"):
            self._status_dot._apply_theme(modo)

        self._btn_min._apply_theme(modo)
        if self._btn_max is not None:
            self._btn_max._apply_theme(modo)
        self._btn_close._apply_theme(modo)
        self._mark._apply_theme(modo)

        # Sin borde en los botones de la titlebar (Volver/Ajustes/Tema): el
        # feedback es solo el hover, según pedido del owner. Aplica en todos los
        # módulos, Home, Hub, ventanas y subventanas que usan NMWindowChrome.
        tool_btn_style = (
            f"QPushButton {{ border: none; "
            "background: transparent; border-radius: 12px; padding: 0px; } "
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
        )

        if hasattr(self, "_btn_settings"):
            self._btn_settings.setStyleSheet(tool_btn_style)
            self._btn_settings.setIcon(
                nm_icon("cog", v3c("ink_secondary", self._modo), size=14)
            )

        if hasattr(self, "_btn_theme"):
            self._btn_theme.setStyleSheet(tool_btn_style)
            is_dark = "dark" in self._modo
            icon_name = "sun" if is_dark else "moon"
            self._btn_theme.setIcon(nm_icon(icon_name, v3c("ink_secondary", self._modo), size=14))

        if hasattr(self, "_ctx_title"):
            self._apply_ctx_theme()

        self.update()

    # ── Contexto de módulo (Suite, BL-07) ──────────────────────────────────────

    def _on_ctx_back(self):
        cb = getattr(self, "_ctx_back_cb", None)
        if callable(cb):
            cb()

    def _apply_ctx_icon(self):
        if not hasattr(self, "_ctx_icon"):
            return
        key = getattr(self, "_ctx_icon_key", "") or ""
        if not key:
            self._ctx_icon.clear()
            self._ctx_icon.hide()
            return
        try:
            pm = nm_icon(key, v3c("accent", self._modo), size=18).pixmap(18, 18)
            if not pm.isNull():
                self._ctx_icon.setPixmap(pm)
                self._ctx_icon.show()
                return
        except Exception:
            pass
        self._ctx_icon.hide()

    def _apply_ctx_theme(self):
        if not hasattr(self, "_ctx_title"):
            return
        c_ink2 = v3c("ink_2", self._modo)
        self._ctx_title.setFont(qfont("size_caption", weight=600))
        self._ctx_title.setStyleSheet(f"color: {c_ink2.name()}; background: transparent;")
        self._ctx_back.setStyleSheet(
            "QPushButton { background: transparent; "
            "border: none; border-radius: 12px; "
            f"color: {c_ink2.name()}; padding: 0px; }} "
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; }}"
        )
        self._apply_ctx_icon()

    def set_module_context(self, title: str = "", icon: str = "", back_callback=None):
        """Suite: muestra back + icono + título de módulo en la titlebar y oculta el brand."""
        self._ctx_back_cb = back_callback
        self._ctx_icon_key = icon or ""
        self._ctx_title.setText((title or "").strip())
        if hasattr(self, "_title_wrap"):
            self._title_wrap.hide()
        self._ctx_wrap.show()
        self._apply_ctx_theme()

    def clear_module_context(self):
        """Suite: vuelve al brand normal de la titlebar (Home)."""
        self._ctx_back_cb = None
        if hasattr(self, "_ctx_wrap"):
            self._ctx_wrap.hide()
        if hasattr(self, "_title_wrap"):
            self._title_wrap.show()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_subtitle(self, text: str | None):
        if hasattr(self, "_lbl_sub"):
            self._lbl_sub.setText(text or "")

    def set_status(self, tone: str | None, label: str = ""):
        if hasattr(self, "_status_dot"):
            self._status_dot.set_tone(tone or "ok")
        if hasattr(self, "_lbl_status_txt"):
            self._lbl_status_txt.setText(label)


# ── NMRow ─────────────────────────────────────────────────────────────────────
# Handoff §2.7: fila genérica de lista con hover/selected/focus-visible.
# - hover:    bg surface_2
# - selected: bg primary_soft + barra vertical 3×18 primary
# - bottom border: 1px LINE (omitida en la última fila usando hide_divider)


class NMRow(QFrame):
    """Fila genérica de lista (handoff §2.7).

    Señales:
        clicked           — clic sobre la fila
        selected_changed  — cambio de estado selected (bool)

    Args:
        row_height:   Altura fija en px (default 56 Suite / 48 Hub).
        selectable:   Si True, clic marca la fila como selected.
        hide_divider: Si True, no dibuja el borde inferior (útil para la última fila).
    """

    clicked = pyqtSignal()
    selected_changed = pyqtSignal(bool)

    def __init__(
        self,
        parent=None,
        modo: str | None = None,
        row_height: int = 56,
        selectable: bool = True,
        hide_divider: bool = False,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = False
        self._hover = False
        self._selectable = selectable
        self._hide_divider = hide_divider

        self.setFixedHeight(row_height)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if selectable else Qt.CursorShape.ArrowCursor
        )
        _tm().theme_changed.connect(self._apply_theme)

    # ── API pública ────────────────────────────────────────────────────────────

    @property
    def selected(self) -> bool:
        return self._selected

    def set_selected(self, value: bool):
        if self._selected != value:
            self._selected = value
            self.update()
            self.selected_changed.emit(value)

    def set_hide_divider(self, hide: bool):
        self._hide_divider = hide
        self.update()

    # ── Interacción ───────────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
            if self._selectable:
                self.set_selected(True)
        super().mouseReleaseEvent(event)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        if self._selected:
            bg = v3c("primary_soft", self._modo)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRect(rect)
            # Barra vertical 3×18 PRIMARY a la izquierda
            bar_col = v3c("primary", self._modo)
            bar_y = (h - 18.0) / 2.0
            bar = QRectF(0, bar_y, 3, 18)
            p.setBrush(QBrush(bar_col))
            p.drawRoundedRect(bar, 1.5, 1.5)
        elif self._hover:
            bg = v3c("surface_2", self._modo)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRect(rect)

        # Focus ring (2px PRIMARY outline)
        if self.hasFocus():
            acc = v3c("primary", self._modo)
            acc.setAlpha(180)
            p.setPen(QPen(acc, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(QRectF(1, 1, w - 2, h - 2))

        # Divider inferior (1px LINE)
        if not self._hide_divider:
            border_c = v3c("line", self._modo)
            p.setPen(QPen(border_c, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(0, int(h) - 1, int(w), int(h) - 1)

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMPageHeader ──────────────────────────────────────────────────────────────


class NMPageHeader(ThemeAwareWidgetMixin, QWidget):
    """Header estándar para vistas/páginas del Hub.

    Eyebrow (CAPS secundario) + título serif h2, con slot de acciones
    a la derecha. Consolida el patrón NMSectionHeader + v3_font + action_row.

    Uso::
        hdr = NMPageHeader("Pacientes", "5 vinculados", modo=modo)
        hdr.add_action(btn_sync)
        layout.addWidget(hdr)
    """

    def __init__(self, eyebrow: str = "", title: str = "", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMPageHeader")
        self.setStyleSheet("background: transparent;")

        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(V3_SP["md"])

        text_col = QVBoxLayout()
        text_col.setSpacing(V3_SP["xs"])
        text_col.setContentsMargins(0, 0, 0, 0)

        # OJO: SIEMPRE con parent y visibilidad DESPUÉS de addWidget.
        # setVisible(True) sobre un QLabel sin padre lo muestra un instante
        # como ventana top-level — ERA la "mini ventana titilante" del owner
        # (se recreaba en cada _refresh_all_views del Hub).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())

        self._title_lbl = QLabel(title or "", self)
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))

        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._title_lbl)
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        self._root.addLayout(text_col, stretch=1)

        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(V3_SP["sm"])
        self._action_row.setContentsMargins(0, 0, 0, 0)
        self._action_row.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._root.addLayout(self._action_row)

        self._connect_theme()
        self._apply_theme(self._modo)

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def add_action(self, widget: QWidget) -> None:
        self._action_row.addWidget(widget, alignment=Qt.AlignmentFlag.AlignVCenter)

    def clear_actions(self) -> None:
        while self._action_row.count():
            item = self._action_row.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")


# ── NMChartPanel ──────────────────────────────────────────────────────────────


class NMChartPanel(NMCard):
    """Panel de gráfico con zonas reservadas: eyebrow, métrica, canvas, leyenda.

    Garantiza que datos/líneas no invadan chips, labels o tabs.

    Zonas verticales (de arriba a abajo):
      - header: eyebrow (izq) + métrica inline (der)
      - subtitle: texto pequeño opcional
      - canvas: widget chart con stretch=1 (zona reservada, nunca invadida)
      - legend: labels de eje X (opcional, altura fija 16px)

    Uso::
        panel = NMChartPanel("ULTIMOS 7 DIAS", modo=modo)
        panel.set_metric("7.3/10", "Promedio")
        panel.set_chart(NMWaveChart(modo=modo))
    """

    def __init__(self, eyebrow: str = "", subtitle: str = "", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._chart_widget = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["xs"])
        self._lay = lay

        hdr = QHBoxLayout()
        hdr.setSpacing(V3_SP["sm"])
        hdr.setContentsMargins(0, 0, 0, 0)

        # Parent + visibilidad post-addWidget: setVisible(True) en un widget
        # sin padre lo muestra un instante como top-level (mini ventana).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())
        hdr.addWidget(self._eyebrow_lbl)
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        hdr.addStretch()

        self._header_tabs_row: list[QPushButton] = []
        self._header_tabs_group = QButtonGroup(self)
        self._header_tabs_group.setExclusive(True)

        self._metric_val = QLabel()
        self._metric_val.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._metric_val.setVisible(False)
        hdr.addWidget(self._metric_val)

        self._metric_label = QLabel()
        self._metric_label.setFont(qfont("size_caption_xs"))
        self._metric_label.setVisible(False)
        hdr.addWidget(self._metric_label)

        self._hdr = hdr
        lay.addLayout(hdr)

        self._subtitle_lbl = QLabel(subtitle or "", self)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        lay.addWidget(self._subtitle_lbl)
        self._subtitle_lbl.setVisible(bool(subtitle))

        # Optional h2 serif title (for charts with a display title below the eyebrow)
        self._title_lbl = QLabel()
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setVisible(False)
        lay.addWidget(self._title_lbl)

        self._canvas_slot = QWidget()
        self._canvas_slot.setStyleSheet("background: transparent;")
        self._canvas_lay = QVBoxLayout(self._canvas_slot)
        self._canvas_lay.setContentsMargins(0, 0, 0, 0)
        self._canvas_lay.setSpacing(0)
        lay.addWidget(self._canvas_slot, stretch=1)

        self._legend_row = QHBoxLayout()
        self._legend_row.setContentsMargins(0, 0, 0, 0)
        self._legend_row.setSpacing(0)
        self._legend_widget = QWidget()
        self._legend_widget.setStyleSheet("background: transparent;")
        self._legend_widget.setLayout(self._legend_row)
        self._legend_widget.setFixedHeight(16)
        self._legend_widget.setVisible(False)
        lay.addWidget(self._legend_widget)

        self._apply_chart_theme(self._modo)
        _tm().theme_changed.connect(self._apply_chart_theme)

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_title(self, text: str) -> None:
        """Título display h2 serif (para charts con título visible debajo del eyebrow)."""
        self._title_lbl.setText(text or "")
        self._title_lbl.setVisible(bool(text))

    def set_metric(self, value: str, label: str = "") -> None:
        self._metric_val.setText(value or "")
        self._metric_val.setVisible(bool(value))
        self._metric_label.setText(f"· {label}" if label else "")
        self._metric_label.setVisible(bool(label))

    def set_header_tabs(self, labels: list[str], on_select=None) -> None:
        """Añade tabs de selección de período en el header (reemplaza tabs previos).

        Args:
            labels:    Lista de etiquetas ("7D", "30D", "ALL"…).
            on_select: Callable(label: str) invocado al seleccionar.
        """
        for btn in self._header_tabs_row:
            btn.setParent(None)
        self._header_tabs_row.clear()
        for lbl in labels:
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            btn.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if on_select is not None:
                btn.clicked.connect(lambda _=False, lb=lbl: on_select(lb))
            self._header_tabs_group.addButton(btn)
            self._hdr.addWidget(btn)
            self._header_tabs_row.append(btn)
        if self._header_tabs_row:
            self._header_tabs_row[0].setChecked(True)
        self._apply_chart_theme(self._modo)

    def set_chart(self, widget: QWidget) -> None:
        while self._canvas_lay.count():
            item = self._canvas_lay.takeAt(0)
            if item.widget() and item.widget() is not widget:
                item.widget().setParent(None)
        self._chart_widget = widget
        widget.setParent(self._canvas_slot)
        self._canvas_lay.addWidget(widget)

    def set_legend(self, labels: list) -> None:
        while self._legend_row.count():
            item = self._legend_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not labels:
            self._legend_widget.setVisible(False)
            return
        ink2 = v3c("ink_secondary", self._modo).name()
        for lbl in labels:
            lbl_w = QLabel(str(lbl))
            lbl_w.setFont(qfont("size_caption_xs"))
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_w.setStyleSheet(f"color: {ink2}; background: transparent;")
            self._legend_row.addWidget(lbl_w, stretch=1)
        self._legend_widget.setVisible(True)

    def _apply_chart_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        primary = v3c("primary", self._modo).name()
        soft = v3c("bgAlt", self._modo).name()
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._metric_val.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._metric_label.setStyleSheet(f"color: {ink2}; background: transparent;")
        for i in range(self._legend_row.count()):
            item = self._legend_row.itemAt(i)
            if item and item.widget():
                item.widget().setStyleSheet(f"color: {ink2}; background: transparent;")
        for btn in self._header_tabs_row:
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {ink2}; "
                f"border: none; border-radius: 10px; padding: 2px 7px; }}"
                f"QPushButton:checked {{ background: {soft}; color: {primary}; }}"
                f"QPushButton:hover {{ color: {ink1}; }}"
            )


# ── NMMetricCard ──────────────────────────────────────────────────────────────


class NMMetricCard(NMCard):
    """Stat card unificada: eyebrow + valor grande + badge/chip opcional.

    Consolida NMStatCard (Dashboard) y las custom stat cards de Respiración
    en un componente con jerarquía y densidad consistentes.
    Altura fija FIXED_H px para grid de métricas uniforme.

    Uso::
        card = NMMetricCard("PACIENTES", "5", modo=modo)
        card.set_badge("· 3 nuevos", "primary")
        card.set_tone("primary")
    """

    # M3 premium: altura para que entren eyebrow + número serif (size_display_m=26)
    # + badge SIN cortarse, con aire interno (lectura calma, no "admin denso").
    FIXED_H = 96

    def __init__(self, label: str = "", value: str = "—", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._tone = None
        self.setFixedHeight(self.FIXED_H)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(3)

        self._label_lbl = QLabel(label or "")
        self._label_lbl.setFont(eyebrow_font())

        self._value_lbl = QLabel(value or "—")
        try:
            from shared.theme_qt import v3_font as _v3f
            self._value_lbl.setFont(_v3f("size_display_m", weight=TYPOGRAPHY["weight_semibold"], serif=True))
        except Exception:
            self._value_lbl.setFont(qfont("size_h1", weight=TYPOGRAPHY["weight_semibold"]))

        self._badge_row = QHBoxLayout()
        self._badge_row.setContentsMargins(0, 0, 0, 0)
        self._badge_row.setSpacing(V3_SP["xs"])
        self._badge_lbl = QLabel()
        self._badge_lbl.setFont(qfont("size_caption"))
        self._badge_lbl.setVisible(False)
        self._badge_row.addWidget(self._badge_lbl)
        self._badge_row.addStretch()

        lay.addWidget(self._label_lbl)
        lay.addWidget(self._value_lbl)
        lay.addLayout(self._badge_row)

        _tm().theme_changed.connect(self._apply_metric_theme)
        self._apply_metric_theme(self._modo)

    def set_label(self, text: str) -> None:
        self._label_lbl.setText(text or "")

    def set_value(self, text: str) -> None:
        self._value_lbl.setText(text or "—")

    def set_badge(self, text: str, variant: str = "default") -> None:
        if not text:
            self._badge_lbl.setVisible(False)
            return
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(True)
        _tone_map = {
            "accent": "accent", "primary": "primary", "success": "success",
            "danger": "danger", "teal": "teal", "amber": "warning",
            "default": "ink_secondary",
        }
        color_key = _tone_map.get(variant, "ink_secondary")
        try:
            color = v3c(color_key, self._modo).name()
        except Exception:
            color = v3c("ink_secondary", self._modo).name()
        surf = v3c("surface2", self._modo).name()
        self._badge_lbl.setStyleSheet(
            f"color: {color}; background: {surf}; border-radius: 6px; padding: 2px 8px;"
        )

    def set_tone(self, token: str) -> None:
        self._tone = token
        self._apply_metric_theme(self._modo)

    def _apply_metric_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink2 = v3c("ink_secondary", self._modo).name()
        self._label_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        if self._tone:
            try:
                val_color = v3c(self._tone, self._modo).name()
            except Exception:
                val_color = v3c("ink_primary", self._modo).name()
        else:
            val_color = v3c("ink_primary", self._modo).name()
        self._value_lbl.setStyleSheet(f"color: {val_color}; background: transparent;")


# ── NMListRow ─────────────────────────────────────────────────────────────────


class NMListRow(ThemeAwareWidgetMixin, QWidget):
    """Fila premium para listas internas: icono, título, subtítulo, trailing widget.

    Hover highlight, divider inferior opcional, click signal.
    Consolida patrones de fila dispares en Avisos, Pacientes y Registro.

    Uso::
        row = NMListRow("bell", "Medicación", "Salud · 08:00", modo=modo)
        row.set_trailing(NMBadge("Completado", modo=modo))
        row.clicked.connect(callback)
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        icon: str = "",
        title: str = "",
        subtitle: str = "",
        modo: str = None,
        parent=None,
        divider: bool = True,
        clickable: bool = True,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._divider = divider
        self._clickable = clickable
        self._hover = False
        self.setFixedHeight(56)
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QHBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], 0, V3_SP["lg"], 0)
        root.setSpacing(V3_SP["md"])

        # Parent explícito + visibilidad post-addWidget: setVisible(True) en
        # un widget sin padre lo muestra un instante como top-level.
        self._icon_lbl = QLabel(self)
        self._icon_lbl.setFixedSize(20, 20)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        self._icon_name = icon
        if icon:
            try:
                # nm_icon devuelve QIcon — pedir el pixmap explícito (pasarlo
                # directo a setPixmap tiraba TypeError y caía a la letra).
                self._icon_lbl.setPixmap(
                    nm_icon(icon, v3c("ink_secondary", self._modo), size=16).pixmap(16, 16)
                )
            except Exception:
                self._icon_lbl.setText(icon[:1].upper())
        root.addWidget(self._icon_lbl)
        self._icon_lbl.setVisible(bool(icon))

        txt = QVBoxLayout()
        txt.setSpacing(1)
        txt.setContentsMargins(0, 0, 0, 0)
        self._title_lbl = QLabel(title or "", self)
        self._title_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        self._subtitle_lbl = QLabel(subtitle or "", self)
        self._subtitle_lbl.setFont(qfont("size_caption_xs"))
        txt.addWidget(self._title_lbl)
        txt.addWidget(self._subtitle_lbl)
        self._subtitle_lbl.setVisible(bool(subtitle))
        root.addLayout(txt, stretch=1)

        self._trailing_slot = QHBoxLayout()
        self._trailing_slot.setContentsMargins(0, 0, 0, 0)
        self._trailing_slot.setSpacing(V3_SP["xs"])
        root.addLayout(self._trailing_slot)

        self._connect_theme()
        self._apply_theme(self._modo)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def set_subtitle(self, text: str) -> None:
        self._subtitle_lbl.setText(text or "")
        self._subtitle_lbl.setVisible(bool(text))

    def set_trailing(self, widget: QWidget) -> None:
        while self._trailing_slot.count():
            item = self._trailing_slot.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._trailing_slot.addWidget(widget)

    def set_divider(self, show: bool) -> None:
        self._divider = show
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if self._hover and self._clickable:
            bg = QColor(v3c("surface2", self._modo))
            bg.setAlpha(120)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRect(0, 0, w, h)
        if self._divider:
            div_c = QColor(v3c("border", self._modo))
            div_c.setAlpha(60)
            p.setPen(QPen(div_c, 1))
            p.drawLine(V3_SP["lg"], h - 1, w - V3_SP["lg"], h - 1)
        p.end()

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        if self._icon_name and self._icon_lbl.isVisible():
            try:
                self._icon_lbl.setPixmap(
                    nm_icon(self._icon_name, v3c("ink_secondary", self._modo), size=16)
                )
            except Exception:
                pass
        self.update()


# ── NMFormPanel ───────────────────────────────────────────────────────────────


class NMFormPanel(NMCard):
    """Formulario inline compacto con cuerpo de campos y footer de acciones fijo.

    Estructura: eyebrow/título → body (campos) → footer con botones.
    El footer siempre queda pegado al borde inferior de la card.

    Uso::
        form = NMFormPanel("Nuevo aviso", modo=modo)
        form.body_layout().addWidget(campo_widget)
        form.add_action("Cancelar", role="ghost", callback=form.hide)
        form.add_action("Guardar", role="primary", callback=on_save)
    """

    def __init__(self, title: str = "", eyebrow: str = "", modo: str = None, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self._modo = norm_modo(modo or _tm().modo)
        self._action_buttons: list[QPushButton] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["sm"])

        self._eyebrow_lbl = QLabel(eyebrow or "")
        self._eyebrow_lbl.setFont(eyebrow_font())
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        lay.addWidget(self._eyebrow_lbl)

        self._title_lbl = QLabel(title or "")
        self._title_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        self._title_lbl.setVisible(bool(title))
        lay.addWidget(self._title_lbl)

        self._body_lay = QVBoxLayout()
        self._body_lay.setSpacing(V3_SP["sm"])
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._body_lay, stretch=1)

        self._sep = QWidget()
        self._sep.setFixedHeight(1)
        lay.addWidget(self._sep)

        self._footer_row = QHBoxLayout()
        self._footer_row.setSpacing(V3_SP["sm"])
        self._footer_row.setContentsMargins(0, V3_SP["xs"], 0, 0)
        self._footer_row.addStretch()
        lay.addLayout(self._footer_row)

        _tm().theme_changed.connect(self._apply_form_theme)
        self._apply_form_theme(self._modo)

    def body_layout(self) -> QVBoxLayout:
        return self._body_lay

    def footer_layout(self) -> QHBoxLayout:
        """Layout del footer — permite añadir widgets custom (p.ej. NMButton)."""
        return self._footer_row

    def add_action(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        """Agrega botón al footer. role: 'primary'|'secondary'|'ghost'|'danger'."""
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(80)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_row.addWidget(btn)
        self._action_buttons.append(btn)
        self._style_actions()
        return btn

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")
        self._title_lbl.setVisible(bool(text))

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def _style_actions(self) -> None:
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_on_acc = v3c("primary_ink", self._modo).name()
        text_m = v3c("text2", self._modo).name()
        text = v3c("text", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._action_buttons:
            role = btn.property("nm_role") or "secondary"
            if role == "primary":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; }}"
                )
            elif role == "danger":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_m}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )

    def _apply_form_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        sep_c = v3c("border", self._modo)
        sep_c.setAlpha(60)
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._sep.setStyleSheet(
            f"background: rgba({sep_c.red()},{sep_c.green()},{sep_c.blue()},60);"
        )
        self._style_actions()


# ── NMDialogScaffold ──────────────────────────────────────────────────────────


class NMDialogScaffold(QWidget):
    """Ventana auxiliar standalone con header, cuerpo y footer de acciones.

    Para editores y ventanas secundarias (no overlay). Incluye:
      - Header fijo: eyebrow opcional + título + botón cerrar
      - Cuerpo: widget principal (flexible, con stretch)
      - Footer fijo: action bar con botones alineados a la derecha

    Uso::
        win = NMDialogScaffold("Editor de textos", modo=modo)
        win.set_body(editor_widget)
        win.add_action("Cancelar", role="ghost", callback=win.close)
        win.add_action("Guardar", role="primary", callback=on_save)
        win.show()
    """

    def __init__(
        self,
        title: str = "",
        eyebrow: str = "",
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._action_buttons: list[QPushButton] = []
        # Flags de ventana SOLO standalone. Con parent (embebido en un QDialog
        # via addWidget) el flag Window NO se limpia porque el parent ya
        # coincide y addChildWidget saltea el setParent → el scaffold quedaba
        # como top-level invisible y el diálogo medía 360×0 (la "mini ventana"
        # de Olvidé mi PIN / Quitar paciente / Exportar informe).
        if parent is None:
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
            )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        root.setSpacing(0)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(V3_SP["sm"])
        hdr.setContentsMargins(0, 0, 0, V3_SP["sm"])

        vtext = QVBoxLayout()
        vtext.setSpacing(2)
        # Parent explícito pre-addWidget: setVisible(True) sobre un QLabel
        # huérfano lo muestra como top-level fugaz (AGENTS §10.9).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        vtext.addWidget(self._eyebrow_lbl)

        self._title_lbl = QLabel(title or "")
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        vtext.addWidget(self._title_lbl)
        hdr.addLayout(vtext, stretch=1)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setFlat(True)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close)
        hdr.addWidget(self._close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(hdr)

        # Body slot
        self._body_slot = QVBoxLayout()
        self._body_slot.setContentsMargins(0, 0, 0, 0)
        self._body_slot.setSpacing(0)
        root.addLayout(self._body_slot, stretch=1)

        # Footer
        self._footer_sep = QWidget()
        self._footer_sep.setFixedHeight(1)
        root.addWidget(self._footer_sep)

        footer = QHBoxLayout()
        footer.setSpacing(V3_SP["sm"])
        footer.setContentsMargins(0, V3_SP["sm"], 0, 0)
        footer.addStretch()
        root.addLayout(footer)
        self._footer_lay = footer

        _tm().theme_changed.connect(self._apply_scaffold_theme)
        self._apply_scaffold_theme(self._modo)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_body(self, widget: QWidget) -> None:
        while self._body_slot.count():
            item = self._body_slot.takeAt(0)
            if item.widget() and item.widget() is not widget:
                item.widget().setParent(None)
        self._body_slot.addWidget(widget)

    def add_action(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(90)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_lay.addWidget(btn)
        self._action_buttons.append(btn)
        self._style_scaffold_actions()
        return btn

    def _style_scaffold_actions(self) -> None:
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_m = v3c("text2", self._modo).name()
        text = v3c("text", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._action_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if role == "primary":
                text_on_acc = v3c("text_on_accent", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; color: {text_on_acc}; }}"
                )
            elif role == "danger":
                text_on_danger = v3c("primary_ink", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_danger}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_m}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )

    def _apply_scaffold_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self.setStyleSheet(f"QWidget {{ background: {bg}; }}")
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {ink2}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; color: {ink1}; }}"
        )
        sep_c = v3c("border", self._modo)
        self._footer_sep.setStyleSheet(
            f"background: rgba({sep_c.red()},{sep_c.green()},{sep_c.blue()},60);"
        )
        self._style_scaffold_actions()
