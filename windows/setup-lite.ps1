#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$Tmp = Join-Path $Root '.setup-tmp'
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host 'DpiBypass Lite — setup' -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host 'Python not found. Install from https://python.org' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$Root\venv")) {
    python -m venv "$Root\venv"
}
& "$Root\venv\Scripts\pip.exe" install -r "$Root\requirements.txt" -q
Write-Host '[OK] Python dependencies' -ForegroundColor Green

$TgVendor = Join-Path $Root 'third_party\tg-ws-proxy'

function Clear-Dir {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        cmd /c "rd /s /q `"$Path`"" | Out-Null
    }
}

if (-not (Test-Path (Join-Path $TgVendor 'proxy\tg_ws_proxy.py'))) {
    Write-Host '[1/1] tg-ws-proxy source...' -ForegroundColor Yellow
    $zip = Join-Path $Tmp 'tgws-src.zip'
    $ex = Join-Path $Tmp 'tgws-extract'
    if (Test-Path $ex) { Clear-Dir $ex }
    New-Item -ItemType Directory -Force -Path (Split-Path $TgVendor) | Out-Null
    & curl.exe -sS -fL -o $zip 'https://github.com/Flowseal/tg-ws-proxy/archive/refs/heads/main.zip'
    Expand-Archive $zip $ex -Force
    $inner = Get-ChildItem $ex -Directory | Select-Object -First 1
    if (Test-Path $TgVendor) { Clear-Dir $TgVendor }
    Move-Item $inner.FullName $TgVendor
    Write-Host "  OK $TgVendor" -ForegroundColor Green
} else {
    Write-Host '[1/1] tg-ws-proxy source OK' -ForegroundColor Green
}

Write-Host ''
Write-Host 'Run: DpiBypassLite.bat' -ForegroundColor Cyan
