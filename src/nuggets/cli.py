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
    import json as json_module
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
    results = list(lib_index.entries)

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
        output_path.write_text(
            json_module.dumps({"title": title, "nuggets": nuggets}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        console.print(f"[green]✓[/] Exported {len(nuggets)} nuggets to: [cyan]{output_path}[/]")

    else:
        console.print(f"[red]Error:[/] Collection export to {output_format} not supported. Use --format markdown or json.")


def _export_single_episode(episode_id: str, output_format: str, folder: str, output: str | None) -> None:
    """Export a single episode."""
    import json as json_module
    from nuggets.models import Episode

    # Find in analysis/ directory
    analysis_dir = Path("data/analysis")
    episode_file = None

    for f in analysis_dir.rglob("*.json"):
        try:
            data = json_module.loads(f.read_text(encoding="utf-8"))
            if data.get("id") == episode_id:
                episode_file = f
                break
        except (json_module.JSONDecodeError, KeyError):
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
                console.print("[red]Error:[/] Multiple matches found:")
                for m in matches:
                    console.print(f"  - {m.stem}")
                return
            else:
                console.print(f"[red]Error:[/] Episode not found: {episode_id}")
                return

    # Load episode
    with open(episode_file, encoding="utf-8") as f:
        data = json_module.load(f)
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
                console.print(f"[red]Error exporting:[/] {e}")
                return

        console.print(f"[green]✓[/] Exported to Apple Notes folder: [cyan]{folder}[/]")

    elif output_format == "markdown":
        from nuggets.export.markdown import export_to_markdown

        path = export_to_markdown(episode, output)
        console.print(f"[green]✓[/] Exported to: [cyan]{path}[/]")

    elif output_format == "json":
        output_path = Path(output) if output else Path(f"data/exports/{episode.id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            data if isinstance(data, str) else json_module.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        console.print(f"[green]✓[/] Exported to: [cyan]{output_path}[/]")


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
    lib_index = manager.load_index()

    if lib_index is None or lib_index.total_episodes == 0:
        console.print("[yellow]No episodes found. Run 'nuggets index rebuild' first.[/]")
        return

    # Group by episode
    episodes: dict[str, dict] = {}
    for entry in lib_index.entries:
        if entry.episode_id not in episodes:
            episodes[entry.episode_id] = {
                "source": entry.source_name,
                "date": entry.date.strftime("%Y-%m-%d"),
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
    total = len(results)
    results = results[:limit]

    if not results:
        console.print("[yellow]No episodes match filters.[/]")
        return

    # Display
    table = Table(title=f"Episodes ({len(results)} of {total})")
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Source", style="white")
    table.add_column("Nuggets", justify="center", width=8)
    table.add_column("ID", style="dim")

    for episode_id, ep in results:
        short_id = episode_id[:35] + "..." if len(episode_id) > 35 else episode_id
        table.add_row(
            ep["date"],
            ep["source"] or "(unknown)",
            str(ep["nugget_count"]),
            short_id,
        )

    console.print(table)


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
    from nuggets.models import NuggetType

    manager = IndexManager()
    lib_index = manager.load_index()

    if lib_index is None:
        console.print("[yellow]No index found. Run 'nuggets index rebuild' first.[/]")
        return

    # Convert nugget_type string to NuggetType enum if provided
    nugget_type_enum = None
    if nugget_type:
        try:
            nugget_type_enum = NuggetType(nugget_type.lower())
        except ValueError:
            valid_types = ", ".join([t.value for t in NuggetType])
            console.print(f"[red]Error:[/] Invalid nugget type '{nugget_type}'")
            console.print(f"[dim]Valid types: {valid_types}[/]")
            return

    results = manager.search(
        lib_index,
        query=query,
        topic=topic,
        stars=stars,
        source=source,
        year=year,
        nugget_type=nugget_type_enum,
    )

    if not results:
        console.print("[yellow]No nuggets found matching your search.[/]")
        return

    # Sort by importance then date
    results.sort(key=lambda x: (-(x.importance or 0), x.date))

    # Limit
    total = len(results)
    results = results[:limit]

    # Display
    console.print(f"[bold]Found {total} nuggets[/]" + (f" (showing {limit})" if total > limit else "") + "\n")

    type_icons = {
        "insight": "💡",
        "action": "✅",
        "quote": "💬",
        "concept": "📖",
        "story": "📖",
    }

    for entry in results:
        icon = type_icons.get(entry.type.value, "•")
        stars_str = "⭐" * (entry.stars or 0) if entry.stars else ""

        # Content (truncate if too long)
        content = entry.content
        if len(content) > 100:
            content = content[:97] + "..."

        console.print(f"{icon} [bold]{content}[/]")

        # Metadata line
        meta_parts = [f"[dim]{entry.source_name or 'Unknown'}[/]", f"[dim]{entry.date.strftime('%Y-%m-%d')}[/]"]
        if entry.topic:
            meta_parts.append(f"[cyan]#{entry.topic}[/]")
        if stars_str:
            meta_parts.append(stars_str)

        console.print(f"   {' • '.join(meta_parts)}")
        console.print()


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
    from nuggets.curation import get_unrated_nuggets, set_nugget_stars

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

        content = nugget["content"]
        if len(content) > 100:
            content = content[:97] + "..."

        console.print(f"{icon} [bold]{content}[/]")
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
            stars_val = int(choice)
            success = set_nugget_stars(
                nugget["episode_id"],
                nugget["nugget_index"],
                stars_val,
            )
            if success:
                console.print(f"   [green]✓ Set {'⭐' * stars_val}[/]\n")
                rated_count += 1
            else:
                console.print(f"   [red]Failed to save[/]\n")
        else:
            console.print(f"   [yellow]Skipped[/]\n")

    console.print(f"\n[bold]Done![/] Rated {rated_count} nuggets.")
    if rated_count > 0:
        console.print("[dim]Run 'nuggets index rebuild' to update the index[/]")


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
