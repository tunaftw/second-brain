"""Tests for library path utilities."""

from pathlib import Path

import pytest

from nuggets.library import LibraryPaths, slugify


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Basic channel name to slug."""
        assert slugify("Huberman Lab") == "huberman-lab"

    def test_special_characters(self):
        """Removes special characters."""
        assert slugify("Tim Ferriss Show!") == "tim-ferriss-show"

    def test_multiple_spaces(self):
        """Handles multiple spaces."""
        assert slugify("The   Joe   Rogan   Experience") == "the-joe-rogan-experience"

    def test_unicode(self):
        """Handles unicode characters."""
        assert slugify("Café Podcast") == "cafe-podcast"


class TestLibraryPaths:
    """Tests for LibraryPaths."""

    def test_default_base_path(self):
        """Default base path is data/."""
        paths = LibraryPaths()
        assert paths.base == Path("data")

    def test_raw_youtube_path(self):
        """Raw YouTube path construction."""
        paths = LibraryPaths()
        result = paths.raw_youtube("Huberman Lab", "2024-01-15", "abc123")
        assert result == Path("data/raw/youtube/huberman-lab/2024-01-15-abc123.json")

    def test_analysis_youtube_path(self):
        """Analysis YouTube path construction."""
        paths = LibraryPaths()
        result = paths.analysis_youtube("Huberman Lab", "2024-01-15", "abc123")
        assert result == Path("data/analysis/youtube/huberman-lab/2024-01-15-abc123.json")

    def test_library_index_path(self):
        """Library index path."""
        paths = LibraryPaths()
        assert paths.library_index == Path("data/library/index.json")

    def test_library_sources_path(self):
        """Library sources path."""
        paths = LibraryPaths()
        assert paths.library_sources == Path("data/library/sources.json")

    def test_library_starred_path(self):
        """Library starred path."""
        paths = LibraryPaths()
        assert paths.library_starred == Path("data/library/starred.json")

    def test_custom_base_path(self):
        """Can use custom base path."""
        paths = LibraryPaths(base=Path("/custom/path"))
        assert paths.base == Path("/custom/path")
        assert paths.library_index == Path("/custom/path/library/index.json")
