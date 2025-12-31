---
name: nuggets-ingest
description: Process a YouTube video, Twitter/X thread, or podcast into the knowledge library. Use when given a URL or asked to process new content.
---

# Podcast Nuggets: Ingest Workflow

Process new content into your knowledge library.

## Trigger Phrases

- "Process this video"
- "Add this podcast"
- "Process this tweet/thread"
- YouTube URLs
- Twitter/X URLs
- "Ingest [URL]"

## Supported Sources

| Source | Command | Example |
|--------|---------|---------|
| YouTube | `nuggets youtube <url>` | youtube.com/watch?v=... |
| Twitter/X | `nuggets twitter <url>` | x.com/user/status/... |

## YouTube Workflow

### Step 1: Fetch Transcript

```bash
nuggets youtube "<URL>" --transcript-only
```

Saves to `data/raw/youtube/{channel}/{date}-{id}.json`.

### Step 2: Analyze Content

```bash
nuggets youtube "<URL>"
```

Or for interactive theme-based analysis (more control):

1. Read the transcript file
2. Identify 3-8 themes in the content
3. Ask user which themes to focus on and at what detail level (1-5)
4. Extract nuggets for selected themes
5. Categorize each nugget with topic and wisdom_type
6. Save to `data/analysis/youtube/{channel}/{date}-{id}.json`

## Twitter/X Workflow

### Step 1: Fetch Content

```bash
nuggets twitter "<URL>" --transcript-only
```

Saves to `data/raw/twitter/{author}/{date}-{id}.json`.

Works with:
- Threads (multiple tweets)
- Articles (long-form X posts)
- Regular tweets

### Step 2: Analyze Content

```bash
nuggets twitter "<URL>"
```

Fetches via Jina Reader API (free, no API key needed) and analyzes with Claude.

## After Ingesting

### Update Index

```bash
nuggets index rebuild
```

### Show Summary

Display:
- Episode title and source
- Number of nuggets extracted
- Top 3 most important nuggets
- Category breakdown

## Category Guidelines

**Topics** (auto-assigned):
- sleep, productivity, health, relationships, business
- creativity, learning, fitness, nutrition, mindset
- technology, parenting, finance, communication

**Wisdom Types** (auto-assigned):
- `principle` — Fundamental truth or rule
- `habit` — Concrete behavior to implement
- `mental-model` — Way of thinking
- `life-lesson` — Broad life wisdom
- `technique` — Specific method
- `warning` — Something to avoid

## Example Output

### YouTube
```
✓ Processed: "How to Optimize Your Sleep" by Huberman Lab

📊 Summary:
- 12 nuggets extracted
- Topics: sleep (8), health (3), productivity (1)
- Types: technique (5), principle (4), habit (3)

💡 Top Nuggets:
1. ⭐ "View bright light within 30-60 minutes of waking"
2. ⭐ "Keep room temperature between 65-68°F for optimal sleep"
3. ⭐ "Avoid caffeine 8-10 hours before bed"

Next: Run 'nuggets star --interactive' to rate these nuggets
```

### Twitter/X
```
✓ Fetched: "19 Quality of Life Improvements"
✓ Author: @thebeautyofsaas
✓ Found 15 nuggets

💡 Top Nuggets:
1. ⭐ "Health > Time > Money — each builds on the others"
2. ⭐ "24-48 hour digital detoxes reset your attention"
3. ⭐ "Do the opposite of the masses regarding consumption"

Next: Run 'nuggets star --interactive' to rate these nuggets
```
