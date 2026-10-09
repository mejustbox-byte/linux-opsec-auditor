# linux-opsec-auditor

GITHUB-OPSEC read-only Linux posture auditing, **0.1.0a1 prerelease**. Evaluate a
strict normalized evidence snapshot and produce actionable JSON or readable
findings. A deliberately small local collector reads fixed SSH configuration and
critical-file metadata; it never runs commands, sudo, remediation or network calls.

**No Linux platform is validated yet.** Synthetic tests do not validate a real
kernel, SELinux/AppArmor, systemd, container boundary, logging or backup restoration.
A `pass` describes only a supplied observation and this limited policy, not host safety.

## Quick start (Python 3.12+ on Linux)

From the source checkout, no runtime dependencies or installation are needed:

```bash
PYTHONPATH=src python3 -m linux_opsec_auditor --version
PYTHONPATH=src python3 -m linux_opsec_auditor audit --input fixtures/unsafe.json --format text
```

Exit 1 is expected for a fresh unsafe fixture. All bundled fixtures use the fixed
synthetic date `2026-10-09T00:00:00Z`; after 24 hours they correctly become unknown.
For an always-fresh synthetic demo, update only its timestamp in a private copy:

```bash
opsec_demo_dir=$(mktemp -d)
python3 - "$opsec_demo_dir/synthetic.json" <<'PY'
from datetime import datetime, timezone
import json, sys
from pathlib import Path
snapshot = json.loads(Path('fixtures/healthy.json').read_text())
snapshot['collected_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
Path(sys.argv[1]).write_text(json.dumps(snapshot))
PY
PYTHONPATH=src python3 -m linux_opsec_auditor audit --input "$opsec_demo_dir/synthetic.json" --format json --fail-on incomplete
```

This demo is synthetic. It must not be presented as evidence from a server.
See [installation and CLI guide](docs/usage.md) for wheel installation, collection,
exit codes, safe report handling and exact release artifact commands.

## Scope

12 rule families: SSH, sudo, PAM, systemd, critical file permissions, kernel patch
assertions, LSM, containers, audit/journal, backups, drift and vendor support/patches.
The local collector implements **only static SSH fragments, four fixed file paths'
metadata, OS identity and a limited SELinux indicator**. Most rule families require
operator-normalized input and are unknown when absent. Remote SSH collection,
PAM/sudo parsing, vendor feeds and runtime service probes are deferred.

Findings include `pass/fail/unknown/not_run`, stable check ID, severity, limited or
asserted confidence, whitelisted evidence, rationale, remediation and limitations.
Unknown versions/architectures do not inherit a pass. No arbitrary strings or raw
configuration are accepted as evidence. JSON is limited to 1 MiB; unknown fields,
duplicate keys, invalid types, non-finite numbers and invalid timestamps are rejected.

## Development and validation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --no-deps --only-binary=:all: -r requirements-build.lock
PYTHONPATH=src .venv/bin/python tools/verify.py
SOURCE_DATE_EPOCH=1791504000 .venv/bin/python -m build --no-isolation
.venv/bin/python tools/smoke_wheel.py
.venv/bin/python tools/check_reproducible.py
```

The build-only lockfile pins wheel hashes. Runtime and tests use the standard library.
CI executes these commands on Ubuntu runners with Python 3.12/3.13, read-only token
permissions and SHA-pinned Actions. CI runner tests are not OS support certification.

- [Requirements and MVP acceptance](docs/requirements.md)
- [Threat model](docs/threat-model.md)
- [Architecture](docs/architecture.md)
- [ADR-001: Python and evidence-first scope](docs/adr-001.md)
- [Rule/evidence matrix](docs/check-matrix.md)
- [Real laboratory protocol and platform matrix](docs/laboratory.md)
- [Release notes and known gaps](docs/release-notes.md)
- [Cloud environment setup](docs/environment.md)
- [Verified release publication](docs/release-workflow.md)
- [Security reporting](SECURITY.md)
- [Input JSON Schema](schemas/input-v1.schema.json)

No real credentials, raw host configuration, inventory or audit dumps belong in
this public repository. Please use only synthetic fixtures in issues and PRs.
