"""
shared/components_qt.py
Biblioteca de componentes UI PyQt6 para NeuroMood V3.

Cada componente implementa apply_theme(modo) y se conecta
automáticamente al singleton ThemeManager al instanciarse.

NO importa CustomTkinter. Compatible con contexto frozen.
"""

import sys
import os
from datetime import datetime as _dt

from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QRectF,
    QPointF, QSize, pyqtSignal, pyqtProperty, QObject, QRect,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    QVariantAnimation, QAbstractAnimation, QDate,
)
from PyQt6 import sip
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QConicalGradient, QPainterPath,
    QFontMetrics, QPixmap, QPaintEvent, QMouseEvent,
    QResizeEvent, QEnterEvent, QIcon, QPolygonF, QImage,
)
from PyQt6.QtWidgets import (
    QWidget, QFrame, QPushButton, QLineEdit, QLabel,
    QHBoxLayout, QVBoxLayout, QStackedWidget, QAbstractButton,
    QSizePolicy, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QApplication, QScrollArea, QGridLayout, QTextEdit,
)

try:
    from shared.theme_qt import (
        # Legacy (intacto)
        qcolor, qfont, qfont_mono, linear_gradient, rich_gradient,
        linear_gradient_vertical, radial_glow, noise_overlay, gradient_colors,
        conical_arc_gradient, ring_color, aura_opacity, blob_opacity,
        C, colors, norm_modo, interpolate_color, label_style, SessionColor,
        nm_icon, nm_font, sp, fx, focus_ring_stylesheet, ThemeAwareWidgetMixin,
        ANIM, EASE_OUT,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_INPUT, RADIUS_PILL, RADIUS_SMALL,
        CHECKBOX_SIZE, qcolor_to_rgba_css, qcolor_hex, shadow_effect,
        PAD_CONTAINER, PAD_CARD, GAP_CARDS, GAP_ELEMENTS, HEADER_H,
        FONT_MONO, SIZE_TIME_LARGE, SIZE_TIME_TIMER,
        RING_GOOD_THRESHOLD, RING_MID_THRESHOLD,
        stylesheet_lineedit, aplicar_captionbar_qt,
        obtener_ruta_recurso, recolorear_logo_light,
        # v3 (nuevos helpers para los sub-pasos 2-8)
        v3c, parse_rgba, v3_shadow, v3_linear_gradient,
        v3_conical_signature, v3_font, mood_qcolor, mood_gradient,
        V3_SP, V3_RD,
    )
    from shared.theme import (
        TYPOGRAPHY, LAYOUT, CATEGORY_COLORS, get_gradient,
        # v3
        V3_LIGHT, V3_DARK, V3_SPACE, V3_RADIUS, V3_SHADOWS, V3_GRADIENTS,
        MOOD_PALETTE, get_v3_palette, get_mood, v3_mode, icon_stroke_width,
    )
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme_qt import (
        qcolor, qfont, qfont_mono, linear_gradient, rich_gradient,
        linear_gradient_vertical, radial_glow, noise_overlay, gradient_colors,
        conical_arc_gradient, ring_color, aura_opacity, blob_opacity,
        C, colors, norm_modo, interpolate_color, label_style, SessionColor,
        nm_icon, nm_font, sp, fx, focus_ring_stylesheet, ThemeAwareWidgetMixin,
        ANIM, EASE_OUT,
        RADIUS_CARD, RADIUS_BUTTON, RADIUS_INPUT, RADIUS_PILL, RADIUS_SMALL,
        CHECKBOX_SIZE, qcolor_to_rgba_css, qcolor_hex, shadow_effect,
        PAD_CONTAINER, PAD_CARD, GAP_CARDS, GAP_ELEMENTS, HEADER_H,
        FONT_MONO, SIZE_TIME_LARGE, SIZE_TIME_TIMER,
        RING_GOOD_THRESHOLD, RING_MID_THRESHOLD,
        stylesheet_lineedit, aplicar_captionbar_qt,
        obtener_ruta_recurso, recolorear_logo_light,
        v3c, parse_rgba, v3_shadow, v3_linear_gradient,
        v3_conical_signature, v3_font, mood_qcolor, mood_gradient,
        V3_SP, V3_RD,
    )
    from theme import (
        TYPOGRAPHY, LAYOUT, CATEGORY_COLORS, get_gradient,
        V3_LIGHT, V3_DARK, V3_SPACE, V3_RADIUS, V3_SHADOWS, V3_GRADIENTS,
        MOOD_PALETTE, get_v3_palette, get_mood, v3_mode, icon_stroke_width,
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
    theme_changed = pyqtSignal(str)   # emite el nuevo modo

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
        self._transitioning = False   # evita re-entradas durante una animación

    @property
    def modo(self) -> str:
        return self._modo

    def switch_mode(self, new_modo: str, animate: bool = True):
        new_modo = norm_modo(new_modo)
        if new_modo == self._modo or self._transitioning:
            return

        if not animate or QApplication.instance() is None:
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
            QTimer.singleShot(self.TRANSITION_MS + 20,
                              lambda: setattr(self, "_transitioning", False))

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
    """Widget de estado vacío con icono, título y subtítulo."""

    def __init__(self, icon_key: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self._icon_key = icon_key
        self._modo = norm_modo(_tm().modo)

        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp("xl"), sp("xl"), sp("xl"), sp("xl"))
        layout.setSpacing(sp("sm"))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(56, 56)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(nm_font("h2"))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setFont(nm_font("body"))
        self._subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_lbl.setWordWrap(True)
        layout.addWidget(self._subtitle_lbl)

        self._apply_theme(self._modo)
        self._connect_theme()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        icon_color = QColor(c["accent"])
        icon_color.setAlphaF(0.4)
        self._icon_lbl.setPixmap(nm_icon(self._icon_key, icon_color, size=48).pixmap(48, 48))
        self._title_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")


class NMCard(QFrame):
    """
    Card v3 — superficie limpia con border ``borderSoft`` y radius 14.

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

    def __init__(self, parent=None, accent_color: str = None,
                 clickable: bool = True, modo: str = None,
                 disabled: bool = False, disabled_reason: str = "",
                 glow: bool = False):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._accent = accent_color
        self._base_accent = accent_color
        self._clickable = clickable
        self._glow = glow
        self._hover = False
        self._disabled = False
        self._disabled_effect: QGraphicsOpacityEffect | None = None
        self._disabled_reason = ""
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._card_shadow: QGraphicsDropShadowEffect | None = None

        self.setObjectName("NMCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor if clickable
                       else Qt.CursorShape.ArrowCursor)
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

        Spec README V3_SHADOWS:
          light card:  blur 12, offset (0,4), rgba(15,23,42,13)
          dark  card:  blur 30, offset (0,10), rgba(0,0,0,115)
          light ring:  blur 20, offset (0,4), rgba(20,184,166,76)  (glow=True)
          dark  glow:  blur 40, offset (0,0),  rgba(94,234,212,46) (glow=True)
        """
        if self._disabled:
            return
        if self._card_shadow is None:
            self._card_shadow = QGraphicsDropShadowEffect(self)
        is_dark = "dark" in self._modo
        if self._glow:
            # Halo teal — "glow" en dark, "ring" en light
            if is_dark:
                self._card_shadow.setBlurRadius(40)
                self._card_shadow.setOffset(0, 0)
                sc = v3c("teal", self._modo)
                sc.setAlpha(120)
            else:
                self._card_shadow.setBlurRadius(20)
                self._card_shadow.setOffset(0, 4)
                sc = v3c("teal", self._modo)
                sc.setAlpha(96)
        else:
            # Sombra estándar de card
            if is_dark:
                self._card_shadow.setBlurRadius(30)
                self._card_shadow.setOffset(0, 10)
                sc = QColor(0, 0, 0, 115)
            else:
                self._card_shadow.setBlurRadius(16)
                self._card_shadow.setOffset(0, 4)
                sc = QColor(15, 23, 42, 22)
        self._card_shadow.setColor(sc)
        self.setGraphicsEffect(self._card_shadow)

    # ── hover (solo cambia el color del border, sin escalado) ─────────────────

    def enterEvent(self, event: QEnterEvent):
        self._hover = True
        if not self._disabled and self.isEnabled() and self._card_shadow is not None:
            shadow = self._card_shadow
            shadow.setBlurRadius(36 if "dark" in self._modo else 20)
            shadow.setOffset(0, 12 if "dark" in self._modo else 6)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if not self._disabled and self.isEnabled() and self._card_shadow is not None:
            shadow = self._card_shadow
            is_dark = "dark" in self._modo
            shadow.setBlurRadius(30 if is_dark else 16)
            shadow.setOffset(0, 10 if is_dark else 4)
        self.update()
        super().leaveEvent(event)

    # ── click (v3 no aplica scale a cards en press; solo se emite clicked) ────

    def mouseReleaseEvent(self, event: QMouseEvent):
        if (self._clickable and not self._disabled
                and event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.pos())):
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
            self._scale_anim.stop()
        self._scale_anim = QPropertyAnimation(self, b"geometry", self)
        self._scale_anim.setDuration(ANIM["fast"])
        self._scale_anim.setStartValue(self.geometry())
        self._scale_anim.setEndValue(target)
        self._scale_anim.setEasingCurve(EASE_OUT)
        self._scale_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── paintEvent v3 ─────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = "dark" in self._modo
        r = V3_RD["lg"]                 # radius 14
        w, h = self.width(), self.height()
        rect = QRectF(0, 0, w, h)

        # 1. Halo exterior (glow=True): líneas concéntricas decrecientes
        if self._glow and not self._disabled and self.isEnabled():
            halo_hex = self._accent or v3c("teal", self._modo).name()
            base_alpha = 96 if is_dark else 50
            for i in range(6):
                a = int(base_alpha * (1 - i * 0.16))
                if a <= 0:
                    break
                col = QColor(halo_hex)
                col.setAlpha(a)
                p.setPen(QPen(col, 1))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(
                    QRectF(-i - 1, -i - 1, w + (i + 1) * 2, h + (i + 1) * 2),
                    r + i + 1, r + i + 1,
                )

        # 2. Superficie — glassmorphism en ambos temas
        if not self._disabled and self.isEnabled():
            if is_dark:
                surf_col = QColor(18, 28, 45, 200)  # glass dark
            else:
                surf_col = QColor(255, 255, 255, 235)  # glass light (sutil translúcido)
            p.setBrush(QBrush(surf_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)

            # 2b. Top specular highlight (efecto vidrio — línea reflejada arriba)
            highlight_h = min(h * 0.5, 60.0)
            hg = QLinearGradient(0, 0, 0, highlight_h)
            if is_dark:
                hg.setColorAt(0.0, QColor(255, 255, 255, 28))
                hg.setColorAt(1.0, QColor(255, 255, 255, 0))
            else:
                hg.setColorAt(0.0, QColor(255, 255, 255, 180))
                hg.setColorAt(1.0, QColor(255, 255, 255, 0))
            # Clipping al rounded rect para no salirse por el border-radius
            clip_path = QPainterPath()
            clip_path.addRoundedRect(rect, r, r)
            p.save()
            p.setClipPath(clip_path)
            p.setBrush(QBrush(hg))
            p.drawRect(QRectF(0, 0, w, highlight_h))
            p.restore()
        else:
            # Disabled: sin glassmorphism, surface sólida (legibilidad)
            surface_key = "surfaceSolid" if is_dark else "surface"
            p.setBrush(QBrush(v3c(surface_key, self._modo)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)

        # 3. Overlay gradient translúcido teal→violet (solo dark + glow)
        if self._glow and is_dark and not self._disabled and self.isEnabled():
            p.save()
            p.setOpacity(0.10)
            grad = v3_linear_gradient(rect, self._modo, 135, "signature")
            p.setBrush(QBrush(grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, r, r)
            p.restore()

        # 4. Border: borderSoft normal, borderStrong en hover
        border_key = "borderStrong" if (self._hover and self.isEnabled()
                                        and not self._disabled) else "borderSoft"
        p.setPen(QPen(v3c(border_key, self._modo), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), r, r)

        p.end()

    # ── theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))
        self._apply_card_shadow()
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
            self.setCursor(Qt.CursorShape.PointingHandCursor if self._clickable
                           else Qt.CursorShape.ArrowCursor)
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
            self._success_anim.stop()
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

        self._success_anim = QSequentialAnimationGroup(self)
        self._success_anim.addAnimation(grow)
        self._success_anim.addAnimation(shrink)

        def _restore():
            self._accent = prev_accent
            self._glow = prev_glow
            self.update()

        self._success_anim.finished.connect(_restore)
        self._success_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMButton ──────────────────────────────────────────────────────────────────

# Sizes v3 según README: sm/md/lg → 32/40/48
_NM_BUTTON_HEIGHT = {"sm": 32, "md": 40, "lg": 48}
_NM_BUTTON_FONT   = {"sm": "size_small", "md": "size_body", "lg": "size_body"}


class NMButton(QPushButton):
    """
    Botón v3 — pill, 3 variantes (``gradient`` / ``secondary`` / ``ghost``),
    3 sizes (``sm`` / ``md`` / ``lg`` → 32 / 40 / 48).

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

    def __init__(self, text: str = "", parent=None, modo: str = None,
                 width: int = 180, height: int | None = None,
                 variant: str = "gradient", size: str = "md"):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._variant = variant if variant in ("gradient", "secondary", "ghost") else "gradient"
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._hover = False
        self._pressed = False
        self._ripples = []
        self._success_anim: QSequentialAnimationGroup | None = None
        self._scale_anim: QPropertyAnimation | None = None
        self._base_geom = None
        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(16)
        self._ripple_timer.timeout.connect(self._tick_ripples)
        self._btn_shadow: QGraphicsDropShadowEffect | None = None

        eff_height = height if height is not None else _NM_BUTTON_HEIGHT[self._size]
        self.setFixedHeight(eff_height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_semibold"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        self._apply_btn_shadow()
        _tm().theme_changed.connect(self._apply_theme)

    # ── API v3 ────────────────────────────────────────────────────────────────

    def set_variant(self, variant: str):
        if variant in ("gradient", "secondary", "ghost"):
            self._variant = variant
            self._apply_btn_shadow()
            self.update()

    def variant(self) -> str:
        return self._variant

    def set_size(self, size: str):
        if size in ("sm", "md", "lg") and size != self._size:
            self._size = size
            self.setFixedHeight(_NM_BUTTON_HEIGHT[size])
            self.setFont(qfont(_NM_BUTTON_FONT[size],
                               weight=TYPOGRAPHY["weight_semibold"]))
            self.update()

    # ── ripples (solo variant=gradient) ───────────────────────────────────────

    def _tick_ripples(self):
        alive = []
        alpha_step = max(1, int(80 * self._ripple_timer.interval() / ANIM["fast"]))
        for rip in self._ripples:
            rip["r"] += 8
            rip["a"] = max(0, rip["a"] - alpha_step)
            if rip["a"] > 0:
                alive.append(rip)
        self._ripples = alive
        if not alive:
            self._ripple_timer.stop()
        self.update()

    # ── paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        # Pill perfecto: cap radius a half-height por si LAYOUT['radius_button']
        # es 999 (default v3) y el botón es bajo.
        r = min(LAYOUT["radius_button"], h // 2)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        if not self.isEnabled():
            p.setOpacity(0.4)

        if self._variant == "gradient":
            grad = v3_linear_gradient(rect, self._modo, 135, "signature")
            p.fillPath(path, QBrush(grad))

            # Glow exterior teal en hover
            if self._hover and not self._pressed and self.isEnabled():
                glow = v3c("teal", self._modo)
                glow.setAlpha(90 if "dark" in self._modo else 64)
                glow_w = 2
                p.setPen(QPen(glow, glow_w))
                p.setBrush(Qt.BrushStyle.NoBrush)
                inset = glow_w / 2
                p.drawRoundedRect(rect.adjusted(inset, inset, -inset, -inset), r, r)

            text_color = QColor(C("text_on_accent", self._modo))

        elif self._variant == "secondary":
            is_dark = "dark" in self._modo
            surf_key = "surfaceSolid" if is_dark else "surface"
            elev_key = "elevatedSolid" if is_dark else "elevated"
            bg_col = v3c(elev_key if self._hover else surf_key, self._modo)
            p.fillPath(path, QBrush(bg_col))

            border_key = "borderStrong" if (self._hover or self._pressed) else "border"
            border_col = v3c(border_key, self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, h - 1), r, r)

            text_color = v3c("text", self._modo)

        else:  # ghost
            if self._hover and not self._pressed and self.isEnabled():
                bg_col = v3c("borderSoft", self._modo)
                p.fillPath(path, QBrush(bg_col))
            text_color = v3c("text2", self._modo)

        # Texto
        p.setPen(QPen(text_color))
        p.setFont(self.font())
        p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())

        # Ripples (solo gradient)
        if self._variant == "gradient":
            for rip in self._ripples:
                rip_col = QColor(255, 255, 255, rip["a"])
                p.setBrush(QBrush(rip_col))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(rip["center"], rip["r"], rip["r"])
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
            if self._variant == "gradient":
                pos = event.position() if hasattr(event, "position") else QPointF(event.pos())
                self._ripples.append({"center": pos, "r": 0, "a": 80})
                self._ripple_timer.start()
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
            self._scale_anim.stop()
        self._scale_anim = QPropertyAnimation(self, b"geometry", self)
        self._scale_anim.setDuration(100)
        self._scale_anim.setStartValue(self.geometry())
        self._scale_anim.setEndValue(target)
        self._scale_anim.setEasingCurve(EASE_OUT)
        self._scale_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
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
            # Glow teal pronunciado (CTA primary)
            shadow.setBlurRadius(30 if is_dark else 20)
            shadow.setOffset(0, 8 if is_dark else 4)
            sc = v3c("teal", self._modo)
            sc.setAlpha(100 if is_dark else 55)
        elif self._variant == "secondary":
            # Sombra neutra sutil (lift discreto)
            shadow.setBlurRadius(12 if is_dark else 8)
            shadow.setOffset(0, 4 if is_dark else 2)
            sc = QColor(0, 0, 0, 80 if is_dark else 18)
        else:  # ghost
            # Sombra mínima — apenas perceptible
            shadow.setBlurRadius(6 if is_dark else 4)
            shadow.setOffset(0, 2 if is_dark else 1)
            sc = QColor(0, 0, 0, 50 if is_dark else 10)
        shadow.setColor(sc)

    def play_success(self):
        """Pulso de escala."""
        base = self.geometry()
        if base.isNull():
            return
        target = base.adjusted(-2, -2, 2, 2)
        if self._success_anim:
            self._success_anim.stop()
        self._success_anim = QSequentialAnimationGroup(self)
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
        self._success_anim.addAnimation(grow)
        self._success_anim.addAnimation(shrink)
        self._success_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMButtonOutline ───────────────────────────────────────────────────────────

class NMButtonOutline(QPushButton):
    """Botón pill toggleable v3 — variant ``secondary`` cuando inactivo,
    fill gradient teal→violet cuando activo.

    Si ``toggleable=True`` alterna ``active`` en cada click. Estilo coherente
    con :class:`NMButton` (mismo radius pill, misma tipografía sm).
    """

    def __init__(self, text: str = "", parent=None, modo: str = None,
                 toggleable: bool = False, size: str = "md"):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._hover = False
        self._active = False
        self._toggleable = toggleable
        self._size = size if size in ("sm", "md", "lg") else "md"
        self._success_anim: QSequentialAnimationGroup | None = None

        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_medium"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setMinimumHeight(_NM_BUTTON_HEIGHT[self._size])
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        _tm().theme_changed.connect(self._apply_theme)

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
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        if self._active:
            # Fill gradient teal→violet (v3 active = primary)
            grad = v3_linear_gradient(rect, self._modo, 135, "signature")
            p.fillPath(path, QBrush(grad))
            text_color = QColor(C("text_on_accent", self._modo))
        elif self._hover:
            # secondary hover
            is_dark = "dark" in self._modo
            elev_key = "elevatedSolid" if is_dark else "elevated"
            p.fillPath(path, QBrush(v3c(elev_key, self._modo)))
            border_col = v3c("borderStrong", self._modo)
            p.setPen(QPen(border_col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, h - 1), r, r)
            text_color = v3c("text", self._modo)
        else:
            is_dark = "dark" in self._modo
            surf_key = "surfaceSolid" if is_dark else "surface"
            p.fillPath(path, QBrush(v3c(surf_key, self._modo)))
            p.setPen(QPen(v3c("border", self._modo), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, h - 1), r, r)
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
            self._success_anim.stop()
        self._success_anim = QSequentialAnimationGroup(self)
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
        self._success_anim.addAnimation(grow)
        self._success_anim.addAnimation(shrink)
        self._success_anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


# ── NMInput ───────────────────────────────────────────────────────────────────

class NMInput(QLineEdit):
    """
    QLineEdit estilizado. Focus anima el color del borde border→border_focus en 200ms.
    """

    def __init__(self, placeholder: str = "", parent=None, modo: str = None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._focus_glow: QGraphicsDropShadowEffect | None = None
        self.setPlaceholderText(placeholder)
        self.setFont(qfont("size_body"))
        self.setMinimumHeight(LAYOUT["min_touch_target"])
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._apply_base_style()

        _tm().theme_changed.connect(self._apply_theme)

    def _apply_base_style(self):
        c = colors(self._modo)
        r = RADIUS_INPUT
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1px solid {c.get('border_card', c['border'])};
                border-radius: {r}px;
                padding: 0 12px;
                font-size: {TYPOGRAPHY['size_body']}pt;
                selection-background-color: {c['accent']};
                selection-color: {c['text_on_accent']};
            }}
            QLineEdit:focus {{
                border: 2px solid {c['border_focus']};
            }}
            {focus_ring_stylesheet(self._modo)}
        """)

    def focusInEvent(self, event):
        """Enciende glow teal alrededor del input."""
        super().focusInEvent(event)
        is_dark = "dark" in self._modo
        if self._focus_glow is None:
            self._focus_glow = QGraphicsDropShadowEffect(self)
        self._focus_glow.setBlurRadius(16 if is_dark else 12)
        self._focus_glow.setOffset(0, 0)
        gc = v3c("teal", self._modo)
        gc.setAlpha(120 if is_dark else 70)
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
        self._shimmer_pos = 0.0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(16)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _tm().theme_changed.connect(self._apply_theme)

    def _tick_shimmer(self):
        if self._value <= 0 or not self.isVisible():
            self._sync_shimmer_timer()
            return
        self._shimmer_pos = (self._shimmer_pos + 0.015) % 1.2
        self.update()

    def _sync_shimmer_timer(self):
        should_run = self._value > 0 and self.isVisible()
        if should_run and not self._shimmer_timer.isActive():
            self._shimmer_timer.start()
        elif not should_run and self._shimmer_timer.isActive():
            self._shimmer_timer.stop()

    # value como pyqtProperty para QPropertyAnimation
    def _get_value(self) -> float:
        return self._value

    def _set_value(self, v: float):
        self._value = max(0.0, min(1.0, v))
        if self._value <= 0:
            self._shimmer_pos = 0.0
        self._sync_shimmer_timer()
        self.update()

    value = pyqtProperty(float, _get_value, _set_value)

    def animate_to(self, target: float, duration: int = 400):
        a = QPropertyAnimation(self, b"value", self)
        a.setDuration(duration)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.setEndValue(target)
        a.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

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

        # Fill gradiente
        fill_w = w * self._value
        if fill_w > 0:
            fill_rect = QRectF(0, 0, fill_w, h)
            grad = linear_gradient(fill_rect, self._modo, angle=0)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(fill_rect, r, r)

            if fill_w > 4:
                shimmer_x = (self._shimmer_pos - 0.2) * fill_w
                shimmer_w = fill_w * 0.3
                sh_grad = QLinearGradient(shimmer_x, 0, shimmer_x + shimmer_w, 0)
                sh_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
                sh_grad.setColorAt(0.5, QColor(255, 255, 255, 45))
                sh_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(QBrush(sh_grad))
                p.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(fill_rect, r, r)
                p.setClipPath(clip_path)
                p.drawRoundedRect(QRectF(max(0, shimmer_x), 0, shimmer_w, h), r, r)
                p.restore()

        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_shimmer_timer()

    def hideEvent(self, event):
        self._sync_shimmer_timer()
        super().hideEvent(event)


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
            # v3: gradient firma teal→violet + glow shadow
            glow_r = r + 2
            glow_rect = QRectF(-2, -2, self._track_w + 4, self._track_h + 4)
            glow_col = v3c("teal", self._modo)
            glow_col.setAlpha(60)
            p.setBrush(QBrush(glow_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(glow_rect, glow_r, glow_r)

            grad = v3_linear_gradient(track_rect, self._modo, 0, "signature")
            p.setBrush(QBrush(grad))
        else:
            # Inactivo: text4 en light (#cbd5e1 — spec JSX), borderSolid en dark
            track_col = v3c("text4", self._modo) if not is_dark \
                else v3c("borderSolid", self._modo)
            p.setBrush(QBrush(track_col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(track_rect, r, r)

        # Thumb (knob blanco) — sombra suave solo cuando activo (v3 spec)
        ty = self._track_h / 2
        if self.isChecked():
            shadow_col = QColor(0, 0, 0, 50)
            p.setBrush(QBrush(shadow_col))
            p.drawEllipse(QPointF(self._thumb_x, ty + 1),
                          self._thumb_r, self._thumb_r)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(self._thumb_x, ty),
                      self._thumb_r, self._thumb_r)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMToast ───────────────────────────────────────────────────────────────────

class NMToast(QWidget):
    """
    Notificación flotante en esquina inferior derecha. Slide + fade in/out.
    Variantes: 'success', 'error', 'info', 'warning'.
    Se muestra sobre todos los demás widgets (Qt.WindowType.ToolTip).
    """

    _VARIANT_COLORS = {
        "success": "#10b981",
        "error":   "#ef4444",
        "info":    "#6366f1",
        "warning": "#f59e0b",
    }

    def __init__(self, parent_window: QWidget, message: str,
                 variant: str = "info", duration_ms: int = 2500):
        super().__init__(parent_window, Qt.WindowType.ToolTip)
        self._parent_win = parent_window
        self._variant = variant
        self._message = message
        self._duration = duration_ms
        self._color = self._VARIANT_COLORS.get(variant, self._VARIANT_COLORS["info"])

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._setup_ui()
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Indicador de color
        dot = QWidget()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background: {self._color}; border-radius: 4px;"
        )
        layout.addWidget(dot)

        lbl = QLabel(self._message)
        lbl.setFont(qfont("size_body"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {C('text_on_accent', 'dark_hybrid')}; background: transparent;")
        layout.addWidget(lbl)

        self.setStyleSheet(f"""
            NMToast {{
                background-color: rgba(30, 41, 59, 235);
                border-radius: 12px;
                border: 1px solid {self._color};
            }}
        """)
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)
        self.adjustSize()

    def show_toast(self):
        if not self._parent_win:
            return
        self._reposition()
        super().show()   # QWidget.show() — evita recursión con classmethod show()
        self.raise_()

        # Fade in
        anim_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        # Auto-dismiss
        QTimer.singleShot(
            self._duration,
            lambda: self._dismiss() if not sip.isdeleted(self) else None,
        )

    def _dismiss(self):
        anim_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim_out.setDuration(200)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        anim_out.finished.connect(self.close)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _reposition(self):
        pw = self._parent_win
        margin = 20
        anchor = pw
        central_getter = getattr(pw, "centralWidget", None)
        if callable(central_getter):
            central = central_getter()
            if central is not None:
                anchor = central
        top_left = anchor.mapToGlobal(anchor.rect().topLeft())
        x = top_left.x() + anchor.width() - self.width() - margin
        y = top_left.y() + anchor.height() - self.height() - margin
        self.move(x, y)

    @classmethod
    def display(cls, parent_window: QWidget, message: str,
                variant: str = "info", duration_ms: int = 2500):
        """Factory: crea y muestra un toast de una línea."""
        toast = cls(parent_window, message, variant, duration_ms)
        toast.show_toast()
        return toast



# ── NMSidebar ─────────────────────────────────────────────────────────────────

class _SidebarItem(QWidget):
    """Ítem individual del sidebar."""
    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, icon: str | QIcon, label: str,
                 parent=None, modo: str = "dark_hybrid"):
        super().__init__(parent)
        self._id = item_id
        self._icon = icon
        self._icon_pixmap = icon.pixmap(20, 20) if isinstance(icon, QIcon) else None
        self._label = label
        self._modo = norm_modo(modo)
        self._active = False
        self._hover = False
        self._hover_alpha = 0.0
        self._bar_anim_val = 0.0   # 0.0→1.0 para la barra izquierda

        self.setFixedHeight(44)
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
        c = colors(self._modo)
        w, h = self.width(), self.height()
        r = RADIUS_BUTTON

        # Fondo hover/active con glow sutil
        if self._active:
            bg = QColor(C("accent", self._modo))
            bg.setAlpha(18)
        elif self._hover:
            bg = QColor(c["bg_elevated"])
            bg.setAlpha(int(120 * self._hover_alpha))
        else:
            bg = QColor(0, 0, 0, 0)

        if bg.alpha() > 0:
            path = QPainterPath()
            path.addRoundedRect(QRectF(4, 2, w - 8, h - 4), r, r)
            p.fillPath(path, QBrush(bg))

        if self.hasFocus():
            focus_pen = QPen(QColor(C("accent", self._modo)), 2)
            p.setPen(focus_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(5, 3, w - 10, h - 6), r, r)

        # Barra izquierda animada (3px)
        if self._bar_anim_val > 0:
            bar_h = int((h - 8) * self._bar_anim_val)
            bar_y = (h - bar_h) // 2
            bar_path = QPainterPath()
            bar_path.addRoundedRect(QRectF(0, bar_y, 3, bar_h), 2, 2)
            p.fillPath(bar_path, QBrush(QColor(C("accent", self._modo))))

        # Icono + texto
        text_color = QColor(c["text_primary"] if (self._active or self._hover)
                            else c["text_secondary"])
        p.setPen(QPen(text_color))

        icon_rect = QRect(14, 0, 28, h)
        if self._icon_pixmap is not None:
            x = icon_rect.x() + (icon_rect.width() - self._icon_pixmap.width()) // 2
            y = icon_rect.y() + (icon_rect.height() - self._icon_pixmap.height()) // 2
            p.drawPixmap(x, y, self._icon_pixmap)
        else:
            font_icon = qfont("size_body")
            font_icon.setFamily("Segoe UI Emoji")
            p.setFont(font_icon)
            p.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self._icon)

        font_label = qfont("size_small", bold=self._active)
        p.setFont(font_label)
        label_rect = QRect(44, 0, w - 48, h)
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

        self.setFixedWidth(220)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_bg(self):
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["sidebar_bg"]))
        p.end()
        super().paintEvent(event)

    def add_header(self, title: str, subtitle: str = ""):
        """Añade sección de título/logo al tope del sidebar."""
        c = colors(self._modo)
        w = QWidget()
        w.setObjectName("SidebarHeader")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 16, 16, 8)
        vl.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setFont(qfont("size_small", bold=True))
        lbl_title.setStyleSheet(label_style(self._modo, 'accent'))
        self._theme_labels.append((lbl_title, "accent"))
        vl.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setFont(qfont("size_caption"))
            lbl_sub.setStyleSheet(label_style(self._modo, 'text_tertiary'))
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
                icon_name = "logos-icon-light.png" if "light" in self._modo else "logos-icon-dark.png"
                path = obtener_ruta_recurso(icon_name)
                if not os.path.exists(path):
                    path = obtener_ruta_recurso("LOGO.png")
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    168, 36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logo_lbl.setPixmap(pm)
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
        c = colors(self._modo)
        sep.setStyleSheet(f"background: {c.get('border_card', c['border'])};")
        self._layout.addWidget(sep)

    def add_spacer(self):
        from PyQt6.QtWidgets import QSpacerItem
        self._layout.addStretch()

    def add_label(self, text: str):
        c = colors(self._modo)
        lbl = QLabel(text)
        lbl.setFont(qfont("size_caption"))
        lbl.setWordWrap(True)
        lbl.setContentsMargins(14, 4, 14, 4)
        lbl.setStyleSheet(label_style(self._modo, 'text_tertiary'))
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
        c = colors(self._modo)
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
        # Recolorear logo en light mode
        if self._logo_lbl is not None:
            try:
                path = obtener_ruta_recurso("LOGO.png")
                if os.path.exists(path):
                    pm = QPixmap(path)
                    if "light" in self._modo:
                        from PIL import Image as PILImage
                        img = PILImage.open(path).convert("RGBA")
                        img = recolorear_logo_light(img)
                        data = img.tobytes("raw", "RGBA")
                        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                        pm = QPixmap.fromImage(qimg)
                    self._logo_lbl.setPixmap(pm.scaled(
                        168, 36,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
            except Exception:
                pass
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and w.minimumHeight() == 1 and w.maximumHeight() == 1:
                w.setStyleSheet(f"background: {c.get('border_card', c['border'])};")


# ── NMHeader ──────────────────────────────────────────────────────────────────

class NMHeader(QWidget):
    """
    Header de 56px con logo NeuroMood, nombre de usuario
    y toggle dark/light. Emite theme_toggle() al hacer click en el toggle.

    Modos:
      - Normal (default): logo + username + theme toggle
      - show_back=True: boton volver + icono + titulo de modulo
      - home_mode=True: greeting + subtitle + streak badge + theme toggle
    """
    theme_toggle = pyqtSignal()

    def __init__(self, parent=None, modo: str = None,
                 username: str = "", show_back: bool = False,
                 module_title: str = "", module_icon: str = "",
                 home_mode: bool = False, greeting: str = "",
                 subtitle: str = "", streak: int = 0):
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

        self.setFixedHeight(HEADER_H)
        self._setup_ui()
        self._apply_bg()
        _tm().theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp("md"), 0, sp("md"), 0)
        layout.setSpacing(sp("sm"))

        c = colors(self._modo)

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
            title_lbl.setStyleSheet(label_style(self._modo, 'text_primary'))
            self._module_title_lbl = title_lbl
            layout.addWidget(title_lbl)
        else:
            if self._home_mode:
                # Home mode: greeting + subtitle + streak
                left_col = QVBoxLayout()
                left_col.setSpacing(2)
                greet_lbl = QLabel(self._greeting)
                greet_lbl.setFont(qfont("size_h1", bold=True))
                greet_lbl.setStyleSheet(label_style(self._modo, 'text_primary'))
                self._greet_lbl = greet_lbl
                left_col.addWidget(greet_lbl)
                sub_lbl = QLabel(self._subtitle_text)
                sub_lbl.setFont(qfont("size_small"))
                sub_lbl.setStyleSheet(label_style(self._modo, 'text_tertiary'))
                self._sub_lbl = sub_lbl
                left_col.addWidget(sub_lbl)
                layout.addLayout(left_col, stretch=1)
                layout.addSpacing(sp("md"))

                if self._streak > 0:
                    self._streak_badge = NMStreakBadge(self._streak, self._modo)
                    layout.addWidget(self._streak_badge)
            else:
                # Normal home: logo NeuroMood
                self._logo_widget = _LogoLabel(self)
                self._logo_widget.set_modo(self._modo)
                layout.addWidget(self._logo_widget)

                if self._username:
                    user_lbl = QLabel(f"Hola, {self._username}")
                    user_lbl.setFont(qfont("size_small"))
                    user_lbl.setStyleSheet(label_style(self._modo, 'text_tertiary'))
                    self._user_lbl = user_lbl
                    layout.addWidget(user_lbl)

        layout.addStretch()

        self._theme_lbl = QLabel(self._theme_label_text())
        self._theme_lbl.setFont(qfont("size_caption"))
        self._theme_lbl.setStyleSheet(label_style(self._modo, "text_secondary"))
        layout.addWidget(self._theme_lbl)

        # Toggle dark/light
        self._toggle = NMToggle(self, self._modo)
        self._toggle.setChecked("light" in self._modo)
        self._toggle.toggled.connect(lambda _: self.theme_toggle.emit())
        layout.addWidget(self._toggle)

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
        if hasattr(self, "_context_badge_lbl"):
            self._context_badge_lbl.hide()

    def set_context_badge(self, text: str = "", color_key: str = "teal"):
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
        c = colors(self._modo)
        p.fillRect(self.rect(), QColor(c["bg_surface"]))
        p.setPen(QPen(QColor(c.get("border_card", c["border"])), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()
        super().paintEvent(event)

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
            f"font-size: 11pt; "
            f"font-weight: 600; "
            f"}} "
            f"QPushButton:hover {{ "
            f"background-color: {c['bg_elevated']}; "
            f"color: {C('text_secondary', self._modo)}; "
            f"}}"
        )

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_bg()
        if hasattr(self, "_logo_widget"):
            self._logo_widget.set_modo(modo)
        if hasattr(self, "_user_lbl"):
            self._user_lbl.setStyleSheet(label_style(modo, 'text_tertiary'))
        if hasattr(self, "_btn_back"):
            self._apply_back_btn_style()
        if hasattr(self, "_module_title_lbl"):
            self._module_title_lbl.setStyleSheet(label_style(modo, 'text_primary'))
        self._apply_module_icon()
        if hasattr(self, "_theme_lbl"):
            self._theme_lbl.setText(self._theme_label_text())
            self._theme_lbl.setStyleSheet(label_style(modo, "text_secondary"))
        self._apply_context_badge_style()
        self._toggle._apply_theme(modo)
        was_blocked = self._toggle.blockSignals(True)
        self._toggle.setChecked("light" in modo)
        self._toggle.blockSignals(was_blocked)

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

        if self._pixmap and not self._pixmap.isNull():
            pm = self._get_pixmap()
            if pm and not pm.isNull():
                pm = pm.scaled(
                140, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - pm.width()) // 2
            y = (self.height() - pm.height()) // 2
            p.drawPixmap(x, y, pm)
        else:
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
    QStackedWidget con transición fade entre páginas.
    setCurrentWidget() override: fade-out/in en 200ms OutCubic.
    """

    def __init__(self, parent=None, duration: int = 200):
        super().__init__(parent)
        self._duration = duration
        self._animating = False
        self._snapshot: QLabel | None = None

    def setCurrentWidget(self, widget: QWidget):
        if widget is self.currentWidget():
            return
        if self._animating:
            return
        self._fade_to(widget)

    def _fade_to(self, target: QWidget):
        self._animating = True
        current = self.currentWidget()

        # Captura snapshot del widget actual
        if current:
            px = current.grab()
            snap = QLabel(self)
            snap.setPixmap(px)
            snap.setGeometry(0, 0, self.width(), self.height())
            snap.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            snap.show()
            snap.raise_()
            self._snapshot = snap

            # Fade out snapshot
            eff = QGraphicsOpacityEffect(snap)
            snap.setGraphicsEffect(eff)

            fade_out = QPropertyAnimation(eff, b"opacity", self)
            fade_out.setDuration(self._duration)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _on_out_done():
                snap.deleteLater()
                self._snapshot = None
                self._animating = False

            fade_out.finished.connect(_on_out_done)

            # Mostrar target mientras sale el snapshot
            super().setCurrentWidget(target)
            fade_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        else:
            super().setCurrentWidget(target)
            self._animating = False

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

    def __init__(self, parent=None, width=200, height=16,
                 radius=8, modo=None):
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
                self, modo=self._modo,
                show_back=True,
                module_title=self.MODULE_TITLE,
                module_icon=self.MODULE_ICON,
            )
            self._header.set_back_callback(self.back_requested.emit)
            self._root_layout.addWidget(self._header)

        # Contenido del modulo (build_ui lo llena) con centrado premium
        self._content = QWidget()
        self._content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
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
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Gradiente radial desde centro-izquierda hacia los bordes
        grad = QRadialGradient(w * 0.2, h * 0.5, w * 0.85)
        grad.setColorAt(0, self._session.aura_qcolor(self._modo))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRect(self.rect())
        p.end()

    @property
    def modo(self) -> str:
        return self._modo

    def build_ui(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} debe implementar build_ui()"
        )

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

    def __init__(self, text: str = "", color_key: str = "success",
                 modo: str = "dark_hybrid", parent=None):
        super().__init__(text, parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._color_key = color_key
        self.setFont(qfont("size_caption"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(22)
        self._apply_style()
        _tm().theme_changed.connect(self._apply_theme)

    def _apply_style(self):
        c = colors(self._modo)
        color = C(self._color_key, self._modo)
        self.setStyleSheet(f"""
            NMStatusChip {{
                color: {color};
                background-color: transparent;
                border: 1px solid {color};
                border-radius: {RADIUS_PILL // 2}px;
                padding: 2px 10px;
            }}
        """)

    def set_color(self, color_key: str):
        self._color_key = color_key
        self._apply_style()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._apply_style()


# ── NMSectionCard ─────────────────────────────────────────────────────────────

class NMSectionCard(QFrame):
    """Card con título decorativo. content_widget() devuelve el área para widgets."""

    def __init__(self, title: str = "", icon: str = "",
                 modo: str = "dark_hybrid", parent=None):
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
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
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
                background-color: {c['bg_surface']};
                border-radius: {RADIUS_CARD}px;
                border: 1px solid {c.get('border_card', c['border'])};
            }}
        """)


# ── NMFormField ────────────────────────────────────────────────────────────────

class NMFormField(QWidget):
    """Label + input en fila horizontal, con espaciado consistente."""

    def __init__(self, label: str = "", widget: QWidget = None,
                 modo: str = "dark_hybrid", parent=None):
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


def responsive_columns(available_width: int, min_card_width: int = 280,
                       max_columns: int = 3) -> int:
    """Devuelve el número óptimo de columnas según ancho disponible."""
    cols = max(1, min(max_columns, available_width // min_card_width))
    return cols


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


def _paint_v3_arc(p: QPainter, rect: QRectF,
                  start_angle_deg: float, span_deg: float,
                  pen_width: int, modo: str,
                  segments: int = 64):
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
        color_key: clave de la paleta v3 (``'text'``, ``'text2'``, ``'text3'``,
                   ``'teal'``, ``'violet'``, ``'danger'``…). Si se pasa, el
                   icono se re-renderiza automáticamente en cada theme change
                   y ``color`` se ignora.
        modo:      override de tema (None = sigue ThemeManager).

    Si el nombre no está en el catálogo v3, cae a QtAwesome vía
    :func:`shared.theme_qt.nm_icon` (compat durante migración).
    """

    def __init__(self, name: str, size: int = 24,
                 color: str | None = None, color_key: str | None = None,
                 modo: str = None, parent=None):
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

    def __init__(self, level: int = 5, size: int = 64,
                 glow: bool = True, modo: str = None, parent=None):
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
        pix = _nm_mood_pixmap(self._level, self._size,
                              glow=self._glow, is_dark=is_dark)
        if pix is not None and not pix.isNull():
            self.setPixmap(pix)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._render()


# ── NMSegmentedChoice ─────────────────────────────────────────────────────────

class NMSegmentedChoice(QWidget):
    """Grupo de NMButtonOutline con selección exclusiva. Emite choice_made(str)."""
    choice_made = pyqtSignal(str)

    def __init__(self, choices: list[tuple[str, str]], modo: str = "dark_hybrid",
                 parent=None):
        """
        choices: lista de (label, value). Ej: [("Hecha", "hecha"), ("No pude", "no_pude")]
        """
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._btns: dict[str, NMButtonOutline] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for label, value in choices:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=True)
            btn.setFixedHeight(30)
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

class NMCustomCheck(QWidget):
    """Checklist row matching the HTML `.check-item` / `.cbox` pattern."""
    toggled = pyqtSignal(bool)

    def __init__(self, text: str, checked: bool = False,
                 modo: str = None, parent=None, strike_on_check: bool = True):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._checked = checked
        self._strike_on_check = strike_on_check
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(10)
        self._box = QLabel()
        self._box.setFixedSize(18, 18)
        self._box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._box.setFont(qfont("size_caption", bold=True))
        lay.addWidget(self._box)
        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_checked(self, checked: bool):
        self._checked = checked
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
            self._apply_theme(self._modo)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = C("teal", self._modo) if self._checked else c.get("border_card", c["border"])
        bg = C("teal", self._modo) if self._checked else "transparent"
        self._box.setText("\u2713" if self._checked else "")
        self._box.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {C('text_on_accent', self._modo)}; "
            f"border: 2px solid {border}; border-radius: 5px; }}"
        )
        decoration = "line-through" if self._checked and self._strike_on_check else "none"
        self._label.setStyleSheet(
            f"color: {C('text_secondary', self._modo)}; background: transparent; "
            f"text-decoration: {decoration};"
        )


class NMActivityCard(QFrame):
    """Card de actividad con barra izquierda y acciones exclusivas."""
    completed = pyqtSignal()
    skipped = pyqtSignal()

    def __init__(self, title: str, description: str, category: str = "Autocuidado",
                 completed: bool = False, modo: str = None, parent=None):
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
            f"font-size: {TYPOGRAPHY['size_caption']}pt; font-weight: bold; }}"
        )
        self._no_btn.setVisible(not self._completed)
        self._no_btn.setStyleSheet(
            f"QPushButton {{ background: {c['bg_elevated']}; color: {c['text_tertiary']}; "
            f"border: none; border-radius: 8px; padding: 4px 12px; "
            f"font-size: {TYPOGRAPHY['size_caption']}pt; font-weight: bold; }}"
        )
        self.update()


class NMPresetChip(QPushButton):
    """Chip de preset del timer."""
    def __init__(self, text: str, active: bool = False,
                 modo: str = None, parent=None):
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
        c = colors(self._modo)
        if self._active:
            bg = _rgba(C("teal", self._modo), 0.12)
            border = _rgba(C("teal", self._modo), 0.30)
            col = C("teal", self._modo)
        else:
            bg = "transparent"
            border = c.get("border_card", c["border"])
            col = c["text_tertiary"]
        self.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {col}; border: 1px solid {border}; "
            f"border-radius: {RADIUS_PILL}px; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {c['bg_elevated']}; color: {c['text_secondary']}; }}"
        )


class NMFocusArc(QWidget):
    """Arco circular de foco con aura y texto central."""
    def __init__(self, size: int = 160, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct = 0.0
        self._time_text = "25:00"
        self._state_text = "listo"
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_data(self, pct: float, time_text: str, state_text: str = "listo"):
        self._pct = max(0.0, min(1.0, pct))
        self._time_text = time_text
        self._state_text = state_text
        self.update()

    def update_data(self, progress: float, time_text: str):
        self.set_data(progress, time_text, self._state_text)

    def start_pulse(self):
        self._state_text = "en curso"
        self.update()

    def stop_pulse(self):
        self._state_text = "pausado"
        self.update()

    def start_blink(self):
        self.update()

    def stop_blink(self):
        self.update()

    def show_finish(self):
        self.set_data(1.0, "00:00", "terminado")

    def reset(self):
        self.set_data(0.0, self._time_text, "listo")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        cx = cy = w / 2

        # Aura radial teal v3
        aura = QRadialGradient(QPointF(cx, cy), w * 0.42)
        ac = v3c("teal", self._modo)
        ac.setAlphaF(0.18 if "dark" in self._modo else 0.12)
        aura.setColorAt(0.0, ac)
        aura.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(aura)
        p.drawEllipse(QPointF(cx, cy), w * 0.38, w * 0.38)

        # Track + arco progreso con gradient v3 teal→violet
        pen_w = _ring_stroke(w)
        r = w / 2 - pen_w - 1
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)

        # Track sutil
        track_col = v3c("borderSoft", self._modo)
        p.setPen(QPen(track_col, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Arco progreso (CW desde 90° = top)
        if self._pct > 0.001:
            # Glow blur detrás del arco — teal+violet en dark, teal en light
            is_dark = "dark" in self._modo
            glow_w = pen_w + 6
            glow_r_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
            glow_col = v3c("teal", self._modo)
            glow_col.setAlpha(40 if is_dark else 28)
            p.setPen(QPen(glow_col, glow_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(glow_r_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            if is_dark:
                glow_col2 = v3c("violet", self._modo)
                glow_col2.setAlpha(25)
                p.setPen(QPen(glow_col2, glow_w - 2,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
                p.drawArc(glow_r_rect, int(90 * 16), int(-360.0 * self._pct * 16))
            _paint_v3_arc(p, rect, 90.0, -360.0 * self._pct, pen_w, self._modo)

        # Textos: tiempo (mono) + estado
        time_pt = max(16, int(w * 0.15))
        state_pt = max(10, int(w * 0.075))
        p.setPen(v3c("text", self._modo))
        p.setFont(qfont_mono(time_pt, bold=False))
        p.drawText(QRectF(0, cy - time_pt, w, time_pt + 8),
                   Qt.AlignmentFlag.AlignCenter, self._time_text)
        p.setPen(v3c("text3", self._modo))
        p.setFont(qfont("size_caption"))
        p.drawText(QRectF(0, cy + 6, w, state_pt + 10),
                   Qt.AlignmentFlag.AlignCenter, self._state_text)
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
            f"border-radius: 12px; padding: 4px 11px; }}"
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
    def __init__(self, total: int = 1, current: int = 0,
                 modo: str = None, parent=None):
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
        track = QColor(C("progress_track", self._modo))
        p.fillRect(0, 0, w, h, track)
        if fill_w > 0:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0.0, QColor(C("teal", self._modo)))
            grad.setColorAt(1.0, QColor(C("violet", self._modo)))
            p.fillRect(0, 0, fill_w, h, grad)
        p.end()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()


# ── NMStreakBadge ─────────────────────────────────────────────────────────────

class NMStreakBadge(QLabel):
    """Pill badge de racha diaria: '🔥 N días activo'.

    Usa streak_color / streak_bg del Design System v3.
    Se oculta automáticamente si days <= 0.
    """
    def __init__(self, days: int = 0, modo: str = None, parent=None):
        super().__init__(parent)
        self._days = days
        self._modo = norm_modo(modo or _tm().modo)
        self.setFixedHeight(28)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(12, 0, 12, 0)
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
            self.setText(f"\U0001f525 {self._days} día{suffix} activo")
            self.show()

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        color = C("streak_color", self._modo)
        bg = C("streak_bg", self._modo)
        r = RADIUS_PILL
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border-radius: {r}px;
                padding: 2px 12px;
                font-size: {TYPOGRAPHY['size_small']}pt;
                font-weight: bold;
            }}
        """)


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
        self._sub_lbl.setStyleSheet(f"color: {C('text_tertiary', self._modo)}; background: transparent;")
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
        ("\U0001f615", "Bajo",      3),
        ("\U0001f610", "Neutro",    5),
        ("\U0001f642", "Bien",      7),
        ("\U0001f604", "Excelente", 9),
    ]

    _BTN_SIZE = 48

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo     = norm_modo(modo or _tm().modo)
        self._selected: int | None = None
        self._btns:   list[QPushButton] = []
        self._labels: list[QLabel]      = []
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
        teal   = C("teal",          self._modo)
        border = C("border",        self._modo)
        bg_el  = C("bg_elevated",   self._modo)
        bg_ov  = C("bg_overlay",    self._modo)
        txt_s  = C("text_secondary", self._modo)
        r      = self._BTN_SIZE // 2

        for i, (btn, lbl) in enumerate(zip(self._btns, self._labels)):
            is_sel = (i == self._selected)
            if is_sel:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: 2px solid {teal};
                        border-radius: {r}px;
                        font-size: 22pt;
                    }}
                    QPushButton:hover {{ background: {bg_ov}; }}
                """)
                lbl.setStyleSheet(
                    f"color: {teal}; font-weight: bold; font-size: {TYPOGRAPHY['size_caption']}pt;"
                )
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {bg_el};
                        border: 1px solid {border};
                        border-radius: {r}px;
                        font-size: 20pt;
                    }}
                    QPushButton:hover {{
                        background: {bg_ov};
                        border-color: {teal};
                    }}
                """)
                lbl.setStyleSheet(
                    f"color: {txt_s}; font-size: {TYPOGRAPHY['size_caption']}pt;"
                )


# ── NMWaveChart ───────────────────────────────────────────────────────────────

class NMWaveChart(QWidget):
    """Gráfico de área dual-serie para el módulo Ánimo.

    Serie teal = semana actual. Serie violet (semitransparente) = semana anterior.
    Emite week_changed(int) con offset de semana (0=actual, -1=anterior…).
    """
    week_changed = pyqtSignal(int)

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._data_current:  list[float | None] = [None] * 7
        self._data_previous: list[float | None] = [None] * 7
        self._week_offset = 0
        self._hover_idx   = -1
        self._labels = ["L", "M", "M", "J", "V", "S", "D"]

        self.setMinimumHeight(140)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        _tm().theme_changed.connect(self._apply_theme)

    def set_data(self, current: list, previous: list):
        self._data_current  = list(current[:7])
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
        idx  = round((event.pos().x() - ml) / step)
        idx  = max(0, min(n - 1, idx))
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
        c  = colors(self._modo)
        ml, mr = 32, 16
        mt, mb = 12, 28
        cw = w - ml - mr
        ch = h - mt - mb

        teal_hex   = C("teal",   self._modo)
        violet_hex = C("violet", self._modo)

        # Faint grid
        for row in range(1, 5):
            y_grid = mt + ch - (ch * row / 4)
            gc = QColor(c["border"])
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
            poly_pts  = [QPointF(pts[0].x(), bottom_y)]
            poly_pts += pts
            poly_pts.append(QPointF(pts[-1].x(), bottom_y))
            poly = QPolygonF(poly_pts)
            path = QPainterPath()
            path.addPolygon(poly)
            fill_grad = QLinearGradient(0, mt, 0, mt + ch)
            fc = QColor(color_hex); fc.setAlpha(alpha_fill)
            ec = QColor(color_hex); ec.setAlpha(0)
            fill_grad.setColorAt(0.0, fc)
            fill_grad.setColorAt(1.0, ec)
            p.fillPath(path, QBrush(fill_grad))
            lc = QColor(color_hex); lc.setAlpha(alpha_line)
            p.setPen(QPen(lc, 2.0))
            p.setBrush(Qt.BrushStyle.NoBrush)
            line_path = QPainterPath()
            line_path.moveTo(pts[0])
            for pt in pts[1:]:
                line_path.lineTo(pt)
            p.drawPath(line_path)

        is_dark = "dark" in self._modo
        prev_pts = _pts(self._data_previous)
        _draw_area(prev_pts, violet_hex,
                   alpha_fill=31 if is_dark else 26, alpha_line=90)

        curr_pts = _pts(self._data_current)
        _draw_area(curr_pts, teal_hex,
                   alpha_fill=64 if is_dark else 46, alpha_line=210)

        # Dots
        p.setBrush(QBrush(QColor(teal_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        for i, pt in enumerate(curr_pts):
            r = 5 if i == self._hover_idx else 3
            p.drawEllipse(pt, r, r)

        # Hover tooltip
        if 0 <= self._hover_idx < len(self._data_current):
            val = self._data_current[self._hover_idx]
            if val is not None and self._hover_idx < len(curr_pts):
                pt = curr_pts[self._hover_idx]
                is_today = self._hover_idx == len(self._data_current) - 1
                tip_text = f"Hoy: {val:.0f}" if is_today else f"{val:.0f}/10"
                tw, th = 60, 22
                tx = min(pt.x() - tw / 2, w - mr - tw)
                ty = max(float(mt), pt.y() - th - 8)
                tip_bg = QColor(c["bg_elevated"]); tip_bg.setAlpha(220)
                tip_r  = QRectF(tx, ty, tw, th)
                tip_path = QPainterPath()
                tip_path.addRoundedRect(tip_r, RADIUS_SMALL, RADIUS_SMALL)
                p.fillPath(tip_path, tip_bg)
                p.setPen(QColor(c["text_primary"]))
                p.setFont(qfont("size_small"))
                p.drawText(tip_r, Qt.AlignmentFlag.AlignCenter, tip_text)

        # Day labels
        p.setPen(QColor(c["text_tertiary"]))
        p.setFont(qfont("size_caption"))
        n = len(self._labels)
        for i, lbl in enumerate(self._labels):
            x = ml + (i / max(1, n - 1)) * cw
            p.drawText(QRectF(x - 12, h - mb + 4, 24, 14),
                       Qt.AlignmentFlag.AlignCenter, lbl)

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
        ("Mantén 7s",    "manten"),
        ("Exhala ↓ 8s",  "exhala"),
    ]

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo   = norm_modo(modo or _tm().modo)
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
            active = (key == self._active)
            phase_color = C(self._PHASE_COLOR_KEY.get(key, "teal"), self._modo)
            if active:
                bg     = phase_color
                col    = C("text_on_accent", self._modo)
                border = phase_color
            else:
                # Estado preview: tint suave del color de fase + texto del color
                bg     = _rgba(phase_color, 0.12)
                col    = phase_color
                border = _rgba(phase_color, 0.25)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_BUTTON}px;
                    font-size: {TYPOGRAPHY['size_small']}pt;
                    font-weight: {'bold' if active else 'normal'};
                }}
            """)


# ── NMCycleRing ───────────────────────────────────────────────────────────────

class NMCycleRing(QWidget):
    """Anillo de trazo pequeño con contador de ciclos de respiración.

    Columna izquierda del módulo Respiración.
    """
    def __init__(self, size: int = 56, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo   = norm_modo(modo or _tm().modo)
        self._cycles = 0
        self._size   = size
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
        s  = self._size
        cx, cy = s / 2, s / 2
        pen_w = _ring_stroke(s)
        r_out = s / 2 - pen_w - 1
        rect = QRectF(cx - r_out, cy - r_out, r_out * 2, r_out * 2)

        # Contorno completo con gradient firma v3 (no es progreso — siempre 360°)
        _paint_v3_arc(p, rect, 90.0, -359.99, pen_w, self._modo, segments=80)

        p.setPen(v3c("text", self._modo))
        p.setFont(qfont_mono(max(10, int(s * 0.22)),
                             bold=False))
        # Peso semibold sin usar bold flag: usar v3_font sería ideal pero qfont_mono no
        # acepta weight; pintamos directo con la familia mono y dejamos bold=False
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter,
                   str(self._cycles))
        p.restore()
        p.end()


# ── NMCalmBadge ───────────────────────────────────────────────────────────────

class NMCalmBadge(QWidget):
    """Badge decorativo 'Calm ♥ / N BPM' para la columna derecha de Respiración."""

    def __init__(self, bpm: int = 60, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._bpm  = bpm
        self._blink_alpha = 255
        self._blink_dir   = -1
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
        self._calm_lbl.setFont(qfont("size_small", bold=True))
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
            f"QWidget#NMCalmBadge {{ background: {C('bg_elevated', self._modo)}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {C('border', self._modo)}; }}"
            f"QWidget#NMCalmBadge QLabel {{ background: transparent; border: none; }}"
        )
        self._calm_lbl.setStyleSheet(f"color: {violet};")
        self._bpm_lbl.setStyleSheet(f"color: {violet};")
        self._unit_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))

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


# ── NMTCCStepper ──────────────────────────────────────────────────────────────

class NMTCCStepper(QWidget):
    """Stepper horizontal de N pasos para el asistente TCC (y cualquier wizard).

    Estado por paso: pasado=verde+check, activo=accent, futuro=gris.
    """
    def __init__(self, steps: list[str], modo: str = None, parent=None):
        super().__init__(parent)
        self._modo    = norm_modo(modo or _tm().modo)
        self._steps   = steps
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

        w, h   = self.width(), self.height()
        circle_r = 14
        cy       = 22
        step_w   = w / n

        for i, label in enumerate(self._steps):
            cx = int(step_w * i + step_w / 2)

            # Connector line
            if i > 0:
                prev_cx = int(step_w * (i - 1) + step_w / 2)
                lc = QColor(C("success" if i <= self._current else "border", self._modo))
                p.setPen(QPen(lc, 2))
                p.drawLine(prev_cx + circle_r, cy, cx - circle_r, cy)

            # Circle
            circ_rect = QRectF(cx - circle_r, cy - circle_r, circle_r * 2, circle_r * 2)
            if i < self._current:
                p.setBrush(QBrush(QColor(C("success", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
                p.setFont(qfont("size_small", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, "✓")
            elif i == self._current:
                p.setBrush(QBrush(QColor(C("accent", self._modo))))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_on_accent", self._modo)))
                p.setFont(qfont("size_small", bold=True))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))
            else:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(C("border", self._modo)), 2))
                p.drawEllipse(QPointF(cx, cy), circle_r, circle_r)
                p.setPen(QColor(C("text_tertiary", self._modo)))
                p.setFont(qfont("size_small"))
                p.drawText(circ_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

            # Label below circle
            col = "text_primary" if i == self._current else "text_tertiary"
            p.setPen(QColor(C(col, self._modo)))
            p.setFont(qfont("size_caption"))
            p.drawText(
                QRectF(cx - step_w / 2 + 4, cy + circle_r + 4, step_w - 8, 16),
                Qt.AlignmentFlag.AlignCenter, label,
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

    _COLD = "#3b82f6"
    _MID  = "#8b5cf6"
    _HOT  = "#ef4444"

    def __init__(self, value: int = 50, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo     = norm_modo(modo or _tm().modo)
        self._value    = max(0, min(100, value))
        self._dragging = False
        self.setFixedHeight(52)
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

    def _color_at(self, t: float) -> QColor:
        if t <= 0.5:
            return QColor(interpolate_color(self._COLD, self._MID, t * 2))
        return QColor(interpolate_color(self._MID, self._HOT, (t - 0.5) * 2))

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
        t      = max(0.0, min(1.0, (x - margin) / usable))
        new_v  = int(t * 100)
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

        w, h   = self.width(), self.height()
        margin = 16
        gh     = 8
        gy     = (h - gh) // 2 - 6
        gw     = w - margin * 2

        groove_rect = QRectF(margin, gy, gw, gh)
        grad = QLinearGradient(margin, 0, margin + gw, 0)
        grad.setColorAt(0.0, QColor(self._COLD))
        grad.setColorAt(0.5, QColor(self._MID))
        grad.setColorAt(1.0, QColor(self._HOT))
        path = QPainterPath()
        path.addRoundedRect(groove_rect, gh / 2, gh / 2)
        p.fillPath(path, grad)

        t   = self._value / 100.0
        hx  = margin + t * gw
        hc  = self._color_at(t)
        p.setPen(QPen(QColor(C("text_on_accent", self._modo)), 2))
        p.setBrush(QBrush(hc))
        p.drawEllipse(QPointF(hx, gy + gh / 2), 10, 10)

        p.setPen(QColor(C("text_secondary", self._modo)))
        p.setFont(qfont("size_caption"))
        p.drawText(QRectF(0, gy + gh + 12, w, 14),
                   Qt.AlignmentFlag.AlignCenter, f"{self._value}%")

        p.restore()
        p.end()


# ── NMRoutineSection ──────────────────────────────────────────────────────────

class NMRoutineSection(QWidget):
    """Sección colapsable de rutina con cabecera tintada de color semántico.

    section_type: 'morning' | 'afternoon' | 'night'
    Añadir ítems con content_layout().addWidget(…).
    """
    _TINTS = {
        "morning":   ("routine_morning_tint",   "☀️"),
        "afternoon": ("routine_afternoon_tint",  "\U0001f324"),
        "night":     ("routine_night_tint",      "\U0001f319"),
    }

    def __init__(self, section_type: str, title: str,
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo         = norm_modo(modo or _tm().modo)
        self._section_type = section_type
        self._collapsed    = False
        self.setObjectName("NMRoutineSection")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._main_lay = QVBoxLayout(self)
        self._main_lay.setContentsMargins(0, 0, 0, 0)
        self._main_lay.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setFixedHeight(44)
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
                fill_c = QColor(C("success", self._modo) if "success" in c else C("teal", self._modo))
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
        self._content.setStyleSheet(f"background: {_rgba('#000000', 0.01 if 'light' in self._modo else 0.02)};")


# ── NMDayNote ─────────────────────────────────────────────────────────────────

class NMDayNote(QWidget):
    """Card de nota del día con estado bloqueado/desbloqueado.

    Bloqueada: ícono de candado + razón de bloqueo.
    Desbloqueada: QTextEdit expandible.
    Emite note_changed(str).
    """
    note_changed = pyqtSignal(str)

    def __init__(self, locked: bool = True, lock_reason: str = "",
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo   = norm_modo(modo or _tm().modo)
        self._locked = locked
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

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
        lay.addLayout(row)

        self._locked_lbl = QLabel()
        self._locked_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._locked_lbl.setFont(qfont("size_small"))
        self._locked_lbl.setWordWrap(True)
        lay.addWidget(self._locked_lbl)

        self._textarea = QTextEdit()
        self._textarea.setPlaceholderText("Escribe tu reflexión del día...")
        self._textarea.setFixedHeight(90)
        self._textarea.textChanged.connect(
            lambda: self.note_changed.emit(self._textarea.toPlainText()))
        lay.addWidget(self._textarea)

        self.set_locked(locked, lock_reason)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_locked(self, locked: bool, reason: str = ""):
        self._locked = locked
        self._locked_lbl.setVisible(locked)
        self._textarea.setVisible(not locked)
        self._icon_lbl.setText("\U0001f512" if locked else "\U0001f4dd")
        if locked:
            self._locked_lbl.setText(reason or "Completa tu rutina del día para desbloquear")

    def set_note(self, text: str):
        self._textarea.blockSignals(True)
        self._textarea.setPlainText(text)
        self._textarea.blockSignals(False)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        border = _rgba(C("accent", self._modo), 0.20 if "light" in self._modo else 0.25)
        bg = _rgba(C("accent", self._modo), 0.04 if "light" in self._modo else 0.06)
        self.setStyleSheet(
            f"background: {bg}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {border};"
        )
        self._locked_lbl.setStyleSheet(label_style(self._modo, "text_tertiary"))
        self._textarea.setStyleSheet(
            f"QTextEdit {{ background: {c['bg_input']}; color: {c['text_primary']}; "
            f"border: 1px solid {c['border']}; border-radius: {RADIUS_INPUT}px; "
            f"padding: 6px 10px; font-size: {TYPOGRAPHY['size_body']}pt; }}"
        )


# ── NMMoodContextHeader ────────────────────────────────────────────────────────

class NMMoodContextHeader(QWidget):
    """Banner contextual: 'Basado en tu ánimo de hoy (N/10) EMOJI'.

    Se usa en la cabecera del módulo Actividades.
    """
    _SCORE_MAP = [
        (3,  "\U0001f61e"),  # <=2  muy bajo
        (5,  "\U0001f615"),  # 3-4  bajo
        (7,  "\U0001f610"),  # 5-6  neutro
        (9,  "\U0001f642"),  # 7-8  bien
        (11, "\U0001f604"),  # 9-10 excelente
    ]

    def __init__(self, score: int = 5, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo  = norm_modo(modo or _tm().modo)
        self._score = score
        self.setFixedHeight(44)
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
            f"background: {bg}; "
            f"border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {border};"
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
        self._modo     = norm_modo(modo or _tm().modo)
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
            is_sel     = (self._selected == cat) or (cat == "" and self._selected is None)
            cat_color  = CATEGORY_COLORS.get(cat, C("accent", self._modo)) if cat else C("accent", self._modo)
            bg     = _rgba(cat_color, 0.20 if is_sel else 0.14)
            border = _rgba(cat_color, 0.25)
            col    = cat_color if cat else C("text_secondary", self._modo)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {col};
                    border: 1px solid {border};
                    border-radius: {RADIUS_PILL}px;
                    padding: 3px 12px;
                    font-size: {TYPOGRAPHY['size_caption']}pt;
                    font-weight: bold;
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
    STATUS_ACTIVE  = "activo"
    STATUS_FIRED   = "disparado"
    STATUS_EXPIRED = "expirado"

    def __init__(self, time_str: str, message: str,
                 status: str = "activo", modo: str = None, parent=None):
        super().__init__(parent)
        self._modo   = norm_modo(modo or _tm().modo)
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
            self.STATUS_ACTIVE:  "● Activo",
            self.STATUS_FIRED:   "✓ Disparado",
            self.STATUS_EXPIRED: "○ Expirado",
        }
        self._pill.setText(labels.get(self._status, self._status))

    def _status_pill_colors(self) -> tuple[str, str]:
        if self._status == self.STATUS_ACTIVE:
            return C("teal",   self._modo), C("text_on_accent", self._modo)
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
            f"border-radius: 10px; font-size: {TYPOGRAPHY['size_caption']}pt; "
            f"font-weight: bold; }}"
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
            bar_top = QColor(C("teal",   self._modo))
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

    def __init__(self, name: str, subtitle: str = "", initials: str = "",
                 pct: float = 0.0, selected: bool = False,
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._selected = selected
        self._name_hash = sum(ord(c) for c in (name or "?")) % len(_PATIENT_AVATAR_PAIRS)
        self.setObjectName("NMPatientRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)
        self._avatar = QLabel(initials or "".join(part[:1] for part in name.split()[:2]).upper())
        self._avatar.setFixedSize(32, 32)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFont(qfont("size_small", bold=True))
        lay.addWidget(self._avatar)
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._name = QLabel(name)
        self._name.setFont(qfont("size_small", bold=True))
        self._subtitle = QLabel(subtitle)
        self._subtitle.setFont(qfont("size_caption"))
        text_col.addWidget(self._name)
        text_col.addWidget(self._subtitle)
        lay.addLayout(text_col, stretch=1)
        # Ring 40px: tamaño suficiente para mostrar "85%" sin recorte
        self._ring = NMModuleRing(size=40, pct=pct, modo=self._modo)
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
        c = colors(self._modo)
        if self._selected:
            bg = _rgba(C("teal", self._modo), 0.05)
            border = _rgba(C("teal", self._modo), 0.30)
        else:
            bg = c["bg_surface"] if "light" in self._modo else _rgba("#ffffff", 0.03)
            border = c.get("border_card", c["border"])
        self.setStyleSheet(
            f"QFrame#NMPatientRow {{ background: {bg}; border: 1px solid {border}; "
            f"border-radius: 10px; }}"
        )
        k1, k2 = _PATIENT_AVATAR_PAIRS[self._name_hash]
        self._avatar.setStyleSheet(
            f"QLabel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, "
            f"stop:0 {C(k1, self._modo)}, stop:1 {C(k2, self._modo)}); "
            f"color: white; border-radius: 16px; "
            f"border: 1px solid {_rgba('#ffffff', 0.18 if 'dark' in self._modo else 0.35)}; }}"
        )
        self._name.setStyleSheet(label_style(self._modo, "text_primary"))
        self._subtitle.setStyleSheet(label_style(self._modo, "text_tertiary"))


class NMSettingsSection(QFrame):
    """Sección de configuración v3 (NMConfigRow del README).

      - Surface card con radius ``V3_RD["lg"]`` (14).
      - Header eyebrow (caption semibold) con separador ``borderSoft``.
      - Filas key-value separadas con line ``borderSoft``.
      - Right slot acepta QWidget arbitrario (NMToggle, NMStatusChip, valor).
    """
    def __init__(self, title: str, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self.setObjectName("NMSettingsSection")
        self._sec_shadow: QGraphicsDropShadowEffect | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._header = QLabel(title)
        self._header.setFont(qfont("size_caption",
                                   weight=TYPOGRAPHY["weight_semibold"]))
        self._header.setContentsMargins(V3_SP["lg"], V3_SP["md"],
                                         V3_SP["lg"], V3_SP["md"])
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
            self._sec_shadow.setBlurRadius(30); self._sec_shadow.setOffset(0, 10)
            self._sec_shadow.setColor(QColor(0, 0, 0, 115))
        else:
            self._sec_shadow.setBlurRadius(16); self._sec_shadow.setOffset(0, 6)
            self._sec_shadow.setColor(QColor(15, 23, 42, 22))
        self.setGraphicsEffect(self._sec_shadow)

    def paintEvent(self, event):
        """Pinta el QSS background + top specular highlight (efecto vidrio)."""
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = "dark" in self._modo
        r = V3_RD["lg"]
        w, h = self.width(), self.height()
        # Top highlight con clip al rounded rect
        highlight_h = min(h * 0.4, 50.0)
        hg = QLinearGradient(0, 0, 0, highlight_h)
        if is_dark:
            hg.setColorAt(0.0, QColor(255, 255, 255, 22))
            hg.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            hg.setColorAt(0.0, QColor(255, 255, 255, 140))
            hg.setColorAt(1.0, QColor(255, 255, 255, 0))
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setClipPath(clip_path)
        p.setBrush(QBrush(hg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(0, 0, w, highlight_h))
        p.end()

    def add_row(self, label: str, value):
        row = QWidget()
        row.setObjectName("NMSettingsRow")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["sm"] + 2,
                                V3_SP["lg"], V3_SP["sm"] + 2)
        left = QLabel(label)
        left.setFont(qfont("size_small"))
        lay.addWidget(left)
        lay.addStretch()
        if isinstance(value, QWidget):
            lay.addWidget(value)
        else:
            right = QLabel(str(value))
            sval = str(value)
            right.setFont(qfont_mono(9) if "http" in sval or "..." in sval
                          else qfont("size_caption"))
            lay.addWidget(right)
        self._rows.addWidget(row)
        self._apply_theme(self._modo)
        return row

    def add_log(self, html: str):
        log = QLabel(html)
        log.setTextFormat(Qt.TextFormat.RichText)
        log.setFont(qfont_mono(9))
        log.setWordWrap(True)
        log.setContentsMargins(V3_SP["lg"], V3_SP["sm"],
                                V3_SP["lg"], V3_SP["sm"])
        self._rows.addWidget(log)
        self._apply_theme(self._modo)
        return log

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        surf_key = "surfaceSolid" if is_dark else "surface"
        bg = v3c(surf_key, self._modo).name()
        border = v3c("borderSoft", self._modo).name()
        text_eyebrow = v3c("text3", self._modo).name()
        text_body = v3c("text2", self._modo).name()
        radius = V3_RD["lg"]
        self.setStyleSheet(
            f"QFrame#NMSettingsSection {{ background: {bg}; "
            f"border: 1px solid {border}; border-radius: {radius}px; }}"
            f"QWidget#NMSettingsRow {{ background: transparent; "
            f"border-top: 1px solid {border}; }}"
        )
        self._header.setStyleSheet(
            f"color: {text_eyebrow}; background: transparent; "
            f"border-bottom: 1px solid {border};"
        )
        for lbl in self.findChildren(QLabel):
            if lbl is not self._header:
                lbl.setStyleSheet(
                    f"color: {text_body}; background: transparent;")
        # Re-aplicar sombra al cambiar tema
        if getattr(self, "_sec_shadow", None) is not None:
            self._apply_section_shadow()


class NMInstallProgress(QWidget):
    """Progress bar + terminal del instalador/desinstalador."""
    def __init__(self, accent_key: str = "teal", modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = "dark_hybrid"
        self._accent_key = accent_key
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self._bar = NMProgressBar(height=4, modo=self._modo)
        lay.addWidget(self._bar)
        self._label = QLabel("0%")
        self._label.setFont(qfont_mono(11))
        lay.addWidget(self._label)
        self._terminal = QTextEdit()
        self._terminal.setReadOnly(True)
        self._terminal.setFixedHeight(128)
        lay.addWidget(self._terminal)
        self._apply_theme(self._modo)

    def set_progress(self, pct: int, status: str = ""):
        pct = max(0, min(100, pct))
        self._bar.animate_to(pct / 100)
        self._label.setText(f"{pct}%{(' · ' + status) if status else ''}")

    def set_lines(self, lines: list[str]):
        self._terminal.setPlainText("\n".join(lines))

    def append_line(self, line: str):
        self._terminal.append(line)

    def _apply_theme(self, modo: str = "dark_hybrid"):
        c = colors("dark_hybrid")
        self._label.setStyleSheet(label_style("dark_hybrid", "text_tertiary"))
        self._terminal.setStyleSheet(
            f"QTextEdit {{ background: {c['installer_terminal_bg']}; color: {c['text_tertiary']}; "
            f"border: 1px solid {c['border']}; border-radius: 8px; padding: 10px; "
            f"font-family: '{FONT_MONO}'; font-size: {TYPOGRAPHY['size_caption']}pt; }}"
        )


class _GradientTextLabel(QWidget):
    """Label que pinta texto con gradiente horizontal izquierda→derecha."""

    def __init__(self, text: str, font, color_left: str, color_right: str,
                 height: int = 28, margins=(10, 6, 10, 10), parent=None):
        super().__init__(parent)
        self._text = text
        self._font = font
        self._c1   = QColor(color_left)
        self._c2   = QColor(color_right)
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

    def __init__(self, items: list[tuple[str, str, str]], active: str = "",
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._active = active or (items[0][0] if items else "")
        self._items_tuple = items
        self._buttons: dict[str, QPushButton] = {}
        self.setFixedWidth(240)
        lay = QVBoxLayout(self)
        self._layout = lay
        lay.setContentsMargins(8, 12, 8, 8)
        lay.setSpacing(3)
        self._logo = _GradientTextLabel(
            "NeuroMood Hub", qfont("size_small", bold=True),
            C("accent", self._modo), C("teal", self._modo),
            height=28, margins=(10, 6, 10, 10),
        )
        lay.addWidget(self._logo)
        for key, icon, label in items:
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            try:
                qicon = nm_icon(icon, C("text3", self._modo), size=16)
                if qicon and not qicon.isNull():
                    btn.setIcon(qicon)
                    btn.setIconSize(QSize(18, 18))
            except Exception:
                pass
            btn.clicked.connect(lambda checked=False, k=key: self._select(k))
            lay.addWidget(btn)
            self._buttons[key] = btn
        lay.addStretch()
        self._footer = QLabel()
        self._footer.setFont(qfont("size_caption"))
        self._footer.setContentsMargins(10, 10, 10, 4)
        lay.addWidget(self._footer)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)

    def set_footer(self, text: str):
        self._footer.setText(text)

    def set_active(self, key: str):
        self._active = key
        self._apply_theme(self._modo)

    def _select(self, key: str):
        self.set_active(key)
        self.nav_clicked.emit(key)

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        c = colors(self._modo)
        self.setStyleSheet(
            f"background: {C('sidebar_bg', self._modo)}; "
            f"border-right: 1px solid {c.get('border_card', c['border'])};"
        )
        self._logo.set_colors(C("accent", self._modo), C("teal", self._modo))
        self._footer.setStyleSheet(
            f"color: {c['text_tertiary']}; background: transparent; "
            f"border-top: 1px solid {c.get('border_card', c['border'])};"
        )
        for key, btn in self._buttons.items():
            active = key == self._active
            btn.setStyleSheet(
                f"QPushButton {{ text-align: left; background: "
                f"{_rgba(C('teal', self._modo), 0.08) if active else 'transparent'}; "
                f"color: {c['text_primary'] if active else c['text_tertiary']}; "
                f"border: none; border-left: {3 if active else 0}px solid {C('teal', self._modo)}; "
                f"border-radius: 8px; padding: 7px 10px; font-size: {TYPOGRAPHY['size_small']}pt; }}"
                f"QPushButton:hover {{ background: {_rgba('#ffffff', 0.05)}; color: {c['text_secondary']}; }}"
            )
            icon_color = c['text_primary'] if active else c['text_tertiary']
            for item in self._items_tuple:
                if item[0] == key:
                    try:
                        qicon = nm_icon(item[1], icon_color, size=16)
                        if qicon and not qicon.isNull():
                            btn.setIcon(qicon)
                    except Exception:
                        pass
                    break


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

        # Tags row (pills)
        self._tags_widget = QWidget()
        self._tags_widget.setStyleSheet("background: transparent;")
        self._tags_layout = QHBoxLayout(self._tags_widget)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(sp("xs") if hasattr(sp, "__call__") else 4)
        self._tags_layout.addStretch()
        self._tags_widget.setVisible(False)
        lay.addWidget(self._tags_widget)

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
        # Limpiar tags anteriores (conservar el stretch)
        while self._tags_layout.count() > 1:
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not tags:
            self._tags_widget.setVisible(False)
            return
        color_map = {
            "teal":   ("teal",   0.14),
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
            self._tags_layout.insertWidget(self._tags_layout.count() - 1, chip)
        self._tags_widget.setVisible(True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.save()

        w, h = self.width(), self.height()
        r    = RADIUS_CARD
        c    = colors(self._modo)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.fillPath(path, QColor(c["bg_surface"]))

        op = blob_opacity(self._modo)
        teal_c = QColor(C("hub_blob_teal", self._modo))
        teal_c.setAlphaF(op)
        blob1 = QRadialGradient(QPointF(w * 0.2, h * 0.3), w * 0.55)
        blob1.setColorAt(0.0, teal_c)
        blob1.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, blob1)

        violet_c = QColor(C("hub_blob_violet", self._modo))
        violet_c.setAlphaF(op * 0.75)
        blob2 = QRadialGradient(QPointF(w * 0.8, h * 0.75), w * 0.45)
        blob2.setColorAt(0.0, violet_c)
        blob2.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, blob2)

        border_c = QColor(c.get("border_card", c["border"]))
        border_c.setAlpha(50)
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
            f"color: {teal}; background: transparent; letter-spacing: 0.06em;"
        )
        self._score_lbl.setStyleSheet(f"color: {C('text_primary', self._modo)}; background: transparent;")
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
    """
    def __init__(self, size: int = 56, pct: float = 0.0,
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._pct  = max(0.0, min(1.0, pct))
        self._size = size
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

        s        = self._size
        cx, cy   = s / 2, s / 2
        pen_w    = _ring_stroke(s)
        r_arc    = s / 2 - pen_w - 1
        arc_rect = QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2)

        # ── 0. Glow radial detrás del arco (teal/violet) — solo si hay progreso ──
        # Spec README: "Anillos de progreso: glow blur teal+violet detrás del
        # arco en dark". Más sutil en light.
        is_dark = "dark" in self._modo
        if self._pct > 0.05:
            glow_r = r_arc + pen_w * 1.5
            glow_grad = QRadialGradient(QPointF(cx, cy), glow_r)
            # Color base: teal del gradient firma v3
            glow_col = v3c("teal", self._modo)
            glow_col.setAlpha(70 if is_dark else 30)
            glow_grad.setColorAt(0.5, glow_col)
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow_grad))
            p.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # Track sutil (borderSoft v3 — TODOS los rings usan el mismo lenguaje)
        track_c = v3c("borderSoft", self._modo)
        p.setPen(QPen(track_c, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r_arc, r_arc)

        # Arco progreso con gradient firma v3 (uniforme entre rings)
        if self._pct > 0.001:
            _paint_v3_arc(p, arc_rect, 90.0, -360.0 * self._pct, pen_w, self._modo)

        # Texto centrado
        p.setPen(v3c("text", self._modo))
        p.setFont(qfont_mono(max(9, int(s * 0.20)), bold=False))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter,
                   f"{int(self._pct * 100)}%")

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
    def __init__(self, text: str = "", side: str = "left",
                 modo: str = None, typing: bool = False, parent=None):
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
        self._bubble.setMaximumWidth(360)
        self._bubble.setContentsMargins(V3_SP["md"], V3_SP["sm"],
                                        V3_SP["md"], V3_SP["sm"])
        self._bubble.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
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
        self._bubble.setText("●" * self._typing_dots_state +
                             "○" * (3 - self._typing_dots_state))

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        r = V3_RD["lg"]                 # radius 14
        pad = f"padding: {V3_SP['sm']}px {V3_SP['md']}px;"
        fsize = f"font-size: {TYPOGRAPHY['size_body']}pt;"
        if self._side == "left":
            # IA — superficie clara con borderSoft, cola en top-left
            surf_key = "surfaceSolid" if is_dark else "surface"
            bg = v3c(surf_key, self._modo).name()
            col = v3c("text", self._modo).name()
            border = v3c("borderSoft", self._modo).name()
            radii = (f"border-top-left-radius: 3px; "
                     f"border-top-right-radius: {r}px; "
                     f"border-bottom-left-radius: {r}px; "
                     f"border-bottom-right-radius: {r}px;")
            self._bubble.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {col}; "
                f"border: 1px solid {border}; {radii} {pad} {fsize} }}"
            )
        else:
            # Usuario — gradient firma v3 (teal → cyan-mid → violet), cola en top-right
            gf = v3c("gradFrom", self._modo).name()
            gm = v3c("gradMid",  self._modo).name()
            gt = v3c("gradTo",   self._modo).name()
            text_col = C("text_on_accent", self._modo)
            radii = (f"border-top-left-radius: {r}px; "
                     f"border-top-right-radius: 3px; "
                     f"border-bottom-left-radius: {r}px; "
                     f"border-bottom-right-radius: {r}px;")
            self._bubble.setStyleSheet(
                f"QLabel {{ background: qlineargradient("
                f"x1:0,y1:0,x2:1,y2:1, stop:0 {gf}, stop:0.5 {gm}, stop:1 {gt}); "
                f"color: {text_col}; border: none; {radii} {pad} {fsize} }}"
            )


# ── NMTypingDots ──────────────────────────────────────────────────────────────

class NMTypingDots(QWidget):
    """Indicador animado de 'IA escribiendo...' (3 puntos secuenciales).

    Llamar a start()/stop() para controlar la animación.
    """
    # Spec README v3: "3 dots con animación translateY(-4px) escalonada
    # (delay 0/0.15/0.3s)" — implementado con phase continuous + sin wave.
    _PERIOD_MS = 1200            # ciclo completo
    _STAGGER_MS = 150            # 0.15s entre dots
    _BOUNCE_PX = 4               # translateY -4px en el pico

    def __init__(self, modo: str = None, parent=None):
        super().__init__(parent)
        self._modo   = norm_modo(modo or _tm().modo)
        self._t_ms   = 0
        self._timer  = QTimer(self)
        self._timer.setInterval(33)   # ~30 fps (suave para anim continua)
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
        dot_r   = 4
        gap     = 12
        y_c     = self.height() / 2
        x_start = dot_r + 2
        base_c  = QColor(C("teal", self._modo))
        for i in range(3):
            # Phase shift por dot — 0.15s stagger
            if self._running:
                phase = ((self._t_ms - i * self._STAGGER_MS) % self._PERIOD_MS) / self._PERIOD_MS
                # bounce: pico arriba en phase 0.5, queda abajo en 0/1
                # Usamos curva senoidal solo en la primera mitad del ciclo
                if 0 <= phase < 0.5:
                    bounce = math.sin(phase * math.pi)   # 0→1→0
                else:
                    bounce = 0.0
                offset_y = -self._BOUNCE_PX * bounce
                alpha = 0.4 + 0.6 * bounce               # 0.4 idle, 1.0 peak
            else:
                offset_y = 0.0
                alpha = 0.3
            dc = QColor(base_c)
            dc.setAlphaF(alpha)
            p.setBrush(QBrush(dc))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x_start + i * gap, y_c + offset_y),
                           dot_r, dot_r)
        p.restore()
        p.end()


# ── NMSyncOrb ─────────────────────────────────────────────────────────────────

class NMProviderChip(QWidget):
    """Chip compacto para proveedor/modelo IA activo."""
    def __init__(self, text: str = "IA verificando", state: str = "syncing",
                 modo: str = None, parent=None):
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
        self.setMinimumWidth(190)
        self.setMaximumWidth(230)
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
            ("animo", "Animo 7d", "7.2/10"),
            ("distorsiones", "Distorsiones", "3"),
            ("racha", "Racha", "5d"),
        ]:
            row = QWidget()
            row_l = QVBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(1)
            l = QLabel(label)
            l.setFont(qfont("size_caption"))
            v = QLabel(value)
            v.setFont(qfont("size_small", bold=True))
            row_l.addWidget(l)
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
            color_key = "teal" if key == "animo" else ("violet" if key == "distorsiones" else "text_primary")
            lbl.setStyleSheet(label_style(self._modo, color_key))
        for label in self.findChildren(QLabel):
            if label is self._title or label in self._rows.values():
                continue
            label.setStyleSheet(label_style(self._modo, "text_tertiary"))


class NMSyncOrb(QWidget):
    """Orb circular de estado de sincronización con animación de pulso.

    state: 'ok' (verde) | 'error' (rojo) | 'syncing' (ámbar, pulsa).
    """
    def __init__(self, state: str = "ok", size: int = 12,
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._modo       = norm_modo(modo or _tm().modo)
        self._state      = state
        self._anim_alpha = 255
        self._fade_dir   = -1
        self._timer      = QTimer(self)
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
            self._fade_dir =  1
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
    def __init__(self, steps: list[str], current: int = 0,
                 accent_key: str = "teal", parent=None):
        super().__init__(parent)
        self._steps      = steps
        self._current    = current
        self._accent_key = accent_key
        self._modo       = "dark_hybrid"
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
            p.restore(); p.end(); return

        w, h     = self.width(), self.height()
        circle_r = 12
        cy       = 20
        step_w   = w / n
        accent   = C(self._accent_key, self._modo)

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
                Qt.AlignmentFlag.AlignCenter, label,
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

    def __init__(self, title: str, description: str, checked: bool = True,
                 parent=None):
        super().__init__(parent)
        self._modo    = "dark_hybrid"
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
            f"color: {C('warning', self._modo)}; background: transparent;")
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
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {C('teal', self._modo)}, stop:1 {C('accent', self._modo)}); "
                f"border-radius: {RADIUS_PILL}px; border: none; }}"
            )
            self._state_lbl.setStyleSheet(f"color: {C('teal', self._modo)}; background: transparent;")
        else:
            self._toggle_btn.setStyleSheet(
                f"QPushButton {{ background: {c['bg_elevated']}; "
                f"border-radius: {RADIUS_PILL}px; border: 1px solid {c['border']}; }}"
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

    def __init__(self, level: int = 5, parent=None):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self.setFixedHeight(56)
        self.setMinimumWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv != self._level:
            self._level = lv
            self.update()

    def level(self) -> int:
        return self._level

    def _dot_positions(self) -> list[float]:
        margin_x = 16
        w = self.width() - 2 * margin_x
        return [margin_x + (i / 9) * w for i in range(10)]

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

        # Dots (10)
        positions = self._dot_positions()
        center_y = h / 2
        for i, x in enumerate(positions):
            n = i + 1
            lv_color = get_mood(n)["to"]
            if n == self._level:
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

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = (event.position().x() if hasattr(event, "position")
                 else float(event.pos().x()))
            positions = self._dot_positions()
            closest = min(range(10), key=lambda i: abs(positions[i] - x))
            n = closest + 1
            if n != self._level:
                self.set_level(n)
            self.level_clicked.emit(n)
        super().mousePressEvent(event)


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

    def __init__(self, level: int = 5,
                 title: str = "¿Cómo te sientes hoy?",
                 subtitle: str = "Deslizá para encontrar el número que mejor describe tu estado.",
                 modo: str = None, parent=None):
        super().__init__(parent)
        self._level = max(1, min(10, int(level)))
        self._modo = norm_modo(modo or _tm().modo)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(V3_SP["lg"])

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(V3_SP["lg"])

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(qfont("size_h2",
                                      weight=TYPOGRAPHY["weight_bold"]))
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
        self._eyebrow_lbl = QLabel("HOY")
        self._eyebrow_lbl.setFont(
            qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        self._eyebrow_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl = QLabel(get_mood(self._level)["name"])
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._name_lbl.setFont(
            qfont("size_display", weight=TYPOGRAPHY["weight_bold"]))
        self._numeric_lbl = QLabel(f"{self._level}/10")
        self._numeric_lbl.setFont(qfont_mono(12, bold=False))
        self._numeric_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_col.addWidget(self._eyebrow_lbl)
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._numeric_lbl)
        text_col.addStretch()
        right.addLayout(text_col)

        self._emoji_big = NMMoodEmoji(level=self._level, size=104,
                                      glow=True, modo=self._modo)
        right.addWidget(self._emoji_big,
                        alignment=Qt.AlignmentFlag.AlignVCenter)

        header.addLayout(right)
        root.addLayout(header)

        # ── Slashbar ──────────────────────────────────────────────────────────
        self._track = _MoodTrackBar(level=self._level)
        self._track.level_clicked.connect(self._on_level_clicked)
        root.addWidget(self._track)

        # ── Fila de números 1-10 ──────────────────────────────────────────────
        num_row = QWidget()
        nrow_layout = QHBoxLayout(num_row)
        nrow_layout.setContentsMargins(16, 0, 16, 0)
        nrow_layout.setSpacing(0)
        self._num_labels: list[_MoodPickLabel] = []
        for n in range(1, 11):
            lbl = _MoodPickLabel(str(n), n)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(24)
            lbl.picked.connect(self._on_level_clicked)
            self._num_labels.append(lbl)
            nrow_layout.addWidget(lbl)
            if n < 10:
                nrow_layout.addStretch()
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
            d.setFont(qfont("size_caption",
                            weight=TYPOGRAPHY["weight_semibold"]))
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
            is_active = (n == self._level)
            emoji = NMMoodEmoji(level=n,
                                size=(38 if is_active else 32),
                                glow=is_active, modo=self._modo)
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

    # ── API pública ──────────────────────────────────────────────────────────

    def level(self) -> int:
        return self._level

    def set_level(self, level: int):
        lv = max(1, min(10, int(level)))
        if lv == self._level:
            return
        self._level = lv
        self._track.set_level(lv)
        self._emoji_big.set_level(lv)
        self._name_lbl.setText(get_mood(lv)["name"])
        self._numeric_lbl.setText(f"{lv}/10")
        for cell, emoji, lbl, n in self._preview_cells:
            active = (n == lv)
            emoji.set_size(38 if active else 32)
            emoji.set_glow(active)
        self._refresh_styles()
        self.level_changed.emit(lv)

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
        c_text3 = v3c("text3", self._modo).name()
        c_text4 = v3c("text4", self._modo).name()
        elev_key = "elevatedSolid" if is_dark else "elevated"
        c_elev = v3c(elev_key, self._modo).name()
        c_border = v3c("borderSoft", self._modo).name()
        lv_color = get_mood(self._level)["to"]

        self._title_lbl.setStyleSheet(
            f"color: {c_text}; background: transparent;")
        self._subtitle_lbl.setStyleSheet(
            f"color: {c_text2}; background: transparent;")
        self._eyebrow_lbl.setStyleSheet(
            f"color: {c_text3}; background: transparent;")
        self._name_lbl.setStyleSheet(
            f"color: {lv_color}; background: transparent;")
        self._numeric_lbl.setStyleSheet(
            f"color: {c_text2}; background: transparent;")
        for d in self._desc_labels:
            d.setStyleSheet(f"color: {c_text3}; background: transparent;")
        for lbl in self._num_labels:
            active = (lbl._value == self._level)
            col = (get_mood(lbl._value)["to"] if active else c_text3)
            lbl.setFont(qfont_mono(11, bold=active))
            lbl.setStyleSheet(f"color: {col}; background: transparent;")
        for cell, emoji, num_lbl, n in self._preview_cells:
            active = (n == self._level)
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

    def __init__(self, icon_name: str = "play", size: str = "md",
                 modo: str = None, parent=None):
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
        surf_key = ("elevatedSolid" if (self._hover and is_dark)
                    else "elevated" if self._hover
                    else "surfaceSolid" if is_dark
                    else "surface")
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
