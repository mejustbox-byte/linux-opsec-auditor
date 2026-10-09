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


GROUP_DESCRIPTIONS = {
    "ssh": "SSH: явные root/password флаги и подтверждение effective config.",
    "sudo": "Нормализованные широкие grants и полнота проверки sudo.",
    "pam": "Утверждение об обходе PAM и полноте service include stack.",
    "systemd": "Выбранные защитные свойства конкретной службы.",
    "files": "Агрегированные mode/owner и полнота файлового объёма.",
    "kernel": "Утверждения о patched booted kernel, reboot и актуальности advisories.",
    "lsm": "SELinux/AppArmor enforcement и установленный host context.",
    "containers": "Утверждения privileged/host mounts и полнота объёма.",
    "logs": "Audit, persistent journal и независимо проверенная доставка.",
    "backups": "Возраст backup и внешнее свидетельство восстановления.",
    "drift": "Утверждённый baseline и digest нормализованной конфигурации.",
    "patches": "Vendor support, свежесть advisories и число security updates.",
}

def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required),
            "additionalProperties": False}


INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/mejustbox-byte/linux-opsec-auditor/input-v1",
    "title": "Нормализованный снимок Linux OPSEC: версия 1",
    "description": "Закрытая схема утверждений. Не принимает сырую инфраструктуру или секреты; source не является аттестацией.",
    **obj({
        "schema_version": {"const": 1, "description": "Версия контракта входных данных."},
        "collected_at": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"},
        "platform": obj({"family": {"enum": ["ubuntu", "debian", "rhel", "other"]},
                         "version": {"type": "string", "pattern": r"^[0-9]{1,2}(\.[0-9]{1,2})?$"},
                         "architecture": {"enum": ["x86_64", "aarch64", "other"]}},
                        ["family", "version", "architecture"]),
        "observations": obj({name: obj({
            "state": {"enum": ["observed", "unavailable", "not_run"]},
            "source": {"enum": ["synthetic", "operator", "static", "runtime"]},
            "values": obj(fields),
        }, ["state", "source", "values"]) | {"description": GROUP_DESCRIPTIONS[name]} for name, fields in GROUPS.items()}),
    }, ["schema_version", "collected_at", "platform", "observations"]),
}


FIELD_DESCRIPTIONS = {
    "permit_root": "Явно разрешён SSH-вход root.", "password_auth": "Разрешена SSH-аутентификация паролем.",
    "effective": "Поставщик установил эффективную SSH-конфигурацию нужного контекста.",
    "unrestricted": "Выявлено широкое неограниченное разрешение sudo.",
    "complete": "Поставщик заявляет полноту ограниченной проверки; схема её не доказывает.",
    "bypass": "Выявлен обход PAM-аутентификации.", "no_new_privileges": "Заявлено NoNewPrivileges службы.",
    "protect_system": "Заявлена защита системных путей службы.", "private_tmp": "Заявлен отдельный tmp службы.",
    "root_owned": "Все проверенные критические файлы принадлежат root.",
    "group_world_writable": "Хотя бы один проверенный файл имеет group/world write mode.",
    "reboot_required": "Заявлена необходимость перезагрузки для исправлений ядра.",
    "advisory_current": "Заявлена актуальность внешних advisories ядра.", "patched": "Заявлено исправленное запущенное ядро.",
    "selinux": "Нормализованное состояние SELinux; наличие конфигурации не равно runtime enforcement.",
    "apparmor_enforcing": "Заявлен enforcing AppArmor.", "host_context": "Поставщик установил контекст хоста, не контейнера.",
    "privileged": "Заявлен privileged контейнер.", "host_mounts": "Заявлены host mounts контейнера.",
    "audit_active": "Заявлен активный audit.", "persistent_journal": "Заявлено постоянное хранение journal.",
    "delivery_verified": "Поставщик независимо проверил доставку журналов.",
    "age_hours": "Возраст backup в целых часах; предел политики 24 ч.",
    "restore_verified": "Внешнее свидетельство restore; сам аудитор восстановление не выполняет.",
    "baseline_approved": "Baseline утверждён извне.", "baseline_sha256": "SHA256 утверждённого нормализованного baseline.",
    "current_sha256": "SHA256 текущей нормализованной конфигурации; в отчёте остаётся только равенство.",
    "support_active": "Заявлена действующая vendor support/entitlement.", "feed_current": "Заявлена свежесть внешнего feed.",
    "security_updates_pending": "Заявленное число ожидающих security updates.",
}
for group, observation_schema in INPUT_SCHEMA["properties"]["observations"]["properties"].items():
    properties = observation_schema["properties"]
    properties["source"]["description"] = "Самодекларированный источник; не подпись и не аттестация."
    properties["state"]["description"] = "Доступность/выполнение наблюдения; unavailable и not_run требуют пустых values."
    for key, field in list(properties["values"]["properties"].items()):
        properties["values"]["properties"][key] = {**field, "description": FIELD_DESCRIPTIONS[key]}
INPUT_SCHEMA["properties"]["collected_at"]["description"] = "Момент получения данных UTC до секунды; допустимая свежесть 24 ч."
INPUT_SCHEMA["properties"]["platform"]["description"] = "Профиль-кандидат, не заявление проверенной поддержки ОС."


class InputError(ValueError):
    """Safe error messages contain schema paths, never input values."""


def validate(value, schema=INPUT_SCHEMA, path="input"):
    if "const" in schema and (type(value) is not int or value != schema["const"]):
        raise InputError(f"{path}: неподдерживаемая версия схемы")
    if "enum" in schema and (type(value) is not str or value not in schema["enum"]):
        raise InputError(f"{path}: неподдерживаемое значение enum")
    kind = schema.get("type")
    types = {"object": dict, "boolean": bool, "integer": int, "string": str}
    if kind and type(value) is not types[kind]:
        raise InputError(f"{path}: ожидается {kind}")
    if kind == "object":
        fields = schema["properties"]
        if set(value) - set(fields):
            raise InputError(f"{path}: лишнее поле")
        if set(schema["required"]) - set(value):
            raise InputError(f"{path}: отсутствует обязательное поле")
        for key, item in value.items():
            validate(item, fields[key], f"{path}.{key}")
    if kind == "integer" and not schema["minimum"] <= value <= schema["maximum"]:
        raise InputError(f"{path}: integer вне диапазона")
    if kind == "string" and not re.fullmatch(schema["pattern"], value, flags=re.ASCII):
        raise InputError(f"{path}: неверный формат строки")


def timestamp(text):
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise InputError("input.collected_at: неверная дата UTC") from None


def _pairs(items):
    result = {}
    for key, val in items:
        if key in result:
            raise InputError("input: повторный ключ JSON")
        result[key] = val
    return result


def loads(raw):
    if len(raw) > MAX_BYTES:
        raise InputError("input: превышен лимит 1 MiB")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(InputError("input: неfinite число")))
    except (json.JSONDecodeError, UnicodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("input: некорректный JSON") from None
    validate(value)
    timestamp(value["collected_at"])
    for observation in value["observations"].values():
        if observation["state"] != "observed" and observation["values"]:
            raise InputError("input.observations: для unavailable/not_run values должен быть пуст")
    return value
