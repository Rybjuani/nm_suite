"""assets.py — Helper centralizado para resolución de logos e íconos."""

import os
import sys
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

# Constantes simbólicas para assets canónicos
LOGO_LIGHT = "logo_light.png"
LOGO_DARK = "logo_dark.png"
LOGO_ICON = "NM_icon.ico"  # icono cerebro multicolor (sin texto), theme-neutral
APP_ICON = "app_icon.ico"
INSTALLER_ICON = "installer_icon.ico"
UNINSTALLER_ICON = "no_symbol.ico"


def obtener_logo(modo: str | None) -> str:
    """Ruta del wordmark theme-aware (HANDOFF F0.2).

    La palabra "Neuro" nunca debe desaparecer: variante oscura sobre fondos
    claros (light) y blanca sobre fondos oscuros (dark).
    """
    nombre = LOGO_LIGHT if "light" in (modo or "") else LOGO_DARK
    return obtener_ruta_asset(nombre)


def obtener_icono_marca() -> str:
    """Ruta del icono de marca (cerebro, sin texto) para sidebar colapsada,
    titlebar y superficies compactas. Multicolor: legible en ambos temas."""
    return obtener_ruta_asset(LOGO_ICON)


def obtener_ruta_asset(nombre_archivo: str) -> str:
    """Resuelve la ruta a un recurso/asset de manera robusta.

    Funciona tanto en desarrollo (buscando en el directorio 'assets/')
    como en producción (congelado con PyInstaller, buscando en la raíz o en 'assets/').
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        # La raíz del proyecto es el padre de la carpeta 'shared'
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Probar ruta directa (raíz en frozen, o si se pasó una ruta relativa completa)
    path = os.path.join(base, nombre_archivo)
    if os.path.exists(path):
        return path

    # 2. Probar dentro de la subcarpeta 'assets/'
    assets_path = os.path.join(base, "assets", nombre_archivo)
    if os.path.exists(assets_path):
        return assets_path

    # Fallback por compatibilidad
    return path


def nm_logo_pixmap(modo: str, tipo: str = "full", width: int = None, height: int = None) -> QPixmap:
    """Obtiene el pixmap del logo de la marca (Theme-aware).

    Args:
        modo: 'light' o 'dark' (o strings que lo contengan como 'light_hybrid').
        tipo: 'full' (logo completo) o 'icon' (solo cerebro sin texto).
        width: ancho opcional al cual escalar.
        height: alto opcional al cual escalar.
    """
    is_dark = "dark" in modo.lower()
    nombre = "logo_dark.png" if is_dark else "logo_light.png"
    ruta = obtener_ruta_asset(nombre)
    if not os.path.exists(ruta):
        ruta = obtener_ruta_asset("LOGO.png")

    pm = QPixmap(ruta)

    if tipo == "icon" and not pm.isNull():
        # Los archivos "-icon-" son idénticos al wordmark completo (1536x326).
        # Recortamos la región del cerebro: cols 6-372, rows 18-326 del original.
        pm = pm.copy(6, 18, 366, 308)

    if width and height:
        pm = pm.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    elif width:
        pm = pm.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
    elif height:
        pm = pm.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation)

    return pm
