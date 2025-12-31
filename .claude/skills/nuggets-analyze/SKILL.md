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
Analyzed: "{title}"
  Segments: 12 | Nuggets: 47
  Topics: sleep (15), productivity (12), mindset (10), ...

Top insights:
  "Morning sunlight within 30 min sets circadian rhythm"
  "Caffeine blocks adenosine, doesn't create energy"
  "The obstacle is the way" - Marcus Aurelius

Next: Run /nuggets-curate to rate these nuggets
```

## Alternative: OpenCode Batch Processing

For batch processing without token cost, use OpenCode with GLM-4.7:

```bash
python scripts/analyze_batch.py --source youtube --pending
```

This is useful for processing many episodes at once.
