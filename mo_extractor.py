#!/usr/bin/env python3
"""
PaniniFS v3.24: MO (GNU Message Catalog) Format Extractor
==========================================================

GNU gettext binary message catalog format (.mo files).

Structure (binary):
- Magic: 0x950412DE (little-endian) or 0xDE120495 (big-endian)
- Revision: Major.minor version
- String count: N (number of messages)
- Original strings offset table (N entries)
- Translated strings offset table (N entries)
- Hash table size and offset
- String data (NUL-terminated)

Header entry (empty msgid):
- Contains metadata as key: value pairs
- Project-Id-Version
- POT-Creation-Date
- PO-Revision-Date
- Last-Translator
- Language-Team
- Language
- MIME-Version
- Content-Type
- Content-Transfer-Encoding
- Plural-Forms

Metadata extracted:
- Magic number and byte order
- Revision version
- Message count
- Project information
- Language code
- Plural forms definition
- Translator information
- Sample message pairs (original → translation)
- Statistics

Format: Binary, structured
Encoding: UTF-8 (typically)
Endianness: Little or big-endian

Sample usage:
MO files are used by gettext for runtime i18n/l10n.
Common locations: /usr/share/locale/*/LC_MESSAGES/*.mo

Author: PaniniFS Research Team
Version: 3.25
Date: 2025-01-14
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class MOExtractor:
    """Extract metadata from GNU gettext .mo files."""
    
    # Magic numbers
    MO_MAGIC_LE = 0x950412DE  # Little-endian
    MO_MAGIC_BE = 0xDE120495  # Big-endian
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        self.is_big_endian = False
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "GNU Message Catalog (MO)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "magic": None,
            "byte_order": None,
            "revision": None,
            "metadata": {},
            "messages": [],
            "statistics": {},
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Parse header
            self._parse_header()
            
            # Parse strings
            self._parse_strings()
            
            # Calculate statistics
            self._calculate_statistics()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_header(self):
        """Parse MO file header."""
        if len(self.raw_data) < 28:
            raise ValueError("File too small to be valid MO")
        
        # Read magic
        magic = struct.unpack('<I', self.raw_data[0:4])[0]
        
        if magic == self.MO_MAGIC_LE:
            self.is_big_endian = False
            self.data["byte_order"] = "little-endian"
        elif magic == self.MO_MAGIC_BE:
            self.is_big_endian = True
            self.data["byte_order"] = "big-endian"
        else:
            # Try swapping
            magic_swapped = struct.unpack('>I', self.raw_data[0:4])[0]
            if magic_swapped == self.MO_MAGIC_BE:
                self.is_big_endian = True
                self.data["byte_order"] = "big-endian"
            else:
                raise ValueError(f"Invalid MO magic: {magic:08X}")
        
        self.data["magic"] = f"{magic:08X}"
        
        # Choose struct format
        fmt = '>' if self.is_big_endian else '<'
        
        # Parse header fields
        # Offset 4: Revision
        revision = struct.unpack(f'{fmt}I', self.raw_data[4:8])[0]
        major = revision >> 16
        minor = revision & 0xFFFF
        self.data["revision"] = f"{major}.{minor}"
        
        # Offset 8: Number of strings
        self.num_strings = struct.unpack(f'{fmt}I', self.raw_data[8:12])[0]
        
        # Offset 12: Offset of original strings table
        self.orig_table_offset = struct.unpack(f'{fmt}I', self.raw_data[12:16])[0]
        
        # Offset 16: Offset of translated strings table
        self.trans_table_offset = struct.unpack(f'{fmt}I', self.raw_data[16:20])[0]
        
        # Offset 20: Hash table size
        self.hash_size = struct.unpack(f'{fmt}I', self.raw_data[20:24])[0]
        
        # Offset 24: Hash table offset
        self.hash_offset = struct.unpack(f'{fmt}I', self.raw_data[24:28])[0]
    
    def _parse_strings(self):
        """Parse original and translated strings."""
        fmt = '>' if self.is_big_endian else '<'
        
        # Read first message (header with metadata)
        if self.num_strings > 0:
            # First entry should be empty msgid with metadata
            orig_len, orig_offset = self._read_string_descriptor(
                self.orig_table_offset, 0, fmt
            )
            trans_len, trans_offset = self._read_string_descriptor(
                self.trans_table_offset, 0, fmt
            )
            
            # Read header metadata
            if orig_len == 0 and trans_len > 0:
                header = self._read_string(trans_offset, trans_len)
                self._parse_metadata(header)
        
        # Sample other messages (skip header)
        sample_count = min(20, self.num_strings - 1)
        
        for i in range(1, sample_count + 1):
            if i >= self.num_strings:
                break
            
            try:
                orig_len, orig_offset = self._read_string_descriptor(
                    self.orig_table_offset, i, fmt
                )
                trans_len, trans_offset = self._read_string_descriptor(
                    self.trans_table_offset, i, fmt
                )
                
                original = self._read_string(orig_offset, orig_len)
                translation = self._read_string(trans_offset, trans_len)
                
                if original:  # Skip empty
                    self.data["messages"].append({
                        "original": original[:200],
                        "translation": translation[:200] if translation else ""
                    })
            except Exception:
                continue
    
    def _read_string_descriptor(self, table_offset: int, index: int, fmt: str) -> Tuple[int, int]:
        """Read string length and offset from descriptor table."""
        offset = table_offset + (index * 8)
        
        if offset + 8 > len(self.raw_data):
            return 0, 0
        
        length = struct.unpack(f'{fmt}I', self.raw_data[offset:offset+4])[0]
        str_offset = struct.unpack(f'{fmt}I', self.raw_data[offset+4:offset+8])[0]
        
        return length, str_offset
    
    def _read_string(self, offset: int, length: int) -> str:
        """Read string from data section."""
        if offset + length > len(self.raw_data):
            return ""
        
        data = self.raw_data[offset:offset+length]
        
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return data.decode('latin-1')
            except:
                return data.hex()
    
    def _parse_metadata(self, header: str):
        """Parse metadata from header entry."""
        lines = header.split('\n')
        
        metadata = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Common metadata fields
                if key == 'Project-Id-Version':
                    metadata['project'] = value
                elif key == 'Language':
                    metadata['language'] = value
                elif key == 'PO-Revision-Date':
                    metadata['revision_date'] = value
                elif key == 'Last-Translator':
                    metadata['translator'] = value
                elif key == 'Language-Team':
                    metadata['team'] = value
                elif key == 'Plural-Forms':
                    metadata['plural_forms'] = value
                elif key == 'Content-Type':
                    metadata['content_type'] = value
        
        self.data["metadata"] = metadata
    
    def _calculate_statistics(self):
        """Calculate MO statistics."""
        self.data["statistics"] = {
            "total_messages": self.num_strings - 1,  # Exclude header
            "sampled_messages": len(self.data["messages"]),
            "has_metadata": bool(self.data["metadata"]),
            "hash_table_size": self.hash_size,
            "language": self.data["metadata"].get("language"),
            "project": self.data["metadata"].get("project")
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python mo_extractor.py <file.mo>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = MOExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
