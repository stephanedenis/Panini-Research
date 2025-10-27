#!/usr/bin/env python3
"""
INI/CONF Configuration File Format Extractor - PaniniFS v3.40

This extractor analyzes generic INI-style configuration files (.ini, .conf, .cfg).
These files use a simple key-value format with optional section headers.

Format Structure:
- Sections: [SectionName]
- Key-value pairs: key=value or key: value
- Comments: # or ; at line start
- Multi-line values: indentation or backslash continuation
- No escaping (usually plain text)
- Case-sensitive or case-insensitive (application-dependent)

Common Variants:
- Standard INI: [section], key=value
- Python ConfigParser: [section], key=value or key: value
- Systemd-like: [Section], Key=Value (multi-value support)
- Apache-like: Key value (no = sign)
- LDAP config: KEY value (uppercase keys)
- Custom: Application-specific syntax

Key Features:
- Section detection ([Section])
- Key-value parsing (multiple delimiters: =, :, space)
- Comment detection (# and ;)
- Boolean detection (yes/no, true/false, on/off, 0/1)
- Number detection (integer, float)
- List detection (comma-separated values)
- Multi-line value support

This extractor uses Python's configparser module for robust parsing
with fallback to basic parsing for non-standard formats.

Author: PaniniFS Research Team
Version: 3.40
Target: Configuration files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import re
from configparser import ConfigParser, MissingSectionHeaderError, ParsingError

class INIExtractor:
    """Extract metadata from INI/CONF configuration files."""
    
    # Boolean value patterns
    BOOLEAN_TRUE = {"true", "yes", "on", "1", "enabled"}
    BOOLEAN_FALSE = {"false", "no", "off", "0", "disabled"}
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the INI/CONF file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "INI/CONF",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Try standard configparser first
            try:
                parser = ConfigParser(allow_no_value=True, strict=False)
                parser.read_string(content)
                metadata.update(self._parse_with_configparser(parser, content))
                metadata["parser"] = "configparser"
            except (MissingSectionHeaderError, ParsingError) as e:
                # Fallback to basic parsing for non-standard formats
                metadata.update(self._basic_parse(content))
                metadata["parser"] = "basic"
                metadata["configparser_error"] = str(e)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "INI/CONF",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_with_configparser(self, parser: ConfigParser, content: str) -> Dict[str, Any]:
        """Parse using Python's configparser."""
        result = {}
        
        # Count sections
        sections = parser.sections()
        result["section_count"] = len(sections)
        result["sections"] = sections
        
        # Analyze each section
        section_data = {}
        all_keys = set()
        
        for section in sections:
            items = dict(parser.items(section))
            all_keys.update(items.keys())
            
            section_info = {
                "key_count": len(items),
                "keys": list(items.keys()),
            }
            
            # Analyze value types
            value_types = self._analyze_value_types(items)
            section_info["value_types"] = value_types
            
            # Sample values
            samples = {}
            for key, value in list(items.items())[:5]:
                samples[key] = self._analyze_value(value)
            section_info["value_samples"] = samples
            
            section_data[section] = section_info
        
        result["section_details"] = section_data
        result["unique_keys"] = sorted(list(all_keys))[:30]  # Sample
        result["unique_key_count"] = len(all_keys)
        
        # Count comments
        comment_lines = sum(1 for line in content.split('\n') 
                          if line.strip().startswith('#') or line.strip().startswith(';'))
        result["comment_lines"] = comment_lines
        
        return result
    
    def _basic_parse(self, content: str) -> Dict[str, Any]:
        """Basic parsing for non-standard formats."""
        result = {}
        
        lines = content.split('\n')
        result["line_count"] = len(lines)
        
        # Count sections
        sections = []
        for line in lines:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1]
                sections.append(section_name)
        
        result["section_count"] = len(sections)
        if sections:
            result["sections"] = sections
        
        # Count comments
        comment_lines = sum(1 for line in lines 
                          if line.strip().startswith('#') or line.strip().startswith(';'))
        result["comment_lines"] = comment_lines
        
        # Detect keys (various formats)
        keys = set()
        key_patterns = [
            r'^([a-zA-Z_][\w.-]*)\s*=\s*(.*)$',  # key=value
            r'^([a-zA-Z_][\w.-]*)\s*:\s*(.*)$',  # key: value
            r'^([A-Z_]+)\s+(.*)$',                # KEY value
        ]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            if line.startswith('['):
                continue
            
            for pattern in key_patterns:
                match = re.match(pattern, line)
                if match:
                    keys.add(match.group(1))
                    break
        
        if keys:
            result["keys_detected"] = sorted(list(keys))[:30]  # Sample
            result["key_count"] = len(keys)
        
        return result
    
    def _analyze_value_types(self, items: Dict[str, str]) -> Dict[str, int]:
        """Analyze types of values."""
        type_counts = {
            "boolean": 0,
            "integer": 0,
            "float": 0,
            "string": 0,
            "list": 0,
            "empty": 0,
        }
        
        for value in items.values():
            if value is None or value == "":
                type_counts["empty"] += 1
            elif self._is_boolean(value):
                type_counts["boolean"] += 1
            elif self._is_integer(value):
                type_counts["integer"] += 1
            elif self._is_float(value):
                type_counts["float"] += 1
            elif self._is_list(value):
                type_counts["list"] += 1
            else:
                type_counts["string"] += 1
        
        # Remove zero counts
        return {k: v for k, v in type_counts.items() if v > 0}
    
    def _analyze_value(self, value: str) -> Any:
        """Analyze a single value and return typed representation."""
        if value is None or value == "":
            return None
        
        value_lower = value.lower()
        
        # Boolean
        if value_lower in self.BOOLEAN_TRUE:
            return {"type": "boolean", "value": True}
        elif value_lower in self.BOOLEAN_FALSE:
            return {"type": "boolean", "value": False}
        
        # Integer
        if self._is_integer(value):
            return {"type": "integer", "value": int(value)}
        
        # Float
        if self._is_float(value):
            return {"type": "float", "value": float(value)}
        
        # List
        if self._is_list(value):
            items = [item.strip() for item in value.split(',')]
            return {"type": "list", "items": items[:5], "length": len(items)}
        
        # String
        return {"type": "string", "value": value[:100]}
    
    def _is_boolean(self, value: str) -> bool:
        """Check if value is a boolean."""
        value_lower = value.lower()
        return value_lower in self.BOOLEAN_TRUE or value_lower in self.BOOLEAN_FALSE
    
    def _is_integer(self, value: str) -> bool:
        """Check if value is an integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def _is_float(self, value: str) -> bool:
        """Check if value is a float."""
        try:
            float(value)
            return '.' in value or 'e' in value.lower()
        except ValueError:
            return False
    
    def _is_list(self, value: str) -> bool:
        """Check if value is a comma-separated list."""
        return ',' in value and len(value.split(',')) > 1

def main():
    if len(sys.argv) < 2:
        print("Usage: ini_extractor.py <ini_or_conf_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = INIExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
