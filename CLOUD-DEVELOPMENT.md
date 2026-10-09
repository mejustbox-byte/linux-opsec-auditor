# Разработка в облачной среде

Используйте существующий /workspace/linux-opsec-auditor: задача уже изолирована.
Не создавать worktree без просьбы пользователя. Проверить AGENTS.md и git status;
сохранять изменения пользователя. Весь setup находится в checkout, внешние onboarding
файлы и сохранённый venv не требуются.

```bash
cd /workspace/linux-opsec-auditor
bash tools/setup_environment.sh
.venv/bin/linux-opsec-auditor --version
PYTHONPATH=src .venv/bin/python tools/verify.py
```

Setup создаёт .venv и новый временный build output, проверяет lockfile/hash, запускает
тесты и build/smoke/reproducibility, затем устанавливает wheel. Не удаляет посторонние
outputs и не аудирует реальный хост. Runtime/tests не нуждаются в credentials.
Build tools требуют PyPI; CLI службы не запускает. SOURCE_DATE_EPOCH фиксирован.

## Сохранение и восстановление

install_script вызывает этот скрипт; start_skill содержит русские инструкции начала
работы, реальные ограничения и запрет автоматического production collect. Сохранение
draft не выполняет команды и не публикует snapshot. Пользователь просматривает,
сохраняет настройки среды и публикует её. Публикация среды и GitHub release — разные операции.

В новой задаче проверить checkout/version/status. При отсутствии .venv повторить setup;
не считать восстановление filesystem доказательством работающей authentication.
Процессы отсутствуют, поэтому нечего перезапускать. Реальное восстановление snapshot
в новой облачной задаче **НЕ ВЫПОЛНЕНО** в рамках этой доставки.

## Сеть и GitHub

Git read/push — штатный HTTPS proxy. API — api.github.com; cloud upload — uploads.github.com;
подробные Actions logs — results-receiver.actions.githubusercontent.com, если разрешён.
Сборка — pypi.org/files.pythonhosted.org. Presets сохраняются, неизвестный allowlist не
заменяется. Credentials не копировать/печатать и не добавлять в scripts/draft/public git.
Доступ проверяется реальной операцией, а не наличием GH_TOKEN.

При uploads 401 штатный Actions GITHUB_TOKEN публикует verified assets; write право
только у publish job. PR и CI сначала, tag/commit/ID и скачанные checksum после.
Сценарий — RELEASE-CHECKLIST.md и docs/release-workflow.md; локальная среда — LOCAL-PC.md.
