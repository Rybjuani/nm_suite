"""Tests unitarios para el modo audit-mockup de Visual Sentinel.

Foco en ``_load_latest_captures`` (bug crítico reportado 2026-06-24 v3):
el root manifest ``qa/_captures_v8/CAPTURE_MANIFEST.json`` (generado
por ``qa/capture_v8.py --all``) debe tener prioridad sobre los iter
dirs históricos, y los iters deben ordenarse por número real (no
lexicográfico, donde iter100 < iter89 en ASCII).

No requiere PyQt6 ni harness completo — los tests crean manifests
sintéticos en directorios tmp.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Cargar ``visual_sentinel`` desde su path absoluto (pytest no incluye
# ``qa/`` en sys.path). ``spec_from_file_location`` evita colisiones
# con el nombre del módulo.
_QA_DIR = Path(__file__).resolve().parent.parent / "qa"
_spec = importlib.util.spec_from_file_location(
    "visual_sentinel_under_test", _QA_DIR / "visual_sentinel.py"
)
visual_sentinel = importlib.util.module_from_spec(_spec)
sys.modules["visual_sentinel_under_test"] = visual_sentinel
_spec.loader.exec_module(visual_sentinel)


def _write_manifest(path: Path, results: list[dict]) -> None:
    """Escribe un CAPTURE_MANIFEST.json con la lista de results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"harness": "test", "total": len(results), "results": results},
                  indent=2),
        encoding="utf-8",
    )


def _entry(app: str, view: str, theme: str, file_name: str) -> dict:
    """Construye un entry de CAPTURE_MANIFEST.json exitoso."""
    return {
        "file": file_name,
        "app": app,
        "view": view,
        "theme": theme,
        "resolution": "960x600",
        "success": True,
        "size_bytes": 50000,
        "evidence_contract": "main_base",
    }


def test_load_latest_captures_root_manifest_with_86_results_loads_completely(
    tmp_path, monkeypatch
):
    """Test (a): root manifest con 86 results se carga completo.

    El modo ``audit-mockup`` debe ver 86 capturas cuando existe el root
    manifest. Bug pre-fix: la implementación sólo leía ``iter*/`` y veía
    1 captura (iter89_baseline). Post-fix: el root manifest se procesa
    y las 86 entries se registran.
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()
    results = [
        _entry("suite" if i < 43 else "hub",
               f"view_{i:02d}", "light" if i % 2 == 0 else "dark",
               f"x-{i:02d}.png")
        for i in range(86)
    ]
    # Crear PNGs dummy para que la función no los descarte.
    for e in results:
        (cap_root / e["file"]).write_bytes(b"PNG")
    _write_manifest(cap_root / "CAPTURE_MANIFEST.json", results)

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    out = visual_sentinel._load_latest_captures()
    assert len(out) == 86, (
        f"Esperaba 86 entradas del root manifest, obtuve {len(out)}. "
        f"Esto indica que _load_latest_captures no leyó el root "
        f"manifest raíz (bug pre-fix)."
    )
    # Cada key es (app, view, theme) y el source es "root".
    for key, entry in out.items():
        assert entry["iter"] == "root", (
            f"key {key} no viene del root manifest (iter={entry['iter']})"
        )
        assert entry["png"] == cap_root / entry["png"].name


def test_load_latest_captures_numeric_sort_picks_higher_iter(tmp_path, monkeypatch):
    """Test (b): iter89 e iter100 presentes → iter100 gana como más reciente.

    Bug pre-fix: sorted() lexicográfico ponía ``iter100`` ANTES de
    ``iter89`` (porque '1' < '8' en ASCII), y el último procesado
    (iter89) ganaba → resultado INCORRECTO. Post-fix: orden numérico
    por el número real extraído con ``_iter_number``.
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()

    # Crear iter89 con 1 captura
    iter89 = cap_root / "iter89_baseline"
    iter89.mkdir()
    (iter89 / "suite-pacientes-light.png").write_bytes(b"PNG89")
    _write_manifest(iter89 / "CAPTURE_MANIFEST.json", [
        _entry("suite", "pacientes", "light", "suite-pacientes-light.png"),
    ])

    # Crear iter100 con la misma (app, view, theme) — debe ganar.
    iter100 = cap_root / "iter100_latest"
    iter100.mkdir()
    (iter100 / "suite-pacientes-light.png").write_bytes(b"PNG100")
    _write_manifest(iter100 / "CAPTURE_MANIFEST.json", [
        _entry("suite", "pacientes", "light", "suite-pacientes-light.png"),
    ])

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    out = visual_sentinel._load_latest_captures()
    assert ("suite", "pacientes", "light") in out
    # iter100 debe ser el que ganó (orden numérico, no lexicográfico).
    assert out[("suite", "pacientes", "light")]["iter"] == "iter100_latest", (
        f"iter100 debería ganar sobre iter89 (orden numérico), pero "
        f"ganó {out[('suite', 'pacientes', 'light')]['iter']}. "
        f"Esto indica sort lexicográfico (bug pre-fix)."
    )
    # El path debe apuntar al PNG de iter100.
    assert out[("suite", "pacientes", "light")]["png"].parent == iter100


def test_audit_mockup_v8_captures_count_matches_root_manifest(tmp_path, monkeypatch):
    """Test (c): ``audit-mockup`` no reporta ``V8_CAPTURES_LATEST=1`` cuando
    existe un root manifest válido con 86 resultados.

    Antes del fix: el root manifest se ignoraba → ``_load_latest_captures``
    sólo veía el iter89_baseline (1 captura) → audit-mockup imprimía
    ``V8_CAPTURES_LATEST: 1`` y reportaba registry incompleto. Después
    del fix: el root manifest se carga completo → ``V8_CAPTURES_LATEST``
    debe acercarse a 86.
    """
    cap_root = tmp_path / "_captures_v8"
    cap_root.mkdir()
    # Iter89 con 1 captura que también existe en el root (verificación
    # cruzada de prioridad root > iter).
    iter89 = cap_root / "iter89_baseline"
    iter89.mkdir()
    (iter89 / "suite-home-light.png").write_bytes(b"old")
    _write_manifest(iter89 / "CAPTURE_MANIFEST.json", [
        _entry("suite", "home", "light", "suite-home-light.png"),
    ])
    # Root manifest con 86 resultados (incluyendo suite/home/light que
    # también está en iter89 — el root debe override).
    results = [
        _entry("suite" if i < 43 else "hub",
               f"view_{i:02d}", "light" if i % 2 == 0 else "dark",
               f"x-{i:02d}.png")
        for i in range(86)
    ]
    # Sobrescribir suite/home/light en el root con el mismo key que iter89.
    results[0] = _entry("suite", "home", "light", "suite-home-light.png")
    for e in results:
        (cap_root / e["file"]).write_bytes(b"new")
    _write_manifest(cap_root / "CAPTURE_MANIFEST.json", results)

    monkeypatch.setattr(visual_sentinel, "_CAPTURE_ROOT", cap_root)
    captures = visual_sentinel._load_latest_captures()
    # El bug pre-fix daba 1 (sólo iter89). Post-fix da 86.
    assert len(captures) == 86, (
        f"V8_CAPTURES_LATEST={len(captures)} sugiere que el root manifest "
        f"se está ignorando. Esperaba 86. Bug pre-fix: 1."
    )
    # El key que aparece en AMBOS manifests debe ser del root (prioridad).
    shared_key = ("suite", "home", "light")
    assert shared_key in captures
    assert captures[shared_key]["iter"] == "root", (
        f"Esperaba que root override iter89 para {shared_key} (root "
        f"tiene prioridad como batch actual), pero ganó "
        f"{captures[shared_key]['iter']}."
    )
