"""
Biography generation module.

Provides AI-powered and template-based biography generation from RootsMagic databases.
"""

from .citations import CitationProcessor
from .generator import BiographyGenerator
from .models import (
    Biography,
    BiographyLength,
    CitationInfo,
    CitationStyle,
    CitationTracker,
    EventContext,
    LLMMetadata,
    PersonContext,
)
from .rendering import BiographyRenderer
from .templates import BiographyTemplates

# Public API - classes that external code should use
__all__ = [
    # Main generator
    "BiographyGenerator",
    # Core data models
    "Biography",
    "BiographyLength",
    "CitationStyle",
    "PersonContext",
    "EventContext",
    "LLMMetadata",
    "CitationInfo",
    "CitationTracker",
    # Helper classes (for advanced usage)
    "BiographyRenderer",
    "CitationProcessor",
    "BiographyTemplates",
]
