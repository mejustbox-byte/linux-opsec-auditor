# Rule and evidence matrix (policy v1)

All rules require fresh input and a candidate x86_64 platform. Evidence fields are
normalized claims, not instructions to run commands. Unit/integration coverage is
synthetic only. All rows include positive, negative, missing and not_run fixtures;
malformed typed observations reject the entire document. Rule version is 1.
Severity is the importance of the selected policy gap, independent of confidence.

| ID / severity | Observation and prerequisite for pass | Local collection | Limit / remediation focus |
|---|---|---|---|
| SSH-01 high | permit_root=false, password_auth=false; effective=true | static global explicit yes/no; Include means unknown, Match ignored; effective always false | Review effective Include/Match authentication; no sshd execution |
| SUDO-01 high | unrestricted=false; complete=true | absent | Review command-level grants/NOPASSWD; no parser or sudo execution |
| PAM-01 high | bypass=false; complete=true | absent | Review service include stack and recovery; no auth probe |
| UNIT-01 medium | no_new_privileges/protect_system/private_tmp=true | absent | Selected service properties only; compatibility before changes |
| FILE-01 high | root_owned=true, group_world_writable=false; complete=true | aggregate metadata for four paths, complete always false | ACLs/parents/mounts absent; detected writable mode still fails |
| KERN-01 high | reboot_required=false, patched=true; advisory_current=true | absent | Vendor backports and running kernel must be externally established |
| LSM-01 high | host_context=true and SELinux enforcing OR AppArmor enforcing | optional SELinux enforce indicator, host_context=false | Namespace unknown prohibits pass; no policy-coverage claim |
| CONT-01 high | privileged=false, host_mounts=false; complete=true | absent | Full sockets/caps/userns review remains external |
| AUD-01 medium | audit_active/persistent_journal/delivery_verified=true | absent | No journal content collected; delivery independent |
| BACK-01 high | age_hours<=24, restore_verified=true | absent | Operator assertion only; no restore executed |
| DRIFT-01 info | baseline_approved=true, two equal SHA256 digests | absent | Difference is not vulnerability; normalization/approval external |
| PATCH-01 high | support_active=true, security_updates_pending=0; feed_current=true | absent | Entitlement/backport/advisory authentication external |

Known unsafe values fail even if a completeness prerequisite is missing. Stale
snapshots are unknown globally, including unsafe flags. Static positive evidence
for SSH/LSM/systemd/logs/kernel/containers is unknown. `source=operator` or `synthetic`
gets asserted confidence; `static`/`runtime` gets limited confidence, not attestation.
The schema cannot prove that the observation producer is honest.

Fixed local paths: /etc/os-release, fallback /usr/lib/os-release (16 KiB),
/etc/ssh/sshd_config (64 KiB); metadata for /etc/passwd, /etc/group,
/etc/ssh/sshd_config and /etc/sudoers; optional /sys/fs/selinux/enforce (16 bytes).
Missing/denied/symlink inputs are omitted/unavailable without exposing their contents.
No arbitrary root path expansion, recursion, Include expansion or ACL read occurs.
Local collection groups absent from the snapshot become unknown, never not_run/pass.
