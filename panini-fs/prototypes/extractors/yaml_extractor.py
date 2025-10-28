#!/usr/bin/env python3
"""
YAML Format Extractor - PaniniFS v3.38

This extractor analyzes YAML (YAML Ain't Markup Language) files.
YAML is a human-readable data serialization format commonly used for
configuration files, data exchange, and structured data storage.

Format Structure:
- Key-value pairs: key: value
- Nested structures with indentation
- Lists with - prefix
- Multi-line strings with | (literal) or > (folded)
- Comments start with #
- Multiple documents separated by ---
- Document end marker: ...

Data Types:
- Scalars: strings, numbers, booleans, null
- Sequences: lists/arrays
- Mappings: dictionaries/objects
- Anchors & aliases: &anchor, *alias
- Tags: !!str, !!int, !!bool, etc.

Special Values:
- null: null, Null, NULL, ~
- true: true, True, TRUE, yes, Yes, YES, on, On, ON
- false: false, False, FALSE, no, No, NO, off, Off, OFF
- Numbers: 123, 1.23, 1.23e-10, 0x1A (hex), 0o17 (octal)

Common Use Cases:
- Configuration files (application settings)
- CI/CD pipelines (.gitlab-ci.yml, .github/workflows)
- Kubernetes manifests (deployment, service, pod)
- Ansible playbooks
- Docker Compose (docker-compose.yml)
- OpenAPI specifications

This extractor uses PyYAML for robust parsing and provides:
- Document count (multiple documents in one file)
- Structure analysis (keys, nesting depth)
- Data type statistics
- Key path enumeration
- Value sampling

Author: PaniniFS Research Team
Version: 3.38
Target: YAML files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import re

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

class YAMLExtractor:
    """Extract metadata from YAML files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the YAML file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "YAML",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            if not HAS_YAML:
                # Fallback: basic parsing without PyYAML
                metadata.update(self._basic_parse(content))
            else:
                # Full parsing with PyYAML
                metadata.update(self._full_parse(content))
            
            return metadata
            
        except Exception as e:
            return {
                "format": "YAML",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _basic_parse(self, content: str) -> Dict[str, Any]:
        """Basic parsing without PyYAML (fallback)."""
        result = {}
        
        # Count lines
        lines = content.split('\n')
        result["line_count"] = len(lines)
        
        # Count document separators
        doc_separators = content.count('\n---')
        result["document_count"] = doc_separators + 1
        
        # Count comment lines
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        result["comment_lines"] = comment_lines
        
        # Detect common keys (simple regex)
        keys = set()
        for line in lines:
            # Match "key:" pattern
            match = re.match(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_-]*)\s*:', line)
            if match:
                keys.add(match.group(2))
        
        if keys:
            result["keys_detected"] = sorted(list(keys))[:20]  # Sample
            result["key_count"] = len(keys)
        
        result["parser"] = "basic"
        return result
    
    def _full_parse(self, content: str) -> Dict[str, Any]:
        """Full parsing with PyYAML."""
        result = {}
        
        # Parse all documents
        try:
            documents = list(yaml.safe_load_all(content))
            result["document_count"] = len(documents)
            
            # Analyze each document
            all_keys = set()
            all_types = set()
            max_depth = 0
            
            for i, doc in enumerate(documents):
                if doc is not None:
                    # Collect keys and analyze structure
                    keys, types, depth = self._analyze_structure(doc)
                    all_keys.update(keys)
                    all_types.update(types)
                    max_depth = max(max_depth, depth)
            
            result["unique_keys"] = sorted(list(all_keys))[:30]  # Sample
            result["unique_key_count"] = len(all_keys)
            result["data_types"] = sorted(list(all_types))
            result["max_nesting_depth"] = max_depth
            
            # Analyze first document in detail
            if documents and documents[0] is not None:
                first_doc = documents[0]
                result["first_document"] = self._summarize_document(first_doc)
            
            result["parser"] = "pyyaml"
            
        except yaml.YAMLError as e:
            result["parse_error"] = str(e)
            result["parser"] = "pyyaml_failed"
            # Fall back to basic parsing
            result.update(self._basic_parse(content))
        
        return result
    
    def _analyze_structure(self, obj: Any, prefix: str = "", depth: int = 0) -> tuple:
        """Recursively analyze YAML structure."""
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
    
    def _summarize_document(self, doc: Any) -> Dict[str, Any]:
        """Summarize a YAML document."""
        summary = {
            "type": type(doc).__name__
        }
        
        if isinstance(doc, dict):
            summary["top_level_keys"] = list(doc.keys())[:20]  # Sample
            summary["key_count"] = len(doc)
            
            # Sample values
            samples = {}
            for key, value in list(doc.items())[:5]:
                samples[key] = self._sample_value(value)
            summary["value_samples"] = samples
            
        elif isinstance(doc, list):
            summary["item_count"] = len(doc)
            summary["item_types"] = list(set(type(item).__name__ for item in doc[:10]))
            
            # Sample items
            samples = []
            for item in doc[:3]:
                samples.append(self._sample_value(item))
            summary["item_samples"] = samples
            
        else:
            summary["value"] = self._sample_value(doc)
        
        return summary
    
    def _sample_value(self, value: Any, max_str_len: int = 100) -> Any:
        """Create a sample representation of a value."""
        if value is None:
            return None
        elif isinstance(value, (bool, int, float)):
            return value
        elif isinstance(value, str):
            if len(value) > max_str_len:
                return value[:max_str_len] + "..."
            return value
        elif isinstance(value, dict):
            return {
                "_type": "dict",
                "_keys": list(value.keys())[:10],
                "_size": len(value)
            }
        elif isinstance(value, list):
            return {
                "_type": "list",
                "_length": len(value),
                "_first": self._sample_value(value[0]) if value else None
            }
        else:
            return {
                "_type": type(value).__name__,
                "_repr": str(value)[:100]
            }

def main():
    if len(sys.argv) < 2:
        print("Usage: yaml_extractor.py <yaml_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not HAS_YAML:
        print("Warning: PyYAML not installed, using basic parsing", file=sys.stderr)
    
    extractor = YAMLExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
