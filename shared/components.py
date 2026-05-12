"""
NeuroMood Hybrid Unified Components
Versión: 2.0 — Mayo 2026
Paleta dual: dark_hybrid + light_hybrid con soporte de ThemeManager
"""

import customtkinter as ctk
from PIL import Image
import os
import sys

# ── Importación robusta (frozen / dev / con o sin shared/ en sys.path) ──
try:
    from shared.theme import (
        COLORS, TYPOGRAPHY, LAYOUT, get_colors, get_gradient, TRANSITIONS,
    )
except ImportError:
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from theme import (
        COLORS, TYPOGRAPHY, LAYOUT, get_colors, get_gradient, TRANSITIONS,
    )


# ── Utilidades de gradiente (usadas por módulos con canvas circular) ──

def interpolate_color(c1: str, c2: str, t: float) -> str:
    """Interpolación lineal entre dos colores hex. t=0 → c1, t=1 → c2."""
    c1 = c1.lstrip("#")
    c2 = c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _blend_to_bg(color_hex: str, bg_hex: str, alpha: float) -> str:
    """Mezcla color_hex sobre bg_hex con opacidad alpha (0-1)."""
    return interpolate_color(bg_hex, color_hex, alpha)


def draw_gradient_arc(canvas, cx: int, cy: int, r: int, width: int,
                      start_deg: float, extent_deg: float,
                      color_a: str, color_b: str,
                      tag: str = "gradient_arc", segments: int = 72):
    """Dibuja un arco con gradiente de color_a a color_b sobre un tkinter Canvas.

    Args:
        canvas: tkinter Canvas widget.
        cx, cy: centro del arco en píxeles.
        r: radio en píxeles.
        width: grosor del arco en píxeles.
        start_deg: ángulo inicial (0 = este, positivo = sentido antihorario).
        extent_deg: extensión angular en grados. 0 no dibuja nada.
        color_a: color hex del inicio del gradiente.
        color_b: color hex del final del gradiente.
        tag: tag de Canvas para borrado selectivo.
        segments: número de segmentos (más = más suave, más lento).
    """
    canvas.delete(tag)
    if extent_deg <= 0:
        return
    seg_extent = extent_deg / segments
    x0, y0 = cx - r, cy - r
    x1, y1 = cx + r, cy + r
    for i in range(segments):
        t = i / max(segments - 1, 1)
        color = interpolate_color(color_a, color_b, t)
        angle = start_deg + i * seg_extent
        canvas.create_arc(
            x0, y0, x1, y1,
            start=angle, extent=seg_extent + 0.5,
            style="arc", width=width, outline=color,
            tags=tag,
        )


def draw_glow_arc(canvas, cx: int, cy: int, r: int,
                  start_deg: float, extent_deg: float,
                  glow_color: str, bg_color: str,
                  tag: str = "glow_arc"):
    """Dibuja un halo difuso debajo del arco principal.

    Usa dos arcos más gruesos con el color mezclado sobre el fondo.
    Llama antes de draw_gradient_arc para que quede debajo.
    """
    canvas.delete(tag)
    if extent_deg <= 0:
        return
    for thickness, alpha in ((16, 0.15), (10, 0.25)):
        blended = _blend_to_bg(glow_color, bg_color, alpha)
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r
        canvas.create_arc(
            x0, y0, x1, y1,
            start=start_deg, extent=extent_deg,
            style="arc", width=thickness, outline=blended,
            tags=tag,
        )


# ── CTK-safe: rgba de theme_hybrid convertidas a hex blended ─────────
# tkinter no acepta rgba(...); estos valores se calcularon blending
# sobre el fondo predominante de cada modo.
_CTK_SAFE = {
    "dark_hybrid": {
        # rgba(240,244,255,0.72) on #0e1421
        "text_secondary":  "#B1B5C1",
        # rgba(240,244,255,0.45) on #0e1421
        "text_tertiary":   "#747985",
        # rgba(255,255,255,0.10) on #050911
        "border":          "#1E2229",
        # rgba(0,212,200,0.35) on #0e1421
        "border_accent":   "#09575B",
        # rgba(0,212,200,0.25) on #0e1421
        "accent_glow":     "#0B444B",
        # rgba(124,91,242,0.25) on #0e1421
        "violet_glow":     "#2A2655",
        # rgba(14,20,33,0.72) → solid equivalente
        "bg_glass":        "#0E1421",
        # alias de bg_overlay (no existe en theme_hybrid)
        "bg_hover":        "#1A2340",
        # alias de bg_elevated
        "bg_list_item":    "#141C2E",
        "accent_subtle":   "#0B444B",
    },
    "light_hybrid": {
        # ya hex en theme_hybrid — se repite para uniformidad de acceso
        "text_secondary":  "#334155",
        "text_tertiary":   "#64748B",
        # rgba(15,23,42,0.10) on #f8fafc
        "border":          "#E1E3E7",
        # rgba(8,145,178,0.40) on #ffffff
        "border_accent":   "#9CD3E0",
        # rgba(8,145,178,0.20) on #ffffff
        "accent_glow":     "#CEE9F0",
        # rgba(124,58,237,0.15) on #ffffff
        "violet_glow":     "#EBE1FC",
        # rgba(255,255,255,0.75) → solid equivalente
        "bg_glass":        "#FFFFFF",
        # alias de bg_overlay
        "bg_hover":        "#DDE6F0",
        # alias de bg_elevated
        "bg_list_item":    "#E8EEF6",
        "accent_subtle":   "#CEE9F0",
    },
}


def _c(modo: str, key: str) -> str:
    """Devuelve color CTK-compatible: si theme_hybrid retorna rgba usa _CTK_SAFE."""
    colores = get_colors(modo)
    val = colores.get(key)
    if val is None or (isinstance(val, str) and val.startswith("rgba")):
        return _CTK_SAFE.get(modo, {}).get(key, "#888888")
    return val


def _norm_modo(modo: str) -> str:
    """Normaliza: 'dark' → 'dark_hybrid', 'light' → 'light_hybrid'."""
    if modo == "dark":
        return "dark_hybrid"
    if modo == "light":
        return "light_hybrid"
    return modo if modo in ("dark_hybrid", "light_hybrid") else "dark_hybrid"


# ── Utilidades de recurso ─────────────────────────────────────────────

def obtener_ruta_recurso(nombre_archivo: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre_archivo)


def obtener_icono_solido() -> str:
    return obtener_ruta_recurso("NM_icon.ico")


# ── Win32: congelado de ventana ───────────────────────────────────────

def _freeze_window(window) -> int:
    """Pausa el repintado para evitar deformación durante rebuild. Devuelve HWND."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()
        ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 0, 0)
        return hwnd
    except Exception:
        return 0


def _unfreeze_window(hwnd: int):
    """Reactiva el repintado y fuerza redibujado completo."""
    if not hwnd:
        return
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 1, 0)
        ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x0185)
    except Exception:
        pass


def _es_windows_11() -> bool:
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:
        return False


def _aplicar_acento_win10(hwnd, bg_hex: str):
    """
    Windows 10: colorea la barra de título vía SetWindowCompositionAttribute.
    ACCENT_ENABLE_GRADIENT (AccentState=1) aplica un color sólido al backdrop DWM.
    El área cliente queda cubierta por los widgets opacos de CTk, por lo que
    el efecto solo es visible en la barra de título y el marco.
    """
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

        accent = ACCENT_POLICY(
            AccentState=1,   # ACCENT_ENABLE_GRADIENT — color sólido
            AccentFlags=2,
            GradientColor=int(color_abgr.value),
        )
        data = WINCOMPATTRDATA(
            Attribute=19,    # WCA_ACCENT_POLICY
            pData=ctypes.cast(ctypes.addressof(accent), ctypes.c_void_p),
            ulDataSize=ctypes.sizeof(accent),
        )
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception:
        pass


# ── Caption bar DWM ──────────────────────────────────────────────────

def aplicar_captionbar(window, modo: str):
    modo = _norm_modo(modo)
    bg = "#050911" if "dark" in modo else "#f8fafc"
    fg = "#f0f4ff" if "dark" in modo else "#0f172a"
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()

        # dark / light toggle — Win10 build 17763+ y Win11
        dark_val = ctypes.c_int(1 if "dark" in modo else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_val), 4)
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark_val), 4)
        except Exception:
            pass

        # color personalizado
        r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        color = ctypes.c_uint(r | (g << 8) | (b << 16))
        if _es_windows_11():
            # DWMWA_CAPTION_COLOR (attr 35) — solo Win11
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        else:
            # Windows 10: SetWindowCompositionAttribute como fallback
            _aplicar_acento_win10(hwnd, bg)

        # fuerza recalculo de NC área (SWP_FRAMECHANGED + flags de posición)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
        if not _es_windows_11():
            ctypes.windll.user32.UpdateWindow(hwnd)
    except Exception:
        pass
    try:
        window.wm_attributes("-titlebarcolor", bg)
        try:
            window.wm_attributes("-titlebartext", fg)
        except Exception:
            pass
    except Exception:
        pass


def aplicar_captionbar_flush(window, modo: str):
    """Caption bar con flush DWM completo — usar en toggle explícito post-unfreeze."""
    aplicar_captionbar(window, modo)
    try:
        window.update_idletasks()
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.dwmapi.DwmFlush()
    except Exception:
        pass


def _recolorear_logo_light(img):
    """Invierte píxeles blancos del logo a oscuro para el tema claro."""
    img = img.convert("RGBA")
    data = img.getdata()
    nueva = []
    for r, g, b, a in data:
        if r > 200 and g > 200 and b > 200 and a > 0:
            nueva.append((5, 9, 17, a))
        else:
            nueva.append((r, g, b, a))
    img.putdata(nueva)
    return img


# ── ThemeManager ──────────────────────────────────────────────────────

class ThemeManager:
    """
    Gestiona el cambio de tema en toda la ventana.

    Uso:
        tm = ThemeManager(root, "dark_hybrid")
        tm.register_widget(mi_header)
        tm.register_widget(mi_card)
        tm.switch_mode("light_hybrid")
    """

    def __init__(self, root, initial_mode: str = "dark_hybrid"):
        self.root = root
        self.current_mode = _norm_modo(initial_mode)
        self._widgets: list = []

    def register_widget(self, widget):
        if widget not in self._widgets:
            self._widgets.append(widget)

    def unregister_widget(self, widget):
        if widget in self._widgets:
            self._widgets.remove(widget)

    def switch_mode(self, new_mode: str):
        new_mode = _norm_modo(new_mode)
        if new_mode == self.current_mode:
            return

        hwnd = _freeze_window(self.root)
        self.current_mode = new_mode
        colores = get_colors(new_mode)

        for widget in list(self._widgets):
            try:
                if hasattr(widget, "apply_theme"):
                    widget.apply_theme(new_mode, colores)
                elif isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=colores["bg_surface"])
                elif isinstance(widget, ctk.CTkButton):
                    widget.configure(
                        fg_color=_c(new_mode, "accent"),
                        hover_color=colores["accent_hover"],
                        text_color=colores["text_on_accent"],
                    )
                elif isinstance(widget, ctk.CTkLabel):
                    widget.configure(text_color=colores["text_primary"])
            except Exception:
                pass

        _unfreeze_window(hwnd)
        aplicar_captionbar_flush(self.root, new_mode)
        self.root.update_idletasks()


# ── HeaderFrame ───────────────────────────────────────────────────────

class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, titulo: str, subtitulo: str, modo: str = "dark_hybrid",
                 on_toggle_modo=None, theme_manager=None, **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        super().__init__(
            master,
            fg_color=colores["bg_primary"],
            height=LAYOUT["header_height"],
            corner_radius=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.modo = modo
        self.on_toggle_modo = on_toggle_modo
        self.theme_manager = theme_manager

        self._contenedor = ctk.CTkFrame(self, fg_color="transparent")
        self._contenedor.pack(fill="x", padx=LAYOUT["padding_container"], pady=12)

        # Logo
        self._logo_label = None
        self._logo_img_original = None
        try:
            logo_path = obtener_ruta_recurso("LOGO.png")
            self._logo_img_original = Image.open(logo_path)
            self._logo_label = ctk.CTkLabel(self._contenedor, image=None, text="")
            self._logo_label.pack(side="left", padx=(0, 16))
            self._actualizar_logo(modo)
        except Exception:
            pass

        # Texto
        self._texto_frame = ctk.CTkFrame(self._contenedor, fg_color="transparent")
        self._texto_frame.pack(side="left", fill="y")

        self._lbl_titulo = ctk.CTkLabel(
            self._texto_frame,
            text=titulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=colores["text_primary"],
        )
        self._lbl_titulo.pack(anchor="w")

        self._lbl_subtitulo = ctk.CTkLabel(
            self._texto_frame,
            text=subtitulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=_c(modo, "text_tertiary"),
        )
        self._lbl_subtitulo.pack(anchor="w")

        # Botón toggle
        self.btn_modo = None
        if on_toggle_modo or theme_manager:
            self.btn_modo = self._crear_boton_toggle(modo, colores)
            self.btn_modo.pack(side="right", padx=(8, 0))

        # Separador inferior
        self._separador = ctk.CTkFrame(
            self, height=1, fg_color=_c(modo, "border"), corner_radius=0
        )
        self._separador.pack(fill="x", side="bottom")

        # Caption bar con múltiples delays (necesario para que DWM procese la cola Win32)
        self._aplicar_caption_con_delay(modo)

    # ── internals ──

    def _actualizar_logo(self, modo: str):
        if not self._logo_label or not self._logo_img_original:
            return
        ratio = self._logo_img_original.width / self._logo_img_original.height
        alto = 44
        img = (
            _recolorear_logo_light(self._logo_img_original.copy())
            if "light" in modo
            else self._logo_img_original.copy()
        )
        logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(int(alto * ratio), alto))
        self._logo_label.configure(image=logo_ctk)
        self._logo_label._img_ref = logo_ctk  # evita GC

    def _crear_boton_toggle(self, modo: str, colores: dict) -> ctk.CTkButton:
        icono = "☀" if "dark" in modo else "☾"
        if "light" in modo:
            fg, hover, txt = colores["accent"], colores["accent_hover"], colores["text_on_accent"]
        else:
            fg, hover, txt = _c(modo, "bg_hover"), colores["accent"], colores["text_primary"]
        return ctk.CTkButton(
            self._contenedor,
            text=icono,
            width=50,
            height=36,
            corner_radius=LAYOUT["radius_button"],
            fg_color=fg,
            hover_color=hover,
            text_color=txt,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
            command=self._on_toggle,
        )

    def _on_toggle(self):
        if self.theme_manager:
            new_mode = "light_hybrid" if "dark" in self.modo else "dark_hybrid"
            self.theme_manager.switch_mode(new_mode)
        elif self.on_toggle_modo:
            self.on_toggle_modo()

    def _aplicar_caption_con_delay(self, modo: str):
        try:
            _win = self.winfo_toplevel()
            aplicar_captionbar(_win, modo)
            _win.after(0,   lambda: aplicar_captionbar(_win, modo))
            _win.after(100, lambda: aplicar_captionbar(_win, modo))
            _win.after(300, lambda: aplicar_captionbar(_win, modo))
            _win.after(600, lambda: aplicar_captionbar(_win, modo))
        except Exception:
            pass

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        self.modo = new_mode
        self.configure(fg_color=colores["bg_primary"])
        self._contenedor.configure(fg_color="transparent")
        self._texto_frame.configure(fg_color="transparent")
        self._lbl_titulo.configure(text_color=colores["text_primary"])
        self._lbl_subtitulo.configure(text_color=_c(new_mode, "text_tertiary"))
        self._separador.configure(fg_color=_c(new_mode, "border"))
        self._actualizar_logo(new_mode)
        if self.btn_modo:
            icono = "☀" if "dark" in new_mode else "☾"
            if "light" in new_mode:
                fg, hover, txt = colores["accent"], colores["accent_hover"], colores["text_on_accent"]
            else:
                fg, hover, txt = _c(new_mode, "bg_hover"), colores["accent"], colores["text_primary"]
            self.btn_modo.configure(text=icono, fg_color=fg, hover_color=hover, text_color=txt)
        self._aplicar_caption_con_delay(new_mode)


# ── CardFrame ─────────────────────────────────────────────────────────

class CardFrame(ctk.CTkFrame):
    def __init__(self, master, modo: str = "dark_hybrid", destacada: bool = False, **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        self._destacada = destacada
        border_color = _c(modo, "border_accent") if destacada else _c(modo, "border")
        border_width = LAYOUT["border_accent_width"] if destacada else LAYOUT["border_card_width"]
        super().__init__(
            master,
            fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_color=border_color,
            border_width=border_width,
            **kwargs,
        )

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        border_color = _c(new_mode, "border_accent") if self._destacada else _c(new_mode, "border")
        self.configure(fg_color=colores["bg_surface"], border_color=border_color)


# ── BotonPrimario ─────────────────────────────────────────────────────

class BotonPrimario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        defaults = {
            "fg_color":      colores["accent"],
            "hover_color":   colores["accent_hover"],
            "text_color":    colores["text_on_accent"],
            "corner_radius": LAYOUT["radius_button"],
            "font":          (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            "height":        LAYOUT["min_touch_target"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        self.configure(
            fg_color=colores["accent"],
            hover_color=colores["accent_hover"],
            text_color=colores["text_on_accent"],
        )


# ── BotonSecundario ───────────────────────────────────────────────────

class BotonSecundario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        if "light" in modo:
            defaults = {
                "fg_color":      colores["warning"],
                "hover_color":   "#B06830",
                "text_color":    colores["text_on_accent"],
                "border_width":  0,
                "corner_radius": LAYOUT["radius_button"],
                "font":          (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                "height":        LAYOUT["min_touch_target"],
            }
        else:
            defaults = {
                "fg_color":      "transparent",
                "hover_color":   _c(modo, "bg_hover"),
                "text_color":    colores["accent"],
                "border_color":  colores["accent"],
                "border_width":  LAYOUT["border_button_width"],
                "corner_radius": LAYOUT["radius_button"],
                "font":          (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                "height":        LAYOUT["min_touch_target"],
            }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        if "light" in new_mode:
            self.configure(
                fg_color=colores["warning"],
                hover_color="#B06830",
                text_color=colores["text_on_accent"],
                border_width=0,
            )
        else:
            self.configure(
                fg_color="transparent",
                hover_color=_c(new_mode, "bg_hover"),
                text_color=colores["accent"],
                border_color=colores["accent"],
                border_width=LAYOUT["border_button_width"],
            )


# ── BadgeLabel ────────────────────────────────────────────────────────

class BadgeLabel(ctk.CTkLabel):
    def __init__(self, master, texto: str, color: str = "accent",
                 modo: str = "dark_hybrid", **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        self._color_key = color
        color_texto = colores.get(color, colores["accent"])
        if isinstance(color_texto, str) and color_texto.startswith("rgba"):
            color_texto = _c(modo, color)
        super().__init__(
            master,
            text=texto,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=color_texto,
            fg_color=_c(modo, "accent_glow"),
            corner_radius=LAYOUT["radius_badge"],
            padx=12,
            pady=4,
            **kwargs,
        )

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        color_texto = colores.get(self._color_key, colores["accent"])
        if isinstance(color_texto, str) and color_texto.startswith("rgba"):
            color_texto = _c(new_mode, self._color_key)
        self.configure(text_color=color_texto, fg_color=_c(new_mode, "accent_glow"))


# ── InputTexto ────────────────────────────────────────────────────────

class InputTexto(ctk.CTkEntry):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        defaults = {
            "fg_color":               colores["bg_input"],
            "border_color":           _c(modo, "border"),
            "text_color":             colores["text_primary"],
            "placeholder_text_color": _c(modo, "text_tertiary"),
            "corner_radius":          LAYOUT["radius_input"],
            "font":                   (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            "height":                 LAYOUT["min_touch_target"],
            "border_width":           LAYOUT["border_width"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        self.configure(
            fg_color=colores["bg_input"],
            border_color=_c(new_mode, "border"),
            text_color=colores["text_primary"],
            placeholder_text_color=_c(new_mode, "text_tertiary"),
        )


# ── AreaTexto ─────────────────────────────────────────────────────────

class AreaTexto(ctk.CTkTextbox):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        modo = _norm_modo(modo)
        colores = get_colors(modo)
        defaults = {
            "fg_color":                     colores["bg_input"],
            "border_color":                 _c(modo, "border"),
            "text_color":                   colores["text_primary"],
            "corner_radius":                LAYOUT["radius_input"],
            "font":                         (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            "border_width":                 LAYOUT["border_width"],
            "scrollbar_button_color":       _c(modo, "border"),
            "scrollbar_button_hover_color": colores["accent"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        new_mode = _norm_modo(new_mode)
        self.configure(
            fg_color=colores["bg_input"],
            border_color=_c(new_mode, "border"),
            text_color=colores["text_primary"],
            scrollbar_button_color=_c(new_mode, "border"),
            scrollbar_button_hover_color=colores["accent"],
        )


# ── NMToplevel ────────────────────────────────────────────────────────

class NMToplevel(ctk.CTkToplevel):
    """CTkToplevel con icono NM y caption bar sin flash blanco."""

    def __init__(self, *args, **kwargs):
        self._nm_modo = _norm_modo(kwargs.pop("modo", "dark_hybrid"))
        super().__init__(*args, **kwargs)
        self.wm_attributes("-alpha", 0.0)
        try:
            _ico = obtener_icono_solido()
            self.iconbitmap(_ico)
            _modo = self._nm_modo
            def _revelar():
                try:
                    if self.winfo_exists():
                        self.iconbitmap(_ico)
                        aplicar_captionbar(self, _modo)
                        self.wm_attributes("-alpha", 1.0)
                except Exception:
                    pass
            self.after(220, _revelar)
        except Exception:
            self.after(5, lambda: self.wm_attributes("-alpha", 1.0))


# ── Diálogos ──────────────────────────────────────────────────────────

def mostrar_acerca_de(master, modo: str = "dark_hybrid"):
    modo = _norm_modo(modo)
    colores = get_colors(modo)
    ventana = NMToplevel(master, modo=modo)
    ventana.title("Acerca de")
    _w, _h = 450, 360
    _sw = ventana.winfo_screenwidth()
    _sh = ventana.winfo_screenheight()
    ventana.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")
    ventana.resizable(False, False)
    ventana.configure(fg_color=colores["bg_primary"] if "light" in modo else colores["bg_surface"])
    ventana.grab_set()
    ventana.after(10, ventana.focus_force)

    frame = ctk.CTkFrame(ventana, fg_color="transparent")
    frame.pack(expand=True, fill="both",
               padx=LAYOUT["padding_container"], pady=LAYOUT["padding_container"])

    try:
        logo_path = obtener_ruta_recurso("LOGO.png")
        logo_img = Image.open(logo_path)
        ancho_logo, alto_logo = logo_img.size
        alto_target = 50
        ancho_target = int(ancho_logo * alto_target / alto_logo)
        logo_mostrar = _recolorear_logo_light(logo_img.copy()) if "light" in modo else logo_img
        logo_ctk = ctk.CTkImage(light_image=logo_mostrar, dark_image=logo_mostrar,
                                size=(ancho_target, alto_target))
        ctk.CTkLabel(frame, image=logo_ctk, text="").pack(pady=(0, 6))
        ventana._logo_ref = logo_ctk
    except Exception:
        pass

    ctk.CTkLabel(
        frame, text="Suite de herramientas terapéuticas",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
        text_color=_c(modo, "text_secondary"),
    ).pack(pady=(0, 12))

    ctk.CTkLabel(
        frame, text="neuromood.com.ar",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
        text_color=colores.get("info", colores["accent"]) if "light" in modo else colores["accent"],
    ).pack()

    ctk.CTkLabel(
        frame, text="Dra. Lucía Fazzito",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=_c(modo, "text_secondary") if "light" in modo else _c(modo, "text_tertiary"),
    ).pack(pady=(3, 0))

    ctk.CTkFrame(frame, fg_color=colores["accent"], height=2, corner_radius=0).pack(
        fill="x", pady=12
    )

    ctk.CTkLabel(
        frame, text="neuromood.com.ar@gmail.com",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=_c(modo, "text_secondary"),
    ).pack(pady=(0, 3))

    ctk.CTkLabel(
        frame, text="La Paz y Aménebar, Belgrano, CABA",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=_c(modo, "text_tertiary"),
    ).pack()

    ctk.CTkLabel(
        frame, text="® Marca Registrada 2023 – Todos los derechos reservados",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
        text_color=_c(modo, "text_tertiary"),
    ).pack(pady=(8, 0))

    if "light" in modo:
        BotonPrimario(
            frame, text="Cerrar", modo=modo, command=ventana.destroy,
            width=120, height=36,
            fg_color=colores.get("info", colores["accent"]),
            hover_color="#3A6E95",
        ).pack(pady=(14, 0))
    else:
        BotonSecundario(
            frame, text="Cerrar", modo=modo, command=ventana.destroy,
            width=120, height=36,
        ).pack(pady=(14, 0))


def mostrar_mensaje(master, titulo: str, mensaje: str,
                    tipo: str = "info", modo: str = "dark_hybrid"):
    modo = _norm_modo(modo)
    colores = get_colors(modo)
    _colores_t = {
        "info":    colores.get("info", colores["accent"]),
        "warning": colores["warning"],
        "error":   colores["error"],
        "success": colores["success"],
    }
    _iconos_t = {"info": "ℹ", "warning": "⚠", "error": "✕", "success": "✓"}
    color_t = _colores_t.get(tipo, colores["accent"])
    ventana = NMToplevel(master, modo=modo)
    ventana.title(titulo)
    _w, _h = 380, 230
    _sw = ventana.winfo_screenwidth()
    _sh = ventana.winfo_screenheight()
    ventana.geometry(f"{_w}x{_h}+{(_sw - _w) // 2}+{(_sh - _h) // 2}")
    ventana.resizable(False, False)
    ventana.configure(fg_color=colores["bg_surface"])
    ventana.grab_set()

    ctk.CTkFrame(ventana, fg_color=color_t, height=3, corner_radius=0).pack(fill="x")
    frame = ctk.CTkFrame(ventana, fg_color="transparent")
    frame.pack(expand=True, fill="both", padx=28, pady=(14, 20))

    ctk.CTkLabel(
        frame, text=_iconos_t.get(tipo, "ℹ"),
        font=(TYPOGRAPHY["font_family"], 26),
        text_color=color_t,
    ).pack(pady=(0, 6))

    ctk.CTkLabel(
        frame, text=titulo,
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
        text_color=color_t if "light" in modo else colores["text_primary"],
    ).pack(pady=(0, 6))

    ctk.CTkLabel(
        frame, text=mensaje,
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
        text_color=_c(modo, "text_secondary"),
        wraplength=312, justify="center",
    ).pack(pady=(0, 16))

    _hover_btn = {"info": "#3A6E95", "warning": "#B06830", "error": "#BF5555", "success": "#4A8A70"}
    _kw_btn = (
        {"fg_color": color_t, "hover_color": _hover_btn.get(tipo, colores["accent_hover"])}
        if "light" in modo else {}
    )
    BotonPrimario(frame, text="Aceptar", modo=modo, width=110,
                  command=ventana.destroy, **_kw_btn).pack()
    ventana.after(10, ventana.focus_force)
    ventana.wait_window()
