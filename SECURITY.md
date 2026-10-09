# Security policy

0.1.0a1 is experimental. No real-host Linux platform support is certified.
Use only explicitly authorized laboratory hosts; do not treat a result as proof
against a compromised kernel, complete compliance or reliable backup restoration.

Never include production dumps, credentials, private keys, users, hostnames, IP
inventories or raw audit logs in public issues/PRs. Prefer a small synthetic fixture
and reproducible steps. Use GitHub private vulnerability reporting if it is enabled;
otherwise contact the repository owner through an available private channel before
sharing sensitive security details. Do not post a live secret publicly.

Runtime scope and residual risks are documented in docs/threat-model.md. Auditing
must remain read-only: no escalation, network calls, remediation or configuration
writes. Reports are still sensitive; keep them outside the public checkout.
