"""
capturar_pantallas.py — Captura ventanas en segundo plano (PrintWindow API).
No interfiere con otros procesos del usuario — la captura es invisible.
"""
import subprocess
import time
import os
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path
from PIL import Image as PILImage
import struct

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASE, "dist")
SCREENSHOTS = os.path.join(BASE, "screenshots")
Path(SCREENSHOTS).mkdir(exist_ok=True)

# ── Win32 API ─────────────────────────────────────────────────
user32 = ctypes.windll.user32
gdi32  = ctypes.windll.gdi32

SW_RESTORE = 9
SW_MINIMIZE = 6
WM_CLOSE = 0x0010
PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2

BI_RGB = 0
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          ctypes.c_uint32),
        ("biWidth",         ctypes.c_int32),
        ("biHeight",        ctypes.c_int32),
        ("biPlanes",        ctypes.c_uint16),
        ("biBitCount",      ctypes.c_uint16),
        ("biCompression",   ctypes.c_uint32),
        ("biSizeImage",     ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed",       ctypes.c_uint32),
        ("biClrImportant",  ctypes.c_uint32),
    ]

class RGBQUAD(ctypes.Structure):
    _fields_ = [
        ("rgbBlue",     ctypes.c_ubyte),
        ("rgbGreen",    ctypes.c_ubyte),
        ("rgbRed",      ctypes.c_ubyte),
        ("rgbReserved", ctypes.c_ubyte),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", RGBQUAD * 256),
    ]

# ── Funciones Win32 ───────────────────────────────────────────
def _enum_windows(hwnd, windows):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            windows.append((hwnd, buf.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.py_object)

def find_window(substr):
    windows = []
    user32.EnumWindows(WNDENUMPROC(_enum_windows), ctypes.py_object(windows))
    low = substr.lower()
    for hwnd, title in windows:
        if low in title.lower():
            return hwnd, title
    return None, None

def get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def close_window(hwnd):
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

def minimize_window(hwnd):
    user32.ShowWindow(hwnd, SW_MINIMIZE)

def capture_window_invisible(hwnd):
    """Captura contenido de la ventana usando PrintWindow (invisible)."""
    left, top, right, bottom = get_window_rect(hwnd)
    width = right - left
    height = bottom - top

    if width < 50 or height < 50:
        return None

    hdc_window = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)

    # Usar BITMAPINFO con 32 bits para datos RGBA
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # negativo = top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    pixels = ctypes.create_string_buffer(width * height * 4)
    hbmp = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(bmi), DIB_RGB_COLORS,
                                   ctypes.byref(pixels), None, 0)
    old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

    # Capturar
    result = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)

    # Convertir a PIL Image
    if result:
        # Los datos vienen como BGRA, convertir a RGBA
        raw = bytes(pixels)
        # Reordenar BGRA -> RGBA
        rgba_data = bytearray(width * height * 4)
        for i in range(0, len(raw), 4):
            b_val, g_val, r_val, a_val = raw[i], raw[i+1], raw[i+2], raw[i+3]
            rgba_data[i]   = r_val
            rgba_data[i+1] = g_val
            rgba_data[i+2] = b_val
            rgba_data[i+3] = a_val
        img = PILImage.frombytes("RGBA", (width, height), bytes(rgba_data))
    else:
        img = None

    # Limpiar
    gdi32.SelectObject(hdc_mem, old_bmp)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwnd, hdc_window)

    return img

def kill_all_neuromood():
    names = [
        "TermometroEmocional.exe", "VisualizadorEvolucion.exe",
        "GuiaRespiracion.exe", "AsistenteActivacion.exe",
        "RecordatoriosBienestar.exe", "TemporizadorActividades.exe",
        "ChecklistRutina.exe", "RegistroPensamientos.exe",
        "Instalar NeuroMood Suite.exe", "Desinstalar NeuroMood.exe",
        "_nm_desinstalar.exe",
    ]
    for name in names:
        try:
            subprocess.run(["taskkill", "/F", "/IM", name],
                           capture_output=True, timeout=5)
        except Exception:
            pass
    time.sleep(1)

def capturar_app(exe_file, window_substr, out_name, timeout=25, extra_args=None):
    exe_path = os.path.join(DIST, exe_file)
    if not os.path.exists(exe_path):
        print(f"  [!!] No existe: {exe_path}")
        return False

    print(f"  Lanzando {exe_file}...")
    args = [exe_path]
    if extra_args:
        args.extend(extra_args)
    proc = subprocess.Popen(args)

    hwnd = None
    title = None
    for i in range(timeout * 2):
        time.sleep(1)
        hwnd, title = find_window(window_substr)
        if hwnd:
            break
        if i % 5 == 0 and i > 0:
            print(f"  ... esperando ({i}s)")

    if not hwnd:
        print(f"  [!!] Ventana no encontrada: '{window_substr}'")
        proc.kill()
        return False

    print(f"  Ventana: {repr(title)}")
    # Minimizar para que no moleste visualmente
    minimize_window(hwnd)
    time.sleep(0.3)

    img = capture_window_invisible(hwnd)
    if img is None:
        print(f"  [!!] PrintWindow fallo (posible DPI o composicion)")
        close_window(hwnd)
        proc.kill()
        return False

    out_path = os.path.join(SCREENSHOTS, out_name)
    img.convert("RGB").save(out_path, "PNG")
    print(f"  [OK] {out_name} ({img.width}x{img.height})")

    close_window(hwnd)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    time.sleep(1)
    return True

def main():
    print("NeuroMood Suite - Captura invisible de pantallas\n" + "=" * 60)
    print("Cerrando procesos previos...")
    kill_all_neuromood()
    print("Listo.\n")

    apps = [
        ("TermometroEmocional.exe",     "NeuroMood", "01_termometro.png"),
        ("VisualizadorEvolucion.exe",   "NeuroMood", "02_visualizador.png"),
        ("GuiaRespiracion.exe",         "NeuroMood", "03_respiracion.png"),
        ("AsistenteActivacion.exe",     "NeuroMood", "04_activacion.png"),
        ("RecordatoriosBienestar.exe",  "NeuroMood", "05_recordatorios.png"),
        ("TemporizadorActividades.exe", "NeuroMood", "06_temporizador.png"),
        ("ChecklistRutina.exe",         "NeuroMood", "07_checklist.png"),
        ("RegistroPensamientos.exe",    "NeuroMood", "08_pensamientos.png"),
    ]

    for exe, substr, archivo in apps:
        print(f"\n[{archivo}]")
        capturar_app(exe, substr, archivo)

    kill_all_neuromood()

    print(f"\n[Instalador]")
    capturar_app("Instalar NeuroMood Suite.exe", "Instalador \u2014 NeuroMood",
                 "09_instalador.png", timeout=35)

    kill_all_neuromood()

    print(f"\n[Desinstalador]")
    capturar_app("Desinstalar NeuroMood.exe", "Desinstalar \u2014 NeuroMood",
                 "10_desinstalador.png", timeout=25,
                 extra_args=["--from-temp", "--install-dir",
                             os.path.join(BASE, "NeuroMood_temp")])

    print(f"\n{'='*60}")
    print(f"Capturas en: {SCREENSHOTS}")
    archivos = list(Path(SCREENSHOTS).glob("*.png"))
    print(f"Total: {len(archivos)} de 10 capturas generadas.")

if __name__ == "__main__":
    main()
