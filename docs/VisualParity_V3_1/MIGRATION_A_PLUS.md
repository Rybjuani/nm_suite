# Migración A+ — Archivo forense pre-V3.1

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
> Este documento describe el plan de migración forense. **Fase 0D NO ejecuta
> tag/bundle/release.** Sólo documenta. V1/V2 siguen intactos en `main`.
>
> **Actualización Fase 0D:**
> - Preflight detallado: ver `FORENSIC_SNAPSHOT_PREFLIGHT.md` (comandos
>   futuros marcados `FUTURE_PHASE_ONLY`).
> - Plan de ejecución de 8 pasos: ver
>   `MIGRATION_A_PLUS_EXECUTION_PLAN.md` (cada paso con objetivo, files
>   allowed/forbidden, validation, rollback).
> - Decisiones owner cerradas: ver `OWNER_DECISIONS_LOCKED.md` (LOCK-1
>   bundle ubicación, LOCK-4 timing).
> - Dry-run script: `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1`.
> - Checklist de aceptación Fase 0D: `PHASE_0D_CHECKLIST.md`.

## Tesis

V1 (`qa/` closer/comparator/replay/anti-fraud viejos) y V2 (`harness/`
stubs no funcionales) son material forense, no base operativa. Antes de
removerlos del working tree de `main`, se preservan íntegramente vía tag +
git bundle externo + SHA256, de modo que cualquier estado futuro pueda
reconstruirse sin ambigüedad.

## Regla de preservación (redline)

**V1/V2 código, scripts, evidence records, tarballs o bundles NO se archivan
dentro de `main`.** La preservación forense es **externa** al working tree.

`docs/_archive/` puede contener **sólo documentación histórica no
ejecutable** (`.md`, `.pdf`, `.png` de propuestas previas, notas forenses,
logs históricos en formato documento). Prohibido:

- scripts V1/V2 (`.py`, `.ps1`)
- evidence records V1 (`docs/closure_evidence/*.json`)
- tarballs ejecutables (`.bundle`, `.tar.gz`, `.zip` con código)
- copias completas del harness viejo
- `qa/` scripts
- `harness/` V2 completo

## Plan A+ (a ejecutar en Fase posterior, no en 0A)

### Paso 1 — Tag forense

```bash
git tag -a forensic-pre-v3.1 \
  -m "Snapshot forense de V1+V2+V3-previo antes de migración V3.1"
```

Tag anotado en `main` apuntando al HEAD actual (`c645405e` al momento de
este documento). El tag es referencia inmutable; cualquier futuro checkout
del tag reconstruye el estado exacto.

### Paso 2 — Git bundle externo

```bash
git bundle create nm_suite-forensic-pre-v3.1.bundle --all
```

El bundle se publica como **GitHub Release asset** del propio `nm_suite`
(decisión owner pendiente — ver `PHASE_0A_DECISIONS.md` #1) o como
**storage owner privado**. El bundle **no se commitea al working tree**.

### Paso 3 — SHA256 del bundle

```bash
sha256sum nm_suite-forensic-pre-v3.1.bundle > nm_suite-forensic-pre-v3.1.bundle.sha256
```

El archivo `.sha256` se publica junto al bundle (mismo Release asset o
mismo storage owner). Referenciado en el MANIFEST puntero (Paso 4).

### Paso 4 — MANIFEST puntero en `main`

`docs/VisualParity_V3_1/MIGRATION_A_PLUS.md` (este archivo) se actualiza en
Fase posterior con:

- Tag: `forensic-pre-v3.1`
- URL del bundle (GitHub Release asset o storage owner)
- SHA256 del bundle
- Fecha de creación
- Owner responsable
- Alcance del snapshot (V1 completo, V2 completo, V3-previo docs, 116
  evidence records V1 + 2 revoked, `qa/` scripts, `harness/` V2)
- Instrucción de restauración: `git clone nm_suite-forensic-pre-v3.1.bundle`

### Paso 5 — Eliminación del working tree (Fase posterior, no 0A)

Tras confirmar que el bundle + SHA256 están publicados y son descargables:

- Eliminar `qa/{close_visual_key,layered_visual_compare,replay_visual_closure,target_scope,anti_fraud_scan,vas_gate,vas_engine,odiff_runner,spec_generator,visual_gate_calibration,visual_auditor_spec,runtime_live_probe}.py`
- Eliminar `qa/run_visual.ps1`, `qa/specs/`
- Eliminar `harness/` (V2 completo)
- Eliminar `docs/closure_evidence/` (116 records + 2 revoked)
- Eliminar `docs/VisualParity_V3/` (mover sólo `.md`/`.pdf`/`.png` a `docs/_archive/VisualParity_V3_PRE_FORENSIC/`)
- Eliminar `.github/workflows/visual-closure-replay.yml` (reemplazado)
- Eliminar `VISUAL_REPAIR_HANDOFF.md` (sujeto a owner decision #4)
- Eliminar `WORKER_VISUAL_QA_FLOW.md` (sujeto a owner decision #8)

**Cada eliminación es commit separado.** No mixed commits.

## Estado actual

| Item | Estado Fase 0A |
|---|---|
| Tag `forensic-pre-v3.1` | No creado |
| Git bundle externo | No creado |
| SHA256 del bundle | No calculado |
| MANIFEST puntero | Este documento (placeholder) |
| Eliminación de V1/V2 del working tree | No ejecutada |
| V1/V2 en `main` | Intactos |

## Riesgos si se ejecuta mal

- **Borrar V1/V2 sin bundle:** pérdida irrecuperable de evidencia forense.
  Cualquier auditoría futura no podría reconstruir el estado pre-V3.1.
- **Commitear el bundle al working tree:** inflación del repo; violación de
  la regla "no tarballs en `main`".
- **Archivar V1/V2 código en `docs/_archive/`:** violación de la redline;
  `docs/_archive/` debe ser sólo documentación no ejecutable.
- **No registrar SHA256:** el bundle podría ser sustituido sin detección.
- **Mixed commit (snapshot + eliminación + scaffold):** imposibilita
  revertir selectivamente. Cada paso debe ser commit atómico.

## Owner decision requerida

Ver `PHASE_0A_DECISIONS.md` #1: ubicación del bundle forense (GitHub Release
asset en `nm_suite` vs. storage owner privado).
