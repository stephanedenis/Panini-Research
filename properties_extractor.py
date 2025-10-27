#!/usr/bin/env python3
"""
Java Properties Format Extractor - PaniniFS v3.47

This extractor analyzes Java .properties configuration files.
Properties files are simple key-value configuration files used by Java applications
and many other systems.

Format Structure:
- Key-value pairs: key=value or key:value or key value
- Comments: # comment or ! comment
- Continuation lines: backslash at end of line
- Unicode escapes: \\uXXXX
- Empty lines: ignored
- Whitespace: trimmed around keys/values

Key-Value Formats:
- key=value
- key:value  
- key value (space separator)
- key = value (spaces around separator)
- key: value (spaces around separator)

Special Characters:
- \\n: newline
- \\r: carriage return
- \\t: tab
- \\\\: backslash
- \\uXXXX: Unicode character

Continuation:
```
long.key=This is a very long value that \\
         continues on the next line
```

Comments:
- # This is a comment
- ! This is also a comment
- Leading whitespace before # or ! is ignored

Use Cases:
- Java application configuration
- Internationalization (i18n) resource bundles
- JVM configuration (logging, management, security)
- Build tool configuration (Maven, Ant)
- Font mappings
- System preferences

Common Files:
- application.properties (Spring Boot)
- log4j.properties (Log4j logging)
- hibernate.properties (Hibernate ORM)
- *_en.properties, *_fr.properties (i18n bundles)
- logging.properties (JVM logging)
- management.properties (JMX)

This extractor provides:
- Key-value pair counting
- Key analysis (length, patterns, hierarchy)
- Value type detection (boolean, numeric, path, URL, etc.)
- Comment analysis
- Continuation line detection
- Unicode escape detection
- Key hierarchy analysis (dot-separated)
- Multi-line value support
- Encoding detection

Author: PaniniFS Research Team
Version: 3.47
Target: .properties files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import re

class PropertiesExtractor:
    """Extract metadata from Java .properties files."""
    
    # Key-value patterns (in order of precedence)
    PATTERNS = [
        re.compile(r'^([^#!:=\s][^:=]*?)\s*[:=]\s*(.*)$'),  # key=value or key:value
        re.compile(r'^([^#!:=\s][^\s]*?)\s+(.*)$'),         # key value
    ]
    
    # Comment pattern
    COMMENT = re.compile(r'^\s*[#!](.*)$')
    
    # Unicode escape pattern
    UNICODE_ESCAPE = re.compile(r'\\u[0-9a-fA-F]{4}')
    
    # Value type patterns
    BOOL_PATTERN = re.compile(r'^(true|false|yes|no|on|off)$', re.IGNORECASE)
    INT_PATTERN = re.compile(r'^-?\d+$')
    FLOAT_PATTERN = re.compile(r'^-?\d+\.\d+$')
    PATH_PATTERN = re.compile(r'^[/\\]|^[A-Za-z]:[/\\]|^\.\.?[/\\]')
    URL_PATTERN = re.compile(r'^[a-z]+://')
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the properties file."""
        try:
            # Read file (try UTF-8, fallback to Latin-1)
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                encoding = 'UTF-8'
            except UnicodeDecodeError:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                encoding = 'Latin-1'
            
            metadata = {
                "format": "Java Properties",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "encoding": encoding,
            }
            
            # Parse properties
            properties = self._parse_properties(lines)
            
            # Analyze properties
            analysis = self._analyze_properties(properties, lines)
            metadata.update(analysis)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Java Properties",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_properties(self, lines: List[str]) -> List[Tuple[str, str]]:
        """Parse properties file into key-value pairs."""
        properties = []
        current_key = None
        current_value = None
        
        for line in lines:
            # Remove newline
            line = line.rstrip('\n\r')
            
            # Check if continuation of previous line
            if current_key is not None:
                # Previous line ended with backslash
                current_value += line.lstrip()
                
                # Check if this line also continues
                if not line.endswith('\\'):
                    # End of multi-line value
                    properties.append((current_key, current_value.rstrip('\\')))
                    current_key = None
                    current_value = None
                continue
            
            # Skip blank lines
            if not line.strip():
                continue
            
            # Skip comments
            if self.COMMENT.match(line):
                continue
            
            # Try to match key-value patterns
            matched = False
            for pattern in self.PATTERNS:
                match = pattern.match(line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    
                    # Check for continuation
                    if value.endswith('\\'):
                        current_key = key
                        current_value = value
                    else:
                        properties.append((key, value))
                    
                    matched = True
                    break
            
            # If no pattern matched and line is not comment, might be malformed
            if not matched and line.strip() and not line.strip().startswith(('#', '!')):
                # Try to extract key only
                key = line.strip().split()[0] if line.strip().split() else line.strip()
                if key:
                    properties.append((key, ''))
        
        return properties
    
    def _analyze_properties(self, properties: List[Tuple[str, str]], 
                           lines: List[str]) -> Dict[str, Any]:
        """Analyze parsed properties."""
        result = {}
        
        # Line counts
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if self.COMMENT.match(line))
        blank_lines = sum(1 for line in lines if not line.strip())
        property_lines = total_lines - comment_lines - blank_lines
        
        result["line_counts"] = {
            "total": total_lines,
            "properties": property_lines,
            "comments": comment_lines,
            "blank": blank_lines,
        }
        
        # Property counts
        result["property_count"] = len(properties)
        
        if not properties:
            return result
        
        # Key analysis
        keys = [k for k, v in properties]
        
        key_lengths = [len(k) for k in keys]
        result["key_statistics"] = {
            "total_keys": len(keys),
            "unique_keys": len(set(keys)),
            "avg_key_length": round(sum(key_lengths) / len(key_lengths), 1),
            "max_key_length": max(key_lengths),
            "min_key_length": min(key_lengths),
        }
        
        # Key hierarchy (dot-separated keys)
        hierarchical_keys = [k for k in keys if '.' in k]
        if hierarchical_keys:
            result["key_hierarchy"] = {
                "hierarchical_count": len(hierarchical_keys),
                "max_depth": max(k.count('.') + 1 for k in hierarchical_keys),
                "prefixes": list(set(k.split('.')[0] for k in hierarchical_keys))[:20],
            }
        
        # Value analysis
        values = [v for k, v in properties]
        
        value_types = {
            "boolean": 0,
            "integer": 0,
            "float": 0,
            "path": 0,
            "url": 0,
            "empty": 0,
            "string": 0,
        }
        
        unicode_escapes = 0
        
        for value in values:
            if not value:
                value_types["empty"] += 1
            elif self.BOOL_PATTERN.match(value):
                value_types["boolean"] += 1
            elif self.INT_PATTERN.match(value):
                value_types["integer"] += 1
            elif self.FLOAT_PATTERN.match(value):
                value_types["float"] += 1
            elif self.PATH_PATTERN.match(value):
                value_types["path"] += 1
            elif self.URL_PATTERN.match(value):
                value_types["url"] += 1
            else:
                value_types["string"] += 1
            
            # Check for unicode escapes
            if self.UNICODE_ESCAPE.search(value):
                unicode_escapes += 1
        
        result["value_types"] = {k: v for k, v in value_types.items() if v > 0}
        
        if unicode_escapes > 0:
            result["unicode_escapes"] = unicode_escapes
        
        # Sample properties
        samples = []
        for key, value in properties[:10]:
            sample = {
                "key": key,
                "value": value[:100] if len(value) > 100 else value,
            }
            if len(value) > 100:
                sample["value_truncated"] = True
            samples.append(sample)
        
        result["property_samples"] = samples
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: properties_extractor.py <properties_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = PropertiesExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
