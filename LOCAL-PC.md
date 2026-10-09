# Локальная лаборатория Linux

Это отдельный от cloud CI план реальных проверок. Нужны имеющиеся одноразовые VM
или физический лабораторный хост, recovery/snapshot и согласованные права. Платные
ресурсы и реальные production credentials не создаются. Windows/Hyper-V/WSL могут
быть средой оператора, но их подготовка и Linux runtime там **НЕ ПРОВЕРЕНЫ** здесь.

| Кандидат | Требуемое реальное evidence |
|---|---|
| Ubuntu 22.04/24.04 LTS | Exact minor, GA/HWE kernel, AppArmor enforcing/disabled, systemd |
| Debian 12/13 | Lifecycle/security/LTS, фактический AppArmor, init/kernel |
| RHEL 9/10 | Exact minor/kernel, vendor backports/entitlement, SELinux enforcing/permissive |

x86_64 — начальный target; aarch64 и другие версии не подтверждены. RHEL clones не
получают статус RHEL. Образ контейнера проверяет userspace, не собственный kernel,
LSM и host namespace. Никакой matrix row пока не является подтверждённой поддержкой.

До аудита оператор отдельно provision'ит Python >=3.12 и тестовые состояния. Аудитор
не устанавливает пакеты, не меняет sshd/PAM/sudo/systemd/sysctl/LSM/audit rules,
не создаёт опасные состояния и не выполняет rollback. Приватно фиксируются image
hash, commit, OS/minor/kernel, architecture, LSM, namespace и UID.

Минимальный эксперимент: проверить wheel/hash, непривилегированный collect и
--fail-on incomplete, до/после сравнить охраняемые bytes/owner/mode/ACL, учесть
atime/журналы. Denied/missing/symlink не должны давать pass. Независимые effective
SSH, kernel advisory, LSM, service/container/logging/restore свидетельства нужны
отдельно: локальный collector их не реализует. Public raw reports запрещены.

Полный воспроизводимый протокол и 11 шагов — [docs/laboratory](docs/laboratory.md).
Выполненные проверки и список НЕ ВЫПОЛНЕНО — [VERIFICATION](VERIFICATION.md).
Стабильный release требует этого уровня evidence, не лишь synthetic/CI success.
