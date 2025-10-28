#!/usr/bin/env python3
"""
PaniniFS v3.30: ODT (OpenDocument Text) Extractor
===================================================

ODT - OpenDocument Text Document format (word processing).

Structure (ZIP container):
- mimetype (first file, uncompressed)
- META-INF/manifest.xml (file listing)
- meta.xml (document metadata)
- content.xml (document text content)
- styles.xml (document styles)
- settings.xml (document settings)

content.xml structure:
- office:document-content root
- office:body → office:text
- text:h (headings, level attribute)
- text:p (paragraphs)
- text:span (inline formatting)
- text:list (lists with text:list-item)
- text:a (hyperlinks, xlink:href attribute)
- table:table (tables with table:table-row, table:table-cell)
- draw:frame (images, frames)
- text:bookmark (bookmarks)
- text:note (footnotes, endnotes)

meta.xml structure:
- office:document-meta root
- office:meta element
- dc:title, dc:creator, dc:subject, dc:description
- meta:creation-date, dc:date (modified)
- meta:keyword (multiple)
- meta:initial-creator, meta:printed-by
- meta:editing-cycles, meta:editing-duration
- meta:generator (LibreOffice version)
- meta:document-statistic (page-count, word-count, character-count, etc.)

Metadata extracted:
- Title, author, subject, description
- Creation and modification dates
- Keywords
- Generator (software)
- Statistics (pages, words, characters, paragraphs)
- Headings hierarchy
- Paragraph count
- Text samples
- Hyperlinks
- Table count
- Image count
- List items

Format: ZIP container, XML content
Encoding: UTF-8
Namespace: OASIS OpenDocument Format

Author: PaniniFS Research Team
Version: 3.30
Date: 2025-01-14
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional


class ODTExtractor:
    """Extract metadata from ODT (OpenDocument Text) files."""
    
    # ODF namespaces
    NAMESPACES = {
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
        'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
        'xlink': 'http://www.w3.org/1999/xlink',
        'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "ODT (OpenDocument Text)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "metadata": {},
            "statistics": {},
            "content": {},
            "errors": []
        }
        
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zf:
                # Verify mimetype
                if not self._verify_mimetype(zf):
                    self.data["errors"].append("Invalid or missing mimetype")
                
                # Extract metadata
                if 'meta.xml' in zf.namelist():
                    self._parse_meta(zf)
                
                # Extract content info
                if 'content.xml' in zf.namelist():
                    self._parse_content(zf)
                
        except zipfile.BadZipFile:
            self.data["errors"].append("Not a valid ZIP file")
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _verify_mimetype(self, zf: zipfile.ZipFile) -> bool:
        """Verify ODT mimetype."""
        try:
            if 'mimetype' not in zf.namelist():
                return False
            
            mimetype = zf.read('mimetype').decode('utf-8').strip()
            expected = 'application/vnd.oasis.opendocument.text'
            
            if mimetype != expected:
                self.data["errors"].append(f"Unexpected mimetype: {mimetype}")
                return False
            
            self.data["mimetype"] = mimetype
            return True
            
        except Exception as e:
            self.data["errors"].append(f"Mimetype verification failed: {str(e)}")
            return False
    
    def _parse_meta(self, zf: zipfile.ZipFile):
        """Parse meta.xml for document metadata."""
        try:
            meta_content = zf.read('meta.xml')
            root = ET.fromstring(meta_content)
            
            # Find office:meta element
            meta_elem = root.find('.//office:meta', self.NAMESPACES)
            if meta_elem is None:
                return
            
            # Basic metadata
            self._extract_text(meta_elem, 'dc:title', 'title')
            self._extract_text(meta_elem, 'dc:creator', 'author')
            self._extract_text(meta_elem, 'dc:subject', 'subject')
            self._extract_text(meta_elem, 'dc:description', 'description')
            
            # Dates
            self._extract_text(meta_elem, 'meta:creation-date', 'created')
            self._extract_text(meta_elem, 'dc:date', 'modified')
            
            # Additional metadata
            self._extract_text(meta_elem, 'meta:initial-creator', 'initial_creator')
            self._extract_text(meta_elem, 'meta:printed-by', 'printed_by')
            self._extract_text(meta_elem, 'meta:editing-cycles', 'editing_cycles')
            self._extract_text(meta_elem, 'meta:editing-duration', 'editing_duration')
            self._extract_text(meta_elem, 'meta:generator', 'generator')
            
            # Keywords
            keywords = []
            for kw in meta_elem.findall('.//meta:keyword', self.NAMESPACES):
                if kw.text:
                    keywords.append(kw.text)
            if keywords:
                self.data["metadata"]["keywords"] = keywords
            
            # Document statistics
            stats_elem = meta_elem.find('.//meta:document-statistic', self.NAMESPACES)
            if stats_elem is not None:
                stats = {}
                
                for attr in ['page-count', 'table-count', 'draw-count', 'image-count',
                           'object-count', 'paragraph-count', 'word-count', 
                           'character-count', 'non-whitespace-character-count']:
                    value = stats_elem.get(f'{{meta:}}{attr}')
                    if value is None:
                        # Try without namespace prefix
                        value = stats_elem.get(attr)
                    
                    if value:
                        try:
                            key = attr.replace('-', '_')
                            stats[key] = int(value)
                        except ValueError:
                            pass
                
                if stats:
                    self.data["statistics"] = stats
            
        except ET.ParseError as e:
            self.data["errors"].append(f"meta.xml parse error: {str(e)}")
        except Exception as e:
            self.data["errors"].append(f"meta.xml extraction error: {str(e)}")
    
    def _extract_text(self, parent, xpath: str, key: str):
        """Extract text from XML element."""
        elem = parent.find(f'.//{xpath}', self.NAMESPACES)
        if elem is not None and elem.text:
            self.data["metadata"][key] = elem.text
    
    def _parse_content(self, zf: zipfile.ZipFile):
        """Parse content.xml for document structure."""
        try:
            content_data = zf.read('content.xml')
            root = ET.fromstring(content_data)
            
            # Find office:text element
            text_elem = root.find('.//office:text', self.NAMESPACES)
            if text_elem is None:
                return
            
            content = {
                "headings": [],
                "paragraph_count": 0,
                "list_count": 0,
                "table_count": 0,
                "image_count": 0,
                "hyperlink_count": 0,
                "text_samples": []
            }
            
            # Extract headings
            for heading in text_elem.findall('.//text:h', self.NAMESPACES):
                level = heading.get(f'{{{self.NAMESPACES["text"]}}}outline-level')
                text = self._get_element_text(heading)
                
                if text:
                    content["headings"].append({
                        "level": int(level) if level else None,
                        "text": text[:200]  # Truncate long headings
                    })
            
            # Count paragraphs (direct children only to avoid counting table cells)
            paragraphs = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}p'))
            content["paragraph_count"] = len(paragraphs)
            
            # Extract text samples
            sample_count = 0
            for para in paragraphs[:5]:  # First 5 paragraphs
                text = self._get_element_text(para)
                if text and len(text.strip()) > 10:
                    content["text_samples"].append(text[:200])
                    sample_count += 1
                    if sample_count >= 3:
                        break
            
            # Count lists
            lists = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}list'))
            content["list_count"] = len(lists)
            
            # Count list items
            list_items = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}list-item'))
            content["list_item_count"] = len(list_items)
            
            # Count tables
            tables = list(text_elem.iter(f'{{{self.NAMESPACES["table"]}}}table'))
            content["table_count"] = len(tables)
            
            # Count images/drawings
            frames = list(text_elem.iter(f'{{{self.NAMESPACES["draw"]}}}frame'))
            content["image_count"] = len(frames)
            
            # Extract hyperlinks
            links = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}a'))
            content["hyperlink_count"] = len(links)
            
            hyperlinks = []
            for link in links[:10]:  # First 10 links
                href = link.get(f'{{{self.NAMESPACES["xlink"]}}}href')
                text = self._get_element_text(link)
                if href:
                    hyperlinks.append({
                        "url": href,
                        "text": text[:100] if text else None
                    })
            
            if hyperlinks:
                content["hyperlinks"] = hyperlinks
            
            # Count bookmarks
            bookmarks = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}bookmark'))
            content["bookmark_count"] = len(bookmarks)
            
            # Count notes (footnotes/endnotes)
            notes = list(text_elem.iter(f'{{{self.NAMESPACES["text"]}}}note'))
            content["note_count"] = len(notes)
            
            self.data["content"] = content
            
        except ET.ParseError as e:
            self.data["errors"].append(f"content.xml parse error: {str(e)}")
        except Exception as e:
            self.data["errors"].append(f"content.xml extraction error: {str(e)}")
    
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
        print("Usage: python odt_extractor.py <file.odt>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = ODTExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
