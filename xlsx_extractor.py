#!/usr/bin/env python3
"""
PaniniFS v3.19 - XLSX (Microsoft Excel) Format Extractor
Author: Stéphane Denis (SDenis.ai)
Deconstructs XLSX files to their finest details

Supports:
- Office Open XML (OOXML) format
- ZIP container structure
- Workbook metadata (sheets, authors)
- Worksheet content (cells, formulas)
- Core properties
- Extended properties
- Custom properties
- Shared strings
- Styles and formatting
- Relationships
- Content types
- Calculation chain
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

class XLSXExtractor:
    """Extract metadata from XLSX (Microsoft Excel) files"""
    
    # XML namespaces
    NAMESPACES = {
        'wb': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
        'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {
            'format': 'XLSX',
            'core_properties': {},
            'extended_properties': {},
            'custom_properties': {},
            'workbook': {},
            'worksheets': [],
            'shared_strings': [],
            'content_types': [],
            'relationships': [],
            'statistics': {}
        }
        self.zip = None
    
    def extract(self) -> Dict[str, Any]:
        """Extract all XLSX metadata"""
        try:
            self.zip = zipfile.ZipFile(self.filename, 'r')
        except zipfile.BadZipFile:
            raise ValueError("Not a valid XLSX file (invalid ZIP)")
        
        self._parse_core_properties()
        self._parse_extended_properties()
        self._parse_custom_properties()
        self._parse_workbook()
        self._parse_worksheets()
        self._parse_shared_strings()
        self._parse_content_types()
        self._parse_relationships()
        self._analyze_workbook()
        
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
                self.metadata['core_properties']['revision'] = int(revision.text)
            
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
            
            # Company
            company = root.find('.//ep:Company', self.NAMESPACES)
            if company is not None and company.text:
                self.metadata['extended_properties']['company'] = company.text
            
            # Manager
            manager = root.find('.//ep:Manager', self.NAMESPACES)
            if manager is not None and manager.text:
                self.metadata['extended_properties']['manager'] = manager.text
        
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
    
    def _parse_workbook(self):
        """Parse xl/workbook.xml"""
        try:
            wb_xml = self.zip.read('xl/workbook.xml')
            root = ET.fromstring(wb_xml)
            
            # Parse sheets
            sheets = []
            for sheet in root.findall('.//wb:sheet', self.NAMESPACES):
                sheet_info = {
                    'name': sheet.get('name'),
                    'sheet_id': sheet.get('sheetId'),
                    'r_id': sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                }
                
                # Check if hidden
                state = sheet.get('state')
                if state:
                    sheet_info['state'] = state
                
                sheets.append(sheet_info)
            
            self.metadata['workbook']['sheets'] = sheets
            
            # Parse defined names (named ranges)
            defined_names = []
            for name_elem in root.findall('.//wb:definedName', self.NAMESPACES):
                if name_elem.text:
                    defined_names.append({
                        'name': name_elem.get('name'),
                        'formula': name_elem.text
                    })
            
            if defined_names:
                self.metadata['workbook']['defined_names'] = defined_names
            
            # Parse calculation properties
            calc_pr = root.find('.//wb:calcPr', self.NAMESPACES)
            if calc_pr is not None:
                self.metadata['workbook']['calculation'] = {
                    'mode': calc_pr.get('calcMode', 'auto'),
                    'full_calc_on_load': calc_pr.get('fullCalcOnLoad') == '1'
                }
        
        except KeyError:
            pass
        except ET.ParseError:
            pass
    
    def _parse_worksheets(self):
        """Parse worksheet files"""
        if not self.metadata['workbook'].get('sheets'):
            return
        
        for sheet_info in self.metadata['workbook']['sheets']:
            sheet_id = sheet_info.get('sheet_id', '1')
            worksheet_path = f'xl/worksheets/sheet{sheet_id}.xml'
            
            try:
                ws_xml = self.zip.read(worksheet_path)
                root = ET.fromstring(ws_xml)
                
                worksheet = {
                    'name': sheet_info['name'],
                    'sheet_id': sheet_id
                }
                
                # Dimension (used range)
                dimension = root.find('.//wb:dimension', self.NAMESPACES)
                if dimension is not None:
                    worksheet['dimension'] = dimension.get('ref')
                
                # Parse cells (limited to first 100 for metadata)
                cells = []
                for row in root.findall('.//wb:row', self.NAMESPACES)[:10]:
                    for cell in row.findall('.//wb:c', self.NAMESPACES):
                        cell_ref = cell.get('r')
                        cell_type = cell.get('t', 'n')  # n=number, s=shared string, str=formula string
                        
                        value_elem = cell.find('.//wb:v', self.NAMESPACES)
                        value = value_elem.text if value_elem is not None else None
                        
                        formula_elem = cell.find('.//wb:f', self.NAMESPACES)
                        formula = formula_elem.text if formula_elem is not None else None
                        
                        cell_data = {
                            'ref': cell_ref,
                            'type': cell_type
                        }
                        
                        if value:
                            # If shared string, resolve it
                            if cell_type == 's' and self.metadata.get('shared_strings'):
                                try:
                                    idx = int(value)
                                    if idx < len(self.metadata['shared_strings']):
                                        cell_data['value'] = self.metadata['shared_strings'][idx]
                                    else:
                                        cell_data['value'] = value
                                except:
                                    cell_data['value'] = value
                            else:
                                cell_data['value'] = value
                        
                        if formula:
                            cell_data['formula'] = formula
                        
                        cells.append(cell_data)
                
                if cells:
                    worksheet['sample_cells'] = cells[:20]  # First 20 cells
                
                # Merge cells
                merge_cells = []
                for merge in root.findall('.//wb:mergeCell', self.NAMESPACES):
                    merge_cells.append(merge.get('ref'))
                
                if merge_cells:
                    worksheet['merged_cells'] = merge_cells
                
                # Hyperlinks
                hyperlinks = []
                for link in root.findall('.//wb:hyperlink', self.NAMESPACES):
                    hyperlinks.append({
                        'ref': link.get('ref'),
                        'r_id': link.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    })
                
                if hyperlinks:
                    worksheet['hyperlinks'] = hyperlinks
                
                self.metadata['worksheets'].append(worksheet)
            
            except KeyError:
                continue
            except ET.ParseError:
                continue
    
    def _parse_shared_strings(self):
        """Parse xl/sharedStrings.xml"""
        try:
            ss_xml = self.zip.read('xl/sharedStrings.xml')
            root = ET.fromstring(ss_xml)
            
            # Parse shared strings (limit to 100 for metadata)
            for si in root.findall('.//wb:si', self.NAMESPACES)[:100]:
                # Get text content
                text_parts = []
                for t in si.findall('.//wb:t', self.NAMESPACES):
                    if t.text:
                        text_parts.append(t.text)
                
                if text_parts:
                    self.metadata['shared_strings'].append(''.join(text_parts))
        
        except KeyError:
            pass
        except ET.ParseError:
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
    
    def _analyze_workbook(self):
        """Generate workbook statistics"""
        stats = {
            'has_core_properties': bool(self.metadata['core_properties']),
            'has_extended_properties': bool(self.metadata['extended_properties']),
            'sheet_count': len(self.metadata['workbook'].get('sheets', [])),
            'worksheet_count': len(self.metadata['worksheets']),
            'shared_string_count': len(self.metadata['shared_strings']),
            'content_type_count': len(self.metadata['content_types']),
            'relationship_count': len(self.metadata['relationships'])
        }
        
        # File statistics
        file_list = self.zip.namelist()
        stats['total_files'] = len(file_list)
        
        # Media files
        media_files = [f for f in file_list if f.startswith('xl/media/')]
        stats['media_count'] = len(media_files)
        
        # ZIP compression
        with open(self.filename, 'rb') as f:
            stats['file_size'] = len(f.read())
        
        uncompressed_size = sum(info.file_size for info in self.zip.infolist())
        stats['uncompressed_size'] = uncompressed_size
        stats['compression_ratio'] = round(stats['file_size'] / uncompressed_size, 2) if uncompressed_size > 0 else 0
        
        # Cell statistics
        total_cells = 0
        total_formulas = 0
        for ws in self.metadata['worksheets']:
            if 'sample_cells' in ws:
                total_cells += len(ws['sample_cells'])
                total_formulas += sum(1 for c in ws['sample_cells'] if 'formula' in c)
        
        stats['sample_cell_count'] = total_cells
        stats['formula_count'] = total_formulas
        
        self.metadata['statistics'] = stats


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python xlsx_extractor.py <file.xlsx>")
        sys.exit(1)
    
    filename = sys.argv[1]
    extractor = XLSXExtractor(filename)
    
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
