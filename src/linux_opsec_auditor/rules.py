"""Pure evaluation of bounded, normalized evidence, never host execution."""
from datetime import datetime, timezone
from . import __version__
from .schema import PROFILES, timestamp, loads
import json

# group: id, title, severity, expected field values, prerequisite, remediation, limitation
RULES = {
    "ssh": ("SSH-01", "SSH root/password authentication", "high",
            {"permit_root": False, "password_auth": False}, "effective",
            "Review effective SSH policy including Match/Include before disabling root and password login.",
            "Static fragments cannot prove effective Match/Include policy or authentication safety."),
    "sudo": ("SUDO-01", "Unrestricted sudo grants", "high", {"unrestricted": False}, "complete",
             "Review broad grants, NOPASSWD and writable command paths with the administrator.",
             "A normalized grant summary does not prove command-level privilege safety."),
    "pam": ("PAM-01", "PAM authentication bypass", "high", {"bypass": False}, "complete",
            "Review the full service-specific PAM include stack; test recovery access separately.",
            "No PAM stack parser or login probe is implemented."),
    "systemd": ("UNIT-01", "Selected service hardening", "medium",
                {"no_new_privileges": True, "protect_system": True, "private_tmp": True}, None,
                "Assess service-specific sandboxing and compatibility before changes.",
                "Selected properties do not establish complete service isolation."),
    "files": ("FILE-01", "Critical file ownership and write permissions", "high",
              {"root_owned": True, "group_world_writable": False}, "complete",
              "Review owners, modes, ACLs and mount policy for critical configuration.",
              "Mode bits exclude ACLs, mount effects, directory ownership and paths outside scope."),
    "kernel": ("KERN-01", "Running kernel patch evidence", "high",
               {"reboot_required": False, "patched": True}, "advisory_current",
               "Verify vendor backports, running kernel and maintenance/reboot policy.",
               "No version comparison, advisory download or kernel attestation is performed."),
    "lsm": ("LSM-01", "Host LSM enforcement", "high", {}, "host_context",
            "Review host SELinux/AppArmor runtime enforcement with distribution-specific policy.",
            "Container observations cannot establish host LSM enforcement or policy coverage."),
    "containers": ("CONT-01", "Container boundary exposure", "high",
                   {"privileged": False, "host_mounts": False}, "complete",
                   "Review privileged mode, host mounts, sockets, capabilities and user namespaces.",
                   "Two exposure flags do not establish a complete container boundary."),
    "logs": ("AUD-01", "Audit and journal evidence", "medium",
             {"audit_active": True, "persistent_journal": True, "delivery_verified": True}, None,
             "Review audit coverage, persistent journal retention and independently verify delivery.",
             "Configuration alone does not prove retained logs or remote delivery."),
    "backups": ("BACK-01", "Backup freshness and restore evidence", "high",
                {"restore_verified": True}, None,
                "Review backup freshness and independent isolated restore evidence.",
                "Restore assertions are not an executed restoration test; fixed freshness budget is 24 h."),
    "drift": ("DRIFT-01", "Approved configuration baseline", "info", {}, "baseline_approved",
              "Review differences against the approved baseline; drift is not automatically a vulnerability.",
              "Digest comparison depends on externally approved normalization and baseline integrity."),
    "patches": ("PATCH-01", "Security update and support evidence", "high",
                {"support_active": True, "security_updates_pending": 0}, "feed_current",
                "Review vendor support and current security advisories, including extended support entitlements.",
                "No live package manager query or vendor entitlement validation is performed."),
}


def decide(group, values):
    _, _, _, expected, gate, _, _ = RULES[group]
    # Known unsafe evidence remains a failure even when completeness is absent.
    if any(key in values and values[key] != target for key, target in expected.items()):
        return "fail", "Observed value does not meet the selected policy."
    if group == "backups":
        if values.get("age_hours", 0) > 24:
            return "fail", "Backup freshness exceeds the 24-hour policy."
        if "age_hours" not in values:
            return "unknown", "Backup freshness was not observed."
    if group == "lsm":
        if values.get("host_context") is not True:
            return "unknown", "Host namespace context was not established."
        if values.get("selinux") == "enforcing" or values.get("apparmor_enforcing") is True:
            return "pass", "An enforcing LSM was reported for host context."
        if values.get("selinux") in {"disabled", "permissive"} and values.get("apparmor_enforcing") is False:
            return "fail", "Neither supported LSM was reported enforcing."
        return "unknown", "LSM enforcement evidence is incomplete."
    if group == "drift":
        if values.get(gate) is not True:
            return "unknown", "Baseline approval was not established."
        if not {"baseline_sha256", "current_sha256"} <= values.keys():
            return "unknown", "Baseline/current digest is missing."
        if values["baseline_sha256"] != values["current_sha256"]:
            return "fail", "Configuration digest differs from the approved baseline."
        return "pass", "Configuration digests agree."
    if gate and values.get(gate) is not True:
        return "unknown", "Effective, complete or current evidence is not established."
    if not expected.keys() <= values.keys():
        return "unknown", "Required evidence is missing."
    return "pass", "Observed values meet this limited policy."


def audit(snapshot, selected=None, now=None, max_age_hours=24):
    # Validate direct Python API calls as rigorously as the CLI.
    snapshot = loads(json.dumps(snapshot).encode())
    now = now or datetime.now(timezone.utc)
    selected = set(RULES) if selected is None else set(selected)
    if selected - RULES.keys():
        raise ValueError("unsupported check selection")
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
            status, reason = "not_run", "Check not selected or explicitly not collected."
            evidence = {}
        elif not supported:
            status, reason = "unknown", "Platform/version/architecture is outside the candidate policy profiles."
        elif age < -300 or age > max_age_hours * 3600:
            status, reason = "unknown", "Evidence is stale or future-dated."
        elif not observation or observation["state"] != "observed":
            status, reason = "unknown", "Evidence was unavailable or omitted."
        else:
            status, reason = decide(group, observation["values"])
            if status == "pass" and source == "static" and group in {"ssh", "lsm", "systemd", "logs", "kernel", "containers"}:
                status, reason = "unknown", "Static evidence cannot establish this runtime property."
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
    lines = [f"Linux OPSEC Auditor {report['tool_version']} — candidate platforms UNVERIFIED",
             "Results apply only to the supplied evidence; not a host safety certification.",
             "Summary: " + ", ".join(f"{k}={v}" for k, v in report["summary"].items())]
    for finding in report["findings"]:
        lines.extend([f"[{finding['status'].upper()}] {finding['check_id']} ({finding['severity']}): {finding['title']}",
                      f"  Evidence ({finding['source']}): {json.dumps(finding['evidence'], sort_keys=True)}",
                      f"  {finding['reason']}", f"  Review: {finding['remediation']}",
                      f"  Limit: {finding['limitation']}"])
    return "\n".join(lines) + "\n"
