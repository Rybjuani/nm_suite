# start_episode.ps1
# Crea un episodio con su estructura de carpetas y template.
# Uso: .\start_episode.ps1 -Name "fix_clipping" -Profile "nm_suite_safe_bugfix"

param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Profile
)

# Directorio base del harness (donde vive este script)
$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$HarnessRoot = Split-Path -Parent $HarnessRoot

# Verificar que el perfil existe
$ProfilePath = Join-Path $HarnessRoot "profiles\$Profile\PROFILE.md"
if (-not (Test-Path $ProfilePath)) {
    Write-Host "ERROR: Perfil no encontrado: $ProfilePath" -ForegroundColor Red
    Write-Host "Perfiles disponibles:" -ForegroundColor Yellow
    Get-ChildItem (Join-Path $HarnessRoot "profiles") -Directory | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor DarkGray
    }
    exit 1
}

# Crear nombre de carpeta con timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$episodeFolderName = "${timestamp}_${Name}"
$episodesDir = Join-Path $HarnessRoot "episodes"
$episodePath = Join-Path $episodesDir $episodeFolderName

# Crear estructura
New-Item -ItemType Directory -Path $episodePath -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $episodePath "evidence") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $episodePath "logs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $episodePath "diffs") -Force | Out-Null

# Copiar template de episodio
$templatePath = Join-Path $HarnessRoot "EPISODE_TEMPLATE.md"
$episodeFile = Join-Path $episodePath "EPISODE.md"

if (Test-Path $templatePath) {
    Copy-Item $templatePath $episodeFile -Force
} else {
    # Template basico si no existe el archivo template
    @"
# Episode: $Name

## Identificacion

- **ID episodio:** $episodeFolderName
- **Fecha:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **Repo objetivo:**
- **Perfil usado:** $Profile
- **Agente/Modelo:**

## Objetivo

(pendiente)

## No objetivos

(pendiente)

## Presupuesto

- **Presupuesto maximo:** (definir)

## Scope

### Archivos permitidos

(listar)

### Archivos prohibidos

(listar)

## Estado inicial

- **Baseline antes:** (pendiente)

## Plan

- **Plan corto:** (pendiente)

## Ejecucion

- **Cambios realizados:** (pendiente)

## Validacion

- **Validacion ejecutada:** (pendiente)

## Evidencia

- **Antes:** (pendiente)
- **Despues:** (pendiente)

## Resultado

- **Diff stat:** (pendiente)
- **Archivos tocados:** (pendiente)
- **Commit:** (pendiente)
- **Deuda restante:** (pendiente)

## Decision final

- [ ] Commit
- [ ] Rollback
- [ ] Pedir revision
- [ ] Descartar
"@ | Out-File -FilePath $episodeFile -Encoding UTF8
}

# Escribir perfil y timestamp en el episodio
$content = Get-Content $episodeFile -Raw -Encoding UTF8
$content = $content -replace '\*\*Perfil usado:\*\*\s*$', "**Perfil usado:** $Profile"
$content = $content -replace '\*\*Fecha:\*\*\s*$', "**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Set-Content $episodeFile $content -Encoding UTF8 -NoNewline

Write-Host "Episodio creado: $episodePath" -ForegroundColor Green
Write-Host "  Perfil: $Profile" -ForegroundColor Yellow
Write-Host "  Carpeta: $episodeFolderName" -ForegroundColor Yellow
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Cyan
Write-Host "  1. Editar EPISODE.md con objetivo y scope"
Write-Host "  2. Verificar estado del repo: .\scripts\verify_git_state.ps1 -RepoPath '<ruta>'"
Write-Host "  3. Correr agente con perfil + episodio + prompt"
