$script:WindowsRoot = Split-Path -Parent $PSScriptRoot
$script:BinDir = Join-Path $WindowsRoot 'bin'
$script:DataDir = Join-Path $env:APPDATA 'DpiBypass'
$script:ConfigFile = Join-Path $DataDir 'config.json'

function Get-DpiBypassPaths {
    [PSCustomObject]@{
        Root       = $script:WindowsRoot
        BinDir     = $script:BinDir
        DataDir    = $script:DataDir
        ConfigFile = $script:ConfigFile
        ByeDpiExe  = Join-Path $script:BinDir 'ciadpi.exe'
        TgWsExe    = Join-Path $script:BinDir 'TgWsProxy_windows.exe'
    }
}

function Get-DpiBypassConfig {
    $defaults = @{
        preset         = 'youtube'
        enableByeDpi   = $true
        enableTgWs     = $true
        enableSysProxy = $true
        socksPort      = 1080
        tgWsPort       = 1443
    }
    if (-not (Test-Path $script:ConfigFile)) {
        return [PSCustomObject]$defaults
    }
    try {
        $loaded = Get-Content $script:ConfigFile -Raw | ConvertFrom-Json
        foreach ($key in $defaults.Keys) {
            if ($null -eq $loaded.$key) { $loaded | Add-Member -NotePropertyName $key -NotePropertyValue $defaults[$key] -Force }
        }
        return $loaded
    } catch {
        return [PSCustomObject]$defaults
    }
}

function Save-DpiBypassConfig {
    param($Config)
    New-Item -ItemType Directory -Force -Path $script:DataDir | Out-Null
    $Config | ConvertTo-Json | Set-Content -Path $script:ConfigFile -Encoding UTF8
}

function Ensure-DpiBypassDirs {
    New-Item -ItemType Directory -Force -Path $script:BinDir | Out-Null
    New-Item -ItemType Directory -Force -Path $script:DataDir | Out-Null
}
