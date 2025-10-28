#!/usr/bin/env python3
"""
🔬 PNG Grammar Extractor - PaniniFS POC

Analyse un fichier PNG et identifie les PATTERNS UNIVERSELS réutilisables
pour d'autres formats binaires.

Philosophie PaniniFS:
- Chaque format binaire = composition de patterns atomiques
- Les patterns sont UNIVERSELS et réutilisables
- La grammaire décrit comment composer ces patterns

Patterns universels identifiés dans PNG:
1. MAGIC_NUMBER: Signature de format (8 bytes fixes)
2. LENGTH_PREFIXED_DATA: Taille avant données (4 bytes big-endian)
3. TYPED_CHUNK: Bloc avec type + données + validation
4. CRC_CHECKSUM: Validation d'intégrité (CRC-32)
5. SEQUENTIAL_STRUCTURE: Suite de chunks jusqu'à terminateur
"""

import struct
import zlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict


# ============================================================================
# DÉFINITIONS DES PATTERNS UNIVERSELS
# ============================================================================

@dataclass
class UniversalPattern:
    """Pattern atomique réutilisable pour d'autres formats"""
    name: str
    category: str  # structural, validation, composition
    description: str
    parameters: Dict[str, Any]
    applicable_to: List[str]  # Autres formats où ce pattern apparaît


# Catalogue de patterns universels
UNIVERSAL_PATTERNS = {
    "MAGIC_NUMBER": UniversalPattern(
        name="MAGIC_NUMBER",
        category="structural",
        description="Signature fixe identifiant le format de fichier",
        parameters={
            "size": "variable",
            "position": "file_start",
            "encoding": "bytes"
        },
        applicable_to=["PNG", "JPEG", "GIF", "PDF", "ELF", "ZIP", "GZIP"]
    ),
    
    "LENGTH_PREFIXED_DATA": UniversalPattern(
        name="LENGTH_PREFIXED_DATA",
        category="structural",
        description="Bloc de données précédé de sa taille",
        parameters={
            "length_size": "1-8 bytes",
            "endianness": "big|little",
            "length_includes_self": "boolean"
        },
        applicable_to=["PNG", "IFF", "RIFF", "EBML", "Matroska", "TLV"]
    ),
    
    "TYPED_CHUNK": UniversalPattern(
        name="TYPED_CHUNK",
        category="composition",
        description="Bloc avec type + taille + données + validation",
        parameters={
            "type_size": "usually 4 bytes",
            "type_encoding": "ASCII|binary",
            "has_checksum": "boolean"
        },
        applicable_to=["PNG", "IFF", "RIFF", "WAV", "AVI"]
    ),
    
    "CRC_CHECKSUM": UniversalPattern(
        name="CRC_CHECKSUM",
        category="validation",
        description="Somme de contrôle CRC pour validation d'intégrité",
        parameters={
            "algorithm": "CRC-32|CRC-16|etc",
            "polynomial": "varies",
            "covers": "specified data range"
        },
        applicable_to=["PNG", "ZIP", "GZIP", "Ethernet", "USB"]
    ),
    
    "SEQUENTIAL_STRUCTURE": UniversalPattern(
        name="SEQUENTIAL_STRUCTURE",
        category="composition",
        description="Suite de blocs jusqu'à un terminateur spécifique",
        parameters={
            "block_pattern": "reference to pattern",
            "terminator": "specific value",
            "min_blocks": "integer",
            "max_blocks": "integer|unlimited"
        },
        applicable_to=["PNG", "IFF", "TIFF", "Matroska"]
    )
}


# ============================================================================
# ANALYSEUR PNG
# ============================================================================

class PNGAnalyzer:
    """Analyse un PNG et extrait sa structure en patterns universels"""
    
    # Signature PNG (pattern MAGIC_NUMBER)
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    # Types de chunks critiques vs ancillaires
    CRITICAL_CHUNKS = {'IHDR', 'PLTE', 'IDAT', 'IEND'}
    ANCILLARY_CHUNKS = {'tRNS', 'gAMA', 'cHRM', 'sRGB', 'iCCP', 
                        'tEXt', 'zTXt', 'iTXt', 'bKGD', 'pHYs', 'tIME'}
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.data = filepath.read_bytes()
        self.offset = 0
        self.chunks = []
        self.patterns_used = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyse complète du PNG avec identification des patterns"""
        
        result = {
            "file": str(self.filepath),
            "size": len(self.data),
            "format": "PNG",
            "patterns_detected": [],
            "grammar": {},
            "structure": {}
        }
        
        # 1. Vérifier signature (MAGIC_NUMBER pattern)
        if not self._verify_signature():
            raise ValueError("Invalid PNG signature")
        
        result["patterns_detected"].append({
            "pattern": "MAGIC_NUMBER",
            "offset": 0,
            "size": 8,
            "value": self.PNG_SIGNATURE.hex(),
            "universal_pattern": asdict(UNIVERSAL_PATTERNS["MAGIC_NUMBER"])
        })
        
        # 2. Lire tous les chunks (SEQUENTIAL_STRUCTURE + TYPED_CHUNK patterns)
        while self.offset < len(self.data):
            chunk = self._read_chunk()
            if chunk is None:
                break
            self.chunks.append(chunk)
        
        # 3. Documenter la structure en patterns universels
        result["structure"] = {
            "signature": {
                "pattern": "MAGIC_NUMBER",
                "bytes": self.PNG_SIGNATURE.hex(),
                "size": 8
            },
            "body": {
                "pattern": "SEQUENTIAL_STRUCTURE",
                "terminator": "IEND chunk",
                "chunks": self.chunks
            }
        }
        
        # 4. Générer la grammaire PNG en termes de patterns universels
        result["grammar"] = self._generate_grammar()
        
        # 5. Statistiques sur les patterns
        result["patterns_detected"].extend(self._analyze_patterns())
        
        return result
    
    def _verify_signature(self) -> bool:
        """Vérifie la signature PNG (MAGIC_NUMBER pattern)"""
        signature = self.data[:8]
        self.offset = 8
        return signature == self.PNG_SIGNATURE
    
    def _read_chunk(self) -> Dict[str, Any]:
        """
        Lit un chunk PNG (TYPED_CHUNK pattern)
        
        Structure d'un chunk PNG:
        - Length: 4 bytes (LENGTH_PREFIXED_DATA pattern)
        - Type: 4 bytes ASCII (TYPED_CHUNK pattern)
        - Data: Length bytes
        - CRC: 4 bytes (CRC_CHECKSUM pattern)
        """
        if self.offset >= len(self.data):
            return None
        
        try:
            # Lire la taille (LENGTH_PREFIXED_DATA)
            length = struct.unpack('>I', self.data[self.offset:self.offset+4])[0]
            self.offset += 4
            
            # Lire le type (TYPED_CHUNK)
            chunk_type = self.data[self.offset:self.offset+4].decode('ascii')
            self.offset += 4
            
            # Lire les données
            chunk_data = self.data[self.offset:self.offset+length]
            self.offset += length
            
            # Lire le CRC (CRC_CHECKSUM pattern)
            crc_stored = struct.unpack('>I', self.data[self.offset:self.offset+4])[0]
            self.offset += 4
            
            # Calculer et vérifier le CRC
            crc_data = self.data[self.offset-length-8:self.offset-4]
            crc_calculated = zlib.crc32(crc_data)
            crc_valid = (crc_stored == crc_calculated)
            
            chunk_info = {
                "type": chunk_type,
                "length": length,
                "offset": self.offset - length - 12,
                "data_hex": chunk_data[:32].hex() + ("..." if length > 32 else ""),
                "crc_stored": f"{crc_stored:08x}",
                "crc_calculated": f"{crc_calculated:08x}",
                "crc_valid": crc_valid,
                "critical": chunk_type in self.CRITICAL_CHUNKS,
                "patterns": [
                    {"name": "LENGTH_PREFIXED_DATA", "field": "length"},
                    {"name": "TYPED_CHUNK", "field": "type+data"},
                    {"name": "CRC_CHECKSUM", "field": "crc"}
                ]
            }
            
            # Interpréter les chunks critiques
            if chunk_type == 'IHDR':
                chunk_info["interpretation"] = self._parse_ihdr(chunk_data)
            elif chunk_type == 'IEND':
                chunk_info["interpretation"] = "End of PNG datastream"
            
            return chunk_info
            
        except Exception as e:
            print(f"Error reading chunk at offset {self.offset}: {e}")
            return None
    
    def _parse_ihdr(self, data: bytes) -> Dict[str, Any]:
        """Parse le chunk IHDR (Image Header)"""
        width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack('>IIBBBBB', data)
        
        color_types = {
            0: "Grayscale",
            2: "Truecolor",
            3: "Indexed",
            4: "Grayscale with alpha",
            6: "Truecolor with alpha"
        }
        
        return {
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_types.get(color_type, f"Unknown ({color_type})"),
            "compression": compression,
            "filter": filter_method,
            "interlace": interlace
        }
    
    def _generate_grammar(self) -> Dict[str, Any]:
        """
        Génère la grammaire PNG en termes de patterns universels
        
        Cette grammaire peut être réutilisée pour générer des parsers
        pour d'autres formats avec des patterns similaires
        """
        return {
            "format": "PNG",
            "version": "ISO/IEC 15948:2004",
            "composition": {
                "root": {
                    "pattern": "SEQUENTIAL",
                    "elements": [
                        {
                            "name": "signature",
                            "pattern": "MAGIC_NUMBER",
                            "value": self.PNG_SIGNATURE.hex(),
                            "size": 8,
                            "required": True
                        },
                        {
                            "name": "chunks",
                            "pattern": "SEQUENTIAL_STRUCTURE",
                            "element": {
                                "pattern": "TYPED_CHUNK",
                                "structure": [
                                    {
                                        "name": "length",
                                        "pattern": "LENGTH_PREFIXED_DATA",
                                        "size": 4,
                                        "endianness": "big",
                                        "type": "uint32"
                                    },
                                    {
                                        "name": "type",
                                        "size": 4,
                                        "encoding": "ASCII",
                                        "constraint": "^[A-Za-z]{4}$"
                                    },
                                    {
                                        "name": "data",
                                        "size": "from_length",
                                        "encoding": "bytes"
                                    },
                                    {
                                        "name": "crc",
                                        "pattern": "CRC_CHECKSUM",
                                        "size": 4,
                                        "algorithm": "CRC-32",
                                        "covers": ["type", "data"]
                                    }
                                ]
                            },
                            "terminator": {
                                "field": "type",
                                "value": "IEND"
                            }
                        }
                    ]
                }
            },
            "constraints": {
                "chunk_order": [
                    {"type": "IHDR", "position": "first", "required": True},
                    {"type": "PLTE", "before": "IDAT", "required": "if color_type=3"},
                    {"type": "IDAT", "multiple": True, "required": True},
                    {"type": "IEND", "position": "last", "required": True}
                ]
            },
            "patterns_used": list(UNIVERSAL_PATTERNS.keys())
        }
    
    def _analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyse et compte les patterns utilisés"""
        pattern_stats = {}
        
        for chunk in self.chunks:
            for pattern_ref in chunk.get("patterns", []):
                pattern_name = pattern_ref["name"]
                if pattern_name not in pattern_stats:
                    pattern_stats[pattern_name] = {
                        "pattern": pattern_name,
                        "count": 0,
                        "universal": asdict(UNIVERSAL_PATTERNS[pattern_name])
                    }
                pattern_stats[pattern_name]["count"] += 1
        
        return list(pattern_stats.values())


# ============================================================================
# EXPORTATION GRAMMAIRE RÉUTILISABLE
# ============================================================================

def export_universal_patterns(output_path: Path):
    """Exporte le catalogue de patterns universels en JSON"""
    patterns_export = {
        "version": "1.0.0",
        "description": "Universal patterns for binary format decomposition (PaniniFS)",
        "patterns": {
            name: asdict(pattern)
            for name, pattern in UNIVERSAL_PATTERNS.items()
        }
    }
    
    output_path.write_text(json.dumps(patterns_export, indent=2))
    print(f"✅ Universal patterns exported to {output_path}")


def export_png_grammar(grammar: Dict[str, Any], output_path: Path):
    """Exporte la grammaire PNG pour réutilisation"""
    grammar_export = {
        "version": "1.0.0",
        "description": "PNG format grammar using universal patterns (PaniniFS)",
        "grammar": grammar,
        "usage": {
            "decomposer": "Use this grammar with generic_decomposer.py",
            "reconstructor": "Use this grammar with generic_reconstructor.py",
            "validator": "Validate PNG files against this grammar"
        }
    }
    
    output_path.write_text(json.dumps(grammar_export, indent=2))
    print(f"✅ PNG grammar exported to {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python png_grammar_extractor.py <png_file>")
        print("\nExtracts universal patterns from PNG files for PaniniFS")
        sys.exit(1)
    
    png_file = Path(sys.argv[1])
    
    if not png_file.exists():
        print(f"❌ File not found: {png_file}")
        sys.exit(1)
    
    print(f"\n🔬 Analyzing PNG: {png_file}")
    print("=" * 70)
    
    # Analyser le PNG
    analyzer = PNGAnalyzer(png_file)
    result = analyzer.analyze()
    
    # Afficher les résultats
    print(f"\n📊 File: {result['file']}")
    print(f"   Size: {result['size']} bytes")
    print(f"   Format: {result['format']}")
    
    print(f"\n🧩 Chunks detected: {len(result['structure']['body']['chunks'])}")
    for chunk in result['structure']['body']['chunks']:
        status = "✓" if chunk['crc_valid'] else "✗"
        critical = "🔴" if chunk['critical'] else "⚪"
        print(f"   {status} {critical} {chunk['type']:8s} - {chunk['length']:6d} bytes at offset {chunk['offset']}")
        if 'interpretation' in chunk:
            if isinstance(chunk['interpretation'], dict):
                for key, value in chunk['interpretation'].items():
                    print(f"      {key}: {value}")
    
    print(f"\n🎯 Universal Patterns Detected:")
    for pattern in result['patterns_detected']:
        if isinstance(pattern, dict) and 'pattern' in pattern:
            if 'count' in pattern:
                print(f"   • {pattern['pattern']}: used {pattern['count']} times")
            else:
                print(f"   • {pattern['pattern']}: at offset {pattern.get('offset', 'N/A')}")
    
    # Créer les dossiers de sortie
    output_dir = Path("format_grammars")
    output_dir.mkdir(exist_ok=True)
    
    # Exporter les patterns universels
    patterns_file = output_dir / "generic_patterns.json"
    export_universal_patterns(patterns_file)
    
    # Exporter la grammaire PNG
    grammar_file = output_dir / "png.json"
    export_png_grammar(result['grammar'], grammar_file)
    
    # Exporter l'analyse complète
    analysis_file = output_dir / f"png_analysis_{png_file.stem}.json"
    analysis_file.write_text(json.dumps(result, indent=2))
    print(f"✅ Full analysis exported to {analysis_file}")
    
    print(f"\n✨ Analysis complete!")
    print(f"   → Universal patterns: {patterns_file}")
    print(f"   → PNG grammar: {grammar_file}")
    print(f"   → Full analysis: {analysis_file}")
    print(f"\n💡 Next step: Use these grammars with generic_decomposer.py")


if __name__ == "__main__":
    main()
