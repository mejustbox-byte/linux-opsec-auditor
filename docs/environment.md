# Cloud development environment

The repository is the complete setup source; no /workspace/onboarding directory or
saved virtualenv is required. Tasks are already isolated: use the existing checkout,
not a new Git worktree unless explicitly requested. Preserve unrelated user changes.

## Install / refresh

From the checkout on a Linux cloud worker with Python 3.12+ and Git:

```bash
bash tools/setup_environment.sh
```

This creates `.venv`, installs build-only wheels from `requirements-build.lock` using
hash verification, executes the nonempty synthetic unit/integration suite, checks
repository text/schema/links and secret patterns, builds wheel/sdist, smoke-tests an
isolated installation, checks deterministic wheel bytes and installs the wheel in
`.venv`. It never executes a real-host audit or modifies host security settings.
The script was tested after moving the initially created venv out of the checkout.
Runtime/tests have no third-party dependencies. Only package-manager downloads need
pypi.org/files.pythonhosted.org. No credentials or injected secret values are saved.

## Start / use

No service or database needs startup. Commands:

```bash
.venv/bin/linux-opsec-auditor --version
PYTHONPATH=src .venv/bin/python tools/verify.py
.venv/bin/linux-opsec-auditor schema
```

If `.venv` is absent or invalid, rerun setup instead of assuming a snapshot retained
it. Use [usage](usage.md) for synthetic demos and explicitly authorized laboratory
collection; never auto-collect private infrastructure during cloud startup.
All real-host and OS support gates are in [laboratory](laboratory.md).

## Saved configuration and publication

`install_script` invokes the checkout setup script; `start_skill` points to these
checkout instructions. The former docs-only restriction is superseded by the user's
implementation and publishing authorization. A saved draft is separate from runtime
execution and publishing an environment snapshot. After a new task restores a
snapshot, rerun readiness checks and verify the checkout/artifacts; live processes
and credentials are not assumed to persist. There are no services to restore here.

Git reads/push use the existing platform Git proxy. PR, merge, CI results and release
API need api.github.com; artifact upload also needs uploads.github.com. Those two
custom domains are in the draft; package-manager presets are preserved. Authentication
comes from the provided connection; do not extract it, print it, or add credentials
to configuration. Domain access does not imply authorization; verify actual operations.
