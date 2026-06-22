# Creates a local release keystore and release-signing.properties (gitignored).
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-RandomPassword {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    -join (1..$Length | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

$keystore = Join-Path $ProjectRoot "release.keystore"
$propsFile = Join-Path $ProjectRoot "release-signing.properties"
$javaHome = $env:JAVA_HOME
if (-not $javaHome) {
    $javaHome = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
}
$keytool = Join-Path $javaHome "bin\keytool.exe"
if (-not (Test-Path $keytool)) {
    throw "keytool not found at $keytool. Set JAVA_HOME to JDK 17+."
}

if ((Test-Path $keystore) -or (Test-Path $propsFile)) {
    Write-Host "release.keystore or release-signing.properties already exists."
    Write-Host "Delete them first if you want to regenerate signing keys."
    exit 1
}

$storePassword = New-RandomPassword
$keyAlias = "dpibypass"

& $keytool -genkeypair -v `
    -keystore $keystore `
    -alias $keyAlias `
    -keyalg RSA -keysize 2048 -validity 10000 `
    -storepass $storePassword -keypass $storePassword `
    -dname "CN=DpiBypass, OU=Local, O=DpiBypass, L=Local, ST=Local, C=RU"

@"
storePassword=$storePassword
keyPassword=$storePassword
keyAlias=$keyAlias
"@ | Set-Content -Path $propsFile -Encoding ASCII -NoNewline

Write-Host "Created:"
Write-Host "  $keystore"
Write-Host "  $propsFile"
Write-Host "Passwords are random and stored only in release-signing.properties (gitignored)."
