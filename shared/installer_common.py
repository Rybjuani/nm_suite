"""installer_common.py — Utilidades compartidas entre instaladores y desinstaladores."""
import sys
import os
import subprocess
import tempfile

try:
    from shared.theme import COLORS, TYPOGRAPHY, LAYOUT
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from theme import COLORS, TYPOGRAPHY, LAYOUT

# ── Colores para instaladores (desde theme hybrid) ──────────────────────────
_C = COLORS["dark_hybrid"]
_T = TYPOGRAPHY

BG_PRIMARY = _C["bg_primary"]
BG_SECONDARY = _C["bg_secondary"]
BG_SURFACE = _C["bg_surface"]
ACCENT = _C["accent"]
ACCENT_HOVER = _C["accent_hover"]
TEXT_PRIMARY = _C["text_primary"]
TEXT_SEC = _C["text_secondary"]
TEXT_TERT = _C["text_tertiary"]
TEXT_ON_ACCENT = _C["text_on_accent"]
BORDER = _C["border"]
SUCCESS = _C["success"]
WARNING_C = _C["warning"]
ERROR_C = _C["error"]

FONT_FAMILY = _T.get("font_family", "Segoe UI")
RADIUS_BUTTON = LAYOUT["radius_button"]
RADIUS_CARD = LAYOUT["radius_card"]

# Colores del gradiente teal→violet del tema
_GRAD = COLORS["dark_hybrid"]
VIOLET       = _GRAD["violet"]
VIOLET_HOVER = _GRAD["violet_hover"]
TEAL         = _GRAD.get("teal", ACCENT)
TEAL_HOVER   = _GRAD.get("teal_hover", TEAL)
SUCCESS_BG   = "#091E10"   # fondo info verde oscuro


def stylesheet_installer() -> str:
    """
    Stylesheet premium unificado para los 4 instaladores/desinstaladores.
    Usa el design system dark_hybrid: gradiente teal-violet en botones primarios,
    sidebar con borde accent, inputs y cards con la paleta exacta de la app.
    """
    return f"""
* {{ font-family: "{FONT_FAMILY}", Arial; color: {TEXT_PRIMARY}; }}
QMainWindow, QWidget {{ background: {BG_PRIMARY}; }}
QLabel {{ background: transparent; }}

/* ── Inputs ──────────────────────────────────────────────────── */
QLineEdit {{
    background: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_BUTTON}px;
    padding: 6px 12px;
    font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; border-width: 2px; }}
QLineEdit::placeholder {{ color: {_GRAD["text_tertiary"]}; }}

/* ── Botón primario — gradiente simulado con borde accent ───── */
QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:0.45 {TEAL}, stop:1 {VIOLET}
    );
    color: {TEXT_ON_ACCENT};
    border: none;
    border-radius: {RADIUS_BUTTON}px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_HOVER}, stop:0.45 {TEAL_HOVER}, stop:1 {VIOLET_HOVER}
    );
}}
QPushButton:disabled {{
    background: {BORDER};
    color: {_GRAD["text_tertiary"]};
}}

/* ── Botón outline ───────────────────────────────────────────── */
QPushButton#outline {{
    background: transparent;
    color: {ACCENT};
    border: 2px solid {ACCENT};
}}
QPushButton#outline:hover {{
    background: {_GRAD["bg_elevated"]};
}}

/* ── Botón danger (desinstalar) ─────────────────────────────── */
QPushButton#danger {{
    background: {ERROR_C};
    color: white;
    border: none;
}}
QPushButton#danger:hover {{ background: #c83040; }}

/* ── Checkbox ───────────────────────────────────────────────── */
QCheckBox {{
    color: {TEXT_SEC};
    font-size: 11px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ── Progress bar ───────────────────────────────────────────── */
QProgressBar {{
    background: {BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:0.45 {TEAL}, stop:1 {VIOLET}
    );
    border-radius: 4px;
}}

/* ── Scroll Premium Glass ──────────────────────────────────── */
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: rgba(255, 255, 255, 0.05); width: 6px; margin: 0; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00F2FF, stop:1 #4A00E0);
    border: 1px solid #00F2FF; border-radius: 3px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E0FFFF, stop:1 #7B2FF7);
    border: 1px solid #E0FFFF;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: rgba(255, 255, 255, 0.05); height: 6px; margin: 0; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F2FF, stop:1 #4A00E0);
    border: 1px solid #00F2FF; border-radius: 3px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E0FFFF, stop:1 #7B2FF7);
    border: 1px solid #E0FFFF;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Sidebar ────────────────────────────────────────────────── */
QWidget#Sidebar {{
    background: {BG_SECONDARY};
    border-right: 1px solid {_GRAD.get("border_card", BORDER)};
}}

/* ── Nav bar inferior ───────────────────────────────────────── */
QWidget#NavBar {{
    background: {BG_SECONDARY};
    border-top: 1px solid {_GRAD.get("border_card", BORDER)};
}}

/* ── Log area ───────────────────────────────────────────────── */
QScrollArea#LogArea {{
    background: {BG_SURFACE};
    border-radius: 10px;
    border: 1px solid {BORDER};
}}

/* ── Info card verde ────────────────────────────────────────── */
QFrame#InfoCard {{
    background: {SUCCESS_BG};
    border-radius: 8px;
    border: 1px solid {SUCCESS};
}}

/* ── Card de inputs ─────────────────────────────────────────── */
QFrame#InputCard {{
    background: {BG_SURFACE};
    border-radius: {RADIUS_CARD}px;
    border: 1px solid {BORDER};
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
