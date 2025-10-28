#!/usr/bin/env python3
"""
PaniniFS v3.31: PNG (Portable Network Graphics) Extractor
==========================================================

PNG - Portable Network Graphics raster image format.

Structure:
- PNG signature (8 bytes): 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A
- Chunks (repeating):
  - Length (4 bytes, big-endian): chunk data length
  - Chunk Type (4 bytes): ASCII letters (e.g., IHDR, IDAT, IEND)
  - Chunk Data (variable length)
  - CRC (4 bytes): CRC-32 of type and data

Critical chunks:
- IHDR (Image Header): must be first chunk
  - Width (4 bytes)
  - Height (4 bytes)
  - Bit depth (1 byte): 1, 2, 4, 8, 16
  - Color type (1 byte): 0=grayscale, 2=RGB, 3=indexed, 4=grayscale+alpha, 6=RGBA
  - Compression method (1 byte): always 0 (deflate)
  - Filter method (1 byte): always 0 (adaptive)
  - Interlace method (1 byte): 0=none, 1=Adam7
  
- PLTE (Palette): for indexed color images (color type 3)
  - RGB triplets (3 bytes each)
  
- IDAT (Image Data): compressed pixel data (can be multiple chunks)

- IEND (Image End): must be last chunk, marks end

Ancillary chunks:
- tRNS (Transparency): transparency info
- gAMA (Gamma): image gamma
- cHRM (Chromaticity): color space info
- sRGB (sRGB): standard RGB color space
- iCCP (ICC Profile): embedded ICC profile
- tEXt (Text): uncompressed Latin-1 text
- zTXt (Compressed Text): compressed Latin-1 text
- iTXt (International Text): UTF-8 text
- bKGD (Background): background color
- pHYs (Physical): physical pixel dimensions (DPI)
- sBIT (Significant Bits): significant bits per sample
- tIME (Time): last modification time

Metadata extracted:
- Image dimensions (width, height)
- Bit depth and color type
- Color mode description
- Interlacing
- Compression and filter methods
- Physical dimensions (DPI if present)
- Text metadata (tEXt, zTXt, iTXt)
- Gamma, chromaticity, sRGB
- Transparency info
- Last modification time
- Chunk list and sizes

Format: Binary, big-endian
Compression: DEFLATE (zlib)

Author: PaniniFS Research Team
Version: 3.31
Date: 2025-01-14
"""

import sys
import struct
import zlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class PNGExtractor:
    """Extract metadata from PNG image files."""
    
    # PNG signature
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    # Color types
    COLOR_TYPES = {
        0: "Grayscale",
        2: "RGB",
        3: "Indexed (Palette)",
        4: "Grayscale + Alpha",
        6: "RGBA"
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "PNG (Portable Network Graphics)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "width": None,
            "height": None,
            "bit_depth": None,
            "color_type": None,
            "color_mode": None,
            "interlaced": False,
            "chunks": [],
            "text_metadata": {},
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Verify signature
            if not self._verify_signature():
                raise ValueError("Invalid PNG signature")
            
            # Parse chunks
            self._parse_chunks()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _verify_signature(self) -> bool:
        """Verify PNG signature."""
        if len(self.raw_data) < 8:
            return False
        
        return self.raw_data[:8] == self.PNG_SIGNATURE
    
    def _parse_chunks(self):
        """Parse PNG chunks."""
        offset = 8  # Skip signature
        
        while offset < len(self.raw_data):
            # Check for minimum chunk size
            if offset + 12 > len(self.raw_data):
                break
            
            # Read chunk length
            length = struct.unpack('>I', self.raw_data[offset:offset+4])[0]
            offset += 4
            
            # Read chunk type
            chunk_type = self.raw_data[offset:offset+4].decode('ascii', errors='replace')
            offset += 4
            
            # Read chunk data
            if offset + length + 4 > len(self.raw_data):
                self.data["errors"].append(f"Truncated chunk: {chunk_type}")
                break
            
            chunk_data = self.raw_data[offset:offset+length]
            offset += length
            
            # Read CRC (skip verification for now)
            crc = struct.unpack('>I', self.raw_data[offset:offset+4])[0]
            offset += 4
            
            # Store chunk info
            self.data["chunks"].append({
                "type": chunk_type,
                "size": length
            })
            
            # Parse specific chunks
            if chunk_type == 'IHDR':
                self._parse_ihdr(chunk_data)
            elif chunk_type == 'tEXt':
                self._parse_text(chunk_data)
            elif chunk_type == 'zTXt':
                self._parse_ztxt(chunk_data)
            elif chunk_type == 'iTXt':
                self._parse_itxt(chunk_data)
            elif chunk_type == 'pHYs':
                self._parse_phys(chunk_data)
            elif chunk_type == 'tIME':
                self._parse_time(chunk_data)
            elif chunk_type == 'gAMA':
                self._parse_gama(chunk_data)
            elif chunk_type == 'sRGB':
                self._parse_srgb(chunk_data)
            elif chunk_type == 'tRNS':
                self.data["has_transparency"] = True
            elif chunk_type == 'PLTE':
                self._parse_palette(chunk_data)
            elif chunk_type == 'IEND':
                break
    
    def _parse_ihdr(self, data: bytes):
        """Parse IHDR chunk (Image Header)."""
        if len(data) < 13:
            self.data["errors"].append("Invalid IHDR chunk size")
            return
        
        width = struct.unpack('>I', data[0:4])[0]
        height = struct.unpack('>I', data[4:8])[0]
        bit_depth = data[8]
        color_type = data[9]
        compression = data[10]
        filter_method = data[11]
        interlace = data[12]
        
        self.data["width"] = width
        self.data["height"] = height
        self.data["bit_depth"] = bit_depth
        self.data["color_type"] = color_type
        self.data["color_mode"] = self.COLOR_TYPES.get(color_type, f"Unknown ({color_type})")
        self.data["compression_method"] = compression
        self.data["filter_method"] = filter_method
        self.data["interlaced"] = bool(interlace)
        
        # Calculate total pixels
        self.data["total_pixels"] = width * height
    
    def _parse_text(self, data: bytes):
        """Parse tEXt chunk (uncompressed text)."""
        try:
            # Find null terminator
            null_idx = data.find(b'\x00')
            if null_idx == -1:
                return
            
            keyword = data[:null_idx].decode('latin-1')
            text = data[null_idx+1:].decode('latin-1')
            
            self.data["text_metadata"][keyword] = text
            
        except Exception as e:
            self.data["errors"].append(f"tEXt parse error: {str(e)}")
    
    def _parse_ztxt(self, data: bytes):
        """Parse zTXt chunk (compressed text)."""
        try:
            # Find null terminator
            null_idx = data.find(b'\x00')
            if null_idx == -1:
                return
            
            keyword = data[:null_idx].decode('latin-1')
            compression = data[null_idx+1]
            
            if compression != 0:
                return
            
            compressed = data[null_idx+2:]
            text = zlib.decompress(compressed).decode('latin-1')
            
            self.data["text_metadata"][keyword] = text
            
        except Exception as e:
            self.data["errors"].append(f"zTXt parse error: {str(e)}")
    
    def _parse_itxt(self, data: bytes):
        """Parse iTXt chunk (international text, UTF-8)."""
        try:
            # Find null terminator
            null_idx = data.find(b'\x00')
            if null_idx == -1:
                return
            
            keyword = data[:null_idx].decode('latin-1')
            offset = null_idx + 1
            
            compression_flag = data[offset]
            compression_method = data[offset+1]
            offset += 2
            
            # Language tag
            null_idx = data.find(b'\x00', offset)
            if null_idx == -1:
                return
            language = data[offset:null_idx].decode('ascii', errors='replace')
            offset = null_idx + 1
            
            # Translated keyword
            null_idx = data.find(b'\x00', offset)
            if null_idx == -1:
                return
            offset = null_idx + 1
            
            # Text
            text_data = data[offset:]
            
            if compression_flag:
                text = zlib.decompress(text_data).decode('utf-8', errors='replace')
            else:
                text = text_data.decode('utf-8', errors='replace')
            
            self.data["text_metadata"][keyword] = text
            
        except Exception as e:
            self.data["errors"].append(f"iTXt parse error: {str(e)}")
    
    def _parse_phys(self, data: bytes):
        """Parse pHYs chunk (physical pixel dimensions)."""
        if len(data) < 9:
            return
        
        pixels_per_unit_x = struct.unpack('>I', data[0:4])[0]
        pixels_per_unit_y = struct.unpack('>I', data[4:8])[0]
        unit = data[8]
        
        self.data["pixels_per_unit_x"] = pixels_per_unit_x
        self.data["pixels_per_unit_y"] = pixels_per_unit_y
        
        if unit == 1:  # Meter
            # Convert to DPI (dots per inch)
            dpi_x = round(pixels_per_unit_x * 0.0254)
            dpi_y = round(pixels_per_unit_y * 0.0254)
            self.data["dpi_x"] = dpi_x
            self.data["dpi_y"] = dpi_y
    
    def _parse_time(self, data: bytes):
        """Parse tIME chunk (modification time)."""
        if len(data) < 7:
            return
        
        year = struct.unpack('>H', data[0:2])[0]
        month = data[2]
        day = data[3]
        hour = data[4]
        minute = data[5]
        second = data[6]
        
        try:
            dt = datetime(year, month, day, hour, minute, second)
            self.data["last_modified"] = dt.isoformat()
        except ValueError:
            pass
    
    def _parse_gama(self, data: bytes):
        """Parse gAMA chunk (gamma)."""
        if len(data) < 4:
            return
        
        gamma_int = struct.unpack('>I', data[0:4])[0]
        gamma = gamma_int / 100000.0
        self.data["gamma"] = round(gamma, 5)
    
    def _parse_srgb(self, data: bytes):
        """Parse sRGB chunk."""
        if len(data) < 1:
            return
        
        rendering_intent = data[0]
        intents = {
            0: "Perceptual",
            1: "Relative colorimetric",
            2: "Saturation",
            3: "Absolute colorimetric"
        }
        
        self.data["srgb"] = True
        self.data["rendering_intent"] = intents.get(rendering_intent, f"Unknown ({rendering_intent})")
    
    def _parse_palette(self, data: bytes):
        """Parse PLTE chunk (palette)."""
        if len(data) % 3 != 0:
            return
        
        num_colors = len(data) // 3
        self.data["palette_colors"] = num_colors


def main():
    if len(sys.argv) < 2:
        print("Usage: python png_extractor.py <file.png>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = PNGExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
