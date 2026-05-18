"""
shared/icons_svg.py — Sistema propio de iconos SVG NeuroMood v3.

Reemplaza QtAwesome con paths SVG inline definidos en el handoff:
``design_handoff_neuromood_v3/js/v3-emojis.jsx`` función ``NMIcon``.

Cada icono se define como un fragmento SVG (sin el wrapper ``<svg>``) que se
inserta en un viewBox 0 0 24 24 con stroke = color, stroke-width = proporcional
al tamaño según ``shared.theme.icon_stroke_width(size)``.

Uso:
    from shared.icons_svg import nm_svg_pixmap, has_icon, available_icons

    pix = nm_svg_pixmap("home", color="#0f172a", size=24)
    label.setPixmap(pix)
"""

import os
import sys
import logging

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

_log = logging.getLogger(__name__)

try:
    from shared.theme import icon_stroke_width
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme import icon_stroke_width


# ── Catálogo de iconos v3 ─────────────────────────────────────────────────────
#
# Plantillas con ``{color}`` (hex) y ``{sw_07}`` (= stroke_width * 0.7). El
# stroke-width principal viene del wrapper <svg>.
#
# Convenciones del wrapper SVG:
#   fill="none" stroke=color stroke-width=sw stroke-linecap=round stroke-linejoin=round
#
# Iconos con relleno sólido (play/pause/stop/skip/dots/eyes) usan
# explícitamente ``fill="{color}"`` + ``stroke="none"`` en sus elementos.

ICON_BODIES: dict[str, str] = {
    # ── Sidebar / core ──────────────────────────────────────────────────────
    "home":         '<path d="M3 11l9-7 9 7v9a2 2 0 0 1-2 2h-4v-6h-6v6H5a2 2 0 0 1-2-2v-9z"/>',
    "mood":         '<circle cx="12" cy="12" r="9"/>'
                    '<circle cx="8.5" cy="10" r="1.1" fill="{color}" stroke="none"/>'
                    '<circle cx="15.5" cy="10" r="1.1" fill="{color}" stroke="none"/>'
                    '<path d="M8 14.5c2 2 6 2 8 0"/>',
    "breath":       '<path d="M12 13c0-3.5-2.5-6-6-6c0 3.5 2.5 6 6 6z'
                    'M12 13c0-3.5 2.5-6 6-6c0 3.5-2.5 6-6 6z'
                    'M12 13c0 3.5-2.5 6-6 6c0-3.5 2.5-6 6-6z'
                    'M12 13c0 3.5 2.5 6 6 6c0-3.5-2.5-6-6-6z"/>',
    "lungs":        '<path d="M12 4v9M9 9C9 6 5 5 5 9c0 3 0 7 2 9 2 1.5 4 1 4-2V9z'
                    'M15 9c0-3 4-4 4 0 0 3 0 7-2 9-2 1.5-4 1-4-2V9z"/>',
    "brain":        '<path d="M7 4a3 3 0 0 0-3 3v3c0 1.5 1 2.5 1 4v3a3 3 0 0 0 3 3"/>'
                    '<path d="M17 4a3 3 0 0 1 3 3v3c0 1.5-1 2.5-1 4v3a3 3 0 0 1-3 3"/>'
                    '<path d="M8 9c1.5 0 3 1 3 3M16 9c-1.5 0-3 1-3 3M11 12v8M13 12v8"/>',
    "bulb":         '<path d="M9 17h6M10 20h4M12 3a6 6 0 0 0-4 10.5c1 1 1.5 2 1.5 3.5h5c0-1.5.5-2.5 1.5-3.5A6 6 0 0 0 12 3z"/>',
    "thought":      '<path d="M9 17h6M10 20h4M12 3a6 6 0 0 0-4 10.5c1 1 1.5 2 1.5 3.5h5c0-1.5.5-2.5 1.5-3.5A6 6 0 0 0 12 3z"/>'
                    '<path d="M12 8v4M10 10h4"/>',
    "routine":      '<rect x="3" y="5" width="18" height="16" rx="2"/>'
                    '<path d="M8 2v6M16 2v6M3 10h18"/>'
                    '<path d="M8 15l2 2 4-4"/>',
    "spark":        '<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/>',
    "sparkle":      '<path d="M12 2l1.5 5L18 9l-4.5 2L12 16l-1.5-5L6 9l4.5-2z"/>'
                    '<path d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z" stroke-width="{sw_07}"/>'
                    '<path d="M5 4l.5 1.5L7 6l-1.5.5L5 8l-.5-1.5L3 6l1.5-.5z" stroke-width="{sw_07}"/>',
    "timer":        '<circle cx="12" cy="13" r="8"/>'
                    '<path d="M12 13V8M9 2h6M17 5l2 2"/>',
    "bell":         '<path d="M6 9a6 6 0 0 1 12 0c0 6 2 7 2 7H4s2-1 2-7z"/>'
                    '<path d="M10 20a2 2 0 0 0 4 0"/>',
    "user":         '<circle cx="12" cy="8" r="3.5"/>'
                    '<path d="M4 21c0-3.5 3-6 8-6s8 2.5 8 6"/>',
    "cog":          '<circle cx="12" cy="12" r="3"/>'
                    '<path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.5 4.5l1.5 1.5M18 18l1.5 1.5M4.5 19.5l1.5-1.5M18 6l1.5-1.5"/>',
    # ── Hub ─────────────────────────────────────────────────────────────────
    "dashboard":    '<rect x="3" y="3" width="8" height="9" rx="1.5"/>'
                    '<rect x="3" y="14" width="8" height="7" rx="1.5"/>'
                    '<rect x="13" y="3" width="8" height="6" rx="1.5"/>'
                    '<rect x="13" y="11" width="8" height="10" rx="1.5"/>',
    "users":        '<circle cx="9" cy="9" r="3"/>'
                    '<path d="M3 20c0-3 2.5-5 6-5s6 2 6 5"/>'
                    '<circle cx="17" cy="11" r="2.5"/>'
                    '<path d="M15 20c0-2 2-3.5 4-3.5"/>',
    "ai":           '<path d="M5 6h14v8H10l-4 3V14H5z"/>'
                    '<circle cx="9" cy="10" r="1.1" fill="{color}" stroke="none"/>'
                    '<circle cx="15" cy="10" r="1.1" fill="{color}" stroke="none"/>',
    "therapy":      '<path d="M12 3 L4 7 L12 11 L20 7 Z"/>'
                    '<path d="M4 12 L12 16 L20 12"/>'
                    '<path d="M4 17 L12 21 L20 17"/>',
    "report":       '<rect x="4" y="3" width="16" height="18" rx="2"/>'
                    '<path d="M8 8h8M8 12h8M8 16h5"/>',
    "bookmark":     '<path d="M6 3h12v18l-6-4-6 4V3z"/>',
    "download":     '<path d="M12 3v12m-5-5l5 5 5-5M4 19h16"/>',
    # ── Salud / bienestar ──────────────────────────────────────────────────
    "flame":        '<path d="M12 3c0 4-5 5-5 10a5 5 0 0 0 10 0c0-2-1-3-2-4 0 2-1 3-2 3 0-4 2-5-1-9z"/>',
    "heart":        '<path d="M12 21s-7-4.5-9-9c-2-4.5 1.5-8 5-7 1.5.5 3 1.5 4 3 1-1.5 2.5-2.5 4-3 3.5-1 7 2.5 5 7-2 4.5-9 9-9 9z"/>',
    "leaf":         '<path d="M12 4c-5 0-8 4-8 8 0 1 .3 2 .7 3 4 0 7-1 9-3s3-5 3-9c-1.3-.5-2.6-1-4.7-1z"/>'
                    '<path d="M6 16c2-2 4-4 8-6"/>',
    "medicine":     '<rect x="3" y="9" width="18" height="6" rx="3"/>'
                    '<path d="M12 9v6"/>',
    "water":        '<path d="M12 3c-3 5-6 7-6 11a6 6 0 0 0 12 0c0-4-3-6-6-11z"/>',
    "moon":         '<path d="M19 14a7 7 0 0 1-9-9 7 7 0 1 0 9 9z"/>',
    "sun":          '<circle cx="12" cy="12" r="4"/>'
                    '<path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.6 4.6L6 6M18 18l1.4 1.4M4.6 19.4L6 18M18 6l1.4-1.4"/>',
    "run":          '<circle cx="13" cy="4" r="2"/>'
                    '<path d="M10 22l3-7 3 7M7 12l4-2 4 2-2 3h-4l-2-3z"/>',
    # ── Acciones ──────────────────────────────────────────────────────────
    "check":        '<path d="M5 12l4 4 10-10"/>',
    "plus":         '<path d="M12 5v14M5 12h14"/>',
    "minus":        '<path d="M5 12h14"/>',
    "arrowRight":   '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "arrowLeft":    '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "chevronDown":  '<path d="M6 9l6 6 6-6"/>',
    "chevronRight": '<path d="M9 6l6 6-6 6"/>',
    # ── Player controls (filled) ──────────────────────────────────────────
    "play":         '<path d="M7 4l13 8-13 8z" fill="{color}" stroke="none"/>',
    "pause":        '<rect x="6" y="4" width="4" height="16" rx="1" fill="{color}" stroke="none"/>'
                    '<rect x="14" y="4" width="4" height="16" rx="1" fill="{color}" stroke="none"/>',
    "stop":         '<rect x="5" y="5" width="14" height="14" rx="2" fill="{color}" stroke="none"/>',
    "skip":         '<path d="M5 4v16l10-8z" fill="{color}" stroke="none"/>'
                    '<rect x="17" y="4" width="2.5" height="16" rx="1" fill="{color}" stroke="none"/>',
    # ── Charts / data ─────────────────────────────────────────────────────
    "chart":        '<path d="M3 20h18"/>'
                    '<path d="M5 16l4-5 4 3 6-8"/>'
                    '<circle cx="5" cy="16" r="1.5" fill="{color}" stroke="none"/>'
                    '<circle cx="9" cy="11" r="1.5" fill="{color}" stroke="none"/>'
                    '<circle cx="13" cy="14" r="1.5" fill="{color}" stroke="none"/>'
                    '<circle cx="19" cy="6" r="1.5" fill="{color}" stroke="none"/>',
    "barchart":     '<rect x="3" y="11" width="4" height="9" rx="1"/>'
                    '<rect x="10" y="6" width="4" height="14" rx="1"/>'
                    '<rect x="17" y="14" width="4" height="6" rx="1"/>',
    # ── Utility ───────────────────────────────────────────────────────────
    "search":       '<circle cx="10" cy="10" r="6"/>'
                    '<path d="M15 15l5 5"/>',
    "calendar":     '<rect x="3" y="5" width="18" height="16" rx="2"/>'
                    '<path d="M3 10h18M8 3v4M16 3v4"/>',
    "clock":        '<circle cx="12" cy="12" r="9"/>'
                    '<path d="M12 7v5l3 2"/>',
    "edit":         '<path d="M3 21h4l11-11-4-4L3 17v4z"/>'
                    '<path d="M14 6l4 4"/>',
    "book":         '<path d="M4 4h7a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H4z"/>'
                    '<path d="M20 4h-7a3 3 0 0 0-3 3v13a3 3 0 0 1 3-3h7z"/>',
    "note":         '<path d="M5 4h11l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>'
                    '<path d="M15 4v5h5M8 13h8M8 17h5"/>',
    "send":         '<path d="M3 11l18-8-8 18-3-7-7-3z"/>',
    "save":         '<path d="M5 4h11l4 4v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/>'
                    '<path d="M8 4v5h7V4M7 14h10v6H7z"/>',
    "dots":         '<circle cx="6" cy="12" r="1.7" fill="{color}" stroke="none"/>'
                    '<circle cx="12" cy="12" r="1.7" fill="{color}" stroke="none"/>'
                    '<circle cx="18" cy="12" r="1.7" fill="{color}" stroke="none"/>',
    "list":         '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "grid":         '<rect x="3" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="3" width="7" height="7" rx="1"/>'
                    '<rect x="3" y="14" width="7" height="7" rx="1"/>'
                    '<rect x="14" y="14" width="7" height="7" rx="1"/>',
    "bolt":         '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "gem":          '<path d="M6 3h12l3 6-9 12L3 9z"/>'
                    '<path d="M3 9h18M6 3l3 6L12 21M18 3l-3 6L12 21"/>',
    # ── Semantic / status ────────────────────────────────────────────────
    "warning":      '<path d="M12 3l10 18H2z"/>'
                    '<path d="M12 10v5M12 18.5h.01"/>',
    "info":         '<circle cx="12" cy="12" r="9"/>'
                    '<path d="M12 8v.01M11 12h1v5h1"/>',
    "close":        '<path d="M6 6l12 12M18 6L6 18"/>',
    "refresh":      '<path d="M3 12a9 9 0 0 1 15.5-6.5L21 8M21 4v4h-4"/>'
                    '<path d="M21 12a9 9 0 0 1-15.5 6.5L3 16M3 20v-4h4"/>',
    "target":       '<circle cx="12" cy="12" r="9"/>'
                    '<circle cx="12" cy="12" r="5"/>'
                    '<circle cx="12" cy="12" r="1.5" fill="{color}" stroke="none"/>',
    "trophy":       '<path d="M8 4h8v6a4 4 0 0 1-8 0V4z"/>'
                    '<path d="M16 6h2a2 2 0 0 1 2 2v1a3 3 0 0 1-3 3M8 6H6a2 2 0 0 0-2 2v1a3 3 0 0 0 3 3"/>'
                    '<path d="M10 14h4l-1 4h-2zM8 21h8"/>',
    "handshake":    '<path d="M7 12l-3-3 4-4 3 3M17 12l3-3-4-4-3 3"/>'
                    '<path d="M7 12l5 5 5-5"/>',
    "palette":      '<path d="M12 3a9 9 0 1 0 0 18c1 0 2-1 2-2 0-1-1-1-1-2s1-1 2-1h2a4 4 0 0 0 4-4 9 9 0 0 0-9-9z"/>'
                    '<circle cx="7" cy="10" r="1.2" fill="{color}" stroke="none"/>'
                    '<circle cx="12" cy="7" r="1.2" fill="{color}" stroke="none"/>'
                    '<circle cx="17" cy="10" r="1.2" fill="{color}" stroke="none"/>',
}


# ── Cache de pixmaps por (name, color, size) ─────────────────────────────────
_PIXMAP_CACHE: dict[tuple, QPixmap] = {}
_CACHE_LIMIT = 256


def _wrap_svg(body_template: str, color: str, sw: float) -> str:
    """Envuelve un body template en un <svg> v3 con stroke/color resueltos."""
    body = body_template.format(color=color, sw=sw, sw_07=sw * 0.7)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{sw:g}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


def nm_svg_pixmap(name: str, color: str = "#1a2236", size: int = 24,
                  stroke_width: float | None = None) -> QPixmap | None:
    """Renderiza un icono v3 a ``QPixmap``.

    Args:
        name:         Nombre del icono (ver ``available_icons()``).
        color:        Color hex del trazo y de los elementos rellenos.
        size:         Lado del pixmap cuadrado (px).
        stroke_width: Override. None = ``icon_stroke_width(size)`` del README.

    Returns:
        ``QPixmap`` o ``None`` si el nombre no existe (el caller decide
        fallback a QtAwesome).
    """
    body = ICON_BODIES.get(name)
    if body is None:
        return None
    sw = stroke_width if stroke_width is not None else icon_stroke_width(size)
    cache_key = (name, color.lower(), int(size), round(sw, 2))
    cached = _PIXMAP_CACHE.get(cache_key)
    if cached is not None:
        return cached
    svg_str = _wrap_svg(body, color, sw)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    if not renderer.isValid():
        _log.warning("SVG inválido para icono %r", name)
        return None
    pix = QPixmap(int(size), int(size))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    if len(_PIXMAP_CACHE) >= _CACHE_LIMIT:
        # Política trivial: limpiar todo cuando se llena. Suficiente para
        # uso típico (~60 iconos × ~3 colores × ~5 tamaños).
        _PIXMAP_CACHE.clear()
    _PIXMAP_CACHE[cache_key] = pix
    return pix


def has_icon(name: str) -> bool:
    """True si ``name`` está en el catálogo v3."""
    return name in ICON_BODIES


def available_icons() -> list[str]:
    """Lista ordenada de nombres disponibles."""
    return sorted(ICON_BODIES.keys())


def clear_cache():
    """Invalida el cache de pixmaps (útil al cambiar de tema)."""
    _PIXMAP_CACHE.clear()
    _MOOD_PIXMAP_CACHE.clear()


# ── NMMoodEmoji — 10 niveles, SVG line-style (handoff v3-emojis.jsx) ─────────

_MOOD_MOUTHS = {
    1:  "M 32 67 Q 50 56 68 67",
    2:  "M 36 65 Q 50 57 64 65",
    3:  "M 38 62 Q 50 58 62 62",
    4:  "M 40 60 L 60 60",
    5:  "M 40 60 L 60 60",
    6:  "M 40 58 Q 50 63 60 58",
    7:  "M 36 56 Q 50 65 64 56",
    8:  "M 34 54 Q 50 68 66 54",
    9:  "M 32 52 Q 50 71 68 52",
    10: "M 30 50 Q 50 73 70 50",
}

_MOOD_BROW_ANGLES = {1: 18, 2: 14, 3: 10, 9: -8, 10: -12}


def _mood_palette_entry(level: int) -> dict:
    """Acceso lazy a MOOD_PALETTE (evita import circular si theme no cargó)."""
    try:
        from shared.theme import MOOD_PALETTE
    except ImportError:
        from theme import MOOD_PALETTE  # type: ignore
    lv = max(1, min(10, int(level)))
    return MOOD_PALETTE[lv]


def _mood_emoji_svg(level: int, glow: bool, is_dark: bool) -> str:
    """Construye el string SVG del emoji para un nivel dado.

    Viewbox 0..100, escalable a cualquier tamaño en el render. El stroke
    base = 2.5 (calibrado para que QSvgRenderer lo escale uniformemente).
    """
    lv = max(1, min(10, int(level)))
    p = _mood_palette_entry(lv)
    stroke = 2.5
    eye_r = stroke * 0.85
    mouth_sw = stroke * 0.85
    brow_sw = stroke * 0.75
    color_to = p["to"]
    color_from = p["from"]
    color_glow = p["glow"]

    parts: list[str] = []

    # 1. Halo exterior (3 capas concéntricas — simula feGaussianBlur sin filtros)
    if glow:
        halo_alpha = 0.22 if is_dark else 0.15
        for i, r in enumerate((46, 49, 52)):
            a = halo_alpha * (1.0 - i * 0.30)
            parts.append(
                f'<circle cx="50" cy="50" r="{r}" fill="{color_glow}" '
                f'opacity="{a:.3f}"/>'
            )

    # 2. Círculo de cara (solo contorno)
    parts.append(
        f'<circle cx="50" cy="50" r="40" fill="none" stroke="{color_to}" '
        f'stroke-width="{stroke}"/>'
    )

    # 3. Ojos
    parts.append(f'<circle cx="38" cy="42" r="{eye_r:g}" fill="{color_to}"/>')
    parts.append(f'<circle cx="62" cy="42" r="{eye_r:g}" fill="{color_to}"/>')

    # 4. Boca
    parts.append(
        f'<path d="{_MOOD_MOUTHS[lv]}" stroke="{color_to}" '
        f'stroke-width="{mouth_sw:g}" fill="none" stroke-linecap="round"/>'
    )

    # 5. Cejas (solo extremos: 1-3, 9-10)
    if lv in _MOOD_BROW_ANGLES:
        ang = _MOOD_BROW_ANGLES[lv]
        y_off = 32 + ang * 0.3
        parts.append(
            f'<line x1="32" y1="32" x2="44" y2="{y_off:g}" '
            f'stroke="{color_to}" stroke-width="{brow_sw:g}" stroke-linecap="round"/>'
        )
        parts.append(
            f'<line x1="56" y1="{y_off:g}" x2="68" y2="32" '
            f'stroke="{color_to}" stroke-width="{brow_sw:g}" stroke-linecap="round"/>'
        )

    # 6. Lágrimas (1-2)
    if lv == 1:
        for d in (
            "M 28 50 Q 26 58 24 62 Q 22 58 24 52 Z",
            "M 72 50 Q 74 58 76 62 Q 78 58 76 52 Z",
        ):
            parts.append(
                f'<path d="{d}" fill="{color_from}" stroke="{color_to}" '
                f'stroke-width="{stroke * 0.55:g}" stroke-linejoin="round"/>'
            )
    elif lv == 2:
        parts.append(
            f'<path d="M 28 50 Q 26 56 25 59 Q 24 56 26 52 Z" '
            f'fill="{color_from}" stroke="{color_to}" '
            f'stroke-width="{stroke * 0.55:g}" stroke-linejoin="round"/>'
        )

    # 7. Blush (7-10): opacidad sube con el nivel
    if lv >= 7:
        blush_op = 0.5 + (lv - 7) * 0.10
        parts.append(
            f'<circle cx="28" cy="58" r="3.5" fill="{color_from}" '
            f'opacity="{blush_op:.2f}"/>'
        )
        parts.append(
            f'<circle cx="72" cy="58" r="3.5" fill="{color_from}" '
            f'opacity="{blush_op:.2f}"/>'
        )

    # 8. Sparkles (9-10): 2 estrellas de 4 puntas
    if lv >= 9:
        for d in (
            "M 18 22 L 19 25 L 22 26 L 19 27 L 18 30 L 17 27 L 14 26 L 17 25 Z",
            "M 78 18 L 79 21 L 82 22 L 79 23 L 78 26 L 77 23 L 74 22 L 77 21 Z",
        ):
            parts.append(f'<path d="{d}" fill="{color_glow}" opacity=".9"/>')

    # 9. Crown sparkle (10 — corona)
    if lv == 10:
        parts.append(
            f'<path d="M 50 10 L 51 14 L 55 15 L 51 16 L 50 20 L 49 16 L 45 15 L 49 14 Z" '
            f'fill="{color_glow}" opacity=".9"/>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'{"".join(parts)}</svg>'
    )


# Cache: (level, size, glow, is_dark) → QPixmap
_MOOD_PIXMAP_CACHE: dict[tuple, QPixmap] = {}


def nm_mood_pixmap(level: int, size: int = 64,
                   glow: bool = True,
                   is_dark: bool = False) -> QPixmap | None:
    """Renderiza un NMMoodEmoji a QPixmap.

    Args:
        level:   1-10 (clamp).
        size:    lado del pixmap cuadrado (px).
        glow:    Si True, halo radial detrás del emoji.
        is_dark: True ajusta la opacidad del halo (0.22 dark vs 0.15 light).
    """
    lv = max(1, min(10, int(level)))
    key = (lv, int(size), bool(glow), bool(is_dark))
    cached = _MOOD_PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached
    svg_str = _mood_emoji_svg(lv, glow=glow, is_dark=is_dark)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    if not renderer.isValid():
        _log.warning("SVG mood emoji inválido level=%d", lv)
        return None
    pix = QPixmap(int(size), int(size))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    if len(_MOOD_PIXMAP_CACHE) >= 80:
        _MOOD_PIXMAP_CACHE.clear()
    _MOOD_PIXMAP_CACHE[key] = pix
    return pix
