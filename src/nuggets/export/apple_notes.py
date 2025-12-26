"""Apple Notes export for Podcast Nuggets.

This module exports episodes to Apple Notes using AppleScript.
macOS only.
"""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nuggets.models import Episode


def detect_language(text: str) -> str:
    """Detect language from text content.

    Simple heuristic based on common words.

    Returns:
        'sv' for Swedish, 'en' for English (default).
    """
    text_lower = text.lower()

    # Swedish indicators
    swedish_words = [" och ", " att ", " det ", " som ", " för ", " med ",
                     " har ", " den ", " är ", " av ", " till ", " en "]
    swedish_count = sum(1 for word in swedish_words if word in text_lower)

    # English indicators
    english_words = [" the ", " and ", " that ", " this ", " for ", " with ",
                     " have ", " are ", " was ", " you ", " your ", " about "]
    english_count = sum(1 for word in english_words if word in text_lower)

    return "sv" if swedish_count > english_count else "en"


# Labels for different languages
LABELS = {
    "en": {
        "summary": "📝 Summary",
        "action": "✅ Action Items",
        "insight": "💡 Insights",
        "quote": "💬 Quotes",
        "concept": "📖 Concepts",
        "story": "📚 Stories",
        "notes": "✏️ My Notes",
        "open_link": "🔗 Open on YouTube",
    },
    "sv": {
        "summary": "📝 Sammanfattning",
        "action": "✅ Att göra",
        "insight": "💡 Insikter",
        "quote": "💬 Citat",
        "concept": "📖 Koncept",
        "story": "📚 Berättelser",
        "notes": "✏️ Mina anteckningar",
        "open_link": "🔗 Öppna på YouTube",
    },
}


def format_for_apple_notes(episode: "Episode") -> str:
    """Format episode as HTML for Apple Notes.

    Apple Notes supports basic HTML formatting:
    - <h1>, <h2>, <h3> for headings
    - <b>, <i> for bold/italic
    - <ul>, <li> for lists
    - <a href="..."> for links
    - <br> for line breaks

    Args:
        episode: The Episode to format.

    Returns:
        HTML-formatted string for Apple Notes.
    """
    # Detect language from summary and nuggets
    content_for_detection = episode.summary + " ".join(n.content for n in episode.nuggets)
    lang = detect_language(content_for_detection)
    labels = LABELS[lang]

    lines = []

    # Title as H1
    lines.append(f"<h1>{episode.title}</h1>")

    # Metadata block (compact, at top)
    meta_parts = [f"📺 {episode.source_name}"]
    if episode.duration_minutes:
        hours, mins = divmod(episode.duration_minutes, 60)
        if hours:
            meta_parts.append(f"⏱ {hours}h {mins}min")
        else:
            meta_parts.append(f"⏱ {mins} min")
    if episode.guests:
        meta_parts.append(f"👥 {', '.join(episode.guests)}")

    lines.append(f"<p>{' · '.join(meta_parts)}</p>")

    if episode.url:
        lines.append(f'<p><a href="{episode.url}">{labels["open_link"]}</a></p>')

    # Tags at top (Apple Notes recognizes #hashtags)
    if episode.tags:
        tag_str = " ".join([f"#{tag}" for tag in episode.tags])
        lines.append(f"<p>{tag_str}</p>")

    lines.append("<br>")

    # Summary
    lines.append(f"<h2>{labels['summary']}</h2>")
    lines.append(f"<p>{episode.summary}</p>")
    lines.append("<br>")

    # Group nuggets by type
    nuggets_by_type: dict[str, list] = {}
    for nugget in sorted(episode.nuggets, key=lambda n: -n.importance):
        nugget_type = nugget.type.value
        if nugget_type not in nuggets_by_type:
            nuggets_by_type[nugget_type] = []
        nuggets_by_type[nugget_type].append(nugget)

    # Type order
    type_order = ["action", "insight", "quote", "concept", "story"]

    # Output nuggets by type (in preferred order)
    for nugget_type in type_order:
        if nugget_type not in nuggets_by_type:
            continue
        nuggets = nuggets_by_type[nugget_type]
        label = labels.get(nugget_type, nugget_type.title())

        lines.append(f"<h2>{label}</h2>")

        for nugget in nuggets:
            # Build the nugget line (no stars - cleaner)
            parts = [f"<b>{nugget.content}</b>"]

            # Add speaker if available
            if nugget.speaker:
                parts.append(f"— {nugget.speaker}")

            # Add timestamp if available
            if nugget.timestamp:
                parts.append(f"[{nugget.timestamp}]")

            lines.append(f"<p>{' '.join(parts)}</p>")

            # Add context on separate line if available
            if nugget.context:
                lines.append(f"<p><i>↳ {nugget.context}</i></p>")

            lines.append("")  # Extra spacing between nuggets

        lines.append("<br>")

    # Personal notes section
    lines.append(f"<h2>{labels['notes']}</h2>")
    if episode.personal_notes:
        lines.append(f"<p>{episode.personal_notes}</p>")
    else:
        lines.append("<p></p>")  # Empty paragraph for easy editing

    return "\n".join(lines)


def export_to_apple_notes(
    episode: "Episode",
    folder: str = "Podcast Nuggets",
) -> bool:
    """Export episode to Apple Notes via AppleScript.

    Creates a new note in Apple Notes with the formatted episode content.

    Args:
        episode: The Episode to export.
        folder: Name of the folder in Apple Notes (created if doesn't exist).

    Returns:
        True if successful, False otherwise.

    Raises:
        RuntimeError: If not running on macOS.
        subprocess.CalledProcessError: If AppleScript fails.
    """
    if sys.platform != "darwin":
        raise RuntimeError("Apple Notes export is only available on macOS")

    html_content = format_for_apple_notes(episode)

    # Escape for AppleScript
    # Replace backslashes and quotes
    escaped_content = html_content.replace("\\", "\\\\").replace('"', '\\"')
    escaped_title = episode.title.replace("\\", "\\\\").replace('"', '\\"')
    escaped_folder = folder.replace("\\", "\\\\").replace('"', '\\"')

    # AppleScript to create note in folder
    applescript = f'''
tell application "Notes"
    -- Find or create folder
    set targetFolder to missing value
    repeat with f in folders
        if name of f is "{escaped_folder}" then
            set targetFolder to f
            exit repeat
        end if
    end repeat

    if targetFolder is missing value then
        set targetFolder to make new folder with properties {{name:"{escaped_folder}"}}
    end if

    -- Create note with HTML body
    set noteBody to "{escaped_content}"
    make new note at targetFolder with properties {{name:"{escaped_title}", body:noteBody}}

    return "success"
end tell
'''

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
        text=True,
        check=True,
    )

    return "success" in result.stdout
