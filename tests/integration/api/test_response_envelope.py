"""Tests for the standard response envelope (FR-039).

Verifies that every /api/v1/* endpoint returns the uniform
{ok, data|error} envelope shape.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import _collections, app
from rapidcull.collections import Collection

TEST_COLLECTION_ID = "env-col-001"

_METADATA: dict[str, dict[str, str | int | float | bool | None | list[str]]] = {
    "img_001": {
        "camera": "LeicaQ2",
        "iso": 400,
        "fnumber": 2.8,
        "focal": 28.0,
        "date": "2024-01-15",
        "person": [],
        "keyword": [],
        "lens": "Summilux28",
    },
}


@pytest.fixture(autouse=True)
def setup_and_teardown_registry() -> pytest.Generator[None, None, None]:
    collection = Collection.from_metadata(
        collection_id=TEST_COLLECTION_ID,
        name="Envelope Test Collection",
        metadata_dict=_METADATA,  # type: ignore[arg-type]
    )
    _collections[TEST_COLLECTION_ID] = collection
    yield
    _collections.pop(TEST_COLLECTION_ID, None)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _query_url(collection_id: str = TEST_COLLECTION_ID) -> str:
    return f"/api/v1/collections/{collection_id}/query"


class TestSuccessEnvelope:
    def test_ok_true_and_data_present(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "camera=LeicaQ2"})
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert "data" in body
        assert "error" not in body or body.get("error") is None

    def test_data_contains_expected_fields(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "camera=LeicaQ2"})
        body = response.json()
        data = body["data"]
        assert "matching_ids" in data
        assert "total_count" in data
        assert "query_expression" in data

    def test_meta_field_present(self, client: TestClient) -> None:
        """meta may be null but the key must be present in the envelope."""
        response = client.post(_query_url(), json={"query_text": "camera=LeicaQ2"})
        body = response.json()
        assert "meta" in body


class TestParseErrorEnvelope:
    def test_ok_false_on_parse_error(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "badfield=foo"})
        assert response.status_code == 400
        body = response.json()
        assert body["ok"] is False

    def test_error_code_is_query_parse_error(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "badfield=foo"})
        body = response.json()
        assert body["error"]["code"] == "QUERY_PARSE_ERROR"

    def test_error_message_is_non_empty(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "badfield=foo"})
        body = response.json()
        assert isinstance(body["error"]["message"], str)
        assert len(body["error"]["message"]) > 0

    def test_no_data_key_on_error(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "badfield=foo"})
        body = response.json()
        # ok=false responses must have "error"; "data" must be absent or null
        assert "error" in body
        assert body.get("data") is None or "data" not in body


class TestNotFoundEnvelope:
    def test_ok_false_on_unknown_collection(self, client: TestClient) -> None:
        response = client.post(_query_url("unknown-col"), json={"query_text": "camera=LeicaQ2"})
        assert response.status_code == 404
        body = response.json()
        assert body["ok"] is False

    def test_error_code_is_collection_not_found(self, client: TestClient) -> None:
        response = client.post(_query_url("unknown-col"), json={"query_text": "camera=LeicaQ2"})
        body = response.json()
        assert body["error"]["code"] == "COLLECTION_NOT_FOUND"

    def test_error_message_references_collection_id(self, client: TestClient) -> None:
        response = client.post(_query_url("unknown-col"), json={"query_text": "camera=LeicaQ2"})
        body = response.json()
        assert "unknown-col" in body["error"]["message"]


class TestValidationErrorEnvelope:
    def test_missing_query_text_returns_422(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={})
        assert response.status_code == 422

    def test_validation_error_code(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={})
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_details_lists_offending_field(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={})
        body = response.json()
        details = body["error"]["details"]
        assert isinstance(details, list)
        assert len(details) > 0
        # At least one error should reference "query_text"
        field_names = [loc for entry in details for loc in (entry.get("loc") or [])]
        assert "query_text" in field_names
