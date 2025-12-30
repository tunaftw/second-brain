"""Category constants for nugget classification.

Topics describe WHAT the nugget is about.
Wisdom types describe WHAT KIND of insight it is.
"""

TOPICS: list[str] = [
    "sleep",
    "productivity",
    "health",
    "relationships",
    "business",
    "creativity",
    "learning",
    "fitness",
    "nutrition",
    "mindset",
    "technology",
    "parenting",
    "finance",
    "communication",
]

WISDOM_TYPES: list[str] = [
    "principle",      # Fundamental truth or rule
    "habit",          # Concrete behavior to implement
    "mental-model",   # Way of thinking about something
    "life-lesson",    # Broad life wisdom
    "technique",      # Specific method or technique
    "warning",        # Something to avoid
]


def is_valid_topic(topic: str) -> bool:
    """Check if topic is in the predefined list."""
    return topic.lower() in TOPICS


def is_valid_wisdom_type(wisdom_type: str) -> bool:
    """Check if wisdom_type is in the predefined list."""
    return wisdom_type.lower() in WISDOM_TYPES
