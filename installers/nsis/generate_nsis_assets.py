"""Generate NeuroMood NSIS Modern UI 2 BMP assets — identidad V6 (Indigo Profundo).

Produce los bitmaps de marca que MUI2 compila dentro de los instaladores:
    - <app>_welcome.bmp  (164x314)  panel lateral de las paginas Welcome/Finish
    - <app>_header.bmp   (150x57)   franja superior de las paginas internas

La identidad lee los tokens ADN en runtime desde `shared/theme.py` (V3_DARK,
tema "Indigo Profundo"): lienzo #07091A, lavanda #A99CFF (Suite) y aqua
#5EE0C7 (Hub). NUNCA hardcodear los hex aca: cambiar tokens y reejecutar.
Se compone la marca real (cerebro de nodos de colores + wordmark "NeuroMood")
desde `assets/logos-light.png` para paridad con la app.

Salida: installers/nsis/assets/  (referida por common.nsh).
Reejecutar tras cualquier cambio de marca:
    .venv\\Scripts\\python.exe installers\\nsis\\generate_nsis_assets.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# F6 "Índigo Calmado": los colores se IMPORTAN de la fuente única de tokens
# (shared/theme.py es data pura, sin dependencia Qt). Si cambia la paleta,
# los BMPs se regeneran solos en el build — nunca más desfasados.
from shared.theme import V3_DARK  # noqa: E402

OUT = ROOT / "installers" / "nsis" / "assets"
FONTS = ROOT / "assets" / "fonts"
LOGO_SRC = ROOT / "assets" / "logos-light.png"  # cerebro a color + "NeuroMood" blanco/teal

WELCOME_SIZE = (164, 314)
HEADER_SIZE = (150, 57)


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ── Tokens DARK (instaladores siempre dark, igual que stylesheet_installer) ───
INK = V3_DARK["text"]
INK_MUTED = V3_DARK["textMuted"]
CANVAS = _hex(V3_DARK["bg"])
SURFACE = _hex(V3_DARK["surface"])
SURFACE2 = _hex(V3_DARK["surface2"])
SIDEBAR = _hex(V3_DARK["bgSidebar"])
BORDER = _hex(V3_DARK["borderSolid"])


def _glow_de(accent_hex: str) -> tuple[int, int, int]:
    """Halo = el propio acento atenuado (70%) — siempre coherente con tokens."""
    r, g, b = _hex(accent_hex)
    return (int(r * 0.7), int(g * 0.7), int(b * 0.7))


SUITE = {
    "accent": V3_DARK["primary"],   # lavanda
    "accent_rgb": _hex(V3_DARK["primary"]),
    "glow": _glow_de(V3_DARK["primary"]),
    "eyebrow": "SUITE",
    "app_label": "NeuroMood Suite",
    "desc1": "Tu espacio personal",
    "desc2": "de bienestar.",
}
HUB = {
    "accent": V3_DARK["accent"],   # aqua
    "accent_rgb": _hex(V3_DARK["accent"]),
    "glow": _glow_de(V3_DARK["accent"]),
    "eyebrow": "HUB",
    "app_label": "NeuroMood Hub",
    "desc1": "La plataforma clínica",
    "desc2": "para profesionales.",
}


# ── Fuentes (Manrope/Newsreader bundle, fallback a Segoe) ──────────────────────
def _font(family: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "sans": ["Manrope-SemiBold.ttf"],
        "sans_bold": ["Manrope-Bold.ttf"],
        "sans_med": ["Manrope-Medium.ttf"],
        "serif": ["Newsreader-SemiBold.ttf", "Newsreader-Medium.ttf"],
    }[family]
    for name in candidates:
        p = FONTS / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass
    for sys_font in ("segoeui.ttf", "segoeuib.ttf", "arial.ttf"):
        p = Path("C:/Windows/Fonts") / sys_font
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass
    return ImageFont.load_default()


def _vgradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, top)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = col
    return img


def _radial_glow(size: tuple[int, int], center: tuple[int, int], radius: int,
                 color: tuple[int, int, int], strength: float = 0.55) -> Image.Image:
    """Devuelve una capa RGBA con un halo radial suave para dar profundidad."""
    w, h = size
    layer = Image.new("L", size, 0)
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=int(255 * strength))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.6))
    glow = Image.new("RGBA", size, color + (0,))
    glow.putalpha(layer)
    return glow


def _brain_mark(target_h: int) -> Image.Image:
    """Recorta el cerebro de nodos de colores del wordmark y lo escala a target_h."""
    logo = Image.open(LOGO_SRC).convert("RGBA")
    # El cerebro vive en cols ~15-361, rows ~25-318 del asset 1536x326.
    crop = logo.crop((6, 18, 372, 326))
    ratio = target_h / crop.height
    return crop.resize((max(1, int(crop.width * ratio)), target_h), Image.LANCZOS)


def _draw_wordmark(draw: ImageDraw.ImageDraw, xy: tuple[int, int], accent: str, size: int) -> None:
    """Escribe 'Neuro' (off-white) + 'Mood' (accent) en una sola linea."""
    x, y = xy
    f = _font("sans_bold", size)
    draw.text((x, y), "Neuro", font=f, fill=_hex(INK))
    w = draw.textlength("Neuro", font=f)
    draw.text((x + w, y), "Mood", font=f, fill=_hex(accent))


def _welcome(theme: dict, path: Path) -> None:
    img = _vgradient(WELCOME_SIZE, CANVAS, SURFACE).convert("RGBA")
    accent_rgb = theme["accent_rgb"]

    # Halos calmados (F6 ADN: antes 0.45/0.20 — "nada brilla").
    img.alpha_composite(_radial_glow(WELCOME_SIZE, (82, 90), 100, theme["glow"], 0.22))
    img.alpha_composite(_radial_glow(WELCOME_SIZE, (150, 314), 110, theme["glow"], 0.10))

    draw = ImageDraw.Draw(img)

    # Cerebro de nodos — centrado, tamaño prominente.
    brain = _brain_mark(56)
    brain_x = (WELCOME_SIZE[0] - brain.width) // 2
    img.alpha_composite(brain, (brain_x, 28))

    # Wordmark centrado bajo el cerebro.
    f_wm = _font("sans_bold", 15)
    neuro_w = int(draw.textlength("Neuro", font=f_wm))
    mood_w = int(draw.textlength("Mood", font=f_wm))
    total_w = neuro_w + mood_w
    wm_x = (WELCOME_SIZE[0] - total_w) // 2
    wm_y = 94
    draw.text((wm_x, wm_y), "Neuro", font=f_wm, fill=_hex(INK))
    draw.text((wm_x + neuro_w, wm_y), "Mood", font=f_wm, fill=_hex(theme["accent"]))

    # Eyebrow "SUITE" o "HUB" — centrado, tracking amplio.
    eb = _font("sans_bold", 8)
    eyebrow_txt = theme["eyebrow"]
    ew = int(draw.textlength(eyebrow_txt, font=eb))
    _spaced(draw, ((WELCOME_SIZE[0] - ew - len(eyebrow_txt) * 2) // 2, 114),
            eyebrow_txt, eb, accent_rgb, 2)

    # Línea separadora de acento.
    line_w = 40
    line_x = (WELCOME_SIZE[0] - line_w) // 2
    draw.line([line_x, 136, line_x + line_w, 136], fill=accent_rgb, width=1)

    # Descripción de la aplicación — sin slogans inventados.
    desc1 = _font("sans_med", 11)
    desc2 = _font("serif", 13)
    d1_w = int(draw.textlength(theme["desc1"], font=desc1))
    d2_w = int(draw.textlength(theme["desc2"], font=desc2))
    draw.text(((WELCOME_SIZE[0] - d1_w) // 2, 152), theme["desc1"],
              font=desc1, fill=_hex(INK_MUTED))
    draw.text(((WELCOME_SIZE[0] - d2_w) // 2, 170), theme["desc2"],
              font=desc2, fill=_hex(INK))

    # Línea de versión al pie (discreta).
    ver = _font("sans_med", 8)
    ver_txt = "neuromood.app"
    ver_w = int(draw.textlength(ver_txt, font=ver))
    draw.text(((WELCOME_SIZE[0] - ver_w) // 2, 292), ver_txt,
              font=ver, fill=BORDER)

    img.convert("RGB").save(path)


def _header(theme: dict, path: Path) -> None:
    img = _vgradient(HEADER_SIZE, SIDEBAR, CANVAS).convert("RGBA")
    img.alpha_composite(_radial_glow(HEADER_SIZE, (HEADER_SIZE[0] - 20, 28), 46, theme["glow"], 0.18))
    draw = ImageDraw.Draw(img)
    # Cerebro a la derecha (MUI_HEADERIMAGE_RIGHT).
    brain = _brain_mark(36)
    brain_y = (HEADER_SIZE[1] - brain.height) // 2
    img.alpha_composite(brain, (HEADER_SIZE[0] - brain.width - 6, brain_y))
    # Wordmark a la izquierda.
    f = _font("sans_bold", 13)
    neuro_w = int(draw.textlength("Neuro", font=f))
    draw.text((10, (HEADER_SIZE[1] - 16) // 2), "Neuro", font=f, fill=_hex(INK))
    draw.text((10 + neuro_w, (HEADER_SIZE[1] - 16) // 2), "Mood", font=f, fill=_hex(theme["accent"]))
    img.convert("RGB").save(path)


# ── Helpers de dibujo ──────────────────────────────────────────────────────────
def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _spaced(draw, xy, text, font, fill, spacing):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + spacing


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _welcome(SUITE, OUT / "suite_welcome.bmp")
    _header(SUITE, OUT / "suite_header.bmp")
    _welcome(HUB, OUT / "hub_welcome.bmp")
    _header(HUB, OUT / "hub_header.bmp")
    print(f"Generated NSIS assets (V6 Indigo Profundo) in {OUT}")
    for f in sorted(OUT.glob("*.bmp")):
        print(f"  {f.name}  ({Image.open(f).size[0]}x{Image.open(f).size[1]})")


if __name__ == "__main__":
    main()
