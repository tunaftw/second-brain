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
Fetched: "{title}"
  Host: {host} | Guest: {guest}
  Duration: {duration}
  Saved to: {path}

Next: Run /nuggets-analyze to extract insights
```
