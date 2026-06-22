# Fetches libtgwsproxy.so from tg-ws-proxy-android release into jniLibs.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$jniLibs = Join-Path $root "app\src\main\jniLibs"
$store = Join-Path $root "app\third_party\tgwsproxy"
$tmpdir = Join-Path $env:TEMP "tgws-fetch"
New-Item -ItemType Directory -Force -Path $tmpdir | Out-Null

$apk = Join-Path $tmpdir "tgws-universal.apk"
$url = "https://github.com/amurcanov/tg-ws-proxy-android/releases/download/v1.2.3/v1.2.3-release-universal.apk"
Write-Host "Downloading $url ..."
curl.exe -L $url -o $apk

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($apk)
foreach ($abi in @("arm64-v8a", "armeabi-v7a")) {
    $entry = $zip.GetEntry("lib/$abi/libtgwsproxy.so")
    if ($null -eq $entry) { throw "Missing lib/$abi/libtgwsproxy.so in APK" }
    $outDir = Join-Path $store $abi
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $outFile = Join-Path $outDir "libtgwsproxy.so"
    $stream = $entry.Open()
    $fs = [System.IO.File]::Create($outFile)
    $stream.CopyTo($fs)
    $fs.Close()
    $stream.Close()
    Copy-Item $outFile (Join-Path (Join-Path $jniLibs $abi) "libtgwsproxy.so") -Force
    Write-Host "OK $outFile"
}
$zip.Dispose()
Write-Host "Done."
