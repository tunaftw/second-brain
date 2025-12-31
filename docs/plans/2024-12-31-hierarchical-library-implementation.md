# Hierarchical Knowledge Library - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure podcast-nuggets with Segment/Nugget hierarchy and 4 Claude skills.

**Architecture:** Episodes contain Segments (thematic blocks with full context), which contain Nuggets (individual insights). Skills automate fetch → analyze → explore → curate workflow. **Analysis is done directly by Claude Code in conversation** (no API calls needed) or via OpenCode for batch processing.

**Tech Stack:** Python 3.11+, Pydantic, Click CLI

**Analysis Methods:**
| Method | How it works | Cost |
|--------|--------------|------|
| **Claude Code** | Claude analyzes directly in conversation | Tokens only (no API key) |
| **OpenCode** | Local GLM-4.7 model | Free |

**Embeddings:** Deferred to later phase. Current implementation uses fulltext search.

---

## Phase 1: Data Models & Storage

### Task 1.1: Add Segment Model

**Files:**
- Modify: `src/nuggets/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
class TestSegment:
    """Tests for Segment model."""

    def test_segment_minimal(self):
        """Segment can be created with minimal fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="This is the raw transcript text...",
            topic="productivity",
            theme_name="Morning Routines",
        )
        assert segment.id == "segment-ep123-0"
        assert segment.topic == "productivity"
        assert segment.full is None  # optional

    def test_segment_with_all_fields(self):
        """Segment supports all optional fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="Raw transcript...",
            full="Edited comprehensive summary...",
            topic="sleep",
            theme_name="Sleep Optimization",
            start_timestamp="01:23:45",
            end_timestamp="01:28:30",
            speakers=["Andrew Huberman", "Matt Walker"],
            primary_speaker="Matt Walker",
            related_segment_ids=["segment-ep456-2", "segment-ep789-1"],
        )
        assert segment.full == "Edited comprehensive summary..."
        assert segment.speakers == ["Andrew Huberman", "Matt Walker"]
        assert len(segment.related_segment_ids) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::TestSegment -v`
Expected: FAIL with "cannot import name 'Segment'"

**Step 3: Write Segment model**

Add to `src/nuggets/models.py` after the `Nugget` class:

```python
class Segment(BaseModel):
    """A thematic block from an episode.

    Contains raw transcript, optional edited summary, and metadata.
    Nuggets are extracted from segments.
    """

    id: str = Field(..., description="Unique ID: segment-{episode_id}-{index}")
    episode_id: str = Field(..., description="ID of the parent episode")

    # Content levels
    raw_segment: str = Field(..., description="Exact transcript text for this segment")
    full: Optional[str] = Field(
        None, description="Edited, comprehensive summary (if enough material)"
    )

    # Metadata
    topic: str = Field(..., description="Topic category: sleep, productivity, etc.")
    theme_name: str = Field(..., description="Human-readable theme name")
    start_timestamp: Optional[str] = Field(None, description="Start time HH:MM:SS")
    end_timestamp: Optional[str] = Field(None, description="End time HH:MM:SS")

    # Speakers
    speakers: list[str] = Field(default_factory=list, description="All speakers in segment")
    primary_speaker: Optional[str] = Field(None, description="Main speaker for this segment")

    # Connections (for future semantic search)
    related_segment_ids: list[str] = Field(
        default_factory=list, description="IDs of similar segments from other episodes"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::TestSegment -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/nuggets/models.py tests/test_models.py
git commit -m "feat(models): add Segment model for thematic blocks"
```

---

### Task 1.2: Update Nugget Model with Hierarchy Fields

**Files:**
- Modify: `src/nuggets/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py` in `TestNugget`:

```python
    def test_nugget_hierarchy_fields(self):
        """Nugget supports segment_id and multi-level content."""
        nugget = Nugget(
            content="Legacy field",  # Keep for backwards compat
            type=NuggetType.INSIGHT,
            segment_id="segment-ep123-0",
            headline="Morning sunlight boosts cortisol",
            condensed="Huberman explains that viewing bright light within 30 minutes of waking triggers a cortisol pulse that helps set your circadian rhythm.",
            quote="Get sunlight in your eyes within 30-60 minutes of waking.",
        )
        assert nugget.segment_id == "segment-ep123-0"
        assert nugget.headline == "Morning sunlight boosts cortisol"
        assert nugget.condensed is not None
        assert nugget.quote is not None

    def test_nugget_flexible_levels(self):
        """Not all content levels need to be present."""
        # Quote without full context
        nugget = Nugget(
            content="The obstacle is the way",
            type=NuggetType.QUOTE,
            headline="Stoic wisdom on obstacles",
            quote="The obstacle is the way",
            condensed=None,  # No extra context
        )
        assert nugget.quote == "The obstacle is the way"
        assert nugget.condensed is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::TestNugget::test_nugget_hierarchy_fields -v`
Expected: FAIL with "unexpected keyword argument 'segment_id'"

**Step 3: Update Nugget model**

Modify `Nugget` class in `src/nuggets/models.py`:

```python
class Nugget(BaseModel):
    """A valuable insight extracted from content.

    Part of a Segment. Has multiple content levels for different zoom views.
    """

    # Legacy field (kept for backwards compatibility)
    content: str = Field(..., description="The nugget content - clear and specific")
    type: NuggetType = Field(..., description="Type of nugget")

    # Hierarchy
    segment_id: Optional[str] = Field(None, description="ID of parent segment")

    # Multi-level content (all optional except headline for new nuggets)
    headline: Optional[str] = Field(None, description="One-line summary for scanning")
    condensed: Optional[str] = Field(None, description="Core insight with enough context")
    quote: Optional[str] = Field(None, description="Verbatim quote if applicable")

    # Existing fields
    timestamp: Optional[str] = Field(
        None, description="Timestamp in format HH:MM:SS or MM:SS"
    )
    context: Optional[str] = Field(
        None, description="Brief context about what was being discussed"
    )
    importance: int = Field(
        3, ge=1, le=5, description="Importance rating from 1 (low) to 5 (critical)"
    )
    speaker: Optional[str] = Field(None, description="Who said this")

    # Fields for interactive/exhaustive mode
    theme: Optional[str] = Field(None, description="Which theme this nugget belongs to")
    raw_segment: Optional[str] = Field(
        None, description="Raw transcript segment (for exhaustive detail level)"
    )

    # Knowledge library fields
    topic: Optional[str] = Field(
        None, description="Topic category: sleep, productivity, health, etc."
    )
    wisdom_type: Optional[str] = Field(
        None, description="Type: principle, habit, mental-model, life-lesson, technique, warning"
    )
    stars: Optional[int] = Field(
        None, ge=1, le=3, description="Personal rating 1-3 (None = unrated)"
    )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py::TestNugget -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/models.py tests/test_models.py
git commit -m "feat(models): add hierarchy fields to Nugget (segment_id, headline, condensed, quote)"
```

---

## Phase 2: nuggets-fetch Skill

### Task 2.1: Create Skill Structure

**Files:**
- Create: `.claude/skills/nuggets-fetch/SKILL.md`
- Create: `.claude/skills/nuggets-fetch/references/metadata-parsing.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-fetch/SKILL.md`:

```markdown
---
name: nuggets-fetch
description: Fetch content from YouTube, Twitter/X, or podcasts into the knowledge library. Use when given a URL or asked to download/fetch content.
---

# Nuggets Fetch

Download and store raw content for later analysis.

## Triggers

- YouTube URLs (youtube.com, youtu.be)
- Twitter/X URLs (twitter.com, x.com)
- "fetch", "download", "hämta"
- "get transcript from..."

## Workflow

### YouTube

1. Run the CLI command to fetch transcript:

```bash
nuggets youtube "<URL>" --transcript-only
```

2. Verify the file was saved to `data/raw/youtube/{channel}/{date}-{id}.json`

3. Report success with file path and metadata (title, duration, guest if detected)

### Twitter/X

1. Run the CLI command:

```bash
nuggets twitter "<URL>" --transcript-only
```

2. If Jina Reader fails, offer to use browser automation with `/chrome`

3. Verify file saved to `data/raw/twitter/{author}/{date}-{id}.json`

## Speaker Hints

After fetching, parse and report:
- **Host**: From known channel mapping (see `references/metadata-parsing.md`)
- **Guest**: From title patterns like "with {Guest}" or "{Guest}: Topic"

These hints are used by nuggets-analyze for speaker attribution.

## Output

After successful fetch, suggest:
```
✓ Fetched: "{title}"
  Host: {host} | Guest: {guest}
  Duration: {duration}
  Saved to: {path}

Next: Run /nuggets-analyze to extract insights
```
```

**Step 2: Create metadata-parsing.md reference**

Create `.claude/skills/nuggets-fetch/references/metadata-parsing.md`:

```markdown
# Metadata Parsing

## Guest Extraction from Title

Common patterns:

| Pattern | Example | Extracted Guest |
|---------|---------|-----------------|
| "with {Guest}" | "Sleep Tips with Dr. Matt Walker" | Dr. Matt Walker |
| "{Guest}: Topic" | "Andy Galpin: How to Build Muscle" | Andy Galpin |
| "{Guest} - Topic" | "David Goggins - Mental Toughness" | David Goggins |
| "#{Number} {Guest}" | "#1892 David Goggins" | David Goggins |

## Host Detection from Channel

| Channel | Host |
|---------|------|
| Huberman Lab | Andrew Huberman |
| The Joe Rogan Experience | Joe Rogan |
| Modern Wisdom | Chris Williamson |
| Diary of a CEO | Steven Bartlett |
| Lex Fridman Podcast | Lex Fridman |
| The Tim Ferriss Show | Tim Ferriss |
| Jay Shetty Podcast | Jay Shetty |
```

**Step 3: Commit**

```bash
git add .claude/skills/nuggets-fetch/
git commit -m "feat(skills): add nuggets-fetch skill structure"
```

---

### Task 2.2: Add Speaker Parsing to YouTube Module

**Files:**
- Modify: `src/nuggets/transcribe/youtube.py`
- Test: `tests/test_youtube.py`

**Step 1: Write the failing test**

Add to `tests/test_youtube.py`:

```python
class TestSpeakerParsing:
    """Tests for speaker parsing from metadata."""

    def test_parse_guest_with_pattern(self):
        """Parse guest from 'with Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Sleep Tips with Dr. Matt Walker") == "Dr. Matt Walker"

    def test_parse_guest_colon_pattern(self):
        """Parse guest from 'Guest: Topic' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Andy Galpin: How to Build Muscle") == "Andy Galpin"

    def test_parse_guest_number_pattern(self):
        """Parse guest from '#Number Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("#1892 David Goggins") == "David Goggins"

    def test_parse_host_from_channel(self):
        """Get known host from channel name."""
        from nuggets.transcribe.youtube import get_host_from_channel

        assert get_host_from_channel("Huberman Lab") == "Andrew Huberman"
        assert get_host_from_channel("Unknown Channel") is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_youtube.py::TestSpeakerParsing -v`
Expected: FAIL with "cannot import name 'parse_guest_from_title'"

**Step 3: Add speaker parsing functions**

Add to `src/nuggets/transcribe/youtube.py`:

```python
import re

GUEST_PATTERNS = [
    r"with\s+(.+?)(?:\s*[-:|]|$)",
    r"^(.+?):\s+",
    r"^(.+?)\s+-\s+",
    r"^(.+?)\s+\|\s+",
    r"(?:ft\.|feat\.)\s+(.+?)(?:\s*[-:|]|$)",
    r"^#\d+\s+(.+?)(?:\s*[-:|]|$)",
    r"^[Ee]p\.?\s*\d+[:\s]+(.+?)(?:\s*[-:|]|$)",
]

KNOWN_HOSTS = {
    "Huberman Lab": "Andrew Huberman",
    "The Joe Rogan Experience": "Joe Rogan",
    "Modern Wisdom": "Chris Williamson",
    "Diary of a CEO": "Steven Bartlett",
    "Lex Fridman Podcast": "Lex Fridman",
    "The Tim Ferriss Show": "Tim Ferriss",
    "Jay Shetty Podcast": "Jay Shetty",
}


def parse_guest_from_title(title: str) -> str | None:
    """Extract guest name from video title."""
    for pattern in GUEST_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            if len(guest) > 2 and not guest.lower().startswith(
                ("how", "what", "why", "the", "a ", "an ")
            ):
                return guest
    return None


def get_host_from_channel(channel_name: str) -> str | None:
    """Get known host from channel name."""
    return KNOWN_HOSTS.get(channel_name)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_youtube.py::TestSpeakerParsing -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/transcribe/youtube.py tests/test_youtube.py
git commit -m "feat(youtube): add speaker parsing from title and channel"
```

---

## Phase 3: nuggets-analyze Skill

### Task 3.1: Create Skill Structure

**IMPORTANT:** This skill instructs Claude Code to do the analysis DIRECTLY in conversation.
No API calls are made - Claude Code reads the transcript and extracts insights itself.

**Files:**
- Create: `.claude/skills/nuggets-analyze/SKILL.md`
- Create: `.claude/skills/nuggets-analyze/references/extraction-guide.md`
- Create: `.claude/skills/nuggets-analyze/references/output-schema.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-analyze/SKILL.md`:

```markdown
---
name: nuggets-analyze
description: Analyze fetched content to extract segments and nuggets. Claude Code does the analysis directly - no API needed. Use after nuggets-fetch.
---

# Nuggets Analyze

Extract segments and nuggets from raw transcripts.

**How it works:** Claude Code reads the transcript and performs the analysis directly in conversation. No API calls needed - just token cost.

## Triggers

- "analyze", "analysera"
- "extract nuggets from..."
- After successful fetch
- Raw transcript file path

## Workflow

### Step 1: Load Raw Transcript

Read the JSON file from `data/raw/{source}/{channel}/{date}-{id}.json`

### Step 2: Identify Speaker Hints

From the metadata:
- Host: From channel name (see nuggets-fetch/references/metadata-parsing.md)
- Guest: From title parsing

### Step 3: Segment the Transcript

Identify 8-15 thematic blocks. For each segment:
- theme_name: Clear descriptive name
- topic: Category (sleep, productivity, health, etc.)
- start_timestamp / end_timestamp
- raw_segment: Exact transcript text
- full: Comprehensive summary (if segment has depth, else null)
- speakers: Who speaks
- primary_speaker: Main speaker for this segment

### Step 4: Extract Nuggets per Segment

For each segment, extract 2-8 nuggets:
- headline: One-line summary (ALWAYS required)
- condensed: Core insight with context (if substantial)
- quote: Verbatim quote (only if truly quotable)
- type: insight/quote/action/concept/story
- wisdom_type: principle/habit/mental-model/life-lesson/technique/warning
- speaker: Who said this
- timestamp: Specific moment
- importance: 1-5

**Be selective:** Not all nuggets need all levels. A name-dropped quote may only have headline + quote. A deep discussion may have headline + condensed + full but no quote.

### Step 5: Save Results

Write JSON to `data/analysis/{source}/{channel}/{date}-{id}.json`

See `references/output-schema.md` for exact format.

### Step 6: Update Index

Run: `nuggets index rebuild`

## Output

```
✓ Analyzed: "{title}"
  Segments: 12 | Nuggets: 47
  Topics: sleep (15), productivity (12), mindset (10), ...

Top insights:
  💡 "Morning sunlight within 30 min sets circadian rhythm"
  💡 "Caffeine blocks adenosine, doesn't create energy"
  💬 "The obstacle is the way" - Marcus Aurelius

Next: Run /nuggets-curate to rate these nuggets
```

## Alternative: OpenCode Batch Processing

For batch processing without token cost, use OpenCode with GLM-4.7:

```bash
python scripts/analyze_batch.py --source youtube --pending
```

This is useful for processing many episodes at once.
```

**Step 2: Create extraction-guide.md reference**

Create `.claude/skills/nuggets-analyze/references/extraction-guide.md`:

```markdown
# Extraction Guide

## Segmentation Principles

1. **Topic-based**: Each segment covers ONE main topic/discussion
2. **Natural breaks**: Look for topic transitions, new questions, subject changes
3. **Reasonable length**: 2-20 minutes per segment typically
4. **Speaker shifts**: Major guest monologues often form natural segments

## Nugget Extraction

### What makes a good nugget?

- **Actionable**: Can be implemented
- **Memorable**: Worth remembering
- **Specific**: Not vague platitudes
- **Attributed**: Clear who said it

### Content Level Guidelines

| Level | When to include | Length |
|-------|-----------------|--------|
| headline | ALWAYS | 1 sentence, <20 words |
| condensed | When there's real substance | 2-4 sentences |
| quote | When truly quotable/memorable | Verbatim |
| full | Deep, valuable discussions | Paragraph |
| raw_segment | On segment level only | Exact transcript |

### Type Classification

- **insight**: Key learning, surprising fact, important principle
- **quote**: Memorable statement worth saving verbatim
- **action**: Specific actionable advice ("do X every morning")
- **concept**: Definition or mental model
- **story**: Illustrative anecdote

### Wisdom Type Classification

- **principle**: Fundamental truth ("Sleep is the foundation of health")
- **habit**: Concrete behavior ("Get morning sunlight within 30 min")
- **mental-model**: Way of thinking ("The 40% rule")
- **life-lesson**: Broad wisdom ("Embrace discomfort")
- **technique**: Specific method ("4-7-8 breathing")
- **warning**: Something to avoid ("Don't check phone first thing")
```

**Step 3: Create output-schema.md reference**

Create `.claude/skills/nuggets-analyze/references/output-schema.md`:

```markdown
# Output Schema

## File: `data/analysis/{source}/{channel}/{date}-{id}.json`

```json
{
  "id": "youtube-2024-12-31-abc123",
  "source_type": "youtube",
  "source_name": "Huberman Lab",
  "title": "Dr. Andy Galpin: How to Build Strength",
  "url": "https://youtube.com/watch?v=abc123",
  "date": "2024-12-31",
  "duration_minutes": 120,
  "host": "Andrew Huberman",
  "guest": "Andy Galpin",

  "summary": "2-3 sentence summary of the entire episode",

  "segments": [
    {
      "id": "segment-youtube-2024-12-31-abc123-0",
      "episode_id": "youtube-2024-12-31-abc123",
      "theme_name": "Strength Training Fundamentals",
      "topic": "fitness",
      "start_timestamp": "05:30",
      "end_timestamp": "22:15",
      "speakers": ["Andrew Huberman", "Andy Galpin"],
      "primary_speaker": "Andy Galpin",
      "raw_segment": "Exact transcript text...",
      "full": "Comprehensive edited summary of this segment...",

      "nuggets": [
        {
          "id": "nugget-segment-youtube-2024-12-31-abc123-0-0",
          "segment_id": "segment-youtube-2024-12-31-abc123-0",
          "headline": "3-5 sets is optimal for strength gains",
          "condensed": "Andy explains that research consistently shows 3-5 sets per muscle group per session is the sweet spot for strength development...",
          "quote": null,
          "type": "insight",
          "wisdom_type": "principle",
          "speaker": "Andy Galpin",
          "timestamp": "08:42",
          "importance": 4,
          "topic": "fitness"
        }
      ]
    }
  ],

  "analyzed_at": "2024-12-31T14:30:00Z",
  "analysis_method": "claude-code"
}
```

## Notes

- `analysis_method`: "claude-code" or "opencode"
- Segments and nuggets have hierarchical IDs
- All timestamps in HH:MM:SS or MM:SS format
- `full` on segment level, `condensed` on nugget level
```

**Step 4: Commit**

```bash
git add .claude/skills/nuggets-analyze/
git commit -m "feat(skills): add nuggets-analyze skill for direct Claude Code analysis"
```

---

## Phase 4: nuggets-explore Skill

### Task 4.1: Create Skill Structure

**Files:**
- Create: `.claude/skills/nuggets-explore/SKILL.md`
- Create: `.claude/skills/nuggets-explore/references/query-patterns.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-explore/SKILL.md`:

```markdown
---
name: nuggets-explore
description: Search, explore, and connect insights in the knowledge library. Use for queries about what you know, finding related content, or comparing sources.
---

# Nuggets Explore

Navigate and discover insights in your knowledge library.

## Triggers

- "search", "sök", "find", "hitta"
- "what do I know about...", "vad vet jag om..."
- "explore", "utforska"
- "connect", "compare", "jämför"
- "who said...", "vem sa..."

## Commands

### Search (Nugget-level)

```bash
nuggets search "morning sunlight"
nuggets search "dopamine" --speaker "Anna Lembke"
nuggets search --topic sleep --stars 2
```

### List Episodes

```bash
nuggets list
nuggets list --source "Huberman"
nuggets list --year 2024
```

### Deep Dive

When user wants more context on a nugget:
1. Find the nugget in the analysis JSON
2. Show: headline → condensed → full (segment level) → raw_segment
3. Include YouTube timestamp link if available

### Connect Sources

When user asks "what do Huberman and Goggins say about discipline":
1. Search for relevant nuggets from each source
2. Present side-by-side comparison
3. Identify common themes

## Output Patterns

See `references/query-patterns.md` for display formats.
```

**Step 2: Create query-patterns.md reference**

Create `.claude/skills/nuggets-explore/references/query-patterns.md`:

```markdown
# Query Patterns

## Search Results

```
🔍 Found 5 nuggets for "morning sunlight"

⭐⭐ [Huberman Lab] 00:15:32
"Morning sunlight within 30 min boosts cortisol"
→ Huberman explains that viewing bright light early triggers...
Speaker: Andrew Huberman

⭐ [Modern Wisdom] 01:05:20
"Sunlight exposure sets circadian rhythm"
Speaker: Chris Williamson
```

## Deep Dive

```
📖 Deep Dive: Morning sunlight routine

HEADLINE:
Morning sunlight within 30 minutes boosts cortisol

CONDENSED:
Huberman explains that viewing bright light within 30-60 minutes
of waking triggers a cortisol pulse that helps set circadian rhythm.

FULL (from segment):
[Complete segment summary with all context...]

RAW TRANSCRIPT:
[Exact transcript if requested...]

🔗 Watch: youtube.com/watch?v=xyz&t=932
```

## Connect Results

```
🔗 Connecting: Huberman ↔ Goggins on "discipline"

HUBERMAN says:
  💡 "Dopamine is released in anticipation, not reward"
  → Focus on the process, not the outcome

GOGGINS says:
  💡 "Embrace the suck - discomfort is growth"
  → Pain is the path to mental toughness

COMMON THEMES:
  • Process over outcome
  • Discomfort as growth
```
```

**Step 3: Commit**

```bash
git add .claude/skills/nuggets-explore/
git commit -m "feat(skills): add nuggets-explore skill structure"
```

---

## Phase 5: Update nuggets-curate Skill

### Task 5.1: Restructure as Proper Skill

**Files:**
- Remove: `.claude/skills/nuggets-curate.md`
- Create: `.claude/skills/nuggets-curate/SKILL.md`

**Step 1: Create new skill structure**

Create `.claude/skills/nuggets-curate/SKILL.md`:

```markdown
---
name: nuggets-curate
description: Rate and curate nuggets in your knowledge library. Use for star ratings, reviewing insights, and creating best-of collections.
---

# Nuggets Curate

Personal curation of your knowledge library.

## Triggers

- "rate", "star", "betygsätt"
- "review nuggets", "granska"
- "favorites", "best of"
- "curate"

## Star Rating System

| Stars | Meaning | Use For |
|-------|---------|---------|
| ⭐ | Worth remembering | Good insights to review |
| ⭐⭐ | Important insight | Key learnings |
| ⭐⭐⭐ | Goated | Core philosophy, life-changing |

## Commands

### Rate Single Nugget

```bash
nuggets star <nugget-id> <1-3>
```

### Interactive Rating

```bash
nuggets star --interactive
nuggets star --interactive --unrated
nuggets star --interactive --topic sleep
```

### Export Best-Of

```bash
nuggets export --best-of
nuggets export --stars 3
nuggets export --stars 2 --topic sleep
```

## Interactive Mode Display

```
⭐ Rating Mode - 15 unrated nuggets

[1/15] From: Huberman Lab - Sleep Optimization
       Topic: sleep | Type: technique

       "Morning sunlight within 30 minutes of waking sets
        your circadian rhythm and improves sleep quality."

       Speaker: Andrew Huberman | 00:15:32

Rate (1-3, s=skip, q=quit): _
```

## Export with Timestamps

Include clickable YouTube links:

```markdown
## ⭐⭐⭐ Goated Insights

### Sleep
- [00:15:32] Morning sunlight sets circadian rhythm
  [Watch](https://youtube.com/watch?v=xyz&t=932)
```
```

**Step 2: Remove old file and commit**

```bash
rm -f .claude/skills/nuggets-curate.md
mkdir -p .claude/skills/nuggets-curate
git add .claude/skills/nuggets-curate/
git add -u .claude/skills/
git commit -m "feat(skills): restructure nuggets-curate as proper skill"
```

---

## Phase 6: Integration Test

### Task 6.1: Verify Full Workflow

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for the full workflow."""

import tempfile
from pathlib import Path

import pytest


class TestDataModels:
    """Test data model hierarchy."""

    @pytest.mark.integration
    def test_segment_nugget_hierarchy(self):
        """Segments contain nuggets with proper IDs."""
        from nuggets.models import Segment, Nugget, NuggetType

        segment = Segment(
            id="segment-ep1-0",
            episode_id="ep1",
            raw_segment="Test transcript...",
            topic="productivity",
            theme_name="Morning Routines",
        )

        nugget = Nugget(
            content="Test insight",
            type=NuggetType.INSIGHT,
            segment_id=segment.id,
            headline="Test headline",
        )

        assert nugget.segment_id == segment.id
        assert segment.id.startswith("segment-")
        assert "ep1" in nugget.segment_id

    @pytest.mark.integration
    def test_nugget_flexible_content_levels(self):
        """Nuggets can have varying content levels."""
        from nuggets.models import Nugget, NuggetType

        # Full nugget
        full_nugget = Nugget(
            content="Full content",
            type=NuggetType.INSIGHT,
            headline="Headline",
            condensed="Condensed version",
            quote="Quotable quote",
        )
        assert full_nugget.headline is not None
        assert full_nugget.condensed is not None
        assert full_nugget.quote is not None

        # Quote-only nugget
        quote_nugget = Nugget(
            content="The obstacle is the way",
            type=NuggetType.QUOTE,
            headline="Stoic wisdom",
            quote="The obstacle is the way",
        )
        assert quote_nugget.condensed is None
        assert quote_nugget.quote is not None
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v -m integration`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for data model hierarchy"
```

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|------------------|
| 1 | 1.1-1.2 | Segment model, updated Nugget with hierarchy fields |
| 2 | 2.1-2.2 | nuggets-fetch skill, speaker parsing |
| 3 | 3.1 | nuggets-analyze skill (Claude Code does analysis directly) |
| 4 | 4.1 | nuggets-explore skill |
| 5 | 5.1 | Updated nuggets-curate skill |
| 6 | 6.1 | Integration tests |

**Total: 8 tasks**

**Key Architecture Point:** Analysis is done by Claude Code directly in conversation (costs tokens, no API key needed) or via OpenCode/GLM-4.7 for free batch processing. No external embedding APIs required for initial version - fulltext search works for current scale.
