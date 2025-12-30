"""Command-line interface for Podcast Nuggets.

Simple CLI for transcribing, analyzing, and exporting podcast nuggets.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _format_duration(seconds: int | None) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    if seconds is None:
        return "Unknown"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


@click.group()
@click.version_option()
def main() -> None:
    """Podcast Nuggets - Extract valuable insights from podcasts and videos."""
    pass


@main.command()
@click.option("--apple", "source_apple", type=str, help="Podcast name from Apple Podcasts")
@click.option("--youtube", "source_youtube", type=str, help="YouTube URL")
@click.option("--file", "source_file", type=click.Path(exists=True), help="Audio file path")
@click.option("--model", default="large-v3", help="Whisper model to use")
@click.option("--language", default="sv", help="Language code (default: sv)")
def transcribe(
    source_apple: str | None,
    source_youtube: str | None,
    source_file: str | None,
    model: str,
    language: str,
) -> None:
    """Transcribe audio from various sources.

    Examples:
        nuggets transcribe --apple "Huberman Lab"
        nuggets transcribe --youtube "https://youtube.com/watch?v=..."
        nuggets transcribe --file episode.mp3
    """
    if source_apple:
        console.print(f"[blue]Transcribing from Apple Podcasts:[/] {source_apple}")
        # TODO: Implement Apple Podcasts transcription
        console.print("[yellow]Apple Podcasts transcription not yet implemented[/]")

    elif source_youtube:
        console.print(f"[blue]Transcribing from YouTube:[/] {source_youtube}")
        # TODO: Implement YouTube transcription
        console.print("[yellow]YouTube transcription not yet implemented[/]")

    elif source_file:
        console.print(f"[blue]Transcribing file:[/] {source_file}")
        # TODO: Implement file transcription
        console.print("[yellow]File transcription not yet implemented[/]")

    else:
        console.print("[red]Error:[/] Specify a source with --apple, --youtube, or --file")
        raise SystemExit(1)


def _display_nuggets(nuggets: list, limit: int = 5) -> None:
    """Display nuggets in a formatted table."""
    from nuggets.models import Nugget

    # Sort by importance
    sorted_nuggets = sorted(nuggets, key=lambda n: n.importance, reverse=True)

    table = Table(title=f"Top Nuggets ({min(limit, len(nuggets))} of {len(nuggets)})")
    table.add_column("Type", style="cyan", width=8)
    table.add_column("Content", style="white")
    table.add_column("Rating", justify="center", width=8)

    type_icons = {
        "insight": "\U0001f4a1",  # lightbulb
        "action": "\u2705",  # checkmark
        "quote": "\U0001f4ac",  # speech bubble
        "concept": "\U0001f4d6",  # book
        "story": "\U0001f4d6",  # book
    }

    for nugget in sorted_nuggets[:limit]:
        icon = type_icons.get(nugget.type.value, "")
        stars = "\u2b50" * nugget.importance
        content = nugget.content
        if len(content) > 80:
            content = content[:77] + "..."
        if nugget.timestamp:
            content = f"[{nugget.timestamp}] {content}"
        table.add_row(f"{icon} {nugget.type.value}", content, stars)

    console.print(table)


@main.command()
@click.argument("transcript", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for nuggets JSON")
def analyze(transcript: str, output: str | None) -> None:
    """Analyze a transcript and extract nuggets.

    Example:
        nuggets analyze data/transcripts/huberman-2024-01-15.txt
    """
    from nuggets.analyze import analyze_transcript_file, create_episode, save_episode
    from nuggets.models import SourceType

    transcript_path = Path(transcript)

    with console.status("[bold blue]Analyzing transcript...") as status:

        def progress(msg: str) -> None:
            status.update(f"[bold blue]{msg}")

        try:
            analysis, metadata = analyze_transcript_file(
                transcript_path,
                progress_callback=progress,
            )
        except ValueError as e:
            console.print(f"[red]Error:[/] {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]Error analyzing:[/] {e}")
            raise SystemExit(1)

    # Display results
    console.print()
    console.print(f"[green]\u2713[/] Analyzed: [bold]{metadata.get('title', transcript_path.stem)}[/]")
    console.print(f"[green]\u2713[/] Found {len(analysis.nuggets)} nuggets")
    console.print(f"[green]\u2713[/] Tags: {', '.join(analysis.suggested_tags)}")

    # Show summary
    console.print()
    console.print(Panel(analysis.summary, title="Summary", border_style="green"))

    # Show top nuggets
    console.print()
    _display_nuggets(analysis.nuggets, limit=5)

    # Determine source type
    source_type = SourceType.YOUTUBE
    if "youtube" in str(transcript_path):
        source_type = SourceType.YOUTUBE
    elif "podcast" in str(transcript_path):
        source_type = SourceType.PODCAST

    # Create and save episode
    episode = create_episode(analysis, metadata, transcript_path, source_type)

    if output:
        output_path = Path(output)
    else:
        output_path = save_episode(episode)

    console.print()
    console.print(f"[green]\u2713[/] Saved to: [cyan]{output_path}[/]")
    console.print(f"[dim]Export with: nuggets export {episode.id}[/]")


@main.command(name="export")
@click.argument("episode_id")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["apple-notes", "markdown", "json"]),
    default="apple-notes",
    help="Export format (default: apple-notes)",
)
@click.option("--folder", default="Podcast Nuggets", help="Apple Notes folder name")
@click.option("--output", "-o", type=click.Path(), help="Output file path (for markdown/json)")
def export_cmd(episode_id: str, output_format: str, folder: str, output: str | None) -> None:
    """Export an analyzed episode to various formats.

    Examples:
        nuggets export youtube-2025-12-25-hLIvhTiE
        nuggets export youtube-2025-12-25-hLIvhTiE --format apple-notes --folder "Podcasts"
        nuggets export youtube-2025-12-25-hLIvhTiE --format json
    """
    import json
    from nuggets.models import Episode

    # Find the nuggets file
    nuggets_dir = Path("data/nuggets")
    nuggets_file = nuggets_dir / f"{episode_id}.json"

    if not nuggets_file.exists():
        # Try partial match
        matches = list(nuggets_dir.glob(f"*{episode_id}*.json"))
        if len(matches) == 1:
            nuggets_file = matches[0]
        elif len(matches) > 1:
            console.print(f"[red]Error:[/] Multiple matches found:")
            for m in matches:
                console.print(f"  - {m.stem}")
            raise SystemExit(1)
        else:
            console.print(f"[red]Error:[/] Episode not found: {episode_id}")
            console.print(f"[dim]Looking in: {nuggets_dir}[/]")
            raise SystemExit(1)

    # Load episode
    with open(nuggets_file, encoding="utf-8") as f:
        data = json.load(f)
    episode = Episode.model_validate(data)

    if output_format == "apple-notes":
        from nuggets.export import export_to_apple_notes

        with console.status("[bold blue]Exporting to Apple Notes..."):
            try:
                export_to_apple_notes(episode, folder=folder)
            except RuntimeError as e:
                console.print(f"[red]Error:[/] {e}")
                raise SystemExit(1)
            except Exception as e:
                console.print(f"[red]Error exporting:[/] {e}")
                raise SystemExit(1)

        console.print(f"[green]✓[/] Exported to Apple Notes")
        console.print(f"[dim]Folder: {folder}[/]")
        console.print(f"[dim]Note: {episode.title}[/]")

    elif output_format == "json":
        output_path = Path(output) if output else Path(f"data/exports/{episode_id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(episode.model_dump_json(indent=2))
        console.print(f"[green]✓[/] Exported to: [cyan]{output_path}[/]")

    elif output_format == "markdown":
        console.print("[yellow]Markdown export not yet implemented[/]")
        console.print("[dim]Use --format apple-notes instead[/]")


@main.command(name="list")
@click.option("--source", help="Filter by source name")
@click.option("--tag", help="Filter by tag")
def list_cmd(source: str | None, tag: str | None) -> None:
    """List all analyzed episodes.

    Example:
        nuggets list
        nuggets list --source "Huberman Lab"
        nuggets list --tag sleep
    """
    console.print("[blue]Listing episodes...[/]")
    # TODO: Implement list
    console.print("[yellow]List not yet implemented[/]")


@main.command()
@click.argument("query")
@click.option("--type", "nugget_type", help="Filter by nugget type")
def search(query: str, nugget_type: str | None) -> None:
    """Search through your nuggets.

    Example:
        nuggets search "dopamine"
        nuggets search "morning routine" --type action
    """
    console.print(f"[blue]Searching for:[/] {query}")
    # TODO: Implement search
    console.print("[yellow]Search not yet implemented[/]")


# Config command group
@main.group()
def config() -> None:
    """Manage analysis configurations.

    Save and reuse theme configurations for different podcast types.
    """
    pass


@config.command(name="list")
def config_list() -> None:
    """List all saved configurations.

    Example:
        nuggets config list
    """
    from nuggets.config import list_configs

    configs = list_configs()

    if not configs:
        console.print("[dim]No saved configurations.[/]")
        console.print("[dim]Use 'nuggets config save <name>' after interactive analysis.[/]")
        return

    table = Table(title="Saved Configurations")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Themes", justify="center")

    for cfg in configs:
        table.add_row(
            cfg["name"],
            cfg["description"] or "[dim]No description[/]",
            str(cfg["theme_count"]),
        )

    console.print(table)


@config.command(name="show")
@click.argument("name")
def config_show(name: str) -> None:
    """Show details of a saved configuration.

    Example:
        nuggets config show huberman-style
    """
    from nuggets.config import load_config
    from nuggets.models import DetailLevel

    try:
        cfg = load_config(name)
    except FileNotFoundError:
        console.print(f"[red]Error:[/] Config not found: {name}")
        raise SystemExit(1)

    console.print(f"\n[bold cyan]{cfg.name}[/]")
    if cfg.description:
        console.print(f"[dim]{cfg.description}[/]")
    console.print(f"Mode: {cfg.mode}")
    console.print(f"Default detail level: {cfg.default_detail_level.value}")

    if cfg.theme_configs:
        console.print("\n[bold]Theme Configurations:[/]")
        table = Table()
        table.add_column("Theme", style="white")
        table.add_column("Enabled", justify="center")
        table.add_column("Detail Level", justify="center")

        detail_names = {
            1: "Minimal",
            2: "Light",
            3: "Standard",
            4: "Detailed",
            5: "Exhaustive",
        }

        for tc in cfg.theme_configs:
            enabled = "[green]Yes[/]" if tc.enabled else "[red]No[/]"
            level_name = detail_names.get(tc.detail_level.value, str(tc.detail_level.value))
            table.add_row(tc.theme_name, enabled, f"{level_name} ({tc.detail_level.value})")

        console.print(table)


@config.command(name="delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this config?")
def config_delete(name: str) -> None:
    """Delete a saved configuration.

    Example:
        nuggets config delete huberman-style
    """
    from nuggets.config import delete_config

    if delete_config(name):
        console.print(f"[green]Deleted:[/] {name}")
    else:
        console.print(f"[red]Error:[/] Config not found: {name}")
        raise SystemExit(1)


# Index command group
@main.group()
def index() -> None:
    """Manage the library index."""
    pass


@index.command(name="rebuild")
def index_rebuild() -> None:
    """Rebuild the library index from analysis files."""
    from nuggets.index import IndexManager

    manager = IndexManager()

    with console.status("[bold blue]Rebuilding index..."):
        lib_index = manager.build_index()
        manager.save_index(lib_index)

    console.print("[green]\u2713[/] Index rebuilt")
    console.print(f"  Episodes: {lib_index.total_episodes}")
    console.print(f"  Nuggets: {lib_index.total_nuggets}")
    sources = [s for s in lib_index.sources if s]  # Filter empty strings
    console.print(f"  Sources: {', '.join(sources) if sources else 'None'}")
    console.print(f"[dim]Saved to: data/library/index.json[/]")


@index.command(name="stats")
def index_stats() -> None:
    """Show library statistics."""
    from nuggets.index import IndexManager

    manager = IndexManager()
    lib_index = manager.load_index()

    if lib_index is None or lib_index.total_nuggets == 0:
        console.print("[yellow]No index found. Run 'nuggets index rebuild' first.[/]")
        return

    stats = manager.get_stats(lib_index)

    console.print()
    console.print("[bold]Podcast Nuggets Library[/]")
    console.print("\u2500" * 40)
    console.print(f"Episodes:     {lib_index.total_episodes}")
    console.print(f"Nuggets:      {lib_index.total_nuggets}")

    # Stars breakdown
    starred = stats.get("starred_count", 0)
    console.print(f"  Starred:    {starred}")
    console.print(f"  Unrated:    {lib_index.total_nuggets - starred}")

    # Top sources
    if stats.get("by_source"):
        console.print()
        console.print("[bold]Top sources:[/]")
        for source, count in list(stats["by_source"].items())[:5]:
            source_name = source if source else "(unknown)"
            console.print(f"  {source_name:20} {count} nuggets")

    # Top topics
    if stats.get("by_topic"):
        console.print()
        console.print("[bold]Top topics:[/]")
        for topic, count in list(stats["by_topic"].items())[:5]:
            console.print(f"  {topic:20} {count} nuggets")


@main.command()
@click.argument("url")
@click.option(
    "--transcript-only",
    is_flag=True,
    help="Only fetch transcript, skip analysis",
)
@click.option(
    "--whisper",
    "force_whisper",
    is_flag=True,
    help="Force Whisper transcription (skip YouTube captions)",
)
@click.option(
    "--language",
    "-l",
    default="sv",
    help="Preferred caption language (default: sv)",
)
@click.option(
    "--model",
    default="large-v3",
    help="Whisper model for fallback transcription",
)
def youtube(
    url: str,
    transcript_only: bool,
    force_whisper: bool,
    language: str,
    model: str,
) -> None:
    """Process a YouTube video: fetch transcript and extract nuggets.

    This is the primary way to process YouTube content. It will:
    1. Fetch video metadata (title, channel, duration)
    2. Get transcript (YouTube captions or Whisper fallback)
    3. Optionally analyze with Claude to extract nuggets

    Examples:
        nuggets youtube "https://youtube.com/watch?v=abc123"
        nuggets youtube "https://youtu.be/abc123" --transcript-only
        nuggets youtube "https://youtube.com/watch?v=abc123" --whisper
    """
    from nuggets.transcribe.youtube import process_youtube_video, save_transcript

    languages = [language, "en"] if language != "en" else ["en"]

    with console.status("[bold blue]Processing YouTube video...") as status:

        def progress(msg: str) -> None:
            status.update(f"[bold blue]{msg}")

        try:
            result = process_youtube_video(
                url,
                force_whisper=force_whisper,
                languages=languages,
                whisper_model=model,
                whisper_language=language,
                progress_callback=progress,
            )
        except ValueError as e:
            console.print(f"[red]Error:[/] {e}")
            raise SystemExit(1)
        except Exception as e:
            console.print(f"[red]Error processing video:[/] {e}")
            raise SystemExit(1)

    # Display results
    console.print()
    console.print(f"[green]\u2713[/] Video: [bold]{result['title']}[/]")
    console.print(f"[green]\u2713[/] Channel: {result['channel']}")
    console.print(f"[green]\u2713[/] Duration: {_format_duration(result.get('duration'))}")
    console.print(
        f"[green]\u2713[/] Transcript: {result['transcript_source'].replace('_', ' ')}"
    )

    # Save raw data to library structure
    from nuggets.transcribe.youtube import save_raw_youtube
    raw_filepath = save_raw_youtube(result)
    console.print(f"[green]\u2713[/] Raw data saved to: [cyan]{raw_filepath}[/]")

    # Also save legacy transcript for backwards compatibility
    filepath = save_transcript(result)

    # Show transcript preview
    transcript_lines = result["transcript"].split("\n")
    preview_lines = transcript_lines[:10]
    if len(transcript_lines) > 10:
        preview_lines.append(f"... ({len(transcript_lines) - 10} more lines)")

    console.print()
    console.print(Panel("\n".join(preview_lines), title="Transcript Preview", border_style="dim"))

    if transcript_only:
        console.print()
        console.print("[dim]Skipping analysis (--transcript-only)[/]")
        console.print(f"[dim]To analyze later: nuggets analyze {filepath}[/]")
    else:
        # Analyze with Claude
        from nuggets.analyze import extract_nuggets, save_episode, create_episode
        from nuggets.models import SourceType

        console.print()

        with console.status("[bold blue]Analyzing with Claude...") as status:

            def analysis_progress(msg: str) -> None:
                status.update(f"[bold blue]{msg}")

            try:
                analysis = extract_nuggets(
                    transcript=result["transcript"],
                    source_name=result.get("channel", "Unknown"),
                    title=result.get("title", "Unknown"),
                    duration_minutes=result.get("duration", 0) // 60 if result.get("duration") else None,
                    progress_callback=analysis_progress,
                )
            except ValueError as e:
                console.print(f"[yellow]Analysis skipped:[/] {e}")
                console.print(f"[dim]To analyze later: nuggets analyze {filepath}[/]")
                return
            except Exception as e:
                console.print(f"[yellow]Analysis failed:[/] {e}")
                console.print(f"[dim]To analyze later: nuggets analyze {filepath}[/]")
                return

        # Display results
        console.print(f"[green]\u2713[/] Found {len(analysis.nuggets)} nuggets")
        console.print(f"[green]\u2713[/] Tags: {', '.join(analysis.suggested_tags)}")

        # Show summary
        console.print()
        console.print(Panel(analysis.summary, title="Summary", border_style="green"))

        # Show top nuggets
        console.print()
        _display_nuggets(analysis.nuggets, limit=5)

        # Create and save episode
        metadata = {
            "title": result.get("title"),
            "channel": result.get("channel"),
            "duration": _format_duration(result.get("duration")),
            "url": result.get("url"),
            "video id": result.get("video_id"),
        }
        episode = create_episode(analysis, metadata, filepath, SourceType.YOUTUBE)
        nuggets_path = save_episode(episode)

        console.print()
        console.print(f"[green]\u2713[/] Nuggets saved to: [cyan]{nuggets_path}[/]")
        console.print(f"[dim]Export with: nuggets export {episode.id}[/]")


if __name__ == "__main__":
    main()
