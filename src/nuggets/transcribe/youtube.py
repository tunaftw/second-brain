"""YouTube transcription for Podcast Nuggets.

This module handles fetching transcripts from YouTube videos,
either via YouTube captions (preferred) or by downloading and
transcribing with Whisper (fallback).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

if TYPE_CHECKING:
    from collections.abc import Callable


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL.

    Args:
        url: YouTube URL in various formats.

    Returns:
        11-character video ID.

    Raises:
        ValueError: If video ID cannot be extracted.

    Examples:
        >>> extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata using yt-dlp.

    Args:
        video_id: YouTube video ID.

    Returns:
        Dict with title, channel, duration, upload_date, chapters.
    """
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://youtube.com/watch?v={video_id}",
            download=False,
        )

        # Extract chapters if available
        chapters = []
        raw_chapters = info.get("chapters") or []
        for ch in raw_chapters:
            chapters.append({
                "title": ch.get("title", ""),
                "start_time": ch.get("start_time", 0),
                "end_time": ch.get("end_time"),
            })

        return {
            "title": info.get("title"),
            "channel": info.get("channel"),
            "duration": info.get("duration"),
            "upload_date": info.get("upload_date"),
            "chapters": chapters,
        }


def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    if seconds is None:
        return "Unknown"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_chapters(chapters: list[dict]) -> str:
    """Format chapters list to readable text.

    Args:
        chapters: List of chapter dicts with title, start_time, end_time.

    Returns:
        Formatted string with chapters.
    """
    if not chapters:
        return ""

    lines = ["", "CHAPTERS:", "-" * 40]
    for ch in chapters:
        timestamp = format_duration(ch.get("start_time", 0))
        title = ch.get("title", "")
        lines.append(f"  [{timestamp}] {title}")
    lines.append("-" * 40)
    lines.append("")

    return "\n".join(lines)


def get_youtube_transcript(
    video_id: str,
    languages: list[str] | None = None,
) -> tuple[str | None, bool]:
    """Fetch transcript from YouTube captions.

    Args:
        video_id: YouTube video ID.
        languages: Preferred languages in order (default: ['sv', 'en']).

    Returns:
        Tuple of (transcript_text, has_timestamps).
        transcript_text is None if no captions available.
    """
    if languages is None:
        languages = ["sv", "en"]

    try:
        # youtube-transcript-api 1.x uses fetch() method
        fetcher = YouTubeTranscriptApi()

        # Try to list available transcripts to find preferred language
        transcript_list = fetcher.list(video_id)

        # Try preferred languages first
        transcript = None
        for lang in languages:
            try:
                transcript = transcript_list.find_transcript([lang]).fetch()
                break
            except Exception:
                continue

        # If no preferred language found, try any available
        if transcript is None:
            try:
                # Get first available transcript
                available = list(transcript_list)
                if available:
                    transcript = available[0].fetch()
            except Exception:
                pass

        if transcript is None:
            return None, False

        # Format transcript with timestamps
        lines = []
        for snippet in transcript.snippets:
            start = int(snippet.start)
            mins, secs = divmod(start, 60)
            hours, mins = divmod(mins, 60)
            if hours:
                timestamp = f"{hours:02d}:{mins:02d}:{secs:02d}"
            else:
                timestamp = f"{mins:02d}:{secs:02d}"
            lines.append(f"[{timestamp}] {snippet.text}")

        return "\n".join(lines), True

    except Exception:
        return None, False


def download_audio(
    video_id: str,
    output_dir: Path | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> Path:
    """Download audio from YouTube video.

    Args:
        video_id: YouTube video ID.
        output_dir: Directory for downloaded files (default: data/audio).
        progress_callback: Optional callback for progress updates.

    Returns:
        Path to downloaded audio file.
    """
    if output_dir is None:
        output_dir = Path("data/audio")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    if progress_callback:
        progress_callback("Downloading audio...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://youtube.com/watch?v={video_id}"])

    return output_dir / f"{video_id}.mp3"


def download_and_transcribe(
    video_id: str,
    model: str = "large-v3",
    language: str = "sv",
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """Fallback: download audio and transcribe with Whisper.

    Args:
        video_id: YouTube video ID.
        model: Whisper model to use.
        language: Language code for transcription.
        progress_callback: Optional callback for progress updates.

    Returns:
        Transcribed text.
    """
    from .whisper import transcribe

    # Download audio
    audio_path = download_audio(video_id, progress_callback=progress_callback)

    # Transcribe with Whisper
    if progress_callback:
        progress_callback("Transcribing with Whisper...")

    return transcribe(audio_path, model=model, language=language)


def process_youtube_video(
    url: str,
    force_whisper: bool = False,
    languages: list[str] | None = None,
    whisper_model: str = "large-v3",
    whisper_language: str = "sv",
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    """Process a YouTube video: fetch metadata and transcript.

    This is the main entry point for YouTube processing.

    Args:
        url: YouTube video URL.
        force_whisper: Skip YouTube captions and use Whisper.
        languages: Preferred caption languages.
        whisper_model: Whisper model for fallback transcription.
        whisper_language: Language for Whisper transcription.
        progress_callback: Optional callback for progress updates.

    Returns:
        Dict with video_id, title, channel, duration, url,
        transcript, transcript_source, has_timestamps.
    """
    if progress_callback:
        progress_callback("Extracting video ID...")

    video_id = extract_video_id(url)

    if progress_callback:
        progress_callback("Fetching video metadata...")

    metadata = get_video_metadata(video_id)

    # Try YouTube captions first (unless force_whisper)
    if not force_whisper:
        if progress_callback:
            progress_callback("Fetching YouTube captions...")

        transcript, has_timestamps = get_youtube_transcript(video_id, languages)

        if transcript:
            return {
                **metadata,
                "video_id": video_id,
                "url": url,
                "transcript": transcript,
                "transcript_source": "youtube_captions",
                "has_timestamps": has_timestamps,
            }

    # Fallback to Whisper
    if progress_callback:
        progress_callback("No captions available, using Whisper fallback...")

    transcript = download_and_transcribe(
        video_id,
        model=whisper_model,
        language=whisper_language,
        progress_callback=progress_callback,
    )

    return {
        **metadata,
        "video_id": video_id,
        "url": url,
        "transcript": transcript,
        "transcript_source": "whisper",
        "has_timestamps": False,
    }


def save_transcript(
    result: dict,
    output_dir: Path | None = None,
) -> Path:
    """Save transcript to file.

    Args:
        result: Result dict from process_youtube_video.
        output_dir: Directory for transcripts (default: data/transcripts/youtube).

    Returns:
        Path to saved transcript file.
    """
    if output_dir is None:
        output_dir = Path("data/transcripts/youtube")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: channel-date-video_id.txt
    channel = result.get("channel", "unknown")
    # Sanitize channel name for filename
    channel_safe = re.sub(r"[^\w\s-]", "", channel).strip().replace(" ", "-").lower()

    upload_date = result.get("upload_date", "unknown")
    if upload_date and len(upload_date) == 8:
        # Format: YYYYMMDD -> YYYY-MM-DD
        date_formatted = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        date_formatted = upload_date or "unknown"

    video_id = result["video_id"]
    filename = f"{channel_safe}-{date_formatted}-{video_id}.txt"
    filepath = output_dir / filename

    # Build header
    header_lines = [
        "=" * 60,
        f"Title: {result.get('title', 'Unknown')}",
        f"Channel: {result.get('channel', 'Unknown')}",
        f"Duration: {format_duration(result.get('duration'))}",
        f"URL: {result.get('url', '')}",
        f"Video ID: {video_id}",
        f"Transcript source: {result.get('transcript_source', 'unknown')}",
        "=" * 60,
    ]

    # Add chapters if available
    chapters = result.get("chapters", [])
    if chapters:
        header_lines.append(format_chapters(chapters))
    else:
        header_lines.append("")

    header = "\n".join(header_lines)

    # Write file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(result["transcript"])
        f.write("\n")

    return filepath
