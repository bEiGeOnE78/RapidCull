---
source: Context7 API + Official docs
library: pytest
package: pytest
topic: venv setup and invocation remediation (python -m pytest vs pytest)
fetched: 2026-03-07T00:00:00Z
official_docs: https://docs.pytest.org/en/stable/how-to/usage.html
---

## Practical remediation for `pytest: command not found`

### 1) Create and use a virtual environment

```bash
python -m venv .venv
```

Activate it:

- macOS/Linux (bash/zsh):

```bash
source .venv/bin/activate
```

- Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

### 2) Install pytest into that exact interpreter

Use the interpreter-bound installer to avoid PATH/interpreter mismatches:

```bash
python -m pip install -U pip pytest
```

If your `pyproject.toml` defines test extras/dependency groups, install those instead (example):

```bash
python -m pip install -e ".[dev]"
```

### 3) Run tests with the recommended invocation

```bash
python -m pytest
```

Why this is recommended for reliability:

- It guarantees pytest runs with the same Python interpreter/environment as `python`.
- It avoids failures when the `pytest` console script is missing from PATH.
- Pytest docs explicitly note using `python -m pytest` for running local copies in common layouts.

`pytest` (without `python -m`) is fine after activation when the entrypoint exists in that venv’s scripts directory, but `python -m pytest` is more robust in CI and multi-Python setups.

### 4) pyproject.toml baseline config (optional but common)

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = ["tests"]
```

### 5) Quick diagnostics if still failing

```bash
python -c "import sys; print(sys.executable)"
python -m pip show pytest
python -m pytest --version
```

If `pip show` returns nothing, pytest is not installed in the active interpreter.

## Source highlights used

- pytest docs: use venv + pip; run tests with `python -m pytest`; pyproject configuration support and import/path caveats.
- Python docs (`venv`): activation is optional, but scripts are interpreter/path-dependent; using explicit interpreter avoids ambiguity.
