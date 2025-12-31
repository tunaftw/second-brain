---
name: nuggets-curate
description: Review and rate nuggets with star ratings. Use when asked to curate, rate, or review nuggets.
---

# Podcast Nuggets: Curate Workflow

Review and rate nuggets in your knowledge library.

## Trigger Phrases

- "Curate nuggets"
- "Rate my nuggets"
- "Review new nuggets"
- "Star the best ones"

## Star Rating System

- **1 star** ⭐ — Worth remembering
- **2 stars** ⭐⭐ — Important insight
- **3 stars** ⭐⭐⭐ — "Goated" — Core to personal philosophy

## Workflow Options

### Option A: Interactive CLI

```bash
nuggets star --interactive
```

Shows unrated nuggets one by one (highest AI importance first).
Input: 1/2/3 to rate, s to skip, q to quit.

### Option B: Batch with Claude

1. Get unrated nuggets:
   ```bash
   nuggets search --stars 0 --limit 20
   ```

2. Review each nugget and suggest rating:
   - Consider: Is this actionable? Universal? Life-changing?
   - 3 stars = "I want to live by this principle"
   - 2 stars = "Important to remember"
   - 1 star = "Nice to know"

3. Rate nuggets:
   ```bash
   nuggets star <nugget-id> <1-3>
   ```

4. Rebuild index:
   ```bash
   nuggets index rebuild
   ```

### Option C: Quick Best-Of

For quickly marking exceptional nuggets:

```bash
# Find high-importance unrated
nuggets search --stars 0 | head -10

# Mark the best ones
nuggets star <id> 3
nuggets star <id> 3
```

## Curation Questions

When deciding on ratings, consider:

1. **Actionability**: Can I implement this today?
2. **Universality**: Does this apply broadly to life?
3. **Memorability**: Will I remember this in a year?
4. **Personal resonance**: Does this align with my values?

## After Curation

Update index and check stats:

```bash
nuggets index rebuild
nuggets index stats
```

Export your best insights:

```bash
nuggets export --best-of --group-by topic
nuggets export --stars 3
```

## Example Session

```
📋 Curation Session

💡 "The dose makes the poison - any substance can be
   harmful in excess, including water and oxygen"
   — Huberman Lab • 2024-12-15
   AI importance: 5/5

Rate (1/2/3/s/q): 2
✓ Set ⭐⭐

💬 "You don't rise to the level of your goals,
   you fall to the level of your systems"
   — Tim Ferriss • 2024-12-10
   AI importance: 5/5

Rate (1/2/3/s/q): 3
✓ Set ⭐⭐⭐

Done! Rated 15 nuggets.
Run 'nuggets index rebuild' to update the index
```
