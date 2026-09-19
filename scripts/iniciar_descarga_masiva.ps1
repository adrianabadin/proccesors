# Inicia la descarga masiva de municipios SIBOM en segundo plano (desatendido)
# Omite automáticamente Saladillo (108) y 25 de Mayo (130)

param (
    [int]$Desde = 1,
    [int]$Hasta = 135,
    [string]$Orden = "id",            # "id", "tamano-asc", "tamano-desc"
    [int]$Limite = 0,                 # 0 = sin límite
    [switch]$SoloIndexar = $false,
    [int[]]$Omitir = @()
)

$estadoDir = Join-Path (Get-Location) "sibom\_estado"
if (-not (Test-Path $estadoDir)) {
    New-Item -ItemType Directory -Force -Path $estadoDir | Out-Null
}

$logOut = Join-Path $estadoDir "lote_descarga.log"
$logErr = Join-Path $estadoDir "lote_descarga.err.log"

$argList = @("-u", "scripts\descarga_masiva_sibom.py", "--desde", "$Desde", "--hasta", "$Hasta", "--orden", "$Orden")

if ($SoloIndexar) {
    $argList += "--solo-indexar"
}
if ($Limite -gt 0) {
    $argList += @("--limite", "$Limite")
}
if ($Omitir.Count -gt 0) {
    $argList += "--omitir"
    foreach ($o in $Omitir) { $argList += "$o" }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INICIANDO DESCARGA MASIVA SIBOM EN SEGUNDO PLANO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Rango: $Desde a $Hasta | Orden: $Orden"
Write-Host " Omitiendo automáticamente: 108 (Saladillo) y 130 (25 de Mayo)" -ForegroundColor Yellow
if ($Limite -gt 0) { Write-Host " Límite de municipios: $Limite" }
if ($SoloIndexar) { Write-Host " Modo: Solo Indexar" }
Write-Host " Log de salida: $logOut"
Write-Host " Log de errores: $logErr"
Write-Host "------------------------------------------------------------"

$proc = Start-Process -FilePath "python" `
    -ArgumentList $argList `
    -WorkingDirectory (Get-Location).Path `
    -RedirectStandardOutput $logOut `
    -RedirectStandardError $logErr `
    -WindowStyle Hidden `
    -PassThru

Write-Host " Proceso iniciado con PID: $($proc.Id)" -ForegroundColor Green
Write-Host "------------------------------------------------------------"
Write-Host " COMANDOS DE MONITOREO:" -ForegroundColor Cyan
Write-Host " 1. Ver progreso en tiempo real:"
Write-Host "    Get-Content -Path '$logOut' -Tail 25 -Wait" -ForegroundColor White
Write-Host ""
Write-Host " 2. Ver estado global de todos los municipios:"
Write-Host "    python scripts\sibom_scraper.py status --global" -ForegroundColor White
Write-Host ""
Write-Host " 3. Detener el proceso si es necesario:"
Write-Host "    Stop-Process -Id $($proc.Id) -Force" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Cyan
