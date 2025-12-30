# Phase 2: Index & Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a searchable index of all nuggets and implement list/search CLI commands.

**Architecture:** Create an IndexManager class that builds and queries `library/index.json`. The index aggregates all nuggets from `analysis/` with metadata for fast filtering. CLI commands use IndexManager for list/search operations.

**Tech Stack:** Python 3.11+, Pydantic 2.0, pytest, Click CLI

---

## Task 1: Create Index Models

**Files:**
- Create: `src/nuggets/index.py`
- Create: `tests/test_index.py`

**Step 1: Write failing tests**

Create `tests/test_index.py`:

```python
"""Tests for library index."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from nuggets.index import IndexEntry, LibraryIndex, IndexManager


class TestIndexEntry:
    """Tests for IndexEntry model."""

    def test_create_entry(self):
        """Can create an index entry."""
        entry = IndexEntry(
            nugget_id="abc123-0",
            episode_id="youtube-2024-01-15-abc123",
            content="Morning sunlight is key",
            type="insight",
            source_name="Huberman Lab",
            source_type="youtube",
            date="2024-01-15",
            topic="sleep",
            wisdom_type="principle",
            stars=3,
            importance=5,
        )
        assert entry.nugget_id == "abc123-0"
        assert entry.stars == 3


class TestLibraryIndex:
    """Tests for LibraryIndex model."""

    def test_empty_index(self):
        """Can create empty index."""
        index = LibraryIndex()
        assert index.entries == []
        assert index.total_nuggets == 0

    def test_index_with_entries(self):
        """Index tracks total count."""
        entry = IndexEntry(
            nugget_id="abc123-0",
            episode_id="ep1",
            content="Test",
            type="insight",
            source_name="Test",
            source_type="youtube",
            date="2024-01-15",
        )
        index = LibraryIndex(entries=[entry], total_nuggets=1)
        assert index.total_nuggets == 1


class TestIndexManager:
    """Tests for IndexManager."""

    def test_build_index_empty(self, tmp_path):
        """Build index with no analysis files."""
        manager = IndexManager(base_path=tmp_path)
        index = manager.build_index()
        assert index.total_nuggets == 0

    def test_build_index_from_episode(self, tmp_path):
        """Build index from episode file."""
        # Create analysis directory structure
        analysis_dir = tmp_path / "analysis" / "youtube" / "test-channel"
        analysis_dir.mkdir(parents=True)

        # Create episode file
        episode = {
            "id": "youtube-2024-01-15-abc123",
            "source_type": "youtube",
            "source_name": "Test Channel",
            "title": "Test Episode",
            "date": "2024-01-15T00:00:00",
            "nuggets": [
                {
                    "content": "First nugget",
                    "type": "insight",
                    "importance": 4,
                    "topic": "productivity",
                    "wisdom_type": "principle",
                },
                {
                    "content": "Second nugget",
                    "type": "quote",
                    "importance": 3,
                },
            ],
        }
        (analysis_dir / "2024-01-15-abc123.json").write_text(
            json.dumps(episode), encoding="utf-8"
        )

        # Build index
        manager = IndexManager(base_path=tmp_path)
        index = manager.build_index()

        assert index.total_nuggets == 2
        assert len(index.entries) == 2
        assert index.entries[0].source_name == "Test Channel"

    def test_save_and_load_index(self, tmp_path):
        """Can save and load index."""
        manager = IndexManager(base_path=tmp_path)

        # Create library dir
        (tmp_path / "library").mkdir(parents=True)

        # Create index
        entry = IndexEntry(
            nugget_id="abc-0",
            episode_id="ep1",
            content="Test",
            type="insight",
            source_name="Test",
            source_type="youtube",
            date="2024-01-15",
        )
        index = LibraryIndex(entries=[entry], total_nuggets=1)

        # Save and load
        manager.save_index(index)
        loaded = manager.load_index()

        assert loaded.total_nuggets == 1
        assert loaded.entries[0].content == "Test"
```

**Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_index.py -v
```

Expected: FAIL - module doesn't exist

**Step 3: Implement index module**

Create `src/nuggets/index.py`:

```python
"""Library index for fast nugget lookup and search.

The index aggregates all nuggets from analysis/ into a single
searchable structure stored in library/index.json.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class IndexEntry(BaseModel):
    """A single nugget entry in the index."""

    nugget_id: str = Field(..., description="Unique ID: episode_id-index")
    episode_id: str = Field(..., description="Parent episode ID")
    content: str = Field(..., description="Nugget content")
    type: str = Field(..., description="Nugget type: insight, quote, etc.")

    # Source info
    source_name: str = Field(..., description="Channel/podcast name")
    source_type: str = Field(..., description="youtube or podcast")
    date: str = Field(..., description="Episode date YYYY-MM-DD")

    # Optional categorization
    topic: Optional[str] = Field(None, description="Topic category")
    wisdom_type: Optional[str] = Field(None, description="Wisdom type")
    stars: Optional[int] = Field(None, description="Personal rating 1-3")
    importance: Optional[int] = Field(None, description="AI importance 1-5")

    # For display
    speaker: Optional[str] = Field(None, description="Who said it")
    timestamp: Optional[str] = Field(None, description="Timestamp in episode")


class LibraryIndex(BaseModel):
    """The complete library index."""

    entries: list[IndexEntry] = Field(default_factory=list)
    total_nuggets: int = Field(0)
    total_episodes: int = Field(0)
    sources: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class IndexManager:
    """Manages the library index."""

    def __init__(self, base_path: Path | None = None):
        """Initialize with optional custom base path."""
        self.base_path = base_path or Path("data")
        self.index_path = self.base_path / "library" / "index.json"

    def build_index(self) -> LibraryIndex:
        """Build index from all analysis files."""
        entries: list[IndexEntry] = []
        sources: set[str] = set()
        episode_count = 0

        # Scan analysis directories
        analysis_dir = self.base_path / "analysis"
        if not analysis_dir.exists():
            return LibraryIndex()

        for episode_file in analysis_dir.rglob("*.json"):
            try:
                data = json.loads(episode_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            episode_id = data.get("id", episode_file.stem)
            source_name = data.get("source_name", "Unknown")
            source_type = data.get("source_type", "youtube")

            # Parse date
            date_str = data.get("date", "")
            if date_str:
                date_str = date_str[:10]  # YYYY-MM-DD
            else:
                date_str = "unknown"

            sources.add(source_name)
            episode_count += 1

            # Index each nugget
            nuggets = data.get("nuggets", [])
            for i, nugget in enumerate(nuggets):
                entry = IndexEntry(
                    nugget_id=f"{episode_id}-{i}",
                    episode_id=episode_id,
                    content=nugget.get("content", ""),
                    type=nugget.get("type", "insight"),
                    source_name=source_name,
                    source_type=source_type,
                    date=date_str,
                    topic=nugget.get("topic"),
                    wisdom_type=nugget.get("wisdom_type"),
                    stars=nugget.get("stars"),
                    importance=nugget.get("importance"),
                    speaker=nugget.get("speaker"),
                    timestamp=nugget.get("timestamp"),
                )
                entries.append(entry)

        return LibraryIndex(
            entries=entries,
            total_nuggets=len(entries),
            total_episodes=episode_count,
            sources=sorted(sources),
        )

    def save_index(self, index: LibraryIndex) -> Path:
        """Save index to library/index.json."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            index.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return self.index_path

    def load_index(self) -> LibraryIndex:
        """Load index from library/index.json."""
        if not self.index_path.exists():
            return LibraryIndex()

        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return LibraryIndex.model_validate(data)

    def search(
        self,
        query: str | None = None,
        topic: str | None = None,
        wisdom_type: str | None = None,
        stars: int | None = None,
        source: str | None = None,
        year: int | None = None,
        nugget_type: str | None = None,
    ) -> list[IndexEntry]:
        """Search the index with filters."""
        index = self.load_index()
        results = index.entries

        if query:
            query_lower = query.lower()
            results = [e for e in results if query_lower in e.content.lower()]

        if topic:
            results = [e for e in results if e.topic == topic]

        if wisdom_type:
            results = [e for e in results if e.wisdom_type == wisdom_type]

        if stars is not None:
            results = [e for e in results if e.stars == stars]

        if source:
            source_lower = source.lower()
            results = [e for e in results if source_lower in e.source_name.lower()]

        if year:
            results = [e for e in results if e.date.startswith(str(year))]

        if nugget_type:
            results = [e for e in results if e.type == nugget_type]

        return results

    def get_stats(self) -> dict:
        """Get index statistics."""
        index = self.load_index()

        # Count by stars
        star_counts = {1: 0, 2: 0, 3: 0, None: 0}
        for entry in index.entries:
            star_counts[entry.stars] = star_counts.get(entry.stars, 0) + 1

        # Count by topic
        topic_counts: dict[str, int] = {}
        for entry in index.entries:
            if entry.topic:
                topic_counts[entry.topic] = topic_counts.get(entry.topic, 0) + 1

        # Count by source
        source_counts: dict[str, int] = {}
        for entry in index.entries:
            source_counts[entry.source_name] = source_counts.get(entry.source_name, 0) + 1

        return {
            "total_nuggets": index.total_nuggets,
            "total_episodes": index.total_episodes,
            "sources": index.sources,
            "star_counts": star_counts,
            "topic_counts": topic_counts,
            "source_counts": source_counts,
        }
```

**Step 4: Run tests**

```bash
source .venv/bin/activate && pytest tests/test_index.py -v
```

Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/nuggets/index.py tests/test_index.py
git commit -m "feat: add library index with IndexManager"
```

---

## Task 2: Implement `nuggets index` Commands

**Files:**
- Modify: `src/nuggets/cli.py`

**Step 1: Add index command group**

Add after the `config` command group (around line 380):

```python
# Index command group
@main.group()
def index() -> None:
    """Manage the library index.

    The index aggregates all nuggets for fast search and filtering.
    """
    pass


@index.command(name="rebuild")
def index_rebuild() -> None:
    """Rebuild the library index from analysis files.

    Scans all files in data/analysis/ and creates library/index.json.

    Example:
        nuggets index rebuild
    """
    from nuggets.index import IndexManager

    manager = IndexManager()

    with console.status("[bold blue]Rebuilding index..."):
        lib_index = manager.build_index()
        index_path = manager.save_index(lib_index)

    console.print(f"[green]✓[/] Index rebuilt")
    console.print(f"  Episodes: {lib_index.total_episodes}")
    console.print(f"  Nuggets: {lib_index.total_nuggets}")
    console.print(f"  Sources: {', '.join(lib_index.sources)}")
    console.print(f"[dim]Saved to: {index_path}[/]")


@index.command(name="stats")
def index_stats() -> None:
    """Show library statistics.

    Example:
        nuggets index stats
    """
    from nuggets.index import IndexManager

    manager = IndexManager()
    stats = manager.get_stats()

    if stats["total_nuggets"] == 0:
        console.print("[yellow]No index found. Run 'nuggets index rebuild' first.[/]")
        return

    # Header
    console.print()
    console.print("[bold]📚 Podcast Nuggets Library[/]")
    console.print("─" * 40)

    # Totals
    console.print(f"Episodes:     {stats['total_episodes']}")
    console.print(f"Nuggets:      {stats['total_nuggets']}")

    # Stars breakdown
    star_counts = stats["star_counts"]
    console.print(f"  ⭐⭐⭐        {star_counts.get(3, 0)}")
    console.print(f"  ⭐⭐          {star_counts.get(2, 0)}")
    console.print(f"  ⭐           {star_counts.get(1, 0)}")
    console.print(f"  Unrated:    {star_counts.get(None, 0)}")

    # Top sources
    if stats["source_counts"]:
        console.print()
        console.print("[bold]Top sources:[/]")
        sorted_sources = sorted(
            stats["source_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        for source, count in sorted_sources:
            console.print(f"  {source:20} {count} nuggets")

    # Top topics
    if stats["topic_counts"]:
        console.print()
        console.print("[bold]Top topics:[/]")
        sorted_topics = sorted(
            stats["topic_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        for topic, count in sorted_topics:
            console.print(f"  {topic:20} {count} nuggets")
```

**Step 2: Test manually**

```bash
source .venv/bin/activate
nuggets index rebuild
nuggets index stats
```

**Step 3: Commit**

```bash
git add src/nuggets/cli.py
git commit -m "feat(cli): add index rebuild and stats commands"
```

---

## Task 3: Implement `nuggets list` Command

**Files:**
- Modify: `src/nuggets/cli.py`

**Step 1: Update list command**

Replace the existing stub `list_cmd` function:

```python
@main.command(name="list")
@click.option("--source", help="Filter by source name")
@click.option("--year", type=int, help="Filter by year")
@click.option("--limit", "-n", default=20, help="Number of results (default: 20)")
def list_cmd(source: str | None, year: int | None, limit: int) -> None:
    """List all analyzed episodes.

    Example:
        nuggets list
        nuggets list --source "Huberman Lab"
        nuggets list --year 2024
    """
    from nuggets.index import IndexManager

    manager = IndexManager()
    index = manager.load_index()

    if index.total_episodes == 0:
        console.print("[yellow]No episodes found. Run 'nuggets index rebuild' first.[/]")
        return

    # Group by episode
    episodes: dict[str, dict] = {}
    for entry in index.entries:
        if entry.episode_id not in episodes:
            episodes[entry.episode_id] = {
                "source": entry.source_name,
                "date": entry.date,
                "nugget_count": 0,
            }
        episodes[entry.episode_id]["nugget_count"] += 1

    # Apply filters
    results = list(episodes.items())

    if source:
        source_lower = source.lower()
        results = [(eid, e) for eid, e in results if source_lower in e["source"].lower()]

    if year:
        results = [(eid, e) for eid, e in results if e["date"].startswith(str(year))]

    # Sort by date descending
    results.sort(key=lambda x: x[1]["date"], reverse=True)

    # Limit
    results = results[:limit]

    if not results:
        console.print("[yellow]No episodes match filters.[/]")
        return

    # Display
    table = Table(title=f"Episodes ({len(results)} of {len(episodes)})")
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Source", style="white")
    table.add_column("Nuggets", justify="center", width=8)
    table.add_column("ID", style="dim")

    for episode_id, ep in results:
        table.add_row(
            ep["date"],
            ep["source"],
            str(ep["nugget_count"]),
            episode_id[:30] + "..." if len(episode_id) > 30 else episode_id,
        )

    console.print(table)
```

**Step 2: Test manually**

```bash
nuggets list
nuggets list --source "Chris"
nuggets list --year 2025
```

**Step 3: Commit**

```bash
git add src/nuggets/cli.py
git commit -m "feat(cli): implement list command with filters"
```

---

## Task 4: Implement `nuggets search` Command

**Files:**
- Modify: `src/nuggets/cli.py`

**Step 1: Update search command**

Replace the existing stub `search` function:

```python
@main.command()
@click.argument("query", required=False)
@click.option("--topic", help="Filter by topic")
@click.option("--type", "nugget_type", help="Filter by nugget type")
@click.option("--stars", type=int, help="Filter by star rating (1-3)")
@click.option("--source", help="Filter by source name")
@click.option("--year", type=int, help="Filter by year")
@click.option("--limit", "-n", default=20, help="Number of results (default: 20)")
def search(
    query: str | None,
    topic: str | None,
    nugget_type: str | None,
    stars: int | None,
    source: str | None,
    year: int | None,
    limit: int,
) -> None:
    """Search through your nuggets.

    Example:
        nuggets search "dopamine"
        nuggets search --topic sleep
        nuggets search --stars 3
        nuggets search "morning routine" --type action
    """
    from nuggets.index import IndexManager

    manager = IndexManager()

    results = manager.search(
        query=query,
        topic=topic,
        wisdom_type=None,
        stars=stars,
        source=source,
        year=year,
        nugget_type=nugget_type,
    )

    if not results:
        console.print("[yellow]No nuggets found matching your search.[/]")
        return

    # Sort by importance then date
    results.sort(key=lambda x: (-(x.importance or 0), x.date), reverse=False)

    # Limit
    results = results[:limit]

    # Display
    console.print(f"[bold]Found {len(results)} nuggets[/]\n")

    type_icons = {
        "insight": "💡",
        "action": "✅",
        "quote": "💬",
        "concept": "📖",
        "story": "📖",
    }

    for entry in results:
        icon = type_icons.get(entry.type, "•")
        stars_str = "⭐" * (entry.stars or 0) if entry.stars else ""

        console.print(f"{icon} [bold]{entry.content[:80]}{'...' if len(entry.content) > 80 else ''}[/]")

        meta_parts = [f"[dim]{entry.source_name}[/]", f"[dim]{entry.date}[/]"]
        if entry.topic:
            meta_parts.append(f"[cyan]#{entry.topic}[/]")
        if stars_str:
            meta_parts.append(stars_str)

        console.print(f"   {' • '.join(meta_parts)}")
        console.print()
```

**Step 2: Test manually**

```bash
nuggets search "meditation"
nuggets search --topic productivity
nuggets search --stars 3
```

**Step 3: Commit**

```bash
git add src/nuggets/cli.py
git commit -m "feat(cli): implement search command with filters"
```

---

## Task 5: Add Search Tests

**Files:**
- Modify: `tests/test_index.py`

**Step 1: Add search tests**

Add to `tests/test_index.py`:

```python
class TestIndexManagerSearch:
    """Tests for IndexManager.search()."""

    @pytest.fixture
    def populated_index(self, tmp_path):
        """Create an index with test data."""
        manager = IndexManager(base_path=tmp_path)
        (tmp_path / "library").mkdir(parents=True)

        entries = [
            IndexEntry(
                nugget_id="ep1-0",
                episode_id="ep1",
                content="Morning sunlight helps sleep",
                type="insight",
                source_name="Huberman Lab",
                source_type="youtube",
                date="2024-01-15",
                topic="sleep",
                wisdom_type="principle",
                stars=3,
                importance=5,
            ),
            IndexEntry(
                nugget_id="ep1-1",
                episode_id="ep1",
                content="Cold exposure boosts dopamine",
                type="insight",
                source_name="Huberman Lab",
                source_type="youtube",
                date="2024-01-15",
                topic="health",
                wisdom_type="principle",
                importance=4,
            ),
            IndexEntry(
                nugget_id="ep2-0",
                episode_id="ep2",
                content="Discipline equals freedom",
                type="quote",
                source_name="Jocko Podcast",
                source_type="youtube",
                date="2023-06-01",
                topic="mindset",
                wisdom_type="principle",
                stars=3,
                importance=5,
            ),
        ]

        index = LibraryIndex(entries=entries, total_nuggets=3, total_episodes=2)
        manager.save_index(index)
        return manager

    def test_search_by_query(self, populated_index):
        """Search by text query."""
        results = populated_index.search(query="dopamine")
        assert len(results) == 1
        assert "dopamine" in results[0].content.lower()

    def test_search_by_topic(self, populated_index):
        """Filter by topic."""
        results = populated_index.search(topic="sleep")
        assert len(results) == 1
        assert results[0].topic == "sleep"

    def test_search_by_stars(self, populated_index):
        """Filter by star rating."""
        results = populated_index.search(stars=3)
        assert len(results) == 2
        assert all(r.stars == 3 for r in results)

    def test_search_by_source(self, populated_index):
        """Filter by source name."""
        results = populated_index.search(source="Jocko")
        assert len(results) == 1
        assert "Jocko" in results[0].source_name

    def test_search_by_year(self, populated_index):
        """Filter by year."""
        results = populated_index.search(year=2023)
        assert len(results) == 1
        assert results[0].date.startswith("2023")

    def test_search_combined_filters(self, populated_index):
        """Combine multiple filters."""
        results = populated_index.search(source="Huberman", topic="sleep")
        assert len(results) == 1
        assert results[0].topic == "sleep"
        assert "Huberman" in results[0].source_name
```

**Step 2: Run tests**

```bash
source .venv/bin/activate && pytest tests/test_index.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_index.py
git commit -m "test: add search filter tests"
```

---

## Task 6: Final Verification

**Step 1: Run all tests**

```bash
source .venv/bin/activate && pytest -v
```

Expected: All tests pass

**Step 2: Build and test index**

```bash
nuggets index rebuild
nuggets index stats
nuggets list
nuggets search "meditation"
```

**Step 3: Commit any remaining changes**

```bash
git status
git add .
git commit -m "chore: complete phase 2 index and search"
```

---

## Summary

Phase 2 complete. We now have:

- [x] `IndexEntry` and `LibraryIndex` models
- [x] `IndexManager` for building/querying index
- [x] `nuggets index rebuild` command
- [x] `nuggets index stats` command
- [x] `nuggets list` with filters (--source, --year)
- [x] `nuggets search` with filters (query, --topic, --type, --stars, --source, --year)
- [x] Test coverage for index and search

**Next:** Phase 3 - Curation (star rating commands)
