# Установка, проверка, обновление и удаление

Поддерживаемый путь запуска — Linux с настоящим procfs и Python >=3.12. Это требование
runtime, а не подтверждённая поддержка аудируемой ОС. Реальные платформенные проверки
не выполнены. На аудитируемом хосте нельзя устанавливать предпосылки в процессе аудита;
готовьте лабораторию заранее или оценивайте снимок на отдельной Linux-машине.

## Wheel: без сети при установке

Скачайте три native assets из публичного v0.1.0-alpha.2 и проверьте их вместе:

```bash
opsec_install_dir=$(mktemp -d)
cd "$opsec_install_dir"
gh release download v0.1.0-alpha.2 --repo mejustbox-byte/linux-opsec-auditor \
  --pattern 'linux_opsec_auditor-0.1.0a2*' --pattern SHA256SUMS
sha256sum --check SHA256SUMS
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a2-py3-none-any.whl
.venv/bin/linux-opsec-auditor --version
.venv/bin/linux-opsec-auditor schema
```

Версия должна быть 0.1.0a2. Checksum неподписан: это защита от повреждения, не независимое
доказательство издателя. Установка wheel не требует build tools или credentials.

## Исходники: checkout или sdist

Из проверенного checkout выполните `bash tools/setup_environment.sh`. Из скачанного
и проверенного sdist распакуйте linux_opsec_auditor-0.1.0a2.tar.gz в новый каталог,
перейдите в linux_opsec_auditor-0.1.0a2 и выполните тот же скрипт. Это не установка
в системный Python: используется .venv, build-only lock и временный каталог сборки.
Нужна сеть к PyPI для build tools; готовый wheel подходит для offline-установки.
Можно обойтись без установки: `PYTHONPATH=src python3 -m linux_opsec_auditor --version`.

Демонстрация на свежей копии synthetic fixture и ожидаемые exit codes описаны в
[инструкции](docs/usage.md). Отсутствие fail при unknown не считать полной проверкой.

## Windows

Нативный Windows runtime не поддерживается: нужны Linux/procfs/O_PATH. На Windows
можно загрузить assets и проверить SHA256 через Get-FileHash, но CLI не запускается
как поддерживаемое Windows-приложение. В уже подготовленном WSL2/VM откройте Linux
(`wsl.exe -d Ubuntu`) и следуйте POSIX-командам. WSL2, Hyper-V и эти Windows-команды
здесь **НЕ ВЫПОЛНЕНЫ**; не выдавайте их за подтверждение ядра/LSM Linux-сервера.
Лабораторные VM готовит оператор отдельно; продукт не меняет настройки хоста Windows.

## Обновление и удаление

Для обновления скачайте новую версию в новый приватный каталог, проверьте checksum,
установите в новый venv и выполните smoke до замены рабочего инструмента. Не двигайте
старые tags и не переписывайте исторические reports. Изменения политики сверяйте по
policy/rule versions и CHANGELOG.

Удаление только из выбранного venv:
`.venv/bin/python -m pip uninstall -y linux-opsec-auditor`.
Каталог .venv можно затем удалить вручную, убедившись, что это созданная вами среда.
Частные отчёты удаляются по согласованной retention-политике; системные конфигурации
не трогать. Ошибки доступа/unsafe path/несовместимой версии — [RUNBOOK](RUNBOOK.md).
