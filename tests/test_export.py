"""Tests for export functionality."""

import json
from pathlib import Path

import pytest

from nuggets.models import Episode, Nugget, NuggetType


class TestMarkdownExport:
    """Tests for Markdown export."""

    def test_format_episode(self):
        """Format episode as Markdown."""
        from nuggets.export.markdown import format_for_markdown

        episode = Episode(
            id="test-123",
            title="Test Episode",
            source_name="Test Show",
            source_type="youtube",
            summary="A test summary.",
            nuggets=[
                Nugget(content="Test insight", type=NuggetType.INSIGHT, importance=4),
                Nugget(content="Test quote", type=NuggetType.QUOTE, importance=3, stars=2),
            ],
        )

        md = format_for_markdown(episode)

        assert "# Test Episode" in md
        assert "Test Show" in md
        assert "Test insight" in md
        assert "Test quote" in md
        assert "⭐⭐" in md  # 2 stars

    def test_format_with_metadata(self):
        """Include metadata in Markdown."""
        from nuggets.export.markdown import format_for_markdown

        episode = Episode(
            id="test-123",
            title="Test Episode",
            source_name="Test Show",
            source_type="youtube",
            summary="A test summary.",
            duration_minutes=65,
            guests=["Alice", "Bob"],
            tags=["health", "science"],
            nuggets=[],
        )

        md = format_for_markdown(episode)

        assert "1h 5min" in md
        assert "Alice, Bob" in md
        assert "`#health`" in md
        assert "`#science`" in md

    def test_export_to_file(self, tmp_path):
        """Export episode to file."""
        from nuggets.export.markdown import export_to_markdown

        episode = Episode(
            id="test-123",
            title="Test Episode",
            source_name="Test Show",
            source_type="youtube",
            summary="A test summary.",
            nuggets=[],
        )

        output = tmp_path / "test.md"
        result = export_to_markdown(episode, output)

        assert result == output
        assert output.exists()
        assert "# Test Episode" in output.read_text()


class TestCollectionExport:
    """Tests for collection export."""

    def test_format_collection(self):
        """Format collection as Markdown."""
        from nuggets.export.collection import format_collection_markdown

        nuggets = [
            {"content": "First nugget", "type": "insight", "stars": 3, "source_name": "Show A", "date": "2024-01-15"},
            {"content": "Second nugget", "type": "quote", "stars": 2, "source_name": "Show B", "date": "2024-01-16"},
        ]

        md = format_collection_markdown(nuggets, "My Collection")

        assert "# My Collection" in md
        assert "First nugget" in md
        assert "Second nugget" in md
        assert "⭐⭐⭐" in md

    def test_format_empty_collection(self):
        """Handle empty collection."""
        from nuggets.export.collection import format_collection_markdown

        md = format_collection_markdown([], "Empty")

        assert "# Empty" in md
        assert "0 nuggets" in md
        assert "No nuggets found" in md

    def test_format_grouped(self):
        """Format collection grouped by topic."""
        from nuggets.export.collection import format_collection_markdown

        nuggets = [
            {"content": "Sleep tip", "type": "insight", "topic": "sleep", "source_name": "A", "date": "2024-01-15"},
            {"content": "Productivity tip", "type": "insight", "topic": "productivity", "source_name": "B", "date": "2024-01-15"},
        ]

        md = format_collection_markdown(nuggets, "Grouped", group_by="topic")

        assert "## productivity" in md
        assert "## sleep" in md

    def test_format_grouped_by_source(self):
        """Format collection grouped by source."""
        from nuggets.export.collection import format_collection_markdown

        nuggets = [
            {"content": "Tip 1", "type": "insight", "source_name": "Huberman Lab", "date": "2024-01-15"},
            {"content": "Tip 2", "type": "insight", "source_name": "Tim Ferriss", "date": "2024-01-15"},
        ]

        md = format_collection_markdown(nuggets, "By Source", group_by="source_name")

        assert "## Huberman Lab" in md
        assert "## Tim Ferriss" in md

    def test_export_to_file(self, tmp_path):
        """Export collection to file."""
        from nuggets.export.collection import export_collection_markdown

        nuggets = [
            {"content": "Test", "type": "insight", "source_name": "Test", "date": "2024-01-15"},
        ]

        output = tmp_path / "collection.md"
        result = export_collection_markdown(nuggets, output, "Test Collection")

        assert result == output
        assert output.exists()
        assert "# Test Collection" in output.read_text()

    def test_export_creates_directories(self, tmp_path):
        """Export creates parent directories."""
        from nuggets.export.collection import export_collection_markdown

        nuggets = [{"content": "Test", "type": "insight", "source_name": "Test", "date": "2024-01-15"}]

        output = tmp_path / "nested" / "dir" / "collection.md"
        result = export_collection_markdown(nuggets, output, "Test")

        assert result == output
        assert output.exists()
