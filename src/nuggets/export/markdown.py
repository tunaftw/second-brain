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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_for_markdown(episode)
    output_path.write_text(content, encoding="utf-8")

    return output_path
