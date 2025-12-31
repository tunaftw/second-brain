# Podcast Nuggets - Master Plan

> **Syfte:** Detta dokument är en komplett blueprint för att bygga `podcast-nuggets` - ett personligt kunskapsbibliotek. Kopiera denna fil till ditt `podcast-nuggets`-repo och kör `/brainstorm` i Claude Code för att läsa planen och påbörja implementation.

---

## Projektöversikt

**podcast-nuggets** är ett personligt kunskapsbibliotek som fångar insikter från:
- **YouTube** (primär källa för transkript) - Huberman Lab, Joe Rogan, Chris Williamson, Diary of a CEO, m.fl.
- **Podcasts** (när innehåll inte finns på YouTube)
- **Twitter/X** - tweets, trådar, och artiklar länkade från Twitter

### Vad systemet producerar

1. **Taggade takeaways** - Korta insikter med kategorier och taggar, sökbara
2. **Strukturerade anteckningar** - Längre sammanfattningar per källa
3. **Citat** - Minnesvärda quotes med kontext och talare
4. **Kunskapskort** - Flashcard-format: koncept + förklaring
5. **Action items** - Konkreta saker att göra

### Analysmetoder (användaren väljer)

| Metod | Beskrivning | När |
|-------|-------------|-----|
| **Claude Code** | Direkt i konversation, interaktivt | Enstaka analyser, snabb feedback |
| **OpenCode/GLM-4.7** | Python-script i separat terminal, gratis | Batch-körning, stora volymer |

### Lagring

- **JSON-filer** som source of truth (läsbara, versionerbara)
- **SQLite** som sökbart index (synkas från JSON)
- **Framtida:** Vector embeddings för semantisk sökning, Apple Notes export

---

## Mappstruktur

```
podcast-nuggets/
├── .claude/
│   └── skills/                        # Claude Code skills
│       ├── youtube-download/
│       │   ├── SKILL.md
│       │   └── references/
│       │       └── download-method.md
│       ├── podcast-download/
│       │   ├── SKILL.md
│       │   └── references/
│       │       └── download-method.md
│       ├── twitter-download/
│       │   ├── SKILL.md
│       │   └── references/
│       │       └── download-method.md
│       ├── analyze/
│       │   ├── SKILL.md
│       │   └── references/
│       │       ├── claude-method.md
│       │       ├── opencode-method.md
│       │       └── output-schema.md
│       ├── database-sync/
│       │   ├── SKILL.md
│       │   └── references/
│       │       └── sync-method.md
│       └── search/
│           ├── SKILL.md
│           └── references/
│               └── search-method.md
├── src/
│   └── nuggets/                       # Python-moduler
│       ├── __init__.py
│       ├── analyze/
│       │   ├── __init__.py
│       │   ├── prompt_builder.py      # Bygger analys-prompts
│       │   └── validator.py           # Pydantic-validering
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py              # SQLAlchemy-modeller
│       │   └── sync.py                # JSON → SQLite sync
│       └── export/
│           ├── __init__.py
│           └── apple_notes.py         # Framtida Apple Notes export
├── scripts/
│   └── analyze_batch.py               # OpenCode batch-analys
├── data/
│   ├── youtube/
│   │   ├── transcripts/               # Råa transkript
│   │   └── analyses/                  # JSON-analyser
│   ├── podcasts/
│   │   ├── transcripts/
│   │   └── analyses/
│   ├── twitter/
│   │   ├── sources/                   # Tweets, artiklar
│   │   └── analyses/
│   ├── nuggets.db                     # SQLite sökindex
│   └── categories.json                # Konfigurerbara kategorier
├── pyproject.toml
└── README.md
```

---

## Kategorier

Flexibla kategorier som kan utökas över tid.

**`data/categories.json`:**
```json
{
  "categories": [
    {"id": "philosophy", "name": "Filosofi & Livsvisdom", "emoji": "🧠"},
    {"id": "career", "name": "Karriär & Professionell utveckling", "emoji": "💼"},
    {"id": "health", "name": "Hälsa & Träning", "emoji": "💪"},
    {"id": "relationships", "name": "Relationer & Kommunikation", "emoji": "🤝"},
    {"id": "productivity", "name": "Produktivitet & Vanor", "emoji": "⚡"},
    {"id": "creativity", "name": "Kreativitet & Lärande", "emoji": "🎨"}
  ]
}
```

---

## JSON-schema för analyser

Varje analyserad källa producerar en JSON-fil med detta schema:

**`data/{source}/analyses/{id}.json`:**
```json
{
  "source": {
    "type": "youtube|podcast|twitter",
    "url": "https://...",
    "title": "Andrew Huberman: Sleep Optimization",
    "author": "Huberman Lab",
    "date": "2025-01-15",
    "duration_minutes": 120
  },
  "summary": "Kortfattad sammanfattning av hela innehållet. 2-3 meningar som fångar kärnan.",
  "takeaways": [
    {
      "id": "uuid-here",
      "text": "Morgonsol inom 30 min efter uppvaknande förbättrar dygnsrytm",
      "category": "health",
      "tags": ["sleep", "circadian", "sunlight"],
      "confidence": "high|medium|low",
      "timestamp": "00:15:32"
    }
  ],
  "quotes": [
    {
      "id": "uuid-here",
      "text": "Your nervous system is not designed for chronic stress",
      "speaker": "Andrew Huberman",
      "context": "Diskussion om stress-respons och dess påverkan på sömn",
      "timestamp": "00:42:18"
    }
  ],
  "knowledge_cards": [
    {
      "id": "uuid-here",
      "concept": "Adenosinuppbyggnad",
      "explanation": "Adenosin är en molekyl som byggs upp under vakenhet och skapar sömnighet. Koffein blockerar adenosinreceptorer tillfälligt men tar inte bort adenosinet - därför känner man sig trött när koffeinet släpper.",
      "category": "health",
      "related_concepts": ["caffeine", "sleep-pressure", "circadian-rhythm"]
    }
  ],
  "action_items": [
    "Gå ut i morgonsol inom 30 min efter uppvaknande",
    "Undvik koffein de första 90 minuterna efter uppvaknande",
    "Håll sovrummet mörkt och svalt"
  ],
  "metadata": {
    "analyzed_at": "2025-01-20T14:30:00Z",
    "analysis_method": "claude-code|opencode",
    "model": "claude-opus-4-5-20251101|glm-4.7",
    "schema_version": "1.0",
    "embedding": null
  }
}
```

---

## SQLite-databasschema

**`data/nuggets.db`:**

```sql
-- Källor (YouTube, podcasts, Twitter)
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('youtube', 'podcast', 'twitter')),
    url TEXT UNIQUE,
    title TEXT,
    author TEXT,
    date DATE,
    duration_minutes INTEGER,
    transcript_path TEXT,
    analysis_path TEXT,
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Takeaways (sökbara insikter)
CREATE TABLE takeaways (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    category TEXT,
    tags TEXT,  -- JSON array: ["sleep", "circadian"]
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    timestamp TEXT,  -- "00:15:32"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Citat
CREATE TABLE quotes (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    speaker TEXT,
    context TEXT,
    timestamp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kunskapskort
CREATE TABLE knowledge_cards (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    explanation TEXT NOT NULL,
    category TEXT,
    related_concepts TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Action items
CREATE TABLE action_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kategorier (konfigurerbara)
CREATE TABLE categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    emoji TEXT,
    sort_order INTEGER DEFAULT 0
);

-- Index för snabbare queries
CREATE INDEX idx_takeaways_category ON takeaways(category);
CREATE INDEX idx_takeaways_source ON takeaways(source_id);
CREATE INDEX idx_quotes_speaker ON quotes(speaker);
CREATE INDEX idx_knowledge_cards_category ON knowledge_cards(category);
CREATE INDEX idx_sources_type ON sources(type);
CREATE INDEX idx_sources_author ON sources(author);

-- FTS5 för fulltext-sökning
CREATE VIRTUAL TABLE takeaways_fts USING fts5(
    text,
    tags,
    content=takeaways,
    content_rowid=rowid
);

CREATE VIRTUAL TABLE quotes_fts USING fts5(
    text,
    speaker,
    context,
    content=quotes,
    content_rowid=rowid
);

CREATE VIRTUAL TABLE knowledge_cards_fts USING fts5(
    concept,
    explanation,
    content=knowledge_cards,
    content_rowid=rowid
);

-- Triggers för att hålla FTS synkad
CREATE TRIGGER takeaways_ai AFTER INSERT ON takeaways BEGIN
    INSERT INTO takeaways_fts(rowid, text, tags) VALUES (NEW.rowid, NEW.text, NEW.tags);
END;

CREATE TRIGGER quotes_ai AFTER INSERT ON quotes BEGIN
    INSERT INTO quotes_fts(rowid, text, speaker, context) VALUES (NEW.rowid, NEW.text, NEW.speaker, NEW.context);
END;

CREATE TRIGGER knowledge_cards_ai AFTER INSERT ON knowledge_cards BEGIN
    INSERT INTO knowledge_cards_fts(rowid, concept, explanation) VALUES (NEW.rowid, NEW.concept, NEW.explanation);
END;
```

---

## Skills

### 1. youtube-download

**Syfte:** Ladda ner transkript från YouTube-videos.

**`.claude/skills/youtube-download/SKILL.md`:**
```markdown
---
name: youtube-download
description: Ladda ner transkript från YouTube-video. Sparar med beskrivande
  filnamn inkl. kanal, titel och datum.
---

# YouTube Download Skill

## Trigger
Använd när användaren vill ladda ner transkript från en YouTube-URL.

## Metod
1. Användaren ger en YouTube-URL
2. Extrahera video-metadata (titel, kanal, datum, längd)
3. Hämta transkript (föredra manuella captions, fallback till auto-generated)
4. Spara till `data/youtube/transcripts/{kanal}-{datum}-{slug}.md`
5. Bekräfta för användaren

## Filnamnformat
`huberman-lab-2025-01-15-sleep-optimization.md`

## Dependencies
- yt-dlp eller youtube-transcript-api
```

---

### 2. podcast-download

**Syfte:** Ladda ner podcast-transkript via RSS eller Apple Podcasts.

**`.claude/skills/podcast-download/SKILL.md`:**
```markdown
---
name: podcast-download
description: Ladda ner podcast-transkript. Använder Apple Podcasts API
  (om tillgängligt) eller Whisper för transkribering.
---

# Podcast Download Skill

## Trigger
Använd när användaren vill ladda ner transkript från en podcast-episod.

## Metoder
1. **Apple Podcasts** (föredraget) - Om transkript finns tillgängligt
2. **Whisper** (fallback) - Ladda ner audio och transkribera lokalt

## Flöde
1. Användaren ger podcast-namn och episod (eller RSS-URL)
2. Sök efter episoden
3. Försök hämta transkript via Apple Podcasts API
4. Om ej tillgängligt: ladda ner audio och kör Whisper
5. Spara till `data/podcasts/transcripts/{podcast}-{datum}-{slug}.md`
```

---

### 3. twitter-download

**Syfte:** Hämta tweets, trådar och artiklar från Twitter/X.

**`.claude/skills/twitter-download/SKILL.md`:**
```markdown
---
name: twitter-download
description: Ladda ner tweets, trådar och artiklar från Twitter/X.
  Stödjer både enskilda tweets och länkade artiklar.
---

# Twitter Download Skill

## Trigger
Använd när användaren vill samla innehåll från Twitter.

## Innehållstyper
1. **Enskilda tweets** - Spara tweet-text med metadata
2. **Trådar** - Samla hela tråden i ordning
3. **Artiklar** - Extrahera innehåll från länkade artiklar (Substack, Medium, etc.)

## Metoder
1. **Twitter API** (om tillgänglig) - Automatiserat
2. **Browser scraping** (manuellt) - Användaren kopierar innehåll

## Filformat
Spara till `data/twitter/sources/{handle}-{datum}-{id}.json`
```

---

### 4. analyze

**Syfte:** Analysera transkript och extrahera insikter.

**`.claude/skills/analyze/SKILL.md`:**
```markdown
---
name: analyze
description: Analysera transkript för att extrahera takeaways, citat,
  kunskapskort och action items. Två metoder: Claude Code (interaktiv)
  eller OpenCode/GLM-4.7 (batch).
---

# Analyze Skill

## Trigger
Använd när användaren vill analysera ett transkript.

## Steg 1: Välj metod
Fråga användaren:
1. **Claude Code** - Analysera direkt i konversationen
2. **OpenCode/GLM-4.7** - Kör batch-script i separat terminal

## Vid Claude Code
Läs `references/claude-method.md` och följ instruktionerna.

## Vid OpenCode
Läs `references/opencode-method.md` och visa kommandot.

## Output
Sparas som JSON enligt `references/output-schema.md`
```

**`.claude/skills/analyze/references/claude-method.md`:**
```markdown
# Claude Code Analysmetod

## Instruktioner
1. Läs transkriptet som ska analyseras
2. Läs kategorierna från `data/categories.json`
3. Analysera innehållet och extrahera:
   - Summary (2-3 meningar)
   - Takeaways (minst 5, med kategori och taggar)
   - Quotes (minnesvärda citat med kontext)
   - Knowledge cards (koncept som förklaras)
   - Action items (konkreta saker att göra)
4. Generera UUIDs för varje item
5. Spara JSON till `data/{source_type}/analyses/{id}.json`
6. Bekräfta för användaren

## Prompt-mall
Se output-schema.md för exakt JSON-format att producera.
```

**`.claude/skills/analyze/references/opencode-method.md`:**
```markdown
# OpenCode/GLM-4.7 Analysmetod

## Förutsättningar
- OpenCode körs lokalt
- GLM-4.7 modell tillgänglig

## Användning

### Analysera en specifik fil:
```bash
python scripts/analyze_batch.py --file data/youtube/transcripts/huberman-2025-01-15-sleep.md
```

### Analysera alla väntande transkript:
```bash
python scripts/analyze_batch.py --source youtube --pending
```

### Analysera med specifik modell:
```bash
python scripts/analyze_batch.py --pending --model glm-4.7
```

## Output
Resultat sparas automatiskt till `data/{source}/analyses/`
```

---

### 5. database-sync

**Syfte:** Synka JSON-analyser till SQLite.

**`.claude/skills/database-sync/SKILL.md`:**
```markdown
---
name: database-sync
description: Synka JSON-analysfiler till SQLite-databasen. Kör efter
  nya analyser för att göra innehållet sökbart.
---

# Database Sync Skill

## Trigger
Använd efter att nya analyser har skapats.

## Flöde
1. Skanna `data/*/analyses/` efter JSON-filer
2. Jämför med befintliga poster i SQLite
3. Lägg till nya / uppdatera ändrade
4. Visa sammanfattning: X nya, Y uppdaterade

## Kommando
```bash
python -m nuggets.db.sync
```
```

---

### 6. search

**Syfte:** Sök i kunskapsbiblioteket.

**`.claude/skills/search/SKILL.md`:**
```markdown
---
name: search
description: Sök i kunskapsbiblioteket efter takeaways, citat eller koncept.
---

# Search Skill

## Trigger
Använd när användaren vill söka i sitt kunskapsbibliotek.

## Söktyper
1. **Fulltext** - "sök efter sleep optimization"
2. **Kategori** - "visa alla health takeaways"
3. **Källa** - "vad har Huberman sagt?"
4. **Tags** - "hitta allt taggat med 'discipline'"

## Exempel-queries
- "Vad har jag lärt mig om morgonrutiner?"
- "Visa citat från Joe Rogan"
- "Alla kunskapskort i kategorin philosophy"
```

---

## Python-moduler

### `src/nuggets/analyze/prompt_builder.py`

```python
"""Bygger analys-prompts för både Claude Code och OpenCode."""

import json
from pathlib import Path

def load_categories() -> list[dict]:
    """Ladda kategorier från categories.json."""
    path = Path("data/categories.json")
    if path.exists():
        return json.loads(path.read_text())["categories"]
    return []

def build_analysis_prompt(
    transcript: str,
    source_metadata: dict,
    categories: list[dict] | None = None
) -> str:
    """
    Bygg prompt för kunskapsextraktion.

    Args:
        transcript: Transkriptet att analysera
        source_metadata: {"type": "youtube", "title": "...", "author": "..."}
        categories: Lista av kategorier, eller None för att ladda från fil

    Returns:
        Komplett prompt för LLM
    """
    if categories is None:
        categories = load_categories()

    category_list = "\n".join(
        f"- {c['id']}: {c['name']}" for c in categories
    )

    return f'''Analysera följande transkript och extrahera värdefulla insikter.

## Källa
- Typ: {source_metadata.get("type", "unknown")}
- Titel: {source_metadata.get("title", "Unknown")}
- Författare: {source_metadata.get("author", "Unknown")}

## Kategorier
{category_list}

## Uppgift
Extrahera:
1. **Summary** - 2-3 meningar som fångar kärnan
2. **Takeaways** - Minst 5 konkreta insikter med kategori och taggar
3. **Quotes** - Minnesvärda citat med talare och kontext
4. **Knowledge Cards** - Koncept som förklaras (concept + explanation)
5. **Action Items** - Konkreta saker man kan göra

## Output Format
Returnera som JSON enligt detta schema:
{{
  "summary": "...",
  "takeaways": [...],
  "quotes": [...],
  "knowledge_cards": [...],
  "action_items": [...]
}}

## Transkript
{transcript}
'''
```

### `scripts/analyze_batch.py`

```python
#!/usr/bin/env python3
"""
Batch-analys av transkript via OpenCode/GLM-4.7.

Användning:
    python scripts/analyze_batch.py --source youtube --pending
    python scripts/analyze_batch.py --file path/to/transcript.md
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import uuid

# Konfigurera via environment
OPENCODE_API_URL = os.getenv("OPENCODE_API_URL", "http://localhost:11434")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "glm-4.7")

def find_pending_transcripts(source: str) -> list[Path]:
    """Hitta transkript som saknar analys."""
    transcript_dir = Path(f"data/{source}/transcripts")
    analysis_dir = Path(f"data/{source}/analyses")

    if not transcript_dir.exists():
        return []

    pending = []
    for transcript in transcript_dir.glob("*.md"):
        analysis_path = analysis_dir / f"{transcript.stem}.json"
        if not analysis_path.exists():
            pending.append(transcript)

    return pending

def analyze_transcript(transcript_path: Path, model: str = OPENCODE_MODEL) -> dict:
    """Analysera ett transkript via OpenCode."""
    from nuggets.analyze.prompt_builder import build_analysis_prompt

    # Läs transkript
    transcript = transcript_path.read_text()

    # Extrahera metadata från filnamn
    # Format: author-YYYY-MM-DD-slug.md
    parts = transcript_path.stem.split("-")
    source_metadata = {
        "type": transcript_path.parent.parent.name,
        "title": " ".join(parts[4:]).replace("-", " ").title() if len(parts) > 4 else transcript_path.stem,
        "author": parts[0] if parts else "Unknown",
        "date": f"{parts[1]}-{parts[2]}-{parts[3]}" if len(parts) >= 4 else None
    }

    # Bygg prompt
    prompt = build_analysis_prompt(transcript, source_metadata)

    # Anropa OpenCode/GLM-4.7
    # TODO: Implementera faktiskt API-anrop
    # response = call_opencode(prompt, model)

    # Placeholder för nu
    print(f"Would analyze: {transcript_path}")
    print(f"Using model: {model}")

    return {}

def main():
    parser = argparse.ArgumentParser(description="Batch-analysera transkript")
    parser.add_argument("--source", choices=["youtube", "podcasts", "twitter"])
    parser.add_argument("--file", type=Path, help="Specifik fil att analysera")
    parser.add_argument("--pending", action="store_true", help="Analysera alla väntande")
    parser.add_argument("--model", default=OPENCODE_MODEL)

    args = parser.parse_args()

    if args.file:
        analyze_transcript(args.file, args.model)
    elif args.pending and args.source:
        pending = find_pending_transcripts(args.source)
        print(f"Hittade {len(pending)} väntande transkript")
        for path in pending:
            analyze_transcript(path, args.model)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

---

## Implementation - Nästa steg

> **OBS:** Innan implementation, undersök vad som redan finns i repot och anpassa planen därefter.

### Fas 1: Grundstruktur
1. Skapa mappstruktur enligt ovan
2. Skapa `data/categories.json` med initiala kategorier
3. Sätt upp `pyproject.toml` med dependencies

### Fas 2: Download Skills
1. Implementera `youtube-download` skill
2. Implementera `podcast-download` skill
3. Implementera `twitter-download` skill

### Fas 3: Analys
1. Skapa `src/nuggets/analyze/` moduler
2. Implementera `analyze` skill med båda metoder
3. Skapa `scripts/analyze_batch.py`

### Fas 4: Databas
1. Skapa SQLite-schema
2. Implementera `src/nuggets/db/sync.py`
3. Skapa `database-sync` skill

### Fas 5: Sökning
1. Implementera `search` skill
2. Lägg till FTS-queries

### Fas 6: Export (framtid)
1. Apple Notes export
2. Vector embeddings för semantisk sökning

---

## Tekniska dependencies

```toml
[project]
dependencies = [
    "yt-dlp",              # YouTube downloads
    "youtube-transcript-api",
    "pydantic>=2.0",       # Validering
    "sqlalchemy>=2.0",     # Database ORM
    "rich",                # CLI output
]

[project.optional-dependencies]
whisper = [
    "mlx-whisper",         # Apple Silicon transkribering
]
```

---

## Inspiration från PodStock

Följande filer från `finance-agent` kan användas som referens:
- `.claude/skills/analyze/` - Skill-struktur och dual-method approach
- `.claude/skills/youtube-download/` - YouTube-nedladdning
- `.claude/skills/twitter-download/` - Twitter-hantering
- `src/podstock/db/` - SQLAlchemy-modeller och sync-logik
- `scripts/` - Batch-scripts för OpenCode
