---
source: Context7 API + mypy official docs
library: mypy
package: mypy
topic: missing py.typed marker and installed-module import resolution in src layout
fetched: 2026-03-07T00:00:00Z
official_docs: https://mypy.readthedocs.io/en/stable/running_mypy.html
---

## Relevant mypy guidance (current docs)

- Error meaning: `Skipping analyzing 'X': module is installed, but missing library stubs or py.typed marker` means mypy found an installed module but it is not PEP 561-typed (no inline typing marker `py.typed`, no stubs).
- Mypy import search path includes: `MYPYPATH`, `mypy_path`, directories passed on command line, and installed PEP 561 packages.
- For src layouts without top-level `__init__.py`, docs recommend using `--explicit-package-bases` with `MYPYPATH=src` (or `mypy_path = .../src`) so module mapping is unambiguous.
- `mypy_path` paths are resolved relative to current working directory unless you use `$MYPY_CONFIG_FILE_DIR`.
- `follow_untyped_imports = true` is available but warned as lower-quality / slower analysis; prefer typed deps or stubs.

## Concise remediation options for `src/rapidcull` project

### A) Run mypy on source path (recommended for first-party strict checks)

```bash
python -m mypy src
```

or package-targeted from source root:

```bash
python -m mypy -p rapidcull
```

Use this only when `rapidcull` resolves to local `src/rapidcull` (not an untyped installed wheel).

### B) Configure `mypy_path` for src layout (recommended)

```toml
[tool.mypy]
python_version = "3.11"
strict = true
mypy_path = "$MYPY_CONFIG_FILE_DIR/src"
files = ["src"]
namespace_packages = true
explicit_package_bases = true
```

### C) Add `py.typed` under package (required if package is installed and should be treated as typed)

Add file:

```text
src/rapidcull/py.typed
```

And include it in packaging metadata so wheels/sdists ship it.

Setuptools example:

```toml
[tool.setuptools.package-data]
rapidcull = ["py.typed"]
```

### D) Avoid installed-package resolution pitfalls

1. Run with environment-qualified executable:

```bash
python -m mypy src
python -m pip show rapidcull mypy
```

2. If mypy picks wrong interpreter/site-packages, pin interpreter:

```bash
python -m mypy --python-executable "$(python -c 'import sys; print(sys.executable)')" src
```

3. If you only want local source checking and to ignore installed typed packages discovery:

```bash
python -m mypy --no-site-packages src
```

4. For genuinely untyped third-party libs (not your first-party package), prefer targeted overrides (instead of global ignore):

```toml
[[tool.mypy.overrides]]
module = ["some_untyped_lib.*"]
ignore_missing_imports = true
```

## Practical recommendation order

1. **Primary**: check `src` directly + `mypy_path` + `explicit_package_bases`.
2. **If package is imported as installed artifact**: add and ship `py.typed`.
3. **Use suppress/follow_untyped_imports only as temporary exceptions**.
