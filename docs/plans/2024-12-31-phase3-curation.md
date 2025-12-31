# Phase 3: Curation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement star rating commands for personal curation of nuggets.

**Architecture:** Add `nuggets star` command to set ratings on individual nuggets. Store stars in the analysis JSON files and update the index. Add interactive mode for batch curation.

**Tech Stack:** Python 3.11+, Click CLI, Rich for interactive display

---

## Task 1: Add Star Rating Command

**Files:**
- Modify: `src/nuggets/cli.py`
- Create: `src/nuggets/curation.py`

**Step 1: Create curation module**

Create `src/nuggets/curation.py`:

```python
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
                    "type": entry.type,
                    "source_name": entry.source_name,
                    "date": entry.date,
                    "importance": entry.importance,
                })

    # Sort by importance descending (most important first)
    unrated.sort(key=lambda x: -(x.get("importance") or 0))

    return unrated
```

**Step 2: Add star command to CLI**

Add to `src/nuggets/cli.py`:

```python
@main.command()
@click.argument("nugget_id", required=False)
@click.argument("stars", type=int, required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive curation mode")
def star(nugget_id: str | None, stars: int | None, interactive: bool) -> None:
    """Rate a nugget with stars (1-3).

    Examples:
        nuggets star youtube-2025-12-25-abc123-0 3
        nuggets star --interactive
    """
    from nuggets.curation import set_nugget_stars, get_unrated_nuggets
    from nuggets.index import IndexManager

    if interactive:
        _interactive_curation()
        return

    if not nugget_id or stars is None:
        console.print("[red]Error:[/] Provide nugget_id and stars (1-3)")
        console.print("[dim]Example: nuggets star youtube-2025-12-25-abc123-0 3[/]")
        console.print("[dim]Or use: nuggets star --interactive[/]")
        return

    if stars < 1 or stars > 3:
        console.print("[red]Error:[/] Stars must be 1, 2, or 3")
        return

    # Parse nugget_id: episode_id-index
    parts = nugget_id.rsplit("-", 1)
    if len(parts) != 2:
        console.print(f"[red]Error:[/] Invalid nugget ID format: {nugget_id}")
        return

    episode_id = parts[0]
    try:
        nugget_index = int(parts[1])
    except ValueError:
        console.print(f"[red]Error:[/] Invalid nugget index in: {nugget_id}")
        return

    success = set_nugget_stars(episode_id, nugget_index, stars)

    if success:
        console.print(f"[green]✓[/] Set {'⭐' * stars} on nugget {nugget_id}")
        console.print("[dim]Run 'nuggets index rebuild' to update the index[/]")
    else:
        console.print(f"[red]Error:[/] Nugget not found: {nugget_id}")


def _interactive_curation() -> None:
    """Interactive curation mode."""
    from nuggets.curation import set_nugget_stars, get_unrated_nuggets
    from nuggets.index import IndexManager

    unrated = get_unrated_nuggets()

    if not unrated:
        console.print("[green]✓[/] All nuggets have been rated!")
        return

    console.print(f"[bold]Interactive Curation[/]")
    console.print(f"Found {len(unrated)} unrated nuggets\n")
    console.print("[dim]Commands: 1/2/3 = set stars, s = skip, q = quit[/]\n")

    rated_count = 0

    for nugget in unrated:
        # Display nugget
        type_icons = {"insight": "💡", "action": "✅", "quote": "💬", "concept": "📖", "story": "📖"}
        icon = type_icons.get(nugget["type"], "•")

        console.print(f"{icon} [bold]{nugget['content'][:100]}{'...' if len(nugget['content']) > 100 else ''}[/]")
        console.print(f"   [dim]{nugget['source_name']} • {nugget['date']}[/]")
        if nugget.get("importance"):
            console.print(f"   [dim]AI importance: {nugget['importance']}/5[/]")

        # Get input
        try:
            choice = console.input("\n   [bold]Rate (1/2/3/s/q):[/] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "q":
            break
        elif choice == "s":
            console.print()
            continue
        elif choice in ("1", "2", "3"):
            stars = int(choice)
            success = set_nugget_stars(
                nugget["episode_id"],
                nugget["nugget_index"],
                stars,
            )
            if success:
                console.print(f"   [green]✓ Set {'⭐' * stars}[/]\n")
                rated_count += 1
            else:
                console.print(f"   [red]Failed to save[/]\n")
        else:
            console.print(f"   [yellow]Skipped[/]\n")

    console.print(f"\n[bold]Done![/] Rated {rated_count} nuggets.")
    if rated_count > 0:
        console.print("[dim]Run 'nuggets index rebuild' to update the index[/]")
```

**Step 3: Test manually**

```bash
source .venv/bin/activate
nuggets star --interactive
# Rate a few nuggets
nuggets index rebuild
nuggets index stats
```

**Step 4: Commit**

```bash
git add src/nuggets/curation.py src/nuggets/cli.py
git commit -m "feat: add star rating command with interactive mode"
```

---

## Task 2: Add Curation Tests

**Files:**
- Create: `tests/test_curation.py`

**Step 1: Create tests**

```python
"""Tests for curation utilities."""

import json
from pathlib import Path

import pytest

from nuggets.curation import set_nugget_stars, get_unrated_nuggets


class TestSetNuggetStars:
    """Tests for set_nugget_stars."""

    def test_set_stars_success(self, tmp_path):
        """Successfully set stars on a nugget."""
        # Create episode file
        analysis_dir = tmp_path / "analysis" / "youtube" / "test"
        analysis_dir.mkdir(parents=True)

        episode = {
            "id": "youtube-2024-01-15-abc123",
            "nuggets": [
                {"content": "First", "type": "insight"},
                {"content": "Second", "type": "quote"},
            ],
        }
        episode_file = analysis_dir / "2024-01-15-abc123.json"
        episode_file.write_text(json.dumps(episode), encoding="utf-8")

        # Set stars
        result = set_nugget_stars(
            "youtube-2024-01-15-abc123",
            nugget_index=0,
            stars=3,
            base_path=tmp_path,
        )

        assert result is True

        # Verify saved
        saved = json.loads(episode_file.read_text())
        assert saved["nuggets"][0]["stars"] == 3
        assert "stars" not in saved["nuggets"][1]

    def test_set_stars_not_found(self, tmp_path):
        """Returns False if episode not found."""
        (tmp_path / "analysis").mkdir(parents=True)

        result = set_nugget_stars(
            "nonexistent-episode",
            nugget_index=0,
            stars=2,
            base_path=tmp_path,
        )

        assert result is False


class TestGetUnratedNuggets:
    """Tests for get_unrated_nuggets."""

    def test_returns_unrated(self, tmp_path):
        """Returns nuggets without stars."""
        # Create library index
        (tmp_path / "library").mkdir(parents=True)

        from nuggets.index import IndexEntry, LibraryIndex, IndexManager

        entries = [
            IndexEntry(
                nugget_id="ep1-0",
                episode_id="ep1",
                content="Rated",
                type="insight",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                stars=3,
            ),
            IndexEntry(
                nugget_id="ep1-1",
                episode_id="ep1",
                content="Unrated",
                type="quote",
                source_name="Test",
                source_type="youtube",
                date="2024-01-15",
                stars=None,
            ),
        ]
        index = LibraryIndex(entries=entries, total_nuggets=2)

        manager = IndexManager(base_path=tmp_path)
        manager.save_index(index)

        # Get unrated
        unrated = get_unrated_nuggets(base_path=tmp_path)

        assert len(unrated) == 1
        assert unrated[0]["content"] == "Unrated"
```

**Step 2: Run tests**

```bash
source .venv/bin/activate && pytest tests/test_curation.py -v
```

**Step 3: Commit**

```bash
git add tests/test_curation.py
git commit -m "test: add curation tests"
```

---

## Summary

Phase 3 complete. We now have:

- [x] `nuggets star <id> <1-3>` - Set stars on a nugget
- [x] `nuggets star --interactive` - Batch curation mode
- [x] `set_nugget_stars()` utility
- [x] `get_unrated_nuggets()` utility
- [x] Test coverage

**Next:** Phase 4 - Export
