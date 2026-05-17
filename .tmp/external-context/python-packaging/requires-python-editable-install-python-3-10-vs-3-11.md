---
source: Official docs (PyPA pip/setuptools/packaging)
library: Python packaging
package: python-packaging
topic: requires-python mismatch and editable install workflow
fetched: 2026-03-07T00:00:00Z
official_docs: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
---

## Relevant guidance from official docs

### `requires-python` is authoritative project metadata
- In `pyproject.toml`, `[project].requires-python` declares the minimum supported Python version (example shown by PyPA: `requires-python = ">= 3.8"`).
- This metadata is used by installers to decide interpreter compatibility.
- Classifiers are not enough to enforce install compatibility; `requires-python` is the field that controls install constraints.

Source: PyPA packaging guide (`Writing your pyproject.toml` → `requires-python`).

### Editable installs are still installs and rely on project metadata
- pip supports both regular local installs (`pip install .`) and editable local installs (`pip install -e .`).
- Editable installs are meant for development convenience, but project metadata still matters.
- Editable installs can differ from regular installs depending on build backend, and metadata changes require re-install.

Sources: pip local project installs docs; setuptools development mode docs.

### Recommended environment model for development
- Use an isolated virtual environment (`python -m venv .venv`) and install tooling/dependencies there.
- Setuptools docs explicitly demonstrate editable install inside a venv.

Source: setuptools development mode docs.

## Practical implication for Python 3.10 runtime vs `requires-python >=3.11`

If your runtime is Python 3.10 but project metadata says `requires-python >=3.11`, install workflows that honor metadata (including editable installs) can fail due to interpreter incompatibility.

## Concise workflow options (with tradeoffs)

1) Lower `requires-python` to include 3.10 (only if truly supported)
- Pros: Unblocks local installs on 3.10; metadata matches dev/runtime reality.
- Cons: Commits you to supporting/testing 3.10; potential hidden incompatibilities if code/deps are actually 3.11+.

2) Keep `requires-python >=3.11`, move local dev to 3.11 via pyenv + venv
- Pros: Metadata stays accurate; avoids divergence between declared and actual support.
- Cons: Requires environment upgrade; may diverge from a production runtime still pinned to 3.10.

3) Skip editable install, install only dev tools directly
- Example pattern: install `ruff`, `pytest`, `mypy`, etc. in a venv without `pip install -e .`.
- Pros: Lets lint/test infra proceed when package install is blocked.
- Cons: You are not validating package installation/import path behavior; can mask packaging errors until later.

## Early-stage bootstrap recommendation

For a bootstrapped project in early stage, prefer **Option 2** by default:
- Keep `requires-python` honest and align local dev interpreter to it (3.11).
- If deployment must remain 3.10 short-term, either:
  - temporarily widen `requires-python` **only after** basic tests pass on 3.10, or
  - explicitly separate “package support floor” from infrastructure runtime plan and track migration.

This keeps packaging metadata trustworthy while minimizing future cleanup.
