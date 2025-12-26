"""Data models for Podcast Nuggets.

Pydantic models for representing transcripts, nuggets, and episodes.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DetailLevel(int, Enum):
    """Detail level for theme extraction (1-5 scale)."""

    MINIMAL = 1      # Brief mention only: "X app recommended for Y"
    LIGHT = 2        # Key points only: 1-2 short nuggets
    STANDARD = 3     # Normal analysis: 2-4 nuggets with context
    DETAILED = 4     # Thorough: 4-6 nuggets, rich context
    EXHAUSTIVE = 5   # Full coverage: all details + raw_segment with transcript


class NuggetType(str, Enum):
    """Types of nuggets that can be extracted."""

    INSIGHT = "insight"  # Key learning, surprising fact, important principle
    QUOTE = "quote"  # Memorable quote worth saving
    ACTION = "action"  # Specific actionable advice
    CONCEPT = "concept"  # Important definition or mental model
    STORY = "story"  # Illustrative anecdote or example


class SourceType(str, Enum):
    """Types of content sources."""

    PODCAST = "podcast"
    YOUTUBE = "youtube"
    AUDIO = "audio"


class Theme(BaseModel):
    """A thematic segment identified in a transcript.

    Used for interactive analysis mode where users can configure
    extraction depth per theme.
    """

    name: str = Field(..., description="Theme name, e.g., 'Meditation', 'Produktivitet'")
    description: str = Field("", description="Brief description of what's covered")
    start_timestamp: Optional[str] = Field(None, description="Start time [MM:SS] or [HH:MM:SS]")
    end_timestamp: Optional[str] = Field(None, description="End time")
    keywords: list[str] = Field(default_factory=list, description="Key terms in this theme")
    estimated_duration_minutes: Optional[int] = Field(None, description="Approximate duration")


class ThemeConfig(BaseModel):
    """User configuration for a theme's analysis depth."""

    theme_name: str = Field(..., description="Name of the theme")
    enabled: bool = Field(True, description="Whether to include this theme")
    detail_level: DetailLevel = Field(
        DetailLevel.STANDARD, description="1-5 detail level for extraction"
    )


class AnalysisConfig(BaseModel):
    """Configuration for how an analysis was/should be performed.

    Stores theme configurations for reproducibility and config reuse.
    """

    name: Optional[str] = Field(None, description="Config name for saving/loading")
    description: Optional[str] = Field(None, description="Description of this config")
    mode: Literal["standard", "interactive"] = Field("standard")
    theme_configs: list[ThemeConfig] = Field(default_factory=list)
    default_detail_level: DetailLevel = Field(DetailLevel.STANDARD)
    created_at: datetime = Field(default_factory=datetime.now)


class Nugget(BaseModel):
    """A valuable insight extracted from content.

    A nugget is a discrete piece of information worth remembering:
    an insight, quote, action item, concept, or story.
    """

    content: str = Field(..., description="The nugget content - clear and specific")
    type: NuggetType = Field(..., description="Type of nugget")
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


class Episode(BaseModel):
    """An analyzed episode with extracted nuggets.

    Represents a complete analysis of a podcast episode, YouTube video,
    or audio file, including all extracted nuggets.
    """

    # Identification
    id: str = Field(..., description="Unique ID: source-YYYY-MM-DD-hash")
    source_type: SourceType = Field(..., description="Type of source")
    source_name: str = Field(..., description="Name of podcast/channel")
    title: str = Field(..., description="Episode/video title")

    # Metadata
    date: Optional[datetime] = Field(None, description="Publication date")
    url: Optional[str] = Field(None, description="URL if available")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    guests: list[str] = Field(default_factory=list, description="Guest names")

    # Analysis results
    summary: str = Field(..., description="2-3 sentence summary")
    nuggets: list[Nugget] = Field(default_factory=list, description="Extracted nuggets")
    tags: list[str] = Field(default_factory=list, description="Topic tags")

    # Personal additions
    personal_notes: str = Field("", description="Your own notes")
    rating: Optional[int] = Field(
        None, ge=1, le=5, description="Your rating of the episode"
    )

    # File references
    transcript_path: Optional[str] = Field(None, description="Path to transcript file")

    # Analysis configuration (for reproducibility)
    analysis_config: Optional[AnalysisConfig] = Field(
        None, description="Configuration used for this analysis"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this was created"
    )
    analyzed_at: Optional[datetime] = Field(
        None, description="When analysis was performed"
    )


class TranscriptMetadata(BaseModel):
    """Metadata for a transcript file.

    Used when loading/saving transcripts to track source information.
    """

    source_type: SourceType
    source_name: str
    title: str
    date: Optional[datetime] = None
    url: Optional[str] = None
    duration_minutes: Optional[int] = None
    has_timestamps: bool = False


class AnalysisResult(BaseModel):
    """Result from Claude analysis.

    Matches the expected output format from the extraction prompt.
    """

    summary: str
    guests: list[str] = Field(default_factory=list)
    suggested_tags: list[str] = Field(default_factory=list)
    nuggets: list[Nugget] = Field(default_factory=list)

    # Fields for interactive mode
    themes_identified: list[Theme] = Field(
        default_factory=list, description="Themes identified in the transcript"
    )
    analysis_config: Optional[AnalysisConfig] = Field(
        None, description="Configuration used for this analysis"
    )
