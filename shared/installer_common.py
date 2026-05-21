"""installer_common.py — Utilidades compartidas entre instaladores y desinstaladores."""
import sys
import os
import subprocess
import tempfile

try:
    from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, V3_DARK
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from theme import COLORS, TYPOGRAPHY, LAYOUT, V3_DARK

# ── Colores para instaladores ──────────────────────────────────────────────
# Premium clinical desktop installer — Deep dark theme (calm, safe, trustworthy)
_C = COLORS["dark_hybrid"]
_T = TYPOGRAPHY

BG_PRIMARY     = V3_DARK.get("bg", "#080c1e")
BG_SECONDARY   = V3_DARK.get("bgAlt", "#121b2d")
BG_SURFACE     = V3_DARK.get("surfaceSolid", "#121c2d")
BG_ELEVATED    = V3_DARK.get("elevatedSolid", "#19243d")
ACCENT         = V3_DARK.get("teal", "#2dd4bf")
ACCENT_HOVER   = V3_DARK.get("cyan", "#22d3ee")
TEXT_PRIMARY   = V3_DARK.get("text", "#f8fafc")
TEXT_SEC       = V3_DARK.get("text2", "#cbd5e1")
TEXT_TERT      = V3_DARK.get("text3", "#94a3b8")
TEXT_ON_ACCENT = "#020617"
BORDER         = V3_DARK.get("borderSolid", "#1e293b")
SUCCESS        = V3_DARK.get("success", "#10b981")
WARNING_C      = V3_DARK.get("warning", "#f59e0b")
ERROR_C        = V3_DARK.get("danger", "#ef4444")

# Refined clinical premium gradients (subtle teal depth, no neon)
GRAD_FROM = V3_DARK.get("gradFrom", ACCENT)
GRAD_MID  = V3_DARK.get("gradMid", ACCENT_HOVER)
GRAD_TO   = V3_DARK.get("gradTo", ACCENT_HOVER)

# Danger gradient (soft red to deep red, avoiding yellow neon)
DANGER_FROM = ERROR_C
DANGER_TO   = "#b91c1c"

# Tipografía
FONT_FAMILY = (_T.get("font_family_fallback_chain", ["Segoe UI"])[0]
                if isinstance(_T.get("font_family_fallback_chain"), list)
                else "Segoe UI")

# Elegant structural radius (desktop app style, not pills)
RADIUS_INPUT  = 8
RADIUS_BUTTON = 8
RADIUS_CARD   = 12

# Compat: aliases viejos que otras partes del código pueden usar
_GRAD       = COLORS["dark_hybrid"]
VIOLET      = V3_DARK.get("violet", "#a78bfa")
VIOLET_HOVER = V3_DARK.get("violet", "#a78bfa")
TEAL        = ACCENT
TEAL_HOVER  = ACCENT_HOVER
SUCCESS_BG  = "#10261e"


def _rgba(hex_color: str, alpha: float) -> str:
    """RGBA Qt-friendly desde un hex, con alpha en rango 0..1."""
    raw = (hex_color or "#000000").strip()
    if raw.startswith("#") and len(raw) >= 7:
        try:
            r = int(raw[1:3], 16)
            g = int(raw[3:5], 16)
            b = int(raw[5:7], 16)
            a = max(0, min(255, int(alpha * 255)))
            return f"rgba({r}, {g}, {b}, {a})"
        except Exception:
            pass
    return raw


ACCENT_SOFT = _rgba(ACCENT, 0.14)
WARM_SOFT = _rgba(WARNING_C, 0.14)
DANGER_SOFT = _rgba(ERROR_C, 0.16)


def stylesheet_installer() -> str:
    """
    Stylesheet premium unificado para los 4 instaladores/desinstaladores.
    Refinado para una apariencia clínica, calmada y elegante.
    """
    return f"""
* {{ font-family: "{FONT_FAMILY}", Arial; color: {TEXT_PRIMARY}; }}
QMainWindow, QWidget {{ background: {BG_PRIMARY}; }}
QWidget#InstallerRoot {{ background: {BG_PRIMARY}; }}
QWidget#InstallerHeader {{
    background: {BG_SECONDARY};
    border-bottom: 1px solid {BORDER};
}}
QWidget#InstallerPage {{ background: transparent; }}
QWidget#InstallerNav {{
    background: {BG_SECONDARY};
    border-top: 1px solid {BORDER};
}}
QLabel {{ background: transparent; }}

/* ── Inputs ─────────── */
QLineEdit {{
    background: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_INPUT}px;
    min-height: 22px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {ACCENT};
    selection-color: {TEXT_ON_ACCENT};
}}
QLineEdit:focus {{ border-color: {GRAD_MID}; border-width: 1px; background: {BG_ELEVATED}; }}
QLineEdit::placeholder {{ color: {TEXT_TERT}; }}

/* ── Botón primario — gradient clínico ── */
QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {GRAD_FROM}, stop:0.5 {GRAD_MID}, stop:1 {GRAD_TO}
    );
    color: {TEXT_ON_ACCENT};
    border: none;
    border-radius: {RADIUS_BUTTON}px;
    min-height: 26px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {GRAD_MID};
}}
QPushButton:pressed {{
    padding: 10px 22px 8px 22px;
}}
QPushButton:disabled {{
    background: {BORDER};
    color: {TEXT_TERT};
}}
QPushButton:focus {{ border: 1px solid {GRAD_MID}; }}

/* ── Botón outline (ghost/secondary) ────────────────────────── */
QPushButton#outline {{
    background: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    font-weight: 500;
}}
QPushButton#outline:hover {{
    background: {BG_ELEVATED};
    border-color: {GRAD_MID};
}}

/* ── Botón ghost (texto sin borde) ────────────────────────── */
QPushButton#ghost {{
    background: transparent;
    color: {TEXT_SEC};
    border: none;
    font-weight: 500;
}}
QPushButton#ghost:hover {{
    color: {TEXT_PRIMARY};
    background: {BG_ELEVATED};
    border-radius: {RADIUS_BUTTON}px;
}}

/* ── Botón danger (uninstaller) ── */
QPushButton#danger {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {DANGER_FROM}, stop:1 {DANGER_TO}
    );
    color: {TEXT_ON_ACCENT};
    border: none;
    font-weight: 600;
}}
QPushButton#danger:hover {{
    background: {DANGER_FROM};
}}

/* ── Checkbox clínico ────────────────── */
QCheckBox {{
    color: {TEXT_SEC};
    font-size: 13px;
    spacing: 10px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background: {BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {GRAD_FROM}, stop:1 {GRAD_TO}
    );
    border-color: {GRAD_MID};
}}

/* ── Progress bar ────────── */
QProgressBar {{
    background: {BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {GRAD_FROM}, stop:0.5 {GRAD_MID}, stop:1 {GRAD_TO}
    );
    border-radius: 4px;
}}

/* ── Progress bar danger ──── */
QProgressBar#danger::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {DANGER_FROM}, stop:1 {DANGER_TO}
    );
    border-radius: 4px;
}}

/* ── Scroll ─────────────────────────────────────────────────── */
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: rgba(255, 255, 255, 0.05); width: 6px; margin: 0; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 3px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_TERT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: rgba(255, 255, 255, 0.05); height: 6px; margin: 0; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 3px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_TERT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Sidebar ────────────────────────────────────────────────── */
QWidget#Sidebar {{
    background: {BG_SECONDARY};
    border-right: 1px solid {BORDER};
}}

/* ── Nav bar inferior ───────────────────────────────────────── */
QWidget#NavBar {{
    background: {BG_SECONDARY};
    border-top: 1px solid {BORDER};
}}

/* ── Log area ───────────────────────────────────────────────── */
QScrollArea#LogArea {{
    background: {BG_SURFACE};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {BORDER};
}}

/* ── Info card verde ────────────────────────────────────────── */
QFrame#InfoCard {{
    background: {SUCCESS_BG};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {SUCCESS};
}}

/* ── Card de inputs ─────────────────────────────────────────── */
QFrame#InputCard,
QFrame#AuthCard,
QFrame#LegalPanel,
QFrame#AcceptCard,
QFrame#WelcomeLogoCard,
QFrame#InstallerSurfaceCard {{
    background: {BG_SURFACE};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {BORDER};
}}

QFrame#InstallerElevatedCard {{
    background: {BG_ELEVATED};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {BORDER};
}}

QFrame#InstallerWarningCard {{
    background: {WARM_SOFT};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {_rgba(WARNING_C, 0.34)};
}}

QFrame#InstallerDangerCard {{
    background: {DANGER_SOFT};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {_rgba(ERROR_C, 0.42)};
}}

QFrame#InstallerSuccessCard {{
    background: {SUCCESS_BG};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {_rgba(SUCCESS, 0.50)};
}}
"""


def recurso(nombre: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        return os.path.join(base, nombre)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(repo, "assets", nombre)
    if os.path.exists(candidate):
        return candidate
    return os.path.join(repo, nombre)


def crear_acceso_directo(origen: str, destino_lnk: str, icono: str):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        lnk = shell.CreateShortcut(destino_lnk)
        lnk.TargetPath = origen
        lnk.IconLocation = f"{icono},0"
        lnk.Save()
    except Exception:
        ps_script = (
            f'$s = New-Object -ComObject WScript.Shell\n'
            f'$l = $s.CreateShortcut("{destino_lnk}")\n'
            f'$l.TargetPath = "{origen}"\n'
            f'$l.IconLocation = "{icono},0"\n'
            f'$l.Save()\n'
        )
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".ps1", delete=False) as f:
            f.write(b'\xef\xbb\xbf')
            f.write(ps_script.encode("utf-8"))
            ps1_path = f.name
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            os.unlink(ps1_path)
        except Exception:
            pass


# ── InstallerShell — Clase base común para los 4 instaladores ────────────────

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
        QApplication, QLabel, QPushButton, QStackedWidget,
    )
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import (
        QIcon, QPixmap, QFont, QFontMetrics,
        QColor, QPainter, QPainterPath, QLinearGradient,
    )
    _QT_OK = True
except ImportError:
    _QT_OK = False


if _QT_OK:
    class GradientTextLabel(QLabel):
        """QLabel cuyo texto se pinta con gradiente lineal horizontal."""
        def __init__(self, text="", from_color=None, to_color=None,
                     font_size=32, bold=True, parent=None):
            super().__init__(parent)
            self._text = text
            self._from = QColor(from_color or GRAD_FROM)
            self._to = QColor(to_color or GRAD_TO)
            self._font_size = font_size
            self._bold = bold
            font = QFont(FONT_FAMILY, font_size)
            if bold:
                font.setWeight(QFont.Weight.Bold)
            self.setFont(font)
            self.setText(text)
            self.setStyleSheet("background: transparent;")

        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            font = QFont(FONT_FAMILY, self._font_size)
            if self._bold:
                font.setWeight(QFont.Weight.Bold)
            fm = QFontMetrics(font)
            path = QPainterPath()
            path.addText(0, fm.ascent(), font, self._text)
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0.0, self._from)
            grad.setColorAt(1.0, self._to)
            p.fillPath(path, grad)
            p.end()


class InstallerShell(QMainWindow):
    """Ventana base común para installer y uninstaller. Provee header con logo,
    indicador de pasos, contenido apilado (QStackedWidget), y nav footer."""

    # Override en subclases
    APP_NAME: str = "NeuroMood"
    WINDOW_SIZE: tuple = (680, 480)
    STEPS: list[str] = []
    WINDOW_ROLE: str = "Instalador"
    APP_VERSION: str = "1.0.0"
    BUILD_DATE: str = "2026-05-16"

    def __init__(self):
        super().__init__()
        self._pagina = 0
        self._pages: list[QWidget] = []
        self._step_widgets: list[tuple[QLabel, QLabel]] = []

        self.setWindowTitle(self.APP_NAME if not self.WINDOW_ROLE else f"{self.WINDOW_ROLE} — {self.APP_NAME}")
        w, h = self.WINDOW_SIZE
        self.resize(w, h)
        self.setMinimumSize(min(w, 760), min(h, 560))
        self.setStyleSheet(stylesheet_installer())
        try:
            self.setWindowIcon(QIcon(recurso("installer_icon.ico")))
        except Exception:
            pass

        screen = QApplication.primaryScreen().availableGeometry()
        self.move((screen.width() - w) // 2, (screen.height() - h) // 2)
        aplicar_captionbar_installer(self)

    def _build_shell(self):
        """Construye el layout común: header + steps + stack + footer."""
        central = QWidget()
        central.setObjectName("InstallerRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("InstallerHeader")
        header.setFixedHeight(60)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        hl.setSpacing(14)
        logo_lbl = QLabel()
        try:
            from PIL import Image as PILImage
            from PyQt6.QtGui import QImage
            img = PILImage.open(recurso("logos-dark.png")).convert("RGBA")
            img.thumbnail((130, 36), PILImage.LANCZOS)
            qimg = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
            logo_lbl.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            logo_lbl.setText(self.APP_NAME)
            logo_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 14px; font-weight: bold; background: transparent;")
        hl.addWidget(logo_lbl)
        hl.addStretch()
        # Badge de versión (spec mockup v3)
        v_badge = QLabel(f"v{self.APP_VERSION} · build {self.BUILD_DATE}")
        v_badge.setStyleSheet(
            f"background: {BG_ELEVATED}; border: 1px solid {BORDER};"
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace;"
            f"border-radius: 999px; padding: 3px 10px;"
        )
        hl.addWidget(v_badge)
        root.addWidget(header)

        # Separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        root.addWidget(sep)

        # ── NMInstallStepper (V3 premium) ─────────────────────────────────────
        self._nm_stepper = None
        if self.STEPS:
            try:
                from shared.components_qt import NMInstallStepper
                accent_key = getattr(self, "_STEPPER_ACCENT", "teal")
                self._nm_stepper = NMInstallStepper(
                    self.STEPS, current=0, accent_key=accent_key
                )
                root.addWidget(self._nm_stepper)
            except Exception:
                pass

        # Content stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; }")
        root.addWidget(self._stack, stretch=1)

        # Nav footer — v3 spec
        nav = QWidget()
        nav.setObjectName("InstallerNav")
        nav.setFixedHeight(62)
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(24, 8, 24, 8)
        nl.setSpacing(8)

        # Texto mono izquierda (spec mockup)
        lbl_footer = QLabel(f"{self.APP_NAME} · NeuroMood Suite v{self.APP_VERSION}")
        lbl_footer.setStyleSheet(
            f"color: {TEXT_TERT}; font-size: 10px; font-family: Consolas, monospace;"
            f"background: transparent;"
        )
        nl.addWidget(lbl_footer)
        nl.addStretch()

        # btn_ant
        self.btn_ant = QPushButton("← Volver")
        self.btn_ant.setFixedSize(118, 42)
        self.btn_ant.setAccessibleName("Volver")
        self.btn_ant.setStyleSheet(
            f"QPushButton {{ border: 1px solid {BORDER}; border-radius: {RADIUS_BUTTON}px;"
            f"background: transparent; color: {TEXT_SEC}; font-size: 12px;"
            f"font-weight: 500; padding: 8px 16px; }}"
            f"QPushButton:hover {{ border-color: {GRAD_MID}; color: {TEXT_PRIMARY}; background: {BG_ELEVATED}; }}"
        )
        self.btn_ant.setVisible(False)
        nl.addWidget(self.btn_ant)

        # btn_sig
        self.btn_sig = QPushButton("Siguiente →")
        self.btn_sig.setFixedSize(158, 42)
        self.btn_sig.setAccessibleName("Continuar")
        self.btn_sig.setStyleSheet(
            f"QPushButton {{ border: none; border-radius: {RADIUS_BUTTON}px;"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            f"stop:0 {GRAD_FROM}, stop:0.5 {GRAD_MID}, stop:1 {GRAD_TO});"
            f"color: {TEXT_ON_ACCENT}; font-size: 12px; font-weight: 600;"
            f"padding: 9px 22px; }}"
            f"QPushButton:hover {{ background: {GRAD_MID}; }}"
            f"QPushButton:disabled {{ background: {BORDER}; color: {TEXT_TERT}; }}"
        )
        nl.addWidget(self.btn_sig)
        root.addWidget(nav)

    def _add_page(self, builder_fn):
        """Crea una página y la agrega al stack."""
        page = QWidget()
        page.setObjectName("InstallerPage")
        page.setStyleSheet("QWidget#InstallerPage { background: transparent; }")
        try:
            import inspect
            params = [
                p for p in inspect.signature(builder_fn).parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
        except Exception:
            params = [None, None]
        if len(params) <= 1:
            builder_fn(page)
        else:
            lay = QVBoxLayout(page)
            lay.setContentsMargins(24, 16, 24, 8)
            lay.setSpacing(8)
            builder_fn(page, lay)
        self._stack.addWidget(page)
        self._pages.append(page)

    def _ir_a(self, n: int):
        if n == self._pagina:
            return
        self._pagina = n
        self._fade_to(n)

    def _fade_to(self, n: int):
        current = self._stack.currentWidget()
        if current is None:
            self._stack.setCurrentIndex(n)
            return
        target = self._stack.widget(n)
        if target is None:
            return
        snap = current.grab()
        overlay = QLabel(self._stack)
        overlay.setPixmap(snap)
        overlay.setGeometry(0, 0, self._stack.width(), self._stack.height())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.show()
        overlay.raise_()
        try:
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation
            eff = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", overlay)
            anim.setDuration(150)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._stack.setCurrentIndex(n)
            anim.finished.connect(overlay.deleteLater)
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        except Exception:
            self._stack.setCurrentIndex(n)
            overlay.deleteLater()

        # Update step indicators (v3: active = gradient firma, done = success)
        for i, (circle, lbl) in enumerate(self._step_widgets):
            if i == n:
                circle.setStyleSheet(
                    f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                    f"stop:0 {GRAD_FROM}, stop:1 {GRAD_TO}); "
                    f"color: {TEXT_ON_ACCENT}; border-radius: 11px;"
                    f"font-weight: 600; font-size: 10px;"
                )
                lbl.setStyleSheet(
                    f"color: {TEXT_PRIMARY}; font-size: 11px; "
                    f"font-weight: 600; background: transparent;"
                )
            elif i < n:
                circle.setStyleSheet(
                    f"background: {SUCCESS}; color: #0b1220; border-radius: 11px;"
                    f"font-weight: 600; font-size: 10px;"
                )
                lbl.setStyleSheet(
                    f"color: {TEXT_SEC}; font-size: 11px; background: transparent;"
                )
            else:
                circle.setStyleSheet(
                    f"background: {BORDER}; color: {TEXT_TERT}; border-radius: 11px;"
                    f"font-weight: 500; font-size: 10px;"
                )
                lbl.setStyleSheet(
                    f"color: {TEXT_TERT}; font-size: 11px; background: transparent;"
                )

        self.btn_ant.setVisible(n > 0)
        self.btn_sig.setEnabled(True)

        # Advance NMInstallStepper if available
        if self._nm_stepper is not None:
            try:
                self._nm_stepper.set_step(n)
            except Exception:
                pass


def aplicar_captionbar_installer(window):
    try:
        import ctypes
        hwnd = int(window.winId())
        v = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
        if sys.getwindowsversion().build >= 22000:
            r, g, b = int(BG_SECONDARY[1:3], 16), int(BG_SECONDARY[3:5], 16), int(BG_SECONDARY[5:7], 16)
            color = ctypes.c_uint(r | (g << 8) | (b << 16))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
    except Exception:
        pass
