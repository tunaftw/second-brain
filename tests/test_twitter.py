"""Tests for Twitter/X content fetching."""

import json
from pathlib import Path

import pytest

from nuggets.transcribe.twitter import (
    extract_tweet_id,
    extract_author,
    save_raw_twitter,
)


class TestExtractTweetId:
    """Tests for extract_tweet_id."""

    def test_x_url(self):
        """Extract ID from x.com URL."""
        url = "https://x.com/thebeautyofsaas/status/2006104228381721052"
        assert extract_tweet_id(url) == "2006104228381721052"

    def test_twitter_url(self):
        """Extract ID from twitter.com URL."""
        url = "https://twitter.com/user/status/123456789"
        assert extract_tweet_id(url) == "123456789"

    def test_with_query_params(self):
        """Extract ID from URL with query parameters."""
        url = "https://x.com/user/status/999?s=20&t=abc"
        assert extract_tweet_id(url) == "999"

    def test_invalid_url(self):
        """Raise error for invalid URL."""
        with pytest.raises(ValueError, match="Could not extract tweet ID"):
            extract_tweet_id("https://example.com/not-twitter")

    def test_missing_status(self):
        """Raise error for URL without status."""
        with pytest.raises(ValueError, match="Could not extract tweet ID"):
            extract_tweet_id("https://x.com/user")


class TestExtractAuthor:
    """Tests for extract_author."""

    def test_x_url(self):
        """Extract author from x.com URL."""
        url = "https://x.com/thebeautyofsaas/status/123"
        assert extract_author(url) == "thebeautyofsaas"

    def test_twitter_url(self):
        """Extract author from twitter.com URL."""
        url = "https://twitter.com/elonmusk/status/456"
        assert extract_author(url) == "elonmusk"

    def test_invalid_url_returns_unknown(self):
        """Return 'unknown' for invalid URL."""
        assert extract_author("https://example.com/page") == "unknown"


class TestSaveRawTwitter:
    """Tests for save_raw_twitter."""

    def test_saves_to_correct_path(self, tmp_path):
        """Save Twitter content to library structure."""
        result = {
            "tweet_id": "123456",
            "author": "testuser",
            "url": "https://x.com/testuser/status/123456",
            "title": "Test Thread",
            "content": "This is test content",
            "date": "2024-12-31",
            "source": "twitter",
        }

        output_path = save_raw_twitter(result, base_path=tmp_path)

        assert output_path.exists()
        assert "twitter" in str(output_path)
        assert "testuser" in str(output_path)
        assert "123456" in str(output_path)

        # Verify content
        saved = json.loads(output_path.read_text())
        assert saved["content"] == "This is test content"
        assert saved["author"] == "testuser"

    def test_creates_parent_directories(self, tmp_path):
        """Create parent directories if they don't exist."""
        result = {
            "tweet_id": "999",
            "author": "newuser",
            "url": "https://x.com/newuser/status/999",
            "title": "New Thread",
            "content": "Content",
            "date": "2024-12-31",
            "source": "twitter",
        }

        output_path = save_raw_twitter(result, base_path=tmp_path)

        assert output_path.exists()
        assert output_path.parent.exists()


class TestLibraryPathsTwitter:
    """Tests for LibraryPaths Twitter methods."""

    def test_raw_twitter_path(self, tmp_path):
        """Generate correct raw Twitter path."""
        from nuggets.library import LibraryPaths

        paths = LibraryPaths(tmp_path)
        result = paths.raw_twitter("Test User", "2024-12-31", "123456")

        assert result == tmp_path / "raw" / "twitter" / "test-user" / "2024-12-31-123456.json"

    def test_analysis_twitter_path(self, tmp_path):
        """Generate correct analysis Twitter path."""
        from nuggets.library import LibraryPaths

        paths = LibraryPaths(tmp_path)
        result = paths.analysis_twitter("Test User", "2024-12-31", "123456")

        assert result == tmp_path / "analysis" / "twitter" / "test-user" / "2024-12-31-123456.json"
