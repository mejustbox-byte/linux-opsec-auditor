# Облачная среда разработки

Checkout содержит всю настройку: внешняя onboarding-директория и сохранённый venv
не требуются. Задачи уже изолированы; используйте существующий checkout без нового
Git worktree, если пользователь не попросил его. Сохраняйте посторонние изменения.

## Установка и обновление

Linux worker, Python 3.12+ и Git:

```bash
bash tools/setup_environment.sh
```

Создаётся `.venv`, сборочные wheels ставятся по requirements-build.lock с проверкой
хешей. Затем непустые unit/integration tests, проверка текста/schema/ссылок/паттернов
секретов, wheel/sdist, отдельная установка CLI, воспроизводимость wheel и установка
CLI в `.venv`. Скрипт не запускает аудит реального хоста и не меняет настройки безопасности.
Сборка использует новый временный каталог, не требует сохранённого venv и не удаляет
посторонние результаты. Проверка на чистом venv обязательна при изменении настройки.
Runtime/tests — stdlib. Для сборочных загрузок нужны pypi.org/files.pythonhosted.org.
Credentials или значения injected secrets в настройке не сохраняются.

## Начало работы

Службы, daemon и БД не запускаются:

```bash
.venv/bin/linux-opsec-auditor --version
PYTHONPATH=src .venv/bin/python tools/verify.py
.venv/bin/linux-opsec-auditor schema
```

Если `.venv` отсутствует/непригоден, повторите setup. [Инструкция](usage.md) содержит
синтетические примеры и явно разрешённый лабораторный collect. Не собирать production
данные автоматически при старте. Платформенные ограничения — в [лаборатории](laboratory.md).

## Draft и публикация среды

install_script вызывает checkout setup; start_skill ссылается на эти инструкции.
Прежнее docs-only ограничение отменено пользователем. Сохранённый draft отличается
от runtime-выполнения и публикации snapshot. В новой задаче повторно проверьте
checkout, setup и artifacts; процессы и credentials не считаются сохранёнными.

Git читает/публикует через штатный proxy. API PR/merge/CI/release — api.github.com;
cloud upload — uploads.github.com. Для подробных Actions logs может потребоваться
results-receiver.actions.githubusercontent.com. Домены сохранены в draft без
credentials и с сохранением package-manager presets. Разрешённый домен не доказывает
авторизацию: проверяются реальные операции. Нативные assets публикуются через
[Actions workflow](release-workflow.md) со штатным GITHUB_TOKEN; новые credentials не нужны.
