"""Library path utilities for organized data storage.

Provides consistent path generation for the knowledge library structure:
- raw/youtube/{channel}/    Raw transcripts and metadata
- raw/podcasts/{podcast}/   Raw podcast data
- analysis/youtube/{channel}/  Analyzed episodes with nuggets
- analysis/podcasts/{podcast}/ Analyzed podcast episodes
- library/                    Index and aggregated data
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Text to slugify (e.g., "Huberman Lab")

    Returns:
        Lowercase slug with hyphens (e.g., "huberman-lab")
    """
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)

    # Strip leading/trailing hyphens
    return text.strip("-")


class LibraryPaths:
    """Generates consistent paths for the knowledge library.

    Structure:
        data/
        ├── raw/
        │   ├── youtube/{channel-slug}/{date}-{video-id}.json
        │   └── podcasts/{podcast-slug}/{date}-{episode-id}.json
        ├── analysis/
        │   ├── youtube/{channel-slug}/{date}-{video-id}.json
        │   └── podcasts/{podcast-slug}/{date}-{episode-id}.json
        └── library/
            ├── index.json
            ├── sources.json
            └── starred.json
    """

    def __init__(self, base: Path | None = None):
        """Initialize with optional custom base path.

        Args:
            base: Base directory (default: Path("data"))
        """
        self.base = base or Path("data")

    # Raw paths

    def raw_youtube(self, channel: str, date: str, video_id: str) -> Path:
        """Path for raw YouTube data."""
        return self.base / "raw" / "youtube" / slugify(channel) / f"{date}-{video_id}.json"

    def raw_podcast(self, podcast: str, date: str, episode_id: str) -> Path:
        """Path for raw podcast data."""
        return self.base / "raw" / "podcasts" / slugify(podcast) / f"{date}-{episode_id}.json"

    # Analysis paths

    def analysis_youtube(self, channel: str, date: str, video_id: str) -> Path:
        """Path for analyzed YouTube episode."""
        return self.base / "analysis" / "youtube" / slugify(channel) / f"{date}-{video_id}.json"

    def analysis_podcast(self, podcast: str, date: str, episode_id: str) -> Path:
        """Path for analyzed podcast episode."""
        return self.base / "analysis" / "podcasts" / slugify(podcast) / f"{date}-{episode_id}.json"

    # Library paths

    @property
    def library_index(self) -> Path:
        """Path to aggregated nuggets index."""
        return self.base / "library" / "index.json"

    @property
    def library_sources(self) -> Path:
        """Path to sources registry."""
        return self.base / "library" / "sources.json"

    @property
    def library_starred(self) -> Path:
        """Path to starred nuggets cache."""
        return self.base / "library" / "starred.json"

    # Directory creation

    def ensure_dirs(self) -> None:
        """Create all library directories if they don't exist."""
        dirs = [
            self.base / "raw" / "youtube",
            self.base / "raw" / "podcasts",
            self.base / "analysis" / "youtube",
            self.base / "analysis" / "podcasts",
            self.base / "library",
            self.base / "exports",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
