# close_episode.ps1
# Muestra el estado final del repo para cerrar un episodio.
# Uso: .\close_episode.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

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
    Write-Host "=== Cierre de Episodio ===" -ForegroundColor Cyan
    Write-Host "Repo: $RepoPath" -ForegroundColor Yellow
    Write-Host ""

    # Git status
    Write-Host "--- git status -sb ---" -ForegroundColor Cyan
    git status -sb

    # Diff stat
    Write-Host ""
    Write-Host "--- git diff --stat ---" -ForegroundColor Cyan
    $diffStat = git diff --stat 2>$null
    if ($diffStat) {
        $diffStat
    } else {
        Write-Host "(sin cambios sin stage)" -ForegroundColor DarkGray
    }

    # Diff staged
    Write-Host ""
    Write-Host "--- git diff --cached --stat ---" -ForegroundColor Cyan
    $stagedStat = git diff --cached --stat 2>$null
    if ($stagedStat) {
        $stagedStat
    } else {
        Write-Host "(sin cambios en stage)" -ForegroundColor DarkGray
    }

    # Archivos modificados
    Write-Host ""
    Write-Host "--- Archivos tocados ---" -ForegroundColor Cyan
    $files = git diff --name-only 2>$null
    $stagedFiles = git diff --cached --name-only 2>$null
    $allFiles = @($files) + @($stagedFiles) | Where-Object { $_ } | Sort-Object -Unique
    if ($allFiles) {
        $allFiles | ForEach-Object { Write-Host "  $_" }
    } else {
        Write-Host "(sin archivos modificados)" -ForegroundColor DarkGray
    }

    # Commits locales no pusheados
    Write-Host ""
    Write-Host "--- Commits locales no pusheados ---" -ForegroundColor Cyan
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    $unpushed = git log "origin/$branch..HEAD" --oneline 2>$null
    if ($unpushed) {
        $unpushed | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    } else {
        Write-Host "(sin commits pendientes de push)" -ForegroundColor DarkGray
    }

    # Advertencia
    Write-Host ""
    Write-Host "=== ADVERTENCIA ===" -ForegroundColor Red
    Write-Host "Revisar manualmente que los archivos tocados esten dentro del scope del episodio." -ForegroundColor Yellow
    Write-Host "Este script no puede verificar scope automaticamente." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "No se hizo commit. No se hizo push." -ForegroundColor Red
}
finally {
    Pop-Location
}
