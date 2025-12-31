---
name: nuggets-curate
description: Rate and curate nuggets in your knowledge library. Use for star ratings, reviewing insights, and creating best-of collections.
---

# Nuggets Curate

Personal curation of your knowledge library.

## Triggers

- "rate", "star", "betygsatt"
- "review nuggets", "granska"
- "favorites", "best of"
- "curate"

## Star Rating System

| Stars | Meaning | Use For |
|-------|---------|---------|
| 1 | Worth remembering | Good insights to review |
| 2 | Important insight | Key learnings |
| 3 | Goated | Core philosophy, life-changing |

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
Rating Mode - 15 unrated nuggets

[1/15] From: Huberman Lab - Sleep Optimization
       Topic: sleep | Type: technique

       "Morning sunlight within 30 minutes of waking sets
        your circadian rhythm and improves sleep quality."

       Speaker: Andrew Huberman | 00:15:32

Rate (1-3, s=skip, q=quit): _
```

## Curation Questions

When deciding on ratings, consider:

1. **Actionability**: Can I implement this today?
2. **Universality**: Does this apply broadly to life?
3. **Memorability**: Will I remember this in a year?
4. **Personal resonance**: Does this align with my values?

## Export with Timestamps

Include clickable YouTube links:

```markdown
## Goated Insights

### Sleep
- [00:15:32] Morning sunlight sets circadian rhythm
  [Watch](https://youtube.com/watch?v=xyz&t=932)
```
