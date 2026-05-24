from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import _collections, app
from rapidcull.collections import Collection

TEST_COLLECTION_ID = "test-col-001"

_METADATA: dict[str, dict[str, str | int | float | bool | None | list[str]]] = {
    "img_001": {
        "camera": "LeicaQ2",
        "iso": 400,
        "fnumber": 2.8,
        "focal": 28.0,
        "date": "2024-01-15",
        "person": ["alice", "bob"],
        "keyword": ["portrait"],
        "lens": "Summilux28",
    },
    "img_002": {
        "camera": "NikonZf",
        "iso": 800,
        "fnumber": 2.0,
        "focal": 50.0,
        "date": "2024-02-20",
        "person": ["charlie"],
        "keyword": ["street"],
        "lens": "Nikkor50",
    },
    "img_003": {
        "camera": "LeicaQ2",
        "iso": 1600,
        "fnumber": 1.7,
        "focal": 28.0,
        "date": "2024-03-10",
        "person": [],
        "keyword": ["landscape"],
        "lens": "Summilux28",
    },
}


@pytest.fixture(autouse=True)
def setup_and_teardown_registry() -> pytest.Generator[None, None, None]:
    """Populate the in-memory registry before each test and clean up after."""
    collection = Collection.from_metadata(
        collection_id=TEST_COLLECTION_ID,
        name="Test Collection",
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


class TestValidQuery:
    def test_matching_ids_returned(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "camera=LeicaQ2"})
        assert response.status_code == 200
        body = response.json()
        assert set(body["matching_ids"]) == {"img_001", "img_003"}
        assert body["total_count"] == 3
        assert body["query_expression"] == "camera=LeicaQ2"

    def test_iso_filter_returns_correct_subset(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "iso>400"})
        assert response.status_code == 200
        body = response.json()
        assert set(body["matching_ids"]) == {"img_002", "img_003"}

    def test_no_matches_returns_empty_list(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "camera=Pentax"})
        assert response.status_code == 200
        body = response.json()
        assert body["matching_ids"] == []
        assert body["total_count"] == 3


class TestParseError:
    def test_unknown_field_returns_400(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "badfield=foo"})
        assert response.status_code == 400
        assert "badfield" in response.json()["detail"].lower()

    def test_invalid_syntax_returns_400(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "AND camera=LeicaQ2"})
        assert response.status_code == 400
        assert response.json()["detail"]

    def test_error_message_is_human_readable(self, client: TestClient) -> None:
        response = client.post(_query_url(), json={"query_text": "iso=notanumber"})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert isinstance(detail, str)
        assert len(detail) > 0


class TestCollectionNotFound:
    def test_unknown_collection_returns_404(self, client: TestClient) -> None:
        response = client.post(_query_url("nonexistent-col"), json={"query_text": "camera=LeicaQ2"})
        assert response.status_code == 404
        assert "nonexistent-col" in response.json()["detail"]
