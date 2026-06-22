#Requires -Version 5.1
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'Stop'
$WindowsRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Lib = Join-Path $WindowsRoot 'lib'

. (Join-Path $Lib 'Config.ps1')
. (Join-Path $Lib 'Presets.ps1')
. (Join-Path $Lib 'ByeDpiManager.ps1')
. (Join-Path $Lib 'TgWsManager.ps1')
. (Join-Path $Lib 'SystemProxy.ps1')

Ensure-DpiBypassDirs
$paths = Get-DpiBypassPaths
$config = Get-DpiBypassConfig
$script:running = $false

$form = New-Object System.Windows.Forms.Form
$form.Text = 'DpiBypass'
$form.Size = New-Object System.Drawing.Size(480, 420)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)

$info = New-Object System.Windows.Forms.Label
$info.Location = New-Object System.Drawing.Point(16, 12)
$info.Size = New-Object System.Drawing.Size(440, 48)
$info.Text = "TG: WS-прокси (TgWsProxy)`nYouTube/Instagram: ByeDPI SOCKS5 + системный прокси"
$form.Controls.Add($info)

$status = New-Object System.Windows.Forms.Label
$status.Location = New-Object System.Drawing.Point(16, 64)
$status.Size = New-Object System.Drawing.Size(440, 24)
$status.Text = 'Статус: выключено'
$status.ForeColor = [System.Drawing.Color]::DarkRed
$form.Controls.Add($status)

$lblPreset = New-Object System.Windows.Forms.Label
$lblPreset.Location = New-Object System.Drawing.Point(16, 96)
$lblPreset.Size = New-Object System.Drawing.Size(120, 24)
$lblPreset.Text = 'Пресет ByeDPI:'
$form.Controls.Add($lblPreset)

$combo = New-Object System.Windows.Forms.ComboBox
$combo.Location = New-Object System.Drawing.Point(16, 120)
$combo.Size = New-Object System.Drawing.Size(440, 28)
$combo.DropDownStyle = 'DropDownList'
foreach ($name in Get-PresetNames) {
    [void]$combo.Items.Add((Get-PresetLabel $name))
}
$idx = [array]::IndexOf((Get-PresetNames), $config.preset)
if ($idx -lt 0) { $idx = 0 }
$combo.SelectedIndex = $idx
$form.Controls.Add($combo)

$chkByeDpi = New-Object System.Windows.Forms.CheckBox
$chkByeDpi.Location = New-Object System.Drawing.Point(16, 160)
$chkByeDpi.Size = New-Object System.Drawing.Size(440, 24)
$chkByeDpi.Text = 'ByeDPI — YouTube / Instagram (SOCKS 127.0.0.1:1080)'
$chkByeDpi.Checked = [bool]$config.enableByeDpi
$form.Controls.Add($chkByeDpi)

$chkTgWs = New-Object System.Windows.Forms.CheckBox
$chkTgWs.Location = New-Object System.Drawing.Point(16, 188)
$chkTgWs.Size = New-Object System.Drawing.Size(440, 24)
$chkTgWs.Text = 'Telegram WS-прокси (TgWsProxy, порт 1443)'
$chkTgWs.Checked = [bool]$config.enableTgWs
$form.Controls.Add($chkTgWs)

$chkSysProxy = New-Object System.Windows.Forms.CheckBox
$chkSysProxy.Location = New-Object System.Drawing.Point(16, 216)
$chkSysProxy.Size = New-Object System.Drawing.Size(440, 24)
$chkSysProxy.Text = 'Системный SOCKS-прокси (браузер, Edge, часть приложений)'
$chkSysProxy.Checked = [bool]$config.enableSysProxy
$form.Controls.Add($chkSysProxy)

$btnToggle = New-Object System.Windows.Forms.Button
$btnToggle.Location = New-Object System.Drawing.Point(16, 256)
$btnToggle.Size = New-Object System.Drawing.Size(440, 40)
$btnToggle.Text = 'Включить обход'
$form.Controls.Add($btnToggle)

$btnTg = New-Object System.Windows.Forms.Button
$btnTg.Location = New-Object System.Drawing.Point(16, 306)
$btnTg.Size = New-Object System.Drawing.Size(440, 32)
$btnTg.Text = 'Открыть настройки прокси Telegram'
$form.Controls.Add($btnTg)

$btnSetup = New-Object System.Windows.Forms.Button
$btnSetup.Location = New-Object System.Drawing.Point(16, 348)
$btnSetup.Size = New-Object System.Drawing.Size(440, 28)
$btnSetup.Text = 'Установить / обновить компоненты (setup.ps1)'
$form.Controls.Add($btnSetup)

function Update-UiState {
    if ($script:running) {
        $status.Text = 'Статус: обход активен'
        $status.ForeColor = [System.Drawing.Color]::DarkGreen
        $btnToggle.Text = 'Выключить обход'
        $combo.Enabled = $false
        $chkByeDpi.Enabled = $false
        $chkTgWs.Enabled = $false
        $chkSysProxy.Enabled = $false
    } else {
        $status.Text = 'Статус: выключено'
        $status.ForeColor = [System.Drawing.Color]::DarkRed
        $btnToggle.Text = 'Включить обход'
        $combo.Enabled = $true
        $chkByeDpi.Enabled = $true
        $chkTgWs.Enabled = $true
        $chkSysProxy.Enabled = $true
    }
}

function Get-SelectedPresetName {
    $names = @(Get-PresetNames)
    return $names[$combo.SelectedIndex]
}

function Start-Bypass {
    $preset = Get-SelectedPresetName
    if ($chkByeDpi.Checked) {
        if (-not (Test-Path $paths.ByeDpiExe)) {
            throw "Нет ciadpi.exe. Нажмите «Установить компоненты»."
        }
        Start-ByeDpi -ExePath $paths.ByeDpiExe -PresetName $preset
        if ($chkSysProxy.Checked) {
            Enable-SystemSocksProxy -Port $config.socksPort
        }
    }
    if ($chkTgWs.Checked) {
        if (-not (Test-Path $paths.TgWsExe)) {
            throw "Нет TgWsProxy_windows.exe. Нажмите «Установить компоненты»."
        }
        Start-TgWsProxy -ExePath $paths.TgWsExe
    }
    $script:running = $true
    Update-UiState
}

function Stop-Bypass {
    Stop-ByeDpi
    Stop-TgWsProxy
    Disable-SystemSocksProxy
    $script:running = $false
    Update-UiState
}

$btnToggle.Add_Click({
    try {
        if ($script:running) {
            Stop-Bypass
        } else {
            Start-Bypass
        }
    } catch {
        [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'DpiBypass', 'OK', 'Error')
    }
})

$btnTg.Add_Click({
    try {
        if (-not (Test-TgWsRunning)) {
            [System.Windows.Forms.MessageBox]::Show(
                'Сначала включите обход с TG WS-прокси, затем в трее TgWsProxy нажмите «Open in Telegram».',
                'DpiBypass', 'OK', 'Information')
        }
        Open-TelegramProxyLink
    } catch {
        [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'DpiBypass', 'OK', 'Error')
    }
})

$btnSetup.Add_Click({
  try {
        $setup = Join-Path $WindowsRoot 'setup.ps1'
        Start-Process powershell.exe -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $setup) -Wait
    } catch {
        [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'DpiBypass', 'OK', 'Error')
    }
})

$form.Add_FormClosing({
    if ($script:running) { Stop-Bypass }
    $names = @(Get-PresetNames)
    Save-DpiBypassConfig -Config ([PSCustomObject]@{
        preset         = $names[$combo.SelectedIndex]
        enableByeDpi   = $chkByeDpi.Checked
        enableTgWs     = $chkTgWs.Checked
        enableSysProxy = $chkSysProxy.Checked
        socksPort      = 1080
        tgWsPort       = 1443
    })
})

if (-not (Test-Path $paths.ByeDpiExe) -or -not (Test-Path $paths.TgWsExe)) {
    [System.Windows.Forms.MessageBox]::Show(
        'Компоненты не установлены. Нажмите «Установить / обновить компоненты».',
        'DpiBypass', 'OK', 'Warning')
}

Update-UiState
[void]$form.ShowDialog()
