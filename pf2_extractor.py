#!/usr/bin/env python3
"""
PaniniFS v3.26: PF2 (GRUB2 Font) Format Extractor
==================================================

GRUB2 PFF2 (Portable Font Format 2) font files.

Structure (binary):
- Magic: FILE (4 bytes ASCII: 0x46 0x49 0x4C 0x45)
- Section marker: PFF2 (4 bytes)
- Sections with chunk headers:
  - NAME: Font family name
  - FAMI: Font family (alternative)
  - WEIG: Weight (e.g., "bold")
  - SLAN: Slant (e.g., "normal", "italic")
  - PTSZ: Point size
  - MAXW: Maximum character width
  - MAXH: Maximum character height
  - ASCE: Ascent
  - DESC: Descent
  - CHIX: Character index
  - DATA: Glyph bitmap data

Chunk format:
- Type: 4-byte ASCII identifier
- Length: 4-byte little-endian uint32
- Data: Variable length

Metadata extracted:
- Font family name
- Weight (normal, bold, etc.)
- Slant (normal, italic, etc.)
- Point size
- Maximum dimensions (width, height)
- Ascent and descent
- Character count
- Glyph data size

Format: Binary, chunk-based
Encoding: ASCII for headers, binary for glyph data

Sample fonts:
- DejaVu Sans, DejaVu Serif, Unifont
- Common in GRUB2 themes
- Locations: /boot/grub2/fonts/, /boot/grub2/themes/*/

Author: PaniniFS Research Team
Version: 3.26
Date: 2025-01-14
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, Optional


class PF2Extractor:
    """Extract metadata from GRUB2 .pf2 font files."""
    
    # Expected magic
    FILE_MAGIC = b'FILE'
    PFF2_MAGIC = b'PFF2'
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "GRUB2 Font (PF2)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "font_family": None,
            "weight": None,
            "slant": None,
            "point_size": None,
            "max_width": None,
            "max_height": None,
            "ascent": None,
            "descent": None,
            "character_count": None,
            "glyph_data_size": None,
            "chunks": [],
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Verify magic
            self._verify_magic()
            
            # Parse chunks
            self._parse_chunks()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _verify_magic(self):
        """Verify PF2 file signature."""
        if len(self.raw_data) < 12:
            raise ValueError("File too small")
        
        if self.raw_data[0:4] != self.FILE_MAGIC:
            raise ValueError("Invalid FILE magic")
        
        # Skip section count/length (4 bytes at offset 4-7)
        # Offset 8-11 should be PFF2
        if self.raw_data[8:12] != self.PFF2_MAGIC:
            raise ValueError("Invalid PFF2 magic")
    
    def _parse_chunks(self):
        """Parse PF2 chunks."""
        offset = 12  # Skip FILE (4) + section length (4) + PFF2 (4)
        
        while offset + 8 <= len(self.raw_data):
            # Read chunk header
            chunk_type = self.raw_data[offset:offset+4]
            
            if chunk_type == b'\x00\x00\x00\x00':
                break  # End marker
            
            # Read chunk length (BIG-endian)
            chunk_len = struct.unpack('>I', self.raw_data[offset+4:offset+8])[0]
            
            offset += 8
            
            # Check bounds
            if offset + chunk_len > len(self.raw_data):
                self.data["errors"].append(f"Chunk extends beyond file: {chunk_type}")
                break
            
            # Extract chunk data
            chunk_data = self.raw_data[offset:offset+chunk_len]
            
            # Process by type
            try:
                chunk_type_str = chunk_type.decode('ascii', errors='replace')
            except:
                chunk_type_str = chunk_type.hex()
            
            self.data["chunks"].append({
                "type": chunk_type_str,
                "length": chunk_len
            })
            
            # Parse specific chunks
            if chunk_type == b'NAME':
                self.data["font_family"] = self._decode_string(chunk_data)
            elif chunk_type == b'FAMI':
                if not self.data["font_family"]:
                    self.data["font_family"] = self._decode_string(chunk_data)
            elif chunk_type == b'WEIG':
                self.data["weight"] = self._decode_string(chunk_data)
            elif chunk_type == b'SLAN':
                self.data["slant"] = self._decode_string(chunk_data)
            elif chunk_type == b'PTSZ' and chunk_len >= 2:
                self.data["point_size"] = struct.unpack('>H', chunk_data[0:2])[0]
            elif chunk_type == b'MAXW' and chunk_len >= 2:
                self.data["max_width"] = struct.unpack('>H', chunk_data[0:2])[0]
            elif chunk_type == b'MAXH' and chunk_len >= 2:
                self.data["max_height"] = struct.unpack('>H', chunk_data[0:2])[0]
            elif chunk_type == b'ASCE' and chunk_len >= 2:
                self.data["ascent"] = struct.unpack('>H', chunk_data[0:2])[0]
            elif chunk_type == b'DESC' and chunk_len >= 2:
                self.data["descent"] = struct.unpack('>H', chunk_data[0:2])[0]
            elif chunk_type == b'CHIX':
                # Character index - count entries
                # Each entry: 4 bytes code + 1 byte flags + 4 bytes offset
                entry_size = 9
                count = chunk_len // entry_size
                self.data["character_count"] = count
            elif chunk_type == b'DATA':
                self.data["glyph_data_size"] = chunk_len
            
            offset += chunk_len
    
    def _decode_string(self, data: bytes) -> str:
        """Decode null-terminated string."""
        # Find null terminator
        null_pos = data.find(b'\x00')
        if null_pos != -1:
            data = data[:null_pos]
        
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.decode('latin-1', errors='replace')


def main():
    if len(sys.argv) < 2:
        print("Usage: python pf2_extractor.py <file.pf2>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = PF2Extractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
