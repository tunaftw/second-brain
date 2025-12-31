---
name: nuggets-explore
description: Search, explore, and connect insights in the knowledge library. Use for queries about what you know, finding related content, or comparing sources.
---

# Nuggets Explore

Navigate and discover insights in your knowledge library.

## Triggers

- "search", "sok", "find", "hitta"
- "what do I know about...", "vad vet jag om..."
- "explore", "utforska"
- "connect", "compare", "jamfor"
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
2. Show: headline -> condensed -> full (segment level) -> raw_segment
3. Include YouTube timestamp link if available

### Connect Sources

When user asks "what do Huberman and Goggins say about discipline":
1. Search for relevant nuggets from each source
2. Present side-by-side comparison
3. Identify common themes

## Output Patterns

See `references/query-patterns.md` for display formats.
