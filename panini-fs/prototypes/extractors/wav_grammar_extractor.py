#!/usr/bin/env python3
"""WAV Grammar Extractor - PaniniFS (80% RIFF reuse from WebP)"""
import json, struct
from pathlib import Path

class WAVAnalyzer:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.data = self.filepath.read_bytes()
        self.size = len(self.data)
        self.offset = 0
        self.chunks = []
        self.patterns = set()
    
    def read_bytes(self, n):
        data = self.data[self.offset:self.offset+n]
        self.offset += n
        return data
    
    def read_fourcc(self):
        return self.read_bytes(4).decode('ascii', errors='ignore')
    
    def read_u32_le(self):
        return struct.unpack('<I', self.read_bytes(4))[0]
    
    def read_u16_le(self):
        return struct.unpack('<H', self.read_bytes(2))[0]
    
    def analyze(self):
        print(f"\n🎵 Analysing WAV: {self.filepath.name} ({self.size} bytes)")
        
        # RIFF header (reuse WebP patterns)
        sig = self.read_fourcc()
        assert sig == 'RIFF'
        self.patterns.add('MAGIC_NUMBER')
        self.patterns.add('RIFF_HEADER')
        
        file_size = self.read_u32_le()
        form_type = self.read_fourcc()
        assert form_type == 'WAVE'
        self.patterns.add('RIFF_FORM_TYPE')
        
        print(f"RIFF/WAVE, size: {file_size+8} bytes")
        
        # Read chunks
        while self.offset < self.size:
            if self.offset + 8 > self.size:
                break
            
            fourcc = self.read_fourcc()
            chunk_size = self.read_u32_le()
            
            chunk_data = self.read_bytes(min(chunk_size, self.size - self.offset))
            
            self.patterns.add('RIFF_CHUNK')
            
            chunk_info = {'fourcc': fourcc, 'size': chunk_size}
            
            if fourcc == 'fmt ':
                fmt = struct.unpack('<HHIIHH', chunk_data[:16])
                chunk_info.update({
                    'audio_format': fmt[0],
                    'channels': fmt[1],
                    'sample_rate': fmt[2],
                    'bits_per_sample': fmt[5]
                })
                self.patterns.add('FMT_CHUNK')
                print(f"  fmt: {fmt[1]}ch, {fmt[2]}Hz, {fmt[5]}bit")
            elif fourcc == 'data':
                self.patterns.add('DATA_CHUNK')
                print(f"  data: {chunk_size} bytes audio")
            else:
                print(f"  {fourcc}: {chunk_size} bytes")
            
            self.chunks.append(chunk_info)
            
            if chunk_size % 2 == 1 and self.offset < self.size:
                self.read_bytes(1)
                self.patterns.add('PADDING_ALIGNMENT')
        
        return {
            'file': str(self.filepath),
            'size': self.size,
            'format': 'WAV',
            'chunks': self.chunks,
            'patterns_found': sorted(list(self.patterns))
        }

def generate_grammar(analysis):
    return {
        'format': 'WAV',
        'version': '1.0',
        'description': 'Waveform Audio File Format (RIFF-based)',
        'byte_order': 'little-endian',
        'composition': {
            'root': {
                'pattern': 'SEQUENTIAL',
                'elements': [
                    {'name': 'riff_header', 'pattern': 'RIFF_HEADER'},
                    {
                        'name': 'chunks',
                        'pattern': 'SEQUENTIAL_STRUCTURE',
                        'element': {'pattern': 'RIFF_CHUNK'},
                        'terminator': {'type': 'eof'}
                    }
                ]
            }
        }
    }

def update_generic_patterns(patterns):
    patterns_file = Path('format_grammars/generic_patterns.json')
    existing = json.load(open(patterns_file, 'r')) if patterns_file.exists() else {'patterns': {}}
    
    new_patterns = {
        'FMT_CHUNK': {
            'name': 'FMT_CHUNK',
            'description': 'WAV format chunk (audio parameters)',
            'reusable': False,
            'formats': ['WAV'],
            'size': '16_or_18_bytes'
        },
        'DATA_CHUNK': {
            'name': 'DATA_CHUNK',
            'description': 'WAV data chunk (raw PCM audio samples)',
            'reusable': False,
            'formats': ['WAV'],
            'size': 'variable'
        }
    }
    
    for name, pattern in new_patterns.items():
        if name not in existing['patterns']:
            existing['patterns'][name] = pattern
            print(f"  ➕ {name}")
    
    json.dump(existing, open(patterns_file, 'w'), indent=2)
    print(f"✅ Updated patterns")

if __name__ == '__main__':
    import sys
    analyzer = WAVAnalyzer(sys.argv[1])
    analysis = analyzer.analyze()
    
    grammar = generate_grammar(analysis)
    
    out_dir = Path('format_grammars')
    out_dir.mkdir(exist_ok=True)
    
    json.dump(grammar, open(out_dir / 'wav.json', 'w'), indent=2)
    json.dump(analysis, open(out_dir / f"wav_analysis_{Path(sys.argv[1]).stem}.json", 'w'), indent=2)
    
    print(f"\n✅ Grammar: format_grammars/wav.json")
    update_generic_patterns(analysis['patterns_found'])
    print(f"\n🧩 Patterns: {len(analysis['patterns_found'])}")
    for p in sorted(analysis['patterns_found']):
        print(f"  • {p}")
