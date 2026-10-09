"""Pure evaluation of bounded, normalized evidence, never host execution."""
from datetime import datetime, timezone
from . import __version__
from .schema import PROFILES, timestamp, loads
import json

# group: id, title, severity, expected field values, prerequisite, remediation, limitation
RULES = {
    "ssh": ("SSH-01", "SSH: вход root и аутентификация паролем", "high",
            {"permit_root": False, "password_auth": False}, "effective",
            "Проверьте эффективную SSH-политику и Match/Include до отключения root/password входа.",
            "Статический фрагмент не доказывает эффективную Match/Include-политику или безопасность входа."),
    "sudo": ("SUDO-01", "Неограниченные разрешения sudo", "high", {"unrestricted": False}, "complete",
             "Совместно с администратором проверьте широкие grants, NOPASSWD и доступные на запись пути команд.",
             "Нормализованная сводка не доказывает безопасность привилегий отдельных команд."),
    "pam": ("PAM-01", "Обход аутентификации PAM", "high", {"bypass": False}, "complete",
            "Проверьте полный PAM include stack конкретной службы; recovery-доступ проверяйте отдельно.",
            "Парсер PAM stack и проба входа не реализованы."),
    "systemd": ("UNIT-01", "Выбранные защитные свойства службы", "medium",
                {"no_new_privileges": True, "protect_system": True, "private_tmp": True}, None,
                "До изменений оцените совместимость и изоляцию конкретной службы.",
                "Выбранные свойства не доказывают полную изоляцию службы."),
    "files": ("FILE-01", "Владельцы и права записи критических файлов", "high",
              {"root_owned": True, "group_world_writable": False}, "complete",
              "Проверьте владельцев, mode, ACL и mount-политику критической конфигурации.",
              "Mode bits не учитывают ACL, mount, владельцев каталогов и пути вне объёма проверки."),
    "kernel": ("KERN-01", "Данные об исправлениях запущенного ядра", "high",
               {"reboot_required": False, "patched": True}, "advisory_current",
               "Проверьте vendor backports, запущенное ядро и политику обслуживания/перезагрузки.",
               "Сравнение версий, загрузка advisories и аттестация ядра не выполняются."),
    "lsm": ("LSM-01", "Применение LSM на хосте", "high", {}, "host_context",
            "Проверьте runtime SELinux/AppArmor хоста с учётом политики дистрибутива.",
            "Наблюдение в контейнере не подтверждает host LSM enforcement или полноту политики."),
    "containers": ("CONT-01", "Опасные контейнерные границы", "high",
                   {"privileged": False, "host_mounts": False}, "complete",
                   "Проверьте privileged mode, host mounts, sockets, capabilities и user namespaces.",
                   "Два флага не доказывают полноценную контейнерную изоляцию."),
    "logs": ("AUD-01", "Данные audit и journal", "medium",
             {"audit_active": True, "persistent_journal": True, "delivery_verified": True}, None,
             "Проверьте audit coverage, retention persistent journal и независимо подтвердите доставку.",
             "Конфигурация не доказывает сохранность журналов или удалённую доставку."),
    "backups": ("BACK-01", "Свежесть резервной копии и данные восстановления", "high",
                {"restore_verified": True}, None,
                "Проверьте свежесть backup и независимые данные изолированного восстановления.",
                "Утверждение не является выполненным restore test; предел свежести — 24 ч."),
    "drift": ("DRIFT-01", "Утверждённый baseline конфигурации", "info", {}, "baseline_approved",
              "Проверьте различия с утверждённым baseline; дрейф не равен уязвимости.",
              "Сравнение digest зависит от внешнего утверждения normalization и целостности baseline."),
    "patches": ("PATCH-01", "Данные security updates и поддержки", "high",
                {"support_active": True, "security_updates_pending": 0}, "feed_current",
                "Проверьте vendor support и актуальные security advisories, включая entitlement расширенной поддержки.",
                "Live-запрос package manager и проверка vendor entitlement не выполняются."),
}


def decide(group, values):
    _, _, _, expected, gate, _, _ = RULES[group]
    # Known unsafe evidence remains a failure even when completeness is absent.
    if any(key in values and values[key] != target for key, target in expected.items()):
        return "fail", "Наблюдаемое значение не соответствует выбранной политике."
    if group == "backups":
        if values.get("age_hours", 0) > 24:
            return "fail", "Свежесть backup превышает 24-часовой предел."
        if "age_hours" not in values:
            return "unknown", "Свежесть backup не установлена."
    if group == "lsm":
        if values.get("host_context") is not True:
            return "unknown", "Host namespace context не установлен."
        if values.get("selinux") == "enforcing" or values.get("apparmor_enforcing") is True:
            return "pass", "Для host context заявлен enforcing LSM."
        if values.get("selinux") in {"disabled", "permissive"} and values.get("apparmor_enforcing") is False:
            return "fail", "Ни один из рассматриваемых LSM не заявлен enforcing."
        return "unknown", "Данные LSM enforcement неполны."
    if group == "drift":
        if values.get(gate) is not True:
            return "unknown", "Утверждение baseline не подтверждено."
        if not {"baseline_sha256", "current_sha256"} <= values.keys():
            return "unknown", "Отсутствует baseline/current digest."
        if values["baseline_sha256"] != values["current_sha256"]:
            return "fail", "Digest конфигурации отличается от утверждённого baseline."
        return "pass", "Digest конфигурации совпадают."
    if gate and values.get(gate) is not True:
        return "unknown", "Эффективность, полнота или актуальность данных не установлена."
    if not expected.keys() <= values.keys():
        return "unknown", "Обязательные данные отсутствуют."
    return "pass", "Наблюдаемые значения соответствуют этой ограниченной политике."


def audit(snapshot, selected=None, now=None, max_age_hours=24):
    # Validate direct Python API calls as rigorously as the CLI.
    snapshot = loads(json.dumps(snapshot).encode())
    now = now or datetime.now(timezone.utc)
    selected = set(RULES) if selected is None else set(selected)
    if selected - RULES.keys():
        raise ValueError("неподдерживаемый выбор проверки")
    age = (now - timestamp(snapshot["collected_at"])).total_seconds()
    platform = snapshot["platform"]
    supported = (platform["version"] in PROFILES.get(platform["family"], set())
                 and platform["architecture"] == "x86_64")
    findings = []
    for group, rule in RULES.items():
        check_id, title, severity, _, _, remediation, limitation = rule
        observation = snapshot["observations"].get(group)
        source = observation["source"] if observation else "none"
        evidence = observation["values"].copy() if observation and observation["state"] == "observed" else {}
        # Baseline digests are private evidence: report equality, not actual digests.
        if group == "drift":
            digest_a = evidence.pop("baseline_sha256", None)
            digest_b = evidence.pop("current_sha256", None)
            if digest_a is not None and digest_b is not None:
                evidence["digests_equal"] = digest_a == digest_b
        if group not in selected or (observation and observation["state"] == "not_run"):
            status, reason = "not_run", "Проверка не выбрана либо явно не выполнялась."
            evidence = {}
        elif not supported:
            status, reason = "unknown", "Платформа/версия/архитектура вне профилей-кандидатов политики."
        elif age < -300 or age > max_age_hours * 3600:
            status, reason = "unknown", "Данные устарели или датированы будущим."
        elif not observation or observation["state"] != "observed":
            status, reason = "unknown", "Данные недоступны или пропущены."
        else:
            status, reason = decide(group, observation["values"])
            if status == "pass" and source == "static" and group in {"ssh", "lsm", "systemd", "logs", "kernel", "containers"}:
                status, reason = "unknown", "Статические данные не устанавливают это runtime-свойство."
        findings.append({"check_id": check_id, "rule_version": 1, "title": title,
                         "status": status, "severity": severity, "source": source,
                         "confidence": "asserted" if source in {"operator", "synthetic"} else "limited",
                         "evidence": evidence, "reason": reason,
                         "remediation": remediation, "limitation": limitation})
    summary = {s: sum(f["status"] == s for f in findings) for s in ("pass", "fail", "unknown", "not_run")}
    return {"schema_version": 1, "tool_version": __version__, "policy_version": 1,
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "collected_at": snapshot["collected_at"], "platform": platform,
            "platform_validation": "unverified_candidate", "summary": summary,
            "complete": summary["unknown"] == 0 and summary["not_run"] == 0,
            "findings": findings}


def render_text(report):
    lines = [f"Linux OPSEC Auditor {report['tool_version']} — платформы-кандидаты НЕ ПРОВЕРЕНЫ",
             "Результат относится только к предоставленным данным; это не сертификация безопасности хоста.",
             "Итоги: " + ", ".join(f"{k}={v}" for k, v in report["summary"].items())]
    for finding in report["findings"]:
        lines.extend([f"[{finding['status'].upper()}] {finding['check_id']} ({finding['severity']}): {finding['title']}",
                      f"  Данные ({finding['source']}): {json.dumps(finding['evidence'], sort_keys=True)}",
                      f"  {finding['reason']}", f"  Рекомендация: {finding['remediation']}",
                      f"  Ограничение: {finding['limitation']}"])
    return "\n".join(lines) + "\n"
