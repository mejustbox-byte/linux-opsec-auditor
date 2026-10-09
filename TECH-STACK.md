# Технологический стек и версии

Выбор: Python >=3.12 на Linux, стандартная библиотека runtime и unittest. Текущая
облачная проверка: Python 3.12.14; CI — ветки Python 3.12 и 3.13 без фиксации patch.
Значит полная бинарная идентичность всей ОС/toolchain между машинами не обещается.
Аргументы выбора и альтернативы Go/Rust/shell — [ADR](docs/adr-001.md).

| Компонент | Точная фиксация | Назначение |
|---|---|---|
| package | 0.1.0a2, pyproject.toml и __version__ | Экспериментальная версия |
| build | 1.3.0 | Сборка без isolation после verified установки tools |
| setuptools | 80.9.0 | Backend wheel/sdist |
| packaging | 25.0 | Зависимость сборки |
| pyproject-hooks | 1.2.0 | Зависимость сборки |
| wheel | 0.45.1 | Сборочные инструменты |
| runtime/tests | Сторонних зависимостей нет | argparse/json/os/pathlib/unittest |

Каждый build wheel имеет SHA256 в requirements-build.lock. Установка:
`pip install --require-hashes --no-deps --only-binary=:all: -r requirements-build.lock`.
TLS/hash verification сохраняются. Lockfile не переписывается установкой. Новая
версия зависимости требует ревью wheel из доверенного источника и нового хеша,
а не подмены checksum для обхода ошибки.

Actions закреплены полным SHA в .github/workflows/*.yml; комментарии указывают версии
checkout v4.2.2, setup-python v5.6.0, upload-artifact v4.6.2, download-artifact v4.3.0.
SOURCE_DATE_EPOCH=1791504000 используется для сравнения wheel в одной toolchain;
байтовая воспроизводимость sdist не подтверждена. Linux/procfs нужны файловым fd
операциям; нативный Windows не поддержан, WSL2 как лаборатория не проверен.

## Inventory лицензий и supply chain

| Что используется | Лицензия по verified package metadata | Поставляется в runtime wheel проекта |
|---|---|---|
| Собственный код | MIT; LICENSE и LICENSE.ru.md | Да, оба текста и metadata MIT |
| Python/stdlb | Условия Python Software Foundation; проверяются в установленном runtime | Нет, предпосылка среды |
| build 1.3.0 | MIT | Нет, build-only |
| setuptools 80.9.0 | MIT | Нет, build-only |
| packaging 25.0 | Apache/BSD; LICENSE.APACHE и LICENSE.BSD | Нет, build-only |
| pyproject-hooks 1.2.0 | MIT | Нет, build-only |
| wheel 0.45.1 | MIT | Нет, build-only |
| Actions | SHA-pinned automation; лицензии соответствующих официальных репозиториев | Нет, только CI |

Версии/лицензии build tools сверены с METADATA скачанных wheels, совпадающих с lockfile.
Не копировать их license inventory как лицензию собственных bundled dependencies:
в runtime сторонних dependencies нет. Обновления проходят provenance/hash/license
ревью. Проверки assets сравнивают license bytes с Git и metadata с MIT.
