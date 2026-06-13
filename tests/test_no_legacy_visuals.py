"""Guardia anti-reintroducción de deuda visual (plan ADN Fase 10).

El canon vive en `ADN/`. Cualquier hex de las
paletas viejas (V2 slate, Indigo pre-ADN, Linen pre-ADN) o componente/harness
demolido que reaparezca en código de producto es reciclaje prohibido.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Carpetas de producto donde NO puede volver lo viejo.
_SCAN_DIRS = ("shared", "app", "hub", "installers")

# Paletas demolidas (case-insensitive):
#  - V2 slate: 0F172A / F1F5F9 / 94A3B8 / 6366F1 / A855F7
#  - Indigo pre-ADN: 0B0C19 / 121530 / 181C33 / 1C2140 / 0D1225 / A49BE8 / 6FCDBA
#  - Linen pre-ADN: EEE6D4 / FBF7EE / F2EBDA / F1ECE0 / 3D5A48 / B6892B
_FORBIDDEN_HEX = [
    "0F172A", "F1F5F9", "94A3B8", "6366F1", "A855F7",
    "0B0C19", "121530", "181C33", "1C2140", "0D1225", "A49BE8", "6FCDBA",
    "EEE6D4", "FBF7EE", "F2EBDA", "F1ECE0", "3D5A48", "B6892B",
]

# Identificadores/harnesses demolidos.
_FORBIDDEN_NAMES = [
    "_SidePanel",
    "show_side_panel",
    "NMSidebarFooterRow",
    "capture_v6",
    "capture_v7",
]

_HEX_RE = re.compile(
    "#(?:" + "|".join(_FORBIDDEN_HEX) + r")\b", re.IGNORECASE
)


def _iter_py_files():
    for d in _SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            yield path


def test_no_forbidden_hex_in_product_code():
    hits = []
    for path in _iter_py_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            if _HEX_RE.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()[:90]}")
    assert not hits, "Hex de paleta demolida reintroducido:\n" + "\n".join(hits)


def test_no_forbidden_legacy_names():
    hits = []
    for path in _iter_py_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for name in _FORBIDDEN_NAMES:
            for n, line in enumerate(text.splitlines(), 1):
                if name in line:
                    hits.append(f"{path.relative_to(ROOT)}:{n}: {name}")
    assert not hits, "Componente/harness demolido reintroducido:\n" + "\n".join(hits)


def test_legacy_harnesses_deleted():
    assert not (ROOT / "qa" / "capture_v6.py").exists()
    assert not (ROOT / "qa" / "capture_v7.py").exists()
