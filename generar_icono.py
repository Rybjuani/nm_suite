from PIL import Image
import numpy as np
import os

base = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base, "LOGO.png")
ico_path = os.path.join(base, "NM_icon.ico")

img = Image.open(logo_path).convert("RGBA")
arr = np.array(img)

# Detectar dónde termina el cerebro buscando el gap entre ícono y texto
alpha = arr[:, :, 3]
col_has_content = np.any(alpha > 10, axis=0)
content_cols = np.where(col_has_content)[0]
diffs = np.diff(content_cols)
gaps = np.where(diffs > 30)[0]

if len(gaps) > 0:
    corte = content_cols[gaps[0]] + 1
else:
    corte = int(img.width * 0.25)

cerebro = img.crop((0, 0, corte, img.height))

# Trim transparencia
bbox = cerebro.getbbox()
if bbox:
    cerebro = cerebro.crop(bbox)

# Hacer cuadrada con padding
cw, ch = cerebro.size
lado = max(cw, ch)
padding = int(lado * 0.12)
lado_final = lado + padding * 2

cuadrada = Image.new("RGBA", (lado_final, lado_final), (0, 0, 0, 0))
offset_x = (lado_final - cw) // 2
offset_y = (lado_final - ch) // 2
cuadrada.paste(cerebro, (offset_x, offset_y), cerebro)

# Generar ICO con múltiples tamaños
cuadrada.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Icono generado: {ico_path} ({lado_final}x{lado_final} base)")
