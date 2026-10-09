# linux-opsec-auditor

GITHUB-OPSEC: аудит состояния Linux только на чтение, предварительный выпуск
**0.1.0a2**. CLI проверяет нормализованный JSON-снимок и выдаёт JSON или читаемый
отчёт с рекомендациями. Ограниченный локальный collector читает фиксированные
источники SSH и файловых метаданных; команды, sudo, сеть и исправления не используются.

**Работа на реальных платформах Linux ещё не подтверждена.** Синтетические тесты
не проверяют ядро, SELinux/AppArmor, systemd, контейнерную изоляцию, доставку журналов
или восстановление резервных копий. `pass` относится только к представленным данным
и ограниченному правилу, а не удостоверяет безопасность сервера.

## Быстрый запуск: Linux и Python 3.12+

Из checkout, без установки и сторонних зависимостей:

```bash
PYTHONPATH=src python3 -m linux_opsec_auditor --version
PYTHONPATH=src python3 -m linux_opsec_auditor audit --input fixtures/unsafe.json --format text
```

Для свежей небезопасной фикстуры ожидается exit 1. Дата всех фикстур фиксирована:
`2026-10-09T00:00:00Z`. После 24 часов результаты становятся `unknown`.
Для демонстрации обновляйте дату только в приватной копии синтетической фикстуры:

```bash
opsec_demo_dir=$(mktemp -d)
python3 - "$opsec_demo_dir/synthetic.json" <<'PY'
from datetime import datetime, timezone
import json, sys
from pathlib import Path
snapshot = json.loads(Path('fixtures/healthy.json').read_text())
snapshot['collected_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
Path(sys.argv[1]).write_text(json.dumps(snapshot))
PY
PYTHONPATH=src python3 -m linux_opsec_auditor audit --input "$opsec_demo_dir/synthetic.json" --format json --fail-on incomplete
```

Это синтетическая демонстрация, не свидетельство с реального сервера.
Подробные команды установки, сбора и обработки результатов — в [инструкции](docs/usage.md).

## Возможности и границы MVP

12 групп правил: SSH, sudo, PAM, systemd, файловые права, обновление ядра, LSM,
контейнерные границы, audit/journal, резервные копии, дрейф и обновления пакетов.
Локальный collector реализует **только статические фрагменты SSH, метаданные четырёх
фиксированных файлов, определение ОС и ограниченный индикатор SELinux**. Остальным
группам нужны нормализованные внешние данные; при их отсутствии результат `unknown`.
Удалённый SSH, парсеры sudo/PAM, vendor advisories и runtime-проверки служб отложены.

Результат содержит `pass/fail/unknown/not_run`, стабильный ID, severity, confidence,
evidence, объяснение, рекомендацию и ограничения. Неизвестные версии и архитектуры
не наследуют `pass`. Произвольные строки и сырая конфигурация в evidence запрещены.
JSON ограничен 1 MiB; лишние поля, повторные ключи, неверные типы, числа вне диапазона
и некорректные даты отвергаются. Свежесть данных не подтверждает их подлинность.

## Разработка и проверка

```bash
bash tools/setup_environment.sh
```

Скрипт создаёт `.venv` без зависимости от сохранённого состояния, устанавливает
сборочные инструменты по версиям и хешам, выполняет непустой набор тестов, собирает
wheel/sdist, проверяет отдельную установку CLI и воспроизводимость wheel.
Runtime и тесты используют стандартную библиотеку. CI проверяет Python 3.12/3.13;
успех на Ubuntu runner не является подтверждением поддержки ОС.

## Полный индекс документации

| Раздел | Основной документ | Подробности |
|---|---|---|
| Назначение, требования и этапы | [ROADMAP](ROADMAP.md) | [Требования](docs/requirements.md) |
| Компоненты и поток данных | [ARCHITECTURE](ARCHITECTURE.md) | [Архитектура](docs/architecture.md) |
| Стек и точные зависимости | [TECH-STACK](TECH-STACK.md) | [ADR](docs/adr-001.md) |
| Установка, обновление, удаление | [INSTALL](INSTALL.md) | [CLI-инструкция](docs/usage.md) |
| Участие и review | [CONTRIBUTING](CONTRIBUTING.md) | [История изменений](CHANGELOG.md) |
| Лицензия и следующие циклы | [MIT](LICENSE), [русский перевод](LICENSE.ru.md) | [AGENTS](AGENTS.md) |
| Безопасность и угрозы | [SECURITY](SECURITY.md), [THREAT-MODEL](THREAT-MODEL.md) | [Полная модель](docs/threat-model.md) |
| CLI/JSON/library и расширение правил | [CORE-CONTRACT](CORE-CONTRACT.md) | [Schema](schemas/input-v1.schema.json), [матрица](docs/check-matrix.md) |
| Эксплуатация и ошибки | [RUNBOOK](RUNBOOK.md) | [CLI-инструкция](docs/usage.md) |
| Облако и восстановление | [CLOUD-DEVELOPMENT](CLOUD-DEVELOPMENT.md) | [Среда](docs/environment.md) |
| Реальная локальная лаборатория | [LOCAL-PC](LOCAL-PC.md) | [Протокол](docs/laboratory.md) |
| Проверки и полнота документов | [VERIFICATION](VERIFICATION.md) | [Матрица](docs/check-matrix.md) |
| Выпуск/tag/assets | [RELEASE-CHECKLIST](RELEASE-CHECKLIST.md) | [Workflow](docs/release-workflow.md) |
| Примечания к выпуску | [RELEASE-NOTES](RELEASE-NOTES.md) | [Ограничения](docs/release-notes.md) |

Реальные credentials, конфигурация инфраструктуры, инвентари и дампы аудита не должны
попадать в этот публичный репозиторий. В issues и PR используйте только синтетические данные.
