#!/usr/bin/env python3
"""
CSS (Cascading Style Sheets) Format Extractor - PaniniFS v3.43

This extractor analyzes CSS stylesheet files.
CSS is a style sheet language used for describing the presentation
of HTML or XML documents.

Format Structure:
- Selectors: element, .class, #id, [attribute], :pseudo-class
- Declaration blocks: { property: value; }
- At-rules: @import, @media, @keyframes, @font-face
- Comments: /* comment */
- Values: colors, lengths, URLs, functions
- Media queries: responsive design rules

CSS Versions:
- CSS 1 (1996) - Basic styling
- CSS 2.1 (2011) - Standard reference
- CSS 3 (modular) - Modern features

Selectors:
- Type: element
- Class: .classname
- ID: #idname
- Universal: *
- Attribute: [attr], [attr=value]
- Pseudo-class: :hover, :active, :nth-child()
- Pseudo-element: ::before, ::after
- Combinators: descendant (space), child (>), sibling (+, ~)

Properties (common):
- Layout: display, position, float, flexbox, grid
- Box model: width, height, margin, padding, border
- Typography: font-family, font-size, color, text-align
- Colors: color, background-color, opacity
- Transform: transform, transition, animation

This extractor provides:
- Rule counting (selector + declarations)
- Selector analysis (type, class, id, pseudo)
- Property statistics (most used)
- At-rule detection (@import, @media, @keyframes)
- Color value extraction
- Font family enumeration
- Media query detection
- Comment counting

Author: PaniniFS Research Team
Version: 3.43
Target: CSS files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import re

class CSSExtractor:
    """Extract metadata from CSS files."""
    
    # Common CSS properties
    PROPERTY_CATEGORIES = {
        "layout": ["display", "position", "float", "clear", "top", "left", "right", "bottom", 
                  "flex", "grid", "z-index"],
        "box_model": ["width", "height", "margin", "padding", "border", "outline"],
        "typography": ["font-family", "font-size", "font-weight", "font-style", "line-height", 
                      "text-align", "text-decoration", "letter-spacing"],
        "colors": ["color", "background-color", "background", "opacity"],
        "transform": ["transform", "transition", "animation", "transition-duration"],
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the CSS file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "CSS",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Remove comments for parsing
            content_no_comments = self._remove_comments(content)
            
            # Count comments
            metadata["comment_count"] = self._count_comments(content)
            
            # Parse rules
            metadata.update(self._parse_rules(content_no_comments))
            
            # Parse at-rules
            metadata.update(self._parse_at_rules(content_no_comments))
            
            # Extract values
            metadata.update(self._extract_values(content_no_comments))
            
            return metadata
            
        except Exception as e:
            return {
                "format": "CSS",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _remove_comments(self, content: str) -> str:
        """Remove CSS comments."""
        return re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    def _count_comments(self, content: str) -> int:
        """Count CSS comments."""
        return len(re.findall(r'/\*.*?\*/', content, flags=re.DOTALL))
    
    def _parse_rules(self, content: str) -> Dict[str, Any]:
        """Parse CSS rules (selector + declarations)."""
        result = {}
        
        # Match rules: selector { declarations }
        # Exclude at-rules
        rules = re.findall(r'([^@{]+)\{([^}]*)\}', content)
        
        result["rule_count"] = len(rules)
        
        # Analyze selectors
        selectors = []
        selector_types = {
            "element": 0,
            "class": 0,
            "id": 0,
            "attribute": 0,
            "pseudo_class": 0,
            "pseudo_element": 0,
            "universal": 0,
        }
        
        for selector, _ in rules:
            selector = selector.strip()
            if not selector:
                continue
            
            selectors.append(selector[:100])  # Truncate
            
            # Count selector types
            if re.search(r'\.\w+', selector):
                selector_types["class"] += 1
            if re.search(r'#\w+', selector):
                selector_types["id"] += 1
            if re.search(r'\[[^\]]+\]', selector):
                selector_types["attribute"] += 1
            if re.search(r':\w+', selector):
                selector_types["pseudo_class"] += 1
            if re.search(r'::\w+', selector):
                selector_types["pseudo_element"] += 1
            if selector == '*':
                selector_types["universal"] += 1
            if re.match(r'^[a-z][\w-]*$', selector.split()[0] if ' ' in selector else selector):
                selector_types["element"] += 1
        
        result["selector_samples"] = selectors[:10]  # Sample
        result["selector_types"] = {k: v for k, v in selector_types.items() if v > 0}
        
        # Analyze properties
        property_counts = {}
        all_properties = []
        
        for _, declarations in rules:
            # Parse declarations
            props = re.findall(r'([\w-]+)\s*:\s*([^;]+)', declarations)
            for prop, value in props:
                prop = prop.strip().lower()
                property_counts[prop] = property_counts.get(prop, 0) + 1
                all_properties.append(prop)
        
        if property_counts:
            # Top properties
            sorted_props = dict(sorted(property_counts.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:20])  # Top 20
            result["property_counts"] = sorted_props
            result["unique_properties"] = len(property_counts)
            result["total_declarations"] = len(all_properties)
            
            # Categorize properties
            categories = {}
            for prop in set(all_properties):
                for category, props in self.PROPERTY_CATEGORIES.items():
                    if prop in props or any(prop.startswith(p) for p in props):
                        categories[category] = categories.get(category, 0) + 1
            
            if categories:
                result["property_categories"] = categories
        
        return result
    
    def _parse_at_rules(self, content: str) -> Dict[str, Any]:
        """Parse CSS at-rules."""
        result = {}
        
        # @import
        imports = re.findall(r'@import\s+([^;]+);', content)
        if imports:
            result["import_count"] = len(imports)
            result["imports"] = [imp.strip() for imp in imports[:5]]  # Sample
        
        # @media
        media_queries = re.findall(r'@media\s+([^{]+)\{', content)
        if media_queries:
            result["media_query_count"] = len(media_queries)
            result["media_queries"] = [mq.strip() for mq in media_queries[:5]]  # Sample
        
        # @keyframes
        keyframes = re.findall(r'@(?:-\w+-)?keyframes\s+([\w-]+)', content)
        if keyframes:
            result["animation_count"] = len(keyframes)
            result["animations"] = keyframes[:5]  # Sample
        
        # @font-face
        font_faces = re.findall(r'@font-face\s*\{', content)
        if font_faces:
            result["font_face_count"] = len(font_faces)
        
        return result
    
    def _extract_values(self, content: str) -> Dict[str, Any]:
        """Extract interesting values (colors, fonts)."""
        result = {}
        
        # Colors
        colors = set()
        
        # Hex colors
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,8}', content)
        colors.update(hex_colors)
        
        # RGB/RGBA
        rgb_colors = re.findall(r'rgba?\([^)]+\)', content)
        colors.update(rgb_colors)
        
        # Named colors
        named_colors = re.findall(r'\b(red|blue|green|white|black|yellow|gray|grey|purple|orange|pink|brown)\b', 
                                 content, re.IGNORECASE)
        colors.update(named_colors)
        
        if colors:
            result["color_count"] = len(colors)
            result["colors"] = sorted(list(colors))[:10]  # Sample
        
        # Font families
        fonts = set()
        font_matches = re.findall(r'font-family\s*:\s*([^;]+)', content, re.IGNORECASE)
        for font_list in font_matches:
            # Split by comma and clean
            families = [f.strip().strip('"\'') for f in font_list.split(',')]
            fonts.update(families)
        
        if fonts:
            result["font_families"] = sorted(list(fonts))[:10]  # Sample
            result["font_family_count"] = len(fonts)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: css_extractor.py <css_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = CSSExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
