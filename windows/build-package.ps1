#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

& "$Root\build-exe.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dist = Join-Path $Root 'dist'
$binSrc = Join-Path $Root 'bin'
$binDst = Join-Path $dist 'bin'
$exe = Join-Path $dist 'DpiBypass.exe'

if (-not (Test-Path $exe)) {
    Write-Host 'DpiBypass.exe not found in dist\' -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $binDst | Out-Null
if (Test-Path (Join-Path $binSrc 'ciadpi.exe')) {
    Copy-Item (Join-Path $binSrc 'ciadpi.exe') (Join-Path $binDst 'ciadpi.exe') -Force
    Write-Host '[OK] bin\ciadpi.exe copied to dist\bin\' -ForegroundColor Green
} else {
    Write-Host '[WARN] bin\ciadpi.exe missing — run setup.ps1 first' -ForegroundColor Yellow
}

$zapretSrc = Join-Path $binSrc 'zapret'
if (Test-Path $zapretSrc) {
    Copy-Item $zapretSrc (Join-Path $binDst 'zapret') -Recurse -Force
    Write-Host '[OK] bin\zapret copied (Discord / winws)' -ForegroundColor Green
} else {
    Write-Host '[WARN] bin\zapret missing — run setup.ps1 for Discord' -ForegroundColor Yellow
}

$zip = Join-Path $dist 'DpiBypass-Windows.zip'
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $exe, $binDst -DestinationPath $zip -Force
Write-Host "Package: $zip" -ForegroundColor Cyan
