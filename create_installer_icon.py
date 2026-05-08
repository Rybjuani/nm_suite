"""
Genera installer_icon.ico a partir de NM_icon.ico con un engranaje estilo Windows Settings
en la esquina inferior derecha.
Ejecutar: python create_installer_icon.py
"""
from PIL import Image, ImageDraw
import math


def dibujar_engranaje_windows(size):
    """Dibuja un engranaje gris estilo Windows Settings sobre fondo transparente."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = size / 2
    cy = size / 2
    num_dientes = 8
    radio_ext = size * 0.46
    radio_int = size * 0.34
    radio_agujero = size * 0.18
    ancho_diente = 0.22

    gris = (190, 195, 200, 255)
    gris_oscuro = (140, 145, 150, 255)
    borde_claro = (255, 255, 255, 200)

    puntos = []
    steps = num_dientes * 4
    for i in range(steps):
        angulo = (2 * math.pi * i) / steps - math.pi / 2
        fase = (i % 4)
        if fase == 0 or fase == 1:
            r = radio_ext
        else:
            r = radio_int
        x = cx + r * math.cos(angulo)
        y = cy + r * math.sin(angulo)
        puntos.append((x, y))

    # Borde blanco externo para contraste en dark theme
    outline_w = max(2, size // 36)
    draw.polygon(puntos, fill=None, outline=borde_claro, width=outline_w)
    draw.polygon(puntos, fill=gris, outline=gris_oscuro)

    draw.ellipse(
        [cx - radio_int, cy - radio_int, cx + radio_int, cy + radio_int],
        fill=gris, outline=gris_oscuro, width=1
    )

    draw.ellipse(
        [cx - radio_agujero, cy - radio_agujero, cx + radio_agujero, cy + radio_agujero],
        fill=(0, 0, 0, 0), outline=borde_claro, width=max(2, size // 40)
    )

    return img


def crear_icono_instalador():
    base = Image.open("NM_icon.ico").convert("RGBA")
    base = base.resize((256, 256), Image.LANCZOS)

    # Engranaje: ocupa ~45% del ícono, posicionado en esquina inferior derecha
    gear_size = 112
    gear = dibujar_engranaje_windows(gear_size)

    # Sombra sutil
    sombra = Image.new("RGBA", (gear_size, gear_size), (0, 0, 0, 0))
    draw_s = ImageDraw.Draw(sombra)
    # Rellenar con negro semi-transparente donde hay gear
    for y in range(gear_size):
        for x in range(gear_size):
            if gear.getpixel((x, y))[3] > 50:
                sombra.putpixel((x, y), (0, 0, 0, 70))

    pos_x = 4
    pos_y = 256 - gear_size - 4

    base.paste(sombra, (pos_x + 3, pos_y + 3), sombra)
    base.paste(gear, (pos_x, pos_y), gear)

    # Generar ICO con todas las resoluciones
    sizes = [256, 128, 64, 48, 32, 16]
    imgs = []
    for s in sizes:
        resized = base.resize((s, s), Image.LANCZOS)
        imgs.append(resized)

    imgs[0].save(
        "installer_icon.ico",
        format="ICO",
        append_images=imgs[1:],
    )
    print("installer_icon.ico creado exitosamente")


if __name__ == "__main__":
    crear_icono_instalador()
