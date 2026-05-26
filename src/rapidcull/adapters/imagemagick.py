from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageMagickProxyOutcome:
    ok: bool
    reason: str | None


class ImageMagickAdapter:
    def __init__(self, heif_supported: bool | None = None) -> None:
        resolved_heif_supported = (
            detect_heif_support() if heif_supported is None else heif_supported
        )
        self._heif_supported = resolved_heif_supported

    def _run_command(self, command: list[str]) -> int:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        return result.returncode

    def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
        output_path = path.with_name(path.stem + ".proxy.jpg")
        command = [
            "magick",
            str(path.resolve()),
            str(output_path.resolve()),
        ]
        try:
            exit_code = self._run_command(command)
        except OSError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")

        if exit_code == 0:
            return ImageMagickProxyOutcome(ok=True, reason=None)
        return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")

    def generate_heic_proxy(self, path: Path) -> ImageMagickProxyOutcome:
        if not self._heif_supported:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heif_unsupported")

        output_path = path.with_name(path.stem + ".proxy.jpg")
        command = [
            "magick",
            str(path.resolve()),
            str(output_path.resolve()),
        ]
        try:
            exit_code = self._run_command(command)
        except TimeoutError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_timeout")
        except OSError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_execution_error")

        if exit_code == 0:
            return ImageMagickProxyOutcome(ok=True, reason=None)
        return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_nonzero_exit")


def detect_heif_support() -> bool:
    command: list[str] | None = None
    magick_binary = shutil.which("magick")
    if magick_binary is not None:
        command = [magick_binary, "-list", "format"]
    else:
        convert_binary = shutil.which("convert")
        if convert_binary is not None:
            command = [convert_binary, "-list", "format"]

    if command is None:
        return False

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, OSError):
        return False

    return "HEIC" in result.stdout or "HEIF" in result.stdout
