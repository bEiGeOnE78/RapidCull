"""FR-040: Pure unit tests for Job state machine transitions.

Covers all 25 state-pair combinations: legal ones succeed, illegal ones raise
InvalidJobTransition. Also covers JobStore.cancel() rejecting terminal jobs.
Also covers Job frozen-dataclass immutability (B1).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from rapidcull.jobs import (
    VALID_TRANSITIONS,
    InvalidJobTransition,
    Job,
    JobNotCancellable,
    JobState,
    JobStore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(state: JobState = JobState.QUEUED) -> Job:
    """Create a minimal Job in the given state (bypasses store)."""
    job = Job(job_id="job_00000001", kind="test", params={})
    # Drive to the desired state via valid transitions.
    _drive_to(job, state)
    return job


_DRIVE_PATH: dict[JobState, list[JobState]] = {
    JobState.QUEUED: [],
    JobState.RUNNING: [JobState.RUNNING],
    JobState.SUCCEEDED: [JobState.RUNNING, JobState.SUCCEEDED],
    JobState.FAILED: [JobState.RUNNING, JobState.FAILED],
    JobState.CANCELLED: [JobState.CANCELLED],  # from QUEUED
}


def _drive_to(job: Job, target: JobState) -> None:
    for s in _drive_path(job.state, target):
        job.transition(s)


def _drive_path(start: JobState, target: JobState) -> list[JobState]:
    """Return the shortest legal transition sequence from start to target."""
    if start == target:
        return []
    if target in VALID_TRANSITIONS.get(start, set()):
        return [target]
    # QUEUED -> RUNNING -> terminal
    if start == JobState.QUEUED and target in {
        JobState.SUCCEEDED,
        JobState.FAILED,
    }:
        return [JobState.RUNNING, target]
    return []


# ---------------------------------------------------------------------------
# Legal transition tests
# ---------------------------------------------------------------------------


class TestLegalTransitions:
    def test_queued_to_running(self) -> None:
        job = _make_job(JobState.QUEUED)
        job.transition(JobState.RUNNING)
        assert job.state == JobState.RUNNING

    def test_queued_to_cancelled(self) -> None:
        job = _make_job(JobState.QUEUED)
        job.transition(JobState.CANCELLED)
        assert job.state == JobState.CANCELLED

    def test_running_to_succeeded(self) -> None:
        job = _make_job(JobState.RUNNING)
        job.transition(JobState.SUCCEEDED)
        assert job.state == JobState.SUCCEEDED

    def test_running_to_failed(self) -> None:
        job = _make_job(JobState.RUNNING)
        job.transition(JobState.FAILED)
        assert job.state == JobState.FAILED

    def test_running_to_cancelled(self) -> None:
        job = _make_job(JobState.RUNNING)
        job.transition(JobState.CANCELLED)
        assert job.state == JobState.CANCELLED


# ---------------------------------------------------------------------------
# Illegal transition tests (all 20 illegal pairs)
# ---------------------------------------------------------------------------


class TestIllegalTransitions:
    @pytest.mark.parametrize(
        ("from_state", "to_state"),
        [
            # QUEUED cannot go to terminal non-CANCELLED states or stay at QUEUED
            (JobState.QUEUED, JobState.QUEUED),
            (JobState.QUEUED, JobState.SUCCEEDED),
            (JobState.QUEUED, JobState.FAILED),
            # RUNNING cannot loop or go back to QUEUED
            (JobState.RUNNING, JobState.QUEUED),
            (JobState.RUNNING, JobState.RUNNING),
            # SUCCEEDED is a sink
            (JobState.SUCCEEDED, JobState.QUEUED),
            (JobState.SUCCEEDED, JobState.RUNNING),
            (JobState.SUCCEEDED, JobState.SUCCEEDED),
            (JobState.SUCCEEDED, JobState.FAILED),
            (JobState.SUCCEEDED, JobState.CANCELLED),
            # FAILED is a sink
            (JobState.FAILED, JobState.QUEUED),
            (JobState.FAILED, JobState.RUNNING),
            (JobState.FAILED, JobState.SUCCEEDED),
            (JobState.FAILED, JobState.FAILED),
            (JobState.FAILED, JobState.CANCELLED),
            # CANCELLED is a sink
            (JobState.CANCELLED, JobState.QUEUED),
            (JobState.CANCELLED, JobState.RUNNING),
            (JobState.CANCELLED, JobState.SUCCEEDED),
            (JobState.CANCELLED, JobState.FAILED),
            (JobState.CANCELLED, JobState.CANCELLED),
        ],
    )
    def test_invalid_transition_raises(self, from_state: JobState, to_state: JobState) -> None:
        job = _make_job(from_state)
        with pytest.raises(InvalidJobTransition) as exc_info:
            job.transition(to_state)
        assert exc_info.value.from_state == from_state
        assert exc_info.value.to_state == to_state


# ---------------------------------------------------------------------------
# Terminal-state sink tests
# ---------------------------------------------------------------------------


class TestTerminalStateSinks:
    @pytest.mark.parametrize(
        "terminal",
        [JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED],
    )
    def test_terminal_states_accept_no_transitions(self, terminal: JobState) -> None:
        job = _make_job(terminal)
        for target in JobState:
            with pytest.raises(InvalidJobTransition):
                job.transition(target)


# ---------------------------------------------------------------------------
# Progress entry tests
# ---------------------------------------------------------------------------


class TestProgressEntries:
    def test_progress_entries_append_in_order(self) -> None:
        job = _make_job()
        job.add_progress("step 1", percent=10.0)
        job.add_progress("step 2", percent=50.0)
        job.add_progress("step 3")
        assert len(job.progress) == 3
        assert job.progress[0].message == "step 1"
        assert job.progress[1].message == "step 2"
        assert job.progress[2].message == "step 3"
        assert job.progress[0].percent == pytest.approx(10.0)
        assert job.progress[2].percent is None

    def test_empty_progress_on_new_job(self) -> None:
        job = _make_job()
        assert job.progress == []


# ---------------------------------------------------------------------------
# JobStore.cancel rejects terminal jobs
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Job frozen-dataclass immutability tests (B1)
# ---------------------------------------------------------------------------


class TestJobImmutability:
    def test_direct_state_assignment_raises_frozen_instance_error(self) -> None:
        """Directly setting job.state must raise FrozenInstanceError."""
        job = _make_job(JobState.QUEUED)
        with pytest.raises(FrozenInstanceError):
            job.state = JobState.RUNNING  # type: ignore[misc]

    def test_direct_result_assignment_raises_frozen_instance_error(self) -> None:
        """Directly setting job.result must raise FrozenInstanceError."""
        job = _make_job(JobState.QUEUED)
        with pytest.raises(FrozenInstanceError):
            job.result = {"count": 1}  # type: ignore[misc]

    def test_direct_error_assignment_raises_frozen_instance_error(self) -> None:
        """Directly setting job.error must raise FrozenInstanceError."""
        job = _make_job(JobState.QUEUED)
        with pytest.raises(FrozenInstanceError):
            job.error = "boom"  # type: ignore[misc]

    def test_guarded_transition_still_works_on_frozen_job(self) -> None:
        """The transition() method must still succeed via object.__setattr__."""
        job = _make_job(JobState.QUEUED)
        job.transition(JobState.RUNNING)
        assert job.state == JobState.RUNNING

    def test_add_progress_still_works_on_frozen_job(self) -> None:
        """The add_progress() method must still append to the progress list."""
        job = _make_job(JobState.QUEUED)
        job.add_progress("step", percent=50.0)
        assert len(job.progress) == 1
        assert job.progress[0].message == "step"


class TestJobStoreCancelTerminal:
    def test_cancel_succeeded_raises_not_cancellable(self) -> None:
        store = JobStore()
        job = store.create(kind="test")
        store.mark_running(job.job_id)
        store.mark_succeeded(job.job_id)
        with pytest.raises(JobNotCancellable) as exc_info:
            store.cancel(job.job_id)
        assert exc_info.value.job_id == job.job_id
        assert exc_info.value.state == JobState.SUCCEEDED

    def test_cancel_failed_raises_not_cancellable(self) -> None:
        store = JobStore()
        job = store.create(kind="test")
        store.mark_running(job.job_id)
        store.mark_failed(job.job_id, error="something went wrong")
        with pytest.raises(JobNotCancellable):
            store.cancel(job.job_id)

    def test_cancel_already_cancelled_raises_not_cancellable(self) -> None:
        store = JobStore()
        job = store.create(kind="test")
        store.cancel(job.job_id)
        with pytest.raises(JobNotCancellable):
            store.cancel(job.job_id)
