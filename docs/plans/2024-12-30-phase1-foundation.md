# Phase 1: Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update data models, create new folder structure, and migrate existing data to support the personal knowledge library.

**Architecture:** Extend Nugget model with topic/wisdom_type/stars fields. Reorganize data into raw/analysis/library structure. Update youtube command to save to new locations.

**Tech Stack:** Python 3.11+, Pydantic 2.0, pytest

---

## Task 1: Set Up Test Infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Step 1: Create test directory and init file**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 2: Create initial model tests**

Create `tests/test_models.py`:

```python
"""Tests for data models."""

import pytest
from nuggets.models import Nugget, NuggetType


class TestNugget:
    """Tests for Nugget model."""

    def test_nugget_minimal(self):
        """Nugget can be created with minimal fields."""
        nugget = Nugget(
            content="Test insight",
            type=NuggetType.INSIGHT,
        )
        assert nugget.content == "Test insight"
        assert nugget.type == NuggetType.INSIGHT
        assert nugget.importance == 3  # default

    def test_nugget_with_new_fields(self):
        """Nugget supports topic, wisdom_type, and stars."""
        nugget = Nugget(
            content="Morning sunlight sets circadian rhythm",
            type=NuggetType.INSIGHT,
            topic="sleep",
            wisdom_type="principle",
            stars=3,
        )
        assert nugget.topic == "sleep"
        assert nugget.wisdom_type == "principle"
        assert nugget.stars == 3

    def test_nugget_stars_validation(self):
        """Stars must be 1-3 if set."""
        with pytest.raises(ValueError):
            Nugget(
                content="Test",
                type=NuggetType.INSIGHT,
                stars=5,  # Invalid: must be 1-3
            )

    def test_nugget_stars_optional(self):
        """Stars can be None (unrated)."""
        nugget = Nugget(
            content="Test",
            type=NuggetType.INSIGHT,
            stars=None,
        )
        assert nugget.stars is None
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL - `stars` field doesn't exist yet, no validation

**Step 4: Commit test infrastructure**

```bash
git add tests/
git commit -m "test: add initial model tests for new fields"
```

---

## Task 2: Extend Nugget Model

**Files:**
- Modify: `src/nuggets/models.py`

**Step 1: Add new fields to Nugget model**

In `src/nuggets/models.py`, add after line 106 (after `raw_segment` field):

```python
    # Knowledge library fields
    topic: Optional[str] = Field(
        None, description="Topic category: sleep, productivity, health, etc."
    )
    wisdom_type: Optional[str] = Field(
        None, description="Type: principle, habit, mental-model, life-lesson, technique, warning"
    )
    stars: Optional[int] = Field(
        None, ge=1, le=3, description="Personal rating 1-3 (None = unrated)"
    )
```

**Step 2: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: PASS (4 tests)

**Step 3: Commit model changes**

```bash
git add src/nuggets/models.py
git commit -m "feat(models): add topic, wisdom_type, stars to Nugget"
```

---

## Task 3: Add Category Constants

**Files:**
- Create: `src/nuggets/categories.py`
- Create: `tests/test_categories.py`

**Step 1: Write failing test**

Create `tests/test_categories.py`:

```python
"""Tests for category constants."""

from nuggets.categories import TOPICS, WISDOM_TYPES, is_valid_topic, is_valid_wisdom_type


class TestCategories:
    """Tests for category validation."""

    def test_topics_is_list(self):
        """TOPICS is a non-empty list of strings."""
        assert isinstance(TOPICS, list)
        assert len(TOPICS) > 0
        assert all(isinstance(t, str) for t in TOPICS)

    def test_wisdom_types_is_list(self):
        """WISDOM_TYPES is a non-empty list of strings."""
        assert isinstance(WISDOM_TYPES, list)
        assert len(WISDOM_TYPES) > 0
        assert all(isinstance(t, str) for t in WISDOM_TYPES)

    def test_is_valid_topic(self):
        """is_valid_topic validates known topics."""
        assert is_valid_topic("sleep") is True
        assert is_valid_topic("productivity") is True
        assert is_valid_topic("unknown_topic_xyz") is False

    def test_is_valid_wisdom_type(self):
        """is_valid_wisdom_type validates known types."""
        assert is_valid_wisdom_type("principle") is True
        assert is_valid_wisdom_type("habit") is True
        assert is_valid_wisdom_type("unknown_type_xyz") is False

    def test_topics_are_lowercase(self):
        """All topics are lowercase for consistency."""
        assert all(t == t.lower() for t in TOPICS)

    def test_wisdom_types_are_lowercase(self):
        """All wisdom types are lowercase for consistency."""
        assert all(t == t.lower() for t in WISDOM_TYPES)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_categories.py -v
```

Expected: FAIL - module doesn't exist

**Step 3: Implement categories module**

Create `src/nuggets/categories.py`:

```python
"""Category constants for nugget classification.

Topics describe WHAT the nugget is about.
Wisdom types describe WHAT KIND of insight it is.
"""

TOPICS: list[str] = [
    "sleep",
    "productivity",
    "health",
    "relationships",
    "business",
    "creativity",
    "learning",
    "fitness",
    "nutrition",
    "mindset",
    "technology",
    "parenting",
    "finance",
    "communication",
]

WISDOM_TYPES: list[str] = [
    "principle",      # Fundamental truth or rule
    "habit",          # Concrete behavior to implement
    "mental-model",   # Way of thinking about something
    "life-lesson",    # Broad life wisdom
    "technique",      # Specific method or technique
    "warning",        # Something to avoid
]


def is_valid_topic(topic: str) -> bool:
    """Check if topic is in the predefined list."""
    return topic.lower() in TOPICS


def is_valid_wisdom_type(wisdom_type: str) -> bool:
    """Check if wisdom_type is in the predefined list."""
    return wisdom_type.lower() in WISDOM_TYPES
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_categories.py -v
```

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/nuggets/categories.py tests/test_categories.py
git commit -m "feat: add category constants (topics, wisdom_types)"
```

---

## Task 4: Create Library Path Utilities

**Files:**
- Create: `src/nuggets/library.py`
- Create: `tests/test_library.py`

**Step 1: Write failing tests**

Create `tests/test_library.py`:

```python
"""Tests for library path utilities."""

from pathlib import Path

import pytest

from nuggets.library import LibraryPaths, slugify


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Basic channel name to slug."""
        assert slugify("Huberman Lab") == "huberman-lab"

    def test_special_characters(self):
        """Removes special characters."""
        assert slugify("Tim Ferriss Show!") == "tim-ferriss-show"

    def test_multiple_spaces(self):
        """Handles multiple spaces."""
        assert slugify("The   Joe   Rogan   Experience") == "the-joe-rogan-experience"

    def test_unicode(self):
        """Handles unicode characters."""
        assert slugify("Café Podcast") == "caf-podcast"


class TestLibraryPaths:
    """Tests for LibraryPaths."""

    def test_default_base_path(self):
        """Default base path is data/."""
        paths = LibraryPaths()
        assert paths.base == Path("data")

    def test_raw_youtube_path(self):
        """Raw YouTube path construction."""
        paths = LibraryPaths()
        result = paths.raw_youtube("Huberman Lab", "2024-01-15", "abc123")
        assert result == Path("data/raw/youtube/huberman-lab/2024-01-15-abc123.json")

    def test_analysis_youtube_path(self):
        """Analysis YouTube path construction."""
        paths = LibraryPaths()
        result = paths.analysis_youtube("Huberman Lab", "2024-01-15", "abc123")
        assert result == Path("data/analysis/youtube/huberman-lab/2024-01-15-abc123.json")

    def test_library_index_path(self):
        """Library index path."""
        paths = LibraryPaths()
        assert paths.library_index == Path("data/library/index.json")

    def test_library_sources_path(self):
        """Library sources path."""
        paths = LibraryPaths()
        assert paths.library_sources == Path("data/library/sources.json")

    def test_library_starred_path(self):
        """Library starred path."""
        paths = LibraryPaths()
        assert paths.library_starred == Path("data/library/starred.json")

    def test_custom_base_path(self):
        """Can use custom base path."""
        paths = LibraryPaths(base=Path("/custom/path"))
        assert paths.base == Path("/custom/path")
        assert paths.library_index == Path("/custom/path/library/index.json")
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_library.py -v
```

Expected: FAIL - module doesn't exist

**Step 3: Implement library module**

Create `src/nuggets/library.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_library.py -v
```

Expected: PASS (10 tests)

**Step 5: Commit**

```bash
git add src/nuggets/library.py tests/test_library.py
git commit -m "feat: add library path utilities"
```

---

## Task 5: Create Data Migration Script

**Files:**
- Create: `scripts/migrate_to_library.py`

**Step 1: Write migration script**

Create `scripts/migrate_to_library.py`:

```python
#!/usr/bin/env python3
"""Migrate existing data to new library structure.

Moves:
- data/transcripts/youtube/* → data/raw/youtube/{channel}/
- data/nuggets/* → data/analysis/youtube/{channel}/

Run with: python scripts/migrate_to_library.py
Add --dry-run to preview without making changes.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nuggets.library import LibraryPaths, slugify


def migrate_transcripts(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Migrate transcript files to raw/ structure.

    Returns:
        List of (old_path, new_path) tuples for migrated files.
    """
    old_dir = Path("data/transcripts/youtube")
    if not old_dir.exists():
        print("No transcripts to migrate")
        return []

    paths = LibraryPaths()
    migrations: list[tuple[Path, Path]] = []

    for old_file in old_dir.glob("*.txt"):
        # Parse filename: channel-date-videoid.txt
        # Example: chris-williamson-2025-12-25-hLIvhTiytIE.txt
        parts = old_file.stem.rsplit("-", 4)  # Split from right to get video_id
        if len(parts) < 4:
            print(f"  Skipping {old_file.name}: unexpected format")
            continue

        # Reconstruct parts
        video_id = parts[-1]
        day = parts[-2]
        month = parts[-3]
        year = parts[-4]
        channel = "-".join(parts[:-4]) if len(parts) > 4 else "unknown"

        date = f"{year}-{month}-{day}"

        # New path (as JSON with transcript content)
        new_path = paths.base / "raw" / "youtube" / channel / f"{date}-{video_id}.json"

        migrations.append((old_file, new_path))

        if dry_run:
            print(f"  Would move: {old_file} → {new_path}")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Read transcript and save as JSON
            content = old_file.read_text(encoding="utf-8")
            data = {
                "video_id": video_id,
                "channel_slug": channel,
                "date": date,
                "transcript": content,
                "source_file": str(old_file),
            }
            new_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  Migrated: {old_file.name} → {new_path}")

    return migrations


def migrate_nuggets(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Migrate nugget files to analysis/ structure.

    Returns:
        List of (old_path, new_path) tuples for migrated files.
    """
    old_dir = Path("data/nuggets")
    if not old_dir.exists():
        print("No nuggets to migrate")
        return []

    paths = LibraryPaths()
    migrations: list[tuple[Path, Path]] = []

    for old_file in old_dir.glob("*.json"):
        if old_file.name == ".gitkeep":
            continue

        # Load episode data to get channel info
        try:
            data = json.loads(old_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  Skipping {old_file.name}: invalid JSON")
            continue

        source_name = data.get("source_name", "unknown")
        channel_slug = slugify(source_name)

        # Extract date from episode data or ID
        date_str = None
        if data.get("date"):
            # Parse ISO date
            date_str = data["date"][:10]  # "2025-12-25T00:00:00" → "2025-12-25"
        else:
            # Try to extract from ID: youtube-2025-12-25-hLIvhTiE
            episode_id = data.get("id", "")
            parts = episode_id.split("-")
            if len(parts) >= 4:
                date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"

        if not date_str:
            date_str = "unknown"

        # Extract video_id from URL or ID
        video_id = "unknown"
        url = data.get("url", "")
        if "v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        elif data.get("id"):
            video_id = data["id"].split("-")[-1]

        # New path
        new_path = paths.analysis_youtube(source_name, date_str, video_id)

        migrations.append((old_file, new_path))

        if dry_run:
            print(f"  Would move: {old_file} → {new_path}")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_file, new_path)
            print(f"  Migrated: {old_file.name} → {new_path}")

    return migrations


def main():
    """Run migration."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate data to library structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    print("=" * 60)
    print("Migrating to Library Structure")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN - No changes will be made]\n")

    # Ensure library directories exist
    if not args.dry_run:
        paths = LibraryPaths()
        paths.ensure_dirs()
        print("Created library directories\n")

    # Migrate transcripts
    print("Migrating transcripts...")
    transcript_migrations = migrate_transcripts(dry_run=args.dry_run)

    # Migrate nuggets
    print("\nMigrating nuggets...")
    nugget_migrations = migrate_nuggets(dry_run=args.dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Transcripts: {len(transcript_migrations)} files")
    print(f"  Nuggets: {len(nugget_migrations)} files")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")
    else:
        print("\nMigration complete!")
        print("\nNote: Original files were kept. Delete manually after verification:")
        print("  rm -rf data/transcripts/")
        print("  rm -rf data/nuggets/")


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

```bash
chmod +x scripts/migrate_to_library.py
```

**Step 3: Test with dry-run**

```bash
python scripts/migrate_to_library.py --dry-run
```

Expected: Shows what would be migrated without making changes

**Step 4: Commit migration script**

```bash
git add scripts/
git commit -m "feat: add data migration script"
```

---

## Task 6: Run Migration

**Step 1: Run migration**

```bash
python scripts/migrate_to_library.py
```

**Step 2: Verify new structure**

```bash
ls -la data/raw/youtube/
ls -la data/analysis/youtube/
ls -la data/library/
```

Expected: Files organized by channel in new structure

**Step 3: Commit migrated data (if tracked)**

```bash
git status
# If data files are tracked:
git add data/
git commit -m "chore: migrate data to library structure"
```

---

## Task 7: Update YouTube Command for New Structure

**Files:**
- Modify: `src/nuggets/transcribe/youtube.py`
- Create: `tests/test_youtube.py`

**Step 1: Write test for new save function**

Create `tests/test_youtube.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_youtube.py -v
```

Expected: FAIL - save_raw_youtube doesn't exist

**Step 3: Add save_raw_youtube function**

Add to `src/nuggets/transcribe/youtube.py` after the existing `save_transcript` function:

```python
def save_raw_youtube(
    result: dict,
    base_path: Path | None = None,
) -> Path:
    """Save raw YouTube data to library structure.

    Args:
        result: Result dict from process_youtube_video.
        base_path: Base directory (default: Path("data")).

    Returns:
        Path to saved JSON file.
    """
    from nuggets.library import LibraryPaths, slugify

    paths = LibraryPaths(base=base_path)

    # Extract components
    channel = result.get("channel", "unknown")
    video_id = result["video_id"]

    # Parse upload date
    upload_date = result.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

    # Build file path
    filepath = paths.raw_youtube(channel, date, video_id)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data
    data = {
        "video_id": video_id,
        "channel": channel,
        "channel_slug": slugify(channel),
        "title": result.get("title"),
        "date": date,
        "upload_date": upload_date,
        "duration": result.get("duration"),
        "url": result.get("url"),
        "chapters": result.get("chapters", []),
        "transcript": result.get("transcript"),
        "transcript_source": result.get("transcript_source"),
        "has_timestamps": result.get("has_timestamps", False),
    }

    # Write JSON
    import json
    filepath.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return filepath
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_youtube.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/nuggets/transcribe/youtube.py tests/test_youtube.py
git commit -m "feat: add save_raw_youtube for library structure"
```

---

## Task 8: Update CLI to Use New Paths

**Files:**
- Modify: `src/nuggets/cli.py`

**Step 1: Update youtube command to use save_raw_youtube**

In `src/nuggets/cli.py`, find the youtube command (around line 462-464) and update:

Replace:
```python
    # Save transcript
    filepath = save_transcript(result)
    console.print(f"[green]\u2713[/] Saved to: [cyan]{filepath}[/]")
```

With:
```python
    # Save raw data to library structure
    from nuggets.transcribe.youtube import save_raw_youtube
    raw_filepath = save_raw_youtube(result)
    console.print(f"[green]\u2713[/] Raw data saved to: [cyan]{raw_filepath}[/]")

    # Also save legacy transcript for backwards compatibility
    filepath = save_transcript(result)
```

**Step 2: Test manually**

```bash
# Test with a short video
nuggets youtube "https://www.youtube.com/watch?v=jNQXAC9IVRw" --transcript-only
```

Verify: Check that file appears in `data/raw/youtube/` with correct structure

**Step 3: Commit**

```bash
git add src/nuggets/cli.py
git commit -m "feat(cli): save raw YouTube data to library structure"
```

---

## Task 9: Final Verification

**Step 1: Run all tests**

```bash
pytest -v
```

Expected: All tests pass

**Step 2: Verify new structure**

```bash
tree data/ -L 4
```

Expected structure:
```
data/
├── analysis/
│   └── youtube/
│       └── {channel}/
├── library/
├── raw/
│   └── youtube/
│       └── {channel}/
└── ... (legacy folders)
```

**Step 3: Commit any remaining changes**

```bash
git status
git add .
git commit -m "chore: complete phase 1 foundation"
```

---

## Summary

Phase 1 complete. We now have:

- [x] Nugget model with `topic`, `wisdom_type`, `stars` fields
- [x] Category constants (`TOPICS`, `WISDOM_TYPES`)
- [x] Library path utilities (`LibraryPaths`, `slugify`)
- [x] Migration script for existing data
- [x] YouTube command saving to new structure
- [x] Test coverage for new code

**Next:** Phase 2 - Index & Search
