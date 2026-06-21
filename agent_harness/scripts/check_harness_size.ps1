# check_harness_size.ps1
# Verifica que el harness no crecio demasiado.
# Uso: .\check_harness_size.ps1

# Directorio base del harness (donde vive este script)
$HarnessRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$HarnessRoot = Split-Path -Parent $HarnessRoot

Write-Host "=== Harness Size Check ===" -ForegroundColor Cyan
Write-Host "Root: $HarnessRoot" -ForegroundColor Yellow
Write-Host ""

# Contar archivos
Write-Host "--- Cantidad de archivos ---" -ForegroundColor Cyan
$allFiles = Get-ChildItem $HarnessRoot -Recurse -File | Where-Object {
    $_.FullName -notlike "*\.git\*"
}
$totalFiles = ($allFiles | Measure-Object).Count
Write-Host "Total archivos: $totalFiles"

# Lineas por archivo Markdown
Write-Host ""
Write-Host "--- Archivos Markdown (lineas) ---" -ForegroundColor Cyan
$warnings = @()

$mdFiles = $allFiles | Where-Object { $_.Extension -eq ".md" }
foreach ($file in $mdFiles) {
    $lines = (Get-Content $file.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
    $relativePath = $file.FullName.Replace("$HarnessRoot\", "")

    $isPrompt = $relativePath -like "prompts\*"
    $limit = if ($isPrompt) { 160 } else { 220 }

    $status = ""
    if ($lines -gt $limit) {
        $status = " EXCEDIDO (limite: $limit)" -join ""
        Write-Host "  $relativePath : $lines lineas$status" -ForegroundColor Red
        $warnings += "$relativePath tiene $lines lineas (limite: $limit)"
    } else {
        Write-Host "  $relativePath : $lines lineas" -ForegroundColor Green
    }
}

# Verificar archivos prohibidos de contexto global
Write-Host ""
Write-Host "--- Archivos prohibidos de contexto global ---" -ForegroundColor Cyan
$prohibitedFiles = @("AGENTS.md", "AI_CONTEXT.md", "MEMORY.md", "CONTEXT.md", "KNOWLEDGE_BASE.md")
$prohibitedFound = @()

foreach ($pf in $prohibitedFiles) {
    $found = Get-ChildItem $HarnessRoot -Recurse -File -Filter $pf | Where-Object {
        $_.FullName -notlike "*\.git\*"
    }
    if ($found) {
        $found | ForEach-Object {
            $relativePath = $_.FullName.Replace("$HarnessRoot\", "")
            Write-Host "  ENCONTRADO: $relativePath" -ForegroundColor Red
            $prohibitedFound += $relativePath
        }
    }
}

if ($prohibitedFound.Count -eq 0) {
    Write-Host "  Ninguno encontrado." -ForegroundColor Green
}

# Resumen
Write-Host ""
Write-Host "=== Resumen ===" -ForegroundColor Cyan
Write-Host "Archivos totales: $totalFiles"

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "ADVERTENCIAS:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

if ($prohibitedFound.Count -gt 0) {
    Write-Host ""
    Write-Host "ARCHIVOS PROHIBIDOS:" -ForegroundColor Red
    $prohibitedFound | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "Eliminar estos archivos. No deben existir en el harness." -ForegroundColor Red
}

if ($warnings.Count -eq 0 -and $prohibitedFound.Count -eq 0) {
    Write-Host ""
    Write-Host "Todo OK. Harness dentro de limites." -ForegroundColor Green
}
