#!/usr/bin/env python3
"""
🔬 Generic Binary Decomposer - PaniniFS Core Engine

Moteur générique de décomposition basé sur grammaires universelles.
Lit n'importe quelle grammaire JSON et applique les patterns récursivement.

Philosophie:
- UN SEUL moteur pour TOUS les formats
- La grammaire décrit COMMENT décomposer
- Les patterns sont RÉUTILISABLES entre formats
- Décomposition RÉCURSIVE et HIÉRARCHIQUE

Usage:
    python generic_decomposer.py <binary_file> <grammar_file>
    
Example:
    python generic_decomposer.py test.png format_grammars/png.json
"""

import struct
import zlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


# ============================================================================
# PATTERN PROCESSORS - Handlers pour chaque type de pattern universel
# ============================================================================

class PatternProcessor:
    """Classe de base pour traiter un pattern universel"""
    
    def __init__(self, data: bytes, offset: int):
        self.data = data
        self.offset = offset
        self.size = len(data)
    
    def read_bytes(self, count: int) -> bytes:
        """Lit N bytes à l'offset courant"""
        if self.offset + count > self.size:
            raise ValueError(f"Cannot read {count} bytes at offset {self.offset} (file size: {self.size})")
        result = self.data[self.offset:self.offset + count]
        self.offset += count
        return result
    
    def peek_bytes(self, count: int) -> bytes:
        """Regarde N bytes sans avancer l'offset"""
        if self.offset + count > self.size:
            return b''
        return self.data[self.offset:self.offset + count]


class MagicNumberProcessor(PatternProcessor):
    """Traite le pattern MAGIC_NUMBER"""
    
    def process(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        size = spec.get('size', 8)
        expected = bytes.fromhex(spec.get('value', ''))
        
        magic = self.read_bytes(size)
        
        return {
            "pattern": "MAGIC_NUMBER",
            "offset": self.offset - size,
            "size": size,
            "value": magic.hex(),
            "expected": expected.hex(),
            "valid": magic == expected,
            "interpretation": spec.get('name', 'signature')
        }


class LengthPrefixedDataProcessor(PatternProcessor):
    """Traite le pattern LENGTH_PREFIXED_DATA"""
    
    def process(self, spec: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        length_size = spec.get('size', 4)
        endianness = spec.get('endianness', 'big')
        type_name = spec.get('type', 'uint32')
        
        # Lire la taille
        length_bytes = self.read_bytes(length_size)
        
        if type_name == 'uint32':
            if endianness == 'big':
                length = struct.unpack('>I', length_bytes)[0]
            else:
                length = struct.unpack('<I', length_bytes)[0]
        elif type_name == 'uint16':
            if endianness == 'big':
                length = struct.unpack('>H', length_bytes)[0]
            else:
                length = struct.unpack('<H', length_bytes)[0]
        else:
            raise ValueError(f"Unsupported type: {type_name}")
        
        result = {
            "pattern": "LENGTH_PREFIXED_DATA",
            "offset": self.offset - length_size,
            "size": length_size,
            "length_value": length,
            "endianness": endianness,
            "field": spec.get('name', 'length')
        }
        
        return length, result


class CRCChecksumProcessor(PatternProcessor):
    """Traite le pattern CRC_CHECKSUM"""
    
    def process(self, spec: Dict[str, Any], data_to_check: bytes) -> Dict[str, Any]:
        algorithm = spec.get('algorithm', 'CRC-32')
        crc_size = spec.get('size', 4)
        
        # Lire le CRC stocké
        crc_bytes = self.read_bytes(crc_size)
        crc_stored = struct.unpack('>I', crc_bytes)[0]
        
        # Calculer le CRC sur les données spécifiées
        if algorithm == 'CRC-32':
            crc_calculated = zlib.crc32(data_to_check)
        else:
            raise ValueError(f"Unsupported CRC algorithm: {algorithm}")
        
        return {
            "pattern": "CRC_CHECKSUM",
            "offset": self.offset - crc_size,
            "size": crc_size,
            "algorithm": algorithm,
            "stored": f"{crc_stored:08x}",
            "calculated": f"{crc_calculated:08x}",
            "valid": crc_stored == crc_calculated,
            "field": spec.get('name', 'crc')
        }


class TypedChunkProcessor(PatternProcessor):
    """Traite le pattern TYPED_CHUNK"""
    
    def process(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Décompose un chunk typé selon sa structure"""
        
        if self.offset >= self.size:
            return None
        
        chunk_start = self.offset
        structure = spec.get('structure', [])
        chunk_data = {}
        
        length = None
        chunk_type = None
        data_field = None
        
        # Traiter chaque élément de la structure
        for element in structure:
            element_name = element.get('name')
            pattern = element.get('pattern')
            
            if pattern == 'LENGTH_PREFIXED_DATA':
                # Lire la taille
                processor = LengthPrefixedDataProcessor(self.data, self.offset)
                length, length_info = processor.process(element)
                self.offset = processor.offset
                chunk_data['length'] = length_info
                
            elif element_name == 'type':
                # Lire le type (ASCII)
                type_size = element.get('size', 4)
                type_bytes = self.read_bytes(type_size)
                chunk_type = type_bytes.decode('ascii')
                chunk_data['type'] = {
                    "pattern": "TYPE_FIELD",
                    "offset": self.offset - type_size,
                    "size": type_size,
                    "value": chunk_type,
                    "encoding": element.get('encoding', 'ASCII')
                }
                
            elif element_name == 'data':
                # Lire les données
                if length is None:
                    raise ValueError("Data field requires length to be read first")
                data_start = self.offset
                data_bytes = self.read_bytes(length)
                data_field = self.data[chunk_start + 4:chunk_start + 4 + 4 + length]  # type + data pour CRC
                chunk_data['data'] = {
                    "pattern": "DATA_FIELD",
                    "offset": data_start,
                    "size": length,
                    "full_data": data_bytes.hex(),  # TOUTES les données
                    "preview": data_bytes[:32].hex() + ("..." if length > 32 else "")
                }
                
            elif pattern == 'CRC_CHECKSUM':
                # Calculer et vérifier le CRC
                if data_field is None:
                    raise ValueError("CRC requires data field to be read first")
                processor = CRCChecksumProcessor(self.data, self.offset)
                crc_info = processor.process(element, data_field)
                self.offset = processor.offset
                chunk_data['crc'] = crc_info
        
        return {
            "pattern": "TYPED_CHUNK",
            "offset": chunk_start,
            "size": self.offset - chunk_start,
            "type": chunk_type,
            "structure": chunk_data
        }


class SegmentStructureProcessor(PatternProcessor):
    """Traite le pattern SEGMENT_STRUCTURE (JPEG, MPEG, etc.)"""
    
    def process(self, marker: bytes) -> Optional[Dict[str, Any]]:
        """Décompose un segment type JPEG: Marker (2B) + Length (2B BE) + Data"""
        
        if self.offset >= self.size:
            return None
        
        segment_start = self.offset - 2  # Marker déjà lu
        
        # Markers spéciaux sans length/data
        if marker in [b'\xFF\xD8', b'\xFF\xD9']:  # SOI, EOI
            return {
                "pattern": "SEGMENT_STRUCTURE",
                "offset": segment_start,
                "size": 2,
                "marker": marker.hex().upper(),
                "marker_type": self._marker_name(marker),
                "has_data": False
            }
        
        # SOS : cas spécial avec données compressées jusqu'à EOI
        if marker == b'\xFF\xDA':  # SOS
            # Lire la longueur du header SOS
            length_bytes = self.read_bytes(2)
            header_length = struct.unpack('>H', length_bytes)[0]
            header_data = self.read_bytes(header_length - 2)
            
            # Les données compressées vont jusqu'au prochain marker (EOI)
            compressed_start = self.offset
            compressed_data = []
            
            while self.offset < self.size - 1:
                byte = self.data[self.offset]
                next_byte = self.data[self.offset + 1]
                
                # Détecter le marker FF D9 (EOI)
                if byte == 0xFF and next_byte == 0xD9:
                    break
                
                compressed_data.append(byte)
                self.offset += 1
            
            compressed_bytes = bytes(compressed_data)
            
            return {
                "pattern": "SEGMENT_STRUCTURE",
                "offset": segment_start,
                "size": 2 + 2 + header_length - 2 + len(compressed_bytes),
                "marker": marker.hex().upper(),
                "marker_type": "SOS",
                "header_length": header_length,
                "header_data": header_data.hex(),
                "compressed_data": {
                    "offset": compressed_start,
                    "size": len(compressed_bytes),
                    "full_data": compressed_bytes.hex(),
                    "preview": compressed_bytes[:32].hex() + ("..." if len(compressed_bytes) > 32 else "")
                },
                "has_data": True
            }
        
        # Lire la longueur (16-bit big-endian)
        length_bytes = self.read_bytes(2)
        length = struct.unpack('>H', length_bytes)[0]  # Inclut les 2 bytes de longueur
        data_length = length - 2
        
        # Lire les données
        data_start = self.offset
        data_bytes = self.read_bytes(data_length) if data_length > 0 else b''
        
        return {
            "pattern": "SEGMENT_STRUCTURE",
            "offset": segment_start,
            "size": 2 + 2 + data_length,
            "marker": marker.hex().upper(),
            "marker_type": self._marker_name(marker),
            "length": {
                "value": length,
                "format": "big_endian_16bit",
                "includes_self": True
            },
            "data": {
                "offset": data_start,
                "size": data_length,
                "full_data": data_bytes.hex(),
                "preview": data_bytes[:32].hex() + ("..." if data_length > 32 else "")
            },
            "has_data": True
        }
    
    def _marker_name(self, marker: bytes) -> str:
        """Retourne le nom du marker JPEG"""
        markers = {
            b'\xFF\xD8': 'SOI',
            b'\xFF\xD9': 'EOI',
            b'\xFF\xC0': 'SOF0',
            b'\xFF\xC4': 'DHT',
            b'\xFF\xDB': 'DQT',
            b'\xFF\xDA': 'SOS',
            b'\xFF\xE0': 'APP0',
            b'\xFF\xE1': 'APP1',
            b'\xFF\xE2': 'APP2',
            b'\xFF\xFE': 'COM'
        }
        return markers.get(marker, f'UNKNOWN_{marker.hex().upper()}')


# ============================================================================
# GENERIC DECOMPOSER ENGINE
# ============================================================================

class GenericDecomposer:
    """
    Moteur générique de décomposition basé sur grammaires.
    Fonctionne pour N'IMPORTE QUEL format avec une grammaire définie.
    """
    
    def __init__(self, binary_file: Path, grammar_file: Path):
        self.binary_file = binary_file
        self.binary_data = binary_file.read_bytes()
        
        # Charger la grammaire
        grammar_content = json.loads(grammar_file.read_text())
        self.grammar = grammar_content.get('grammar', grammar_content)
        
        # Charger les patterns universels si disponibles
        patterns_file = grammar_file.parent / 'generic_patterns.json'
        if patterns_file.exists():
            patterns_content = json.loads(patterns_file.read_text())
            self.universal_patterns = patterns_content.get('patterns', {})
        else:
            self.universal_patterns = {}
        
        self.offset = 0
        self.decomposition = {
            "source_file": str(binary_file),
            "file_size": len(self.binary_data),
            "format": self.grammar.get('format', 'Unknown'),
            "grammar_version": self.grammar.get('version', 'Unknown'),
            "elements": []
        }
    
    def decompose(self) -> Dict[str, Any]:
        """Décompose le fichier binaire selon sa grammaire"""
        
        composition = self.grammar.get('composition', {})
        root = composition.get('root', {})
        
        if root.get('pattern') == 'SEQUENTIAL':
            elements = root.get('elements', [])
            
            for element_spec in elements:
                element_result = self._process_element(element_spec)
                if element_result:
                    self.decomposition['elements'].append(element_result)
        
        elif root.get('pattern') == 'SEQUENTIAL_SEGMENTS':
            # Format type JPEG: SOI + segments + EOI
            result = self._process_sequential_segments(root)
            if result:
                self.decomposition['elements'] = result
        
        return self.decomposition
    
    def _process_element(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Traite un élément selon son pattern"""
        
        pattern = spec.get('pattern')
        name = spec.get('name', 'unnamed')
        
        if pattern == 'MAGIC_NUMBER':
            processor = MagicNumberProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'SEQUENTIAL_STRUCTURE':
            # Structure séquentielle (ex: chunks PNG)
            return self._process_sequential_structure(spec)
        
        else:
            print(f"⚠️  Unknown pattern: {pattern}")
            return None
    
    def _process_sequential_structure(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une structure séquentielle (liste de chunks, etc.)"""
        
        element_spec = spec.get('element', {})
        terminator = spec.get('terminator', {})
        terminator_field = terminator.get('field')
        terminator_value = terminator.get('value')
        
        elements = []
        
        while self.offset < len(self.binary_data):
            # Traiter un élément
            if element_spec.get('pattern') == 'TYPED_CHUNK':
                processor = TypedChunkProcessor(self.binary_data, self.offset)
                chunk_result = processor.process(element_spec)
                
                if chunk_result is None:
                    break
                
                self.offset = processor.offset
                elements.append(chunk_result)
                
                # Vérifier le terminateur
                if terminator_field == 'type':
                    chunk_type = chunk_result.get('type')
                    if chunk_type == terminator_value:
                        break
            else:
                print(f"⚠️  Unsupported element pattern in sequential: {element_spec.get('pattern')}")
                break
        
        return {
            "pattern": "SEQUENTIAL_STRUCTURE",
            "name": spec.get('name', 'body'),
            "count": len(elements),
            "elements": elements
        }
    
    def _process_sequential_segments(self, root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Traite une structure de segments JPEG-like"""
        
        segments = []
        
        # 1. Traiter le start_marker (SOI)
        start_marker_spec = root.get('start_marker', {})
        if start_marker_spec.get('pattern') == 'MAGIC_NUMBER':
            expected_marker = bytes.fromhex(start_marker_spec.get('value', ''))
            marker = self.binary_data[self.offset:self.offset + 2]
            
            if marker == expected_marker:
                segments.append({
                    "pattern": "MAGIC_NUMBER",
                    "offset": self.offset,
                    "size": 2,
                    "marker": marker.hex().upper(),
                    "marker_type": "SOI",
                    "valid": True
                })
                self.offset += 2
        
        # 2. Traiter les segments
        end_marker = bytes.fromhex(root.get('end_marker', {}).get('value', 'FFD9'))
        
        while self.offset < len(self.binary_data):
            # Lire le marker
            marker = self.binary_data[self.offset:self.offset + 2]
            
            # Si c'est le marqueur de fin, on arrête
            if marker == end_marker:
                segments.append({
                    "pattern": "TERMINATOR",
                    "offset": self.offset,
                    "size": 2,
                    "marker": marker.hex().upper(),
                    "marker_type": "EOI",
                    "valid": True
                })
                self.offset += 2
                break
            
            # Traiter le segment
            self.offset += 2
            processor = SegmentStructureProcessor(self.binary_data, self.offset)
            segment = processor.process(marker)
            if segment:
                self.offset = processor.offset
                segments.append(segment)
            else:
                break
        
        return segments


# ============================================================================
# EXPORT & VALIDATION
# ============================================================================

def export_decomposition(decomposition: Dict[str, Any], output_path: Path):
    """Exporte la décomposition en JSON"""
    output_path.write_text(json.dumps(decomposition, indent=2))
    print(f"✅ Decomposition exported to {output_path}")


def validate_decomposition(decomposition: Dict[str, Any]) -> Dict[str, Any]:
    """Valide la décomposition et génère un rapport"""
    
    stats = {
        "total_elements": 0,
        "patterns_used": {},
        "validation_status": {},
        "integrity_checks": []
    }
    
    def count_elements(element):
        stats["total_elements"] += 1
        
        pattern = element.get('pattern')
        if pattern:
            stats["patterns_used"][pattern] = stats["patterns_used"].get(pattern, 0) + 1
        
        # Vérifier les validations
        if 'valid' in element:
            key = f"{pattern}_{element.get('name', 'unknown')}"
            stats["validation_status"][key] = element['valid']
            if not element['valid']:
                stats["integrity_checks"].append({
                    "pattern": pattern,
                    "field": element.get('name'),
                    "status": "FAILED",
                    "offset": element.get('offset')
                })
        
        # Récursion sur les éléments imbriqués
        if 'elements' in element:
            for sub in element['elements']:
                count_elements(sub)
        
        if 'structure' in element:
            for sub in element['structure'].values():
                if isinstance(sub, dict):
                    count_elements(sub)
    
    for element in decomposition.get('elements', []):
        count_elements(element)
    
    # Résumé
    all_valid = all(stats["validation_status"].values()) if stats["validation_status"] else True
    stats["overall_status"] = "VALID" if all_valid else "INVALID"
    
    return stats


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 3:
        print("Usage: python generic_decomposer.py <binary_file> <grammar_file>")
        print("\nGeneric binary decomposer using universal patterns (PaniniFS)")
        print("\nExample:")
        print("  python generic_decomposer.py test.png format_grammars/png.json")
        sys.exit(1)
    
    binary_file = Path(sys.argv[1])
    grammar_file = Path(sys.argv[2])
    
    if not binary_file.exists():
        print(f"❌ Binary file not found: {binary_file}")
        sys.exit(1)
    
    if not grammar_file.exists():
        print(f"❌ Grammar file not found: {grammar_file}")
        sys.exit(1)
    
    print(f"\n🔬 Generic Decomposer - PaniniFS")
    print("=" * 70)
    print(f"Binary file: {binary_file} ({binary_file.stat().st_size} bytes)")
    print(f"Grammar: {grammar_file}")
    
    # Décomposer
    decomposer = GenericDecomposer(binary_file, grammar_file)
    result = decomposer.decompose()
    
    # Valider
    validation = validate_decomposition(result)
    
    # Afficher les résultats
    print(f"\n📊 Decomposition Results:")
    print(f"   Format: {result['format']}")
    print(f"   Grammar version: {result['grammar_version']}")
    print(f"   Total elements: {validation['total_elements']}")
    
    print(f"\n🧩 Patterns Used:")
    for pattern, count in validation['patterns_used'].items():
        print(f"   • {pattern}: {count}x")
    
    print(f"\n✓ Validation:")
    for key, valid in validation['validation_status'].items():
        status = "✓" if valid else "✗"
        print(f"   {status} {key}")
    
    if validation['integrity_checks']:
        print(f"\n⚠️  Integrity Issues:")
        for issue in validation['integrity_checks']:
            print(f"   • {issue['pattern']} at offset {issue['offset']}: {issue['status']}")
    
    print(f"\n🎯 Overall Status: {validation['overall_status']}")
    
    # Exporter
    output_file = Path(f"decomposition_{binary_file.stem}.json")
    export_decomposition(result, output_file)
    
    # Exporter les stats
    stats_file = Path(f"decomposition_{binary_file.stem}_stats.json")
    stats_file.write_text(json.dumps(validation, indent=2))
    print(f"✅ Statistics exported to {stats_file}")
    
    print(f"\n✨ Decomposition complete!")
    print(f"   → Full decomposition: {output_file}")
    print(f"   → Statistics: {stats_file}")
    print(f"\n💡 Next step: Use generic_reconstructor.py to rebuild the file")


if __name__ == "__main__":
    main()
