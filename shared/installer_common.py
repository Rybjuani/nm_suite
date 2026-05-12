"""installer_common.py — Utilidades compartidas entre instaladores y desinstaladores."""
import sys
import os
import subprocess
import tempfile

from shared.theme import COLORS, TYPOGRAPHY, LAYOUT

# ── Colores para instaladores (desde theme hybrid) ──────────────────────────
_C = COLORS["dark_hybrid"]

BG_PRIMARY = _C["bg_primary"]
BG_SECONDARY = _C["bg_secondary"]
BG_SURFACE = _C["bg_surface"]
ACCENT = _C["accent"]
ACCENT_HOVER = _C["accent_hover"]
TEXT_PRIMARY = _C["text_primary"]
TEXT_SEC = _C["text_secondary"]
TEXT_TERT = _C["text_tertiary"]
BORDER = _C["border"]
SUCCESS = _C["success"]
WARNING_C = _C["warning"]
ERROR_C = _C["error"]

FONT_FAMILY = TYPOGRAPHY["font_family"]
RADIUS_BUTTON = LAYOUT["radius_button"]
RADIUS_CARD = LAYOUT["radius_card"]


def recurso(nombre: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base, nombre)


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
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()
        v = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), 4)
        if sys.getwindowsversion().build >= 22000:
            r, g, b = int(BG_SECONDARY[1:3], 16), int(BG_SECONDARY[3:5], 16), int(BG_SECONDARY[5:7], 16)
            color = ctypes.c_uint(r | (g << 8) | (b << 16))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
    except Exception:
        pass
