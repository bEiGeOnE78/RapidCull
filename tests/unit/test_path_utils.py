"""Unit tests for path normalization utility (FR-046)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.path_utils import normalize_path


class TestNormalizePathBasic:
    def test_string_path_returns_resolved_path(self, tmp_path: Path) -> None:
        target = tmp_path / "file.jpg"
        result = normalize_path(str(target))
        assert result == target.resolve()

    def test_path_object_returns_resolved_path(self, tmp_path: Path) -> None:
        target = tmp_path / "subdir"
        result = normalize_path(target)
        assert result == target.resolve()

    def test_returns_path_instance(self, tmp_path: Path) -> None:
        result = normalize_path(tmp_path / "x")
        assert isinstance(result, Path)

    def test_no_base_dir_allows_any_path(self) -> None:
        result = normalize_path("/etc/passwd")
        assert result == Path("/etc/passwd")


class TestNormalizePathWithBaseDir:
    def test_path_inside_base_dir_allowed(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        base.mkdir()
        target = base / "img.jpg"
        result = normalize_path(target, base_dir=base)
        assert result == target.resolve()

    def test_base_dir_itself_allowed(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        base.mkdir()
        result = normalize_path(base, base_dir=base)
        assert result == base.resolve()

    def test_traversal_attack_raises_value_error(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        base.mkdir()
        traversal = base / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="outside the allowed base directory"):
            normalize_path(traversal, base_dir=base)

    def test_sibling_dir_raises_value_error(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        base.mkdir()
        sibling = tmp_path / "other"
        sibling.mkdir()
        with pytest.raises(ValueError, match="outside the allowed base directory"):
            normalize_path(sibling / "file.jpg", base_dir=base)

    def test_absolute_escape_path_raises_value_error(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        base.mkdir()
        with pytest.raises(ValueError):
            normalize_path("/etc/shadow", base_dir=base)

    def test_nested_path_inside_base_allowed(self, tmp_path: Path) -> None:
        base = tmp_path / "photos"
        nested = base / "2024" / "January"
        nested.mkdir(parents=True)
        target = nested / "img.raw"
        result = normalize_path(target, base_dir=base)
        assert result == target.resolve()
