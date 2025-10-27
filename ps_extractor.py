#!/usr/bin/env python3
"""
PaniniFS v3.23: PS (PostScript) Format Extractor
================================================

PostScript - Page description language by Adobe.

Structure:
- Header: %!PS-Adobe-X.Y [EPSF-X.Y]
- Comments: %% (DSC - Document Structuring Conventions)
- Operators: moveto, lineto, show, setfont, etc.
- Data: text strings, paths, images

DSC Comments (important metadata):
- %%Title: Document title
- %%Creator: Application that created the file
- %%CreationDate: When created
- %%Pages: Number of pages
- %%BoundingBox: Bounding box (llx lly urx ury)
- %%DocumentFonts: Fonts used
- %%LanguageLevel: PostScript language level (1, 2, 3)
- %%EndComments: End of comment section

Metadata extracted:
- PS version and type (PS, EPS)
- DSC level conformance
- Title, creator, creation date
- Page count and bounding box
- Fonts used
- Language level
- Page size (from BoundingBox)
- Text content sample
- Image count (%%BeginDocument markers)

Format: Plain text with binary data sections possible
Encoding: ASCII (7-bit) or Binary (8-bit)

Sample structure:
%!PS-Adobe-3.0
%%Title: Sample Document
%%Creator: groff version 1.22.4
%%CreationDate: Mon Jan 13 2025
%%Pages: 5
%%BoundingBox: 0 0 612 792
%%DocumentFonts: Times-Roman Courier
%%LanguageLevel: 2
%%EndComments
%%BeginProlog
...
%%EndProlog
%%Page: 1 1
...
%%Trailer
%%EOF

Author: PaniniFS Research Team
Version: 3.23
Date: 2025-01-14
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class PSExtractor:
    """Extract metadata from PostScript (.ps, .eps) files."""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "PostScript",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "ps_version": None,
            "is_eps": False,
            "dsc_version": None,
            "title": None,
            "creator": None,
            "creation_date": None,
            "pages": None,
            "bounding_box": None,
            "fonts": [],
            "language_level": None,
            "page_size": None,
            "text_sample": [],
            "statistics": {},
            "errors": []
        }
        
        try:
            # Read file (text mode, with fallback to latin-1)
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(self.filepath, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            # Parse header and DSC comments
            self._parse_header(lines)
            self._parse_dsc_comments(lines)
            self._extract_text_samples(lines)
            self._calculate_statistics(lines)
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_header(self, lines: List[str]):
        """Parse PostScript header."""
        if not lines:
            raise ValueError("Empty file")
        
        first_line = lines[0].strip()
        
        # Check PS header: %!PS-Adobe-X.Y or %!PS-Adobe-X.Y EPSF-X.Y
        ps_match = re.match(r'%!PS-Adobe-(\d+\.\d+)(?:\s+(EPSF-\d+\.\d+))?', first_line)
        
        if ps_match:
            self.data["ps_version"] = ps_match.group(1)
            if ps_match.group(2):
                self.data["is_eps"] = True
                self.data["eps_version"] = ps_match.group(2)
        else:
            # Check if it's just %!PS
            if first_line.startswith('%!PS'):
                self.data["ps_version"] = "unknown"
            else:
                self.data["errors"].append("Invalid PostScript header")
    
    def _parse_dsc_comments(self, lines: List[str]):
        """Parse Document Structuring Convention comments."""
        for line in lines[:200]:  # Check first 200 lines for DSC
            line = line.strip()
            
            if not line.startswith('%%'):
                continue
            
            # %%Title:
            if line.startswith('%%Title:'):
                self.data["title"] = line[8:].strip()
            
            # %%Creator:
            elif line.startswith('%%Creator:'):
                self.data["creator"] = line[10:].strip()
            
            # %%CreationDate:
            elif line.startswith('%%CreationDate:'):
                self.data["creation_date"] = line[15:].strip()
            
            # %%Pages:
            elif line.startswith('%%Pages:'):
                pages_str = line[8:].strip()
                try:
                    self.data["pages"] = int(pages_str.split()[0])
                except ValueError:
                    pass
            
            # %%BoundingBox:
            elif line.startswith('%%BoundingBox:'):
                bbox_str = line[14:].strip()
                if bbox_str != '(atend)':
                    try:
                        coords = [int(x) for x in bbox_str.split()]
                        if len(coords) == 4:
                            self.data["bounding_box"] = {
                                "llx": coords[0],
                                "lly": coords[1],
                                "urx": coords[2],
                                "ury": coords[3]
                            }
                            # Calculate page size
                            width = coords[2] - coords[0]
                            height = coords[3] - coords[1]
                            self.data["page_size"] = {
                                "width": width,
                                "height": height,
                                "width_inches": round(width / 72, 2),
                                "height_inches": round(height / 72, 2)
                            }
                    except ValueError:
                        pass
            
            # %%DocumentFonts: or %%DocumentNeededFonts: or %%DocumentNeededResources:
            elif (line.startswith('%%DocumentFonts:') or 
                  line.startswith('%%DocumentNeededFonts:') or
                  line.startswith('%%DocumentNeededResources: font')):
                fonts = line.split(':', 1)[1].strip()
                # Remove 'font' keyword if present
                fonts = fonts.replace('font', '').strip()
                if fonts:
                    self.data["fonts"].extend([f.strip() for f in fonts.split()])
            
            # %%+ continuation lines (fonts)
            elif line.startswith('%%+ font'):
                fonts = line[8:].strip()  # Skip '%%+ font'
                if fonts:
                    self.data["fonts"].extend([f.strip() for f in fonts.split()])
            
            # %%LanguageLevel:
            elif line.startswith('%%LanguageLevel:'):
                try:
                    self.data["language_level"] = int(line[16:].strip())
                except ValueError:
                    pass
            
            # %%EndComments marks end of DSC header
            elif line.startswith('%%EndComments'):
                break
    
    def _extract_text_samples(self, lines: List[str]):
        """Extract sample text from PostScript show operators."""
        text_samples = []
        
        # Look for (text) show or (text) exch show patterns
        show_pattern = re.compile(r'\((.*?)\)\s*(?:exch\s+)?show')
        
        for line in lines[:1000]:  # Sample first 1000 lines
            matches = show_pattern.findall(line)
            for match in matches:
                # Decode PostScript string escapes
                text = self._decode_ps_string(match)
                if text and len(text) > 2:
                    text_samples.append(text)
                
                if len(text_samples) >= 20:
                    break
            
            if len(text_samples) >= 20:
                break
        
        self.data["text_sample"] = text_samples[:20]
    
    def _decode_ps_string(self, ps_str: str) -> str:
        """Decode PostScript string literals."""
        # Basic escapes: \n \r \t \\ \( \)
        replacements = {
            r'\\n': '\n',
            r'\\r': '\r',
            r'\\t': '\t',
            r'\\\\': '\\',
            r'\(': '(',
            r'\)': ')'
        }
        
        result = ps_str
        for pattern, replacement in replacements.items():
            result = result.replace(pattern, replacement)
        
        return result
    
    def _calculate_statistics(self, lines: List[str]):
        """Calculate PostScript statistics."""
        total_lines = len(lines)
        
        # Count operators
        operator_count = 0
        for line in lines[:500]:
            # Simple heuristic: words without % or () are likely operators
            words = line.split()
            for word in words:
                if word and not word.startswith('%') and not word.startswith('('):
                    if word.isalpha() or word in ['moveto', 'lineto', 'show', 'setfont']:
                        operator_count += 1
        
        # Count comments
        comment_count = sum(1 for line in lines if line.strip().startswith('%'))
        
        # Count page markers
        page_markers = sum(1 for line in lines if line.strip().startswith('%%Page:'))
        
        # Estimate binary data
        binary_lines = 0
        for line in lines[:100]:
            try:
                # Try to encode as ASCII
                line.encode('ascii')
            except UnicodeEncodeError:
                binary_lines += 1
        
        has_binary = binary_lines > 0
        
        self.data["statistics"] = {
            "total_lines": total_lines,
            "comment_lines": comment_count,
            "operator_count_sample": operator_count,
            "page_markers": page_markers,
            "has_binary_data": has_binary,
            "has_fonts": len(self.data["fonts"]) > 0,
            "font_count": len(self.data["fonts"]),
            "text_samples": len(self.data["text_sample"])
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python ps_extractor.py <file.ps>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = PSExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
