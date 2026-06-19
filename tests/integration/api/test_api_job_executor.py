"""Integration tests: FR-042 job executor — jobs actually execute."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import create_app
from rapidcull.api_jobs import configure_executor
from rapidcull.jobs import get_job_store
from rapidcull.schema import create_or_validate_schema


def _wait_for_terminal(client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/v1/jobs/{job_id}")
        data = resp.json()["data"]
        if data["state"] in ("succeeded", "failed", "cancelled"):
            return data
        time.sleep(0.05)
    raise TimeoutError(f"Job {job_id} did not reach terminal state within {timeout}s")


@pytest.fixture(autouse=True)
def _clear_job_store() -> pytest.Generator[None, None, None]:
    get_job_store().clear()
    yield
    # Reset global executor after every test so the bare `app` singleton used
    # by other test modules is not affected.
    configure_executor(None)  # type: ignore[arg-type]
    get_job_store().clear()


@pytest.fixture()
def app_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    return TestClient(create_app(db_path=db_path))


@pytest.mark.fr
@pytest.mark.integration
def test_unknown_job_kind_fails(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "bogus_op", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "failed"
    assert "Unknown job kind" in job["error"]


@pytest.mark.fr
@pytest.mark.integration
def test_cluster_faces_job_succeeds(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "cluster_faces", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "succeeded"
    assert job["result"]["person_count"] == 0


@pytest.mark.fr
@pytest.mark.integration
def test_check_consistency_job_succeeds(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "check_consistency", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "succeeded"
    assert job["result"]["issues"] == []


@pytest.mark.fr
@pytest.mark.integration
def test_repair_consistency_job_succeeds(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "repair_consistency", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "succeeded"
    assert job["result"]["fixed_count"] == 0


@pytest.mark.fr
@pytest.mark.integration
def test_rebuild_galleries_index_job_succeeds(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "rebuild_galleries_index", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "succeeded"


@pytest.mark.fr
@pytest.mark.integration
def test_ingest_without_library_root_fails(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "ingest_and_proxy", "params": {}})
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(app_client, job_id)
    assert job["state"] == "failed"
    assert "library_root" in job["error"]


@pytest.mark.fr
@pytest.mark.integration
def test_progress_entries_appended(app_client: TestClient) -> None:
    resp = app_client.post("/api/v1/jobs", json={"kind": "cluster_faces", "params": {}})
    job_id = resp.json()["data"]["job_id"]
    _wait_for_terminal(app_client, job_id)
    progress_resp = app_client.get(f"/api/v1/jobs/{job_id}/progress")
    entries = progress_resp.json()["data"]["entries"]
    assert len(entries) > 0


@pytest.mark.fr
@pytest.mark.integration
def test_two_jobs_both_succeed(app_client: TestClient) -> None:
    j1 = app_client.post("/api/v1/jobs", json={"kind": "cluster_faces", "params": {}}).json()[
        "data"
    ]["job_id"]
    j2 = app_client.post("/api/v1/jobs", json={"kind": "check_consistency", "params": {}}).json()[
        "data"
    ]["job_id"]
    r1 = _wait_for_terminal(app_client, j1)
    r2 = _wait_for_terminal(app_client, j2)
    assert r1["state"] == "succeeded"
    assert r2["state"] == "succeeded"
