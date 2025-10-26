#!/usr/bin/env python3
"""
PaniniFS Semantic Extractor
============================
Extracts semantic meaning from text-based formats (SVG, XML, JSON, HTML)
Goes beyond structural parsing to capture domain-specific semantics.

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.1-alpha
"""

import xml.etree.ElementTree as ET
import json
import re
from typing import Dict, List, Any, Union
from pathlib import Path
from html.parser import HTMLParser


class SemanticExtractor:
    """Base class for semantic extraction from text-based formats"""
    
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract semantic information from file"""
        raise NotImplementedError


class SVGSemanticExtractor(SemanticExtractor):
    """
    SVG Semantic Extractor
    ======================
    Extracts geometric shapes, text, styles, and transforms from SVG files.
    
    Semantic Elements:
    - Shapes: rectangle, circle, ellipse, line, polyline, polygon, path
    - Text: text content with positioning and styling
    - Groups: grouped elements with transforms
    - Styles: fill, stroke, opacity, transforms
    - Definitions: gradients, patterns, markers
    
    Output: Structured semantic representation with typed elements
    """
    
    # SVG namespace
    NS = {'svg': 'http://www.w3.org/2000/svg'}
    
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract semantic elements from SVG file"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract document metadata
        semantic_doc = {
            'format': 'SVG',
            'version': '1.1',
            'semantic_extraction': True,
            'namespace': root.get('xmlns', self.NS['svg']),
            'viewBox': self._parse_viewbox(root.get('viewBox')),
            'width': root.get('width'),
            'height': root.get('height'),
            'elements': []
        }
        
        # Extract semantic elements
        semantic_doc['elements'].extend(self._extract_rectangles(root))
        semantic_doc['elements'].extend(self._extract_circles(root))
        semantic_doc['elements'].extend(self._extract_ellipses(root))
        semantic_doc['elements'].extend(self._extract_lines(root))
        semantic_doc['elements'].extend(self._extract_polylines(root))
        semantic_doc['elements'].extend(self._extract_polygons(root))
        semantic_doc['elements'].extend(self._extract_paths(root))
        semantic_doc['elements'].extend(self._extract_text(root))
        semantic_doc['elements'].extend(self._extract_groups(root))
        
        # Count element types
        semantic_doc['statistics'] = self._compute_statistics(semantic_doc['elements'])
        
        return semantic_doc
    
    def _parse_viewbox(self, viewbox: str) -> Dict[str, float]:
        """Parse viewBox attribute into semantic representation"""
        if not viewbox:
            return None
        
        values = [float(v) for v in viewbox.split()]
        if len(values) == 4:
            return {
                'x': values[0],
                'y': values[1],
                'width': values[2],
                'height': values[3]
            }
        return None
    
    def _extract_style(self, element: ET.Element) -> Dict[str, Any]:
        """Extract style attributes (fill, stroke, opacity, etc.)"""
        style = {}
        
        # Color attributes
        if element.get('fill'):
            style['fill'] = element.get('fill')
        if element.get('stroke'):
            style['stroke'] = element.get('stroke')
        if element.get('stroke-width'):
            style['stroke_width'] = float(element.get('stroke-width'))
        
        # Opacity
        if element.get('opacity'):
            style['opacity'] = float(element.get('opacity'))
        if element.get('fill-opacity'):
            style['fill_opacity'] = float(element.get('fill-opacity'))
        if element.get('stroke-opacity'):
            style['stroke_opacity'] = float(element.get('stroke-opacity'))
        
        # Transform
        if element.get('transform'):
            style['transform'] = element.get('transform')
        
        return style
    
    def _extract_rectangles(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract rectangle elements with semantic properties"""
        rectangles = []
        
        for rect in root.iter('{http://www.w3.org/2000/svg}rect'):
            semantic_rect = {
                'type': 'rectangle',
                'geometry': {
                    'position': {
                        'x': float(rect.get('x', 0)),
                        'y': float(rect.get('y', 0))
                    },
                    'size': {
                        'width': float(rect.get('width', 0)),
                        'height': float(rect.get('height', 0))
                    }
                },
                'style': self._extract_style(rect)
            }
            
            # Rounded corners
            if rect.get('rx') or rect.get('ry'):
                semantic_rect['geometry']['corner_radius'] = {
                    'x': float(rect.get('rx', 0)),
                    'y': float(rect.get('ry', 0))
                }
            
            rectangles.append(semantic_rect)
        
        return rectangles
    
    def _extract_circles(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract circle elements with semantic properties"""
        circles = []
        
        for circle in root.iter('{http://www.w3.org/2000/svg}circle'):
            semantic_circle = {
                'type': 'circle',
                'geometry': {
                    'center': {
                        'x': float(circle.get('cx', 0)),
                        'y': float(circle.get('cy', 0))
                    },
                    'radius': float(circle.get('r', 0))
                },
                'style': self._extract_style(circle)
            }
            circles.append(semantic_circle)
        
        return circles
    
    def _extract_ellipses(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract ellipse elements with semantic properties"""
        ellipses = []
        
        for ellipse in root.iter('{http://www.w3.org/2000/svg}ellipse'):
            semantic_ellipse = {
                'type': 'ellipse',
                'geometry': {
                    'center': {
                        'x': float(ellipse.get('cx', 0)),
                        'y': float(ellipse.get('cy', 0))
                    },
                    'radii': {
                        'x': float(ellipse.get('rx', 0)),
                        'y': float(ellipse.get('ry', 0))
                    }
                },
                'style': self._extract_style(ellipse)
            }
            ellipses.append(semantic_ellipse)
        
        return ellipses
    
    def _extract_lines(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract line elements with semantic properties"""
        lines = []
        
        for line in root.iter('{http://www.w3.org/2000/svg}line'):
            semantic_line = {
                'type': 'line',
                'geometry': {
                    'start': {
                        'x': float(line.get('x1', 0)),
                        'y': float(line.get('y1', 0))
                    },
                    'end': {
                        'x': float(line.get('x2', 0)),
                        'y': float(line.get('y2', 0))
                    }
                },
                'style': self._extract_style(line)
            }
            lines.append(semantic_line)
        
        return lines
    
    def _extract_polylines(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract polyline elements with semantic properties"""
        polylines = []
        
        for polyline in root.iter('{http://www.w3.org/2000/svg}polyline'):
            points_str = polyline.get('points', '')
            points = self._parse_points(points_str)
            
            semantic_polyline = {
                'type': 'polyline',
                'geometry': {
                    'points': points,
                    'segment_count': len(points) - 1 if len(points) > 1 else 0
                },
                'style': self._extract_style(polyline)
            }
            polylines.append(semantic_polyline)
        
        return polylines
    
    def _extract_polygons(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract polygon elements with semantic properties"""
        polygons = []
        
        for polygon in root.iter('{http://www.w3.org/2000/svg}polygon'):
            points_str = polygon.get('points', '')
            points = self._parse_points(points_str)
            
            semantic_polygon = {
                'type': 'polygon',
                'geometry': {
                    'points': points,
                    'vertex_count': len(points)
                },
                'style': self._extract_style(polygon)
            }
            polygons.append(semantic_polygon)
        
        return polygons
    
    def _parse_points(self, points_str: str) -> List[Dict[str, float]]:
        """Parse points attribute into list of (x, y) coordinates"""
        points = []
        coords = re.findall(r'[-+]?\d*\.?\d+', points_str)
        
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                points.append({
                    'x': float(coords[i]),
                    'y': float(coords[i + 1])
                })
        
        return points
    
    def _extract_paths(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract path elements with semantic properties"""
        paths = []
        
        for path in root.iter('{http://www.w3.org/2000/svg}path'):
            d = path.get('d', '')
            
            semantic_path = {
                'type': 'path',
                'geometry': {
                    'definition': d,
                    'commands': self._parse_path_commands(d)
                },
                'style': self._extract_style(path)
            }
            paths.append(semantic_path)
        
        return paths
    
    def _parse_path_commands(self, d: str) -> List[Dict[str, Any]]:
        """Parse SVG path commands into semantic representation"""
        commands = []
        
        # Match path commands (M, L, C, Q, A, Z, etc.)
        pattern = r'([MLHVCSQTAZmlhvcsqtaz])\s*([^MLHVCSQTAZmlhvcsqtaz]*)'
        matches = re.findall(pattern, d)
        
        for cmd, params in matches:
            coords = [float(x) for x in re.findall(r'[-+]?\d*\.?\d+', params)]
            
            cmd_semantic = {
                'command': cmd,
                'absolute': cmd.isupper(),
                'parameters': coords
            }
            
            # Add semantic interpretation
            if cmd.upper() == 'M':
                cmd_semantic['meaning'] = 'moveto'
            elif cmd.upper() == 'L':
                cmd_semantic['meaning'] = 'lineto'
            elif cmd.upper() == 'C':
                cmd_semantic['meaning'] = 'cubic_bezier'
            elif cmd.upper() == 'Q':
                cmd_semantic['meaning'] = 'quadratic_bezier'
            elif cmd.upper() == 'A':
                cmd_semantic['meaning'] = 'elliptical_arc'
            elif cmd.upper() == 'Z':
                cmd_semantic['meaning'] = 'closepath'
            
            commands.append(cmd_semantic)
        
        return commands
    
    def _extract_text(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract text elements with semantic properties"""
        texts = []
        
        for text in root.iter('{http://www.w3.org/2000/svg}text'):
            semantic_text = {
                'type': 'text',
                'content': text.text or '',
                'geometry': {
                    'position': {
                        'x': float(text.get('x', 0)),
                        'y': float(text.get('y', 0))
                    }
                },
                'typography': {
                    'font_size': text.get('font-size'),
                    'font_family': text.get('font-family'),
                    'font_weight': text.get('font-weight'),
                    'text_anchor': text.get('text-anchor')
                },
                'style': self._extract_style(text)
            }
            
            # Extract tspan children
            tspans = []
            for tspan in text.iter('{http://www.w3.org/2000/svg}tspan'):
                tspans.append({
                    'content': tspan.text or '',
                    'position': {
                        'x': float(tspan.get('x', 0)),
                        'y': float(tspan.get('y', 0))
                    }
                })
            
            if tspans:
                semantic_text['spans'] = tspans
            
            texts.append(semantic_text)
        
        return texts
    
    def _extract_groups(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract group elements with semantic properties"""
        groups = []
        
        for group in root.iter('{http://www.w3.org/2000/svg}g'):
            semantic_group = {
                'type': 'group',
                'id': group.get('id'),
                'class': group.get('class'),
                'style': self._extract_style(group),
                'children_count': len(list(group))
            }
            groups.append(semantic_group)
        
        return groups
    
    def _compute_statistics(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistics on extracted elements"""
        stats = {
            'total_elements': len(elements),
            'element_types': {}
        }
        
        for element in elements:
            elem_type = element['type']
            stats['element_types'][elem_type] = stats['element_types'].get(elem_type, 0) + 1
        
        return stats


class JSONSemanticExtractor(SemanticExtractor):
    """
    JSON Semantic Extractor
    =======================
    Extracts structured data with type inference and schema analysis.
    
    Semantic Elements:
    - Objects: key-value dictionaries with nested structure
    - Arrays: ordered lists with homogeneous or heterogeneous types
    - Primitives: strings, numbers, booleans, null
    - Schema: inferred structure with types and constraints
    
    Output: Object graph with type annotations and schema inference
    """
    
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract semantic structure from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        semantic_doc = {
            'format': 'JSON',
            'semantic_extraction': True,
            'root_type': self._infer_type(data),
            'data': data,
            'schema': self._infer_schema(data),
            'statistics': self._compute_statistics(data)
        }
        
        return semantic_doc
    
    def _infer_type(self, value: Any) -> str:
        """Infer semantic type of JSON value"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'
    
    def _infer_schema(self, data: Any, path: str = '$') -> Dict[str, Any]:
        """Infer JSON schema from data structure"""
        schema = {
            'path': path,
            'type': self._infer_type(data)
        }
        
        if isinstance(data, dict):
            schema['properties'] = {}
            for key, value in data.items():
                child_path = f"{path}.{key}"
                schema['properties'][key] = self._infer_schema(value, child_path)
        
        elif isinstance(data, list):
            if data:
                # Infer type from first element (simplified)
                schema['items'] = self._infer_schema(data[0], f"{path}[0]")
                
                # Check if all elements have same type
                types = set(self._infer_type(item) for item in data)
                schema['homogeneous'] = len(types) == 1
            else:
                schema['items'] = {'type': 'unknown'}
                schema['homogeneous'] = True
        
        elif isinstance(data, str):
            # Additional string analysis
            schema['length'] = len(data)
            
            # Pattern detection
            if re.match(r'^\d{4}-\d{2}-\d{2}$', data):
                schema['pattern'] = 'date'
            elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data):
                schema['pattern'] = 'email'
            elif re.match(r'^https?://', data):
                schema['pattern'] = 'url'
            elif re.match(r'^#[0-9A-Fa-f]{6}$', data):
                schema['pattern'] = 'color_hex'
        
        elif isinstance(data, (int, float)):
            # Numerical constraints
            schema['value'] = data
        
        return schema
    
    def _compute_statistics(self, data: Any) -> Dict[str, Any]:
        """Compute statistics on JSON data"""
        stats = {
            'depth': self._compute_depth(data),
            'node_count': self._count_nodes(data),
            'type_distribution': self._count_types(data)
        }
        
        return stats
    
    def _compute_depth(self, data: Any, current_depth: int = 0) -> int:
        """Compute maximum depth of nested structure"""
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(self._compute_depth(v, current_depth + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(self._compute_depth(item, current_depth + 1) for item in data)
        else:
            return current_depth
    
    def _count_nodes(self, data: Any) -> int:
        """Count total number of nodes in structure"""
        if isinstance(data, dict):
            return 1 + sum(self._count_nodes(v) for v in data.values())
        elif isinstance(data, list):
            return 1 + sum(self._count_nodes(item) for item in data)
        else:
            return 1
    
    def _count_types(self, data: Any, counts: Dict[str, int] = None) -> Dict[str, int]:
        """Count occurrences of each type"""
        if counts is None:
            counts = {}
        
        data_type = self._infer_type(data)
        counts[data_type] = counts.get(data_type, 0) + 1
        
        if isinstance(data, dict):
            for value in data.values():
                self._count_types(value, counts)
        elif isinstance(data, list):
            for item in data:
                self._count_types(item, counts)
        
        return counts


class XMLSemanticExtractor(SemanticExtractor):
    """
    XML Semantic Extractor
    ======================
    Extracts DOM tree structure with elements, attributes, and text content.
    
    Semantic Elements:
    - Elements: tags with attributes and children
    - Text nodes: character data content
    - CDATA sections: unparsed character data
    - Processing instructions: <?...?>
    - Entities: named character references
    - Namespaces: xmlns declarations
    
    Output: DOM tree representation with typed nodes
    """
    
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract semantic DOM tree from XML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        semantic_doc = {
            'format': 'XML',
            'semantic_extraction': True,
            'version': '1.0',
            'encoding': 'UTF-8',
            'root': self._extract_element(root),
            'statistics': {
                'total_elements': self._count_elements(root),
                'depth': self._compute_depth(root),
                'namespaces': self._extract_namespaces(root)
            }
        }
        
        return semantic_doc
    
    def _extract_element(self, element: ET.Element) -> Dict[str, Any]:
        """Extract semantic representation of XML element"""
        semantic_elem = {
            'type': 'element',
            'tag': self._clean_tag(element.tag),
            'namespace': self._extract_namespace(element.tag),
            'attributes': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'tail': element.tail.strip() if element.tail else None,
            'children': []
        }
        
        # Recursively extract children
        for child in element:
            semantic_elem['children'].append(self._extract_element(child))
        
        return semantic_elem
    
    def _clean_tag(self, tag: str) -> str:
        """Remove namespace prefix from tag"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def _extract_namespace(self, tag: str) -> str:
        """Extract namespace URI from tag"""
        if '{' in tag and '}' in tag:
            return tag[tag.index('{') + 1:tag.index('}')]
        return None
    
    def _count_elements(self, element: ET.Element) -> int:
        """Count total number of elements in tree"""
        return 1 + sum(self._count_elements(child) for child in element)
    
    def _compute_depth(self, element: ET.Element, current_depth: int = 0) -> int:
        """Compute maximum depth of XML tree"""
        if not list(element):
            return current_depth
        return max(self._compute_depth(child, current_depth + 1) for child in element)
    
    def _extract_namespaces(self, element: ET.Element) -> Dict[str, str]:
        """Extract all namespace declarations"""
        namespaces = {}
        for elem in element.iter():
            for key, value in elem.attrib.items():
                if key.startswith('{http://www.w3.org/2000/xmlns/}'):
                    prefix = key.split('}')[1]
                    namespaces[prefix] = value
        return namespaces


class HTMLSemanticExtractor(SemanticExtractor):
    """
    HTML Semantic Extractor
    ========================
    Extracts semantic structure from HTML documents.
    
    Semantic Elements:
    - Document structure: head, body, sections
    - Metadata: title, meta tags, links
    - Content: headings, paragraphs, lists, tables
    - Interactive: forms, buttons, inputs
    - Media: images, audio, video, iframes
    - Styles: inline, <style> blocks, external links
    - Scripts: inline <script> blocks, external sources
    
    Output: Semantic document structure with typed elements
    """
    
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract semantic structure from HTML file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = HTMLSemanticParser()
        parser.feed(html_content)
        
        semantic_doc = {
            'format': 'HTML',
            'semantic_extraction': True,
            'version': 'HTML5',
            'doctype': parser.doctype,
            'head': parser.head_elements,
            'body': parser.body_elements,
            'statistics': {
                'total_elements': parser.element_count,
                'tag_distribution': parser.tag_counts,
                'links': len(parser.links),
                'images': len(parser.images),
                'scripts': len(parser.scripts),
                'styles': len(parser.styles)
            }
        }
        
        return semantic_doc


class HTMLSemanticParser(HTMLParser):
    """HTML parser that extracts semantic structure"""
    
    def __init__(self):
        super().__init__()
        self.doctype = None
        self.head_elements = []
        self.body_elements = []
        self.current_section = 'unknown'
        self.tag_stack = []
        self.element_count = 0
        self.tag_counts = {}
        
        # Special element collections
        self.links = []
        self.images = []
        self.scripts = []
        self.styles = []
    
    def handle_decl(self, decl):
        """Handle DOCTYPE declaration"""
        self.doctype = decl
    
    def handle_starttag(self, tag, attrs):
        """Handle opening tags"""
        self.element_count += 1
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        
        # Track current section
        if tag == 'head':
            self.current_section = 'head'
        elif tag == 'body':
            self.current_section = 'body'
        
        # Extract semantic elements
        attrs_dict = dict(attrs)
        
        element = {
            'type': 'element',
            'tag': tag,
            'attributes': attrs_dict,
            'depth': len(self.tag_stack)
        }
        
        # Special handling for semantic tags
        if tag == 'a' and 'href' in attrs_dict:
            self.links.append({
                'url': attrs_dict['href'],
                'text': '',  # Will be filled in handle_data
                'title': attrs_dict.get('title')
            })
        
        elif tag == 'img' and 'src' in attrs_dict:
            self.images.append({
                'src': attrs_dict['src'],
                'alt': attrs_dict.get('alt'),
                'width': attrs_dict.get('width'),
                'height': attrs_dict.get('height')
            })
        
        elif tag == 'script':
            script_elem = {
                'src': attrs_dict.get('src'),
                'type': attrs_dict.get('type', 'text/javascript'),
                'inline': 'src' not in attrs_dict
            }
            self.scripts.append(script_elem)
        
        elif tag == 'link' and attrs_dict.get('rel') == 'stylesheet':
            self.styles.append({
                'href': attrs_dict.get('href'),
                'media': attrs_dict.get('media', 'all')
            })
        
        elif tag == 'style':
            self.styles.append({
                'inline': True,
                'media': attrs_dict.get('media', 'all')
            })
        
        elif tag == 'meta':
            element['semantic_type'] = 'metadata'
            element['name'] = attrs_dict.get('name')
            element['content'] = attrs_dict.get('content')
            element['property'] = attrs_dict.get('property')
        
        elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            element['semantic_type'] = 'heading'
            element['level'] = int(tag[1])
        
        elif tag in ['article', 'section', 'nav', 'header', 'footer', 'aside']:
            element['semantic_type'] = 'landmark'
        
        elif tag in ['ul', 'ol', 'li']:
            element['semantic_type'] = 'list'
        
        elif tag in ['table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td']:
            element['semantic_type'] = 'table'
        
        elif tag in ['form', 'input', 'button', 'select', 'textarea']:
            element['semantic_type'] = 'interactive'
        
        # Add to appropriate section
        if self.current_section == 'head':
            self.head_elements.append(element)
        elif self.current_section == 'body':
            self.body_elements.append(element)
        
        self.tag_stack.append(tag)
    
    def handle_endtag(self, tag):
        """Handle closing tags"""
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
    
    def handle_data(self, data):
        """Handle text content"""
        # Add text to last link if inside <a> tag
        if self.tag_stack and self.tag_stack[-1] == 'a' and self.links:
            self.links[-1]['text'] = data.strip()


# Factory function
def create_extractor(format_type: str) -> SemanticExtractor:
    """Create appropriate semantic extractor for format type"""
    extractors = {
        'svg': SVGSemanticExtractor,
        'json': JSONSemanticExtractor,
        'xml': XMLSemanticExtractor,
        'html': HTMLSemanticExtractor,
        'htm': HTMLSemanticExtractor
    }
    
    extractor_class = extractors.get(format_type.lower())
    if not extractor_class:
        raise ValueError(f"No semantic extractor for format: {format_type}")
    
    return extractor_class()


def main():
    """Test semantic extractors on sample files"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: semantic_extractor.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    format_type = file_path.suffix[1:]  # Remove leading dot
    
    try:
        extractor = create_extractor(format_type)
        semantic_data = extractor.extract(file_path)
        
        # Pretty print results
        print(json.dumps(semantic_data, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
