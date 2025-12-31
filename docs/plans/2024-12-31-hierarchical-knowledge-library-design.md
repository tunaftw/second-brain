# Hierarchical Knowledge Library Design

> **Status:** Validated design, ready for implementation
> **Date:** 2024-12-31
> **Author:** Pontus + Claude

---

## Overview

Omstrukturering av podcast-nuggets till ett hierarkiskt kunskapsbibliotek med:
- **Segment/Nugget-hierarki** för olika "zoom-nivåer"
- **Semantisk sökning** via embeddings
- **Automatiska kopplingar** mellan relaterat innehåll
- **Speaker identification** och **timestamp-bevarande**
- **4 dedikerade Claude skills** för tydliga workflows

---

## Datamodeller

### Segment

Ett tematiskt block från en episode (t.ex. "diskussion om morgonrutiner").

```python
class Segment(BaseModel):
    """Ett tematiskt block från en episode."""

    id: str                          # segment-{episode_id}-{index}
    episode_id: str                  # Koppling till Episode

    # Innehållsnivåer
    raw_segment: str                 # Exakt transkript
    full: str | None                 # Redigerad, uttömmande (om tillräckligt material)

    # Metadata
    topic: str                       # sleep, productivity, etc.
    theme_name: str                  # "Morgonrutiner", "Dopamin och motivation"
    start_timestamp: str | None      # "01:23:45"
    end_timestamp: str | None        # "01:28:30"

    # Speakers
    speakers: list[str]              # Alla som pratar i segmentet
    primary_speaker: str | None      # Huvudtalare för detta segment

    # Semantisk sökning
    embedding: list[float] | None    # Vector för similarity search

    # Kopplingar
    related_segment_ids: list[str]   # Liknande segment från andra episodes
```

### Nugget

En enskild insikt inom ett segment.

```python
class Nugget(BaseModel):
    """En enskild insikt inom ett segment."""

    id: str                          # nugget-{segment_id}-{index}
    segment_id: str                  # Koppling till Segment

    # Innehållsnivåer (alla optional utom headline, fylls i intelligent)
    condensed: str | None            # Kärnan + kontext
    headline: str                    # Alltid - för snabb skanning
    quote: str | None                # Om ordagrant citat finns

    # Klassificering
    type: NuggetType                 # insight, quote, action, concept, story
    wisdom_type: str | None          # principle, habit, technique, etc.
    importance: int                  # 1-5, AI-bedömd
    stars: int | None                # 1-3, personlig rating

    # Attribution
    speaker: str | None              # Vem sa detta
    timestamp: str | None            # "01:25:12" - specifik tidpunkt

    # Semantisk sökning
    embedding: list[float] | None    # Vector för similarity search
```

### Flexibla nivåer

Inte alla nivåer behöver finnas för varje nugget:

```
Scenario 1: Djup diskussion utan tydligt citat
├── raw_segment: ✓ (5 min diskussion)
├── full: ✓ (resonemang + kontext)
├── condensed: ✓ (kärnan)
├── headline: ✓
└── quote: null  ← inget slagkraftigt citat

Scenario 2: Name-droppad quote utan kontext
├── raw_segment: ✓ (kort segment)
├── full: null  ← inte tillräckligt material
├── condensed: null
├── headline: ✓
└── quote: ✓ "The obstacle is the way"

Scenario 3: Komplett nugget
├── raw_segment: ✓
├── full: ✓
├── condensed: ✓
├── headline: ✓
└── quote: ✓
```

---

## Lagring

### Filstruktur

```
data/
├── raw/                          # Oförändrat - råa transkript
│   ├── youtube/{channel}/{date}-{id}.json
│   └── twitter/{author}/{date}-{id}.json
│
├── analysis/                     # Uppdaterad struktur
│   ├── youtube/{channel}/{date}-{id}.json    # Episode + Segments + Nuggets
│   └── twitter/{author}/{date}-{id}.json
│
├── library/
│   ├── index.json               # Snabbindex för CLI
│   └── embeddings.db            # SQLite med vectors (sqlite-vec)
│
└── exports/
```

### Embeddings

```python
# Vad får embeddings?
- Segment.full → embedding (primär för semantisk sökning)
- Nugget.condensed → embedding (för nugget-nivå sökning)

# Teknologi
- Voyage AI eller OpenAI embeddings
- SQLite med sqlite-vec extension
```

---

## Skills-arkitektur

### Översikt

```
nuggets-fetch    → Hämta content till data/raw/
nuggets-analyze  → Extrahera segments/nuggets till data/analysis/
nuggets-explore  → Sök, koppla, deep-dive
nuggets-curate   → Star ratings, best-of
```

### nuggets-fetch

**Trigger:** URL, "ladda ner", "hämta"

**Ansvar:**
- YouTube: youtube-transcript-api (automatisk)
- Twitter: Jina Reader eller /chrome (manuell)
- Podcast: Manuell paste / framtida Apple Podcasts

**Output:** `data/raw/{source}/{channel}/{date}-{id}.json`

**Metadata som sparas:**
- titel, kanal, duration, timestamps
- parsed_host (från kanal)
- parsed_guest (från episodtitel)

### nuggets-analyze

**Trigger:** "analysera", "extrahera", efter fetch

**Ansvar:**
- Identifiera segments (tematiska block)
- Extrahera nuggets per segment
- Speaker identification (host från kanal, gäst från titel)
- Bevara timestamps (segment start/end, nugget-specifik)
- Generera embeddings
- Hitta relaterade segments

**Modes:** standard (auto) | interactive (välj themes/djup)

**Output:** `data/analysis/{source}/{channel}/{date}-{id}.json`

### nuggets-explore

**Trigger:** "sök", "hitta", "vad vet jag om", "koppla", "jämför"

**Kommandon:**
- `search <query>` → Nugget-träffar (headline + condensed)
- `explore <topic>` → Segment-träffar med kopplingar (semantisk)
- `connect <A> <B>` → Jämför två källor/ämnen/talare
- `deep-dive <id>` → Visa full → raw_segment + timestamp
- `related <id>` → Liknande från andra podcasts
- `who-said <query>` → Filtrera på specifik speaker

### nuggets-curate

**Trigger:** "betygsätt", "star", "favoriter"

**Ansvar:**
- Star ratings (1-3)
- Interaktiv genomgång
- Exportera best-of (med timestamps för återlyssning)

### Skill-filstruktur

```
.claude/skills/
├── nuggets-fetch/
│   ├── SKILL.md
│   └── references/
│       ├── youtube-method.md
│       ├── twitter-method.md
│       └── metadata-parsing.md
│
├── nuggets-analyze/
│   ├── SKILL.md
│   └── references/
│       ├── extraction-prompt.md
│       ├── speaker-hints.md
│       └── embedding-strategy.md
│
├── nuggets-explore/
│   ├── SKILL.md
│   └── references/
│       └── query-patterns.md
│
└── nuggets-curate/
    └── SKILL.md
```

---

## Extraktionsprocess

```
INPUT: Raw transcript + metadata
  ↓
STEG 1: Segmentering
  Claude identifierar 8-15 tematiska block med timestamps
  ↓
STEG 2: Segment-nivå extraktion
  raw_segment, full (om tillräckligt), speakers
  ↓
STEG 3: Nugget-extraktion per segment
  2-8 nuggets per segment med headline, condensed, quote, speaker, timestamp
  ↓
STEG 4: Embeddings & kopplingar
  Generera embeddings, hitta relaterade segments (similarity > 0.8)
  ↓
OUTPUT: Episode JSON + embeddings.db
```

---

## Sökning & Utforskning

### nuggets search (nugget-nivå)

```bash
nuggets search "morgonsol"
```

1. Fulltext-sökning i headline + condensed + quote
2. Rankas på: textmatch + importance + stars
3. Visar: headline, condensed, speaker, timestamp, relaterade

### nuggets explore (segment-nivå, semantisk)

```bash
nuggets explore "sömnoptimering"
```

1. Embed query → vector search mot segment.full embeddings
2. Returnera topp-10 mest relevanta segments
3. Visa nuggets som highlights per segment
4. Visa relaterade segments från andra podcasts

### Övriga kommandon

```bash
nuggets connect "Huberman" "Goggins" --topic discipline
nuggets deep-dive nugget-xyz-123
nuggets search "dopamine" --speaker "Anna Lembke"
nuggets related segment-abc-456
```

---

## Speaker Identification

1. **FETCH-steget sparar:**
   - channel_name → host är känd
   - episode_title → gäst extraheras

2. **ANALYZE-steget använder hints:**
   - "Host är Andrew Huberman, gäst är Andy Galpin"
   - Claude identifierar vem som pratar baserat på kontext
   - Varje nugget får speaker-attribution där det är tydligt

---

## Timestamps

```python
Segment:
  start_timestamp: "01:23:45"
  end_timestamp: "01:28:30"

Nugget:
  timestamp: "01:25:12"  # Specifik tidpunkt
```

Export inkluderar klickbara länkar:
```
⭐ [01:25:12] Caffeine blocks adenosine receptors...
→ youtube.com/watch?v=xxx&t=5112
```

---

## Implementation

### Fas 1: Datamodeller & Lagring
- Uppdatera `models.py` med `Segment` och uppdaterad `Nugget`
- Migrera befintlig data
- Sätt upp `embeddings.db` med sqlite-vec

### Fas 2: nuggets-fetch skill
- Skapa proper skill-struktur
- Refaktorera befintlig YouTube/Twitter-logik
- Speaker/guest-parsing från titlar
- Timestamp-bevarande

### Fas 3: nuggets-analyze skill
- Ny extraktionsprompt för segment/nugget-hierarkin
- Embedding-generering
- Koppla relaterade segments
- Interactive mode

### Fas 4: nuggets-explore skill
- Vector search med sqlite-vec
- search, explore, connect, deep-dive, related

### Fas 5: nuggets-curate uppdatering
- Anpassa till ny struktur
- Export med timestamps

### Nya dependencies

```toml
dependencies = [
    "sqlite-vec",          # Vector search i SQLite
    "voyageai",            # Embeddings (alternativ: openai)
]
```

---

## Användningsfall

| Use case | Skill | Kommando |
|----------|-------|----------|
| Spaced repetition | explore/curate | `nuggets explore "favorites"` |
| Just-in-time lookup | search | `nuggets search "discipline"` |
| Kreativ koppling | explore | `nuggets connect "Huberman" "Goggins"` |
| Återlyssning | deep-dive | `nuggets deep-dive <id>` → timestamp-länk |
