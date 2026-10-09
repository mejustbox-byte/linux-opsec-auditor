"""Single schema definition shared by JSON Schema export and strict validation."""
from datetime import datetime, timezone
import json
import re

MAX_BYTES = 1_048_576
PROFILES = {"ubuntu": {"22.04", "24.04"}, "debian": {"12", "13"}, "rhel": {"9", "10"}}
B = {"type": "boolean"}
N = {"type": "integer", "minimum": 0, "maximum": 1_000_000}
H = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
GROUPS = {
    "ssh": {"permit_root": B, "password_auth": B, "effective": B},
    "sudo": {"unrestricted": B, "complete": B},
    "pam": {"bypass": B, "complete": B},
    "systemd": {"no_new_privileges": B, "protect_system": B, "private_tmp": B},
    "files": {"root_owned": B, "group_world_writable": B, "complete": B},
    "kernel": {"reboot_required": B, "advisory_current": B, "patched": B},
    "lsm": {"selinux": {"enum": ["enforcing", "permissive", "disabled", "unavailable"]},
            "apparmor_enforcing": B, "host_context": B},
    "containers": {"privileged": B, "host_mounts": B, "complete": B},
    "logs": {"audit_active": B, "persistent_journal": B, "delivery_verified": B},
    "backups": {"age_hours": N, "restore_verified": B},
    "drift": {"baseline_approved": B, "baseline_sha256": H, "current_sha256": H},
    "patches": {"support_active": B, "feed_current": B, "security_updates_pending": N},
}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required),
            "additionalProperties": False}


INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/mejustbox-byte/linux-opsec-auditor/input-v1",
    **obj({
        "schema_version": {"const": 1},
        "collected_at": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"},
        "platform": obj({"family": {"enum": ["ubuntu", "debian", "rhel", "other"]},
                         "version": {"type": "string", "pattern": r"^[0-9]{1,2}(\.[0-9]{1,2})?$"},
                         "architecture": {"enum": ["x86_64", "aarch64", "other"]}},
                        ["family", "version", "architecture"]),
        "observations": obj({name: obj({
            "state": {"enum": ["observed", "unavailable", "not_run"]},
            "source": {"enum": ["synthetic", "operator", "static", "runtime"]},
            "values": obj(fields),
        }, ["state", "source", "values"]) for name, fields in GROUPS.items()}),
    }, ["schema_version", "collected_at", "platform", "observations"]),
}


class InputError(ValueError):
    """Safe error messages contain schema paths, never input values."""


def validate(value, schema=INPUT_SCHEMA, path="input"):
    if "const" in schema and (type(value) is not int or value != schema["const"]):
        raise InputError(f"{path}: unsupported schema version")
    if "enum" in schema and (type(value) is not str or value not in schema["enum"]):
        raise InputError(f"{path}: unsupported enum")
    kind = schema.get("type")
    types = {"object": dict, "boolean": bool, "integer": int, "string": str}
    if kind and type(value) is not types[kind]:
        raise InputError(f"{path}: expected {kind}")
    if kind == "object":
        fields = schema["properties"]
        if set(value) - set(fields):
            raise InputError(f"{path}: unexpected field")
        if set(schema["required"]) - set(value):
            raise InputError(f"{path}: required field missing")
        for key, item in value.items():
            validate(item, fields[key], f"{path}.{key}")
    if kind == "integer" and not schema["minimum"] <= value <= schema["maximum"]:
        raise InputError(f"{path}: integer out of range")
    if kind == "string" and not re.fullmatch(schema["pattern"], value, flags=re.ASCII):
        raise InputError(f"{path}: invalid string format")


def timestamp(text):
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise InputError("input.collected_at: invalid UTC date") from None


def _pairs(items):
    result = {}
    for key, val in items:
        if key in result:
            raise InputError("input: duplicate JSON key")
        result[key] = val
    return result


def loads(raw):
    if len(raw) > MAX_BYTES:
        raise InputError("input: exceeds 1 MiB limit")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(InputError("input: non-finite number")))
    except (json.JSONDecodeError, UnicodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("input: invalid JSON") from None
    validate(value)
    timestamp(value["collected_at"])
    for observation in value["observations"].values():
        if observation["state"] != "observed" and observation["values"]:
            raise InputError("input.observations: unavailable/not_run must have empty values")
    return value
