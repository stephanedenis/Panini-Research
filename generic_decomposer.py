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
        
        # Supporter plusieurs valeurs possibles (GIF87a/GIF89a)
        expected_values = spec.get('values', [spec.get('value', '')])
        if isinstance(expected_values, str):
            expected_values = [expected_values]
        
        magic = self.read_bytes(size)
        magic_hex = magic.hex()
        
        # Vérifier si magic correspond à une des valeurs attendues
        valid = any(magic_hex == val.lower() for val in expected_values)
        
        return {
            "pattern": "MAGIC_NUMBER",
            "offset": self.offset - size,
            "size": size,
            "value": magic_hex,
            "expected": expected_values,
            "valid": valid,
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


class PaletteDataProcessor(PatternProcessor):
    """Traite le pattern PALETTE_DATA (GIF, PNG plte, BMP)"""
    
    def process(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Décompose une palette RGB: N entrées × 3 bytes"""
        num_colors = spec.get('colors', 256)
        bytes_per_color = spec.get('bytes_per_color', 3)  # RGB
        
        total_bytes = num_colors * bytes_per_color
        palette_data = self.read_bytes(total_bytes)
        
        # Extraire les couleurs
        colors = []
        for i in range(0, len(palette_data), bytes_per_color):
            if bytes_per_color == 3:  # RGB
                r, g, b = palette_data[i:i+3]
                colors.append({"r": r, "g": g, "b": b})
            elif bytes_per_color == 4:  # RGBA
                r, g, b, a = palette_data[i:i+4]
                colors.append({"r": r, "g": g, "b": b, "a": a})
        
        return {
            "pattern": "PALETTE_DATA",
            "offset": self.offset - total_bytes,
            "size": total_bytes,
            "num_colors": num_colors,
            "bytes_per_color": bytes_per_color,
            "colors": colors[:10],  # Preview 10 premières couleurs
            "full_data": palette_data.hex()
        }


class LogicalScreenDescriptorProcessor(PatternProcessor):
    """Traite le pattern LOGICAL_SCREEN_DESCRIPTOR (GIF)"""
    
    def process(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Décompose le Logical Screen Descriptor GIF (7 bytes)"""
        lsd_data = self.read_bytes(7)
        
        width = struct.unpack('<H', lsd_data[0:2])[0]
        height = struct.unpack('<H', lsd_data[2:4])[0]
        packed = lsd_data[4]
        bg_color = lsd_data[5]
        aspect = lsd_data[6]
        
        # Parser le packed byte
        global_color_table = bool(packed & 0x80)
        color_resolution = ((packed & 0x70) >> 4) + 1
        sort_flag = bool(packed & 0x08)
        global_color_table_size = 2 ** ((packed & 0x07) + 1)
        
        return {
            "pattern": "LOGICAL_SCREEN_DESCRIPTOR",
            "offset": self.offset - 7,
            "size": 7,
            "canvas": {
                "width": width,
                "height": height
            },
            "flags": {
                "global_color_table": global_color_table,
                "color_resolution": color_resolution,
                "sort_flag": sort_flag,
                "global_color_table_size": global_color_table_size,
                "packed_value": f"0x{packed:02X}"
            },
            "background_color_index": bg_color,
            "pixel_aspect_ratio": aspect,
            "raw_data": lsd_data.hex()
        }


class ImageDescriptorProcessor(PatternProcessor):
    """Traite le pattern IMAGE_DESCRIPTOR (GIF)"""
    
    def process(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Décompose un Image Descriptor GIF (10 bytes après separator)"""
        # Le separator 0x2C est déjà lu par le parser principal
        desc_data = self.read_bytes(9)
        
        left = struct.unpack('<H', desc_data[0:2])[0]
        top = struct.unpack('<H', desc_data[2:4])[0]
        width = struct.unpack('<H', desc_data[4:6])[0]
        height = struct.unpack('<H', desc_data[6:8])[0]
        packed = desc_data[8]
        
        # Parser le packed byte
        local_color_table = bool(packed & 0x80)
        interlace = bool(packed & 0x40)
        sort_flag = bool(packed & 0x20)
        local_color_table_size = 2 ** ((packed & 0x07) + 1) if local_color_table else 0
        
        return {
            "pattern": "IMAGE_DESCRIPTOR",
            "offset": self.offset - 9,
            "size": 9,
            "position": {
                "left": left,
                "top": top
            },
            "dimensions": {
                "width": width,
                "height": height
            },
            "flags": {
                "local_color_table": local_color_table,
                "interlace": interlace,
                "sort_flag": sort_flag,
                "local_color_table_size": local_color_table_size,
                "packed_value": f"0x{packed:02X}"
            },
            "raw_data": desc_data.hex()
        }


class LZWCompressedDataProcessor(PatternProcessor):
    """Traite le pattern LZW_COMPRESSED_DATA (GIF, TIFF)"""
    
    def process(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Décompose des données LZW en sub-blocks"""
        # Lire LZW minimum code size
        lzw_min_code_size = self.read_bytes(1)[0]
        
        # Lire les sub-blocks (TOUS pour reconstruction)
        sub_blocks = []
        total_data_size = 0
        
        while True:
            block_size = self.read_bytes(1)[0]
            if block_size == 0:  # Block terminator
                break
            
            block_data = self.read_bytes(block_size)
            sub_blocks.append({
                "size": block_size,
                "data": block_data.hex()
            })
            total_data_size += block_size
        
        return {
            "pattern": "LZW_COMPRESSED_DATA",
            "offset": self.offset - (1 + total_data_size + len(sub_blocks) + 1),
            "size": 1 + total_data_size + len(sub_blocks) + 1,
            "lzw_min_code_size": lzw_min_code_size,
            "num_sub_blocks": len(sub_blocks),
            "total_data_bytes": total_data_size,
            "sub_blocks": sub_blocks,  # TOUS les blocks, pas de preview
            "complete": True
        }


class GIFDataBlockProcessor(PatternProcessor):
    """Traite le pattern GIF_DATA_BLOCK (IMAGE ou EXTENSION)"""
    
    def process(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Décompose un data block GIF (image ou extension)"""
        
        if self.offset >= self.size:
            return None
        
        # Regarder le premier byte pour déterminer le type
        block_type_byte = self.peek_bytes(1)[0]
        
        if block_type_byte == 0x3B:  # Trailer/Terminator
            return None  # Fin du data stream
        
        elif block_type_byte == 0x2C:  # Image separator
            return self._process_image_block()
        
        elif block_type_byte == 0x21:  # Extension introducer
            return self._process_extension_block()
        
        else:
            print(f"⚠️  Unknown GIF data block type: 0x{block_type_byte:02X}")
            return None
    
    def _process_image_block(self) -> Dict[str, Any]:
        """Décompose un bloc IMAGE"""
        start_offset = self.offset
        
        # Lire le separator
        separator = self.read_bytes(1)[0]
        assert separator == 0x2C
        
        # Image Descriptor (9 bytes)
        desc_processor = ImageDescriptorProcessor(self.data, self.offset)
        image_desc = desc_processor.process({})
        self.offset = desc_processor.offset
        
        # Local color table (optionnel)
        local_color_table = None
        if image_desc['flags']['local_color_table']:
            num_colors = image_desc['flags']['local_color_table_size']
            palette_processor = PaletteDataProcessor(self.data, self.offset)
            local_color_table = palette_processor.process({
                'colors': num_colors,
                'bytes_per_color': 3
            })
            self.offset = palette_processor.offset
        
        # LZW compressed data
        lzw_processor = LZWCompressedDataProcessor(self.data, self.offset)
        lzw_data = lzw_processor.process({})
        self.offset = lzw_processor.offset
        
        result = {
            "pattern": "GIF_DATA_BLOCK",
            "type": "IMAGE",
            "offset": start_offset,
            "size": self.offset - start_offset,
            "image_descriptor": image_desc,
            "compressed_data": lzw_data
        }
        
        if local_color_table:
            result['local_color_table'] = local_color_table
        
        return result
    
    def _process_extension_block(self) -> Dict[str, Any]:
        """Décompose un bloc EXTENSION"""
        start_offset = self.offset
        
        # Lire introducer et label
        introducer = self.read_bytes(1)[0]
        assert introducer == 0x21
        
        label = self.read_bytes(1)[0]
        
        # Déterminer le type d'extension
        extension_types = {
            0xF9: 'GRAPHIC_CONTROL_EXTENSION',
            0xFE: 'COMMENT_EXTENSION',
            0x01: 'PLAIN_TEXT_EXTENSION',
            0xFF: 'APPLICATION_EXTENSION'
        }
        
        extension_type = extension_types.get(
            label,
            f'UNKNOWN_EXTENSION_0x{label:02X}'
        )
        
        # Lire les sub-blocks
        sub_blocks = []
        total_data_size = 0
        
        while True:
            block_size = self.read_bytes(1)[0]
            if block_size == 0:  # Block terminator
                break
            
            block_data = self.read_bytes(block_size)
            sub_blocks.append({
                "size": block_size,
                "data": block_data.hex()
            })
            total_data_size += block_size
        
        return {
            "pattern": "GIF_DATA_BLOCK",
            "type": "EXTENSION",
            "offset": start_offset,
            "size": self.offset - start_offset,
            "extension_type": extension_type,
            "label": f"0x{label:02X}",
            "num_sub_blocks": len(sub_blocks),
            "total_data_bytes": total_data_size,
            "sub_blocks": sub_blocks
        }


class RiffHeaderProcessor(PatternProcessor):
    """Process RIFF header (RIFF + size + form type)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        start_offset = self.offset
        
        # RIFF signature (4 bytes)
        signature = self.read_bytes(4).decode('ascii', errors='ignore')
        if signature != 'RIFF':
            raise ValueError(f"Invalid RIFF signature: {signature}")
        
        # File size (4 bytes, little-endian, excludes signature + size)
        file_size = struct.unpack('<I', self.read_bytes(4))[0]
        
        # Form type (4 bytes)
        form_type = self.read_bytes(4).decode('ascii', errors='ignore')
        
        return {
            "pattern": "RIFF_HEADER",
            "offset": start_offset,
            "size": 12,
            "signature": signature,
            "file_size": file_size,
            "form_type": form_type,
            "validation": {
                "signature_ok": signature == 'RIFF',
                "expected_total_size": file_size + 8
            }
        }


class RiffChunkProcessor(PatternProcessor):
    """Process RIFF chunk (FourCC + size + data + optional padding)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        start_offset = self.offset
        
        # FourCC (4 bytes)
        fourcc = self.read_bytes(4).decode('ascii', errors='ignore')
        
        # Chunk size (4 bytes, little-endian)
        chunk_size = struct.unpack('<I', self.read_bytes(4))[0]
        
        # Data (chunk_size bytes)
        chunk_data = self.read_bytes(chunk_size)
        
        result = {
            "pattern": "RIFF_CHUNK",
            "offset": start_offset,
            "fourcc": fourcc,
            "chunk_size": chunk_size,
            "data_preview": chunk_data[:32].hex() if len(chunk_data) > 32 else chunk_data.hex(),
            "full_data": chunk_data.hex()
        }
        
        # Analyze specific chunk types for WebP
        if fourcc == 'VP8 ':
            result['chunk_type'] = 'VP8_LOSSY'
            result['details'] = self._analyze_vp8(chunk_data)
        elif fourcc == 'VP8L':
            result['chunk_type'] = 'VP8_LOSSLESS'
            result['details'] = self._analyze_vp8l(chunk_data)
        elif fourcc == 'VP8X':
            result['chunk_type'] = 'VP8_EXTENDED'
            result['details'] = self._analyze_vp8x(chunk_data)
        elif fourcc == 'ALPH':
            result['chunk_type'] = 'ALPHA_CHANNEL'
        elif fourcc == 'ANIM':
            result['chunk_type'] = 'ANIMATION'
        elif fourcc == 'ANMF':
            result['chunk_type'] = 'ANIMATION_FRAME'
        elif fourcc == 'ICCP':
            result['chunk_type'] = 'ICC_PROFILE'
        elif fourcc == 'EXIF':
            result['chunk_type'] = 'EXIF_METADATA'
        elif fourcc == 'XMP ':
            result['chunk_type'] = 'XMP_METADATA'
        else:
            result['chunk_type'] = 'GENERIC'
        
        # RIFF chunks must be word-aligned (pad byte if odd size)
        if chunk_size % 2 == 1:
            # Skip padding byte if present
            if self.offset < len(self.data):
                pad_byte = self.read_bytes(1)
                result['padding'] = pad_byte.hex()
        
        result['size'] = self.offset - start_offset
        
        return result
    
    def _analyze_vp8(self, data: bytes) -> Dict[str, Any]:
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
        width = struct.unpack('<H', data[6:8])[0] & 0x3FFF
        height = struct.unpack('<H', data[8:10])[0] & 0x3FFF
        
        return {
            'key_frame': key_frame,
            'version': version,
            'show_frame': show_frame,
            'first_part_size': first_part_size,
            'start_code': start_code.hex(),
            'width': width,
            'height': height
        }
    
    def _analyze_vp8l(self, data: bytes) -> Dict[str, Any]:
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
    
    def _analyze_vp8x(self, data: bytes) -> Dict[str, Any]:
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


class TIFFHeaderProcessor(PatternProcessor):
    """Process TIFF header (byte order + magic + IFD offset)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        start_offset = self.offset
        
        # Byte order marker (2 bytes)
        byte_order_marker = self.read_bytes(2)
        
        if byte_order_marker == b'II':
            byte_order = '<'  # Little-endian
            byte_order_name = 'little-endian'
        elif byte_order_marker == b'MM':
            byte_order = '>'  # Big-endian
            byte_order_name = 'big-endian'
        else:
            raise ValueError(f"Invalid TIFF byte order: {byte_order_marker.hex()}")
        
        # Magic number (2 bytes): 42
        magic = struct.unpack(f'{byte_order}H', self.read_bytes(2))[0]
        if magic != 42:
            raise ValueError(f"Invalid TIFF magic: {magic}")
        
        # First IFD offset (4 bytes)
        first_ifd_offset = struct.unpack(f'{byte_order}I', self.read_bytes(4))[0]
        
        return {
            "pattern": "TIFF_HEADER",
            "offset": start_offset,
            "size": 8,
            "byte_order_marker": byte_order_marker.decode('ascii'),
            "byte_order": byte_order_name,
            "magic": magic,
            "first_ifd_offset": first_ifd_offset
        }


class IFDStructureProcessor(PatternProcessor):
    """Process TIFF IFD (Image File Directory) with linked list chain."""
    
    def __init__(self, data: bytes, offset: int, byte_order: str = '<'):
        super().__init__(data, offset)
        self.byte_order = byte_order
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        ifds = []
        current_offset = element.get('offset', self.offset)
        ifd_index = 0
        
        while current_offset != 0 and current_offset < self.size:
            self.offset = current_offset
            ifd = self._process_single_ifd(ifd_index)
            ifds.append(ifd)
            current_offset = ifd['next_ifd_offset']
            ifd_index += 1
        
        return {
            "pattern": "IFD_CHAIN",
            "offset": element.get('offset', 0),
            "ifd_count": len(ifds),
            "ifds": ifds
        }
    
    def _process_single_ifd(self, index: int) -> Dict[str, Any]:
        start_offset = self.offset
        
        # Number of entries (2 bytes)
        if self.offset + 2 > self.size:
            raise ValueError(f"Cannot read IFD num_entries at offset {self.offset} (file size: {self.size})")
        num_entries = struct.unpack(f'{self.byte_order}H', self.read_bytes(2))[0]
        
        # Validate IFD fits: 2 (num_entries) + 12*n (entries) + 4 (next_offset)
        bytes_needed = 2 + (num_entries * 12) + 4
        if start_offset + bytes_needed > self.size:
            raise ValueError(f"IFD at offset {start_offset} needs {bytes_needed} bytes but only {self.size - start_offset} available (file size: {self.size})")
        
        # Read all entries
        entries = []
        for _ in range(num_entries):
            entry = self._process_ifd_entry()
            entries.append(entry)
        
        # Next IFD offset (4 bytes, 0 = end)
        next_ifd_offset = struct.unpack(f'{self.byte_order}I', self.read_bytes(4))[0]
        
        return {
            "pattern": "IFD_STRUCTURE",
            "index": index,
            "offset": start_offset,
            "num_entries": num_entries,
            "entries": entries,
            "next_ifd_offset": next_ifd_offset,
            "size": self.offset - start_offset
        }
    
    def _process_ifd_entry(self) -> Dict[str, Any]:
        """Process single IFD entry (12 bytes: tag + type + count + value/offset)."""
        start_offset = self.offset
        
        tag = struct.unpack(f'{self.byte_order}H', self.read_bytes(2))[0]
        field_type = struct.unpack(f'{self.byte_order}H', self.read_bytes(2))[0]
        count = struct.unpack(f'{self.byte_order}I', self.read_bytes(4))[0]
        value_or_offset_bytes = self.read_bytes(4)
        
        # Decode value based on size
        type_sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}
        type_size = type_sizes.get(field_type, 0)
        total_size = count * type_size
        
        if total_size <= 4:
            value = self._decode_inline_value(value_or_offset_bytes[:total_size], field_type, count)
            value_location = 'inline'
        else:
            offset_val = struct.unpack(f'{self.byte_order}I', value_or_offset_bytes)[0]
            value = f"offset_0x{offset_val:08X}"
            value_location = 'offset'
        
        return {
            "pattern": "TAG_VALUE_PAIR",
            "offset": start_offset,
            "tag": tag,
            "type": field_type,
            "count": count,
            "value": value,
            "value_location": value_location,
            "size": 12
        }
    
    def _decode_inline_value(self, data: bytes, field_type: int, count: int) -> Any:
        """Decode inline value."""
        try:
            if field_type == 1:  # BYTE
                return list(data[:count])
            elif field_type == 2:  # ASCII
                return data[:count].decode('ascii', errors='ignore').rstrip('\x00')
            elif field_type == 3:  # SHORT
                if count == 1:
                    return struct.unpack(f'{self.byte_order}H', data[:2])[0]
                return [struct.unpack(f'{self.byte_order}H', data[i:i+2])[0] for i in range(0, count*2, 2)]
            elif field_type == 4:  # LONG
                return struct.unpack(f'{self.byte_order}I', data[:4])[0]
            else:
                return f"<type_{field_type}>"
        except:
            return "<decode_error>"


class PDFObjectProcessor(PatternProcessor):
    """Process PDF objects (simplified - text-based extraction)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PDF objects from text representation."""
        import re
        
        text = self.data.decode('latin1', errors='ignore')
        
        # Find all objects (n m obj ... endobj)
        objects = []
        for match in re.finditer(r'(\d+)\s+(\d+)\s+obj\s+(.*?)\s+endobj', text, re.DOTALL):
            obj_num = int(match.group(1))
            gen_num = int(match.group(2))
            content = match.group(3).strip()
            
            objects.append({
                "pattern": "PDF_OBJECT",
                "object_number": obj_num,
                "generation": gen_num,
                "offset": match.start(),
                "size": match.end() - match.start(),
                "content_preview": content[:100] if len(content) > 100 else content
            })
        
        return {
            "pattern": "SEQUENTIAL_STRUCTURE",
            "object_count": len(objects),
            "elements": objects
        }


class PDFHeaderProcessor(PatternProcessor):
    """Process PDF header (%PDF-x.y)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PDF version from header."""
        text = self.data[:20].decode('latin1', errors='ignore')
        
        import re
        match = re.match(r'%PDF-(\d+)\.(\d+)', text)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return {
                "pattern": "PDF_HEADER",
                "offset": 0,
                "size": len(match.group(0)),
                "version": f"{major}.{minor}",
                "major": major,
                "minor": minor
            }
        
        return {
            "pattern": "PDF_HEADER",
            "offset": 0,
            "size": 0,
            "error": "Invalid PDF header"
        }


class PDFTrailerProcessor(PatternProcessor):
    """Process PDF trailer section."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trailer dictionary."""
        import re
        
        text = self.data.decode('latin1', errors='ignore')
        
        # Find trailer keyword and following dictionary
        trailer_match = re.search(r'trailer\s*<<(.*?)>>', text, re.DOTALL)
        if not trailer_match:
            return {
                "pattern": "PDF_TRAILER",
                "found": False
            }
        
        trailer_dict = trailer_match.group(1).strip()
        
        return {
            "pattern": "PDF_TRAILER",
            "offset": trailer_match.start(),
            "size": trailer_match.end() - trailer_match.start(),
            "content_preview": trailer_dict[:200]
        }


class PDFEOFProcessor(PatternProcessor):
    """Process PDF end-of-file marker."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Find %%EOF marker."""
        text = self.data[-50:].decode('latin1', errors='ignore')
        
        if '%%EOF' in text:
            offset = len(self.data) - 50 + text.index('%%EOF')
            return {
                "pattern": "EOF_MARKER",
                "offset": offset,
                "size": 5,
                "marker": "%%EOF"
            }
        
        return {
            "pattern": "EOF_MARKER",
            "found": False
        }


class PDFXrefProcessor(PatternProcessor):
    """Process PDF objects (simplified - text-based extraction)."""
    
    def process(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PDF objects from text representation."""
        import re
        
        text = self.data.decode('latin1', errors='ignore')
        
        # Find all objects (n m obj ... endobj)
        objects = []
        for match in re.finditer(r'(\d+)\s+(\d+)\s+obj\s+(.*?)\s+endobj', text, re.DOTALL):
            obj_num = int(match.group(1))
            gen_num = int(match.group(2))
            content = match.group(3).strip()
            
            objects.append({
                "pattern": "PDF_OBJECT",
                "object_number": obj_num,
                "generation": gen_num,
                "offset": match.start(),
                "size": match.end() - match.start(),
                "content_preview": content[:100] if len(content) > 100 else content
            })
        
        return {
            "pattern": "SEQUENTIAL_STRUCTURE",
            "object_count": len(objects),
            "elements": objects
        }


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
        
        elif pattern == 'PALETTE_DATA':
            processor = PaletteDataProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'LOGICAL_SCREEN_DESCRIPTOR':
            processor = LogicalScreenDescriptorProcessor(
                self.binary_data, self.offset
            )
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'IMAGE_DESCRIPTOR':
            processor = ImageDescriptorProcessor(
                self.binary_data, self.offset
            )
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'LZW_COMPRESSED_DATA':
            processor = LZWCompressedDataProcessor(
                self.binary_data, self.offset
            )
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'GIF_DATA_BLOCK':
            processor = GIFDataBlockProcessor(
                self.binary_data, self.offset
            )
            result = processor.process(spec)
            if result:
                self.offset = processor.offset
                result['name'] = name
            return result
        
        elif pattern == 'RIFF_HEADER':
            processor = RiffHeaderProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'RIFF_CHUNK':
            processor = RiffChunkProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            return result
        
        elif pattern == 'TIFF_HEADER':
            processor = TIFFHeaderProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            self.offset = processor.offset
            result['name'] = name
            # Store byte order and first IFD offset for IFD processing
            self.tiff_byte_order = result.get('byte_order_marker', 'II')
            self.tiff_first_ifd_offset = result.get('first_ifd_offset', 8)
            return result
        
        elif pattern == 'IFD_CHAIN':
            # Get byte order from header
            byte_order = '<' if getattr(self, 'tiff_byte_order', 'II') == 'II' else '>'
            # Get first IFD offset from previous TIFF header result
            first_ifd_offset = getattr(self, 'tiff_first_ifd_offset', 8)
            processor = IFDStructureProcessor(self.binary_data, first_ifd_offset, byte_order)
            result = processor.process({'offset': first_ifd_offset})
            result['name'] = name
            return result
        
        elif pattern == 'PDF_HEADER':
            processor = PDFHeaderProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            result['name'] = name
            return result
        
        elif pattern == 'PDF_OBJECT':
            processor = PDFObjectProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            result['name'] = name
            return result
        
        elif pattern == 'PDF_TRAILER':
            processor = PDFTrailerProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            result['name'] = name
            return result
        
        elif pattern == 'EOF_MARKER':
            processor = PDFEOFProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
            result['name'] = name
            return result
        
        elif pattern == 'XREF_TABLE':
            processor = PDFXrefProcessor(self.binary_data, self.offset)
            result = processor.process(spec)
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
        terminator_pattern = terminator.get('pattern')
        
        elements = []
        
        while self.offset < len(self.binary_data):
            # Vérifier le terminateur avant de traiter l'élément
            if terminator_pattern == 'TERMINATOR':
                expected_byte = bytes.fromhex(terminator_value)
                next_byte = self.binary_data[self.offset:self.offset+1]
                if next_byte == expected_byte:
                    # Lire et retourner le terminateur
                    elements.append({
                        "pattern": "TERMINATOR",
                        "offset": self.offset,
                        "size": 1,
                        "value": next_byte.hex()
                    })
                    self.offset += 1
                    break
            
            # Traiter un élément
            element_pattern = element_spec.get('pattern')
            
            if element_pattern == 'TYPED_CHUNK':
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
            
            elif element_pattern == 'GIF_DATA_BLOCK':
                processor = GIFDataBlockProcessor(
                    self.binary_data, self.offset
                )
                block_result = processor.process(element_spec)
                
                if block_result is None:
                    break
                
                self.offset = processor.offset
                elements.append(block_result)
            
            elif element_pattern == 'RIFF_CHUNK':
                processor = RiffChunkProcessor(
                    self.binary_data, self.offset
                )
                chunk_result = processor.process(element_spec)
                
                if chunk_result is None:
                    break
                
                self.offset = processor.offset
                elements.append(chunk_result)
                
                # Check EOF terminator
                if terminator.get('type') == 'eof' and self.offset >= len(self.binary_data):
                    break
            
            else:
                print(f"⚠️  Unsupported pattern: {element_pattern}")
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
