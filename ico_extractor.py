#!/usr/bin/env python3
"""
ICO Format Extractor
====================
Extracts structure and metadata from Windows Icon (ICO) files.

ICO Structure:
1. ICONDIR header (6 bytes):
   - Reserved: 0x0000
   - Type: 0x0001 (ICO) or 0x0002 (CUR for cursors)
   - Count: Number of images in file

2. ICONDIRENTRY array (16 bytes × count):
   - Width (1 byte, 0 = 256)
   - Height (1 byte, 0 = 256)
   - Color count (1 byte, 0 if >= 256 colors)
   - Reserved (1 byte)
   - Color planes (2 bytes)
   - Bits per pixel (2 bytes)
   - Image size (4 bytes)
   - Image offset (4 bytes)

3. Image Data (variable, per entry):
   - BMP format (DIB header + optional palette + pixel data)
   - OR PNG format (complete PNG file)

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.2-alpha
"""

import struct
from typing import Dict, List, Any, BinaryIO
from pathlib import Path


class ICOExtractor:
    """Extracts structure and metadata from ICO files"""
    
    # File types
    TYPES = {
        1: 'ICO',  # Icon
        2: 'CUR'   # Cursor
    }
    
    def __init__(self):
        self.header = {}
        self.entries = []
        self.images = []
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract complete ICO structure"""
        with open(file_path, 'rb') as f:
            # Read header
            self._read_header(f)
            
            # Read directory entries
            self._read_entries(f)
            
            # Analyze image data for each entry
            self._analyze_images(f)
        
        return {
            'format': 'ICO',
            'type': self.header['type_name'],
            'header': self.header,
            'entries': self.entries,
            'images': self.images,
            'statistics': self._compute_statistics()
        }
    
    def _read_header(self, f: BinaryIO) -> None:
        """Read ICONDIR header (6 bytes)"""
        f.seek(0)
        
        # Reserved (must be 0)
        reserved = struct.unpack('<H', f.read(2))[0]
        if reserved != 0:
            raise ValueError(f"Invalid ICO reserved field: {reserved}")
        
        # Type (1 = ICO, 2 = CUR)
        icon_type = struct.unpack('<H', f.read(2))[0]
        type_name = self.TYPES.get(icon_type, f'UNKNOWN_{icon_type}')
        
        # Count
        count = struct.unpack('<H', f.read(2))[0]
        
        self.header = {
            'reserved': reserved,
            'type': icon_type,
            'type_name': type_name,
            'count': count
        }
    
    def _read_entries(self, f: BinaryIO) -> None:
        """Read ICONDIRENTRY array"""
        count = self.header['count']
        
        for i in range(count):
            entry = self._read_entry(f, i)
            self.entries.append(entry)
    
    def _read_entry(self, f: BinaryIO, index: int) -> Dict[str, Any]:
        """Read single ICONDIRENTRY (16 bytes)"""
        # Width and height (0 means 256)
        width = struct.unpack('B', f.read(1))[0]
        height = struct.unpack('B', f.read(1))[0]
        width = 256 if width == 0 else width
        height = 256 if height == 0 else height
        
        # Color count (0 if >= 256 colors)
        color_count = struct.unpack('B', f.read(1))[0]
        
        # Reserved
        reserved = struct.unpack('B', f.read(1))[0]
        
        # Color planes
        planes = struct.unpack('<H', f.read(2))[0]
        
        # Bits per pixel
        bpp = struct.unpack('<H', f.read(2))[0]
        
        # Image size
        size = struct.unpack('<I', f.read(4))[0]
        
        # Image offset
        offset = struct.unpack('<I', f.read(4))[0]
        
        return {
            'index': index,
            'width': width,
            'height': height,
            'color_count': color_count if color_count > 0 else 'true-color',
            'reserved': reserved,
            'planes': planes,
            'bits_per_pixel': bpp,
            'size': size,
            'offset': offset,
            'dimensions': f'{width}x{height}'
        }
    
    def _analyze_images(self, f: BinaryIO) -> None:
        """Analyze image data for each entry"""
        for entry in self.entries:
            offset = entry['offset']
            size = entry['size']
            
            f.seek(offset)
            image_data = f.read(min(size, 8))  # Read first 8 bytes for magic detection
            
            # Detect format
            if image_data.startswith(b'\x89PNG'):
                format_type = 'PNG'
            else:
                format_type = 'BMP'
            
            # Create image entry
            image_info = {
                'entry_index': entry['index'],
                'format': format_type,
                'offset': offset,
                'size': size
            }
            self.images.append(image_info)
            
            # Analyze format-specific details
            if format_type == 'PNG':
                self._analyze_png_image(f, entry, offset, size)
            else:
                self._analyze_bmp_image(f, entry, offset, size)
    
    def _analyze_png_image(self, f: BinaryIO, entry: Dict[str, Any],
                           offset: int, size: int) -> None:
        """Analyze PNG image in ICO"""
        f.seek(offset)
        
        # PNG signature
        signature = f.read(8)
        
        # Read IHDR chunk (first chunk after signature)
        chunk_length = struct.unpack('>I', f.read(4))[0]
        chunk_type = f.read(4)
        
        if chunk_type == b'IHDR' and chunk_length >= 13:
            width = struct.unpack('>I', f.read(4))[0]
            height = struct.unpack('>I', f.read(4))[0]
            bit_depth = struct.unpack('B', f.read(1))[0]
            color_type = struct.unpack('B', f.read(1))[0]
            
            self.images[-1].update({
                'png_width': width,
                'png_height': height,
                'bit_depth': bit_depth,
                'color_type': color_type
            })
    
    def _analyze_bmp_image(self, f: BinaryIO, entry: Dict[str, Any],
                          offset: int, size: int) -> None:
        """Analyze BMP image in ICO (DIB format, no file header)"""
        f.seek(offset)
        
        # Read DIB header size
        dib_size = struct.unpack('<I', f.read(4))[0]
        
        if dib_size >= 40:  # BITMAPINFOHEADER or later
            # Read width, height, planes, bit count
            width = struct.unpack('<i', f.read(4))[0]
            height_raw = struct.unpack('<i', f.read(4))[0]
            
            # Height in ICO is double (includes AND mask)
            height = abs(height_raw) // 2
            
            planes = struct.unpack('<H', f.read(2))[0]
            bit_count = struct.unpack('<H', f.read(2))[0]
            compression = struct.unpack('<I', f.read(4))[0]
            
            self.images[-1].update({
                'dib_header_size': dib_size,
                'bmp_width': abs(width),
                'bmp_height': height,
                'planes': planes,
                'bit_count': bit_count,
                'compression': compression
            })
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute ICO statistics"""
        stats = {
            'total_images': len(self.entries),
            'image_formats': {},
            'dimensions': [],
            'total_size': sum(e['size'] for e in self.entries)
        }
        
        # Count image formats
        for img in self.images:
            fmt = img['format']
            stats['image_formats'][fmt] = stats['image_formats'].get(fmt, 0) + 1
        
        # Collect unique dimensions
        seen_dims = set()
        for entry in self.entries:
            dim = entry['dimensions']
            if dim not in seen_dims:
                stats['dimensions'].append(dim)
                seen_dims.add(dim)
        
        # Sort dimensions by size
        stats['dimensions'].sort(key=lambda d: int(d.split('x')[0]))
        
        # Bits per pixel distribution
        bpp_dist = {}
        for entry in self.entries:
            bpp = entry['bits_per_pixel']
            bpp_dist[bpp] = bpp_dist.get(bpp, 0) + 1
        stats['bits_per_pixel_distribution'] = bpp_dist
        
        return stats


def main():
    """Test ICO extractor"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: ico_extractor.py <ico_file>")
        sys.exit(1)
    
    extractor = ICOExtractor()
    result = extractor.extract(sys.argv[1])
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
