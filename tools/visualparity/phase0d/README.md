# tools/visualparity/phase0d/ — Forensic Snapshot Preflight (Dry-Run)

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
>
> Este directorio contiene el script dry-run de preflight para la migración
> forense A+. **No crea tag, bundle, SHA256, ni release.** Sólo valida
> precondiciones e imprime los comandos futuros.

## Qué valida

`preflight_snapshot_dry_run.ps1` valida 3 precondiciones:

1. **Clean tree:** `git status --short` no muestra cambios locales ni
   untracked files.
2. **HEAD == origin/main:** `git rev-parse HEAD` == `git rev-parse origin/main`.
3. **No existe tag `forensic-pre-v3.1`:** verifica que el snapshot forense
   no fue creado ya (WARN si existe, no FAIL).

Si las precondiciones 1 o 2 fallan, el script devuelve exit code 1 y NO
imprime los comandos futuros.

Si todas pasan, el script imprime los comandos futuros (Paso F1 a F5)
marcados como `FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D`, y devuelve
exit code 0.

## Qué NO hace

- ❌ No crea tag real `forensic-pre-v3.1`.
- ❌ No crea git bundle real.
- ❌ No calcula SHA256 real del bundle (no hay bundle).
- ❌ No publica GitHub Release.
- ❌ No escribe archivos.
- ❌ No hace push.
- ❌ No modifica repo.
- ❌ No invoca V1/V2.
- ❌ No invoca `capture_v8.py`.
- ❌ No cierra keys.
- ❌ No reabre keys.

## Cómo correr

### Windows (PowerShell nativo)

```powershell
.\tools\visualparity\phase0d\preflight_snapshot_dry_run.ps1
```

**Requisitos:**

- Windows PowerShell nativo (no Git Bash, no WSL).
- `git` en PATH.
- Estar en el repo (el script localiza el repo root desde su propia ruta).

### Salida esperada (PASS)

```
=== Fase 0D Forensic Snapshot Preflight (DRY-RUN) ===
Repo root: C:\path\to\nm_suite

[1/3] Checking clean tree...
  git status --short --branch:
    ## main...origin/main
  PASS: clean tree.

[2/3] Checking HEAD == origin/main...
  HEAD:         <sha>
  origin/main:  <sha>
  PASS: HEAD == origin/main.

[3/3] Checking no forensic-pre-v3.1 tag exists...
  PASS: tag 'forensic-pre-v3.1' does not exist yet.

=== Future commands (FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D) ===
...
=== End future commands ===

=== Preflight result ===
Repo root:      C:\path\to\nm_suite
HEAD:           <sha>
origin/main:    <sha>
Clean tree:     YES
HEAD == origin: YES
Tag exists:     False

Exit code: 0 (preflight PASS, preconditions met for future migration)

NOTE: This was a DRY-RUN. No tag, bundle, SHA256, or release was created.
```

### Exit codes

- `0` — PASS: precondiciones cumplidas (clean tree + HEAD == origin/main).
- `1` — FAIL: cambios locales o divergencia HEAD/origin/main.
- `2` — ERROR: interno (no se usa actualmente, reservado).

## Cuándo correr

- Antes de avanzar a la fase de ejecución de migración A+.
- Como smoke test de que el repo está en estado committeable y sincronizado.
- En review de PRs que preparen la migración A+.

## Limitaciones

- El script no verifica que el bundle sería descargable tras publicarlo
  (eso se valida manualmente tras el Paso F4 futuro).
- El script no verifica el contenido del repo (sólo estado git).
- El script no reemplaza la revisión humana del plan de ejecución
  (`MIGRATION_A_PLUS_EXECUTION_PLAN.md`).
- Requiere Windows PowerShell nativo. No probado en pwsh de Linux/macOS
  (puede funcionar pero no es el target).

## Documentación relacionada

- `docs/VisualParity_V3_1/FORENSIC_SNAPSHOT_PREFLIGHT.md` — preflight
  detallado con comandos futuros.
- `docs/VisualParity_V3_1/MIGRATION_A_PLUS_EXECUTION_PLAN.md` — plan de
  ejecución de 8 pasos.
- `docs/VisualParity_V3_1/OWNER_DECISIONS_LOCKED.md` — decisiones owner
  cerradas (LOCK-1 bundle ubicación, LOCK-4 timing).
- `docs/VisualParity_V3_1/PHASE_0D_CHECKLIST.md` — checklist de aceptación.
