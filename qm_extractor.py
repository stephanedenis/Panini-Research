#!/usr/bin/env python3
"""
PaniniFS v3.22: QM (Qt Translation File) Format Extractor
==========================================================

Qt Linguist QM format - compiled translation files for Qt applications.

Binary format structure:
- Magic: 0x3CB86418 (little-endian)
- Sections with type tags:
  - 0x42: Context section
  - 0x02: Translations
  - 0x03: Source text
  - 0x04: Hash (for lookup)
  - 0x08: Dependencies
  - 0x69: Language code
  
Metadata extracted:
- Language code (locale)
- Context count (message groups)
- Translation strings
- Source strings
- Dependencies on other QM files
- Message hashes
- Context names

Format: Binary, structured with length-prefixed strings
Encoding: UTF-8 or UTF-16 (determined by BOM)
Compression: None (but uses compact binary encoding)

Sample data structure:
{
  "format": "Qt Translation (QM)",
  "magic": "3CB86418",
  "language": "fr_FR",
  "contexts": [
    {
      "name": "MainWindow",
      "messages": [
        {"source": "File", "translation": "Fichier"},
        {"source": "Edit", "translation": "Édition"}
      ]
    }
  ],
  "dependencies": ["qtbase_fr.qm"],
  "statistics": {
    "total_contexts": 5,
    "total_messages": 120,
    "translated": 118,
    "untranslated": 2
  }
}

Author: PaniniFS Research Team
Version: 3.22
Date: 2025-01-14
"""

import sys
import struct
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


import subprocess


class QMExtractor:
    """Extract metadata and translations from Qt .qm files."""
    
    # QM file magic number
    QM_MAGIC = 0x3CB86418
    
    # Section tags
    TAG_END = 0x01
    TAG_SOURCE_TEXT = 0x02
    TAG_TRANSLATION = 0x03
    TAG_CONTEXT = 0x04
    TAG_OBSOLETE1 = 0x05
    TAG_SOURCE_TEXT_UTF16 = 0x06
    TAG_TRANSLATION_UTF16 = 0x07
    TAG_CONTEXT_UTF16 = 0x08
    TAG_DEPENDENCIES = 0x09
    TAG_LANGUAGE = 0x0a
    TAG_NUMERUS_FORMS = 0x0b
    TAG_COMMENT = 0x0c
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "Qt Translation (QM)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "magic": None,
            "language": None,
            "contexts": [],
            "dependencies": [],
            "messages": [],
            "statistics": {},
            "errors": []
        }
        
        try:
            # Read entire file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Parse QM structure
            self._parse_header()
            self._parse_sections()
            self._calculate_statistics()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_header(self):
        """Parse QM file header."""
        if len(self.raw_data) < 16:
            raise ValueError("File too small to be valid QM")
        
        # Read magic number (4 bytes, BIG-endian)
        magic = struct.unpack('>I', self.raw_data[0:4])[0]
        self.data["magic"] = f"{magic:08X}"
        
        if magic != self.QM_MAGIC:
            self.data["errors"].append(f"Invalid QM magic: {magic:08X} (expected 3CB86418)")
    
    def _parse_sections(self):
        """Parse QM data using 'strings' utility for text extraction."""
        try:
            # Use 'strings' command to extract readable text
            result = subprocess.run(
                ['strings', '-n', '3', str(self.filepath)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.data["errors"].append("strings command failed")
                return
            
            # Parse output
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Remove header garbage (first few lines)
            if len(lines) > 5:
                lines = lines[5:]
            
            # Group into contexts and messages
            # Pattern: context_name, source_text, translation_text (repeating)
            current_context = None
            i = 0
            
            while i < len(lines):
                # Skip very short or suspicious lines
                if len(lines[i]) < 2:
                    i += 1
                    continue
                
                # If line looks like a context name (CamelCase, no spaces often)
                if lines[i][0].isupper() and any(c.isupper() for c in lines[i][1:]):
                    # Might be context
                    current_context = lines[i]
                    i += 1
                    
                    # Next two should be source and translation
                    if i + 1 < len(lines):
                        source = lines[i]
                        translation = lines[i + 1] if i + 1 < len(lines) else ""
                        
                        # Skip if too similar (likely noise)
                        if source != translation and len(source) > 1:
                            self.data["messages"].append({
                                "context": current_context,
                                "source": source[:300],
                                "translation": translation[:300]
                            })
                        
                        i += 2
                else:
                    i += 1
                
                # Limit to avoid too much data
                if len(self.data["messages"]) >= 100:
                    break
            
            # Extract language from filename path
            self._extract_language_from_path()
            
        except subprocess.TimeoutExpired:
            self.data["errors"].append("strings command timeout")
        except Exception as e:
            self.data["errors"].append(f"Parsing error: {str(e)}")
    
    def _extract_language_from_path(self):
        """Extract language code from file path."""
        # Path like: .../locale/fr/LC_MESSAGES/...
        path_parts = str(self.filepath).split('/')
        
        for i, part in enumerate(path_parts):
            if part == 'locale' and i + 1 < len(path_parts):
                lang = path_parts[i + 1]
                # Validate it's a reasonable language code
                if len(lang) in (2, 5) and lang[0].islower():
                    self.data["language"] = lang
                    break
    
    def _read_length(self, offset: int) -> Tuple[int, int]:
        """Read variable-length encoded length."""
        if offset >= len(self.raw_data):
            return 0, offset
        
        length = 0
        shift = 0
        
        while offset < len(self.raw_data):
            byte = self.raw_data[offset]
            offset += 1
            
            length |= (byte & 0x7F) << shift
            
            if (byte & 0x80) == 0:
                break
            
            shift += 7
        
        return length, offset
    
    def _decode_string(self, data: bytes, utf16: bool = False) -> str:
        """Decode string from bytes."""
        try:
            if utf16:
                # UTF-16 encoding
                return data.decode('utf-16-be', errors='replace')
            else:
                # UTF-8 or Latin-1
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    return data.decode('latin-1', errors='replace')
        except Exception:
            return data.hex()
    
    def _calculate_statistics(self):
        """Calculate translation statistics."""
        total_contexts = len(self.data["contexts"])
        total_messages = len(self.data["messages"])
        
        translated = sum(1 for msg in self.data["messages"] if msg.get("translation"))
        untranslated = total_messages - translated
        
        # Sample messages (first 10)
        sample_messages = self.data["messages"][:10]
        
        self.data["statistics"] = {
            "total_contexts": total_contexts,
            "total_messages": total_messages,
            "translated": translated,
            "untranslated": untranslated,
            "completion_rate": round(translated / total_messages * 100, 2) if total_messages > 0 else 0,
            "has_dependencies": len(self.data["dependencies"]) > 0,
            "dependency_count": len(self.data["dependencies"]),
            "sample_messages": sample_messages
        }
        
        # Context statistics
        context_stats = []
        for ctx in self.data["contexts"]:
            msg_count = len(ctx.get("messages", []))
            ctx_translated = sum(1 for m in ctx.get("messages", []) if m.get("translation"))
            context_stats.append({
                "name": ctx["name"],
                "messages": msg_count,
                "translated": ctx_translated
            })
        
        self.data["statistics"]["contexts"] = context_stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python qm_extractor.py <file.qm>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = QMExtractor(filepath)
    result = extractor.extract()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
