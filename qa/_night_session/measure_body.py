from PIL import Image
import numpy as np

cp = 'qa/_mockup_canonical/hub-detalle-dark-960x600.png'
ca = 'qa/_captures_v8/hub-detalle-dark-960x600.png'
cimg = np.asarray(Image.open(cp).convert("RGB"))
pimg = np.asarray(Image.open(ca).convert("RGB"))

# Encontrar el primer Y donde aparece el gap entre form col y body card (x=320)
def first_gap_y(img, x_check, y_start, y_end):
    bg = np.array([13, 16, 26])
    for y in range(y_start, y_end):
        if np.abs(img[y, x_check].astype(int) - bg).sum() < 15:
            return y
    return None

print("Buscando primer Y en x=320 donde aparece gap bg entre las 2 cards del body:")
print(f"  CANONICAL: y={first_gap_y(cimg, 320, 200, 470)}")
print(f"  CAPTURE:   y={first_gap_y(pimg, 320, 200, 470)}")

# Tambien medir donde arrancan las dos cards del body
def card_top(img, x, y_start, y_end):
    bg = np.array([13, 16, 26])
    for y in range(y_start, y_end):
        if np.abs(img[y, x].astype(int) - bg).sum() > 20:
            return y
    return None

print("\nDonde arranca la form col (x=100):")
print(f"  CANONICAL: y={card_top(cimg, 100, 200, 470)}")
print(f"  CAPTURE:   y={card_top(pimg, 100, 200, 470)}")
print("\nDonde arranca el body card (x=500):")
print(f"  CANONICAL: y={card_top(cimg, 500, 200, 470)}")
print(f"  CAPTURE:   y={card_top(pimg, 500, 200, 470)}")
print("\nDonde TERMINAN:")
def card_bottom(img, x, y_start, y_end):
    bg = np.array([13, 16, 26])
    last_y = None
    for y in range(y_start, y_end):
        if np.abs(img[y, x].astype(int) - bg).sum() > 20:
            last_y = y
    return last_y
print("CANONICAL form col bottom (x=100):", card_bottom(cimg, 100, 200, 470))
print("CAPTURE   form col bottom (x=100):", card_bottom(pimg, 100, 200, 470))
print("CANONICAL body card bottom (x=500):", card_bottom(cimg, 500, 200, 470))
print("CAPTURE   body card bottom (x=500):", card_bottom(pimg, 500, 200, 470))