#!/usr/bin/env bash
# Повторяемая подготовка checkout; без аудита хоста и зависимости от сохранённого venv.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Требуется Python 3.12+"'
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir --require-hashes --no-deps --only-binary=:all: -r requirements-build.lock
PYTHONPATH=src .venv/bin/python tools/verify.py
opsec_build_dir=$(mktemp -d)
trap 'rm -rf "$opsec_build_dir"' EXIT
SOURCE_DATE_EPOCH=1791504000 .venv/bin/python -m build --no-isolation --outdir "$opsec_build_dir"
.venv/bin/python tools/smoke_wheel.py --dist "$opsec_build_dir"
.venv/bin/python tools/check_reproducible.py --dist "$opsec_build_dir"
.venv/bin/python -m pip install --no-index --no-deps --force-reinstall "$opsec_build_dir"/*.whl
mkdir -p dist
cp "$opsec_build_dir"/* dist/
.venv/bin/linux-opsec-auditor --version
