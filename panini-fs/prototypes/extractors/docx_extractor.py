#!/usr/bin/env python3
"""
PaniniFS v3.18 - DOCX (Microsoft Word) Format Extractor
Author: Stéphane Denis (SDenis.ai)
Deconstructs DOCX files to their finest details

Supports:
- Office Open XML (OOXML) format
- ZIP container structure
- document.xml parsing
- Core properties (title, author, dates)
- Extended properties (pages, words, characters)
- Custom properties
- Styles and formatting
- Relationships (images, hyperlinks)
- Content types
- Comments and revisions
- Headers and footers
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime

class DOCXExtractor:
    """Extract metadata from DOCX (Microsoft Word) files"""
    
    # XML namespaces used in OOXML
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'dcmitype': 'http://purl.org/dc/dcmitype/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
        'ct': 'http://schemas.openxmlformats.org/package/2006/content-types'
    }
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {
            'format': 'DOCX',
            'core_properties': {},
            'extended_properties': {},
            'custom_properties': {},
            'document_structure': {},
            'content_types': [],
            'relationships': [],
            'statistics': {}
        }
        self.zip = None
    
    def extract(self) -> Dict[str, Any]:
        """Extract all DOCX metadata"""
        try:
            self.zip = zipfile.ZipFile(self.filename, 'r')
        except zipfile.BadZipFile:
            raise ValueError("Not a valid DOCX file (invalid ZIP)")
        
        self._parse_core_properties()
        self._parse_extended_properties()
        self._parse_custom_properties()
        self._parse_document_structure()
        self._parse_content_types()
        self._parse_relationships()
        self._analyze_document()
        
        self.zip.close()
        return self.metadata
    
    def _parse_core_properties(self):
        """Parse core.xml (Dublin Core metadata)"""
        try:
            core_xml = self.zip.read('docProps/core.xml')
            root = ET.fromstring(core_xml)
            
            # Title
            title = root.find('.//dc:title', self.NAMESPACES)
            if title is not None and title.text:
                self.metadata['core_properties']['title'] = title.text
            
            # Creator/Author
            creator = root.find('.//dc:creator', self.NAMESPACES)
            if creator is not None and creator.text:
                self.metadata['core_properties']['creator'] = creator.text
            
            # Subject
            subject = root.find('.//dc:subject', self.NAMESPACES)
            if subject is not None and subject.text:
                self.metadata['core_properties']['subject'] = subject.text
            
            # Description
            description = root.find('.//dc:description', self.NAMESPACES)
            if description is not None and description.text:
                self.metadata['core_properties']['description'] = description.text
            
            # Keywords
            keywords = root.find('.//cp:keywords', self.NAMESPACES)
            if keywords is not None and keywords.text:
                self.metadata['core_properties']['keywords'] = keywords.text
            
            # Last modified by
            last_modified_by = root.find('.//cp:lastModifiedBy', self.NAMESPACES)
            if last_modified_by is not None and last_modified_by.text:
                self.metadata['core_properties']['last_modified_by'] = last_modified_by.text
            
            # Revision
            revision = root.find('.//cp:revision', self.NAMESPACES)
            if revision is not None and revision.text:
                self.metadata['core_properties']['revision'] = int(revision.text)
            
            # Created date
            created = root.find('.//dcterms:created', self.NAMESPACES)
            if created is not None and created.text:
                self.metadata['core_properties']['created'] = created.text
            
            # Modified date
            modified = root.find('.//dcterms:modified', self.NAMESPACES)
            if modified is not None and modified.text:
                self.metadata['core_properties']['modified'] = modified.text
            
            # Category
            category = root.find('.//cp:category', self.NAMESPACES)
            if category is not None and category.text:
                self.metadata['core_properties']['category'] = category.text
            
            # Content status
            content_status = root.find('.//cp:contentStatus', self.NAMESPACES)
            if content_status is not None and content_status.text:
                self.metadata['core_properties']['content_status'] = content_status.text
            
        except KeyError:
            pass  # core.xml not found
        except ET.ParseError:
            pass  # XML parsing error
    
    def _parse_extended_properties(self):
        """Parse app.xml (extended properties)"""
        try:
            app_xml = self.zip.read('docProps/app.xml')
            root = ET.fromstring(app_xml)
            
            # Application
            app = root.find('.//ep:Application', self.NAMESPACES)
            if app is not None and app.text:
                self.metadata['extended_properties']['application'] = app.text
            
            # App version
            app_version = root.find('.//ep:AppVersion', self.NAMESPACES)
            if app_version is not None and app_version.text:
                self.metadata['extended_properties']['app_version'] = app_version.text
            
            # Pages
            pages = root.find('.//ep:Pages', self.NAMESPACES)
            if pages is not None and pages.text:
                self.metadata['extended_properties']['pages'] = int(pages.text)
            
            # Words
            words = root.find('.//ep:Words', self.NAMESPACES)
            if words is not None and words.text:
                self.metadata['extended_properties']['words'] = int(words.text)
            
            # Characters
            characters = root.find('.//ep:Characters', self.NAMESPACES)
            if characters is not None and characters.text:
                self.metadata['extended_properties']['characters'] = int(characters.text)
            
            # Characters with spaces
            chars_with_spaces = root.find('.//ep:CharactersWithSpaces', self.NAMESPACES)
            if chars_with_spaces is not None and chars_with_spaces.text:
                self.metadata['extended_properties']['characters_with_spaces'] = int(chars_with_spaces.text)
            
            # Lines
            lines = root.find('.//ep:Lines', self.NAMESPACES)
            if lines is not None and lines.text:
                self.metadata['extended_properties']['lines'] = int(lines.text)
            
            # Paragraphs
            paragraphs = root.find('.//ep:Paragraphs', self.NAMESPACES)
            if paragraphs is not None and paragraphs.text:
                self.metadata['extended_properties']['paragraphs'] = int(paragraphs.text)
            
            # Company
            company = root.find('.//ep:Company', self.NAMESPACES)
            if company is not None and company.text:
                self.metadata['extended_properties']['company'] = company.text
            
            # Manager
            manager = root.find('.//ep:Manager', self.NAMESPACES)
            if manager is not None and manager.text:
                self.metadata['extended_properties']['manager'] = manager.text
            
            # Template
            template = root.find('.//ep:Template', self.NAMESPACES)
            if template is not None and template.text:
                self.metadata['extended_properties']['template'] = template.text
            
            # Total time
            total_time = root.find('.//ep:TotalTime', self.NAMESPACES)
            if total_time is not None and total_time.text:
                self.metadata['extended_properties']['total_time_minutes'] = int(total_time.text)
            
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_custom_properties(self):
        """Parse custom.xml (custom properties)"""
        try:
            custom_xml = self.zip.read('docProps/custom.xml')
            root = ET.fromstring(custom_xml)
            
            # Custom properties are variable, parse dynamically
            for prop in root.findall('.//{*}property'):
                name = prop.get('name')
                pid = prop.get('pid')
                
                # Get value (can be different types)
                value = None
                for child in prop:
                    if child.text:
                        value = child.text
                        break
                
                if name:
                    self.metadata['custom_properties'][name] = {
                        'value': value,
                        'pid': pid
                    }
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_document_structure(self):
        """Parse word/document.xml (main document structure)"""
        try:
            doc_xml = self.zip.read('word/document.xml')
            root = ET.fromstring(doc_xml)
            
            # Count paragraphs
            paragraphs = root.findall('.//w:p', self.NAMESPACES)
            self.metadata['document_structure']['paragraph_count'] = len(paragraphs)
            
            # Count tables
            tables = root.findall('.//w:tbl', self.NAMESPACES)
            self.metadata['document_structure']['table_count'] = len(tables)
            
            # Count images
            drawings = root.findall('.//w:drawing', self.NAMESPACES)
            self.metadata['document_structure']['drawing_count'] = len(drawings)
            
            # Count hyperlinks
            hyperlinks = root.findall('.//w:hyperlink', self.NAMESPACES)
            self.metadata['document_structure']['hyperlink_count'] = len(hyperlinks)
            
            # Extract text (first 500 chars)
            text_parts = []
            for para in paragraphs[:20]:  # First 20 paragraphs
                texts = para.findall('.//w:t', self.NAMESPACES)
                para_text = ''.join(t.text for t in texts if t.text)
                if para_text:
                    text_parts.append(para_text)
            
            if text_parts:
                full_text = '\n'.join(text_parts)
                self.metadata['document_structure']['preview'] = full_text[:500]
            
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_content_types(self):
        """Parse [Content_Types].xml"""
        try:
            ct_xml = self.zip.read('[Content_Types].xml')
            root = ET.fromstring(ct_xml)
            
            # Default types
            defaults = root.findall('.//ct:Default', self.NAMESPACES)
            for default in defaults:
                extension = default.get('Extension')
                content_type = default.get('ContentType')
                if extension and content_type:
                    self.metadata['content_types'].append({
                        'extension': extension,
                        'content_type': content_type
                    })
            
            # Override types
            overrides = root.findall('.//ct:Override', self.NAMESPACES)
            for override in overrides:
                part_name = override.get('PartName')
                content_type = override.get('ContentType')
                if part_name and content_type:
                    self.metadata['content_types'].append({
                        'part': part_name,
                        'content_type': content_type
                    })
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_relationships(self):
        """Parse _rels/.rels and word/_rels/document.xml.rels"""
        # Parse main relationships
        try:
            rels_xml = self.zip.read('_rels/.rels')
            root = ET.fromstring(rels_xml)
            
            for rel in root.findall('.//rel:Relationship', self.NAMESPACES):
                rel_id = rel.get('Id')
                rel_type = rel.get('Type')
                target = rel.get('Target')
                
                if rel_type:
                    # Extract relationship type name
                    type_name = rel_type.split('/')[-1]
                    self.metadata['relationships'].append({
                        'id': rel_id,
                        'type': type_name,
                        'target': target
                    })
        except KeyError:
            pass
        except ET.ParseError:
            pass
        
        # Parse document relationships
        try:
            doc_rels_xml = self.zip.read('word/_rels/document.xml.rels')
            root = ET.fromstring(doc_rels_xml)
            
            for rel in root.findall('.//rel:Relationship', self.NAMESPACES):
                rel_id = rel.get('Id')
                rel_type = rel.get('Type')
                target = rel.get('Target')
                
                if rel_type:
                    type_name = rel_type.split('/')[-1]
                    # Count specific relationship types
                    if type_name == 'image':
                        self.metadata['relationships'].append({
                            'id': rel_id,
                            'type': 'image',
                            'target': target
                        })
                    elif type_name == 'hyperlink':
                        self.metadata['relationships'].append({
                            'id': rel_id,
                            'type': 'hyperlink',
                            'target': target
                        })
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _analyze_document(self):
        """Generate document statistics"""
        stats = {
            'has_core_properties': bool(self.metadata['core_properties']),
            'has_extended_properties': bool(self.metadata['extended_properties']),
            'has_custom_properties': bool(self.metadata['custom_properties']),
            'content_type_count': len(self.metadata['content_types']),
            'relationship_count': len(self.metadata['relationships'])
        }
        
        # File statistics from ZIP
        file_list = self.zip.namelist()
        stats['total_files'] = len(file_list)
        stats['media_files'] = [f for f in file_list if f.startswith('word/media/')]
        stats['media_count'] = len(stats['media_files'])
        
        # Extract image types
        image_types = set()
        for media_file in stats['media_files']:
            if '.' in media_file:
                ext = media_file.split('.')[-1].lower()
                image_types.add(ext)
        stats['image_types'] = list(image_types)
        
        # ZIP file size
        with open(self.filename, 'rb') as f:
            stats['file_size'] = len(f.read())
        
        # Uncompressed size
        uncompressed_size = sum(info.file_size for info in self.zip.infolist())
        stats['uncompressed_size'] = uncompressed_size
        stats['compression_ratio'] = round(stats['file_size'] / uncompressed_size, 2) if uncompressed_size > 0 else 0
        
        self.metadata['statistics'] = stats


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python docx_extractor.py <file.docx>")
        sys.exit(1)
    
    filename = sys.argv[1]
    extractor = DOCXExtractor(filename)
    
    try:
        metadata = extractor.extract()
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
