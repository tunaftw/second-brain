# Podcast Nuggets - Projektspecifikation

> **Instruktion till Claude Code:** Läs detta dokument noggrant innan du börjar. Det innehåller
> all kontext, arkitektur, och detaljerade krav för projektet.

---

## 1. Projektöversikt

### Vision
**Podcast Nuggets** är ett personligt verktyg för att extrahera värdefulla insikter ("nuggets")
från podcasts, YouTube-videos och ljudfiler. Till skillnad från finansiella analysverktyg
fokuserar detta på **personligt lärande** - att fånga de viktigaste lärdomarna, citaten,
och action items från innehåll du konsumerar.

### Målgrupp
Mig själv (Pontus). Detta är ett personligt verktyg för livslångt lärande.

### Kärnfilosofi
1. **Enkelhet framför allt** - Minimal friktion, få kommandon, snabb feedback
2. **Nuggets, inte transkript** - Fokus på de 5-10 viktigaste insikterna, inte hela texten
3. **Export-först** - Designat för att fungera med Obsidian, Notion, och andra note-taking-appar
4. **Personligt** - Möjlighet att lägga till egna anteckningar och taggar

---

## 2. Funktionella Krav

### 2.1 Transkribering

**Stödda källor:**
1. **YouTube** (KRITISK/PRIMÄR) - Se sektion 2.1.1 nedan
2. **Apple Podcasts** - Extrahera transkript från Apple Podcasts cache
3. **Lokala ljudfiler** - MP3, M4A, WAV, etc.
4. **MLX Whisper** - Snabb transkribering på Apple Silicon (M1/M2/M3/M4)

**Referenskod finns i:**
- `/Users/pontus/Developer/podcast-transcriber/src/podstock/transcribe/whisper.py`
- `/Users/pontus/Developer/podcast-transcriber/src/podstock/transcribe/apple.py`

Dessa filer kan användas som utgångspunkt men ska anpassas för detta projekts enklare struktur.

---

### 2.1.1 KRITISK FUNKTION: YouTube Integration

**YouTube är den primära källan för innehåll.** Mycket av materialet jag tittar på ligger på YouTube.

#### Användarflöde

```
USER: nuggets youtube "https://youtube.com/watch?v=abc123"

OUTPUT:
✓ Video: "How to Build Good Habits" by Andrew Huberman
✓ Duration: 1:23:45
✓ Transcript downloaded (YouTube captions)
✓ Analyzing with Claude...

## Summary
Andrew Huberman discusses the neuroscience of habit formation...

## Top Nuggets (5 of 12)

⭐⭐⭐⭐⭐ [INSIGHT] Dopamine is about motivation, not reward
   → Context: Discussion about habit loops
   → Timestamp: 12:34

⭐⭐⭐⭐⭐ [ACTION] Get morning sunlight within 30 min of waking
   → Context: Morning routine optimization
   → Timestamp: 45:21

...

Saved to: data/nuggets/huberman-2024-01-15-abc123.json
Export with: nuggets export huberman-2024-01-15-abc123
```

#### Teknisk Implementation

**Primär metod: `youtube-transcript-api`**
```python
from youtube_transcript_api import YouTubeTranscriptApi

# Snabb - använder befintliga YouTube-undertexter
transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['sv', 'en'])
# Resultat: [{'text': '...', 'start': 0.0, 'duration': 2.5}, ...]
```

**Fallback: yt-dlp + Whisper**
- För videos utan undertexter
- Laddar ner audio → transkriberar med MLX Whisper
- Långsammare men fungerar alltid

#### CLI-kommandon för YouTube

```bash
# Enklaste - ett kommando gör allt (transcript + analys)
nuggets youtube "https://youtube.com/watch?v=abc123"

# Bara transcript, ingen analys
nuggets youtube "https://youtube.com/watch?v=abc123" --transcript-only

# Tvinga Whisper (skippa YouTube captions)
nuggets youtube "https://youtube.com/watch?v=abc123" --whisper

# Specificera språk för captions
nuggets youtube "https://youtube.com/watch?v=abc123" --language en
```

#### youtube.py Implementation

```python
# src/nuggets/transcribe/youtube.py

from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import re
from pathlib import Path

def extract_video_id(url: str) -> str:
    """Extrahera video ID från YouTube URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")

def get_video_metadata(video_id: str) -> dict:
    """Hämta metadata om videon med yt-dlp."""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://youtube.com/watch?v={video_id}",
            download=False
        )
        return {
            'title': info.get('title'),
            'channel': info.get('channel'),
            'duration': info.get('duration'),
            'upload_date': info.get('upload_date'),
        }

def get_youtube_transcript(
    video_id: str,
    languages: list[str] = ['sv', 'en']
) -> tuple[str, bool]:
    """
    Hämta transcript från YouTube captions.

    Returns:
        (transcript_text, has_timestamps)
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=languages
        )
        lines = []
        for entry in transcript_list:
            mins, secs = divmod(int(entry['start']), 60)
            hours, mins = divmod(mins, 60)
            if hours:
                timestamp = f"{hours:02d}:{mins:02d}:{secs:02d}"
            else:
                timestamp = f"{mins:02d}:{secs:02d}"
            lines.append(f"[{timestamp}] {entry['text']}")
        return "\n".join(lines), True
    except Exception as e:
        return None, False

def download_and_transcribe(video_id: str, model: str = "large-v3") -> str:
    """Fallback: ladda ner audio och transkribera med Whisper."""
    from .whisper import transcribe

    # 1. Ladda ner audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'data/audio/{video_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://youtube.com/watch?v={video_id}"])

    # 2. Transkribera med Whisper
    audio_path = Path(f"data/audio/{video_id}.mp3")
    return transcribe(audio_path, model=model)

def process_youtube_video(
    url: str,
    force_whisper: bool = False,
    languages: list[str] = ['sv', 'en'],
) -> dict:
    """
    Huvudfunktion: processa en YouTube-video.

    Returns dict med:
    - video_id, title, channel, duration
    - transcript
    - transcript_source ('youtube_captions' eller 'whisper')
    """
    video_id = extract_video_id(url)
    metadata = get_video_metadata(video_id)

    if not force_whisper:
        transcript, has_timestamps = get_youtube_transcript(video_id, languages)
        if transcript:
            return {
                **metadata,
                'video_id': video_id,
                'url': url,
                'transcript': transcript,
                'transcript_source': 'youtube_captions',
                'has_timestamps': has_timestamps,
            }

    # Fallback to Whisper
    transcript = download_and_transcribe(video_id)
    return {
        **metadata,
        'video_id': video_id,
        'url': url,
        'transcript': transcript,
        'transcript_source': 'whisper',
        'has_timestamps': False,
    }
```

#### Flödesdiagram

```
┌─────────────────────────────────────────────────────────────┐
│  nuggets youtube "https://youtube.com/watch?v=abc123"       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Extrahera video_id från URL                             │
│  2. Hämta metadata (titel, kanal, längd) med yt-dlp         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Försök hämta YouTube captions                           │
│     youtube-transcript-api                                  │
│     Prioriterar: sv → en → auto-generated                   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
         [Captions OK]                [Inga captions]
              │                               │
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│  Formatera med          │    │  Fallback: yt-dlp + Whisper │
│  tidsstämplar           │    │  (ladda ner → transkribera) │
└─────────────────────────┘    └─────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Spara transcript till data/transcripts/youtube/         │
│     Filnamn: {channel}-{date}-{video_id}.txt                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Analysera med Claude                                    │
│     - Extrahera nuggets                                     │
│     - Generera sammanfattning                               │
│     - Föreslå tags                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Visa resultat + spara till data/nuggets/                │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.2 Analys & Extraktion

Använd Claude API för att extrahera nuggets från transkript.

**Nugget-typer:**
| Typ | Beskrivning | Exempel |
|-----|-------------|---------|
| `insight` | Viktig insikt eller lärdom | "Dopamin handlar mer om motivation än belöning" |
| `quote` | Minnesvärt citat | "The obstacle is the way" |
| `action` | Konkret sak att göra | "Börja dagen med 10 min solljus" |
| `concept` | Begrepp eller definition | "Deliberate practice = fokuserad övning utanför comfort zone" |
| `story` | Illustrerande berättelse | "Steve Jobs berättade om när..." |

**Extraktions-prompt ska:**
- Identifiera 5-15 nuggets per avsnitt
- Ranka efter viktighet (1-5)
- Inkludera tidsstämplar när möjligt
- Generera en kort sammanfattning (2-3 meningar)
- Föreslå relevanta taggar

### 2.3 Export

**Markdown/Obsidian-format:**
```markdown
---
title: "Huberman Lab #42 - The Science of Sleep"
date: 2024-01-15
source: podcast
guests: [Andrew Huberman]
tags: [sleep, neuroscience, health]
---

## Summary
Andrew Huberman diskuterar vetenskapen bakom sömn och ger konkreta tips...

## Key Nuggets

### Insights
- **Morgonljus är kritiskt** - 10 minuter solljus inom första timmen...
  - Timestamp: 12:34
  - Importance: ⭐⭐⭐⭐⭐

### Action Items
- [ ] Exponera dig för solljus inom 30 min efter uppvakning
- [ ] Undvik kaffe första 90 minuterna

### Notable Quotes
> "Your nervous system is not designed for the modern world"

## Personal Notes
[Dina egna anteckningar här]
```

---

## 3. Teknisk Arkitektur

### 3.1 Projektstruktur

```
podcast-nuggets/
├── src/nuggets/
│   ├── __init__.py
│   ├── cli.py                  # Click-baserad CLI
│   │
│   ├── transcribe/
│   │   ├── __init__.py
│   │   ├── whisper.py          # MLX Whisper integration
│   │   ├── apple.py            # Apple Podcasts cache extraction
│   │   └── youtube.py          # yt-dlp + transkribering
│   │
│   ├── analyze/
│   │   ├── __init__.py
│   │   ├── extractor.py        # Claude-baserad nugget extraction
│   │   └── prompts.py          # Prompt templates
│   │
│   ├── models.py               # Pydantic datamodeller
│   │
│   └── export/
│       ├── __init__.py
│       ├── markdown.py         # Obsidian/Markdown export
│       └── json_export.py      # Strukturerad JSON export
│
├── data/
│   ├── transcripts/            # Råa transkript
│   ├── nuggets/                # Extraherade nuggets (JSON)
│   └── exports/                # Exporterade markdown-filer
│
├── prompts/
│   └── extract_nuggets.md      # Huvudprompt för extraktion
│
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

### 3.2 Datamodeller (Pydantic)

```python
# src/nuggets/models.py

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class NuggetType(str, Enum):
    INSIGHT = "insight"
    QUOTE = "quote"
    ACTION = "action"
    CONCEPT = "concept"
    STORY = "story"

class SourceType(str, Enum):
    PODCAST = "podcast"
    YOUTUBE = "youtube"
    AUDIO = "audio"

class Nugget(BaseModel):
    """En värdefull insikt extraherad från innehållet."""
    content: str = Field(..., description="Nuggetens innehåll")
    type: NuggetType
    timestamp: Optional[str] = Field(None, description="Tidsstämpel i formatet HH:MM:SS")
    context: Optional[str] = Field(None, description="Kort kontext om vad som diskuterades")
    importance: int = Field(3, ge=1, le=5, description="Viktighet 1-5")
    speaker: Optional[str] = Field(None, description="Vem sa detta")

class Episode(BaseModel):
    """Ett analyserat avsnitt med alla extraherade nuggets."""
    id: str = Field(..., description="Unikt ID: source-YYYY-MM-DD-hash")
    source_type: SourceType
    source_name: str = Field(..., description="T.ex. 'Huberman Lab', 'Lex Fridman'")
    title: str
    date: Optional[datetime] = None
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    guests: list[str] = Field(default_factory=list)

    # Analysresultat
    summary: str = Field(..., description="2-3 meningar sammanfattning")
    nuggets: list[Nugget] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Personligt
    personal_notes: str = ""
    rating: Optional[int] = Field(None, ge=1, le=5)

    # Metadata
    transcript_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None

class TranscriptMetadata(BaseModel):
    """Metadata för ett transkript."""
    source_type: SourceType
    source_name: str
    title: str
    date: Optional[datetime] = None
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    has_timestamps: bool = False
```

### 3.3 CLI Design

```bash
# Huvudkommandon
nuggets transcribe <source>     # Transkribera från källa
nuggets analyze <transcript>    # Analysera och extrahera nuggets
nuggets export <episode_id>     # Exportera till markdown
nuggets list                    # Lista alla analyserade avsnitt
nuggets search <query>          # Sök i nuggets

# Exempel
nuggets transcribe --apple "Huberman Lab"      # Från Apple Podcasts
nuggets transcribe --youtube "https://..."     # Från YouTube
nuggets transcribe --file episode.mp3          # Från fil

nuggets analyze data/transcripts/huberman-2024-01-15.txt
nuggets export huberman-2024-01-15-a1b2 --format obsidian
```

### 3.4 Dependencies

```toml
# pyproject.toml
[project]
name = "podcast-nuggets"
version = "0.1.0"
description = "Extract valuable nuggets from podcasts and videos"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0.0",           # CLI
    "pydantic>=2.0.0",        # Data validation
    "rich>=13.0.0",           # Terminal UI
    "anthropic>=0.39.0",      # Claude API
    "python-dotenv>=1.0.0",   # Environment config
]

[project.optional-dependencies]
transcribe = [
    "mlx-whisper>=0.1.0",     # Apple Silicon transcription
    "yt-dlp>=2024.1.0",       # YouTube download
]
dev = [
    "pytest>=7.0.0",
    "ruff",
]

[project.scripts]
nuggets = "nuggets.cli:main"
```

---

## 4. Implementationsplan

### Fas 1: Grundstruktur (Börja här)
1. Skapa projektstruktur med alla mappar
2. Skapa `pyproject.toml` med dependencies
3. Skapa `models.py` med alla Pydantic-modeller
4. Skapa `.env.example` och `.gitignore`
5. Skapa basic CLI-skelett med Click

### Fas 2: YouTube (KRITISK - börja här!)
1. Implementera `youtube.py` med:
   - `extract_video_id()` - parsa YouTube URL
   - `get_video_metadata()` - hämta titel, kanal, längd med yt-dlp
   - `get_youtube_transcript()` - hämta captions med youtube-transcript-api
   - `download_and_transcribe()` - fallback med Whisper
   - `process_youtube_video()` - huvudfunktion
2. Lägg till `nuggets youtube` kommando i CLI
3. Testa med en riktig YouTube-video

### Fas 3: Övrig transkribering
1. Implementera `whisper.py` (kopiera och anpassa från podstock)
2. Implementera `apple.py` (kopiera och anpassa från podstock)
3. Integrera i CLI: `nuggets transcribe`

### Fas 4: Analys
1. Skapa `prompts/extract_nuggets.md` med Claude-prompt
2. Implementera `extractor.py` med Claude API-anrop
3. Integrera i CLI: `nuggets analyze`

### Fas 5: Export
1. Implementera `markdown.py` för Obsidian-kompatibel export
2. Implementera `json_export.py` för strukturerad export
3. Integrera i CLI: `nuggets export`

### Fas 6: Kvalitet & UX
1. Lägg till `nuggets list` och `nuggets search`
2. Förbättra felhantering och progress-visning
3. Lägg till tester

---

## 5. Referenskod från podstock

### whisper.py (anpassa detta)

Den befintliga koden i `/Users/pontus/Developer/podcast-transcriber/src/podstock/transcribe/whisper.py`
använder `mlx-whisper` för snabb transkribering på Apple Silicon. Huvudfunktioner:

- `transcribe(audio_path, model, language)` - Transkriberar ljudfil
- `save_transcript(...)` - Sparar med metadata-header
- `load_transcript(...)` - Laddar och skippar header
- `estimate_duration(...)` - Estimerar längd

**Anpassningar för nuggets:**
- Förenkla header-formatet
- Ta bort podcast-specifik logik
- Behåll core transcription logic

### apple.py (anpassa detta)

Den befintliga koden extraherar transkript från Apple Podcasts TTML-cache:

- `list_available_transcripts()` - Listar tillgängliga transkript
- `parse_ttml(path)` - Parsear TTML till text
- `extract_and_save(...)` - Extraherar och sparar

**Anpassningar för nuggets:**
- Ta bort podcast-modell dependency
- Förenkla till standalone-funktion
- Behåll TTML-parsing logic

---

## 6. Claude Prompt för Nugget Extraction

Spara denna som `prompts/extract_nuggets.md`:

```markdown
# Extract Nuggets from Transcript

You are analyzing a transcript to extract the most valuable insights, quotes, and action items.

## Input
- Transcript from: {source_name}
- Episode title: {title}
- Duration: {duration} minutes

## Your Task

Extract 5-15 "nuggets" - the most valuable pieces of information from this content.

### Nugget Types

1. **insight** - Key learnings, surprising facts, important principles
2. **quote** - Memorable quotes worth saving
3. **action** - Specific things the listener should do
4. **concept** - Important definitions or mental models
5. **story** - Illustrative anecdotes or examples

### Output Format

Respond with valid JSON:

```json
{
  "summary": "2-3 sentence summary of the episode",
  "guests": ["Guest Name 1", "Guest Name 2"],
  "suggested_tags": ["tag1", "tag2", "tag3"],
  "nuggets": [
    {
      "content": "The nugget content - clear and actionable",
      "type": "insight|quote|action|concept|story",
      "timestamp": "HH:MM:SS or null if unknown",
      "context": "Brief context about what was being discussed",
      "importance": 1-5,
      "speaker": "Speaker name or null"
    }
  ]
}
```

### Guidelines

1. **Quality over quantity** - Only include truly valuable nuggets
2. **Be specific** - "Exercise 30 min daily" not "Exercise is good"
3. **Preserve voice** - Keep the speaker's phrasing in quotes
4. **Prioritize actionable** - Prefer insights you can act on
5. **Include timestamps** - When available in the transcript

## Transcript

{transcript}
```

---

## 7. Miljövariabler

Skapa `.env.example`:

```bash
# Claude API
ANTHROPIC_API_KEY=your-api-key-here

# Optional: Custom data directory
NUGGETS_DATA_DIR=./data

# Optional: Default Whisper model
WHISPER_MODEL=large-v3

# Optional: Default language for transcription
WHISPER_LANGUAGE=sv
```

---

## 8. .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual environments
venv/
.venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Data (transcripts and nuggets)
data/transcripts/
data/nuggets/
data/exports/
data/audio/

# Keep data structure
!data/.gitkeep
!data/transcripts/.gitkeep
!data/nuggets/.gitkeep
!data/exports/.gitkeep

# macOS
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
```

---

## 9. Checklista för Start

När du startar en ny Claude Code-session i `/Users/pontus/Developer/podcast-nuggets/`:

- [ ] Läs denna fil först (CLAUDE-PROMPT.md)
- [ ] Skapa projektstruktur (alla mappar)
- [ ] Skapa `pyproject.toml`
- [ ] Skapa `src/nuggets/__init__.py` och `models.py`
- [ ] Skapa `.env.example` och `.gitignore`
- [ ] Initiera git repo
- [ ] Börja med Fas 1 i implementationsplanen

---

## 10. Kontakt med podstock

Om du behöver referera till den befintliga koden:

```bash
# Whisper transcription
cat /Users/pontus/Developer/podcast-transcriber/src/podstock/transcribe/whisper.py

# Apple Podcasts extraction
cat /Users/pontus/Developer/podcast-transcriber/src/podstock/transcribe/apple.py

# Configuration pattern
cat /Users/pontus/Developer/podcast-transcriber/src/podstock/core/config.py
```

Men kom ihåg: **podcast-nuggets ska vara enklare och mer fokuserat** än podstock.
Kopiera inte allt - ta bara det som behövs.

---

## 11. Framtida Idéer (Backlog)

Dessa är **inte** del av MVP, men bra att veta om:

1. **Notion-integration** - Automatisk sync till Notion
2. **Tagg-taxonomi** - Fördefinierade taggar per kategori
3. **Spaced repetition** - Visa gamla nuggets för review
4. **Sammanfattning per ämne** - Aggregera nuggets per tagg
5. **Browser extension** - Snabb capture från webben
6. **Podcast-prenumeration** - Auto-transkribera nya avsnitt

---

*Skapad: 2024-12-26*
*Författare: Pontus (med Claude Code)*
