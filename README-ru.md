# DpiBypass — обход DPI для Telegram и YouTube

Android-приложение на базе [ByeDPI](https://github.com/hufrea/byedpi) / [ByeDPIAndroid](https://github.com/dovecoteescapee/ByeDPIAndroid).

**Это не VPN на сервер.** Трафик не шифруется и не уходит за границу — на телефоне запускается локальный SOCKS5 с подменой TLS-пакетов (fake/split), чтобы обойти DPI оператора (МТС, T2, Билайн, Мегафон и др.).

## Два режима

| Режим | Для чего | VPN? |
|-------|----------|------|
| **Обход (VPN)** | YouTube + Telegram без настройки прокси в каждом приложении | Локальный перехват **только** TG/YT (split tunnel). IP не меняется |
| **Прокси** | Только Telegram через SOCKS в настройках мессенджера | Нет перехвата, только `127.0.0.1:1080` |

По умолчанию включено **«Только Telegram и YouTube»** — остальные приложения работают как обычно.

## Быстрый старт

1. Соберите APK (см. ниже) или откройте проект в Android Studio.
2. Установите на телефон.
3. Нажмите **«Включить обход»** → подтвердите системный запрос (это локальный перехват, не удалённый VPN).
4. Откройте YouTube или Telegram на **мобильном интернете** (не Wi‑Fi).

Для Telegram дополнительно можно нажать **«Подключить MTProto-прокси (RU)»** — работает на Wi‑Fi.

## Пресет DPI (GoodbyeDPI)

По умолчанию (v1.0.6+) — рецепт из GoodbyeDPI для YouTube:

```
-i 127.0.0.1 -p 1080 -d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s -r1+s -S -a1 -As -d1 -d3+s -s6+s -d9+s -s12+s -d15+s -s20+s -d25+s -s30+s -d35+s -S -a1
```

| Часть | Назначение |
|-------|------------|
| `-d1 -d3+s -s6+s …` | «Лестница» disorder/split вдоль TLS ClientHello и SNI |
| `-r1+s` | Разбивка TLS-записи на SNI |
| `-S` | TCP MD5 Signature (Android/Linux) |
| `-a1` | 1 UDP fake-пакет |
| `-As` | Вторая группа при ошибке TLS |
| `-i 127.0.0.1 -p 1080` | Привязка SOCKS для VPN-режима |

Другие пресеты: **Настройки → Command line editor → Пресет обхода DPI**.

## Сборка APK

### Подпись release (один раз локально)

```powershell
cd C:\Projects\DpiBypass
powershell -File scripts\setup-signing.ps1
```

Создаёт `release.keystore` и `release-signing.properties` с **случайными** паролями (оба файла в `.gitignore`).  
Шаблон: `release-signing.properties.example`.

### Android Studio (рекомендуется)

1. Android Studio → Open → папка `DpiBypass`
2. SDK 34, NDK (для native ByeDPI)
3. Build → Build APK(s)

### Командная строка (Windows)

Нужны JDK 17+, Android SDK, NDK:

```bat
cd C:\Projects\DpiBypass
scripts\build-release.bat
```

APK: `app\build\outputs\apk\release\app-release.apk` (debug: `scripts\build-debug.bat` → `app-debug.apk`)

> Native-библиотеки (byedpi, hev-socks5) собираются через `ndk-build` при сборке.  
> Если на Windows падает — соберите в WSL/Linux или Android Studio.

## Как это устроено

```
Telegram/YouTube → [локальный tun → SOCKS 127.0.0.1:1080] → ByeDPI (fake/split TLS) → интернет напрямую
```

DPI оператора видит изменённые пакеты и пропускает соединение. Ваш IP остаётся IP оператора.

## Лицензия

Основа — GPL-3.0 (ByeDPIAndroid). См. `LICENSE` в репозитории-источнике.
