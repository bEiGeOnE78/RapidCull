"""Path normalization and validation utilities (FR-046).

All file/path inputs must pass through normalize_path() before use.
This prevents path traversal attacks and ensures canonical resolution.
"""

from __future__ import annotations

from pathlib import Path


def normalize_path(path: str | Path, base_dir: Path | None = None) -> Path:
    """Resolve and normalize a path. Raise ValueError if it escapes base_dir.

    Args:
        path: The path to normalize (string or Path).
        base_dir: Optional base directory. If provided, the resolved path
                  must be inside base_dir or ValueError is raised.

    Returns:
        Resolved absolute Path.

    Raises:
        ValueError: If path escapes base_dir.
    """
    resolved = Path(path).resolve()
    if base_dir is not None:
        base = base_dir.resolve()
        try:
            resolved.relative_to(base)
        except ValueError:
            raise ValueError(
                f"Path '{resolved}' is outside the allowed base directory '{base}'"
            ) from None
    return resolved
