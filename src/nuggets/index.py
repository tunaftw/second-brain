"""Library index for fast searching across all nuggets.

Provides IndexEntry and LibraryIndex models for representing aggregated
nugget data, and IndexManager for building and querying the index.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from nuggets.models import NuggetType


class IndexEntry(BaseModel):
    """A single nugget entry in the library index.

    Contains all searchable fields from a nugget, plus metadata
    from its source episode for filtering.
    """

    # Identity
    nugget_id: str = Field(..., description="Unique ID: {episode_id}-{index}")
    episode_id: str = Field(..., description="ID of the source episode")

    # Core content
    content: str = Field(..., description="The nugget content")
    type: NuggetType = Field(..., description="Type of nugget")

    # Source metadata
    source_name: str = Field(..., description="Name of podcast/channel")
    source_type: str = Field(..., description="youtube or podcast")
    date: datetime = Field(..., description="Publication date")

    # Optional categorization fields
    topic: Optional[str] = Field(None, description="Topic category")
    wisdom_type: Optional[str] = Field(None, description="Wisdom type")
    stars: Optional[int] = Field(None, ge=1, le=3, description="Personal rating 1-3")
    importance: Optional[int] = Field(None, ge=1, le=5, description="Importance 1-5")

    # Optional nugget fields
    speaker: Optional[str] = Field(None, description="Who said this")
    timestamp: Optional[str] = Field(None, description="Timestamp in episode")


class LibraryIndex(BaseModel):
    """The complete library index aggregating all nuggets.

    Provides fast lookup and filtering across the entire library.
    """

    entries: list[IndexEntry] = Field(default_factory=list, description="All nuggets")
    total_nuggets: int = Field(0, description="Total number of nuggets")
    total_episodes: int = Field(0, description="Total number of episodes")
    sources: list[str] = Field(default_factory=list, description="Unique source names")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="When index was last updated"
    )


class IndexManager:
    """Manages building, saving, loading, and querying the library index."""

    def __init__(self, base_path: Path | None = None):
        """Initialize with optional custom base path.

        Args:
            base_path: Base directory (default: Path("data"))
        """
        self.base_path = base_path or Path("data")

    def _index_path(self) -> Path:
        """Get path to index.json file."""
        return self.base_path / "library" / "index.json"

    def _analysis_dirs(self) -> list[Path]:
        """Get all analysis directories to scan."""
        return [
            self.base_path / "analysis" / "youtube",
            self.base_path / "analysis" / "podcasts",
        ]

    def build_index(self) -> LibraryIndex:
        """Scan analysis/ directory and build index from all episodes.

        Returns:
            LibraryIndex with all nuggets aggregated
        """
        entries: list[IndexEntry] = []
        episode_ids: set[str] = set()
        source_names: set[str] = set()

        for analysis_dir in self._analysis_dirs():
            if not analysis_dir.exists():
                continue

            # Scan all channel/podcast subdirectories
            for source_dir in analysis_dir.iterdir():
                if not source_dir.is_dir():
                    continue

                # Scan all episode JSON files
                for episode_file in source_dir.glob("*.json"):
                    try:
                        episode_data = json.loads(episode_file.read_text())
                        episode_entries = self._extract_entries(episode_data)
                        entries.extend(episode_entries)

                        episode_ids.add(episode_data.get("id", ""))
                        source_names.add(episode_data.get("source_name", ""))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed files
                        continue

        return LibraryIndex(
            entries=entries,
            total_nuggets=len(entries),
            total_episodes=len(episode_ids),
            sources=sorted(source_names),
            last_updated=datetime.now(),
        )

    def _extract_entries(self, episode_data: dict) -> list[IndexEntry]:
        """Extract IndexEntry objects from episode data.

        Args:
            episode_data: Parsed episode JSON

        Returns:
            List of IndexEntry objects
        """
        entries = []
        episode_id = episode_data.get("id", "")
        source_name = episode_data.get("source_name", "")
        source_type = episode_data.get("source_type", "")

        # Parse date
        date_str = episode_data.get("date")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                date = datetime.now()
        else:
            date = datetime.now()

        nuggets = episode_data.get("nuggets", [])
        for i, nugget in enumerate(nuggets):
            try:
                nugget_type = NuggetType(nugget.get("type", "insight"))
            except ValueError:
                nugget_type = NuggetType.INSIGHT

            entry = IndexEntry(
                nugget_id=f"{episode_id}-{i}",
                episode_id=episode_id,
                content=nugget.get("content", ""),
                type=nugget_type,
                source_name=source_name,
                source_type=source_type,
                date=date,
                topic=nugget.get("topic"),
                wisdom_type=nugget.get("wisdom_type"),
                stars=nugget.get("stars"),
                importance=nugget.get("importance"),
                speaker=nugget.get("speaker"),
                timestamp=nugget.get("timestamp"),
            )
            entries.append(entry)

        return entries

    def save_index(self, index: LibraryIndex) -> None:
        """Save index to library/index.json.

        Args:
            index: LibraryIndex to save
        """
        index_path = self._index_path()
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize with proper date handling
        index_data = index.model_dump(mode="json")
        index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False))

    def load_index(self) -> LibraryIndex | None:
        """Load index from library/index.json.

        Returns:
            LibraryIndex if file exists, None otherwise
        """
        index_path = self._index_path()
        if not index_path.exists():
            return None

        try:
            data = json.loads(index_path.read_text())
            return LibraryIndex.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def search(
        self,
        index: LibraryIndex,
        query: str | None = None,
        topic: str | None = None,
        wisdom_type: str | None = None,
        stars: int | None = None,
        source: str | None = None,
        year: int | None = None,
        nugget_type: NuggetType | None = None,
    ) -> list[IndexEntry]:
        """Filter index entries by various criteria.

        Args:
            index: LibraryIndex to search
            query: Text search in content (case-insensitive)
            topic: Filter by topic
            wisdom_type: Filter by wisdom type
            stars: Minimum stars (entries must have >= stars)
            source: Filter by source name (exact match)
            year: Filter by publication year
            nugget_type: Filter by nugget type

        Returns:
            List of matching IndexEntry objects
        """
        results = index.entries

        if query:
            query_lower = query.lower()
            results = [e for e in results if query_lower in e.content.lower()]

        if topic:
            results = [e for e in results if e.topic == topic]

        if wisdom_type:
            results = [e for e in results if e.wisdom_type == wisdom_type]

        if stars is not None:
            results = [e for e in results if e.stars is not None and e.stars >= stars]

        if source:
            results = [e for e in results if e.source_name == source]

        if year is not None:
            results = [e for e in results if e.date.year == year]

        if nugget_type is not None:
            results = [e for e in results if e.type == nugget_type]

        return results

    def get_stats(self, index: LibraryIndex) -> dict:
        """Get statistics about the index.

        Args:
            index: LibraryIndex to analyze

        Returns:
            Dictionary with various statistics
        """
        by_type: dict[str, int] = defaultdict(int)
        by_topic: dict[str, int] = defaultdict(int)
        by_source: dict[str, int] = defaultdict(int)
        by_year: dict[int, int] = defaultdict(int)
        starred_count = 0

        for entry in index.entries:
            by_type[entry.type.value] += 1
            if entry.topic:
                by_topic[entry.topic] += 1
            by_source[entry.source_name] += 1
            by_year[entry.date.year] += 1
            if entry.stars is not None:
                starred_count += 1

        return {
            "total_nuggets": index.total_nuggets,
            "total_episodes": index.total_episodes,
            "total_sources": len(index.sources),
            "by_type": dict(by_type),
            "by_topic": dict(by_topic),
            "by_source": dict(by_source),
            "by_year": dict(by_year),
            "starred_count": starred_count,
        }
