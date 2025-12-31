# Claude Code Development Reference

Quick reference for working on podcast-nuggets.

## Project Overview

CLI tool to extract valuable insights ("nuggets") from YouTube videos and podcasts, building a personal knowledge library ("2nd brain").

**Owner:** Pontus (personal learning tool)

## Architecture

```
src/nuggets/
├── cli.py                 # Click CLI (main entry point)
├── models.py              # Pydantic models: Episode, Nugget, Theme, AnalysisConfig
├── config.py              # Config save/load for reusable analysis settings
├── categories.py          # Topic and wisdom type constants
├── library.py             # Library path utilities
├── index.py               # Index management and search
├── curation.py            # Star rating utilities
├── transcribe/
│   ├── youtube.py         # YouTube transcript fetching (primary)
│   └── whisper.py         # MLX Whisper fallback transcription
├── analyze/
│   └── extractor.py       # Claude API analysis (extract_nuggets, create_episode)
└── export/
    ├── apple_notes.py     # AppleScript export to Apple Notes
    ├── markdown.py        # Markdown export
    └── collection.py      # Multi-nugget collection export
```

## Data Storage

```
data/
├── raw/                   # Untouched transcripts
│   ├── youtube/{channel}/{date}-{id}.json
│   └── twitter/{author}/{date}-{id}.json
├── analysis/              # Processed nuggets
│   ├── youtube/{channel}/{date}-{id}.json
│   └── twitter/{author}/{date}-{id}.json
├── library/               # Aggregated index
│   └── index.json
└── exports/               # Exported files
```

## CLI Commands

```bash
# YouTube processing
nuggets youtube <url>                    # Process YouTube video
nuggets youtube <url> --transcript-only  # Just fetch transcript

# Twitter/X processing
nuggets twitter <url>                    # Process Twitter thread/article
nuggets twitter <url> --transcript-only  # Just fetch content

# Index management
nuggets index rebuild                    # Rebuild library index
nuggets index stats                      # Show library statistics

# Browsing
nuggets list                             # List all episodes
nuggets list --source "Huberman"         # Filter by source
nuggets list --year 2024                 # Filter by year

# Search
nuggets search <query>                   # Full-text search
nuggets search --topic sleep             # Filter by topic
nuggets search --stars 2                 # Filter by min stars
nuggets search --type insight            # Filter by nugget type

# Curation
nuggets star <nugget-id> <1-3>           # Rate a nugget
nuggets star --interactive               # Interactive rating mode

# Export
nuggets export <episode_id>              # Export single episode (Markdown)
nuggets export <id> --format apple-notes # Export to Apple Notes
nuggets export --best-of                 # Export all starred nuggets
nuggets export --topic sleep             # Export by topic
nuggets export --stars 3 --group-by topic  # Export grouped
```

## Claude Code Skills

Three skills are available for standardized workflows:

### `/nuggets-ingest`
Process new content into the library.
- Fetch transcript
- Analyze with Claude (auto or interactive)
- Categorize nuggets with topic + wisdom_type
- Update index

### `/nuggets-curate`
Review and rate nuggets.
- Star rating: 1 (worth remembering), 2 (important), 3 (goated)
- Interactive or batch mode
- Export best-of compilations

### `/nuggets-reflect`
Query and discuss the knowledge library.
- "What do I know about..."
- Cross-source pattern finding
- Best-of compilations
- Time-based reflection

## Categories

**Topics** (auto-assigned by Claude):
- sleep, productivity, health, relationships, business
- creativity, learning, fitness, nutrition, mindset
- technology, parenting, finance, communication

**Wisdom Types** (auto-assigned by Claude):
- `principle` — Fundamental truth or rule
- `habit` — Concrete behavior to implement
- `mental-model` — Way of thinking
- `life-lesson` — Broad life wisdom
- `technique` — Specific method
- `warning` — Something to avoid

## Nugget Types

| Type | Icon | Description |
|------|------|-------------|
| `insight` | 💡 | Key learnings and principles |
| `quote` | 💬 | Memorable quotes |
| `action` | ✅ | Actionable advice |
| `concept` | 📖 | Definitions and mental models |
| `story` | 📚 | Illustrative examples |

## Star Rating

Personal curation system (separate from AI importance):

| Stars | Meaning |
|-------|---------|
| ⭐ | Worth remembering |
| ⭐⭐ | Important insight |
| ⭐⭐⭐ | "Goated" — Core to personal philosophy |

## Key Models

```python
class Nugget(BaseModel):
    content: str              # The insight itself
    type: NuggetType          # insight, quote, action, concept, story
    importance: int           # AI-assigned 1-5
    topic: str | None         # sleep, productivity, etc.
    wisdom_type: str | None   # principle, habit, etc.
    stars: int | None         # Personal rating 1-3
```

## Important Implementation Details

### youtube-transcript-api (v1.x)
```python
from youtube_transcript_api import YouTubeTranscriptApi
fetcher = YouTubeTranscriptApi()
transcript_list = fetcher.list(video_id)
transcript = transcript_list.find_transcript(languages)
snippets = transcript.fetch()
```

### Apple Notes Export
Uses AppleScript via `osascript`. Supports basic HTML formatting.

## Dependencies

- `youtube-transcript-api` - YouTube captions
- `yt-dlp` - Video metadata and audio download
- `mlx-whisper` - Apple Silicon transcription (optional)
- `anthropic` - Claude API for analysis
- `click` + `rich` - CLI framework
- `pydantic` - Data models

## Future Work

- [ ] HTML visualization of library
- [ ] Apple Podcasts integration
- [ ] Auto-suggest new categories
