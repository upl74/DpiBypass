@echo off
setlocal
rem Map Android SDK to ASCII drive letter (required for ndk-build on Cyrillic Windows profiles)
if not exist Z:\Sdk (
    subst Z: "%LOCALAPPDATA%\Android"
)
set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d "%~dp0.."
call gradlew.bat assembleDebug %*
if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo.
    echo APK: %CD%\app\build\outputs\apk\debug\app-debug.apk
)
endlocal
