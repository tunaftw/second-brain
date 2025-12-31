"""Tests for data models."""

import pytest
from nuggets.models import Nugget, NuggetType


class TestSegment:
    """Tests for Segment model."""

    def test_segment_minimal(self):
        """Segment can be created with minimal fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="This is the raw transcript text...",
            topic="productivity",
            theme_name="Morning Routines",
        )
        assert segment.id == "segment-ep123-0"
        assert segment.topic == "productivity"
        assert segment.full is None  # optional

    def test_segment_with_all_fields(self):
        """Segment supports all optional fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="Raw transcript...",
            full="Edited comprehensive summary...",
            topic="sleep",
            theme_name="Sleep Optimization",
            start_timestamp="01:23:45",
            end_timestamp="01:28:30",
            speakers=["Andrew Huberman", "Matt Walker"],
            primary_speaker="Matt Walker",
            related_segment_ids=["segment-ep456-2", "segment-ep789-1"],
        )
        assert segment.full == "Edited comprehensive summary..."
        assert segment.speakers == ["Andrew Huberman", "Matt Walker"]
        assert len(segment.related_segment_ids) == 2


class TestNugget:
    """Tests for Nugget model."""

    def test_nugget_minimal(self):
        """Nugget can be created with minimal fields."""
        nugget = Nugget(
            content="Test insight",
            type=NuggetType.INSIGHT,
        )
        assert nugget.content == "Test insight"
        assert nugget.type == NuggetType.INSIGHT
        assert nugget.importance == 3  # default

    def test_nugget_with_new_fields(self):
        """Nugget supports topic, wisdom_type, and stars."""
        nugget = Nugget(
            content="Morning sunlight sets circadian rhythm",
            type=NuggetType.INSIGHT,
            topic="sleep",
            wisdom_type="principle",
            stars=3,
        )
        assert nugget.topic == "sleep"
        assert nugget.wisdom_type == "principle"
        assert nugget.stars == 3

    def test_nugget_stars_validation(self):
        """Stars must be 1-3 if set."""
        with pytest.raises(ValueError):
            Nugget(
                content="Test",
                type=NuggetType.INSIGHT,
                stars=5,  # Invalid: must be 1-3
            )

    def test_nugget_stars_optional(self):
        """Stars can be None (unrated)."""
        nugget = Nugget(
            content="Test",
            type=NuggetType.INSIGHT,
            stars=None,
        )
        assert nugget.stars is None

    def test_nugget_hierarchy_fields(self):
        """Nugget supports segment_id and multi-level content."""
        nugget = Nugget(
            content="Legacy field",  # Keep for backwards compat
            type=NuggetType.INSIGHT,
            segment_id="segment-ep123-0",
            headline="Morning sunlight boosts cortisol",
            condensed="Huberman explains that viewing bright light within 30 minutes of waking triggers a cortisol pulse that helps set your circadian rhythm.",
            quote="Get sunlight in your eyes within 30-60 minutes of waking.",
        )
        assert nugget.segment_id == "segment-ep123-0"
        assert nugget.headline == "Morning sunlight boosts cortisol"
        assert nugget.condensed is not None
        assert nugget.quote is not None

    def test_nugget_flexible_levels(self):
        """Not all content levels need to be present."""
        # Quote without full context
        nugget = Nugget(
            content="The obstacle is the way",
            type=NuggetType.QUOTE,
            headline="Stoic wisdom on obstacles",
            quote="The obstacle is the way",
            condensed=None,  # No extra context
        )
        assert nugget.quote == "The obstacle is the way"
        assert nugget.condensed is None
