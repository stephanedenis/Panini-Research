"""
Pattern Base Classes - Abstract interfaces for all Dhātu-FS patterns

Pāṇinian principle: Each pattern is a primitive operation (dhātu)
that can be composed to parse any binary format.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class MatchResult:
    """Result of a pattern match operation"""
    success: bool
    data: Dict[str, Any]
    bytes_consumed: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Pattern(ABC):
    """
    Abstract base class for all universal patterns (Dhātu-FS).
    
    Each pattern implements a fundamental parsing operation that appears
    across multiple file formats. Patterns are configured via grammar files
    and composed by the universal engine.
    
    Design principles:
    - Stateless: Each match() call is independent
    - Composable: Patterns can nest other patterns
    - Declarative: Behavior defined by config dict, not code
    - Reusable: Same pattern used across diverse formats
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pattern with configuration from grammar file.
        
        Args:
            config: Pattern-specific configuration dict from YAML grammar
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def match(self, data: bytes, offset: int = 0) -> MatchResult:
        """
        Attempt to match pattern at given offset in data.
        
        Args:
            data: Binary data to parse
            offset: Starting byte offset
            
        Returns:
            MatchResult with success flag, extracted data, and bytes consumed
            
        Raises:
            PatternMatchError: If match fails fatally (vs graceful failure)
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate pattern configuration.
        
        Raises:
            ConfigValidationError: If config is invalid
        """
        pass
    
    def get_required_config(self) -> List[str]:
        """
        Get list of required configuration keys.
        
        Returns:
            List of required config key names
        """
        return []
    
    def get_optional_config(self) -> Dict[str, Any]:
        """
        Get dict of optional configuration keys with defaults.
        
        Returns:
            Dict mapping config key to default value
        """
        return {}
    
    @property
    def pattern_name(self) -> str:
        """
        Get pattern name for logging/debugging.
        
        Returns:
            Pattern class name
        """
        return self.__class__.__name__.replace('Pattern', '').upper()


class PatternMatchError(Exception):
    """Raised when pattern matching fails fatally"""
    pass


class ConfigValidationError(Exception):
    """Raised when pattern configuration is invalid"""
    pass


class CompositePattern(Pattern):
    """
    Base class for patterns that compose other patterns.
    
    Used for patterns like CHUNK_STRUCTURE that contain nested patterns
    for chunk contents.
    """
    
    def __init__(self, config: Dict[str, Any], pattern_registry: Dict[str, type]):
        """
        Initialize composite pattern.
        
        Args:
            config: Pattern configuration
            pattern_registry: Registry of available pattern classes
        """
        self.pattern_registry = pattern_registry
        self.sub_patterns: Dict[str, Pattern] = {}
        super().__init__(config)
    
    def create_sub_pattern(self, pattern_name: str, config: Dict[str, Any]) -> Pattern:
        """
        Create instance of sub-pattern.
        
        Args:
            pattern_name: Name of pattern class
            config: Configuration for sub-pattern
            
        Returns:
            Instantiated pattern
            
        Raises:
            ConfigValidationError: If pattern name not found
        """
        if pattern_name not in self.pattern_registry:
            raise ConfigValidationError(
                f"Unknown pattern type: {pattern_name}"
            )
        
        pattern_class = self.pattern_registry[pattern_name]
        return pattern_class(config)


# Pattern registry - populated by importing pattern modules
PATTERN_REGISTRY: Dict[str, type] = {}


def register_pattern(pattern_class: type) -> type:
    """
    Decorator to register pattern class in global registry.
    
    Usage:
        @register_pattern
        class MagicNumberPattern(Pattern):
            ...
    
    Args:
        pattern_class: Pattern class to register
        
    Returns:
        Same class (decorator)
    """
    pattern_name = pattern_class.__name__.replace('Pattern', '').upper()
    PATTERN_REGISTRY[pattern_name] = pattern_class
    return pattern_class
