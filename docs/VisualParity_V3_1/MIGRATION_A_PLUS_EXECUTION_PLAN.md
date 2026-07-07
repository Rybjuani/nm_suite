# Migration A+ Execution Plan

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
>
> Este documento define el orden de ejecución de la migración forense A+.
> **Fase 0D NO ejecuta ningún paso.** Todos los comandos destructivos están
> marcados `FUTURE_PHASE_ONLY`. La ejecución real requiere prompt explícito
> del owner en una fase posterior, tras confirmar que el bundle A+ está
> publicado y es descargable.

## Tesis

La migración A+ es irreversible (remoción de V1/V2 del working tree). Se
ejecuta en 8 pasos ordenados, cada uno commit atómico, cada uno con
objetivo, files allowed, files forbidden, validation y rollback strategy.

## Orden de ejecución

```
Paso 1: snapshot/tag/bundle/checksum        [FUTURE_PHASE_ONLY]
Paso 2: manifest pointer                    [FUTURE_PHASE_ONLY]
Paso 3: archive docs no ejecutables         [FUTURE_PHASE_ONLY]
Paso 4: remove V1/V2 operative code         [FUTURE_PHASE_ONLY]
Paso 5: preserve capture_v8.py              [FUTURE_PHASE_ONLY]
Paso 6: reconcile canon                     [FUTURE_PHASE_ONLY]
Paso 7: replace workflow legacy             [FUTURE_PHASE_ONLY]
Paso 8: implement VisualParity Core/CLI     [Fase 1A, posterior]
```

Cada paso es **commit atómico**. No mixed commits entre pasos.

---

## Paso 1 — Snapshot / tag / bundle / checksum

**Objetivo:** Preservar el estado completo del repo (V1 + V2 + V3-previo +
116 evidence records + scripts) vía tag anotado + git bundle externo +
SHA256, antes de cualquier remoción.

**Files allowed:** Ninguno en el working tree (el bundle se crea fuera del
repo).

**Files forbidden:** `.bundle`, `.zip`, `.tar.gz` en el working tree.

**Comandos:**

```powershell
# FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D
# Ver FORENSIC_SNAPSHOT_PREFLIGHT.md para detalle completo.
git tag -a forensic-pre-v3.1 -m "Snapshot forense de V1+V2+V3-previo antes de migración V3.1"
git bundle create nm_suite-forensic-pre-v3.1.bundle --all
$Hash = (Get-FileHash -Path "nm_suite-forensic-pre-v3.1.bundle" -Algorithm SHA256).Hash.ToLower()
$Hash | Out-File -FilePath "nm_suite-forensic-pre-v3.1.bundle.sha256" -Encoding ascii -NoNewline
gh release create forensic-pre-v3.1 --repo Rybjuani/nm_suite --title "Forensic snapshot pre-V3.1" --notes "..." nm_suite-forensic-pre-v3.1.bundle nm_suite-forensic-pre-v3.1.bundle.sha256
```

**Validation:**

- `git tag -l forensic-pre-v3.1` muestra el tag.
- `git show forensic-pre-v3.1 --no-patch` muestra el mensaje.
- `Get-Content nm_suite-forensic-pre-v3.1.bundle.sha256` imprime el hash.
- GitHub Release visible en `https://github.com/Rybjuani/nm_suite/releases/tag/forensic-pre-v3.1`.
- Download del bundle desde la URL del Release funciona.

**Rollback strategy:** Si el bundle o el Release fallan, **no proceder al
Paso 2**. Eliminar el tag con `git tag -d forensic-pre-v3.1` (sólo si no se
pusheó), eliminar el Release si se creó, y reportar bloqueo.

---

## Paso 2 — Manifest pointer

**Objetivo:** Registrar en `main` el puntero al bundle forense (tag, URL,
SHA256, fecha, owner, alcance, instrucción de restauración).

**Files allowed:** `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` (sólo
editar el placeholder con datos reales).

**Files forbidden:** Cualquier otro archivo.

**Comando:**

```powershell
# FUTURE_PHASE_ONLY
# Editar docs/VisualParity_V3_1/MIGRATION_A_PLUS.md con:
#   - tag: forensic-pre-v3.1
#   - bundle URL: https://github.com/Rybjuani/nm_suite/releases/download/forensic-pre-v3.1/nm_suite-forensic-pre-v3.1.bundle
#   - SHA256: <hash del Paso 1>
#   - fecha, owner, alcance, instrucción de restauración
git add docs/VisualParity_V3_1/MIGRATION_A_PLUS.md
git commit -m "docs(visual-parity-v3.1): register forensic snapshot A+ pointer"
git push origin main
```

**Validation:**

- `git log --oneline -1` muestra el commit.
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` contiene la URL y SHA256.
- Validador Fase 0B sigue PASS.

**Rollback strategy:** `git revert <commit>`. El bundle y el Release
permanecen (no se borran).

---

## Paso 3 — Archive docs no ejecutables

**Objetivo:** Mover sólo documentación histórica no ejecutable
(`.md`/`.pdf`/`.png`) de `docs/VisualParity_V3/` (V3-previo) a
`docs/_archive/VisualParity_V3_PRE_FORENSIC/`.

**Files allowed:**

- Mover: `docs/VisualParity_V3/README.md`,
  `docs/VisualParity_V3/VisualParity_V3_Propuesta_Tecnica.pdf`,
  `docs/VisualParity_V3/VisualParity_V3_Propuesta_Tecnica.docx`,
  `docs/VisualParity_V3/forensic_audit/FORENSIC_AUDIT_V3.md`,
  `docs/VisualParity_V3/diagrams/*.png`.
- Crear: `docs/_archive/VisualParity_V3_PRE_FORENSIC/` (directorio).

**Files forbidden:**

- ❌ Scripts V1/V2 (`.py`, `.ps1`).
- ❌ Evidence records V1 (`docs/closure_evidence/*.json`).
- ❌ Tarballs (`.bundle`, `.zip`, `.tar.gz`).
- ❌ Copias completas del harness viejo.

**Comando:**

```powershell
# FUTURE_PHASE_ONLY
mkdir docs/_archive/VisualParity_V3_PRE_FORENSIC
mkdir docs/_archive/VisualParity_V3_PRE_FORENSIC/diagrams
mkdir docs/_archive/VisualParity_V3_PRE_FORENSIC/forensic_audit
git mv docs/VisualParity_V3/README.md docs/_archive/VisualParity_V3_PRE_FORENSIC/
git mv docs/VisualParity_V3/VisualParity_V3_Propuesta_Tecnica.pdf docs/_archive/VisualParity_V3_PRE_FORENSIC/
git mv docs/VisualParity_V3/VisualParity_V3_Propuesta_Tecnica.docx docs/_archive/VisualParity_V3_PRE_FORENSIC/
git mv docs/VisualParity_V3/forensic_audit/FORENSIC_AUDIT_V3.md docs/_archive/VisualParity_V3_PRE_FORENSIC/forensic_audit/
git mv docs/VisualParity_V3/diagrams/*.png docs/_archive/VisualParity_V3_PRE_FORENSIC/diagrams/
git commit -m "chore(forensic): archive V3-previo docs (non-executable only)"
git push origin main
```

**Validation:**

- `docs/_archive/VisualParity_V3_PRE_FORENSIC/` contiene sólo `.md`/`.pdf`/`.png`/`.docx`.
- `find docs/_archive/ -name "*.py" -o -name "*.ps1" -o -name "*.json"` devuelve vacío.
- `docs/VisualParity_V3/` ya no existe (o está vacío).
- Validador Fase 0B sigue PASS.

**Rollback strategy:** `git revert <commit>`. Los archivos vuelven a su
ubicación original.

---

## Paso 4 — Remove V1/V2 operative code

**Objetivo:** Eliminar del working tree los scripts V1 y el harness V2
completo. Preservación vía bundle A+ (Paso 1).

**Files allowed (eliminar):**

- V1 scripts: `qa/close_visual_key.py`, `qa/layered_visual_compare.py`,
  `qa/replay_visual_closure.py`, `qa/target_scope.py`,
  `qa/anti_fraud_scan.py`, `qa/vas_gate.py`, `qa/vas_engine.py`,
  `qa/odiff_runner.py`, `qa/spec_generator.py`,
  `qa/visual_gate_calibration.py`, `qa/visual_auditor_spec.py`,
  `qa/runtime_live_probe.py`, `qa/run_visual.ps1`, `qa/specs/`.
- V2 completo: `harness/ci_gate/`, `harness/replay/`, `harness/anti_fraud/`,
  `harness/agent_runner/`, `harness/semantic_lint/`, `harness/policy/`,
  `harness/docs/`, `harness/README.md`.
- V3-previo: `docs/VisualParity_V3/` (si quedó algo tras Paso 3).
- Evidence records V1: `docs/closure_evidence/` (116 records + 2 revoked).
- Workflow legacy: `.github/workflows/visual-closure-replay.yml` (se
  reemplaza en Paso 7, no aquí).
- Handoff: `VISUAL_REPAIR_HANDOFF.md` (sujeto a PEND-2; si se elimina).
- Protocolo: `WORKER_VISUAL_QA_FLOW.md` (sujeto a PEND-5; si se archiva).

**Files forbidden (conservar):**

- ✅ `qa/capture_v8.py` (Paso 5).
- ✅ `qa/_mockup_canonical/` (Paso 6).
- ✅ `qa/pack canonico/` (Paso 6; no eliminar hasta reconciliación).
- ✅ `qa/tessdata/` (PEND-3; congelado).
- ✅ `tests/` no-V1 (tests de producto).
- ✅ Producto: `app/`, `hub/`, `shared/`, `db/`, `assets/`, `installers/`.
- ✅ `docs/VisualParity_V3_1/` (docs V3.1 nuevos).
- ✅ `tools/visualparity/` (scaffold V3.1).
- ✅ `harness/v3/` (scaffold V3.1).
- ✅ `.github/workflows/visual-parity-v3-governance.yml` (governance smoke).

**Comando (ejemplo; ejecutar archivo por archivo con commits separados si
es necesario):**

```powershell
# FUTURE_PHASE_ONLY
git rm qa/close_visual_key.py qa/layered_visual_compare.py qa/replay_visual_closure.py qa/target_scope.py qa/anti_fraud_scan.py qa/vas_gate.py qa/vas_engine.py qa/odiff_runner.py qa/spec_generator.py qa/visual_gate_calibration.py qa/visual_auditor_spec.py qa/runtime_live_probe.py qa/run_visual.ps1
git rm -r qa/specs/
git rm -r harness/ci_gate/ harness/replay/ harness/anti_fraud/ harness/agent_runner/ harness/semantic_lint/ harness/policy/ harness/docs/
git rm harness/README.md
git rm -r docs/closure_evidence/
# Sujeto a PEND-2 y PEND-5:
# git rm VISUAL_REPAIR_HANDOFF.md
# git rm WORKER_VISUAL_QA_FLOW.md
git commit -m "chore(forensic): remove V1/V2 operative code (preserved via A+ bundle)"
git push origin main
```

**Validation:**

- `git ls-files qa/` no muestra los scripts V1 eliminados.
- `git ls-files harness/` sólo muestra `harness/v3/`.
- `git ls-files docs/closure_evidence/` devuelve vacío.
- Validador Fase 0B sigue PASS (tras actualizar grupo A si removió archivos
  Fase 0A referenciados — pero los archivos Fase 0A están en
  `docs/VisualParity_V3_1/`, `tools/visualparity/`, `harness/v3/`, que se
  conservan).

**Rollback strategy:** `git revert <commit>`. Los archivos vuelven al
working tree. El bundle A+ permanece como respaldo.

---

## Paso 5 — Preserve `capture_v8.py`

**Objetivo:** Confirmar que `qa/capture_v8.py` se conserva intacto tras el
Paso 4, con los límites declarados en `CAPTURE_V8_TRANSITION.md`.

**Files allowed:** Ninguno (sólo verificación).

**Files forbidden:** Modificar `qa/capture_v8.py`.

**Comando (verificación):**

```powershell
# FUTURE_PHASE_ONLY
git ls-files qa/capture_v8.py
# Debe imprimir: qa/capture_v8.py
```

**Validation:**

- `qa/capture_v8.py` existe en el working tree.
- `git log --oneline -1 -- qa/capture_v8.py` no muestra commits de
  modificación en la fase de migración (sólo commits previos).
- `CAPTURE_V8_TRANSITION.md` sigue declarando los límites (L1, L2, L3).

**Rollback strategy:** N/A (no se modifica nada). Si `capture_v8.py` fue
eliminado por error en Paso 4, `git revert <commit del paso 4>`.

---

## Paso 6 — Reconcile canon

**Objetivo:** Reconciliar `qa/pack canonico/` contra `qa/_mockup_canonical/`,
declarar canon único con paths relativos, migrar assets únicos, eliminar
`pack canonico/` si es duplicado.

**Files allowed:**

- `qa/_mockup_canonical/MANIFEST.json` (re-canonicalizar con paths relativos).
- `qa/_mockup_canonical/` (migrar assets únicos desde `pack canonico/`).
- `qa/pack canonico/` (eliminar tras reconciliación, si es duplicado).

**Files forbidden:** Cualquier otro archivo.

**Comandos (ver `CANON_RECONCILIATION_PLAN.md` para detalle):**

```powershell
# FUTURE_PHASE_ONLY
# 1. Comparar PNGs por SHA256 raw bytes
# 2. Comparar MANIFEST.json campo a campo
# 3. Migrar assets únicos (si los hay)
# 4. Re-canonicalizar MANIFEST.json con paths relativos
# 5. Eliminar pack canonico/ si es duplicado
git add qa/_mockup_canonical/
git rm -r "qa/pack canonico/"
git commit -m "chore(canon): reconcile _mockup_canonical as single canon (paths relativos, pack canonico eliminado tras reconciliacion)"
git push origin main
```

**Validation:**

- `qa/_mockup_canonical/MANIFEST.json` no contiene paths Windows.
- `qa/pack canonico/` no existe (si fue eliminado).
- `find qa/_mockup_canonical/ -name "*.png" | wc -l` == 116.
- Validador Fase 0B sigue PASS.

**Rollback strategy:** `git revert <commit>`. El bundle A+ tiene los PNGs
originales de `pack canonico/` si se necesitan.

---

## Paso 7 — Replace workflow legacy

**Objetivo:** Reemplazar `.github/workflows/visual-closure-replay.yml`
(legacy V1, `--no-regen`) por un workflow V3.1 que sólo bloquea (no
autoriza cierre).

**Files allowed:**

- Eliminar: `.github/workflows/visual-closure-replay.yml`.
- Crear: `.github/workflows/visual-closure-v3-gate.yml` (o nombre similar).

**Files forbidden:** Modificar
`.github/workflows/visual-parity-v3-governance.yml` (governance smoke, no
tocar).

**Comando:**

```powershell
# FUTURE_PHASE_ONLY
git rm .github/workflows/visual-closure-replay.yml
# Crear .github/workflows/visual-closure-v3-gate.yml con contenido V3.1
git add .github/workflows/visual-closure-v3-gate.yml
git commit -m "ci(visual-parity-v3.1): replace legacy closure workflow with V3.1 gate (block-only, no closure)"
git push origin main
```

**Validation:**

- `.github/workflows/visual-closure-replay.yml` no existe.
- `.github/workflows/visual-closure-v3-gate.yml` existe y no referencia V1
  scripts ni `--no-regen`.
- Validador Fase 0B actualizado (grupo L) reconoce el nuevo workflow como
  esperado.

**Rollback strategy:** `git revert <commit>`. El workflow legacy vuelve.
Pero esto revierte la migración; preferible fix-forward.

---

## Paso 8 — Implement VisualParity Core/CLI (Fase 1A)

**Objetivo:** Implementar VisualParity Core/CLI en `tools/visualparity/src/`
(.NET 8).

**Files allowed:** `tools/visualparity/src/**`, `tools/visualparity/tests/**`,
`tools/visualparity/visualparity.lock.json` (real, no `.example`).

**Files forbidden:** Cualquier otro archivo.

**Comando:** N/A (Fase 1A es implementación, no un solo commit).

**Validation:**

- `dotnet build` PASS.
- `dotnet test` PASS contra corpus mínimo.
- `visualparity compare --canon ... --actual ... --out ...` produce bundle
  válido.
- Validador Fase 0B PASS.

**Rollback strategy:** Revertir commits de implementación. El scaffold
Fase 0A-0D permanece.

---

## Dependencias entre pasos

```
Paso 1 (snapshot) → Paso 2 (manifest pointer)
Paso 2 → Paso 3 (archive docs)
Paso 3 → Paso 4 (remove V1/V2)
Paso 4 → Paso 5 (preserve capture_v8, verificación)
Paso 4 → Paso 6 (reconcile canon, requiere V1/V2 removidos para evitar ambigüedad)
Paso 6 → Paso 7 (replace workflow, requiere canon reconciliado)
Paso 7 → Paso 8 (implement Core/CLI, requiere workflow V3.1)
```

No se puede saltar pasos. Cada paso valida el anterior.

## Prohibiciones

- ❌ No ejecutar ningún paso en Fase 0D.
- ❌ No crear tag/bundle/release en Fase 0D.
- ❌ No commitear `.bundle`/`.zip`/`.tar.gz`/evidence V1/scripts V1/V2 a
  `main`.
- ❌ No mixed commits entre pasos.
- ❌ No `--force`.
- ❌ No usar Git Bash/WSL para comandos forenses.

## Owner decisions referenciadas

- LOCK-1 (bundle ubicación): Paso 1.
- LOCK-2 (capture_v8 conservado): Paso 5.
- LOCK-3 (stack .NET 8): Paso 8.
- LOCK-4 (timing por fases): este documento.
- LOCK-5 (canon único): Paso 6.
- PEND-2 (handoff): Paso 4.
- PEND-5 (WORKER_VISUAL_QA_FLOW): Paso 4.
- PEND-6 (116 closures): Paso 4 (evidence records removidos).
