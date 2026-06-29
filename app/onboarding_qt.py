"""app/onboarding_qt.py - Pantalla de primer arranque para NeuroMood Suite.

Responsabilidades:
- Recolectar nombre, email y contraseña del paciente.
- Autenticar al paciente con Supabase Auth.
- Registrar identidad local usando auth.user.id como patient_id.
- Crear legal_consent.json en %APPDATA%\\NeuroMood\\.
- Crear pending_consent.json solo si el consentimiento remoto no pudo enviarse
  después de autenticar.
- No rompe instalaciones existentes: si _is_onboarded() ya es True, nunca
  se llama este módulo.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)

from shared.components import NMButton, NMInput
from shared.adaptive_layout_qt import configure_adaptive_window
from shared.config import supabase_key, supabase_url
from shared.remote_config import t as suite_t
from shared.legal_contract import (
    SUITE_VERSION,
    DISCLAIMER_VERSION,
    PRIVACY_VERSION,
    CONSENT_SCOPE,
    LEGAL_DISCLAIMER_TEXT,
    DISCLAIMER_TEXT_HASH,
    PRIVACY_TEXT_HASH,
)

_CONSENT_TEXT = LEGAL_DISCLAIMER_TEXT
_CONSENT_SUMMARY_PARAGRAPHS = (
    "NeuroMood Suite es una herramienta digital complementaria de bienestar: "
    "registro emocional, organización de hábitos y apoyo personal.",
    "No realiza diagnósticos ni reemplaza la evaluación, seguimiento o "
    "intervención de profesionales de la salud habilitados.",
)
_DISCLAIMER_VERSION = DISCLAIMER_VERSION
_PRIVACY_VERSION = PRIVACY_VERSION
_SUITE_VERSION = SUITE_VERSION
_CONSENT_SCOPE = CONSENT_SCOPE
_DISCLAIMER_TEXT_HASH = DISCLAIMER_TEXT_HASH
_PRIVACY_TEXT_HASH = PRIVACY_TEXT_HASH


class _FocusRingOverlay(QWidget):
    """Anillo de foco canónico del input activo.

    Canónico `.input:focus` (mockup línea 304; aplicado al email en estado
    recover, mockup línea 1425):
    ``box-shadow:0 0 0 3px var(--brand-soft)`` — una banda sólida de 3px de
    brand-soft alrededor del campo. Se apila DETRÁS del input (``stackUnder``):
    el input opaco tapa el centro y solo queda visible la banda 3px. Replica el
    box-shadow sin depender del foco real de Qt (en captura offscreen la ventana
    inactiva no concede foco visual, así que `:focus` nunca pinta).
    QGraphicsDropShadowEffect no sirve: difumina el alpha y no lee como el
    anillo 3px sólido.
    """

    def __init__(self, soft_color: QColor, radius: int, pad: int = 3, parent=None):
        super().__init__(parent)
        self._soft = QColor(soft_color)
        self._radius = int(radius)
        self._pad = int(pad)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._soft))
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        outer_r = self._radius + self._pad
        p.drawRoundedRect(rect, outer_r, outer_r)
        p.end()


class _ConsentCheckBox(QCheckBox):
    """Checkbox legal pintado para asegurar check visible en light/dark."""

    def __init__(self, modo: str = "light_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(22, 22)
        self.setStyleSheet("QCheckBox { background: transparent; spacing: 0px; }")

    def set_modo(self, modo: str) -> None:
        self._modo = modo
        self.update()

    def paintEvent(self, event) -> None:
        try:
            from shared.theme_qt import norm_modo, v3c
            modo = norm_modo(self._modo)
            primary = v3c("primary", modo)
            surface = v3c("surface", modo)
            border = v3c("borderStrong" if self.hasFocus() else "border", modo)
            ink = v3c("primary_ink", modo)
        except Exception:
            primary = QColor("#2E5D43")
            surface = QColor("#FBF8F1")
            border = QColor("#D8D0C0")
            ink = QColor("#F7F3EA")

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(primary if self.isChecked() else border, 2))
        p.setBrush(QBrush(primary if self.isChecked() else surface))
        p.drawRoundedRect(rect, 7, 7)

        if self.isChecked():
            path = QPainterPath()
            path.moveTo(6.0, 11.5)
            path.lineTo(9.4, 15.0)
            path.lineTo(16.4, 7.2)
            p.setPen(QPen(ink, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
        p.end()


def _is_windows_11_or_newer() -> bool:
    if sys.platform != "win32":
        return True
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:
        return False


def run_onboarding() -> bool:
    """Muestra el diálogo de onboarding. Retorna True si el usuario completó el proceso."""
    dlg = OnboardingDialog()
    return dlg.exec() == QDialog.DialogCode.Accepted


class OnboardingDialog(QDialog):
    """Diálogo de primer arranque: Auth Supabase + consentimiento legal."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # P2.B: chrome NeuroMood en lugar de titlebar nativa blanca. La ventana
        # pasa a frameless y la barra (cerebro + título + min/max/close) se inserta
        # desde apply_child_window_chrome en _init_theme.
        self.setWindowTitle("")
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        try:
            from PyQt6.QtCore import QSettings
            from shared.theme_qt import norm_modo

            self._modo = norm_modo(
                QSettings("NeuroMood", "Suite").value("ui/theme", "dark_hybrid", type=str)
            )
        except Exception:
            self._modo = "dark_hybrid"
        try:
            from shared.fonts import load_fonts

            load_fonts()
        except Exception:
            pass
        self._init_theme()
        self._configure_responsive_window()
        self._build_ui()
        # P2.B: el chrome NM se inserta DESPUÉS de _build_ui, cuando el layout ya
        # existe. Si se hace antes (como estaba), apply_child_window_chrome no
        # encuentra layout y deja la barra huérfana fuera de él → ventana
        # frameless sin titlebar usable, barra flotando sobre el contenido.
        self._apply_window_chrome()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def _init_theme(self):
        try:
            from shared.theme_qt import (
                v3_font as _v3_font,
                v3c as _v3c,
            )
            from shared.theme import TYPOGRAPHY as _TY

            modo = self._modo
            self._t = {
                "v3_font": _v3_font,
                "v3c": _v3c,
                "TY": _TY,
                "modo": modo,
                "mute": _v3c("textMuted", modo).name(),
                "text": _v3c("text", modo).name(),
                "text2": _v3c("text2", modo).name(),
                "text3": _v3c("faint", modo).name(),
                "danger": _v3c("danger", modo).name(),
                "accent": _v3c("accent", modo).name(),
                "primary": _v3c("primary", modo).name(),
                "primary_ink": _v3c("primary_ink", modo).name(),
                "surface": _v3c("surface", modo).name(),
                "surface2": _v3c("surface_2", modo).name(),
                "canvas": _v3c("bg", modo).name(),
                "input": _v3c("surface_2", modo).name(),
                "border": _v3c("borderSolid", modo).name(),
                "bg": _v3c("bg", modo).name(),
            }
            self._has_theme = True
            # Fondo de la ventana = color de la card (surface). Antes
            # se usaba canvas (un tono distinto) y se veían dos subfondos
            # azul/gris a los lados cuando la ventana era más ancha que la
            # card. Ahora la card queda "al raz" del borde de la ventana
            # sin costura visible entre el frame y la card.
            self.setStyleSheet(f"OnboardingDialog {{ background-color: {self._t['surface']}; }}")
        except Exception:
            self._t = {}
            self._has_theme = False

    def _fallback_color(self, key: str) -> str:
        """Color tokenizado para el branch pre-shell si theme_qt no cargó."""
        try:
            from shared.design_tokens import DARK, LIGHT

            pal = DARK if "dark" in getattr(self, "_modo", "dark_hybrid") else LIGHT
            return pal[key]
        except Exception:
            return "palette(window-text)"

    def _apply_window_chrome(self):
        """Reemplaza la titlebar nativa por el chrome NM (cerebro + título +
        min/max/close). Se llama tras _build_ui para que el layout exista y la
        barra se inserte en él (no flotando fuera) — fix P2.B."""
        try:
            from shared.adaptive_layout_qt import apply_child_window_chrome

            chrome = apply_child_window_chrome(
                self,
                # Mockup titlebar: tb-title "NeuroMood" (bold) + tb-crumb
                # "/ Configuración inicial" (ink-3). Antes se pasaba combinado con
                # "·" en un solo título → no coincidía con el target.
                title="NeuroMood",
                subtitle="Configuración inicial",
                modo=self._modo,
                show_theme_toggle=True,
                # Ventana de tamaño fijo: solo "—" minimizar y "✕" cerrar.
                show_maximize=False,
                # Pero el semáforo canónico muestra 3 puntos: el ámbar va como
                # decorativo (mockup `.tb-dots` línea 526).
                show_amber_dot=True,
            )
            if hasattr(chrome, "_mark"):
                chrome._mark._icon_name = "brain"
                chrome._mark._apply_theme(self._modo)
            chrome.setFixedHeight(48)
            try:
                from shared.theme_qt import qfont

                chrome_title_font = qfont(13, weight=600)
                chrome_title_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                chrome._lbl_title.setFont(chrome_title_font)
            except Exception:
                pass
            chrome.theme_toggle.connect(self._toggle_theme)
        except Exception:
            pass

    def _toggle_theme(self):
        from shared.theme_manager import ThemeManager
        from shared.theme_qt import norm_modo

        new_modo = "light_hybrid" if "dark" in self._modo else "dark_hybrid"
        self._modo = norm_modo(new_modo)
        ThemeManager.instance().switch_mode(self._modo)
        # El diálogo completo debe repintarse con la nueva paleta. Los
        # QFrame/QLabel/QPushButton fijaron su stylesheet en _build_ui
        # contra tokens del tema anterior; sin este refresh la mitad de
        # los widgets (card, labels, inputs, chips, feedback) conservan
        # los colores viejos y la transición queda a medias.
        self._init_theme()
        try:
            ThemeManager.instance().theme_changed.emit(self._modo)
        except Exception:
            pass
        self._refresh_card_theme()

    def _configure_responsive_window(self):
        from PyQt6.QtCore import QSize

        configure_adaptive_window(
            self,
            default_size=QSize(520, 600),
            min_size=QSize(380, 520),
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Contenedor full-bleed: la ventana entera es la card (el fondo surface
        # lo pinta el stylesheet del diálogo). El contenido se acota a un ancho
        # de lectura cómodo y se centra solo si la ventana se agranda.
        card = QFrame()
        card.setObjectName("AuthCard")
        # Full-bleed: la card ocupa TODA la ventana (mismo surface que el diálogo)
        # → sin maxWidth ni centrado no quedan bandas laterales de otro color ni
        # una "segunda capa" flotando. El borde/radio quedan en el borde de la
        # ventana. Vale igual en compacto y al ampliar.
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self._has_theme:
            border_c = self._t["v3c"]("border", self._modo)
            border_css = (
                f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},{border_c.alpha()})"
            )
            auth_bg = self._t["surface"]
            if "light" in self._modo:
                auth_bg = (
                    "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                    "stop:0 #F4F0E5, stop:0.34 #F5F1E7, "
                    "stop:0.72 #FBF8F1, stop:1 #FBF8F1)"
                )
            card_radius = 22 if _is_windows_11_or_newer() else 0
            card.setStyleSheet(
                f"QFrame#AuthCard {{ background: {auth_bg}; "
                f"border: 1px solid {border_css}; border-radius: {card_radius}px; }}"
            )
        else:
            card.setStyleSheet("QFrame#AuthCard { background: transparent; border: none; }")
        root.addWidget(card)

        # Card internal layout
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form_lay = QVBoxLayout(form_widget)
        self._form_lay = form_lay
        # El target canónico es 520×600 y usa el espaciado COMPLETO del mockup
        # (.screen padding 26×28, sub mb18, inputs mb14). El modo compacto (tighter)
        # se reserva para ventanas genuinamente bajas (<560) cerca del mínimo 520.
        is_compact = self.width() <= 560 or self.height() < 620
        # Márgenes generosos full-bleed (la ventana es la card): aire lateral
        # premium sin doble borde.
        # Mockup .screen padding:26px 28px — top margin reducido para compensar
        # el mayor alto del h-serif 21px del título (metrics distintos al regular
        # anterior): el título debe quedar a ~y=118 en 520×600 como en el target.
        if is_compact:
            form_lay.setContentsMargins(25, 21, 27, 4)
            form_lay.setSpacing(4)
        else:
            # Mockup .screen padding:26px 28px.
            form_lay.setContentsMargins(28, 24, 28, 8)
            form_lay.setSpacing(6)
        form_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Brandmark canónico + título "NeuroMood Suite" ────────────────────
        # Mockup línea 1294-1297:
        #   <div style="display:flex; align-items:center; gap:11px; margin-bottom:6px;">
        #     <div class="brandmark">${svg(I.brain,20)}</div>
        #     <div class="h-serif" style="font-size:21px;">
        #       Neuro<span style="color:var(--brand)">Mood</span>
        #       <span style="font-style:italic; color:var(--ink-3);">Suite</span>
        #     </div>
        #   </div>
        # Brandmark = 34×34 r10 con linear-gradient(140deg, brand, accent) + svg brain 20px blanco.
        # Antes: QPixmap logo file. Ahora: QFrame paintEvent con gradient + SVG brain.
        brand_row = QHBoxLayout()
        self._brand_row = brand_row
        brand_row.setSpacing(8 if is_compact else 11)
        brand_row.setContentsMargins(0, 0, 0, 0)

        class _BrandmarkFrame(QFrame):
            """QFrame 34×34 con paintEvent custom: gradient brand→accent + brain SVG."""

            def __init__(_self, b_color, a_color, parent=None):
                super().__init__(parent)
                _self._b = b_color
                _self._a = a_color
                _self.setFixedSize(34, 34)
                _self.setObjectName("OnbBrandmark")
                _self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

            def paintEvent(_self, _ev):
                from PyQt6.QtGui import QPainter, QLinearGradient, QBrush, QColor
                p = QPainter(_self)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                # linear-gradient(140deg, brand, accent) — 140° en CSS ≈ top-left→bottom-right
                grad = QLinearGradient(0, 0, 34, 34)
                grad.setColorAt(0.0, QColor(_self._b))
                grad.setColorAt(1.0, QColor(_self._a))
                p.setBrush(QBrush(grad))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(0, 0, 34, 34, 10, 10)
                # SVG brain 20px blanco centrado (7,7 offset para 20px en 34×34)
                try:
                    from shared.icons_svg import nm_svg_pixmap
                    pix = nm_svg_pixmap("brain", "#FFFFFF", 20)
                    if pix is not None and not pix.isNull():
                        p.drawPixmap(7, 7, pix)
                except Exception:
                    pass
                p.end()

        if self._has_theme:
            brandmark = _BrandmarkFrame(self._t["primary"], self._t["accent"])
        else:
            # Fallback: QFrame simple con bg sólido (sin gradient ni SVG)
            brandmark = QFrame()
            brandmark.setFixedSize(34, 34)
            brandmark.setObjectName("OnbBrandmark")
            brandmark.setStyleSheet(
                f"QFrame#OnbBrandmark {{ background: {self._fallback_color('primary')};"
                f" border-radius: 10px; }}"
            )
        brand_row.addWidget(brandmark, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Título h-serif 21px con 3 spans: "Neuro" + <span brand>"Mood"</span> + <span italic ink-3>"Suite"</span>
        if self._has_theme:
            ink_c = self._t["text"]
            brand_c = self._t["primary"]
            ink3_c = self._t["text3"]  # faint = ink-3 canónico
            title_html = (
                f"<span style='color:{ink_c};'>Neuro</span>"
                f"<span style='color:{brand_c};'>Mood</span>"
                f" <span style='color:{ink3_c}; font-style:italic;'>Suite</span>"
            )
        else:
            fb_text = self._fallback_color("ink_primary")
            fb_brand = self._fallback_color("primary")
            title_html = (
                f"<span style='color:{fb_text};'>Neuro</span>"
                f"<span style='color:{fb_brand};'>Mood</span>"
                f" <span style='color:{fb_text}; font-style:italic;'>Suite</span>"
            )
        title_lbl = QLabel(title_html)
        self._title_lbl = title_lbl  # ref para repintar spans en toggle de tema
        title_lbl.setTextFormat(Qt.TextFormat.RichText)
        if self._has_theme:
            # Mockup: font-size 21px, h-serif (Fraunces), weight 600 (h-serif default).
            f_disp = self._t["v3_font"](
                19 if is_compact else 21,
                weight=self._t["TY"]["weight_semibold"],
                serif=True,
            )
            if is_compact:
                f_disp.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            title_lbl.setFont(f_disp)
        else:
            f = QFont()
            f.setPixelSize(21)
            title_lbl.setFont(f)
        title_lbl.setStyleSheet("background: transparent;")
        brand_row.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        brand_row.addStretch()
        form_lay.addLayout(brand_row)
        self._brand_to_sub_spacer = QSpacerItem(
            0,
            2 if is_compact else 6,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        form_lay.addItem(self._brand_to_sub_spacer)

        sub = QLabel(
            suite_t(
                "text.onboarding.subtitle",
                "Vinculá tu cuenta de NeuroMood. Tus datos se mantienen cifrados y bajo tu control.",
            )
        )
        sub.setObjectName("OnbSub")
        sub.setWordWrap(not is_compact)
        sub_px = 11 if is_compact else 12
        if self._has_theme:
            sub.setFont(
                self._t["v3_font"](
                    "size_eyebrow" if is_compact else "size_caption",
                    weight=self._t["TY"]["weight_regular"],
                )
            )
        else:
            sub_font = QFont()
            sub_font.setPixelSize(sub_px)
            sub.setFont(sub_font)
        if self._has_theme:
            sub.setStyleSheet(f"color: {self._t['mute']}; background: transparent;")
        else:
            sub.setStyleSheet(f"color: {self._fallback_color('ink_secondary')};")
        if is_compact:
            sub_font = sub.font()
            sub_font.setStretch(97)
            sub_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            sub.setFont(sub_font)
            sub.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            sub.setFixedHeight(16)
            sub.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        form_lay.addWidget(sub)

        self._sub_to_name_spacer = QSpacerItem(
            0,
            8 if is_compact else 14,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        form_lay.addItem(self._sub_to_name_spacer)  # mockup: sub margin 0 0 18px

        # ── Nombre ────────────────────────────────────────────────────────────
        form_lay.addWidget(self._lbl(suite_t("text.onboarding.name_label", "Nombre *"), is_compact))
        self._name = NMInput(suite_t("text.onboarding.name_placeholder", "Tu nombre"), modo=self._modo)
        if is_compact:
            self._name.setFixedHeight(37)
            self._name.setFixedWidth(468)
            self._apply_compact_input_font(self._name)
        form_lay.addWidget(self._name)

        self._name_to_email_spacer = QSpacerItem(
            0,
            10 if is_compact else 10,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        form_lay.addItem(self._name_to_email_spacer)  # mockup: input margin-bottom 14px

        # ── Email ─────────────────────────────────────────────────────────────
        form_lay.addWidget(
            self._lbl(suite_t("text.onboarding.email_label", "Correo electrónico *"), is_compact)
        )
        self._email = NMInput(
            suite_t("text.onboarding.email_placeholder", "correo@ejemplo.com"),
            modo=self._modo,
        )
        if is_compact:
            self._email.setFixedHeight(37)
            self._email.setFixedWidth(468)
            self._apply_compact_input_font(self._email)
        form_lay.addWidget(self._email)

        self._email_to_password_spacer = QSpacerItem(
            0,
            10 if is_compact else 10,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        form_lay.addItem(self._email_to_password_spacer)  # mockup: input margin-bottom 14px

        # ── Contraseña ────────────────────────────────────────────────────────
        form_lay.addWidget(
            self._lbl(
                suite_t("text.onboarding.password_label", "Contraseña * (mín. 6 caracteres)"),
                is_compact,
            )
        )
        self._code = NMInput(
            suite_t("text.onboarding.password_placeholder", "Contraseña de tu cuenta NeuroMood"),
            modo=self._modo,
        )
        self._code.setEchoMode(NMInput.EchoMode.Password)
        if is_compact:
            self._code.setFixedHeight(37)
            self._code.setFixedWidth(468)
            self._apply_compact_input_font(self._code)
        form_lay.addWidget(self._code)

        # (Hint "Se usa Supabase Auth..." eliminado — feedback owner v1.0:
        # información técnica interna, no aporta al usuario.)
        self._password_to_consent_spacer = QSpacerItem(
            0,
            11 if is_compact else 12,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        form_lay.addItem(self._password_to_consent_spacer)  # mockup: password margin-bottom 16px

        # ── Consentimiento: card secundaria ADN con shield icon ─────────────
        consent_card = QFrame()
        consent_card.setObjectName("ConsentCard")
        self._consent_card = consent_card
        if self._has_theme:
            is_dark = "dark" in self._modo
            # Mockup: card de consentimiento = <div class="card"
            # style="background:var(--surface-2)"> — surface-2 en ambos temas
            # (antes usaba surface/input → un escalón de color distinto al target).
            bg_col = self._t["surface2"]
            border_c = self._t["v3c"]("border", self._modo)
            border_css = (
                f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},45)"
                if is_dark
                else "rgba(28,34,24,0.10)"
            )
            consent_card.setStyleSheet(
                f"QFrame#ConsentCard {{ background-color: {bg_col}; "
                f"border: 1px solid {border_css}; "
                f"border-radius: 16px; }}"
            )
        else:
            _is_dark = "dark" in getattr(self, "_modo", "dark_hybrid")
            _bg_fb = self._fallback_color("bg_surface" if _is_dark else "bg_surface2")
            consent_card.setStyleSheet(
                f"QFrame {{ background-color: {_bg_fb}; "
                f"border: 1px solid {self._fallback_color('border')}; "
                "border-radius: 16px; }}"
            )
        cc_lay = QVBoxLayout(consent_card)
        self._consent_card_lay = cc_lay
        if is_compact:
            cc_lay.setContentsMargins(12, 8, 12, 8)
            cc_lay.setSpacing(5)
        else:
            cc_lay.setContentsMargins(16, 12, 16, 12)
            cc_lay.setSpacing(6)

        # Header con shield + título
        cc_head = QHBoxLayout()
        cc_head.setSpacing(8)
        try:
            from shared.icons_svg import nm_svg_pixmap

            shield_pix = nm_svg_pixmap(
                "shield",
                self._t.get("primary", self._fallback_color("primary"))
                if self._has_theme
                else self._fallback_color("primary"),
                size=16,
            )
            if shield_pix is not None:
                shield_lbl = QLabel()
                shield_lbl.setPixmap(shield_pix)
                shield_lbl.setStyleSheet("background: transparent;")
                cc_head.addWidget(shield_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        except Exception:
            pass
        cc_title = QLabel("Privacidad y consentimiento")
        cc_title.setObjectName("OnbCardTitle")
        if self._has_theme:
            cc_title.setFont(
                self._t["v3_font"]("size_caption", weight=self._t["TY"]["weight_semibold"])
            )
            cc_title.setStyleSheet(f"color: {self._t['text']}; background: transparent;")
        self._consent_title = cc_title
        cc_head.addWidget(cc_title)
        cc_head.addStretch()
        cc_lay.addLayout(cc_head)

        cc_body = QWidget()
        cc_body.setObjectName("OnbConsentBody")
        cc_body.setStyleSheet("background: transparent;")
        cc_body_lay = QVBoxLayout(cc_body)
        cc_body_lay.setContentsMargins(0, 0, 0, 0)
        cc_body_lay.setSpacing(6 if is_compact else 8)
        for paragraph in _CONSENT_SUMMARY_PARAGRAPHS:
            consent_txt = QLabel(paragraph)
            consent_txt.setObjectName("OnbConsentText")
            consent_txt.setWordWrap(True)
            if self._has_theme:
                consent_txt.setFont(
                    self._t["v3_font"](
                        11 if is_compact else 12,
                        weight=self._t["TY"]["weight_regular"],
                    )
                )
            else:
                _cfont = consent_txt.font()
                _cfont.setPixelSize(11 if is_compact else 12)
                consent_txt.setFont(_cfont)
            if is_compact:
                _stretch_font = consent_txt.font()
                _stretch_font.setStretch(95)
                _stretch_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
                consent_txt.setFont(_stretch_font)
            if self._has_theme:
                consent_txt.setStyleSheet(
                    f"color: {self._t['text2']}; background: transparent;"
                )
            else:
                consent_txt.setStyleSheet(f"color: {self._fallback_color('ink_secondary')};")
            consent_txt.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            cc_body_lay.addWidget(consent_txt)
        cc_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cc_body.setFixedHeight(74 if is_compact else 116)
        cc_lay.addWidget(cc_body, stretch=1)

        consent_card.setMinimumHeight(123 if is_compact else 162)
        consent_card.setMaximumHeight(123 if is_compact else 180)
        if is_compact:
            consent_card.setFixedWidth(468)
            try:
                from PyQt6.QtWidgets import QGraphicsDropShadowEffect

                card_shadow = QGraphicsDropShadowEffect(consent_card)
                card_shadow.setBlurRadius(6)
                card_shadow.setOffset(0, 2)
                card_shadow.setColor(QColor(49, 45, 39, 20))
                consent_card.setGraphicsEffect(card_shadow)
            except Exception:
                pass
        consent_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        form_lay.addWidget(consent_card, stretch=0)
        self._consent_to_check_spacer = None
        if is_compact:
            self._consent_to_check_spacer = QSpacerItem(
                0,
                8,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Fixed,
            )
            form_lay.addItem(self._consent_to_check_spacer)

        # ── Checkbox de aceptación fuera de la card legal (canónico) ───────
        # Mockup: el checkbox vive bajo la card, no dentro de ella.
        consent_row = QHBoxLayout()
        consent_row.setContentsMargins(2, 0, 0, 0)
        consent_row.setSpacing(9)  # mockup: gap:9px
        self._consent_check = _ConsentCheckBox(self._modo)
        consent_row.addWidget(self._consent_check, alignment=Qt.AlignmentFlag.AlignTop)

        consent_lbl = QLabel("Acepto los términos y la política de privacidad")
        consent_lbl.setObjectName("OnbConsentLabel")
        consent_lbl.setWordWrap(True)
        consent_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        consent_lbl.mouseReleaseEvent = lambda event: self._consent_check.setChecked(
            not self._consent_check.isChecked()
        )
        if self._has_theme:
            lbl_font_sz = "size_caption_xs" if is_compact else "size_small"
            consent_lbl.setFont(
                self._t["v3_font"](lbl_font_sz, weight=self._t["TY"]["weight_medium"])
            )
            consent_lbl.setStyleSheet(f"color: {self._t['text']}; background: transparent;")
        else:
            consent_font = QFont()
            consent_font.setPixelSize(11 if is_compact else 12)
            consent_lbl.setFont(consent_font)
            consent_lbl.setStyleSheet("background: transparent;")
        if is_compact:
            consent_lbl.setFixedHeight(22)
            consent_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        consent_row.addWidget(consent_lbl, stretch=1)

        form_lay.addLayout(consent_row)

        # Scroll area para el formulario: el contenido puede exceder 600px en
        # pantallas compactas o cuando la card legal es grande. Los botones viven
        # en footer_widget (fuera del scroll) y siempre quedan visibles.
        _form_scroll = QScrollArea()
        self._form_scroll = _form_scroll
        _form_scroll.setWidgetResizable(True)
        _form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        _form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if is_compact:
            _form_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        from shared.theme_qt import stylesheet_scrollarea

        _form_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            + stylesheet_scrollarea(self._modo)
        )
        _form_scroll.setWidget(form_widget)
        card_lay.addWidget(_form_scroll, stretch=1)

        # Footer section (fixed at the bottom)
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background: transparent;")
        footer_lay = QVBoxLayout(footer_widget)
        self._footer_lay = footer_lay
        # Mismos márgenes laterales que el form (full-bleed alineado).
        if is_compact:
            footer_lay.setContentsMargins(24, 2, 24, 37)
            footer_lay.setSpacing(12)
        else:
            footer_lay.setContentsMargins(32, 4, 32, 18)
            footer_lay.setSpacing(6)

        # ── Error ─────────────────────────────────────────────────────────────
        self._error_lbl = QLabel("")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setMinimumHeight(14 if is_compact else 18)
        if self._has_theme:
            self._error_lbl.setFont(
                self._t["v3_font"](
                    "size_eyebrow" if is_compact else "size_caption",
                    weight=self._t["TY"]["weight_regular"] if is_compact else self._t["TY"]["weight_medium"],
                )
            )
        else:
            err_font = QFont()
            err_font.setPixelSize(11 if is_compact else 12)
            self._error_lbl.setFont(err_font)
        if self._has_theme:
            self._error_lbl.setStyleSheet(f"color: {self._t['danger']}; background: transparent;")
        else:
            _danger_fb = self._fallback_color("danger_ink")
            self._error_lbl.setStyleSheet(f"color: {_danger_fb}; background: transparent;")
        if is_compact:
            err_stretch = self._error_lbl.font()
            err_stretch.setStretch(95)
            err_stretch.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            self._error_lbl.setFont(err_stretch)
        footer_lay.addWidget(self._error_lbl)

        # ── Botones - Handoff §5.1: secondary "Crear cuenta" + primary "Iniciar" ─
        # ADN: primary sage en light, lavanda en dark.
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        # Link de recuperación de contraseña: Supabase envía un email para
        # restablecerla (la pass está hasheada, no se puede reenviar en claro).
        self._forgot_link = QLabel()
        self._forgot_link.setOpenExternalLinks(False)
        self._forgot_link.setFont(self._error_lbl.font())
        self._forgot_link.setStyleSheet("background: transparent;")
        link_color = (
            self._t["v3c"]("primary", self._modo).name()
            if self._has_theme
            else self._fallback_color("primary")
        )
        self._forgot_link.setText(
            f'<a href="#" style="color:{link_color}; text-decoration:none;">'
            f"{suite_t('text.onboarding.forgot_password', '¿Olvidaste tu contraseña?')}</a>"
        )
        self._forgot_link.linkActivated.connect(self._on_forgot_password)
        btn_row.addWidget(self._forgot_link, 0, Qt.AlignmentFlag.AlignVCenter)
        btn_row.addStretch()

        btn_sz = "sm" if is_compact else "md"
        btn_width = 112 if is_compact else 140
        self._btn_signup = NMButton(
            suite_t("text.onboarding.signup_btn", "Crear cuenta"),
            variant="secondary",
            size=btn_sz,
            width=btn_width,
        )
        if is_compact:
            signup_font = self._btn_signup.font()
            signup_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            self._btn_signup.setFont(signup_font)
        self._btn_signup._disabled_opacity = 1.0
        self._btn_signup.clicked.connect(lambda: self._on_accept("signup"))
        btn_row.addWidget(self._btn_signup)

        self._btn_ok = NMButton(
            suite_t("text.onboarding.login_btn", "Iniciar sesión"),
            variant="primary",
            size=btn_sz,
            width=btn_width,
        )
        if is_compact:
            ok_font = self._btn_ok.font()
            ok_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            self._btn_ok.setFont(ok_font)
        self._btn_ok._disabled_opacity = 0.5
        self._btn_ok.setDefault(True)
        self._btn_ok.clicked.connect(lambda: self._on_accept("login"))
        btn_row.addWidget(self._btn_ok)
        footer_lay.addLayout(btn_row)
        self._consent_check.toggled.connect(self._sync_action_buttons)
        self._sync_action_buttons()

        card_lay.addWidget(footer_widget)

    def _sync_action_buttons(self) -> None:
        enabled = bool(getattr(self, "_consent_check", None) and self._consent_check.isChecked())
        if hasattr(self, "_btn_signup"):
            self._btn_signup.setEnabled(enabled)
        if hasattr(self, "_btn_ok"):
            self._btn_ok.setEnabled(enabled)

    def _refresh_card_theme(self) -> None:
        """Re-aplica los estilos tematizados al cambiar light/dark.

        Necesario porque la card (QFrame) y los labels de título fijan
        stylesheets con tokens del tema actual en _build_ui; cuando el
        usuario hace toggle desde la titlebar, _init_theme refresca los
        tokens del diálogo pero NO toca los hijos. Aquí los
        reaplicamos contra la paleta ya actualizada.
        """
        if not self._has_theme:
            return
        t = self._t
        is_dark = "dark" in self._modo
        border_c = t["v3c"]("border", self._modo)
        border_css = (
            f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},{border_c.alpha()})"
        )
        # Fondo del diálogo (= color de la card, sin bandas laterales).
        try:
            self.setStyleSheet(f"OnboardingDialog {{ background-color: {t['surface']}; }}")
        except Exception:
            pass
        # Frames: AuthCard (full-bleed) + ConsentCard.
        try:
            card_radius = 22 if _is_windows_11_or_newer() else 0
            for frame in self.findChildren(QFrame):
                name = frame.objectName()
                if name == "AuthCard":
                    auth_bg = t["surface"]
                    if "light" in self._modo:
                        auth_bg = (
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                            "stop:0 #F4F0E5, stop:0.34 #F5F1E7, "
                            "stop:0.72 #FBF8F1, stop:1 #FBF8F1)"
                        )
                    frame.setStyleSheet(
                        f"QFrame#AuthCard {{ background: {auth_bg}; "
                        f"border: 1px solid {border_css}; border-radius: {card_radius}px; }}"
                    )
                elif name == "ConsentCard":
                    bg_col = t["surface2"]
                    cc_border = (
                        f"rgba({border_c.red()},{border_c.green()},{border_c.blue()},45)"
                        if is_dark else "rgba(28,34,24,0.10)"
                    )
                    frame.setStyleSheet(
                        f"QFrame#ConsentCard {{ background-color: {bg_col}; "
                        f"border: 1px solid {cc_border}; border-radius: 16px; }}"
                    )
        except Exception:
            pass
        # Scrollarea del consentimiento.
        try:
            from shared.theme_qt import stylesheet_scrollarea
            for sa in self.findChildren(QScrollArea):
                sa.setStyleSheet(stylesheet_scrollarea(self._modo))
        except Exception:
            pass
        try:
            if hasattr(self, "_consent_check") and hasattr(self._consent_check, "set_modo"):
                self._consent_check.set_modo(self._modo)
        except Exception:
            pass
        # Labels crudos por rol (objectName) + títulos.
        role_color = {
            "OnbSub": t["mute"],
            "OnbField": t["text2"],
            "OnbCardTitle": t["text"],
            "OnbConsentText": t["text2"],
            "OnbConsentLabel": t["text"],
        }
        try:
            for lbl in self.findChildren(QLabel):
                name = lbl.objectName()
                if name in role_color:
                    lbl.setStyleSheet(f"color: {role_color[name]}; background: transparent;")
        except Exception:
            pass
        # Título de 3 spans "NeuroMood Suite": el rich-text fija los colores brand/
        # ink-3 al construirse; sin reconstruir el HTML, "Mood" quedaba con el verde
        # del tema anterior tras el toggle (bug de hot-reload).
        try:
            if hasattr(self, "_title_lbl"):
                ink_c = t["text"]
                brand_c = t["primary"]
                ink3_c = t["text3"]
                self._title_lbl.setText(
                    f"<span style='color:{ink_c};'>Neuro</span>"
                    f"<span style='color:{brand_c};'>Mood</span>"
                    f" <span style='color:{ink3_c}; font-style:italic;'>Suite</span>"
                )
        except Exception:
            pass
        # Error + link de recuperación (mockup: "¿Olvidaste...?" = color brand).
        try:
            if hasattr(self, "_error_lbl"):
                self._error_lbl.setStyleSheet(f"color: {t['danger']}; background: transparent;")
            if hasattr(self, "_forgot_link"):
                link_color = t["primary"]
                self._forgot_link.setText(
                    f'<a href="#" style="color:{link_color}; text-decoration:none;">'
                    f"{suite_t('text.onboarding.forgot_password', '¿Olvidaste tu contraseña?')}</a>"
                )
        except Exception:
            pass

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

    def _lbl(self, text: str, is_compact: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("OnbField")
        if self._has_theme:
            sz = "size_caption_xs" if is_compact else "size_caption"
            lbl.setFont(self._t["v3_font"](sz, weight=self._t["TY"]["weight_medium"]))
            lbl.setStyleSheet(f"color: {self._t['text2']}; background: transparent;")
        else:
            lbl_font = QFont()
            lbl_font.setPixelSize(11 if is_compact else 12)
            lbl.setFont(lbl_font)
            lbl.setStyleSheet("background: transparent;")
        if is_compact:
            lbl.setFixedHeight(14)
            lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            lbl_font = lbl.font()
            lbl_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            lbl.setFont(lbl_font)
        return lbl

    def _apply_compact_input_font(self, line: NMInput) -> None:
        font = line.font()
        font.setStretch(90)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        line.setFont(font)
        line.setStyleSheet(line.styleSheet().replace("font-size: 14px;", "font-size: 12px;"))

    def _on_accept(self, action: str):
        nombre = self._name.text().strip()
        email = self._email.text().strip()
        password = self._code.text().strip()

        # Limpiar estados de error visuales de los inputs antes de re-validar.
        self._name.clear_error()
        self._email.clear_error()
        if hasattr(self, "_name_error_ring"):
            self._name_error_ring.hide()
        # Resetear color a danger por si venía un mensaje verde de recuperación.
        self._set_feedback("")

        if not nombre:
            # Mockup onboarding error: input Nombre con borde rose + halo rose-soft
            # + mensaje rose "Completá tu nombre para crear la cuenta."
            self._name.set_error("Nombre requerido")
            self._apply_compact_feedback_visual_tuning()
            self._error_lbl.setText(
                suite_t(
                    "text.onboarding.error_name_required",
                    "Completá tu nombre para crear la cuenta.",
                )
            )
            self._name.setFocus()
            self._name.setGraphicsEffect(None)
            self._show_name_error_ring()
            return
        if "@" not in email or "." not in email:
            self._email.set_error("Email inválido")
            self._error_lbl.setText(suite_t("text.onboarding.error_invalid_email", "Ingresá un email válido."))
            self._email.setFocus()
            return
        if len(password) < 6:
            self._error_lbl.setText(
                suite_t(
                    "text.onboarding.error_short_password",
                    "La contraseña debe tener al menos 6 caracteres.",
                )
            )
            self._code.setFocus()
            return
        if not self._consent_check.isChecked():
            self._error_lbl.setText(
                suite_t("text.onboarding.error_terms_required", "Debés aceptar los términos para continuar.")
            )
            return

        self._error_lbl.setText("")
        self._btn_ok.setEnabled(False)
        self._btn_signup.setEnabled(False)
        self._btn_ok.setText(suite_t("text.onboarding.connecting_btn", "Conectando..."))
        self._btn_signup.setText(suite_t("text.onboarding.connecting_btn", "Conectando..."))

        try:
            self._save(nombre, email, password, action)
            self.accept()
        except Exception as exc:
            self._error_lbl.setText(f"Error al guardar la configuración: {str(exc)[:220]}")
            self._btn_ok.setText(suite_t("text.onboarding.login_btn", "Iniciar sesión"))
            self._btn_signup.setText(suite_t("text.onboarding.signup_btn", "Crear cuenta"))
            self._sync_action_buttons()

    def _apply_compact_feedback_visual_tuning(self) -> None:
        """Ajustes compactos propios de estados con feedback visible.

        Recovery y onboarding-error agregan una línea de feedback y un halo de
        input. Con el layout base de onboarding eso deja pequeñas bandas
        estructurales fuera del gate. Estos cambios replican el balance CSS de
        esos estados sin mover el onboarding base.
        """
        if not (self.width() <= 560 or self.height() < 620):
            return

        def _spacer(attr: str, height: int) -> None:
            sp = getattr(self, attr, None)
            if sp is not None:
                sp.changeSize(
                    0,
                    height,
                    QSizePolicy.Policy.Minimum,
                    QSizePolicy.Policy.Fixed,
                )

        _spacer("_brand_to_sub_spacer", 0)
        _spacer("_sub_to_name_spacer", 10)
        _spacer("_name_to_email_spacer", 9)
        _spacer("_email_to_password_spacer", 10)
        _spacer("_password_to_consent_spacer", 9)
        _spacer("_consent_to_check_spacer", 8)

        brand_row = getattr(self, "_brand_row", None)
        if brand_row is not None:
            brand_row.setSpacing(5)

        form_scroll = getattr(self, "_form_scroll", None)
        if form_scroll is not None:
            form_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        form_lay = getattr(self, "_form_lay", None)
        if form_lay is not None:
            form_lay.setContentsMargins(24, 18, 42, 4)

        for input_widget in (
            getattr(self, "_name", None),
            getattr(self, "_email", None),
            getattr(self, "_code", None),
        ):
            if input_widget is not None:
                input_widget.setFixedHeight(36)
                input_widget.setFixedWidth(471)

        consent_card = getattr(self, "_consent_card", None)
        if consent_card is not None:
            consent_card.setFixedWidth(470)
            consent_card.setMinimumHeight(121)
            consent_card.setMaximumHeight(121)

        consent_lay = getattr(self, "_consent_card_lay", None)
        if consent_lay is not None:
            consent_lay.setContentsMargins(12, 12, 12, 8)

        consent_title = getattr(self, "_consent_title", None)
        if consent_title is not None:
            consent_title.setFixedHeight(18)
            consent_title.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )

        footer_lay = getattr(self, "_footer_lay", None)
        if footer_lay is not None:
            footer_lay.setContentsMargins(24, 0, 24, 39)

        for lay in (
            getattr(self, "_form_lay", None),
            consent_lay,
            footer_lay,
            self.layout(),
        ):
            if lay is not None:
                lay.invalidate()
        self.updateGeometry()

    def _show_email_focus_ring(self) -> None:
        """Pinta el anillo 3px brand-soft canónico detrás del email (campo activo
        del flujo de recuperación). Ver `_FocusRingOverlay`."""
        if not hasattr(self, "_email"):
            return
        parent = self._email.parentWidget()
        if parent is None:
            return
        if self._has_theme:
            soft = self._t["v3c"]("primary_soft", self._modo)
        else:
            soft = QColor(self._fallback_color("primary"))
            soft.setAlpha(33)  # ≈ brand-soft .13
        ring = getattr(self, "_email_focus_ring", None)
        if ring is None:
            from shared.theme_qt import LAYOUT

            ring = _FocusRingOverlay(soft, int(LAYOUT["radius_input"]), pad=0, parent=parent)
            self._email_focus_ring = ring
        else:
            ring._soft = QColor(soft)
        geo = self._email.geometry()
        pad = ring._pad
        ring.setGeometry(
            geo.x() - pad, geo.y() - pad, geo.width() + 2 * pad, geo.height() + 2 * pad
        )
        ring.stackUnder(self._email)
        ring.show()
        ring.update()

    def _show_name_error_ring(self) -> None:
        """Pinta el halo rose-soft canónico del campo Nombre en error."""
        if not hasattr(self, "_name"):
            return
        parent = self._name.parentWidget()
        if parent is None:
            return
        if self._has_theme:
            soft = self._t["v3c"]("dangerSoft", self._modo)
        else:
            soft = QColor(self._fallback_color("danger_ink"))
            soft.setAlpha(41)
        ring = getattr(self, "_name_error_ring", None)
        if ring is None:
            from shared.theme_qt import LAYOUT

            ring = _FocusRingOverlay(soft, int(LAYOUT["radius_input"]), pad=2, parent=parent)
            self._name_error_ring = ring
        else:
            ring._soft = QColor(soft)
        geo = self._name.geometry()
        pad = ring._pad
        ring.setGeometry(
            geo.x() - pad, geo.y() - pad, geo.width() + 2 * pad, geo.height() + 2 * pad
        )
        ring.stackUnder(self._name)
        ring.show()
        ring.update()

    def _set_feedback(self, msg: str, *, ok: bool = False, kind: str = ""):
        """Muestra un mensaje en la línea de estado.

        kind:
          - "" (default): ok=success, no ok=danger (comportamiento histórico)
          - "accent": usa accent token (peach/copper) — mockup recover línea 1316
          - "danger": fuerza danger token (rose)
          - "success": fuerza success token (mind)
        """
        self._error_lbl.setText(msg)
        if kind == "accent":
            color = (
                self._t["v3c"]("accent", self._modo).name()
                if self._has_theme
                else self._fallback_color("accent")
            )
        elif kind == "danger":
            color = (
                self._t["v3c"]("danger", self._modo).name()
                if self._has_theme
                else self._fallback_color("danger_ink")
            )
        elif kind == "success" or ok:
            color = (
                self._t["v3c"]("success", self._modo).name()
                if self._has_theme
                else self._fallback_color("success_ink")
            )
        else:
            color = (
                self._t["v3c"]("danger", self._modo).name()
                if self._has_theme
                else self._fallback_color("danger_ink")
            )
        self._error_lbl.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def _on_forgot_password(self):
        """Pide a Supabase que envíe un email de restablecimiento de contraseña."""
        email = self._email.text().strip()
        if "@" not in email or "." not in email:
            self._set_feedback(
                "Escribí tu email arriba y tocá de nuevo para recuperar la contraseña.",
                kind="accent",  # mockup línea 1316: color:var(--accent)
            )
            self._recover_prompt_active = True
            self._apply_compact_feedback_visual_tuning()
            # El email es el campo activo del flujo de recuperación: debe mostrar
            # su anillo de foco canónico (brand-line + halo brand-soft,
            # `.input:focus` línea 304 / recover línea 1425). En captura
            # offscreen la ventana inactiva
            # no concede foco visual, así que se fuerza el anillo explícitamente.
            # (El bloqueo previo de `setGraphicsEffect` era un resto del commit
            # fraudulento b0286be y suprimía el anillo genuino.)
            self._email.setFocus()
            try:
                self._email.set_focus_ring(True)
                self._show_email_focus_ring()
            except Exception:
                pass
            self.update()
            return
        self._forgot_link.setEnabled(False)
        self._set_feedback("Enviando email de recuperación...", ok=True)
        QApplication.processEvents()
        try:
            client = self._supabase_client()
            auth = client.auth
            # supabase-py v2: reset_password_for_email; fallback a nombres viejos.
            for _name in ("reset_password_for_email", "reset_password_email"):
                fn = getattr(auth, _name, None)
                if callable(fn):
                    fn(email)
                    break
            else:
                raise RuntimeError("El cliente de Supabase no soporta recuperación por email.")
            self._set_feedback(
                "Listo: te enviamos un enlace a tu email para restablecer la contraseña.",
                ok=True,
            )
        except Exception as exc:
            self._set_feedback(f"No se pudo enviar el email: {str(exc)[:160]}")
        finally:
            self._forgot_link.setEnabled(True)

    def _supabase_client(self):
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Falta instalar el paquete supabase.") from exc
        url, key = supabase_url(), supabase_key()
        if not url or not key:
            raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_KEY en el entorno o .env runtime.")
        return create_client(url, key)

    def _auth(self, email: str, password: str, action: str):
        client = self._supabase_client()
        if action == "signup":
            res = client.auth.sign_up({"email": email, "password": password})
        else:
            res = client.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None)
        session = getattr(res, "session", None)
        if not user or not getattr(user, "id", ""):
            raise RuntimeError("Supabase no devolvió un usuario válido.")
        if not session or not getattr(session, "access_token", ""):
            raise RuntimeError("La cuenta requiere confirmación por email antes de continuar.")
        return client, user, session

    def _save(self, nombre: str, email: str, password: str, action: str):
        from shared.db import guardar_config
        from shared.identidad import guardar_password

        client, user, session = self._auth(email, password, action)
        pid = str(user.id)
        access_token = getattr(session, "access_token", "")
        refresh_token = getattr(session, "refresh_token", "")
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            try:
                client.postgrest.auth(access_token)
            except Exception:
                pass

        guardar_config("patient_id", pid)
        guardar_config("patient_name", nombre.strip())
        guardar_config("patient_email", email)
        guardar_config("auth_user_id", pid)
        guardar_config("auth_access_token", access_token)
        guardar_config("auth_refresh_token", refresh_token)
        # Cuenta (re)vinculada: si esta instalación venía de un paciente
        # desvinculado por el profesional, la identidad nueva rehabilita el sync.
        guardar_config("sync_unlinked", "0")
        guardar_password(password, pid)

        try:
            client.table("patients").upsert(
                {
                    "patient_id": pid,
                    "patient_name": nombre.strip(),
                    "pwd": "",
                    "email": email,
                    "perm_checklist_activacion": True,
                    "perm_checklist_manual": True,
                    "perm_temporizador_manual": True,
                    "perm_recordatorios_manual": True,
                }
            ).execute()
        except Exception:
            # Schema viejo sin columna email: reintento mínimo sin ella.
            try:
                client.table("patients").upsert(
                    {
                        "patient_id": pid,
                        "patient_name": nombre.strip(),
                        "pwd": "",
                        "perm_checklist_activacion": True,
                        "perm_checklist_manual": True,
                        "perm_temporizador_manual": True,
                        "perm_recordatorios_manual": True,
                    }
                ).execute()
            except Exception:
                pass

        self._write_consent_files(client, pid, email)

    def _write_consent_files(self, client, patient_id: str, email: str):
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        nm_dir = pathlib.Path(appdata) / "NeuroMood"
        nm_dir.mkdir(parents=True, exist_ok=True)

        now_iso = datetime.now(timezone.utc).isoformat()

        payload: dict = {
            "user_id": patient_id,
            "patient_id": patient_id,
            "email": email,
            "accepted_at_utc": now_iso,
            "product_name": "NeuroMood Suite",
            "neuromood_suite_version": _SUITE_VERSION,
            "instalador_suite_version": _SUITE_VERSION,
            "disclaimer_version": _DISCLAIMER_VERSION,
            "privacy_version": _PRIVACY_VERSION,
            "disclaimer_text_hash": _DISCLAIMER_TEXT_HASH,
            "privacy_text_hash": _PRIVACY_TEXT_HASH,
            "consent_scope": _CONSENT_SCOPE,
            "status": "vigente",
        }

        encoded = json.dumps(payload, ensure_ascii=False, indent=2)
        sent_remote = False
        try:
            existing = (
                client.table("legal_consents")
                .select("id")
                .eq("user_id", patient_id)
                .eq("disclaimer_version", _DISCLAIMER_VERSION)
                .eq("privacy_version", _PRIVACY_VERSION)
                .eq("disclaimer_text_hash", _DISCLAIMER_TEXT_HASH)
                .limit(1)
                .execute()
            )
            if getattr(existing, "data", None):
                sent_remote = True
            else:
                client.table("legal_consents").insert(payload).execute()
                sent_remote = True
        except Exception:
            sent_remote = False

        # legal_consent.json - gate de onboarding local.
        (nm_dir / "legal_consent.json").write_text(encoded, encoding="utf-8")

        pending = nm_dir / "pending_consent.json"
        if sent_remote:
            if pending.exists():
                pending.unlink()
        elif not pending.exists():
            pending.write_text(encoded, encoding="utf-8")
