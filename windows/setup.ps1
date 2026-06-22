#Requires -Version 5.1
param(
    [switch]$ForceZapret
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$Tmp = Join-Path $Root '.setup-tmp'
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
$ZapretVersion = '1.9.9c'
$ZapretUrl = "https://github.com/Flowseal/zapret-discord-youtube/releases/download/$ZapretVersion/zapret-discord-youtube-$ZapretVersion.zip"

Write-Host 'DpiBypass — setup' -ForegroundColor Cyan

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
    Write-Host '[1/3] tg-ws-proxy source...' -ForegroundColor Yellow
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
    Write-Host '[1/3] tg-ws-proxy source OK' -ForegroundColor Green
}

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
    $zip = Join-Path $Tmp 'byedpi.zip'
    $ok = Get-File @(
        'https://github.com/hufrea/byedpi/releases/download/v0.17.3/byedpi-17.3-x86_64-w64.zip',
        'https://github.com/hufrea/byedpi/releases/download/v0.17.3/byedpi-17.3-i686-w64.zip'
    ) $zip
    if ($ok) {
        $ex = Join-Path $Tmp 'byedpi-ex'
        if (Test-Path $ex) { Clear-Dir $ex }
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

$ZapretRoot = Join-Path $Bin 'zapret'
$Winws = Join-Path $ZapretRoot 'bin\winws.exe'
$VersionFile = Join-Path $ZapretRoot 'dpibypass_version.txt'
$needZapret = $ForceZapret -or (-not (Test-Path $Winws))
if (-not $needZapret -and (Test-Path $VersionFile)) {
    $installed = (Get-Content $VersionFile -Raw).Trim()
    if ($installed -ne $ZapretVersion) { $needZapret = $true }
}
if (-not $needZapret -and (Test-Path (Join-Path $ZapretRoot 'service.bat'))) {
    $svc = Get-Content (Join-Path $ZapretRoot 'service.bat') -Raw
    if ($svc -notmatch "LOCAL_VERSION=$ZapretVersion") { $needZapret = $true }
}

if ($needZapret) {
    Write-Host "[3/3] zapret $ZapretVersion (Discord)..." -ForegroundColor Yellow
    $zip = Join-Path $Tmp 'zapret-discord.zip'
    $ok = Get-File @($ZapretUrl) $zip
    if ($ok) {
        $ex = Join-Path $Tmp 'zapret-extract'
        if (Test-Path $ex) { Clear-Dir $ex }
        Expand-Archive $zip $ex -Force
        $inner = Get-ChildItem $ex -Directory | Select-Object -First 1
        if (Test-Path $ZapretRoot) { Clear-Dir $ZapretRoot }
        Move-Item $inner.FullName $ZapretRoot
        if (Test-Path $Winws) {
            Set-Content -Path $VersionFile -Value $ZapretVersion -Encoding UTF8
            Write-Host "  OK zapret $ZapretVersion -> $Winws" -ForegroundColor Green
        } else {
            Write-Host '  winws.exe not found in archive' -ForegroundColor Red
        }
    } else {
        Write-Host '  Manual: github.com/Flowseal/zapret-discord-youtube/releases' -ForegroundColor Red
    }
} else {
    $ver = if (Test-Path $VersionFile) { (Get-Content $VersionFile -Raw).Trim() } else { '?' }
    Write-Host "[3/3] zapret $ver OK (latest $ZapretVersion)" -ForegroundColor Green
}

# Обновить ipset-списки с GitHub (актуальные CDN Discord)
$ipsetFile = Join-Path $ZapretRoot 'lists\ipset-all.txt'
$ipsetUrl = 'https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/ipset-service.txt'
if (Test-Path $ZapretRoot) {
    Write-Host 'Updating zapret ipset lists...' -ForegroundColor Yellow
    & curl.exe -sS -fL -o $ipsetFile $ipsetUrl
    if ($LASTEXITCODE -eq 0) {
        Write-Host '  OK ipset-all.txt' -ForegroundColor Green
    }
}

Write-Host ''
Write-Host "zapret: $ZapretVersion (Flowseal/zapret-discord-youtube)" -ForegroundColor Cyan
Write-Host 'Run: DpiBypass.exe as Administrator for Discord' -ForegroundColor Cyan
