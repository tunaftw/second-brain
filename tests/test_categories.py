"""Tests for category constants."""

from nuggets.categories import TOPICS, WISDOM_TYPES, is_valid_topic, is_valid_wisdom_type


class TestCategories:
    """Tests for category validation."""

    def test_topics_is_list(self):
        """TOPICS is a non-empty list of strings."""
        assert isinstance(TOPICS, list)
        assert len(TOPICS) > 0
        assert all(isinstance(t, str) for t in TOPICS)

    def test_wisdom_types_is_list(self):
        """WISDOM_TYPES is a non-empty list of strings."""
        assert isinstance(WISDOM_TYPES, list)
        assert len(WISDOM_TYPES) > 0
        assert all(isinstance(t, str) for t in WISDOM_TYPES)

    def test_is_valid_topic(self):
        """is_valid_topic validates known topics."""
        assert is_valid_topic("sleep") is True
        assert is_valid_topic("productivity") is True
        assert is_valid_topic("unknown_topic_xyz") is False

    def test_is_valid_wisdom_type(self):
        """is_valid_wisdom_type validates known types."""
        assert is_valid_wisdom_type("principle") is True
        assert is_valid_wisdom_type("habit") is True
        assert is_valid_wisdom_type("unknown_type_xyz") is False

    def test_topics_are_lowercase(self):
        """All topics are lowercase for consistency."""
        assert all(t == t.lower() for t in TOPICS)

    def test_wisdom_types_are_lowercase(self):
        """All wisdom types are lowercase for consistency."""
        assert all(t == t.lower() for t in WISDOM_TYPES)
