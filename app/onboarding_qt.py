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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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
_DISCLAIMER_VERSION = DISCLAIMER_VERSION
_PRIVACY_VERSION = PRIVACY_VERSION
_SUITE_VERSION = SUITE_VERSION
_CONSENT_SCOPE = CONSENT_SCOPE
_DISCLAIMER_TEXT_HASH = DISCLAIMER_TEXT_HASH
_PRIVACY_TEXT_HASH = PRIVACY_TEXT_HASH


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
        self._init_theme()
        self._configure_responsive_window()
        self._build_ui()
        # P2.B: el chrome NM se inserta DESPUÉS de _build_ui, cuando el layout ya
        # existe. Si se hace antes (como estaba), apply_child_window_chrome no
        # encuentra layout y deja la barra huérfana fuera de él → ventana
        # frameless sin titlebar usable, barra flotando sobre el contenido.
        self._apply_window_chrome()

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
                "danger": _v3c("danger", modo).name(),
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
                title="NeuroMood · Configuración inicial",
                modo=self._modo,
                show_theme_toggle=True,
                # Ventana de tamaño fijo: solo "—" minimizar y "✕" cerrar.
                show_maximize=False,
            )
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
            card_radius = 22 if _is_windows_11_or_newer() else 0
            card.setStyleSheet(
                f"QFrame#AuthCard {{ background: {self._t['surface']}; "
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
        is_compact = self.height() <= 600
        # Márgenes generosos full-bleed (la ventana es la card): aire lateral
        # premium sin doble borde.
        if is_compact:
            form_lay.setContentsMargins(20, 14, 20, 4)
            form_lay.setSpacing(4)
        else:
            form_lay.setContentsMargins(24, 18, 24, 8)
            form_lay.setSpacing(6)

        # ── Logo de marca real (HANDOFF F0.3: logo completo en onboarding) ────
        # Theme-aware: "Neuro" nunca desaparece (oscuro en light, blanco en dark).
        try:
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtCore import Qt as _Qt
            from shared.assets import obtener_logo

            _logo_path = obtener_logo(self._modo)
            if os.path.exists(_logo_path):
                _pm = QPixmap(_logo_path)
                if not _pm.isNull():
                    _logo = QLabel()
                    _logo.setPixmap(
                        _pm.scaledToWidth(
                            150 if is_compact else 188, _Qt.TransformationMode.SmoothTransformation
                        )
                    )
                    _logo.setStyleSheet("background: transparent;")
                    form_lay.addWidget(_logo)
                    form_lay.addSpacing(2 if is_compact else 6)
        except Exception:
            pass

        # (Eyebrow "BIENVENIDA · CONFIGURACIÓN" eliminado — feedback owner v1.0:
        # rótulo técnico redundante; el saludo real es el título de abajo.)

        # ── Título - Handoff §5.1: hero serif (Newsreader display) ────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(4 if is_compact else 8)
        title_main = QLabel(suite_t("text.onboarding.title_main", "Bienvenido a NeuroMood"))
        title_tail = QLabel(suite_t("text.onboarding.title_suffix", "Suite"))
        if self._has_theme:
            title_size = "size_h2" if is_compact else "size_h1"
            f_disp = self._t["v3_font"](
                title_size, weight=self._t["TY"]["weight_medium"], serif=True
            )
            f_it = self._t["v3_font"](
                title_size, weight=self._t["TY"]["weight_medium"], serif=True, italic=True
            )
            title_main.setFont(f_disp)
            title_tail.setFont(f_it)
            # Color EXPLÍCITO: sin él, el QLabel hereda el negro por defecto
            # (el onboarding corre antes de la paleta global de la app) y el
            # saludo era invisible sobre fondo oscuro — feedback owner v1.0.
            title_main.setStyleSheet(
                f"color: {self._t['text']}; background: transparent;"
            )
            title_tail.setStyleSheet(f"color: {self._t['primary']}; background: transparent;")
        else:
            f = QFont()
            f.setPixelSize(16 if is_compact else 22)
            f.setBold(False)
            title_main.setFont(f)
            title_tail.setFont(f)
            fb_text = self._fallback_color("ink_primary")
            title_main.setStyleSheet(f"color: {fb_text};")
            title_tail.setStyleSheet(f"color: {fb_text};")
        title_row.addWidget(title_main)
        title_row.addWidget(title_tail)
        title_row.addStretch()
        form_lay.addLayout(title_row)

        sub = QLabel(
            suite_t(
                "text.onboarding.subtitle",
                "Vinculá tu cuenta de NeuroMood. Tus datos se mantienen cifrados y bajo tu control.",
            )
        )
        sub.setObjectName("OnbSub")
        sub.setWordWrap(True)
        sub_px = 11 if is_compact else 12
        if self._has_theme:
            sub.setFont(
                self._t["v3_font"](
                    "size_eyebrow" if is_compact else "size_caption",
                    weight=self._t["TY"]["weight_medium"],
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
        form_lay.addWidget(sub)

        form_lay.addSpacing(2 if is_compact else 8)

        # ── Nombre ────────────────────────────────────────────────────────────
        form_lay.addWidget(self._lbl(suite_t("text.onboarding.name_label", "Nombre *"), is_compact))
        self._name = NMInput(suite_t("text.onboarding.name_placeholder", "Tu nombre"), modo=self._modo)
        if is_compact:
            self._name.setMinimumHeight(34)
        form_lay.addWidget(self._name)

        form_lay.addSpacing(0 if is_compact else 4)

        # ── Email ─────────────────────────────────────────────────────────────
        form_lay.addWidget(
            self._lbl(suite_t("text.onboarding.email_label", "Correo electrónico *"), is_compact)
        )
        self._email = NMInput(
            suite_t("text.onboarding.email_placeholder", "correo@ejemplo.com"),
            modo=self._modo,
        )
        if is_compact:
            self._email.setMinimumHeight(34)
        form_lay.addWidget(self._email)

        form_lay.addSpacing(0 if is_compact else 4)

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
            self._code.setMinimumHeight(34)
        form_lay.addWidget(self._code)

        # (Hint "Se usa Supabase Auth..." eliminado — feedback owner v1.0:
        # información técnica interna, no aporta al usuario.)
        form_lay.addSpacing(2 if is_compact else 8)

        # ── Consentimiento: card secundaria ADN con shield icon ─────────────
        consent_card = QFrame()
        consent_card.setObjectName("ConsentCard")
        if self._has_theme:
            is_dark = "dark" in self._modo
            bg_col = self._t["surface"] if is_dark else self._t["input"]
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
        if is_compact:
            cc_lay.setContentsMargins(12, 8, 12, 8)
            cc_lay.setSpacing(6)
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
        cc_head.addWidget(cc_title)
        cc_head.addStretch()
        cc_lay.addLayout(cc_head)

        cc_body = QScrollArea()
        cc_body.setWidgetResizable(True)
        cc_body.setFrameShape(QFrame.Shape.NoFrame)
        cc_body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Scrollbar canónico (clínico, neutro, 10px) en vez del handle lavanda
        # brillante de 6px que violaba el ADN.
        from shared.theme_qt import stylesheet_scrollarea

        cc_body.setStyleSheet(stylesheet_scrollarea(self._modo))

        consent_txt = QLabel(_CONSENT_TEXT)
        consent_txt.setObjectName("OnbConsentText")
        consent_txt.setWordWrap(True)
        # Fuente vía QFont (no font-size CSS): el alto del visor se calcula con
        # fontMetrics y deben coincidir para no cortar líneas a la mitad.
        _cfont = consent_txt.font()
        _cfont.setPixelSize(11 if is_compact else 12)
        consent_txt.setFont(_cfont)
        if self._has_theme:
            consent_txt.setStyleSheet(
                f"color: {self._t['text2']}; background: transparent;"
            )
        else:
            consent_txt.setStyleSheet(f"color: {self._fallback_color('ink_secondary')};")
        cc_body.setWidget(consent_txt)
        # Área de lectura GRANDE (feedback owner v1.0): mínimo 4-6 líneas
        # completas y EXPANDIBLE — absorbe el espacio que antes moría en
        # stretches arriba/abajo de la card. La base mínima alineada a líneas
        # enteras evita que el piso del visor corte una línea a la mitad.
        _lines = 4 if is_compact else 6
        _view_h = consent_txt.fontMetrics().lineSpacing() * _lines
        cc_body.setMinimumHeight(_view_h)
        cc_body.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        cc_lay.addWidget(cc_body, stretch=1)
        cc_lay.addSpacing(4)

        # Split checkbox and text to ensure full word wrapping and accessibility
        consent_row = QHBoxLayout()
        consent_row.setContentsMargins(0, 0, 0, 0)
        consent_row.setSpacing(8)
        self._consent_check = QCheckBox()
        self._consent_check.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._has_theme:
            self._consent_check.setStyleSheet("QCheckBox { background: transparent; }")
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
        consent_row.addWidget(consent_lbl, stretch=1)
        cc_lay.addLayout(consent_row)

        # El consentimiento absorbe el alto sobrante (contenido top-aligned,
        # sin stretches muertos arriba/abajo — feedback owner v1.0).
        form_lay.addWidget(consent_card, stretch=1)

        card_lay.addWidget(form_widget, stretch=1)

        # Footer section (fixed at the bottom)
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background: transparent;")
        footer_lay = QVBoxLayout(footer_widget)
        # Mismos márgenes laterales que el form (full-bleed alineado).
        if is_compact:
            footer_lay.setContentsMargins(28, 2, 28, 12)
            footer_lay.setSpacing(4)
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
                    weight=self._t["TY"]["weight_medium"],
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
            self._t["v3c"]("aqua", self._modo).name()
            if self._has_theme
            else self._fallback_color("teal")
        )
        self._forgot_link.setText(
            f'<a href="#" style="color:{link_color}; text-decoration:none;">'
            f"{suite_t('text.onboarding.forgot_password', '¿Olvidaste tu contraseña?')}</a>"
        )
        self._forgot_link.linkActivated.connect(self._on_forgot_password)
        btn_row.addWidget(self._forgot_link, 0, Qt.AlignmentFlag.AlignVCenter)
        btn_row.addStretch()

        btn_sz = "sm" if is_compact else "md"
        self._btn_signup = NMButton(
            suite_t("text.onboarding.signup_btn", "Crear cuenta"),
            variant="secondary",
            size=btn_sz,
            width=140,
        )
        self._btn_signup.clicked.connect(lambda: self._on_accept("signup"))
        btn_row.addWidget(self._btn_signup)

        self._btn_ok = NMButton(
            suite_t("text.onboarding.login_btn", "Iniciar sesión"),
            variant="gradient",
            size=btn_sz,
            width=140,
        )
        self._btn_ok.setDefault(True)
        self._btn_ok.clicked.connect(lambda: self._on_accept("login"))
        btn_row.addWidget(self._btn_ok)
        footer_lay.addLayout(btn_row)

        card_lay.addWidget(footer_widget)

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
                    frame.setStyleSheet(
                        f"QFrame#AuthCard {{ background: {t['surface']}; "
                        f"border: 1px solid {border_css}; border-radius: {card_radius}px; }}"
                    )
                elif name == "ConsentCard":
                    bg_col = t["surface"] if is_dark else t["input"]
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
                elif lbl.text() == "Bienvenido a NeuroMood":
                    lbl.setStyleSheet(f"color: {t['text']}; background: transparent;")
                elif lbl.text() == suite_t("text.onboarding.title_suffix", "Suite"):
                    lbl.setStyleSheet(f"color: {t['primary']}; background: transparent;")
        except Exception:
            pass
        # Error + link de recuperación.
        try:
            if hasattr(self, "_error_lbl"):
                self._error_lbl.setStyleSheet(f"color: {t['danger']}; background: transparent;")
            if hasattr(self, "_forgot_link"):
                link_color = t["v3c"]("aqua", self._modo).name()
                self._forgot_link.setText(
                    f'<a href="#" style="color:{link_color}; text-decoration:none;">'
                    f"{suite_t('text.onboarding.forgot_password', '¿Olvidaste tu contraseña?')}</a>"
                )
        except Exception:
            pass

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
        return lbl

    def _on_accept(self, action: str):
        nombre = self._name.text().strip()
        email = self._email.text().strip()
        password = self._code.text().strip()

        # Resetear color a danger por si venía un mensaje verde de recuperación.
        self._set_feedback("")

        if not nombre:
            self._error_lbl.setText(suite_t("text.onboarding.error_name_required", "El nombre es obligatorio."))
            self._name.setFocus()
            return
        if "@" not in email or "." not in email:
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
            self._btn_ok.setEnabled(True)
            self._btn_signup.setEnabled(True)
            self._btn_ok.setText(suite_t("text.onboarding.login_btn", "Iniciar sesión"))
            self._btn_signup.setText(suite_t("text.onboarding.signup_btn", "Crear cuenta"))

    def _set_feedback(self, msg: str, *, ok: bool = False):
        """Muestra un mensaje en la línea de estado: verde si ok, rojo si error."""
        self._error_lbl.setText(msg)
        if self._has_theme:
            key = "success" if ok else "danger"
            color = self._t["v3c"](key, self._modo).name()
        else:
            if ok:
                color = self._fallback_color("success_ink")
            else:
                color = self._fallback_color("danger_ink")
        self._error_lbl.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

    def _on_forgot_password(self):
        """Pide a Supabase que envíe un email de restablecimiento de contraseña."""
        email = self._email.text().strip()
        if "@" not in email or "." not in email:
            self._set_feedback("Escribí tu email arriba y tocá de nuevo para recuperar la contraseña.")
            self._email.setFocus()
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
