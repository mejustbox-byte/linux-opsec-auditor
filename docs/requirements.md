# Requirements and MVP plan

Updated 2026-10-09 from the onboarding design. User authorization now includes
implementation, commit, push, PR, merge and prerelease; the earlier documentation-only
restriction is superseded. No paid resources, real credentials or production dumps.

## Requirements

| ID | Requirement | MVP evidence / gap |
|---|---|---|
| R01 | Read-only audit; no remediation, service changes, package installation or kernel changes | Runtime imports no command/network APIs; fixed-path reads; only requested report file is written |
| R02 | No sudo or escalation by default; inaccessible sources unknown | No escalation implementation; unavailable/omitted source unknown |
| R03 | No arbitrary command/policy execution or shell interpolation | No runtime subprocess; schema rejects unknown fields |
| R04 | Stable versioned rules, UTC timestamps, severity, evidence, reason, remediation, limits | 12 groups, rule/policy/schema versions, readable and JSON reports |
| R05 | Minimize secrets/infrastructure data | Whitelisted boolean/enum/integer evidence; digest equality only in reports |
| R06 | Local/private output; no network publishing | Explicit report path, private directory and create-only 0600 output; stdout is operator-controlled |
| R07 | Bound untrusted input; reject symlinks, FIFO, devices, traversal | 1 MiB input, 64 KiB SSH, 16 KiB OS identity, nofollow fd traversal; no hard filesystem I/O deadline |
| R08 | Distinguish static configuration, runtime observations and asserted/synthetic facts | Evidence source and limitation; runtime-oriented static pass downgraded |
| R09 | OS/version-specific applicability; no implicit fallback | Ubuntu 22.04/24.04, Debian 12/13, RHEL 9/10 candidate profiles, x86_64 only |
| R10 | Unavailable is not clean; malformed input is an error | unknown vs not_run, CLI exit 2, no payload echo |
| R11 | Deterministic evaluation apart from timestamps | Pure evaluation with injected clock; stable order/IDs |
| R12 | Target 60 s and 128 MiB on reference host | Not benchmarked on reference host; no hard timeout/memory claim |
| R13 | No network on target; verified dated advisory inputs | Offline assertions only; advisory authenticity/entitlement not implemented |

Additional acceptance: local collection must not change guarded configuration;
report output must never overwrite existing files; nonempty tests must run; wheel
must install without network or runtime dependencies; examples are synthetic.
No `not_applicable` or `error` finding statuses: omitted/inapplicable candidate
platform evidence is unknown; disabled checks are not_run; invalid documents fail
before partial evaluation with exit 2. This intentionally updates the initial design.

## Delivered MVP sequence

1. Freeze requirements/threat model and source-of-evidence semantics.
2. Implement strict normalized schema and pure evaluator for 12 limited policies.
3. Implement bounded local SSH/metadata observation and private output.
4. Add pass/fail/unknown/not_run fixtures, malformed input and filesystem tests.
5. Build hash-locked packaging, wheel smoke, deterministic-wheel check and CI.
6. Prepare prerelease artifacts and limitations; publish only with real remote success.

## Next increments and release gate

Next: per-file findings, ACL/parent-dir context; SSH effective config with explicit
Match contexts; OS-specific sudo/PAM parsers; systemd runtime collector; vendor
backport/advisory verification; SSH transport ADR; approved baseline signing.
Each needs supported failure tests and safe commands/read sources before rollout.
No stable release or claim of OS support until real VM protocols pass separately
for each supported release and architecture. A host read can update atime or audit
logs: read-only means no configuration/remediation writes, not no side effects.
