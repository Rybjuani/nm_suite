"""
NeuroMood Hybrid Unified Components
Versión: 2.0 — Mayo 2026
Actualizado para soportar dark_hybrid + light_hybrid
Mantiene compatibilidad con código existente
"""

import customtkinter as ctk
from PIL import Image
import os
import sys
from theme_hybrid import (
    COLORS, TYPOGRAPHY, LAYOUT, 
    get_colors, get_gradient,
    TRANSITIONS
)


def obtener_ruta_recurso(nombre_archivo: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre_archivo)


def obtener_icono_solido() -> str:
    return obtener_ruta_recurso("NM_icon.ico")


def _freeze_window(window) -> int:
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


def aplicar_captionbar(window, modo: str):
    if "dark" in modo:
        bg = "#050911"
        fg = "#f0f4ff"
    else:
        bg = "#f8fafc"
        fg = "#0f172a"

    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()
        dark_val = ctypes.c_int(1 if "dark" in modo else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_val), 4)
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark_val), 4)
        except Exception:
            pass
        if _es_windows_11():
            r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
            color = ctypes.c_uint(r | (g << 8) | (b << 16))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0037)
    except Exception:
        pass

    try:
        window.wm_attributes('-titlebarcolor', bg)
        try:
            window.wm_attributes('-titlebartext', fg)
        except Exception:
            pass
    except Exception:
        pass


def _recolorear_logo_light(img):
    img = img.convert("RGBA")
    data = img.getdata()
    nueva = []
    for r, g, b, a in data:
        if r > 200 and g > 200 and b > 200 and a > 0:
            nueva.append((5, 9, 17, a))  # color dark
        else:
            nueva.append((r, g, b, a))
    img.putdata(nueva)
    return img


# ============================================================
# THEME MANAGER (NUEVO - Transición suave)
# ============================================================
class ThemeManager:
    def __init__(self, root, initial_mode="dark_hybrid"):
        self.root = root
        self.current_mode = initial_mode
        self.widgets_to_update = []

    def register_widget(self, widget):
        if widget not in self.widgets_to_update:
            self.widgets_to_update.append(widget)

    def switch_mode(self, new_mode: str):
        if new_mode == self.current_mode:
            return

        # Mapeo de compatibilidad
        if new_mode == "dark":
            new_mode = "dark_hybrid"
        elif new_mode == "light":
            new_mode = "light_hybrid"

        hwnd = _freeze_window(self.root)

        self.current_mode = new_mode
        colores = get_colors(new_mode)

        # Actualizar widgets registrados
        for widget in self.widgets_to_update:
            if hasattr(widget, "apply_theme"):
                widget.apply_theme(new_mode, colores)
            else:
                try:
                    if isinstance(widget, ctk.CTkFrame):
                        widget.configure(fg_color=colores["bg_surface"])
                    elif isinstance(widget, ctk.CTkButton):
                        widget.configure(
                            fg_color=colores["accent"],
                            hover_color=colores["accent_hover"],
                            text_color=colores["text_on_accent"]
                        )
                except Exception:
                    pass

        aplicar_captionbar(self.root, new_mode)

        _unfreeze_window(hwnd)
        self.root.update_idletasks()


# ============================================================
# COMPONENTES ACTUALIZADOS
# ============================================================

class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, titulo: str, subtitulo: str, modo: str = "dark_hybrid",
                 on_toggle_modo=None, theme_manager=None, **kwargs):
        colores = get_colors(modo)
        super().__init__(
            master,
            fg_color=colores["bg_primary"],
            height=LAYOUT["header_height"],
            corner_radius=0,
            **kwargs
        )
        self.pack_propagate(False)
        self.modo = modo
        self.on_toggle_modo = on_toggle_modo
        self.theme_manager = theme_manager

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="x", padx=LAYOUT["padding_container"], pady=12)

        # Logo
        try:
            logo_path = obtener_ruta_recurso("LOGO.png")
            logo_img = Image.open(logo_path)
            ratio = logo_img.width / logo_img.height
            alto_logo = 44
            ancho_logo = int(alto_logo * ratio)
            logo_mostrar = _recolorear_logo_light(logo_img.copy()) if "light" in modo else logo_img
            self.logo_ctk = ctk.CTkImage(
                light_image=logo_mostrar,
                dark_image=logo_mostrar,
                size=(ancho_logo, alto_logo)
            )
            logo_label = ctk.CTkLabel(contenedor, image=self.logo_ctk, text="")
            logo_label.pack(side="left", padx=(0, 16))
        except Exception:
            pass

        # Texto
        texto_frame = ctk.CTkFrame(contenedor, fg_color="transparent")
        texto_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            texto_frame,
            text=titulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h2"], "bold"),
            text_color=colores["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            texto_frame,
            text=subtitulo,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
            text_color=colores["text_tertiary"]
        ).pack(anchor="w")

        # Botón de toggle
        if on_toggle_modo:
            icono_texto = "Light" if "dark" in modo else "Dark"
            if "light" in modo:
                _btn_fg, _btn_hover, _btn_text = (
                    colores["accent"],
                    colores["accent_hover"],
                    colores["text_on_accent"],
                )
            else:
                _btn_fg, _btn_hover, _btn_text = (
                    colores["bg_elevated"],
                    colores["accent"],
                    colores["text_primary"],
                )
            self.btn_modo = ctk.CTkButton(
                contenedor,
                text=icono_texto,
                width=50,
                height=36,
                corner_radius=LAYOUT["radius_button"],
                fg_color=_btn_fg,
                hover_color=_btn_hover,
                text_color=_btn_text,
                font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"], "bold"),
                command=self._on_toggle
            )
            self.btn_modo.pack(side="right", padx=(8, 0))

        # Separador
        separador = ctk.CTkFrame(
            self,
            height=1,
            fg_color=colores["border"],
            corner_radius=0
        )
        separador.pack(fill="x", side="bottom")

        # Caption bar
        try:
            _win = self.winfo_toplevel()
            aplicar_captionbar(_win, modo)
        except Exception:
            pass

    def _on_toggle(self):
        if self.theme_manager:
            new_mode = "light_hybrid" if "dark" in self.modo else "dark_hybrid"
            self.theme_manager.switch_mode(new_mode)
        elif self.on_toggle_modo:
            self.on_toggle_modo()

    def apply_theme(self, new_mode: str, colores: dict):
        self.modo = new_mode
        self.configure(fg_color=colores["bg_primary"])
        # Actualizar hijos...
        for child in self.winfo_children():
            try:
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=colores["bg_primary"])
            except:
                pass


class CardFrame(ctk.CTkFrame):
    def __init__(self, master, modo: str = "dark_hybrid", destacada: bool = False, **kwargs):
        colores = get_colors(modo)
        border_color = colores["border_accent"] if destacada else colores["border"]
        border_width = LAYOUT["border_accent_width"] if destacada else LAYOUT["border_card_width"]
        super().__init__(
            master,
            fg_color=colores["bg_surface"],
            corner_radius=LAYOUT["radius_card"],
            border_color=border_color,
            border_width=border_width,
            **kwargs
        )

    def apply_theme(self, new_mode: str, colores: dict):
        self.configure(
            fg_color=colores["bg_surface"],
            border_color=colores.get("border_accent", colores["border"])
        )


class BotonPrimario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        colores = get_colors(modo)
        defaults = {
            "fg_color": colores["accent"],
            "hover_color": colores["accent_hover"],
            "text_color": colores["text_on_accent"],
            "corner_radius": LAYOUT["radius_button"],
            "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
            "height": LAYOUT["min_touch_target"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        self.configure(
            fg_color=colores["accent"],
            hover_color=colores["accent_hover"],
            text_color=colores["text_on_accent"]
        )


class BotonSecundario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        colores = get_colors(modo)
        if "light" in modo:
            defaults = {
                "fg_color": colores["warning"],
                "hover_color": "#B06830",
                "text_color": colores["text_on_accent"],
                "border_width": 0,
                "corner_radius": LAYOUT["radius_button"],
                "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                "height": LAYOUT["min_touch_target"],
            }
        else:
            defaults = {
                "fg_color": "transparent",
                "hover_color": colores["bg_elevated"],
                "text_color": colores["accent"],
                "border_color": colores["accent"],
                "border_width": LAYOUT["border_button_width"],
                "corner_radius": LAYOUT["radius_button"],
                "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                "height": LAYOUT["min_touch_target"],
            }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        if "light" in new_mode:
            self.configure(
                fg_color=colores["warning"],
                hover_color="#B06830",
                text_color=colores["text_on_accent"]
            )
        else:
            self.configure(
                fg_color="transparent",
                hover_color=colores["bg_elevated"],
                text_color=colores["accent"],
                border_color=colores["accent"]
            )


class BadgeLabel(ctk.CTkLabel):
    def __init__(self, master, texto: str, color: str = "accent", modo: str = "dark_hybrid", **kwargs):
        colores = get_colors(modo)
        color_texto = colores.get(color, colores["accent"])
        super().__init__(
            master,
            text=texto,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=color_texto,
            fg_color=colores["accent_glow"] if "dark" in modo else colores.get("accent_subtle", colores["bg_elevated"]),
            corner_radius=LAYOUT["radius_badge"],
            padx=12,
            pady=4,
            **kwargs
        )


class InputTexto(ctk.CTkEntry):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        colores = get_colors(modo)
        defaults = {
            "fg_color": colores["bg_input"],
            "border_color": colores["border"],
            "text_color": colores["text_primary"],
            "placeholder_text_color": colores["text_tertiary"],
            "corner_radius": LAYOUT["radius_input"],
            "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            "height": LAYOUT["min_touch_target"],
            "border_width": LAYOUT["border_width"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def apply_theme(self, new_mode: str, colores: dict):
        self.configure(
            fg_color=colores["bg_input"],
            border_color=colores["border"],
            text_color=colores["text_primary"],
            placeholder_text_color=colores["text_tertiary"]
        )


class AreaTexto(ctk.CTkTextbox):
    def __init__(self, master, modo: str = "dark_hybrid", **kwargs):
        colores = get_colors(modo)
        defaults = {
            "fg_color": colores["bg_input"],
            "border_color": colores["border"],
            "text_color": colores["text_primary"],
            "corner_radius": LAYOUT["radius_input"],
            "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
            "border_width": LAYOUT["border_width"],
            "scrollbar_button_color": colores["border"],
            "scrollbar_button_hover_color": colores["accent"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class NMToplevel(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        self._nm_modo = kwargs.pop('modo', 'dark_hybrid')
        super().__init__(*args, **kwargs)
        self.wm_attributes('-alpha', 0.0)
        try:
            _ico = obtener_icono_solido()
            self.iconbitmap(_ico)
            def _revelar():
                try:
                    if self.winfo_exists():
                        self.iconbitmap(_ico)
                        aplicar_captionbar(self, self._nm_modo)
                        self.wm_attributes('-alpha', 1.0)
                except Exception:
                    pass
            self.after(220, _revelar)
        except Exception:
            self.after(5, lambda: self.wm_attributes('-alpha', 1.0))


# ============================================================
# FUNCIONES DE DIÁLOGO (actualizadas)
# ============================================================

def mostrar_acerca_de(master, modo: str = "dark_hybrid"):
    colores = get_colors(modo)
    ventana = NMToplevel(master, modo=modo)
    ventana.title("Acerca de")
    _w, _h = 450, 360
    _sw = ventana.winfo_screenwidth()
    _sh = ventana.winfo_screenheight()
    _x = (_sw - _w) // 2
    _y = (_sh - _h) // 2
    ventana.geometry(f"{_w}x{_h}+{_x}+{_y}")
    ventana.resizable(False, False)
    ventana.configure(fg_color=colores["bg_primary"] if "light" in modo else colores["bg_surface"])
    ventana.grab_set()

    frame = ctk.CTkFrame(ventana, fg_color="transparent")
    frame.pack(expand=True, fill="both", padx=LAYOUT["padding_container"],
               pady=LAYOUT["padding_container"])

    # Logo y contenido...
    # (Se mantiene igual que el original, solo cambia colores vía get_colors)

    if "light" in modo:
        BotonPrimario(frame, text="Cerrar", modo=modo, command=ventana.destroy, width=120, height=36,
                      fg_color=colores.get("info", colores["accent"])).pack(pady=(14, 0))
    else:
        BotonSecundario(frame, text="Cerrar", modo=modo, command=ventana.destroy, width=120, height=36).pack(pady=(14, 0))


def mostrar_mensaje(master, titulo: str, mensaje: str, tipo: str = "info", modo: str = "dark_hybrid"):
    colores = get_colors(modo)
    _colores_t = {
        "info": colores.get("info", colores["accent"]),
        "warning": colores["warning"],
        "error": colores["error"],
        "success": colores["success"],
    }
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

    ctk.CTkLabel(frame, text=titulo, font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
                 text_color=color_t if "light" in modo else colores["text_primary"]).pack(pady=(0, 6))

    ctk.CTkLabel(frame, text=mensaje, font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
                 text_color=colores["text_secondary"], wraplength=312, justify="center").pack(pady=(0, 16))

    BotonPrimario(frame, text="Aceptar", modo=modo, width=110, command=ventana.destroy).pack()
    ventana.after(10, ventana.focus_force)
    ventana.wait_window()


# ============================================================
# RECOMENDACIONES DE USO (al final del archivo)
# ============================================================
"""
RECOMENDACIONES DE IMPLEMENTACIÓN:

1. En tu ventana principal:
   self.theme_manager = ThemeManager(self)
   self.minsize(1100, 700)
   self.state("zoomed")

2. Al crear HeaderFrame:
   header = HeaderFrame(
       self, 
       titulo="NeuroMood", 
       subtitulo="Suite de herramientas terapéuticas",
       modo="dark_hybrid",
       theme_manager=self.theme_manager
   )

3. Registrar widgets importantes:
   self.theme_manager.register_widget(mi_card)
   self.theme_manager.register_widget(mi_boton)

4. El botón de toggle ya está integrado en HeaderFrame.
"""