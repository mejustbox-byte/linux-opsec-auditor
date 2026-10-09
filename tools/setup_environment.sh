#!/usr/bin/env bash
# Repeatable checkout setup. Never audits a host or depends on a retained venv.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ required"'
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir --require-hashes --no-deps --only-binary=:all: -r requirements-build.lock
PYTHONPATH=src .venv/bin/python tools/verify.py
SOURCE_DATE_EPOCH=1791504000 .venv/bin/python -m build --no-isolation
.venv/bin/python tools/smoke_wheel.py
.venv/bin/python tools/check_reproducible.py
.venv/bin/python -m pip install --no-index --no-deps --force-reinstall dist/linux_opsec_auditor-0.1.0a1-py3-none-any.whl
.venv/bin/linux-opsec-auditor --version
