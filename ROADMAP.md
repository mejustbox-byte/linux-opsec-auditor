# Этапы и критерии приёмки

| Этап | Состояние | Критерий завершения |
|---|---|---|
| Требования, threat model, ADR, schema | Реализовано для MVP | Закрытый вход, пределы гарантий, source и неизвестность описаны |
| Offline evaluator, JSON/текст, collector SSH/metadata | Реализовано ограниченно | Непустые tests, безопасные ошибки, no-write/no-command, приватный вывод |
| CI, wheel/sdist, native release assets | Реализовано в alpha.1; повторяется в alpha.2 | Точный tag/commit, clean install, скачанные checksum, публичный prerelease |
| Русская полная документация | Текущий 0.1.0a2 | Индекс, самостоятельные разделы, ссылки и соответствие исходникам |
| Пообъектные findings, ACL/parents | Не реализовано | Сопоставление с VM, отказ доступа, symlink/ACL негативные случаи |
| Effective SSH и sudo/PAM по ОС | Не реализовано | Match/Include/context, версии parsers, recovery, no escalation |
| systemd/containers/logs runtime | Не реализовано | Безопасный allowlist источников и реальные host evidence |
| Advisories/backports и baseline trust | Не реализовано | Подлинность/свежесть/entitlement, normalization/signatures |
| Remote SSH | Не реализовано | Отдельный ADR, strict known_hosts, ограниченные команды/таймауты |
| Стабильная поддержка платформ | Не подтверждена | Отдельные реальные Ubuntu/Debian/RHEL/architecture VM и ресурсные измерения |

Никаких автоматических исправлений: read-only остаётся обязательным. Fixture/container
не заменяет VM и работу собственного ядра/LSM. Unknown нельзя превращать в pass
ради выпуска. Для неподдерживаемой версии нужен новый явно проверенный профиль.
Реальные secrets/инвентари и платные ресурсы не нужны и не разрешены.

Требования — [docs](docs/requirements.md); по каждой группе — [матрица](docs/check-matrix.md).
Критерии выпуска — [checklist](RELEASE-CHECKLIST.md), реальные этапы — [лаборатория](LOCAL-PC.md).
