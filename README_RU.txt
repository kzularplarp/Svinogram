TELEGRAM 11.12 UNSIGNED BUILDER
================================

Что это
-------
Этот набор файлов запускает GitHub Actions на macOS и собирает Telegram iOS
11.12 (release-11.12) из официального репозитория:

https://github.com/TelegramMessenger/Telegram-iOS

Никакой готовый decrypted IPA не скачивается.

Что загрузить на GitHub
-----------------------
Создай пустой PUBLIC репозиторий, например:
telegram-11-12-builder

Загрузи в него:
.github/workflows/build-telegram-11.12.yml
build_unsigned.py

Потом:
1. Открой Actions.
2. Выбери "Build Telegram 11.12 unsigned".
3. Нажми "Run workflow".
4. Дождись окончания.
5. Внизу запуска появится artifact "Telegram-11.12-unsigned".
6. Скачай его — внутри будет Telegram-11.12-unsigned.ipa.

Дальше для Svinogram
--------------------
В Feather:
1. Импортируй Telegram-11.12-unsigned.ipa.
2. Добавь Svinogram .deb как tweak.
3. Подпиши своим сертификатом.
4. Установи.

Версии
------
Telegram: release-11.12
macOS runner: macos-15
Xcode: 16.2
Bazel: из официального versions.json Telegram (8.2.1).

Важно
-----
В официальном Telegram-iOS есть открытый issue о проблемах сборки release-11.12
на некоторых конфигурациях. Этот workflow убирает provisioning/signing из
сборки и отключает extensions, но upstream-ошибка компиляции всё равно
теоретически возможна.

Если Action упадёт, пришли лог красного шага "Build unsigned arm64 IPA".
