"""
Pattern implementations package.

Contains all 12 universal Dhātu-FS patterns identified in Phase 6 analysis.
"""

from .base import (
    Pattern,
    MatchResult,
    PatternMatchError,
    ConfigValidationError,
    CompositePattern,
    PATTERN_REGISTRY,
    register_pattern
)

# Import pattern implementations to populate registry
from .magic_number import MagicNumberPattern
from .key_value import KeyValuePattern
from .header_body import HeaderBodyPattern

__all__ = [
    'Pattern',
    'MatchResult',
    'PatternMatchError',
    'ConfigValidationError',
    'CompositePattern',
    'PATTERN_REGISTRY',
    'register_pattern',
    'MagicNumberPattern',
    'KeyValuePattern',
    'HeaderBodyPattern',
]
