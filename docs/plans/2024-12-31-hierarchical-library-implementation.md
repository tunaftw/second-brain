# Hierarchical Knowledge Library - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure podcast-nuggets with Segment/Nugget hierarchy, embeddings, and 4 Claude skills.

**Architecture:** Episodes contain Segments (thematic blocks with full context), which contain Nuggets (individual insights). Embeddings enable semantic search. Skills automate fetch → analyze → explore → curate workflow.

**Tech Stack:** Python 3.11+, Pydantic, sqlite-vec, Voyage AI embeddings, Click CLI, Claude API

---

## Phase 1: Data Models & Storage

### Task 1.1: Add Segment Model

**Files:**
- Modify: `src/nuggets/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
class TestSegment:
    """Tests for Segment model."""

    def test_segment_minimal(self):
        """Segment can be created with minimal fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="This is the raw transcript text...",
            topic="productivity",
            theme_name="Morning Routines",
        )
        assert segment.id == "segment-ep123-0"
        assert segment.topic == "productivity"
        assert segment.full is None  # optional

    def test_segment_with_all_fields(self):
        """Segment supports all optional fields."""
        from nuggets.models import Segment

        segment = Segment(
            id="segment-ep123-0",
            episode_id="ep123",
            raw_segment="Raw transcript...",
            full="Edited comprehensive summary...",
            topic="sleep",
            theme_name="Sleep Optimization",
            start_timestamp="01:23:45",
            end_timestamp="01:28:30",
            speakers=["Andrew Huberman", "Matt Walker"],
            primary_speaker="Matt Walker",
            related_segment_ids=["segment-ep456-2", "segment-ep789-1"],
        )
        assert segment.full == "Edited comprehensive summary..."
        assert segment.speakers == ["Andrew Huberman", "Matt Walker"]
        assert len(segment.related_segment_ids) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::TestSegment -v`
Expected: FAIL with "cannot import name 'Segment'"

**Step 3: Write Segment model**

Add to `src/nuggets/models.py` after the `Nugget` class:

```python
class Segment(BaseModel):
    """A thematic block from an episode.

    Contains raw transcript, optional edited summary, and metadata.
    Nuggets are extracted from segments.
    """

    id: str = Field(..., description="Unique ID: segment-{episode_id}-{index}")
    episode_id: str = Field(..., description="ID of the parent episode")

    # Content levels
    raw_segment: str = Field(..., description="Exact transcript text for this segment")
    full: Optional[str] = Field(
        None, description="Edited, comprehensive summary (if enough material)"
    )

    # Metadata
    topic: str = Field(..., description="Topic category: sleep, productivity, etc.")
    theme_name: str = Field(..., description="Human-readable theme name")
    start_timestamp: Optional[str] = Field(None, description="Start time HH:MM:SS")
    end_timestamp: Optional[str] = Field(None, description="End time HH:MM:SS")

    # Speakers
    speakers: list[str] = Field(default_factory=list, description="All speakers in segment")
    primary_speaker: Optional[str] = Field(None, description="Main speaker for this segment")

    # Semantic search
    embedding: Optional[list[float]] = Field(None, description="Vector embedding for similarity")

    # Connections
    related_segment_ids: list[str] = Field(
        default_factory=list, description="IDs of similar segments from other episodes"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::TestSegment -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/nuggets/models.py tests/test_models.py
git commit -m "feat(models): add Segment model for thematic blocks"
```

---

### Task 1.2: Update Nugget Model with Hierarchy Fields

**Files:**
- Modify: `src/nuggets/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py` in `TestNugget`:

```python
    def test_nugget_hierarchy_fields(self):
        """Nugget supports segment_id and multi-level content."""
        nugget = Nugget(
            content="Legacy field",  # Keep for backwards compat
            type=NuggetType.INSIGHT,
            segment_id="segment-ep123-0",
            headline="Morning sunlight boosts cortisol",
            condensed="Huberman explains that viewing bright light within 30 minutes of waking triggers a cortisol pulse that helps set your circadian rhythm.",
            quote="Get sunlight in your eyes within 30-60 minutes of waking.",
        )
        assert nugget.segment_id == "segment-ep123-0"
        assert nugget.headline == "Morning sunlight boosts cortisol"
        assert nugget.condensed is not None
        assert nugget.quote is not None

    def test_nugget_flexible_levels(self):
        """Not all content levels need to be present."""
        # Quote without full context
        nugget = Nugget(
            content="The obstacle is the way",
            type=NuggetType.QUOTE,
            headline="Stoic wisdom on obstacles",
            quote="The obstacle is the way",
            condensed=None,  # No extra context
        )
        assert nugget.quote == "The obstacle is the way"
        assert nugget.condensed is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::TestNugget::test_nugget_hierarchy_fields -v`
Expected: FAIL with "unexpected keyword argument 'segment_id'"

**Step 3: Update Nugget model**

Modify `Nugget` class in `src/nuggets/models.py`:

```python
class Nugget(BaseModel):
    """A valuable insight extracted from content.

    Part of a Segment. Has multiple content levels for different zoom views.
    """

    # Legacy field (kept for backwards compatibility)
    content: str = Field(..., description="The nugget content - clear and specific")
    type: NuggetType = Field(..., description="Type of nugget")

    # Hierarchy
    segment_id: Optional[str] = Field(None, description="ID of parent segment")

    # Multi-level content (all optional except headline for new nuggets)
    headline: Optional[str] = Field(None, description="One-line summary for scanning")
    condensed: Optional[str] = Field(None, description="Core insight with enough context")
    quote: Optional[str] = Field(None, description="Verbatim quote if applicable")

    # Existing fields
    timestamp: Optional[str] = Field(
        None, description="Timestamp in format HH:MM:SS or MM:SS"
    )
    context: Optional[str] = Field(
        None, description="Brief context about what was being discussed"
    )
    importance: int = Field(
        3, ge=1, le=5, description="Importance rating from 1 (low) to 5 (critical)"
    )
    speaker: Optional[str] = Field(None, description="Who said this")

    # Fields for interactive/exhaustive mode
    theme: Optional[str] = Field(None, description="Which theme this nugget belongs to")
    raw_segment: Optional[str] = Field(
        None, description="Raw transcript segment (for exhaustive detail level)"
    )

    # Knowledge library fields
    topic: Optional[str] = Field(
        None, description="Topic category: sleep, productivity, health, etc."
    )
    wisdom_type: Optional[str] = Field(
        None, description="Type: principle, habit, mental-model, life-lesson, technique, warning"
    )
    stars: Optional[int] = Field(
        None, ge=1, le=3, description="Personal rating 1-3 (None = unrated)"
    )

    # Semantic search
    embedding: Optional[list[float]] = Field(None, description="Vector embedding")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py::TestNugget -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/models.py tests/test_models.py
git commit -m "feat(models): add hierarchy fields to Nugget (segment_id, headline, condensed, quote)"
```

---

### Task 1.3: Add Embeddings Module

**Files:**
- Create: `src/nuggets/embeddings.py`
- Test: `tests/test_embeddings.py`

**Step 1: Write the failing test**

Create `tests/test_embeddings.py`:

```python
"""Tests for embeddings module."""

import pytest
from unittest.mock import patch, MagicMock


class TestEmbeddingGenerator:
    """Tests for EmbeddingGenerator."""

    def test_generator_init(self):
        """Generator initializes with provider."""
        from nuggets.embeddings import EmbeddingGenerator

        gen = EmbeddingGenerator(provider="voyage")
        assert gen.provider == "voyage"

    def test_generator_default_provider(self):
        """Generator defaults to voyage provider."""
        from nuggets.embeddings import EmbeddingGenerator

        gen = EmbeddingGenerator()
        assert gen.provider == "voyage"

    @patch("nuggets.embeddings.voyageai")
    def test_generate_single(self, mock_voyage):
        """Generate embedding for single text."""
        from nuggets.embeddings import EmbeddingGenerator

        mock_client = MagicMock()
        mock_voyage.Client.return_value = mock_client
        mock_client.embed.return_value.embeddings = [[0.1, 0.2, 0.3]]

        gen = EmbeddingGenerator(provider="voyage")
        result = gen.generate("test text")

        assert result == [0.1, 0.2, 0.3]
        mock_client.embed.assert_called_once()

    @patch("nuggets.embeddings.voyageai")
    def test_generate_batch(self, mock_voyage):
        """Generate embeddings for batch of texts."""
        from nuggets.embeddings import EmbeddingGenerator

        mock_client = MagicMock()
        mock_voyage.Client.return_value = mock_client
        mock_client.embed.return_value.embeddings = [[0.1, 0.2], [0.3, 0.4]]

        gen = EmbeddingGenerator(provider="voyage")
        results = gen.generate_batch(["text1", "text2"])

        assert len(results) == 2
        assert results[0] == [0.1, 0.2]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_embeddings.py -v`
Expected: FAIL with "No module named 'nuggets.embeddings'"

**Step 3: Create embeddings module**

Create `src/nuggets/embeddings.py`:

```python
"""Embedding generation for semantic search.

Supports Voyage AI (default) and OpenAI embeddings.
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """Generate embeddings for text using various providers."""

    def __init__(
        self,
        provider: Literal["voyage", "openai"] = "voyage",
        model: str | None = None,
    ):
        """Initialize embedding generator.

        Args:
            provider: Embedding provider (voyage or openai)
            model: Model name (default: voyage-3-lite or text-embedding-3-small)
        """
        self.provider = provider

        if provider == "voyage":
            import voyageai

            self.client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
            self.model = model or "voyage-3-lite"
        elif provider == "openai":
            import openai

            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model or "text-embedding-3-small"
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        return self.generate_batch([text])[0]

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.provider == "voyage":
            result = self.client.embed(texts, model=self.model, input_type="document")
            return result.embeddings
        elif self.provider == "openai":
            result = self.client.embeddings.create(input=texts, model=self.model)
            return [item.embedding for item in result.data]
        else:
            raise ValueError(f"Unknown provider: {self.provider}")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity (-1 to 1)
    """
    import math

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_embeddings.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/embeddings.py tests/test_embeddings.py
git commit -m "feat(embeddings): add EmbeddingGenerator with Voyage AI support"
```

---

### Task 1.4: Add Embeddings Database

**Files:**
- Create: `src/nuggets/embeddings_db.py`
- Test: `tests/test_embeddings_db.py`

**Step 1: Write the failing test**

Create `tests/test_embeddings_db.py`:

```python
"""Tests for embeddings database."""

import tempfile
from pathlib import Path

import pytest


class TestEmbeddingsDB:
    """Tests for EmbeddingsDB."""

    def test_db_init_creates_tables(self):
        """Database creates tables on init."""
        from nuggets.embeddings_db import EmbeddingsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = EmbeddingsDB(db_path)

            # Check tables exist
            cursor = db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            assert "segment_embeddings" in tables
            assert "nugget_embeddings" in tables

    def test_store_and_retrieve_segment(self):
        """Can store and retrieve segment embedding."""
        from nuggets.embeddings_db import EmbeddingsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = EmbeddingsDB(db_path)

            embedding = [0.1, 0.2, 0.3, 0.4]
            db.store_segment_embedding("seg-1", embedding)

            result = db.get_segment_embedding("seg-1")
            assert result is not None
            assert len(result) == 4
            assert abs(result[0] - 0.1) < 0.001

    def test_find_similar_segments(self):
        """Can find similar segments by embedding."""
        from nuggets.embeddings_db import EmbeddingsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = EmbeddingsDB(db_path)

            # Store some embeddings
            db.store_segment_embedding("seg-1", [1.0, 0.0, 0.0])
            db.store_segment_embedding("seg-2", [0.9, 0.1, 0.0])  # Similar to seg-1
            db.store_segment_embedding("seg-3", [0.0, 1.0, 0.0])  # Different

            # Find similar to seg-1's embedding
            similar = db.find_similar_segments([1.0, 0.0, 0.0], top_k=2)

            assert len(similar) == 2
            assert similar[0][0] == "seg-1"  # Most similar (itself)
            assert similar[1][0] == "seg-2"  # Second most similar
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_embeddings_db.py -v`
Expected: FAIL with "No module named 'nuggets.embeddings_db'"

**Step 3: Create embeddings database module**

Create `src/nuggets/embeddings_db.py`:

```python
"""SQLite database for storing and searching embeddings.

Uses sqlite-vec extension for efficient vector similarity search.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class EmbeddingsDB:
    """SQLite database for embeddings storage and search."""

    def __init__(self, db_path: Path | str):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self._init_tables()

    def _init_tables(self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS segment_embeddings (
                segment_id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS nugget_embeddings (
                nugget_id TEXT PRIMARY KEY,
                segment_id TEXT,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_nugget_segment
            ON nugget_embeddings(segment_id);
        """)
        self.conn.commit()

    def store_segment_embedding(self, segment_id: str, embedding: list[float]) -> None:
        """Store embedding for a segment.

        Args:
            segment_id: Segment ID
            embedding: Embedding vector
        """
        embedding_json = json.dumps(embedding)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO segment_embeddings (segment_id, embedding)
            VALUES (?, ?)
            """,
            (segment_id, embedding_json),
        )
        self.conn.commit()

    def store_nugget_embedding(
        self, nugget_id: str, segment_id: str, embedding: list[float]
    ) -> None:
        """Store embedding for a nugget.

        Args:
            nugget_id: Nugget ID
            segment_id: Parent segment ID
            embedding: Embedding vector
        """
        embedding_json = json.dumps(embedding)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO nugget_embeddings (nugget_id, segment_id, embedding)
            VALUES (?, ?, ?)
            """,
            (nugget_id, segment_id, embedding_json),
        )
        self.conn.commit()

    def get_segment_embedding(self, segment_id: str) -> list[float] | None:
        """Get embedding for a segment.

        Args:
            segment_id: Segment ID

        Returns:
            Embedding vector or None if not found
        """
        cursor = self.conn.execute(
            "SELECT embedding FROM segment_embeddings WHERE segment_id = ?",
            (segment_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def get_nugget_embedding(self, nugget_id: str) -> list[float] | None:
        """Get embedding for a nugget.

        Args:
            nugget_id: Nugget ID

        Returns:
            Embedding vector or None if not found
        """
        cursor = self.conn.execute(
            "SELECT embedding FROM nugget_embeddings WHERE nugget_id = ?",
            (nugget_id,),
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def find_similar_segments(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        exclude_ids: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Find segments most similar to query embedding.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            exclude_ids: Segment IDs to exclude

        Returns:
            List of (segment_id, similarity_score) tuples
        """
        from nuggets.embeddings import cosine_similarity

        cursor = self.conn.execute("SELECT segment_id, embedding FROM segment_embeddings")
        results = []

        exclude_set = set(exclude_ids or [])

        for row in cursor:
            segment_id, embedding_json = row
            if segment_id in exclude_set:
                continue

            embedding = json.loads(embedding_json)
            similarity = cosine_similarity(query_embedding, embedding)
            results.append((segment_id, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def find_similar_nuggets(
        self,
        query_embedding: list[float],
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """Find nuggets most similar to query embedding.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return

        Returns:
            List of (nugget_id, similarity_score) tuples
        """
        from nuggets.embeddings import cosine_similarity

        cursor = self.conn.execute("SELECT nugget_id, embedding FROM nugget_embeddings")
        results = []

        for row in cursor:
            nugget_id, embedding_json = row
            embedding = json.loads(embedding_json)
            similarity = cosine_similarity(query_embedding, embedding)
            results.append((nugget_id, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_embeddings_db.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/embeddings_db.py tests/test_embeddings_db.py
git commit -m "feat(embeddings): add EmbeddingsDB for vector storage and search"
```

---

### Task 1.5: Add Dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Step 1: Update dependencies**

Add to `dependencies` list in `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "voyageai>=0.3.0",             # Embeddings
]
```

**Step 2: Install updated dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installs voyageai

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add voyageai for embeddings"
```

---

## Phase 2: nuggets-fetch Skill

### Task 2.1: Create Skill Structure

**Files:**
- Create: `.claude/skills/nuggets-fetch/SKILL.md`
- Create: `.claude/skills/nuggets-fetch/references/youtube-method.md`
- Create: `.claude/skills/nuggets-fetch/references/metadata-parsing.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-fetch/SKILL.md`:

```markdown
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

1. Extract video ID from URL
2. Fetch metadata (title, channel, duration, date)
3. Parse guest name from title if present
4. Fetch transcript with timestamps
5. Save to `data/raw/youtube/{channel}/{date}-{id}.json`

```bash
nuggets youtube "<URL>" --transcript-only
```

### Twitter/X

1. Fetch via Jina Reader API
2. If blocked, use /chrome for manual extraction
3. Parse author and date
4. Save to `data/raw/twitter/{author}/{date}-{id}.json`

```bash
nuggets twitter "<URL>" --transcript-only
```

## Output Format

```json
{
  "id": "video-id",
  "source_type": "youtube",
  "title": "Episode Title",
  "channel": "Channel Name",
  "parsed_host": "Andrew Huberman",
  "parsed_guest": "Andy Galpin",
  "date": "2024-12-31",
  "duration_seconds": 7200,
  "url": "https://...",
  "transcript": [
    {"start": 0.0, "text": "Welcome to..."},
    {"start": 5.2, "text": "Today we..."}
  ]
}
```

## Speaker Parsing

See `references/metadata-parsing.md` for guest extraction patterns.
```

**Step 2: Create metadata-parsing.md reference**

Create `.claude/skills/nuggets-fetch/references/metadata-parsing.md`:

```markdown
# Metadata Parsing

## Guest Extraction from Title

Common patterns:

| Pattern | Example | Extracted Guest |
|---------|---------|-----------------|
| "with {Guest}" | "Sleep Tips with Dr. Matt Walker" | Dr. Matt Walker |
| "{Guest}: Topic" | "Andy Galpin: How to Build Muscle" | Andy Galpin |
| "{Guest} - Topic" | "David Goggins - Mental Toughness" | David Goggins |
| "{Guest} \| Topic" | "Naval Ravikant \| Happiness" | Naval Ravikant |
| "ft. {Guest}" | "Productivity ft. Cal Newport" | Cal Newport |
| "feat. {Guest}" | "Health feat. Peter Attia" | Peter Attia |
| "#{Number} {Guest}" | "#1892 David Goggins" | David Goggins |
| "Ep {Number}: {Guest}" | "Ep 127: Dr. Andy Galpin" | Dr. Andy Galpin |

## Host Detection from Channel

| Channel | Host |
|---------|------|
| Huberman Lab | Andrew Huberman |
| The Joe Rogan Experience | Joe Rogan |
| Modern Wisdom | Chris Williamson |
| Diary of a CEO | Steven Bartlett |
| Lex Fridman Podcast | Lex Fridman |
| The Tim Ferriss Show | Tim Ferriss |
| Jay Shetty Podcast | Jay Shetty |

## Implementation

```python
import re

GUEST_PATTERNS = [
    r"with\s+(.+?)(?:\s*[-:|]|$)",
    r"^(.+?):\s+",
    r"^(.+?)\s+-\s+",
    r"^(.+?)\s+\|\s+",
    r"(?:ft\.|feat\.)\s+(.+?)(?:\s*[-:|]|$)",
    r"^#\d+\s+(.+?)(?:\s*[-:|]|$)",
    r"^[Ee]p\.?\s*\d+[:\s]+(.+?)(?:\s*[-:|]|$)",
]

def parse_guest_from_title(title: str) -> str | None:
    for pattern in GUEST_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Filter out common non-guest matches
            if len(guest) > 2 and not guest.lower().startswith(("how", "what", "why", "the")):
                return guest
    return None
```
```

**Step 3: Commit**

```bash
git add .claude/skills/nuggets-fetch/
git commit -m "feat(skills): add nuggets-fetch skill structure"
```

---

### Task 2.2: Add Speaker Parsing to YouTube Module

**Files:**
- Modify: `src/nuggets/transcribe/youtube.py`
- Test: `tests/test_youtube.py`

**Step 1: Write the failing test**

Add to `tests/test_youtube.py`:

```python
class TestSpeakerParsing:
    """Tests for speaker parsing from metadata."""

    def test_parse_guest_with_pattern(self):
        """Parse guest from 'with Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Sleep Tips with Dr. Matt Walker") == "Dr. Matt Walker"

    def test_parse_guest_colon_pattern(self):
        """Parse guest from 'Guest: Topic' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("Andy Galpin: How to Build Muscle") == "Andy Galpin"

    def test_parse_guest_number_pattern(self):
        """Parse guest from '#Number Guest' pattern."""
        from nuggets.transcribe.youtube import parse_guest_from_title

        assert parse_guest_from_title("#1892 David Goggins") == "David Goggins"

    def test_parse_host_from_channel(self):
        """Get known host from channel name."""
        from nuggets.transcribe.youtube import get_host_from_channel

        assert get_host_from_channel("Huberman Lab") == "Andrew Huberman"
        assert get_host_from_channel("Unknown Channel") is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_youtube.py::TestSpeakerParsing -v`
Expected: FAIL with "cannot import name 'parse_guest_from_title'"

**Step 3: Add speaker parsing functions**

Add to `src/nuggets/transcribe/youtube.py`:

```python
import re

GUEST_PATTERNS = [
    r"with\s+(.+?)(?:\s*[-:|]|$)",
    r"^(.+?):\s+",
    r"^(.+?)\s+-\s+",
    r"^(.+?)\s+\|\s+",
    r"(?:ft\.|feat\.)\s+(.+?)(?:\s*[-:|]|$)",
    r"^#\d+\s+(.+?)(?:\s*[-:|]|$)",
    r"^[Ee]p\.?\s*\d+[:\s]+(.+?)(?:\s*[-:|]|$)",
]

KNOWN_HOSTS = {
    "Huberman Lab": "Andrew Huberman",
    "The Joe Rogan Experience": "Joe Rogan",
    "Modern Wisdom": "Chris Williamson",
    "Diary of a CEO": "Steven Bartlett",
    "Lex Fridman Podcast": "Lex Fridman",
    "The Tim Ferriss Show": "Tim Ferriss",
    "Jay Shetty Podcast": "Jay Shetty",
}


def parse_guest_from_title(title: str) -> str | None:
    """Extract guest name from video title.

    Args:
        title: Video title

    Returns:
        Guest name or None if not found
    """
    for pattern in GUEST_PATTERNS:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            guest = match.group(1).strip()
            # Filter out common non-guest matches
            if len(guest) > 2 and not guest.lower().startswith(
                ("how", "what", "why", "the", "a ", "an ")
            ):
                return guest
    return None


def get_host_from_channel(channel_name: str) -> str | None:
    """Get known host from channel name.

    Args:
        channel_name: YouTube channel name

    Returns:
        Host name or None if not a known podcast channel
    """
    return KNOWN_HOSTS.get(channel_name)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_youtube.py::TestSpeakerParsing -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/transcribe/youtube.py tests/test_youtube.py
git commit -m "feat(youtube): add speaker parsing from title and channel"
```

---

## Phase 3: nuggets-analyze Skill

### Task 3.1: Create Skill Structure

**Files:**
- Create: `.claude/skills/nuggets-analyze/SKILL.md`
- Create: `.claude/skills/nuggets-analyze/references/extraction-prompt.md`
- Create: `.claude/skills/nuggets-analyze/references/speaker-hints.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-analyze/SKILL.md`:

```markdown
---
name: nuggets-analyze
description: Analyze fetched content to extract segments and nuggets. Use after nuggets-fetch or when asked to analyze/extract insights.
---

# Nuggets Analyze

Extract segments and nuggets from raw transcripts.

## Triggers

- "analyze", "analysera"
- "extract nuggets from..."
- After successful fetch
- Raw transcript file path

## Workflow

1. Load raw transcript from `data/raw/`
2. Get speaker hints (host from channel, guest from title)
3. Call Claude to segment and extract
4. Generate embeddings for segments and nuggets
5. Find related segments from existing library
6. Save to `data/analysis/{source}/{channel}/{date}-{id}.json`
7. Update embeddings database

## Modes

### Standard (default)
Automatic extraction with default settings.

```bash
nuggets analyze data/raw/youtube/huberman-lab/2024-12-31-xyz.json
```

### Interactive
Choose themes and detail levels.

```bash
nuggets analyze --interactive data/raw/youtube/...
```

## Extraction Process

See `references/extraction-prompt.md` for the Claude prompt.
See `references/speaker-hints.md` for speaker identification.

## Output Structure

```json
{
  "id": "youtube-2024-12-31-xyz",
  "source_type": "youtube",
  "source_name": "Huberman Lab",
  "title": "...",
  "host": "Andrew Huberman",
  "guest": "Andy Galpin",
  "segments": [
    {
      "id": "segment-youtube-2024-12-31-xyz-0",
      "raw_segment": "...",
      "full": "...",
      "topic": "fitness",
      "theme_name": "Strength Training Principles",
      "start_timestamp": "05:30",
      "end_timestamp": "22:15",
      "speakers": ["Andrew Huberman", "Andy Galpin"],
      "nuggets": [...]
    }
  ]
}
```
```

**Step 2: Create extraction-prompt.md reference**

Create `.claude/skills/nuggets-analyze/references/extraction-prompt.md`:

```markdown
# Extraction Prompt

## System Message

You are an expert at extracting valuable insights from podcast transcripts. Your task is to:

1. Identify thematic segments (8-15 per episode)
2. Extract nuggets from each segment (2-8 per segment)
3. Preserve speaker attribution
4. Include timestamps

## Prompt Template

```
Analyze this podcast transcript and extract structured insights.

## Speakers
- Host: {host}
- Guest: {guest}

## Instructions

1. **Identify Segments**: Find 8-15 thematic blocks. Each segment should cover one main topic/discussion.

2. **For Each Segment**, provide:
   - theme_name: Clear name for this discussion
   - topic: Category (sleep, productivity, health, relationships, etc.)
   - start_timestamp: When it starts (MM:SS or HH:MM:SS)
   - end_timestamp: When it ends
   - raw_segment: Exact transcript text
   - full: Comprehensive summary if the segment has depth (null if brief)
   - speakers: Who speaks in this segment
   - primary_speaker: Main speaker (usually guest explaining something)

3. **For Each Nugget** within a segment:
   - headline: One-line summary (always required)
   - condensed: Core insight with context (if substantial)
   - quote: Verbatim quote (if memorable/quotable)
   - type: insight/quote/action/concept/story
   - wisdom_type: principle/habit/mental-model/life-lesson/technique/warning
   - speaker: Who said this
   - timestamp: Specific moment
   - importance: 1-5

4. **Be Selective**: Not every segment needs all content levels. Include:
   - headline: Always
   - condensed: When there's real substance
   - quote: Only when truly quotable
   - full: Only for deep, valuable discussions

## Output Format

Return valid JSON:
{
  "segments": [
    {
      "theme_name": "...",
      "topic": "...",
      "start_timestamp": "...",
      "end_timestamp": "...",
      "raw_segment": "...",
      "full": "..." or null,
      "speakers": ["...", "..."],
      "primary_speaker": "...",
      "nuggets": [
        {
          "headline": "...",
          "condensed": "..." or null,
          "quote": "..." or null,
          "type": "...",
          "wisdom_type": "...",
          "speaker": "...",
          "timestamp": "...",
          "importance": 4
        }
      ]
    }
  ]
}

## Transcript

{transcript}
```
```

**Step 3: Commit**

```bash
git add .claude/skills/nuggets-analyze/
git commit -m "feat(skills): add nuggets-analyze skill structure"
```

---

### Task 3.2: Create Segment Extractor

**Files:**
- Create: `src/nuggets/analyze/segment_extractor.py`
- Test: `tests/test_segment_extractor.py`

**Step 1: Write the failing test**

Create `tests/test_segment_extractor.py`:

```python
"""Tests for segment extraction."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestSegmentExtractor:
    """Tests for SegmentExtractor."""

    def test_extractor_init(self):
        """Extractor initializes with model."""
        from nuggets.analyze.segment_extractor import SegmentExtractor

        extractor = SegmentExtractor(model="claude-sonnet-4-20250514")
        assert extractor.model == "claude-sonnet-4-20250514"

    def test_build_prompt(self):
        """Build prompt includes transcript and speaker hints."""
        from nuggets.analyze.segment_extractor import SegmentExtractor

        extractor = SegmentExtractor()
        prompt = extractor.build_prompt(
            transcript="Hello this is a test",
            host="Andrew Huberman",
            guest="Matt Walker",
        )

        assert "Andrew Huberman" in prompt
        assert "Matt Walker" in prompt
        assert "Hello this is a test" in prompt

    @patch("nuggets.analyze.segment_extractor.anthropic")
    def test_extract_returns_segments(self, mock_anthropic):
        """Extract returns parsed segments and nuggets."""
        from nuggets.analyze.segment_extractor import SegmentExtractor

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "segments": [
                {
                    "theme_name": "Test Theme",
                    "topic": "productivity",
                    "start_timestamp": "00:00",
                    "end_timestamp": "05:00",
                    "raw_segment": "Test transcript",
                    "full": None,
                    "speakers": ["Host"],
                    "primary_speaker": "Host",
                    "nuggets": [
                        {
                            "headline": "Test insight",
                            "condensed": None,
                            "quote": None,
                            "type": "insight",
                            "wisdom_type": "principle",
                            "speaker": "Host",
                            "timestamp": "01:00",
                            "importance": 3,
                        }
                    ],
                }
            ]
        }))]
        mock_client.messages.create.return_value = mock_response

        extractor = SegmentExtractor()
        result = extractor.extract(
            transcript="Test transcript",
            episode_id="test-ep",
            host="Host",
            guest=None,
        )

        assert len(result.segments) == 1
        assert result.segments[0].theme_name == "Test Theme"
        assert len(result.segments[0].nuggets) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_segment_extractor.py -v`
Expected: FAIL with "No module named 'nuggets.analyze.segment_extractor'"

**Step 3: Create segment extractor**

Create `src/nuggets/analyze/segment_extractor.py`:

```python
"""Segment and nugget extraction using Claude."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from nuggets.models import Nugget, NuggetType, Segment

if TYPE_CHECKING:
    from collections.abc import Callable

load_dotenv()

PROMPT_TEMPLATE = '''Analyze this podcast transcript and extract structured insights.

## Speakers
- Host: {host}
- Guest: {guest}

## Instructions

1. **Identify Segments**: Find 8-15 thematic blocks. Each segment should cover one main topic.

2. **For Each Segment**, provide:
   - theme_name: Clear name for this discussion
   - topic: Category (sleep, productivity, health, relationships, fitness, mindset, business, etc.)
   - start_timestamp: When it starts (MM:SS or HH:MM:SS)
   - end_timestamp: When it ends
   - raw_segment: Exact transcript text for this segment
   - full: Comprehensive summary if the segment has depth (null if brief)
   - speakers: Who speaks in this segment
   - primary_speaker: Main speaker

3. **For Each Nugget** within a segment (2-8 per segment):
   - headline: One-line summary (always required)
   - condensed: Core insight with context (if substantial)
   - quote: Verbatim quote (if memorable)
   - type: insight/quote/action/concept/story
   - wisdom_type: principle/habit/mental-model/life-lesson/technique/warning
   - speaker: Who said this
   - timestamp: Specific moment
   - importance: 1-5

4. **Be Selective**: Not all levels needed for every nugget.

## Output Format

Return valid JSON with "segments" array.

## Transcript

{transcript}
'''


class ExtractionResult(BaseModel):
    """Result from segment extraction."""

    segments: list[Segment] = Field(default_factory=list)
    total_nuggets: int = 0


class SegmentExtractor:
    """Extract segments and nuggets from transcripts using Claude."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize extractor.

        Args:
            model: Claude model to use
        """
        self.model = model

    def build_prompt(
        self,
        transcript: str,
        host: str | None = None,
        guest: str | None = None,
    ) -> str:
        """Build extraction prompt.

        Args:
            transcript: Full transcript text
            host: Host name
            guest: Guest name

        Returns:
            Complete prompt
        """
        return PROMPT_TEMPLATE.format(
            host=host or "Unknown",
            guest=guest or "Unknown/None",
            transcript=transcript,
        )

    def extract(
        self,
        transcript: str,
        episode_id: str,
        host: str | None = None,
        guest: str | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> ExtractionResult:
        """Extract segments and nuggets from transcript.

        Args:
            transcript: Full transcript text
            episode_id: Episode ID for generating segment/nugget IDs
            host: Host name
            guest: Guest name
            progress_callback: Optional progress callback

        Returns:
            ExtractionResult with segments and nuggets
        """
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        if progress_callback:
            progress_callback("Building extraction prompt...")

        prompt = self.build_prompt(transcript, host, guest)

        if progress_callback:
            progress_callback(f"Extracting with Claude ({self.model})...")

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text

        if progress_callback:
            progress_callback("Parsing response...")

        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        # Convert to models
        segments = []
        total_nuggets = 0

        for i, seg_data in enumerate(data.get("segments", [])):
            segment_id = f"segment-{episode_id}-{i}"

            # Parse nuggets for this segment
            nuggets = []
            for j, nug_data in enumerate(seg_data.get("nuggets", [])):
                nugget_id = f"nugget-{segment_id}-{j}"

                try:
                    nugget_type = NuggetType(nug_data.get("type", "insight"))
                except ValueError:
                    nugget_type = NuggetType.INSIGHT

                nugget = Nugget(
                    content=nug_data.get("headline", ""),  # Use headline as content
                    type=nugget_type,
                    segment_id=segment_id,
                    headline=nug_data.get("headline"),
                    condensed=nug_data.get("condensed"),
                    quote=nug_data.get("quote"),
                    speaker=nug_data.get("speaker"),
                    timestamp=nug_data.get("timestamp"),
                    importance=nug_data.get("importance", 3),
                    wisdom_type=nug_data.get("wisdom_type"),
                    topic=seg_data.get("topic"),
                )
                nuggets.append(nugget)
                total_nuggets += 1

            segment = Segment(
                id=segment_id,
                episode_id=episode_id,
                raw_segment=seg_data.get("raw_segment", ""),
                full=seg_data.get("full"),
                topic=seg_data.get("topic", "general"),
                theme_name=seg_data.get("theme_name", f"Segment {i + 1}"),
                start_timestamp=seg_data.get("start_timestamp"),
                end_timestamp=seg_data.get("end_timestamp"),
                speakers=seg_data.get("speakers", []),
                primary_speaker=seg_data.get("primary_speaker"),
            )
            # Store nuggets separately - they reference segment by ID
            segment._nuggets = nuggets  # Temporary storage
            segments.append(segment)

        result = ExtractionResult(segments=segments, total_nuggets=total_nuggets)

        # Attach nuggets to result
        result._all_nuggets = []
        for seg in segments:
            if hasattr(seg, "_nuggets"):
                result._all_nuggets.extend(seg._nuggets)

        return result
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_segment_extractor.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/analyze/segment_extractor.py tests/test_segment_extractor.py
git commit -m "feat(analyze): add SegmentExtractor for hierarchical extraction"
```

---

## Phase 4: nuggets-explore Skill

### Task 4.1: Create Skill Structure

**Files:**
- Create: `.claude/skills/nuggets-explore/SKILL.md`
- Create: `.claude/skills/nuggets-explore/references/query-patterns.md`

**Step 1: Create SKILL.md**

Create `.claude/skills/nuggets-explore/SKILL.md`:

```markdown
---
name: nuggets-explore
description: Search, explore, and connect insights in the knowledge library. Use for queries about what you know, finding related content, or comparing sources.
---

# Nuggets Explore

Navigate and discover insights in your knowledge library.

## Triggers

- "search", "sök", "find", "hitta"
- "what do I know about...", "vad vet jag om..."
- "explore", "utforska"
- "connect", "compare", "jämför"
- "related to...", "similar to..."
- "who said...", "vem sa..."

## Commands

### Search (Nugget-level)
Find specific nuggets matching a query.

```bash
nuggets search "morning sunlight"
nuggets search "dopamine" --speaker "Anna Lembke"
nuggets search --topic sleep --stars 2
```

### Explore (Segment-level, semantic)
Find thematically related segments using embeddings.

```bash
nuggets explore "sleep optimization"
nuggets explore "building discipline"
```

### Connect
Compare what different sources say about a topic.

```bash
nuggets connect "Huberman" "Goggins" --topic discipline
nuggets connect "sleep" "productivity"
```

### Deep Dive
Expand from headline → condensed → full → raw.

```bash
nuggets deep-dive nugget-xyz-123
nuggets deep-dive segment-abc-456
```

### Related
Find segments connected to a given segment.

```bash
nuggets related segment-abc-456
```

## Output Formatting

See `references/query-patterns.md` for display patterns.
```

**Step 2: Create query-patterns.md reference**

Create `.claude/skills/nuggets-explore/references/query-patterns.md`:

```markdown
# Query Patterns

## Search Results (Nugget-level)

```
🔍 Found 5 nuggets for "morning sunlight"

⭐⭐ [Huberman Lab] 00:15:32
"Morning sunlight within 30 min boosts cortisol"
→ Huberman explains that viewing bright light early triggers...
Speaker: Andrew Huberman
📎 2 related segments

⭐ [Modern Wisdom] 01:05:20
"Sunlight exposure sets circadian rhythm"
→ Chris discusses the importance of natural light...
Speaker: Chris Williamson

[Press number to deep-dive, 'r' for related, 'q' to quit]
```

## Explore Results (Segment-level)

```
🌐 Exploring "sleep optimization" (semantic search)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEGMENT: Sleep Physiology [Huberman Lab #127]
22:15 - 38:40 | Matt Walker, Andrew Huberman
Topic: sleep | Similarity: 0.94

Nuggets:
  💡 Adenosine builds up during wakefulness
  💡 REM sleep critical for emotional regulation
  💬 "Sleep is the foundation of all health"

Related:
  → Sleep and Recovery [Chris Williamson #412] (0.89)
  → Why We Sleep [Joe Rogan #1109] (0.85)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Expand full segment
[2] Show related
[3] Next result
```

## Connect Results

```
🔗 Connecting: Huberman ↔ Goggins on "discipline"

HUBERMAN says:
  💡 "Dopamine is released in anticipation, not reward"
  💡 Forward ambiguity creates motivation
  → Focus on the process, not the outcome

GOGGINS says:
  💡 "Embrace the suck - discomfort is growth"
  💡 The 40% rule: you're capable of much more
  → Pain is the path to mental toughness

COMMON THEMES:
  • Both emphasize process over outcome
  • Discomfort as necessary for growth
  • Mental framing determines experience
```

## Deep Dive Expansion

```
📖 Deep Dive: nugget-huberman-sleep-001

HEADLINE:
Morning sunlight within 30 minutes boosts cortisol

CONDENSED:
Huberman explains that viewing bright light (ideally sunlight) within
30-60 minutes of waking triggers a cortisol pulse that helps set your
circadian rhythm. This early cortisol is healthy and different from
stress-induced cortisol later in the day.

FULL:
[Full segment summary with complete context...]

RAW TRANSCRIPT:
[Exact transcript text with timestamps...]

🔗 youtube.com/watch?v=xyz&t=932
```
```

**Step 3: Commit**

```bash
git add .claude/skills/nuggets-explore/
git commit -m "feat(skills): add nuggets-explore skill structure"
```

---

### Task 4.2: Add Explore Command to CLI

**Files:**
- Modify: `src/nuggets/cli.py`
- Test: `tests/test_cli_explore.py`

**Step 1: Write the failing test**

Create `tests/test_cli_explore.py`:

```python
"""Tests for explore CLI command."""

from click.testing import CliRunner
import pytest


class TestExploreCommand:
    """Tests for nuggets explore command."""

    def test_explore_command_exists(self):
        """Explore command is registered."""
        from nuggets.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["explore", "--help"])
        assert result.exit_code == 0
        assert "semantic" in result.output.lower() or "explore" in result.output.lower()

    def test_explore_requires_query(self):
        """Explore requires a query argument."""
        from nuggets.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["explore"])
        # Should fail or show help without query
        assert result.exit_code != 0 or "query" in result.output.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_explore.py -v`
Expected: FAIL with "No such command 'explore'"

**Step 3: Add explore command**

Add to `src/nuggets/cli.py`:

```python
@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results")
def explore(query: str, top_k: int) -> None:
    """Semantic search across segments.

    Uses embeddings to find thematically related content.
    """
    from pathlib import Path
    from rich.console import Console
    from rich.panel import Panel

    from nuggets.embeddings import EmbeddingGenerator
    from nuggets.embeddings_db import EmbeddingsDB

    console = Console()

    db_path = Path("data/library/embeddings.db")
    if not db_path.exists():
        console.print("[yellow]No embeddings database found. Run 'nuggets index rebuild' first.[/yellow]")
        return

    console.print(f"[blue]🌐 Exploring:[/blue] {query}")

    try:
        generator = EmbeddingGenerator()
        query_embedding = generator.generate(query)

        db = EmbeddingsDB(db_path)
        similar = db.find_similar_segments(query_embedding, top_k=top_k)

        if not similar:
            console.print("[yellow]No matching segments found.[/yellow]")
            return

        for segment_id, similarity in similar:
            console.print(Panel(
                f"[bold]{segment_id}[/bold]\nSimilarity: {similarity:.2f}",
                title="Segment",
            ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli_explore.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/nuggets/cli.py tests/test_cli_explore.py
git commit -m "feat(cli): add explore command for semantic search"
```

---

## Phase 5: Update nuggets-curate Skill

### Task 5.1: Update Skill for New Structure

**Files:**
- Modify: `.claude/skills/nuggets-curate.md` → `.claude/skills/nuggets-curate/SKILL.md`

**Step 1: Restructure skill**

Create `.claude/skills/nuggets-curate/SKILL.md`:

```markdown
---
name: nuggets-curate
description: Rate and curate nuggets in your knowledge library. Use for star ratings, reviewing insights, and creating best-of collections.
---

# Nuggets Curate

Personal curation of your knowledge library.

## Triggers

- "rate", "star", "betygsätt"
- "review nuggets", "granska"
- "favorites", "best of"
- "curate"

## Star Rating System

| Stars | Meaning | Use For |
|-------|---------|---------|
| ⭐ | Worth remembering | Good insights to review |
| ⭐⭐ | Important insight | Key learnings |
| ⭐⭐⭐ | Goated | Core philosophy, life-changing |

## Commands

### Rate Single Nugget
```bash
nuggets star <nugget-id> <1-3>
nuggets star nugget-huberman-sleep-001 3
```

### Interactive Rating
```bash
nuggets star --interactive
nuggets star --interactive --unrated  # Only unrated
nuggets star --interactive --topic sleep
```

### View Favorites
```bash
nuggets list --stars 3        # All goated
nuggets list --stars 2        # Important+
```

### Export Best-Of
```bash
nuggets export --best-of                    # All starred
nuggets export --stars 3                    # Only goated
nuggets export --stars 2 --topic sleep      # Important sleep insights
nuggets export --stars 2 --group-by speaker # Grouped by speaker
```

## Interactive Mode

```
⭐ Rating Mode - 15 unrated nuggets

[1/15] From: Huberman Lab - Sleep Optimization
       Topic: sleep | Type: technique

       "Morning sunlight within 30 minutes of waking sets
        your circadian rhythm and improves sleep quality."

       Speaker: Andrew Huberman | 00:15:32

Rate (1-3, s=skip, q=quit): 2

✓ Rated ⭐⭐ - Important insight

[2/15] ...
```

## Export with Timestamps

Export includes clickable YouTube links:

```markdown
## ⭐⭐⭐ Goated Insights

### Sleep
- [00:15:32] Morning sunlight sets circadian rhythm
  [Watch](https://youtube.com/watch?v=xyz&t=932)
```
```

**Step 2: Remove old file, commit**

```bash
rm .claude/skills/nuggets-curate.md
mkdir -p .claude/skills/nuggets-curate
# Create SKILL.md as above
git add .claude/skills/nuggets-curate/
git commit -m "feat(skills): restructure nuggets-curate as proper skill"
```

---

## Final: Integration Test

### Task 6.1: End-to-End Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for the full workflow."""

import json
import tempfile
from pathlib import Path

import pytest


class TestFullWorkflow:
    """Test complete fetch → analyze → explore workflow."""

    @pytest.mark.integration
    def test_segment_nugget_hierarchy(self):
        """Segments contain nuggets with proper IDs."""
        from nuggets.models import Segment, Nugget, NuggetType

        segment = Segment(
            id="segment-ep1-0",
            episode_id="ep1",
            raw_segment="Test transcript...",
            topic="productivity",
            theme_name="Morning Routines",
        )

        nugget = Nugget(
            content="Test insight",
            type=NuggetType.INSIGHT,
            segment_id=segment.id,
            headline="Test headline",
        )

        assert nugget.segment_id == segment.id
        assert segment.id.startswith("segment-")

    @pytest.mark.integration
    def test_embeddings_roundtrip(self):
        """Embeddings can be stored and retrieved."""
        from nuggets.embeddings_db import EmbeddingsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = EmbeddingsDB(Path(tmpdir) / "test.db")

            db.store_segment_embedding("seg-1", [0.1, 0.2, 0.3])
            result = db.get_segment_embedding("seg-1")

            assert result is not None
            assert len(result) == 3

    @pytest.mark.integration
    def test_similarity_search(self):
        """Similar segments can be found."""
        from nuggets.embeddings_db import EmbeddingsDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = EmbeddingsDB(Path(tmpdir) / "test.db")

            db.store_segment_embedding("seg-1", [1.0, 0.0, 0.0])
            db.store_segment_embedding("seg-2", [0.9, 0.1, 0.0])
            db.store_segment_embedding("seg-3", [0.0, 0.0, 1.0])

            similar = db.find_similar_segments([1.0, 0.0, 0.0], top_k=2)

            assert similar[0][0] == "seg-1"  # Most similar
            assert similar[1][0] == "seg-2"  # Second
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v -m integration`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full workflow"
```

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|------------------|
| 1 | 1.1-1.5 | Segment model, updated Nugget, EmbeddingsDB |
| 2 | 2.1-2.2 | nuggets-fetch skill, speaker parsing |
| 3 | 3.1-3.2 | nuggets-analyze skill, SegmentExtractor |
| 4 | 4.1-4.2 | nuggets-explore skill, explore CLI command |
| 5 | 5.1 | Updated nuggets-curate skill |
| 6 | 6.1 | Integration tests |

**Total: 12 tasks, ~2-3 hours implementation time**
