---
name: nuggets-reflect
description: Query and discuss your knowledge library. Use when asked about insights, patterns, or wisdom from podcasts.
---

# Podcast Nuggets: Reflect Workflow

Query and discuss your accumulated wisdom.

## Trigger Phrases

- "What do I know about..."
- "What have I learned about..."
- "Find patterns in..."
- "Show my best insights on..."
- "Compare what X and Y say about..."

## Loading the Library

First, load the library index for context:

```bash
cat data/library/index.json
```

Or use search to find relevant nuggets:

```bash
nuggets search "sleep"
nuggets search --topic health --stars 2
nuggets search --source "Huberman"
```

## Query Types

### 1. Topic Deep Dive

"What do I know about sleep?"

```bash
nuggets search --topic sleep
nuggets export --topic sleep -o sleep-insights.md
```

Review all sleep-related nuggets across sources.

### 2. Cross-Source Patterns

"What principles appear in both Huberman and Ferriss?"

1. Search each source
2. Find overlapping themes
3. Highlight convergent wisdom

### 3. Best-Of Compilation

"Show my 3-star insights"

```bash
nuggets search --stars 3
nuggets export --stars 3 --group-by topic
```

### 4. Wisdom Type Focus

"What habits have I collected?"

```bash
nuggets search --type habit
```

### 5. Time-Based Reflection

"What did I learn this year?"

```bash
nuggets search --year 2024 --stars 2
```

## Reflection Prompts

Use these to explore your library:

1. **Principles**: What fundamental truths keep appearing?
2. **Contradictions**: Where do sources disagree?
3. **Gaps**: What topics have I not explored?
4. **Action items**: What habits should I implement?
5. **Philosophy**: What 3-star insights define my worldview?

## Example Conversations

### Query: "What have my podcasts taught me about productivity?"

```
Based on your library, here are key productivity insights:

💡 Principles:
- "Energy management matters more than time management" (⭐⭐⭐)
- "The two-minute rule: if it takes less than 2 mins, do it now" (⭐⭐)

✅ Habits:
- Morning sunlight exposure within 30 mins of waking (⭐⭐⭐)
- Time-blocking for deep work (⭐⭐)

⚠️ Warnings:
- Multitasking reduces cognitive performance by 40% (⭐⭐)

Sources: Huberman Lab (5), Tim Ferriss (3), Cal Newport (2)
```

### Query: "Compare what different sources say about morning routines"

```
📊 Morning Routine Comparison:

Huberman Lab:
- Light exposure first
- Delay caffeine 90-120 mins
- Cold exposure for alertness

Tim Ferriss:
- 5-minute journal
- No phone first hour
- Exercise or movement

Common themes:
- All emphasize sunlight/light
- All delay digital devices
- All include some physical activity

Your 3-star picks:
- "View bright light within 30-60 minutes of waking"
- "Never check email before completing one meaningful task"
```

## CLI Reference

```bash
# Search
nuggets search <query>
nuggets search --topic <topic>
nuggets search --stars <min>
nuggets search --source <name>
nuggets search --year <year>
nuggets search --type <type>

# Export findings
nuggets export --topic <topic>
nuggets export --stars <min>
nuggets export --best-of
nuggets export --group-by topic|source|type

# Stats
nuggets index stats
```
