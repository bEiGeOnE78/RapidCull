from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from rapidcull.models import MetadataValue


@dataclass(frozen=True)
class ExifToolExtractionSuccess:
    path: Path
    metadata: dict[str, MetadataValue]


@dataclass(frozen=True)
class ExifToolExtractionFailure:
    path: Path
    reason: str


ExifToolExtractionOutcome = ExifToolExtractionSuccess | ExifToolExtractionFailure


class ExifToolBatchExtractor:
    def __init__(self) -> None:
        self._queued_outcomes: list[ExifToolExtractionOutcome] = []

    def enqueue_success(self, path: Path, metadata: dict[str, MetadataValue]) -> None:
        self._queued_outcomes.append(
            ExifToolExtractionSuccess(path=path.resolve(), metadata=metadata)
        )

    def enqueue_failure(self, path: Path, reason: str) -> None:
        self._queued_outcomes.append(ExifToolExtractionFailure(path=path.resolve(), reason=reason))

    def enqueue_malformed_response(self, path: Path) -> None:
        self.enqueue_failure(path=path, reason="parse_error")

    def enqueue_transport_failure(self, path: Path) -> None:
        self.enqueue_failure(path=path, reason="transport_error")

    def restart(self) -> None:
        return

    def extract(self, path: Path) -> ExifToolExtractionOutcome:
        resolved_path = path.resolve()
        if not self._queued_outcomes:
            return ExifToolExtractionFailure(path=resolved_path, reason="tool_error")

        outcome = self._queued_outcomes.pop(0)
        if outcome.path != resolved_path:
            return ExifToolExtractionFailure(path=resolved_path, reason="parse_error")
        return outcome


class RealExifToolBatchExtractor:
    def __init__(
        self,
        requested_tags: Sequence[str] | None = None,
        request_timeout_seconds: float = 2.0,
    ) -> None:
        self._request_id = 0
        self._process: subprocess.Popen[str] | None = None
        self._requested_tags = list(
            requested_tags
            if requested_tags is not None
            else ["-FileType", "-DateTimeOriginal", "-CreateDate", "-Make", "-Model"]
        )
        self._request_timeout_seconds = request_timeout_seconds

    def __enter__(self) -> RealExifToolBatchExtractor:
        self._start_process()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _start_process(self) -> None:
        self._process = subprocess.Popen(
            [
                "exiftool",
                "-stay_open",
                "True",
                "-@",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def close(self) -> None:
        if self._process is None:
            return
        if self._process.stdin is not None:
            self._request_id += 1
            self._process.stdin.write("-stay_open\n")
            self._process.stdin.write("False\n")
            self._process.stdin.write(f"-execute{self._request_id}\n")
            self._process.stdin.flush()
        self._process.terminate()
        self._process.wait(timeout=2)
        self._process = None

    def restart(self) -> None:
        self.close()
        self._start_process()

    def _read_until_marker(self, marker: str) -> list[str] | None:
        if self._process is None or self._process.stdout is None:
            return None

        response_lines: list[str] = []
        deadline = time.monotonic() + self._request_timeout_seconds

        while True:
            if time.monotonic() > deadline:
                return None

            line = self._process.stdout.readline()
            if line == "":
                return None

            stripped = line.rstrip("\n")
            if stripped == marker:
                return response_lines

            response_lines.append(line)

    def extract(self, path: Path) -> ExifToolExtractionOutcome:
        if self._process is None:
            return ExifToolExtractionFailure(path=path.resolve(), reason="tool_unavailable")
        if self._process.stdin is None or self._process.stdout is None:
            return ExifToolExtractionFailure(path=path.resolve(), reason="tool_error")

        self._request_id += 1
        marker = f"{{ready{self._request_id}}}"

        self._process.stdin.write("-j\n")
        self._process.stdin.write("-G4\n")
        self._process.stdin.write("-n\n")
        self._process.stdin.write("-api\n")
        self._process.stdin.write("structformat=jsonq\n")
        for tag in self._requested_tags:
            self._process.stdin.write(f"{tag}\n")
        self._process.stdin.write(str(path.resolve()) + "\n")
        self._process.stdin.write(f"-execute{self._request_id}\n")
        self._process.stdin.flush()

        response_lines = self._read_until_marker(marker)
        if response_lines is None:
            return ExifToolExtractionFailure(path=path.resolve(), reason="transport_error")

        payload = "".join(response_lines).strip()
        if not payload:
            return ExifToolExtractionFailure(path=path.resolve(), reason="parse_error")

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return ExifToolExtractionFailure(path=path.resolve(), reason="parse_error")

        if not isinstance(decoded, list) or not decoded:
            return ExifToolExtractionFailure(path=path.resolve(), reason="parse_error")

        first_item = decoded[0]
        if not isinstance(first_item, dict):
            return ExifToolExtractionFailure(path=path.resolve(), reason="parse_error")

        normalized: dict[str, MetadataValue] = {}
        for key, value in first_item.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[str(key)] = value

        return ExifToolExtractionSuccess(path=path.resolve(), metadata=normalized)
