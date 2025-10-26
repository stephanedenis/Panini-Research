#!/usr/bin/env python3
"""MP4 Grammar Extractor - PaniniFS (ISO BMFF boxes)"""
import json, struct
from pathlib import Path

class MP4Analyzer:
    def __init__(self, filepath):
        self.data = Path(filepath).read_bytes()
        self.size = len(self.data)
        self.offset = 0
        self.patterns = set()
        self.boxes = []
    
    def read_u32_be(self):
        val = struct.unpack('>I', self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return val
    
    def read_bytes(self, n):
        data = self.data[self.offset:self.offset+n]
        self.offset += n
        return data
    
    def analyze(self):
        print(f"\n🎬 Analysing MP4: {self.size} bytes")
        
        while self.offset < self.size:
            if self.offset + 8 > self.size:
                break
            
            # Box: size (4) + type (4) + data
            box_size = self.read_u32_be()
            box_type = self.read_bytes(4).decode('ascii', errors='ignore')
            
            box_data_size = box_size - 8 if box_size >= 8 else 0
            
            if box_data_size > 0 and self.offset + box_data_size <= self.size:
                self.read_bytes(box_data_size)
            
            self.patterns.add('BOX_STRUCTURE')
            self.patterns.add('LENGTH_PREFIXED_DATA')
            
            if box_type == 'ftyp':
                self.patterns.add('FTYP_BOX')
            elif box_type == 'moov':
                self.patterns.add('MOOV_BOX')
                self.patterns.add('NESTED_BOX')
            elif box_type == 'mdat':
                self.patterns.add('MDAT_BOX')
            
            self.boxes.append({'type': box_type, 'size': box_size})
            print(f"  Box: {box_type} ({box_size} bytes)")
        
        self.patterns.add('MAGIC_NUMBER')
        self.patterns.add('SEQUENTIAL_STRUCTURE')
        
        return {
            'format': 'MP4',
            'size': self.size,
            'boxes': self.boxes,
            'patterns_found': sorted(list(self.patterns))
        }

def update_generic_patterns():
    patterns_file = Path('format_grammars/generic_patterns.json')
    existing = json.load(open(patterns_file))
    
    new = {
        'BOX_STRUCTURE': {
            'name': 'BOX_STRUCTURE',
            'description': 'ISO BMFF box (size + type + data)',
            'structure': ['LENGTH_PREFIXED_DATA', 'FOURCC', 'DATA'],
            'reusable': True,
            'formats': ['MP4', 'MOV', '3GP', 'M4A'],
            'size': 'variable'
        },
        'NESTED_BOX': {
            'name': 'NESTED_BOX',
            'description': 'Box containing child boxes (recursive)',
            'reusable': True,
            'formats': ['MP4', 'MOV'],
            'size': 'variable'
        },
        'FTYP_BOX': {
            'name': 'FTYP_BOX',
            'description': 'File type box (brand + compatibility)',
            'reusable': False,
            'formats': ['MP4', 'MOV'],
            'size': 'variable'
        },
        'MOOV_BOX': {
            'name': 'MOOV_BOX',
            'description': 'Movie metadata box (nested structure)',
            'reusable': False,
            'formats': ['MP4', 'MOV'],
            'size': 'variable'
        },
        'MDAT_BOX': {
            'name': 'MDAT_BOX',
            'description': 'Media data box (audio/video samples)',
            'reusable': False,
            'formats': ['MP4', 'MOV'],
            'size': 'variable'
        }
    }
    
    for name, pattern in new.items():
        if name not in existing['patterns']:
            existing['patterns'][name] = pattern
            print(f"  ➕ {name}")
    
    json.dump(existing, open(patterns_file, 'w'), indent=2)

if __name__ == '__main__':
    import sys
    analysis = MP4Analyzer(sys.argv[1]).analyze()
    
    grammar = {
        'format': 'MP4',
        'version': '1.0',
        'description': 'MPEG-4 Part 14 (ISO Base Media File Format)',
        'byte_order': 'big-endian',
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {'name': 'boxes', 'pattern': 'SEQUENTIAL_STRUCTURE'}
                ]
            }
        }
    }
    
    Path('format_grammars').mkdir(exist_ok=True)
    json.dump(grammar, open('format_grammars/mp4.json', 'w'), indent=2)
    json.dump(analysis, open(f"format_grammars/mp4_analysis_{Path(sys.argv[1]).stem}.json", 'w'), indent=2)
    
    print(f"\n✅ Grammar: format_grammars/mp4.json")
    update_generic_patterns()
    print(f"\n🧩 Patterns: {len(analysis['patterns_found'])}")
    for p in sorted(analysis['patterns_found']):
        print(f"  • {p}")
