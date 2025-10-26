#!/usr/bin/env python3
"""
TIFF Grammar Extractor - PaniniFS Research
Analyzes TIFF files to extract universal binary patterns.
TIFF = Tagged Image File Format (Adobe/Aldus, very flexible).
"""

import json
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional

class TIFFAnalyzer:
    """Analyze TIFF structure and extract patterns."""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = self.filepath.read_bytes()
        self.size = len(self.data)
        self.offset = 0
        self.byte_order = None  # '<' (little) ou '>' (big)
        self.ifds = []
        self.patterns = set()
        
    def read_bytes(self, n: int) -> bytes:
        """Read n bytes and advance offset."""
        if self.offset + n > self.size:
            raise ValueError(f"Cannot read {n} bytes at offset {self.offset}")
        data = self.data[self.offset:self.offset + n]
        self.offset += n
        return data
    
    def read_u16(self) -> int:
        """Read 16-bit unsigned integer (respects byte order)."""
        return struct.unpack(f'{self.byte_order}H', self.read_bytes(2))[0]
    
    def read_u32(self) -> int:
        """Read 32-bit unsigned integer (respects byte order)."""
        return struct.unpack(f'{self.byte_order}I', self.read_bytes(4))[0]
    
    def peek_at(self, offset: int, n: int) -> bytes:
        """Peek at n bytes at specific offset without moving."""
        if offset + n > self.size:
            return b''
        return self.data[offset:offset + n]
    
    def analyze(self) -> Dict[str, Any]:
        """Main analysis entry point."""
        print(f"\n📸 Analysing TIFF: {self.filepath.name}")
        print(f"Size: {self.size} bytes")
        
        # Analyze header
        header = self.analyze_header()
        
        # Analyze IFD chain
        ifd_offset = header['first_ifd_offset']
        ifd_index = 0
        
        while ifd_offset != 0:
            print(f"\n📑 Analyzing IFD #{ifd_index} at offset 0x{ifd_offset:08X}")
            ifd = self.analyze_ifd(ifd_offset)
            self.ifds.append(ifd)
            ifd_offset = ifd['next_ifd_offset']
            ifd_index += 1
        
        print(f"\n✅ Found {len(self.ifds)} IFD(s)")
        
        # Build complete analysis
        analysis = {
            'file': str(self.filepath),
            'size': self.size,
            'format': 'TIFF',
            'byte_order': 'little-endian' if self.byte_order == '<' else 'big-endian',
            'header': header,
            'ifds': self.ifds,
            'patterns_found': sorted(list(self.patterns))
        }
        
        return analysis
    
    def analyze_header(self) -> Dict[str, Any]:
        """Analyze TIFF header (8 bytes: byte_order + magic + IFD offset)."""
        start_offset = self.offset
        
        # Byte order (2 bytes)
        byte_order_marker = self.read_bytes(2)
        
        if byte_order_marker == b'II':
            self.byte_order = '<'  # Little-endian (Intel)
            bo_name = 'little-endian (II)'
        elif byte_order_marker == b'MM':
            self.byte_order = '>'  # Big-endian (Motorola)
            bo_name = 'big-endian (MM)'
        else:
            raise ValueError(f"Invalid byte order marker: {byte_order_marker.hex()}")
        
        print(f"Byte order: {bo_name}")
        self.patterns.add('BYTE_ORDER_MARKER')
        
        # Magic number (2 bytes): 0x002A (42)
        magic = self.read_u16()
        if magic != 42:
            raise ValueError(f"Invalid TIFF magic number: {magic} (expected 42)")
        
        print(f"Magic: {magic} (0x{magic:04X})")
        self.patterns.add('MAGIC_NUMBER')
        
        # Offset to first IFD (4 bytes)
        first_ifd_offset = self.read_u32()
        print(f"First IFD offset: 0x{first_ifd_offset:08X}")
        
        self.patterns.add('TIFF_HEADER')
        self.patterns.add('OFFSET_POINTER')
        
        return {
            'offset': start_offset,
            'byte_order_marker': byte_order_marker.decode('ascii'),
            'byte_order': bo_name,
            'magic': magic,
            'first_ifd_offset': first_ifd_offset,
            'size': 8
        }
    
    def analyze_ifd(self, ifd_offset: int) -> Dict[str, Any]:
        """Analyze one IFD (Image File Directory)."""
        self.offset = ifd_offset
        start_offset = ifd_offset
        
        # Number of directory entries (2 bytes)
        num_entries = self.read_u16()
        print(f"  Entries: {num_entries}")
        
        self.patterns.add('IFD_STRUCTURE')
        
        # Read all entries
        entries = []
        for i in range(num_entries):
            entry = self.analyze_ifd_entry()
            entries.append(entry)
        
        # Offset to next IFD (4 bytes, 0 = no more IFDs)
        next_ifd_offset = self.read_u32()
        
        return {
            'offset': start_offset,
            'num_entries': num_entries,
            'entries': entries,
            'next_ifd_offset': next_ifd_offset,
            'size': self.offset - start_offset
        }
    
    def analyze_ifd_entry(self) -> Dict[str, Any]:
        """Analyze one IFD entry (12 bytes: tag + type + count + value/offset)."""
        start_offset = self.offset
        
        # Tag (2 bytes)
        tag = self.read_u16()
        
        # Type (2 bytes)
        field_type = self.read_u16()
        
        # Count (4 bytes)
        count = self.read_u32()
        
        # Value or offset (4 bytes)
        value_or_offset = self.read_bytes(4)
        
        self.patterns.add('TAG_VALUE_PAIR')
        
        # Decode tag name
        tag_name = self.get_tag_name(tag)
        
        # Decode type name
        type_name = self.get_type_name(field_type)
        
        # Calculate value size
        type_sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}
        type_size = type_sizes.get(field_type, 0)
        total_size = count * type_size
        
        # Decode value
        if total_size <= 4:
            # Value is inline
            value = self.decode_value(value_or_offset[:total_size], field_type, count)
            value_location = 'inline'
        else:
            # Value is at offset
            offset_val = struct.unpack(f'{self.byte_order}I', value_or_offset)[0]
            value = f"offset 0x{offset_val:08X}"
            value_location = 'offset'
            
            # If it's strip data, mark pattern
            if tag in [273, 279, 324, 325]:  # StripOffsets, StripByteCounts, TileOffsets, TileByteCounts
                self.patterns.add('STRIP_DATA')
        
        return {
            'offset': start_offset,
            'tag': tag,
            'tag_name': tag_name,
            'type': field_type,
            'type_name': type_name,
            'count': count,
            'value': value,
            'value_location': value_location,
            'size': 12
        }
    
    def decode_value(self, data: bytes, field_type: int, count: int) -> Any:
        """Decode inline value based on type."""
        if count == 0:
            return None
        
        try:
            if field_type == 1:  # BYTE
                return list(data[:count])
            elif field_type == 2:  # ASCII
                return data[:count].decode('ascii', errors='ignore').rstrip('\x00')
            elif field_type == 3:  # SHORT
                if count == 1:
                    return struct.unpack(f'{self.byte_order}H', data[:2])[0]
                else:
                    return [struct.unpack(f'{self.byte_order}H', data[i:i+2])[0] 
                            for i in range(0, count*2, 2)]
            elif field_type == 4:  # LONG
                if count == 1:
                    return struct.unpack(f'{self.byte_order}I', data[:4])[0]
            else:
                return f"<{field_type}:{count}>"
        except Exception as e:
            return f"<decode error: {e}>"
    
    def get_tag_name(self, tag: int) -> str:
        """Get TIFF tag name."""
        tags = {
            254: 'NewSubfileType',
            256: 'ImageWidth',
            257: 'ImageLength',
            258: 'BitsPerSample',
            259: 'Compression',
            262: 'PhotometricInterpretation',
            273: 'StripOffsets',
            277: 'SamplesPerPixel',
            278: 'RowsPerStrip',
            279: 'StripByteCounts',
            282: 'XResolution',
            283: 'YResolution',
            284: 'PlanarConfiguration',
            296: 'ResolutionUnit',
            305: 'Software',
            306: 'DateTime',
            315: 'Artist',
            320: 'ColorMap',
            324: 'TileOffsets',
            325: 'TileByteCounts',
            338: 'ExtraSamples',
        }
        return tags.get(tag, f"Tag{tag}")
    
    def get_type_name(self, field_type: int) -> str:
        """Get TIFF field type name."""
        types = {
            1: 'BYTE',
            2: 'ASCII',
            3: 'SHORT',
            4: 'LONG',
            5: 'RATIONAL',
            6: 'SBYTE',
            7: 'UNDEFINED',
            8: 'SSHORT',
            9: 'SLONG',
            10: 'SRATIONAL',
            11: 'FLOAT',
            12: 'DOUBLE'
        }
        return types.get(field_type, f"Type{field_type}")

def generate_grammar(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate TIFF grammar from analysis."""
    
    byte_order = 'little-endian' if analysis['header']['byte_order_marker'] == 'II' else 'big-endian'
    
    grammar = {
        'format': 'TIFF',
        'version': '1.0',
        'description': 'Tagged Image File Format (flexible byte order)',
        'byte_order': byte_order,
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {
                        'name': 'tiff_header',
                        'pattern': 'TIFF_HEADER'
                    },
                    {
                        'name': 'ifd_chain',
                        'pattern': 'IFD_CHAIN',
                        'description': 'Linked list of Image File Directories'
                    }
                ]
            }
        }
    }
    
    return grammar

def update_generic_patterns(patterns: set) -> None:
    """Update generic_patterns.json with new patterns from TIFF."""
    patterns_file = Path('format_grammars/generic_patterns.json')
    
    if patterns_file.exists():
        with open(patterns_file, 'r') as f:
            existing = json.load(f)
    else:
        existing = {'patterns': {}}
    
    # TIFF-specific patterns to add
    new_patterns = {
        'TIFF_HEADER': {
            'name': 'TIFF_HEADER',
            'description': 'TIFF file header (byte order + magic + IFD offset)',
            'structure': ['BYTE_ORDER_MARKER', 'MAGIC_NUMBER', 'OFFSET_POINTER'],
            'reusable': False,
            'formats': ['TIFF'],
            'size': 'fixed_8_bytes'
        },
        'BYTE_ORDER_MARKER': {
            'name': 'BYTE_ORDER_MARKER',
            'description': 'Byte order marker (II=little, MM=big endian)',
            'example': 'II (Intel), MM (Motorola)',
            'reusable': True,
            'formats': ['TIFF', 'EXIF', 'DNG'],
            'size': 'fixed_2_bytes'
        },
        'OFFSET_POINTER': {
            'name': 'OFFSET_POINTER',
            'description': 'Pointer to data location elsewhere in file',
            'reusable': True,
            'formats': ['TIFF', 'PDF', 'ZIP', 'ELF'],
            'size': 'variable_2_4_8_bytes'
        },
        'IFD_STRUCTURE': {
            'name': 'IFD_STRUCTURE',
            'description': 'Image File Directory (count + entries + next pointer)',
            'structure': ['COUNT', 'TAG_VALUE_PAIR_ARRAY', 'OFFSET_POINTER'],
            'reusable': False,
            'formats': ['TIFF', 'EXIF', 'DNG'],
            'size': 'variable'
        },
        'TAG_VALUE_PAIR': {
            'name': 'TAG_VALUE_PAIR',
            'description': 'Tagged field (tag + type + count + value/offset)',
            'structure': ['TAG_ID', 'TYPE_CODE', 'COUNT', 'VALUE_OR_OFFSET'],
            'reusable': True,
            'formats': ['TIFF', 'EXIF', 'ID3v2', 'PNG_tEXt'],
            'size': 'fixed_12_bytes'
        },
        'STRIP_DATA': {
            'name': 'STRIP_DATA',
            'description': 'Image data organized in strips or tiles',
            'reusable': False,
            'formats': ['TIFF'],
            'size': 'variable'
        },
        'IFD_CHAIN': {
            'name': 'IFD_CHAIN',
            'description': 'Linked list of IFDs via offset pointers',
            'structure': ['IFD_STRUCTURE', 'OFFSET_POINTER to next'],
            'reusable': True,
            'formats': ['TIFF', 'EXIF', 'DNG'],
            'size': 'variable'
        }
    }
    
    # Add patterns that don't exist yet
    existing_names = set(existing['patterns'].keys())
    for name, pattern in new_patterns.items():
        if name not in existing_names:
            existing['patterns'][name] = pattern
            print(f"  ➕ Added pattern: {name}")
    
    # Save updated patterns
    with open(patterns_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"\n✅ Updated: {patterns_file}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 tiff_grammar_extractor.py <tiff_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    # Analyze TIFF
    analyzer = TIFFAnalyzer(filepath)
    analysis = analyzer.analyze()
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  IFDs: {len(analysis['ifds'])}")
    for i, ifd in enumerate(analysis['ifds']):
        print(f"    IFD #{i}: {ifd['num_entries']} entries")
        # Show key tags
        for entry in ifd['entries'][:5]:  # First 5 entries
            print(f"      • {entry['tag_name']}: {entry['value']}")
        if ifd['num_entries'] > 5:
            print(f"      ... ({ifd['num_entries'] - 5} more entries)")
    
    # Generate grammar
    grammar = generate_grammar(analysis)
    
    # Save outputs
    output_dir = Path('format_grammars')
    output_dir.mkdir(exist_ok=True)
    
    # Save grammar
    grammar_file = output_dir / 'tiff.json'
    with open(grammar_file, 'w') as f:
        json.dump(grammar, f, indent=2)
    print(f"\n✅ Grammar saved: {grammar_file}")
    
    # Save analysis
    analysis_file = output_dir / f"tiff_analysis_{Path(filepath).stem}.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"✅ Analysis saved: {analysis_file}")
    
    # Update generic patterns
    update_generic_patterns(analysis['patterns_found'])
    
    print(f"\n🧩 Patterns found: {len(analysis['patterns_found'])}")
    for pattern in sorted(analysis['patterns_found']):
        print(f"  • {pattern}")

if __name__ == '__main__':
    main()
