#!/usr/bin/env python3
"""
PaniniFS v3.33: SVG (Scalable Vector Graphics) Extractor
==========================================================

SVG - XML-based vector graphics format.

Structure:
- XML document with root <svg> element
- Namespace: http://www.w3.org/2000/svg
- Can include metadata, defs, styles, and graphic elements

Root <svg> attributes:
- width, height: dimensions (with units: px, pt, mm, cm, in, etc.)
- viewBox: coordinate system (minX minY width height)
- version: SVG version (1.0, 1.1, 1.2, 2.0)
- xmlns: namespace declarations

Metadata elements:
- <metadata>: RDF/Dublin Core metadata
  - dc:title, dc:creator, dc:date, dc:description
- <title>: document title
- <desc>: description
- Inkscape metadata: inkscape:version, sodipodi:docname

Graphic elements:
- <g>: group
- <path>: path data (commands: M, L, C, Z, etc.)
- <rect>: rectangle
- <circle>: circle
- <ellipse>: ellipse
- <line>: line
- <polyline>: polyline
- <polygon>: polygon
- <text>: text
- <image>: embedded raster image
- <use>: reference to another element

Styling:
- <defs>: definitions (gradients, patterns, etc.)
- <style>: CSS styles
- <linearGradient>, <radialGradient>: gradients
- <pattern>: pattern fill
- <clipPath>: clipping path
- <mask>: masking

Metadata extracted:
- Dimensions (width, height)
- ViewBox coordinates
- SVG version
- Namespaces used
- Title and description
- Creator and date (from metadata)
- Inkscape/Sodipodi metadata
- Element counts (paths, shapes, text, etc.)
- Gradient and pattern counts
- Embedded image count
- Text content samples

Format: XML, UTF-8
Standard: W3C SVG

Author: PaniniFS Research Team
Version: 3.33
Date: 2025-01-14
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional


class SVGExtractor:
    """Extract metadata from SVG vector graphics files."""
    
    # SVG namespaces
    NAMESPACES = {
        'svg': 'http://www.w3.org/2000/svg',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'cc': 'http://creativecommons.org/ns#',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
        'xlink': 'http://www.w3.org/1999/xlink',
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "SVG (Scalable Vector Graphics)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "metadata": {},
            "elements": {},
            "errors": []
        }
        
        try:
            # Parse XML
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            
            # Register namespaces
            for prefix, uri in self.NAMESPACES.items():
                ET.register_namespace(prefix, uri)
            
            # Extract root attributes
            self._parse_root_attributes(root)
            
            # Extract metadata
            self._parse_metadata(root)
            
            # Count elements
            self._count_elements(root)
            
        except ET.ParseError as e:
            self.data["errors"].append(f"XML parse error: {str(e)}")
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_root_attributes(self, root):
        """Parse SVG root element attributes."""
        # Width and height
        width = root.get('width')
        height = root.get('height')
        
        if width:
            self.data["width"] = width
        if height:
            self.data["height"] = height
        
        # ViewBox
        viewbox = root.get('viewBox')
        if viewbox:
            try:
                parts = viewbox.strip().split()
                if len(parts) == 4:
                    self.data["viewBox"] = {
                        "minX": float(parts[0]),
                        "minY": float(parts[1]),
                        "width": float(parts[2]),
                        "height": float(parts[3])
                    }
            except ValueError:
                pass
        
        # SVG version
        version = root.get('version')
        if version:
            self.data["version"] = version
        
        # Inkscape/Sodipodi attributes
        inkscape_version = root.get(f'{{{self.NAMESPACES["inkscape"]}}}version')
        if inkscape_version:
            self.data["metadata"]["inkscape_version"] = inkscape_version
        
        sodipodi_docname = root.get(f'{{{self.NAMESPACES["sodipodi"]}}}docname')
        if sodipodi_docname:
            self.data["metadata"]["sodipodi_docname"] = sodipodi_docname
        
        # Namespaces
        namespaces = []
        for key, value in root.attrib.items():
            if key.startswith('{http://www.w3.org/2000/xmlns/}'):
                prefix = key.split('}')[1]
                if prefix:
                    namespaces.append(prefix)
        
        if namespaces:
            self.data["namespaces"] = namespaces
    
    def _parse_metadata(self, root):
        """Extract metadata from SVG."""
        # Title
        title = root.find('.//svg:title', self.NAMESPACES)
        if title is not None and title.text:
            self.data["metadata"]["title"] = title.text.strip()
        
        # Description
        desc = root.find('.//svg:desc', self.NAMESPACES)
        if desc is not None and desc.text:
            self.data["metadata"]["description"] = desc.text.strip()
        
        # Dublin Core metadata
        metadata_elem = root.find('.//svg:metadata', self.NAMESPACES)
        if metadata_elem is not None:
            # DC Title
            dc_title = metadata_elem.find('.//dc:title', self.NAMESPACES)
            if dc_title is not None and dc_title.text:
                self.data["metadata"]["dc_title"] = dc_title.text.strip()
            
            # DC Creator
            dc_creator = metadata_elem.find('.//dc:creator', self.NAMESPACES)
            if dc_creator is not None:
                agent = dc_creator.find('.//cc:Agent', self.NAMESPACES)
                if agent is not None:
                    title = agent.find('.//dc:title', self.NAMESPACES)
                    if title is not None and title.text:
                        self.data["metadata"]["creator"] = title.text.strip()
            
            # DC Date
            dc_date = metadata_elem.find('.//dc:date', self.NAMESPACES)
            if dc_date is not None and dc_date.text:
                self.data["metadata"]["date"] = dc_date.text.strip()
            
            # DC Description
            dc_description = metadata_elem.find('.//dc:description', self.NAMESPACES)
            if dc_description is not None and dc_description.text:
                self.data["metadata"]["dc_description"] = dc_description.text.strip()
    
    def _count_elements(self, root):
        """Count various SVG elements."""
        elements = {
            "paths": 0,
            "rectangles": 0,
            "circles": 0,
            "ellipses": 0,
            "lines": 0,
            "polylines": 0,
            "polygons": 0,
            "text_elements": 0,
            "images": 0,
            "groups": 0,
            "uses": 0,
            "linear_gradients": 0,
            "radial_gradients": 0,
            "patterns": 0,
            "masks": 0,
            "clip_paths": 0
        }
        
        # Count elements (search with and without namespace)
        svg_ns = f'{{{self.NAMESPACES["svg"]}}}'
        
        def count_elem(tag):
            """Count elements with or without namespace."""
            with_ns = len(list(root.iter(svg_ns + tag)))
            without_ns = len(list(root.iter(tag)))
            return max(with_ns, without_ns)
        
        elements["paths"] = count_elem('path')
        elements["rectangles"] = count_elem('rect')
        elements["circles"] = count_elem('circle')
        elements["ellipses"] = count_elem('ellipse')
        elements["lines"] = count_elem('line')
        elements["polylines"] = count_elem('polyline')
        elements["polygons"] = count_elem('polygon')
        elements["text_elements"] = count_elem('text')
        elements["images"] = count_elem('image')
        elements["groups"] = count_elem('g')
        elements["uses"] = count_elem('use')
        
        elements["linear_gradients"] = count_elem('linearGradient')
        elements["radial_gradients"] = count_elem('radialGradient')
        elements["patterns"] = count_elem('pattern')
        elements["masks"] = count_elem('mask')
        elements["clip_paths"] = count_elem('clipPath')
        
        # Calculate total shapes
        total_shapes = (elements["paths"] + elements["rectangles"] + 
                       elements["circles"] + elements["ellipses"] + 
                       elements["lines"] + elements["polylines"] + 
                       elements["polygons"])
        
        elements["total_shapes"] = total_shapes
        
        # Calculate total gradients
        total_gradients = elements["linear_gradients"] + elements["radial_gradients"]
        elements["total_gradients"] = total_gradients
        
        self.data["elements"] = elements
        
        # Extract text samples
        text_samples = []
        for text_elem in root.iter(f'{{{self.NAMESPACES["svg"]}}}text'):
            text_content = self._get_element_text(text_elem)
            if text_content and len(text_content.strip()) > 0:
                text_samples.append(text_content[:100])
                if len(text_samples) >= 5:
                    break
        
        if text_samples:
            self.data["text_samples"] = text_samples
    
    def _get_element_text(self, elem) -> str:
        """Recursively extract all text from element."""
        parts = []
        
        if elem.text:
            parts.append(elem.text)
        
        for child in elem:
            child_text = self._get_element_text(child)
            if child_text:
                parts.append(child_text)
            
            if child.tail:
                parts.append(child.tail)
        
        return ''.join(parts).strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python svg_extractor.py <file.svg>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = SVGExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
