# Visual Repair Handoff

Status: RESET on 2026-06-28 after a false stale/pass closure.
Branch base: `main`.

Read first: `WORKER_VISUAL_QA_FLOW.md` (protocolo completo archivado en
`docs/_archive/protocol_v1.md`).

> **WORKERS**: Para cerrar una key NO leas este archivo completo.
> Seguí `WORKER_VISUAL_QA_FLOW.md` (se entrega por separado, <=300 líneas,
> 2 comandos por key).

> ✅ **Las 60 keys legacy pre-replay-era (cerradas sin evidence canónica) fueron
> REABIERTAS** el 2026-07-04 (`qa/close_visual_key.py --reopen-legacy-all`):
> como no tenían record en `docs/closure_evidence/`, nada probaba que hubieran
> pasado el gate vigente, así que dejarlas `[x]` mentía sobre el estado. Ahora
> son `[ ]` abiertas, a revalidar con evidencia real vía `close_visual_key.py`.
> Sólo quedan `[x]` los cierres evidence-backed (record íntegro + notas
> `evidence:`/`evidence-record:`/`commit:`), que son la única fuente de verdad
> de una key cerrada. `--skip-legacy` ya no es necesario (0 legacy restantes).

## NEXT_KEY

`NEXT_KEY` = el primer `- [ ]` abierto de la sección Checklist. Es la
resolución del target mode `next-key` (ver `WORKER_VISUAL_QA_FLOW.md` §0
"OWNER_TARGET_MODE"). El scope real de trabajo lo declara el owner en su
prompt — puede ser `next-key` (esta key sola), `first-N`, `batch`, `family`,
`all-open-keys`, o `explicit-list`. Resolvé mecánicamente con
`qa\target_scope.py --mode <modo>` en vez de re-derivar a mano.

`NEXT_KEY` **no se hardcodea acá** — un snapshot queda stale tras el primer
cierre. Resolvelo SIEMPRE en vivo (lee el `## Checklist` real):

```powershell
.\.venv\Scripts\python.exe qa\target_scope.py --mode next-key
```

> El "Repair Order" histórico quedó obsoleto y fue removido (ver git log).
> La selección de `NEXT_KEY` es puramente posicional (top-down en Checklist).

## OPEN KEYS — cómo listarlas (sin snapshot)

Esta vista **no lista keys hardcodeadas** (una lista a mano queda stale tras
cada cierre/reapertura). La lista viva, ordenada y sin duplicados sale del
resolver, que lee el `## Checklist` real:

```powershell
# todas las abiertas, en orden de documento
.\.venv\Scripts\python.exe qa\target_scope.py --mode all-open-keys
# la familia (misma sección ###) de una seed
.\.venv\Scripts\python.exe qa\target_scope.py --mode family --seed-key <key>
# las primeras N (first-N/batch)
.\.venv\Scripts\python.exe qa\target_scope.py --mode first-n --n <N>
```

Tier por línea del checklist (dato ya presente): `HIGH` = `severity=high`;
`LOW` = `severity=medium` con `changed <= 0.10` (umbral dense-aware,
`LayeredThresholds.text_dense_max_changed_pixel_ratio`); `MED` = el resto. La
familia es el heading `###` que agrupa a la key en `## Checklist`. Fuente de
verdad mecánica = el `- [ ]` real; no cierres ni edites keys desde acá.

## MANDATORY PRE-FLIGHT FOR EACH OPEN CHECKBOX

> **STOP.** Do not touch UI/runtime code for an item until this pre-flight is
> done for that item. A blind pixel fix without the mapping below is a protocol
> violation. This uses the Design-System Translation Bridge
> (`docs/DESIGN_SYSTEM_TRANSLATION_BRIDGE.md`).

For each open `[ ]` checkbox in the owner-declared target set (see
`WORKER_VISUAL_QA_FLOW.md` § "OWNER_TARGET_MODE" — the set may be 1 key or
many), the agent must:

1. **Identify the exact key** (e.g. `suite:recuperar-acceso@light`).
2. **Consult the bridge**: `docs/BRIDGE_USAGE_FOR_AGENTS.md`,
   `docs/CSS_TO_PYQT_EQUIVALENCE_MATRIX.md`,
   `docs/VISUAL_COMPONENT_CATALOG.md`, `docs/QT_HTML_KNOWN_MISMATCHES.md`.
3. **Use Graphify if available** to navigate
   `canonical selector → bridge entry → PyQt component → shared.theme tokens →
   runtime file/screen → tests/probes → visual key`. If Graphify is not
   available, **report it** and continue with the bridge docs — never fabricate
   graph output.
4. **Produce the mapping** for the key before editing any code:

   | Field | Source |
   |---|---|
   | visual key | this handoff |
   | canonical selector/pattern | matrix (with HTML line) |
   | visual family (F1–F15) | matrix / overview |
   | PyQt component actual/propuesto | catalog |
   | `shared.theme` tokens | `shared/theme.py` via `shared/theme_qt.py` |
   | runtime file/screen | `app/` or `hub/` |
   | known Qt/HTML mismatches | `QT_HTML_KNOWN_MISMATCHES.md` (IRREDUCIBLE / WORKAROUND / DECISIÓN-OWNER) |
   | tests/probes | matrix / `qa/` |

5. **Only after that mapping** may the agent touch code, reusing the mapped
   token/helper/component — never invented QSS.
6. If Graphify is unavailable, proceed with the bridge docs and say so; do not
   invent graph output.
7. **No blind pixel fixes** without the mapping above.
8. **No closure** without a real `PASS` for the exact key (see Required Closure
   Evidence). The bridge never replaces the comparator, never enables
   threshold-only closure, and never authorizes overlays/blits/canonical
   injection or any anti-fraud bypass.

## Reset Reason

The prior checked items in this file are not trusted. Many were closed as
`STALE: fidelity PASS al recapturar`, but that evidence came from auxiliary or
incomplete signals, not from a valid layered-comparator `PASS` plus a versioned
evidence record. Those closures are invalid until revalidated with the workflow
below. (Manual/panel inspection is never closure evidence — see Anti-Fraud Rule
and Required Closure Evidence.)

Forbidden closure words/reasons: `STALE`, `fidelity PASS`, `diff_fidelity PASS`,
`capture_v8 success`, zip-based comparison, or any report with
`REPORT_EVIDENCE_VALID: NO`. `HANDOFF_CLOSURE_ALLOWED: NO` is **not** a forbidden
closure reason for an individual checkbox when the exact key is `PASS` in an
officially valid report. Also forbidden: owner acceptance, human review,
"looks good enough", acceptable residue, partial progress, "mostly fixed",
blocked / too hard / won’t fix, degrading or reclassifying to skip, or any
claim that a divergence is "minor", "cosmetic", or "acceptable" without a
comparator `PASS`.

Manual/panel inspection is only diagnostic context; it never closes a checkbox
without the mandatory technical gates in Required Closure Evidence. (The old
legacy closure notes that leaned on such phrasing were stripped when the 60
evidence-less legacy closures were reopened — 2026-07-04.)
If an exact key appears both in an active checklist and in a historical or
superseded section, only the active checklist row governs closure. Historical
duplicates must stay isolated under explicit historical headings and must not be
cited as current PASS evidence.

## Active Sources

- Canonical images: `qa/_mockup_canonical/`
- Canonical HTML: `qa/pack canonico/neuromood-mockup_reparado.html`
- Runtime captures: fresh full run in `qa/_captures_v8/`
- Comparator: `qa/layered_visual_compare.py`
- Canonical HTML/mockup parity auditor:
  `tools/qa/audit_mockup_parity_baseline.py`
- Fresh report used to seed this handoff:
  `reports/qa/layered_visual_compare_fresh/LAYERED_VISUAL_REPORT.json`

Do not use desktop zips as operational evidence. They are archival only.

DBT canonical v2 is now the active baseline. The official canon has 116
captures (58 views x 2 themes), and the DBT family contains 16 formal practice
modal surfaces. The older DBT closure against `suite:dbt-practice-stop` only is
obsolete by baseline promotion, not by regression: it remains historical
evidence but cannot close DBT completo. The runtime PyQt DBT module must be
recreated and validated against this 16-practice canon before DBT can be closed
as a family.

Promotion evidence (2026-07-01): canonical generation produced 116/116 PNG with
surfaces `window=76`, `narrow=6`, `modal=0`, `window_modal=34`; both
`qa/pack canonico/capturas_test/MANIFEST.json` and
`qa/_mockup_canonical/MANIFEST.json` point to
`qa/pack canonico/neuromood-mockup_reparado.html`, not `reports/`.
`capture_v8.py --all --clean` captured 116/116 runtime PNG and all 16 DBT
practice recipes. Modal audit `reports/qa/modal_backdrop_blur/20260701_221602/`
passed 32/32 DBT practice modals; the only `--all` modal failure was
`hub:detalle-resumen-ia-0@dark` (`MODAL_CENTER_FAIL`), outside DBT. Layered DBT
compare `reports/qa/layered_visual_compare_dbt_v2/LAYERED_VISUAL_REPORT.json`
is **not closed**: 36 DBT keys, 18 PASS, 18 FAIL. Therefore DBT PyQt v2 is
structurally recreated but still visually open; do not close DBT or the global
checklist from this promotion.

Runtime alignment evidence (2026-07-02): DBT runtime was re-audited from the
active canon without editing
`qa/pack canonico/neuromood-mockup_reparado.html` (SHA256
`08D8D8E3927ECB49166E4413BAEF2E8D8A4A185EE313086C35739FF7E006732E`,
CRLF=2084, stray LF=0). The repair is runtime-only and confines changes to
`app/modules/dbt_qt.py` plus DBT/modal visual contract tests. Final fresh full
capture saved 116/116 runtime PNG. DBT modal audit
`reports/qa/dbt_modal_audit_after_shadow/AUDIT.json` passed 32/32 DBT practice
modals; the only `--all` modal failure remains
`hub:detalle-resumen-ia-0@dark`, outside DBT. Layered DBT compare
`reports/qa/dbt_full_compare_after_shadow/LAYERED_VISUAL_REPORT.md` is
**not closed**: 36 DBT keys, 34 PASS, 2 FAIL. All 32 DBT practice modal keys
PASS; open exact-key debt is `suite:dbt-library@light` and
`suite:dbt-library@dark` (`VISUAL_STYLE_REVIEW`). Do not close DBT as a family
until those library keys pass.

No HTML under `reports/` is a canonical source. Auditor snapshots such as
`reports/.../sources/original_HEAD.html` are `DO_NOT_USE_AS_CANON`; they compare
`HEAD` against working tree only. Official canonical captures must be generated
from `qa/pack canonico/neuromood-mockup_reparado.html`.

## Graphify Preflight

Before manual code exploration in this active visual repair flow, run:

```powershell
graphify . --update
```

If the environment exposes Graphify as a slash command, run:

```text
/graphify . --update
```

Consult the generated graph before opening product code by hand.

## Resource-Safe Validation

Microfix de una pantalla:

- Nunca usar `capture_v8.py --all --clean` por defecto.
- Usar `capture_v8.py --app ... --view ... --theme ... --out-dir qa\_captures_v8 --no-clean`.
- Luego correr `layered_visual_compare.py` con filtro de key/app/view/theme para validar solo la superficie relevante.
- El reporte puede ser `REPORT_SCOPE: PARTIAL` y sirve como evidencia individual si `REPORT_EVIDENCE_VALID: YES` y la exact key esta en `PASS`.

Familia chica:

- Capturar solo las vistas/temas afectados, repitiendo comandos puntuales con `--no-clean`.
- Usar comparator filtrado por `--keys-file` o filtros equivalentes.
- No correr `--all` salvo que la familia toque una base compartida amplia.

Cambio transversal grande:

- Si toca `theme`, `chrome`, `NMCard`, layout shell, tokens, navegacion base, helpers de captura compartidos o componentes globales, ahi si corresponde una regresion amplia con `capture_v8.py --all --clean`.

Regresion final:

- Solo para cierre global o verificacion amplia.
- Usar `capture_v8.py --all --clean` + comparator full.
- Si tambien cambia el HTML canonico, la receta de captura, los PNG canonicos,
  o el baseline/seed que alimenta esta checklist, correr el auditor HTML/mockup
  canonico y registrar su `AUDIT.md`.

Harness canonico HTML/mockup:

```powershell
.\.venv\Scripts\python.exe tools\qa\audit_mockup_parity_baseline.py
```

Este harness renderiza la receta completa como original A/B para medir ruido
natural y original/modificado para medir delta real. Es PASS solo si el set
completo de 116 capturas (incluidos modales accionados) queda dentro del baseline
dinamico o del baseline estadistico automatico, y si `AUDIT.json` reporta
`summary.fail == 0`. Es FAIL si falta una captura, falla la receta, o cualquier
fila queda fuera del baseline despues del escalamiento estadistico.

Outputs esperados:

- `reports\qa\mockup_parity_baseline\<timestamp>\AUDIT.json`
- `reports\qa\mockup_parity_baseline\<timestamp>\AUDIT.csv`
- `reports\qa\mockup_parity_baseline\<timestamp>\AUDIT.md`
- `TEXT_DIFF_NORMALIZED.patch`
- `EOL_DELTA.txt`

El auditor normaliza CRLF/LF antes del diff textual y reporta EOL-only aparte.
Su PASS/FAIL convive con `capture_v8`, `layered_visual_compare`, anti-fraud y
VAS; no reemplaza ningun gate runtime ni autoriza cerrar una divergencia visual
sin exact-key `PASS` del comparador activo.

Reglas de scope adicionales:

- Los wrappers advisory retirados (`run_visual_scope_regression`,
  `runtime_noise_envelope`, `runtime_internal_nav_parity`,
  `audit_diff_confinement`, `diff_fidelity`) ya no existen; sus etiquetas
  historicas (`REVIEW_NOISE`, `NOISE_WARNING`, `delta_best`) nunca fueron ni
  seran evidencia de cierre.
- Ningun agente puede saltar DBT v2 porque no estaba sembrado en la checklist
  vieja: DBT v2 tiene 36 exact keys y esta seccion gobierna la cola actual.
- `panel_crop`, `capture_v8` success, `audit_mockup_parity_baseline.py` PASS
  aislado, criterios subjetivos de aceptacion o etiquetas esteticas no cierran
  checklist.
- Si `qa/anti_fraud_scan.py` falla, ningun PASS posterior del comparator es
  valido hasta corregir la causa y rerun anti-fraud.

Disciplina de recursos:

- No correr varios harnesses pesados en simultaneo.
- No correr `capture_v8 --all`, `runtime_live_probe --all`, E2E completo y comparator full al mismo tiempo.
- En agentes baratos/Hermes Desktop, usar una sola validacion pesada por vez.
- Para microfix, preferir validacion puntual, no matriz completa.
- `REPORT_SCOPE: PARTIAL` nunca puede habilitar `HANDOFF_CLOSURE_ALLOWED: YES`.
- `REPORT_SCOPE: PARTIAL` si puede servir para cerrar un checkbox individual si la exact key esta en `PASS` y `REPORT_EVIDENCE_VALID: YES`.
- `REPORT_SCOPE: FULL` es requerido para cierre global del handoff.

Ejemplos seguros:

Microfix pantalla exacta:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py `
  --app suite `
  --view dbt-practice-wise-mind `
  --theme light `
  --out-dir qa\_captures_v8 `
  --no-clean

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_item `
  --key "suite:dbt-practice-wise-mind@light"
```

Familia chica:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-running --theme light --out-dir qa\_captures_v8 --no-clean
.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view timer-paused  --theme light --out-dir qa\_captures_v8 --no-clean

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_family `
  --keys-file reports\qa\visual_family_keys.txt
```

Runtime probe puntual:

```powershell
.\.venv\Scripts\python.exe qa\runtime_live_probe.py `
  --app suite `
  --view timer `
  --theme light `
  --mode offscreen
```

E2E puntual:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\e2e\suite\test_e2e_s07_timer.py -q
```

E2E smoke:

```powershell
.\scripts\e2e\run-e2e-smoke.ps1
```

Regresion final completa:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py --all --clean --out-dir qa\_captures_v8

.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_fresh
```

## Operational Discipline

The checklist scope is **owner-directed**, not a fixed sequential queue. See
`WORKER_VISUAL_QA_FLOW.md` § "OWNER_TARGET_MODE" for how the owner's prompt
declares scope (`next-key`, `first-N`, `batch`, `family`, `all-open-keys`,
`explicit-list`). Rules:

1. Work exactly the target set the owner declared — no smaller (don't drop
   keys from the declared scope by cost/fatigue/perceived risk) and no
   larger (don't add keys the owner didn't declare), except when a key in
   the declared set does not exist, is a duplicate, or is no longer open —
   report that deviation explicitly, don't apply it silently.
2. Within the target set, repair each key on its own merits; a key that
   remains `FAIL` does not block progress on the other keys in the same
   declared scope.
3. You may not ask the owner for a decision to skip or accept a key inside
   the declared scope.
4. You may not close, downgrade, or reclassify a key because it is
   difficult, costly, or "risky" — if a key in scope can't be closed, report
   the blockage per `WORKER_VISUAL_QA_FLOW.md` §2.4; don't mask it as done.
5. The only way to advance any key's checkbox is a `PASS` from the active
   layered comparator (`qa/layered_visual_compare.py`) plus a real evidence
   record (see Required Closure Evidence) — regardless of target mode.
6. If the checklist seed/baseline or canonical mockup changes, the HTML/mockup
   parity auditor must also PASS before the harness can be treated as current.

## Current Item Definition (target-set aware)

- `NEXT_KEY` = the first unchecked `[ ]` checkbox in this document, read
  strictly top to bottom. It is always defined and resolvable, whether the
  owner's declared scope is 1 key or all open keys.
- The **declared target set** is resolved from the owner's trigger phrase per
  `WORKER_VISUAL_QA_FLOW.md` § "OWNER_TARGET_MODE" (mechanically via
  `qa/target_scope.py`) — it may be exactly `NEXT_KEY`, an ordered prefix of
  open keys, a family cluster, an explicit list, or the full open set. The
  agent does not infer or negotiate this; the owner's prompt is authoritative.
- "Family" = the open keys sharing the same `###` section heading in
  `## Checklist` as the seed key (default seed: `NEXT_KEY`) — deterministic,
  mirrors `## OPEN KEYS — family/complexity order` above.
- Closure remains per-key: each exact key must independently reach `PASS`
  before its own checkbox flips, and each closed key requires its own
  evidence record under `docs/closure_evidence/`.
- Commit granularity follows the target mode: `next-key`/`first-N`/
  `explicit-list` default to one commit per closed key; `batch`/
  `all-open-keys`/`family` may bundle multiple closures (each still with its
  own evidence record) into fewer commits. The replay gate validates the
  full audited range regardless of how commits are split.
- The agent does not switch to keys outside the declared target set on its
  own initiative. If the declared set is exhausted (all keys closed or
  blocked with a report), stop and report — don't silently expand scope.

## Comparator Command Lock

Valid comparator closure evidence must use the active comparator command documented in Fresh Baseline or Resource-Safe Validation. Full reports are required for global handoff closure; filtered `REPORT_SCOPE: PARTIAL` reports are valid only for individual checkbox evidence. Any report generated with the following overrides is **exploratory only** and **not valid** as closure evidence:

- `--raw-changed-threshold`
- `--raw-mad-threshold`
- `--min-ssim`
- `--max-odiff-diff-pct`
- `--max-bbox-shift-px`
- `--no-odiff`
- `--no-panels`

Do not use threshold overrides, disabled odiff, or disabled panels to close a checklist item.

## Anti-Fraud Rule

A `PASS` must come from real changes in the product or UI. It is strictly forbidden to modify any of the following in order to make a visual divergence pass:

- QA scripts, tests, or assertions
- Comparators, thresholds, or scoring logic
- Capture scripts, canonical images, or fixtures
- Reports, manifests, or baselines

If a divergence is fixed, the fix must be in the actual product code, styles, or assets. Any attempt to game the comparator is a protocol violation.

### No canonical/reference artifacts in product or runtime

Product or runtime code may **never** read, render, mount, copy, blit, or
overlay any canonical / reference / mockup artifact (e.g. anything under
`qa/_mockup_canonical/`, `qa/pack canonico/`, the canonical HTML, or any
reference image/fixture) in order to pass — or appear to pass — a visual
comparison. The runtime must render only its own real UI. A capture that
shows a reference artifact instead of a genuine render is fraudulent.

If any closure depends, directly or indirectly, on such canonical/reference
injection into the product or runtime, that closure is automatically
**invalid** and the affected checklist item(s) must be **reopened** and
re-validated with a real render. This applies retroactively to already-closed
items.

## Gate Hardening (mandatory)

These mechanisms harden the visual gate. They only ever make it STRICTER, never
looser: the honest closure thresholds (SSIM / changed_pixel_ratio /
mean_abs_diff / bbox / odiff) are unchanged, while fraud detection was
strengthened (2026-07-04: the density-aware canonical-injection ceiling was
added and the `-empty` name exemption was removed — both add blocking cases, no
honest render is newly closed by them).

### Mandatory static anti-fraud scan

`qa/anti_fraud_scan.py` statically scans `app/`, `hub/`, `shared/` and fails if
runtime/product code reads, renders, copies, mounts or overlays any
canonical / reference / mockup / QA-report artifact. It is wired into the
official runner (`qa/run_visual.ps1`, modos `-Key`/`-PlanFile`/`-All`)
and runs BEFORE capture/compare. If the scan fails the
run aborts and **no report it would have produced is valid closure evidence,
even if the comparator reports `PASS`**. Run standalone with
`.\.venv\Scripts\python.exe qa\anti_fraud_scan.py`. It does not ban `QPixmap`
globally — only its use with QA/reference artifacts.

For closure evidence also run
`.\.venv\Scripts\python.exe qa\anti_fraud_scan.py --mode qa-harness`: the QA
harness scan forbids `qa/capture_v8.py` from reading/copying canonical mockup,
reports, canonical HTML, or prior captures as visual input; comparators and
auditors may read `qa/_mockup_canonical` only as declared canonical source.

### Suspicious perfect match

The comparator flags any result that is pixel-identical to the canonical
(`ssim=1.0`, `mad=0.0`, `changed=0`) on a non-trivial surface as
`status=SUSPICIOUS_PERFECT_MATCH` with `suspicious_perfect_match: true`. This is
physically implausible for genuine Qt-vs-Chromium rendering and is the signature
of reference-artifact injection. It counts as a real divergence and **blocks
closure pending audit** — it can never be closure evidence. The only exemption
is a flat / near-constant canonical (grayscale std < 2.0), where a perfect match
is information-free. There is **no** name-based `-empty` exemption: the real
`*-empty` canonicals are content-rich (std 13-16) and stay protected.

The comparator also flags non-trivial near-perfect matches as
`status=NEAR_PERFECT_MATCH` / `near_perfect_match: true` when
`changed_pixel_ratio < 0.005` and `ssim > 0.995`. This catches copied canonical
PNGs with tiny injected noise and blocks closure exactly like
`SUSPICIOUS_PERFECT_MATCH` (`repair_bucket=AUDIT_REQUIRED`). The same std-only
trivial exemption applies here.

### Canonical-injection ceiling (density-aware global ssim)

`near_perfect_match` also fires when the **global** ssim is implausibly high for
the surface's density class — the signature of a smuggled canonical copy (added
as a product asset, so the static scan's path tokens don't fire) even after
noise is added to dodge the exact/near-perfect thresholds. Ceilings are
calibrated on the real 116-key corpus: honest global-ssim max is `0.743` for
text-dense/content surfaces (canonical grayscale std `< 35`) and `0.966` for
sparse high-contrast surfaces. A capture over the ceiling for its class is
blocked (`AUDIT_REQUIRED`):

- **dense** (std `< 35`): `ssim >= 0.90` (margin 0.157 above honest max)
- **sparse** (std `>= 35`): `ssim >= 0.985` (margin 0.019 above honest max)

These sit above every honest render in the corpus, so no honest capture is
blocked (verified: full-corpus PASS count unchanged, 0 keys reclassified).
Honest text-dense renders (global ssim 0.4-0.74) and the anti-fraud static scan
are unaffected. A determined heavy-noise copy whose global ssim drops below the
ceiling still has to clear `changed_pixel_ratio`/windowed-SSIM (degrading as
noise rises) and VAS introspection; this ceiling closes the wide, easy band.

### Density-aware gate (text-dense surfaces)

Two layers are density-aware. Sparse, high-contrast surfaces keep the strict bars
(`ssim >= 0.92`, `changed_pixel_ratio <= 0.08`). Text-dense, low-contrast
surfaces — canonical grayscale std `< 35.0` (e.g. the 520x600 Acceso/registro
forms) — instead use:

- **windowed SSIM `>= 0.65`** (standard Wang et al. metric) instead of global
  `ssim >= 0.92`, because global single-window SSIM has a measured ~0.55 hard
  floor on these surfaces (Qt-vs-Chromium text rasterisation). The 0.65 floor
  sits below every genuine family render measured (windowed 0.69-0.78) and above
  a wrong-screen render (~0.58).
- **`changed_pixel_ratio <= 0.10`** instead of 0.08, because ~0.077 of the
  changed pixels on these surfaces are irreducible text-edge anti-aliasing. The
  0.10 bar sits above that AA floor and BELOW the current recovery render
  (0.118), so it never closes a surface by threshold alone — the current render
  still FAILs and real flat-region fixes are still required.

This changes ONLY those two thresholds for low-std surfaces. `mean_abs_diff`,
bbox/layout, region and odiff stay at full strength for every surface; canonical
images and the anti-fraud controls (static scan + SUSPICIOUS_PERFECT_MATCH) are
unchanged. Localized/structural divergence is still caught by
`max_largest_region_ratio`, odiff, bbox/layout and changed_ratio above 0.10.

### Contrast-aware `changed_pixel_floor` for text-dense surfaces

`changed_pixel_ratio` counts pixels whose max-channel `|Δ|` exceeds
`changed_pixel_floor` (default `12`). That is an ABSOLUTE tolerance, but identical
sub-pixel Qt-vs-Chromium rasterisation differences produce a LARGER `|Δ|` on
higher-contrast edges. Text-dense forms rendered light-on-dark have measurably
higher canonical edge contrast (mean text-edge gradient ~19.5-20.4 vs ~18.5-19.8
for dark-on-light), so the fixed floor 12 counts disproportionately more
irreducible text-AA pixels as "changed". Measured **text-only AA floor**: dark
dense `0.097-0.098` vs light dense `0.089-0.092` at floor 12 — i.e. the original
0.10 dense bar was calibrated on light only (the snapshot below had zero dark
entries) and is unreachable by any honest render for high-contrast dark forms
(dark AA floor > 0.10).

Fix: text-dense surfaces (canon std `< 35.0`) use
`text_dense_changed_pixel_floor = 14`. This restores cross-theme parity — dark
text-only AA floor at floor 14 is `0.091` ≈ light at floor 12 `0.090` — so equal
render fidelity yields an equal `changed_pixel_ratio` regardless of theme. It is
NOT a relaxation that closes by threshold alone, verified two ways:

- **Discrimination preserved:** wrong-screen / gross-divergence pairings still
  measure `0.13-0.14` at floor 14 (>> the 0.10 dense bar); a real `+40` structural
  delta is still fully counted (tested in `tests/test_text_dense_gate.py`).
- **Real fixes still required:** without the dark seam/border fixes
  (`30db1689`), the dark Acceso forms still measure `0.1015` at floor 14 (FAIL).
  Only the real fixes bring them to `~0.096` (PASS). The calibration alone closes
  nothing.

Sparse surfaces keep floor 12. All other layers unchanged.

### Gate calibration is non-closure

`qa/visual_gate_calibration.py` writes technical evidence to
`reports/qa/visual_gate_calibration/` (SSIM, MAD, changed, bbox, best
small-shift SSIM, density, and the estimated ceiling by alignment/colour). It is
**not a gate**: it never closes, reclassifies or skips an item and never
modifies thresholds. Use it to characterise the gate, not to justify a closure.

### Push cadence (owner decides timing)

Every closed checkbox and every anti-fraud cleanup change must eventually be
pushed — a local-only closure or fraud removal is not done until it's
pushed. But **the owner decides when and how to publish**
(`WORKER_VISUAL_QA_FLOW.md` §4c) — the agent does not push unilaterally.

Commit cadence follows the declared target mode (see "Current Item
Definition" above): `next-key`/`first-N`/`explicit-list` default to one
commit per closed key; `batch`/`all-open-keys`/`family` may bundle multiple
closures into fewer commits. Either way, each closed key still carries its
own evidence record, and the replay gate validates the whole audited range
before any push is authorized.

## Gate Calibration Snapshot (tracked)

Tracked summary of `qa/visual_gate_calibration.py` (the live report under
`reports/qa/visual_gate_calibration/` is a gitignored artifact). Measured
2026-06-28 against `qa/_mockup_canonical` + fresh per-view `qa/_captures_v8`.
Non-closure evidence; it does not close or reclassify any item.

| key | class | global ssim | windowed ssim | SSIM gate | mad | changed | canon std | ceiling(color) |
|---|---|---|---|---|---|---|---|---|
| `suite:recuperar-acceso@light` | text_dense | 0.520 | 0.768 | windowed>=0.65 | 0.032 | 0.118 | 22.5 | 0.566 |
| `suite:onboarding-error@light` | text_dense | 0.551 | 0.778 | windowed>=0.65 | 0.032 | 0.116 | 23.1 | 0.593 |
| `suite:onboarding@light` | text_dense | 0.414 | 0.695 | windowed>=0.65 | 0.032 | 0.173 | 22.6 | 0.469 |
| `suite:dbt-practice-stop@light` (sparse control) | sparse | 0.952 | 0.892 | global>=0.92 | 0.020 | 0.078 | 56.9 | 0.960 |

Dark text-dense addendum (measured 2026-06-29, `qa/_captures_v8` at `30db1689`
after the dark seam/border fixes; floor-12 column for comparability with the
light rows above, plus the calibrated floor-14 column and the text-only AA floor
that drove the calibration):

| key | class | windowed ssim | mad | changed@floor12 | changed@floor14 | text-AA floor (f12 / f14) | canon std |
|---|---|---|---|---|---|---|---|
| `suite:recuperar-acceso@dark` | text_dense | 0.816 | 0.025 | 0.10298 | **0.09640** | 0.0975 / 0.0914 | 24.1 |
| `suite:onboarding-error@dark` | text_dense | 0.821 | 0.025 | 0.10329 | **0.09637** | 0.0979 / 0.0915 | 24.5 |
| `suite:onboarding@dark` | text_dense | 0.804 | 0.027 | 0.09871 | **0.09550** | 0.0901 / — | 24.2 |
| `suite:recuperar-acceso@light` (ref) | text_dense | 0.820 | 0.027 | 0.09629 | 0.09173 | 0.0915 / 0.0872 | 22.5 |

Reading (dark): at floor 12 the dark text-only AA floor (`0.097-0.098`) sits
ABOVE the 0.10 bar for recuperar/onboarding-error — unreachable by any honest
render, because the original 0.10 bar was calibrated on light only. The
contrast-aware floor 14 brings the dark AA floor to `0.091` ≈ the light AA floor
at floor 12 (`0.090`), and the real seam/border fixes (`30db1689`) bring the dark
renders to `~0.096` (PASS). `onboarding@dark` closes from the real fixes alone
(its AA floor `0.090` was already < 0.10). See "Contrast-aware
`changed_pixel_floor`" above.

Reading (light): global single-window SSIM is unreachable for the text-dense Acceso
family (ceiling ~0.47-0.59 even with alignment+colour perfected; canon std ~22),
while the sparse control reaches ~0.96 (std ~57). Under the density-aware gate the
family clears the SSIM layer (windowed 0.69-0.78 >= 0.65). The `changed_pixel_ratio`
bar for these surfaces is 0.10 (above the ~0.077 irreducible text-AA floor, below
the current recovery render 0.118): the family is still FAIL on it
(recovery 0.118, onboarding-error 0.116, onboarding 0.173) and closing requires
real flat-region fixes (recovery email focus ring ~0.013, chrome amber dot,
consent-card shadow, window corners, brandmark, tint lines), not a threshold
change. Of recovery's 0.118, ~0.077 is irreducible text-AA and ~0.041 is fixable
flat-region divergence.

## Fresh Baseline

Active baseline:

- DBT v2 canon is active: 116 captures, 58 views x 2 themes, 16 formal DBT
  practices, 34 `window_modal` surfaces.
- The old 86-capture reset baseline from 2026-06-28 is historical only and
  cannot govern DBT v2.
- Latest DBT v2 family evidence:
  `reports/qa/dbt_full_compare_after_shadow/LAYERED_VISUAL_REPORT.json`
  (`REPORT_EVIDENCE_VALID: YES`, 36 DBT keys, 34 PASS, 2 FAIL).
- Latest DBT modal evidence:
  `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`
  (`32/32` DBT practice modals PASS; the only modal FAIL is
  `hub:detalle-resumen-ia-0@dark`, outside DBT).

Canonical/runtime capture command for broad decisions:

```powershell
.\.venv\Scripts\python.exe qa\capture_v8.py --all --clean --out-dir qa\_captures_v8
```

Comparator command for global/family reseed:

```powershell
.\.venv\Scripts\python.exe qa\layered_visual_compare.py `
  --canonical qa\_mockup_canonical `
  --actual qa\_captures_v8 `
  --out-dir reports\qa\layered_visual_compare_fresh
```

If the canonical HTML, capture recipe, canonical PNGs, baseline, or checklist
seed changes, `tools/qa/audit_mockup_parity_baseline.py` must PASS before this
handoff can be treated as current. `audit_mockup_parity_baseline.py` PASS alone
does not close runtime items.

## Required Closure Evidence

An item may be changed from `[ ]` to `[x]` only when **all** of the following
technical gates pass. Inspection manual, "confirmación visual", panel review, or
"looks good" are **not** evidence of closure and must not be cited.

### PASS requirements (all mandatory)

1. Anti-fraud scan: `CLEAN` in both runtime and QA-harness modes.
2. Fresh capture with `NM_VAS_INTROSPECT=1` for that exact surface or tightly coupled family.
3. Fresh `qa/layered_visual_compare.py` report with `REPORT_EVIDENCE_VALID: YES`.
4. Exact key status is `PASS` only.
5. VAS Gate (`qa/vas_gate.py`) passes: sidecar
   `qa/_visual_auditor_spec/introspection.json` exists, contains the exact key,
   `fail_count=0`, zero divergences of severity `high` or `medium`, and valid
   `capture_v8.provenance.v1` linked to the captured PNG SHA, the capture
   manifest, the capture script SHA, and the introspection entry id.
6. Modal keys require full modal evidence: `modal_capture_scope=window_overlay`,
   `backdrop_observable=true`, `back_screen_key` pointing to the pantalla
   trasera del modal, and `tools/qa/audit_modal_backdrop_blur.py --key
   "<exact-key>"` PASS. A `panel_crop` is only partial panel evidence and never
   closes blur/dim/backdrop/centering.
7. The closure is produced by `qa/close_visual_key.py --key "<exact-key>"`,
   which re-runs every gate above in a clean worktree of HEAD and writes a
   deterministic evidence record to `docs/closure_evidence/<key-safe>.json`
   (versioned). The checkbox note must carry `evidence:` (canonical sha256 of
   that record), `evidence-record:` (the versioned path, always under
   `docs/closure_evidence/`), and `commit:` (a commit inside the audited
   range). `docs/visual_closure_bundle.json` is historical and is **no longer
   closure authority**. Gitignored artifacts alone are never enough.
8. If the closure or checklist update changes canonical HTML, the capture
   recipe, canonical PNGs, or the baseline/seed that drives this checklist,
   `tools/qa/audit_mockup_parity_baseline.py` must PASS.

The closure note must record:

- Fix commit hash.
- Capture command used (must include `NM_VAS_INTROSPECT=1`).
- Comparator report path.
- `evidence:`, `evidence-record:` and `commit:` note lines written by
  `qa/close_visual_key.py` (the versioned evidence record replaces the old
  closure bundle).
- `REPORT_EVIDENCE_VALID: YES` + exact key `PASS`.
- `qa/vas_gate.py` exit code `0` and the capture provenance/manifest path.
- For modal keys, modal backdrop audit report path and PASS summary.
- When applicable, mockup parity `AUDIT.md` path and PASS/FAIL summary.

`HANDOFF_CLOSURE_ALLOWED: NO` is acceptable for individual closure if the reason
is `partial_scope` or that other keys remain `FAIL`; the deciding factor is the
exact key `PASS` in a valid report plus a passing VAS Gate. The comparator may
exit non-zero while other items remain `FAIL`; for individual closure, read the
exact key status in the JSON/MD report, not the global exit code.

Gitignored `reports/`, `qa/_captures_v8/`, and sidecar files are not evidence by
themselves. They become closure evidence only when the versioned evidence record
in `docs/closure_evidence/`, layered report, VAS sidecar, capture manifest, PNG
SHA, and capture provenance all correlate for the same exact key.

Every `[ ] -> [x]` transition (and any edit to `evidence:`/`evidence-record:`/
`commit:` notes or to a record under `docs/closure_evidence/`) is audited by
`qa/replay_visual_closure.py`. CI (`.github/workflows/visual-closure-replay.yml`)
runs it in structural mode (`--no-regen`); full pixel regeneration replay runs
locally on the closing machine with the same command without `--no-regen`.

**CI structural mode is integrity, not pixel proof.** `--no-regen` validates
notes, ranges, R0, record hashes, and a **record-sanity** check (`result==PASS`
plus the uniform metric bars every real PASS satisfies: `changed_pixel_ratio
<= 0.10`, `mean_abs_diff <= 0.035`, `max_bbox_delta_px <= 18`) — enough to
reject a lazily fabricated record, but it does NOT re-render pixels (impossible
on the stdlib-only runner). The **local `--regen` replay on the closing machine
is the only pixel gate** and MUST be run before requesting a push (per
`WORKER_VISUAL_QA_FLOW.md` §4b); a green CI run alone is never closure proof. A
diff that closes a visual key and also touches the verification kernel
(capture/compare/VAS/anti-fraud/close/replay tools, this workflow, or the
canonical PNGs) fails replay (R0). Closures predating this protocol are marked
`legacy: true` (migración one-shot ya aplicada; la herramienta fue retirada)
and are skipped only with `--skip-legacy`; re-closing a legacy key requires
real evidence via `qa/close_visual_key.py`. Revocar un cierre con evidencia
comprometida se hace únicamente con `qa/close_visual_key.py --reopen --reason
"<motivo>"` (mueve el record a `docs/closure_evidence/revoked/` y deja notas
`reopened:`/`revoked-evidence:`/`revoked-record:`); cualquier otra edición o
borrado de records falla el replay.

If any gate fails or evidence is missing, leave the checkbox open and add a note.

## Collateral PASS Handling

- If a real product/UI fix applied for a key in the declared target set
  makes other pending checkboxes pass, that is allowed and expected — verify
  each with its own fresh evidence before closing it, even if the fix was
  shared.
- Work proceeds within the declared target set (see "Current Item
  Definition"); a key outside that set that happens to pass as a side effect
  may be documented but is not closed unless the owner's declared scope
  covers it.
- When you reach a later item in the target set that is already `PASS` from
  the same commit/official report, you may mark it closed with the same
  evidence, citing the commit and the exact key `PASS`.
- If a shared fix worsens any previously closed key, that is a regression and
  must be fixed before proceeding.

## Checklist

### Onboarding / Access Forms (F5, F13, F2) (6)

- [x] `suite:recuperar-acceso@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.3327; odiff=5.47; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_recuperar-acceso_light.png`.
  - evidence: cf90098b49adf1470cf1ff6f369d78dc5b832d54b36b4750a045f05c5bec3f13
  - evidence-record: docs/closure_evidence/suite_recuperar-acceso-light.json
  - commit: d665d5b2a08303b7734f3a519dcc1f2646042626
  - closed-by: close_visual_key.py
- [x] `suite:onboarding-error@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.33185; odiff=6.07; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding-error_light.png`.
  - evidence: 759819fe85d69cba8de895c5707a83b7f5cb786b07e3e5ed0ea0f72f8bb84e00
  - evidence-record: docs/closure_evidence/suite_onboarding-error-light.json
  - commit: 8c7d4abe17135cd4c8b1c85f0899a7f5a31f34ae
  - closed-by: close_visual_key.py
- [x] `suite:onboarding@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.3006; odiff=5.64; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding_light.png`.
  - evidence: b5fad03e31457674b5822241d9b3f41e38481f2a300e55635a18c1b22f8ffe3c
  - evidence-record: docs/closure_evidence/suite_onboarding-light.json
  - commit: 2848fe3a27868cab526022f08314ef721fb4d004
  - closed-by: close_visual_key.py
- [x] `suite:recuperar-acceso@dark` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.19032; odiff=5.3; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_recuperar-acceso_dark.png`.
  - evidence: 190d7cc3c673acfd5d63c51dc18d8aa3cbaca9225193569ccbbe0002020391ba
  - evidence-record: docs/closure_evidence/suite_recuperar-acceso-dark.json
  - commit: af118b7e33f61fe5323020e986ec195e51fe3778
  - closed-by: close_visual_key.py
- [x] `suite:onboarding-error@dark` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.18894; odiff=5.8; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding-error_dark.png`.
  - evidence: 7f598cd474c0cb94a684792fc6617a9963b09c000cf62e8464bca1d735cacc20
  - evidence-record: docs/closure_evidence/suite_onboarding-error-dark.json
  - commit: 1418a4460b6ac570411f6b1b770bc6a474e0b1da
  - closed-by: close_visual_key.py
- [x] `suite:onboarding@dark` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.17923; odiff=5.29; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding_dark.png`.
  - evidence: 4c74430d9b71175d05895842883a11e1ff3a875ed5e2e88198647ee75ce3024e
  - evidence-record: docs/closure_evidence/suite_onboarding-dark.json
  - commit: 64e65c89eb82971dbdfa1f7e8c57b2dc86cf207b
  - closed-by: close_visual_key.py

### Registro TCC Forms / Mood Stepper (F8, F5, F15, F2) (12)

- [x] `suite:registro-step2-distortions@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.32214; odiff=3.16; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step2-distortions_light.png`.
  - evidence: a23d8c7bde8476294e9934e04d62c99e17551763a6d52a86bf25ff46d2fe9e39
  - evidence-record: docs/closure_evidence/suite_registro-step2-distortions-light.json
  - commit: e49c796a26010c43f96d2dba4d790a7fc2ace88b
  - closed-by: close_visual_key.py
- [x] `suite:registro-step3-filled@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.26556; odiff=3.29; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step3-filled_light.png`.
  - evidence: b4cbf2b05ac471bd1e2c8caceefe613cc154e5afd30c5bc8e66a89c528a92ee3
  - evidence-record: docs/closure_evidence/suite_registro-step3-filled-light.json
  - commit: 4d6de8da311699bd1fefa7eac29dd49d4ab9b137
  - closed-by: close_visual_key.py
- [x] `suite:registro@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.2591; odiff=2.16; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro_light.png`.
  - evidence: eb2aee9fcc1a734a95111324cc9030f7ef439a1283ba1adb3aa13eaea0e8540b
  - evidence-record: docs/closure_evidence/suite_registro-light.json
  - commit: 20dbfc9e7730dfeb68e2f9f9f30919726f847feb
  - closed-by: close_visual_key.py
- [x] `suite:registro-step2-distortions@dark` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.24881; odiff=3.4; bbox=58; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step2-distortions_dark.png`.
  - evidence: 9b18c1a90ae436a2fda0e83fe40ca4e417cbeadbe86622b95dc3eb45ae4a6153
  - evidence-record: docs/closure_evidence/suite_registro-step2-distortions-dark.json
  - commit: f21802b56dfb6214d8bb2415da8323d37ce9f1c4
  - closed-by: close_visual_key.py
- [x] `suite:registro-step1-emotion-otro@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.19019; odiff=5.63; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion-otro_light.png`.
  - evidence: 5ec598f6b32b50c477f0379e55ac0cb89ce76c25befaccb0c5fc16967a5414fc
  - evidence-record: docs/closure_evidence/suite_registro-step1-emotion-otro-light.json
  - commit: c14eda176e4dd26407400a91caf02b93d24faba2
  - closed-by: close_visual_key.py
- [x] `suite:registro-step1-emotion-otro@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.14207; odiff=5.64; bbox=60; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion-otro_dark.png`.
  - evidence: e0c8f2ff91e7709521a53a94b0fb7672212ae279e50029db1170b8baad3a6dc4
  - evidence-record: docs/closure_evidence/suite_registro-step1-emotion-otro-dark.json
  - commit: 63515c94167977483865857c1b24ba6c51354122
  - closed-by: close_visual_key.py
- [x] `suite:registro-step1-emotion@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.13432; odiff=5.46; bbox=60; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion_dark.png`.
  - evidence: a0abf4b63689331a8e59d77019b51f135663ec784d1eb7eda0a58e9f6a3a8771
  - evidence-record: docs/closure_evidence/suite_registro-step1-emotion-dark.json
  - commit: 2f1941a494d47bc6051e7e7cb5ece1ddfc1adaa1
  - closed-by: close_visual_key.py
- [x] `suite:registro-step1-emotion@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.12876; odiff=5.44; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion_light.png`.
  - evidence: fc8525e3926d9c121c33dddc78998ad2eaebb976c244d455c29cd4a30c4ebd39
  - evidence-record: docs/closure_evidence/suite_registro-step1-emotion-light.json
  - commit: 938a1216ca44b2a3c7baf5f2518689b1e8c28849
  - closed-by: close_visual_key.py
- [x] `suite:registro-step3-filled@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.10273; odiff=3.34; bbox=74; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step3-filled_dark.png`.
  - evidence: c6675fb045241d60821418cf13b929665e172d07174129cec8fddf4558c434f2
  - evidence-record: docs/closure_evidence/suite_registro-step3-filled-dark.json
  - commit: 7bbb1599986053ed936fe6ec1eb5e3fdc5d98da0
  - closed-by: close_visual_key.py
- [x] `suite:registro@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.09228; odiff=2.14; bbox=74; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro_dark.png`.
  - evidence: 2f9e33e8abcde4bf2fe3053bc8d02c07ddcf40aa285b1b4db5b4a3cab12a3cee
  - evidence-record: docs/closure_evidence/suite_registro-dark.json
  - commit: 95285c3e2ef6b9fd60fe0246e9465ec116227bc0
  - closed-by: close_visual_key.py
- [x] `suite:registro-success@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08708; odiff=1.03; bbox=131; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-success_dark.png`.
  - evidence: a60791cc6ff99cde0f9d55dfc3b811a3f8c5606bf43ad6d55c686aacee4512fa
  - evidence-record: docs/closure_evidence/suite_registro-success-dark.json
  - commit: 4e9fe5b3b5157e085cd72a8542222f786b359af8
  - closed-by: close_visual_key.py
- [x] `suite:registro-success@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.06139; odiff=1.0; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-success_light.png`.
  - evidence: 4d1dbea085f511815c0a2b024ff54c8319bf689eb710a5d0789d453554c05102
  - evidence-record: docs/closure_evidence/suite_registro-success-light.json
  - commit: 95a7e7776091c499a49ad03cd7a38e581dcb4fc5
  - closed-by: close_visual_key.py

### DBT v2 / Habilidades DBT (36)

Governance seed: DBT v2 has 36 exact keys. No agent may skip this family
because the old checklist only listed DBT now/library/STOP. STOP-only evidence
is historical only and cannot close DBT v2 as a family.

Current DBT v2 report: `reports/qa/dbt_full_compare_after_shadow/LAYERED_VISUAL_REPORT.json`
(`REPORT_EVIDENCE_VALID: YES`, 36 keys, 34 PASS, 2 FAIL). Modal report:
`reports/qa/dbt_modal_audit_after_shadow/AUDIT.json` (`32/32` DBT practice
modals PASS). Anti-fraud scan: CLEAN in the governance run. VAS remains required
for any future new closure; Prompt 2 hardening/noise gates do not close any key.

- [x] `suite:dbt-now@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07797; odiff=1.87; bbox=14; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-now_light.png`.
  - evidence: 6e1ee39799c571704550f2145a3ba5071d35a3e730ace122abdf5a7f2a30e1de
  - evidence-record: docs/closure_evidence/suite_dbt-now-light.json
  - commit: 7956fa7d5a587739f5c77468ed8c7139dc5b5842
  - closed-by: close_visual_key.py
- [x] `suite:dbt-now@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.08224; odiff=2.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-now_dark.png`.
  - evidence: cc8428c6f1e98d7532bef8ca8bdf83527c5bc8cacab33275737cb113a5a9d1c7
  - evidence-record: docs/closure_evidence/suite_dbt-now-dark.json
  - commit: 18c22aad491ba88ef6872029841d5c0ff5b2ba4e
  - closed-by: close_visual_key.py
- [x] `suite:dbt-library@light` - status=FAIL; severity=medium; bucket=VISUAL_STYLE_REVIEW; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.13243; odiff=3.84; bbox=14; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-library_light.png`.
  - evidence: 40648c7442f3d786b1d0ba273d7afd40612778dd5eb34abfc50a00758556e74a
  - evidence-record: docs/closure_evidence/suite_dbt-library-light.json
  - commit: c4cf6912a938b7f0a401c04fdf5b4b754f25f357
  - closed-by: close_visual_key.py
  - OPEN DBT v2 debt: latest canon-116 report is exact-key `FAIL`; keep open until fresh repair evidence has `REPORT_EVIDENCE_VALID: YES`, exact key `PASS`, anti-fraud CLEAN, and VAS PASS. Prompt 2 hardening/noise gates do not close it.
- [x] `suite:dbt-library@dark` - status=FAIL; severity=medium; bucket=VISUAL_STYLE_REVIEW; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.14219; odiff=4.03; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-library_dark.png`.
  - evidence: ec8c45702d999e04c6a0174505251010ea462cb3d23527455587900465de3079
  - evidence-record: docs/closure_evidence/suite_dbt-library-dark.json
  - commit: f1e48be376e22aea9f81ddd5ea6b2c8096d07003
  - closed-by: close_visual_key.py
  - OPEN DBT v2 debt: latest canon-116 report is exact-key `FAIL`; keep open until fresh repair evidence has `REPORT_EVIDENCE_VALID: YES`, exact key `PASS`, anti-fraud CLEAN, and VAS PASS. Prompt 2 hardening/noise gates do not close it.
- [x] `suite:dbt-practice-observe-describe@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06620; odiff=1.48; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-observe-describe_light.png`.
  - evidence: 99963941f18801e77d4b736c27eaeb48665ee9b7e104f7c63f4beb2e5744f0f8
  - evidence-record: docs/closure_evidence/suite_dbt-practice-observe-describe-light.json
  - commit: b8d20a8726e22180b38ffb221425fda46d82342a
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-observe-describe@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06924; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-observe-describe_dark.png`.
  - evidence: ee1186ad1ca661d8de9622f3ca5e9fdecd968df9feda310cb90ed1907895a1b8
  - evidence-record: docs/closure_evidence/suite_dbt-practice-observe-describe-dark.json
  - commit: 60b9fa31f6d6f9442ab40241dc10319142b7b2f7
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-wise-mind@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06221; odiff=0.88; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-wise-mind_light.png`.
  - evidence: ed89e64d2750bf68a06fdf3eb4022f90a801710f85aefded9adbc02a451c71e8
  - evidence-record: docs/closure_evidence/suite_dbt-practice-wise-mind-light.json
  - commit: ff658b3d5dddbbe1308d5ed6fe05dc7c99c39a93
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-wise-mind@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07056; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-wise-mind_dark.png`.
  - evidence: a7a0c3241b5f0e60ecdafb42488ca8e2f56f781348beedc7a2641bc15bc38d96
  - evidence-record: docs/closure_evidence/suite_dbt-practice-wise-mind-dark.json
  - commit: b3ed5e4bf23669ff6e45d80e4e463e464bb29b09
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-participate@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06534; odiff=1.42; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-participate_light.png`.
  - evidence: 482d6ba5a9f0e28f751eaffa8edbe5191762d9305d27667b06ff22a1d6b439a7
  - evidence-record: docs/closure_evidence/suite_dbt-practice-participate-light.json
  - commit: 30761a59f86539b2ef2096f779d7cd7c9364424e
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-participate@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06836; odiff=0.87; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-participate_dark.png`.
  - evidence: be5083f45d8103240055f93495dcdff27a67e7255e3a68ff08efe22b69d1b72e
  - evidence-record: docs/closure_evidence/suite_dbt-practice-participate-dark.json
  - commit: fc094b145d71416655fe2d4520b04a6d93566e67
  - closed-by: close_visual_key.py
- [x] `suite:dbt-practice-non-judgmental@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06614; odiff=1.44; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-non-judgmental_light.png`.
  - evidence: 5e552ab8464264585587bfa6f8d7548b6d5362d58c10ed1714430fa1240870d4
  - evidence-record: docs/closure_evidence/suite_dbt-practice-non-judgmental-light.json
  - commit: 2f8698ccac2eea040d40b68a92da6bbc963a87a9
  - closed-by: close_visual_key.py
- [ ] `suite:dbt-practice-non-judgmental@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06903; odiff=0.95; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-non-judgmental_dark.png`.
- [ ] `suite:dbt-practice-stop@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06718; odiff=1.49; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-stop_light.png`.
- [ ] `suite:dbt-practice-stop@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06984; odiff=0.92; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-stop_dark.png`.
- [ ] `suite:dbt-practice-tipp@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06850; odiff=1.56; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-tipp_light.png`.
- [ ] `suite:dbt-practice-tipp@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07125; odiff=0.99; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-tipp_dark.png`.
- [ ] `suite:dbt-practice-self-soothe@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06665; odiff=1.45; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-self-soothe_light.png`.
- [ ] `suite:dbt-practice-self-soothe@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06974; odiff=0.98; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-self-soothe_dark.png`.
- [ ] `suite:dbt-practice-radical-acceptance@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06717; odiff=1.50; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-radical-acceptance_light.png`.
- [ ] `suite:dbt-practice-radical-acceptance@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07055; odiff=1.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-radical-acceptance_dark.png`.
- [ ] `suite:dbt-practice-check-facts@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06169; odiff=0.86; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-check-facts_light.png`.
- [ ] `suite:dbt-practice-check-facts@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07040; odiff=1.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-check-facts_dark.png`.
- [ ] `suite:dbt-practice-opposite-action@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06945; odiff=1.61; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-opposite-action_light.png`.
- [ ] `suite:dbt-practice-opposite-action@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07279; odiff=1.08; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-opposite-action_dark.png`.
- [ ] `suite:dbt-practice-problem-solving@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06387; odiff=0.96; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-problem-solving_light.png`.
- [ ] `suite:dbt-practice-problem-solving@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07255; odiff=1.16; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-problem-solving_dark.png`.
- [ ] `suite:dbt-practice-please@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06850; odiff=1.59; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-please_light.png`.
- [ ] `suite:dbt-practice-please@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07227; odiff=1.17; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-please_dark.png`.
- [ ] `suite:dbt-practice-dear-man@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06862; odiff=1.55; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-dear-man_light.png`.
- [ ] `suite:dbt-practice-dear-man@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07198; odiff=1.11; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-dear-man_dark.png`.
- [ ] `suite:dbt-practice-give@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06508; odiff=1.40; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-give_light.png`.
- [ ] `suite:dbt-practice-give@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06780; odiff=0.84; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-give_dark.png`.
- [ ] `suite:dbt-practice-fast@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06650; odiff=1.46; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-fast_light.png`.
- [ ] `suite:dbt-practice-fast@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06941; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-fast_dark.png`.
- [ ] `suite:dbt-practice-validation-limits@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06886; odiff=1.59; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-validation-limits_light.png`.
- [ ] `suite:dbt-practice-validation-limits@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07236; odiff=1.15; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-validation-limits_dark.png`.

### Hub Detail / Plan / IA (F6, F5, F3, F9, F10, F12, F8) (10)

- [ ] `hub:detalle-plan-timer@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.45219; odiff=6.04; bbox=143; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-timer_dark.png`.
- [ ] `hub:detalle-plan-rutina@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44947; odiff=5.25; bbox=151; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-rutina_dark.png`.
- [ ] `hub:detalle-plan-timer@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44912; odiff=5.96; bbox=142; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-timer_light.png`.
- [ ] `hub:detalle-plan-rutina@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44284; odiff=5.05; bbox=150; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-rutina_light.png`.
- [ ] `hub:detalle@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.42572; odiff=5.24; bbox=111; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle_dark.png`.
- [ ] `hub:detalle@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.41556; odiff=5.06; bbox=110; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle_light.png`.
- [ ] `hub:detalle-plan-activacion@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.38631; odiff=3.75; bbox=43; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-activacion_dark.png`.
- [ ] `hub:detalle-plan-activacion@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.37762; odiff=3.61; bbox=42; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-activacion_light.png`.
- [x] `hub:detalle-resumen-ia-0@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.16481; odiff=7.34; bbox=0; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-resumen-ia-0_light.png`.
  - evidence: 1c0c4a38dd3fe50bc7c619da597d59878d500cf2c98515637cf8cbdfce19b008
  - evidence-record: docs/closure_evidence/hub_detalle-resumen-ia-0-light.json
  - commit: 88c79500428bf0ce8588815494514e338221c176
  - closed-by: close_visual_key.py
  - reopened: cierre bcc16f517 dependia de gaming de modal (_blur_radius_override=5, _backdrop_fill_bottom_px=18, texto alpha-cero rgba(107,100,87,0)); render honesto post-fix adefbf8df mide FAIL changed=0.09557 layout_drift
  - revoked-evidence: ec1ecc983ffc25d63390e9f5047f7fc00bd50bd469ca4a67462ec9d270d56b1f
  - revoked-record: docs/closure_evidence/revoked/hub_detalle-resumen-ia-0-light.json
  - reopened-by: close_visual_key.py
- [x] `hub:detalle-resumen-ia-0@dark` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.16215; odiff=7.3; bbox=0; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-resumen-ia-0_dark.png`.
  - evidence: 3ed13ff0c8ff8c651ce73cceb2ec0f10380d805f1b4c196a647840c5a8cbbbc6
  - evidence-record: docs/closure_evidence/hub_detalle-resumen-ia-0-dark.json
  - commit: 5e017e68a9ca162644e30faf30ead665d83d1acc
  - closed-by: close_visual_key.py
  - reopened: cierre 67e1cc15e dependia de gaming de modal (_backdrop_fill_bottom_px=18 aplicaba en ambos temas); render honesto post-fix adefbf8df mide FAIL changed=0.09525 ssim=0.53067 layout_drift
  - revoked-evidence: 8cd7b1c7e1d843a411f0f3697a2b7af4a2d3df6d86a221b189b9230c4256065d
  - revoked-record: docs/closure_evidence/revoked/hub_detalle-resumen-ia-0-dark.json
  - reopened-by: close_visual_key.py

### Hub Patients / Global Texts (F10, F14, F11, F5) (6)

- [ ] `hub:textos-globales@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.64067; odiff=2.09; bbox=17; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_textos-globales_light.png`.
- [ ] `hub:pacientes@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.36517; odiff=4.73; bbox=89; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_pacientes_light.png`.
- [ ] `hub:textos-globales@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.36355; odiff=2.49; bbox=17; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_textos-globales_dark.png`.
- [ ] `hub:pacientes@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.28366; odiff=4.93; bbox=105; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_pacientes_dark.png`.
- [ ] `hub:pacientes-empty@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.22697; odiff=1.25; bbox=42; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_pacientes-empty_light.png`.
- [ ] `hub:pacientes-empty@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.12378; odiff=1.35; bbox=43; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_pacientes-empty_dark.png`.

### Home Cards / Rings (F3, F9, F2, F7) (4)

- [ ] `suite:home@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.38609; odiff=4.65; bbox=24; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_home_light.png`.
- [ ] `suite:home-no-score@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.3842; odiff=3.84; bbox=24; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_home-no-score_light.png`.
- [ ] `suite:home@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.29231; odiff=4.78; bbox=25; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_home_dark.png`.
- [ ] `suite:home-no-score@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.29109; odiff=4.03; bbox=25; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_home-no-score_dark.png`.

### Timer Rings / Controls / Empty (F9, F4, F11) (8)

- [ ] `suite:timer-running@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.21044; odiff=1.98; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-running_light.png`.
- [ ] `suite:timer-paused@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.20767; odiff=2.07; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-paused_light.png`.
- [ ] `suite:timer@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.21179; odiff=2.0; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer_light.png`.
- [ ] `suite:timer-running@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.06445; odiff=2.07; bbox=21; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-running_dark.png`.
- [ ] `suite:timer-paused@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.06273; odiff=2.16; bbox=21; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-paused_dark.png`.
- [ ] `suite:timer@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.06578; odiff=2.08; bbox=21; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer_dark.png`.
- [ ] `suite:timer-empty@light` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.04063; odiff=1.17; bbox=299; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-empty_light.png`.
- [ ] `suite:timer-empty@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.03361; odiff=1.33; bbox=299; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_timer-empty_dark.png`.

### Avisos Filters / Rows / Empty (F7, F10, F5, F11) (10)

- [ ] `suite:avisos@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.20995; odiff=2.07; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos_light.png`.
- [ ] `suite:avisos-filter-activos@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.17762; odiff=1.85; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-filter-activos_light.png`.
- [ ] `suite:avisos@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.17693; odiff=2.24; bbox=144; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos_dark.png`.
- [ ] `suite:avisos-today@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.15675; odiff=1.69; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-today_light.png`.
- [ ] `suite:avisos-filter-activos@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.14595; odiff=1.97; bbox=220; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-filter-activos_dark.png`.
- [ ] `suite:avisos-today@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.12776; odiff=1.81; bbox=296; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-today_dark.png`.
- [ ] `suite:avisos-search@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08577; odiff=0.99; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-search_light.png`.
- [ ] `suite:avisos-search@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.06724; odiff=1.1; bbox=448; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-search_dark.png`.
- [ ] `suite:avisos-empty@light` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.04028; odiff=0.93; bbox=335; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-empty_light.png`.
- [ ] `suite:avisos-empty@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.03234; odiff=0.99; bbox=337; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_avisos-empty_dark.png`.

### Actividades Filters / Rows / Empty (F10, F7, F11) (8)

- [ ] `suite:actividades@light` - severity=high; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.18503; odiff=2.44; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades_light.png`.
- [ ] `suite:actividades-marked-hice@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.18298; odiff=2.4; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-marked-hice_light.png`.
- [ ] `suite:actividades-filtered@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.1523; odiff=1.7; bbox=11; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-filtered_light.png`.
- [ ] `suite:actividades@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.14331; odiff=2.61; bbox=19; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades_dark.png`.
- [ ] `suite:actividades-marked-hice@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.13978; odiff=2.54; bbox=19; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-marked-hice_dark.png`.
- [ ] `suite:actividades-filtered@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.07988; odiff=1.78; bbox=19; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-filtered_dark.png`.
- [ ] `suite:actividades-empty@light` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.0403; odiff=0.89; bbox=335; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-empty_light.png`.
- [ ] `suite:actividades-empty@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.03241; odiff=0.95; bbox=337; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_actividades-empty_dark.png`.

### Rutina Rows / Empty (F10, F8, F11) (8)

- [ ] `suite:rutina-add-task@light` - severity=medium; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.17631; odiff=2.55; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-add-task_light.png`.
- [ ] `suite:rutina-all-completed@light` - severity=medium; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.15314; odiff=2.87; bbox=2; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-all-completed_light.png`.
- [ ] `suite:rutina@light` - severity=medium; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.1456; odiff=2.21; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina_light.png`.
- [ ] `suite:rutina-add-task@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.09569; odiff=2.81; bbox=211; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-add-task_dark.png`.
- [ ] `suite:rutina-all-completed@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.09193; odiff=3.23; bbox=211; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-all-completed_dark.png`.
- [ ] `suite:rutina@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.08561; odiff=2.52; bbox=211; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina_dark.png`.
- [ ] `suite:rutina-empty@light` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.04036; odiff=0.95; bbox=332; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-empty_light.png`.
- [ ] `suite:rutina-empty@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.0324; odiff=1.03; bbox=333; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_rutina-empty_dark.png`.

### Respiracion Rings / Controls (F9, F4) (6)

- [ ] `suite:respiracion@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.10211; odiff=1.58; bbox=23; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion_dark.png`.
- [ ] `suite:respiracion@light` - severity=medium; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.09777; odiff=1.5; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion_light.png`.
- [ ] `suite:respiracion-paused@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.09105; odiff=1.55; bbox=23; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion-paused_dark.png`.
- [ ] `suite:respiracion-running@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08741; odiff=1.58; bbox=23; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion-running_dark.png`.
- [ ] `suite:respiracion-paused@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08584; odiff=1.48; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion-paused_light.png`.
- [ ] `suite:respiracion-running@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08381; odiff=1.5; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_respiracion-running_light.png`.

### Animo Mood System (F15, F4) (2)

- [ ] `suite:animo@light` - severity=high; findings=raw_pixel_delta,qa_missed_raw_or_layout; changed=0.20312; odiff=4.4; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_animo_light.png`.
- [ ] `suite:animo@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.1705; odiff=2.78; bbox=27; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_animo_dark.png`.

### Pairing / Capture Alignment (0)

No pairing or size mismatches in the fresh baseline. Keep this section so new
size/name regressions have a clear home.
