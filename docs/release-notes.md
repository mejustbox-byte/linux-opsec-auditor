# v0.1.0-alpha.1 / Python version 0.1.0a1

Intended first experimental prerelease. Publication is a separate GitHub operation;
this file does not assert that a release or a merged PR exists.

## Features

- Strict versioned input schema, duplicate/type/date/range/size validation and safe errors.
- 12 limited posture rule families with evidence, confidence, severity, remediation
  and pass/fail/unknown/not_run outcomes; unsupported/stale snapshots unknown.
- JSON/readable reports, explicit check selection and fail thresholds.
- Small no-command/no-network/no-sudo collector for fixed SSH configuration,
  critical-file metadata and a limited SELinux indicator; private create-only output.
- Synthetic fixtures, nonempty unit and filesystem/CLI integration tests.
- No third-party runtime dependencies; hash-locked build toolchain, installable wheel
  and source archive, isolated wheel smoke and same-toolchain wheel reproducibility.
- SHA-pinned GitHub Actions CI for Python 3.12/3.13 on Ubuntu runners.

## Validation and limitations

Local synthetic tests and installed-wheel checks are recorded in the delivery
report. GitHub CI results must be verified separately, never inferred from local tests.
Real Ubuntu 22.04/24.04, Debian 12/13, RHEL 9/10 VM tests are **not executed**. Aarch64,
container userspace tests, effective sshd policy, host kernel/backports, actual LSM,
systemd, container isolation, audit/journal delivery, restore and drift-baseline
integrity are **not validated**. No paid infrastructure has been created.

Most domains require normalized external facts; their collectors are not implemented.
Input source tags are self-reported and not attested. Local SSH does not expand
Include/Match, metadata excludes ACLs/parent dirs, LSM host_context is always false.
No remote SSH transport, package/advisory acquisition, sudo/PAM parser, repair or
secret collection. Kernel/filesystem stalls lack a hard I/O deadline.
Only wheel bytes have a reproducibility check; sdist bytes are not claimed reproducible.
Read effects such as atime/audit logs remain possible; no host settings are changed.

## Artifacts and installation

Intended assets: linux_opsec_auditor-0.1.0a1-py3-none-any.whl,
linux_opsec_auditor-0.1.0a1.tar.gz, SHA256SUMS. Download them together and verify the
checksums. Install wheel into a Python 3.12+ Linux venv using
`python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a1-py3-none-any.whl`.
The source archive includes documentation and fixtures. Exact commands and exit
semantics are in [usage](usage.md); real-host gates are in [laboratory](laboratory.md).
Checksums are unsigned corruption checks, not independent provenance attestation.
