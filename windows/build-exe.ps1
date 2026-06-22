#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

if (-not (Test-Path "$Root\venv\Scripts\pip.exe")) {
    Write-Host 'Run setup.ps1 first (venv missing)' -ForegroundColor Red
    exit 1
}

$TgVendor = Join-Path $Root 'third_party\tg-ws-proxy'
if (-not (Test-Path (Join-Path $TgVendor 'proxy\tg_ws_proxy.py'))) {
    Write-Host 'Run setup.ps1 first (tg-ws-proxy source missing)' -ForegroundColor Red
    exit 1
}

& "$Root\venv\Scripts\pip.exe" install pyinstaller -q

$main = Join-Path $Root 'app\main.py'
$dist = Join-Path $Root 'dist'
$addData = "$TgVendor;tg-ws-proxy"

Push-Location $Root
try {
    & "$Root\venv\Scripts\pyinstaller.exe" `
        --noconfirm --clean --windowed --onefile `
        --name DpiBypass `
        --paths (Join-Path $Root 'app') `
        --paths $TgVendor `
        --add-data $addData `
        --collect-submodules proxy `
        --collect-submodules utils `
        --hidden-import cryptography `
        --hidden-import winreg `
        --collect-all customtkinter `
        $main
    Write-Host "Built: $dist\DpiBypass.exe" -ForegroundColor Green
    Write-Host "Copy bin\ciadpi.exe next to DpiBypass.exe if needed"
} finally {
    Pop-Location
}
