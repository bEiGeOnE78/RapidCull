from __future__ import annotations

import shutil
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

    def generate_raw_proxy(
        self, path: Path, pipeline_available: bool, output_path: Path | None = None
    ) -> RawTherapeeProxyOutcome:
        if pipeline_available:
            resolved_output = output_path if output_path is not None else path.with_name(path.stem + ".proxy.jpg")
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
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

                if exit_code == 0:
                    generated_file = Path(tmp_dir) / (path.stem + ".jpg")
                    if not generated_file.exists():
                        return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")
                    shutil.move(str(generated_file), resolved_output)
                    return RawTherapeeProxyOutcome(ok=True, reason=None)
            return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")

        return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_pipeline_unavailable")
