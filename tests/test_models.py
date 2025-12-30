"""Tests for data models."""

import pytest
from nuggets.models import Nugget, NuggetType


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
