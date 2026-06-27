from PIL import Image
import numpy as np

cp = 'qa/_mockup_canonical/hub-detalle-dark-960x600.png'
ca = 'qa/_captures_v8/hub-detalle-dark-960x600.png'
cimg = np.asarray(Image.open(cp).convert("RGB"))
pimg = np.asarray(Image.open(ca).convert("RGB"))

# Color bg-ventana dark: ~(13,16,26)
# Color card-bg dark: mas claro. Promediar un pixel del centro de una card visible
# En canonical, en (500, 250) hay un card-bg (zona interna del body card)
y_check = 350
print("CANONICAL pixel en (500, 250):", cimg[250, 500])  # body card interior
print("CANONICAL pixel en (100, 250):", cimg[250, 100])  # form col interior
print("CANONICAL pixel en (320, 250):", cimg[250, 320])  # posible gap
print("CANONICAL pixel en (1, 250):", cimg[250, 1])      # bg-ventana
print()
print("CAPTURE pixel en (500, 250):", pimg[250, 500])
print("CAPTURE pixel en (100, 250):", pimg[250, 100])
print("CAPTURE pixel en (320, 250):", pimg[250, 320])
print("CAPTURE pixel en (1, 250):", pimg[250, 1])

# Promediar una fila horizontal
print("\nCANONICAL row y=300 desde x=0 a x=960 (sample):")
for x in [0, 12, 50, 100, 200, 320, 350, 400, 500, 600, 700, 800, 940]:
    print(f"  x={x}: {cimg[300, x]}")
print("\nCAPTURE row y=300 desde x=0 a x=960 (sample):")
for x in [0, 12, 50, 100, 200, 320, 350, 400, 500, 600, 700, 800, 940]:
    print(f"  x={x}: {pimg[300, x]}")