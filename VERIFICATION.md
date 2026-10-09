# Проверка и полнота документации

Не путать продуктовые synthetic tests, CI/packaging, публикацию assets и реальные
платформенные доказательства. Exit 0/открытый порт/нулевой набор тестов недостаточны.

## Зафиксированные реальные результаты

| Проверка | Фактический результат и свидетельство |
|---|---|
| Исходный MVP | 27 local unit/filesystem/CLI tests; source commit 70d43abb5bbc5350e7df2ed20e41847bba36938e |
| CI исходного main | Python 3.12/3.13 успешно: https://github.com/mejustbox-byte/linux-opsec-auditor/actions/runs/37924131624 |
| Guards публикации | 10 дополнительных synthetic tests; 37 всего до русского PR |
| Native assets alpha.1 | Успешный стандартный token/workflow: https://github.com/mejustbox-byte/linux-opsec-auditor/actions/runs/37926575177 |
| Проверка alpha.1 после скачивания | Два SHA256 и точное соответствие source/wheel commit; tag не передвигался |
| Чистая установка | Новый checkout venv и unpacked sdist setup, установленный wheel CLI, одинаковые wheel bytes в одной toolchain |
| Русский 0.1.0a2 | 39 local tests успешно; новая установка без сохранённого venv, wheel smoke и wheel reproducibility успешно; точные финальные SHA/CI/workflow в PR и русских release notes |

```bash
bash tools/setup_environment.sh
PYTHONPATH=src .venv/bin/python tools/verify.py
.venv/bin/python tools/release_artifacts.py --help
```

Runner требует непустые tests и ненулевой exit при failures. Проверяются повреждённые/
слишком большие/recursive JSON, типы и даты, stale/unknown платформы, missing/not_run,
symlink/FIFO/device, отказ перезаписи, mode 0600, cleanup ошибки и no-write synthetic root.
Guards проверяют tag/commit, метаданные и unexpected/tampered archive/checksum/asset.
Secret-pattern scan и ручное ревью выполнены; scan не доказывает абсолютное отсутствие секретов.

**НЕ ВЫПОЛНЕНО:** реальные VM всех candidate OS, aarch64, Windows/WSL2/Hyper-V,
container userspace tests, kernel/LSM/systemd/container host guarantees, delivery
журналов, backup restore, baseline/advisory authenticity, ресурсные 60 с/128 MiB,
новая облачная задача после snapshot. Sdist byte reproducibility не заявлена.

## Сопоставление полноты с прежними проектами

Использован перечень смысловых разделов, проверенный управляющим чатом для
sigma-ruleforge, autonomous-pentest-ai, modular-c2-framework, redblue-arena,
honeypot-grid. Не копируются их функции, стек, результаты и HTTP API.

| Общий раздел | Самостоятельный документ этого offline MVP |
|---|---|
| Назначение и индекс | README.md |
| Архитектура / стек | ARCHITECTURE.md / TECH-STACK.md / docs/adr-001.md |
| Установка / участие / этапы | INSTALL.md / CONTRIBUTING.md / ROADMAP.md |
| Безопасность / изменения | SECURITY.md / CHANGELOG.md |
| Модель угроз / API-контракт | THREAT-MODEL.md / CORE-CONTRACT.md, без HTTP API |
| Эксплуатация | RUNBOOK.md |
| Cloud / локальная инфраструктура | CLOUD-DEVELOPMENT.md / LOCAL-PC.md |
| Валидация / выпуск | VERIFICATION.md / RELEASE-CHECKLIST.md / RELEASE-NOTES.md |

Подробные docs/ сохранены на русском и связаны индексом; они не расширяют фактические
гарантии корневых документов. Полноту проверяют содержанием, исходниками и ссылками,
а не длиной текста. Включение root *.md в sdist обязательно и проверяется release guard.
