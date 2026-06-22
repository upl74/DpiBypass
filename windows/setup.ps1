#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

Write-Host 'DpiBypass — setup' -ForegroundColor Cyan

# Python venv + deps
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host 'Python not found. Install from https://python.org' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "$Root\venv")) {
    python -m venv "$Root\venv"
}
& "$Root\venv\Scripts\pip.exe" install -r "$Root\requirements.txt" -q
Write-Host '[OK] Python dependencies' -ForegroundColor Green

# tg-ws-proxy source (embedded Telegram proxy)
$TgVendor = Join-Path $Root 'third_party\tg-ws-proxy'
if (-not (Test-Path (Join-Path $TgVendor 'proxy\tg_ws_proxy.py'))) {
    Write-Host '[1/2] tg-ws-proxy source...' -ForegroundColor Yellow
    $zip = Join-Path $env:TEMP 'tgws-src.zip'
    $ex = Join-Path $env:TEMP 'tgws-extract'
    if (Test-Path $ex) { Remove-Item $ex -Recurse -Force }
    New-Item -ItemType Directory -Force -Path (Split-Path $TgVendor) | Out-Null
    & curl.exe -sS -fL -o $zip 'https://github.com/Flowseal/tg-ws-proxy/archive/refs/heads/main.zip'
    Expand-Archive $zip $ex -Force
    $inner = Get-ChildItem $ex -Directory | Select-Object -First 1
    if (Test-Path $TgVendor) { Remove-Item $TgVendor -Recurse -Force }
    Move-Item $inner.FullName $TgVendor
    Write-Host "  OK $TgVendor" -ForegroundColor Green
} else {
    Write-Host '[1/2] tg-ws-proxy source OK' -ForegroundColor Green
}

# ByeDPI binary
$Bin = Join-Path $Root 'bin'
New-Item -ItemType Directory -Force -Path $Bin | Out-Null

function Get-File {
    param([string[]]$Urls, [string]$Out)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        foreach ($u in $Urls) {
            Write-Host "  -> $u"
            & curl.exe -sS -fL --retry 2 --retry-delay 2 -o $Out $u
            if ($LASTEXITCODE -eq 0 -and (Test-Path $Out) -and (Get-Item $Out).Length -gt 1024) { return $true }
            Remove-Item $Out -Force -ErrorAction SilentlyContinue
        }
        return $false
    } finally {
        $ErrorActionPreference = $prev
    }
}

$ciadpi = Join-Path $Bin 'ciadpi.exe'
if (-not (Test-Path $ciadpi)) {
    Write-Host '[2/3] ciadpi.exe...' -ForegroundColor Yellow
    $zip = Join-Path $env:TEMP 'byedpi.zip'
    $ok = Get-File @(
        'https://github.com/hufrea/byedpi/releases/download/v0.17.3/byedpi-17.3-x86_64-w64.zip',
        'https://github.com/hufrea/byedpi/releases/download/v0.17.3/byedpi-17.3-i686-w64.zip'
    ) $zip
    if ($ok) {
        $ex = Join-Path $env:TEMP 'byedpi-ex'
        if (Test-Path $ex) { Remove-Item $ex -Recurse -Force }
        Expand-Archive $zip $ex -Force
        $f = Get-ChildItem $ex -Recurse -Filter ciadpi.exe | Select-Object -First 1
        Copy-Item $f.FullName $ciadpi -Force
        Write-Host "  OK $ciadpi" -ForegroundColor Green
    } else {
        Write-Host '  Manual: github.com/hufrea/byedpi/releases -> ciadpi.exe' -ForegroundColor Red
    }
} else {
    Write-Host '[2/3] ciadpi.exe OK' -ForegroundColor Green
}

# zapret winws (Discord voice — WinDivert, needs admin)
$ZapretRoot = Join-Path $Bin 'zapret'
$Winws = Join-Path $ZapretRoot 'bin\winws.exe'
if (-not (Test-Path $Winws)) {
    Write-Host '[3/3] zapret winws (Discord)...' -ForegroundColor Yellow
    $zip = Join-Path $env:TEMP 'zapret-discord.zip'
    $ok = Get-File @(
        'https://github.com/Flowseal/zapret-discord-youtube/releases/download/1.9.9c/zapret-discord-youtube-1.9.9c.zip'
    ) $zip
    if ($ok) {
        $ex = Join-Path $env:TEMP 'zapret-extract'
        if (Test-Path $ex) { Remove-Item $ex -Recurse -Force }
        Expand-Archive $zip $ex -Force
        $inner = Get-ChildItem $ex -Directory | Select-Object -First 1
        if (Test-Path $ZapretRoot) { Remove-Item $ZapretRoot -Recurse -Force }
        Move-Item $inner.FullName $ZapretRoot
        if (Test-Path $Winws) {
            Write-Host "  OK $Winws" -ForegroundColor Green
        } else {
            Write-Host '  winws.exe not found in archive' -ForegroundColor Red
        }
    } else {
        Write-Host '  Manual: github.com/Flowseal/zapret-discord-youtube/releases' -ForegroundColor Red
    }
} else {
    Write-Host '[3/3] zapret winws OK' -ForegroundColor Green
}

Write-Host ''
Write-Host 'Run: DpiBypass.bat (Discord: run as Administrator)' -ForegroundColor Cyan
