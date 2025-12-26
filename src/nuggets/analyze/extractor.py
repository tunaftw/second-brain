"""Claude-based nugget extraction for Podcast Nuggets.

This module uses Claude API to analyze transcripts and extract
valuable nuggets (insights, quotes, actions, etc.).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from nuggets.models import AnalysisResult, Episode, Nugget, NuggetType, SourceType

if TYPE_CHECKING:
    from collections.abc import Callable

# Load environment variables
load_dotenv()

# Prompt template path
PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "extract_nuggets.md"


def load_prompt_template() -> str:
    """Load the extraction prompt template."""
    if PROMPT_TEMPLATE_PATH.exists():
        return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")

    # Fallback minimal prompt if file not found
    return """Extract 5-15 valuable nuggets from this transcript.

Respond with JSON:
{
  "summary": "2-3 sentence summary",
  "guests": [],
  "suggested_tags": [],
  "nuggets": [
    {"content": "...", "type": "insight|quote|action|concept|story", "timestamp": null, "context": null, "importance": 3, "speaker": null}
  ]
}

Transcript:
{transcript}"""


def build_prompt(
    transcript: str,
    source_name: str = "Unknown",
    title: str = "Unknown",
    duration_minutes: int | None = None,
    date: str | None = None,
) -> str:
    """Build the full prompt with transcript and metadata."""
    template = load_prompt_template()

    return template.format(
        source_name=source_name,
        title=title,
        duration=duration_minutes or "Unknown",
        date=date or "Unknown",
        transcript=transcript,
    )


def extract_nuggets(
    transcript: str,
    source_name: str = "Unknown",
    title: str = "Unknown",
    duration_minutes: int | None = None,
    date: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    progress_callback: Callable[[str], None] | None = None,
) -> AnalysisResult:
    """Extract nuggets from a transcript using Claude.

    Args:
        transcript: The full transcript text.
        source_name: Name of the source (channel, podcast name).
        title: Title of the episode/video.
        duration_minutes: Duration in minutes.
        date: Date string.
        model: Claude model to use.
        progress_callback: Optional callback for progress updates.

    Returns:
        AnalysisResult with summary, guests, tags, and nuggets.

    Raises:
        ValueError: If API key not set or API call fails.
    """
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Add it to .env file or environment."
        )

    if progress_callback:
        progress_callback("Building analysis prompt...")

    prompt = build_prompt(
        transcript=transcript,
        source_name=source_name,
        title=title,
        duration_minutes=duration_minutes,
        date=date,
    )

    if progress_callback:
        progress_callback(f"Analyzing with Claude ({model})...")

    client = anthropic.Anthropic(api_key=api_key)

    # Use a reasonable max_tokens for long transcripts
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    # Extract the response text
    response_text = message.content[0].text

    if progress_callback:
        progress_callback("Parsing response...")

    # Parse JSON response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {e}") from e

    # Convert to AnalysisResult
    nuggets = []
    for n in data.get("nuggets", []):
        try:
            nugget_type = NuggetType(n.get("type", "insight"))
        except ValueError:
            nugget_type = NuggetType.INSIGHT

        nuggets.append(
            Nugget(
                content=n.get("content", ""),
                type=nugget_type,
                timestamp=n.get("timestamp"),
                context=n.get("context"),
                importance=n.get("importance", 3),
                speaker=n.get("speaker"),
            )
        )

    return AnalysisResult(
        summary=data.get("summary", ""),
        guests=data.get("guests", []),
        suggested_tags=data.get("suggested_tags", []),
        nuggets=nuggets,
    )


def analyze_transcript_file(
    transcript_path: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[AnalysisResult, dict]:
    """Analyze a transcript file and extract nuggets.

    Args:
        transcript_path: Path to transcript file.
        progress_callback: Optional callback for progress updates.

    Returns:
        Tuple of (AnalysisResult, metadata_dict).
    """
    if progress_callback:
        progress_callback(f"Reading {transcript_path.name}...")

    content = transcript_path.read_text(encoding="utf-8")

    # Parse header if present
    metadata = {}
    transcript_text = content

    if content.startswith("=" * 10):
        lines = content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if i > 0 and line.startswith("=" * 10):
                header_end = i + 1
                break
            if ":" in line and not line.startswith("="):
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()

        # Skip header and empty lines
        while header_end < len(lines) and not lines[header_end].strip():
            header_end += 1
        transcript_text = "\n".join(lines[header_end:])

    # Extract duration in minutes if present
    duration_minutes = None
    if "duration" in metadata:
        duration_str = metadata["duration"]
        parts = duration_str.split(":")
        if len(parts) == 3:
            h, m, s = map(int, parts)
            duration_minutes = h * 60 + m
        elif len(parts) == 2:
            m, s = map(int, parts)
            duration_minutes = m

    result = extract_nuggets(
        transcript=transcript_text,
        source_name=metadata.get("channel", "Unknown"),
        title=metadata.get("title", transcript_path.stem),
        duration_minutes=duration_minutes,
        date=metadata.get("upload_date"),
        progress_callback=progress_callback,
    )

    return result, metadata


def create_episode(
    analysis: AnalysisResult,
    metadata: dict,
    transcript_path: Path,
    source_type: SourceType = SourceType.YOUTUBE,
) -> Episode:
    """Create an Episode from analysis results and metadata.

    Args:
        analysis: The AnalysisResult from extract_nuggets.
        metadata: Metadata dict from transcript file.
        transcript_path: Path to the transcript file.
        source_type: Type of source.

    Returns:
        Complete Episode object.
    """
    # Generate episode ID
    video_id = metadata.get("video id", transcript_path.stem.split("-")[-1])
    date_str = metadata.get("upload_date", datetime.now().strftime("%Y-%m-%d"))
    if len(date_str) == 8 and date_str.isdigit():
        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    episode_id = f"{source_type.value}-{date_str}-{video_id[:8]}"

    # Parse duration
    duration_minutes = None
    if "duration" in metadata:
        duration_str = metadata["duration"]
        parts = duration_str.split(":")
        if len(parts) == 3:
            h, m, s = map(int, parts)
            duration_minutes = h * 60 + m
        elif len(parts) == 2:
            m, s = map(int, parts)
            duration_minutes = m

    return Episode(
        id=episode_id,
        source_type=source_type,
        source_name=metadata.get("channel", "Unknown"),
        title=metadata.get("title", "Unknown"),
        url=metadata.get("url"),
        duration_minutes=duration_minutes,
        guests=analysis.guests,
        summary=analysis.summary,
        nuggets=analysis.nuggets,
        tags=analysis.suggested_tags,
        transcript_path=str(transcript_path),
        analyzed_at=datetime.now(),
    )


def save_episode(episode: Episode, output_dir: Path | None = None) -> Path:
    """Save an episode to JSON file.

    Args:
        episode: The Episode to save.
        output_dir: Directory for nuggets (default: data/nuggets).

    Returns:
        Path to saved file.
    """
    if output_dir is None:
        output_dir = Path("data/nuggets")
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{episode.id}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(episode.model_dump_json(indent=2))

    return filepath
