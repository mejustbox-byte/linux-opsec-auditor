# Матрица правил и evidence: policy v1

Нужны свежие данные и профиль-кандидат x86_64. Поля — нормализованные утверждения,
не инструкции исполнения. Тесты синтетические; для каждой группы есть положительные,
отрицательные, отсутствующие и not_run данные. Неверные типы отвергают весь документ.
rule_version=1. Severity отражает важность политики отдельно от confidence.

| ID / severity | Данные и предпосылки pass | Локальный сбор | Ограничения и рекомендации |
|---|---|---|---|
| SSH-01 high | permit_root=false, password_auth=false; effective=true | Явные global yes/no; Include неизвестен; Match игнорируется; effective всегда false | Проверить effective Include/Match; sshd не запускается |
| SUDO-01 high | unrestricted=false; complete=true | Нет | Ревью grants/NOPASSWD; парсер и sudo отсутствуют |
| PAM-01 high | bypass=false; complete=true | Нет | Проверить service include stack и recovery; auth probe нет |
| UNIT-01 medium | no_new_privileges/protect_system/private_tmp=true | Нет | Лишь выбранные свойства; совместимость до изменения |
| FILE-01 high | root_owned=true, group_world_writable=false; complete=true | Метаданные четырёх путей; complete всегда false | ACL/parents/mounts отсутствуют; опасный mode даёт fail |
| KERN-01 high | reboot_required=false, patched=true; advisory_current=true | Нет | Vendor backports и booted kernel подтверждаются извне |
| LSM-01 high | host_context=true и SELinux enforcing либо AppArmor enforcing | Ограниченный SELinux-индикатор; host_context=false | Неизвестный namespace запрещает pass; coverage не доказано |
| CONT-01 high | privileged=false, host_mounts=false; complete=true | Нет | Полное ревью sockets/caps/userns внешнее |
| AUD-01 medium | audit_active/persistent_journal/delivery_verified=true | Нет | Журналы не выгружаются; доставка проверяется отдельно |
| BACK-01 high | age_hours<=24, restore_verified=true | Нет | Утверждение оператора, не выполненное восстановление |
| DRIFT-01 info | baseline_approved=true, одинаковые SHA256 | Нет | Дрейф не равен уязвимости; normalization/approval внешние |
| PATCH-01 high | support_active=true, security_updates_pending=0; feed_current=true | Нет | Entitlement/backports/advisory authenticity внешние |

Известные опасные факты дают fail даже без полноты; устаревший снимок даёт unknown
целиком. Безопасные static-факты SSH/LSM/systemd/logs/kernel/containers дают unknown.
operator/synthetic confidence — asserted; static/runtime — limited, не аттестация.
Схема не доказывает честность поставщика.

Фиксированные источники: /etc/os-release либо /usr/lib/os-release (16 KiB),
/etc/ssh/sshd_config (64 KiB); метаданные /etc/passwd, /etc/group,
/etc/ssh/sshd_config, /etc/sudoers; /sys/fs/selinux/enforce (16 байт), если доступен.
Отсутствующие, запрещённые и symlink-источники не раскрывают содержимое. Рекурсии,
Include expansion и чтения ACL нет. Несобранные группы становятся unknown, не pass/not_run.
