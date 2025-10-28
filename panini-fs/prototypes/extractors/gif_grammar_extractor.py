#!/usr/bin/env python3
"""
🎨 GIF Grammar Extractor - PaniniFS

Analyse les fichiers GIF et extrait les patterns universels.
Supporte GIF87a et GIF89a (avec animations).

Structure GIF:
- Header (6 bytes): "GIF87a" ou "GIF89a"
- Logical Screen Descriptor (7 bytes)
- Global Color Table (optionnel, 3×2^(N+1) bytes)
- Data Stream (Images + Extensions + Trailer)
- Trailer (1 byte): 0x3B

Nouveaux patterns universels:
- PALETTE_DATA: Table de couleurs indexées RGB
- LOGICAL_SCREEN_DESCRIPTOR: Métadonnées écran logique
- IMAGE_DESCRIPTOR: Position et taille d'une image
- GRAPHIC_CONTROL_EXTENSION: Contrôle animation (délai, transparence)
- LZW_COMPRESSED_DATA: Données image compressées LZW

Usage:
    python gif_grammar_extractor.py <gif_file>
"""

import struct
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# ============================================================================
# GIF CONSTANTS
# ============================================================================

# Block separators
IMAGE_SEPARATOR = 0x2C
EXTENSION_INTRODUCER = 0x21
TRAILER = 0x3B

# Extension labels
GRAPHIC_CONTROL_LABEL = 0xF9
COMMENT_LABEL = 0xFE
PLAIN_TEXT_LABEL = 0x01
APPLICATION_EXTENSION_LABEL = 0xFF


# ============================================================================
# GIF ANALYZER
# ============================================================================

class GIFAnalyzer:
    """Analyse un fichier GIF et extrait les patterns universels"""
    
    def __init__(self, gif_file: Path):
        self.gif_file = gif_file
        self.data = gif_file.read_bytes()
        self.offset = 0
        self.size = len(self.data)
        
        self.analysis = {
            "file": str(gif_file),
            "size": self.size,
            "version": None,
            "logical_screen": {},
            "global_color_table": None,
            "images": [],
            "extensions": [],
            "patterns_found": set()
        }
    
    def read_bytes(self, count: int) -> bytes:
        """Lit N bytes"""
        if self.offset + count > self.size:
            raise ValueError(f"Cannot read {count} bytes at {self.offset}")
        result = self.data[self.offset:self.offset + count]
        self.offset += count
        return result
    
    def peek_byte(self) -> int:
        """Regarde le prochain byte sans avancer"""
        if self.offset >= self.size:
            return -1
        return self.data[self.offset]
    
    def read_sub_blocks(self) -> bytes:
        """Lit une séquence de sub-blocks (utilisé pour données LZW, etc.)"""
        result = bytearray()
        
        while True:
            block_size = self.data[self.offset]
            self.offset += 1
            
            if block_size == 0:
                break
            
            block_data = self.read_bytes(block_size)
            result.extend(block_data)
        
        return bytes(result)
    
    def analyze(self) -> Dict[str, Any]:
        """Analyse complète du fichier GIF"""
        
        print(f"📸 Analysing GIF: {self.gif_file.name}")
        print(f"   Size: {self.size} bytes")
        
        # 1. Header
        self._parse_header()
        
        # 2. Logical Screen Descriptor
        self._parse_logical_screen_descriptor()
        
        # 3. Global Color Table (si présent)
        if self.analysis['logical_screen']['has_global_color_table']:
            self._parse_global_color_table()
        
        # 4. Data Stream
        self._parse_data_stream()
        
        print(f"   ✓ Found {len(self.analysis['images'])} image(s)")
        print(f"   ✓ Found {len(self.analysis['extensions'])} extension(s)")
        
        return self.analysis
    
    def _parse_header(self):
        """Parse GIF header (6 bytes)"""
        header = self.read_bytes(6).decode('ascii')
        
        if header not in ['GIF87a', 'GIF89a']:
            raise ValueError(f"Invalid GIF header: {header}")
        
        self.analysis['version'] = header
        self.analysis['patterns_found'].add('MAGIC_NUMBER')
        
        print(f"   Version: {header}")
    
    def _parse_logical_screen_descriptor(self):
        """Parse Logical Screen Descriptor (7 bytes)"""
        width = struct.unpack('<H', self.read_bytes(2))[0]
        height = struct.unpack('<H', self.read_bytes(2))[0]
        
        packed = self.read_bytes(1)[0]
        has_gct = bool(packed & 0x80)
        color_resolution = ((packed & 0x70) >> 4) + 1
        sort_flag = bool(packed & 0x08)
        gct_size = 2 ** ((packed & 0x07) + 1)
        
        bg_color_index = self.read_bytes(1)[0]
        pixel_aspect_ratio = self.read_bytes(1)[0]
        
        self.analysis['logical_screen'] = {
            "width": width,
            "height": height,
            "has_global_color_table": has_gct,
            "color_resolution": color_resolution,
            "sort_flag": sort_flag,
            "gct_size": gct_size,
            "background_color_index": bg_color_index,
            "pixel_aspect_ratio": pixel_aspect_ratio
        }
        
        self.analysis['patterns_found'].add('LOGICAL_SCREEN_DESCRIPTOR')
        
        print(f"   Canvas: {width}×{height}, colors: {gct_size}")
    
    def _parse_global_color_table(self):
        """Parse Global Color Table"""
        gct_size = self.analysis['logical_screen']['gct_size']
        gct_bytes = gct_size * 3
        
        palette_data = self.read_bytes(gct_bytes)
        
        # Extraire quelques couleurs pour l'analyse
        colors = []
        for i in range(min(5, gct_size)):
            r, g, b = palette_data[i*3:(i+1)*3]
            colors.append(f"#{r:02X}{g:02X}{b:02X}")
        
        self.analysis['global_color_table'] = {
            "size": gct_size,
            "bytes": gct_bytes,
            "sample_colors": colors,
            "full_data_hex": palette_data.hex()
        }
        
        self.analysis['patterns_found'].add('PALETTE_DATA')
        
        print(f"   Global palette: {gct_size} colors")
    
    def _parse_data_stream(self):
        """Parse le Data Stream (images + extensions)"""
        
        while self.offset < self.size:
            separator = self.peek_byte()
            
            if separator == IMAGE_SEPARATOR:
                self._parse_image()
            
            elif separator == EXTENSION_INTRODUCER:
                self._parse_extension()
            
            elif separator == TRAILER:
                self.offset += 1
                print(f"   ✓ Trailer found at offset {self.offset-1}")
                self.analysis['patterns_found'].add('TERMINATOR')
                break
            
            else:
                print(f"   ⚠ Unknown separator: 0x{separator:02X} at {self.offset}")
                break
    
    def _parse_image(self):
        """Parse un Image Descriptor + Image Data"""
        self.offset += 1  # Skip separator
        
        left = struct.unpack('<H', self.read_bytes(2))[0]
        top = struct.unpack('<H', self.read_bytes(2))[0]
        width = struct.unpack('<H', self.read_bytes(2))[0]
        height = struct.unpack('<H', self.read_bytes(2))[0]
        
        packed = self.read_bytes(1)[0]
        has_lct = bool(packed & 0x80)
        interlace = bool(packed & 0x40)
        sort_flag = bool(packed & 0x20)
        lct_size = 2 ** ((packed & 0x07) + 1) if has_lct else 0
        
        image_data = {
            "offset": self.offset - 10,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "has_local_color_table": has_lct,
            "interlace": interlace,
            "local_color_table_size": lct_size
        }
        
        # Local Color Table (si présent)
        if has_lct:
            lct_bytes = lct_size * 3
            lct_data = self.read_bytes(lct_bytes)
            image_data['local_color_table_hex'] = lct_data.hex()
            self.analysis['patterns_found'].add('PALETTE_DATA')
        
        # LZW Minimum Code Size
        lzw_min_code_size = self.read_bytes(1)[0]
        image_data['lzw_min_code_size'] = lzw_min_code_size
        
        # Image Data (sub-blocks)
        compressed_start = self.offset
        compressed_data = self.read_sub_blocks()
        image_data['compressed_data'] = {
            "offset": compressed_start,
            "size": len(compressed_data),
            "preview": compressed_data[:32].hex()
        }
        
        self.analysis['images'].append(image_data)
        self.analysis['patterns_found'].add('IMAGE_DESCRIPTOR')
        self.analysis['patterns_found'].add('LZW_COMPRESSED_DATA')
    
    def _parse_extension(self):
        """Parse une Extension"""
        self.offset += 1  # Skip introducer
        
        label = self.read_bytes(1)[0]
        
        extension_data = {
            "offset": self.offset - 2,
            "label": f"0x{label:02X}"
        }
        
        if label == GRAPHIC_CONTROL_LABEL:
            extension_data['type'] = 'Graphic Control'
            block_size = self.read_bytes(1)[0]
            
            packed = self.read_bytes(1)[0]
            disposal_method = (packed & 0x1C) >> 2
            user_input = bool(packed & 0x02)
            transparent = bool(packed & 0x01)
            
            delay = struct.unpack('<H', self.read_bytes(2))[0]
            transparent_index = self.read_bytes(1)[0]
            
            self.read_bytes(1)  # Block terminator
            
            extension_data.update({
                "disposal_method": disposal_method,
                "user_input_flag": user_input,
                "transparent_color_flag": transparent,
                "delay_time": delay,
                "transparent_color_index": transparent_index
            })
            
            self.analysis['patterns_found'].add('GRAPHIC_CONTROL_EXTENSION')
        
        elif label == APPLICATION_EXTENSION_LABEL:
            extension_data['type'] = 'Application Extension'
            block_size = self.read_bytes(1)[0]
            app_id = self.read_bytes(8).decode('ascii', errors='ignore')
            auth_code = self.read_bytes(3)
            extension_data['application_id'] = app_id
            extension_data['auth_code'] = auth_code.hex()
            
            # Sub-blocks
            app_data = self.read_sub_blocks()
            extension_data['data_size'] = len(app_data)
        
        elif label == COMMENT_LABEL:
            extension_data['type'] = 'Comment'
            comment_data = self.read_sub_blocks()
            extension_data['comment'] = comment_data.decode('ascii', errors='ignore')
        
        else:
            extension_data['type'] = f'Unknown (0x{label:02X})'
            # Skip data
            self.read_sub_blocks()
        
        self.analysis['extensions'].append(extension_data)
    
    def export_grammar(self, output_dir: Path):
        """Exporte la grammaire GIF en JSON"""
        
        grammar = {
            "format": "GIF",
            "version": "1.0",
            "variants": ["GIF87a", "GIF89a"],
            "composition": {
                "root": {
                    "pattern": "SEQUENTIAL",
                    "elements": [
                        {
                            "name": "header",
                            "pattern": "MAGIC_NUMBER",
                            "size": 6,
                            "values": ["474946383761", "474946383961"],
                            "description": "GIF87a or GIF89a signature"
                        },
                        {
                            "name": "logical_screen_descriptor",
                            "pattern": "LOGICAL_SCREEN_DESCRIPTOR",
                            "size": 7,
                            "structure": [
                                {"name": "width", "type": "uint16_le"},
                                {"name": "height", "type": "uint16_le"},
                                {"name": "packed_fields", "type": "uint8"},
                                {"name": "bg_color_index", "type": "uint8"},
                                {"name": "pixel_aspect_ratio", "type": "uint8"}
                            ]
                        },
                        {
                            "name": "global_color_table",
                            "pattern": "PALETTE_DATA",
                            "optional": True,
                            "size_formula": "3 * 2^((packed_fields & 0x07) + 1)",
                            "condition": "packed_fields & 0x80"
                        },
                        {
                            "name": "data_stream",
                            "pattern": "SEQUENTIAL_STRUCTURE",
                            "element": {
                                "pattern": "GIF_DATA_BLOCK",
                                "variants": ["IMAGE", "EXTENSION"]
                            },
                            "terminator": {
                                "pattern": "TERMINATOR",
                                "value": "3B"
                            }
                        }
                    ]
                }
            },
            "data_blocks": {
                "IMAGE": {
                    "separator": "2C",
                    "pattern": "IMAGE_DESCRIPTOR",
                    "structure": [
                        {"name": "left", "type": "uint16_le"},
                        {"name": "top", "type": "uint16_le"},
                        {"name": "width", "type": "uint16_le"},
                        {"name": "height", "type": "uint16_le"},
                        {"name": "packed_fields", "type": "uint8"}
                    ],
                    "optional_local_color_table": {
                        "pattern": "PALETTE_DATA",
                        "condition": "packed_fields & 0x80"
                    },
                    "compressed_data": {
                        "pattern": "LZW_COMPRESSED_DATA",
                        "lzw_min_code_size": "uint8",
                        "sub_blocks": "terminated by 0x00"
                    }
                },
                "EXTENSION": {
                    "introducer": "21",
                    "labels": {
                        "F9": "GRAPHIC_CONTROL_EXTENSION",
                        "FE": "COMMENT_EXTENSION",
                        "01": "PLAIN_TEXT_EXTENSION",
                        "FF": "APPLICATION_EXTENSION"
                    }
                }
            }
        }
        
        output_file = output_dir / "gif.json"
        with open(output_file, 'w') as f:
            json.dump(grammar, f, indent=2)
        
        print(f"📝 GIF grammar: {output_file}")
    
    def export_patterns(self, output_dir: Path):
        """Met à jour generic_patterns.json avec les nouveaux patterns GIF"""
        
        patterns_file = output_dir / "generic_patterns.json"
        
        if patterns_file.exists():
            with open(patterns_file) as f:
                patterns_data = json.load(f)
        else:
            patterns_data = {"patterns": {}}
        
        # Ajouter les nouveaux patterns GIF
        new_patterns = {
            "PALETTE_DATA": {
                "category": "data",
                "description": "Indexed color palette (RGB table)",
                "structure": "Array of RGB triplets (R, G, B bytes)",
                "usage": "Color lookup table for indexed images",
                "applicable_formats": ["GIF", "PNG (plte)", "BMP", "PCX"],
                "universality": 4
            },
            "LOGICAL_SCREEN_DESCRIPTOR": {
                "category": "structural",
                "description": "Canvas/screen metadata",
                "structure": "Width, Height, Flags, Background, AspectRatio",
                "usage": "Defines logical screen dimensions and properties",
                "applicable_formats": ["GIF"],
                "universality": 2
            },
            "IMAGE_DESCRIPTOR": {
                "category": "structural",
                "description": "Image position and size metadata",
                "structure": "Left, Top, Width, Height, Flags",
                "usage": "Defines image placement within logical screen",
                "applicable_formats": ["GIF", "multi-image formats"],
                "universality": 3
            },
            "GRAPHIC_CONTROL_EXTENSION": {
                "category": "metadata",
                "description": "Animation control (delay, transparency)",
                "structure": "Disposal, UserInput, Transparent, Delay, TransparentIndex",
                "usage": "Controls animation timing and transparency",
                "applicable_formats": ["GIF89a", "APNG"],
                "universality": 2
            },
            "LZW_COMPRESSED_DATA": {
                "category": "data",
                "description": "LZW-compressed image data",
                "structure": "MinCodeSize + Sub-blocks (size + data) terminated by 0x00",
                "usage": "Compressed raster data",
                "applicable_formats": ["GIF", "TIFF (LZW)", "PDF (LZW)"],
                "universality": 3
            }
        }
        
        patterns_data['patterns'].update(new_patterns)
        
        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2)
        
        print(f"📝 Generic patterns updated: {patterns_file}")
        print(f"   Added {len(new_patterns)} new patterns")
    
    def export_analysis(self, output_dir: Path):
        """Exporte l'analyse détaillée"""
        
        # Convertir set en list pour JSON
        analysis_copy = self.analysis.copy()
        analysis_copy['patterns_found'] = list(self.analysis['patterns_found'])
        
        output_file = output_dir / f"gif_analysis_{self.gif_file.stem}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis_copy, f, indent=2)
        
        print(f"📝 Full analysis: {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) != 2:
        print("Usage: python gif_grammar_extractor.py <gif_file>")
        sys.exit(1)
    
    gif_file = Path(sys.argv[1])
    
    if not gif_file.exists():
        print(f"Error: File not found: {gif_file}")
        sys.exit(1)
    
    # Analyser
    analyzer = GIFAnalyzer(gif_file)
    analysis = analyzer.analyze()
    
    # Exporter
    output_dir = gif_file.parent / "format_grammars"
    output_dir.mkdir(exist_ok=True)
    
    analyzer.export_grammar(output_dir)
    analyzer.export_patterns(output_dir)
    analyzer.export_analysis(output_dir)
    
    print(f"\n✅ Analysis complete:")
    print(f"   Version: {analysis['version']}")
    print(f"   Canvas: {analysis['logical_screen']['width']}×{analysis['logical_screen']['height']}")
    print(f"   Images: {len(analysis['images'])}")
    print(f"   Extensions: {len(analysis['extensions'])}")
    print(f"   Patterns found: {len(analysis['patterns_found'])}")


if __name__ == "__main__":
    main()
