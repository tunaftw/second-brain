"""Tests for YouTube transcription."""

import json
from pathlib import Path

import pytest

from nuggets.transcribe.youtube import save_raw_youtube, extract_video_id


class TestExtractVideoId:
    """Tests for extract_video_id."""

    def test_standard_url(self):
        """Standard watch URL."""
        assert extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        """Short youtu.be URL."""
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


class TestSaveRawYoutube:
    """Tests for save_raw_youtube."""

    def test_saves_to_correct_path(self, tmp_path):
        """Saves raw data to correct library path."""
        result = {
            "video_id": "abc123",
            "title": "Test Video",
            "channel": "Test Channel",
            "upload_date": "20240115",
            "duration": 3600,
            "url": "https://youtube.com/watch?v=abc123",
            "transcript": "Hello world",
            "transcript_source": "youtube_captions",
            "has_timestamps": True,
        }

        filepath = save_raw_youtube(result, base_path=tmp_path)

        assert filepath.exists()
        assert "raw/youtube/test-channel" in str(filepath)
        assert "2024-01-15-abc123.json" in str(filepath)

        # Verify content
        data = json.loads(filepath.read_text())
        assert data["video_id"] == "abc123"
        assert data["transcript"] == "Hello world"


class TestSpeakerParsing:
    """Tests for speaker parsing from metadata."""

    def test_parse_guest_with_pattern(self):
        """Parse guest from 'with Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Sleep Tips with Dr. Matt Walker") == "Dr. Matt Walker"

    def test_parse_guest_colon_pattern(self):
        """Parse guest from 'Guest: Topic' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Andy Galpin: How to Build Muscle") == "Andy Galpin"

    def test_parse_guest_number_pattern(self):
        """Parse guest from '#Number Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("#1892 David Goggins") == "David Goggins"

    def test_parse_host_from_channel(self):
        """Get known host from channel name."""
        from nuggets.transcribe.youtube import get_host_from_channel

        assert get_host_from_channel("Huberman Lab") == "Andrew Huberman"
        assert get_host_from_channel("Unknown Channel") is None
