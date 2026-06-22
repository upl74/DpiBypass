# DpiBypass для Windows

Нормальное десктоп-приложение: тёмная тема, иконка в трее, без консоли.

## Быстрый старт

```powershell
cd C:\CompanyCall\User\DpiBypassApp\windows
.\setup.ps1
```

Двойной клик по **`DpiBypass.bat`** — откроется окно приложения.

## Возможности

- Современный интерфейс (CustomTkinter, тёмная тема)
- Сворачивание в **системный трей** — обход работает в фоне
- Переключатель вкл/выкл, выбор пресета ByeDPI
- Telegram WS + YouTube/Instagram через ByeDPI
- Настройки в `%APPDATA%\DpiBypass\config.json`

## Использование

1. **Компоненты** — скачать `ciadpi.exe` и `TgWsProxy_windows.exe` (один раз).
2. **Включить обход**.
3. **Telegram** — в трее TgWsProxy → подтвердить прокси.
4. **YouTube / Instagram** — в браузере (Edge/Chrome) с системным SOCKS.

## Сборка одного EXE (опционально)

```powershell
.\build-exe.ps1
```

Получите `dist\DpiBypass.exe`. Рядом положите папку `bin\` с `ciadpi.exe` и `TgWsProxy_windows.exe`.

## Структура

```
windows/
  DpiBypass.bat       — запуск (venv + GUI)
  setup.ps1           — зависимости Python + бинарники
  build-exe.ps1       — PyInstaller → DpiBypass.exe
  app/main.py         — интерфейс
  app/core/           — движок (как на Android)
  bin/                — ciadpi.exe, TgWsProxy
  lib/                — legacy PowerShell (не нужен для GUI)
```

## Требования

- Windows 10/11
- Python 3.10+ (устанавливается автоматически в venv при первом запуске)

## Отличия от Android

Per-app VPN на Windows нет — браузер идёт через системный SOCKS. Мобильного YouTube на ПК нет.
