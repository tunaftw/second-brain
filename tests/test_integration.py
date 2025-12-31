"""Integration tests for the full workflow."""

import tempfile
from pathlib import Path

import pytest


class TestDataModels:
    """Test data model hierarchy."""

    @pytest.mark.integration
    def test_segment_nugget_hierarchy(self):
        """Segments contain nuggets with proper IDs."""
        from nuggets.models import Segment, Nugget, NuggetType

        segment = Segment(
            id="segment-ep1-0",
            episode_id="ep1",
            raw_segment="Test transcript...",
            topic="productivity",
            theme_name="Morning Routines",
        )

        nugget = Nugget(
            content="Test insight",
            type=NuggetType.INSIGHT,
            segment_id=segment.id,
            headline="Test headline",
        )

        assert nugget.segment_id == segment.id
        assert segment.id.startswith("segment-")
        assert "ep1" in nugget.segment_id

    @pytest.mark.integration
    def test_nugget_flexible_content_levels(self):
        """Nuggets can have varying content levels."""
        from nuggets.models import Nugget, NuggetType

        # Full nugget
        full_nugget = Nugget(
            content="Full content",
            type=NuggetType.INSIGHT,
            headline="Headline",
            condensed="Condensed version",
            quote="Quotable quote",
        )
        assert full_nugget.headline is not None
        assert full_nugget.condensed is not None
        assert full_nugget.quote is not None

        # Quote-only nugget
        quote_nugget = Nugget(
            content="The obstacle is the way",
            type=NuggetType.QUOTE,
            headline="Stoic wisdom",
            quote="The obstacle is the way",
        )
        assert quote_nugget.condensed is None
        assert quote_nugget.quote is not None
