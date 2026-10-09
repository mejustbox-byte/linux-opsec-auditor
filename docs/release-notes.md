# v0.1.0-alpha.2 / package 0.1.0a2

Обновлённый экспериментальный prerelease с русской документацией и пользовательскими
описаниями. Сам этот файл не доказывает публикацию: нужны успешный workflow,
публичный prerelease, три загруженных assets и проверенные checksum. Старый выпуск
v0.1.0-alpha.1 и его tag сохраняются без передвижения.

## Возможности

- Строгая схема версии 1: типы/даты/диапазоны/размер, запрет повторных ключей, безопасные ошибки.
- 12 групп правил: evidence, confidence, severity, remediation, pass/fail/unknown/not_run.
  Неизвестная платформа и устаревшее evidence дают unknown.
- JSON и читаемый отчёт, выбор правил и порога неуспеха.
- Ограниченный collector SSH/метаданных/SELinux без команд, сети, sudo и исправлений;
  приватный новый файл вместо перезаписи.
- Синтетические unit, filesystem и CLI integration tests; guards публикации.
- Нет runtime-зависимостей; hash-locked сборка, wheel/sdist, smoke установленного CLI
  и воспроизводимость wheel в одной toolchain.
- SHA-pinned CI Python 3.12/3.13 и Actions публикация с contents:write только у publish job.
- Русские README, docs, безопасность, участие, CHANGELOG, schema/rule/help описания
  и сохранённые инструкции среды.

## Проверка и ограничения

Локальные/CI тесты и packaging не являются тестами инфраструктуры. Реальные VM
Ubuntu 22.04/24.04, Debian 12/13, RHEL 9/10 **не проверены**. Aarch64, контейнерный
userspace, effective sshd, kernel/backports, реальный LSM/systemd/container isolation,
audit/journal delivery, restore и baseline integrity **не подтверждены**.
Платные ресурсы не создавались.

Большинство collectors не реализованы; нужны внешние нормализованные факты.
source не подписан. SSH не раскрывает Include/Match, FILE исключает ACL/parents,
LSM host_context всегда false. Нет remote SSH, vendor feed downloads, парсеров
sudo/PAM, remediation или сбора секретов. У I/O нет жёсткого timeout.
Проверена воспроизводимость wheel, но не байтовая воспроизводимость sdist.
Возможны atime/журналы чтения; настройки хоста не меняются.

## Assets и установка

Ожидаемые native assets: linux_opsec_auditor-0.1.0a2-py3-none-any.whl,
linux_opsec_auditor-0.1.0a2.tar.gz, SHA256SUMS. Workflow проверяет исходный tag/commit,
содержимое файлов и скачанные checksum до публикации. Скачать все три и проверить
sha256sum. Установка в Linux venv с Python 3.12+:

```bash
python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a2-py3-none-any.whl
```

Исходный архив содержит инструкции и фикстуры. Полные команды и exit codes — в
[инструкции](usage.md); реальная приёмка — в [лаборатории](laboratory.md).
Checksum не подписан и не является независимой аттестацией происхождения.
