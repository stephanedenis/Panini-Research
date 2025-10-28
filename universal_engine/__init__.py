"""
PaniniFS v4.0 - Universal Pattern Engine
Based on empirical Dhātu-FS pattern analysis (Phase 6)

The universal engine that replaces 70+ specialized extractors with
declarative grammar files, achieving 74% code reduction.
"""

__version__ = "4.0.0"
__author__ = "PaniniFS Research"

# Import only implemented components
try:
    from .content_addressed_store import ContentAddressedStore
    __all__ = ['ContentAddressedStore']
except ImportError:
    __all__ = []

try:
    from .patterns.base import Pattern, register_pattern, PATTERN_REGISTRY
    __all__.extend(['Pattern', 'register_pattern', 'PATTERN_REGISTRY'])
except ImportError:
    pass
