# Installation and CLI reference

Requires Linux, genuine procfs and Python >=3.12. Do not run as root unless the
operator has separately authorized privileged reads. Local audit does not provision
Python, install packages, run sudo or change configuration. Runtime has no dependencies.

## Install from source

The README development commands install only hash-locked build tools into `.venv`.
After building:

```bash
.venv/bin/python -m pip install --no-index --no-deps dist/linux_opsec_auditor-0.1.0a1-py3-none-any.whl
.venv/bin/linux-opsec-auditor --version
```

Or use `PYTHONPATH=src python3 -m linux_opsec_auditor` directly, with no installation.

## Install release artifacts (once the prerelease is actually published)

The intended tag is `v0.1.0-alpha.1`. These commands need an accessible published
release; a release-note file alone does not establish that one exists.

```bash
mkdir -p opsec-download
cd opsec-download
gh release download v0.1.0-alpha.1 --repo mejustbox-byte/linux-opsec-auditor \
  --pattern 'linux_opsec_auditor-0.1.0a1-py3-none-any.whl' \
  --pattern 'linux_opsec_auditor-0.1.0a1.tar.gz' --pattern SHA256SUMS
sha256sum --check SHA256SUMS
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a1-py3-none-any.whl
.venv/bin/linux-opsec-auditor --version
```

Checksums detect corruption; unsigned release checksums are not independent
publisher attestation. Build tools are not required to install the wheel.

## Local bounded collection and report

On an explicitly authorized laboratory host with Python already installed:

```bash
opsec_report_dir=$(mktemp -d)
linux-opsec-auditor collect --output "$opsec_report_dir/snapshot.json"
linux-opsec-auditor audit --input "$opsec_report_dir/snapshot.json" \
  --format json --output "$opsec_report_dir/report.json" --fail-on incomplete
```

The incomplete exit is expected: this collector cannot provide full policy evidence.
Do not publish these private files. The CLI creates no directory, overwrites no file,
follows no symlinks, and writes only the explicitly requested new 0600 report/snapshot.
Parent directory must be owned by your effective UID with no group/world bits.
Use a private directory outside the public checkout. stdout is a deliberate export:
terminal logs and pipelines are your responsibility. No infrastructure dump is needed.
`--root PATH` selects a synthetic filesystem tree; it is not a remote-host transport.
For every read, unsafe path components, symlinks and nonregular files are rejected.
Input paths must also avoid symlink parent directories, e.g. some platform `/var/run`
aliases; use a real private directory rather than following the alias.

## Offline evidence

`linux-opsec-auditor schema` prints the versioned input schema. See synthetic files
in `fixtures/` and the rule matrix for the exact normalized fields. A producer may
only submit whitelisted fields with the documented types and declared source.
Do not paste real config, usernames, tokens, hostnames or log contents into snapshots.
`collected_at` must be an actual UTC second timestamp, not a date chosen to bypass
freshness for real evidence. For synthetic demonstrations only, refreshing the
fixture date is acceptable and must retain `source=synthetic`.

```bash
linux-opsec-auditor audit --input /private/path/snapshot.json --format text
linux-opsec-auditor audit --input /private/path/snapshot.json --format json --checks ssh files
```

Selection uses group names: ssh sudo pam systemd files kernel lsm containers logs
backups drift patches. Nonselected checks remain not_run and the full report remains
incomplete. No configuration knobs execute commands or change thresholds silently.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Command succeeded at selected fail threshold; can still include unknown/not_run |
| 1 | Policy failure exists with default `--fail-on fail` or `--fail-on incomplete` |
| 2 | Invalid invocation/input, unavailable file, unsafe output or I/O error |
| 3 | No policy failures, but unknown/not_run exists with `--fail-on incomplete` |

`--fail-on none` returns 0 after valid evaluation even with failures. It never hides
parse/I/O errors. A `complete` report can still fail and is never a certification.
Static source, self-reported runtime source and unsupported platform limitations
remain visible in each finding. Original input values never appear in error messages.
