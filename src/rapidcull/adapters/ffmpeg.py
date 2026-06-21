from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FFmpegProxyOutcome:
    ok: bool
    reason: str | None
    thumbnail_path: Path | None = None
    display_path: Path | None = None


class FFmpegAdapter:
    def _run_command(self, command: list[str]) -> int:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        return result.returncode

    def _probe_duration(self, source_path: Path) -> float | None:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(source_path.resolve()),
        ]
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                stripped = result.stdout.strip()
                if stripped:
                    return float(stripped)
        except (OSError, ValueError):
            pass
        return None

    def _extract_frame(
        self,
        source_path: Path,
        output_path: Path,
        timestamp: str,
        width: int,
        height: int,
        quality: int,
    ) -> bool:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
        command = [
            "ffmpeg",
            "-ss", timestamp,
            "-i", str(source_path.resolve()),
            "-frames:v", "1",
            "-vf", scale_filter,
            "-quality", str(quality),
            "-y",
            str(output_path.resolve()),
        ]
        try:
            return self._run_command(command) == 0
        except OSError:
            return False

    def generate_video_proxies(
        self,
        source_path: Path,
        proxy_dir: Path,
        thumb_path: Path | None = None,
        display_path: Path | None = None,
    ) -> FFmpegProxyOutcome:
        duration = self._probe_duration(source_path)
        timestamp = "00:00:01" if (duration is None or duration >= 2.0) else "00:00:00"

        resolved_thumb = thumb_path if thumb_path is not None else proxy_dir / (source_path.stem + ".thumb.webp")
        resolved_display = display_path if display_path is not None else proxy_dir / (source_path.stem + ".display.webp")

        try:
            if not self._extract_frame(source_path, resolved_thumb, timestamp, 300, 300, 80):
                return FFmpegProxyOutcome(ok=False, reason="ffmpeg_video_thumbnail_failed")
            if not self._extract_frame(source_path, resolved_display, timestamp, 1920, 1920, 85):
                return FFmpegProxyOutcome(ok=False, reason="ffmpeg_video_display_failed")
        except OSError:
            return FFmpegProxyOutcome(ok=False, reason="ffmpeg_execution_error")

        return FFmpegProxyOutcome(
            ok=True,
            reason=None,
            thumbnail_path=resolved_thumb,
            display_path=resolved_display,
        )


def generate_video_proxies(source_path: Path, proxy_dir: Path) -> tuple[Path, Path]:
    """Extract video thumbnail and display frames using FFmpeg.

    Returns (thumbnail_path, display_path) as Path objects.
    Raises RuntimeError on failure.
    """
    adapter = FFmpegAdapter()
    outcome = adapter.generate_video_proxies(source_path, proxy_dir)
    if not outcome.ok or outcome.thumbnail_path is None or outcome.display_path is None:
        raise RuntimeError(f"ffmpeg proxy generation failed: {outcome.reason}")
    return outcome.thumbnail_path, outcome.display_path
