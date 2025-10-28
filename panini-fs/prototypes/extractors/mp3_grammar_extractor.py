#!/usr/bin/env python3
"""MP3 Grammar Extractor - PaniniFS (ID3 + MPEG frames)"""
import json, struct
from pathlib import Path

class MP3Analyzer:
    def __init__(self, filepath):
        self.data = Path(filepath).read_bytes()
        self.size = len(self.data)
        self.patterns = set()
    
    def analyze(self):
        print(f"\n🎵 Analysing MP3: {self.size} bytes")
        
        offset = 0
        
        # Check for ID3v2 tag
        if self.data[:3] == b'ID3':
            version = f"{self.data[3]}.{self.data[4]}"
            # ID3 size is synchsafe int (7 bits per byte)
            size_bytes = self.data[6:10]
            id3_size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
            print(f"  ID3v2.{version} tag: {id3_size + 10} bytes")
            self.patterns.add('ID3_TAG')
            offset = 10 + id3_size
        
        # Find MPEG sync words (0xFFF or 0xFFE)
        frames = 0
        while offset < self.size - 4:
            # Check for sync word
            if self.data[offset] == 0xFF and (self.data[offset+1] & 0xE0) == 0xE0:
                frames += 1
                self.patterns.add('MPEG_FRAME')
                self.patterns.add('FRAME_HEADER')
                
                # Parse frame header
                header = struct.unpack('>I', self.data[offset:offset+4])[0]
                
                # Extract fields (simplified)
                mpeg_version = (header >> 19) & 0x03
                layer = (header >> 17) & 0x03
                bitrate_index = (header >> 12) & 0x0F
                
                # Estimate frame size (simplified, 144 for Layer III)
                frame_size = 144 if bitrate_index > 0 else 4
                offset += frame_size
            else:
                offset += 1
        
        print(f"  MPEG frames found: {frames}")
        
        self.patterns.add('MAGIC_NUMBER')
        self.patterns.add('SEQUENTIAL_STRUCTURE')
        
        return {
            'format': 'MP3',
            'size': self.size,
            'frames': frames,
            'patterns_found': sorted(list(self.patterns))
        }

def update_generic_patterns():
    patterns_file = Path('format_grammars/generic_patterns.json')
    existing = json.load(open(patterns_file))
    
    new = {
        'ID3_TAG': {
            'name': 'ID3_TAG',
            'description': 'ID3 metadata tag (v1 or v2)',
            'reusable': False,
            'formats': ['MP3'],
            'size': 'variable'
        },
        'MPEG_FRAME': {
            'name': 'MPEG_FRAME',
            'description': 'MPEG audio frame (sync + header + data)',
            'reusable': True,
            'formats': ['MP3', 'MP4', 'MPEG'],
            'size': 'variable'
        },
        'FRAME_HEADER': {
            'name': 'FRAME_HEADER',
            'description': 'Frame header with sync word (0xFFF)',
            'reusable': True,
            'formats': ['MP3', 'MP4', 'AAC'],
            'size': 'fixed_4_bytes'
        }
    }
    
    for name, pattern in new.items():
        if name not in existing['patterns']:
            existing['patterns'][name] = pattern
            print(f"  ➕ {name}")
    
    json.dump(existing, open(patterns_file, 'w'), indent=2)

if __name__ == '__main__':
    import sys
    analysis = MP3Analyzer(sys.argv[1]).analyze()
    
    grammar = {
        'format': 'MP3',
        'version': '1.0',
        'description': 'MPEG Audio Layer III',
        'byte_order': 'big-endian',
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {'name': 'id3_tag', 'pattern': 'ID3_TAG', 'optional': True},
                    {'name': 'mpeg_frames', 'pattern': 'SEQUENTIAL_STRUCTURE'}
                ]
            }
        }
    }
    
    Path('format_grammars').mkdir(exist_ok=True)
    json.dump(grammar, open('format_grammars/mp3.json', 'w'), indent=2)
    json.dump(analysis, open(f"format_grammars/mp3_analysis_{Path(sys.argv[1]).stem}.json", 'w'), indent=2)
    
    print(f"\n✅ Grammar: format_grammars/mp3.json")
    update_generic_patterns()
    print(f"\n🧩 Patterns: {len(analysis['patterns_found'])}")
    for p in sorted(analysis['patterns_found']):
        print(f"  • {p}")
