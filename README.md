# v0.1.0-alpha.1 verified build artifacts

Built from merged product commit 70d43abb5bbc5350e7df2ed20e41847bba36938e.
Native release asset upload returned HTTP 401 for uploads.github.com; this branch
is the authorized Git-push handoff, not a workaround for API authentication.

Download wheel, source archive and SHA256SUMS together; run `sha256sum --check SHA256SUMS`.
Runtime installation: `python3 -m venv .venv`, then
`.venv/bin/python -m pip install --no-index --no-deps linux_opsec_auditor-0.1.0a1-py3-none-any.whl`.
Python 3.12+ on Linux is required. Source archive includes user/laboratory instructions.

27 local synthetic tests passed, source fresh-venv setup passed, and GitHub CI passed
on Python 3.12/3.13. No real-host platform validation: kernel/LSM/systemd/containers,
backup restore and log delivery remain unverified. Do not put real infrastructure
or credentials in this public branch. Checksums are unsigned integrity checks.
