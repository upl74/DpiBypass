$script:TgWsProcess = $null

function Test-TgWsRunning {
    return $null -ne $script:TgWsProcess -and -not $script:TgWsProcess.HasExited
}

function Start-TgWsProxy {
    param([string]$ExePath)
    if (Test-TgWsRunning) { return }
    if (-not (Test-Path $ExePath)) {
        throw "TgWsProxy_windows.exe not found: $ExePath. Run setup.ps1"
    }
    $script:TgWsProcess = Start-Process -FilePath $ExePath -PassThru
    Start-Sleep -Milliseconds 800
    if ($script:TgWsProcess.HasExited) {
        throw "TgWsProxy exited. Try TgWsProxy_windows_7_64bit.exe (see README)."
    }
}

function Stop-TgWsProxy {
    if ($null -eq $script:TgWsProcess) { return }
    if (-not $script:TgWsProcess.HasExited) {
        $script:TgWsProcess | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    $script:TgWsProcess = $null
    Get-Process -Name 'TgWsProxy_windows*' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

function Open-TelegramProxyLink {
    param(
        [string]$ProxyHost = '127.0.0.1',
        [int]$Port = 1443,
        [string]$SecretFile = (Join-Path $env:APPDATA 'DpiBypass\tg_secret.txt')
    )
    $secret = ''
    if (Test-Path $SecretFile) {
        $secret = (Get-Content $SecretFile -Raw).Trim()
    }
    if ([string]::IsNullOrWhiteSpace($secret)) {
        Start-Process 'https://t.me/proxy'
        return
    }
    $url = "https://t.me/proxy?server=$ProxyHost&port=$Port&secret=$secret"
    Start-Process $url
}
