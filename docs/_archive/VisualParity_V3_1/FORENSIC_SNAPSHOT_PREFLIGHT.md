# Forensic Snapshot Preflight — A+ Migration

> **Fase 0D — migration planning. No runtime authority. No visual closure.**
>
> Este documento describe el preflight de la migración forense A+. **Fase 0D
> NO ejecuta tag/bundle/release.** Sólo documenta los comandos futuros y los
> marca como `FUTURE_PHASE_ONLY`. La ejecución real requiere prompt explícito
> del owner en una fase posterior.

## Tesis

Antes de remover V1/V2 del working tree de `main`, se preserva el estado
completo del repo vía tag anotado + git bundle externo + SHA256. Esto
garantiza que cualquier estado futuro pueda reconstruirse sin ambigüedad.

Fase 0D **prepara** el preflight; **no lo ejecuta**. El script dry-run
`tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1` valida las
precondiciones (clean tree, HEAD == origin/main) sin crear tag, bundle, ni
release.

## Reglas (redline)

- **Fase 0D NO ejecuta tag/bundle/release.** Sólo documenta.
- **No crear tag real** `forensic-pre-v3.1` en Fase 0D.
- **No crear git bundle real** `nm_suite-forensic-pre-v3.1.bundle` en Fase 0D.
- **No crear GitHub Release real** en Fase 0D.
- **No commit de `.bundle`, `.zip`, `.tar.gz`, evidence V1 o scripts V1/V2
  en `main`.** Preservación es externa al working tree.
- **Prohibido Git Bash/WSL** para los comandos forenses. Windows PowerShell
  nativo únicamente. Razón: paths y EOL handling deben ser consistentes con
  el entorno owner.
- **No `--force`** en ningún comando git.

## Precondiciones (validadas por dry-run)

El script `preflight_snapshot_dry_run.ps1` valida:

1. **Clean tree:** `git status --short --branch` no muestra cambios locales
   sin commitear ni untracked files.
2. **HEAD == origin/main:** `git rev-parse HEAD` == `git rev-parse origin/main`.
3. **HEAD == base esperada:** el SHA de HEAD debe coincidir con el SHA
   declarado como base de la fase.

Si cualquiera falla, el dry-run devuelve exit code 1 y NO imprime los
comandos futuros (porque las precondiciones no se cumplen).

## Comandos futuros (FUTURE_PHASE_ONLY)

Los siguientes comandos **NO se ejecutan en Fase 0D**. Se documentan aquí
para que la fase posterior pueda ejecutarlos con copia-pega, tras confirmar
que el dry-run pasó y que el owner dio prompt explícito.

### Paso F1 — Crear tag anotado `forensic-pre-v3.1`

```powershell
# FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D
# Requiere: dry-run PASS + prompt explícito del owner.

$TagMessage = "Snapshot forense de V1+V2+V3-previo antes de migración V3.1"
git tag -a forensic-pre-v3.1 -m $TagMessage
```

**Validación post-tag:**

```powershell
# FUTURE_PHASE_ONLY
git tag -l forensic-pre-v3.1
git show forensic-pre-v3.1 --no-patch
```

### Paso F2 — Crear git bundle externo

```powershell
# FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D
git bundle create nm_suite-forensic-pre-v3.1.bundle --all
```

**Notas:**

- El bundle se crea **fuera** del working tree (en el directorio actual de
  PowerShell, que debería ser un directorio temporal o de releases, no el
  repo).
- El bundle **NO se commitea al working tree**.
- Tamaño esperado: ~50-200 MB dependiendo del historial.

### Paso F3 — Calcular SHA256 del bundle

```powershell
# FUTURE_PHASE_ONLY
$BundlePath = "nm_suite-forensic-pre-v3.1.bundle"
$Hash = (Get-FileHash -Path $BundlePath -Algorithm SHA256).Hash.ToLower()
$Hash | Out-File -FilePath "nm_suite-forensic-pre-v3.1.bundle.sha256" -Encoding ascii -NoNewline
Write-Host "SHA256: $Hash"
```

**Validación:**

```powershell
# FUTURE_PHASE_ONLY
Get-Content "nm_suite-forensic-pre-v3.1.bundle.sha256"
# Debe coincidir con el hash impreso en el paso anterior.
```

### Paso F4 — Publicar como GitHub Release asset

```powershell
# FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D
# Requiere: GitHub CLI (gh) instalado y autenticado, o upload manual vía web.

# Opción A: GitHub CLI
gh release create forensic-pre-v3.1 `
  --repo Rybjuani/nm_suite `
  --title "Forensic snapshot pre-V3.1" `
  --notes "Snapshot forense de V1+V2+V3-previo antes de migración V3.1. Ver docs/VisualParity_V3_1/MIGRATION_A_PLUS.md." `
  nm_suite-forensic-pre-v3.1.bundle `
  nm_suite-forensic-pre-v3.1.bundle.sha256

# Opción B: upload manual vía https://github.com/Rybjuani/nm_suite/releases/new
```

**Notas:**

- LOCK-1 (decisión owner): GitHub Release asset del propio `nm_suite` es
  opción primaria.
- Fallback documentado: storage owner privado (S3, drive). Si se usa
  fallback, registrar URL + SHA256 en `MIGRATION_A_PLUS.md`.

### Paso F5 — Registrar MANIFEST puntero en `main`

Tras confirmar que el bundle + SHA256 están publicados y son descargables:

```powershell
# FUTURE_PHASE_ONLY — DO NOT RUN IN PHASE 0D
# Editar docs/VisualParity_V3_1/MIGRATION_A_PLUS.md para incluir:
#   - tag: forensic-pre-v3.1
#   - bundle URL: https://github.com/Rybjuani/nm_suite/releases/download/forensic-pre-v3.1/nm_suite-forensic-pre-v3.1.bundle
#   - SHA256: <hash del paso F3>
#   - fecha: <ISO8601>
#   - owner: <id>
#   - alcance: V1 completo, V2 completo, V3-previo docs, 116 evidence records V1 + 2 revoked, qa/ scripts, harness/ V2
#   - instrucción de restauración: git clone nm_suite-forensic-pre-v3.1.bundle

git add docs/VisualParity_V3_1/MIGRATION_A_PLUS.md
git commit -m "docs(visual-parity-v3.1): register forensic snapshot A+ pointer"
git push origin main
```

## Dry-run (Fase 0D)

El script `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1`:

- Valida precondiciones (clean tree, HEAD == origin/main).
- Imprime los comandos futuros marcados como `FUTURE_PHASE_ONLY`.
- **No crea tag.**
- **No crea bundle.**
- **No calcula SHA256 real.**
- **No publica Release.**
- **No escribe archivos.**
- **No hace push.**
- **No modifica repo.**

Devuelve exit code 0 si clean y HEAD == origin/main; exit code 1 si hay
cambios locales o divergencia.

## Prohibiciones explícitas

- ❌ No crear tag real `forensic-pre-v3.1` en Fase 0D.
- ❌ No crear bundle real `nm_suite-forensic-pre-v3.1.bundle` en Fase 0D.
- ❌ No calcular SHA256 real del bundle en Fase 0D (no hay bundle).
- ❌ No crear GitHub Release en Fase 0D.
- ❌ No commitear `.bundle`, `.zip`, `.tar.gz`, evidence V1, scripts V1/V2 a
  `main`.
- ❌ No usar Git Bash/WSL para comandos forenses.
- ❌ No usar `--force`.

## Estado actual (Fase 0D)

| Item | Estado |
|---|---|
| Tag `forensic-pre-v3.1` | No creado (FUTURE_PHASE_ONLY) |
| Git bundle externo | No creado (FUTURE_PHASE_ONLY) |
| SHA256 del bundle | No calculado (FUTURE_PHASE_ONLY) |
| GitHub Release | No creado (FUTURE_PHASE_ONLY) |
| MANIFEST puntero en `main` | Placeholder en `MIGRATION_A_PLUS.md` (sin URL/SHA256 reales) |
| Dry-run script | Creado en `tools/visualparity/phase0d/preflight_snapshot_dry_run.ps1` |
| V1/V2 en `main` | Intactos |

## Riesgos si se ejecuta mal (en fase futura)

- **Borrar V1/V2 sin bundle:** pérdida irrecuperable de evidencia forense.
- **Commitear el bundle al working tree:** inflación del repo; violación de
  la redline.
- **No registrar SHA256:** el bundle podría ser sustituido sin detección.
- **Usar Git Bash/WSL:** paths y EOL pueden diferir del entorno owner,
  rompiendo reproducibilidad del bundle.
- **Mixed commit (snapshot + eliminación + scaffold):** imposibilita
  revertir selectivamente. Cada paso debe ser commit atómico.

## Owner decision referenciada

- LOCK-1 (bundle ubicación): GitHub Release asset primario, storage owner
  privado fallback. Ver `OWNER_DECISIONS_LOCKED.md`.
- LOCK-4 (timing): Fase 0D prepara; fase posterior ejecuta con prompt
  explícito.
