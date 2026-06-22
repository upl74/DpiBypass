# DpiBypass для Windows (v1.3.3+)

Десктоп-приложение с интерфейсом как на Android: тёмная тема Material 3, трей, автозапуск.

## Быстрый старт

```powershell
cd C:\Projects\DpiBypass\windows
.\setup.ps1
.\DpiBypass.bat
```

Или готовый пакет: `dist\DpiBypass-Windows.zip` после `.\build-package.ps1`.

## Возможности

- Современный интерфейс (CustomTkinter, палитра как в Android v1.3.3)
- **Автозапуск с Windows** — переключатель в настройках
- **Автовключение обхода** — при старте приложения
- Сворачивание в **системный трей**
- ByeDPI (YouTube/Instagram в браузере) + Telegram WS-прокси
- **Discord** — UDP-обход, Drop SACK, запуск десктоп-клиента через SOCKS
- Настройки: `%APPDATA%\DpiBypass\config.json`

## Использование

1. **Компоненты** — один раз скачать `ciadpi.exe` (кнопка в приложении).
2. Включите **автозапуск** / **автовключение** при необходимости.
3. **Включить обход**.
4. **Telegram** — кнопка «Telegram» для ссылки на локальный прокси.
5. **YouTube** — откройте в Edge/Chrome (системный SOCKS).

## Сборка EXE

```powershell
.\setup.ps1          # venv + ciadpi.exe
.\build-package.ps1  # dist\DpiBypass.exe + dist\DpiBypass-Windows.zip
```

Рядом с `DpiBypass.exe` нужна папка `bin\ciadpi.exe` (копируется в zip автоматически).

## Структура

```
windows/
  DpiBypass.bat
  setup.ps1
  build-exe.ps1
  build-package.ps1
  app/main.py
  app/core/
  bin/ciadpi.exe
  dist/DpiBypass.exe
```

## Требования

- Windows 10/11
- Python 3.10+ (для разработки; EXE работает без Python)
