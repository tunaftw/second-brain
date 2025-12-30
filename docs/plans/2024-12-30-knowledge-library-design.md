# Podcast Nuggets: Personal Knowledge Library

Design document for transforming podcast-nuggets into a personal knowledge library ("2nd brain") for wisdom and insights.

## Overview

Evolve the current CLI tool into a structured knowledge system that:
- Separates raw data from analysis
- Automatically categorizes insights
- Supports personal curation with star ratings
- Enables querying and reflection across the entire library
- Exports flexibly to Apple Notes, Markdown, and HTML

## Data Model Changes

### Nugget Model Extensions

```python
class Nugget(BaseModel):
    # Existing fields remain...

    # New fields:
    topic: str | None = None          # "sleep", "productivity", "health", etc.
    wisdom_type: str | None = None    # "principle", "habit", "mental-model", etc.
    stars: int | None = None          # 1-3, personal rating (None = unrated)
```

### Predefined Categories

**Topics** (what it's about):
- sleep, productivity, health, relationships, business
- creativity, learning, fitness, nutrition, mindset
- technology, parenting

**Wisdom Types** (what kind of insight):
- `principle` — Fundamental truth or rule
- `habit` — Concrete behavior to implement
- `mental-model` — Way of thinking about something
- `life-lesson` — Broad life wisdom
- `technique` — Specific method or technique
- `warning` — Something to avoid

Categories are set automatically by Claude during analysis. Can be extended over time.

### Star Rating System

- **1 star**: Worth remembering
- **2 stars**: Important insight
- **3 stars**: "Goated" — Core to personal philosophy

Stars are set manually via CLI or curation skill.

## Folder Structure

```
data/
├── raw/
│   ├── youtube/
│   │   └── {channel-slug}/
│   │       └── {date}-{video-id}.json
│   └── podcasts/
│       └── {podcast-slug}/
│           └── {date}-{episode-id}.json
│
├── analysis/
│   ├── youtube/
│   │   └── {channel-slug}/
│   │       └── {date}-{video-id}.json
│   └── podcasts/
│       └── {podcast-slug}/
│           └── {date}-{episode-id}.json
│
├── library/
│   ├── index.json          # Aggregated index of all nuggets
│   ├── sources.json        # List of all channels/podcasts
│   └── starred.json        # Cache of starred nuggets
│
└── exports/
    └── ...
```

**Separation logic:**
- `raw/` — Untouched data: transcript, metadata, exactly as fetched
- `analysis/` — Processed data: nuggets, categories, summaries
- `library/` — Index and aggregated data for fast access

## CLI Commands

### Updated Commands

```bash
# YouTube processing with new structure
nuggets youtube <url>                    # → raw/ + analysis/
nuggets youtube <url> --transcript-only  # → raw/ only

# Flexible export
nuggets export <id> --format apple-notes
nuggets export <id> --format markdown
nuggets export --starred --format markdown
nuggets export --topic sleep --format apple-notes
nuggets export --stars 3 --format markdown
```

### New Commands

```bash
# Star rating
nuggets star <nugget-id> <1-3>
nuggets star --interactive

# Library browsing
nuggets list
nuggets list --source "Huberman Lab"
nuggets list --year 2024

# Search
nuggets search <query>
nuggets search "dopamine" --topic health
nuggets search --stars 3

# Index management
nuggets index rebuild
nuggets index stats
```

## Claude Code Skills

### Skill 1: `nuggets:ingest`

**Purpose:** Standardized ingestion of new content

**Trigger:** "Process this video/podcast", YouTube URL

**Flow:**
1. Fetch transcript → save to `raw/`
2. Analyze with Claude → extract nuggets with topic and wisdom_type
3. Display summary + top nuggets
4. Save to `analysis/`
5. Update `library/index.json`

### Skill 2: `nuggets:curate`

**Purpose:** Review and rate nuggets

**Trigger:** "Curate latest", "Review new nuggets"

**Flow:**
1. Show nuggets without stars (newest first)
2. For each: show context, suggest rating
3. User confirms/adjusts: "3", "skip", "1"
4. Option to adjust topic/wisdom_type if wrong
5. Update `starred.json`

### Skill 3: `nuggets:reflect`

**Purpose:** Query and discuss the library

**Trigger:** "What do I know about...", "Find patterns in..."

**Flow:**
1. Load `library/index.json` as context
2. Answer questions based on full library
3. Can filter by: topic, wisdom_type, stars, source, year
4. Can find connections between sources

**Examples:**
- "What do my podcasts say about morning routines?"
- "Which principles appear in both Huberman and Ferriss?"
- "Show my 3-star quotes about discipline"

## Export Formats

### A) Per Episode

Full episode with all nuggets, grouped by type.

### B) Per Category

All nuggets for a topic (e.g., "Sleep") across all sources.

### C) "Best Of"

Only starred nuggets, organized by category. The personal philosophy document.

## Implementation Phases

### Phase 1: Foundation
- Update `Nugget` model with new fields
- Create new folder structure
- Migrate existing data
- Update `youtube` command for new structure

### Phase 2: Index & Search
- Build `library/index.json`
- Implement `nuggets list` with filters
- Implement `nuggets search`
- Implement `nuggets index rebuild` and `nuggets index stats`

### Phase 3: Curation
- Implement `nuggets star`
- Implement interactive curation
- Create `starred.json` cache

### Phase 4: Export
- Update Markdown export
- Add filter flags
- Per-category export
- "Best of" export

### Phase 5: Skills
- `nuggets:ingest`
- `nuggets:curate`
- `nuggets:reflect`

### Phase 6: Future
- HTML visualization
- Apple Podcasts integration
- Auto-suggest new categories

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Folder structure | Flat per type | Simpler, channel as metadata |
| Categories | Auto by Claude | Consistent, less manual work |
| Star rating | 1-3 manual | Simple, personal curation |
| Primary interface | Claude sessions | Most powerful for reflection |
| Export | Flexible formats | Different needs, different views |
