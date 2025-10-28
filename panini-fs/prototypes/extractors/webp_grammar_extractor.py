#!/usr/bin/env python3
"""
WebP Grammar Extractor - PaniniFS Research
Analyzes WebP files to extract universal binary patterns.
WebP is a RIFF-based format, so high pattern reusability expected (~70-80%).
"""

import json
import struct
from pathlib import Path
from typing import Dict, List, Any, Tuple

class WebPAnalyzer:
    """Analyze WebP structure and extract patterns."""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = self.filepath.read_bytes()
        self.size = len(self.data)
        self.offset = 0
        self.chunks = []
        self.patterns = set()
        
    def read_bytes(self, n: int) -> bytes:
        """Read n bytes and advance offset."""
        if self.offset + n > self.size:
            raise ValueError(f"Cannot read {n} bytes at offset {self.offset}")
        data = self.data[self.offset:self.offset + n]
        self.offset += n
        return data
    
    def peek_bytes(self, n: int) -> bytes:
        """Peek n bytes without advancing offset."""
        if self.offset + n > self.size:
            return b''
        return self.data[self.offset:self.offset + n]
    
    def read_fourcc(self) -> str:
        """Read FOURCC (4-char code)."""
        return self.read_bytes(4).decode('ascii', errors='ignore')
    
    def read_u32_le(self) -> int:
        """Read 32-bit unsigned little-endian integer."""
        return struct.unpack('<I', self.read_bytes(4))[0]
    
    def analyze(self) -> Dict[str, Any]:
        """Main analysis entry point."""
        print(f"\n📸 Analysing WebP: {self.filepath.name}")
        print(f"Size: {self.size} bytes")
        
        # Analyze RIFF header
        riff_header = self.analyze_riff_header()
        
        # Analyze WEBP form type
        form_type = self.read_fourcc()
        if form_type != 'WEBP':
            raise ValueError(f"Not a WebP file: expected 'WEBP', got '{form_type}'")
        
        print(f"Form type: {form_type}")
        self.patterns.add('RIFF_FORM_TYPE')
        
        # Analyze chunks until EOF
        while self.offset < self.size:
            chunk_info = self.analyze_chunk()
            if chunk_info:
                self.chunks.append(chunk_info)
        
        print(f"\n📦 Found {len(self.chunks)} chunk(s):")
        for chunk in self.chunks:
            print(f"  • {chunk['fourcc']}: {chunk['size']} bytes @ offset {chunk['offset']}")
        
        # Build complete analysis
        analysis = {
            'file': str(self.filepath),
            'size': self.size,
            'format': 'WebP',
            'riff_header': riff_header,
            'form_type': form_type,
            'chunks': self.chunks,
            'patterns_found': sorted(list(self.patterns))
        }
        
        return analysis
    
    def analyze_riff_header(self) -> Dict[str, Any]:
        """Analyze RIFF header (12 bytes: RIFF + size + WEBP)."""
        start_offset = self.offset
        
        # RIFF signature
        signature = self.read_fourcc()
        if signature != 'RIFF':
            raise ValueError(f"Not a RIFF file: expected 'RIFF', got '{signature}'")
        
        self.patterns.add('MAGIC_NUMBER')
        
        # File size (little-endian, excludes signature+size itself)
        file_size = self.read_u32_le()
        expected_size = self.size - 8  # Exclude RIFF + size
        
        print(f"RIFF signature: {signature}")
        print(f"File size (in header): {file_size} bytes")
        print(f"Actual size (calculated): {expected_size} bytes")
        
        if file_size != expected_size:
            print(f"⚠️  Size mismatch: header says {file_size}, actual is {expected_size}")
        
        self.patterns.add('LENGTH_PREFIXED_DATA')
        self.patterns.add('RIFF_HEADER')
        
        return {
            'offset': start_offset,
            'signature': signature,
            'file_size': file_size,
            'size_match': file_size == expected_size
        }
    
    def analyze_chunk(self) -> Dict[str, Any]:
        """Analyze a RIFF chunk (FourCC + size + data)."""
        if self.offset >= self.size:
            return None
        
        start_offset = self.offset
        
        # FourCC (4 bytes)
        fourcc = self.read_fourcc()
        if not fourcc or len(fourcc) != 4:
            print(f"⚠️  Invalid FourCC at offset {start_offset}: {fourcc}")
            return None
        
        # Chunk size (4 bytes, little-endian)
        chunk_size = self.read_u32_le()
        
        # Data (chunk_size bytes)
        if self.offset + chunk_size > self.size:
            print(f"⚠️  Chunk size {chunk_size} exceeds file bounds at offset {self.offset}")
            chunk_size = self.size - self.offset
        
        chunk_data = self.read_bytes(chunk_size)
        
        # RIFF chunks must be word-aligned (pad byte if odd size)
        if chunk_size % 2 == 1:
            if self.offset < self.size:
                pad_byte = self.read_bytes(1)
                self.patterns.add('PADDING_ALIGNMENT')
        
        self.patterns.add('RIFF_CHUNK')
        self.patterns.add('LENGTH_PREFIXED_DATA')
        
        # Analyze specific chunk types
        chunk_info = {
            'offset': start_offset,
            'fourcc': fourcc,
            'size': chunk_size,
            'data_preview': chunk_data[:32].hex() if len(chunk_data) > 32 else chunk_data.hex()
        }
        
        if fourcc == 'VP8 ':
            chunk_info['type'] = 'VP8_LOSSY'
            chunk_info['details'] = self.analyze_vp8_chunk(chunk_data)
            self.patterns.add('VP8_BITSTREAM')
        elif fourcc == 'VP8L':
            chunk_info['type'] = 'VP8_LOSSLESS'
            chunk_info['details'] = self.analyze_vp8l_chunk(chunk_data)
            self.patterns.add('VP8L_BITSTREAM')
        elif fourcc == 'VP8X':
            chunk_info['type'] = 'VP8_EXTENDED'
            chunk_info['details'] = self.analyze_vp8x_chunk(chunk_data)
            self.patterns.add('VP8X_HEADER')
        elif fourcc == 'ALPH':
            chunk_info['type'] = 'ALPHA_CHANNEL'
            self.patterns.add('ALPHA_DATA')
        elif fourcc == 'ANIM':
            chunk_info['type'] = 'ANIMATION'
            self.patterns.add('ANIMATION_DATA')
        elif fourcc == 'ANMF':
            chunk_info['type'] = 'ANIMATION_FRAME'
            self.patterns.add('ANIMATION_FRAME_DATA')
        elif fourcc == 'ICCP':
            chunk_info['type'] = 'ICC_PROFILE'
            self.patterns.add('ICC_PROFILE_DATA')
        elif fourcc == 'EXIF':
            chunk_info['type'] = 'EXIF_METADATA'
            self.patterns.add('EXIF_DATA')
        elif fourcc == 'XMP ':
            chunk_info['type'] = 'XMP_METADATA'
            self.patterns.add('XMP_DATA')
        else:
            chunk_info['type'] = 'UNKNOWN'
        
        return chunk_info
    
    def analyze_vp8_chunk(self, data: bytes) -> Dict[str, Any]:
        """Analyze VP8 lossy bitstream."""
        if len(data) < 10:
            return {'error': 'Chunk too small'}
        
        # Frame tag (3 bytes)
        frame_tag = struct.unpack('<I', data[:3] + b'\x00')[0]
        key_frame = (frame_tag & 0x01) == 0
        version = (frame_tag >> 1) & 0x07
        show_frame = (frame_tag >> 4) & 0x01
        first_part_size = (frame_tag >> 5) & 0x7FFFF
        
        # Start code (3 bytes): 0x9d 0x01 0x2a
        start_code = data[3:6]
        
        # Width and height (2 bytes each, little-endian)
        if len(data) >= 10:
            width = struct.unpack('<H', data[6:8])[0] & 0x3FFF
            height = struct.unpack('<H', data[8:10])[0] & 0x3FFF
        else:
            width = height = 0
        
        return {
            'key_frame': key_frame,
            'version': version,
            'show_frame': show_frame,
            'first_part_size': first_part_size,
            'start_code': start_code.hex(),
            'width': width,
            'height': height
        }
    
    def analyze_vp8l_chunk(self, data: bytes) -> Dict[str, Any]:
        """Analyze VP8L lossless bitstream."""
        if len(data) < 5:
            return {'error': 'Chunk too small'}
        
        # Signature byte: 0x2f
        signature = data[0]
        if signature != 0x2f:
            return {'error': f'Invalid VP8L signature: 0x{signature:02x}'}
        
        # Width and height encoded in 14 bits each
        size_bits = struct.unpack('<I', data[1:5])[0]
        width = (size_bits & 0x3FFF) + 1
        height = ((size_bits >> 14) & 0x3FFF) + 1
        alpha_used = (size_bits >> 28) & 0x01
        version = (size_bits >> 29) & 0x07
        
        return {
            'signature': f'0x{signature:02x}',
            'width': width,
            'height': height,
            'alpha_used': bool(alpha_used),
            'version': version
        }
    
    def analyze_vp8x_chunk(self, data: bytes) -> Dict[str, Any]:
        """Analyze VP8X extended header."""
        if len(data) < 10:
            return {'error': 'Chunk too small'}
        
        # Flags byte
        flags = data[0]
        has_icc = bool(flags & 0x20)
        has_alpha = bool(flags & 0x10)
        has_exif = bool(flags & 0x08)
        has_xmp = bool(flags & 0x04)
        has_animation = bool(flags & 0x02)
        
        # Canvas size (3 bytes each, little-endian, +1)
        canvas_width = struct.unpack('<I', data[4:7] + b'\x00')[0] + 1
        canvas_height = struct.unpack('<I', data[7:10] + b'\x00')[0] + 1
        
        return {
            'flags': f'0x{flags:02x}',
            'has_icc': has_icc,
            'has_alpha': has_alpha,
            'has_exif': has_exif,
            'has_xmp': has_xmp,
            'has_animation': has_animation,
            'canvas_width': canvas_width,
            'canvas_height': canvas_height
        }

def generate_grammar(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate WebP grammar from analysis."""
    
    # Build grammar structure
    grammar = {
        'format': 'WebP',
        'description': 'WebP image format (RIFF-based)',
        'byte_order': 'little-endian',
        'magic_number': {
            'value': '52494646',  # 'RIFF'
            'offset': 0,
            'length': 4
        },
        'structure': [
            {
                'name': 'riff_header',
                'pattern': 'RIFF_HEADER',
                'offset': 0,
                'length': 12,
                'components': [
                    {
                        'name': 'signature',
                        'pattern': 'MAGIC_NUMBER',
                        'value': 'RIFF',
                        'length': 4
                    },
                    {
                        'name': 'file_size',
                        'pattern': 'LENGTH_PREFIXED_DATA',
                        'type': 'uint32_le',
                        'length': 4,
                        'description': 'File size (excludes RIFF header)'
                    },
                    {
                        'name': 'form_type',
                        'pattern': 'RIFF_FORM_TYPE',
                        'value': 'WEBP',
                        'length': 4
                    }
                ]
            },
            {
                'name': 'chunks',
                'pattern': 'SEQUENTIAL_STRUCTURE',
                'description': 'RIFF chunks until EOF',
                'repeat': 'until_eof',
                'element': {
                    'name': 'riff_chunk',
                    'pattern': 'RIFF_CHUNK',
                    'components': [
                        {
                            'name': 'fourcc',
                            'type': 'fourcc',
                            'length': 4
                        },
                        {
                            'name': 'chunk_size',
                            'type': 'uint32_le',
                            'length': 4
                        },
                        {
                            'name': 'chunk_data',
                            'type': 'bytes',
                            'length_field': 'chunk_size',
                            'variants': [
                                {
                                    'condition': 'fourcc == "VP8 "',
                                    'pattern': 'VP8_BITSTREAM'
                                },
                                {
                                    'condition': 'fourcc == "VP8L"',
                                    'pattern': 'VP8L_BITSTREAM'
                                },
                                {
                                    'condition': 'fourcc == "VP8X"',
                                    'pattern': 'VP8X_HEADER'
                                }
                            ]
                        },
                        {
                            'name': 'padding',
                            'pattern': 'PADDING_ALIGNMENT',
                            'condition': 'chunk_size % 2 == 1',
                            'length': 1,
                            'optional': True
                        }
                    ]
                }
            }
        ]
    }
    
    return grammar

def update_generic_patterns(patterns: set) -> None:
    """Update generic_patterns.json with new patterns from WebP."""
    patterns_file = Path('format_grammars/generic_patterns.json')
    
    if patterns_file.exists():
        with open(patterns_file, 'r') as f:
            existing = json.load(f)
    else:
        existing = {'patterns': {}}
    
    # WebP-specific patterns to add
    new_patterns = {
        'RIFF_HEADER': {
            'name': 'RIFF_HEADER',
            'description': 'RIFF file header (signature + size + form type)',
            'structure': ['MAGIC_NUMBER', 'LENGTH_PREFIXED_DATA', 'RIFF_FORM_TYPE'],
            'reusable': True,
            'formats': ['WebP', 'WAV', 'AVI', 'MIDI'],
            'size': 'fixed_12_bytes'
        },
        'RIFF_FORM_TYPE': {
            'name': 'RIFF_FORM_TYPE',
            'description': 'RIFF form type identifier (FOURCC)',
            'example': 'WEBP, WAVE, AVI, RMID',
            'reusable': True,
            'formats': ['WebP', 'WAV', 'AVI', 'MIDI'],
            'size': 'fixed_4_bytes'
        },
        'RIFF_CHUNK': {
            'name': 'RIFF_CHUNK',
            'description': 'RIFF chunk (FourCC + size + data + optional padding)',
            'structure': ['FOURCC', 'LENGTH_PREFIXED_DATA', 'OPTIONAL_PADDING'],
            'reusable': True,
            'formats': ['WebP', 'WAV', 'AVI', 'MIDI'],
            'alignment': 'word_aligned'
        },
        'VP8_BITSTREAM': {
            'name': 'VP8_BITSTREAM',
            'description': 'VP8 lossy video bitstream',
            'structure': ['FRAME_TAG', 'START_CODE', 'WIDTH_HEIGHT', 'COMPRESSED_DATA'],
            'reusable': False,
            'formats': ['WebP', 'WebM', 'MP4'],
            'compression': 'VP8'
        },
        'VP8L_BITSTREAM': {
            'name': 'VP8L_BITSTREAM',
            'description': 'VP8L lossless image bitstream',
            'structure': ['SIGNATURE', 'WIDTH_HEIGHT_ALPHA', 'COMPRESSED_DATA'],
            'reusable': False,
            'formats': ['WebP'],
            'compression': 'VP8L'
        },
        'VP8X_HEADER': {
            'name': 'VP8X_HEADER',
            'description': 'VP8X extended features header',
            'structure': ['FLAGS', 'CANVAS_SIZE'],
            'reusable': False,
            'formats': ['WebP'],
            'features': ['ICC', 'ALPHA', 'EXIF', 'XMP', 'ANIMATION']
        },
        'PADDING_ALIGNMENT': {
            'name': 'PADDING_ALIGNMENT',
            'description': 'Padding byte for word alignment',
            'reusable': True,
            'formats': ['WebP', 'WAV', 'AVI', 'MIDI', 'IFF'],
            'size': '1_byte_if_odd'
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
        print("Usage: python3 webp_grammar_extractor.py <webp_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    # Analyze WebP
    analyzer = WebPAnalyzer(filepath)
    analysis = analyzer.analyze()
    
    # Generate grammar
    grammar = generate_grammar(analysis)
    
    # Save outputs
    output_dir = Path('format_grammars')
    output_dir.mkdir(exist_ok=True)
    
    # Save grammar
    grammar_file = output_dir / 'webp.json'
    with open(grammar_file, 'w') as f:
        json.dump(grammar, f, indent=2)
    print(f"\n✅ Grammar saved: {grammar_file}")
    
    # Save analysis
    analysis_file = output_dir / f"webp_analysis_{Path(filepath).stem}.json"
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
