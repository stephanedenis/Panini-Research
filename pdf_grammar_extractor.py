#!/usr/bin/env python3
"""PDF Grammar Extractor - PaniniFS (text+binary mixed format)"""
import json, re
from pathlib import Path

class PDFAnalyzer:
    def __init__(self, filepath):
        self.data = Path(filepath).read_bytes()
        self.text = self.data.decode('latin1', errors='ignore')
        self.size = len(self.data)
        self.patterns = set()
    
    def analyze(self):
        print(f"\n📄 Analysing PDF: {self.size} bytes")
        
        # Header
        if self.text.startswith('%PDF-'):
            version = self.text[5:8]
            print(f"  PDF version: {version}")
            self.patterns.add('MAGIC_NUMBER')
            self.patterns.add('PDF_HEADER')
        
        # Objects (1 0 obj ... endobj)
        objects = re.findall(r'\d+ \d+ obj', self.text)
        print(f"  Objects: {len(objects)}")
        if objects:
            self.patterns.add('PDF_OBJECT')
        
        # Streams (stream ... endstream)
        streams = re.findall(r'stream.*?endstream', self.text, re.DOTALL)
        print(f"  Streams: {len(streams)}")
        if streams:
            self.patterns.add('CONTENT_STREAM')
        
        # Cross-reference table
        if 'xref' in self.text:
            print(f"  xref table found")
            self.patterns.add('XREF_TABLE')
        
        # Trailer
        if 'trailer' in self.text:
            print(f"  trailer found")
            self.patterns.add('PDF_TRAILER')
        
        # EOF marker
        if '%%EOF' in self.text:
            self.patterns.add('EOF_MARKER')
        
        self.patterns.add('SEQUENTIAL_STRUCTURE')
        
        return {
            'format': 'PDF',
            'size': self.size,
            'objects': len(objects),
            'streams': len(streams),
            'patterns_found': sorted(list(self.patterns))
        }

def update_generic_patterns():
    patterns_file = Path('format_grammars/generic_patterns.json')
    existing = json.load(open(patterns_file))
    
    new = {
        'PDF_HEADER': {
            'name': 'PDF_HEADER',
            'description': 'PDF header (%PDF-version)',
            'reusable': False,
            'formats': ['PDF'],
            'size': 'variable'
        },
        'PDF_OBJECT': {
            'name': 'PDF_OBJECT',
            'description': 'PDF indirect object (n m obj ... endobj)',
            'reusable': False,
            'formats': ['PDF'],
            'size': 'variable'
        },
        'CONTENT_STREAM': {
            'name': 'CONTENT_STREAM',
            'description': 'PDF content stream (stream ... endstream)',
            'reusable': False,
            'formats': ['PDF'],
            'size': 'variable'
        },
        'XREF_TABLE': {
            'name': 'XREF_TABLE',
            'description': 'PDF cross-reference table (object offsets)',
            'reusable': False,
            'formats': ['PDF'],
            'size': 'variable'
        },
        'PDF_TRAILER': {
            'name': 'PDF_TRAILER',
            'description': 'PDF trailer dictionary',
            'reusable': False,
            'formats': ['PDF'],
            'size': 'variable'
        },
        'EOF_MARKER': {
            'name': 'EOF_MARKER',
            'description': 'End-of-file marker (%%EOF)',
            'reusable': True,
            'formats': ['PDF', 'PostScript'],
            'size': 'fixed_5_bytes'
        }
    }
    
    for name, pattern in new.items():
        if name not in existing['patterns']:
            existing['patterns'][name] = pattern
            print(f"  ➕ {name}")
    
    json.dump(existing, open(patterns_file, 'w'), indent=2)

if __name__ == '__main__':
    import sys
    analysis = PDFAnalyzer(sys.argv[1]).analyze()
    
    grammar = {
        'format': 'PDF',
        'version': '1.0',
        'description': 'Portable Document Format (text+binary mixed)',
        'byte_order': 'n/a',
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {'name': 'header', 'pattern': 'PDF_HEADER'},
                    {'name': 'body', 'pattern': 'SEQUENTIAL_STRUCTURE'},
                    {'name': 'xref', 'pattern': 'XREF_TABLE'},
                    {'name': 'trailer', 'pattern': 'PDF_TRAILER'},
                    {'name': 'eof', 'pattern': 'EOF_MARKER'}
                ]
            }
        }
    }
    
    Path('format_grammars').mkdir(exist_ok=True)
    json.dump(grammar, open('format_grammars/pdf.json', 'w'), indent=2)
    json.dump(analysis, open(f"format_grammars/pdf_analysis_{Path(sys.argv[1]).stem}.json", 'w'), indent=2)
    
    print(f"\n✅ Grammar: format_grammars/pdf.json")
    update_generic_patterns()
    print(f"\n🧩 Patterns: {len(analysis['patterns_found'])}")
    for p in sorted(analysis['patterns_found']):
        print(f"  • {p}")
