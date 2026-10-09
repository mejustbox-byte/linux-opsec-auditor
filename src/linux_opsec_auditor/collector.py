"""Small fixed-path collector. No subprocess, sudo, network or configuration writes."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat
from .schema import MAX_BYTES, InputError


class SafeRoot:
    """Open every directory component with O_NOFOLLOW; caller controls only the root."""
    def __init__(self, root):
        absolute = os.path.abspath(root)
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in absolute.split("/")[1:]:
                if not part:
                    continue
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
        except BaseException:
            os.close(fd)
            raise
        self.fd = fd

    def close(self):
        os.close(self.fd)

    def open(self, relative, flags=os.O_RDONLY):
        parts = relative.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise InputError("path: unsafe path component")
        parent = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = child
            return os.open(parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally:
            os.close(parent)

    def read(self, relative, limit=MAX_BYTES):
        fd = self.open(relative, os.O_PATH)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise InputError("input: requires a regular file")
            read_fd = os.open(f"/proc/self/fd/{fd}", os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(read_fd, "rb") as stream:
                data = stream.read(limit + 1)
            if len(data) > limit:
                raise InputError("input: size limit exceeded")
            return data
        finally:
            os.close(fd)

    def metadata(self, relative):
        fd = self.open(relative, os.O_PATH)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise InputError("metadata: requires a regular file")
            return info.st_uid, stat.S_IMODE(info.st_mode)
        finally:
            os.close(fd)


def read_input(path):
    path = Path(os.path.abspath(path))
    root = SafeRoot("/")
    try:
        return root.read(str(path)[1:])
    finally:
        root.close()


def parse_os_release(text):
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r'(ID|VERSION_ID)=(?:"([a-z0-9.]+)"|([a-z0-9.]+))', line)
        if match:
            values[match[1]] = match[2] or match[3]
    family = values.get("ID", "other")
    if family not in {"ubuntu", "debian", "rhel"}:
        family = "other"
    version = values.get("VERSION_ID", "0")
    if not re.fullmatch(r"[0-9]{1,2}(\.[0-9]{1,2})?", version):
        version = "0"
    # RHEL minor release belongs to a major policy candidate, not a supported claim.
    if family == "rhel":
        version = version.split(".")[0]
    return family, version


def parse_ssh(text):
    values = {"effective": False}
    # Includes may define the first effective value; do not guess their expansion.
    for line in text.splitlines():
        words = line.partition("#")[0].split()
        if words and words[0].lower() == "include":
            return values
    seen = set()
    in_match = False
    for line in text.splitlines():
        line = line.partition("#")[0].strip()
        words = line.split()
        if not words:
            continue
        key = words[0].lower()
        if key == "match":
            in_match = True
        if in_match or len(words) != 2:
            continue
        mapping = {"permitrootlogin": "permit_root", "passwordauthentication": "password_auth"}
        if key in mapping and key not in seen:
            seen.add(key)
            # Only exact disabling/enabling tokens are facts; unusual syntax stays unknown.
            if words[1].lower() in {"yes", "no"}:
                values[mapping[key]] = words[1].lower() == "yes"
    return values


def collect(root="/"):
    safe = SafeRoot(root)
    try:
        platform = {"family": "other", "version": "0", "architecture": "other"}
        machine = os.uname().machine
        platform["architecture"] = machine if machine in {"x86_64", "aarch64"} else "other"
        for path in ("etc/os-release", "usr/lib/os-release"):
            try:
                platform["family"], platform["version"] = parse_os_release(safe.read(path, 16384).decode("utf-8"))
                break
            except (OSError, UnicodeError, InputError):
                continue
        observations = {}
        try:
            values = parse_ssh(safe.read("etc/ssh/sshd_config", 65536).decode("utf-8"))
            observations["ssh"] = {"state": "observed", "source": "static", "values": values}
        except (OSError, UnicodeError, InputError):
            observations["ssh"] = {"state": "unavailable", "source": "static", "values": {}}
        # Fixed scope, metadata only. No reading sudo/PAM contents or journal records.
        owners, writable = [], []
        for path in ("etc/passwd", "etc/group", "etc/ssh/sshd_config", "etc/sudoers"):
            try:
                uid, mode = safe.metadata(path)
                owners.append(uid == 0)
                writable.append(bool(mode & 0o022))
            except (OSError, InputError):
                continue
        values = {"complete": False}  # ACLs and parent directories are not collected.
        if owners:
            values.update(root_owned=all(owners), group_world_writable=any(writable))
        observations["files"] = {"state": "observed", "source": "static", "values": values}
        # Namespace/host identity is deliberately unproven: never grant an LSM pass.
        observations["lsm"] = {"state": "observed", "source": "runtime", "values": {"host_context": False}}
        try:
            state = safe.read("sys/fs/selinux/enforce", 16).strip()
            if state in {b"0", b"1"}:
                observations["lsm"]["values"]["selinux"] = "enforcing" if state == b"1" else "permissive"
        except (OSError, InputError):
            pass
        return {"schema_version": 1, "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "platform": platform, "observations": observations}
    finally:
        safe.close()
