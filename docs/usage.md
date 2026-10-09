# Установка и команды CLI

Нужны Linux, настоящий procfs и Python >=3.12. Не запускать от root без отдельно
согласованных привилегированных чтений. Аудитор не устанавливает Python/пакеты,
не выполняет sudo и не меняет конфигурацию. Runtime-зависимостей нет.

## Из исходников

```bash
bash tools/setup_environment.sh
.venv/bin/linux-opsec-auditor --version
```

Или без установки: `PYTHONPATH=src python3 -m linux_opsec_auditor`.
Сборочные инструменты устанавливаются только в `.venv` по hash-locked списку.

## Из проверенных release assets

Tag обновлённого выпуска: `v0.1.0-alpha.2`, версия package: `0.1.0a2`.
Команды ниже требуют реально опубликованных native assets; один draft или текст
release notes не подтверждают готовность. Старый tag `v0.1.0-alpha.1` сохранён.

```bash
mkdir -p opsec-download
cd opsec-download
gh release download v0.1.0-alpha.2 --repo mejustbox-byte/linux-opsec-auditor \
  --pattern 'linux_opsec_auditor-0.1.0a2-py3-none-any.whl' \
  --pattern 'linux_opsec_auditor-0.1.0a2.tar.gz' --pattern SHA256SUMS
sha256sum --check SHA256SUMS
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a2-py3-none-any.whl
.venv/bin/linux-opsec-auditor --version
```

Checksum обнаруживает повреждение; неподписанный checksum из того же release не
является независимой аттестацией издателя. Для установки wheel сборочные инструменты не нужны.

## Ограниченный локальный сбор

На явно разрешённом лабораторном хосте с заранее подготовленным Python:

```bash
opsec_report_dir=$(mktemp -d)
linux-opsec-auditor collect --output "$opsec_report_dir/snapshot.json"
linux-opsec-auditor audit --input "$opsec_report_dir/snapshot.json" \
  --format json --output "$opsec_report_dir/report.json" --fail-on incomplete
```

Ожидается неполнота: collector не собирает всё evidence политики. Не публиковать
эти файлы. CLI не создаёт каталог, не перезаписывает файл и не следует symlink;
записывается только явно выбранный новый файл 0600. Каталог должен принадлежать
эффективному UID и не иметь group/world bits. Используйте приватный каталог вне
public checkout. stdout — намеренный экспорт; журналы терминала и pipeline контролирует оператор.
`--root PATH` задаёт синтетическое дерево, а не удалённый хост. Нерегулярные файлы,
symlink и опасные компоненты отвергаются. Родительские каталоги input тоже не должны
быть symlink; избегайте алиасов вроде /var/run и выбирайте настоящий приватный путь.

## Нормализованные данные

`linux-opsec-auditor schema` печатает JSON Schema версии 1. Поля и примеры перечислены
в fixtures/ и матрице правил. Допустимы только утверждения правильного типа с объявленным
source. Не вставляйте конфигурацию, usernames, tokens, hostnames или журналы.
collected_at — реальный момент получения фактов UTC, не дата для обхода свежести.
Обновлять дату демонстрации можно только при сохранении source=synthetic.

```bash
linux-opsec-auditor audit --input /private/path/snapshot.json --format text
linux-opsec-auditor audit --input /private/path/snapshot.json --format json --checks ssh files
```

Имена групп: ssh sudo pam systemd files kernel lsm containers logs backups drift patches.
Не выбранные остаются not_run и не делают полный отчёт complete. Настройки не
выполняют команды и не меняют пороги скрытно.

## Exit codes

| Код | Значение |
|---|---|
| 0 | Команда успешна при выбранном пороге; unknown/not_run всё ещё возможны |
| 1 | Есть fail при --fail-on fail либо --fail-on incomplete |
| 2 | Неверный вызов/вход, недоступный файл, небезопасный вывод или I/O error |
| 3 | Fail нет, но есть unknown/not_run при --fail-on incomplete |

`--fail-on none` даёт 0 после корректной оценки даже при fail, но не скрывает ошибки
парсинга/I/O. Complete может содержать fail и не является сертификацией. source,
ограничения и непроверенная поддержка видны в findings. Ошибки не выводят исходные значения.
