"""Fix atómico: eliminar márgenes laterales wraps top/plan en pacientes_qt.py.
Cambia `setContentsMargins(12, 4, 12, 2)` -> `(0, 0, 0, 0)` en top_wrap
y `setContentsMargins(12, 0, 12, 4)` -> `(0, 0, 0, 0)` en plan_wrap.
"""
import sys
from pathlib import Path

target = Path("hub/pacientes_qt.py")
src = target.read_text(encoding="utf-8")
original = src

# Cambio 1: top_wrap
old1 = "        top_lay.setContentsMargins(12, 4, 12, 2)\n"
new1 = "        top_lay.setContentsMargins(0, 0, 0, 0)\n"
assert src.count(old1) == 1, f"old1 no encontrado o duplicado. count={src.count(old1)}"
src = src.replace(old1, new1, 1)

# Cambio 2: plan_wrap
old2 = "        plan_lay.setContentsMargins(12, 0, 12, 4)\n"
new2 = "        plan_lay.setContentsMargins(0, 0, 0, 0)\n"
assert src.count(old2) == 1, f"old2 no encontrado o duplicado. count={src.count(old2)}"
src = src.replace(old2, new2, 1)

target.write_text(src, encoding="utf-8")
print(f"OK: 2 cambios aplicados a {target}")
print(f"Diff total: {(len(src) - len(original))} chars")