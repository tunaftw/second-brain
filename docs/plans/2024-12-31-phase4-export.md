# Phase 4: Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement flexible export formats with filtering by stars, topic, and "best of" compilations.

**Architecture:** Extend `nuggets export` to support multiple modes: single episode, filtered collection, or "best of" starred nuggets. Add Markdown export format alongside existing Apple Notes.

**Tech Stack:** Python 3.11+, Click CLI, Rich for output

---

## Task 1: Add Markdown Export Format

**Files:**
- Create: `src/nuggets/export/markdown.py`

**Step 1: Create markdown export module**

```python
"""Markdown export for Podcast Nuggets."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nuggets.models import Episode


def format_for_markdown(episode: "Episode") -> str:
    """Format episode as Markdown.

    Args:
        episode: The Episode to format.

    Returns:
        Markdown-formatted string.
    """
    lines = []

    # Title
    lines.append(f"# {episode.title}")
    lines.append("")

    # Metadata
    meta = [f"**Source:** {episode.source_name}"]
    if episode.duration_minutes:
        hours, mins = divmod(episode.duration_minutes, 60)
        if hours:
            meta.append(f"**Duration:** {hours}h {mins}min")
        else:
            meta.append(f"**Duration:** {mins} min")
    if episode.guests:
        meta.append(f"**Guests:** {', '.join(episode.guests)}")
    if episode.url:
        meta.append(f"**Link:** [{episode.url}]({episode.url})")

    lines.append(" | ".join(meta))
    lines.append("")

    # Tags
    if episode.tags:
        lines.append(" ".join([f"`#{tag}`" for tag in episode.tags]))
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(episode.summary)
    lines.append("")

    # Group nuggets by type
    nuggets_by_type: dict[str, list] = {}
    for nugget in sorted(episode.nuggets, key=lambda n: -n.importance):
        nugget_type = nugget.type.value
        if nugget_type not in nuggets_by_type:
            nuggets_by_type[nugget_type] = []
        nuggets_by_type[nugget_type].append(nugget)

    type_labels = {
        "action": "Action Items",
        "insight": "Insights",
        "quote": "Quotes",
        "concept": "Concepts",
        "story": "Stories",
    }
    type_icons = {
        "action": "✅",
        "insight": "💡",
        "quote": "💬",
        "concept": "📖",
        "story": "📚",
    }

    for nugget_type in ["action", "insight", "quote", "concept", "story"]:
        if nugget_type not in nuggets_by_type:
            continue
        nuggets = nuggets_by_type[nugget_type]
        label = type_labels.get(nugget_type, nugget_type.title())
        icon = type_icons.get(nugget_type, "•")

        lines.append(f"## {icon} {label}")
        lines.append("")

        for nugget in nuggets:
            # Star rating if present
            stars = "⭐" * (nugget.stars or 0) if nugget.stars else ""

            # Main content
            content = f"- **{nugget.content}**"
            if stars:
                content += f" {stars}"

            # Speaker and timestamp
            meta_parts = []
            if nugget.speaker:
                meta_parts.append(nugget.speaker)
            if nugget.timestamp:
                meta_parts.append(f"[{nugget.timestamp}]")
            if meta_parts:
                content += f" — {' '.join(meta_parts)}"

            lines.append(content)

            # Context
            if nugget.context:
                lines.append(f"  - *{nugget.context}*")

        lines.append("")

    # Personal notes
    lines.append("## Notes")
    lines.append("")
    if episode.personal_notes:
        lines.append(episode.personal_notes)
    else:
        lines.append("*Add your notes here*")
    lines.append("")

    return "\n".join(lines)


def export_to_markdown(
    episode: "Episode",
    output_path: Path | str | None = None,
) -> Path:
    """Export episode to Markdown file.

    Args:
        episode: The Episode to export.
        output_path: Output file path. If None, uses data/exports/{id}.md.

    Returns:
        Path to the created file.
    """
    if output_path is None:
        exports_dir = Path("data/exports")
        exports_dir.mkdir(parents=True, exist_ok=True)
        output_path = exports_dir / f"{episode.id}.md"
    else:
        output_path = Path(output_path)

    content = format_for_markdown(episode)
    output_path.write_text(content, encoding="utf-8")

    return output_path
```

**Step 2: Update export/__init__.py**

Add to `src/nuggets/export/__init__.py`:

```python
from nuggets.export.markdown import export_to_markdown, format_for_markdown
```

---

## Task 2: Add Collection Export

**Files:**
- Create: `src/nuggets/export/collection.py`

**Step 1: Create collection export module**

```python
"""Collection export for multiple nuggets."""

from __future__ import annotations

from pathlib import Path
from datetime import date


def format_collection_markdown(
    nuggets: list[dict],
    title: str = "Nuggets Collection",
    group_by: str | None = None,
) -> str:
    """Format a collection of nuggets as Markdown.

    Args:
        nuggets: List of nugget dicts from index.
        title: Title for the collection.
        group_by: Optional grouping: "topic", "source", "type", "date".

    Returns:
        Markdown string.
    """
    lines = [f"# {title}", "", f"*{len(nuggets)} nuggets*", ""]

    if not nuggets:
        lines.append("*No nuggets found.*")
        return "\n".join(lines)

    type_icons = {
        "insight": "💡",
        "action": "✅",
        "quote": "💬",
        "concept": "📖",
        "story": "📚",
    }

    if group_by:
        # Group nuggets
        groups: dict[str, list] = {}
        for n in nuggets:
            key = n.get(group_by, "Other") or "Other"
            if key not in groups:
                groups[key] = []
            groups[key].append(n)

        # Sort groups
        for group_name in sorted(groups.keys()):
            group_nuggets = groups[group_name]
            lines.append(f"## {group_name}")
            lines.append("")

            for n in group_nuggets:
                _format_nugget(n, lines, type_icons)

            lines.append("")
    else:
        # Flat list
        for n in nuggets:
            _format_nugget(n, lines, type_icons)

    return "\n".join(lines)


def _format_nugget(n: dict, lines: list[str], type_icons: dict) -> None:
    """Format a single nugget and append to lines."""
    icon = type_icons.get(n.get("type", ""), "•")
    stars = "⭐" * (n.get("stars") or 0) if n.get("stars") else ""
    content = n.get("content", "")

    line = f"- {icon} **{content}**"
    if stars:
        line += f" {stars}"

    lines.append(line)

    # Source and date
    source = n.get("source_name", "")
    date_str = n.get("date", "")
    if source or date_str:
        meta = f"  - *{source}"
        if date_str:
            meta += f" ({date_str})"
        meta += "*"
        lines.append(meta)


def export_collection_markdown(
    nuggets: list[dict],
    output_path: Path | str,
    title: str = "Nuggets Collection",
    group_by: str | None = None,
) -> Path:
    """Export nugget collection to Markdown file.

    Args:
        nuggets: List of nugget dicts.
        output_path: Output file path.
        title: Title for the collection.
        group_by: Optional grouping.

    Returns:
        Path to created file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = format_collection_markdown(nuggets, title, group_by)
    output_path.write_text(content, encoding="utf-8")

    return output_path
```

---

## Task 3: Extend Export CLI Command

**Files:**
- Modify: `src/nuggets/cli.py`

**Step 1: Update export command with filter options**

Replace the export command with:

```python
@main.command(name="export")
@click.argument("episode_id", required=False)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["apple-notes", "markdown", "json"]),
    default="markdown",
    help="Export format (default: markdown)",
)
@click.option("--folder", default="Podcast Nuggets", help="Apple Notes folder name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--stars", type=int, help="Filter by minimum stars (1-3)")
@click.option("--topic", help="Filter by topic")
@click.option("--source", help="Filter by source name")
@click.option("--best-of", is_flag=True, help="Export only starred nuggets (best of)")
@click.option("--group-by", type=click.Choice(["topic", "source", "type"]), help="Group nuggets by field")
def export_cmd(
    episode_id: str | None,
    output_format: str,
    folder: str,
    output: str | None,
    stars: int | None,
    topic: str | None,
    source: str | None,
    best_of: bool,
    group_by: str | None,
) -> None:
    """Export nuggets to various formats.

    Examples:
        nuggets export ep123                    # Single episode to Markdown
        nuggets export ep123 --format apple-notes
        nuggets export --best-of               # All starred nuggets
        nuggets export --topic sleep           # All sleep nuggets
        nuggets export --stars 3 --group-by topic  # 3-star grouped by topic
    """
    import json
    from nuggets.models import Episode
    from nuggets.index import IndexManager

    # Single episode mode
    if episode_id:
        _export_single_episode(episode_id, output_format, folder, output)
        return

    # Collection mode - requires filters
    if not (stars or topic or source or best_of):
        console.print("[red]Error:[/] Specify episode_id or use filters (--stars, --topic, --source, --best-of)")
        return

    # Load index
    manager = IndexManager()
    lib_index = manager.load_index()

    if lib_index is None:
        console.print("[red]Error:[/] No index found. Run: nuggets index rebuild")
        return

    # Apply filters
    results = lib_index.entries

    if best_of:
        results = [e for e in results if e.stars is not None]

    if stars:
        results = [e for e in results if (e.stars or 0) >= stars]

    if topic:
        results = [e for e in results if e.topic and topic.lower() in e.topic.lower()]

    if source:
        results = [e for e in results if source.lower() in e.source_name.lower()]

    if not results:
        console.print("[yellow]No nuggets match the filters.[/]")
        return

    # Convert to dicts
    nuggets = [
        {
            "content": e.content,
            "type": e.type.value if hasattr(e.type, "value") else e.type,
            "stars": e.stars,
            "topic": e.topic,
            "source_name": e.source_name,
            "date": e.date.isoformat() if hasattr(e.date, "isoformat") else str(e.date),
        }
        for e in results
    ]

    # Build title
    title_parts = []
    if best_of:
        title_parts.append("Best Of")
    if stars:
        title_parts.append(f"{stars}+ Stars")
    if topic:
        title_parts.append(topic.title())
    if source:
        title_parts.append(source)
    title = " - ".join(title_parts) if title_parts else "Nuggets Collection"

    # Export
    if output_format == "markdown":
        from nuggets.export.collection import export_collection_markdown
        from datetime import date

        if output is None:
            slug = title.lower().replace(" ", "-").replace("/", "-")[:30]
            output = f"data/exports/{date.today().isoformat()}-{slug}.md"

        path = export_collection_markdown(nuggets, output, title, group_by)
        console.print(f"[green]✓[/] Exported {len(nuggets)} nuggets to: [cyan]{path}[/]")

    elif output_format == "json":
        from datetime import date

        if output is None:
            slug = title.lower().replace(" ", "-").replace("/", "-")[:30]
            output = f"data/exports/{date.today().isoformat()}-{slug}.json"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"title": title, "nuggets": nuggets}, indent=2), encoding="utf-8")
        console.print(f"[green]✓[/] Exported {len(nuggets)} nuggets to: [cyan]{output_path}[/]")

    else:
        console.print(f"[red]Error:[/] Collection export to {output_format} not supported. Use --format markdown or json.")


def _export_single_episode(episode_id: str, output_format: str, folder: str, output: str | None) -> None:
    """Export a single episode."""
    import json
    from nuggets.models import Episode

    # Find in analysis/ directory
    analysis_dir = Path("data/analysis")
    episode_file = None

    for f in analysis_dir.rglob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("id") == episode_id:
                episode_file = f
                break
        except (json.JSONDecodeError, KeyError):
            continue

    # Fallback to old location
    if episode_file is None:
        nuggets_dir = Path("data/nuggets")
        if (nuggets_dir / f"{episode_id}.json").exists():
            episode_file = nuggets_dir / f"{episode_id}.json"
        else:
            matches = list(nuggets_dir.glob(f"*{episode_id}*.json"))
            if len(matches) == 1:
                episode_file = matches[0]
            elif len(matches) > 1:
                console.print(f"[red]Error:[/] Multiple matches found:")
                for m in matches:
                    console.print(f"  - {m.stem}")
                return
            else:
                console.print(f"[red]Error:[/] Episode not found: {episode_id}")
                return

    # Load episode
    with open(episode_file, encoding="utf-8") as f:
        data = json.load(f)
    episode = Episode.model_validate(data)

    if output_format == "apple-notes":
        from nuggets.export import export_to_apple_notes

        with console.status("[bold blue]Exporting to Apple Notes..."):
            try:
                export_to_apple_notes(episode, folder=folder)
            except RuntimeError as e:
                console.print(f"[red]Error:[/] {e}")
                return
            except Exception as e:
                console.print(f"[red]Error:[/] {e}")
                return

        console.print(f"[green]✓[/] Exported to Apple Notes folder: [cyan]{folder}[/]")

    elif output_format == "markdown":
        from nuggets.export.markdown import export_to_markdown

        path = export_to_markdown(episode, output)
        console.print(f"[green]✓[/] Exported to: [cyan]{path}[/]")

    elif output_format == "json":
        output_path = Path(output) if output else Path(f"data/exports/{episode.id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(data if isinstance(data, str) else json.dumps(data, indent=2), encoding="utf-8")
        console.print(f"[green]✓[/] Exported to: [cyan]{output_path}[/]")
```

---

## Task 4: Add Export Tests

**Files:**
- Create: `tests/test_export.py`

**Step 1: Create tests**

```python
"""Tests for export functionality."""

import json
from pathlib import Path

import pytest

from nuggets.models import Episode, Nugget, NuggetType


class TestMarkdownExport:
    """Tests for Markdown export."""

    def test_format_episode(self):
        """Format episode as Markdown."""
        from nuggets.export.markdown import format_for_markdown

        episode = Episode(
            id="test-123",
            title="Test Episode",
            source_name="Test Show",
            source_type="youtube",
            summary="A test summary.",
            nuggets=[
                Nugget(content="Test insight", type=NuggetType.INSIGHT, importance=4),
                Nugget(content="Test quote", type=NuggetType.QUOTE, importance=3, stars=2),
            ],
        )

        md = format_for_markdown(episode)

        assert "# Test Episode" in md
        assert "Test Show" in md
        assert "Test insight" in md
        assert "Test quote" in md
        assert "⭐⭐" in md  # 2 stars

    def test_export_to_file(self, tmp_path):
        """Export episode to file."""
        from nuggets.export.markdown import export_to_markdown

        episode = Episode(
            id="test-123",
            title="Test Episode",
            source_name="Test Show",
            source_type="youtube",
            summary="A test summary.",
            nuggets=[],
        )

        output = tmp_path / "test.md"
        result = export_to_markdown(episode, output)

        assert result == output
        assert output.exists()
        assert "# Test Episode" in output.read_text()


class TestCollectionExport:
    """Tests for collection export."""

    def test_format_collection(self):
        """Format collection as Markdown."""
        from nuggets.export.collection import format_collection_markdown

        nuggets = [
            {"content": "First nugget", "type": "insight", "stars": 3, "source_name": "Show A", "date": "2024-01-15"},
            {"content": "Second nugget", "type": "quote", "stars": 2, "source_name": "Show B", "date": "2024-01-16"},
        ]

        md = format_collection_markdown(nuggets, "My Collection")

        assert "# My Collection" in md
        assert "First nugget" in md
        assert "Second nugget" in md
        assert "⭐⭐⭐" in md

    def test_format_grouped(self):
        """Format collection grouped by topic."""
        from nuggets.export.collection import format_collection_markdown

        nuggets = [
            {"content": "Sleep tip", "type": "insight", "topic": "sleep", "source_name": "A", "date": "2024-01-15"},
            {"content": "Productivity tip", "type": "insight", "topic": "productivity", "source_name": "B", "date": "2024-01-15"},
        ]

        md = format_collection_markdown(nuggets, "Grouped", group_by="topic")

        assert "## productivity" in md
        assert "## sleep" in md

    def test_export_to_file(self, tmp_path):
        """Export collection to file."""
        from nuggets.export.collection import export_collection_markdown

        nuggets = [
            {"content": "Test", "type": "insight", "source_name": "Test", "date": "2024-01-15"},
        ]

        output = tmp_path / "collection.md"
        result = export_collection_markdown(nuggets, output, "Test Collection")

        assert result == output
        assert output.exists()
```

**Step 2: Run tests**

```bash
source .venv/bin/activate && pytest tests/test_export.py -v
```

**Step 3: Commit**

```bash
git add src/nuggets/export/ tests/test_export.py src/nuggets/cli.py
git commit -m "feat: add flexible export with filters and Markdown format"
```

---

## Summary

Phase 4 complete. We now have:

- [x] `nuggets export <id>` - Export single episode
- [x] `nuggets export --best-of` - Export all starred nuggets
- [x] `nuggets export --stars 3` - Export by minimum stars
- [x] `nuggets export --topic sleep` - Export by topic
- [x] `nuggets export --group-by topic` - Group collection output
- [x] Markdown export format
- [x] Collection export utilities
- [x] Test coverage

**Next:** Phase 5 - Claude Code Skills
