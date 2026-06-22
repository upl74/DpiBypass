@echo off
setlocal
if not exist Z:\Sdk subst Z: "%LOCALAPPDATA%\Android"
set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d "%~dp0.."

if not exist "release.keystore" (
    echo release.keystore not found. Running setup-signing.ps1 ...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-signing.ps1"
    if errorlevel 1 exit /b 1
)

call gradlew.bat assembleRelease --no-daemon %*
if exist "app\build\outputs\apk\release\app-release.apk" (
    echo.
    echo Release APK: %CD%\app\build\outputs\apk\release\app-release.apk
)
endlocal
