"""
_nm_screenshots.py  —  NeuroMood Suite · Screenshot Capture
Uso: python _nm_screenshots.py   (desde la raiz del proyecto)
Guarda capturas en ./_doc_screenshots/
"""
import sys, os, time, subprocess, ctypes
from PIL import ImageGrab

# DPI awareness para que las coordenadas win32 coincidan con la captura
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import win32gui, win32con, win32api

BASE   = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "_doc_screenshots")
os.makedirs(OUTPUT, exist_ok=True)


# ── Helpers Win32 ───────────────────────────────────────────────────────────

class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def _visible_rect(hwnd):
    """Rect visible real de la ventana via DWM (excluye bordes invisibles)."""
    r = _RECT()
    if ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) == 0:
        return r.left, r.top, r.right, r.bottom
    return win32gui.GetWindowRect(hwnd)


def _find(frag, timeout=14):
    """Encuentra una ventana visible cuyo titulo contenga 'frag'."""
    end = time.time() + timeout
    while time.time() < end:
        found = [None]

        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    if frag.lower() in win32gui.GetWindowText(hwnd).lower():
                        found[0] = hwnd
                        return False
                except Exception:
                    pass
            return True

        try:
            win32gui.EnumWindows(cb, None)
        except Exception:
            pass
        if found[0]:
            return found[0]
        time.sleep(0.25)
    return None


def _shot(hwnd, path, retries=2):
    """Captura la ventana y guarda la imagen."""
    for attempt in range(retries + 1):
        try:
            bbox = _visible_rect(hwnd)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w < 10 or h < 10:
                raise ValueError(f"Bbox invalido: {bbox}")
            img = ImageGrab.grab(bbox=bbox)
            img.save(path)
            print(f"    OK  {os.path.basename(path)}  ({w}x{h}px)")
            return img
        except Exception as e:
            if attempt < retries:
                time.sleep(0.5)
            else:
                print(f"    FAIL  {os.path.basename(path)}: {e}")
    return None


def _set_size_centered(hwnd, w, h):
    """Redimensiona y centra la ventana; la pone siempre al frente."""
    sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    x = (sw - w) // 2
    y = max(30, (sh - h) // 2 - 30)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, w, h, 0)
    time.sleep(0.1)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, x, y, w, h, 0)


def _click_screen(sx, sy):
    """Mueve el cursor y simula click izquierdo."""
    ctypes.windll.user32.SetCursorPos(int(sx), int(sy))
    time.sleep(0.15)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP


# ── Capture funciones ───────────────────────────────────────────────────────

def capture_app(app_id, script_rel, frag, wait=5.0, size=(960, 680)):
    out = os.path.join(OUTPUT, f"{app_id}.png")
    print(f"  [{app_id}]  lanzando...")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, script_rel)],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(wait)
    hwnd = _find(frag)
    if not hwnd:
        print(f"    ! ventana no encontrada para '{frag}'")
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except Exception:
            proc.kill()
        return None

    # Maximizar ventana
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.6)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.45)

    _shot(hwnd, out)

    proc.terminate()
    try:
        proc.wait(timeout=4)
    except Exception:
        proc.kill()
    time.sleep(0.35)
    return out


def capture_installer():
    """Captura pagina 0 (Bienvenida) y pagina 1 (Seleccion) del instalador."""
    print("  [installer]  lanzando...")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "installer.py")],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3.8)
    hwnd = _find("Instalador", timeout=6)
    if not hwnd:
        print("    ! ventana del instalador no encontrada")
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except Exception:
            proc.kill()
        return

    # Traer al frente (el instalador no es redimensionable: 740x540)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.6)

    # Captura pagina 0 (Bienvenida)
    _shot(hwnd, os.path.join(OUTPUT, "installer_p0.png"))

    # Navegar a pagina 1: click en "Siguiente ->"
    # Nav bar: height=58, pack side=bottom. Boton: side=right, padx=16, width=140, height=36, pady=11
    vl, vt, vr, vb = _visible_rect(hwnd)
    btn_cx = vr - 16 - 70          # right_edge - padx - mitad_ancho
    btn_cy = vb - 58 + 11 + 18     # bottom - nav_h + pady_top + mitad_altura
    _click_screen(btn_cx, btn_cy)
    time.sleep(1.1)

    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.4)

    # Captura pagina 1 (Seleccion de apps)
    _shot(hwnd, os.path.join(OUTPUT, "installer_p1.png"))

    proc.terminate()
    try:
        proc.wait(timeout=4)
    except Exception:
        proc.kill()
    time.sleep(0.4)


def capture_uninstaller():
    """Captura la pantalla de confirmacion del desinstalador."""
    print("  [uninstaller]  lanzando...")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "uninstaller.py")],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3.8)
    hwnd = _find("Desinstalar", timeout=6)
    if not hwnd:
        print("    ! ventana del desinstalador no encontrada")
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except Exception:
            proc.kill()
        return

    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.6)
    _shot(hwnd, os.path.join(OUTPUT, "uninstaller.png"))

    proc.terminate()
    try:
        proc.wait(timeout=4)
    except Exception:
        proc.kill()
    time.sleep(0.4)


# ── Main ────────────────────────────────────────────────────────────────────

APPS = [
    ("termometro",    "apps/termometro/main.py",    "Termómetro"),
    ("visualizador",  "apps/visualizador/main.py",  "Visualizador"),
    ("temporizador",  "apps/temporizador/main.py",  "Temporizador"),
    ("respiracion",   "apps/respiracion/main.py",   "Respiración"),
    ("checklist",     "apps/checklist/main.py",     "Checklist"),
    ("recordatorios", "apps/recordatorios/main.py", "Recordatorios"),
    ("pensamientos",  "apps/pensamientos/main.py",  "Pensamientos"),
    ("activacion",    "apps/activacion/main.py",    "Activación"),
]


def main():
    print("=" * 50)
    print("  NeuroMood Screenshot Capture")
    print(f"  Destino: {OUTPUT}")
    print("=" * 50)

    print("\n[1/3] Apps...")
    for app_id, script, frag in APPS:
        capture_app(app_id, script, frag)

    print("\n[2/3] Instalador...")
    capture_installer()

    print("\n[3/3] Desinstalador...")
    capture_uninstaller()

    captured = [f for f in os.listdir(OUTPUT) if f.endswith(".png")]
    print(f"\nCompletado. {len(captured)} capturas en: {OUTPUT}")


if __name__ == "__main__":
    main()
