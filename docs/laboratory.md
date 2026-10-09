# Real laboratory protocol and candidate platforms

**Not executed in this environment. No platform is validated or supported by a
stable release yet.** Do not infer real-host behavior from fixtures or containers.
No paid resources are created. An operator must supply existing disposable VM or
physical laboratory capacity; absence of that capacity is a release limitation.

| Distribution | Candidate versions | Distinct validation required |
|---|---|---|
| Ubuntu | 22.04 LTS, 24.04 LTS | GA/HWE kernel, AppArmor enabled/enforcing and disabled cases; ESM separate |
| Debian | 12, 13 | Security/LTS lifecycle separately; actual AppArmor availability, systemd runtime |
| RHEL | 9, 10 | Exact minor/kernel and vendor backports, SELinux enforcing/permissive, entitlement |

Initial architecture target x86_64. Aarch64 is unverified and policies produce unknown.
RHEL clones are not RHEL; separate profiles/evidence would be needed. Ubuntu 26.04,
RHEL 8 and other releases are outside the MVP candidate matrix. Check current vendor
lifecycle before promoting any version. CLI Python >=3.12 is a prerequisite distinct
from distribution support; provision it independently before the audit, not during.

## Levels of evidence

L0 unit/integration: synthetic normalized JSON and synthetic local filesystem trees.
Tests can prove evaluator/parser/CLI contracts, not host control effectiveness.
L1 container userspace: optional future packaging/parser checks; no host kernel,
LSM, systemd or boundary certification from a distribution image. Not executed here.
L2 full VM: own kernel, real init, real LSM with separately prepared positive/negative
states. Required before host-support claims. Not executed here.
L3 SSH: known_hosts rejection, command allowlist, timeouts and permissions on disposable
VMs, after transport implementation. Deferred; no SSH transport exists in 0.1.0a1.

## Reproducible real-host checklist (operator-run, not auditor remediation)

1. Use a disposable authorized VM with snapshot/recovery and isolated network; no
production credentials/inventory. Record distro exact minor, image digest, kernel,
architecture, Python, LSM, namespace and effective UID in a private evidence record.
2. Install the verified wheel in a preprovisioned environment. Do not ask the auditor
to install packages or fix host settings. Test configuration states are established
by a separate operator/provisioner before collection, never by the auditor.
3. Compare allowed configuration file bytes, owners, modes and ACL metadata before
and after the audit using an independent read-only mechanism. Compare inventories
of configuration changes, not all filesystem bytes: atime/audit/journal activity
from reads and sessions is expected and must be explicitly accounted for.
4. Run the bounded collection command in the usage guide with an unprivileged UID,
then offline evaluation with `--fail-on incomplete`. Record expected unknowns for
nonimplemented sources. Missing sudoers access must not produce a clean result.
5. Independently inspect sshd effective config for explicit Match/Include contexts
with administrator-approved read-only validation. Compare with fragment findings;
Include-containing static input should remain unknown, never an effective pass.
6. Verify file ownership/mode detections against actual metadata; test denied reads,
symlink aliases, missing files and ACL-granted write access. ACL cases must remain
outside collector completeness until ACL collection is implemented.
7. Independently compare booted kernel against authenticated vendor backport/advisory
information and installed kernels. No version-string-only patch claims. Normalize
into a private snapshot only with defensible current facts; authenticity is external.
8. On Ubuntu/Debian inspect actual AppArmor loaded/enforcing profiles; on RHEL inspect
SELinux runtime enforcement and policy scope. Container reads must not grant host
context; local MVP always leaves host_context=false. No active enforcement probe
that changes audited settings is permitted.
9. Independently inspect selected systemd properties, container boundary settings,
audit retention/delivery and external restore evidence. These normalized assertions
can exercise rules but do not constitute implemented local collectors.
10. Keep a private record with commit/artifact hash, policy and feed/baseline versions,
checks run, pass/fail/unknown/not_run counts, limitations and before/after findings.
Publish only a sanitized synthetic-compatible summary after review; never raw outputs.
11. Restore/destroy disposable test states and VM snapshots through the lab owner.
The product itself does not roll back or remediate anything.

A stable-release gate requires per-version real evidence, negative/denied cases,
reviewed scope and privacy, measured resource limits and verified dependency trust.
No claim of 60-second/128-MiB host performance has been established. Network/distributed
filesystem hangs are an explicit remaining limitation despite input-size bounds.
