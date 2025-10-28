#!/usr/bin/env python3
"""
PaniniFS v3.24: ODS (OpenDocument Spreadsheet) Format Extractor
================================================================

OpenDocument Spreadsheet format - open standard by OASIS.

Structure (ZIP container):
- mimetype: application/vnd.oasis.opendocument.spreadsheet
- META-INF/manifest.xml: File manifest
- content.xml: Main spreadsheet content
  - Sheets: <table:table>
  - Rows: <table:table-row>
  - Cells: <table:table-cell>
  - Values: office:value, office:value-type
- styles.xml: Styles and formatting
- meta.xml: Document metadata
  - dc:title, dc:creator, dc:date, etc.
  - meta:generator (application)
  - meta:editing-cycles
  - meta:editing-duration
- settings.xml: Application settings

Metadata extracted:
- Document title, creator, date
- Generator application
- Sheet names and counts
- Row/column counts per sheet
- Cell data samples
- Cell types (float, string, date, formula)
- Formula samples
- Named ranges
- Statistics (total cells, sheets, etc.)

Format: ZIP containing XML files
Encoding: UTF-8
Compression: DEFLATE (typical compression ratio ~70%)

Sample content.xml structure:
<office:spreadsheet>
  <table:table table:name="Sheet1">
    <table:table-row>
      <table:table-cell office:value-type="string">
        <text:p>Name</text:p>
      </table:table-cell>
      <table:table-cell office:value-type="float" office:value="123">
        <text:p>123</text:p>
      </table:table-cell>
    </table:table-row>
  </table:table>
</office:spreadsheet>

Author: PaniniFS Research Team
Version: 3.24
Date: 2025-01-14
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional


class ODSExtractor:
    """Extract metadata from OpenDocument Spreadsheet files."""
    
    # ODF namespaces
    NS = {
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
        'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'manifest': 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.zip: Optional[zipfile.ZipFile] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "OpenDocument Spreadsheet (ODS)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "metadata": {},
            "sheets": [],
            "named_ranges": [],
            "statistics": {},
            "errors": []
        }
        
        try:
            # Open ZIP
            self.zip = zipfile.ZipFile(self.filepath, 'r')
            
            # Verify mimetype
            self._verify_mimetype()
            
            # Parse metadata
            self._parse_meta()
            
            # Parse content (sheets, cells)
            self._parse_content()
            
            # Calculate statistics
            self._calculate_statistics()
            
        except zipfile.BadZipFile:
            self.data["errors"].append("Invalid ZIP file")
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        finally:
            if self.zip:
                self.zip.close()
        
        return self.data
    
    def _verify_mimetype(self):
        """Verify ODS mimetype."""
        if 'mimetype' in self.zip.namelist():
            mimetype = self.zip.read('mimetype').decode('utf-8').strip()
            expected = 'application/vnd.oasis.opendocument.spreadsheet'
            if mimetype != expected:
                self.data["errors"].append(f"Wrong mimetype: {mimetype}")
    
    def _parse_meta(self):
        """Parse meta.xml for document metadata."""
        if 'meta.xml' not in self.zip.namelist():
            return
        
        try:
            meta_xml = self.zip.read('meta.xml')
            root = ET.fromstring(meta_xml)
            
            # Find office:meta element
            meta_elem = root.find('.//office:meta', self.NS)
            if meta_elem is None:
                return
            
            # Extract metadata
            title = meta_elem.find('dc:title', self.NS)
            creator = meta_elem.find('dc:creator', self.NS)
            date = meta_elem.find('dc:date', self.NS)
            generator = meta_elem.find('meta:generator', self.NS)
            
            self.data["metadata"] = {
                "title": title.text if title is not None else None,
                "creator": creator.text if creator is not None else None,
                "date": date.text if date is not None else None,
                "generator": generator.text if generator is not None else None
            }
            
        except ET.ParseError as e:
            self.data["errors"].append(f"Meta XML parse error: {str(e)}")
    
    def _parse_content(self):
        """Parse content.xml for sheets and cells."""
        if 'content.xml' not in self.zip.namelist():
            return
        
        try:
            content_xml = self.zip.read('content.xml')
            root = ET.fromstring(content_xml)
            
            # Find all tables (sheets)
            tables = root.findall('.//table:table', self.NS)
            
            for table in tables:
                sheet_name = table.get(f"{{{self.NS['table']}}}name", "Unnamed")
                
                # Count rows and columns
                rows = table.findall('.//table:table-row', self.NS)
                
                # Sample cells (first 10 non-empty)
                cells_sample = []
                total_cells = 0
                
                for row_idx, row in enumerate(rows[:100]):  # Sample first 100 rows
                    cells = row.findall('table:table-cell', self.NS)
                    
                    for col_idx, cell in enumerate(cells):
                        total_cells += 1
                        
                        # Get cell value and type
                        value_type = cell.get(f"{{{self.NS['office']}}}value-type")
                        value = None
                        
                        if value_type == 'float':
                            value = cell.get(f"{{{self.NS['office']}}}value")
                        elif value_type == 'string':
                            text_elem = cell.find('.//text:p', self.NS)
                            if text_elem is not None:
                                value = text_elem.text
                        elif value_type == 'date':
                            value = cell.get(f"{{{self.NS['office']}}}date-value")
                        
                        # Check for formula
                        formula = cell.get(f"{{{self.NS['table']}}}formula")
                        
                        if value or formula:
                            if len(cells_sample) < 10:
                                cells_sample.append({
                                    "row": row_idx,
                                    "col": col_idx,
                                    "type": value_type,
                                    "value": value,
                                    "formula": formula
                                })
                
                sheet_data = {
                    "name": sheet_name,
                    "row_count": len(rows),
                    "cell_sample": cells_sample,
                    "total_cells_sampled": total_cells
                }
                
                self.data["sheets"].append(sheet_data)
                
        except ET.ParseError as e:
            self.data["errors"].append(f"Content XML parse error: {str(e)}")
    
    def _calculate_statistics(self):
        """Calculate ODS statistics."""
        total_sheets = len(self.data["sheets"])
        total_rows = sum(sheet["row_count"] for sheet in self.data["sheets"])
        total_cells = sum(sheet["total_cells_sampled"] for sheet in self.data["sheets"])
        
        # Formulas count
        formulas = []
        for sheet in self.data["sheets"]:
            for cell in sheet.get("cell_sample", []):
                if cell.get("formula"):
                    formulas.append(cell["formula"])
        
        # Compression ratio
        compressed_size = self.filepath.stat().st_size
        
        try:
            uncompressed_size = sum(info.file_size for info in self.zip.infolist())
            compression_ratio = round(compressed_size / uncompressed_size, 2) if uncompressed_size > 0 else 1.0
        except:
            compression_ratio = None
        
        self.data["statistics"] = {
            "total_sheets": total_sheets,
            "total_rows_sampled": total_rows,
            "total_cells_sampled": total_cells,
            "formula_count": len(formulas),
            "formulas_sample": formulas[:5],
            "compression_ratio": compression_ratio,
            "has_metadata": bool(self.data["metadata"].get("title") or self.data["metadata"].get("creator"))
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python ods_extractor.py <file.ods>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = ODSExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
