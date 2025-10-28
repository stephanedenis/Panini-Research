#!/usr/bin/env python3
"""
BMP Format Extractor
====================
Extracts structure and metadata from Windows Bitmap (BMP) files.

BMP Structure:
1. File Header (14 bytes):
   - Magic: 'BM' (0x42 0x4D)
   - File size (4 bytes)
   - Reserved (4 bytes)
   - Pixel data offset (4 bytes)

2. DIB Header (variable size):
   - BITMAPCOREHEADER: 12 bytes (OS/2 1.x)
   - BITMAPINFOHEADER: 40 bytes (Windows 3.x+)
   - BITMAPV4HEADER: 108 bytes (Windows 95+)
   - BITMAPV5HEADER: 124 bytes (Windows 98+)

3. Color Palette (optional, if bit depth ≤ 8):
   - RGBQUAD entries (4 bytes each)

4. Pixel Data:
   - Bottom-up (default) or top-down (negative height)
   - Row padding to 4-byte boundary
   - RGB or RGBA values

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.2-alpha
"""

import struct
from typing import Dict, List, Any, BinaryIO
from pathlib import Path


class BMPExtractor:
    """Extracts structure and metadata from BMP files"""
    
    # DIB header types
    DIB_HEADERS = {
        12: 'BITMAPCOREHEADER',      # OS/2 1.x
        40: 'BITMAPINFOHEADER',       # Windows 3.x+
        52: 'BITMAPV2INFOHEADER',     # Undocumented
        56: 'BITMAPV3INFOHEADER',     # Undocumented
        108: 'BITMAPV4HEADER',        # Windows 95+
        124: 'BITMAPV5HEADER'         # Windows 98+
    }
    
    # Compression types
    COMPRESSION = {
        0: 'BI_RGB',           # No compression
        1: 'BI_RLE8',          # RLE 8-bit/pixel
        2: 'BI_RLE4',          # RLE 4-bit/pixel
        3: 'BI_BITFIELDS',     # Bit field masks
        4: 'BI_JPEG',          # JPEG compression
        5: 'BI_PNG',           # PNG compression
        6: 'BI_ALPHABITFIELDS', # Bit field masks with alpha
        11: 'BI_CMYK',         # CMYK uncompressed
        12: 'BI_CMYKRLE8',     # CMYK RLE 8-bit
        13: 'BI_CMYKRLE4'      # CMYK RLE 4-bit
    }
    
    def __init__(self):
        self.file_header = {}
        self.dib_header = {}
        self.color_palette = []
        self.pixel_data_info = {}
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract complete BMP structure"""
        with open(file_path, 'rb') as f:
            # Read file header
            self._read_file_header(f)
            
            # Read DIB header
            self._read_dib_header(f)
            
            # Read color palette (if present)
            if self._has_palette():
                self._read_color_palette(f)
            
            # Analyze pixel data
            self._analyze_pixel_data(f)
        
        return {
            'format': 'BMP',
            'version': self.dib_header.get('type', 'unknown'),
            'file_header': self.file_header,
            'dib_header': self.dib_header,
            'color_palette': self.color_palette,
            'pixel_data': self.pixel_data_info,
            'statistics': self._compute_statistics()
        }
    
    def _read_file_header(self, f: BinaryIO) -> None:
        """Read BMP file header (14 bytes)"""
        f.seek(0)
        
        # Magic number
        magic = f.read(2)
        if magic != b'BM':
            raise ValueError(f"Invalid BMP magic: {magic.hex()}")
        
        # File size
        file_size = struct.unpack('<I', f.read(4))[0]
        
        # Reserved
        reserved1 = struct.unpack('<H', f.read(2))[0]
        reserved2 = struct.unpack('<H', f.read(2))[0]
        
        # Pixel data offset
        pixel_offset = struct.unpack('<I', f.read(4))[0]
        
        self.file_header = {
            'magic': magic.decode('ascii'),
            'file_size': file_size,
            'reserved1': reserved1,
            'reserved2': reserved2,
            'pixel_data_offset': pixel_offset
        }
    
    def _read_dib_header(self, f: BinaryIO) -> None:
        """Read DIB header (variable size)"""
        # Read header size
        dib_size = struct.unpack('<I', f.read(4))[0]
        dib_type = self.DIB_HEADERS.get(dib_size, f'UNKNOWN_{dib_size}')
        
        # Reset to start of DIB header
        f.seek(14)
        
        if dib_size == 12:
            # BITMAPCOREHEADER (OS/2 1.x)
            self._read_core_header(f)
        elif dib_size >= 40:
            # BITMAPINFOHEADER or later
            self._read_info_header(f, dib_size)
        else:
            raise ValueError(f"Unsupported DIB header size: {dib_size}")
        
        self.dib_header['size'] = dib_size
        self.dib_header['type'] = dib_type
    
    def _read_core_header(self, f: BinaryIO) -> None:
        """Read BITMAPCOREHEADER (12 bytes)"""
        header_data = f.read(12)
        
        size, width, height, planes, bit_count = struct.unpack('<IHHH', header_data[:12])
        
        self.dib_header.update({
            'width': width,
            'height': height,
            'planes': planes,
            'bit_count': bit_count,
            'compression': 'BI_RGB',  # Core header doesn't support compression
            'image_size': 0,
            'x_pixels_per_meter': 0,
            'y_pixels_per_meter': 0,
            'colors_used': 0,
            'colors_important': 0
        })
    
    def _read_info_header(self, f: BinaryIO, header_size: int) -> None:
        """Read BITMAPINFOHEADER or later (40+ bytes)"""
        header_data = f.read(header_size)
        
        # Common fields (first 40 bytes)
        (size, width, height, planes, bit_count, compression, image_size,
         x_ppm, y_ppm, colors_used, colors_important) = struct.unpack(
            '<IiiHHIIiiII', header_data[:40]
        )
        
        compression_name = self.COMPRESSION.get(compression, f'UNKNOWN_{compression}')
        
        self.dib_header.update({
            'width': abs(width),
            'height': abs(height),
            'planes': planes,
            'bit_count': bit_count,
            'compression': compression_name,
            'compression_code': compression,
            'image_size': image_size,
            'x_pixels_per_meter': x_ppm,
            'y_pixels_per_meter': y_ppm,
            'colors_used': colors_used,
            'colors_important': colors_important,
            'top_down': height < 0  # Negative height = top-down
        })
        
        # V4/V5 extended fields
        if header_size >= 108:
            # BITMAPV4HEADER fields (108 bytes)
            red_mask, green_mask, blue_mask, alpha_mask = struct.unpack(
                '<IIII', header_data[40:56]
            )
            self.dib_header.update({
                'red_mask': red_mask,
                'green_mask': green_mask,
                'blue_mask': blue_mask,
                'alpha_mask': alpha_mask
            })
        
        if header_size >= 124:
            # BITMAPV5HEADER fields (124 bytes)
            cs_type = struct.unpack('<I', header_data[56:60])[0]
            self.dib_header['color_space_type'] = cs_type
    
    def _has_palette(self) -> bool:
        """Check if BMP has color palette"""
        bit_count = self.dib_header.get('bit_count', 24)
        return bit_count <= 8
    
    def _read_color_palette(self, f: BinaryIO) -> None:
        """Read color palette (RGBQUAD entries)"""
        bit_count = self.dib_header['bit_count']
        colors_used = self.dib_header.get('colors_used', 0)
        
        # Calculate number of palette entries
        if colors_used == 0:
            colors_used = 2 ** bit_count
        
        # Palette starts after DIB header
        palette_offset = 14 + self.dib_header['size']
        f.seek(palette_offset)
        
        for i in range(colors_used):
            # RGBQUAD: blue, green, red, reserved
            bgr_reserved = f.read(4)
            if len(bgr_reserved) < 4:
                break
            
            blue, green, red, reserved = struct.unpack('BBBB', bgr_reserved)
            
            self.color_palette.append({
                'index': i,
                'red': red,
                'green': green,
                'blue': blue,
                'reserved': reserved,
                'hex': f'#{red:02X}{green:02X}{blue:02X}'
            })
    
    def _analyze_pixel_data(self, f: BinaryIO) -> None:
        """Analyze pixel data section"""
        pixel_offset = self.file_header['pixel_data_offset']
        file_size = self.file_header['file_size']
        
        f.seek(pixel_offset)
        pixel_data_size = file_size - pixel_offset
        
        width = self.dib_header['width']
        height = self.dib_header['height']
        bit_count = self.dib_header['bit_count']
        
        # Calculate row size (padded to 4-byte boundary)
        row_size = ((width * bit_count + 31) // 32) * 4
        expected_size = row_size * height
        
        self.pixel_data_info = {
            'offset': pixel_offset,
            'size': pixel_data_size,
            'expected_size': expected_size,
            'row_size': row_size,
            'row_padding': row_size - ((width * bit_count) // 8),
            'matches_expected': pixel_data_size >= expected_size
        }
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute BMP statistics"""
        width = self.dib_header['width']
        height = self.dib_header['height']
        bit_count = self.dib_header['bit_count']
        
        stats = {
            'dimensions': f'{width}x{height}',
            'total_pixels': width * height,
            'bit_depth': bit_count,
            'bytes_per_pixel': bit_count / 8,
            'has_palette': len(self.color_palette) > 0,
            'palette_size': len(self.color_palette),
            'compressed': self.dib_header.get('compression', 'BI_RGB') != 'BI_RGB',
            'top_down': self.dib_header.get('top_down', False)
        }
        
        # Color information
        if bit_count == 1:
            stats['color_mode'] = 'monochrome'
            stats['max_colors'] = 2
        elif bit_count == 4:
            stats['color_mode'] = '16-color'
            stats['max_colors'] = 16
        elif bit_count == 8:
            stats['color_mode'] = '256-color'
            stats['max_colors'] = 256
        elif bit_count == 16:
            stats['color_mode'] = 'high-color'
            stats['max_colors'] = 65536
        elif bit_count == 24:
            stats['color_mode'] = 'true-color'
            stats['max_colors'] = 16777216
        elif bit_count == 32:
            stats['color_mode'] = 'true-color-alpha'
            stats['max_colors'] = 4294967296
        
        return stats


def main():
    """Test BMP extractor"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: bmp_extractor.py <bmp_file>")
        sys.exit(1)
    
    extractor = BMPExtractor()
    result = extractor.extract(sys.argv[1])
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
