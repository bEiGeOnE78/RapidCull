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

    def _run_resize(self, input_path: Path, output_path: Path, size: str, quality: int) -> bool:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = ["magick", str(input_path.resolve()), "-resize", size, "-quality", str(quality), str(output_path.resolve())]
        return self._run_command(command) == 0

    def _run_convert(self, input_path: Path, output_path: Path, quality: int) -> bool:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = ["magick", str(input_path.resolve()), "-quality", str(quality), str(output_path.resolve())]
        return self._run_command(command) == 0

    def generate_still_thumbnail(
        self,
        path: Path,
        output_path: Path | None = None,
        thumb_path: Path | None = None,
        display_path: Path | None = None,
        full_path: Path | None = None,
    ) -> ImageMagickProxyOutcome:
        if thumb_path is None and output_path is not None:
            thumb_path = output_path

        if thumb_path is None and display_path is None:
            thumb_path = path.with_name(path.stem + ".proxy.jpg")

        try:
            if thumb_path is not None:
                if not self._run_resize(path, thumb_path, "400x400>", 75):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")
            if display_path is not None:
                if not self._run_resize(path, display_path, "1920x1920>", 82):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")
            if full_path is not None:
                if not self._run_convert(path, full_path, 82):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")
        except OSError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_still_failed")

        return ImageMagickProxyOutcome(ok=True, reason=None)

    def generate_heic_proxy(
        self,
        path: Path,
        output_path: Path | None = None,
        thumb_path: Path | None = None,
        display_path: Path | None = None,
        full_path: Path | None = None,
    ) -> ImageMagickProxyOutcome:
        if not self._heif_supported:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heif_unsupported")

        if thumb_path is None and output_path is not None:
            thumb_path = output_path

        if thumb_path is None and display_path is None:
            thumb_path = path.with_name(path.stem + ".proxy.jpg")

        try:
            if thumb_path is not None:
                if not self._run_resize(path, thumb_path, "400x400>", 75):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_nonzero_exit")
            if display_path is not None:
                if not self._run_resize(path, display_path, "1920x1920>", 82):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_nonzero_exit")
            if full_path is not None:
                if not self._run_convert(path, full_path, 82):
                    return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_nonzero_exit")
        except TimeoutError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_timeout")
        except OSError:
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_execution_error")

        return ImageMagickProxyOutcome(ok=True, reason=None)


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
