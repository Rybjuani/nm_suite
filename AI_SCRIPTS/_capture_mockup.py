"""
_capture_mockup.py — Captura pantallas del mockup HTML usando Chrome headless.
Genera PNGs para usar en los PDFs.
"""

import os, re, subprocess, tempfile, shutil, time
from pathlib import Path

PROJ = Path(__file__).resolve().parent
HTML = PROJ / "neuromood_v3_all_screens.html"
OUT = PROJ / "_qa_output" / "mockup_screens"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

SCREENS = {
    "s1": "01 Home · Grid de módulos",
    "s2": "02 Ánimo · Registro emocional",
    "s3": "03 Respiración · Guía animada",
    "s4": "04 TCC · Registro de pensamientos",
    "s5": "05 Rutina · Checklist diario",
    "s6": "06 Actividades · Activación conductual",
    "s7": "07 Timer · Sesiones de enfoque",
    "s8": "08 Avisos · Recordatorios",
    "s9": "09 Hub · Lista de Pacientes",
    "s10": "10 Hub · Dashboard",
    "s11": "11 Hub · IA Asistente",
    "s12": "12 Hub · Configuración",
    "s13": "13 Instalador Suite",
    "s14": "14 Instalador Hub Pro",
    "s15": "15 Desinstalador Suite",
}


def capture_all():
    if not os.path.exists(CHROME):
        print(f"ERROR: Chrome not found at {CHROME}")
        return False

    os.makedirs(OUT, exist_ok=True)

    html_text = HTML.read_text(encoding="utf-8")

    # Pre-extract CSS and JS for each modified HTML
    for screen_id, label in SCREENS.items():
        print(f"  Capturing {screen_id} — {label}...")

        # Create a modified HTML that shows only this screen
        modified = html_text
        # Remove existing "show" classes
        modified = re.sub(r'class="([^"]*)\bshow\b([^"]*)"', r'class="\1\2"', modified)
        # Add "show" to the target screen div
        modified = modified.replace(f'<div id="{screen_id}" class="page"', f'<div id="{screen_id}" class="page show"')

        # Handle screen with tabs — set correct active tabs
        if screen_id in ("s1","s2","s3","s4","s5","s6","s7","s8"):
            # Patient tabs
            modified = modified.replace('id="tabs-paciente" style="display:none"', 'id="tabs-paciente"')
            modified = modified.replace('id="tabs-hub" style="display:none"', 'id="tabs-hub" style="display:none"')
            modified = modified.replace('id="tabs-installer" style="display:none"', 'id="tabs-installer" style="display:none"')
        elif screen_id in ("s9","s10","s11","s12"):
            # Hub tabs
            modified = modified.replace('id="tabs-paciente" style="display:none"', 'id="tabs-paciente" style="display:none"')
            modified = modified.replace('id="tabs-hub" style="display:none"', 'id="tabs-hub"')
            modified = modified.replace('id="tabs-installer" style="display:none"', 'id="tabs-installer" style="display:none"')
        elif screen_id in ("s13","s14","s15"):
            # Installer tabs
            modified = modified.replace('id="tabs-paciente" style="display:none"', 'id="tabs-paciente" style="display:none"')
            modified = modified.replace('id="tabs-hub" style="display:none"', 'id="tabs-hub" style="display:none"')
            modified = modified.replace('id="tabs-installer" style="display:none"', 'id="tabs-installer"')

        # Also remove chrome "active" from wrong block buttons
        modified = modified.replace(
            '<button id="btn-paciente" class="block-btn active"',
            '<button id="btn-paciente" class="block-btn"',
        )

        tmp_path = OUT / f"_tmp_{screen_id}.html"
        tmp_path.write_text(modified, encoding="utf-8")
        out_img = OUT / f"{screen_id}.png"

        try:
            result = subprocess.run(
                [
                    CHROME,
                    "--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--screenshot={out_img}",
                    "--window-size=1200,900",
                    "--hide-scrollbars",
                    f"file:///{tmp_path.as_posix()}",
                ],
                capture_output=True, text=True, timeout=30,
            )
            if os.path.exists(out_img) and os.path.getsize(out_img) > 1000:
                print(f"    OK: {out_img} ({os.path.getsize(out_img)//1024} KB)")
            else:
                print(f"    WARN: Screenshot may be empty for {screen_id}")
        except subprocess.TimeoutExpired:
            print(f"    ERROR: Timeout for {screen_id}")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    print(f"\nDone. {len(list(OUT.glob('*.png')))} screenshots in {OUT}")
    return True

if __name__ == "__main__":
    capture_all()
