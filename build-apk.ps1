# Сборка DpiBypass APK
$ErrorActionPreference = "Stop"

function Fix-GitSymlinkStubs {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return }
    $fixed = 0
    Get-ChildItem -Recurse -File $Root | ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -match '^\.\./[^\r\n]+$') {
            $target = [System.IO.Path]::GetFullPath((Join-Path $_.DirectoryName $content.Trim()))
            if (Test-Path $target) {
                Copy-Item -Force $target $_.FullName
                $fixed++
            }
        }
    }
    if ($fixed -gt 0) { Write-Host "Fixed $fixed git symlink stubs under $Root" }
}

$hevDir = Join-Path $PSScriptRoot "app\src\main\jni\hev-socks5-tunnel"
if (-not (Test-Path (Join-Path $hevDir "Android.mk"))) {
    Write-Host "Cloning hev-socks5-tunnel..."
    git clone --recursive --depth 1 https://github.com/heiher/hev-socks5-tunnel.git $hevDir
}
Fix-GitSymlinkStubs $hevDir

$byedpiDir = Join-Path $PSScriptRoot "app\src\main\cpp\byedpi"
if (-not (Test-Path (Join-Path $byedpiDir "proxy.c"))) {
    Write-Host "Cloning byedpi v0.13..."
    git clone --depth 1 --branch v0.13 https://github.com/hufrea/byedpi.git $byedpiDir
}

$studioJbr = @(
    "$env:ProgramFiles\Android\Android Studio\jbr\bin\java.exe",
    "${env:ProgramFiles(x86)}\Android\Android Studio\jbr\bin\java.exe",
    "$env:LOCALAPPDATA\Programs\Android Studio\jbr\bin\java.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($studioJbr) {
    $env:JAVA_HOME = Split-Path (Split-Path $studioJbr)
    Write-Host "JAVA_HOME=$env:JAVA_HOME"
} elseif (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Error "Установите Android Studio или JDK 17+, затем повторите."
}

Set-Location $PSScriptRoot
.\gradlew.bat assembleDebug
Write-Host ""
Write-Host "APK: $PSScriptRoot\app\build\outputs\apk\debug\app-debug.apk"
