"""Mide SOLO coordenadas Y de los bloques principales:
- top del header paciente (hero card)
- top de tabs
- top del body/card principal
- top de botones inferiores (CTA primarios: Agregar, Exportar PDF)

Salida: tabla Y canon vs capture + delta.

Estrategia robusta:
1. Detectar filas con 'mucho borde horizontal' (border de card top/bottom)
2. Detectar filas donde aparece color de botón primary (verde)
3. Detectar filas donde aparece el texto del header paciente (medir por brillo)
"""
from PIL import Image
import numpy as np
import json
import sys

BG_LIGHT = np.array([247, 244, 235])  # light bg aproximado
BG_DARK = np.array([13, 16, 26])
PRIMARY_GREEN = np.array([56, 142, 110])  # verde primario NM

def find_horizontal_borders(img_arr, min_x=50, max_x=950, threshold=30, min_run=200):
    """Devuelve lista de filas con borde horizontal (>= min_run pixeles diferentes)."""
    diffs = np.abs(np.diff(img_arr.astype(int), axis=0)).sum(axis=2)
    borders = []
    for y in range(diffs.shape[0]):
        cnt = (diffs[y, min_x:max_x] > threshold).sum()
        if cnt >= min_run:
            borders.append((y, cnt))
    # Cluster
    clusters = []
    if not borders:
        return []
    cur_start = borders[0][0]; cur_max = borders[0][1]; last_y = borders[0][0]
    for y, c in borders[1:]:
        if y - last_y <= 2:
            cur_max = max(cur_max, c); last_y = y
        else:
            clusters.append((cur_start, cur_max))
            cur_start = y; cur_max = c; last_y = y
    clusters.append((cur_start, cur_max))
    return [c for c in clusters if c[1] > 250]

def find_first_green_row(img_arr, x_start=400, x_end=900):
    """Encuentra primera fila donde aparece el botón verde primario."""
    r, g, b = img_arr[:,:,0], img_arr[:,:,1], img_arr[:,:,2]
    # pixel verde NM aproximado: R<100, G>120, B<140
    is_green = (r < 120) & (g > 110) & (b < 140) & (g > r) & (g > b)
    # Restringir a rango x
    in_range = is_green.copy()
    in_range[:, :x_start] = False
    in_range[:, x_end:] = False
    rows_with_green = np.where(in_range.any(axis=1))[0]
    if len(rows_with_green) == 0:
        return None
    return int(rows_with_green[0])

def find_avatar_orange_row(img_arr):
    """Avatar típico: rounded square color naranja/marrón.
    Buscar pixel naranja (R>180, G>80, B<120)."""
    r, g, b = img_arr[:,:,0], img_arr[:,:,1], img_arr[:,:,2]
    is_orange = (r > 180) & (g > 60) & (g < 180) & (b < 130) & (r > b + 50)
    rows = np.where(is_orange.any(axis=1))[0]
    if len(rows) == 0:
        return None, None
    return int(rows[0]), int(rows[-1])

def analyze(surface, theme):
    cp = f'qa/_mockup_canonical/{surface}-{theme}-960x600.png'
    ca = f'qa/_captures_v8/{surface}-{theme}-960x600.png'
    cimg = np.asarray(Image.open(cp).convert("RGB"))
    pimg = np.asarray(Image.open(ca).convert("RGB"))

    cb = find_horizontal_borders(cimg)
    pb = find_horizontal_borders(pimg)

    cg = find_first_green_row(cimg)
    pg = find_first_green_row(pimg)

    co_t, co_b = find_avatar_orange_row(cimg)
    po_t, po_b = find_avatar_orange_row(pimg)

    return {
        'canon_borders': cb[:15],
        'capt_borders': pb[:15],
        'canon_first_green': cg,
        'capt_first_green': pg,
        'canon_avatar': (co_t, co_b),
        'capt_avatar': (po_t, po_b),
    }

if __name__ == '__main__':
    surfaces = ['hub-detalle-plan-activacion', 'hub-detalle', 'hub-detalle-resumen-ia-0']
    for s in surfaces:
        for theme in ['light', 'dark']:
            try:
                r = analyze(s, theme)
                print(f"\n=== {s} {theme} ===")
                print(f"  CANON borders (top 15): {r['canon_borders']}")
                print(f"  CAPT  borders (top 15): {r['capt_borders']}")
                print(f"  CANON first green (botón): y={r['canon_first_green']}")
                print(f"  CAPT  first green (botón): y={r['capt_first_green']}")
                print(f"  CANON avatar orange: y={r['canon_avatar']}")
                print(f"  CAPT  avatar orange: y={r['capt_avatar']}")
            except FileNotFoundError as e:
                print(f"SKIP {s} {theme}: {e}")