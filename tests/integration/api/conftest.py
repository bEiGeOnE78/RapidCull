"""Shared fixtures for integration/api tests.

Ensures the module-level JobExecutor singleton in api_jobs is torn down after
every test that calls create_app().  Without this, any test that wires an
executor (via create_app(db_path=...)) leaves a live ThreadPoolExecutor running
after the test ends.  Subsequent tests that use the bare module-level `app` and
POST /api/v1/jobs will have their freshly-created job immediately picked up by
the orphaned executor thread, transitioning it to 'failed' before the test can
manually advance its state — causing InvalidJobTransition errors.
"""

from __future__ import annotations

import pytest

from rapidcull.api_jobs import configure_executor, get_executor


@pytest.fixture(autouse=True)
def _teardown_executor() -> pytest.Generator[None, None, None]:
    """Shut down and deregister any JobExecutor wired during the test."""
    yield
    executor = get_executor()
    if executor is not None:
        executor.shutdown(wait=True)
        configure_executor(None)  # type: ignore[arg-type]
