from PIL import Image
import numpy as np

cp = 'qa/_mockup_canonical/hub-detalle-dark-960x600.png'
ca = 'qa/_captures_v8/hub-detalle-dark-960x600.png'
cimg = np.asarray(Image.open(cp).convert("RGB"))
pimg = np.asarray(Image.open(ca).convert("RGB"))

# Encontrar el borde derecho exacto de la form col y borde izquierdo exacto del body card
def find_card_right_edge(img, y, x_start=0, x_end=400):
    """Encuentra el último pixel de la form col empezando desde x_start."""
    bg = np.array([13, 16, 26])
    row = img[y, x_start:x_end].astype(int)
    diffs = np.abs(row - bg).sum(axis=1)
    card_xs = np.where(diffs > 15)[0]
    if len(card_xs) == 0: return None
    return int(card_xs[-1] + x_start)

def find_card_left_edge(img, y, x_start=300, x_end=700):
    """Encuentra el primer pixel del body card desde x_start."""
    bg = np.array([13, 16, 26])
    row = img[y, x_start:x_end].astype(int)
    diffs = np.abs(row - bg).sum(axis=1)
    card_xs = np.where(diffs > 15)[0]
    if len(card_xs) == 0: return None
    return int(card_xs[0] + x_start)

print(f"{'y':>4}  {'CANON form_right':>16}  {'CANON body_left':>16}  {'CAPT form_right':>16}  {'CAPT body_left':>16}")
for y in [220, 250, 280, 300, 350, 400, 430]:
    cfr = find_card_right_edge(cimg, y, 0, 350)
    cbl = find_card_left_edge(cimg, y, 300, 700)
    pfr = find_card_right_edge(pimg, y, 0, 350)
    pbl = find_card_left_edge(pimg, y, 300, 700)
    cgap = cbl - cfr - 1 if cfr and cbl else None
    pgap = pbl - pfr - 1 if pfr and pbl else None
    print(f"{y:4d}  {str(cfr):>16}  {str(cbl):>16}  {str(pfr):>16}  {str(pbl):>16}    canon_gap={cgap} capt_gap={pgap}")