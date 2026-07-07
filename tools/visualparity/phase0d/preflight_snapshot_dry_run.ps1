<#
.SYNOPSIS
    Dry-run preflight para la migracion forense A+ de VisualParity V3.1.

.DESCRIPTION
    Solo dry-run. Valida precondiciones para la migracion A+:
      - clean tree (no cambios locales, no untracked)
      - HEAD == origin/main
    Imprime los comandos futuros que se ejecutarian para tag/bundle/SHA256,
    marcados como FUTURE_PHASE_ONLY.

    NO crea tag. NO crea bundle. NO calcula SHA256 real. NO publica Release.
    NO escribe archivos. NO hace push. NO modifica repo.

    Devuelve exit code 0 si clean y HEAD == origin/main.
    Devuelve exit code 1 si hay cambios locales o divergencia.

.NOTES
    Fase 0D - migration planning. No runtime authority. No visual closure.
    Windows PowerShell nativo (no Git Bash, no WSL).
#>

# --- Locate repo root from this script's path ------------------------------
# This script lives at <repo-root>\tools\visualparity\phase0d\preflight_snapshot_dry_run.ps1
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$RepoRoot = (Get-Item $ScriptDir).Parent.Parent.Parent.FullName

Write-Host "=== Fase 0D Forensic Snapshot Preflight (DRY-RUN) ===" -ForegroundColor Cyan
Write-Host "Repo root: $RepoRoot"
Write-Host ""

# --- Precondition 1: clean tree --------------------------------------------
Write-Host "[1/3] Checking clean tree..." -ForegroundColor Yellow
$StatusOutput = git -C $RepoRoot status --short --branch 2>&1
$StatusShort = git -C $RepoRoot status --short 2>&1
$HasLocalChanges = $false
if ($StatusShort) {
    $Lines = $StatusShort | Where-Object { $_.Trim() -ne "" }
    if ($Lines.Count -gt 0) {
        $HasLocalChanges = $true
    }
}

Write-Host "  git status --short --branch:"
$StatusOutput | ForEach-Object { Write-Host "    $_" }

if ($HasLocalChanges) {
    Write-Host "  FAIL: working tree has local changes or untracked files." -ForegroundColor Red
    Write-Host ""
    Write-Host "=== Preflight result: FAIL (local changes) ===" -ForegroundColor Red
    Write-Host "Exit code: 1"
    exit 1
}
Write-Host "  PASS: clean tree." -ForegroundColor Green
Write-Host ""

# --- Precondition 2: HEAD == origin/main -----------------------------------
Write-Host "[2/3] Checking HEAD == origin/main..." -ForegroundColor Yellow
$LocalHead = git -C $RepoRoot rev-parse HEAD 2>&1
$RemoteHead = git -C $RepoRoot rev-parse origin/main 2>&1

Write-Host "  HEAD:         $LocalHead"
Write-Host "  origin/main:  $RemoteHead"

if ($LocalHead -ne $RemoteHead) {
    Write-Host "  FAIL: HEAD != origin/main (divergence)." -ForegroundColor Red
    Write-Host ""
    Write-Host "=== Preflight result: FAIL (divergence) ===" -ForegroundColor Red
    Write-Host "Exit code: 1"
    exit 1
}
Write-Host "  PASS: HEAD == origin/main." -ForegroundColor Green
Write-Host ""

# --- Precondition 3: no forensic-pre-v3.1 tag exists yet -------------------
Write-Host "[3/3] Checking no forensic-pre-v3.1 tag exists..." -ForegroundColor Yellow
$ExistingTag = git -C $RepoRoot tag -l forensic-pre-v3.1 2>&1
if ($ExistingTag -and $ExistingTag.Trim() -ne "") {
    Write-Host "  WARN: tag 'forensic-pre-v3.1' already exists:" -ForegroundColor Yellow
    Write-Host "    $ExistingTag"
    Write-Host "  This is unexpected in Fase 0D. Snapshot may have been created already." -ForegroundColor Yellow
} else {
    Write-Host "  PASS: tag 'forensic-pre-v3.1' does not exist yet." -ForegroundColor Green
}
Write-Host ""

# --- Print FUTURE_PHASE_ONLY commands --------------------------------------
Write-Host "=== Future commands (FUTURE_PHASE_ONLY - DO NOT RUN IN PHASE 0D) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "The following commands would be executed in a FUTURE phase, only after:"
Write-Host "  - This dry-run returns exit code 0."
Write-Host "  - Owner gives explicit prompt to execute migration A+."
Write-Host "  - PowerShell native (no Git Bash, no WSL)."
Write-Host ""
Write-Host "--- Step F1: Create annotated tag forensic-pre-v3.1 ---" -ForegroundColor White
Write-Host '  $TagMessage = "Snapshot forense de V1+V2+V3-previo antes de migracion V3.1"'
Write-Host '  git tag -a forensic-pre-v3.1 -m $TagMessage'
Write-Host ""
Write-Host "--- Step F2: Create git bundle (outside working tree) ---" -ForegroundColor White
Write-Host "  # Run from a temp/releases directory, NOT from repo root."
Write-Host "  git -C `"$RepoRoot`" bundle create nm_suite-forensic-pre-v3.1.bundle --all"
Write-Host ""
Write-Host "--- Step F3: Compute SHA256 of bundle ---" -ForegroundColor White
Write-Host '  $BundlePath = "nm_suite-forensic-pre-v3.1.bundle"'
Write-Host '  $Hash = (Get-FileHash -Path $BundlePath -Algorithm SHA256).Hash.ToLower()'
Write-Host '  $Hash | Out-File -FilePath "nm_suite-forensic-pre-v3.1.bundle.sha256" -Encoding ascii -NoNewline'
Write-Host '  Write-Host "SHA256: $Hash"'
Write-Host ""
Write-Host "--- Step F4: Publish as GitHub Release asset ---" -ForegroundColor White
Write-Host "  # Requires GitHub CLI (gh) or manual upload via web."
Write-Host '  gh release create forensic-pre-v3.1 \'
Write-Host '    --repo Rybjuani/nm_suite \'
Write-Host '    --title "Forensic snapshot pre-V3.1" \'
Write-Host '    --notes "Snapshot forense de V1+V2+V3-previo. Ver docs/VisualParity_V3_1/MIGRATION_A_PLUS.md." \'
Write-Host '    nm_suite-forensic-pre-v3.1.bundle \'
Write-Host '    nm_suite-forensic-pre-v3.1.bundle.sha256'
Write-Host ""
Write-Host "--- Step F5: Register MANIFEST pointer in main ---" -ForegroundColor White
Write-Host "  # Edit docs/VisualParity_V3_1/MIGRATION_A_PLUS.md with tag, URL, SHA256, date, owner, scope."
Write-Host '  git -C $RepoRoot add docs/VisualParity_V3_1/MIGRATION_A_PLUS.md'
Write-Host '  git -C $RepoRoot commit -m "docs(visual-parity-v3.1): register forensic snapshot A+ pointer"'
Write-Host '  git -C $RepoRoot push origin main'
Write-Host ""
Write-Host "=== End future commands ===" -ForegroundColor Cyan
Write-Host ""

# --- Final summary ---------------------------------------------------------
Write-Host "=== Preflight result ===" -ForegroundColor Cyan
Write-Host "Repo root:      $RepoRoot"
Write-Host "HEAD:           $LocalHead"
Write-Host "origin/main:    $RemoteHead"
Write-Host "Clean tree:     YES"
Write-Host "HEAD == origin: YES"
Write-Host "Tag exists:     $([bool]$ExistingTag)"
Write-Host ""
Write-Host "Exit code: 0 (preflight PASS, preconditions met for future migration)" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: This was a DRY-RUN. No tag, bundle, SHA256, or release was created." -ForegroundColor Yellow
Write-Host "      To execute the actual migration, see" -ForegroundColor Yellow
Write-Host "      docs/VisualParity_V3_1/MIGRATION_A_PLUS_EXECUTION_PLAN.md" -ForegroundColor Yellow
Write-Host "      and require explicit owner prompt." -ForegroundColor Yellow

exit 0
