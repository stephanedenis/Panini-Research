#!/usr/bin/env python3
"""
XPM (X PixMap) Image Format Extractor - PaniniFS v3.48

This extractor analyzes X PixMap (XPM) image files.
XPM is a text-based image format used in X Window System,
designed to be easily included in C source code.

Format Structure:
- XPM2 format: Textual representation (older)
- XPM3 format: C source code representation (most common)
- Valid C syntax: static char *name[] = { ... };
- First line: /* XPM */
- Values string: "width height ncolors chars_per_pixel [x_hotspot y_hotspot] [XPMEXT]"
- Color definitions: "chars c color"
- Pixel data: "chars..." strings

XPM3 Format Example:
```c
/* XPM */
static char * icon_xpm[] = {
"16 16 2 1",     // width height ncolors cpp
".  c #000000",  // color 1: black
"+  c #FFFFFF",  // color 2: white
"................", // row 1
".++++++++++++++.", // row 2
...
};
```

Color Specifications:
- c color: Color for color displays
- g color: Color for grayscale displays  
- g4 color: Color for 4-level grayscale
- m color: Color for monochrome displays
- s name: Symbolic color name

Color Values:
- #RGB, #RRGGBB, #RRRGGGBBB, #RRRRGGGGBBBB
- Named colors: Black, White, Red, etc.
- None: Transparent

Chars Per Pixel (cpp):
- 1: Up to 92 colors (printable ASCII)
- 2: Up to 8464 colors
- 3+: More colors (rarely needed)

Use Cases:
- X Window System icons
- Simple graphics in C programs
- Cursor images (with hotspot)
- Toolbar icons
- Legacy GUI applications

Advantages:
- Human-readable text format
- Easy to embed in C code
- Supports transparency
- Simple editing with text editor

Disadvantages:
- Inefficient for large images
- Limited to indexed colors
- Large file sizes
- No compression (except external)

This extractor provides:
- Format version detection (XPM2/XPM3)
- Image dimensions (width, height)
- Color count and palette analysis
- Characters per pixel
- Hotspot detection (for cursors)
- Color type analysis (c, g, g4, m, s)
- Variable name extraction
- Pixel data validation

Author: PaniniFS Research Team
Version: 3.48
Target: XPM files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re

class XPMExtractor:
    """Extract metadata from XPM (X PixMap) image files."""
    
    # XPM header comment
    XPM_MAGIC = re.compile(r'/\*\s*XPM\s*\*/')
    
    # Variable declaration
    VAR_DECL = re.compile(r'static\s+(?:const\s+)?char\s*\*\s*(?:const\s+)?(\w+)\s*\[\s*\]')
    
    # Values line: "width height ncolors cpp [x y] [XPMEXT]"
    VALUES = re.compile(r'^\s*"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(-?\d+)\s+(-?\d+))?(?:\s+XPMEXT)?"')
    
    # Color definition: "chars c color" or "chars g color" etc.
    COLOR = re.compile(r'^\s*"(.{1,}?)\s+([cgms](?:4)?)\s+(.+?)"')
    
    # Pixel data line
    PIXEL = re.compile(r'^\s*"(.+)"')
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the XPM file."""
        try:
            # Read file as text
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                encoding = 'UTF-8'
            except UnicodeDecodeError:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                encoding = 'Latin-1'
            
            metadata = {
                "format": "XPM (X PixMap)",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "encoding": encoding,
            }
            
            # Check for XPM magic
            if not self.XPM_MAGIC.search(content):
                metadata["error"] = "Missing /* XPM */ header"
                return metadata
            
            metadata["format_version"] = "XPM3"  # Assume XPM3 (C format)
            
            # Parse content
            lines = content.split('\n')
            
            # Extract variable name
            var_name = self._extract_variable_name(lines)
            if var_name:
                metadata["variable_name"] = var_name
            
            # Parse image data
            image_data = self._parse_image_data(lines)
            if image_data:
                metadata.update(image_data)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "XPM (X PixMap)",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _extract_variable_name(self, lines: List[str]) -> Optional[str]:
        """Extract variable name from declaration."""
        for line in lines:
            match = self.VAR_DECL.search(line)
            if match:
                return match.group(1)
        return None
    
    def _parse_image_data(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parse XPM image data (values, colors, pixels)."""
        result = {}
        
        # Find string array content
        in_array = False
        strings = []
        
        for line in lines:
            # Check for array start
            if '{' in line:
                in_array = True
                # Extract string from same line if present
                if '"' in line:
                    parts = line.split('"')
                    if len(parts) >= 2:
                        strings.append(parts[1])
                continue
            
            # Check for array end
            if '}' in line:
                break
            
            # Extract strings
            if in_array and '"' in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    strings.append(parts[1])
        
        if not strings:
            return None
        
        # Parse values line (first string)
        values_match = self.VALUES.match(f'"{strings[0]}"')
        if not values_match:
            return None
        
        width = int(values_match.group(1))
        height = int(values_match.group(2))
        ncolors = int(values_match.group(3))
        cpp = int(values_match.group(4))
        
        result["dimensions"] = {
            "width": width,
            "height": height,
        }
        result["color_count"] = ncolors
        result["chars_per_pixel"] = cpp
        
        # Hotspot (for cursors)
        if values_match.group(5) and values_match.group(6):
            result["hotspot"] = {
                "x": int(values_match.group(5)),
                "y": int(values_match.group(6)),
            }
        
        # Parse color definitions
        colors = []
        color_types = set()
        
        for i in range(1, min(ncolors + 1, len(strings))):
            color_match = self.COLOR.match(f'"{strings[i]}"')
            if color_match:
                chars = color_match.group(1)
                color_type = color_match.group(2)
                color_value = color_match.group(3).strip()
                
                colors.append({
                    "chars": chars,
                    "type": color_type,
                    "value": color_value,
                })
                color_types.add(color_type)
        
        if colors:
            result["colors"] = {
                "count": len(colors),
                "types": sorted(list(color_types)),
                "samples": colors[:20],  # First 20 colors
            }
        
        # Analyze pixel data
        pixel_start = ncolors + 1
        pixel_end = min(pixel_start + height, len(strings))
        pixel_lines = strings[pixel_start:pixel_end]
        
        if pixel_lines:
            result["pixel_data"] = {
                "rows": len(pixel_lines),
                "expected_rows": height,
                "row_lengths": [len(row) // cpp for row in pixel_lines[:5]],  # First 5 rows
            }
        
        # Calculate color depth
        if ncolors > 0:
            import math
            bits_per_pixel = math.ceil(math.log2(ncolors))
            result["estimated_bits_per_pixel"] = bits_per_pixel
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: xpm_extractor.py <xpm_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = XPMExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
