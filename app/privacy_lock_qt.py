"""
app/privacy_lock_qt.py — Pantalla de bloqueo por PIN (F3.A)

Flujo:
  1. NeuroMoodApp llama ``check_lock(parent)`` al arrancar.
  2. Si privacy_lock_enabled=0 → retorna True inmediatamente (sin UI).
  3. Si hay lock temporal (privacy_lock_until en el futuro) → muestra
     cuántos minutos quedan y sale.
  4. Si enabled=1 → muestra PrivacyLockScreen como QDialog modal.
     - 3 intentos fallidos → bloqueo 5 min (guarda timestamp).
     - Link "Olvidé mi PIN" → reset Supabase + mensaje.
  5. Devuelve True solo si el usuario ingresa PIN correcto.
"""

from __future__ import annotations

import sys
import os
import time
import threading
import logging

_log = logging.getLogger("NeuroMood.PrivacyLock")

# ── path bootstrap (frozen / dev) ────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base not in sys.path:
    sys.path.insert(0, _base)

from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QApplication,
    QGraphicsOpacityEffect,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QAbstractAnimation,
    QRectF,
    QPointF,
    QSize,
)
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QLinearGradient,
    QBrush,
    QPen,
)
from PyQt6 import sip

from shared.db import guardar_config, leer_config
from shared.identidad import _hash_pwd, _verify_pwd, obtener_nombre_paciente
from shared.components import NMInput, NMButton, NMDialogScaffold, ThemeManager
try:
    from shared.icons_svg import nm_svg_pixmap as _nm_svg_pixmap
except ImportError:
    _nm_svg_pixmap = None
from shared.theme_qt import (
    v3c,
    nm_font,
    norm_modo,
    app_palette,
    qfont,
    C,
    V3_SP,
    stylesheet_base,
)
from shared.theme import TYPOGRAPHY
from shared.adaptive_layout_qt import configure_adaptive_window, window_edge_radius

# ── Constantes ────────────────────────────────────────────────────────────────

_MAX_ATTEMPTS = 3
_LOCK_SECONDS = 5 * 60  # 5 minutos
_CONFIG_ENABLED = "privacy_lock_enabled"
_CONFIG_HASH = "privacy_pin_hash"
_CONFIG_UNTIL = "privacy_lock_until"


# ── Helpers públicos (usados también por Settings) ───────────────────────────


def is_lock_enabled() -> bool:
    return leer_config(_CONFIG_ENABLED, "0") == "1"


def is_locked_out() -> bool:
    """True si hay bloqueo temporal activo."""
    until = leer_config(_CONFIG_UNTIL, "0")
    try:
        return float(until) > time.time()
    except (ValueError, TypeError):
        return False


def seconds_remaining() -> int:
    """Segundos restantes de bloqueo temporal (0 si no hay)."""
    until = leer_config(_CONFIG_UNTIL, "0")
    try:
        rem = float(until) - time.time()
        return max(0, int(rem))
    except (ValueError, TypeError):
        return 0


def set_lock_enabled(enabled: bool):
    guardar_config(_CONFIG_ENABLED, "1" if enabled else "0")


def set_pin(pin: str):
    """Guarda el hash PBKDF2 del PIN."""
    guardar_config(_CONFIG_HASH, _hash_pwd(pin))


def check_lock(parent: QWidget | None = None) -> bool:
    """
    Punto de entrada principal.

    Returns:
        True  → puede continuar al Home.
        False → no debe continuar (dialog cerrado sin autenticarse).
    """
    if not is_lock_enabled():
        return True

    # Safety valve: si el lock fue activado sin configurar un PIN (hash vacío),
    # lo desactivamos automáticamente en lugar de bloquear el acceso para siempre.
    if not leer_config(_CONFIG_HASH, ""):
        _log.warning(
            "PIN activado sin hash configurado — desactivando lock y liberando acceso. "
            "El usuario deberá configurar un PIN desde Ajustes antes de activar el lock."
        )
        set_lock_enabled(False)
        return True

    dlg = PrivacyLockDialog(parent)
    dlg.setModal(True)
    result = dlg.exec()
    dlg.deleteLater()
    return result == QDialog.DialogCode.Accepted


# ── Subwidgets ────────────────────────────────────────────────────────────────


class _LogoBadge(QWidget):
    """Logo cerebro NeuroMood con glow radial suave y pulso calmo.

    El glow es un gradiente radial que se desvanece a transparente: redondo
    completo y difuminado, con margen propio para no recortarse en los bordes
    del widget (antes el halo sólido quedaba cortado — feedback owner).
    """

    _GLOW_MARGIN = 26

    def __init__(self, size: int = 72, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._size = size
        self._modo = norm_modo(modo)
        self._pulse = 0.0
        self._pulse_dir = 1
        m = self._GLOW_MARGIN
        self._hint_size = QSize(size + m * 2, size + m * 2)
        self.setMinimumSize(self._hint_size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._pix = None
        self._load_pix()
        ThemeManager.instance().theme_changed.connect(self._on_theme)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)
        self._pulse_timer.timeout.connect(self._tick)
        self._pulse_timer.start()

    def sizeHint(self) -> QSize:
        return QSize(self._hint_size)

    def _load_pix(self):
        try:
            from shared.assets import nm_logo_pixmap

            # 2x para nitidez en pantallas HiDPI; se dibuja escalado al rect.
            self._pix = nm_logo_pixmap(
                self._modo, tipo="icon", width=self._size * 2, height=self._size * 2
            )
            if self._pix is not None and self._pix.isNull():
                self._pix = None
        except Exception:
            self._pix = None

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._load_pix()
        self.update()

    def _tick(self):
        self._pulse += 0.04 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QRadialGradient

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        cx = self.width() / 2
        cy = self.height() / 2
        r = self._size / 2

        # Glow radial difuminado: centro suave → transparente en el borde.
        glow_r = r + 8 + self._GLOW_MARGIN * (0.45 + 0.25 * self._pulse)
        aqua = v3c("aqua", self._modo)
        grad = QRadialGradient(QPointF(cx, cy), glow_r)
        c0 = QColor(aqua)
        c0.setAlpha(int(46 + self._pulse * 22))
        c1 = QColor(aqua)
        c1.setAlpha(int(18 + self._pulse * 10))
        c2 = QColor(aqua)
        c2.setAlpha(0)
        grad.setColorAt(0.0, c0)
        grad.setColorAt(0.55, c1)
        grad.setColorAt(1.0, c2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # Disco de apoyo sutil bajo el cerebro (superficie, no neón).
        disc = QColor(v3c("surface", self._modo))
        disc.setAlpha(235)
        p.setBrush(QBrush(disc))
        p.drawEllipse(QPointF(cx, cy), r + 4, r + 4)

        if self._pix is not None and not self._pix.isNull():
            # Cerebro NeuroMood centrado (KeepAspectRatio ya aplicado al cargar).
            target = QRectF(cx - r, cy - r, self._size, self._size)
            src = QRectF(self._pix.rect())
            # Ajustar target para mantener proporción del recorte del cerebro.
            ar = src.width() / max(1.0, src.height())
            if ar >= 1.0:
                th = self._size / ar
                target = QRectF(cx - r, cy - th / 2, self._size, th)
            else:
                tw = self._size * ar
                target = QRectF(cx - tw / 2, cy - r, tw, self._size)
            p.drawPixmap(target, self._pix, src)
        else:
            # Fallback sin asset: monograma sobre gradiente de identidad.
            grad_l = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
            grad_l.setColorAt(0.0, v3c("primary", self._modo))
            grad_l.setColorAt(1.0, v3c("terracotta", self._modo))
            p.setBrush(QBrush(grad_l))
            p.drawEllipse(QPointF(cx, cy), r, r)
            font = nm_font("h1", bold_override=True)
            font.setPixelSize(int(r * 0.7))
            p.setFont(font)
            p.setPen(QPen(v3c("textOnSolid", self._modo)))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "N")
        p.end()


class _PINDots(QWidget):
    """4 puntos que muestran cuántos dígitos del PIN se ingresaron."""

    def __init__(self, max_len: int = 6, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._max = max_len
        self._modo = modo
        self._filled = 0
        self._error = False
        self.setFixedSize(max_len * 22 + (max_len - 1) * 12, 24)

    def set_filled(self, n: int, error: bool = False):
        self._filled = min(n, self._max)
        self._error = error
        self.update()

    def set_modo(self, modo: str):
        self._modo = modo
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dot_r = 10
        gap = 12
        total_w = self._max * (dot_r * 2) + (self._max - 1) * gap
        x = (self.width() - total_w) / 2

        for i in range(self._max):
            cx = x + dot_r + i * (dot_r * 2 + gap)
            cy = self.height() / 2
            if i < self._filled:
                col = v3c("danger", self._modo) if self._error else v3c("primary", self._modo)
                p.setBrush(QBrush(col))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)
            else:
                outline = v3c("primary", self._modo)
                outline.setAlpha(60)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(outline, 1.5))
                p.drawEllipse(QPointF(cx, cy), dot_r - 0.75, dot_r - 0.75)
        p.end()


class _ShakingFrame(QFrame):
    """Frame que puede ejecutar animación de 'shake' horizontal al fallar."""

    def shake(self):
        orig = self.pos()
        vanim = _KeyframeAnim(self, orig, self)
        vanim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._shake_anim = vanim


class _KeyframeAnim(QPropertyAnimation):
    """Shake horizontal rápido con 7 keyframes."""

    def __init__(self, target: QWidget, orig_pos, parent=None):
        super().__init__(target, b"pos", parent)
        self._orig = orig_pos
        offsets = [0, -10, 9, -7, 6, -4, 0]
        total = len(offsets) - 1
        self.setDuration(400)
        self.setStartValue(orig_pos)
        for i, off in enumerate(offsets):
            ratio = i / total
            self.setKeyValueAt(ratio, orig_pos + QPointF(off, 0).toPoint())
        self.setEndValue(orig_pos)
        self.setEasingCurve(QEasingCurve.Type.Linear)


# ── _PINRecoveryDialog ───────────────────────────────────────────────────────


class _PINRecoveryDialog(QDialog):
    """Verifica la contraseña Supabase del paciente para desbloquear el acceso.

    El PIN es un hash local: no existe recuperación por email.
    La verificación de identidad se hace con la contraseña de la cuenta Supabase.
    Si tiene éxito, el llamador debe limpiar el hash y desactivar el lock.
    """

    def __init__(self, parent=None, modo: str = "dark_hybrid"):
        # 3.3: themed con NMDialogScaffold (chrome NM, fondo opaco, header con
        # título y cerrar). Antes usaba QDialog nativo con QLineEdit/QPushButton
        # crudos — feedback P0/P1: en light el fondo se veía nativo, sin tema.
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self._modo = norm_modo(modo)
        self._attempts = 0
        self.setWindowTitle("Recuperar acceso")
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setMinimumHeight(280)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scaffold = NMDialogScaffold(
            title="Verificar identidad",
            eyebrow="Recuperar acceso",
            modo=self._modo,
            parent=self,
        )
        # Ocultar el subrayado abajo del campo de texto (footer separator de la scaffold)
        self._scaffold._footer_sep.hide()

        # Conectar el botón X de la scaffold para que cierre el diálogo
        try:
            self._scaffold._close_btn.clicked.disconnect()
        except Exception:
            pass
        self._scaffold._close_btn.clicked.connect(self.reject)

        # Aplicar fondo opaco theme-aware al contenedor (scaffold es theme-aware
        # pero el QDialog exterior necesita el color sólido para no destapar la
        # ventana nativa en light).
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("borderStrong" if is_dark else "border", self._modo)
        self.setStyleSheet(
            f"_PINRecoveryDialog {{ background: {card_bg}; border: 1px solid {border}; "
            f"border-radius: {window_edge_radius()}px; }}"
        )

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        blay = QVBoxLayout(body)
        blay.setContentsMargins(0, V3_SP["sm"], 0, 0)
        blay.setSpacing(V3_SP["lg"])

        info = QLabel(
            "El PIN se guarda localmente y no puede recuperarse por email.\n"
            "Para restablecer el acceso, ingresá la contraseña de tu cuenta."
        )
        info.setFont(qfont("size_small"))
        info.setWordWrap(True)
        info.setStyleSheet(
            f"color: {v3c('textMuted', self._modo).name()}; background: transparent;"
        )
        blay.addWidget(info)

        self._pwd_input = NMInput("Contraseña de tu cuenta", modo=self._modo)
        self._pwd_input.setEchoMode(NMInput.EchoMode.Password)
        self._pwd_input.setMaxLength(128)
        blay.addWidget(self._pwd_input)

        self._error_lbl = QLabel("")
        self._error_lbl.setFont(qfont("size_small"))
        self._error_lbl.setStyleSheet(
            f"color: {v3c('danger', self._modo).name()}; background: transparent;"
        )
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        blay.addWidget(self._error_lbl)

        self._scaffold.set_body(body)
        self._scaffold.add_action("Cancelar", role="ghost", callback=self.reject)
        self._btn_ok = self._scaffold.add_action(
            "Verificar y desbloquear", role="primary", callback=self._on_verify
        )

        root.addWidget(self._scaffold)
        self._pwd_input.returnPressed.connect(self._on_verify)
        ThemeManager.instance().theme_changed.connect(self._on_theme)
        from shared.adaptive_layout_qt import apply_native_rounded_corners

        apply_native_rounded_corners(self)

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        card_bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("borderStrong" if is_dark else "border", self._modo)
        self.setStyleSheet(
            f"_PINRecoveryDialog {{ background: {card_bg}; border: 1px solid {border}; "
            f"border-radius: {window_edge_radius()}px; }}"
        )

    def _on_verify(self):
        pwd = self._pwd_input.text()
        if not pwd:
            self._show_error("Ingresá tu contraseña.")
            return

        self._btn_ok.setEnabled(False)
        self._btn_ok.setText("Verificando...")
        self._error_lbl.hide()
        QApplication.processEvents()

        email = leer_config("patient_email", "")
        if not email:
            self._show_error("No hay email registrado. Reinstalá la app.")
            self._btn_ok.setEnabled(True)
            self._btn_ok.setText("Verificar y desbloquear")
            return

        # Para evitar trabadas de asyncio/deadlocks por el cliente Supabase
        # en threads de GUI, hacemos la llamada en el hilo principal de la UI.
        try:
            from shared.config import supabase_url, supabase_key
            from supabase import create_client
            url, key = supabase_url(), supabase_key()
            if not url or not key:
                raise RuntimeError("Credenciales Supabase no configuradas.")
            client = create_client(url, key)
            res = client.auth.sign_in_with_password({"email": email, "password": pwd})
            if not getattr(getattr(res, "user", None), "id", ""):
                raise RuntimeError("Credenciales incorrectas.")
            self.accept()
        except Exception as exc:
            err = str(exc)[:120]
            self._on_verify_failed(err)

    def _on_verify_failed(self, reason: str):
        # Clasificar error y descontar intentos
        reason_lower = reason.lower()
        is_creds_error = (
            "credential" in reason_lower
            or "incorrect" in reason_lower
            or "invalid" in reason_lower
            or "contraseña" in reason_lower
            or "auth" in reason_lower
        )
        if is_creds_error:
            self._attempts += 1
            remaining = 3 - self._attempts
            if remaining > 0:
                msg = f"Contraseña incorrecta. Te queda{'n' if remaining > 1 else ''} {remaining} intento{'s' if remaining > 1 else ''}."
                self._show_error(msg)
                self._btn_ok.setEnabled(True)
                self._btn_ok.setText("Verificar y desbloquear")
            else:
                self._show_error("Demasiados intentos fallidos. Ventana bloqueada.")
                self._btn_ok.setEnabled(False)
                QTimer.singleShot(1500, self.reject)
        else:
            self._show_error(f"Error de verificación: {reason}")
            self._btn_ok.setEnabled(True)
            self._btn_ok.setText("Verificar y desbloquear")

    def _show_error(self, msg: str):
        self._error_lbl.setText(msg)
        self._error_lbl.show()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()

    def center_on_parent(self):
        parent = self.parentWidget()
        if parent:
            self.adjustSize()
            parent_rect = parent.rect()
            parent_global_pos = parent.mapToGlobal(parent_rect.topLeft())
            x = parent_global_pos.x() + (parent_rect.width() - self.width()) // 2
            y = parent_global_pos.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

# ── PrivacyLockDialog ─────────────────────────────────────────────────────────


class PrivacyLockDialog(QDialog):
    """
    Pantalla de desbloqueo por PIN.

    Uso:
        dlg = PrivacyLockDialog(parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # continuar al Home
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(
            parent,
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint,
        )
        # 3.1: leer el tema persistido del usuario (QSettings ui/theme) en vez
        # de forzar light_hybrid. Antes siempre arrancaba en light, incluso si
        # el paciente usaba dark — feedback P0.
        try:
            from app.main_qt import _saved_theme
            self._modo = _saved_theme("dark_hybrid")
        except Exception:
            self._modo = "dark_hybrid"
        self._attempts = 0
        self._nombre = obtener_nombre_paciente() or "Paciente"
        self._recovery_in_progress = False

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._configure_responsive_window()

        self._build_ui()
        self._apply_global_style()
        from shared.adaptive_layout_qt import apply_native_rounded_corners

        apply_native_rounded_corners(self)

        # Si hay bloqueo temporal activo, mostrar cuenta regresiva
        if is_locked_out():
            self._show_locked_out()
        else:
            self._show_pin_form()

        # Timer de cuenta regresiva (para lockout)
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        if is_locked_out():
            self._countdown_timer.start()

        # Conectar ThemeManager (poco probable que cambie aquí, pero robustez)
        ThemeManager.instance().theme_changed.connect(self._on_theme)

    def _configure_responsive_window(self):
        configure_adaptive_window(
            self,
            default_size=QSize(440, 520),
            min_size=QSize(340, 420),
        )

    # ── construcción UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Fondo pintado
        self._bg = _LockBackground(modo=self._modo, parent=self)
        layout.addWidget(self._bg)

        # Panel central flotante
        center_layout = QVBoxLayout(self._bg)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Card container
        self._card = _LockCard(modo=self._modo, parent=self._bg)
        center_layout.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(0)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        self._logo = _LogoBadge(size=44, modo=self._modo, parent=self._card)
        card_layout.addWidget(self._logo, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(10)

        # Título bienvenida
        self._title_lbl = QLabel(f"Bienvenido, {self._nombre}")
        self._title_lbl.setFont(nm_font("h2"))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        card_layout.addWidget(self._title_lbl)
        card_layout.addSpacing(4)

        # Subtítulo
        self._sub_lbl = QLabel("Ingresá tu PIN para continuar")
        self._sub_lbl.setFont(nm_font("body"))
        self._sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_lbl.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        card_layout.addWidget(self._sub_lbl)
        card_layout.addSpacing(14)

        # Stacked: PIN form | lockout panel
        from PyQt6.QtWidgets import QStackedWidget

        self._stack = QStackedWidget(self._card)
        self._stack.setStyleSheet("background: transparent;")
        card_layout.addWidget(self._stack)

        # ── Página 0: formulario PIN ───────────────────────────────────────
        self._pin_page = QWidget()
        self._pin_page.setStyleSheet("background: transparent;")
        pin_layout = QVBoxLayout(self._pin_page)
        pin_layout.setContentsMargins(0, 0, 0, 0)
        pin_layout.setSpacing(8)
        pin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Puntos visuales PIN
        self._dots = _PINDots(max_len=6, modo=self._modo, parent=self._pin_page)
        pin_layout.addWidget(self._dots, alignment=Qt.AlignmentFlag.AlignCenter)
        pin_layout.addSpacing(2)

        self._pin_hint = QLabel("PIN de 4 a 6 dígitos")
        self._pin_hint.setFont(nm_font("sm"))
        self._pin_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_hint.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        pin_layout.addWidget(self._pin_hint, alignment=Qt.AlignmentFlag.AlignCenter)

        # Input PIN (oculto visualmente pero funcional)
        self._pin_input = NMInput("Ingresá tu PIN", parent=self._pin_page, modo=self._modo)
        self._pin_input.setEchoMode(NMInput.EchoMode.Password)
        self._pin_input.setMaxLength(6)
        self._pin_input.setFixedWidth(260)
        self._pin_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pin_input.textChanged.connect(self._on_pin_changed)
        self._pin_input.returnPressed.connect(self._on_unlock_clicked)
        pin_layout.addWidget(self._pin_input, alignment=Qt.AlignmentFlag.AlignCenter)

        # Completamente invisible, no ocupa espacio
        self._pin_input.setStyleSheet(
            "background: transparent; border: none; color: transparent; min-height: 0px; max-height: 0px;"
        )
        self._pin_input.setFixedHeight(0)

        # Mensaje de error
        self._error_lbl = QLabel("")
        self._error_lbl.setFont(nm_font("sm"))
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setStyleSheet(
            f"color: {v3c('danger', self._modo).name()}; background: transparent;"
        )
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setFixedWidth(300)
        self._error_lbl.setMinimumHeight(20)
        pin_layout.addWidget(self._error_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botón Desbloquear
        self._unlock_btn = NMButton(
            "Desbloquear",
            parent=self._pin_page,
            modo=self._modo,
            variant="gradient",
            size="md",
            width=220,
        )
        self._unlock_btn.setMinimumHeight(36)
        self._unlock_btn.setMaximumHeight(36)
        # NoFocus: el botón no debe robarle el foco al input oculto del PIN
        # (si lo roba, el tecleo posterior no entra y los puntos no se pintan).
        self._unlock_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._unlock_btn.clicked.connect(self._on_unlock_clicked)
        self._unlock_btn.setEnabled(False)
        pin_layout.addWidget(self._unlock_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        pin_layout.addSpacing(14)

        # Link "Olvidé mi PIN"
        self._forgot_btn = QLabel()
        self._forgot_btn.setFont(nm_font("sm"))
        self._forgot_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._forgot_btn.setOpenExternalLinks(False)
        self._forgot_btn.setStyleSheet("background: transparent;")
        self._forgot_btn.linkActivated.connect(self._on_forgot_pin)
        self._refresh_forgot_link()
        pin_layout.addWidget(self._forgot_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._stack.addWidget(self._pin_page)  # index 0

        # ── Página 1: lockout ──────────────────────────────────────────────
        self._lockout_page = QWidget()
        self._lockout_page.setStyleSheet("background: transparent;")
        lo_layout = QVBoxLayout(self._lockout_page)
        lo_layout.setContentsMargins(0, 0, 0, 0)
        lo_layout.setSpacing(12)
        lo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lock_icon_lbl = QLabel()
        lock_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_icon_lbl.setStyleSheet("background: transparent;")
        if _nm_svg_pixmap is not None:
            pix = _nm_svg_pixmap("shield", color=v3c("danger", self._modo).name(), size=44)
            if pix and not pix.isNull():
                lock_icon_lbl.setPixmap(pix)
        else:
            lock_icon_lbl.setText("⛔")
        lo_layout.addWidget(lock_icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._lockout_lbl = QLabel(
            "Demasiados intentos fallidos.\nEsperá antes de volver a intentar."
        )
        self._lockout_lbl.setFont(nm_font("body"))
        self._lockout_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lockout_lbl.setWordWrap(True)
        self._lockout_lbl.setStyleSheet(
            f"color: {v3c('danger', self._modo).name()}; background: transparent;"
        )
        lo_layout.addWidget(self._lockout_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._countdown_lbl = QLabel("")
        self._countdown_lbl.setFont(nm_font("h2"))
        self._countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        lo_layout.addWidget(self._countdown_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._stack.addWidget(self._lockout_page)  # index 1

        self._stack.setCurrentIndex(0)

    # ── show/hide de páginas ──────────────────────────────────────────────────

    def _show_pin_form(self):
        self._stack.setCurrentIndex(0)
        QTimer.singleShot(
            100, lambda: self._pin_input.setFocus() if not sip.isdeleted(self._pin_input) else None
        )

    def _show_locked_out(self):
        self._stack.setCurrentIndex(1)
        self._update_countdown_label()

    # ── countdown ─────────────────────────────────────────────────────────────

    def _tick_countdown(self):
        if not is_locked_out():
            self._countdown_timer.stop()
            self._attempts = 0
            self._error_lbl.setText("")
            self._pin_input.clear()
            self._show_pin_form()
        else:
            self._update_countdown_label()

    def _update_countdown_label(self):
        rem = seconds_remaining()
        mins = rem // 60
        secs = rem % 60
        self._countdown_lbl.setText(f"{mins}:{secs:02d}")

    # ── lógica de verificación ────────────────────────────────────────────────

    def _on_pin_changed(self, text: str):
        self._dots.set_filled(len(text))
        self._unlock_btn.setEnabled(bool(text.strip()))
        if self._error_lbl.text():
            self._error_lbl.setText("")
            self._dots.set_filled(len(text), error=False)

    def _on_unlock_clicked(self):
        if is_locked_out():
            self._show_locked_out()
            if not self._countdown_timer.isActive():
                self._countdown_timer.start()
            return

        pin = self._pin_input.text().strip()
        if not pin:
            self._shake_error("Ingresá tu PIN.")
            return

        stored_hash = leer_config(_CONFIG_HASH, "")
        if not stored_hash:
            # Sin hash configurado → no hay lock real, dejar pasar
            _log.warning("privacy_pin_hash vacío — desbloqueando sin verificación")
            self.accept()
            return

        if _verify_pwd(pin, stored_hash):
            # Correcto
            guardar_config(_CONFIG_UNTIL, "0")  # limpiar lockout si había
            self._attempts = 0
            self._animate_success()
        else:
            self._attempts += 1
            remaining_tries = _MAX_ATTEMPTS - self._attempts
            if remaining_tries > 0:
                msg = (
                    f"PIN incorrecto. "
                    f"{'Queda' if remaining_tries == 1 else 'Quedan'} "
                    f"{remaining_tries} intento{'s' if remaining_tries > 1 else ''}."
                )
            else:
                # Bloquear
                until = time.time() + _LOCK_SECONDS
                guardar_config(_CONFIG_UNTIL, str(until))
                msg = "Demasiados intentos. Bloqueado por 5 minutos."
                self._show_locked_out()
                self._countdown_timer.start()
            self._shake_error(msg)

    def _shake_error(self, msg: str):
        typed = len(self._pin_input.text())
        # Limpiar el input PRIMERO y con señales bloqueadas: clear() dispara
        # textChanged → _on_pin_changed borraba el mensaje de error en el
        # mismo tick y "PIN incorrecto" nunca llegaba a verse (bug owner).
        self._pin_input.blockSignals(True)
        self._pin_input.clear()
        self._pin_input.blockSignals(False)
        self._unlock_btn.setEnabled(False)
        self._error_lbl.setText(msg)
        self._dots.set_filled(typed, error=True)
        # Shake del card
        if hasattr(self._card, "shake"):
            self._card.shake()
        # Re-focus: el click en "Desbloquear" roba el foco del input oculto;
        # sin esto el paciente tecleaba y no entraba nada (app "bloqueada").
        self._pin_input.setFocus()

    def _animate_success(self):
        """Flash verde breve y luego accept."""
        self._unlock_btn.setEnabled(False)
        self._sub_lbl.setText("✓ Acceso concedido")
        self._sub_lbl.setStyleSheet(
            f"color: {v3c('success', self._modo).name()}; background: transparent;"
        )

        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def on_finished():
            self.hide()
            self.accept()

        anim.finished.connect(on_finished)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── recovery ──────────────────────────────────────────────────────────────

    def _on_forgot_pin(self):
        """Muestra diálogo de recuperación: verifica contraseña Supabase → limpia PIN."""
        if self._recovery_in_progress:
            return
        dlg = _PINRecoveryDialog(self, self._modo)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # La verificación fue exitosa → limpiar lock y cerrar
            guardar_config(_CONFIG_HASH, "")
            set_lock_enabled(False)
            self.accept()
        else:
            # Volver al form con el input enfocado: sin esto el tecleo
            # posterior no entraba (foco perdido en el link/diálogo).
            self._show_pin_form()

    def _recovery_failed(self, reason: str):
        short = reason if len(reason) < 80 else reason[:77] + "..."
        self._forgot_btn.setText(
            f'<span style="color:{v3c("danger", self._modo).name()};">Error: {short}</span>'
        )
        self._recovery_in_progress = False

    # ── tema ──────────────────────────────────────────────────────────────────

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self._dots.set_modo(self._modo)
        if hasattr(self, "_pin_hint"):
            self._pin_hint.setStyleSheet(
                f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
            )
        self._refresh_forgot_link()
        self._apply_global_style()

    def _refresh_forgot_link(self):
        color = v3c("aqua", self._modo).name()
        self._forgot_btn.setText(
            f'<a href="#" style="color:{color}; text-decoration:none;">Olvidé mi PIN</a>'
        )

    def _apply_global_style(self):
        app = QApplication.instance()
        if app:
            app.setPalette(app_palette(self._modo))
            app.setStyleSheet(stylesheet_base(self._modo))

    # ── overrides ────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        # No cerrar con Escape
        if event.key() == Qt.Key.Key_Escape:
            return
        # Red de seguridad: si el foco quedó en cualquier otro lado (botón,
        # link), el tecleo se redirige al input oculto del PIN.
        if (
            hasattr(self, "_stack")
            and self._stack.currentIndex() == 0
            and not self._pin_input.hasFocus()
        ):
            self._pin_input.setFocus()
            QApplication.sendEvent(self._pin_input, event)
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.result() == QDialog.DialogCode.Accepted:
            event.accept()
        else:
            event.ignore()


# Alias for compatibility
PrivacyLockScreen = PrivacyLockDialog


# ── Widgets de fondo / card ───────────────────────────────────────────────────


class _LockBackground(QWidget):
    """Fondo completo con gradiente shell + blobs, igual al shell de la app."""

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        ThemeManager.instance().theme_changed.connect(self._on_theme)

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), v3c("bg", self._modo))
        p.end()


class _LockCard(_ShakingFrame):
    """Card glassmorphic central con blur simulado."""

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = modo
        self.setMinimumSize(340, 380)
        self.resize(380, 420)
        ThemeManager.instance().theme_changed.connect(self._on_theme)

    def _on_theme(self, modo: str):
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = 22.0
        rect = QRectF(0, 0, w, h)

        # Fondo sereno de card, sin fullscreen ni overlay oscuro.
        bg = v3c("surface", self._modo)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, r, r)

        # Border
        border_col = v3c("borderSoft", self._modo)
        p.setPen(QPen(border_col, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), r, r)

        p.end()
