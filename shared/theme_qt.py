"""
shared/theme_qt.py
Bridge entre theme.py (tokens de diseño) y objetos Qt nativos.

Todas las funciones son puras y sin estado: reciben modo y devuelven objetos Qt.
No importan CustomTkinter. Compatibles con contexto frozen (PyInstaller).

Uso:
    from shared.theme_qt import qcolor, qfont, shadow_effect, linear_gradient, C, MODO

    btn.setStyleSheet(f"background: {C('accent')};")
    lbl.setFont(qfont('size_h2', bold=True))
"""

import os
import sys
import logging

import qtawesome as qta

_log = logging.getLogger(__name__)

from PyQt6.QtCore import QPointF, QRectF, Qt, QEasingCurve
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase,
    QLinearGradient, QRadialGradient, QConicalGradient,
    QPalette, QBrush, QPainter, QPixmap,
)
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QApplication

# ── Importación robusta de tokens ─────────────────────────────────────────────
try:
    from shared.theme import COLORS, TYPOGRAPHY, LAYOUT, GRADIENTS, CATEGORY_COLORS, get_gradient
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme import COLORS, TYPOGRAPHY, LAYOUT, GRADIENTS, CATEGORY_COLORS, get_gradient


FONT_SCALE = {
    "display": {"size": 28, "weight": 700, "line_height": 1.2},
    "h1":      {"size": 22, "weight": 600, "line_height": 1.3},
    "h2":      {"size": 18, "weight": 600, "line_height": 1.35},
    "h3":      {"size": 15, "weight": 500, "line_height": 1.4},
    "body":    {"size": 13, "weight": 400, "line_height": 1.6},
    "sm":      {"size": 12, "weight": 400, "line_height": 1.5},
    "caption": {"size": 11, "weight": 400, "line_height": 1.4},
}


SPACE = {
    "xs":  4,
    "sm":  8,
    "md":  16,
    "lg":  24,
    "xl":  32,
    "xxl": 48,
}


ANIM = {
    "fast":   150,
    "medium": 250,
    "slow":   400,
}
EASE_OUT = QEasingCurve.Type.OutCubic
EASE_IN  = QEasingCurve.Type.InCubic

EFFECTS = {
    "dark": {
        "card_glow_radius":    15,
        "card_glow_opacity":   0.35,
        "card_shadow_blur":    20,
        "button_glow_radius":  10,
        "noise_opacity":       0.04,
        "surface_overlay":     0.06,
    },
    "light": {
        "card_glow_radius":    6,
        "card_glow_opacity":   0.18,
        "card_shadow_blur":    8,
        "button_glow_radius":  4,
        "noise_opacity":       0.02,
        "surface_overlay":     0.03,
    },
}

FOCUS_RING_STYLE = """
    *:focus {{
        outline: 2px solid {accent};
        outline-offset: 2px;
    }}
    *:focus:not(:focus-visible) {{
        outline: none;
    }}
"""

# WCAG AA ratios (text sobre bg_primary, dark mode):
# text_primary (#f1f5f9) sobre bg_primary (#0f172a): ~15.5:1 OK
# accent (#6366f1) sobre bg_primary (#0f172a):        ~5.2:1  OK
# text_secondary (#94a3b8) sobre bg_primary (#0f172a): ~6.1:1 OK
# LIGHT MODE — verificar que los mismos pares cumplen AA

MODULE_ICONS = {
    "animo":         "fa5s.heart",
    "respiracion":   "fa5s.wind",
    "registro_tcc":  "fa5s.brain",
    "rutina":        "fa5s.list-check",
    "actividades":   "fa5s.running",
    "timer":         "fa5s.hourglass-half",
    "avisos":        "fa5s.bell",
}
HUB_ICONS = {
    "pacientes":     "fa5s.users",
    "ia_asistente":  "fa5s.robot",
    "exportar":      "fa5s.file-pdf",
    "configuracion": "fa5s.cog",
}

_ICON_FALLBACKS = {
    "fa5s.list-check": "fa5s.tasks",
}


def sp(key: str) -> int:
    return SPACE[key]


def fx(key: str, modo: str) -> float | int:
    bucket = "light" if "light" in norm_modo(modo) else "dark"
    return EFFECTS[bucket][key]


def focus_ring_stylesheet(modo: str) -> str:
    return FOCUS_RING_STYLE.format(accent=C("accent", modo))


def apply_chart_theme(modo: str):
    import matplotlib
    bg  = C("bg_primary", modo)
    fg  = C("text_primary", modo)
    acc = C("accent", modo)
    teal = "#14b8a6"
    matplotlib.rcParams.update({
        "figure.facecolor":  bg,
        "axes.facecolor":    bg,
        "axes.edgecolor":    C("border", modo),
        "axes.labelcolor":   fg,
        "xtick.color":       fg,
        "ytick.color":       fg,
        "text.color":        fg,
        "grid.color":        C("border", modo),
        "grid.alpha":        0.3,
        "lines.color":       acc,
        "patch.facecolor":   acc,
        "font.family":       "Segoe UI",
        "axes.spines.top":   False,
        "axes.spines.right": False,
    })


def nm_icon(key: str, color: str, size: int = 20):
    icon_name = MODULE_ICONS.get(key, HUB_ICONS.get(key, key))
    icon_name = _ICON_FALLBACKS.get(icon_name, icon_name)
    try:
        return qta.icon(icon_name, color=color)
    except Exception as e:
        fallback = _ICON_FALLBACKS.get(icon_name, "fa5s.circle")
        _log.warning(f"Icono QtAwesome no cargó ({icon_name}, {size}px): {e}")
        return qta.icon(fallback, color=color)


def _tm():
    from shared.components_qt import ThemeManager
    return ThemeManager.instance()


class ThemeAwareWidgetMixin:
    """Mixin para widgets que reaccionan al cambio de tema."""
    def _connect_theme(self):
        _tm().theme_changed.connect(self._apply_theme)
        self.destroyed.connect(self._disconnect_theme)

    def _disconnect_theme(self):
        try:
            _tm().theme_changed.disconnect(self._apply_theme)
        except (RuntimeError, TypeError):
            pass

    def _apply_theme(self, modo: str):
        raise NotImplementedError


def _load_premium_fonts():
    """Intenta cargar Inter Variable o Satoshi si estan disponibles."""
    font_candidates = [
        "Inter-Variable.ttf", "Inter.ttf",
        "Satoshi-Variable.ttf", "Satoshi-Regular.ttf",
    ]
    base_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts"),
        os.path.join(os.path.expanduser("~"), "NeuroMood", "assets", "fonts"),
    ]
    loaded = []
    for d in base_dirs:
        for f in font_candidates:
            path = os.path.join(d, f)
            if os.path.exists(path):
                fid = QFontDatabase.addApplicationFont(path)
                if fid >= 0:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    loaded.extend(families)
    return loaded[0] if loaded else None


_PREMIUM_FONT_FAMILY = None
_PREMIUM_FONT_ATTEMPTED = False
_noise_pixmap_cache: dict = {}


def _ensure_premium_font():
    global _PREMIUM_FONT_FAMILY, _PREMIUM_FONT_ATTEMPTED
    if _PREMIUM_FONT_ATTEMPTED or QApplication.instance() is None:
        return
    _PREMIUM_FONT_ATTEMPTED = True
    try:
        _PREMIUM_FONT_FAMILY = _load_premium_fonts()
    except Exception as e:
        _log.warning(f"Fuente premium no cargó: {e}")
        _PREMIUM_FONT_FAMILY = None


def _font_family() -> str:
    _ensure_premium_font()
    return _PREMIUM_FONT_FAMILY or "Segoe UI"


def _gradient_stops(modo: str = "dark_hybrid") -> list[tuple[str, float]]:
    raw = get_gradient(norm_modo(modo))
    if raw and isinstance(raw[0], (tuple, list)):
        return [(str(color_hex), float(pos)) for color_hex, pos in raw]
    if len(raw) >= 2:
        return [(str(raw[0]), 0.0), (str(raw[1]), 1.0)]
    return [("#6366f1", 0.0), ("#a855f7", 1.0)]


def gradient_colors(modo: str = "dark_hybrid") -> list[str]:
    """Devuelve solo los colores hex del gradiente activo."""
    return [color_hex for color_hex, _ in _gradient_stops(modo)]


def _as_hex(color_like) -> str:
    if isinstance(color_like, (tuple, list)) and color_like:
        return str(color_like[0])
    return str(color_like)


# ── Normalización de modo ─────────────────────────────────────────────────────

def norm_modo(modo: str) -> str:
    """'dark' → 'dark_hybrid', 'light' → 'light_hybrid'. Pasa los hybrid sin cambio."""
    if modo == "dark":
        return "dark_hybrid"
    if modo == "light":
        return "light_hybrid"
    return modo if modo in ("dark_hybrid", "light_hybrid") else "dark_hybrid"


# ── Acceso a tokens raw ───────────────────────────────────────────────────────

def C(key: str, modo: str = "dark_hybrid") -> str:
    """Devuelve el valor hex del token de color. Shorthand legible."""
    modo = norm_modo(modo)
    return COLORS.get(modo, COLORS["dark_hybrid"]).get(key, "#888888")


def colors(modo: str = "dark_hybrid") -> dict:
    """Devuelve el dict completo de colores del modo."""
    return COLORS.get(norm_modo(modo), COLORS["dark_hybrid"])


# ── QColor ────────────────────────────────────────────────────────────────────

def qcolor(key: str, modo: str = "dark_hybrid", alpha: int = 255) -> QColor:
    """
    Devuelve un QColor a partir de un token de color del tema.

    Args:
        key:   Token de COLORS (ej: 'accent', 'bg_surface', 'text_primary')
        modo:  'dark_hybrid' | 'light_hybrid' | 'dark' | 'light'
        alpha: Opacidad 0-255 (255 = opaco)

    Ejemplos:
        qcolor('accent')                     -> QColor("#6366f1")
        qcolor('bg_surface', 'light_hybrid') -> QColor("#ffffff")
        qcolor('accent', alpha=80)           -> QColor teal semitransparente
    """
    hex_val = C(key, modo)
    c = QColor(hex_val)
    if alpha != 255:
        c.setAlpha(alpha)
    return c


def qcolor_hex(hex_str: str, alpha: int = 255) -> QColor:
    """QColor directo desde hex string. Para CATEGORY_COLORS y COLORES_PUNTAJE."""
    c = QColor(hex_str)
    if alpha != 255:
        c.setAlpha(alpha)
    return c


# ── Interpolación de color ────────────────────────────────────────────────────

def interpolate_color(c1: str, c2: str, t: float) -> str:
    """Interpolación lineal entre dos hex. t=0 → c1, t=1 → c2. Pura, sin estado."""
    c1 = _as_hex(c1)
    c2 = _as_hex(c2)
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_color(color_hex: str, bg_hex: str, alpha: float) -> str:
    """Mezcla color sobre bg con opacidad alpha (0.0-1.0). Para simular rgba."""
    return interpolate_color(bg_hex, color_hex, alpha)


# ── QFont ─────────────────────────────────────────────────────────────────────

def qfont(size_key: str = "size_body", bold: bool = False,
          family: str = None) -> QFont:
    """
    Devuelve un QFont configurado con los tokens de tipografía del tema.

    Args:
        size_key: Key de TYPOGRAPHY (ej: 'size_h1', 'size_body', 'size_caption')
                  o un int directo de tamaño de punto.
        bold:     Si True, peso QFont.Weight.Bold, si no Normal.
        family:   Override de familia; si None usa TYPOGRAPHY['font_family'].

    Ejemplos:
        qfont('size_h2', bold=True)
        qfont('size_body')
        qfont(size_key=28, bold=True)  # tamaño directo
    """
    fam = family or _font_family()
    if isinstance(size_key, int):
        pt = size_key
    else:
        pt = TYPOGRAPHY.get(size_key, TYPOGRAPHY.get("size_body", 14))

    f = QFont(fam, pt)
    f.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    if size_key in ("size_h1", "size_h2"):
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.5)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def nm_font(level: str, bold_override=False) -> QFont:
    """Devuelve un QFont segun la escala tipografica NeuroMood."""
    spec = FONT_SCALE.get(level, FONT_SCALE["body"])
    weight = QFont.Weight.Bold if bold_override else QFont.Weight(spec["weight"])
    f = QFont(_font_family(), spec["size"])
    f.setWeight(weight)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def qfont_emoji(size_key: str = "size_emoji") -> QFont:
    """Font específico para emojis — usa Segoe UI Emoji en Windows."""
    pt = TYPOGRAPHY.get(size_key, 64)
    families = ["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji",
                TYPOGRAPHY.get("font_family", "Segoe UI")]
    db = QFontDatabase()
    chosen = TYPOGRAPHY.get("font_family", "Segoe UI")
    for fam in families:
        if fam in db.families():
            chosen = fam
            break
    return QFont(chosen, pt)


# ── QGraphicsDropShadowEffect ─────────────────────────────────────────────────

def shadow_effect(tipo: str = "card", modo: str = "dark_hybrid",
                  parent=None) -> QGraphicsDropShadowEffect:
    """
    Devuelve un QGraphicsDropShadowEffect calibrado con los valores de SHADOWS.

    Args:
        tipo:   'card' | 'card_hover' | 'glow_teal' | 'button'
        modo:   'dark_hybrid' | 'light_hybrid'
        parent: QObject padre (necesario si el efecto no se aplica inmediatamente)

    Sombras definidas:
        dark card:       blur=28, offset=(0,8),  alpha=115  (~0.45 * 255)
        dark card_hover: blur=42, offset=(0,14), alpha=140
        dark glow_teal:  blur=24, offset=(0,0),  color=teal alpha=77
        light card:      blur=16, offset=(0,4),  alpha=25
        light card_hover:blur=24, offset=(0,8),  alpha=40
        button:          blur=12, offset=(0,4),  alpha=60 (modo-independiente casi)
    """
    modo = norm_modo(modo)
    is_dark = "dark" in modo

    shadow = QGraphicsDropShadowEffect(parent)

    if tipo == "card":
        shadow.setBlurRadius(fx("card_shadow_blur", modo))
        shadow.setOffset(0, 8)
        col = QColor(0, 0, 0, 115 if is_dark else 25)
    elif tipo == "card_hover":
        shadow.setBlurRadius(fx("card_shadow_blur", modo) + (14 if is_dark else 8))
        shadow.setOffset(0, 14)
        col = QColor(0, 0, 0, 140 if is_dark else 40)
    elif tipo == "glow_teal":
        accent = C("accent", modo)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 0)
        col = QColor(accent)
        col.setAlpha(77 if is_dark else 50)
    elif tipo == "glow_violet":
        violet = C("violet", modo)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        col = QColor(violet)
        col.setAlpha(60 if is_dark else 40)
    elif tipo == "button":
        shadow.setBlurRadius(fx("button_glow_radius", modo) + 2)
        shadow.setOffset(0, 4)
        col = QColor(0, 0, 0, 60)
    elif tipo == "glass":
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 20)
        col = QColor(C("accent", modo))
        col.setAlpha(20)
    else:
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        col = QColor(0, 0, 0, 30)

    shadow.setColor(col)
    return shadow


# ── QLinearGradient ───────────────────────────────────────────────────────────

def linear_gradient(rect: QRectF, modo: str = "dark_hybrid",
                    angle: float = 135,
                    color_a: str = None, color_b: str = None,
                    alpha_a: int = 255, alpha_b: int = 255) -> QLinearGradient:
    """
    Gradiente lineal teal → violet (o colores custom) sobre un rect.

    Args:
        rect:    QRectF que define el área del widget
        modo:    Modo del tema (para obtener colores del gradiente)
        angle:   Ángulo en grados (0=horizontal derecha, 90=vertical abajo, 135=diagonal)
        color_a: Override hex del color inicial (None = teal del tema)
        color_b: Override hex del color final (None = violet del tema)
        alpha_a: Alpha del color inicial (0-255)
        alpha_b: Alpha del color final (0-255)

    Ejemplo:
        grad = linear_gradient(self.rect(), modo)
        painter.fillRect(self.rect(), grad)
    """
    modo = norm_modo(modo)
    stops = _gradient_stops(modo)

    # Calcular puntos de inicio/fin a partir del ángulo
    import math
    rad = math.radians(angle)
    cx, cy = rect.center().x(), rect.center().y()
    hw = rect.width() / 2
    hh = rect.height() / 2
    dx = math.cos(rad) * hw
    dy = math.sin(rad) * hh

    grad = QLinearGradient(
        QPointF(cx - dx, cy - dy),
        QPointF(cx + dx, cy + dy),
    )
    if color_a or color_b:
        colors_only = gradient_colors(modo)
        ca = QColor(color_a or colors_only[0])
        cb = QColor(color_b or colors_only[-1])
        ca.setAlpha(alpha_a)
        cb.setAlpha(alpha_b)
        grad.setColorAt(0.0, ca)
        grad.setColorAt(1.0, cb)
    else:
        for color_hex, pos in stops:
            c = QColor(color_hex)
            if pos <= 0:
                c.setAlpha(alpha_a)
            elif pos >= 1:
                c.setAlpha(alpha_b)
            grad.setColorAt(pos, c)
    return grad


def rich_gradient(rect: QRectF, modo: str = "dark_hybrid",
                  angle: float = 135) -> QLinearGradient:
    """
    Gradiente premium de 3 paradas (indigo -> teal -> violet).
    Usa la estructura GRADIENTS nueva de theme.py.
    """
    modo = norm_modo(modo)
    stops = _gradient_stops(modo)

    import math
    rad = math.radians(angle)
    w, h = rect.width(), rect.height()
    cx, cy = rect.center().x(), rect.center().y()
    half = max(w, h) / 2
    x1 = cx - math.cos(rad) * half
    y1 = cy - math.sin(rad) * half
    x2 = cx + math.cos(rad) * half
    y2 = cy + math.sin(rad) * half

    grad = QLinearGradient(x1, y1, x2, y2)
    for color_hex, pos in stops:
        grad.setColorAt(pos, QColor(color_hex))
    return grad


def linear_gradient_vertical(rect: QRectF, color_top: QColor,
                              color_bottom: QColor) -> QLinearGradient:
    """Gradiente vertical simple top → bottom. Para área bajo curva en gráficos."""
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    grad.setColorAt(0.0, color_top)
    grad.setColorAt(1.0, color_bottom)
    return grad


# ── QRadialGradient (glow) ────────────────────────────────────────────────────

def noise_overlay(painter: QPainter, rect: QRectF,
                  opacity: float = 0.035, modo: str = "dark_hybrid"):
    """
    Pinta un patron de ruido fino sobre rect para dar sensacion de material.
    El QPixmap de ruido se genera una sola vez y se cachea.
    """
    global _noise_pixmap_cache
    size = 64
    key = f"noise_{size}"
    if key not in _noise_pixmap_cache:
        import random
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        noise_p = QPainter(px)
        rng = random.Random(42)
        for _ in range(size * size // 3):
            x = rng.randint(0, size - 1)
            y = rng.randint(0, size - 1)
            v = rng.randint(180, 255)
            noise_p.setPen(QColor(v, v, v, rng.randint(10, 40)))
            noise_p.drawPoint(x, y)
        noise_p.end()
        _noise_pixmap_cache[key] = px

    old_opacity = painter.opacity()
    painter.setOpacity(opacity)
    px = _noise_pixmap_cache[key]
    x, y = int(rect.x()), int(rect.y())
    w, h = int(rect.width()), int(rect.height())
    for tx in range(x, x + w, size):
        for ty in range(y, y + h, size):
            painter.drawPixmap(tx, ty, px)
    painter.setOpacity(old_opacity)


def radial_glow(center: QPointF, radius: float,
                color_hex: str, alpha: int = 80) -> QRadialGradient:
    """
    Gradiente radial para simular glow/resplandor alrededor de un elemento.

    Args:
        center:    Centro del glow (QPointF)
        radius:    Radio del glow en píxeles
        color_hex: Color hex del glow (ej: '#6366f1')
        alpha:     Intensidad máxima en el centro (0-255). Decae a 0 en el borde.

    Uso típico en paintEvent:
        glow = radial_glow(QPointF(cx, cy), 60, C('accent'), alpha=100)
        painter.fillRect(glow_rect, glow)
    """
    grad = QRadialGradient(center, radius)
    inner = QColor(color_hex)
    inner.setAlpha(alpha)
    outer = QColor(color_hex)
    outer.setAlpha(0)
    grad.setColorAt(0.0, inner)
    grad.setColorAt(1.0, outer)
    return grad


def radial_glow_double(center: QPointF, radius: float,
                       color_hex: str) -> QRadialGradient:
    """Glow doble: centro más brillante, decaimiento suave. Para arcos de respiración."""
    grad = QRadialGradient(center, radius)
    core = QColor(color_hex); core.setAlpha(120)
    mid  = QColor(color_hex); mid.setAlpha(60)
    edge = QColor(color_hex); edge.setAlpha(0)
    grad.setColorAt(0.0,  core)
    grad.setColorAt(0.4,  mid)
    grad.setColorAt(1.0,  edge)
    return grad


# ── QConicalGradient (arco) ───────────────────────────────────────────────────

def conical_arc_gradient(center: QPointF, start_angle: float,
                         modo: str = "dark_hybrid") -> QConicalGradient:
    """
    Gradiente cónico teal → violet para arcos circulares (respiración, timer).

    Args:
        center:      Centro del arco (QPointF)
        start_angle: Ángulo de inicio en grados (0 = este, Qt usa sentido horario)
        modo:        Modo del tema

    Nota: Qt usa ángulos en sentido antihorario para QConicalGradient.
    """
    modo = norm_modo(modo)
    grad = QConicalGradient(center, start_angle)
    for color_hex, pos in _gradient_stops(modo):
        grad.setColorAt(pos, QColor(color_hex))
    return grad


# ── Stylesheet helpers ────────────────────────────────────────────────────────

def stylesheet_base(modo: str = "dark_hybrid") -> str:
    """
    Stylesheet global QApplication mínimo: fondo, texto, scrollbars, tooltips.
    Se aplica una vez en QApplication antes de construir la UI.
    """
    modo = norm_modo(modo)
    c = colors(modo)
    sc_handle = C("teal", modo)
    sc_handle_end = C("accent", modo)
    sc_hover = C("accent", modo)
    sc_hover_end = C("violet", modo)
    return f"""
    QWidget {{
        background-color: {c['bg_primary']};
        color: {c['text_primary']};
        font-family: "{_font_family()}";
        font-size: {TYPOGRAPHY['size_body']}pt;
    }}
    QScrollBar:vertical {{
        background: rgba(255, 255, 255, 0.05);
        width: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {sc_handle}, stop:1 {sc_handle_end}
        );
        border: 1px solid {sc_handle};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {sc_hover}, stop:1 {sc_hover_end}
        );
        border: 1px solid {sc_hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: rgba(255, 255, 255, 0.05);
        height: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {sc_handle}, stop:1 {sc_handle_end}
        );
        border: 1px solid {sc_handle};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {sc_hover}, stop:1 {sc_hover_end}
        );
        border: 1px solid {sc_hover};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QToolTip {{
        background-color: {c['bg_elevated']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: 6px;
        padding: 4px 8px;
        font-size: {TYPOGRAPHY['size_small']}pt;
    }}
    """


def stylesheet_scrollarea(modo: str = "dark_hybrid") -> str:
    """Stylesheet scrollbars con tokens del tema."""
    sc_handle = C("teal", modo)
    sc_handle_end = C("accent", modo)
    sc_hover = C("accent", modo)
    sc_hover_end = C("violet", modo)
    return f"""
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: rgba(255, 255, 255, 0.05);
        width: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {sc_handle}, stop:1 {sc_handle_end}
        );
        border: 1px solid {sc_handle};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {sc_hover}, stop:1 {sc_hover_end}
        );
        border: 1px solid {sc_hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: rgba(255, 255, 255, 0.05);
        height: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {sc_handle}, stop:1 {sc_handle_end}
        );
        border: 1px solid {sc_handle};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {sc_hover}, stop:1 {sc_hover_end}
        );
        border: 1px solid {sc_hover};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """


def stylesheet_slider(modo: str = "dark_hybrid") -> str:
    """QSlider horizontal con groove gradiente y handle blanco con sombra."""
    modo = norm_modo(modo)
    c = colors(modo)
    grad = _gradient_stops(modo)
    grad_css = ", ".join(
        f"stop:{pos:g} {color_hex}" for color_hex, pos in grad
    )
    first_color = grad[0][0]
    return f"""
    QSlider::groove:horizontal {{
        height: 6px;
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            {grad_css}
        );
        border-radius: 3px;
        margin: 0 8px;
    }}
    QSlider::handle:horizontal {{
        background: white;
        border: 2px solid {c['bg_elevated']};
        width: 20px;
        height: 20px;
        margin: -7px -4px;
        border-radius: 10px;
    }}
    QSlider::handle:horizontal:hover {{
        border-color: {first_color};
    }}
    QSlider::sub-page:horizontal {{
        background: transparent;
    }}
    QSlider::add-page:horizontal {{
        background: {c['progress_track']};
        border-radius: 3px;
        height: 6px;
        margin: 0 8px;
    }}
    """


def stylesheet_tabwidget(modo: str = "dark_hybrid") -> str:
    """QTabWidget con tabs como pills (no rectangulares)."""
    modo = norm_modo(modo)
    c = colors(modo)
    r = LAYOUT["radius_pill"]
    return f"""
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c['text_secondary']};
        padding: 6px 18px;
        margin: 2px 3px;
        border-radius: {LAYOUT['radius_button']}px;
        font-size: {TYPOGRAPHY['size_small']}pt;
        font-weight: normal;
    }}
    QTabBar::tab:selected {{
        background: {c['bg_elevated']};
        color: {c['text_primary']};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background: {c.get('border_card', c['border'])};
        color: {c['text_primary']};
    }}
    QTabBar {{
        background: transparent;
    }}
    """


def stylesheet_lineedit(modo: str = "dark_hybrid") -> str:
    """QLineEdit con colores del tema. Los focus borders se manejan en NMInput."""
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QLineEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: {LAYOUT['radius_input']}px;
        padding: 6px 12px;
        font-size: {TYPOGRAPHY['size_body']}pt;
        selection-background-color: {c['accent']};
        selection-color: {c['text_on_accent']};
    }}
    QLineEdit::placeholder {{
        color: {c['text_tertiary']};
    }}
    QLineEdit:focus {{
        border-color: {c['border_focus']};
    }}
    """


def stylesheet_textedit(modo: str = "dark_hybrid") -> str:
    """QTextEdit y QPlainTextEdit."""
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QTextEdit, QPlainTextEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: {LAYOUT['radius_input']}px;
        padding: 8px;
        font-size: {TYPOGRAPHY['size_body']}pt;
        selection-background-color: {c['accent']};
        selection-color: {c['text_on_accent']};
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c['border_focus']};
    }}
    """


def stylesheet_combobox(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QComboBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: {LAYOUT['radius_input']}px;
        padding: 6px 12px;
        font-size: {TYPOGRAPHY['size_body']}pt;
        min-height: 36px;
    }}
    QComboBox:focus {{
        border-color: {c['border_focus']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c['text_secondary']};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_surface']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: {LAYOUT['radius_card']}px;
        selection-background-color: {c['bg_elevated']};
        padding: 4px;
        outline: none;
    }}
    """


def stylesheet_timeedit(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QTimeEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c.get('border_card', c['border'])};
        border-radius: {LAYOUT['radius_input']}px;
        padding: 6px 12px;
        font-size: {TYPOGRAPHY['size_body']}pt;
        min-height: 36px;
    }}
    QTimeEdit:focus {{
        border-color: {c['border_focus']};
    }}
    QTimeEdit::up-button, QTimeEdit::down-button {{
        width: 0;
        border: none;
    }}
    """


# ── QPalette ─────────────────────────────────────────────────────────────────

def app_palette(modo: str = "dark_hybrid") -> QPalette:
    """
    QPalette global para QApplication. Establece colores base que QStyle
    usa cuando no hay stylesheet específica.
    """
    modo = norm_modo(modo)
    c = colors(modo)
    p = QPalette()

    bg   = QColor(c["bg_primary"])
    surf = QColor(c["bg_surface"])
    elev = QColor(c["bg_elevated"])
    tp   = QColor(c["text_primary"])
    ts   = QColor(c["text_secondary"])
    acc  = QColor(c["accent"])
    brdr = QColor(c.get("border_card", c["border"]))
    dis  = QColor(c["text_tertiary"])

    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        p.setColor(group, QPalette.ColorRole.Window,          bg)
        p.setColor(group, QPalette.ColorRole.WindowText,      tp)
        p.setColor(group, QPalette.ColorRole.Base,            surf)
        p.setColor(group, QPalette.ColorRole.AlternateBase,   elev)
        p.setColor(group, QPalette.ColorRole.Text,            tp)
        p.setColor(group, QPalette.ColorRole.BrightText,      tp)
        p.setColor(group, QPalette.ColorRole.ButtonText,      tp)
        p.setColor(group, QPalette.ColorRole.Button,          elev)
        p.setColor(group, QPalette.ColorRole.Highlight,       acc)
        p.setColor(group, QPalette.ColorRole.HighlightedText, QColor(c["text_on_accent"]))
        p.setColor(group, QPalette.ColorRole.PlaceholderText, QColor(c["text_tertiary"]))
        p.setColor(group, QPalette.ColorRole.Mid,             brdr)
        p.setColor(group, QPalette.ColorRole.Dark,            bg)
        p.setColor(group, QPalette.ColorRole.Shadow,          QColor(0, 0, 0, 80))

    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, dis)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       dis)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, dis)

    return p


# ── Utilidades de recurso (preservadas de components.py) ─────────────────────

def obtener_ruta_recurso(nombre_archivo: str) -> str:
    """Ruta a un recurso: usa sys._MEIPASS en frozen, raíz del proyecto en dev."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre_archivo)


def obtener_icono_solido() -> str:
    return obtener_ruta_recurso("NM_icon.ico")


# ── Caption bar DWM (Win32) reescrita para PyQt6 ─────────────────────────────

def _es_windows_11() -> bool:
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:
        return False


def _aplicar_acento_win10(hwnd: int, bg_hex: str):
    """Windows 10: colorea barra de título vía SetWindowCompositionAttribute."""
    try:
        import ctypes

        r = int(bg_hex[1:3], 16)
        g = int(bg_hex[3:5], 16)
        b = int(bg_hex[5:7], 16)
        color_abgr = ctypes.c_uint((0xFF << 24) | (b << 16) | (g << 8) | r)

        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState",   ctypes.c_int),
                ("AccentFlags",   ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId",   ctypes.c_int),
            ]

        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute",  ctypes.c_int),
                ("pData",      ctypes.c_void_p),
                ("ulDataSize", ctypes.c_ulong),
            ]

        accent = ACCENT_POLICY(AccentState=1, AccentFlags=2,
                               GradientColor=int(color_abgr.value))
        data = WINCOMPATTRDATA(
            Attribute=19,
            pData=ctypes.cast(ctypes.addressof(accent), ctypes.c_void_p),
            ulDataSize=ctypes.sizeof(accent),
        )
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        _log.exception("Win10 accent color failed")


def aplicar_captionbar_qt(window, modo: str):
    """
    Aplica caption bar coloreada en PyQt6.
    Usa window.winId() en vez de window.winfo_id() (tkinter).
    Compatible con QMainWindow y QWidget.
    """
    _ensure_premium_font()
    modo = norm_modo(modo)
    bg = C("bg_secondary", modo)
    try:
        import ctypes
        hwnd = int(window.winId())

        dark_val = ctypes.c_int(1 if "dark" in modo else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_val), 4)
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark_val), 4)
        except Exception:
            pass

        r2, g2, b2 = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        color = ctypes.c_uint(r2 | (g2 << 8) | (b2 << 16))
        if _es_windows_11():
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        else:
            _aplicar_acento_win10(hwnd, bg)

        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
        if not _es_windows_11():
            ctypes.windll.user32.UpdateWindow(hwnd)
    except Exception:
        _log.exception("Caption bar setup failed")


def recolorear_logo_light(img):
    """Invierte píxeles blancos del logo a oscuro para el tema claro (PIL Image)."""
    img = img.convert("RGBA")
    data = img.getdata()
    nueva = []
    for r, g, b, a in data:
        if r > 200 and g > 200 and b > 200 and a > 0:
            nueva.append((13, 17, 23, a))   # bg_primary dark
        else:
            nueva.append((r, g, b, a))
    img.putdata(nueva)
    return img


# ── Constantes de layout como Python ints (conveniencia) ─────────────────────

RADIUS_CARD   = LAYOUT["radius_card"]
RADIUS_BUTTON = LAYOUT["radius_button"]
RADIUS_INPUT  = LAYOUT["radius_input"]
RADIUS_PILL   = LAYOUT["radius_pill"]
RADIUS_BADGE  = LAYOUT["radius_badge"]
RADIUS_SMALL  = LAYOUT["radius_small"]
CHECKBOX_SIZE = LAYOUT["checkbox_size"]
PAD_CONTAINER = LAYOUT["padding_container"]
PAD_CARD      = LAYOUT["padding_card"]
GAP_CARDS     = LAYOUT["gap_cards"]
GAP_ELEMENTS  = LAYOUT["gap_elements"]
HEADER_H      = LAYOUT["header_height"]


def qcolor_to_rgba_css(color: "QColor") -> str:
    """Convierte un QColor a string rgba() para usar en stylesheets Qt."""
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"


def label_style(modo: str, key: str = "text_primary") -> str:
    """Shortcut para QLabel: color del tema + fondo transparente.

    Uso: lbl.setStyleSheet(label_style(modo, 'text_secondary'))
    Equivale a: f'color: {C(key, modo)}; background: transparent;'
    """
    return f"color: {C(key, modo)}; background: transparent;"


# ── SessionColor — vibe aleatorio de sesión (aura + glow) ─────────────────────

import random as _random

_SESSION_COLORS = {
    "dark":  {"cyan": "#00f2fe",   "violet": "#7367f0"},
    "light": {"cyan": "#89f7fe",   "violet": "#e0c3fc"},
}


class SessionColor:
    """Color de sesión aleatorio (cyan o violeta) para aura, glow y acentos."""

    _inst = None

    @classmethod
    def instance(cls) -> "SessionColor":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        self._variant = _random.choice(["cyan", "violet"])

    @property
    def variant(self) -> str:
        return self._variant

    def hex_for(self, modo: str) -> str:
        """Hex del color de sesión para el modo dado."""
        m = "dark" if "dark" in modo else "light"
        return _SESSION_COLORS[m][self._variant]

    def qcolor(self, modo: str, alpha: int = 255) -> "QColor":
        """QColor del color de sesión con opacidad."""
        c = QColor(self.hex_for(modo))
        if alpha != 255:
            c.setAlpha(alpha)
        return c

    def glow_qcolor(self, modo: str) -> "QColor":
        """Color de glow para sombras (alpha 180 en dark, 120 en light)."""
        alpha = 180 if "dark" in modo else 120
        return self.qcolor(modo, alpha)

    def aura_qcolor(self, modo: str) -> "QColor":
        """Color de aura para fondo radial (alpha 20 en dark, 30 en light)."""
        alpha = 20 if "dark" in modo else 30
        return self.qcolor(modo, alpha)

    def accent_hex(self, modo: str) -> str:
        """Color de acento derivado de la sesión (para bordes, iconos)."""
        return self.hex_for(modo)
