"""Transcription modules for Podcast Nuggets."""

from .youtube import (
    extract_video_id,
    get_video_metadata,
    get_youtube_transcript,
    process_youtube_video,
    save_transcript,
)
from .twitter import (
    extract_tweet_id,
    extract_author,
    fetch_via_jina,
    process_twitter_source,
    save_raw_twitter,
)

__all__ = [
    # YouTube
    "extract_video_id",
    "get_video_metadata",
    "get_youtube_transcript",
    "process_youtube_video",
    "save_transcript",
    # Twitter
    "extract_tweet_id",
    "extract_author",
    "fetch_via_jina",
    "process_twitter_source",
    "save_raw_twitter",
]
