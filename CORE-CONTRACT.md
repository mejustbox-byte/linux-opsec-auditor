# Контракт CLI, JSON и Python library

HTTP API отсутствует. Единственные интерфейсы — CLI, schema v1 и Python-функции.
Имена команд/ключей/статусов не переводятся; пояснения и отчёты на русском.

## CLI

| Команда | Фактическое поведение |
|---|---|
| --version | Версия package 0.1.0a2 |
| schema | Draft 2020-12 JSON Schema входа |
| collect --output PATH [--root PATH] | Фиксированные локальные чтения, новый приватный snapshot; root для synthetic tree |
| audit --input PATH [--format json\|text] [--output PATH] | Оценка snapshot, 12 findings; без host/network operations |
| --checks GROUP... | Выбор из 12 групп; прочие not_run, отчёт остаётся incomplete |
| --fail-on none\|fail\|incomplete | 0 после валидной оценки; 1 при fail; 3 при неполноте без fail; ошибки всегда 2 |

JSON максимум 1 MiB и регулярный файл без symlink в пути. Output — новый файл 0600
в каталоге владельца без group/world permissions; перезапись запрещена.

## Вход

Обязательны schema_version=1, collected_at UTC секунд, platform и observations.
Platform: family ubuntu/debian/rhel/other, version ограниченной формы, architecture
x86_64/aarch64/other. Candidate profiles перечислены в LOCAL-PC; остальные unknown.

Наблюдение содержит state observed/unavailable/not_run, source
synthetic/operator/static/runtime и values. Поля values опциональны: пропуск даёт
unknown, не безопасный default. Для unavailable/not_run values должен быть пуст.
Лишние поля и произвольные строки запрещены; числа/boolean различаются строго.
Повторные ключи, невозможные даты, неfinite числа и повреждённый JSON — ошибка.

```json
{"schema_version":1,"collected_at":"2026-10-09T00:00:00Z","platform":{"family":"ubuntu","version":"24.04","architecture":"x86_64"},"observations":{"ssh":{"state":"observed","source":"synthetic","values":{"permit_root":true,"password_auth":false,"effective":true}}}}
```

Это синтетический пример с фиксированной датой: после 24 ч он unknown. Свежую дату
реального факта не подделывать. Перечень typed fields — [schema](schemas/input-v1.schema.json)
и [матрица](docs/check-matrix.md).

## Выход и library

JSON: schema_version, tool_version, policy_version, generated_at/collected_at, platform,
platform_validation=unverified_candidate, summary по четырём статусам, complete,
findings. Finding: check_id/rule_version/title/status/severity/source/confidence,
evidence/reason/remediation/limitation. Нет hostname/username/raw config; digests
заменены digests_equal. Complete не равно safe. Статусы не скрывают ошибки документа:
некорректный input отвергается целиком до частичной оценки.

```python
from datetime import datetime, timezone
from linux_opsec_auditor.schema import loads, InputError
from linux_opsec_auditor.rules import audit, render_text
snapshot = loads(payload_bytes)
report = audit(snapshot, selected=None, now=datetime.now(timezone.utc))
text = render_text(report)
```

payload_bytes должен соответствовать schema. InputError не раскрывает исходные
значения. audit повторно валидирует snapshot; неверная selection вызывает ValueError.
now должен быть aware UTC; API max_age_hours по умолчанию 24, CLI его не меняет.
render_text принимает отчёт audit, а не произвольный недоверенный документ.

## Расширение правил

Добавьте типы в GROUPS и правило в RULES с устойчивым ID, severity, ожидаемыми values,
предпосылкой, рекомендацией и границей доказательства. Добавьте описание источника,
прав, OS/version scope, ложных срабатываний и synthetic pass/fail/unknown/not_run,
malformed/denied/stale cases. Обновите экспорт schema, fixtures, тестовые counts,
матрицу и policy/schema version по совместимости. Не расширяйте число групп,
уменьшая assertions; не добавляйте command execution. Новому collector нужны
allowlist, no-write tests и реальные VM evidence до обещания поддержки.
