"""
MAGIC_NUMBER Pattern - Format identification via signature bytes

Usage: 59.7% of formats (46/77)

Most common pattern for format identification. Matches fixed byte
sequence at specific offset.

Examples:
- PNG: \\x89PNG\\r\\n\\x1a\\n at offset 0
- ZIP: PK\\x03\\x04 at offset 0
- PDF: %PDF- at offset 0
- JPEG: \\xFF\\xD8\\xFF at offset 0
"""

import struct
from typing import Any, Dict
from .base import Pattern, MatchResult, ConfigValidationError, register_pattern


@register_pattern
class MagicNumberPattern(Pattern):
    """
    Match fixed byte signature at given offset.
    
    Config:
        signature: bytes | str - Signature to match (hex string or bytes)
        offset: int - Byte offset to check (default: 0)
        length: int - Optional length (inferred from signature if not given)
        mask: bytes | str - Optional bitmask for partial matching
        required: bool - Whether match is required (default: True)
    
    Returns:
        data:
            matched: bool
            signature: bytes
            offset: int
    """
    
    def validate_config(self) -> None:
        """Validate configuration"""
        if 'signature' not in self.config:
            raise ConfigValidationError(
                "MAGIC_NUMBER pattern requires 'signature' config"
            )
        
        # Convert signature to bytes if string
        sig = self.config['signature']
        if isinstance(sig, str):
            # Try to decode as hex string or use raw bytes
            try:
                self.signature = bytes.fromhex(sig.replace('\\x', ''))
            except ValueError:
                self.signature = sig.encode('latin-1')
        else:
            self.signature = sig
        
        self.offset = self.config.get('offset', 0)
        self.length = self.config.get('length', len(self.signature))
        self.required = self.config.get('required', True)
        
        # Optional mask for partial matching
        mask = self.config.get('mask')
        if mask:
            if isinstance(mask, str):
                try:
                    self.mask = bytes.fromhex(mask.replace('\\x', ''))
                except ValueError:
                    self.mask = mask.encode('latin-1')
            else:
                self.mask = mask
        else:
            self.mask = None
        
        # Validate lengths match
        if self.mask and len(self.mask) != len(self.signature):
            raise ConfigValidationError(
                f"Mask length ({len(self.mask)}) must match "
                f"signature length ({len(self.signature)})"
            )
    
    def match(self, data: bytes, offset: int = 0) -> MatchResult:
        """
        Match magic number at offset.
        
        Args:
            data: Binary data
            offset: Starting offset (added to config offset)
            
        Returns:
            MatchResult with success and matched signature
        """
        actual_offset = self.offset + offset
        end_offset = actual_offset + self.length
        
        # Check bounds
        if end_offset > len(data):
            if self.required:
                return MatchResult(
                    success=False,
                    data={'error': 'Insufficient data for magic number'},
                    bytes_consumed=0
                )
            else:
                return MatchResult(
                    success=True,
                    data={'matched': False, 'reason': 'insufficient_data'},
                    bytes_consumed=0
                )
        
        # Extract bytes at offset
        actual_bytes = data[actual_offset:end_offset]
        
        # Apply mask if present
        if self.mask:
            actual_bytes = bytes(a & m for a, m in zip(actual_bytes, self.mask))
            expected_bytes = bytes(s & m for s, m in zip(self.signature, self.mask))
        else:
            expected_bytes = self.signature
        
        # Compare
        matched = actual_bytes == expected_bytes
        
        if not matched and self.required:
            return MatchResult(
                success=False,
                data={
                    'error': 'Magic number mismatch',
                    'expected': expected_bytes.hex(),
                    'actual': actual_bytes.hex(),
                    'offset': actual_offset
                },
                bytes_consumed=0
            )
        
        return MatchResult(
            success=True,
            data={
                'matched': matched,
                'signature': self.signature.hex(),
                'offset': actual_offset,
                'length': self.length
            },
            bytes_consumed=self.length,
            metadata={
                'pattern': 'MAGIC_NUMBER',
                'signature_hex': self.signature.hex()
            }
        )
    
    def get_required_config(self) -> list:
        """Required config keys"""
        return ['signature']
    
    def get_optional_config(self) -> Dict[str, Any]:
        """Optional config keys with defaults"""
        return {
            'offset': 0,
            'length': None,  # Inferred from signature
            'mask': None,
            'required': True
        }
