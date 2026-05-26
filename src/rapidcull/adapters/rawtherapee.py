from __future__ import annotations

import subprocess
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

    def generate_raw_proxy(self, path: Path, pipeline_available: bool) -> RawTherapeeProxyOutcome:
        if pipeline_available:
            output_path = path.with_name(path.stem + ".proxy.jpg")
            command = [
                "rawtherapee-cli",
                "-o",
                str(output_path.resolve()),
                str(path.resolve()),
            ]
            try:
                exit_code = self._run_command(command)
            except OSError:
                return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

            if exit_code == 0:
                return RawTherapeeProxyOutcome(ok=True, reason=None)
            return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

        return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_pipeline_unavailable")
