from PIL import Image
import numpy as np

cp = 'qa/_mockup_canonical/hub-detalle-dark-960x600.png'
ca = 'qa/_captures_v8/hub-detalle-dark-960x600.png'
cimg = np.asarray(Image.open(cp).convert("RGB"))
pimg = np.asarray(Image.open(ca).convert("RGB"))

# En y=350 (mitad del body), encontrar donde termina la form col y donde arranca el body card
def find_card_gap(img, y, x_start=300, x_end=340):
    """Encuentra la primera y última x donde hay bg-color (gap entre cards)."""
    bg = np.array([13, 16, 26])
    # buscar columnas consecutivas con bg en y
    row = img[y, x_start:x_end].astype(int)
    diffs = np.abs(row - bg).sum(axis=1)
    bg_cols = np.where(diffs < 15)[0] + x_start
    if len(bg_cols) == 0: return None, None
    return int(bg_cols.min()), int(bg_cols.max())

# Encontrar x_right de form col y x_left de body card en múltiples Y
def edges(img, y, x_search=range(250, 700)):
    bg = np.array([13, 16, 26])
    row = img[y, x_search[0]:x_search[-1]+1].astype(int)
    diffs = np.abs(row - bg).sum(axis=1)
    card = diffs > 15
    if not card.any(): return None
    xs = np.where(card)[0] + x_search[0]
    # encontrar gap
    gaps = np.where(~card)[0] + x_search[0]
    return xs, gaps

print(f"{'y':>4}  {'CANON (form-right, gap, body-left)':<40}  {'CAPT':<40}")
for y in [220, 240, 260, 280, 300, 350, 400, 440]:
    c_xs, c_gaps = edges(cimg, y)
    p_xs, p_gaps = edges(pimg, y)
    c_str = f"right={c_xs[-1] if len(c_xs) else '-'} gap={c_gaps[-1]-c_gaps[0]+1 if len(c_gaps)>1 else 0} left={c_xs[0] if len(c_xs) else '-'}"
    p_str = f"right={p_xs[-1] if len(p_xs) else '-'} gap={p_gaps[-1]-p_gaps[0]+1 if len(p_gaps)>1 else 0} left={p_xs[0] if len(p_xs) else '-'}"
    print(f"{y:4d}  {c_str:<40}  {p_str:<40}")