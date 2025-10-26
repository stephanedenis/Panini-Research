#!/usr/bin/env python3
"""ZIP Grammar Extractor - PaniniFS (double index architecture)"""
import json, struct
from pathlib import Path

class ZIPAnalyzer:
    def __init__(self, filepath):
        self.data = Path(filepath).read_bytes()
        self.size = len(self.data)
        self.patterns = set()
    
    def analyze(self):
        print(f"\n📦 Analysing ZIP: {self.size} bytes")
        
        # Find local file headers (PK\x03\x04)
        local_headers = []
        offset = 0
        while True:
            pos = self.data.find(b'PK\x03\x04', offset)
            if pos == -1:
                break
            local_headers.append(pos)
            self.patterns.add('LOCAL_FILE_HEADER')
            offset = pos + 4
        
        print(f"  Local headers: {len(local_headers)}")
        
        # Find central directory (PK\x01\x02)
        central_dir = []
        offset = 0
        while True:
            pos = self.data.find(b'PK\x01\x02', offset)
            if pos == -1:
                break
            central_dir.append(pos)
            self.patterns.add('CENTRAL_DIRECTORY_HEADER')
            offset = pos + 4
        
        print(f"  Central directory entries: {len(central_dir)}")
        
        # Find end of central directory (PK\x05\x06)
        eocd_pos = self.data.rfind(b'PK\x05\x06')
        if eocd_pos != -1:
            self.patterns.add('END_OF_CENTRAL_DIR')
            print(f"  EOCD at: 0x{eocd_pos:X}")
        
        self.patterns.add('MAGIC_NUMBER')
        self.patterns.add('SEQUENTIAL_STRUCTURE')
        
        return {
            'format': 'ZIP',
            'size': self.size,
            'local_headers': len(local_headers),
            'central_directory_entries': len(central_dir),
            'patterns_found': sorted(list(self.patterns))
        }

def update_generic_patterns():
    patterns_file = Path('format_grammars/generic_patterns.json')
    existing = json.load(open(patterns_file))
    
    new = {
        'LOCAL_FILE_HEADER': {
            'name': 'LOCAL_FILE_HEADER',
            'description': 'ZIP local file header (PK\\x03\\x04 + metadata + compressed data)',
            'reusable': False,
            'formats': ['ZIP', 'JAR', 'APK'],
            'size': 'variable'
        },
        'CENTRAL_DIRECTORY_HEADER': {
            'name': 'CENTRAL_DIRECTORY_HEADER',
            'description': 'ZIP central directory entry (PK\\x01\\x02 + file metadata)',
            'reusable': False,
            'formats': ['ZIP', 'JAR', 'APK'],
            'size': 'variable'
        },
        'END_OF_CENTRAL_DIR': {
            'name': 'END_OF_CENTRAL_DIR',
            'description': 'ZIP end of central directory (PK\\x05\\x06 + global metadata)',
            'reusable': False,
            'formats': ['ZIP', 'JAR', 'APK'],
            'size': 'minimum_22_bytes'
        }
    }
    
    for name, pattern in new.items():
        if name not in existing['patterns']:
            existing['patterns'][name] = pattern
            print(f"  ➕ {name}")
    
    json.dump(existing, open(patterns_file, 'w'), indent=2)

if __name__ == '__main__':
    import sys
    analysis = ZIPAnalyzer(sys.argv[1]).analyze()
    
    grammar = {
        'format': 'ZIP',
        'version': '1.0',
        'description': 'ZIP archive (double index: local + central)',
        'byte_order': 'little-endian',
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {'name': 'local_files', 'pattern': 'SEQUENTIAL_STRUCTURE'},
                    {'name': 'central_directory', 'pattern': 'SEQUENTIAL_STRUCTURE'},
                    {'name': 'eocd', 'pattern': 'END_OF_CENTRAL_DIR'}
                ]
            }
        }
    }
    
    Path('format_grammars').mkdir(exist_ok=True)
    json.dump(grammar, open('format_grammars/zip.json', 'w'), indent=2)
    json.dump(analysis, open(f"format_grammars/zip_analysis_{Path(sys.argv[1]).stem}.json", 'w'), indent=2)
    
    print(f"\n✅ Grammar: format_grammars/zip.json")
    update_generic_patterns()
    print(f"\n🧩 Patterns: {len(analysis['patterns_found'])}")
    for p in sorted(analysis['patterns_found']):
        print(f"  • {p}")
