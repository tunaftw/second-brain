# Claude Code Development Reference

Quick reference for working on podcast-nuggets.

## Project Overview

CLI tool to extract valuable insights ("nuggets") from YouTube videos and podcasts, then export to Apple Notes.

**Owner:** Pontus (personal learning tool)

## Architecture

```
src/nuggets/
├── cli.py                 # Click CLI (main entry point)
├── models.py              # Pydantic models: Episode, Nugget, Theme, AnalysisConfig
├── config.py              # Config save/load for reusable analysis settings
├── transcribe/
│   ├── youtube.py         # YouTube transcript fetching (primary)
│   └── whisper.py         # MLX Whisper fallback transcription
├── analyze/
│   └── extractor.py       # Claude API analysis (extract_nuggets, create_episode)
└── export/
    └── apple_notes.py     # AppleScript export to Apple Notes
```

## Key Workflows

### 1. YouTube Processing
```bash
nuggets youtube "https://youtube.com/watch?v=..."
```
Flow: `extract_video_id()` → `get_video_metadata()` → `get_youtube_transcript()` → (optional) `extract_nuggets()` → `save_episode()`

### 2. Apple Notes Export
```bash
nuggets export <episode_id> --format apple-notes
```
Flow: Load JSON → `format_for_apple_notes()` → `export_to_apple_notes()` (AppleScript)

## Data Storage

- `data/transcripts/youtube/` - Raw transcripts with timestamps
- `data/nuggets/` - Analyzed episodes as JSON
- `data/exports/` - Exported files
- `data/configs/` - Saved analysis configurations

## Important Implementation Details

### youtube-transcript-api (v1.x)
The API changed in v1.x. Use instance method:
```python
from youtube_transcript_api import YouTubeTranscriptApi
fetcher = YouTubeTranscriptApi()
transcript_list = fetcher.list(video_id)
transcript = transcript_list.find_transcript(languages)
snippets = transcript.fetch()
```

### Apple Notes Export
Uses AppleScript via `osascript`. Supports basic HTML:
- `<h1>`, `<h2>`, `<h3>` headings
- `<b>`, `<i>` for bold/italic
- `<ul>`, `<li>` for lists
- `<a href="...">` for links
- Tags with `#hashtag` format are recognized by Apple Notes

### Language Detection
`detect_language()` in `apple_notes.py` uses word frequency to detect Swedish vs English and adjusts UI labels accordingly. The nugget *content* language depends on how the analysis was written.

## Nugget Types

| Type | Description |
|------|-------------|
| `insight` | Key learnings and principles |
| `quote` | Memorable quotes |
| `action` | Actionable advice |
| `concept` | Definitions and mental models |
| `story` | Illustrative examples |

## CLI Commands

```bash
# YouTube processing
nuggets youtube <url>           # Process YouTube video
nuggets youtube <url> --transcript-only  # Just fetch transcript

# Analysis
nuggets analyze <transcript>    # Analyze existing transcript

# Export
nuggets export <id>             # Export to Apple Notes
nuggets export <id> --format json  # Export as JSON

# Config management
nuggets config list             # List saved configurations
nuggets config show <name>      # Show config details
nuggets config delete <name>    # Delete a config

# Not yet implemented
nuggets list                    # List episodes
nuggets search <query>          # Search nuggets
```

## Dependencies

- `youtube-transcript-api` - YouTube captions
- `yt-dlp` - Video metadata and audio download
- `mlx-whisper` - Apple Silicon transcription (optional)
- `anthropic` - Claude API for analysis
- `click` + `rich` - CLI framework

## Two-Mode Analysis System

### Standard Mode (CLI)
Run `nuggets youtube <url>` for automatic analysis via Claude API (~$0.18/run).

### Interactive Mode (Claude Code Session)
For more control, work with Claude Code directly:

1. **Fetch transcript only:**
   ```bash
   nuggets youtube <url> --transcript-only
   ```

2. **In Claude Code session:**
   - Ask: "Analysera denna podcast interaktivt"
   - Claude Code identifies 3-8 themes
   - You adjust detail levels (1-5) per theme
   - Claude Code writes nuggets JSON

3. **Export:**
   ```bash
   nuggets export <id> --format apple-notes
   ```

### Detail Levels (1-5)

| Level | Name | Description |
|-------|------|-------------|
| 1 | Minimal | Brief mention only |
| 2 | Light | Key points, 1-2 nuggets |
| 3 | Standard | Normal analysis, 2-4 nuggets |
| 4 | Detailed | Thorough, 4-6 nuggets |
| 5 | Exhaustive | All details + raw transcript segment |

### Config System

Save and reuse analysis configurations:
```bash
nuggets config list              # List saved configs
nuggets config show huberman     # Show config details
```

Configs are stored in `data/configs/` as JSON.

## Key Models

- `DetailLevel` - Enum (1-5) for extraction depth
- `Theme` - Identified theme with timestamps
- `ThemeConfig` - User's preference for a theme
- `AnalysisConfig` - Complete analysis configuration
- `Nugget.theme` - Which theme a nugget belongs to
- `Nugget.raw_segment` - Raw transcript for exhaustive mode

## Future Work

- [ ] Implement `nuggets list` command
- [ ] Implement `nuggets search` command
- [ ] Markdown export format
- [ ] Apple Podcasts integration
