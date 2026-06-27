# Mockup Reference Normalized

> Nota 2026-06-27: este documento describe un flujo histórico de normalización
> sobre `qa/mockup_reference_static/`. El canonical operativo vigente del repo es
> `qa/_mockup_canonical/`; la ruta vieja se conserva sólo como referencia
> histórica/no canónica.

## Purpose

`qa/mockup_reference_static/` contains 86 PNGs captured from `neuromood-mockup.html`
but with variable content heights (22 distinct sizes). `qa/capture_mockup.py` uses
`_force_image_size()` which crops top-left, losing footers. `qa/diff_fidelity.py`
stretches vertically via LANCZOS resize, distorting SSIM/MAD/changed metrics.

`qa/mockup_reference_normalized/` applies **per-surface normalization** with 7
documented methods so every PNG matches the exact size that `capture_v8.py`
produces for its viewport class:

| Viewport class | Canonical size | Surfaces |
|---|---|---|
| `window` | 960×600 | 78 |
| `narrow` | 520×600 | 6 |
| `modal` | 480×325 | 2 |

## Methods

| Method | When used | Content loss |
|---|---|---|
| `identity` | Source already matches target | None |
| `resize_only` | Width differs, height matches after resize | None |
| `resize+crop_center` | Too tall, lost_pct < 5% | Symmetric crop top+bottom |
| `resize+crop_top` | Too tall, header is decorative | Crop from top |
| `resize+crop_bottom` | Too tall, footer is decorative | Crop from bottom |
| `resize+pad_bottom_surface` | Too short, pad < 50px | Pad bottom with surface color |
| `manual_override` | lost_pct ≥ 5% or pad ≥ 50px | Best-effort candidate |

## Usage

```powershell
# Generate normalized reference
.\.venv\Scripts\python.exe qa\normalize_mockup_reference.py

# Validate all PNGs have canonical sizes
.\.venv\Scripts\python.exe qa\normalize_mockup_reference.py doctor

# Audit — list surfaces with review_required=true
.\.venv\Scripts\python.exe qa\normalize_mockup_reference.py audit

# Re-generate one surface with a different method (post-hoc)
.\.venv\Scripts\python.exe qa\normalize_mockup_reference.py regenerate `
    --surface suite:dbtlib@light `
    --method resize+crop_bottom `
    --reason "footer is decorative library content"
```

## `review_required` flag

- **Informativo, NO bloqueante.** V3 audita igual sobre todas las superficies.
- Set when `lost_pct >= 5%` or `pad_pixels >= 50`.
- Expected count: ~10–15 surfaces (empirically ~14/86).
- The owner can regenerate a surface with a better method if the candidate is
  unsatisfactory, but V3 already produces a best-effort diagnosis on the
  original candidate.

## Git hygiene

```gitignore
qa/mockup_reference_normalized/*
!qa/mockup_reference_normalized/manifest.json
```

- **PNG files** are regenerable → **gitignored**.
- **`manifest.json`** is metadata (method, lost pixels, pad, review flags) →
  **committed**.
- `qa/mockup_reference_static/` is preserved as historical/non-canonical.

## Architecture

```
qa/mockup_reference_static/
  manifest.json          ← 86 items with original sizes (980×571, 980×572, etc.)
  light/.../Foo.png
  dark/.../Bar.png

qa/normalize_mockup_reference.py
  ↓ reads static manifest
  ↓ maps (screen_id, state_id) → capture_v8 view name
  ↓ selects method per surface (auto, based on size delta)
  ↓ writes

qa/mockup_reference_normalized/
  manifest.json          ← 86 entries with method, lost_pixels, pad, review_required
  light/{view}.png       ← 43 PNGs, all 960×600 / 520×600 / 480×325
  dark/{view}.png        ← 43 PNGs, all 960×600 / 520×600 / 480×325
```

## Stop conditions

If `doctor` reports fewer than 86/86 canonical sizes, do **not** proceed to
Fase 2. Fix the normalization first.
