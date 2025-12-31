"""Collection export for multiple nuggets."""

from __future__ import annotations

from pathlib import Path


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
