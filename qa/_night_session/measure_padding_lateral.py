"""Medir el padding lateral REAL del canonical en todas las superficies hub-detalle."""
from PIL import Image
import numpy as np

def find_left_card_edge(img, y, x_max=200):
    """Encuentra el primer pixel que NO es bg-ventana empezando desde x=0."""
    bg = np.array([13, 16, 26])
    bg_light = np.array([245, 246, 248])  # light mode
    row = img[y, :x_max].astype(int)
    # Test ambos bg (dark + light)
    diff_dark = np.abs(row - bg).sum(axis=1)
    diff_light = np.abs(row - bg_light).sum(axis=1)
    diff = np.minimum(diff_dark, diff_light)
    nonbg = np.where(diff > 15)[0]
    if len(nonbg) == 0: return None
    return int(nonbg[0])

surfaces = [
    ('hub-detalle-dark-960x600', 'dark'),
    ('hub-detalle-light-960x600', 'light'),
    ('hub-detalle-plan-activacion-dark-960x600', 'dark'),
    ('hub-detalle-plan-activacion-light-960x600', 'light'),
    ('hub-detalle-plan-rutina-dark-960x600', 'dark'),
    ('hub-detalle-plan-rutina-light-960x600', 'light'),
    ('hub-detalle-plan-timer-dark-960x600', 'dark'),
    ('hub-detalle-plan-timer-light-960x600', 'light'),
]

print(f"{'surface':<55} {'hero L':>8} {'body L':>8}")
for surf, theme in surfaces:
    cp = f'qa/_mockup_canonical/{surf}.png'
    ca = f'qa/_captures_v8/{surf}.png'
    cimg = np.asarray(Image.open(cp).convert("RGB"))
    pimg = np.asarray(Image.open(ca).convert("RGB"))
    # Hero está aprox y=80, body aprox y=300
    c_hero_l = find_left_card_edge(cimg, 80)
    c_body_l = find_left_card_edge(cimg, 300)
    p_hero_l = find_left_card_edge(pimg, 80)
    p_body_l = find_left_card_edge(pimg, 300)
    print(f"{surf:<55} canon=({c_hero_l},{c_body_l})  capt=({p_hero_l},{p_body_l})")