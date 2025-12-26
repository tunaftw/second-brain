# Podcast Nuggets

Extract valuable insights ("nuggets") from podcasts, YouTube videos, and audio files.

## What is this?

A personal tool for capturing the most valuable lessons from the content you consume.
Instead of re-listening to hours of podcasts, extract the key insights, quotes, and action items.

## Features

- **YouTube integration** - Fetch transcripts from YouTube (captions or Whisper fallback)
- **Transcribe** from Apple Podcasts or audio files
- **Extract** key insights using Claude AI
- **Export** to Apple Notes (macOS)

## Quick Start

```bash
# Install
pip install -e ".[whisper]"

# Process a YouTube video (transcript + analysis)
nuggets youtube "https://youtube.com/watch?v=..."

# Export to Apple Notes
nuggets export youtube-2025-12-25-hLIvhTiE --format apple-notes
```

## Commands

### YouTube (Primary)

```bash
# Full workflow: transcript + analysis
nuggets youtube "https://youtube.com/watch?v=abc123"

# Just transcript, skip analysis
nuggets youtube "https://youtube.com/watch?v=abc123" --transcript-only

# Force Whisper (skip YouTube captions)
nuggets youtube "https://youtube.com/watch?v=abc123" --whisper

# Specify language for captions
nuggets youtube "https://youtube.com/watch?v=abc123" --language en
```

### Analyze

```bash
# Analyze an existing transcript
nuggets analyze data/transcripts/youtube/video-2025-01-01.txt
```

### Export

```bash
# Export to Apple Notes (default)
nuggets export youtube-2025-12-25-hLIvhTiE

# Specify folder in Apple Notes
nuggets export youtube-2025-12-25-hLIvhTiE --folder "Podcasts"

# Export as JSON
nuggets export youtube-2025-12-25-hLIvhTiE --format json
```

## Nugget Types

| Type | Icon | Description |
|------|------|-------------|
| `insight` | 💡 | Key learnings and principles |
| `quote` | 💬 | Memorable quotes |
| `action` | ✅ | Actionable advice |
| `concept` | 📖 | Definitions and mental models |
| `story` | 📚 | Illustrative examples |

## Apple Notes Format

The export creates a nicely formatted note with:

- Title and metadata (source, duration, guests)
- Link to YouTube video
- Tags (recognized as #hashtags by Apple Notes)
- Summary
- Nuggets grouped by type (Actions, Insights, Quotes, etc.)
- Personal notes section

Language detection automatically uses Swedish or English labels based on the content.

## Data Storage

```
data/
├── transcripts/youtube/    # Raw transcripts
├── nuggets/                 # Analyzed episodes (JSON)
└── exports/                 # Exported files
```

## Requirements

- Python 3.11+
- macOS (for Apple Notes export and MLX Whisper)
- Anthropic API key (for Claude analysis)

## License

MIT
