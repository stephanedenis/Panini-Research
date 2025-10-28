#!/usr/bin/env python3
"""
PaniniFS v3.21 - PPTX (Microsoft PowerPoint) Format Extractor
Author: Stéphane Denis (SDenis.ai)
Deconstructs PPTX files to their finest details

Supports:
- Office Open XML (OOXML) format
- ZIP container structure
- Presentation metadata
- Slide content and structure
- Core properties
- Extended properties
- Slide layouts and masters
- Relationships
- Content types
- Comments
- Notes
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

class PPTXExtractor:
    """Extract metadata from PPTX (Microsoft PowerPoint) files"""
    
    # XML namespaces
    NAMESPACES = {
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
        'ct': 'http://schemas.openxmlformats.org/package/2006/content-types'
    }
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {
            'format': 'PPTX',
            'core_properties': {},
            'extended_properties': {},
            'custom_properties': {},
            'presentation': {},
            'slides': [],
            'layouts': [],
            'masters': [],
            'content_types': [],
            'relationships': [],
            'statistics': {}
        }
        self.zip = None
    
    def extract(self) -> Dict[str, Any]:
        """Extract all PPTX metadata"""
        try:
            self.zip = zipfile.ZipFile(self.filename, 'r')
        except zipfile.BadZipFile:
            raise ValueError("Not a valid PPTX file (invalid ZIP)")
        
        self._parse_core_properties()
        self._parse_extended_properties()
        self._parse_custom_properties()
        self._parse_presentation()
        self._parse_slides()
        self._parse_layouts()
        self._parse_content_types()
        self._parse_relationships()
        self._analyze_presentation()
        
        self.zip.close()
        return self.metadata
    
    def _parse_core_properties(self):
        """Parse core.xml"""
        try:
            core_xml = self.zip.read('docProps/core.xml')
            root = ET.fromstring(core_xml)
            
            # Title
            title = root.find('.//dc:title', self.NAMESPACES)
            if title is not None and title.text:
                self.metadata['core_properties']['title'] = title.text
            
            # Creator
            creator = root.find('.//dc:creator', self.NAMESPACES)
            if creator is not None and creator.text:
                self.metadata['core_properties']['creator'] = creator.text
            
            # Subject
            subject = root.find('.//dc:subject', self.NAMESPACES)
            if subject is not None and subject.text:
                self.metadata['core_properties']['subject'] = subject.text
            
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
                try:
                    self.metadata['core_properties']['revision'] = int(revision.text)
                except:
                    self.metadata['core_properties']['revision'] = revision.text
            
            # Created
            created = root.find('.//dcterms:created', self.NAMESPACES)
            if created is not None and created.text:
                self.metadata['core_properties']['created'] = created.text
            
            # Modified
            modified = root.find('.//dcterms:modified', self.NAMESPACES)
            if modified is not None and modified.text:
                self.metadata['core_properties']['modified'] = modified.text
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_extended_properties(self):
        """Parse app.xml"""
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
            
            # Total time
            total_time = root.find('.//ep:TotalTime', self.NAMESPACES)
            if total_time is not None and total_time.text:
                self.metadata['extended_properties']['total_time_minutes'] = int(total_time.text)
            
            # Words
            words = root.find('.//ep:Words', self.NAMESPACES)
            if words is not None and words.text:
                self.metadata['extended_properties']['words'] = int(words.text)
            
            # Paragraphs
            paragraphs = root.find('.//ep:Paragraphs', self.NAMESPACES)
            if paragraphs is not None and paragraphs.text:
                self.metadata['extended_properties']['paragraphs'] = int(paragraphs.text)
            
            # Slides
            slides = root.find('.//ep:Slides', self.NAMESPACES)
            if slides is not None and slides.text:
                self.metadata['extended_properties']['slides'] = int(slides.text)
            
            # Notes
            notes = root.find('.//ep:Notes', self.NAMESPACES)
            if notes is not None and notes.text:
                self.metadata['extended_properties']['notes'] = int(notes.text)
            
            # Hidden slides
            hidden_slides = root.find('.//ep:HiddenSlides', self.NAMESPACES)
            if hidden_slides is not None and hidden_slides.text:
                self.metadata['extended_properties']['hidden_slides'] = int(hidden_slides.text)
            
            # Company
            company = root.find('.//ep:Company', self.NAMESPACES)
            if company is not None and company.text:
                self.metadata['extended_properties']['company'] = company.text
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_custom_properties(self):
        """Parse custom.xml"""
        try:
            custom_xml = self.zip.read('docProps/custom.xml')
            root = ET.fromstring(custom_xml)
            
            for prop in root.findall('.//{*}property'):
                name = prop.get('name')
                value = None
                for child in prop:
                    if child.text:
                        value = child.text
                        break
                
                if name:
                    self.metadata['custom_properties'][name] = value
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_presentation(self):
        """Parse ppt/presentation.xml"""
        try:
            pres_xml = self.zip.read('ppt/presentation.xml')
            root = ET.fromstring(pres_xml)
            
            # Slide size
            sld_sz = root.find('.//p:sldSz', self.NAMESPACES)
            if sld_sz is not None:
                self.metadata['presentation']['slide_size'] = {
                    'width': int(sld_sz.get('cx', 0)),
                    'height': int(sld_sz.get('cy', 0))
                }
            
            # Slide IDs
            slide_ids = []
            for sld_id in root.findall('.//p:sldId', self.NAMESPACES):
                slide_ids.append({
                    'id': sld_id.get('id'),
                    'r_id': sld_id.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                })
            
            self.metadata['presentation']['slide_ids'] = slide_ids
            
            # Slide master IDs
            master_ids = []
            for master_id in root.findall('.//p:sldMasterId', self.NAMESPACES):
                master_ids.append({
                    'id': master_id.get('id'),
                    'r_id': master_id.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                })
            
            if master_ids:
                self.metadata['presentation']['master_ids'] = master_ids
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_slides(self):
        """Parse slide files"""
        if not self.metadata['presentation'].get('slide_ids'):
            return
        
        for idx, slide_info in enumerate(self.metadata['presentation']['slide_ids'], 1):
            slide_path = f'ppt/slides/slide{idx}.xml'
            
            try:
                slide_xml = self.zip.read(slide_path)
                root = ET.fromstring(slide_xml)
                
                slide = {
                    'number': idx,
                    'id': slide_info.get('id')
                }
                
                # Extract text content
                text_parts = []
                for text_elem in root.findall('.//a:t', self.NAMESPACES):
                    if text_elem.text:
                        text_parts.append(text_elem.text)
                
                if text_parts:
                    slide['text'] = ' '.join(text_parts)[:500]  # First 500 chars
                
                # Count shapes
                shapes = root.findall('.//p:sp', self.NAMESPACES)
                slide['shape_count'] = len(shapes)
                
                # Count images
                pics = root.findall('.//p:pic', self.NAMESPACES)
                slide['image_count'] = len(pics)
                
                # Check for notes
                notes_path = f'ppt/notesSlides/notesSlide{idx}.xml'
                if notes_path in self.zip.namelist():
                    slide['has_notes'] = True
                
                self.metadata['slides'].append(slide)
            
            except KeyError:
                continue
            except ET.ParseError:
                continue
    
    def _parse_layouts(self):
        """Parse slide layouts"""
        try:
            # Find all layout files
            layout_files = [f for f in self.zip.namelist() if f.startswith('ppt/slideLayouts/slideLayout')]
            
            for layout_file in layout_files:
                try:
                    layout_xml = self.zip.read(layout_file)
                    root = ET.fromstring(layout_xml)
                    
                    layout = {
                        'file': layout_file
                    }
                    
                    # Get layout type if available
                    cSld = root.find('.//p:cSld', self.NAMESPACES)
                    if cSld is not None:
                        layout['name'] = cSld.get('name')
                    
                    self.metadata['layouts'].append(layout)
                
                except ET.ParseError:
                    continue
        
        except KeyError:
            pass
    
    def _parse_content_types(self):
        """Parse [Content_Types].xml"""
        try:
            ct_xml = self.zip.read('[Content_Types].xml')
            root = ET.fromstring(ct_xml)
            
            for default in root.findall('.//ct:Default', self.NAMESPACES):
                extension = default.get('Extension')
                content_type = default.get('ContentType')
                if extension and content_type:
                    self.metadata['content_types'].append({
                        'extension': extension,
                        'content_type': content_type
                    })
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_relationships(self):
        """Parse _rels/.rels"""
        try:
            rels_xml = self.zip.read('_rels/.rels')
            root = ET.fromstring(rels_xml)
            
            for rel in root.findall('.//rel:Relationship', self.NAMESPACES):
                rel_type = rel.get('Type')
                if rel_type:
                    type_name = rel_type.split('/')[-1]
                    self.metadata['relationships'].append({
                        'id': rel.get('Id'),
                        'type': type_name,
                        'target': rel.get('Target')
                    })
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _analyze_presentation(self):
        """Generate presentation statistics"""
        stats = {
            'has_core_properties': bool(self.metadata['core_properties']),
            'has_extended_properties': bool(self.metadata['extended_properties']),
            'slide_count': len(self.metadata['slides']),
            'layout_count': len(self.metadata['layouts']),
            'content_type_count': len(self.metadata['content_types']),
            'relationship_count': len(self.metadata['relationships'])
        }
        
        # File statistics
        file_list = self.zip.namelist()
        stats['total_files'] = len(file_list)
        
        # Media files
        media_files = [f for f in file_list if f.startswith('ppt/media/')]
        stats['media_count'] = len(media_files)
        
        # Extract media types
        media_types = set()
        for media_file in media_files:
            if '.' in media_file:
                ext = media_file.split('.')[-1].lower()
                media_types.add(ext)
        stats['media_types'] = list(media_types)
        
        # ZIP compression
        with open(self.filename, 'rb') as f:
            stats['file_size'] = len(f.read())
        
        uncompressed_size = sum(info.file_size for info in self.zip.infolist())
        stats['uncompressed_size'] = uncompressed_size
        stats['compression_ratio'] = round(stats['file_size'] / uncompressed_size, 2) if uncompressed_size > 0 else 0
        
        # Slide statistics
        total_shapes = sum(s.get('shape_count', 0) for s in self.metadata['slides'])
        total_images = sum(s.get('image_count', 0) for s in self.metadata['slides'])
        slides_with_notes = sum(1 for s in self.metadata['slides'] if s.get('has_notes'))
        
        stats['total_shapes'] = total_shapes
        stats['total_images'] = total_images
        stats['slides_with_notes'] = slides_with_notes
        
        # Average shapes per slide
        if self.metadata['slides']:
            stats['avg_shapes_per_slide'] = round(total_shapes / len(self.metadata['slides']), 2)
        
        self.metadata['statistics'] = stats


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python pptx_extractor.py <file.pptx>")
        sys.exit(1)
    
    filename = sys.argv[1]
    extractor = PPTXExtractor(filename)
    
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
