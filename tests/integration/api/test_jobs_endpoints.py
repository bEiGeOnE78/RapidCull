"""FR-041: HTTP integration tests for /api/v1/jobs endpoints.

Uses FastAPI TestClient with an autouse fixture that clears the in-memory
JobStore between tests to ensure isolation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import app
from rapidcull.jobs import get_job_store


@pytest.fixture(autouse=True)
def reset_job_store() -> pytest.Generator[None, None, None]:
    """Clear the in-memory JobStore before each test."""
    get_job_store().clear()
    yield
    get_job_store().clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Create job
# ---------------------------------------------------------------------------


class TestCreateJob:
    def test_post_returns_201_with_ok_envelope(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "ingest"})
        assert response.status_code == 201
        body = response.json()
        assert body["ok"] is True

    def test_created_job_state_is_queued(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "ingest"})
        data = response.json()["data"]
        assert data["state"] == "queued"

    def test_created_job_id_starts_with_job_(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "ingest"})
        data = response.json()["data"]
        assert data["job_id"].startswith("job_")

    def test_created_job_kind_matches_request(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "proxy_gen"})
        data = response.json()["data"]
        assert data["kind"] == "proxy_gen"

    def test_created_job_has_timestamps(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "ingest"})
        data = response.json()["data"]
        assert data["created_at"].endswith("Z")
        assert data["updated_at"].endswith("Z")

    def test_created_job_result_and_error_are_null(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={"kind": "ingest"})
        data = response.json()["data"]
        assert data["result"] is None
        assert data["error"] is None

    def test_missing_kind_returns_422_validation_error(self, client: TestClient) -> None:
        response = client.post("/api/v1/jobs", json={})
        assert response.status_code == 422
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_params_stored_on_job(self, client: TestClient) -> None:
        params = {"source_dir": "/photos/2026", "dry_run": True}
        response = client.post("/api/v1/jobs", json={"kind": "ingest", "params": params})
        data = response.json()["data"]
        assert data["params"] == params


# ---------------------------------------------------------------------------
# Get job
# ---------------------------------------------------------------------------


class TestGetJob:
    def test_get_known_job_returns_200(self, client: TestClient) -> None:
        create_resp = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = create_resp.json()["data"]["job_id"]
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["data"]["job_id"] == job_id

    def test_get_unknown_job_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/jobs/job_99999999")
        assert response.status_code == 404
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "JOB_NOT_FOUND"

    def test_get_unknown_job_message_contains_id(self, client: TestClient) -> None:
        response = client.get("/api/v1/jobs/job_99999999")
        body = response.json()
        assert "job_99999999" in body["error"]["message"]


# ---------------------------------------------------------------------------
# List jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    def test_list_returns_empty_jobs_array_initially(self, client: TestClient) -> None:
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["data"]["jobs"] == []

    def test_list_determinism_three_jobs(self, client: TestClient) -> None:
        """List returns jobs in creation order on repeated calls."""
        ids = []
        for kind in ("ingest", "proxy_gen", "cleanup"):
            r = client.post("/api/v1/jobs", json={"kind": kind})
            ids.append(r.json()["data"]["job_id"])

        for _ in range(3):
            r = client.get("/api/v1/jobs")
            returned_ids = [j["job_id"] for j in r.json()["data"]["jobs"]]
            assert returned_ids == ids

    def test_list_filter_queued_returns_only_queued(self, client: TestClient) -> None:
        # Create two jobs, drive one to RUNNING
        r1 = client.post("/api/v1/jobs", json={"kind": "ingest"})
        r2 = client.post("/api/v1/jobs", json={"kind": "proxy_gen"})
        job_id_1 = r1.json()["data"]["job_id"]

        store = get_job_store()
        store.mark_running(job_id_1)

        r = client.get("/api/v1/jobs?state=queued")
        assert r.status_code == 200
        returned_ids = [j["job_id"] for j in r.json()["data"]["jobs"]]
        assert r2.json()["data"]["job_id"] in returned_ids
        assert job_id_1 not in returned_ids

    def test_list_filter_running(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        get_job_store().mark_running(job_id)

        r2 = client.get("/api/v1/jobs?state=running")
        assert r2.status_code == 200
        ids = [j["job_id"] for j in r2.json()["data"]["jobs"]]
        assert job_id in ids

    def test_list_invalid_state_filter_returns_400(self, client: TestClient) -> None:
        response = client.get("/api/v1/jobs?state=bogus")
        assert response.status_code == 400
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "INVALID_STATE_FILTER"


# ---------------------------------------------------------------------------
# Cancel job
# ---------------------------------------------------------------------------


class TestCancelJob:
    def test_cancel_queued_job_returns_200_cancelled(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]

        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["state"] == "cancelled"

    def test_cancel_running_job_returns_200_cancelled(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        get_job_store().mark_running(job_id)

        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["state"] == "cancelled"

    def test_cancel_succeeded_job_returns_409(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        store = get_job_store()
        store.mark_running(job_id)
        store.mark_succeeded(job_id)

        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 409
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "JOB_NOT_CANCELLABLE"

    def test_cancel_failed_job_returns_409(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        store = get_job_store()
        store.mark_running(job_id)
        store.mark_failed(job_id, error="boom")

        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "JOB_NOT_CANCELLABLE"

    def test_cancel_unknown_job_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/jobs/job_99999999")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "JOB_NOT_FOUND"


# ---------------------------------------------------------------------------
# Progress endpoint
# ---------------------------------------------------------------------------


class TestJobProgress:
    def test_empty_progress_returns_empty_entries(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]

        resp = client.get(f"/api/v1/jobs/{job_id}/progress")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["entries"] == []

    def test_progress_entries_in_append_order(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        store = get_job_store()
        store.append_progress(job_id, "stage 1", percent=10.0)
        store.append_progress(job_id, "stage 2", percent=50.0)
        store.append_progress(job_id, "stage 3")

        resp = client.get(f"/api/v1/jobs/{job_id}/progress")
        entries = resp.json()["data"]["entries"]
        assert len(entries) == 3
        assert entries[0]["message"] == "stage 1"
        assert entries[0]["percent"] == pytest.approx(10.0)
        assert entries[1]["message"] == "stage 2"
        assert entries[2]["message"] == "stage 3"
        assert entries[2]["percent"] is None

    def test_progress_timestamps_iso_z(self, client: TestClient) -> None:
        r = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = r.json()["data"]["job_id"]
        get_job_store().append_progress(job_id, "tick")

        entries = client.get(f"/api/v1/jobs/{job_id}/progress").json()["data"]["entries"]
        assert entries[0]["timestamp"].endswith("Z")

    def test_progress_unknown_job_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/job_99999999/progress")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"]["code"] == "JOB_NOT_FOUND"
