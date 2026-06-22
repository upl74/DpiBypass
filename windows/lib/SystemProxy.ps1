$script:ProxyRegPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'

function Enable-SystemSocksProxy {
    param(
        [string]$SocksHost = '127.0.0.1',
        [int]$Port = 1080
    )
    Set-ItemProperty -Path $script:ProxyRegPath -Name ProxyEnable -Value 1
    Set-ItemProperty -Path $script:ProxyRegPath -Name ProxyServer -Value "socks=$SocksHost`:$Port"
    Set-ItemProperty -Path $script:ProxyRegPath -Name ProxyOverride -Value '<local>'
}

function Disable-SystemSocksProxy {
    Set-ItemProperty -Path $script:ProxyRegPath -Name ProxyEnable -Value 0
}

function Test-SystemSocksProxy {
    $enabled = (Get-ItemProperty -Path $script:ProxyRegPath -Name ProxyEnable -ErrorAction SilentlyContinue).ProxyEnable
    return $enabled -eq 1
}
