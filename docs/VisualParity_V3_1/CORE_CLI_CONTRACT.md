# Core/CLI Contract — VisualParity V3.1

> **Fase 1 — measurement only. No runtime authority. No visual closure.**

## Tesis

> **VisualParity mide y muestra. El harness decide.**

VisualParity Core/CLI produce métricas crudas y estados de medición. No
decide cierre. No interpreta semántica `nm_suite`. No ejecuta
`capture_v8.py`. No invoca agentes.

## Stack

- .NET 8 (LTS hasta noviembre 2026).
- CLI/Core primero (Fase 1 — implementado).
- WPF después (fase futura, sólo `review_annotation.json`).
- WinUI fuera de V3.1.

## Solución

`tools/visualparity/VisualParity.sln` contiene 3 proyectos:

| Proyecto | Tipo | Rol |
|---|---|---|
| `src/VisualParity.Core` | Library | Medición pura. Bundle, Pairing, Comparators. |
| `src/VisualParity.CLI` | Console Exe | Comandos `compare`, `batch`, `verify-bundle`. |
| `tests/VisualParity.Core.Tests` | xUnit | Tests del Core. |

## Comandos CLI (Fase 1)

```bash
# Comparar un par canonical/actual
visualparity compare <canonical.png> <actual.png> --out <dir> [--git-head <sha>]

# Comparar un manifest de pares
visualparity batch <manifest.json> --out <dir> [--git-head <sha>]

# Verificar bundle + checksums
visualparity verify-bundle <bundle_dir>
```

### Manifest format (batch)

```json
{
  "pairs": [
    {
      "surface_key": "suite:timer@light",
      "canonical": "/path/to/canonical.png",
      "actual": "/path/to/actual.png"
    }
  ]
}
```

## Estados emitidos (Fase 1 — medición only)

| Estado | Cuándo | Acción harness v3 |
|---|---|---|
| `NO_DIFF` | Canonical y actual son byte-iguales. | `CANDIDATE_PASS` (requiere todos los required properties) |
| `MISSING_PAIR` | Falta canonical o actual. | `BLOCK` |
| `SIZE_MISMATCH` | Tamaños difieren. | `BLOCK` |
| `DIFF_UNCLASSIFIED` | Mismo tamaño, hashes distintos. Pixel metrics en fase posterior. | `BLOCK` |

## Estados NO emitidos por VisualParity (los emite el harness v3)

`CLOSURE_ALLOWED`, `BLOCK`, `CLOSURE_PASS`, `HUMAN_REVIEWED_PASS`,
`HUMAN_REVIEWED_FAIL`.

## Estados diferidos a fases posteriores

`LOW_DIFF`, `HIGH_DIFF`, `SUSPICIOUS`, `NEAR_THRESHOLD`,
`NON_DETERMINISTIC`, `MEASUREMENT_DISPUTE_CANDIDATE`. Requieren pixel
metrics (changed_pixel_ratio, mean_abs_diff, bbox clusters) que no están
en Fase 1. En Fase 1, cualquier diff es `DIFF_UNCLASSIFIED` y el harness
v3 lo mapea a `BLOCK`.

## Bundle format

`bundle.json` (LF-normalized):

```json
{
  "schema": "visualparity.bundle.v1",
  "eol": "lf",
  "generated_at_utc": "2026-07-07T00:00:00.0000000Z",
  "git_head": "<sha or empty>",
  "vp_build_sha256": "<sha256 of CLI binary or 'unbuilt-fase-1-scaffold'>",
  "surfaces": [
    {
      "surface_key": "suite:timer@light",
      "status": "NO_DIFF",
      "canonical_png_sha256": "<hex>",
      "actual_png_sha256": "<hex>",
      "canonical_bytes": 12345,
      "actual_bytes": 12345,
      "failure_reason": null
    }
  ],
  "checksums": {
    "bundle_sha256": "<hex>",
    "bundle_json_sha256": "<hex>"
  }
}
```

`integrity/checksums.json`:

```json
{
  "schema": "visualparity.checksums.v1",
  "bundle_sha256": "<hex>",
  "bundle_json_sha256": "<hex>",
  "files": [
    { "path": "bundle.json", "sha256": "<hex>", "bytes": 1234 }
  ]
}
```

## BundleWriter invariantes

- **Wipe OutDir antes de write.** Previene stale-bundle attacks
  (VQA-AF-STALE-001).
- **LF normalization en texto.** `bundle.json` y `checksums.json` se
  escriben con LF (sin CRLF). PNGs se hashean raw (sin EOL normalization).
- **SHA256 sobre raw bytes.** `bundle_sha256` = SHA256 del archivo
  `bundle.json` final.
- **UTF-8 sin BOM.** Para cross-platform reproducibility.

## Lockfile

`tools/visualparity/visualparity.lock.json` contiene el allowlist de
`vp_build_sha256`. En Fase 1 es placeholder (`unbuilt-fase-1-scaffold`)
porque el binario no está construido. El harness v3 `bundle_verifier.py`
trata cualquier `vp_build_sha256` no en el allowlist como `BLOCK`.

Cuando el binario se construya en una fase posterior, reemplazar el
placeholder con el SHA256 real del binario publicado y bump
`lockfile_version`.

## Tests (Fase 1)

`tests/VisualParity.Core.Tests/PixelDiffTests.cs` (xUnit):

- `Same_Png_Bytes_Yields_NoDiff`
- `Missing_Canonical_Yields_MissingPair`
- `Missing_Actual_Yields_MissingPair`
- `Different_Size_Yields_SizeMismatch`
- `Same_Size_Different_Bytes_Yields_DiffUnclassified`
- `Bundle_Checksum_Stable_Across_Writes`
- `Verify_Bundle_Fails_When_File_Altered`

## Límites (no negociables)

- VisualParity Core/CLI **no puede** invocar `qa/capture_v8.py`.
- VisualParity Core/CLI **no puede** invocar agentes.
- VisualParity Core/CLI **no puede** modificar handoff, policy, records.
- VisualParity Core/CLI **no puede** cerrar keys.
- VisualParity Core/CLI **no puede** usar bulk review.
- VisualParity Core/CLI **no puede** leer evidence records.
- VisualParity Core/CLI **no puede** leer handoff.

## Construcción

```bash
cd tools/visualparity
dotnet build VisualParity.sln --configuration Release
dotnet test VisualParity.sln --configuration Release --no-build
```

Si `dotnet` no está disponible localmente, marcar `NOT_EXECUTABLE`. El
workflow CI `visual-parity-v3-governance.yml` instala `dotnet` vía
`setup-dotnet` action y corre los tests en `ubuntu-latest`.

## Próximas fases (no implementadas)

- **Fase posterior:** pixel metrics (changed_pixel_ratio, mean_abs_diff,
  bbox). Habilita `LOW_DIFF`, `HIGH_DIFF`, `SUSPICIOUS`,
  `NEAR_THRESHOLD`, `NON_DETERMINISTIC`, `MEASUREMENT_DISPUTE_CANDIDATE`.
- **Fase posterior:** `DeterminismCheck` (dos actuals).
- **Fase posterior:** `Panel/PanelRenderer` (CANON/ACTUAL/DIFF side-by-side).
- **Fase futura:** WPF UI (sólo `review_annotation.json`).
