#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$WindowsRoot = $PSScriptRoot
$ByeDpiSrc = Join-Path (Split-Path $WindowsRoot -Parent) 'app\src\main\cpp\byedpi'
$OutExe = Join-Path $WindowsRoot 'bin\ciadpi.exe'

if (-not (Test-Path $ByeDpiSrc)) {
    Write-Error "ByeDPI sources not found: $ByeDpiSrc"
}

$gcc = $null
foreach ($c in @('gcc', 'x86_64-w64-mingw32-gcc')) {
    $p = Get-Command $c -ErrorAction SilentlyContinue
    if ($p) { $gcc = $p.Source; break }
}

if (-not $gcc) {
    Write-Host 'MinGW gcc не найден. Варианты:' -ForegroundColor Yellow
    Write-Host '  1. winget install -e --id MSYS2.MSYS2  (затем pacman -S mingw-w64-x86_64-gcc make)'
    Write-Host '  2. Запустите setup.ps1 — скачает готовый ciadpi.exe'
    exit 1
}

Push-Location $ByeDpiSrc
try {
    make clean 2>$null
    make windows CC=$gcc
    if (-not (Test-Path 'ciadpi.exe')) { throw 'make windows failed' }
    New-Item -ItemType Directory -Force -Path (Split-Path $OutExe -Parent) | Out-Null
    Copy-Item 'ciadpi.exe' $OutExe -Force
    Write-Host "Built: $OutExe" -ForegroundColor Green
} finally {
    Pop-Location
}
