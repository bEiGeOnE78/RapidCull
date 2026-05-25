"""Stage 3 — End-to-end tests for job orchestration (FR-038..041).

Two E2E scenarios:
1. Happy path: full lifecycle create -> running -> succeeded -> list -> cancel-rejects.
2. Envelope consistency: shared assert_envelope helper verifies every endpoint returns
   the standard {ok, data|error} shape at the top level.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import _collections, app
from rapidcull.collections import Collection
from rapidcull.jobs import get_job_store

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_METADATA: dict[str, dict[str, str | int | float | bool | None | list[str]]] = {
    "img_001": {
        "camera": "LeicaQ2",
        "iso": 400,
        "fnumber": 2.8,
        "focal": 28.0,
        "date": "2024-01-15",
        "person": ["alice"],
        "keyword": ["portrait"],
        "lens": "Summilux28",
    },
}

TEST_COLLECTION_ID = "e2e-col-001"


@pytest.fixture(autouse=True)
def reset_stores() -> pytest.Generator[None, None, None]:
    """Reset both the JobStore and the collection registry before each test."""
    get_job_store().clear()
    collection = Collection.from_metadata(
        collection_id=TEST_COLLECTION_ID,
        name="E2E Test Collection",
        metadata_dict=_METADATA,  # type: ignore[arg-type]
    )
    _collections[TEST_COLLECTION_ID] = collection
    yield
    get_job_store().clear()
    _collections.pop(TEST_COLLECTION_ID, None)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Shared assertion helper
# ---------------------------------------------------------------------------


def assert_envelope(response_body: dict[str, Any], *, expected_ok: bool) -> None:
    """Assert the top-level envelope structure is present and ok matches expectation."""
    assert "ok" in response_body, "Envelope missing 'ok' key"
    assert isinstance(response_body["ok"], bool), "'ok' must be a bool"
    assert (
        response_body["ok"] is expected_ok
    ), f"Expected ok={expected_ok}, got ok={response_body['ok']}"
    if expected_ok:
        assert "data" in response_body, "Success envelope missing 'data' key"
        assert "meta" in response_body, "Success envelope missing 'meta' key"
        assert "error" not in response_body, "Success envelope must not contain 'error'"
    else:
        assert "error" in response_body, "Error envelope missing 'error' key"
        error = response_body["error"]
        assert "code" in error, "Error envelope missing 'error.code'"
        assert "message" in error, "Error envelope missing 'error.message'"
        assert "details" in error, "Error envelope missing 'error.details'"
        assert isinstance(error["code"], str) and error["code"], "error.code must be non-empty str"
        assert (
            isinstance(error["message"], str) and error["message"]
        ), "error.message must be non-empty str"


# ---------------------------------------------------------------------------
# E2E Scenario 1: Happy path — full job lifecycle
# ---------------------------------------------------------------------------


class TestHappyPathLifecycle:
    """Full lifecycle: create -> GET (queued) -> mark running -> mark succeeded
    -> GET (terminal) -> list -> cancel rejects."""

    def test_full_lifecycle(self, client: TestClient) -> None:
        store = get_job_store()

        # --- Step 1: Create a job via POST /jobs ---
        create_resp = client.post(
            "/api/v1/jobs",
            json={"kind": "ingest", "params": {"source_dir": "/photos/2026"}},
        )
        assert create_resp.status_code == 201
        create_body = create_resp.json()
        assert_envelope(create_body, expected_ok=True)
        job_id = create_body["data"]["job_id"]
        assert job_id.startswith("job_"), f"Unexpected job_id format: {job_id}"
        assert create_body["data"]["state"] == "queued"

        # --- Step 2: GET /jobs/{id} — verify queued state ---
        get_queued_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert get_queued_resp.status_code == 200
        get_queued_body = get_queued_resp.json()
        assert_envelope(get_queued_body, expected_ok=True)
        assert get_queued_body["data"]["state"] == "queued"
        assert get_queued_body["data"]["job_id"] == job_id

        # --- Step 3: Append progress + mark running via store ---
        store.append_progress(job_id, "Starting ingest", percent=0.0)
        store.mark_running(job_id)

        # --- Step 4: GET progress — verify entry exists ---
        progress_resp = client.get(f"/api/v1/jobs/{job_id}/progress")
        assert progress_resp.status_code == 200
        progress_body = progress_resp.json()
        assert_envelope(progress_body, expected_ok=True)
        entries = progress_body["data"]["entries"]
        assert len(entries) == 1
        assert entries[0]["message"] == "Starting ingest"
        assert entries[0]["percent"] == pytest.approx(0.0)
        assert entries[0]["timestamp"].endswith("Z")

        # --- Step 5: GET /jobs/{id} — verify running state ---
        get_running_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert get_running_resp.status_code == 200
        assert get_running_resp.json()["data"]["state"] == "running"

        # --- Step 6: Mark succeeded via store ---
        store.append_progress(job_id, "Ingest complete", percent=100.0)
        store.mark_succeeded(job_id, result={"files_processed": 42})

        # --- Step 7: GET /jobs/{id} — verify terminal state ---
        get_done_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert get_done_resp.status_code == 200
        get_done_body = get_done_resp.json()
        assert_envelope(get_done_body, expected_ok=True)
        done_data = get_done_body["data"]
        assert done_data["state"] == "succeeded"
        assert done_data["result"] == {"files_processed": 42}
        assert done_data["error"] is None

        # --- Step 8: GET /jobs — list shows the succeeded job ---
        list_resp = client.get("/api/v1/jobs")
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert_envelope(list_body, expected_ok=True)
        job_ids_in_list = [j["job_id"] for j in list_body["data"]["jobs"]]
        assert job_id in job_ids_in_list

        # --- Step 9: DELETE /jobs/{id} on terminal job — must return 409 ---
        cancel_resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert cancel_resp.status_code == 409
        cancel_body = cancel_resp.json()
        assert_envelope(cancel_body, expected_ok=False)
        assert cancel_body["error"]["code"] == "JOB_NOT_CANCELLABLE"


# ---------------------------------------------------------------------------
# E2E Scenario 2: Envelope consistency across all endpoints
# ---------------------------------------------------------------------------


class TestEnvelopeConsistency:
    """Every endpoint must return a structurally consistent envelope (ok at top level)."""

    def test_post_jobs_success_envelope(self, client: TestClient) -> None:
        resp = client.post("/api/v1/jobs", json={"kind": "ingest"})
        assert resp.status_code == 201
        assert_envelope(resp.json(), expected_ok=True)

    def test_get_jobs_list_envelope(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert_envelope(resp.json(), expected_ok=True)

    def test_get_job_by_id_found_envelope(self, client: TestClient) -> None:
        create_resp = client.post("/api/v1/jobs", json={"kind": "proxy_gen"})
        job_id = create_resp.json()["data"]["job_id"]
        resp = client.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        assert_envelope(resp.json(), expected_ok=True)

    def test_get_job_by_id_not_found_envelope(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/job_99999999")
        assert resp.status_code == 404
        assert_envelope(resp.json(), expected_ok=False)

    def test_delete_job_success_envelope(self, client: TestClient) -> None:
        create_resp = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = create_resp.json()["data"]["job_id"]
        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        assert_envelope(resp.json(), expected_ok=True)

    def test_delete_terminal_job_error_envelope(self, client: TestClient) -> None:
        store = get_job_store()
        create_resp = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = create_resp.json()["data"]["job_id"]
        store.mark_running(job_id)
        store.mark_succeeded(job_id)
        resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 409
        assert_envelope(resp.json(), expected_ok=False)

    def test_get_job_progress_envelope(self, client: TestClient) -> None:
        create_resp = client.post("/api/v1/jobs", json={"kind": "ingest"})
        job_id = create_resp.json()["data"]["job_id"]
        resp = client.get(f"/api/v1/jobs/{job_id}/progress")
        assert resp.status_code == 200
        assert_envelope(resp.json(), expected_ok=True)

    def test_collection_query_success_envelope(self, client: TestClient) -> None:
        resp = client.post(
            f"/api/v1/collections/{TEST_COLLECTION_ID}/query",
            json={"query_text": "camera=LeicaQ2"},
        )
        assert resp.status_code == 200
        assert_envelope(resp.json(), expected_ok=True)

    def test_collection_query_parse_error_envelope(self, client: TestClient) -> None:
        resp = client.post(
            f"/api/v1/collections/{TEST_COLLECTION_ID}/query",
            json={"query_text": "AND camera=LeicaQ2"},
        )
        assert resp.status_code == 400
        assert_envelope(resp.json(), expected_ok=False)

    def test_collection_query_not_found_envelope(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/collections/no-such-col/query",
            json={"query_text": "camera=LeicaQ2"},
        )
        assert resp.status_code == 404
        assert_envelope(resp.json(), expected_ok=False)

    def test_post_jobs_malformed_body_envelope(self, client: TestClient) -> None:
        """Missing 'kind' field triggers validation — must come back as error envelope."""
        resp = client.post("/api/v1/jobs", json={})
        assert resp.status_code == 422
        assert_envelope(resp.json(), expected_ok=False)
