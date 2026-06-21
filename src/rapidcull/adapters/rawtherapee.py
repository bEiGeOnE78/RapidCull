from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawTherapeeProxyOutcome:
    ok: bool
    reason: str | None


class RawTherapeeAdapter:
    def _run_command(self, command: list[str]) -> int:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        return result.returncode

    def _convert_webp(self, source: Path, output: Path, size: str | None, quality: int) -> bool:
        if size is not None:
            command = ["magick", str(source.resolve()), "-resize", size, "-quality", str(quality), str(output.resolve())]
        else:
            command = ["magick", str(source.resolve()), "-quality", str(quality), str(output.resolve())]
        try:
            return self._run_command(command) == 0
        except OSError:
            return False

    def generate_raw_proxy(
        self,
        path: Path,
        pipeline_available: bool,
        output_path: Path | None = None,
        thumb_path: Path | None = None,
        display_path: Path | None = None,
        full_path: Path | None = None,
    ) -> RawTherapeeProxyOutcome:
        if not pipeline_available:
            return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_pipeline_unavailable")

        # backwards compat: output_path acts as thumb_path when thumb_path not given
        resolved_thumb = thumb_path if thumb_path is not None else output_path
        resolved_display = display_path
        resolved_full = full_path

        with tempfile.TemporaryDirectory() as tmp_dir:
            command = [
                "rawtherapee-cli",
                "-o",
                tmp_dir,
                "-j",
                "-c",
                str(path.resolve()),
            ]
            try:
                exit_code = self._run_command(command)
            except OSError:
                return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

            if exit_code != 0:
                return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

            temp_jpeg = Path(tmp_dir) / (path.stem + ".jpg")
            if not temp_jpeg.exists():
                return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

            if resolved_full is not None:
                resolved_full.parent.mkdir(parents=True, exist_ok=True)
                if not self._convert_webp(temp_jpeg, resolved_full, None, 82):
                    return RawTherapeeProxyOutcome(ok=False, reason="imagemagick_failed")

            if resolved_display is not None:
                resolved_display.parent.mkdir(parents=True, exist_ok=True)
                if not self._convert_webp(temp_jpeg, resolved_display, "1920x1920>", 82):
                    return RawTherapeeProxyOutcome(ok=False, reason="imagemagick_failed")

            if resolved_thumb is not None:
                resolved_thumb.parent.mkdir(parents=True, exist_ok=True)
                if not self._convert_webp(temp_jpeg, resolved_thumb, "400x400>", 75):
                    return RawTherapeeProxyOutcome(ok=False, reason="imagemagick_failed")

        return RawTherapeeProxyOutcome(ok=True, reason=None)
