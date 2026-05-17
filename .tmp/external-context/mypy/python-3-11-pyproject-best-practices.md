---
source: Context7 API + mypy official docs
library: mypy
package: mypy
topic: python-3-11-pyproject-best-practices
fetched: 2026-03-07T00:00:00Z
official_docs: https://mypy.readthedocs.io/en/stable/
---

## Practical best-practice setup (Python 3.11, `pyproject.toml`)

### 1) Dev dependency pinning

- Pin `mypy` to a compatible minor/patch range for reproducible CI (`mypy==1.19.1` or `mypy~=1.19.0`).
- Pin third-party stub packages (`types-requests`, `types-PyYAML`, etc.) like normal dev/test dependencies.
- Prefer explicit stub installs over `mypy --install-types` in CI, since `--install-types` is slower and less reproducible.

### 2) Minimal strict config that is practical

Use strict mode, then explicitly relax only what blocks adoption.

```toml
[tool.mypy]
python_version = "3.11"

# Practical strict baseline
strict = true

# Helpful hygiene / ergonomics
warn_unreachable = true
show_error_codes = true
pretty = true

# Good defaults for modern src-layout repos
namespace_packages = true
explicit_package_bases = true

# Cache (incremental is true by default)
cache_dir = ".mypy_cache"
sqlite_cache = true

# Optional: avoid checking generated/venv paths during recursive discovery
exclude = [
  '^build/',
  '^dist/',
  '^\.venv/'
]
```

### 3) Command invocation

- Prefer `python -m mypy` to ensure the current environment/interpreter is used.
- Standardize one command for local + CI.

```bash
# Local / CI (explicit package)
python -m mypy -p your_package

# Or path-based
python -m mypy src tests

# If needed, force interpreter for PEP 561 packages
python -m mypy --python-executable .venv/bin/python -p your_package
```

### 4) Third-party imports handling

Order of preference from docs:

1. Install library stubs when available (`types-*`, or dedicated stubs like `django-stubs`).
2. Use targeted per-module overrides for truly untyped packages.
3. Avoid global `ignore_missing_imports = true` where possible.

```toml
[[tool.mypy.overrides]]
module = ["some_untyped_lib", "some_untyped_lib.*"]
ignore_missing_imports = true
```

Alternative for migration periods:

```toml
[tool.mypy]
disable_error_code = ["import-untyped"]
```

### 5) Gradual enforcement strategy

- Start with a subset/package and enforce consistent invocation/version in CI.
- Keep `strict = true`, then selectively loosen specific pain points per-module, instead of globally weakening checks.
- Tighten over time: remove per-module ignores, add annotations in frequently imported modules first.
- Use `warn_unused_ignores = true` (included in strict) to clean up legacy suppressions.

Suggested phased pattern:

```toml
[tool.mypy]
python_version = "3.11"
strict = true

[[tool.mypy.overrides]]
module = ["legacy_pkg.*"]
ignore_errors = true

[[tool.mypy.overrides]]
module = ["new_or_refactored_pkg.*"]
disallow_untyped_defs = true
```

Then shrink `legacy_pkg.*` ignores over time.
