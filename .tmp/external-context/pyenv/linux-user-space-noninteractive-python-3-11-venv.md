---
source: Context7 API + official pyenv docs
library: pyenv
package: pyenv
topic: linux user-space install, non-interactive shell init, Python 3.11.x, project-local venv, interpreter verification
fetched: 2026-03-07T00:00:00Z
official_docs: https://github.com/pyenv/pyenv#installation
---

## Scope (Ubuntu/Debian, current pyenv guidance)

Focused steps for:
- installing pyenv in user space (`~/.pyenv`)
- shell init that works in non-interactive scripts
- installing Python 3.11.x
- creating a project-local `.venv` from that pyenv Python
- verifying the interpreter path is the expected pyenv one

---

## 1) Install build dependencies (Ubuntu/Debian)

From pyenv wiki “Suggested build environment”:

```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev curl git \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev
```

If `make` or `gcc` is missing, Python builds fail.

---

## 2) Install pyenv in user space

Recommended installer:

```bash
curl -fsSL https://pyenv.run | bash
```

Equivalent manual location is `~/.pyenv` (user-owned, no sudo).

---

## 3) Shell initialization (interactive + non-interactive-safe pattern)

pyenv docs recommend setting `PYENV_ROOT`, prepending `$PYENV_ROOT/bin`, and running `pyenv init`.

For **Bash on Ubuntu/Debian**, put lines in both `~/.bashrc` and `~/.profile` so login/non-login startup order does not drop shims from PATH.

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
```

For non-interactive script use, pyenv supports a lighter shim setup command:

```bash
eval "$(pyenv init --path)"
```

Practical script preamble when you need pyenv-selected `python` in CI/cron:

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
```

Then run `pyenv exec <cmd>` for deterministic execution:

```bash
pyenv exec python -V
```

---

## 4) Install Python 3.11.x and select it for a project

Install latest available 3.11 patch via prefix resolution:

```bash
pyenv install 3.11
```

Set project-local version (writes `.python-version` in project dir):

```bash
cd /path/to/project
pyenv local 3.11
```

Check selected version:

```bash
pyenv version
python -V
```

---

## 5) Create project-local venv from pyenv Python

Inside the project directory after `pyenv local 3.11`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

This `.venv` is created from the currently selected pyenv interpreter.

---

## 6) Verify interpreter path (critical checks)

Verify shell resolves through pyenv shims and then to the intended install:

```bash
which python
pyenv which python
python -c 'import sys; print(sys.executable)'
```

Expected:
- `which python` -> usually `~/.pyenv/shims/python` (before venv activation)
- `pyenv which python` -> `~/.pyenv/versions/3.11.x/bin/python`
- with venv active, `sys.executable` -> `/path/to/project/.venv/bin/python`

---

## Common pitfalls (from pyenv docs/wiki)

1. **Missing apt build deps** → build fails (`zlib`, `ssl`, etc.).
2. **Only editing one startup file** on Debian/Ubuntu → PATH order can hide shims; configure both `.bashrc` and `.profile`.
3. **Using `eval "$(pyenv init - bash)"` in problematic `BASH_ENV` setups** can cause loops; prefer careful placement and use `--path` for non-interactive contexts.
4. **Not checking build logs** after `BUILD FAILED`; earliest error in log is often root cause.
5. **Assuming fuzzy `.python-version`** values; pyenv expects installed version names/directories.
