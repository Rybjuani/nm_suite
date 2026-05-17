"""_audit_mockup_grid.py — Genera audit_grid.png comparando mockup vs capturas reales.

Pipeline:
  1) Renderiza cada <div id="sN"> del mockup HTML con Chrome headless.
  2) Reutiliza capturas reales de _test_screens/smoke/.
  3) Captura los 3 installers Qt sin ejecutar instalación (solo abre y graba).
  4) Compone un PNG vertical con filas de [mockup | real] por pantalla.

Uso:
  python _audit_mockup_grid.py
"""
from __future__ import annotations

import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
MOCKUP_HTML = Path("C:/Users/nosom/Downloads/neuromood_v3_all_screens.html")
SMOKE_DIR   = ROOT / "_test_screens" / "smoke"
OUT_DIR     = ROOT / "_test_screens" / "audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Map (section_id, label, real_capture_filename_or_None)
SCREENS = [
    ("s1",  "Home paciente",          "s01_home.png"),
    ("s2",  "Ánimo",                  "s_mod_animo.png"),
    ("s3",  "Respiración",            "s_mod_respiracion.png"),
    ("s4",  "Registro TCC",           "s_mod_registro.png"),
    ("s5",  "Rutina",                 "s_mod_rutina.png"),
    ("s6",  "Actividades",            "s_mod_actividades.png"),
    ("s7",  "Temporizador",           "s_mod_timer.png"),
    ("s8",  "Avisos",                 "s_mod_avisos.png"),
    ("s9",  "Hub · Pacientes",        "h02_pacientes.png"),
    ("s10", "Hub · Dashboard",        "h03_dashboard.png"),
    ("s11", "Hub · IA",               "h05_ia_detalle.png"),
    ("s12", "Hub · Config",           "h04_config.png"),
    ("s13", "Instalador Suite",       "i01_installer.png"),
    ("s14", "Instalador Hub",              "i02_installer_pro.png"),
    ("s15", "Desinstalador",          "i03_uninstaller.png"),
]


# ── PASO 1: Renderizar mockup secciones con Chrome headless ─────────────────

def render_mockup_section(html_src: str, section_id: str, out_png: Path,
                          width: int = 1280, height: int = 1600) -> bool:
    """Genera un HTML temporal con `section_id` visible y lo captura con Chrome."""
    css_override = (
        "<style>"
        ".page{display:none !important;}"
        f"#{section_id}{{display:block !important;}}"
        "body{background:#0f172a;}"  # match dark mockup bg
        "</style>"
    )
    html_mod = html_src.replace("</head>", css_override + "</head>", 1)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False, dir=str(OUT_DIR)
    )
    tmp.write(html_mod)
    tmp.close()
    tmp_url = "file:///" + tmp.name.replace("\\", "/")

    try:
        cmd = [
            CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--hide-scrollbars", "--default-background-color=00000000",
            f"--window-size={width},{height}",
            f"--screenshot={out_png}",
            tmp_url,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode != 0:
            print(f"  Chrome error {section_id}: {r.stderr.decode(errors='ignore')[:200]}")
            return False
        return out_png.exists()
    finally:
        try: os.unlink(tmp.name)
        except Exception: pass


def crop_mockup(img_path: Path) -> Path:
    """Recorta el área no-vacía (la 'page' visible) para evitar márgenes enormes."""
    im = Image.open(img_path).convert("RGB")
    bbox = im.getbbox()
    if not bbox:
        return img_path
    # tighten: scan rows from top/bottom that are uniform bg
    px = im.load()
    w, h = im.size
    bg = px[0, 0]
    def row_empty(y):
        for x in range(0, w, 8):
            if px[x, y] != bg: return False
        return True
    top = 0
    while top < h - 1 and row_empty(top): top += 1
    bot = h - 1
    while bot > top and row_empty(bot): bot -= 1
    if bot - top > 100:
        im = im.crop((0, max(0, top - 20), w, min(h, bot + 20)))
        im.save(img_path)
    return img_path


# ── PASO 2: Capturar installers Qt sin ejecutar instalación ─────────────────

def capture_installers():
    """Abre cada installer/desinstalador en su pantalla inicial, captura, cierra."""
    script = r'''
import sys, os
from pathlib import Path
sys.path.insert(0, r"%ROOT%")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

app = QApplication.instance() or QApplication(sys.argv)

results = {}

def _grab(win, out):
    QApplication.processEvents()
    pix = win.grab()
    pix.save(out)
    results[out] = True

# Instalador Suite
from installers.installer import InstaladorNeuroMood
w1 = InstaladorNeuroMood()
w1.show(); QApplication.processEvents()
_grab(w1, r"%OUT%\i01_installer.png")
w1.close()

# Instalador Hub
from installers.installer_pro import InstaladorPro
w2 = InstaladorPro()
w2.show(); QApplication.processEvents()
_grab(w2, r"%OUT%\i02_installer_pro.png")
w2.close()

# Desinstalador Suite
from installers.uninstaller import DesinstaladorNeuroMood
w3 = DesinstaladorNeuroMood()
w3.show(); QApplication.processEvents()
_grab(w3, r"%OUT%\i03_uninstaller.png")
w3.close()

print("OK", len(results))
'''
    script = script.replace("%ROOT%", str(ROOT)).replace("%OUT%", str(SMOKE_DIR))
    tmp = SMOKE_DIR.parent / "_audit_installers_runner.py"
    tmp.write_text(script, encoding="utf-8")
    r = subprocess.run([sys.executable, str(tmp)], capture_output=True, text=True, timeout=60)
    print("  installers:", r.stdout.strip(), r.stderr.strip()[:200] if r.stderr else "")
    try: tmp.unlink()
    except Exception: pass


# ── PASO 3: Composición ──────────────────────────────────────────────────────

ROW_H = 480
MOCK_W = 720
REAL_W = 720
PAD = 16
LABEL_H = 36
BG = (15, 23, 42)         # slate-900
LABEL_BG = (30, 41, 59)   # slate-800
TEXT = (226, 232, 240)
ACCENT = (99, 102, 241)


def _font(size=14, bold=False):
    try:
        name = "segoeuib.ttf" if bold else "segoeui.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    iw, ih = img.size
    ratio = min(max_w / iw, max_h / ih)
    nw, nh = int(iw * ratio), int(ih * ratio)
    return img.resize((nw, nh), Image.LANCZOS)


def compose():
    rows_data = []
    for sid, label, real_name in SCREENS:
        mock = OUT_DIR / f"mock_{sid}.png"
        real = SMOKE_DIR / real_name if real_name else None
        rows_data.append((sid, label, mock, real))

    total_h = LABEL_H + len(rows_data) * (ROW_H + PAD * 2 + LABEL_H)
    total_w = PAD * 3 + MOCK_W + REAL_W
    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.rectangle((0, 0, total_w, LABEL_H), fill=LABEL_BG)
    draw.text((PAD, 8), "NeuroMood V3 — Audit grid  |  Mockup ←→ Captura real",
              fill=TEXT, font=_font(15, bold=True))
    y = LABEL_H

    for sid, label, mock_path, real_path in rows_data:
        # Row label band
        draw.rectangle((0, y, total_w, y + LABEL_H), fill=LABEL_BG)
        draw.text((PAD, y + 8), f"{sid}  ·  {label}",
                  fill=ACCENT, font=_font(13, bold=True))
        y += LABEL_H

        # Mockup
        try:
            if mock_path.exists():
                m = Image.open(mock_path).convert("RGB")
                m = _fit(m, MOCK_W, ROW_H)
                canvas.paste(m, (PAD, y + (ROW_H - m.height) // 2))
            else:
                draw.text((PAD + 20, y + ROW_H // 2),
                          f"[mock {sid} missing]", fill=TEXT, font=_font(12))
        except Exception as e:
            draw.text((PAD + 20, y + ROW_H // 2),
                      f"[mock err: {e}]", fill=(239, 68, 68), font=_font(12))

        # Real
        try:
            if real_path and real_path.exists():
                r = Image.open(real_path).convert("RGB")
                r = _fit(r, REAL_W, ROW_H)
                canvas.paste(r, (PAD * 2 + MOCK_W, y + (ROW_H - r.height) // 2))
            else:
                draw.text((PAD * 2 + MOCK_W + 20, y + ROW_H // 2),
                          f"[real {sid} missing]", fill=TEXT, font=_font(12))
        except Exception as e:
            draw.text((PAD * 2 + MOCK_W + 20, y + ROW_H // 2),
                      f"[real err: {e}]", fill=(239, 68, 68), font=_font(12))

        y += ROW_H + PAD * 2

    out = OUT_DIR / "audit_grid.png"
    canvas.save(out, optimize=True)
    print(f"  Saved: {out}  ({canvas.size[0]}x{canvas.size[1]})")
    return out


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if not MOCKUP_HTML.exists():
        print(f"ERROR: mockup HTML not found: {MOCKUP_HTML}")
        sys.exit(1)

    print("[1/3] Renderizando 15 secciones del mockup con Chrome headless...")
    html_src = MOCKUP_HTML.read_text(encoding="utf-8")
    for sid, label, _ in SCREENS:
        out_png = OUT_DIR / f"mock_{sid}.png"
        ok = render_mockup_section(html_src, sid, out_png)
        if ok:
            crop_mockup(out_png)
            print(f"  {sid}  {label}  ok")
        else:
            print(f"  {sid}  {label}  FAIL")

    print("\n[2/3] Capturando 3 installers Qt...")
    capture_installers()

    print("\n[3/3] Componiendo audit_grid.png...")
    compose()
    print("\nListo. Abre _test_screens/audit/audit_grid.png")


if __name__ == "__main__":
    main()
