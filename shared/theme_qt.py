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

# qtawesome se importa de forma perezosa dentro de ``nm_icon`` (ver allí): su
# import eager cuesta ~200 ms en cada arranque y hoy solo se usa como fallback
# compatibility cuando el catálogo SVG v3 no tiene el icono (caso casi inexistente).

_log = logging.getLogger(__name__)

from PyQt6.QtCore import QPointF, QRectF, Qt, QEasingCurve
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QRadialGradient,
    QConicalGradient,
    QPalette,
    QBrush,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

# ── Importación robusta de tokens ─────────────────────────────────────────────
try:
    from shared.theme import (
        COLORS,
        TYPOGRAPHY,
        LAYOUT,
        GRADIENTS,
        CATEGORY_COLORS,
        get_gradient,
        V3_LIGHT,
        V3_DARK,
        V3_SPACE,
        V3_RADIUS,
        V3_SHADOWS,
        V3_LIFT,
        V3_GRADIENTS,
        VISUAL_DENSITIES,
        MOOD_PALETTE,
        get_v3_palette,
        get_mood,
        v3_mode,
        icon_stroke_width,
    )
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme import (
        COLORS,
        TYPOGRAPHY,
        LAYOUT,
        get_gradient,
        V3_LIGHT,
        V3_SPACE,
        V3_RADIUS,
        V3_SHADOWS,
        V3_LIFT,
        V3_GRADIENTS,
        VISUAL_DENSITIES,
        get_v3_palette,
        get_mood,
        v3_mode,
    )


# Escala tipográfica compact desktop — visual compact (display=22, h1=17, body=13)
FONT_SCALE = {
    # Display (Serif) — títulos principales, números de bienestar
    "display_xl": {"size": 40, "weight": 700, "line_height": 1.2, "serif": True},  # displayXL (runtime, era 56)
    "display_l": {"size": 30, "weight": 700, "line_height": 1.2, "serif": True},  # displayL (runtime, era 38)
    "display_m": {"size": 26, "weight": 500, "line_height": 1.2, "serif": True},  # displayM
    # Heading (Sans) — UI headers
    "heading_l": {"size": 20, "weight": 600, "line_height": 1.3, "serif": False},  # headingL
    "heading_m": {"size": 16, "weight": 600, "line_height": 1.35, "serif": False},  # headingM
    "h1": {"size": 20, "weight": 600, "line_height": 1.3, "serif": False},  # alias headingL
    "h2": {"size": 16, "weight": 600, "line_height": 1.35, "serif": False},  # alias headingM
    "h3": {"size": 14, "weight": 500, "line_height": 1.4, "serif": False},  # alias body
    # Body (Sans)
    "body": {"size": 14, "weight": 400, "line_height": 1.6, "serif": False},
    "sm": {"size": 12, "weight": 400, "line_height": 1.5, "serif": False},
    "caption": {"size": 12, "weight": 400, "line_height": 1.4, "serif": False},
    "eyebrow": {"size": 11, "weight": 700, "line_height": 1.4, "serif": False},
    "mono": {"size": 12, "weight": 500, "line_height": 1.4, "mono": True},
}


def _resolve_default_family() -> str:
    """Devuelve la PRIMERA familia disponible del fallback chain v3.

    `TYPOGRAPHY['font_family']` ahora es un string CSS-style ("Plus Jakarta Sans,
    DM Sans, system-ui, sans-serif"). Qt no resuelve fallback chains: tomamos la
    primera familia del chain explícito, o splitteamos el string como fallback.
    """
    chain = TYPOGRAPHY.get("font_family_fallback_chain")
    if isinstance(chain, (list, tuple)) and chain:
        return chain[0]
    raw = TYPOGRAPHY.get("font_family", "DM Sans")
    return raw.split(",")[0].strip().strip("'\"")


_DEFAULT_FONT_FAMILY = _resolve_default_family()


# SPACE es alias de V3_SPACE (theme.py) — fuente runtime única. La escala v3
# UI (xs:4 / sm:8 / md:12 / lg:16 / xl:20 / xxl:24 / xxxl:32) corre por aquí para
# todo consumidor que importe SPACE desde este módulo.
SPACE = V3_SPACE


ANIM = {
    "fast":   140,   # micro-feedback: press, flash, toggle
    "medium": 240,   # transiciones: checkmark, state change
    "slow":   480,   # expansión completa: ripple, slide
    "ring":   500,   # ring/wave pulse de una sola pasada
    "pulse": 2000,   # loop de pulso ambiental (FocusArc, breathing)
    "blink":  550,   # intervalo de parpadeo de urgencia
}
EASE_OUT = QEasingCurve.Type.OutCubic
EASE_IN = QEasingCurve.Type.InCubic

EFFECTS = {
    "dark": {
        "card_glow_radius": 15,
        "card_glow_opacity": 0.35,
        "card_shadow_blur": 20,
        "button_glow_radius": 10,
        "noise_opacity": 0.04,
        "surface_overlay": 0.06,
    },
    "light": {
        "card_glow_radius": 6,
        "card_glow_opacity": 0.18,
        "card_shadow_blur": 8,
        "button_glow_radius": 4,
        "noise_opacity": 0.02,
        "surface_overlay": 0.03,
    },
}

# Solo CAMPOS DE ENTRADA llevan anillo de foco (comunica dónde se escribe).
# Botones y listas NO: el QPushButton:focus anterior pintaba un borde accent
# en cualquier botón clickeado — en headers full-width (p.ej. "REGISTROS
# PREVIOS" del TCC) quedaba un resplandor verde gigante persistente (informe
# user feedback). El outline:none elimina además los recuadros punteados de
# foco del estilo nativo en botones/tabs/textos seleccionables.
FOCUS_RING_STYLE = """
    * {{
        outline: none;
    }}
    QLineEdit:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDateEdit:focus,
    QTimeEdit:focus {{
        border: 1px solid {accent};
    }}
"""

# WCAG AA ratios (texto sobre canvas, tokens runtime):
# dark:  tinta #ECECFB sobre canvas #07091A — contraste alto, OK
# dark:  lavanda #A99CFF sobre canvas #07091A — AA OK para texto grande/CTA
# light: tinta #1C2218 sobre canvas #F4EFE5 — contraste alto, OK

MODULE_ICONS = {
    "animo": "fa5s.heart",
    "respiracion": "fa5s.wind",
    "registro_tcc": "fa5s.brain",
    "rutina": "fa5s.list-check",
    "actividades": "fa5s.running",
    "timer": "fa5s.hourglass-half",
    "avisos": "fa5s.bell",
}
HUB_ICONS = {
    "pacientes": "fa5s.users",
    "ia_asistente": "fa5s.robot",
    "exportar": "fa5s.file-pdf",
    "configuracion": "fa5s.cog",
}

_ICON_FALLBACKS = {
    "fa5s.list-check": "fa5s.tasks",
}

# v3 — mapeo de claves compatibility (módulos/hub) → nombres SVG del catálogo v3
_MODULE_KEY_V3 = {
    "animo": "mood",
    "respiracion": "breath",
    "registro_tcc": "brain",
    "rutina": "routine",
    "actividades": "run",
    "timer": "timer",
    "avisos": "bell",
}
_HUB_KEY_V3 = {
    "pacientes": "users",
    "ia_asistente": "ai",
    "exportar": "download",
    "configuracion": "cog",
}


def sp(key: str) -> int:
    return V3_SP[key]


def fx(key: str, modo: str) -> float | int:
    bucket = "light" if "light" in norm_modo(modo) else "dark"
    return EFFECTS[bucket][key]


def focus_ring_stylesheet(modo: str) -> str:
    return FOCUS_RING_STYLE.format(accent=C("accent", modo))


def apply_chart_theme(modo: str):
    import matplotlib

    bg = C("bg_primary", modo)
    fg = C("text_primary", modo)
    acc = C("accent", modo)
    matplotlib.rcParams.update(
        {
            "figure.facecolor": bg,
            "axes.facecolor": bg,
            "axes.edgecolor": C("border", modo),
            "axes.labelcolor": fg,
            "xtick.color": fg,
            "ytick.color": fg,
            "text.color": fg,
            "grid.color": C("border", modo),
            "grid.alpha": 0.3,
            "lines.color": acc,
            "patch.facecolor": acc,
            "font.family": _DEFAULT_FONT_FAMILY,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def nm_icon(key: str, color: str, size: int = 20):
    """QIcon desde catálogo SVG v3 → fallback QtAwesome (compatibility).

    1. Mapea ``key`` compatibility ('animo', 'pacientes', …) a nombre v3
       ('mood', 'users', …) si aplica.
    2. Si el nombre existe en ``shared.icons_svg``, renderiza SVG con
       stroke proporcional y lo envuelve en QIcon.
    3. Si no, cae a QtAwesome con el mapping compatibility MODULE_ICONS/HUB_ICONS.
    """
    # Aceptar QColor además de str: icons_svg espera un hex string ('#rrggbb').
    if hasattr(color, "name"):
        color = color.name()
    # 1. Intentar catálogo v3
    try:
        from shared.icons_svg import nm_svg_pixmap, has_icon
    except ImportError:
        try:
            from icons_svg import nm_svg_pixmap, has_icon  # type: ignore
        except ImportError:
            nm_svg_pixmap = None
            has_icon = lambda _n: False  # noqa: E731
    if has_icon is not None:
        v3_name = _MODULE_KEY_V3.get(key) or _HUB_KEY_V3.get(key) or key
        if has_icon(v3_name):
            pix = nm_svg_pixmap(v3_name, color, size)
            if pix is not None and not pix.isNull():
                from PyQt6.QtGui import QIcon

                return QIcon(pix)

    # 2. Fallback QtAwesome (import perezoso: solo se paga el costo de cargar
    #    qtawesome cuando de verdad falta un SVG, no en cada arranque de la app).
    import qtawesome as qta

    icon_name = MODULE_ICONS.get(key, HUB_ICONS.get(key, key))
    icon_name = _ICON_FALLBACKS.get(icon_name, icon_name)
    try:
        return qta.icon(icon_name, color=color)
    except Exception as e:
        fallback = _ICON_FALLBACKS.get(icon_name, "fa5s.circle")
        _log.warning(f"Icono QtAwesome no cargó ({icon_name}, {size}px): {e}")
        return qta.icon(fallback, color=color)


def _tm():
    from shared.theme_manager import ThemeManager

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


def _ensure_ui_font():
    try:
        from shared.fonts import load_fonts

        load_fonts()
    except Exception as e:
        _log.warning(f"load_fonts() falló: {e}")


def _font_family() -> str:
    _ensure_ui_font()
    from shared.fonts import FONT_SANS

    return FONT_SANS


def _serif_family() -> str:
    _ensure_ui_font()
    from shared.fonts import FONT_SERIF

    return FONT_SERIF


def _mono_family() -> str:
    _ensure_ui_font()
    from shared.fonts import FONT_MONO

    return FONT_MONO


_noise_pixmap_cache: dict = {}


def _gradient_stops(modo: str = "dark_hybrid") -> list[tuple[str, float]]:
    raw = get_gradient(norm_modo(modo))
    if raw and isinstance(raw[0], (tuple, list)):
        return [(str(color_hex), float(pos)) for color_hex, pos in raw]
    if len(raw) >= 2:
        return [(str(raw[0]), 0.0), (str(raw[1]), 1.0)]
    pal = V3_DARK if "dark" in norm_modo(modo) else V3_LIGHT
    return [(pal["gradFrom"], 0.0), (pal["gradTo"], 1.0)]


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


def _design_token(key: str, modo: str) -> str | None:
    """Resuelve una clave contra los tokens runtime V6 (shared.design_tokens).

    Vocabulario V6: ``bg_canvas``, ``bg_sidebar``, ``ink_primary``,
    ``primary``, ``accent``, ``teal``, ``cat_*``, etc. Devuelve None si la
    clave tampoco existe ahí.
    """
    try:
        from shared import design_tokens as _dt
    except Exception:  # pragma: no cover - fallback frozen / sys.path
        try:
            import design_tokens as _dt  # type: ignore
        except Exception:
            return None
    pal = _dt.LIGHT if v3_mode(modo) == "light" else _dt.DARK
    return pal.get(key)


def C(key: str, modo: str = "dark_hybrid") -> str:
    """Devuelve el valor hex del token de color. Shorthand legible.

    Resuelve primero contra ``COLORS`` (paletas V3 + bridge compatibility de
    ``shared.theme``). Si la clave no existe ahí, hace fallback al vocabulario
    runtime V6 de ``shared.design_tokens`` (``bg_canvas``, ``ink_primary``,
    ``primary``…), de modo que el código nuevo pueda usar cualquiera de los dos
    vocabularios a través del mismo helper sin romper consumidores existentes.
    """
    modo = norm_modo(modo)
    pal = COLORS.get(modo, COLORS["dark_hybrid"])
    if key in pal:
        return pal[key]
    val = _design_token(key, modo)
    return val if val is not None else "#888888"


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
        qcolor('accent')                     -> QColor("#5EE0C7")
        qcolor('bg_surface', 'light_hybrid') -> QColor("#FBF8F1")
        qcolor('accent', alpha=80)           -> QColor aqua semitransparente
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

_TITLE_FONT_TOKENS = {
    "size_display",
    "size_display_xl",
    "size_display_l",
    "size_display_m",
    "display",
    "displayXL",
    "displayL",
    "displayM",
    "display_xl",
    "display_l",
    "display_m",
    "size_h1",
    "size_h2",
    "size_h3",
    "h1",
    "h2",
    "h3",
    "size_heading_l",
    "size_heading_m",
    "headingL",
    "headingM",
}


def _font_token_allows_title_weight(size_key: str | int) -> bool:
    if isinstance(size_key, int):
        return size_key >= int(TYPOGRAPHY.get("size_heading_m", 16))
    return size_key in _TITLE_FONT_TOKENS


def _adn_clamped_weight(size_key: str | int, weight: int) -> int:
    if int(weight) >= 600 and not _font_token_allows_title_weight(size_key):
        return int(TYPOGRAPHY.get("weight_medium", 500))
    return int(weight)


def qfont(
    size_key: str = "size_body", bold: bool = False, family: str = None, weight: int | None = None
) -> QFont:
    """
    Devuelve un QFont configurado con los tokens de tipografía del tema.

    Args:
        size_key: Key de TYPOGRAPHY (ej: 'size_h1', 'size_body') o int directo.
        bold:     Si True, peso DemiBold 600 (compatibility; runtime "poco bold". Ignorado si `weight`).
        family:   Override de familia; None → fuente UI cargada o default v3.
        weight:   Peso numérico v3 (400/500/600/700). Si se pasa, tiene prioridad
                  sobre `bold`. Para tokens v3 usar TYPOGRAPHY['weight_medium'] etc.

    Ejemplos:
        qfont('size_h2', bold=True)
        qfont('size_h2', weight=TYPOGRAPHY['weight_semibold'])  # v3
        qfont(28, weight=700)
    """
    if family is not None:
        fam = family
    elif isinstance(size_key, str) and size_key in {
        "size_display",
        "size_display_xl",
        "size_display_l",
        "size_display_m",
        "display",
        "displayXL",
        "displayL",
        "displayM",
        "display_xl",
        "display_l",
        "display_m",
        "size_h1",
        "size_h2",
        "size_h3",
        "size_heading_l",
        "size_heading_m",
    }:
        fam = _serif_family()
    elif isinstance(size_key, str) and size_key in {"size_mono", "mono"}:
        fam = _mono_family()
    else:
        fam = _font_family()
    if isinstance(size_key, int):
        px = size_key
    else:
        px = TYPOGRAPHY.get(size_key, TYPOGRAPHY.get("size_body", 14))

    # HANDOFF §2: escala en px (setPixelSize), no pt. A 96 DPI los pt rendían
    # ~33% más grandes que el diseño HTML y aplastaban la jerarquía.
    f = QFont(fam)
    f.setPixelSize(int(px))
    f.setWordSpacing(1.0)
    if weight is not None:
        # QFont.setWeight acepta int 1-1000 desde Qt6 (mapeo CSS-compatible).
        w = _adn_clamped_weight(size_key, int(weight))
        try:
            f.setWeight(QFont.Weight(w))
        except (ValueError, TypeError):
            f.setWeight(QFont.Weight.Bold if w >= 600 else QFont.Weight.Normal)
    else:
        # runtime actual: el camino compatibility bold=True no debe convertir controles y
        # labels en negritas. Los títulos usan weight explícito cuando aplica.
        f.setWeight(QFont.Weight.Medium if bold else QFont.Weight.Normal)
    if size_key in (
        "size_h1",
        "size_h2",
        "size_display",
        "size_display_xl",
        "size_display_l",
        "size_display_m",
        "display",
        "displayXL",
        "displayL",
        "displayM",
        "display_xl",
        "display_l",
        "display_m",
    ):
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def nm_font(level: str, bold_override=False) -> QFont:
    """Devuelve un QFont segun la escala tipografica NeuroMood."""
    spec = FONT_SCALE.get(level, FONT_SCALE["body"])
    weight = QFont.Weight.Bold if bold_override else QFont.Weight(spec["weight"])
    if spec.get("mono"):
        fam = _mono_family()
    elif spec.get("serif"):
        fam = _serif_family()
    else:
        fam = _font_family()
    f = QFont(fam, spec["size"])
    f.setWordSpacing(1.0)
    f.setWeight(weight)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def qfont_emoji(size_key: str = "size_emoji") -> QFont:
    """Font específico para emojis — usa Segoe UI Emoji en Windows."""
    pt = TYPOGRAPHY.get(size_key, 64)
    families = [
        "Segoe UI Emoji",
        "Apple Color Emoji",
        "Noto Color Emoji",
        TYPOGRAPHY.get("font_family", "Segoe UI"),
    ]
    db = QFontDatabase()
    chosen = TYPOGRAPHY.get("font_family", "Segoe UI")
    for fam in families:
        if fam in db.families():
            chosen = fam
            break
    return QFont(chosen, pt)


# ── QGraphicsDropShadowEffect ─────────────────────────────────────────────────


def shadow_effect(
    tipo: str = "card", modo: str = "dark_hybrid", parent=None
) -> QGraphicsDropShadowEffect:
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


def linear_gradient(
    rect: QRectF,
    modo: str = "dark_hybrid",
    angle: float = 135,
    color_a: str = None,
    color_b: str = None,
    alpha_a: int = 255,
    alpha_b: int = 255,
) -> QLinearGradient:
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


def rich_gradient(rect: QRectF, modo: str = "dark_hybrid", angle: float = 135) -> QLinearGradient:
    """
    Gradiente UI de 3 paradas (indigo -> teal -> violet).
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


def linear_gradient_vertical(
    rect: QRectF, color_top: QColor, color_bottom: QColor
) -> QLinearGradient:
    """Gradiente vertical simple top → bottom. Para área bajo curva en gráficos."""
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    grad.setColorAt(0.0, color_top)
    grad.setColorAt(1.0, color_bottom)
    return grad


# ── QRadialGradient (glow) ────────────────────────────────────────────────────


def noise_overlay(
    painter: QPainter, rect: QRectF, opacity: float = 0.035, modo: str = "dark_hybrid"
):
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


def radial_glow(center: QPointF, radius: float, color_hex: str, alpha: int = 80) -> QRadialGradient:
    """
    Gradiente radial para simular glow/resplandor alrededor de un elemento.

    Args:
        center:    Centro del glow (QPointF)
        radius:    Radio del glow en píxeles
        color_hex: Color hex del glow (ej: '#5EE0C7')
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


def radial_glow_double(center: QPointF, radius: float, color_hex: str) -> QRadialGradient:
    """Glow doble: centro más brillante, decaimiento suave. Para arcos de respiración."""
    grad = QRadialGradient(center, radius)
    core = QColor(color_hex)
    core.setAlpha(120)
    mid = QColor(color_hex)
    mid.setAlpha(60)
    edge = QColor(color_hex)
    edge.setAlpha(0)
    grad.setColorAt(0.0, core)
    grad.setColorAt(0.4, mid)
    grad.setColorAt(1.0, edge)
    return grad


# ── QConicalGradient (arco) ───────────────────────────────────────────────────


def conical_arc_gradient(
    center: QPointF, start_angle: float, modo: str = "dark_hybrid"
) -> QConicalGradient:
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


def _clinical_scrollbar_qss(modo: str = "dark_hybrid") -> str:
    """Scrollbars del cockpit clínico: discretas pero presentes.

    Barra neutra y de bajo contraste: debe indicar overflow sin competir con el
    contenido clínico ni parecer un control de estado.
    """
    modo = norm_modo(modo)
    c = colors(modo)
    handle = c.get("line", c.get("border", "#808080"))
    hover = "rgba(255,255,255,0.22)" if "dark" in modo else "rgba(28,34,24,0.24)"
    return f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px 4px 2px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {handle};
        border: none;
        border-radius: 4px;
        min-height: 44px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        background: transparent;
        border: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 2px 4px 2px 4px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {handle};
        border: none;
        border-radius: 4px;
        min-width: 44px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {hover};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: transparent;
        border: none;
    }}
    """


def stylesheet_hidden_scrollbar(modo: str = "dark_hybrid") -> str:
    """Deprecated compatibility alias.

    NeuroMood Adaptive Desktop Layout V1 forbids hidden scrollbars as layout
    patches. Keep the public helper for older imports, but return a visible,
    clinical scrollbar style instead of zero-width bars.
    """
    return _clinical_scrollbar_qss(modo)


_NM_CONTROL_HEIGHT = 36
_NM_CONTROL_COMPACT_HEIGHT = 32
_NM_CONTROL_INNER_HEIGHT = 24
_NM_CONTROL_PAD_X = 12
_NM_CONTROL_PAD_Y = 5
_NM_CONTROL_RADIUS = LAYOUT["radius_input"]
_NM_CONTROL_FONT = TYPOGRAPHY["size_body"]
# Botones (QPushButton global) en negrita: semibold 600 para que el texto de
# todos los botones se lea en negrita (pedido user feedback), no medium 500.
_NM_CONTROL_WEIGHT = TYPOGRAPHY["weight_semibold"]
_NM_TAB_HEIGHT = 32
_NM_TAB_RADIUS = 16
_NM_TAB_FONT = TYPOGRAPHY["size_caption"]


def stylesheet_base(modo: str = "dark_hybrid") -> str:
    """
    Stylesheet global QApplication mínimo: fondo, texto, scrollbars, tooltips.
    Se aplica una vez en QApplication antes de construir la UI.
    """
    modo = norm_modo(modo)
    c = colors(modo)
    # Scrollbars: un solo lenguaje neutro — _clinical_scrollbar_qss apendado al
    # final (el bloque gradiente teal→violeta que vivía acá era código muerto:
    # QSS posterior con igual especificidad lo pisaba siempre).
    return f"""
    QWidget {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
        selection-background-color: {c["accent"]};
        selection-color: {c["text_on_accent"]};
    }}
    QToolTip {{
        background-color: {c["bg_elevated"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: 6px;
        padding: 4px 8px;
        font-size: {TYPOGRAPHY["size_caption"]}px;
    }}
    QPushButton {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_HEIGHT // 2}px;
        padding: 0 14px;
        min-height: {_NM_CONTROL_HEIGHT}px;
        font-weight: {_NM_CONTROL_WEIGHT};
    }}
    QPushButton:hover {{
        background-color: {c["primary_soft"]};
        border-color: {c.get("border_strong", c.get("border_card", c["border"]))};
    }}
    QPushButton:pressed {{
        background-color: {c["bg_elevated"]};
    }}
    QPushButton:disabled {{
        color: {c["text_tertiary"]};
        background-color: {c["bg_input"]};
        border-color: {c.get("border_card", c["border"])};
    }}
    QPushButton[variant="compact"] {{
        min-height: {_NM_CONTROL_COMPACT_HEIGHT}px;
        border-radius: {_NM_CONTROL_COMPACT_HEIGHT // 2}px;
        padding: 0 12px;
    }}
    QTableView, QTableWidget, QListWidget {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {LAYOUT["radius_card"]}px;
        gridline-color: {c.get("border_card", c["border"])};
        alternate-background-color: {c["bg_input"]};
        selection-background-color: {c["primary_soft"]};
        selection-color: {c["text_primary"]};
        outline: none;
    }}
    QHeaderView::section {{
        background-color: {c["bg_surface"]};
        color: {c["text_tertiary"]};
        border: none;
        border-bottom: 1px solid {c.get("border_card", c["border"])};
        padding: 10px 12px;
        font-size: {TYPOGRAPHY["size_eyebrow"]}px;
        font-weight: {_NM_CONTROL_WEIGHT};
    }}
    QTableView::item, QTableWidget::item {{
        padding: 12px;
        border-bottom: 1px solid {c.get("border_card", c["border"])};
    }}
    QListWidget::item {{
        min-height: 34px;
        padding: 6px 10px;
        border-bottom: 1px solid {c.get("border_card", c["border"])};
    }}
    QListWidget::item:hover, QTableView::item:hover, QTableWidget::item:hover {{
        background-color: {c["primary_soft"]};
    }}
    QSplitter::handle {{
        background-color: transparent;
    }}
    
    {focus_ring_stylesheet(modo)}
    {_clinical_scrollbar_qss(modo)}
    """


def stylesheet_scrollarea(modo: str = "dark_hybrid") -> str:
    """Stylesheet scrollbars con tokens del tema (neutro vía _clinical_scrollbar_qss;
    el bloque gradiente teal→violeta que vivía acá era código muerto pisado)."""
    return f"""
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    {_clinical_scrollbar_qss(modo)}
    """


def stylesheet_slider(modo: str = "dark_hybrid") -> str:
    """QSlider horizontal plano (runtime): recorrido `primary` sólido sobre
    track neutro, handle blanco. El groove-gradiente firma anterior leía técnico."""
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QSlider::groove:horizontal {{
        height: 6px;
        background: {c["progress_track"]};
        border-radius: 3px;
        margin: 0 8px;
    }}
    QSlider::handle:horizontal {{
        background: {c["text_on_accent"]};
        border: 2px solid {c["bg_elevated"]};
        width: 20px;
        height: 20px;
        margin: -7px -4px;
        border-radius: 10px;
    }}
    QSlider::handle:horizontal:hover {{
        border-color: {c["primary"]};
    }}
    QSlider::sub-page:horizontal {{
        background: {c["primary"]};
        border-radius: 3px;
        height: 6px;
        margin: 0 8px;
    }}
    QSlider::add-page:horizontal {{
        background: {c["progress_track"]};
        border-radius: 3px;
        height: 6px;
        margin: 0 8px;
    }}
    """


def stylesheet_tabwidget(modo: str = "dark_hybrid") -> str:
    """QTabWidget segmentado compacto según runtime/05."""
    return stylesheet_tabwidget_segmented(modo)


def stylesheet_tabwidget_underline(modo: str = "dark_hybrid") -> str:
    """Compat: las tabs underline se renderizan con el mismo patrón runtime."""
    return stylesheet_tabwidget_segmented(modo)


def stylesheet_tabwidget_segmented(modo: str = "dark_hybrid") -> str:
    """QTabWidget estilo "segmento" (tablero runtime 05 — Tabs & Segmentos).

    Para subniveles que viven DEBAJO de tabs underline: diferencia la
    jerarquía con un segmento de fondo en vez de repetir el subrayado
    (regla anti-frankenstein: no doble subrayado / doble navegación).
    Activo = relleno primary con tinta invertida, como el tablero 05.
    """
    modo = norm_modo(modo)
    c = colors(modo)
    primary = v3c("primary", modo).name()
    primary_ink = v3c("primary_ink", modo).name()
    seg_bg = v3c("surface_2", modo).name()
    return f"""
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar {{
        background: {seg_bg};
        border-radius: {_NM_TAB_RADIUS}px;
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c["text_secondary"]};
        min-height: {_NM_TAB_HEIGHT - 8}px;
        padding: 4px 14px;
        margin: 3px 2px;
        border: none;
        border-radius: {_NM_TAB_RADIUS - 3}px;
        font-size: {_NM_TAB_FONT}px;
        font-weight: {_NM_CONTROL_WEIGHT};
    }}
    QTabBar::tab:selected {{
        background: {primary};
        color: {primary_ink};
        font-weight: {_NM_CONTROL_WEIGHT};
    }}
    QTabBar::tab:hover:!selected {{
        color: {c["text_primary"]};
    }}
    """


def stylesheet_lineedit(modo: str = "dark_hybrid") -> str:
    """QLineEdit con colores del tema. Los focus borders se manejan en NMInput."""
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QLineEdit {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        min-height: {_NM_CONTROL_INNER_HEIGHT}px;
        font-size: {_NM_CONTROL_FONT}px;
        selection-background-color: {c["accent"]};
        selection-color: {c["text_on_accent"]};
    }}
    QLineEdit::placeholder {{
        color: {c["text_tertiary"]};
    }}
    QLineEdit:focus {{
        border-color: {c["border_focus"]};
    }}
    """


def stylesheet_textedit(modo: str = "dark_hybrid") -> str:
    """QTextEdit y QPlainTextEdit."""
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QTextEdit, QPlainTextEdit {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        font-size: {_NM_CONTROL_FONT}px;
        selection-background-color: {c["accent"]};
        selection-color: {c["text_on_accent"]};
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c["border_focus"]};
    }}
    """


_CHEVRON_CACHE: dict[str, str] = {}


def _qss_chevron_url(color_hex: str, direction: str = "down") -> str:
    """SVG chevron para QSS ``image: url(...)``, cacheado por color/dirección.

    El truco de triángulo-por-borde (``image: none`` + borders) renderiza como
    un CUADRADO sólido en Qt6 — el artefacto "▪" junto a los combos (informe
    user feedback). Un SVG real dibuja el chevron fino y temable.
    """
    import tempfile

    key = f"{color_hex.lower()}-{direction}"
    cached = _CHEVRON_CACHE.get(key)
    if cached and os.path.exists(cached):
        return cached.replace("\\", "/")
    path_d = "M6 9l6 6 6-6" if direction == "down" else "M6 15l6-6 6 6"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color_hex}" stroke-width="2.4" '
        f'stroke-linecap="round" stroke-linejoin="round"><path d="{path_d}"/></svg>'
    )
    fd, path = tempfile.mkstemp(suffix=".svg", prefix=f"nm_chevron_{direction}_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(svg)
    _CHEVRON_CACHE[key] = path
    return path.replace("\\", "/")


def stylesheet_combobox(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QComboBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        font-size: {_NM_CONTROL_FONT}px;
        min-height: {_NM_CONTROL_INNER_HEIGHT}px;
    }}
    QComboBox:focus {{
        border-color: {c["border_focus"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox::down-arrow {{
        image: url({_qss_chevron_url(c["text_secondary"])});
        width: 12px;
        height: 12px;
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {LAYOUT["radius_card"]}px;
        selection-background-color: {c["bg_elevated"]};
        padding: 4px;
        outline: none;
    }}
    """


def stylesheet_timeedit(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QTimeEdit {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        font-size: {_NM_CONTROL_FONT}px;
        min-height: {_NM_CONTROL_INNER_HEIGHT}px;
    }}
    QTimeEdit:focus {{
        border-color: {c["border_focus"]};
    }}
    QTimeEdit::up-button, QTimeEdit::down-button {{
        width: 0;
        border: none;
    }}
    """


def stylesheet_dateedit(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QDateEdit {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        font-size: {_NM_CONTROL_FONT}px;
        min-height: {_NM_CONTROL_INNER_HEIGHT}px;
    }}
    QDateEdit:focus {{
        border-color: {c["border_focus"]};
    }}
    QDateEdit::drop-down {{
        border: none;
        width: 28px;
    }}
    QDateEdit::down-arrow {{
        image: url({_qss_chevron_url(c["text_secondary"])});
        width: 12px;
        height: 12px;
        margin-right: 8px;
    }}
    QDateEdit QAbstractItemView {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {LAYOUT["radius_card"]}px;
        selection-background-color: {c["bg_elevated"]};
        outline: none;
    }}
    """


def stylesheet_spinbox(modo: str = "dark_hybrid") -> str:
    modo = norm_modo(modo)
    c = colors(modo)
    return f"""
    QSpinBox {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c.get("border_card", c["border"])};
        border-radius: {_NM_CONTROL_RADIUS}px;
        padding: {_NM_CONTROL_PAD_Y}px {_NM_CONTROL_PAD_X}px;
        font-size: {_NM_CONTROL_FONT}px;
        min-height: {_NM_CONTROL_INNER_HEIGHT}px;
    }}
    QSpinBox:focus {{
        border-color: {c["border_focus"]};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 18px;
        border: none;
        background: {c.get("bg_elevated", c["bg_surface"])};
        border-radius: 3px;
    }}
    QSpinBox::up-arrow {{
        image: url({_qss_chevron_url(c["text_secondary"], "up")});
        width: 10px;
        height: 10px;
        margin: 2px;
    }}
    QSpinBox::down-arrow {{
        image: url({_qss_chevron_url(c["text_secondary"])});
        width: 10px;
        height: 10px;
        margin: 2px;
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

    bg = QColor(c["bg_primary"])
    surf = QColor(c["bg_surface"])
    elev = QColor(c["bg_elevated"])
    tp = QColor(c["text_primary"])
    QColor(c["text_secondary"])
    acc = QColor(c["accent"])
    brdr = QColor(c.get("border_card", c["border"]))
    dis = QColor(c["text_tertiary"])

    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        p.setColor(group, QPalette.ColorRole.Window, bg)
        p.setColor(group, QPalette.ColorRole.WindowText, tp)
        p.setColor(group, QPalette.ColorRole.Base, surf)
        p.setColor(group, QPalette.ColorRole.AlternateBase, elev)
        p.setColor(group, QPalette.ColorRole.Text, tp)
        p.setColor(group, QPalette.ColorRole.BrightText, tp)
        p.setColor(group, QPalette.ColorRole.ButtonText, tp)
        p.setColor(group, QPalette.ColorRole.Button, elev)
        p.setColor(group, QPalette.ColorRole.Highlight, acc)
        p.setColor(group, QPalette.ColorRole.HighlightedText, QColor(c["text_on_accent"]))
        p.setColor(group, QPalette.ColorRole.PlaceholderText, QColor(c["text_tertiary"]))
        p.setColor(group, QPalette.ColorRole.Mid, brdr)
        p.setColor(group, QPalette.ColorRole.Dark, bg)
        p.setColor(group, QPalette.ColorRole.Shadow, QColor(0, 0, 0, 80))

    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, dis)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, dis)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, dis)

    return p


# ── Utilidades de recurso (preservadas de components.py) ─────────────────────


def obtener_ruta_recurso(nombre_archivo: str) -> str:
    """Ruta a un recurso: usa sys._MEIPASS en frozen, raíz del proyecto en dev (con fallback a assets/)."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    path = os.path.join(base, nombre_archivo)
    if not getattr(sys, "frozen", False) and not os.path.exists(path):
        assets_path = os.path.join(base, "assets", nombre_archivo)
        if os.path.exists(assets_path):
            return assets_path
    return path


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
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_uint),
                ("AnimationId", ctypes.c_int),
            ]

        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("pData", ctypes.c_void_p),
                ("ulDataSize", ctypes.c_ulong),
            ]

        accent = ACCENT_POLICY(AccentState=1, AccentFlags=2, GradientColor=int(color_abgr.value))
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
    _ensure_ui_font()
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
    """Invierte píxeles blancos del logo a tinta runtime para el tema claro (PIL Image)."""
    img = img.convert("RGBA")
    ink = QColor(V3_LIGHT["text"])
    tinta = (ink.red(), ink.green(), ink.blue())
    data = img.getdata()
    nueva = []
    for r, g, b, a in data:
        if r > 200 and g > 200 and b > 200 and a > 0:
            nueva.append((*tinta, a))
        else:
            nueva.append((r, g, b, a))
    img.putdata(nueva)
    return img


# ── Constantes de layout como Python ints (conveniencia) ─────────────────────


def pill_radius(widget, fallback: int = 24) -> int:
    """Radio pill efectivo para QSS, clampeado a la mitad de la altura real.

    Qt NO clampa ``border-radius`` en stylesheets: con el token pill (999)
    directo, las esquinas quedan indefinidas y suelen renderizar CUADRADAS.
    Los componentes que pintan a mano ya hacen ``min(999, h // 2)``; este
    helper es el equivalente para los que se estilan vía QSS.
    """
    h = widget.height()
    if h <= 0:
        try:
            h = widget.sizeHint().height()
        except Exception:
            h = 0
    if h <= 0:
        h = fallback
    return min(V3_RADIUS["pill"], max(4, h // 2))


RADIUS_CARD = LAYOUT["radius_card"]
RADIUS_BUTTON = LAYOUT["radius_button"]
RADIUS_INPUT = LAYOUT["radius_input"]
RADIUS_PILL = LAYOUT["radius_pill"]
RADIUS_BADGE = LAYOUT["radius_badge"]
RADIUS_SMALL = LAYOUT["radius_small"]
CHECKBOX_SIZE = LAYOUT["checkbox_size"]
PAD_CONTAINER = LAYOUT["padding_container"]
PAD_CARD = LAYOUT["padding_card"]
GAP_CARDS = LAYOUT["gap_cards"]
GAP_ELEMENTS = LAYOUT["gap_elements"]
HEADER_H = LAYOUT["header_height"]

# ── Tokens de tipografía mono (Design System v3 — Mayo 2026) ──────────────────
FONT_MONO = TYPOGRAPHY.get("font_mono", "Consolas")
SIZE_TIME_LARGE = TYPOGRAPHY.get("size_time_large", 20)  # pt — NMAvisoCard, countdown respiración
SIZE_TIME_TIMER = TYPOGRAPHY.get("size_time_timer", 18)  # pt — NMFocusArc MM:SS

# ── Opacidades de aura y blob ──────────────────────────────────────────────────
AURA_OPACITY_DARK = LAYOUT.get("aura_opacity_dark", 0.18)
AURA_OPACITY_LIGHT = LAYOUT.get("aura_opacity_light", 0.10)
# runtime (F2 índigo-calmado): el wash plano de NMFeaturedCard usa estas
# opacidades — antes 0.22/0.18 alimentaban blobs radiales que leían "manchas".
BLOB_OPACITY_DARK = LAYOUT.get("blob_opacity_dark", 0.06)
BLOB_OPACITY_LIGHT = LAYOUT.get("blob_opacity_light", 0.04)

# ── Umbrales semánticos de progress rings ──────────────────────────────────────
RING_GOOD_THRESHOLD = LAYOUT.get("ring_good_threshold", 80)  # ≥80% → teal
RING_MID_THRESHOLD = LAYOUT.get("ring_mid_threshold", 50)  # 50-79% → accent, <50% → violet


def qcolor_to_rgba_css(color: "QColor") -> str:
    """Convierte un QColor a string rgba() para usar en stylesheets Qt."""
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"


def label_style(modo: str, key: str = "text_primary") -> str:
    """Shortcut para QLabel: color del tema + fondo transparente.

    Uso: lbl.setStyleSheet(label_style(modo, 'text_secondary'))
    Equivale a: f'color: {C(key, modo)}; background: transparent;'
    """
    return f"color: {C(key, modo)}; background: transparent;"


# ── Helpers v3 (Design System v3 — Mayo 2026) ─────────────────────────────────


def qfont_mono(size_pt: int, bold: bool = False) -> QFont:
    """QFont con familia monospace para timers, contadores y log de terminal.

    Args:
        size_pt: Tamaño en puntos (usar SIZE_TIME_LARGE o SIZE_TIME_TIMER como referencia)
        bold:    True para peso Bold

    Ejemplo:
        lbl.setFont(qfont_mono(SIZE_TIME_LARGE, bold=True))
    """
    f = QFont(FONT_MONO, size_pt)
    f.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def ring_color(pct: float, modo: str = "dark_hybrid") -> str:
    """Color semántico para progress rings según porcentaje de completado.

    Regla:
        ≥ RING_GOOD_THRESHOLD (80%) → teal   (bien)
        ≥ RING_MID_THRESHOLD  (50%) → accent  (en progreso)
        <  RING_MID_THRESHOLD       → violet  (bajo / incipiente)

    Args:
        pct:  Porcentaje 0.0–100.0
        modo: Modo del tema

    Ejemplo:
        arc_color = ring_color(progreso * 100, modo)
    """
    if pct >= RING_GOOD_THRESHOLD:
        return C("teal", modo)
    elif pct >= RING_MID_THRESHOLD:
        return C("accent", modo)
    else:
        return C("violet", modo)


def aura_opacity(modo: str = "dark_hybrid") -> float:
    """Opacidad del aura radial de SessionColor según modo.

    dark → 0.18, light → 0.10
    """
    return AURA_OPACITY_DARK if "dark" in norm_modo(modo) else AURA_OPACITY_LIGHT


def blob_opacity(modo: str = "dark_hybrid") -> float:
    """Opacidad del wash plano de NMFeaturedCard según modo (dark 0.06 / light 0.04)."""
    return BLOB_OPACITY_DARK if "dark" in norm_modo(modo) else BLOB_OPACITY_LIGHT


def stylesheet_installer(modo: str = "dark_hybrid") -> str:
    """Stylesheet para ventanas de instalador/desinstalador.

    Siempre dark mode con terminal_bg y tipografía monospace.
    """
    c = colors("dark_hybrid")  # instaladores siempre dark
    return f"""
    QWidget {{
        background-color: {c["bg_primary"]};
        color: {c["text_primary"]};
        font-family: "{_font_family()}";
    }}
    QTextEdit, QPlainTextEdit {{
        background-color: {c["installer_terminal_bg"]};
        color: {c["teal"]};
        border: 1px solid {c["border"]};
        border-radius: {LAYOUT["radius_input"]}px;
        padding: 8px;
        font-family: "{FONT_MONO}";
        font-size: {TYPOGRAPHY["size_small"]}px;
        selection-background-color: {c["accent"]};
        selection-color: {c["text_on_accent"]};
    }}
    {_clinical_scrollbar_qss("dark_hybrid")}
    QToolTip {{
        background-color: {c["bg_elevated"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_card"]};
        border-radius: 6px; padding: 4px 8px;
        font-size: {TYPOGRAPHY["size_small"]}px;
    }}
    """


# ══════════════════════════════════════════════════════════════════════════════
# Helpers v3 (Design System v3 — Mayo 2026)
# ══════════════════════════════════════════════════════════════════════════════
#
# Estos helpers consumen la superficie nueva de tokens (V3_LIGHT/V3_DARK,
# V3_SHADOWS, V3_GRADIENTS, MOOD_PALETTE) y serán usados por la próxima
# refactorización de components_qt.py. Los helpers compatibility de arriba siguen
# operando contra el bridge COLORS y obtienen los mismos colores v3.
# ══════════════════════════════════════════════════════════════════════════════

import re as _re

_RGBA_RE = _re.compile(
    r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)",
    _re.IGNORECASE,
)


def parse_rgba(value: str) -> QColor:
    """Convierte un string ``rgba(r,g,b,a01)`` o ``#rrggbb`` a QColor.

    En V3_DARK varias claves (surface, border, tealSoft, …) están como
    ``rgba(r, g, b, opacity_0_1)``. Qt no acepta ese formato directamente
    en todos los properties — este helper lo traduce a QColor con alpha 0-255.
    """
    if isinstance(value, QColor):
        return QColor(value)
    s = (value or "").strip()
    m = _RGBA_RE.match(s)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a01 = float(m.group(4)) if m.group(4) is not None else 1.0
        a = max(0, min(255, round(a01 * 255)))
        return QColor(r, g, b, a)
    return QColor(s) if s else QColor()


def v3c(key: str, modo: str = "dark", alpha: int | None = None) -> QColor:
    """QColor desde la paleta v3 (V3_LIGHT / V3_DARK).

    Args:
        key:   Clave v3 (``"bg"``, ``"surface"``, ``"text"``, ``"text2"``,
               ``"teal"``, ``"violet"``, ``"gradFrom"``, ``"borderStrong"``…).
        modo:  ``"light"`` / ``"dark"`` (o cualquier alias compatibility: se normaliza).
        alpha: Override 0-255. Si ``None``, respeta el alpha del rgba() original.

    Soporta los keys translúcidos de dark (``rgba(…)``) gracias a parse_rgba.
    """
    pal = get_v3_palette(modo)
    raw = pal.get(key)
    if raw is None:
        # Fallback razonable: buscar en bridge compatibility
        raw = C(key, modo)
    c = parse_rgba(raw)
    if alpha is not None:
        c.setAlpha(max(0, min(255, int(alpha))))
    return c


def paint_card_lift(painter, rect: QRectF, radius: float, modo: str) -> None:
    """Pinta el *highlight* superior interno ("lift") de una superficie.

    Dirección del mockup aprobado: un degradado blanco translúcido que cae
    sobre el ~42% superior de la card y le da material/elevación sin sombra
    dura. Debe llamarse en ``paintEvent`` DESPUÉS de rellenar la superficie y
    ANTES (o después) de dibujar el borde. Recorta al rect redondeado para no
    desbordar las esquinas.

    Args:
        painter: QPainter activo.
        rect:    QRectF de la card (0,0,w,h).
        radius:  radio de las esquinas (mismo que la superficie).
        modo:    tema ('light'/'dark' o alias).
    """
    alpha = V3_LIFT["light" if v3_mode(modo) == "light" else "dark"]
    if alpha <= 0 or rect.height() <= 1:
        return
    painter.save()
    clip = QPainterPath()
    clip.addRoundedRect(rect, radius, radius)
    painter.setClipPath(clip)
    grad = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.top() + rect.height() * 0.42)
    top = QColor(255, 255, 255, int(alpha))
    bottom = QColor(255, 255, 255, 0)
    grad.setColorAt(0.0, top)
    grad.setColorAt(1.0, bottom)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(grad))
    painter.drawRoundedRect(rect, radius, radius)
    painter.restore()


def v3_shadow(name: str = "card", modo: str = "dark", parent=None) -> QGraphicsDropShadowEffect:
    """QGraphicsDropShadowEffect parametrizado desde V3_SHADOWS.

    Args:
        name:  ``"sm"`` / ``"md"`` / ``"card"`` / ``"ring"`` (light)
               o ``"sm"`` / ``"md"`` / ``"card"`` / ``"glow"`` (dark).
        modo:  ``"light"`` / ``"dark"`` (o alias compatibility).
        parent: QObject padre opcional.
    """
    bucket = V3_SHADOWS[v3_mode(modo)]
    spec = bucket.get(name) or next(iter(bucket.values()))
    eff = QGraphicsDropShadowEffect(parent)
    eff.setBlurRadius(spec["blur"])
    dx, dy = spec["offset"]
    eff.setOffset(dx, dy)
    r, g, b, a = spec["color"]
    eff.setColor(QColor(r, g, b, a))
    return eff


def shadow_1(modo: str = "dark", parent=None) -> QGraphicsDropShadowEffect:
    """Card rest state — 1-2 px (visual compact §2.5)."""
    return v3_shadow("shadow_1", modo, parent)


def shadow_2(modo: str = "dark", parent=None) -> QGraphicsDropShadowEffect:
    """Card hover state — shadow-2 (visual compact §2.5)."""
    return v3_shadow("shadow_2", modo, parent)


def shadow_3(modo: str = "dark", parent=None) -> QGraphicsDropShadowEffect:
    """Modal/dialog — shadow-3 (visual compact §2.5)."""
    return v3_shadow("shadow_3", modo, parent)


def row_hover_stylesheet(modo: str, object_name: str, radius: int = 10) -> str:
    """Stylesheet de hover para filas de lista (fondo sutil + borde teal).

    Uso:
        widget.setStyleSheet(row_hover_stylesheet(self._modo, "NMPatientRowUI"))
    """
    is_dark = "dark" in v3_mode(modo)
    col = get_v3_palette(modo)
    col.get("teal", "#38BFA1")
    if is_dark:
        hover_bg = "rgba(56, 191, 161, 0.07)"
        rest_bg = col.get("surfaceSolid", "#1A1F2E")
    else:
        hover_bg = "rgba(56, 191, 161, 0.05)"
        rest_bg = col.get("surface", "#F4F6FB")
    border = col.get("border", col.get("borderSoft", "#2A2F3E"))
    return (
        f"QFrame#{object_name} {{ background: {rest_bg}; border: 1px solid {border}; "
        f"border-radius: {radius}px; }}"
        f"QFrame#{object_name}:hover {{ background: {hover_bg}; "
        f"border-color: rgba(56, 191, 161, 0.40); }}"
    )


def _angle_endpoints(rect: QRectF, angle_deg: float):
    import math

    rad = math.radians(angle_deg)
    cx, cy = rect.center().x(), rect.center().y()
    half = max(rect.width(), rect.height()) / 2
    dx = math.cos(rad) * half
    dy = math.sin(rad) * half
    return QPointF(cx - dx, cy - dy), QPointF(cx + dx, cy + dy)


def v3_linear_gradient(
    rect: QRectF, modo: str = "dark", angle: float = 135.0, kind: str = "signature"
) -> QLinearGradient:
    """Gradiente lineal v3 sobre ``rect``.

    Args:
        rect:  área del widget.
        modo:  ``"light"`` / ``"dark"`` (o alias compatibility).
        angle: grados (0=horizontal derecha, 90=vertical abajo, 135=diagonal).
        kind:  ``"signature"`` (teal → violet, V3_GRADIENTS) o ``"mood"`` para
               la slashbar emocional (que NO varía con theme).
    """
    if kind == "mood":
        # Mood gradient: idéntico en light y dark según README v3
        stops = [
            (V3_LIGHT["moodGradFrom"], 0.0),
            (V3_LIGHT["moodGradMid"], 0.5),
            (V3_LIGHT["moodGradTo"], 1.0),
        ]
    else:
        stops = V3_GRADIENTS[v3_mode(modo)]
    p1, p2 = _angle_endpoints(rect, angle)
    grad = QLinearGradient(p1, p2)
    for color_hex, pos in stops:
        grad.setColorAt(pos, QColor(color_hex))
    return grad


def v3_conical_signature(
    center: QPointF, start_angle: float = 90.0, modo: str = "dark"
) -> QConicalGradient:
    """Cónico teal → violet para anillos (V3Ring, Respiración, Timer)."""
    grad = QConicalGradient(center, start_angle)
    for color_hex, pos in V3_GRADIENTS[v3_mode(modo)]:
        grad.setColorAt(pos, QColor(color_hex))
    return grad


def v3_font(
    size_token: str = "size_body",
    weight: str | int = "weight_regular",
    mono: bool = False,
    serif: bool = False,
    italic: bool = False,
) -> QFont:
    """QFont desde tokens v3 (TYPOGRAPHY size + peso numérico).

    Args:
        size_token: clave de TYPOGRAPHY (``size_display`` … ``size_caption_xs``,
                    runtime spec: ``size_display_xl`` / ``_l`` / ``_m`` / ``size_heading_l`` /
                    ``size_heading_m`` / ``size_eyebrow`` / ``size_mono``)
                    o int directo en pt.
        weight:     clave de TYPOGRAPHY (``weight_regular`` / ``weight_medium``
                    / ``weight_semibold`` / ``weight_bold``) o int 1-1000.
        mono:       True → familia JetBrains Mono (timers, IDs, log installer).
        serif:      True → familia Newsreader (display, hero, números bienestar).
                    Si ``serif=True``, ``mono`` se ignora.
        italic:     True → estilo italic (runtime spec usa serif italic para personalización).
    """
    px = (
        size_token
        if isinstance(size_token, int)
        else TYPOGRAPHY.get(size_token, TYPOGRAPHY.get("size_body", 13))
    )
    if isinstance(weight, str):
        w = TYPOGRAPHY.get(weight, 400)
    else:
        w = int(weight)
    w = _adn_clamped_weight(size_token, int(w))
    if serif:
        fam = _serif_family()
    elif mono:
        fam = _mono_family()
    else:
        fam = _font_family()
    # HANDOFF §2: escala en px (setPixelSize), no pt.
    f = QFont(fam)
    f.setPixelSize(int(px))
    f.setWordSpacing(1.0)
    try:
        f.setWeight(QFont.Weight(w))
    except (ValueError, TypeError):
        f.setWeight(QFont.Weight.Bold if w >= 600 else QFont.Weight.Normal)
    if italic:
        f.setItalic(True)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def mood_qcolor(level: int, key: str = "to", alpha: int = 255) -> QColor:
    """QColor desde MOOD_PALETTE.

    Args:
        level: 1-10 (se clampa).
        key:   ``"from"`` (claro), ``"to"`` (base, default) o ``"glow"``.
        alpha: 0-255.
    """
    spec = get_mood(level)
    c = QColor(spec.get(key, spec["to"]))
    c.setAlpha(max(0, min(255, int(alpha))))
    return c


def mood_gradient(rect: QRectF, level: int, angle: float = 135.0) -> QLinearGradient:
    """Gradiente lineal del MOOD nivel: from → to (NMMoodEmoji, V3MoodSlider)."""
    spec = get_mood(level)
    p1, p2 = _angle_endpoints(rect, angle)
    grad = QLinearGradient(p1, p2)
    grad.setColorAt(0.0, QColor(spec["from"]))
    grad.setColorAt(1.0, QColor(spec["to"]))
    return grad


# Atajos numéricos de SPACE/RADIUS v3 expuestos para componentes nuevos
V3_SP = V3_SPACE
V3_RD = V3_RADIUS


# ── Shell background (gradiente + 3 blobs radiales spec v3) ──────────────────


def paint_shell_background(painter, rect: QRectF, modo: str):
    """Pinta el fondo cockpit: plano, clínico y sin blobs decorativos."""
    is_dark = "dark" in norm_modo(modo)

    # Gradiente muy bajo entre canvas y sidebar, como el mockup desktop.
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectMode)
    if is_dark:
        bg_top = v3c("bgAlt", modo)
        bg_bot = v3c("bg", modo)
    else:
        bg_top = v3c("bg", modo)
        bg_bot = v3c("bgAlt", modo)
    grad.setColorAt(0.0, bg_top)
    grad.setColorAt(1.0, bg_bot)
    painter.fillRect(rect, QBrush(grad))


import random as _random

_SESSION_COLORS = {
    # Aura/glow de sesión: una opción "fría" (acento primario) y una "cálida"
    # (acento secundario). Los keys compatibility "cyan"/"violet" se mantienen para
    # compat con consumidores que ya guardan la variante por nombre.
    # Valores SIEMPRE desde tokens runtime — nunca hex aproximados.
    "dark": {"cyan": V3_DARK["accent"], "violet": V3_DARK["amber"]},  # aqua / oro
    "light": {"cyan": V3_LIGHT["primary"], "violet": V3_LIGHT["accent"]},  # sage / terracota
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


# ── Densidades por producto ─────────────────────────────────────────────────────
# Suite usa la escala comfortable como default de componentes. Hub suma una
# variante professional compact sólo sobre su QMainWindow, sin tocar QApplication
# ni agrandar controles compartidos.

HUB_DENSITY_OBJECT_NAME = "HubMain"
SUITE_DENSITY_ID = "suite_comfortable"
HUB_DENSITY_ID = "hub_professional_compact"


def visual_density_tokens(density_id: str) -> dict:
    """Devuelve una copia de la densidad visual declarada en shared.theme."""
    fallback = VISUAL_DENSITIES[SUITE_DENSITY_ID]
    return dict(VISUAL_DENSITIES.get(density_id, fallback))


def product_density_tokens(product: str) -> dict:
    """Densidad por producto: Suite comfortable, Hub professional compact."""
    key = HUB_DENSITY_ID if str(product).lower() == "hub" else SUITE_DENSITY_ID
    return visual_density_tokens(key)


def hub_density_qss(object_name: str = HUB_DENSITY_OBJECT_NAME) -> str:
    """QSS de densidad reducida para el Hub, scoped al QMainWindow."""
    d = product_density_tokens("hub")
    sel = f"#{object_name}"
    radius = max(4, int(d["control_height"]) // 2)
    compact_radius = max(4, int(d["control_compact_height"]) // 2)
    badge_radius = max(4, int(d["badge_height"]) // 2)
    chip_radius = max(4, int(d["chip_height"]) // 2)
    return (
        f"{sel} QPushButton {{ min-height: {d['button_height']}px; "
        f"padding: {d['pad_y']}px {d['pad_x']}px; border-radius: {radius}px; }}\n"
        f'{sel} QPushButton[variant="compact"] {{ min-height: {d["button_compact_height"]}px; '
        f"padding: 2px {d['pad_x']}px; border-radius: {compact_radius}px; }}\n"
        f"{sel} QLineEdit, {sel} QComboBox {{ min-height: {d['input_height']}px; "
        f"padding: {d['pad_y']}px {d['pad_x']}px; border-radius: {radius}px; }}\n"
        f"{sel} QTextEdit, {sel} QPlainTextEdit {{ min-height: {d['textarea_min_height']}px; "
        f"padding: {d['pad_y'] + 2}px {d['pad_x']}px; border-radius: {radius}px; }}\n"
        f"{sel} QLineEdit:focus, {sel} QTextEdit:focus, {sel} QPlainTextEdit:focus, "
        f"{sel} QComboBox:focus {{ border-width: {d['focus_border_width']}px; }}\n"
        f"{sel} QTabBar::tab {{ min-height: {d['tab_height']}px; "
        f"padding: 2px {d['tab_pad_x']}px; margin: 2px 2px; }}\n"
        f'{sel} QPushButton[role="subtab"], {sel} QPushButton[variant="subtab"] {{ '
        f"min-height: {d['subtab_height']}px; padding: 2px {d['tab_pad_x']}px; "
        f"border-radius: {compact_radius}px; }}\n"
        f'{sel} QPushButton[role="filter"], {sel} QPushButton[variant="filter"] {{ '
        f"min-height: {d['filter_height']}px; padding: 2px {d['tab_pad_x']}px; "
        f"border-radius: {compact_radius}px; }}\n"
        f'{sel} QLabel[role="badge"], {sel} QLabel[variant="badge"] {{ '
        f"min-height: {d['badge_height']}px; padding: 0 {d['badge_pad_x']}px; "
        f"border-radius: {badge_radius}px; }}\n"
        f'{sel} QLabel[role="chip"], {sel} QLabel[variant="chip"] {{ '
        f"min-height: {d['chip_height']}px; padding: 0 {d['badge_pad_x']}px; "
        f"border-radius: {chip_radius}px; }}\n"
        f"{sel} QListView::item, {sel} QListWidget::item {{ "
        f"padding: {d['row_padding_y']}px {d['pad_x']}px; }}\n"
        f"{sel} QScrollBar:vertical {{ width: {d['scrollbar_width']}px; }}\n"
        f"{sel} QScrollBar:horizontal {{ height: {d['scrollbar_width']}px; }}\n"
    )


def apply_hub_density(main_window, object_name: str = HUB_DENSITY_OBJECT_NAME) -> None:
    """Aplica la densidad reducida del Hub a un QMainWindow puntual.

    * Setea ``objectName`` si no estaba seteado, para que el QSS scoped
      tenga efecto.
    * Suma el QSS de densidad al stylesheet existente — no reemplaza.

    Args:
        main_window: QMainWindow del Hub (idealmente ``HubMainWindow``).
        object_name: override del selector (no se usa en producción).

    Idempotente: aplicarlo dos veces no duplica estilos visibles porque las
    reglas se sobreescriben con el mismo valor. No toca QApplication.
    """
    if main_window is None:
        return
    try:
        if not main_window.objectName():
            main_window.setObjectName(object_name)
        existing = main_window.styleSheet() or ""
        extra = hub_density_qss(main_window.objectName() or object_name)
        if extra in existing:
            return
        main_window.setStyleSheet(existing + ("\n" if existing else "") + extra)
    except Exception:
        _log.debug("apply_hub_density: no aplicado (best-effort)")


# ── Helpers convenientes del runtime spec §2.5 ────────────────────────────────────
# Aplican QGraphicsDropShadowEffect directamente sobre un widget.
# No retornan nada — efectos secundarios intencionales.


def shadow_sm(widget, dark: bool = False) -> None:
    """Sombra sutil (card plana, elevación mínima)."""
    e = QGraphicsDropShadowEffect(widget)
    e.setBlurRadius(12)
    e.setOffset(0, 4)
    e.setColor(QColor(0, 0, 0, 76) if dark else QColor(28, 34, 24, 10))
    widget.setGraphicsEffect(e)


def shadow_md(widget, dark: bool = False) -> None:
    """Sombra media (cards primarios, popovers)."""
    e = QGraphicsDropShadowEffect(widget)
    e.setBlurRadius(32)
    e.setOffset(0, 12)
    e.setColor(QColor(0, 0, 0, 90) if dark else QColor(28, 34, 24, 18))
    widget.setGraphicsEffect(e)


def shadow_lg(widget, dark: bool = False) -> None:
    """Sombra grande (modales, NMCardElev)."""
    e = QGraphicsDropShadowEffect(widget)
    e.setBlurRadius(64)
    e.setOffset(0, 24)
    e.setColor(QColor(0, 0, 0, 130) if dark else QColor(28, 34, 24, 26))
    widget.setGraphicsEffect(e)


def eyebrow_font() -> QFont:
    """QFont para eyebrows: 11px semibold con letter-spacing.

    Lenguaje visual del polish Suite+Hub: eyebrows en semibold tracked (frame
    del prototipo: 11px / weight 600 / tracking ~.12em). Se fija el peso fuera
    del clamp de ``_adn_clamped_weight`` (que baja a medium fuera de tokens de
    título) porque los eyebrows sí deben leerse semibold.
    """
    f = v3_font("size_eyebrow", TYPOGRAPHY["weight_semibold"])
    f.setWeight(QFont.Weight(TYPOGRAPHY["weight_semibold"]))
    f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 116)
    return f


def eyebrow_style(modo: str) -> str:
    """Stylesheet inline para QLabel eyebrow (sin fondo, color MUTE)."""
    return (
        f"color: {C('mute', modo)}; background: transparent; "
        f"font-size: {TYPOGRAPHY.get('size_eyebrow', 11)}px; "
        f"font-weight: {TYPOGRAPHY.get('weight_semibold', 600)};"
    )


def nm_separator_style(modo: str) -> str:
    """Stylesheet para QFrame separador 1px horizontal (LINE token)."""
    c = colors(norm_modo(modo))
    border_color = c.get("border_solid", c.get("borderSolid", c.get("border", "#E0D8C8")))
    return f"background: {border_color}; max-height: 1px; border: none;"
