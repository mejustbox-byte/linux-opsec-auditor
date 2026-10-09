# Threat model

Assets: configuration integrity, host availability, private infrastructure metadata,
report integrity and operator trust. Actors: legitimate operator, malicious snapshot
provider, untrusted local filesystem, untrusted PR author and compromised host/root.

Boundaries: local filesystem or operator JSON → strict schema → normalized facts →
pure rule evaluation → whitelisted evidence → private file or explicitly requested
stdout. CI inputs are untrusted source; release credentials are separate from tests.
No remote SSH transport exists in this prerelease.

| Threat | Control | Residual / test |
|---|---|---|
| Command injection | No subprocess/network runtime imports; only fixed paths | Malicious future collector needs review; AST guard and source review |
| Malicious JSON | Strict schema, duplicate rejection, 1 MiB cap, type/date/range checks | JSON parsing up to cap costs memory; invalid/recursive tests |
| FIFO/device/symlink attack | O_PATH validation; component nofollow; reopen verified regular fd via /proc/self/fd | Requires genuine procfs and trusted kernel; filesystem stalls lack hard timeout |
| File replacement race | Read/stat anchored by descriptors; no symlink following | Untrusted mount/kernel cannot be attested |
| Output overwrite/permission leak | Owner/private parent, exclusive 0600 creation, nofollow directory descriptors | Operator may later publish stdout/files; privileged process can read them |
| Secrets in evidence/errors | Closed field vocabulary; generic OS errors; redact digest values | Even boolean posture data is sensitive; keep reports private |
| Fabricated evidence | Label synthetic/operator as asserted; all platforms unverified | Source field is self-reported, no signature/attestation; a pass is conditional |
| Stale facts | UTC date validation, 24-hour maximum age, 5-minute future tolerance | Clock and fact truth controlled externally |
| False confidence | Missing/unsupported/runtime-static facts unknown, limited scope per finding | Normalized inputs cannot validate a full system; manual verification needed |
| Supply chain | Runtime/test stdlib, exact build wheel hashes, pinned Actions, contents:read | Python/pip/runner remain trust roots; updates need review |
| Host compromised by root | No claim of independent attestation | Root/kernel can falsify all observations; external trust outside MVP |
| CI credential exfiltration | No secrets required, no pull_request_target, no publishing CI | Public logs must contain only synthetic data |

Never read private keys, shadow, process environment, full audit/journal records,
backup contents or cloud credential files. No production fixtures. A fixed mode-bit
scope does not include ACLs, directory traversal rights, mount options or all files.
Static SSH findings require review, not blind remediation. LSM enforcement alone is
not proof of complete confinement. Recovery instructions are recommendations only.

Privileged execution is unnecessary and discouraged. A manually run root process
can read more files but this product neither authorizes privilege escalation nor
promises trusted host evidence. Remote collection will need a separate host-key,
credential, command allowlist and transport ADR before implementation.
