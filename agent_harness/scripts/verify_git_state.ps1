# verify_git_state.ps1
# Muestra el estado git del repo objetivo.
# Uso: .\verify_git_state.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath
)

if (-not (Test-Path $RepoPath)) {
    Write-Host "ERROR: Ruta no existe: $RepoPath" -ForegroundColor Red
    exit 1
}

$gitDir = Join-Path $RepoPath ".git"
if (-not (Test-Path $gitDir)) {
    Write-Host "ERROR: No es un repositorio git: $RepoPath" -ForegroundColor Red
    exit 1
}

Push-Location $RepoPath

try {
    Write-Host "=== Git State ===" -ForegroundColor Cyan
    Write-Host ""

    # Ruta
    Write-Host "Ruta: $RepoPath" -ForegroundColor Yellow

    # Rama actual
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    Write-Host "Rama: $branch" -ForegroundColor Yellow

    # Status
    Write-Host ""
    Write-Host "--- git status -sb ---" -ForegroundColor Cyan
    git status -sb

    # Ultimos 5 commits
    Write-Host ""
    Write-Host "--- Ultimos 5 commits ---" -ForegroundColor Cyan
    git log --oneline -5

    # Remoto
    Write-Host ""
    Write-Host "--- Remoto ---" -ForegroundColor Cyan
    $remote = git remote -v 2>$null
    if ($remote) {
        $remote
    } else {
        Write-Host "(sin remoto configurado)" -ForegroundColor DarkGray
    }

    # Ahead/behind
    Write-Host ""
    Write-Host "--- Ahead/Behind ---" -ForegroundColor Cyan
    $aheadBehind = git rev-list --left-right --count "origin/$branch...HEAD" 2>$null
    if ($LASTEXITCODE -eq 0 -and $aheadBehind) {
        $parts = $aheadBehind -split '\s+'
        Write-Host "Behind origin/$branch`: $($parts[0])"
        Write-Host "Ahead origin/$branch`: $($parts[1])"
    } else {
        Write-Host "(no se pudo determinar ahead/behind)" -ForegroundColor DarkGray
    }

    # Archivos modificados
    Write-Host ""
    Write-Host "--- Archivos modificados ---" -ForegroundColor Cyan
    $modified = git diff --name-only 2>$null
    $staged = git diff --cached --name-only 2>$null
    if ($modified) {
        Write-Host "Sin stage:" -ForegroundColor Yellow
        $modified | ForEach-Object { Write-Host "  $_" }
    }
    if ($staged) {
        Write-Host "En stage:" -ForegroundColor Green
        $staged | ForEach-Object { Write-Host "  $_" }
    }
    if (-not $modified -and -not $staged) {
        Write-Host "(sin archivos modificados)" -ForegroundColor DarkGray
    }
}
finally {
    Pop-Location
}
