# summarize_diff.ps1
# Muestra resumen de cambios con advertencias.
# Uso: .\summarize_diff.ps1 -RepoPath "C:\Users\nosom\Desktop\nm_suite"

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
    Write-Host "=== Diff Summary ===" -ForegroundColor Cyan
    Write-Host "Repo: $RepoPath" -ForegroundColor Yellow
    Write-Host ""

    # Diff stat
    Write-Host "--- git diff --stat ---" -ForegroundColor Cyan
    $diffStat = git diff --stat 2>$null
    if ($diffStat) {
        $diffStat
    } else {
        Write-Host "(sin cambios sin stage)" -ForegroundColor DarkGray
    }

    # Staged
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

    # Advertencia: muchos archivos
    $fileCount = ($allFiles | Measure-Object).Count
    Write-Host ""
    if ($fileCount -gt 5) {
        Write-Host "ADVERTENCIA: $fileCount archivos tocados. Verificar scope." -ForegroundColor Red
    } elseif ($fileCount -gt 3) {
        Write-Host "ADVERTENCIA: $fileCount archivos tocados. Revisar que esten dentro del scope." -ForegroundColor Yellow
    }

    # Advertencia: rutas prohibidas
    $prohibitedPatterns = @("build/", "dist/", "installer/", "installers/", "qa/_captures", "qa/_audit_runtime", ".zip", ".exe", ".msi")
    $prohibitedHits = @()
    foreach ($file in $allFiles) {
        foreach ($pattern in $prohibitedPatterns) {
            if ($file -like "*$pattern*") {
                $prohibitedHits += $file
                break
            }
        }
    }

    if ($prohibitedHits.Count -gt 0) {
        Write-Host ""
        Write-Host "ALERTA: Archivos en rutas prohibidas detectados:" -ForegroundColor Red
        $prohibitedHits | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host "Estos archivos NO deberian tocarse salvo tarea release explicita." -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "No se hizo commit. No se hizo push." -ForegroundColor DarkGray
}
finally {
    Pop-Location
}
