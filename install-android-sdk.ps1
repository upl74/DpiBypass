# Install Android SDK + NDK for DpiBypass build
$ErrorActionPreference = "Stop"

$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk"
$Studio = "C:\Program Files\Android\Android Studio"
$Java = "$Studio\jbr\bin\java.exe"

if (-not (Test-Path $Java)) { throw "Android Studio JBR not found: $Java" }

New-Item -ItemType Directory -Force -Path $SdkRoot | Out-Null
$cmdlineZip = "$env:TEMP\commandlinetools-win.zip"
$cmdlineUrl = "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"

if (-not (Test-Path "$SdkRoot\cmdline-tools\latest\bin\sdkmanager.bat")) {
    Write-Host "Downloading Android command-line tools..."
    Invoke-WebRequest -Uri $cmdlineUrl -OutFile $cmdlineZip -UseBasicParsing
    $extract = "$env:TEMP\android-cmdline"
    if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $cmdlineZip -DestinationPath $extract -Force
    New-Item -ItemType Directory -Force -Path "$SdkRoot\cmdline-tools\latest" | Out-Null
    Copy-Item "$extract\cmdline-tools\*" "$SdkRoot\cmdline-tools\latest" -Recurse -Force
}

$sdkmanager = "$SdkRoot\cmdline-tools\latest\bin\sdkmanager.bat"
$yes = "y`n" * 20

Write-Host "Installing SDK packages + NDK (may take several minutes)..."
$packages = @(
    "platform-tools",
    "platforms;android-34",
    "build-tools;34.0.0",
    "ndk;27.2.12479018",
    "cmake;3.22.1"
)

$env:JAVA_HOME = "$Studio\jbr"
$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot

cmd /c "echo $yes | `"$sdkmanager`" --sdk_root=`"$SdkRoot`" $($packages -join ' ')"

Write-Host "SDK root: $SdkRoot"
if (Test-Path "$SdkRoot\ndk") { Get-ChildItem "$SdkRoot\ndk" | Select-Object Name }

# local.properties for Gradle
$props = "sdk.dir=$($SdkRoot -replace '\\','/')"
Set-Content -Path "$PSScriptRoot\local.properties" -Value $props -Encoding ASCII
Write-Host "Wrote local.properties"
