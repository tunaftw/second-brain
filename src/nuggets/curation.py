"""Curation utilities for rating nuggets."""

from __future__ import annotations

import json
from pathlib import Path


def set_nugget_stars(
    episode_id: str,
    nugget_index: int,
    stars: int,
    base_path: Path | None = None,
) -> bool:
    """Set star rating on a nugget.

    Args:
        episode_id: Episode ID (e.g., "youtube-2025-12-25-abc123")
        nugget_index: Index of nugget in episode (0-based)
        stars: Star rating 1-3

    Returns:
        True if successful, False if not found.
    """
    if base_path is None:
        base_path = Path("data")

    # Find the episode file in analysis/
    analysis_dir = base_path / "analysis"

    for episode_file in analysis_dir.rglob("*.json"):
        try:
            data = json.loads(episode_file.read_text(encoding="utf-8"))
            if data.get("id") == episode_id:
                nuggets = data.get("nuggets", [])
                if 0 <= nugget_index < len(nuggets):
                    nuggets[nugget_index]["stars"] = stars
                    episode_file.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    return True
        except (json.JSONDecodeError, KeyError):
            continue

    return False


def get_unrated_nuggets(base_path: Path | None = None) -> list[dict]:
    """Get all nuggets without star ratings.

    Returns:
        List of dicts with episode_id, nugget_index, content, source_name, etc.
    """
    if base_path is None:
        base_path = Path("data")

    from nuggets.index import IndexManager

    manager = IndexManager(base_path=base_path)
    lib_index = manager.load_index()

    if lib_index is None:
        return []

    unrated = []
    for entry in lib_index.entries:
        if entry.stars is None:
            # Parse nugget_index from nugget_id (format: episode_id-index)
            parts = entry.nugget_id.rsplit("-", 1)
            if len(parts) == 2:
                try:
                    nugget_index = int(parts[1])
                except ValueError:
                    continue

                unrated.append({
                    "episode_id": entry.episode_id,
                    "nugget_index": nugget_index,
                    "nugget_id": entry.nugget_id,
                    "content": entry.content,
                    "type": entry.type.value if hasattr(entry.type, "value") else entry.type,
                    "source_name": entry.source_name,
                    "date": entry.date.strftime("%Y-%m-%d") if hasattr(entry.date, "strftime") else str(entry.date),
                    "importance": entry.importance,
                })

    # Sort by importance descending (most important first)
    unrated.sort(key=lambda x: -(x.get("importance") or 0))

    return unrated
