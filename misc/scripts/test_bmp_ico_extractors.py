#!/usr/bin/env python3
"""
Test Suite for BMP and ICO Extractors
======================================
Comprehensive tests for Windows Bitmap and Icon format extractors.

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.2-alpha
"""

import pytest
import struct
import os
from pathlib import Path
from bmp_extractor import BMPExtractor
from ico_extractor import ICOExtractor


class TestBMPExtractor:
    """Test BMP format extraction"""
    
    def test_bmp_24bit_structure(self):
        """Test 24-bit BMP structure extraction"""
        extractor = BMPExtractor()
        result = extractor.extract('test_sample.bmp')
        
        # Verify format
        assert result['format'] == 'BMP'
        assert result['version'] == 'BITMAPINFOHEADER'
        
        # Verify file header
        header = result['file_header']
        assert header['magic'] == 'BM'
        assert header['file_size'] == 306
        assert header['pixel_data_offset'] == 54
        
        # Verify DIB header
        dib = result['dib_header']
        assert dib['width'] == 9
        assert dib['height'] == 9
        assert dib['bit_count'] == 24
        assert dib['compression'] == 'BI_RGB'
        assert dib['planes'] == 1
        
        # Verify no palette (24-bit)
        assert len(result['color_palette']) == 0
        
        # Verify pixel data
        pixel = result['pixel_data']
        assert pixel['offset'] == 54
        assert pixel['size'] == 252
        assert pixel['matches_expected'] is True
        assert pixel['row_padding'] == 1  # 9*3 = 27, padded to 28
    
    def test_bmp_8bit_palette(self):
        """Test 8-bit BMP with color palette"""
        extractor = BMPExtractor()
        result = extractor.extract('test_sample_8bit.bmp')
        
        # Verify 8-bit format
        assert result['dib_header']['bit_count'] == 8
        
        # Verify palette exists
        palette = result['color_palette']
        assert len(palette) == 256
        
        # Verify palette structure
        assert palette[0]['index'] == 0
        assert palette[0]['red'] == 0
        assert palette[0]['green'] == 0
        assert palette[0]['blue'] == 0
        assert palette[0]['hex'] == '#000000'
        
        # Verify grayscale progression
        assert palette[64]['red'] == 64
        assert palette[64]['green'] == 64
        assert palette[64]['blue'] == 64
        assert palette[64]['hex'] == '#404040'
        
        assert palette[255]['red'] == 255
        assert palette[255]['green'] == 255
        assert palette[255]['blue'] == 255
        assert palette[255]['hex'] == '#FFFFFF'
    
    def test_bmp_statistics(self):
        """Test BMP statistics computation"""
        extractor = BMPExtractor()
        result = extractor.extract('test_sample.bmp')
        
        stats = result['statistics']
        
        # Verify dimensions
        assert stats['dimensions'] == '9x9'
        assert stats['total_pixels'] == 81
        
        # Verify color info
        assert stats['bit_depth'] == 24
        assert stats['bytes_per_pixel'] == 3.0
        assert stats['color_mode'] == 'true-color'
        assert stats['max_colors'] == 16777216
        
        # Verify flags
        assert stats['has_palette'] is False
        assert stats['palette_size'] == 0
        assert stats['compressed'] is False
        assert stats['top_down'] is False


class TestICOExtractor:
    """Test ICO format extraction"""
    
    def test_ico_structure(self):
        """Test ICO file structure extraction"""
        extractor = ICOExtractor()
        result = extractor.extract('test_sample.ico')
        
        # Verify format
        assert result['format'] == 'ICO'
        assert result['type'] == 'ICO'
        
        # Verify header
        header = result['header']
        assert header['reserved'] == 0
        assert header['type'] == 1  # ICO type
        assert header['type_name'] == 'ICO'
        assert header['count'] == 5  # 5 images
    
    def test_ico_entries(self):
        """Test ICO directory entries"""
        extractor = ICOExtractor()
        result = extractor.extract('test_sample.ico')
        
        entries = result['entries']
        assert len(entries) == 5
        
        # Verify first entry (smallest)
        entry0 = entries[0]
        assert entry0['index'] == 0
        assert entry0['width'] == 18
        assert entry0['height'] == 18
        assert entry0['dimensions'] == '18x18'
        assert entry0['bits_per_pixel'] == 32
        assert entry0['color_count'] == 'true-color'
        
        # Verify last entry (largest)
        entry4 = entries[4]
        assert entry4['width'] == 72
        assert entry4['height'] == 72
        assert entry4['dimensions'] == '72x72'
        assert entry4['bits_per_pixel'] == 32
    
    def test_ico_images(self):
        """Test ICO image data analysis"""
        extractor = ICOExtractor()
        result = extractor.extract('test_sample.ico')
        
        images = result['images']
        assert len(images) == 5
        
        # Verify all images are BMP format
        for img in images:
            assert img['format'] == 'BMP'
            assert 'dib_header_size' in img
            assert img['dib_header_size'] == 40  # BITMAPINFOHEADER
            assert img['bit_count'] == 32
            assert img['compression'] == 0  # BI_RGB
        
        # Verify dimensions match entries
        assert images[0]['bmp_width'] == 18
        assert images[0]['bmp_height'] == 18
        
        assert images[4]['bmp_width'] == 72
        assert images[4]['bmp_height'] == 72
    
    def test_ico_statistics(self):
        """Test ICO statistics computation"""
        extractor = ICOExtractor()
        result = extractor.extract('test_sample.ico')
        
        stats = result['statistics']
        
        # Verify counts
        assert stats['total_images'] == 5
        assert stats['image_formats']['BMP'] == 5
        
        # Verify dimensions (sorted)
        dims = stats['dimensions']
        assert dims == ['18x18', '26x26', '36x36', '54x54', '72x72']
        
        # Verify total size
        assert stats['total_size'] == 43544  # Sum of all image sizes
        
        # Verify BPP distribution
        assert stats['bits_per_pixel_distribution'][32] == 5


class TestBMPVariants:
    """Test various BMP format variants"""
    
    @pytest.fixture
    def temp_bmp_path(self, tmp_path):
        """Fixture for temporary BMP files"""
        return tmp_path / "test.bmp"
    
    def test_bmp_1bit_monochrome(self, temp_bmp_path):
        """Test 1-bit monochrome BMP"""
        # Create minimal 1-bit BMP (2x2 pixels)
        magic = b'BM'
        file_size = 14 + 40 + 8 + 4  # header + DIB + palette + pixels
        reserved = b'\x00\x00\x00\x00'
        pixel_offset = 14 + 40 + 8
        
        file_header = (magic + struct.pack('<I', file_size) + 
                      reserved + struct.pack('<I', pixel_offset))
        
        # DIB header
        dib = struct.pack('<IiiHHIIiiII',
            40, 2, 2, 1, 1, 0, 4, 0, 0, 2, 0)
        
        # Palette (2 colors: black, white)
        palette = b'\x00\x00\x00\x00\xFF\xFF\xFF\x00'
        
        # Pixel data (2x2, 1 bit per pixel, padded to 4 bytes)
        pixels = b'\x00\x00\x00\x00'  # All black
        
        with open(temp_bmp_path, 'wb') as f:
            f.write(file_header + dib + palette + pixels)
        
        # Test extraction
        extractor = BMPExtractor()
        result = extractor.extract(str(temp_bmp_path))
        
        assert result['dib_header']['bit_count'] == 1
        assert len(result['color_palette']) == 2
        assert result['statistics']['color_mode'] == 'monochrome'
        assert result['statistics']['max_colors'] == 2
    
    def test_bmp_4bit_16color(self, temp_bmp_path):
        """Test 4-bit 16-color BMP"""
        # Create minimal 4-bit BMP (4x4 pixels)
        magic = b'BM'
        file_size = 14 + 40 + 64 + 16  # header + DIB + palette + pixels
        reserved = b'\x00\x00\x00\x00'
        pixel_offset = 14 + 40 + 64
        
        file_header = (magic + struct.pack('<I', file_size) + 
                      reserved + struct.pack('<I', pixel_offset))
        
        # DIB header
        dib = struct.pack('<IiiHHIIiiII',
            40, 4, 4, 1, 4, 0, 16, 0, 0, 16, 0)
        
        # Palette (16 colors)
        palette = b''
        for i in range(16):
            palette += struct.pack('BBBB', i*16, i*16, i*16, 0)
        
        # Pixel data (4x4, 4 bits per pixel)
        pixels = b'\x01\x23\x45\x67' * 4  # 16 bytes
        
        with open(temp_bmp_path, 'wb') as f:
            f.write(file_header + dib + palette + pixels)
        
        # Test extraction
        extractor = BMPExtractor()
        result = extractor.extract(str(temp_bmp_path))
        
        assert result['dib_header']['bit_count'] == 4
        assert len(result['color_palette']) == 16
        assert result['statistics']['color_mode'] == '16-color'
        assert result['statistics']['max_colors'] == 16
    
    def test_bmp_32bit_alpha(self, temp_bmp_path):
        """Test 32-bit BMP with alpha channel"""
        # Create minimal 32-bit BMP (2x2 pixels)
        magic = b'BM'
        file_size = 14 + 40 + 16  # header + DIB + pixels (no palette)
        reserved = b'\x00\x00\x00\x00'
        pixel_offset = 14 + 40
        
        file_header = (magic + struct.pack('<I', file_size) + 
                      reserved + struct.pack('<I', pixel_offset))
        
        # DIB header
        dib = struct.pack('<IiiHHIIiiII',
            40, 2, 2, 1, 32, 0, 16, 0, 0, 0, 0)
        
        # Pixel data (2x2, 4 bytes per pixel: BGRA)
        pixels = b'\xFF\x00\x00\x80' * 4  # Red with 50% alpha
        
        with open(temp_bmp_path, 'wb') as f:
            f.write(file_header + dib + pixels)
        
        # Test extraction
        extractor = BMPExtractor()
        result = extractor.extract(str(temp_bmp_path))
        
        assert result['dib_header']['bit_count'] == 32
        assert result['statistics']['color_mode'] == 'true-color-alpha'
        assert result['statistics']['bytes_per_pixel'] == 4.0


class TestICOVariants:
    """Test various ICO format variants"""
    
    @pytest.fixture
    def temp_ico_path(self, tmp_path):
        """Fixture for temporary ICO files"""
        return tmp_path / "test.ico"
    
    def test_ico_single_image(self, temp_ico_path):
        """Test ICO with single image"""
        # ICONDIR header
        icondir = struct.pack('<HHH', 0, 1, 1)  # reserved, type=ICO, count=1
        
        # ICONDIRENTRY (16x16, 32-bit)
        width = height = 16
        color_count = 0
        reserved = 0
        planes = 1
        bpp = 32
        image_size = 40 + (16 * 16 * 4) + (16 * 16 // 8)  # DIB + RGBA + AND mask
        image_offset = 6 + 16  # After header and entry
        
        entry = struct.pack('<BBBBHHII',
            width, height, color_count, reserved,
            planes, bpp, image_size, image_offset)
        
        # BMP DIB header (BITMAPINFOHEADER)
        dib = struct.pack('<IiiHHIIiiII',
            40, 16, 32, 1, 32, 0, 0, 0, 0, 0, 0)  # height = 32 (includes AND mask)
        
        # Pixel data (dummy)
        pixels = b'\x00' * (16 * 16 * 4)  # RGBA
        and_mask = b'\x00' * (16 * 16 // 8)  # AND mask
        
        with open(temp_ico_path, 'wb') as f:
            f.write(icondir + entry + dib + pixels + and_mask)
        
        # Test extraction
        extractor = ICOExtractor()
        result = extractor.extract(str(temp_ico_path))
        
        assert result['header']['count'] == 1
        assert len(result['entries']) == 1
        assert len(result['images']) == 1
        
        entry = result['entries'][0]
        assert entry['width'] == 16
        assert entry['height'] == 16
        assert entry['bits_per_pixel'] == 32


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
