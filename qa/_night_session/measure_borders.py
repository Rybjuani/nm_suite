from PIL import Image
import numpy as np

cp = 'qa/_mockup_canonical/hub-detalle-dark-960x600.png'
ca = 'qa/_captures_v8/hub-detalle-dark-960x600.png'
cimg = np.asarray(Image.open(cp).convert("RGB"))
pimg = np.asarray(Image.open(ca).convert("RGB"))

# Estrategia: encontrar filas horizontales donde se produce un CAMBIO DE COLOR
# en la MAYORÍA de las columnas (borde horizontal de card)
def find_horizontal_borders(img):
    bg = np.array([13, 16, 26])
    # Diff entre fila y fila siguiente
    diffs = np.abs(np.diff(img.astype(int), axis=0)).sum(axis=2)
    # Border = fila donde hay >=200 pixeles con diff>30 en columnas (50, 950)
    borders = []
    for y in range(diffs.shape[0]):
        cnt = (diffs[y, 50:950] > 30).sum()
        if cnt > 200:
            borders.append((y, cnt))
    # Cluster
    clusters = []
    if borders:
        cs = borders[0][0]; cm = borders[0][1]; last_y = borders[0][0]
        for y, c in borders[1:]:
            if y - last_y <= 2:
                cm = max(cm, c); last_y = y
            else:
                clusters.append((cs, cm))
                cs = y; cm = c; last_y = y
        clusters.append((cs, cm))
    # Filtrar los que tienen strength > 300 (reales borders de cards)
    return [c for c in clusters if c[1] > 300]

c_borders = find_horizontal_borders(cimg)
p_borders = find_horizontal_borders(pimg)
print("=== CANONICAL strong horizontal borders ===")
for y, s in c_borders[:20]:
    print(f"  y={y:4d}  strength={s}")
print(f"  Total: {len(c_borders)}")
print("\n=== CAPTURE strong horizontal borders ===")
for y, s in p_borders[:20]:
    print(f"  y={y:4d}  strength={s}")
print(f"  Total: {len(p_borders)}")