# tools/visualparity/ — VisualParity Core/CLI

> **Fase 0A skeleton — no runtime authority.**
>
> Este directorio es un placeholder. No contiene código productivo.
> VisualParity Core/CLI se implementa en Fase 1A (.NET 8). Ningún archivo
> aquí es leído por CI, por el harness, ni por agentes en Fase 0A.

## Tesis

> **VisualParity mide y muestra. El harness decide.**

VisualParity produce métricas crudas y estados de medición. No decide
cierre. No interpreta semántica `nm_suite`. No ejecuta `capture_v8.py`.
No invoca agentes.

## Stack (futuro)

- .NET 8
- CLI primero (Fase 1A)
- WPF después (fase futura, sólo `review_annotation.json`)
- WinUI fuera de V3.1

## Módulos (futuro)

| Módulo | Responsabilidad |
|---|---|
| `Bundle/EolNormalizer` | Normaliza CRLF/CR→LF sólo para texto. PNGs raw. |
| `Bundle/BundleWriter` | Wipa OutDir antes de escribir. |
| `Comparators/PixelDiff` | changed_pixel_ratio, mean_abs_diff, bbox clusters. Thresholds constantes. |
| `Comparators/DeterminismCheck` | Compara dos actuals. `changed_ratio >= 0.005` → `NON_DETERMINISTIC`. |
| `Pairing/Pairer` | Empareja CANON vs ACTUAL. Detecta missing/extra/duplicate. |
| `Ranking/NearThresholdFlag` | Marca surfaces dentro del 5% del threshold. |
| `Ranking/SeverityRank` | NO_DIFF < LOW_DIFF < SUSPICIOUS < HIGH_DIFF. |
| `Panel/PanelRenderer` | PNG CANON/ACTUAL/DIFF side-by-side. |
| `Integrity/Checksums` | `integrity/checksums.json` con hashes LF-normalized (texto) + raw (PNG). |
| `CLI` | Commands: `compare`, `batch`, `verify-bundle`, `inspect`. |

## Estados permitidos (futuro)

`NO_DIFF`, `LOW_DIFF`, `SUSPICIOUS`, `HIGH_DIFF`, `MISSING_PAIR`,
`SIZE_MISMATCH`, `NEAR_THRESHOLD`, `NON_DETERMINISTIC`,
`MEASUREMENT_DISPUTE_CANDIDATE`.

## Estados prohibidos (futuro)

`CLOSURE_ALLOWED`, `BLOCK`, `CLOSURE_PASS`, `HUMAN_REVIEWED_PASS`,
`HUMAN_REVIEWED_FAIL`. (Esos los emite el harness v3.)

## Límites (no negociables)

- VisualParity Core/CLI **no puede** invocar `qa/capture_v8.py`.
- VisualParity Core/CLI **no puede** invocar agentes.
- VisualParity Core/CLI **no puede** modificar handoff, policy, records.
- VisualParity Core/CLI **no puede** cerrar keys.
- VisualParity Core/CLI **no puede** usar bulk review.

## Lockfile

`visualparity.lock.json` (futuro) contendrá el allowlist de
`vp_build_sha256`. Skeleton en `visualparity.lock.example.json`.

El harness v3 (futuro) verifica `vp_build_sha256` vs este allowlist antes
de consumir cualquier bundle. Si el binario no está en allowlist, BLOCK.

## Estado actual (Fase 0A)

- **Implementado:** sólo `README.md` y `visualparity.lock.example.json`.
- **No implementado:** `src/` (Core + CLI), `tests/` (corpus),
  `visualparity.lock.json` (real).

## Documentación relacionada

- `docs/VisualParity_V3_1/README.md` — tesis, alcance, rutas, no-go.
- `docs/VisualParity_V3_1/ARCHITECTURE.md` — separación de capas.
- `docs/VisualParity_V3_1/POLICY.md` — reglas de cierre.
- `docs/VisualParity_V3_1/CORPUS.md` — corpus mínimo.
