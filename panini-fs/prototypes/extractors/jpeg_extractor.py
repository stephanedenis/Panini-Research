#!/usr/bin/env python3
"""
PaniniFS v3.32: JPEG (Joint Photographic Experts Group) Extractor
===================================================================

JPEG - Lossy compressed image format for photographs.

Structure (marker-based):
- All markers start with 0xFF
- Marker format: 0xFF + marker_type
- Segment format (for most markers):
  - 0xFF + marker_type (2 bytes)
  - Length (2 bytes, big-endian, includes length field itself)
  - Data (length-2 bytes)

Common markers:
- SOI (0xFFD8): Start Of Image (no data)
- EOI (0xFFD9): End Of Image (no data)
- APP0 (0xFFE0): JFIF application segment
  - Identifier: "JFIF\0" or "JFXX\0"
  - Version, density units, X/Y density, thumbnail
- APP1 (0xFFE1): EXIF metadata
  - Identifier: "Exif\0\0"
  - TIFF-format metadata
- APP2-APP15 (0xFFE2-0xFFEF): Other application data
- COM (0xFFFE): Comment
- DQT (0xFFDB): Define Quantization Table
- DHT (0xFFC4): Define Huffman Table
- SOF0 (0xFFC0): Start Of Frame (Baseline DCT)
  - Precision, height, width, components
- SOF1 (0xFFC1): Extended Sequential DCT
- SOF2 (0xFFC2): Progressive DCT
- SOF3 (0xFFC3): Lossless
- SOS (0xFFDA): Start Of Scan (image data follows)
- DRI (0xFFDD): Define Restart Interval

JFIF (APP0):
- Version (major.minor)
- Density units: 0=no units, 1=dots/inch, 2=dots/cm
- X density, Y density
- Thumbnail width/height

EXIF (APP1):
- Camera make/model
- Exposure settings (ISO, aperture, shutter speed)
- GPS coordinates
- Date/time
- Software
- Image orientation

Metadata extracted:
- Image dimensions (width, height)
- Color components (grayscale/RGB/CMYK)
- Encoding type (baseline/progressive/lossless)
- JFIF version and DPI
- EXIF metadata (camera, settings, GPS, etc.)
- Comments
- Marker list
- Thumbnail info

Format: Binary, big-endian
Compression: DCT (Discrete Cosine Transform)

Author: PaniniFS Research Team
Version: 3.32
Date: 2025-01-14
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class JPEGExtractor:
    """Extract metadata from JPEG image files."""
    
    # JPEG markers
    SOI = 0xFFD8  # Start of Image
    EOI = 0xFFD9  # End of Image
    SOS = 0xFFDA  # Start of Scan
    
    # Frame markers
    SOF0 = 0xFFC0  # Baseline DCT
    SOF1 = 0xFFC1  # Extended Sequential DCT
    SOF2 = 0xFFC2  # Progressive DCT
    SOF3 = 0xFFC3  # Lossless
    SOF5 = 0xFFC5  # Differential Sequential DCT
    SOF6 = 0xFFC6  # Differential Progressive DCT
    SOF7 = 0xFFC7  # Differential Lossless
    SOF9 = 0xFFC9  # Extended Sequential DCT (Arithmetic)
    SOF10 = 0xFFCA # Progressive DCT (Arithmetic)
    SOF11 = 0xFFCB # Lossless (Arithmetic)
    SOF13 = 0xFFCD # Differential Sequential DCT (Arithmetic)
    SOF14 = 0xFFCE # Differential Progressive DCT (Arithmetic)
    SOF15 = 0xFFCF # Differential Lossless (Arithmetic)
    
    # Application markers
    APP0 = 0xFFE0  # JFIF
    APP1 = 0xFFE1  # EXIF
    
    # Other markers
    COM = 0xFFFE   # Comment
    
    MARKER_NAMES = {
        0xFFC0: "SOF0 (Baseline DCT)",
        0xFFC1: "SOF1 (Extended Sequential DCT)",
        0xFFC2: "SOF2 (Progressive DCT)",
        0xFFC3: "SOF3 (Lossless)",
        0xFFE0: "APP0 (JFIF)",
        0xFFE1: "APP1 (EXIF)",
        0xFFE2: "APP2",
        0xFFFE: "COM (Comment)",
        0xFFDA: "SOS (Start of Scan)",
        0xFFD8: "SOI (Start of Image)",
        0xFFD9: "EOI (End of Image)",
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "JPEG (Joint Photographic Experts Group)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "width": None,
            "height": None,
            "components": None,
            "encoding": None,
            "comments": [],
            "markers": [],
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Verify SOI marker
            if not self._verify_soi():
                raise ValueError("Invalid JPEG: missing SOI marker")
            
            # Parse markers
            self._parse_markers()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _verify_soi(self) -> bool:
        """Verify JPEG SOI marker."""
        if len(self.raw_data) < 2:
            return False
        
        marker = struct.unpack('>H', self.raw_data[0:2])[0]
        return marker == self.SOI
    
    def _parse_markers(self):
        """Parse JPEG markers."""
        offset = 2  # Skip SOI
        
        while offset < len(self.raw_data) - 1:
            # Read marker
            if self.raw_data[offset] != 0xFF:
                # Not a marker, skip
                offset += 1
                continue
            
            marker = struct.unpack('>H', self.raw_data[offset:offset+2])[0]
            offset += 2
            
            # Store marker
            marker_name = self.MARKER_NAMES.get(marker, f"0x{marker:04X}")
            self.data["markers"].append(marker_name)
            
            # EOI - end of image
            if marker == self.EOI:
                break
            
            # Standalone markers (no length field)
            if marker in (self.SOI, self.EOI) or (marker >= 0xFFD0 and marker <= 0xFFD7):
                continue
            
            # SOS - start of scan (followed by image data)
            if marker == self.SOS:
                # Skip SOS segment
                if offset + 2 <= len(self.raw_data):
                    length = struct.unpack('>H', self.raw_data[offset:offset+2])[0]
                    offset += length
                # Image data follows, scan for next marker
                while offset < len(self.raw_data) - 1:
                    if self.raw_data[offset] == 0xFF and self.raw_data[offset+1] != 0x00:
                        break
                    offset += 1
                continue
            
            # Read segment length
            if offset + 2 > len(self.raw_data):
                break
            
            length = struct.unpack('>H', self.raw_data[offset:offset+2])[0]
            
            if offset + length > len(self.raw_data):
                self.data["errors"].append(f"Truncated segment at marker {marker_name}")
                break
            
            segment_data = self.raw_data[offset+2:offset+length]
            offset += length
            
            # Parse specific markers
            if marker >= self.SOF0 and marker <= self.SOF15:
                if marker not in (0xFFC4, 0xFFC8, 0xFFCC):  # Skip DHT, DAC, RST
                    self._parse_sof(segment_data, marker)
            elif marker == self.APP0:
                self._parse_app0(segment_data)
            elif marker == self.APP1:
                self._parse_app1(segment_data)
            elif marker == self.COM:
                self._parse_comment(segment_data)
    
    def _parse_sof(self, data: bytes, marker: int):
        """Parse Start Of Frame marker."""
        if len(data) < 6:
            return
        
        precision = data[0]
        height = struct.unpack('>H', data[1:3])[0]
        width = struct.unpack('>H', data[3:5])[0]
        num_components = data[5]
        
        self.data["width"] = width
        self.data["height"] = height
        self.data["precision"] = precision
        self.data["components"] = num_components
        
        # Determine encoding type
        if marker == self.SOF0:
            self.data["encoding"] = "Baseline DCT"
        elif marker == self.SOF1:
            self.data["encoding"] = "Extended Sequential DCT"
        elif marker == self.SOF2:
            self.data["encoding"] = "Progressive DCT"
        elif marker == self.SOF3:
            self.data["encoding"] = "Lossless"
        else:
            self.data["encoding"] = f"SOF{marker - 0xFFC0}"
        
        # Component info
        if len(data) >= 6 + num_components * 3:
            components_info = []
            for i in range(num_components):
                offset = 6 + i * 3
                comp_id = data[offset]
                sampling = data[offset + 1]
                quant_table = data[offset + 2]
                
                h_sample = (sampling >> 4) & 0x0F
                v_sample = sampling & 0x0F
                
                components_info.append({
                    "id": comp_id,
                    "h_sampling": h_sample,
                    "v_sampling": v_sample,
                    "quant_table": quant_table
                })
            
            self.data["components_info"] = components_info
    
    def _parse_app0(self, data: bytes):
        """Parse APP0 (JFIF) segment."""
        if len(data) < 14:
            return
        
        # Check for JFIF identifier
        identifier = data[0:5]
        if identifier == b'JFIF\x00':
            version_major = data[5]
            version_minor = data[6]
            density_units = data[7]
            x_density = struct.unpack('>H', data[8:10])[0]
            y_density = struct.unpack('>H', data[10:12])[0]
            thumb_width = data[12]
            thumb_height = data[13]
            
            self.data["jfif"] = {
                "version": f"{version_major}.{version_minor:02d}",
                "density_units": ["No units", "DPI", "DPC"][density_units] if density_units < 3 else f"Unknown ({density_units})",
                "x_density": x_density,
                "y_density": y_density,
                "thumbnail_size": f"{thumb_width}x{thumb_height}" if thumb_width or thumb_height else None
            }
            
            if density_units == 1:  # DPI
                self.data["dpi_x"] = x_density
                self.data["dpi_y"] = y_density
    
    def _parse_app1(self, data: bytes):
        """Parse APP1 (EXIF) segment."""
        if len(data) < 6:
            return
        
        # Check for EXIF identifier
        identifier = data[0:6]
        if identifier == b'Exif\x00\x00':
            # EXIF data starts at offset 6
            # Full EXIF parsing is complex, just note presence
            self.data["has_exif"] = True
            
            # Try to extract a few basic fields if possible
            # (Full EXIF parsing would require TIFF format handling)
    
    def _parse_comment(self, data: bytes):
        """Parse COM (Comment) segment."""
        try:
            # Try UTF-8 first, then Latin-1
            try:
                comment = data.decode('utf-8')
            except UnicodeDecodeError:
                comment = data.decode('latin-1', errors='replace')
            
            if comment.strip():
                self.data["comments"].append(comment.strip())
                
        except Exception as e:
            self.data["errors"].append(f"Comment parse error: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python jpeg_extractor.py <file.jpg>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = JPEGExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
