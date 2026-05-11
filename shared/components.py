import customtkinter as ctk
from PIL import Image
import os
import sys
from shared.theme import COLORS, TYPOGRAPHY, LAYOUT


def obtener_ruta_recurso(nombre_archivo: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre_archivo)


def obtener_icono_solido() -> str:
    return obtener_ruta_recurso("NM_icon.ico")


def _freeze_window(window) -> int:
    """Pausa el repintado para evitar deformación durante rebuild. Devuelve HWND o 0."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()
        ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 0, 0)  # WM_SETREDRAW = False
        return hwnd
    except Exception:
        return 0


def _unfreeze_window(hwnd: int):
    """Reactiva el repintado y fuerza un redibujado completo."""
    if not hwnd:
        return
    try:
        import ctypes
        ctypes.windll.user32.SendMessageW(hwnd, 0x000B, 1, 0)  # WM_SETREDRAW = True
        ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x0185)  # INVALIDATE|UPDATENOW|ERASE|ALLCHILDREN
    except Exception:
        pass


def _es_windows_11() -> bool:
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:
        return False


def aplicar_captionbar(window, modo: str):
    bg = "#0D2137"
    fg = "#E8EEF4"
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if hwnd == 0:
            hwnd = window.winfo_id()
        dark_val = ctypes.c_int(1)
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


def aplicar_captionbar_flush(window, modo: str):
    """Versión con flush completo — usar solo en toggle explícito post-unfreeze."""
    aplicar_captionbar(window, modo)
    try:
        # update_idletasks() bombea la cola Win32: procesa WM_NCCALCSIZE → WM_NCPAINT
        # necesario para que DWM repinte la barra de título con el nuevo atributo
        window.update_idletasks()
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.dwmapi.DwmFlush()
    except Exception:
        pass


def _recolorear_logo_light(img):
    img = img.convert("RGBA")
    data = img.getdata()
    nueva = []
    for r, g, b, a in data:
        if r > 200 and g > 200 and b > 200 and a > 0:
            nueva.append((11, 25, 40, a))
        else:
            nueva.append((r, g, b, a))
    img.putdata(nueva)
    return img


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master, titulo: str, subtitulo: str, modo: str = "dark",
                 on_toggle_modo=None, **kwargs):
        colores = COLORS[modo]
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

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="x", padx=LAYOUT["padding_container"], pady=12)

        try:
            logo_path = obtener_ruta_recurso("LOGO.png")
            logo_img = Image.open(logo_path)
            ratio = logo_img.width / logo_img.height
            alto_logo = 44
            ancho_logo = int(alto_logo * ratio)
            logo_mostrar = _recolorear_logo_light(logo_img.copy()) if modo == "light" else logo_img
            self.logo_ctk = ctk.CTkImage(
                light_image=logo_mostrar,
                dark_image=logo_mostrar,
                size=(ancho_logo, alto_logo)
            )
            logo_label = ctk.CTkLabel(contenedor, image=self.logo_ctk, text="")
            logo_label.pack(side="left", padx=(0, 16))
        except Exception:
            pass

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

        if on_toggle_modo:
            icono_texto = "Light" if modo == "dark" else "Dark"
            # En light: botón oscuro (accent) + texto blanco + hover más claro
            # En dark:  comportamiento original (bg_hover + hover teal + texto primario)
            if modo == "light":
                _btn_fg, _btn_hover, _btn_text = (
                    colores["accent"],
                    colores["accent_hover"],
                    colores["text_on_accent"],
                )
            else:
                _btn_fg, _btn_hover, _btn_text = (
                    colores["bg_hover"],
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
                command=on_toggle_modo
            )
            self.btn_modo.pack(side="right", padx=(8, 0))

        separador = ctk.CTkFrame(
            self,
            height=1,
            fg_color=colores["border"],
            corner_radius=0
        )
        separador.pack(fill="x", side="bottom")

        try:
            _win = self.winfo_toplevel()
            _m = modo
            aplicar_captionbar(_win, _m)
            _win.after(0, lambda: aplicar_captionbar(_win, _m))
            _win.after(100, lambda: aplicar_captionbar(_win, _m))
            _win.after(300, lambda: aplicar_captionbar(_win, _m))
            _win.after(600, lambda: aplicar_captionbar(_win, _m))
        except Exception:
            pass


class CardFrame(ctk.CTkFrame):
    def __init__(self, master, modo: str = "dark", destacada: bool = False, **kwargs):
        colores = COLORS[modo]
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


class BotonPrimario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark", **kwargs):
        colores = COLORS[modo]
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


class BotonSecundario(ctk.CTkButton):
    def __init__(self, master, modo: str = "dark", **kwargs):
        colores = COLORS[modo]
        if modo == "light":
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
                "hover_color": colores["bg_hover"],
                "text_color": colores["accent"],
                "border_color": colores["accent"],
                "border_width": LAYOUT["border_button_width"],
                "corner_radius": LAYOUT["radius_button"],
                "font": (TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
                "height": LAYOUT["min_touch_target"],
            }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class BadgeLabel(ctk.CTkLabel):
    def __init__(self, master, texto: str, color: str = "accent", modo: str = "dark", **kwargs):
        colores = COLORS[modo]
        color_texto = colores.get(color, colores["accent"])
        super().__init__(
            master,
            text=texto,
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"], "bold"),
            text_color=color_texto,
            fg_color=colores["accent_subtle"],
            corner_radius=LAYOUT["radius_badge"],
            padx=12,
            pady=4,
            **kwargs
        )


class InputTexto(ctk.CTkEntry):
    def __init__(self, master, modo: str = "dark", **kwargs):
        colores = COLORS[modo]
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


class AreaTexto(ctk.CTkTextbox):
    def __init__(self, master, modo: str = "dark", **kwargs):
        colores = COLORS[modo]
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
    """CTkToplevel que aparece con NM_icon.ico y caption bar de la identidad visual, sin flash."""

    def __init__(self, *args, **kwargs):
        self._nm_modo = kwargs.pop('modo', 'dark')
        super().__init__(*args, **kwargs)
        self.wm_attributes('-alpha', 0.0)
        try:
            _ico = obtener_icono_solido()
            self.iconbitmap(_ico)
            _modo = self._nm_modo
            def _revelar():
                try:
                    if self.winfo_exists():
                        self.iconbitmap(_ico)
                        aplicar_captionbar(self, _modo)
                        self.wm_attributes('-alpha', 1.0)
                except Exception:
                    pass
            self.after(220, _revelar)
        except Exception:
            self.after(5, lambda: self.wm_attributes('-alpha', 1.0))


def mostrar_acerca_de(master, modo: str = "dark"):
    colores = COLORS[modo]
    ventana = NMToplevel(master, modo=modo)
    ventana.title("Acerca de")
    _w, _h = 450, 360
    _sw = ventana.winfo_screenwidth()
    _sh = ventana.winfo_screenheight()
    _x = (_sw - _w) // 2
    _y = (_sh - _h) // 2
    ventana.geometry(f"{_w}x{_h}+{_x}+{_y}")
    ventana.resizable(False, False)
    ventana.configure(fg_color=colores["bg_primary"] if modo == "light" else colores["bg_surface"])
    ventana.grab_set()

    ventana.after(10, lambda: ventana.focus_force())

    frame = ctk.CTkFrame(ventana, fg_color="transparent")
    frame.pack(expand=True, fill="both", padx=LAYOUT["padding_container"],
               pady=LAYOUT["padding_container"])

    try:
        logo_path = obtener_ruta_recurso("LOGO.png")
        logo_img = Image.open(logo_path)
        ancho_logo, alto_logo = logo_img.size
        alto_target = 50
        ancho_target = int(ancho_logo * alto_target / alto_logo)
        logo_mostrar = _recolorear_logo_light(logo_img.copy()) if modo == "light" else logo_img
        logo_ctk = ctk.CTkImage(light_image=logo_mostrar, dark_image=logo_mostrar, size=(ancho_target, alto_target))
        ctk.CTkLabel(frame, image=logo_ctk, text="").pack(pady=(0, 6))
        ventana._logo_ref = logo_ctk
    except Exception:
        pass

    ctk.CTkLabel(
        frame, text="Suite de herramientas terapéuticas",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
        text_color=colores["text_secondary"]
    ).pack(pady=(0, 12))

    ctk.CTkLabel(
        frame, text="neuromood.com.ar",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"], "bold"),
        text_color=colores.get("info", colores["accent"]) if modo == "light" else colores["accent"]
    ).pack()

    ctk.CTkLabel(
        frame, text="Dra. Lucía Fazzito",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=colores["text_secondary"] if modo == "light" else colores["text_tertiary"]
    ).pack(pady=(3, 0))

    ctk.CTkFrame(
        frame,
        fg_color=colores["accent"],
        height=2,
        corner_radius=0
    ).pack(fill="x", pady=12)

    ctk.CTkLabel(
        frame, text="neuromood.com.ar@gmail.com",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=colores["text_secondary"]
    ).pack(pady=(0, 3))

    ctk.CTkLabel(
        frame, text="La Paz y Aménebar, Belgrano, CABA",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=colores["text_tertiary"]
    ).pack()

    ctk.CTkLabel(
        frame, text="® Marca Registrada 2023 – Todos los derechos reservados",
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_caption"]),
        text_color=colores["text_tertiary"]
    ).pack(pady=(8, 0))

    if modo == "light":
        BotonPrimario(frame, text="Cerrar", modo=modo, command=ventana.destroy, width=120, height=36,
                      fg_color=colores.get("info", colores["accent"]), hover_color="#3A6E95").pack(pady=(14, 0))
    else:
        BotonSecundario(frame, text="Cerrar", modo=modo, command=ventana.destroy, width=120, height=36).pack(pady=(14, 0))


def mostrar_mensaje(master, titulo: str, mensaje: str, tipo: str = "info", modo: str = "dark"):
    colores = COLORS[modo]
    _colores_t = {
        "info": colores.get("info", colores["accent"]),
        "warning": colores["warning"],
        "error": colores["error"],
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
        text_color=color_t
    ).pack(pady=(0, 6))
    ctk.CTkLabel(
        frame, text=titulo,
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
        text_color=color_t if modo == "light" else colores["text_primary"]
    ).pack(pady=(0, 6))
    ctk.CTkLabel(
        frame, text=mensaje,
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_body"]),
        text_color=colores["text_secondary"],
        wraplength=312, justify="center"
    ).pack(pady=(0, 16))
    _hover_btn = {"info": "#3A6E95", "warning": "#B06830", "error": "#BF5555", "success": "#4A8A70"}
    _kw_btn = {"fg_color": color_t, "hover_color": _hover_btn.get(tipo, colores["accent_hover"])} if modo == "light" else {}
    BotonPrimario(frame, text="Aceptar", modo=modo, width=110, command=ventana.destroy, **_kw_btn).pack()
    ventana.after(10, ventana.focus_force)
    ventana.wait_window()
