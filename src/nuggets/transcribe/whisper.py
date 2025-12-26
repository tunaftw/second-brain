"""Whisper transcription for Podcast Nuggets.

This module handles audio transcription using mlx-whisper,
optimized for Apple Silicon (M1/M2/M3/M4).

Used as fallback when YouTube captions are not available.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Available Whisper models (smallest to largest)
WHISPER_MODELS = [
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "large-v2",
    "large-v3",
]

DEFAULT_MODEL = "large-v3"


class TranscribeError(Exception):
    """Error during transcription."""

    pass


def transcribe(
    audio_path: Path,
    model: str = DEFAULT_MODEL,
    *,
    language: str = "sv",
    progress_callback: Callable[[str], None] | None = None,
) -> str:
    """Transcribe audio file using mlx-whisper.

    Args:
        audio_path: Path to audio file (mp3, m4a, wav, etc.).
        model: Whisper model to use.
        language: Language code (default: Swedish).
        progress_callback: Optional callback for status updates.

    Returns:
        Transcribed text.

    Raises:
        TranscribeError: If transcription fails.
    """
    if not audio_path.exists():
        raise TranscribeError(f"Audio file not found: {audio_path}")

    if model not in WHISPER_MODELS:
        raise TranscribeError(f"Unknown model: {model}. Available: {WHISPER_MODELS}")

    try:
        import mlx_whisper
    except ImportError as e:
        raise TranscribeError(
            "mlx-whisper not installed. Install with: pip install 'podcast-nuggets[whisper]'"
        ) from e

    if progress_callback:
        progress_callback(f"Loading model {model}...")

    try:
        # mlx-whisper uses HuggingFace model IDs
        model_id = f"mlx-community/whisper-{model}-mlx"

        if progress_callback:
            progress_callback(f"Transcribing {audio_path.name}...")

        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=model_id,
            language=language,
            verbose=False,
        )

        text = result.get("text", "")

        if not text:
            raise TranscribeError("Transcription returned empty result")

        return text.strip()

    except TranscribeError:
        raise
    except Exception as e:
        raise TranscribeError(f"Transcription failed: {e}") from e
