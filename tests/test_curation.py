"""Tests for curation utilities."""

import json
from pathlib import Path

import pytest

from nuggets.curation import set_nugget_stars, get_unrated_nuggets


class TestSetNuggetStars:
    """Tests for set_nugget_stars."""

    def test_set_stars_success(self, tmp_path):
        """Successfully set stars on a nugget."""
        # Create episode file
        analysis_dir = tmp_path / "analysis" / "youtube" / "test"
        analysis_dir.mkdir(parents=True)

        episode = {
            "id": "youtube-2024-01-15-abc123",
            "nuggets": [
                {"content": "First", "type": "insight"},
                {"content": "Second", "type": "quote"},
            ],
        }
        episode_file = analysis_dir / "2024-01-15-abc123.json"
        episode_file.write_text(json.dumps(episode), encoding="utf-8")

        # Set stars
        result = set_nugget_stars(
            "youtube-2024-01-15-abc123",
            nugget_index=0,
            stars=3,
            base_path=tmp_path,
        )

        assert result is True

        # Verify saved
        saved = json.loads(episode_file.read_text())
        assert saved["nuggets"][0]["stars"] == 3
        assert "stars" not in saved["nuggets"][1]

    def test_set_stars_not_found(self, tmp_path):
        """Returns False if episode not found."""
        (tmp_path / "analysis").mkdir(parents=True)

        result = set_nugget_stars(
            "nonexistent-episode",
            nugget_index=0,
            stars=2,
            base_path=tmp_path,
        )

        assert result is False

    def test_set_stars_invalid_index(self, tmp_path):
        """Returns False if nugget index out of range."""
        analysis_dir = tmp_path / "analysis" / "youtube" / "test"
        analysis_dir.mkdir(parents=True)

        episode = {
            "id": "youtube-2024-01-15-abc123",
            "nuggets": [{"content": "Only one", "type": "insight"}],
        }
        episode_file = analysis_dir / "2024-01-15-abc123.json"
        episode_file.write_text(json.dumps(episode), encoding="utf-8")

        result = set_nugget_stars(
            "youtube-2024-01-15-abc123",
            nugget_index=5,  # Out of range
            stars=2,
            base_path=tmp_path,
        )

        assert result is False


class TestGetUnratedNuggets:
    """Tests for get_unrated_nuggets."""

    def test_returns_unrated(self, tmp_path):
        """Returns nuggets without stars."""
        # Create library index
        (tmp_path / "library").mkdir(parents=True)

        from nuggets.index import IndexEntry, LibraryIndex, IndexManager

        entries = [
            IndexEntry(
                nugget_id="ep1-0",
                episode_id="ep1",
                content="Rated",
                type="insight",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                stars=3,
            ),
            IndexEntry(
                nugget_id="ep1-1",
                episode_id="ep1",
                content="Unrated",
                type="quote",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                stars=None,
            ),
        ]
        index = LibraryIndex(entries=entries, total_nuggets=2)

        manager = IndexManager(base_path=tmp_path)
        manager.save_index(index)

        # Get unrated
        unrated = get_unrated_nuggets(base_path=tmp_path)

        assert len(unrated) == 1
        assert unrated[0]["content"] == "Unrated"

    def test_returns_empty_when_all_rated(self, tmp_path):
        """Returns empty list when all nuggets are rated."""
        (tmp_path / "library").mkdir(parents=True)

        from nuggets.index import IndexEntry, LibraryIndex, IndexManager

        entries = [
            IndexEntry(
                nugget_id="ep1-0",
                episode_id="ep1",
                content="Rated",
                type="insight",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                stars=2,
            ),
        ]
        index = LibraryIndex(entries=entries, total_nuggets=1)

        manager = IndexManager(base_path=tmp_path)
        manager.save_index(index)

        unrated = get_unrated_nuggets(base_path=tmp_path)
        assert len(unrated) == 0

    def test_sorted_by_importance(self, tmp_path):
        """Unrated nuggets are sorted by importance descending."""
        (tmp_path / "library").mkdir(parents=True)

        from nuggets.index import IndexEntry, LibraryIndex, IndexManager

        entries = [
            IndexEntry(
                nugget_id="ep1-0",
                episode_id="ep1",
                content="Low importance",
                type="insight",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                importance=2,
            ),
            IndexEntry(
                nugget_id="ep1-1",
                episode_id="ep1",
                content="High importance",
                type="insight",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                importance=5,
            ),
        ]
        index = LibraryIndex(entries=entries, total_nuggets=2)

        manager = IndexManager(base_path=tmp_path)
        manager.save_index(index)

        unrated = get_unrated_nuggets(base_path=tmp_path)

        assert len(unrated) == 2
        assert unrated[0]["content"] == "High importance"
        assert unrated[1]["content"] == "Low importance"
