#!/usr/bin/env python3
"""
PaniniFS v3.29: GIF (Graphics Interchange Format) Extractor
============================================================

GIF - CompuServe Graphics Interchange Format.

Structure:
- Header (6 bytes):
  - Signature: "GIF" (3 bytes)
  - Version: "87a" or "89a" (3 bytes)
  
- Logical Screen Descriptor (7 bytes):
  - Canvas Width (2 bytes, little-endian)
  - Canvas Height (2 bytes, little-endian)
  - Packed Fields (1 byte):
    - Global Color Table Flag (1 bit)
    - Color Resolution (3 bits)
    - Sort Flag (1 bit)
    - Size of Global Color Table (3 bits)
  - Background Color Index (1 byte)
  - Pixel Aspect Ratio (1 byte)
  
- Global Color Table (optional):
  - 3 bytes per color (RGB)
  - Size: 2^(N+1) colors where N is from packed fields
  
- Data blocks:
  - Image Descriptor (0x2C)
  - Graphic Control Extension (0x21 0xF9) - GIF89a
    - Disposal method, transparent color, delay time
  - Comment Extension (0x21 0xFE)
  - Application Extension (0x21 0xFF)
    - NETSCAPE2.0 for animation loops
  - Plain Text Extension (0x21 0x01)
  
- Trailer: 0x3B

Metadata extracted:
- GIF version (87a/89a)
- Canvas dimensions
- Global/local color tables
- Frame count (animation detection)
- Animation loop count
- Delay times between frames
- Transparent color
- Disposal methods
- Comments
- Compression info

Format: Binary, LZW-compressed
Encoding: Little-endian

Author: PaniniFS Research Team
Version: 3.29
Date: 2025-01-14
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, List, Optional


class GIFExtractor:
    """Extract metadata from GIF image files."""
    
    # Block types
    EXTENSION_INTRODUCER = 0x21
    IMAGE_SEPARATOR = 0x2C
    TRAILER = 0x3B
    
    # Extension labels
    GRAPHIC_CONTROL = 0xF9
    COMMENT = 0xFE
    PLAIN_TEXT = 0x01
    APPLICATION = 0xFF
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "GIF (Graphics Interchange Format)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "version": None,
            "width": None,
            "height": None,
            "has_global_color_table": False,
            "color_table_size": None,
            "background_color_index": None,
            "frames": [],
            "is_animated": False,
            "loop_count": None,
            "comments": [],
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Parse header
            self._parse_header()
            
            # Parse logical screen descriptor
            self._parse_screen_descriptor()
            
            # Parse data blocks
            self._parse_data_blocks()
            
            # Determine if animated
            self._analyze_animation()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_header(self):
        """Parse GIF header."""
        if len(self.raw_data) < 6:
            raise ValueError("File too small to be valid GIF")
        
        # Check signature
        signature = self.raw_data[0:3]
        if signature != b'GIF':
            raise ValueError(f"Invalid GIF signature: {signature}")
        
        # Read version
        version = self.raw_data[3:6].decode('ascii')
        if version not in ('87a', '89a'):
            self.data["errors"].append(f"Unknown GIF version: {version}")
        
        self.data["version"] = version
    
    def _parse_screen_descriptor(self):
        """Parse Logical Screen Descriptor."""
        if len(self.raw_data) < 13:
            raise ValueError("Truncated GIF file")
        
        # Canvas dimensions
        width = struct.unpack('<H', self.raw_data[6:8])[0]
        height = struct.unpack('<H', self.raw_data[8:10])[0]
        
        self.data["width"] = width
        self.data["height"] = height
        
        # Packed fields
        packed = self.raw_data[10]
        
        gct_flag = (packed & 0x80) >> 7
        color_resolution = ((packed & 0x70) >> 4) + 1
        sort_flag = (packed & 0x08) >> 3
        gct_size = 2 ** ((packed & 0x07) + 1)
        
        self.data["has_global_color_table"] = bool(gct_flag)
        self.data["color_resolution"] = color_resolution
        self.data["color_table_size"] = gct_size if gct_flag else 0
        
        # Background color index
        self.data["background_color_index"] = self.raw_data[11]
        
        # Pixel aspect ratio
        pixel_aspect = self.raw_data[12]
        if pixel_aspect != 0:
            self.data["pixel_aspect_ratio"] = (pixel_aspect + 15) / 64.0
    
    def _parse_data_blocks(self):
        """Parse GIF data blocks."""
        # Skip header (6) + screen descriptor (7)
        offset = 13
        
        # Skip global color table if present
        if self.data["has_global_color_table"]:
            offset += self.data["color_table_size"] * 3
        
        frame_count = 0
        current_frame = {}
        
        while offset < len(self.raw_data):
            block_type = self.raw_data[offset]
            
            # Trailer - end of GIF
            if block_type == self.TRAILER:
                break
            
            # Extension
            elif block_type == self.EXTENSION_INTRODUCER:
                offset, frame_data = self._parse_extension(offset)
                if frame_data:
                    current_frame.update(frame_data)
            
            # Image data
            elif block_type == self.IMAGE_SEPARATOR:
                offset = self._parse_image(offset, current_frame)
                frame_count += 1
                current_frame = {}
            
            else:
                # Unknown block, try to skip
                offset += 1
        
        self.data["frame_count"] = frame_count
    
    def _parse_extension(self, offset: int) -> tuple:
        """Parse extension block."""
        if offset + 2 > len(self.raw_data):
            return offset + 1, None
        
        label = self.raw_data[offset + 1]
        offset += 2
        
        frame_data = {}
        
        # Graphic Control Extension
        if label == self.GRAPHIC_CONTROL:
            if offset + 1 < len(self.raw_data):
                block_size = self.raw_data[offset]
                offset += 1
                
                if offset + block_size <= len(self.raw_data):
                    packed = self.raw_data[offset]
                    disposal_method = (packed & 0x1C) >> 2
                    transparent_flag = packed & 0x01
                    
                    delay_time = struct.unpack('<H', self.raw_data[offset+1:offset+3])[0]
                    transparent_index = self.raw_data[offset+3]
                    
                    frame_data = {
                        "disposal_method": disposal_method,
                        "delay_time": delay_time,
                        "transparent": transparent_flag == 1,
                        "transparent_index": transparent_index if transparent_flag else None
                    }
                    
                    offset += block_size
        
        # Application Extension (NETSCAPE for looping)
        elif label == self.APPLICATION:
            if offset + 1 < len(self.raw_data):
                block_size = self.raw_data[offset]
                offset += 1
                
                if offset + block_size <= len(self.raw_data):
                    app_id = self.raw_data[offset:offset+8]
                    
                    if app_id == b'NETSCAPE':
                        # Skip to sub-blocks
                        offset += block_size
                        
                        # Read sub-block
                        if offset + 1 < len(self.raw_data):
                            sub_size = self.raw_data[offset]
                            offset += 1
                            
                            if sub_size == 3 and offset + 3 <= len(self.raw_data):
                                loop_count = struct.unpack('<H', self.raw_data[offset+1:offset+3])[0]
                                self.data["loop_count"] = loop_count
                                offset += sub_size
                    else:
                        offset += block_size
        
        # Comment Extension
        elif label == self.COMMENT:
            comment_data = bytearray()
            
            while offset < len(self.raw_data):
                block_size = self.raw_data[offset]
                offset += 1
                
                if block_size == 0:
                    break
                
                if offset + block_size <= len(self.raw_data):
                    comment_data.extend(self.raw_data[offset:offset+block_size])
                    offset += block_size
            
            if comment_data:
                try:
                    comment = comment_data.decode('ascii', errors='replace')
                    self.data["comments"].append(comment)
                except:
                    pass
        
        # Skip other extension data
        else:
            if offset < len(self.raw_data):
                block_size = self.raw_data[offset]
                offset += 1 + block_size
        
        # Skip to block terminator (0x00)
        while offset < len(self.raw_data):
            size = self.raw_data[offset]
            offset += 1
            
            if size == 0:
                break
            
            offset += size
        
        return offset, frame_data
    
    def _parse_image(self, offset: int, frame_data: dict) -> int:
        """Parse image descriptor."""
        if offset + 10 > len(self.raw_data):
            return offset + 1
        
        # Image position and size
        left = struct.unpack('<H', self.raw_data[offset+1:offset+3])[0]
        top = struct.unpack('<H', self.raw_data[offset+3:offset+5])[0]
        width = struct.unpack('<H', self.raw_data[offset+5:offset+7])[0]
        height = struct.unpack('<H', self.raw_data[offset+7:offset+9])[0]
        
        packed = self.raw_data[offset+9]
        local_color_table = (packed & 0x80) >> 7
        interlaced = (packed & 0x40) >> 6
        
        frame_info = {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "interlaced": bool(interlaced),
            **frame_data
        }
        
        self.data["frames"].append(frame_info)
        
        offset += 10
        
        # Skip local color table if present
        if local_color_table:
            lct_size = 2 ** ((packed & 0x07) + 1)
            offset += lct_size * 3
        
        # Skip LZW minimum code size
        if offset < len(self.raw_data):
            offset += 1
        
        # Skip image data sub-blocks
        while offset < len(self.raw_data):
            block_size = self.raw_data[offset]
            offset += 1
            
            if block_size == 0:
                break
            
            offset += block_size
        
        return offset
    
    def _analyze_animation(self):
        """Determine if GIF is animated."""
        self.data["is_animated"] = self.data["frame_count"] > 1
        
        # Calculate total duration if animated
        if self.data["is_animated"]:
            total_delay = sum(f.get("delay_time", 0) for f in self.data["frames"])
            self.data["total_duration_cs"] = total_delay  # centiseconds
            self.data["total_duration_seconds"] = round(total_delay / 100, 2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python gif_extractor.py <file.gif>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = GIFExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
