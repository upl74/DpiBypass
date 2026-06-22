$script:ByeDpiProcess = $null

function Test-ByeDpiRunning {
    return $null -ne $script:ByeDpiProcess -and -not $script:ByeDpiProcess.HasExited
}

function Start-ByeDpi {
    param(
        [string]$ExePath,
        [string]$PresetName = 'youtube'
    )
    if (Test-ByeDpiRunning) {
        return
    }
    if (-not (Test-Path $ExePath)) {
        throw "ciadpi.exe not found: $ExePath. Run setup.ps1"
    }
    $cmd = Get-PresetCommand -Name $PresetName
    $args = Split-PresetArgs -CommandLine $cmd
    $script:ByeDpiProcess = Start-Process -FilePath $ExePath -ArgumentList $args -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 400
    if ($script:ByeDpiProcess.HasExited) {
        throw "ciadpi.exe exited with code $($script:ByeDpiProcess.ExitCode)"
    }
}

function Stop-ByeDpi {
    if ($null -eq $script:ByeDpiProcess) { return }
    if (-not $script:ByeDpiProcess.HasExited) {
        $script:ByeDpiProcess | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    $script:ByeDpiProcess = $null
}
