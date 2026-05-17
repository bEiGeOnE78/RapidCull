#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ is required for RapidCull")
PY

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install chromium

python -m pytest --version
python -m black --version
python -m ruff --version
python -m mypy --version

echo "RapidCull bootstrap complete."
