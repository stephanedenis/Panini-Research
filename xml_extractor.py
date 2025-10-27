#!/usr/bin/env python3
"""
XML (Extensible Markup Language) Format Extractor - PaniniFS v3.41

This extractor analyzes generic XML files.
XML is a markup language that defines rules for encoding documents
in a format that is both human-readable and machine-readable.

Format Structure:
- XML declaration: <?xml version="1.0" encoding="UTF-8"?>
- Elements: <tag>content</tag> or <tag />
- Attributes: <tag attr="value">
- Namespaces: <tag xmlns="uri"> or <prefix:tag>
- Comments: <!-- comment -->
- CDATA sections: <![CDATA[data]]>
- Processing instructions: <?target data?>
- Entities: &amp; &lt; &gt; &quot; &apos;

XML Features:
- Well-formed: Proper nesting, closing tags
- Valid: Conforms to DTD or Schema
- Hierarchical structure (tree)
- Case-sensitive tags
- Unicode support

Common Use Cases:
- Configuration files (Maven pom.xml, Ant build.xml)
- Data interchange (SOAP, XML-RPC)
- Document formats (DOCX, ODT, SVG - covered separately)
- Web services (WSDL, RSS, Atom)
- Application settings (Android manifest, .NET config)
- Metadata (Dublin Core, EXIF)

This extractor provides:
- XML declaration parsing (version, encoding, standalone)
- Root element detection
- Namespace enumeration
- Element counting (by tag name)
- Attribute statistics
- Text content sampling
- Maximum depth calculation
- Comment and CDATA detection

Author: PaniniFS Research Team
Version: 3.41
Target: XML files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import xml.etree.ElementTree as ET
import re

class XMLExtractor:
    """Extract metadata from XML files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the XML file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "XML",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Parse XML declaration
            metadata.update(self._parse_declaration(content))
            
            # Parse XML structure
            try:
                tree = ET.parse(self.file_path)
                root = tree.getroot()
                metadata.update(self._analyze_structure(root))
            except ET.ParseError as e:
                metadata["parse_error"] = {
                    "message": str(e),
                    "position": e.position if hasattr(e, 'position') else None
                }
            
            # Count comments and CDATA
            metadata.update(self._count_special(content))
            
            return metadata
            
        except Exception as e:
            return {
                "format": "XML",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_declaration(self, content: str) -> Dict[str, Any]:
        """Parse XML declaration."""
        result = {}
        
        # Match <?xml ... ?>
        match = re.search(r'<\?xml\s+([^?]*)\?>', content)
        if match:
            decl_attrs = match.group(1)
            
            # Parse version
            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', decl_attrs)
            if version_match:
                result["xml_version"] = version_match.group(1)
            
            # Parse encoding
            encoding_match = re.search(r'encoding\s*=\s*["\']([^"\']+)["\']', decl_attrs)
            if encoding_match:
                result["encoding"] = encoding_match.group(1)
            
            # Parse standalone
            standalone_match = re.search(r'standalone\s*=\s*["\']([^"\']+)["\']', decl_attrs)
            if standalone_match:
                result["standalone"] = standalone_match.group(1) == "yes"
        
        return result
    
    def _analyze_structure(self, root: ET.Element) -> Dict[str, Any]:
        """Analyze XML structure."""
        result = {}
        
        # Root element
        root_tag = self._strip_namespace(root.tag)
        root_ns = self._extract_namespace(root.tag)
        
        result["root_element"] = root_tag
        if root_ns:
            result["root_namespace"] = root_ns
        
        # Root attributes
        if root.attrib:
            result["root_attributes"] = dict(root.attrib)
        
        # Collect namespaces
        namespaces = self._collect_namespaces(root)
        if namespaces:
            result["namespaces"] = namespaces
        
        # Count elements
        element_counts = {}
        total_elements = 0
        max_depth = 0
        
        for elem, depth in self._iterate_elements(root):
            tag = self._strip_namespace(elem.tag)
            element_counts[tag] = element_counts.get(tag, 0) + 1
            total_elements += 1
            max_depth = max(max_depth, depth)
        
        result["total_elements"] = total_elements
        result["max_depth"] = max_depth
        result["unique_elements"] = len(element_counts)
        result["element_counts"] = dict(sorted(element_counts.items(), 
                                              key=lambda x: x[1], 
                                              reverse=True)[:20])  # Top 20
        
        # Count attributes
        total_attrs = 0
        attr_names = set()
        
        for elem, _ in self._iterate_elements(root):
            total_attrs += len(elem.attrib)
            attr_names.update(elem.attrib.keys())
        
        result["total_attributes"] = total_attrs
        result["unique_attributes"] = len(attr_names)
        if attr_names:
            result["attribute_names"] = sorted(list(attr_names))[:20]  # Sample
        
        # Sample text content
        text_samples = []
        for elem, _ in self._iterate_elements(root):
            if elem.text and elem.text.strip():
                text = elem.text.strip()
                if len(text) > 0 and len(text_samples) < 5:
                    text_samples.append({
                        "element": self._strip_namespace(elem.tag),
                        "text": text[:100]  # Truncate
                    })
        
        if text_samples:
            result["text_samples"] = text_samples
        
        return result
    
    def _iterate_elements(self, root: ET.Element, depth: int = 0):
        """Iterate all elements with depth."""
        for child in root:
            yield child, depth + 1
            yield from self._iterate_elements(child, depth + 1)
    
    def _strip_namespace(self, tag: str) -> str:
        """Remove namespace from tag."""
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag
    
    def _extract_namespace(self, tag: str) -> Optional[str]:
        """Extract namespace URI from tag."""
        if tag.startswith('{') and '}' in tag:
            return tag[1:tag.index('}')]
        return None
    
    def _collect_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """Collect all namespaces used in document."""
        namespaces = {}
        
        # Check root element namespace
        root_ns = self._extract_namespace(root.tag)
        if root_ns:
            namespaces["default"] = root_ns
        
        # Check xmlns attributes
        for key, value in root.attrib.items():
            if key == "xmlns":
                namespaces["default"] = value
            elif key.startswith("xmlns:"):
                prefix = key.split(':', 1)[1]
                namespaces[prefix] = value
        
        # Check child elements
        for elem, _ in self._iterate_elements(root):
            ns = self._extract_namespace(elem.tag)
            if ns and ns not in namespaces.values():
                # Try to find prefix or use URI
                found_prefix = None
                for key, value in elem.attrib.items():
                    if key.startswith("xmlns:") and value == ns:
                        found_prefix = key.split(':', 1)[1]
                        break
                
                if found_prefix:
                    namespaces[found_prefix] = ns
                else:
                    # Use URI as key
                    namespaces[ns] = ns
        
        return namespaces
    
    def _count_special(self, content: str) -> Dict[str, Any]:
        """Count comments and CDATA sections."""
        result = {}
        
        # Count comments
        comments = re.findall(r'<!--.*?-->', content, re.DOTALL)
        if comments:
            result["comment_count"] = len(comments)
        
        # Count CDATA sections
        cdata = re.findall(r'<!\[CDATA\[.*?\]\]>', content, re.DOTALL)
        if cdata:
            result["cdata_count"] = len(cdata)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: xml_extractor.py <xml_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = XMLExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
