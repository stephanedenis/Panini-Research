#!/usr/bin/env python3
"""
HTML (HyperText Markup Language) Format Extractor - PaniniFS v3.42

This extractor analyzes HTML/XHTML documents.
HTML is the standard markup language for documents designed to be
displayed in a web browser.

Format Structure:
- DOCTYPE declaration: <!DOCTYPE html>
- HTML element: <html>
- Head section: <head> (metadata, title, styles, scripts)
- Body section: <body> (visible content)
- Elements: <tag>content</tag> or <tag />
- Attributes: <tag attr="value">
- Comments: <!-- comment -->
- Entities: &nbsp; &copy; &#169; etc.

HTML Versions:
- HTML 4.01 (1999)
- XHTML 1.0 (2000) - XML-compliant HTML
- HTML5 (2014) - Modern standard
- XHTML5 - HTML5 with XML syntax

Document Structure:
- <head>: metadata, title, links, scripts, styles
- <body>: visible content
- Semantic elements: <header>, <nav>, <main>, <article>, <footer>
- Content elements: <p>, <h1>-<h6>, <div>, <span>, <a>, <img>
- Lists: <ul>, <ol>, <li>
- Tables: <table>, <tr>, <td>, <th>
- Forms: <form>, <input>, <button>, <select>

This extractor provides:
- DOCTYPE detection (HTML version)
- Title and meta tags
- Character encoding
- Language attribute
- Element counting
- Link and image enumeration
- Script and style detection
- Heading structure (h1-h6)
- Text content sampling

Author: PaniniFS Research Team
Version: 3.42
Target: HTML files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import re
from html.parser import HTMLParser

class HTMLMetadataParser(HTMLParser):
    """Custom HTML parser for metadata extraction."""
    
    def __init__(self):
        super().__init__()
        self.title = None
        self.meta_tags = []
        self.links = []
        self.scripts = []
        self.styles = []
        self.images = []
        self.headings = {f'h{i}': [] for i in range(1, 7)}
        self.element_counts = {}
        self.current_tag = None
        self.in_title = False
        self.encoding = None
        self.language = None
        
    def handle_starttag(self, tag, attrs):
        """Handle opening tags."""
        # Count elements
        self.element_counts[tag] = self.element_counts.get(tag, 0) + 1
        
        attrs_dict = dict(attrs)
        
        # Track current tag for text extraction
        self.current_tag = tag
        
        # Title
        if tag == 'title':
            self.in_title = True
        
        # HTML language
        if tag == 'html' and 'lang' in attrs_dict:
            self.language = attrs_dict['lang']
        
        # Meta tags
        if tag == 'meta':
            meta = {}
            if 'name' in attrs_dict:
                meta['name'] = attrs_dict['name']
            if 'content' in attrs_dict:
                meta['content'] = attrs_dict['content']
            if 'http-equiv' in attrs_dict:
                meta['http-equiv'] = attrs_dict['http-equiv']
            if 'charset' in attrs_dict:
                self.encoding = attrs_dict['charset']
                meta['charset'] = attrs_dict['charset']
            self.meta_tags.append(meta)
        
        # Links
        if tag == 'link':
            link = {}
            if 'rel' in attrs_dict:
                link['rel'] = attrs_dict['rel']
            if 'href' in attrs_dict:
                link['href'] = attrs_dict['href']
            if 'type' in attrs_dict:
                link['type'] = attrs_dict['type']
            self.links.append(link)
        
        # Scripts
        if tag == 'script':
            script = {}
            if 'src' in attrs_dict:
                script['src'] = attrs_dict['src']
            if 'type' in attrs_dict:
                script['type'] = attrs_dict['type']
            self.scripts.append(script)
        
        # Styles
        if tag == 'style':
            style = {}
            if 'type' in attrs_dict:
                style['type'] = attrs_dict['type']
            self.styles.append(style)
        
        # Images
        if tag == 'img':
            img = {}
            if 'src' in attrs_dict:
                img['src'] = attrs_dict['src']
            if 'alt' in attrs_dict:
                img['alt'] = attrs_dict['alt']
            self.images.append(img)
        
        # Headings
        if tag in self.headings:
            # Will collect text in handle_data
            pass
    
    def handle_endtag(self, tag):
        """Handle closing tags."""
        if tag == 'title':
            self.in_title = False
        self.current_tag = None
    
    def handle_data(self, data):
        """Handle text data."""
        data = data.strip()
        if not data:
            return
        
        # Title
        if self.in_title:
            self.title = data
        
        # Headings
        if self.current_tag in self.headings:
            self.headings[self.current_tag].append(data[:100])  # Truncate

class HTMLExtractor:
    """Extract metadata from HTML files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the HTML file."""
        try:
            # Read file with UTF-8 encoding
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            metadata = {
                "format": "HTML",
                "file_path": str(self.file_path),
                "file_size": len(content),
            }
            
            # Parse DOCTYPE
            metadata.update(self._parse_doctype(content))
            
            # Parse HTML structure
            parser = HTMLMetadataParser()
            try:
                parser.feed(content)
                metadata.update(self._extract_from_parser(parser))
            except Exception as e:
                metadata["parse_error"] = str(e)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "HTML",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_doctype(self, content: str) -> Dict[str, Any]:
        """Parse DOCTYPE declaration."""
        result = {}
        
        # Match <!DOCTYPE ...>
        match = re.search(r'<!DOCTYPE\s+([^>]+)>', content, re.IGNORECASE)
        if match:
            doctype = match.group(1).strip()
            result["doctype"] = doctype
            
            # Detect HTML version
            if 'HTML 5' in doctype or doctype.lower() == 'html':
                result["html_version"] = "HTML5"
            elif 'XHTML 1.0' in doctype:
                if 'Strict' in doctype:
                    result["html_version"] = "XHTML 1.0 Strict"
                elif 'Transitional' in doctype:
                    result["html_version"] = "XHTML 1.0 Transitional"
                elif 'Frameset' in doctype:
                    result["html_version"] = "XHTML 1.0 Frameset"
                else:
                    result["html_version"] = "XHTML 1.0"
            elif 'HTML 4.01' in doctype:
                if 'Strict' in doctype:
                    result["html_version"] = "HTML 4.01 Strict"
                elif 'Transitional' in doctype:
                    result["html_version"] = "HTML 4.01 Transitional"
                else:
                    result["html_version"] = "HTML 4.01"
        
        return result
    
    def _extract_from_parser(self, parser: HTMLMetadataParser) -> Dict[str, Any]:
        """Extract metadata from parser."""
        result = {}
        
        # Title
        if parser.title:
            result["title"] = parser.title
        
        # Language
        if parser.language:
            result["language"] = parser.language
        
        # Encoding
        if parser.encoding:
            result["encoding"] = parser.encoding
        
        # Meta tags
        if parser.meta_tags:
            result["meta_tags"] = parser.meta_tags[:10]  # Sample
            result["meta_tag_count"] = len(parser.meta_tags)
        
        # Links
        if parser.links:
            result["external_links"] = parser.links[:10]  # Sample
            result["link_count"] = len(parser.links)
        
        # Scripts
        if parser.scripts:
            result["scripts"] = parser.scripts[:5]  # Sample
            result["script_count"] = len(parser.scripts)
        
        # Styles
        if parser.styles:
            result["style_count"] = len(parser.styles)
        
        # Images
        if parser.images:
            result["images"] = parser.images[:5]  # Sample
            result["image_count"] = len(parser.images)
        
        # Headings
        headings_summary = {}
        for level, texts in parser.headings.items():
            if texts:
                headings_summary[level] = {
                    "count": len(texts),
                    "samples": texts[:3]  # First 3
                }
        if headings_summary:
            result["headings"] = headings_summary
        
        # Element counts
        if parser.element_counts:
            sorted_counts = dict(sorted(parser.element_counts.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True)[:20])  # Top 20
            result["element_counts"] = sorted_counts
            result["total_elements"] = sum(parser.element_counts.values())
            result["unique_elements"] = len(parser.element_counts)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: html_extractor.py <html_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = HTMLExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
