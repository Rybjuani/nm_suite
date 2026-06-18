"""Guardia de limpieza: no hay consumidores vivos del sistema hash legacy."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_TERMS = (
    "apply_" + "overrides",
    "collect_" + "texts",
    "override_" + "key",
    "text." + "ovr",
)


def test_legacy_hash_text_override_system_removed_from_live_code():
    assert not (ROOT / "shared" / "text_overrides.py").exists()

    offenders: list[str] = []
    for folder in ("app", "hub", "shared"):
        for path in (ROOT / folder).rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            hits = [term for term in LEGACY_TERMS if term in text]
            if hits:
                offenders.append(f"{path.relative_to(ROOT)}: {', '.join(hits)}")

    assert offenders == []
