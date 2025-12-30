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
