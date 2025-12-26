# Extract Nuggets from Transcript

You are analyzing a transcript to extract the most valuable insights, quotes, and action items.
Your goal is to identify the "nuggets" - the pieces of information worth remembering and acting on.

## Input Context
- **Source**: {source_name}
- **Episode**: {title}
- **Duration**: {duration} minutes
- **Date**: {date}

## Your Task

Extract 5-15 "nuggets" from this content. A nugget is a discrete piece of valuable information.

### Nugget Types

| Type | Description | Example |
|------|-------------|---------|
| `insight` | Key learning, surprising fact, important principle | "Dopamin handlar mer om motivation än belöning" |
| `quote` | Memorable quote worth saving | "The obstacle is the way" |
| `action` | Specific actionable advice | "Exponera dig för solljus inom 30 min efter uppvakning" |
| `concept` | Important definition or mental model | "Deliberate practice = fokuserad övning utanför comfort zone" |
| `story` | Illustrative anecdote or example | "När Steve Jobs startade NeXT..." |

### Quality Guidelines

1. **Quality over quantity** - Only include truly valuable nuggets
2. **Be specific** - "Exercise 30 min daily" is better than "Exercise is good"
3. **Preserve voice** - Keep the speaker's exact phrasing in quotes
4. **Prioritize actionable** - Prefer insights you can act on
5. **Include timestamps** - When available in the transcript [HH:MM:SS]
6. **Swedish or English** - Match the language of the content

### Output Format

Respond with valid JSON only (no markdown code blocks):

{
  "summary": "2-3 sentence summary of the main themes and takeaways",
  "guests": ["Guest Name 1", "Guest Name 2"],
  "suggested_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "nuggets": [
    {
      "content": "The nugget content - clear, specific, and valuable",
      "type": "insight",
      "timestamp": "12:34:56",
      "context": "Discussion about morning routines",
      "importance": 5,
      "speaker": "Andrew Huberman"
    },
    {
      "content": "Another nugget here",
      "type": "action",
      "timestamp": null,
      "context": "Talking about sleep optimization",
      "importance": 4,
      "speaker": null
    }
  ]
}

### Importance Scale

- **5** - Life-changing insight, must remember
- **4** - Very valuable, high priority
- **3** - Good to know, worth saving
- **2** - Interesting but not critical
- **1** - Minor point, include if relevant

---

## Transcript

{transcript}
