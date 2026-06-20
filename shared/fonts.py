"""
shared/fonts.py
API pública para la carga de fuentes del ADN visual del mockup canónico.

Las familias se buscan en `assets/fonts/` (empaquetado en el build) y se
registran con `QFontDatabase.addApplicationFont`. Si un `.ttf` no existe,
la familia correspondiente cae a fallback de sistema.

Familias del ADN mockup:
    serif  — Fraunces  (display, números bienestar, headings serif)
    sans   — Inter     (UI, body, labels)
    mono   — JetBrains Mono (timestamps, metadata clínica, log installer)

Uso típico (entrypoints `app/main_qt.py`, `hub/main_qt.py`, instaladores):

    from shared.fonts import load_fonts, FONT_SERIF, FONT_SANS, FONT_MONO

    app = QApplication(sys.argv)
    load_fonts()
    # ya se puede instanciar QFont(FONT_SERIF, 56), etc.

`load_fonts()` es idempotente — segundas llamadas son no-op.
"""

from __future__ import annotations

import os
import sys
import logging

_log = logging.getLogger(__name__)


# ── Constantes públicas ──────────────────────────────────────────────────────
# Se completan con la familia real cuando `load_fonts()` corre. Antes de
# eso devuelven los fallbacks de sistema declarados en el handoff §3.

FONT_SERIF: str = "Georgia"  # fallback hasta que se cargue Fraunces
FONT_SANS: str = "Segoe UI"  # fallback hasta que se cargue Inter
FONT_MONO: str = "Consolas"  # fallback hasta que se cargue JetBrains Mono


_LOADED: bool = False
_AVAILABLE_FAMILIES: list[str] = []


def _fonts_dirs() -> list[str]:
    """Devuelve las rutas absolutas donde buscar fuentes: assets/fonts del repo y local del usuario."""
    dirs = []
    # 1. assets/fonts de la app
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs.append(os.path.join(base, "assets", "fonts"))
    # 2. Carpeta de instalacion local del paciente
    dirs.append(os.path.join(os.path.expanduser("~"), "NeuroMood", "assets", "fonts"))
    return dirs


def load_fonts() -> dict[str, str]:
    """Carga las fuentes del handoff desde `assets/fonts/` con fallback de sistema.

    Devuelve un dict con las familias resueltas:
        {"serif": ..., "sans": ..., "mono": ...}

    Idempotente: una vez cargadas, llamadas sucesivas no recargan nada.

    No falla si `assets/fonts/` no existe o si los .ttf están incompletos —
    las constantes `FONT_*` simplemente se quedan con el fallback de sistema.
    """
    global FONT_SERIF, FONT_SANS, FONT_MONO, _LOADED, _AVAILABLE_FAMILIES

    if _LOADED:
        return {"serif": FONT_SERIF, "sans": FONT_SANS, "mono": FONT_MONO}

    try:
        from PyQt6.QtGui import QFontDatabase
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        _log.debug("PyQt6 no disponible — se omite carga de fuentes")
        _LOADED = True
        return {"serif": FONT_SERIF, "sans": FONT_SANS, "mono": FONT_MONO}

    if QApplication.instance() is None:
        # QFontDatabase.addApplicationFont requiere QApplication viva.
        # Hacemos la carga lazy: la próxima llamada con QApplication existente
        # cargará. No marcamos _LOADED para permitir reintentar.
        _log.debug("Sin QApplication — load_fonts() se reintentará tras crearla")
        return {"serif": FONT_SERIF, "sans": FONT_SANS, "mono": FONT_MONO}

    fdirs = _fonts_dirs()
    any_dir_exists = any(os.path.isdir(d) for d in fdirs)
    if not any_dir_exists:
        _log.warning(
            "Ninguno de los directorios de fuentes existe en %s — usando fallback de sistema", fdirs
        )
        _LOADED = True
        return {"serif": FONT_SERIF, "sans": FONT_SANS, "mono": FONT_MONO}

    # Archivos esperados por familia. Se registran todos los encontrados para que
    # Qt pueda resolver pesos/itálicas; la preferencia final se elige por familia.
    expected = {
        "serif": [
            "Fraunces-Variable.ttf",
            "Fraunces-Italic-Variable.ttf",
            "Fraunces[SOFT,WONK,opsz,wght].ttf",
            "Fraunces-Italic[SOFT,WONK,opsz,wght].ttf",
            "Newsreader-Variable.ttf",
            "Newsreader-Variable.woff2",
            "Newsreader-Regular.ttf",
            "Newsreader-Regular.woff2",
            "Newsreader-Medium.ttf",
            "Newsreader-Medium.woff2",
            "Newsreader-SemiBold.ttf",
            "Newsreader-SemiBold.woff2",
            "Newsreader-Italic.ttf",
            "Newsreader-Italic.woff2",
        ],
        "sans": [
            "Inter-Variable.ttf",
            "Inter[opsz,wght].ttf",
            "Inter-Regular.ttf",
            "Inter-Medium.ttf",
            "Inter-SemiBold.ttf",
            "Inter-Bold.ttf",
            "Manrope-Variable.ttf",
            "Manrope-Variable.woff2",
            "Manrope-Regular.ttf",
            "Manrope-Regular.woff2",
            "Manrope-Medium.ttf",
            "Manrope-Medium.woff2",
            "Manrope-SemiBold.ttf",
            "Manrope-SemiBold.woff2",
            "Manrope-Bold.ttf",
            "Manrope-Bold.woff2",
            # Fallback secundario (compat con sistema previo)
            "PlusJakartaSans-Regular.ttf",
            "PlusJakartaSans-Medium.ttf",
            "PlusJakartaSans-SemiBold.ttf",
            "PlusJakartaSans-Bold.ttf",
            "DMSans-Regular.ttf",
            "DMSans-Medium.ttf",
            "DMSans-Bold.ttf",
        ],
        "mono": [
            "JetBrainsMono-Variable.ttf",
            "JetBrainsMono-Regular.ttf",
            "JetBrainsMono-Medium.ttf",
            "JetBrainsMono-Bold.ttf",
        ],
    }

    families_loaded: list[str] = []
    for _role, filenames in expected.items():
        for fn in filenames:
            for fdir in fdirs:
                path = os.path.join(fdir, fn)
                if not os.path.exists(path):
                    continue
                fid = QFontDatabase.addApplicationFont(path)
                if fid < 0:
                    _log.warning("QFontDatabase rechazó %s", fn)
                    continue
                for fam in QFontDatabase.applicationFontFamilies(fid):
                    if fam and fam not in families_loaded:
                        families_loaded.append(fam)
                break  # si se cargo de un directorio, no hace falta buscar en el otro

    _AVAILABLE_FAMILIES = list(families_loaded)

    # Preferencias por rol — el primero presente gana.
    serif_pref = ("Fraunces", "Newsreader", "Source Serif Pro", "Georgia")
    sans_pref = ("Inter", "Manrope", "Plus Jakarta Sans", "DM Sans", "Satoshi", "Segoe UI")
    mono_pref = ("JetBrains Mono", "Cascadia Mono", "Consolas")

    def _pick(prefs: tuple[str, ...], fallback: str) -> str:
        for p in prefs:
            if p in families_loaded:
                return p
            for fam in families_loaded:
                if fam.startswith(p):
                    return fam
        return fallback

    FONT_SERIF = _pick(serif_pref, "Georgia")
    FONT_SANS = _pick(sans_pref, "Segoe UI")
    FONT_MONO = _pick(mono_pref, "Consolas")

    _LOADED = True
    return {"serif": FONT_SERIF, "sans": FONT_SANS, "mono": FONT_MONO}


def font_summary() -> str:
    """Resumen humano-legible para diagnóstico (`-c` one-liner del README)."""
    if not _LOADED:
        load_fonts()
    return f"sans:  {FONT_SANS}\nserif: {FONT_SERIF}\nmono:  {FONT_MONO}"


def available_families() -> list[str]:
    """Lista de familias que efectivamente cargaron desde assets/fonts/."""
    if not _LOADED:
        load_fonts()
    return list(_AVAILABLE_FAMILIES)
