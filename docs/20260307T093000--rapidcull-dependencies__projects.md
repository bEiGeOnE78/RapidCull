# RapidCull Dependency Catalog

Generated: 2026-03-07T09:30:00

## Purpose

This document captures all known dependencies required to build, run, and test RapidCull on Linux.

---

## 1) Runtime Platform Dependencies (Linux)

## 1.1 Required

- **Python 3.11+**
- **pip** (Python package installer)
- **venv** (virtual environment support)

## 1.2 Required Media/Metadata Toolchain

- **ExifTool** (`exiftool`) — metadata extraction
- **FFmpeg** (`ffmpeg`) — video proxy generation/transcoding
- **ImageMagick** (`magick`/`convert`) — image conversion fallback pipeline
- **RawTherapee CLI** (`rawtherapee-cli`) — RAW proxy generation

## 1.3 Important Build Capability Requirements

- ImageMagick installation should include **HEIC/HEIF support** (typically via libheif) for HEIC workflows.
- HEIC/HEIF capability is treated as a **preflight requirement** for FR-007 workflows; missing support should fail fast with actionable remediation guidance.

---

## 2) Python Application Dependencies

## 2.1 Core Application Libraries (Required)

- **numpy**
- **opencv-python**
- **pillow**
- **scikit-learn**
- **insightface**
- **onnxruntime** (CPU provider expected for InsightFace CPU execution)

## 2.2 Common Supporting Libraries (Likely required by implementation)

- **sqlite3** (standard library)
- **argparse** (standard library)
- **pathlib** (standard library)
- **json** (standard library)
- **datetime** (standard library)

---

## 3) Test and Validation Dependencies

Installed by `scripts/bootstrap.sh`:

- **pytest**
- **pytest-xdist** (parallel test execution)
- **pytest-cov** (coverage)
- **pytest-benchmark** (NFR/performance checks)
- **playwright** (Python)
- **Playwright Chromium runtime**
- **black** (format gate)
- **ruff** (lint gate)
- **mypy** (blocking type gate)

---

## 4) Dependency Classification

## 4.1 Critical Runtime (must exist before app run)

- Python 3.11+
- ExifTool
- FFmpeg
- ImageMagick
- RawTherapee CLI
- numpy
- opencv-python
- pillow
- scikit-learn
- insightface
- onnxruntime

## 4.2 Critical Test Runtime (must exist before full validation)

- pytest
- pytest-xdist
- pytest-cov
- pytest-benchmark
- playwright + chromium runtime

## 4.3 Optional/Deferred (for future CI hardening)

- JSON schema validation tooling for API contract checks
- Additional dependency vulnerability/audit tooling

---

## 5) Linux Package Mapping (Ubuntu/Debian Baseline)

Example system package names (verify against target distro):

- `python3.11`
- `python3.11-venv`
- `python3-pip`
- `libimage-exiftool-perl`
- `ffmpeg`
- `imagemagick`
- `rawtherapee`

Note: package names may differ by distro/version; this section is a baseline reference, not a locked manifest.

---

## 6) Verification Checklist

Minimum verification commands:

```bash
python3 --version
exiftool -ver
ffmpeg -version
magick -version || convert -version
rawtherapee-cli -v
```

HEIF capability verification (ImageMagick delegates/codecs):

```bash
magick -list format | grep -E "HEIC|HEIF" || convert -list format | grep -E "HEIC|HEIF"
```

Expected: output includes `HEIC` or `HEIF` format entries. If missing, install/repair libheif-enabled ImageMagick.

Python verification (inside venv):

```bash
python -c "import numpy, cv2, PIL, sklearn, insightface, onnxruntime; print('ok')"
```

Test tooling verification:

```bash
pytest --version
python -m playwright --version
black --version
ruff --version
mypy --version
```

Bootstrap alignment note:

- Python dependency source of truth is `pyproject.toml` (`.[dev]` extra).
- `scripts/bootstrap.sh` installs `-e ".[dev]"` and browser runtime.
- `scripts/verify_system_deps.sh` validates required Linux media/metadata binaries and fails when ImageMagick HEIC/HEIF capability is unavailable.

---

## 7) Next Actions

1. Add `scripts/install_system_deps.sh` for Linux package installation.
2. Add pinned Python runtime dependency manifest for application packages.
3. Add CI install-smoke job to validate clean-environment dependency installation.
