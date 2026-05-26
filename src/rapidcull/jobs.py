"""In-memory job store with guarded state transitions for RapidCull job orchestration.

This module is single-process only. The threading.Lock inside JobStore serialises
all id allocation and state transitions for concurrent HTTP handlers, but no
cross-process coordination is provided.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Legal state transitions. Terminal states map to empty sets (sinks).
VALID_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.QUEUED: {JobState.RUNNING, JobState.CANCELLED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: set(),
    JobState.CANCELLED: set(),
}

TERMINAL_STATES: frozenset[JobState] = frozenset(
    {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
)


class InvalidJobTransition(Exception):
    """Raised when a state transition is not permitted."""

    def __init__(self, from_state: JobState, to_state: JobState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Cannot transition from {from_state} to {to_state}")


class JobNotCancellable(Exception):
    """Raised when a cancel is attempted on a terminal job."""

    def __init__(self, job_id: str, state: JobState) -> None:
        self.job_id = job_id
        self.state = state
        super().__init__(f"Job '{job_id}' is in terminal state '{state}' and cannot be cancelled.")


@dataclass(frozen=True)
class JobProgressEntry:
    timestamp: datetime
    message: str
    percent: float | None = None


@dataclass(frozen=True)
class Job:
    job_id: str
    kind: str
    params: dict[str, Any]
    state: JobState = field(default=JobState.QUEUED)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    progress: list[JobProgressEntry] = field(default_factory=list)
    result: Any = None
    error: str | None = None

    def transition(self, to_state: JobState) -> None:
        """Perform a guarded state transition. Raises InvalidJobTransition on illegal moves."""
        allowed = VALID_TRANSITIONS.get(self.state, set())
        if to_state not in allowed:
            raise InvalidJobTransition(self.state, to_state)
        object.__setattr__(self, "state", to_state)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def add_progress(self, message: str, percent: float | None = None) -> None:
        """Append a progress entry (append-only)."""
        self.progress.append(
            JobProgressEntry(
                timestamp=datetime.now(UTC),
                message=message,
                percent=percent,
            )
        )


class JobStore:
    """Thread-safe in-memory job registry. Single-process only."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}
        self._counter: int = 0

    def create(self, kind: str, params: dict[str, Any] | None = None) -> Job:
        """Create a new job in QUEUED state and return it."""
        with self._lock:
            self._counter += 1
            job_id = f"job_{self._counter:08d}"
            job = Job(job_id=job_id, kind=kind, params=params or {})
            self._jobs[job_id] = job
            return job

    def get(self, job_id: str) -> Job | None:
        """Return the job with the given id, or None if not found."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, state: JobState | None = None) -> list[Job]:
        """Return all jobs sorted by (created_at, job_id), optionally filtered by state."""
        with self._lock:
            jobs = list(self._jobs.values())
        if state is not None:
            jobs = [j for j in jobs if j.state == state]
        return sorted(jobs, key=lambda j: (j.created_at, j.job_id))

    def mark_running(self, job_id: str) -> Job:
        """Transition a job to RUNNING. Raises InvalidJobTransition if not allowed."""
        with self._lock:
            job = self._jobs[job_id]
            job.transition(JobState.RUNNING)
            return job

    def mark_succeeded(self, job_id: str, result: Any = None) -> Job:
        """Transition a job to SUCCEEDED and optionally set result."""
        with self._lock:
            job = self._jobs[job_id]
            job.transition(JobState.SUCCEEDED)
            object.__setattr__(job, "result", result)
            return job

    def mark_failed(self, job_id: str, error: str) -> Job:
        """Transition a job to FAILED and record the error message."""
        with self._lock:
            job = self._jobs[job_id]
            job.transition(JobState.FAILED)
            object.__setattr__(job, "error", error)
            return job

    def cancel(self, job_id: str) -> Job:
        """Cancel a job. Raises JobNotCancellable if already in a terminal state."""
        with self._lock:
            job = self._jobs[job_id]
            if job.state in TERMINAL_STATES:
                raise JobNotCancellable(job_id, job.state)
            job.transition(JobState.CANCELLED)
            return job

    def append_progress(self, job_id: str, message: str, percent: float | None = None) -> Job:
        """Append a progress entry to the job."""
        with self._lock:
            job = self._jobs[job_id]
            job.add_progress(message=message, percent=percent)
            return job

    def clear(self) -> None:
        """Reset the store (for testing only)."""
        with self._lock:
            self._jobs.clear()
            self._counter = 0


# Module-level singleton — imported by api_jobs.py and tests.
_store: JobStore = JobStore()


def get_job_store() -> JobStore:
    """Return the module-level JobStore singleton."""
    return _store
