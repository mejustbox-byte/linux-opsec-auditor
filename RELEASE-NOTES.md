# Примечания к выпуску 0.1.0a2

Tag: v0.1.0-alpha.2, package: 0.1.0a2. Это prerelease: kernel/LSM и поддержка реальных
платформ не подтверждены. Старый выпуск 0.1.0a1 и его tag сохраняются.

Изменения: русская полная документация с привычными root-разделами и сохранёнными
docs/, русские schema/rule/help описания, воспроизводимая подготовка без сохранённого
venv, ограниченная публикация native assets через стандартный Actions token.
Read-only границы, 12 правил, schema/policy v1 и четыре статуса сохраняются.
Ни remote SSH, ни sudo/PAM/vendor collectors, ни remediation не добавлены.

Assets: linux_opsec_auditor-0.1.0a2-py3-none-any.whl,
linux_opsec_auditor-0.1.0a2.tar.gz, SHA256SUMS. Успех определяется workflow,
публичным состоянием и проверкой скачанных files/checksum, не этим документом.
Конкретные финальные commit/CI/checksum указываются в русских GitHub release notes.

НЕ ВЫПОЛНЕНО: реальные Ubuntu/Debian/RHEL/aarch64 VM, Windows/WSL2, host kernel/LSM,
systemd/containers, audit delivery, backup restore, advisory/baseline authenticity,
Полные ограничения — [docs/release-notes](docs/release-notes.md), приёмка —
[VERIFICATION](VERIFICATION.md), установка/удаление — [INSTALL](INSTALL.md).
