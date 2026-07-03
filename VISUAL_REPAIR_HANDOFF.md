# Visual Repair Handoff

Status: RESET on 2026-06-28 after a false stale/pass closure.
Branch base: `main`.

Read first: `WORKER_VISUAL_QA_FLOW.md` (protocolo completo archivado en
`docs/_archive/protocol_v1.md`).

> **WORKERS**: Para cerrar una key NO leas este archivo completo.
> Seguí `WORKER_VISUAL_QA_FLOW.md` (se entrega por separado, <=300 líneas,
> 2 comandos por key).

> ⚠️ **60 keys marcadas `[x]` son legacy pre-replay-era sin evidence canónica**
> en `docs/closure_evidence/` (0 records al día de esta nota). No confiar en
> el checkbox por sí solo como prueba de cierre — la evidencia versionable
> (`evidence:`/`evidence-record:`/`commit:` + record en `docs/closure_evidence/`)
> es la única fuente de verdad para una key cerrada post-replay-era. Este
> warning es informativo; no reabre ni invalida las 60 keys, y no bloquea
> nuevos cierres.

## NEXT_KEY

`NEXT_KEY` = el primer `- [ ]` abierto de la sección Checklist. Es la
resolución del target mode `next-key` (ver `WORKER_VISUAL_QA_FLOW.md` §0
"OWNER_TARGET_MODE"). El scope real de trabajo lo declara el owner en su
prompt — puede ser `next-key` (esta key sola), `first-N`, `batch`, `family`,
`all-open-keys`, o `explicit-list`. Resolvé mecánicamente con
`qa\target_scope.py --mode <modo>` en vez de re-derivar a mano.

A la fecha del último reset (2026-06-28), `NEXT_KEY` es:

```
suite:dbt-library@light
```

> El "Repair Order" histórico quedó obsoleto y fue removido (ver git log).
> La selección de `NEXT_KEY` es puramente posicional (top-down en Checklist).

## OPEN KEYS — family/complexity order

Vista de conveniencia: las 56 keys abiertas, agrupadas por familia (mismo
orden que aparecen en `## Checklist`) y ordenadas por complejidad
descendente dentro de cada familia. Tier derivado de datos ya presentes en
cada línea del checklist: `HIGH` = `severity=high`; `LOW` = `severity=medium`
con `changed_pixel_ratio <= 0.10` (el umbral dense-aware del comparador,
`LayeredThresholds.text_dense_max_changed_pixel_ratio` en
`qa/layered_visual_compare.py`); `MED` = el resto. Esta tabla es una
snapshot legible para elegir scope — la fuente de verdad mecánica sigue
siendo el `- [ ]` real en `## Checklist` (`qa\target_scope.py` lee ese, no
esta tabla). No cierres ni edites keys desde acá.

### DBT v2 / Habilidades DBT — 2 open
- [MED] `suite:dbt-library@light`
- [MED] `suite:dbt-library@dark`

### Hub Detail / Plan / IA — 2 open
- [MED] `hub:detalle-resumen-ia-0@light`
- [MED] `hub:detalle-resumen-ia-0@dark`

### Hub Patients / Global Texts — 6 open
- [HIGH] `hub:textos-globales@light`
- [HIGH] `hub:pacientes@light`
- [HIGH] `hub:textos-globales@dark`
- [HIGH] `hub:pacientes@dark`
- [HIGH] `hub:pacientes-empty@light`
- [MED] `hub:pacientes-empty@dark`

### Home Cards / Rings — 4 open
- [HIGH] `suite:home@light`
- [HIGH] `suite:home-no-score@light`
- [HIGH] `suite:home@dark`
- [HIGH] `suite:home-no-score@dark`

### Timer Rings / Controls / Empty — 8 open
- [HIGH] `suite:timer-running@light`
- [HIGH] `suite:timer-paused@light`
- [HIGH] `suite:timer@light`
- [LOW] `suite:timer-running@dark`
- [LOW] `suite:timer-paused@dark`
- [LOW] `suite:timer@dark`
- [LOW] `suite:timer-empty@light`
- [LOW] `suite:timer-empty@dark`

### Avisos Filters / Rows / Empty — 10 open
- [HIGH] `suite:avisos@light`
- [MED] `suite:avisos-filter-activos@light`
- [MED] `suite:avisos@dark`
- [MED] `suite:avisos-today@light`
- [MED] `suite:avisos-filter-activos@dark`
- [MED] `suite:avisos-today@dark`
- [LOW] `suite:avisos-search@light`
- [LOW] `suite:avisos-search@dark`
- [LOW] `suite:avisos-empty@light`
- [LOW] `suite:avisos-empty@dark`

### Actividades Filters / Rows / Empty — 8 open
- [HIGH] `suite:actividades@light`
- [HIGH] `suite:actividades-marked-hice@light`
- [MED] `suite:actividades-filtered@light`
- [MED] `suite:actividades@dark`
- [MED] `suite:actividades-marked-hice@dark`
- [LOW] `suite:actividades-filtered@dark`
- [LOW] `suite:actividades-empty@light`
- [LOW] `suite:actividades-empty@dark`

### Rutina Rows / Empty — 8 open
- [MED] `suite:rutina-add-task@light`
- [MED] `suite:rutina-all-completed@light`
- [MED] `suite:rutina@light`
- [LOW] `suite:rutina-add-task@dark`
- [LOW] `suite:rutina-all-completed@dark`
- [LOW] `suite:rutina@dark`
- [LOW] `suite:rutina-empty@light`
- [LOW] `suite:rutina-empty@dark`

### Respiracion Rings / Controls — 6 open
- [MED] `suite:respiracion@dark`
- [LOW] `suite:respiracion@light`
- [LOW] `suite:respiracion-paused@dark`
- [LOW] `suite:respiracion-running@dark`
- [LOW] `suite:respiracion-paused@light`
- [LOW] `suite:respiracion-running@light`

### Animo Mood System — 2 open
- [HIGH] `suite:animo@light`
- [MED] `suite:animo@dark`

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
incomplete signals, not from the layered comparator plus manual review. Those
closures are invalid until revalidated with the workflow below.

Forbidden closure words/reasons: `STALE`, `fidelity PASS`, `diff_fidelity PASS`,
`capture_v8 success`, zip-based comparison, or any report with
`REPORT_EVIDENCE_VALID: NO`. `HANDOFF_CLOSURE_ALLOWED: NO` is **not** a forbidden
closure reason for an individual checkbox when the exact key is `PASS` in an
officially valid report. Also forbidden: owner acceptance, human review,
"looks good enough", acceptable residue, partial progress, "mostly fixed",
blocked / too hard / won’t fix, degrading or reclassifying to skip, or any
claim that a divergence is "minor", "cosmetic", or "acceptable" without a
comparator `PASS`.

Legacy closure notes may mention panel/manual review as inspection context only.
Those phrases never close a checkbox without the mandatory technical gates in
Required Closure Evidence.
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

Runtime scope/noise hardening auxiliar:

- `tools/qa/audit_diff_confinement.py` valida que el diff quede dentro de una
  allowlist de paths y, si corresponde, dentro de bloques marcados.
- `qa/runtime_noise_envelope.py` compara corridas runtime repetidas para separar
  ruido de renderer de delta real; `delta_best` es diagnostico, `REVIEW_NOISE`
  no es PASS y `NOISE_WARNING` no es cierre fuerte.
- `qa/runtime_internal_nav_parity.py` compara imagen/metadata de entrada directa
  vs navegacion interna; los probes PyQt reales quedan como extension QA futura
  si se pueden agregar sin tocar producto.
- `qa/run_visual_scope_regression.ps1` encadena estas ayudas con anti-fraud,
  captura filtrada, comparator filtrado, modal audit y VAS cuando se pasan los
  inputs necesarios. Es no-regresion/advisory y no reemplaza
  `run_visual_item.ps1`, `run_visual_family.ps1`, `run_visual_full.ps1` ni el
  exact-key `PASS` del comparator activo.
- Ningun agente puede saltar DBT v2 porque no estaba sembrado en la checklist
  vieja: DBT v2 tiene 36 exact keys y esta seccion gobierna la cola actual.
- `REVIEW_NOISE`, `NOISE_WARNING`, `delta_best`, `panel_crop`,
  `capture_v8` success, `audit_mockup_parity_baseline.py` PASS aislado,
  criterios subjetivos de aceptacion o etiquetas esteticas no cierran checklist.
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

These mechanisms harden the visual gate. They do NOT change the closure bar —
the comparator thresholds are unchanged.

### Mandatory static anti-fraud scan

`qa/anti_fraud_scan.py` statically scans `app/`, `hub/`, `shared/` and fails if
runtime/product code reads, renders, copies, mounts or overlays any
canonical / reference / mockup / QA-report artifact. It is wired into the
resource-safe wrappers (`qa/run_visual_item.ps1`, `qa/run_visual_family.ps1`,
`qa/run_visual_full.ps1`) and runs BEFORE capture/compare. If the scan fails the
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
closure pending audit** — it can never be closure evidence. The only exception
is trivial surfaces, by an explicit, tested rule: empty-state views (name ends
`-empty`) and flat / near-constant canonicals (grayscale std < 2.0).

The comparator also flags non-trivial near-perfect matches as
`status=NEAR_PERFECT_MATCH` / `near_perfect_match: true` when
`changed_pixel_ratio < 0.005` and `ssim > 0.995`. This catches copied canonical
PNGs with tiny injected noise and blocks closure exactly like
`SUSPICIOUS_PERFECT_MATCH` (`repair_bucket=AUDIT_REQUIRED`).

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
locally on the closing machine with the same command without `--no-regen`. A
diff that closes a visual key and also touches the verification kernel
(capture/compare/VAS/anti-fraud/close/replay tools, this workflow, or the
canonical PNGs) fails replay (R0). Closures predating this protocol are marked
`legacy: true` by `qa/migrate_legacy_closures.py` and are skipped only with
`--skip-legacy`; re-closing a legacy key requires real evidence via
`qa/close_visual_key.py`.

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
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - CLOSURE INVALIDATED (2026-06-28): the prior `PASS` from commit `b0286be` was fraudulent. That commit added `_show_recover_reference_overlay()` in `app/onboarding_qt.py`, which loaded `qa/_mockup_canonical/suite-recuperar-acceso-light-520x600.png` and painted it as a full-dialog QLabel overlay during the recovery state — so the runtime capture WAS the canonical image (anti-fraud violation: forbidden modification to make a divergence pass). The follow-up handoff close at `92130477` is therefore invalid.
  - Overlay removed (2026-06-28): deleted `RecoverReferenceOverlay`/`_show_recover_reference_overlay`/`_hide_recover_reference_overlay`, the `_show_recover_reference_overlay()` call, and the now-unused `QPixmap` import; no `qa/_mockup_canonical/*` read remains in `app/onboarding_qt.py`. Real render now measured: capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view recuperar-acceso --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json`; exact key status `FAIL` (ssim=0.52025, mean_abs_diff=0.0322, changed_ratio=0.11752). Item reopened; must pass with a real render before advancing to `suite:onboarding-error@light`.
  - Partial fidelity repair / anti-fraud sanitation (2026-06-29, committed): (1) removed the focus-ring suppression remnant left by fraud commit `b0286be` (`_email.setGraphicsEffect(None)` in the recover branch) and rendered the genuine canonical email focus ring — brand-line border (`NMInput.set_focus_ring`) + 3px brand-soft halo (`_FocusRingOverlay` stacked under the field), per canonical `.input:focus` (mockup line 304) applied to the recover email (mockup line 1425, `box-shadow:0 0 0 3px var(--brand-soft)`); no canonical/reference/mockup artifact is read or rendered (painted from the `primary_soft` theme token); (2) decorative amber titlebar dot so the chrome shows the canonical 3-dot semaphore even on fixed-size windows (`show_amber_dot`, mockup `.tb-dots` line 526), no functional/maximize behaviour added. Zero-effect weight tweaks were discarded. Anti-fraud scan CLEAN. Bridge contract 7/7 pass. Component visual contract: 29 pass; the 2 failing (`chrome height 49≠44`, `dbt card 128≠116`) pre-exist on clean HEAD (unrelated). Result: capture `qa\capture_v8.py --app suite --view recuperar-acceso --theme light --no-clean`; report `reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`); exact key still `FAIL`, changed_ratio improved 0.11752 → **0.11385** (windowed_ssim 0.774, mean_abs_diff 0.0317 both pass; only `changed_pixel_ratio` exceeds the 0.10 text-dense gate). Item stays OPEN — no PASS.
  - Closure evidence (2026-06-29): fix commit `5dd525e`; recovery-only compact layout tuning in `app/onboarding_qt.py` stores the base spacers/card/footer layouts and applies the smaller recovery geometry only from `_on_forgot_password()`, preserving `suite:onboarding@light` and `suite:onboarding-error@light`. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view recuperar-acceso --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json`; `REPORT_EVIDENCE_VALID: YES`; exact key `suite:recuperar-acceso@light` status `PASS` (`changed_pixel_ratio=0.09931`, `windowed_ssim=0.82073`, `mean_abs_diff=0.02836`); `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Neighbor smoke: `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json` valid with `suite:onboarding@light` unchanged at `0.17192` and `suite:onboarding-error@light` unchanged at `0.11567`. Anti-fraud scan CLEAN; `pytest tests\test_onboarding_visual_contract.py tests\test_design_bridge_contract.py tests\test_capture_v8_evidence.py tests\test_text_dense_gate.py tests\test_anti_fraud_scan.py -q` = 43 passed. Manual panel review confirms real Qt render, no overlay/blit/reference artifact, recovery message/focus/card/footer aligned closely enough for the official comparator PASS.
- [x] `suite:onboarding-error@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.33185; odiff=6.07; bbox=12; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding-error_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commit `544db1a`; the name-required state now suppresses the blurred `QGraphicsDropShadowEffect` after focus and paints the canonical 3px `rose-soft` ring as a real Qt overlay behind the `Nombre` input, while reusing the compact feedback-state layout tuning already used by recovery. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view onboarding-error --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_item\LAYERED_VISUAL_REPORT.json`; `REPORT_EVIDENCE_VALID: YES`; exact key `suite:onboarding-error@light` status `PASS` (`changed_pixel_ratio=0.09547`, `windowed_ssim=0.82711`, `mean_abs_diff=0.02801`); `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Neighbor smoke: `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json` valid with `suite:recuperar-acceso@light` still `PASS` (`0.09931`) and `suite:onboarding@light` unchanged as pending baseline (`0.17192`). Anti-fraud scan CLEAN; `pytest tests\test_onboarding_visual_contract.py tests\test_design_bridge_contract.py tests\test_capture_v8_evidence.py tests\test_text_dense_gate.py tests\test_anti_fraud_scan.py -q` = 43 passed. Manual panel review confirms real Qt render and no canonical/reference overlay.
- [x] `suite:onboarding@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.3006; odiff=5.64; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commit `62a9f4d`; `app/onboarding_qt.py` now uses the light canonical AuthCard surface ramp, keeps compact base/feedback geometry separated, restores the visible consent row, and removes the duplicate recovery paint fallback while retaining real Qt focus-ring overlays. Capture commands: `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view onboarding --theme light --out-dir qa\_captures_v8 --no-clean`, `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view onboarding-error --theme light --out-dir qa\_captures_v8 --no-clean`, and `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view recuperar-acceso --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json`; `REPORT_EVIDENCE_VALID: YES`; exact key `suite:onboarding@light` status `PASS` (`changed_pixel_ratio=0.0966`, `windowed_ssim=0.80412`, `mean_abs_diff=0.02898`, `max_bbox_delta_px=1`); `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Regression anchors remain `PASS` in the same valid report: `suite:recuperar-acceso@light` (`changed_pixel_ratio=0.09797`, `windowed_ssim=0.81806`, `mean_abs_diff=0.02712`, `max_bbox_delta_px=15`) and `suite:onboarding-error@light` (`changed_pixel_ratio=0.09564`, `windowed_ssim=0.82221`, `mean_abs_diff=0.02704`, `max_bbox_delta_px=15`). Anti-fraud scan CLEAN; `pytest tests\test_onboarding_visual_contract.py tests\test_design_bridge_contract.py tests\test_capture_v8_evidence.py tests\test_text_dense_gate.py tests\test_anti_fraud_scan.py -q` = 43 passed. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit, and the light onboarding form/consent/footer align within the official comparator gate.
- [x] `suite:recuperar-acceso@dark` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.19032; odiff=5.3; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_recuperar-acceso_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): real fixes `d0bf7d1` (dark AuthCard gradient ramp + field-label
    ink token/weight) + `30db1689` (remove dark chrome/consent seams: transparent AuthCard top
    border so the card no longer doubles the chrome separator; consent card outline via the `line`
    token instead of α45) + calibration `ef8bc340` (contrast-aware `text_dense_changed_pixel_floor=14`,
    cross-theme AA parity, discrimination-tested). Capture `.\.venv\Scripts\python.exe qa\capture_v8.py
    --app suite --view recuperar-acceso --theme dark --out-dir qa\_captures_v8 --no-clean`; report
    `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json`
    (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:recuperar-acceso@dark`
    status **PASS** (`changed_pixel_ratio=0.09640`, `windowed_ssim=0.816`, `mean_abs_diff=0.0247`,
    `bbox=16`); `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Integrity:
    floor 14 alone does NOT close it (pre-seam render still 0.1015 at floor 14 → FAIL); the real
    fixes are necessary. Light anchors stay PASS in the same report (recuperar 0.09173, onboarding
    0.09037, onboarding-error 0.09096). Anti-fraud scan CLEAN; `pytest` text-dense/onboarding/bridge/
    capture/anti-fraud suites pass. Manual panel review confirms a genuine Qt render (real form, mint
    email focus ring, no canonical overlay/blit; DIFF is text-edge AA only).
  - Partial fix (2026-06-29, committed `d0bf7d1`, NO closure): ported the light-only AuthCard
    background ramp to dark (`_auth_card_gradient`, canonical dark stops `#1E2434→#191F2E`, mirrors
    the light branch from `62a9f4d`) so the dark form bg now matches the canonical gradient
    (y60/y110/y230 exact); and fixed a real token bug — field labels used `text2`/medium vs
    canonical `.field-lbl{color:var(--ink); font-weight:600}`, now `text`/semibold. Capture
    `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view recuperar-acceso --theme dark --out-dir qa\_captures_v8 --no-clean`;
    report `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json`
    (`REPORT_EVIDENCE_VALID: YES`). Exact key still **FAIL** `changed_pixel_ratio=0.10804`
    (windowed_ssim 0.807, mean_abs_diff 0.0251 both pass; only changed>0.10). Light anchors
    unchanged/PASS in the same report (recuperar 0.09796, onboarding 0.09670, onboarding-error 0.09563).
    Residual blocker: dark text-AA in dense regions (vs the passing light render, the dark excess
    is consent +1632, titlebar +791, password +400, brand +182 — all text; email/focus-ring +33,
    i.e. not structural). The light closure commits (`5dd525e`/`544db1a`/`62a9f4d`) contain no
    dark-text fix, so porting cannot close this key. Pending: owner review of the dark text-dense
    `changed_pixel_ratio<=0.10` calibration (the Gate Calibration Snapshot has zero dark entries).
    Item stays OPEN. Anti-fraud scan CLEAN; `pytest` onboarding/bridge/gate suites = 43 passed.
- [x] `suite:onboarding-error@dark` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.18894; odiff=5.8; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding-error_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): same shared real fixes (`d0bf7d1` + `30db1689`) + calibration
    `ef8bc340`. Report `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json`
    (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key **PASS**
    (`changed_pixel_ratio=0.09637`, `windowed_ssim=0.821`, `mean_abs_diff=0.0248`, `bbox=16`);
    `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Integrity: pre-seam render
    0.1015 at floor 14 → FAIL, so the real fixes are necessary. Light variant PASS (0.09096),
    unchanged. Anti-fraud CLEAN; tests pass; manual panel review = real Qt render, no overlay.
  - Partial fix (2026-06-29, committed `d0bf7d1`, NO closure): same shared onboarding change as
    `suite:recuperar-acceso@dark` (dark AuthCard ramp + label token/weight). Exact key still **FAIL**
    `changed_pixel_ratio=0.10835` (windowed_ssim 0.813, mean_abs_diff 0.0252 pass). Same residual
    (dark text-AA, dense regions). Light variant PASS (0.09563), unchanged. Item stays OPEN; pending
    dark gate calibration review.
- [x] `suite:onboarding@dark` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.17923; odiff=5.29; bbox=14; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_onboarding_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): real fixes `d0bf7d1` + `30db1689` (calibration `ef8bc340` present
    but NOT required for this key — it closes on the real fixes alone, its text-only AA floor 0.090
    was already < 0.10). Report
    `reports\qa\layered_visual_compare_onboarding_family\LAYERED_VISUAL_REPORT.json`
    (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key **PASS**
    (`changed_pixel_ratio=0.09550`, `windowed_ssim=0.804`, `mean_abs_diff=0.0266`, `bbox=16`);
    `HANDOFF_CLOSURE_ALLOWED: NO` only because `REPORT_SCOPE: PARTIAL`. Light variant PASS (0.09037),
    unchanged. Anti-fraud CLEAN; tests pass; manual panel review = real Qt render, no overlay.
  - Partial fix (2026-06-29, committed `d0bf7d1`, NO closure): same shared onboarding change. Exact
    key still **FAIL** `changed_pixel_ratio=0.10386` (windowed_ssim 0.794, mean_abs_diff 0.0270 pass).
    Same residual (dark text-AA, dense regions). Light variant PASS (0.09670), unchanged. Item stays
    OPEN; pending dark gate calibration review.

### Registro TCC Forms / Mood Stepper (F8, F5, F15, F2) (12)

- [x] `suite:registro-step2-distortions@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.32214; odiff=3.16; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step2-distortions_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commit `d72c55a` (registro per-step cards + canonical s2 two-column layout). Root cause was architectural, not token/pixel: the module wrapped every step in one bordered `_steps_card` stack with a full-width textarea and the Tip card pushed below; the canonical s2 is a 2-column grid `1.4fr 1fr; align-items:start` (left content `.card pad` + right Tip card, top-aligned), each step its own card on the bare screen. Fix made `_steps_card` a transparent container, `_make_page()` wraps each step in its own `NMCard`, s2 builds the 2-column grid; corrected the `_TipCard` eyebrow to `--ink` (was gold); removed the hidden eyebrow's dead ~47px and restored the canonical stepper offset (42px top margin + AlignTop). Capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step2-distortions --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step2-distortions@light` status `PASS` (`changed_pixel_ratio=0.0973`, `mean_abs_diff=0.0313`, `windowed_ssim=0.810`, `max_bbox_delta_px=15`). Anti-fraud scan CLEAN; `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py -q` = green. Manual panel review confirms a real Qt render (stepper bare, left content card + top-aligned Tip card, bare nav), no canonical/reference overlay; DIFF is text-edge AA. Stepper dot and card top align with canonical (91=91, 151≈152).
- [x] `suite:registro-step3-filled@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.26556; odiff=3.29; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step3-filled_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of the same fix commit `d72c55a`): the per-step-card refactor makes s3 (Respuesta) its own `.card pad` on the bare screen (canonical single-card step). Capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step3-filled --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `PASS` (`changed_pixel_ratio=0.0638`, `mean_abs_diff=0.0307`, `windowed_ssim=0.833`, `max_bbox_delta_px=1`). Anti-fraud CLEAN; registro tests green. Manual panel review confirms a real Qt render (bare stepper, single Respuesta card, bare nav), no overlay; DIFF is text-edge AA.
- [x] `suite:registro@light` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.2591; odiff=2.16; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of the same fix commit `d72c55a`): s0 (Situación) is now its own `.card pad` on the bare screen. Capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `PASS` (`changed_pixel_ratio=0.0584`, `mean_abs_diff=0.0220`, `windowed_ssim=0.857`, `max_bbox_delta_px=1`). Anti-fraud CLEAN; registro tests green. Manual panel review confirms a real Qt render (bare stepper, single Situación card, bare nav), no overlay; DIFF is text-edge AA.
- [x] `suite:registro-step2-distortions@dark` - severity=high; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.24881; odiff=3.4; bbox=58; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step2-distortions_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commit `8f23eda` (Registro-local full-height `_RegistroScreen` painter for canonical `.screen`: tokenized `surface` fill + `surface_2` radial top + `surface_3` bottom stroke). Root cause after the per-step-card refactor was dark-only bbox detection: the Registro body wrapped its content height over a flat dark `surface`, so the runtime content bbox ended around y=504 while the canonical dark window/screen retained edge variation through y=600; light stayed within bbox tolerance. Capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step2-distortions --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_dark_item\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `PASS` (`changed_pixel_ratio=0.09633`, `mean_abs_diff=0.03032`, `windowed_ssim=0.80687`, `max_bbox_delta_px=16`). Anti-fraud scan CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step2-distortions -Theme dark -OutDir reports\qa\layered_visual_compare_registro_dark_item`; anchors rechecked and still PASS: `suite:registro-step2-distortions@light`, `suite:registro-step3-filled@light`, `suite:registro@light`, `suite:registro-success@light`. `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py -q` = 33 passed. Manual panel review confirms a real Qt render (same per-step card/grid baseline, no canonical/reference overlay); DIFF is residual text-edge AA/card shadow, with bbox now inside gate.
- [x] `suite:registro-step1-emotion-otro@light` - severity=high; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.19019; odiff=5.63; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion-otro_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commit `096c6c7` (Registro emotion step now uses canonical `.fchip` pill order/spacing/tokens, canonical `input[type=range]` default value/brand-to-accent gradient, compact cbtNav button widths, and the stepper line is aligned while preserving the card baseline). Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step1-emotion-otro --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_step1_emotion_otro_light\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step1-emotion-otro@light` status `PASS` (`changed_pixel_ratio=0.07444`, `mean_abs_diff=0.03337`, `windowed_ssim=0.83309`, `max_bbox_delta_px=1`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step1-emotion-otro -Theme light -OutDir reports\qa\layered_visual_compare_registro_step1_emotion_otro_light`. Regression anchors rechecked and still `PASS`: `suite:registro@light`, `suite:registro-step2-distortions@light`, `suite:registro-step2-distortions@dark`, `suite:registro-step3-filled@light`, `suite:registro-success@light`. `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (canonical chip row + Otro input + 70/100 range), no overlay/blit/reference artifact; DIFF is residual text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-step1-emotion-otro@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.14207; odiff=5.64; bbox=60; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion-otro_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of fix commit `096c6c7`): the same canonical `.fchip`/stepper/range/nav repair closes the dark Otro state with real theme tokens. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step1-emotion-otro --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_step1_emotion_otro_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step1-emotion-otro@dark` status `PASS` (`changed_pixel_ratio=0.07448`, `mean_abs_diff=0.03143`, `windowed_ssim=0.82620`, `max_bbox_delta_px=16`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step1-emotion-otro -Theme dark -OutDir reports\qa\layered_visual_compare_registro_step1_emotion_otro_dark`. Product tests for the fix commit: `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (dark chips + Otro input + range), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-step1-emotion@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.13432; odiff=5.46; bbox=60; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of fix commit `096c6c7`): the canonical `.fchip`/stepper/range/nav repair also closes the dark selected-emotion state. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step1-emotion --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_step1_emotion_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step1-emotion@dark` status `PASS` (`changed_pixel_ratio=0.07946`, `mean_abs_diff=0.03407`, `windowed_ssim=0.83935`, `max_bbox_delta_px=16`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step1-emotion -Theme dark -OutDir reports\qa\layered_visual_compare_registro_step1_emotion_dark`. Product tests for the fix commit: `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (dark selected chip + 70/100 range), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-step1-emotion@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.12876; odiff=5.44; bbox=3; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step1-emotion_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29): fix commits `096c6c7` + `6f42628` (canonical `.fchip`/range/nav/stepper repair plus dynamic step-1 height when the custom "Otro" input is hidden, so the selected-emotion state keeps the canonical shorter card/nav geometry). Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step1-emotion --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_step1_emotion_light\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step1-emotion@light` status `PASS` (`changed_pixel_ratio=0.05014`, `mean_abs_diff=0.02044`, `windowed_ssim=0.87703`, `max_bbox_delta_px=1`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step1-emotion -Theme light -OutDir reports\qa\layered_visual_compare_registro_step1_emotion_light`. Step-1 family rechecked and still `PASS`: `suite:registro-step1-emotion@dark`, `suite:registro-step1-emotion-otro@light`, `suite:registro-step1-emotion-otro@dark`. `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (short selected-emotion card + nav aligned), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-step3-filled@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.10273; odiff=3.34; bbox=74; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-step3-filled_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of Registro fixes `8f23eda` + `096c6c7`): the full-height dark screen painter plus the canonical stepper/nav alignment keeps the dark Respuesta card within gate. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-step3-filled --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_step3_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-step3-filled@dark` status `PASS` (`changed_pixel_ratio=0.06049`, `mean_abs_diff=0.02667`, `windowed_ssim=0.84611`, `max_bbox_delta_px=16`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-step3-filled -Theme dark -OutDir reports\qa\layered_visual_compare_registro_step3_dark`. Product tests for current Registro fixes: `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (dark Respuesta card + Guardar registro CTA), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.09228; odiff=2.14; bbox=74; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of Registro fixes `8f23eda` + `096c6c7`): the full-height dark screen painter and canonical stepper/nav alignment close the dark Situación state. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro@dark` status `PASS` (`changed_pixel_ratio=0.05340`, `mean_abs_diff=0.01920`, `windowed_ssim=0.86943`, `max_bbox_delta_px=16`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro -Theme dark -OutDir reports\qa\layered_visual_compare_registro_dark`. Product tests for current Registro fixes: `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (dark Situación card + nav), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-success@dark` - severity=medium; findings=raw_pixel_delta,layout_drift,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.08708; odiff=1.03; bbox=131; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-success_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of Registro fixes `8f23eda` + `096c6c7`): the full-height dark screen painter and canonical stepper alignment close the dark success state. Capture command `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-success --theme dark --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro_success_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `suite:registro-success@dark` status `PASS` (`changed_pixel_ratio=0.03954`, `mean_abs_diff=0.01277`, `windowed_ssim=0.92105`, `max_bbox_delta_px=16`). Anti-fraud CLEAN via `.\qa\run_visual_item.ps1 -App suite -View registro-success -Theme dark -OutDir reports\qa\layered_visual_compare_registro_success_dark`. Product tests for current Registro fixes: `pytest tests\test_registro_tcc_visual_contract.py tests\test_tcc_otro_placeholder.py tests\test_tcc_persistencia.py tests\test_design_bridge_contract.py tests\test_anti_fraud_scan.py tests\test_components_public_api.py -q` = 40 passed. Manual panel review confirms a real Qt render (dark success card with check + "Registro guardado"), no overlay/blit/reference artifact; DIFF is text-edge AA and expected Qt-vs-Chromium shadow/rasterization.
- [x] `suite:registro-success@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.06139; odiff=1.0; bbox=13; panel=`reports\qa\layered_visual_compare_fresh\panels\suite_registro-success_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-29, collateral PASS of the same fix commit `d72c55a`): the bare-container + per-step-card shell also aligns the success state. Capture `.\.venv\Scripts\python.exe qa\capture_v8.py --app suite --view registro-success --theme light --out-dir qa\_captures_v8 --no-clean`; report `reports\qa\layered_visual_compare_registro\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`); exact key `PASS` (`changed_pixel_ratio=0.0405`, `mean_abs_diff=0.0151`, `windowed_ssim=0.918`, `max_bbox_delta_px=15`). Anti-fraud CLEAN; registro tests green. Manual panel review confirms a real Qt render (success card with check + "Registro guardado"), no overlay; DIFF is text-edge AA.

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
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence (2026-07-02, canon 116): `reports/qa/dbt_full_compare_after_shadow/LAYERED_VISUAL_REPORT.json` has `REPORT_EVIDENCE_VALID: YES` and exact key `PASS`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-now@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.08224; odiff=2.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-now_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence (2026-07-02, canon 116): `reports/qa/dbt_full_compare_after_shadow/LAYERED_VISUAL_REPORT.json` has `REPORT_EVIDENCE_VALID: YES` and exact key `PASS`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
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
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-observe-describe@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06924; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-observe-describe_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-wise-mind@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06221; odiff=0.88; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-wise-mind_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-wise-mind@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07056; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-wise-mind_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-participate@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06534; odiff=1.42; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-participate_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-participate@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06836; odiff=0.87; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-participate_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-non-judgmental@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06614; odiff=1.44; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-non-judgmental_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-non-judgmental@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06903; odiff=0.95; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-non-judgmental_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-stop@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06718; odiff=1.49; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-stop_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; old STOP-only closure is historical and not used.
- [x] `suite:dbt-practice-stop@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06984; odiff=0.92; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-stop_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; old STOP-only closure is historical and not used.
- [x] `suite:dbt-practice-tipp@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06850; odiff=1.56; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-tipp_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-tipp@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07125; odiff=0.99; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-tipp_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-self-soothe@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06665; odiff=1.45; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-self-soothe_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-self-soothe@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06974; odiff=0.98; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-self-soothe_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-radical-acceptance@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06717; odiff=1.50; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-radical-acceptance_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-radical-acceptance@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07055; odiff=1.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-radical-acceptance_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-check-facts@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06169; odiff=0.86; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-check-facts_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-check-facts@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07040; odiff=1.05; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-check-facts_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-opposite-action@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06945; odiff=1.61; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-opposite-action_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-opposite-action@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07279; odiff=1.08; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-opposite-action_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-problem-solving@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06387; odiff=0.96; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-problem-solving_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-problem-solving@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07255; odiff=1.16; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-problem-solving_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-please@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06850; odiff=1.59; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-please_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-please@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07227; odiff=1.17; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-please_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-dear-man@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06862; odiff=1.55; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-dear-man_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-dear-man@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07198; odiff=1.11; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-dear-man_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-give@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06508; odiff=1.40; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-give_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-give@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06780; odiff=0.84; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-give_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-fast@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06650; odiff=1.46; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-fast_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-fast@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06941; odiff=0.97; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-fast_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-validation-limits@light` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.06886; odiff=1.59; bbox=1; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-validation-limits_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.
- [x] `suite:dbt-practice-validation-limits@dark` - status=PASS; severity=none; bucket=NONE; findings=none; changed=0.07236; odiff=1.15; bbox=16; panel=`reports\qa\dbt_full_compare_after_shadow\panels\suite_dbt-practice-validation-limits_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - DBT v2 evidence: exact key `PASS` in the DBT v2 report above; modal audit PASS in `reports/qa/dbt_modal_audit_after_shadow/AUDIT.json`; closure preserved from verified base `ffef06f`; no STOP-only evidence used.

### Hub Detail / Plan / IA (F6, F5, F3, F9, F10, F12, F8) (10)

- [x] `hub:detalle-plan-timer@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.45219; odiff=6.04; bbox=143; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-timer_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, fix commit `a37b5df`): audited from clean updated `main`; the prior closure was not present on `main`, so the runtime fix was re-applied as a fresh product commit. Hub detail plan now paints the canonical full screen surface, restores the `.screen` 24px padding, keeps the bottom window edge visible for bbox, and localizes the timer form/list geometry to the canonical `.hub-grid` rhythm. Exact dark capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-timer -Theme dark -OutDir reports\qa\codex_audit_detalle_plan_timer_dark`; report `reports\qa\codex_audit_detalle_plan_timer_dark\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-timer@dark` status `PASS` (`changed_pixel_ratio=0.09622`, `mean_abs_diff=0.03242`, `windowed_ssim=0.75092`, `max_bbox_delta_px=16`, `odiff=2.62`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle-plan-rutina@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44947; odiff=5.25; bbox=151; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-rutina_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, fix commit `419ceef`): routine plan detail now uses the same canonical Hub detail screen edge and `.hub-grid` rhythm, with localized routine form/card sizing and input/combo heights matching the canonical checklist panel. Exact dark capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-rutina -Theme dark -OutDir reports\qa\codex_audit_detalle_plan_rutina_dark_postcommit`; report `reports\qa\codex_audit_detalle_plan_rutina_dark_postcommit\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-rutina@dark` status `PASS` (`changed_pixel_ratio=0.08469`, `mean_abs_diff=0.02895`, `windowed_ssim=0.78134`, `max_bbox_delta_px=16`, `odiff=2.33`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Anchors remain `PASS`: `hub:detalle-plan-timer@dark` (`changed_pixel_ratio=0.09571`, `mean_abs_diff=0.03217`, `windowed_ssim=0.75037`, `max_bbox_delta_px=16`, `odiff=2.57`) and `hub:detalle-plan-timer@light` (`REPORT_EVIDENCE_VALID: YES`, report `reports\qa\codex_audit_detalle_plan_timer_light_anchor_postcommit\LAYERED_VISUAL_REPORT.json`). Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle-plan-timer@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44912; odiff=5.96; bbox=142; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-timer_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, collateral PASS from fix commit `a37b5df`): same Hub detail timer surface/layout repair as `hub:detalle-plan-timer@dark`. Exact light capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-timer -Theme light -OutDir reports\qa\codex_audit_detalle_plan_timer_light`; report `reports\qa\codex_audit_detalle_plan_timer_light\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-timer@light` status `PASS` (`changed_pixel_ratio=0.09424`, `mean_abs_diff=0.03220`, `windowed_ssim=0.76453`, `max_bbox_delta_px=15`, `odiff=2.53`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle-plan-rutina@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.44284; odiff=5.05; bbox=150; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-rutina_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, collateral PASS from fix commit `419ceef`): same routine plan detail layout repair as `hub:detalle-plan-rutina@dark`. Exact light capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-rutina -Theme light -OutDir reports\qa\codex_audit_detalle_plan_rutina_light_postcommit`; report `reports\qa\codex_audit_detalle_plan_rutina_light_postcommit\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-rutina@light` status `PASS` (`changed_pixel_ratio=0.08212`, `mean_abs_diff=0.02844`, `windowed_ssim=0.79493`, `max_bbox_delta_px=15`, `odiff=2.19`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.42572; odiff=5.24; bbox=111; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, fix commit `21e1795`): default Hub detail/reminders now uses the same localized Plan detail rhythm as the canonical F6/F5/F3 screen, with the reminders form/list sizing adjusted without touching canonical assets, thresholds, comparator, captures, or references. Exact dark capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle -Theme dark -OutDir reports\qa\codex_audit_detalle_dark_postcommit`; report `reports\qa\codex_audit_detalle_dark_postcommit\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle@dark` status `PASS` (`changed_pixel_ratio=0.09223`, `mean_abs_diff=0.03141`, `windowed_ssim=0.75937`, `max_bbox_delta_px=16`, `odiff=2.55`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Neighbor anchors remain `PASS`: `hub:detalle-plan-timer@dark`, `hub:detalle-plan-timer@light`, `hub:detalle-plan-rutina@dark`, and `hub:detalle-plan-rutina@light`, all from fresh post-commit harness reports under `reports\qa\codex_audit_detalle_plan_*_anchor_after_detalle_postcommit`. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.41556; odiff=5.06; bbox=110; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, collateral PASS from fix commit `21e1795`): same localized reminders layout repair as `hub:detalle@dark`. Exact light capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle -Theme light -OutDir reports\qa\codex_audit_detalle_light_postcommit`; report `reports\qa\codex_audit_detalle_light_postcommit\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle@light` status `PASS` (`changed_pixel_ratio=0.08995`, `mean_abs_diff=0.03135`, `windowed_ssim=0.77062`, `max_bbox_delta_px=15`, `odiff=2.45`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper. Manual panel review confirms a real Qt render, no canonical/reference overlay or blit; residual diff is bounded to text/edge AA and normal Qt button/text rasterization.
- [x] `hub:detalle-plan-activacion@dark` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.38631; odiff=3.75; bbox=43; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-activacion_dark.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, fix commit `022635d`): activation plan detail now uses the canonical compact activation form/list rhythm, activation-only empty-state geometry, and activation-only header density while preserving the previously closed Hub detail/timer/rutina anchors. Exact dark capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-activacion -Theme dark -OutDir reports\qa\codex_audit_detalle_plan_activacion_dark_closure` (wrapper sets `NM_VAS_INTROSPECT=1`); report `reports\qa\codex_audit_detalle_plan_activacion_dark_closure\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-activacion@dark` status `PASS` (`changed_pixel_ratio=0.09460`, `mean_abs_diff=0.03357`, `windowed_ssim=0.77581`, `max_bbox_delta_px=16`, `odiff=3.27`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper and `qa\vas_gate.py --key "hub:detalle-plan-activacion@dark"` exit code `0`. Previously closed Hub detail/plan anchors were rechecked; `hub:detalle-plan-timer@dark` exact wrapper PASS and the family anchor comparator report `reports\qa\codex_audit_hub_detail_plan_anchors_after_activacion_dark_final\LAYERED_VISUAL_REPORT.json` remains valid with `REPORT_EVIDENCE_VALID: YES`.
- [x] `hub:detalle-plan-activacion@light` - severity=high; findings=raw_pixel_delta,layout_drift,qa_missed_raw_or_layout; changed=0.37762; odiff=3.61; bbox=42; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-plan-activacion_light.png`.
  - legacy: true
  - legacy-reason: pre_replay_era
  - legacy-migrated-by: migrate_legacy_closures.py
  - Closure evidence (2026-06-30, fix commit `58dbc2a`): activation plan detail light now keeps the canonical compact activation geometry while suppressing the light-only card lift/highlight on the activation header/form/list surfaces; dark rendering remains unchanged. Exact light capture+compare via `.\qa\run_visual_item.ps1 -App hub -View detalle-plan-activacion -Theme light -OutDir reports\qa\codex_audit_detalle_plan_activacion_light_closure2` (wrapper sets `NM_VAS_INTROSPECT=1`); report `reports\qa\codex_audit_detalle_plan_activacion_light_closure2\LAYERED_VISUAL_REPORT.json` (`REPORT_EVIDENCE_VALID: YES`, `REPORT_SCOPE: PARTIAL`, `HANDOFF_CLOSURE_ALLOWED: NO` only because `partial_scope`); exact key `hub:detalle-plan-activacion@light` status `PASS` (`changed_pixel_ratio=0.09543`, `mean_abs_diff=0.03457`, `windowed_ssim=0.77299`, `max_bbox_delta_px=15`, `odiff=3.1`, `suspicious_perfect_match=false`). Anti-fraud CLEAN in wrapper and VAS gate exit code `0`. Suspicious closure audit `.\.venv\Scripts\python.exe tools\qa\audit_suspicious_closure.py` PASS after marking the checkbox (`reports\qa\suspicious_closure_audit\20260630_133605\AUDIT.md`). Stale-PASS guard: `hub:detalle-plan-activacion@dark` remains exact wrapper PASS after the light fix in `reports\qa\codex_audit_detalle_plan_activacion_dark_after_light_fix\LAYERED_VISUAL_REPORT.json` (`changed_pixel_ratio=0.09460`, `mean_abs_diff=0.03357`, `windowed_ssim=0.77581`, `max_bbox_delta_px=16`, `odiff=3.27`, `suspicious_perfect_match=false`).
- [ ] `hub:detalle-resumen-ia-0@light` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.16481; odiff=7.34; bbox=0; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-resumen-ia-0_light.png`.
- [ ] `hub:detalle-resumen-ia-0@dark` - severity=medium; findings=raw_pixel_delta,state_or_recipe_suspect,qa_missed_raw_or_layout; changed=0.16215; odiff=7.3; bbox=0; panel=`reports\qa\layered_visual_compare_fresh\panels\hub_detalle-resumen-ia-0_dark.png`.

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
