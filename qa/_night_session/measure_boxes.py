from PIL import Image
import numpy as np
import sys

def find_orange(path):
    img = np.asarray(Image.open(path).convert("RGB"))
    r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
    orange = (r > 200) & (g > 80) & (g < 180) & (b < 100)
    ys, xs = np.where(orange)
    if len(ys) == 0: return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())

def find_green_btn(path):
    img = np.asarray(Image.open(path).convert("RGB"))
    r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
    green = (g > 200) & (r < 200) & (b < 200)
    ys, xs = np.where(green)
    if len(ys) == 0: return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())

# all hub-detalle surfaces
surfaces = ['hub-detalle-dark-960x600', 'hub-detalle-light-960x600',
            'hub-detalle-plan-activacion-dark-960x600', 'hub-detalle-plan-activacion-light-960x600',
            'hub-detalle-plan-rutina-dark-960x600', 'hub-detalle-plan-rutina-light-960x600',
            'hub-detalle-plan-timer-dark-960x600', 'hub-detalle-plan-timer-light-960x600',
            'hub-detalle-resumen-ia-0-dark-480x325', 'hub-detalle-resumen-ia-0-light-480x325']

print(f"{'surface':<55}  {'avatar L':>9}  {'avatar R':>9}  {'btn L':>7}  {'btn R':>7}")
for s in surfaces:
    cp = f'qa/_mockup_canonical/{s}.png'
    ca = f'qa/_captures_v8/{s}.png'
    co = find_orange(cp); cg = find_green_btn(cp)
    po = find_orange(ca); pg = find_green_btn(ca)
    def fmt(b):
        if b is None: return '-'
        return f"{b[0]:>3},{b[1]:>3},{b[2]:>3},{b[3]:>3}"
    print(f"{s:<55}  canon orange={fmt(co)} green={fmt(cg)}  |  capt orange={fmt(po)} green={fmt(pg)}")