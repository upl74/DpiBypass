import winreg

_REG = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def enable_socks(host: str = "127.0.0.1", port: int = 1080) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"socks={host}:{port}")
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>")


def disable() -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "ProxyEnable")
            return bool(value)
    except OSError:
        return False
