"""Encuentra los bordes de las cards principales (hero, tabs, body cards).
Estrategia: el fondo dark es aprox (13,16,26). El card-bg es ligeramente más claro.
Detectar cambios pequeños (>=15) en vez de grandes para encontrar bordes sutiles.
"""
from PIL import Image
import numpy as np

BG_DARK = np.array([13, 16, 26])

def card_edges_per_row(img_arr, y, min_x=20, max_x=940):
    """Encuentra los x donde la fila cruza un borde de card (cambio de color sostenido)."""
    row = img_arr[y, min_x:max_x].astype(int)
    diffs = np.abs(row - BG_DARK).sum(axis=1)
    # borde = primer pixel con diff > 20 sostenido
    edges = []
    in_card = False
    start = None
    for i, d in enumerate(diffs):
        if d > 20:
            if not in_card:
                start = min_x + i
                in_card = True
        else:
            if in_card:
                if i - (start - min_x) >= 30:  # al menos 30 px de card
                    edges.append((start, min_x + i - 1))
                in_card = False
    if in_card:
        edges.append((start, max_x - 1))
    return edges

for surf in ['hub-detalle-dark-960x600', 'hub-detalle-light-960x600']:
    cp = f'qa/_mockup_canonical/{surf}.png'
    ca = f'qa/_captures_v8/{surf}.png'
    cimg = np.asarray(Image.open(cp).convert("RGB"))
    pimg = np.asarray(Image.open(ca).convert("RGB"))
    print(f"\n=== {surf} ===")
    print(f"{'y':>4}  {'CANON x ranges':<40}  {'CAPT x ranges':<40}")
    for y in [48, 60, 75, 90, 110, 130, 145, 155, 170, 185, 200, 215, 235, 260, 300, 400]:
        ce = card_edges_per_row(cimg, y)
        pe = card_edges_per_row(pimg, y)
        cs = ' '.join(f"[{a}-{b}]" for a,b in ce[:3])
        ps = ' '.join(f"[{a}-{b}]" for a,b in pe[:3])
        print(f"{y:4d}  {cs:<40}  {ps:<40}")