#!/usr/bin/env python3
"""
JSON Format Extractor - PaniniFS v3.39

This extractor analyzes JSON (JavaScript Object Notation) files.
JSON is a lightweight data interchange format that is easy for humans
to read and write and easy for machines to parse and generate.

Format Structure:
- Objects: {"key": "value"}
- Arrays: [value1, value2, value3]
- Values: string, number, object, array, true, false, null
- Strings: Double-quoted with escape sequences
- Numbers: Integer or floating-point (scientific notation supported)
- Whitespace insensitive

Data Types:
- string: "text"
- number: 123, 1.23, 1.23e-10
- boolean: true, false
- null: null
- object: {}
- array: []

Common Use Cases:
- Configuration files (package.json, tsconfig.json, settings.json)
- API responses and requests (REST APIs)
- Data storage and exchange
- Browser extensions (manifest.json)
- Application settings
- Log files (structured logging)
- Database exports (MongoDB, CouchDB)

This extractor provides:
- Structure analysis (keys, nesting depth)
- Data type statistics
- Key path enumeration
- Value sampling
- Array/object size statistics
- Root type detection
- Schema hints (common patterns)

Author: PaniniFS Research Team
Version: 3.39
Target: JSON files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

class JSONExtractor:
    """Extract metadata from JSON files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the JSON file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "JSON",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Parse JSON
            try:
                data = json.loads(content)
                metadata.update(self._analyze_data(data))
            except json.JSONDecodeError as e:
                metadata["parse_error"] = {
                    "message": str(e),
                    "line": e.lineno,
                    "column": e.colno,
                    "position": e.pos
                }
            
            return metadata
            
        except Exception as e:
            return {
                "format": "JSON",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        """Analyze parsed JSON data."""
        result = {}
        
        # Root type
        root_type = type(data).__name__
        result["root_type"] = root_type
        
        # Analyze structure
        keys, types, depth = self._analyze_structure(data)
        
        result["unique_keys"] = sorted(list(keys))[:30]  # Sample
        result["unique_key_count"] = len(keys)
        result["data_types"] = sorted(list(types))
        result["max_nesting_depth"] = depth
        
        # Root-level analysis
        if isinstance(data, dict):
            result["root_object"] = self._analyze_object(data)
        elif isinstance(data, list):
            result["root_array"] = self._analyze_array(data)
        else:
            result["root_value"] = self._sample_value(data)
        
        # Detect common schema patterns
        schema_hints = self._detect_schema_patterns(data)
        if schema_hints:
            result["schema_hints"] = schema_hints
        
        return result
    
    def _analyze_structure(self, obj: Any, prefix: str = "", depth: int = 0) -> tuple:
        """Recursively analyze JSON structure."""
        keys = set()
        types = set()
        max_depth = depth
        
        # Get type name
        type_name = type(obj).__name__
        types.add(type_name)
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Add key path
                key_path = f"{prefix}.{key}" if prefix else key
                keys.add(key_path)
                
                # Recurse into value
                sub_keys, sub_types, sub_depth = self._analyze_structure(
                    value, key_path, depth + 1
                )
                keys.update(sub_keys)
                types.update(sub_types)
                max_depth = max(max_depth, sub_depth)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                # Sample first few items
                if i < 3:
                    item_path = f"{prefix}[{i}]" if prefix else f"[{i}]"
                    sub_keys, sub_types, sub_depth = self._analyze_structure(
                        item, item_path, depth + 1
                    )
                    keys.update(sub_keys)
                    types.update(sub_types)
                    max_depth = max(max_depth, sub_depth)
        
        return keys, types, max_depth
    
    def _analyze_object(self, obj: dict) -> Dict[str, Any]:
        """Analyze a JSON object."""
        analysis = {
            "key_count": len(obj),
            "keys": list(obj.keys())[:20],  # Sample
        }
        
        # Type distribution
        type_counts = {}
        for value in obj.values():
            value_type = type(value).__name__
            type_counts[value_type] = type_counts.get(value_type, 0) + 1
        analysis["value_types"] = type_counts
        
        # Sample values
        samples = {}
        for key, value in list(obj.items())[:5]:
            samples[key] = self._sample_value(value)
        analysis["value_samples"] = samples
        
        return analysis
    
    def _analyze_array(self, arr: list) -> Dict[str, Any]:
        """Analyze a JSON array."""
        analysis = {
            "length": len(arr),
        }
        
        # Type distribution
        type_counts = {}
        for item in arr:
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        analysis["item_types"] = type_counts
        
        # Sample items
        samples = []
        for item in arr[:3]:
            samples.append(self._sample_value(item))
        analysis["item_samples"] = samples
        
        # Check if all items are same type
        if len(type_counts) == 1:
            analysis["homogeneous"] = True
        else:
            analysis["homogeneous"] = False
        
        return analysis
    
    def _sample_value(self, value: Any, max_str_len: int = 100) -> Any:
        """Create a sample representation of a value."""
        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            if len(value) > max_str_len:
                return value[:max_str_len] + "..."
            return value
        elif isinstance(value, dict):
            return {
                "_type": "object",
                "_keys": list(value.keys())[:10],
                "_size": len(value)
            }
        elif isinstance(value, list):
            return {
                "_type": "array",
                "_length": len(value),
                "_first": self._sample_value(value[0]) if value else None
            }
        else:
            return {
                "_type": type(value).__name__,
                "_repr": str(value)[:100]
            }
    
    def _detect_schema_patterns(self, data: Any) -> List[str]:
        """Detect common JSON schema patterns."""
        hints = []
        
        if isinstance(data, dict):
            keys = set(data.keys())
            
            # Package.json pattern
            if "name" in keys and "version" in keys:
                if "dependencies" in keys or "devDependencies" in keys:
                    hints.append("npm_package")
                elif "scripts" in keys:
                    hints.append("package_metadata")
            
            # Manifest.json pattern
            if "manifest_version" in keys:
                hints.append("browser_extension_manifest")
            
            # tsconfig.json pattern
            if "compilerOptions" in keys:
                hints.append("typescript_config")
            
            # composer.json pattern
            if "require" in keys and ("autoload" in keys or "type" in keys):
                hints.append("php_composer")
            
            # Generic config pattern
            if "settings" in keys or "config" in keys or "configuration" in keys:
                hints.append("configuration_file")
            
            # API response pattern
            if "data" in keys and ("status" in keys or "error" in keys):
                hints.append("api_response")
            
            # Schema pattern
            if "$schema" in keys:
                hints.append("json_schema")
                schema_url = data.get("$schema", "")
                if "draft-07" in schema_url:
                    hints.append("json_schema_draft07")
        
        elif isinstance(data, list):
            # Check if it's an array of objects with same keys
            if data and all(isinstance(item, dict) for item in data):
                # Get keys from first item
                first_keys = set(data[0].keys())
                # Check if all items have similar keys
                if all(set(item.keys()) == first_keys for item in data[:10]):
                    hints.append("array_of_records")
        
        return hints

def main():
    if len(sys.argv) < 2:
        print("Usage: json_extractor.py <json_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = JSONExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
