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
