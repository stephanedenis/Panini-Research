#!/usr/bin/env python3
"""
🔧 Generic Binary Reconstructor - PaniniFS Core Engine

Moteur générique de reconstruction basé sur grammaires universelles.
Lit une décomposition JSON + grammaire et reconstruit le fichier binaire byte-perfect.

Philosophie:
- RECONSTRUCTION PARFAITE (bit-perfect)
- Recalcule TOUS les checksums (CRC, etc.)
- Réutilise les patterns génériques
- Validation de la reconstruction

Usage:
    python generic_reconstructor.py <decomposition_file> <grammar_file> <output_file>
    
Example:
    python generic_reconstructor.py decomposition_test_sample.json format_grammars/png.json reconstructed.png
"""

import struct
import zlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


# ============================================================================
# PATTERN RECONSTRUCTORS - Reconstruit chaque type de pattern universel
# ============================================================================

class PatternReconstructor:
    """Classe de base pour reconstruire un pattern universel"""
    
    def __init__(self):
        self.buffer = bytearray()
    
    def write_bytes(self, data: bytes):
        """Ajoute des bytes au buffer"""
        self.buffer.extend(data)
    
    def get_bytes(self) -> bytes:
        """Retourne les bytes reconstruits"""
        return bytes(self.buffer)


class MagicNumberReconstructor(PatternReconstructor):
    """Reconstruit le pattern MAGIC_NUMBER"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        # Pour JPEG, le field s'appelle 'marker', pour PNG c'est 'value'
        value = element.get('value') or element.get('marker', '')
        return bytes.fromhex(value)


class LengthPrefixedDataReconstructor(PatternReconstructor):
    """Reconstruit le pattern LENGTH_PREFIXED_DATA"""
    
    def reconstruct(self, element: Dict[str, Any], data_length: int) -> bytes:
        """Reconstruit le champ de taille"""
        endianness = element.get('endianness', 'big')
        
        # Pour PNG, c'est toujours uint32 big-endian
        if endianness == 'big':
            return struct.pack('>I', data_length)
        else:
            return struct.pack('<I', data_length)


class CRCChecksumReconstructor(PatternReconstructor):
    """Reconstruit et recalcule le pattern CRC_CHECKSUM"""
    
    def reconstruct(self, element: Dict[str, Any], data_to_check: bytes) -> bytes:
        """Recalcule le CRC sur les données"""
        algorithm = element.get('algorithm', 'CRC-32')
        
        if algorithm == 'CRC-32':
            crc = zlib.crc32(data_to_check)
            return struct.pack('>I', crc)
        else:
            raise ValueError(f"Unsupported CRC algorithm: {algorithm}")


class TypedChunkReconstructor(PatternReconstructor):
    """Reconstruit le pattern TYPED_CHUNK"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit un chunk complet (length + type + data + crc)"""
        structure = element.get('structure', {})
        
        # Extraire les composants
        chunk_type = element.get('type', '').encode('ascii')
        
        # Récupérer les données
        data_info = structure.get('data', {})
        
        # Utiliser full_data si disponible, sinon preview
        if 'full_data' in data_info:
            data_hex = data_info['full_data']
        else:
            data_preview = data_info.get('preview', '')
            if data_preview.endswith('...'):
                data_hex = data_preview[:-3]
            else:
                data_hex = data_preview
        
        data = bytes.fromhex(data_hex)
        
        # Vérifier la taille
        length_info = structure.get('length', {})
        expected_length = length_info.get('length_value', len(data))
        
        if len(data) != expected_length:
            print(f"⚠️  Data length mismatch: {len(data)} vs {expected_length}")
        
        # Construire le chunk
        chunk_buffer = bytearray()
        
        # 1. Length (4 bytes big-endian)
        chunk_buffer.extend(struct.pack('>I', len(data)))
        
        # 2. Type (4 bytes ASCII)
        chunk_buffer.extend(chunk_type)
        
        # 3. Data
        chunk_buffer.extend(data)
        
        # 4. CRC (recalculé sur type + data)
        crc_data = chunk_type + data
        crc = zlib.crc32(crc_data)
        chunk_buffer.extend(struct.pack('>I', crc))
        
        return bytes(chunk_buffer)


class SegmentStructureReconstructor(PatternReconstructor):
    """Reconstruit le pattern SEGMENT_STRUCTURE (JPEG)"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit un segment JPEG: Marker (2B) + Length (2B BE) + Data"""
        segment_buffer = bytearray()
        
        # 1. Marker (2 bytes)
        marker_hex = element.get('marker', '')
        marker = bytes.fromhex(marker_hex)
        segment_buffer.extend(marker)
        
        # Markers sans data (SOI, EOI)
        if not element.get('has_data', True):
            return bytes(segment_buffer)
        
        # Cas spécial SOS avec données compressées
        if element.get('marker_type') == 'SOS':
            # Header
            header_length = element.get('header_length', 0)
            header_hex = element.get('header_data', '')
            
            # Length field
            segment_buffer.extend(struct.pack('>H', header_length))
            
            # Header data
            if header_hex:
                segment_buffer.extend(bytes.fromhex(header_hex))
            
            # Compressed data
            compressed_info = element.get('compressed_data', {})
            compressed_hex = compressed_info.get('full_data', '')
            if compressed_hex:
                segment_buffer.extend(bytes.fromhex(compressed_hex))
            
            return bytes(segment_buffer)
        
        # Segments normaux avec length + data
        length_info = element.get('length', {})
        length_value = length_info.get('value', 0)
        
        # 2. Length (2 bytes big-endian)
        segment_buffer.extend(struct.pack('>H', length_value))
        
        # 3. Data
        data_info = element.get('data', {})
        if 'full_data' in data_info:
            data_hex = data_info['full_data']
        else:
            data_preview = data_info.get('preview', '')
            if data_preview.endswith('...'):
                data_hex = data_preview[:-3]
            else:
                data_hex = data_preview
        
        if data_hex:
            segment_buffer.extend(bytes.fromhex(data_hex))
        
        return bytes(segment_buffer)


class PaletteDataReconstructor(PatternReconstructor):
    """Reconstruit le pattern PALETTE_DATA"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit une palette RGB/RGBA"""
        # Récupérer les données hex complètes
        full_data_hex = element.get('full_data', '')
        if full_data_hex:
            return bytes.fromhex(full_data_hex)
        
        # Fallback : reconstruire depuis les couleurs (preview only)
        colors = element.get('colors', [])
        bytes_per_color = element.get('bytes_per_color', 3)
        
        buffer = bytearray()
        for color in colors:
            buffer.append(color['r'])
            buffer.append(color['g'])
            buffer.append(color['b'])
            if bytes_per_color == 4:
                buffer.append(color.get('a', 255))
        
        return bytes(buffer)


class LogicalScreenDescriptorReconstructor(PatternReconstructor):
    """Reconstruit le pattern LOGICAL_SCREEN_DESCRIPTOR"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit le Logical Screen Descriptor GIF (7 bytes)"""
        raw_data_hex = element.get('raw_data', '')
        if raw_data_hex:
            return bytes.fromhex(raw_data_hex)
        
        # Fallback : reconstruire depuis les champs
        canvas = element.get('canvas', {})
        width = canvas.get('width', 0)
        height = canvas.get('height', 0)
        
        flags = element.get('flags', {})
        packed_hex = flags.get('packed_value', '0x00')
        packed = int(packed_hex, 16)
        
        bg_color = element.get('background_color_index', 0)
        aspect = element.get('pixel_aspect_ratio', 0)
        
        buffer = struct.pack('<H', width)
        buffer += struct.pack('<H', height)
        buffer += bytes([packed, bg_color, aspect])
        
        return buffer


class ImageDescriptorReconstructor(PatternReconstructor):
    """Reconstruit le pattern IMAGE_DESCRIPTOR"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit un Image Descriptor GIF (9 bytes)"""
        raw_data_hex = element.get('raw_data', '')
        if raw_data_hex:
            return bytes.fromhex(raw_data_hex)
        
        # Fallback : reconstruire depuis les champs
        position = element.get('position', {})
        dimensions = element.get('dimensions', {})
        flags = element.get('flags', {})
        
        left = position.get('left', 0)
        top = position.get('top', 0)
        width = dimensions.get('width', 0)
        height = dimensions.get('height', 0)
        packed_hex = flags.get('packed_value', '0x00')
        packed = int(packed_hex, 16)
        
        buffer = struct.pack('<H', left)
        buffer += struct.pack('<H', top)
        buffer += struct.pack('<H', width)
        buffer += struct.pack('<H', height)
        buffer += bytes([packed])
        
        return buffer


class LZWCompressedDataReconstructor(PatternReconstructor):
    """Reconstruit le pattern LZW_COMPRESSED_DATA"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit des données LZW avec sub-blocks"""
        buffer = bytearray()
        
        # LZW min code size
        lzw_min = element.get('lzw_min_code_size', 8)
        buffer.append(lzw_min)
        
        # Sub-blocks
        sub_blocks = element.get('sub_blocks', [])
        for block in sub_blocks:
            size = block.get('size', 0)
            data_hex = block.get('data', '')
            
            buffer.append(size)
            if data_hex:
                buffer.extend(bytes.fromhex(data_hex))
        
        # Block terminator
        buffer.append(0x00)
        
        return bytes(buffer)


class GIFDataBlockReconstructor(PatternReconstructor):
    """Reconstruit le pattern GIF_DATA_BLOCK"""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        """Reconstruit un data block GIF (IMAGE ou EXTENSION)"""
        buffer = bytearray()
        
        block_type = element.get('type')
        
        if block_type == 'IMAGE':
            # Separator 0x2C
            buffer.append(0x2C)
            
            # Image Descriptor
            image_desc = element.get('image_descriptor', {})
            reconstructor = ImageDescriptorReconstructor()
            buffer.extend(reconstructor.reconstruct(image_desc))
            
            # Local color table (optionnel)
            if 'local_color_table' in element:
                palette_recon = PaletteDataReconstructor()
                buffer.extend(
                    palette_recon.reconstruct(element['local_color_table'])
                )
            
            # LZW compressed data
            lzw_data = element.get('compressed_data', {})
            lzw_reconstructor = LZWCompressedDataReconstructor()
            buffer.extend(lzw_reconstructor.reconstruct(lzw_data))
        
        elif block_type == 'EXTENSION':
            # Extension introducer 0x21
            buffer.append(0x21)
            
            # Label
            label_hex = element.get('label', '00')
            label = int(label_hex, 16)
            buffer.append(label)
            
            # Sub-blocks
            sub_blocks = element.get('sub_blocks', [])
            for block in sub_blocks:
                size = block.get('size', 0)
                data_hex = block.get('data', '')
                
                buffer.append(size)
                if data_hex:
                    buffer.extend(bytes.fromhex(data_hex))
            
            # Block terminator
            buffer.append(0x00)
        
        return bytes(buffer)


class RiffHeaderReconstructor(PatternReconstructor):
    """Reconstruct RIFF header."""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        buffer = bytearray()
        
        # RIFF signature (4 bytes)
        signature = element.get('signature', 'RIFF')
        buffer.extend(signature.encode('ascii'))
        
        # File size (4 bytes, little-endian)
        file_size = element.get('file_size', 0)
        buffer.extend(struct.pack('<I', file_size))
        
        # Form type (4 bytes)
        form_type = element.get('form_type', 'WEBP')
        buffer.extend(form_type.encode('ascii'))
        
        return bytes(buffer)


class RiffChunkReconstructor(PatternReconstructor):
    """Reconstruct RIFF chunk."""
    
    def reconstruct(self, element: Dict[str, Any]) -> bytes:
        buffer = bytearray()
        
        # FourCC (4 bytes)
        fourcc = element.get('fourcc', '    ')
        buffer.extend(fourcc.encode('ascii'))
        
        # Chunk data (from full_data hex)
        chunk_data_hex = element.get('full_data', '')
        chunk_data = bytes.fromhex(chunk_data_hex)
        
        # Chunk size (4 bytes, little-endian)
        chunk_size = len(chunk_data)
        buffer.extend(struct.pack('<I', chunk_size))
        
        # Data
        buffer.extend(chunk_data)
        
        # Padding (if odd size)
        if 'padding' in element and chunk_size % 2 == 1:
            padding_hex = element['padding']
            buffer.extend(bytes.fromhex(padding_hex))
        
        return bytes(buffer)


# ============================================================================
# GENERIC RECONSTRUCTOR ENGINE
# ============================================================================

class GenericReconstructor:
    """
    Moteur générique de reconstruction basé sur grammaires.
    Fonctionne pour N'IMPORTE QUEL format avec une grammaire + décomposition.
    """
    
    def __init__(self, decomposition_file: Path, grammar_file: Path):
        # Charger la décomposition
        self.decomposition = json.loads(decomposition_file.read_text())
        
        # Charger la grammaire
        grammar_content = json.loads(grammar_file.read_text())
        self.grammar = grammar_content.get('grammar', grammar_content)
        
        self.buffer = bytearray()
    
    def reconstruct(self) -> bytes:
        """Reconstruit le fichier binaire complet"""
        
        elements = self.decomposition.get('elements', [])
        
        for element in elements:
            reconstructed = self._reconstruct_element(element)
            if reconstructed:
                self.buffer.extend(reconstructed)
        
        return bytes(self.buffer)
    
    def _reconstruct_element(self, element: Dict[str, Any]) -> Optional[bytes]:
        """Reconstruit un élément selon son pattern"""
        
        pattern = element.get('pattern')
        
        if pattern == 'MAGIC_NUMBER':
            reconstructor = MagicNumberReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'PALETTE_DATA':
            reconstructor = PaletteDataReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'LOGICAL_SCREEN_DESCRIPTOR':
            reconstructor = LogicalScreenDescriptorReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'IMAGE_DESCRIPTOR':
            reconstructor = ImageDescriptorReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'LZW_COMPRESSED_DATA':
            reconstructor = LZWCompressedDataReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'GIF_DATA_BLOCK':
            reconstructor = GIFDataBlockReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'RIFF_HEADER':
            reconstructor = RiffHeaderReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'RIFF_CHUNK':
            reconstructor = RiffChunkReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'TERMINATOR':
            # Terminateurs (EOI JPEG, GIF 0x3B, etc.)
            value_hex = element.get('value', element.get('marker', ''))
            return bytes.fromhex(value_hex) if value_hex else None
        
        elif pattern == 'SEQUENTIAL_STRUCTURE':
            # Reconstruire tous les éléments de la séquence
            buffer = bytearray()
            for sub_element in element.get('elements', []):
                reconstructed = self._reconstruct_element(sub_element)
                if reconstructed:
                    buffer.extend(reconstructed)
            return bytes(buffer)
        
        elif pattern == 'TYPED_CHUNK':
            reconstructor = TypedChunkReconstructor()
            return reconstructor.reconstruct(element)
        
        elif pattern == 'SEGMENT_STRUCTURE':
            reconstructor = SegmentStructureReconstructor()
            return reconstructor.reconstruct(element)
        
        else:
            print(f"⚠️  Unknown pattern: {pattern}")
            return None


# ============================================================================
# VALIDATION
# ============================================================================

def validate_reconstruction(original: Path, reconstructed: Path) -> Dict[str, Any]:
    """Compare le fichier original avec la reconstruction"""
    
    original_data = original.read_bytes()
    reconstructed_data = reconstructed.read_bytes()
    
    validation = {
        "original_size": len(original_data),
        "reconstructed_size": len(reconstructed_data),
        "size_match": len(original_data) == len(reconstructed_data),
        "bit_perfect": original_data == reconstructed_data,
        "differences": []
    }
    
    if not validation['bit_perfect']:
        # Trouver les différences
        min_size = min(len(original_data), len(reconstructed_data))
        for i in range(min_size):
            if original_data[i] != reconstructed_data[i]:
                validation['differences'].append({
                    "offset": i,
                    "original": f"{original_data[i]:02x}",
                    "reconstructed": f"{reconstructed_data[i]:02x}"
                })
                if len(validation['differences']) >= 10:
                    validation['differences'].append({"note": "... (more differences)"})
                    break
    
    return validation


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 4:
        print("Usage: python generic_reconstructor.py <decomposition_file> <grammar_file> <output_file>")
        print("\nGeneric binary reconstructor using universal patterns (PaniniFS)")
        print("\nExample:")
        print("  python generic_reconstructor.py decomposition_test.json format_grammars/png.json output.png")
        sys.exit(1)
    
    decomposition_file = Path(sys.argv[1])
    grammar_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3])
    
    if not decomposition_file.exists():
        print(f"❌ Decomposition file not found: {decomposition_file}")
        sys.exit(1)
    
    if not grammar_file.exists():
        print(f"❌ Grammar file not found: {grammar_file}")
        sys.exit(1)
    
    print(f"\n🔧 Generic Reconstructor - PaniniFS")
    print("=" * 70)
    print(f"Decomposition: {decomposition_file}")
    print(f"Grammar: {grammar_file}")
    print(f"Output: {output_file}")
    
    # Charger les infos de la décomposition
    decomp_data = json.loads(decomposition_file.read_text())
    source_file = decomp_data.get('source_file')
    
    # Reconstruire
    print(f"\n🔨 Reconstructing...")
    reconstructor = GenericReconstructor(decomposition_file, grammar_file)
    reconstructed_data = reconstructor.reconstruct()
    
    # Sauvegarder
    output_file.write_bytes(reconstructed_data)
    print(f"✅ Reconstructed file saved: {output_file} ({len(reconstructed_data)} bytes)")
    
    # Valider si le fichier source existe
    if source_file and Path(source_file).exists():
        print(f"\n🔍 Validating reconstruction...")
        validation = validate_reconstruction(Path(source_file), output_file)
        
        print(f"\n📊 Validation Results:")
        print(f"   Original size: {validation['original_size']} bytes")
        print(f"   Reconstructed size: {validation['reconstructed_size']} bytes")
        print(f"   Size match: {'✓' if validation['size_match'] else '✗'}")
        print(f"   Bit-perfect: {'✓' if validation['bit_perfect'] else '✗'}")
        
        if validation['differences']:
            print(f"\n⚠️  Differences found:")
            for diff in validation['differences']:
                if 'note' in diff:
                    print(f"   {diff['note']}")
                else:
                    print(f"   Offset {diff['offset']}: {diff['original']} → {diff['reconstructed']}")
        
        if validation['bit_perfect']:
            print(f"\n🎉 SUCCESS: Bit-perfect reconstruction!")
        else:
            print(f"\n⚠️  WARNING: Reconstruction differs from original")
        
        # Sauvegarder le rapport de validation
        validation_file = output_file.with_suffix('.validation.json')
        validation_file.write_text(json.dumps(validation, indent=2))
        print(f"✅ Validation report: {validation_file}")
    else:
        print(f"\n⚠️  Source file not available for validation")
    
    print(f"\n✨ Reconstruction complete!")


if __name__ == "__main__":
    main()
