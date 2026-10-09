"""CLI with private create-only output and safe input error messages."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
from . import __version__
from .collector import collect, read_input, SafeRoot
from .rules import audit, render_text, RULES
from .schema import loads, INPUT_SCHEMA, InputError


def write_private(path, text):
    path = Path(os.path.abspath(path))
    parent = SafeRoot("/")
    fd = None
    created = False
    # Retain an open directory descriptor throughout the write and any cleanup.
    directory = None
    try:
        if str(path.parent) == "/":
            directory = os.dup(parent.fd)
        else:
            directory = parent.open(str(path.parent)[1:], os.O_RDONLY | os.O_DIRECTORY)
        info = os.fstat(directory)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise InputError("output: каталог должен принадлежать вам и иметь режим 0700")
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        created = True
        with os.fdopen(fd, "w", encoding="utf-8", closefd=False) as stream:
            stream.write(text)
            stream.flush()
            os.fsync(fd)
    except BaseException:
        if created:
            os.unlink(path.name, dir_fd=directory)
        raise
    finally:
        if fd is not None:
            os.close(fd)
        if directory is not None:
            os.close(directory)
        parent.close()


def parser():
    p = argparse.ArgumentParser(description="Аудит Linux только на чтение; платформы-кандидаты не проверены.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("audit", help="проверить нормализованный снимок без операций с хостом или сетью")
    a.add_argument("--input", required=True, help="регулярный JSON-файл до 1 MiB; без symlink")
    a.add_argument("--format", choices=["json", "text"], default="text", help="формат отчёта")
    a.add_argument("--output", help="новый файл в существующем приватном каталоге 0700; иначе stdout")
    a.add_argument("--checks", nargs="+", choices=list(RULES), help="выбранные группы; остальные not_run")
    a.add_argument("--fail-on", choices=["none", "fail", "incomplete"], default="fail", help="порог ненулевого exit code")
    c = sub.add_parser("collect", help="ограниченное чтение фиксированных локальных путей; без sudo/команд/сети")
    c.add_argument("--output", required=True, help="новый снимок в приватном каталоге 0700")
    c.add_argument("--root", default="/", help="root файловой системы; тестовый root не доказывает состояние реального хоста")
    sub.add_parser("schema", help="показать версионированную JSON Schema входа")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps(INPUT_SCHEMA, indent=2, sort_keys=True, ensure_ascii=False))
            return 0
        if args.command == "collect":
            snapshot = collect(args.root)
            # Validate our own collector output before writing.
            loads(json.dumps(snapshot).encode())
            write_private(args.output, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
            return 0
        snapshot = loads(read_input(args.input))
        report = audit(snapshot, selected=args.checks)
        text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n" if args.format == "json" else render_text(report)
        if args.output:
            write_private(args.output, text)
        else:
            sys.stdout.write(text)
        if args.fail_on == "none":
            return 0
        if report["summary"]["fail"]:
            return 1
        if args.fail_on == "incomplete" and not report["complete"]:
            return 3
        return 0
    except (OSError, InputError, UnicodeError) as exc:
        # OSError text includes paths and sometimes payloads; suppress it.
        message = str(exc) if isinstance(exc, InputError) else "ошибка файловой операции (проверьте доступ, регулярный файл и приватный каталог)"
        print(f"ошибка: {message}", file=sys.stderr)
        return 2
