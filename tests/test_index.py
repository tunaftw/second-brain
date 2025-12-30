"""Tests for library index models and IndexManager."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from nuggets.index import IndexEntry, LibraryIndex, IndexManager
from nuggets.models import NuggetType


class TestIndexEntry:
    """Tests for IndexEntry model."""

    def test_create_entry(self):
        """IndexEntry can be created with required fields."""
        entry = IndexEntry(
            nugget_id="youtube-2024-01-15-abc123-0",
            episode_id="youtube-2024-01-15-abc123",
            content="Morning sunlight sets circadian rhythm",
            type=NuggetType.INSIGHT,
            source_name="Huberman Lab",
            source_type="youtube",
            date=datetime(2024, 1, 15),
        )
        assert entry.nugget_id == "youtube-2024-01-15-abc123-0"
        assert entry.episode_id == "youtube-2024-01-15-abc123"
        assert entry.content == "Morning sunlight sets circadian rhythm"
        assert entry.type == NuggetType.INSIGHT
        assert entry.source_name == "Huberman Lab"
        assert entry.source_type == "youtube"
        assert entry.date == datetime(2024, 1, 15)

    def test_create_entry_with_optional_fields(self):
        """IndexEntry supports optional fields."""
        entry = IndexEntry(
            nugget_id="youtube-2024-01-15-abc123-0",
            episode_id="youtube-2024-01-15-abc123",
            content="Get 10 minutes of morning sunlight",
            type=NuggetType.ACTION,
            source_name="Huberman Lab",
            source_type="youtube",
            date=datetime(2024, 1, 15),
            topic="sleep",
            wisdom_type="technique",
            stars=3,
            importance=5,
            speaker="Andrew Huberman",
            timestamp="12:34",
        )
        assert entry.topic == "sleep"
        assert entry.wisdom_type == "technique"
        assert entry.stars == 3
        assert entry.importance == 5
        assert entry.speaker == "Andrew Huberman"
        assert entry.timestamp == "12:34"

    def test_entry_optional_fields_default_none(self):
        """Optional fields default to None."""
        entry = IndexEntry(
            nugget_id="test-0",
            episode_id="test",
            content="Test",
            type=NuggetType.INSIGHT,
            source_name="Test",
            source_type="youtube",
            date=datetime(2024, 1, 1),
        )
        assert entry.topic is None
        assert entry.wisdom_type is None
        assert entry.stars is None
        assert entry.importance is None
        assert entry.speaker is None
        assert entry.timestamp is None


class TestLibraryIndex:
    """Tests for LibraryIndex model."""

    def test_empty_index(self):
        """LibraryIndex can be created empty."""
        index = LibraryIndex(
            entries=[],
            total_nuggets=0,
            total_episodes=0,
            sources=[],
            last_updated=datetime(2024, 1, 1, 12, 0, 0),
        )
        assert index.entries == []
        assert index.total_nuggets == 0
        assert index.total_episodes == 0
        assert index.sources == []
        assert index.last_updated == datetime(2024, 1, 1, 12, 0, 0)

    def test_index_with_entries(self):
        """LibraryIndex can hold multiple entries."""
        entry1 = IndexEntry(
            nugget_id="ep1-0",
            episode_id="ep1",
            content="First nugget",
            type=NuggetType.INSIGHT,
            source_name="Podcast A",
            source_type="podcast",
            date=datetime(2024, 1, 1),
        )
        entry2 = IndexEntry(
            nugget_id="ep2-0",
            episode_id="ep2",
            content="Second nugget",
            type=NuggetType.ACTION,
            source_name="Channel B",
            source_type="youtube",
            date=datetime(2024, 1, 2),
        )
        index = LibraryIndex(
            entries=[entry1, entry2],
            total_nuggets=2,
            total_episodes=2,
            sources=["Podcast A", "Channel B"],
            last_updated=datetime(2024, 1, 2, 12, 0, 0),
        )
        assert len(index.entries) == 2
        assert index.total_nuggets == 2
        assert index.total_episodes == 2
        assert "Podcast A" in index.sources
        assert "Channel B" in index.sources


class TestIndexManager:
    """Tests for IndexManager class."""

    def test_init_default_path(self):
        """IndexManager uses default path."""
        manager = IndexManager()
        assert manager.base_path == Path("data")

    def test_init_custom_path(self):
        """IndexManager accepts custom base path."""
        manager = IndexManager(base_path=Path("/custom/path"))
        assert manager.base_path == Path("/custom/path")

    def test_build_index_empty(self, tmp_path):
        """build_index returns empty index when no episodes exist."""
        # Create empty analysis directories
        (tmp_path / "analysis" / "youtube").mkdir(parents=True)
        (tmp_path / "analysis" / "podcasts").mkdir(parents=True)
        (tmp_path / "library").mkdir(parents=True)

        manager = IndexManager(base_path=tmp_path)
        index = manager.build_index()

        assert index.total_nuggets == 0
        assert index.total_episodes == 0
        assert index.entries == []
        assert index.sources == []

    def test_build_index_from_episode(self, tmp_path):
        """build_index extracts nuggets from episode files."""
        # Create analysis directory
        channel_dir = tmp_path / "analysis" / "youtube" / "huberman-lab"
        channel_dir.mkdir(parents=True)
        (tmp_path / "library").mkdir(parents=True)

        # Create a sample episode file
        episode_data = {
            "id": "youtube-2024-01-15-abc123",
            "source_type": "youtube",
            "source_name": "Huberman Lab",
            "title": "Sleep Episode",
            "date": "2024-01-15T00:00:00",
            "url": "https://youtube.com/watch?v=abc123",
            "duration_minutes": 60,
            "guests": [],
            "summary": "Sleep tips",
            "nuggets": [
                {
                    "content": "Get morning sunlight",
                    "type": "action",
                    "timestamp": "12:34",
                    "importance": 5,
                    "speaker": "Andrew Huberman",
                    "topic": "sleep",
                    "wisdom_type": "technique",
                    "stars": 3,
                },
                {
                    "content": "Caffeine has 8-hour half-life",
                    "type": "insight",
                    "timestamp": "25:00",
                    "importance": 4,
                },
            ],
            "tags": ["sleep", "health"],
        }
        episode_file = channel_dir / "2024-01-15-abc123.json"
        episode_file.write_text(json.dumps(episode_data))

        manager = IndexManager(base_path=tmp_path)
        index = manager.build_index()

        assert index.total_episodes == 1
        assert index.total_nuggets == 2
        assert len(index.entries) == 2
        assert "Huberman Lab" in index.sources

        # Check first entry
        entry = index.entries[0]
        assert entry.episode_id == "youtube-2024-01-15-abc123"
        assert entry.content == "Get morning sunlight"
        assert entry.type == NuggetType.ACTION
        assert entry.source_name == "Huberman Lab"
        assert entry.source_type == "youtube"
        assert entry.topic == "sleep"
        assert entry.wisdom_type == "technique"
        assert entry.stars == 3
        assert entry.importance == 5
        assert entry.speaker == "Andrew Huberman"
        assert entry.timestamp == "12:34"

    def test_save_and_load_index(self, tmp_path):
        """Can save and load index to/from JSON."""
        (tmp_path / "library").mkdir(parents=True)

        entry = IndexEntry(
            nugget_id="test-ep-0",
            episode_id="test-ep",
            content="Test nugget",
            type=NuggetType.INSIGHT,
            source_name="Test Source",
            source_type="youtube",
            date=datetime(2024, 1, 15),
            topic="test-topic",
            stars=2,
        )
        index = LibraryIndex(
            entries=[entry],
            total_nuggets=1,
            total_episodes=1,
            sources=["Test Source"],
            last_updated=datetime(2024, 1, 15, 12, 0, 0),
        )

        manager = IndexManager(base_path=tmp_path)
        manager.save_index(index)

        # Verify file exists
        index_path = tmp_path / "library" / "index.json"
        assert index_path.exists()

        # Load and verify
        loaded_index = manager.load_index()
        assert loaded_index.total_nuggets == 1
        assert loaded_index.total_episodes == 1
        assert len(loaded_index.entries) == 1
        assert loaded_index.entries[0].content == "Test nugget"
        assert loaded_index.entries[0].topic == "test-topic"
        assert loaded_index.entries[0].stars == 2

    def test_load_index_not_found(self, tmp_path):
        """load_index returns None when file doesn't exist."""
        (tmp_path / "library").mkdir(parents=True)
        manager = IndexManager(base_path=tmp_path)
        assert manager.load_index() is None

    def test_search_by_query(self, tmp_path):
        """search filters by text query in content."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="Morning sunlight helps sleep",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="Exercise improves mood",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=2,
            total_episodes=1,
            sources=["Source"],
            last_updated=datetime(2024, 1, 1),
        )

        results = manager.search(index, query="sunlight")
        assert len(results) == 1
        assert "sunlight" in results[0].content.lower()

    def test_search_by_topic(self, tmp_path):
        """search filters by topic."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="Sleep tip",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="sleep",
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="Exercise tip",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="fitness",
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=2,
            total_episodes=1,
            sources=["Source"],
            last_updated=datetime(2024, 1, 1),
        )

        results = manager.search(index, topic="sleep")
        assert len(results) == 1
        assert results[0].topic == "sleep"

    def test_search_by_stars(self, tmp_path):
        """search filters by minimum stars."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="Unrated nugget",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                stars=None,
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="One star",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                stars=1,
            ),
            IndexEntry(
                nugget_id="3",
                episode_id="ep1",
                content="Three stars",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                stars=3,
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=3,
            total_episodes=1,
            sources=["Source"],
            last_updated=datetime(2024, 1, 1),
        )

        results = manager.search(index, stars=2)
        assert len(results) == 1
        assert results[0].stars == 3

    def test_search_by_source(self, tmp_path):
        """search filters by source name."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="From Huberman",
                type=NuggetType.INSIGHT,
                source_name="Huberman Lab",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep2",
                content="From Tim Ferriss",
                type=NuggetType.INSIGHT,
                source_name="Tim Ferriss Show",
                source_type="podcast",
                date=datetime(2024, 1, 2),
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=2,
            total_episodes=2,
            sources=["Huberman Lab", "Tim Ferriss Show"],
            last_updated=datetime(2024, 1, 2),
        )

        results = manager.search(index, source="Huberman Lab")
        assert len(results) == 1
        assert results[0].source_name == "Huberman Lab"

    def test_search_by_year(self, tmp_path):
        """search filters by year."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="From 2023",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2023, 6, 15),
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep2",
                content="From 2024",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 3, 20),
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=2,
            total_episodes=2,
            sources=["Source"],
            last_updated=datetime(2024, 3, 20),
        )

        results = manager.search(index, year=2024)
        assert len(results) == 1
        assert results[0].date.year == 2024

    def test_search_by_nugget_type(self, tmp_path):
        """search filters by nugget type."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="An insight",
                type=NuggetType.INSIGHT,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="An action item",
                type=NuggetType.ACTION,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
            IndexEntry(
                nugget_id="3",
                episode_id="ep1",
                content="A quote",
                type=NuggetType.QUOTE,
                source_name="Source",
                source_type="youtube",
                date=datetime(2024, 1, 1),
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=3,
            total_episodes=1,
            sources=["Source"],
            last_updated=datetime(2024, 1, 1),
        )

        results = manager.search(index, nugget_type=NuggetType.ACTION)
        assert len(results) == 1
        assert results[0].type == NuggetType.ACTION

    def test_search_combined_filters(self, tmp_path):
        """search combines multiple filters."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="Sleep action from Huberman",
                type=NuggetType.ACTION,
                source_name="Huberman Lab",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="sleep",
                stars=3,
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="Sleep insight from Huberman",
                type=NuggetType.INSIGHT,
                source_name="Huberman Lab",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="sleep",
                stars=2,
            ),
            IndexEntry(
                nugget_id="3",
                episode_id="ep2",
                content="Fitness action from Tim",
                type=NuggetType.ACTION,
                source_name="Tim Ferriss",
                source_type="podcast",
                date=datetime(2024, 1, 2),
                topic="fitness",
                stars=3,
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=3,
            total_episodes=2,
            sources=["Huberman Lab", "Tim Ferriss"],
            last_updated=datetime(2024, 1, 2),
        )

        # Combine topic + type + stars
        results = manager.search(
            index, topic="sleep", nugget_type=NuggetType.ACTION, stars=3
        )
        assert len(results) == 1
        assert results[0].nugget_id == "1"

    def test_get_stats(self, tmp_path):
        """get_stats returns statistics about the index."""
        manager = IndexManager(base_path=tmp_path)
        entries = [
            IndexEntry(
                nugget_id="1",
                episode_id="ep1",
                content="Insight 1",
                type=NuggetType.INSIGHT,
                source_name="Huberman Lab",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="sleep",
                stars=3,
            ),
            IndexEntry(
                nugget_id="2",
                episode_id="ep1",
                content="Action 1",
                type=NuggetType.ACTION,
                source_name="Huberman Lab",
                source_type="youtube",
                date=datetime(2024, 1, 1),
                topic="sleep",
            ),
            IndexEntry(
                nugget_id="3",
                episode_id="ep2",
                content="Quote 1",
                type=NuggetType.QUOTE,
                source_name="Tim Ferriss",
                source_type="podcast",
                date=datetime(2023, 6, 15),
                topic="productivity",
                stars=2,
            ),
        ]
        index = LibraryIndex(
            entries=entries,
            total_nuggets=3,
            total_episodes=2,
            sources=["Huberman Lab", "Tim Ferriss"],
            last_updated=datetime(2024, 1, 1),
        )

        stats = manager.get_stats(index)

        assert stats["total_nuggets"] == 3
        assert stats["total_episodes"] == 2
        assert stats["total_sources"] == 2
        assert stats["by_type"]["insight"] == 1
        assert stats["by_type"]["action"] == 1
        assert stats["by_type"]["quote"] == 1
        assert stats["by_topic"]["sleep"] == 2
        assert stats["by_topic"]["productivity"] == 1
        assert stats["by_source"]["Huberman Lab"] == 2
        assert stats["by_source"]["Tim Ferriss"] == 1
        assert stats["by_year"][2024] == 2
        assert stats["by_year"][2023] == 1
        assert stats["starred_count"] == 2
