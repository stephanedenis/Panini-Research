#!/usr/bin/env python3
"""
📸 JPEG Grammar Extractor

Analyse les fichiers JPEG pour identifier patterns universels
et générer une grammaire réutilisable.

JPEG Structure:
- SOI (Start of Image): FF D8
- Segments: Marker (FF XX) + Length (2 bytes) + Data
- SOF (Start of Frame): Dimensions, composantes
- DHT (Huffman Tables): Compression tables
- DQT (Quantization Tables): Quantization matrices
- SOS (Start of Scan): Compressed image data
- EOI (End of Image): FF D9

Universal Patterns identifiés:
1. MAGIC_NUMBER: FF D8 (SOI)
2. SEGMENT_STRUCTURE: Marker + Length + Data
3. SEQUENTIAL_SEGMENTS: Chaîne de segments
4. TERMINATOR: FF D9 (EOI)
"""

import struct
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


# JPEG Markers
MARKERS = {
    0xFFD8: "SOI",   # Start of Image
    0xFFD9: "EOI",   # End of Image  
    0xFFC0: "SOF0",  # Start of Frame (Baseline DCT)
    0xFFC1: "SOF1",  # Start of Frame (Extended Sequential DCT)
    0xFFC2: "SOF2",  # Start of Frame (Progressive DCT)
    0xFFC4: "DHT",   # Define Huffman Table
    0xFFDB: "DQT",   # Define Quantization Table
    0xFFDD: "DRI",   # Define Restart Interval
    0xFFDA: "SOS",   # Start of Scan
    0xFFE0: "APP0",  # Application-specific (JFIF)
    0xFFE1: "APP1",  # Application-specific (EXIF)
    0xFFE2: "APP2",  # Application-specific (ICC)
    0xFFFE: "COM",   # Comment
}


@dataclass
class Segment:
    """Représentation d'un segment JPEG"""
    marker: int
    marker_name: str
    offset: int
    length: Optional[int]  # None pour SOI/EOI
    data_offset: Optional[int]
    data: Optional[bytes]


class JPEGAnalyzer:
    """Analyse les fichiers JPEG pour extraction de grammaire"""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.data = filepath.read_bytes()
        self.segments: List[Segment] = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyse complète du JPEG"""
        print(f"\n📸 Analysing JPEG: {self.filepath.name}")
        print(f"   Size: {len(self.data)} bytes")
        
        # Parse segments
        self._parse_segments()
        
        # Generate universal patterns
        patterns = self._identify_universal_patterns()
        
        # Generate JPEG grammar
        grammar = self._generate_grammar()
        
        # Statistics
        stats = {
            "file_size": len(self.data),
            "segment_count": len(self.segments),
            "segments_by_type": self._count_segments_by_type(),
            "universal_patterns_used": list(patterns.keys())
        }
        
        return {
            "analysis": {
                "file": self.filepath.name,
                "timestamp": datetime.now().isoformat(),
                **stats
            },
            "segments": [self._segment_to_dict(seg) for seg in self.segments],
            "universal_patterns": patterns,
            "grammar": grammar
        }
    
    def _parse_segments(self):
        """Parse tous les segments JPEG"""
        offset = 0
        
        while offset < len(self.data):
            # Recherche du prochain marker (FF XX)
            if self.data[offset] != 0xFF:
                offset += 1
                continue
            
            if offset + 1 >= len(self.data):
                break
            
            marker = struct.unpack('>H', self.data[offset:offset+2])[0]
            marker_name = MARKERS.get(marker, f"UNKNOWN_{marker:04X}")
            
            # SOI et EOI n'ont pas de longueur/data
            if marker in [0xFFD8, 0xFFD9]:
                segment = Segment(
                    marker=marker,
                    marker_name=marker_name,
                    offset=offset,
                    length=None,
                    data_offset=None,
                    data=None
                )
                self.segments.append(segment)
                offset += 2
                
                # EOI = fin du fichier
                if marker == 0xFFD9:
                    break
                continue
            
            # SOS : data jusqu'au prochain marker ou EOI
            if marker == 0xFFDA:
                # Longueur du header SOS
                length = struct.unpack('>H', self.data[offset+2:offset+4])[0]
                data_start = offset + 2 + length
                
                # Recherche de EOI
                eoi_offset = self.data.find(b'\xFF\xD9', data_start)
                if eoi_offset == -1:
                    data_length = len(self.data) - data_start
                else:
                    data_length = eoi_offset - data_start
                
                segment = Segment(
                    marker=marker,
                    marker_name=marker_name,
                    offset=offset,
                    length=length + data_length,
                    data_offset=data_start,
                    data=self.data[data_start:data_start+data_length]
                )
                self.segments.append(segment)
                offset = data_start + data_length
                continue
            
            # Segments normaux : Marker + Length + Data
            if offset + 4 > len(self.data):
                break
            
            length = struct.unpack('>H', self.data[offset+2:offset+4])[0]
            data_offset = offset + 4
            data_end = data_offset + length - 2  # length inclut les 2 bytes de length
            
            if data_end > len(self.data):
                break
            
            segment = Segment(
                marker=marker,
                marker_name=marker_name,
                offset=offset,
                length=length,
                data_offset=data_offset,
                data=self.data[data_offset:data_end]
            )
            self.segments.append(segment)
            offset = data_end
        
        print(f"   ✓ Found {len(self.segments)} segments")
        for seg in self.segments:
            if seg.length is None:
                print(f"     - {seg.marker_name} at offset {seg.offset}")
            else:
                print(f"     - {seg.marker_name} at offset {seg.offset}, length {seg.length}")
    
    def _identify_universal_patterns(self) -> Dict[str, Any]:
        """Identifie les patterns universels dans JPEG"""
        return {
            "MAGIC_NUMBER": {
                "category": "structural",
                "description": "File signature marker (SOI)",
                "jpeg_usage": "FF D8 marker at file start",
                "validation": "Always FF D8",
                "applicable_to": ["JPEG", "JFIF", "EXIF", "Motion JPEG"]
            },
            "SEGMENT_STRUCTURE": {
                "category": "composition",
                "description": "Marker + Length + Data pattern",
                "jpeg_usage": "Most JPEG segments follow this structure",
                "components": {
                    "marker": "2 bytes (FF XX)",
                    "length": "2 bytes big-endian (includes length field)",
                    "data": "Variable length payload"
                },
                "exceptions": "SOI/EOI have no length/data",
                "applicable_to": ["JPEG", "TIFF", "RIFF chunks"]
            },
            "SEQUENTIAL_SEGMENTS": {
                "category": "composition",
                "description": "Sequential chain of segments",
                "jpeg_usage": "File is sequence of segments from SOI to EOI",
                "terminator": "EOI marker (FF D9)",
                "applicable_to": ["JPEG", "PNG chunks", "IFF chunks"]
            },
            "TERMINATOR": {
                "category": "structural",
                "description": "End-of-file marker",
                "jpeg_usage": "EOI (FF D9) marks end of image",
                "validation": "Must be last bytes",
                "applicable_to": ["JPEG", "Some RIFF variants"]
            },
            "BIG_ENDIAN_LENGTH": {
                "category": "structural",
                "description": "Length encoded as big-endian 16-bit integer",
                "jpeg_usage": "All segment lengths in JPEG",
                "note": "Includes the 2 bytes of length field itself",
                "applicable_to": ["JPEG", "Some network protocols", "Some binary formats"]
            }
        }
    
    def _generate_grammar(self) -> Dict[str, Any]:
        """Génère la grammaire JPEG en patterns universels"""
        return {
            "format": "JPEG",
            "version": "1.0",
            "composition": {
                "root": {
                    "pattern": "SEQUENTIAL_SEGMENTS",
                    "start_marker": {
                        "pattern": "MAGIC_NUMBER",
                        "value": "FFD8"
                    },
                    "segments": {
                        "pattern": "SEGMENT_STRUCTURE",
                        "repeatable": True,
                        "components": {
                            "marker": {
                                "type": "bytes",
                                "length": 2,
                                "format": "big_endian",
                                "constraint": "First byte must be FF"
                            },
                            "length": {
                                "type": "integer",
                                "size": 2,
                                "format": "big_endian",
                                "note": "Includes own 2 bytes"
                            },
                            "data": {
                                "type": "bytes",
                                "length_ref": "length - 2"
                            }
                        },
                        "exceptions": {
                            "SOI": "marker only, no length/data",
                            "EOI": "marker only, no length/data",
                            "SOS": "header + compressed data until EOI"
                        }
                    },
                    "end_marker": {
                        "pattern": "TERMINATOR",
                        "value": "FFD9"
                    }
                }
            },
            "segment_types": {
                marker_name: f"{marker:04X}"
                for marker, marker_name in MARKERS.items()
            }
        }
    
    def _segment_to_dict(self, segment: Segment) -> Dict[str, Any]:
        """Convertit un segment en dict pour JSON"""
        result = {
            "marker": f"{segment.marker:04X}",
            "marker_name": segment.marker_name,
            "offset": segment.offset,
        }
        
        if segment.length is not None:
            result["length"] = segment.length
        
        if segment.data is not None:
            # Tronquer data pour lisibilité
            if len(segment.data) > 64:
                result["data_preview"] = segment.data[:64].hex()
                result["data_length"] = len(segment.data)
            else:
                result["data"] = segment.data.hex()
        
        return result
    
    def _count_segments_by_type(self) -> Dict[str, int]:
        """Compte les segments par type"""
        counts = {}
        for seg in self.segments:
            counts[seg.marker_name] = counts.get(seg.marker_name, 0) + 1
        return counts


def main():
    """Point d'entrée principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: jpeg_grammar_extractor.py <jpeg_file>")
        sys.exit(1)
    
    jpeg_file = Path(sys.argv[1])
    
    if not jpeg_file.exists():
        print(f"❌ File not found: {jpeg_file}")
        sys.exit(1)
    
    # Analyse
    analyzer = JPEGAnalyzer(jpeg_file)
    results = analyzer.analyze()
    
    # Save outputs
    output_dir = Path("format_grammars")
    output_dir.mkdir(exist_ok=True)
    
    # Update generic patterns (merge with existing)
    patterns_file = output_dir / "generic_patterns.json"
    if patterns_file.exists():
        existing = json.loads(patterns_file.read_text())
        existing.update(results["universal_patterns"])
        patterns_file.write_text(json.dumps(existing, indent=2))
    else:
        patterns_file.write_text(json.dumps(results["universal_patterns"], indent=2))
    
    # JPEG grammar
    grammar_file = output_dir / "jpeg.json"
    grammar_file.write_text(json.dumps(results["grammar"], indent=2))
    
    # Full analysis
    analysis_file = output_dir / f"jpeg_analysis_{jpeg_file.stem}.json"
    analysis_file.write_text(json.dumps(results, indent=2))
    
    print(f"\n✅ Analysis complete:")
    print(f"   📝 Generic patterns: {patterns_file}")
    print(f"   📝 JPEG grammar: {grammar_file}")
    print(f"   📝 Full analysis: {analysis_file}")
    print(f"\n📊 Statistics:")
    print(f"   Segments: {results['analysis']['segment_count']}")
    for seg_type, count in results['analysis']['segments_by_type'].items():
        print(f"     - {seg_type}: {count}")


if __name__ == "__main__":
    main()
