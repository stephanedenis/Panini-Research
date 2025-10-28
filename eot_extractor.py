#!/usr/bin/env python3
"""
PaniniFS v3.56 - EOT (Embedded OpenType) Format Extractor
Microsoft proprietary font format for web fonts

Extracts:
- EOT header structure (EOTPrefix)
- Embedded font data (TrueType/OpenType)
- Font metadata (family name, version, style)
- Compression detection
- Font metrics (glyphs, tables)
- Unicode ranges
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, Optional

# EOT magic numbers
EOT_MAGIC = b'\x00\x01\x00\x00'  # Or other variations
EOT_VERSION_1 = 0x00010000
EOT_VERSION_2 = 0x00020001
EOT_VERSION_3 = 0x00020002

# Compression types
EOT_COMPRESSION_NONE = 0x00000000
EOT_COMPRESSION_DEFAULT = 0x00000001
EOT_COMPRESSION_SUBSET = 0x00000002


def read_uint32_le(data: bytes, offset: int) -> int:
    """Read 32-bit unsigned integer (little-endian)"""
    return struct.unpack('<I', data[offset:offset+4])[0]


def read_uint16_le(data: bytes, offset: int) -> int:
    """Read 16-bit unsigned integer (little-endian)"""
    return struct.unpack('<H', data[offset:offset+2])[0]


def read_uint8(data: bytes, offset: int) -> int:
    """Read 8-bit unsigned integer"""
    return data[offset]


def read_string_utf16_le(data: bytes, offset: int, max_len: int = 100) -> str:
    """Read null-terminated UTF-16LE string"""
    result = []
    i = 0
    while i < max_len * 2:
        char_code = read_uint16_le(data, offset + i)
        if char_code == 0:
            break
        result.append(chr(char_code))
        i += 2
    return ''.join(result)


def extract_eot_header(data: bytes) -> Dict[str, Any]:
    """Extract EOT header (EOTPrefix structure)"""
    
    if len(data) < 82:
        return {'error': 'File too small for EOT header'}
    
    header = {}
    
    # EOTPrefix structure (minimum 82 bytes)
    try:
        header['eot_size'] = read_uint32_le(data, 0)  # Total file size
        header['font_data_size'] = read_uint32_le(data, 4)  # Embedded font size
        header['version'] = read_uint32_le(data, 8)  # Format version
        header['flags'] = read_uint32_le(data, 12)  # Processing flags
        
        # Font PANOSE classification (10 bytes at offset 16)
        header['panose'] = list(data[16:26])
        
        header['charset'] = read_uint8(data, 26)
        header['italic'] = bool(read_uint8(data, 27))
        header['weight'] = read_uint32_le(data, 28)  # Font weight (100-900)
        header['fs_type'] = read_uint16_le(data, 32)  # Embedding permissions
        header['magic_number'] = read_uint16_le(data, 34)  # Magic 0x504C
        
        # Unicode ranges (4 DWORDs)
        header['unicode_range1'] = read_uint32_le(data, 36)
        header['unicode_range2'] = read_uint32_le(data, 40)
        header['unicode_range3'] = read_uint32_le(data, 44)
        header['unicode_range4'] = read_uint32_le(data, 48)
        
        # Code page ranges
        header['codepage_range1'] = read_uint32_le(data, 52)
        header['codepage_range2'] = read_uint32_le(data, 56)
        
        header['checksum_adjustment'] = read_uint32_le(data, 60)
        
        # Reserved fields
        header['reserved'] = [
            read_uint32_le(data, 64),
            read_uint32_le(data, 68),
            read_uint32_le(data, 72),
            read_uint32_le(data, 76)
        ]
        
        header['padding'] = read_uint16_le(data, 80)
        
        # Detect compression
        if header['flags'] & 0x00000001:
            header['compression'] = 'default'
        elif header['flags'] & 0x00000002:
            header['compression'] = 'subset'
        else:
            header['compression'] = 'none'
        
        # Version string
        version_map = {
            EOT_VERSION_1: 'EOT v1.0',
            EOT_VERSION_2: 'EOT v2.0',
            EOT_VERSION_3: 'EOT v2.0 (subset)'
        }
        header['version_string'] = version_map.get(header['version'], f'Unknown (0x{header["version"]:08X})')
        
    except Exception as e:
        return {'error': f'Failed to parse header: {e}'}
    
    return header


def extract_font_names(data: bytes, offset: int = 82) -> Dict[str, str]:
    """Extract font family name and other strings from EOT"""
    
    names = {}
    
    try:
        # After EOTPrefix, there are length-prefixed UTF-16LE strings
        # Family name length (2 bytes)
        if offset + 2 > len(data):
            return names
        
        family_name_size = read_uint16_le(data, offset)
        offset += 2
        
        if family_name_size > 0 and offset + family_name_size <= len(data):
            family_bytes = data[offset:offset + family_name_size]
            try:
                names['family_name'] = family_bytes.decode('utf-16-le').rstrip('\x00')
            except:
                names['family_name'] = 'Unknown'
            offset += family_name_size
        
        # Style name length
        if offset + 2 <= len(data):
            style_name_size = read_uint16_le(data, offset)
            offset += 2
            
            if style_name_size > 0 and offset + style_name_size <= len(data):
                style_bytes = data[offset:offset + style_name_size]
                try:
                    names['style_name'] = style_bytes.decode('utf-16-le').rstrip('\x00')
                except:
                    names['style_name'] = 'Unknown'
                offset += style_name_size
        
        # Version string
        if offset + 2 <= len(data):
            version_size = read_uint16_le(data, offset)
            offset += 2
            
            if version_size > 0 and offset + version_size <= len(data):
                version_bytes = data[offset:offset + version_size]
                try:
                    names['version_string'] = version_bytes.decode('utf-16-le').rstrip('\x00')
                except:
                    names['version_string'] = 'Unknown'
        
    except Exception as e:
        names['error'] = f'Failed to extract names: {e}'
    
    return names


def extract_eot_metadata(file_path: str) -> Dict[str, Any]:
    """Extract complete EOT metadata"""
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': len(data),
        'format': 'EOT'
    }
    
    # Extract header
    header = extract_eot_header(data)
    if 'error' in header:
        metadata['error'] = header['error']
        return metadata
    
    metadata['header'] = header
    
    # Extract font names
    names = extract_font_names(data, 82)
    metadata['names'] = names
    
    # Analyze embedded font data
    font_data_offset = 82 + sum([
        2 + len(names.get('family_name', '').encode('utf-16-le')),
        2 + len(names.get('style_name', '').encode('utf-16-le')),
        2 + len(names.get('version_string', '').encode('utf-16-le'))
    ])
    
    if font_data_offset < len(data):
        # Check for TrueType/OpenType signature
        ttf_magic = data[font_data_offset:font_data_offset+4]
        if ttf_magic in [b'\x00\x01\x00\x00', b'OTTO', b'true', b'typ1']:
            metadata['embedded_format'] = 'TrueType/OpenType'
        else:
            metadata['embedded_format'] = 'Unknown'
    
    return metadata


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes")
    print(f"Format: {metadata['format']}")
    
    header = metadata.get('header', {})
    if header:
        print(f"\nEOT Header:")
        print(f"  Version: {header.get('version_string', 'Unknown')}")
        print(f"  EOT Size: {header.get('eot_size', 0):,} bytes")
        print(f"  Font Data Size: {header.get('font_data_size', 0):,} bytes")
        print(f"  Compression: {header.get('compression', 'unknown')}")
        print(f"  Weight: {header.get('weight', 0)}")
        print(f"  Italic: {header.get('italic', False)}")
        print(f"  Magic: 0x{header.get('magic_number', 0):04X}")
        
        # PANOSE classification
        panose = header.get('panose', [])
        if panose:
            print(f"  PANOSE: {' '.join(f'{b:02X}' for b in panose[:10])}")
    
    names = metadata.get('names', {})
    if names and not names.get('error'):
        print(f"\nFont Names:")
        if 'family_name' in names:
            print(f"  Family: {names['family_name']}")
        if 'style_name' in names:
            print(f"  Style: {names['style_name']}")
        if 'version_string' in names:
            print(f"  Version: {names['version_string']}")
    
    if 'embedded_format' in metadata:
        print(f"\nEmbedded Font: {metadata['embedded_format']}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python eot_extractor.py <file.eot>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_eot_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
