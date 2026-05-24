from __future__ import annotations

import pytest

from rapidcull.collections import Collection
from rapidcull.query_grammar import parse_query


@pytest.fixture
def sample_metadata() -> dict[str, dict[str, str | int | float | bool | None | list[str]]]:
    """5-10 images with realistic EXIF-like metadata."""
    return {
        "img_001": {
            "person": ["alice", "bob"],
            "date": "2024-01-15",
            "camera": "LeicaQ2",
            "lens": "LeicaSummilux28mm",
            "iso": 400,
            "fnumber": 2.8,
            "focal": 28.0,
            "keyword": ["portrait", "studio"],
        },
        "img_002": {
            "person": ["charlie"],
            "date": "2024-02-20",
            "camera": "NikonZf",
            "lens": "NikkorZ50mm",
            "iso": 800,
            "fnumber": 2.0,
            "focal": 50.0,
            "keyword": ["portrait", "outdoor"],
        },
        "img_003": {
            "person": ["alice"],
            "date": "2024-03-10",
            "camera": "CanonR5",
            "lens": "CanonRF85mm",
            "iso": 200,
            "fnumber": 1.4,
            "focal": 85.0,
            "keyword": ["landscape", "sunset"],
        },
        "img_004": {
            "person": [],
            "date": "2024-01-25",
            "camera": "LeicaQ2",
            "lens": "LeicaSummilux28mm",
            "iso": 600,
            "fnumber": 2.8,
            "focal": 28.0,
            "keyword": ["architecture", "blurred"],
        },
        "img_005": {
            "person": ["bob", "charlie"],
            "date": "2024-04-05",
            "camera": "SonyA7R5",
            "lens": "SonyFE24-70mm",
            "iso": 500,
            "fnumber": 4.0,
            "focal": 50.0,
            "keyword": ["group", "event"],
        },
        "img_006": {
            "person": ["alice", "bob", "charlie"],
            "date": "2024-05-12",
            "camera": "NikonZf",
            "lens": "NikkorZ35mm",
            "iso": 320,
            "fnumber": 2.0,
            "focal": 35.0,
            "keyword": ["portrait", "studio", "group"],
        },
        "img_007": {
            "person": ["david"],
            "date": "2024-06-01",
            "camera": "CanonR5",
            "lens": "CanonRF24-70mm",
            "iso": 1000,
            "fnumber": 5.6,
            "focal": 70.0,
            "keyword": ["landscape"],
        },
        "img_008": {
            "person": ["alice"],
            "date": "2024-02-14",
            "camera": "LeicaM11",
            "lens": "LeicaSummicron35mm",
            "iso": 100,
            "fnumber": 2.0,
            "focal": 35.0,
            "keyword": ["street", "bw"],
        },
    }


@pytest.fixture
def collection(sample_metadata) -> Collection:
    """Create a test collection from sample metadata."""
    return Collection.from_metadata(
        collection_id="test_collection",
        name="Test Photo Collection",
        metadata_dict=sample_metadata,
    )


@pytest.mark.integration
@pytest.mark.fr
def test_collection_exact_match_single_value(collection: Collection) -> None:
    """Test exact match on single-value field (camera)."""
    parse_result = parse_query("camera=LeicaQ2")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="camera=LeicaQ2")

    assert result.total_count == 8
    assert len(result.matching_ids) == 2
    assert "img_001" in result.matching_ids
    assert "img_004" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_exact_match_multi_value_person(collection: Collection) -> None:
    """Test exact match on multi-value field (person)."""
    parse_result = parse_query("person=alice")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="person=alice")

    assert result.total_count == 8
    assert len(result.matching_ids) == 4
    assert "img_001" in result.matching_ids
    assert "img_003" in result.matching_ids
    assert "img_006" in result.matching_ids
    assert "img_008" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_multi_value_keyword_contains(collection: Collection) -> None:
    """Test pattern match on multi-value keyword field."""
    parse_result = parse_query("keyword~portrait")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="keyword~portrait")

    assert result.total_count == 8
    assert len(result.matching_ids) == 3
    assert "img_001" in result.matching_ids
    assert "img_002" in result.matching_ids
    assert "img_006" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_numeric_comparison_iso_greater_than(collection: Collection) -> None:
    """Test numeric comparison on iso field."""
    parse_result = parse_query("iso>400")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="iso>400")

    assert result.total_count == 8
    # iso > 400: img_002=800, img_004=600, img_005=500, img_007=1000 (img_006=320 is NOT >400)
    assert len(result.matching_ids) == 4
    assert "img_002" in result.matching_ids
    assert "img_004" in result.matching_ids
    assert "img_005" in result.matching_ids
    assert "img_007" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_date_range_comparison(collection: Collection) -> None:
    """Test date range comparison."""
    parse_result = parse_query("date>=2024-03-01")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="date>=2024-03-01")

    assert result.total_count == 8
    # Dates >= 2024-03-01: img_003, img_005, img_006, img_007
    assert len(result.matching_ids) == 4
    assert "img_003" in result.matching_ids
    assert "img_005" in result.matching_ids
    assert "img_006" in result.matching_ids
    assert "img_007" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_boolean_and_composition(collection: Collection) -> None:
    """Test AND boolean composition of two conditions."""
    parse_result = parse_query("person=alice AND iso>400")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="person=alice AND iso>400")

    assert result.total_count == 8
    # alice: img_001, img_003, img_006, img_008
    # iso > 400: img_002, img_004, img_005, img_007
    # intersection: img_001 (iso=400 is not >400, so none)
    assert len(result.matching_ids) == 0


@pytest.mark.integration
@pytest.mark.fr
def test_collection_boolean_or_composition(collection: Collection) -> None:
    """Test OR boolean composition of two conditions."""
    parse_result = parse_query("person=charlie OR iso>800")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="person=charlie OR iso>800")

    assert result.total_count == 8
    # person=charlie: img_002, img_005, img_006
    # iso > 800: img_007 (iso=1000)
    # union: img_002, img_005, img_006, img_007
    assert len(result.matching_ids) == 4
    assert "img_002" in result.matching_ids
    assert "img_005" in result.matching_ids
    assert "img_006" in result.matching_ids
    assert "img_007" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_negation_not_blurred(collection: Collection) -> None:
    """Test negation with NOT operator."""
    parse_result = parse_query("NOT keyword=blurred")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="NOT keyword=blurred")

    assert result.total_count == 8
    # keyword=blurred: img_004
    # NOT keyword=blurred: all except img_004
    assert len(result.matching_ids) == 7
    assert "img_004" not in result.matching_ids
    assert "img_001" in result.matching_ids
    assert "img_002" in result.matching_ids
    assert "img_003" in result.matching_ids
    assert "img_005" in result.matching_ids
    assert "img_006" in result.matching_ids
    assert "img_007" in result.matching_ids
    assert "img_008" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_empty_result_no_matches(collection: Collection) -> None:
    """Test query that returns no matches."""
    parse_result = parse_query("person=nonexistent")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="person=nonexistent")

    assert result.total_count == 8
    assert len(result.matching_ids) == 0


@pytest.mark.integration
@pytest.mark.fr
def test_collection_full_result_all_match(collection: Collection) -> None:
    """Test query that matches all records."""
    parse_result = parse_query("iso>0")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(parse_result.expression, query_text="iso>0")

    assert result.total_count == 8
    assert len(result.matching_ids) == 8
    # All images should be in results
    for image_id in [f"img_{i:03d}" for i in range(1, 9)]:
        assert image_id in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_query_result_contains_metadata(collection: Collection) -> None:
    """Test that QueryResult contains expected metadata."""
    parse_result = parse_query("camera=CanonR5")
    assert parse_result.ok
    assert parse_result.expression is not None

    query_text = "camera=CanonR5"
    result = collection.query(parse_result.expression, query_text=query_text)

    assert result.query_expression_text == query_text
    assert result.total_count == 8
    assert len(result.matching_ids) == 2
    assert "img_003" in result.matching_ids
    assert "img_007" in result.matching_ids


@pytest.mark.integration
@pytest.mark.fr
def test_collection_complex_boolean_expression(collection: Collection) -> None:
    """Test complex nested boolean expression."""
    parse_result = parse_query("(person=alice OR person=bob) AND NOT keyword=blurred")
    assert parse_result.ok
    assert parse_result.expression is not None

    result = collection.query(
        parse_result.expression,
        query_text="(person=alice OR person=bob) AND NOT keyword=blurred",
    )

    assert result.total_count == 8
    # person=alice: img_001, img_003, img_006, img_008
    # person=bob: img_001, img_005, img_006
    # union: img_001, img_003, img_005, img_006, img_008
    # NOT blurred: excludes img_004
    # intersection: img_001, img_003, img_005, img_006, img_008 (all already exclude img_004)
    assert len(result.matching_ids) == 5
    assert "img_001" in result.matching_ids
    assert "img_003" in result.matching_ids
    assert "img_005" in result.matching_ids
    assert "img_006" in result.matching_ids
    assert "img_008" in result.matching_ids
    assert "img_004" not in result.matching_ids
