#!/usr/bin/env python3
"""
PaniniFS v3.58 - CBOR (Concise Binary Object Representation) Format Extractor
RFC 8949 binary data serialization format

Extracts:
- Major types (0-7): unsigned int, negative int, byte string, text string,
  array, map, semantic tag, primitive
- Indefinite-length encoding detection
- Semantic tags (date/time, bignum, URI, etc.)
- Nested structure analysis
- Data type distribution
- Size and complexity metrics
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple, Optional

# CBOR major types (3 high bits)
MAJOR_TYPE_UNSIGNED = 0  # Unsigned integer
MAJOR_TYPE_NEGATIVE = 1  # Negative integer
MAJOR_TYPE_BYTES = 2     # Byte string
MAJOR_TYPE_TEXT = 3      # Text string (UTF-8)
MAJOR_TYPE_ARRAY = 4     # Array
MAJOR_TYPE_MAP = 5       # Map (key-value pairs)
MAJOR_TYPE_TAG = 6       # Semantic tag
MAJOR_TYPE_SIMPLE = 7    # Float, simple values, break

# Additional info values
ADDL_INFO_DIRECT = list(range(24))  # 0-23: value directly encoded
ADDL_INFO_UINT8 = 24   # 1-byte uint follows
ADDL_INFO_UINT16 = 25  # 2-byte uint follows
ADDL_INFO_UINT32 = 26  # 4-byte uint follows
ADDL_INFO_UINT64 = 27  # 8-byte uint follows
ADDL_INFO_INDEFINITE = 31  # Indefinite length

# Common semantic tags
TAG_DATETIME_STRING = 0  # Date/time string (RFC 3339)
TAG_EPOCH_DATETIME = 1   # Epoch-based date/time
TAG_POSITIVE_BIGNUM = 2  # Positive bignum
TAG_NEGATIVE_BIGNUM = 3  # Negative bignum
TAG_DECIMAL_FRACTION = 4 # Decimal fraction
TAG_BIGFLOAT = 5        # Bigfloat
TAG_BASE64URL = 21      # Base64url encoding
TAG_BASE64 = 22         # Base64 encoding
TAG_BASE16 = 23         # Base16 encoding
TAG_ENCODED_CBOR = 24   # Encoded CBOR data item
TAG_URI = 32            # URI (RFC 3986)
TAG_BASE64URL_URI = 33  # Base64url URI
TAG_BASE64_URI = 34     # Base64 URI
TAG_REGEXP = 35         # Regular expression
TAG_MIME = 36           # MIME message


class CBORDecoder:
    """CBOR decoder for metadata extraction"""
    
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.stats = {
            'major_types': {i: 0 for i in range(8)},
            'tags': {},
            'indefinite_items': 0,
            'max_nesting': 0,
            'total_items': 0
        }
    
    def read_byte(self) -> int:
        """Read single byte"""
        if self.offset >= len(self.data):
            raise EOFError("Unexpected end of CBOR data")
        byte = self.data[self.offset]
        self.offset += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        """Read multiple bytes"""
        if self.offset + count > len(self.data):
            raise EOFError("Unexpected end of CBOR data")
        result = self.data[self.offset:self.offset + count]
        self.offset += count
        return result
    
    def decode_initial_byte(self) -> Tuple[int, int]:
        """Decode initial byte into major type and additional info"""
        initial = self.read_byte()
        major_type = (initial >> 5) & 0x07
        additional_info = initial & 0x1F
        return major_type, additional_info
    
    def decode_argument(self, additional_info: int) -> Optional[int]:
        """Decode argument value based on additional info"""
        if additional_info < 24:
            return additional_info
        elif additional_info == 24:
            return self.read_byte()
        elif additional_info == 25:
            return struct.unpack('>H', self.read_bytes(2))[0]
        elif additional_info == 26:
            return struct.unpack('>I', self.read_bytes(4))[0]
        elif additional_info == 27:
            return struct.unpack('>Q', self.read_bytes(8))[0]
        elif additional_info == 31:
            return None  # Indefinite length
        else:
            raise ValueError(f"Invalid additional info: {additional_info}")
    
    def decode_item(self, depth: int = 0) -> Any:
        """Decode single CBOR item"""
        
        if depth > self.stats['max_nesting']:
            self.stats['max_nesting'] = depth
        
        if depth > 100:  # Prevent infinite recursion
            raise RecursionError("Maximum nesting depth exceeded")
        
        major_type, additional_info = self.decode_initial_byte()
        self.stats['major_types'][major_type] += 1
        self.stats['total_items'] += 1
        
        # Unsigned integer
        if major_type == MAJOR_TYPE_UNSIGNED:
            return {'type': 'unsigned', 'value': self.decode_argument(additional_info)}
        
        # Negative integer
        elif major_type == MAJOR_TYPE_NEGATIVE:
            arg = self.decode_argument(additional_info)
            return {'type': 'negative', 'value': -1 - arg}
        
        # Byte string
        elif major_type == MAJOR_TYPE_BYTES:
            length = self.decode_argument(additional_info)
            if length is None:  # Indefinite
                self.stats['indefinite_items'] += 1
                chunks = []
                while True:
                    mt, ai = self.decode_initial_byte()
                    if mt == MAJOR_TYPE_SIMPLE and ai == 31:  # Break
                        break
                    if mt != MAJOR_TYPE_BYTES:
                        raise ValueError("Indefinite byte string with non-byte chunk")
                    chunk_len = self.decode_argument(ai)
                    chunks.append(self.read_bytes(chunk_len))
                return {'type': 'bytes', 'length': sum(len(c) for c in chunks), 'indefinite': True}
            else:
                self.read_bytes(length)  # Skip actual bytes
                return {'type': 'bytes', 'length': length}
        
        # Text string
        elif major_type == MAJOR_TYPE_TEXT:
            length = self.decode_argument(additional_info)
            if length is None:  # Indefinite
                self.stats['indefinite_items'] += 1
                return {'type': 'text', 'indefinite': True}
            else:
                text = self.read_bytes(length).decode('utf-8', errors='replace')
                return {'type': 'text', 'length': length, 'value': text[:100]}  # Truncate for display
        
        # Array
        elif major_type == MAJOR_TYPE_ARRAY:
            length = self.decode_argument(additional_info)
            if length is None:  # Indefinite
                self.stats['indefinite_items'] += 1
                items = []
                while True:
                    mt, ai = self.decode_initial_byte()
                    if mt == MAJOR_TYPE_SIMPLE and ai == 31:  # Break
                        break
                    self.offset -= 1  # Put byte back
                    items.append(self.decode_item(depth + 1))
                return {'type': 'array', 'length': len(items), 'indefinite': True}
            else:
                for i in range(length):
                    self.decode_item(depth + 1)
                return {'type': 'array', 'length': length}
        
        # Map
        elif major_type == MAJOR_TYPE_MAP:
            length = self.decode_argument(additional_info)
            if length is None:  # Indefinite
                self.stats['indefinite_items'] += 1
                count = 0
                while True:
                    mt, ai = self.decode_initial_byte()
                    if mt == MAJOR_TYPE_SIMPLE and ai == 31:  # Break
                        break
                    self.offset -= 1  # Put byte back
                    self.decode_item(depth + 1)  # Key
                    self.decode_item(depth + 1)  # Value
                    count += 1
                return {'type': 'map', 'pairs': count, 'indefinite': True}
            else:
                for i in range(length):
                    self.decode_item(depth + 1)  # Key
                    self.decode_item(depth + 1)  # Value
                return {'type': 'map', 'pairs': length}
        
        # Semantic tag
        elif major_type == MAJOR_TYPE_TAG:
            tag = self.decode_argument(additional_info)
            self.stats['tags'][tag] = self.stats['tags'].get(tag, 0) + 1
            tagged_item = self.decode_item(depth + 1)
            return {'type': 'tag', 'tag': tag, 'content': tagged_item}
        
        # Simple values and floats
        elif major_type == MAJOR_TYPE_SIMPLE:
            if additional_info < 20:
                return {'type': 'simple', 'value': additional_info}
            elif additional_info == 20:  # False
                return {'type': 'bool', 'value': False}
            elif additional_info == 21:  # True
                return {'type': 'bool', 'value': True}
            elif additional_info == 22:  # Null
                return {'type': 'null'}
            elif additional_info == 23:  # Undefined
                return {'type': 'undefined'}
            elif additional_info == 25:  # Float16
                self.read_bytes(2)
                return {'type': 'float16'}
            elif additional_info == 26:  # Float32
                self.read_bytes(4)
                return {'type': 'float32'}
            elif additional_info == 27:  # Float64
                self.read_bytes(8)
                return {'type': 'float64'}
            elif additional_info == 31:  # Break (should not appear here)
                raise ValueError("Unexpected break")
            else:
                return {'type': 'simple', 'value': additional_info}
        
        else:
            raise ValueError(f"Unknown major type: {major_type}")


def extract_cbor_metadata(file_path: str) -> Dict[str, Any]:
    """Extract CBOR metadata"""
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': len(data),
        'format': 'CBOR'
    }
    
    decoder = CBORDecoder(data)
    
    try:
        # Decode root item
        root = decoder.decode_item()
        metadata['root'] = root
        metadata['statistics'] = decoder.stats
        
        # Tag names
        tag_names = {}
        tag_map = {
            0: 'DateTime String', 1: 'Epoch DateTime', 2: 'Positive Bignum',
            3: 'Negative Bignum', 4: 'Decimal Fraction', 5: 'Bigfloat',
            21: 'Base64url', 22: 'Base64', 23: 'Base16',
            24: 'Encoded CBOR', 32: 'URI', 35: 'RegExp', 36: 'MIME'
        }
        
        for tag_id, count in decoder.stats['tags'].items():
            tag_names[tag_id] = {
                'count': count,
                'name': tag_map.get(tag_id, f'Tag {tag_id}')
            }
        
        metadata['tags'] = tag_names
        
    except Exception as e:
        metadata['decode_error'] = str(e)
    
    return metadata


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes")
    print(f"Format: {metadata['format']}")
    
    if 'decode_error' in metadata:
        print(f"\nDecode Error: {metadata['decode_error']}")
        return
    
    root = metadata.get('root', {})
    if root:
        print(f"\nRoot Item:")
        print(f"  Type: {root.get('type', 'unknown')}")
        if 'length' in root:
            print(f"  Length: {root['length']}")
        if 'pairs' in root:
            print(f"  Pairs: {root['pairs']}")
        if 'indefinite' in root and root['indefinite']:
            print(f"  Indefinite: Yes")
    
    stats = metadata.get('statistics', {})
    if stats:
        print(f"\nStatistics:")
        print(f"  Total items: {stats.get('total_items', 0)}")
        print(f"  Max nesting: {stats.get('max_nesting', 0)}")
        print(f"  Indefinite items: {stats.get('indefinite_items', 0)}")
        
        major_types = stats.get('major_types', {})
        type_names = [
            'Unsigned Int', 'Negative Int', 'Byte String', 'Text String',
            'Array', 'Map', 'Tag', 'Simple/Float'
        ]
        
        print(f"\n  Major Types Distribution:")
        for i, name in enumerate(type_names):
            count = major_types.get(i, 0)
            if count > 0:
                print(f"    {name}: {count}")
    
    tags = metadata.get('tags', {})
    if tags:
        print(f"\n  Semantic Tags:")
        for tag_id, tag_info in sorted(tags.items()):
            print(f"    Tag {tag_id} ({tag_info['name']}): {tag_info['count']}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python cbor_extractor.py <file.cbor>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_cbor_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
