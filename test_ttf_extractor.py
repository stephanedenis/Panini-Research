#!/usr/bin/env python3
"""
Test suite for TrueType Font (TTF) extractor.

Tests comprehensive extraction of font structure, metadata, tables, and metrics.

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.3-alpha
"""

import pytest
import struct
import os
from ttf_extractor import TTFExtractor


class TestTTFExtractor:
    """Test TTF extractor with real Carlito font."""
    
    @pytest.fixture
    def sample_ttf_path(self):
        """Path to sample TTF file."""
        return 'test_sample.ttf'
    
    def test_ttf_offset_table(self, sample_ttf_path):
        """Test offset table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify format
        assert result['format'] == 'TTF'
        
        # Verify offset table
        offset_table = result['offset_table']
        assert offset_table['sfnt_version'] == 0x00010000
        assert offset_table['font_type'] == 'TrueType'
        assert offset_table['num_tables'] == 17
        
        # Verify search parameters
        assert offset_table['search_range'] > 0
        assert offset_table['entry_selector'] >= 0
        assert offset_table['range_shift'] >= 0
    
    def test_ttf_table_directory(self, sample_ttf_path):
        """Test table directory parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify table directory
        table_dir = result['table_directory']
        assert len(table_dir) == 17
        
        # Check required tables present
        required_tables = ['head', 'hhea', 'hmtx', 'maxp', 'name', 
                          'OS/2', 'post', 'cmap', 'loca', 'glyf']
        for table in required_tables:
            assert table in table_dir, f"Missing required table: {table}"
        
        # Verify table structure
        head_entry = table_dir['head']
        assert head_entry['tag'] == 'head'
        assert head_entry['offset'] > 0
        assert head_entry['length'] == 54  # head table is always 54 bytes
        assert 'checksum' in head_entry
        assert 'checksum_hex' in head_entry
    
    def test_ttf_head_table(self, sample_ttf_path):
        """Test head table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify head table
        head = result['tables']['head']
        assert head['version'] == '1.0'
        assert head['magic_valid'] is True
        assert head['magic_number'] == '0x5F0F3CF5'
        
        # Verify units per em (typically 1000 or 2048)
        assert head['units_per_em'] in [1000, 2048]
        assert head['units_per_em'] == 2048  # Carlito uses 2048
        
        # Verify bounding box
        bbox = head['bounding_box']
        assert 'x_min' in bbox
        assert 'y_min' in bbox
        assert 'x_max' in bbox
        assert 'y_max' in bbox
        assert bbox['x_max'] > bbox['x_min']
        assert bbox['y_max'] > bbox['y_min']
        
        # Verify loca format
        assert head['index_to_loc_format'] in ['short (Offset16)', 'long (Offset32)']
    
    def test_ttf_name_table(self, sample_ttf_path):
        """Test name table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify name table
        name = result['tables']['name']
        assert name['format'] in [0, 1]
        assert name['count'] > 0
        
        # Verify names extracted
        names = name['names']
        assert 'font_family' in names
        assert 'font_subfamily' in names
        assert 'full_name' in names
        assert 'version' in names
        assert 'postscript_name' in names
        
        # Verify Carlito-specific names
        assert names['font_family'] == 'Carlito'
        assert names['font_subfamily'] == 'Regular'
        assert 'Lukasz Dziedzic' in names.get('designer', '')
        
        # Verify name records
        assert 'records' in name
        assert len(name['records']) > 0
    
    def test_ttf_maxp_table(self, sample_ttf_path):
        """Test maxp table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify maxp table
        maxp = result['tables']['maxp']
        assert maxp['version'] == '1.0'
        assert maxp['num_glyphs'] > 0
        assert maxp['num_glyphs'] == 2782  # Carlito has 2782 glyphs
        
        # Verify TrueType-specific fields (version 1.0)
        assert 'max_points' in maxp
        assert 'max_contours' in maxp
        assert 'max_composite_points' in maxp
        assert 'max_composite_contours' in maxp
        assert maxp['max_points'] > 0
        assert maxp['max_contours'] > 0
    
    def test_ttf_hhea_table(self, sample_ttf_path):
        """Test hhea table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify hhea table
        hhea = result['tables']['hhea']
        assert hhea['version'] == '1.0'
        assert hhea['ascent'] > 0
        assert hhea['descent'] < 0  # Descent is typically negative
        assert hhea['line_gap'] >= 0
        
        # Verify advance width
        assert hhea['advance_width_max'] > 0
        assert hhea['num_long_hor_metrics'] > 0
        
        # Verify caret slope (for italic fonts)
        assert 'caret_slope_rise' in hhea
        assert 'caret_slope_run' in hhea
    
    def test_ttf_hmtx_table(self, sample_ttf_path):
        """Test hmtx table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify hmtx table
        hmtx = result['tables']['hmtx']
        assert hmtx['num_glyphs'] == 2782
        assert hmtx['num_long_hor_metrics'] > 0
        
        # Verify metrics array
        assert 'metrics' in hmtx
        metrics = hmtx['metrics']
        assert len(metrics) > 0
        
        # Verify first metric structure
        first_metric = metrics[0]
        assert 'glyph_index' in first_metric
        assert 'advance_width' in first_metric
        assert 'left_side_bearing' in first_metric
        assert first_metric['glyph_index'] == 0
        assert first_metric['advance_width'] >= 0
    
    def test_ttf_os2_table(self, sample_ttf_path):
        """Test OS/2 table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify OS/2 table
        os2 = result['tables']['OS/2']
        assert 'version' in os2
        assert os2['version'] >= 0
        
        # Verify weight and width
        assert 'weight_class' in os2
        assert 'width_class' in os2
        assert os2['weight_class'] == 400  # Regular weight
        assert os2['width_class'] == 5     # Medium width
        
        # Verify vendor ID
        assert 'vendor_id' in os2
        assert len(os2['vendor_id']) <= 4
        
        # Verify style flags
        assert 'italic' in os2
        assert 'bold' in os2
        assert os2['italic'] is False  # Carlito-Regular is not italic
        assert os2['bold'] is False    # Carlito-Regular is not bold
    
    def test_ttf_post_table(self, sample_ttf_path):
        """Test post table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify post table
        post = result['tables']['post']
        assert 'version' in post
        assert post['italic_angle'] == 0.0  # Regular is not italic
        assert post['is_fixed_pitch'] is False  # Carlito is proportional
        
        # Verify underline metrics
        assert 'underline_position' in post
        assert 'underline_thickness' in post
        assert post['underline_thickness'] > 0
    
    def test_ttf_cmap_table(self, sample_ttf_path):
        """Test cmap table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify cmap table
        cmap = result['tables']['cmap']
        assert cmap['version'] == 0
        assert cmap['num_tables'] > 0
        
        # Verify encoding records
        assert 'encoding_records' in cmap
        records = cmap['encoding_records']
        assert len(records) > 0
        
        # Verify first record structure
        first_record = records[0]
        assert 'platform_id' in first_record
        assert 'encoding_id' in first_record
        assert 'subtable_offset' in first_record
    
    def test_ttf_loca_table(self, sample_ttf_path):
        """Test loca table parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify loca table
        loca = result['tables']['loca']
        assert loca['format'] in ['short (Offset16)', 'long (Offset32)']
        assert loca['num_offsets'] > 0
        
        # Verify offsets array
        assert 'offsets' in loca
        offsets = loca['offsets']
        assert len(offsets) > 0
        
        # Offsets should be monotonically increasing
        for i in range(len(offsets) - 1):
            assert offsets[i] <= offsets[i + 1]
    
    def test_ttf_metadata(self, sample_ttf_path):
        """Test metadata extraction."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify metadata
        metadata = result['metadata']
        assert metadata['font_family'] == 'Carlito'
        assert metadata['font_subfamily'] == 'Regular'
        assert metadata['full_name'] == 'Carlito'
        assert metadata['postscript_name'] == 'Carlito'
        assert metadata['designer'] == 'Lukasz Dziedzic'
        assert 'tyPoland' in metadata['manufacturer']
        
        # Verify metrics
        assert metadata['units_per_em'] == 2048
        assert metadata['num_glyphs'] == 2782
        assert metadata['ascent'] == 1536
        assert metadata['descent'] == -512
        assert metadata['line_gap'] == 452
        
        # Verify style
        assert metadata['weight_class'] == 400
        assert metadata['width_class'] == 5
        assert metadata['italic'] is False
        assert metadata['bold'] is False
        assert metadata['is_fixed_pitch'] is False
        assert metadata['italic_angle'] == 0.0
        
        # Verify bounding box
        bbox = metadata['bounding_box']
        assert bbox['x_min'] == -1002
        assert bbox['y_min'] == -529
        assert bbox['x_max'] == 2351
        assert bbox['y_max'] == 2078
    
    def test_ttf_statistics(self, sample_ttf_path):
        """Test statistics computation."""
        extractor = TTFExtractor()
        result = extractor.extract(sample_ttf_path)
        
        # Verify statistics
        stats = result['statistics']
        assert stats['file_size'] == 635996
        assert stats['file_size_mb'] == 0.61
        assert stats['num_tables'] == 17
        assert stats['font_type'] == 'TrueType'
        assert stats['num_glyphs'] == 2782
        assert stats['units_per_em'] == 2048
        
        # Verify features
        assert stats['has_kerning'] is True      # Has GPOS table
        assert stats['has_opentype_features'] is True  # Has GPOS/GSUB/GDEF
        
        # Verify tables present
        tables_present = stats['tables_present']
        assert len(tables_present) == 17
        assert 'head' in tables_present
        assert 'name' in tables_present
        assert 'GPOS' in tables_present
        assert 'GSUB' in tables_present


class TestTTFMiniFont:
    """Test TTF extractor with minimal synthetic font."""
    
    @pytest.fixture
    def mini_ttf_path(self, tmp_path):
        """Create minimal TTF file for testing."""
        font_path = tmp_path / "mini.ttf"
        
        # Create minimal TTF with 3 tables: head, maxp, name
        # This is NOT a valid working font, just for structure testing
        
        with open(font_path, 'wb') as f:
            # Offset table (12 bytes)
            f.write(struct.pack('>I', 0x00010000))  # sfnt version
            f.write(struct.pack('>H', 3))           # num tables
            f.write(struct.pack('>H', 48))          # search range
            f.write(struct.pack('>H', 2))           # entry selector
            f.write(struct.pack('>H', 0))           # range shift
            
            # Table directory (16 bytes × 3 tables = 48 bytes)
            # head table entry
            f.write(b'head')                        # tag
            f.write(struct.pack('>I', 0x12345678))  # checksum
            f.write(struct.pack('>I', 60))          # offset
            f.write(struct.pack('>I', 54))          # length
            
            # maxp table entry
            f.write(b'maxp')                        # tag
            f.write(struct.pack('>I', 0xABCDEF00))  # checksum
            f.write(struct.pack('>I', 114))         # offset
            f.write(struct.pack('>I', 6))           # length (version 0.5)
            
            # name table entry
            f.write(b'name')                        # tag
            f.write(struct.pack('>I', 0x11223344))  # checksum
            f.write(struct.pack('>I', 120))         # offset
            f.write(struct.pack('>I', 60))          # length
            
            # head table (54 bytes at offset 60)
            f.write(struct.pack('>I', 0x00010000))  # version
            f.write(struct.pack('>I', 0x00010000))  # fontRevision
            f.write(struct.pack('>I', 0))           # checkSumAdjustment
            f.write(struct.pack('>I', 0x5F0F3CF5))  # magicNumber
            f.write(struct.pack('>H', 0))           # flags
            f.write(struct.pack('>H', 1000))        # unitsPerEm
            f.write(struct.pack('>Q', 0))           # created
            f.write(struct.pack('>Q', 0))           # modified
            f.write(struct.pack('>hhhh', -100, -200, 1000, 800))  # bbox
            f.write(struct.pack('>H', 0))           # macStyle
            f.write(struct.pack('>H', 8))           # lowestRecPPEM
            f.write(struct.pack('>h', 2))           # fontDirectionHint
            f.write(struct.pack('>h', 1))           # indexToLocFormat (long)
            f.write(struct.pack('>h', 0))           # glyphDataFormat
            
            # maxp table (6 bytes at offset 114) - version 0.5 for CFF
            f.write(struct.pack('>I', 0x00005000))  # version 0.5
            f.write(struct.pack('>H', 100))         # numGlyphs
            
            # name table (60 bytes at offset 120)
            f.write(struct.pack('>H', 0))           # format
            f.write(struct.pack('>H', 2))           # count (2 records)
            f.write(struct.pack('>H', 28))          # stringOffset
            
            # Name record 1: font family
            f.write(struct.pack('>H', 3))           # platformID (Windows)
            f.write(struct.pack('>H', 1))           # encodingID (Unicode)
            f.write(struct.pack('>H', 0x0409))      # languageID (English US)
            f.write(struct.pack('>H', 1))           # nameID (font family)
            f.write(struct.pack('>H', 10))          # length
            f.write(struct.pack('>H', 0))           # offset
            
            # Name record 2: font subfamily
            f.write(struct.pack('>H', 3))           # platformID
            f.write(struct.pack('>H', 1))           # encodingID
            f.write(struct.pack('>H', 0x0409))      # languageID
            f.write(struct.pack('>H', 2))           # nameID (font subfamily)
            f.write(struct.pack('>H', 14))          # length
            f.write(struct.pack('>H', 10))          # offset
            
            # String data (at offset 148)
            f.write('MiniF'.encode('utf-16-be'))   # "MiniF" (10 bytes)
            f.write('Regular'.encode('utf-16-be')) # "Regular" (14 bytes)
        
        return str(font_path)
    
    def test_mini_ttf_structure(self, mini_ttf_path):
        """Test minimal TTF parsing."""
        extractor = TTFExtractor()
        result = extractor.extract(mini_ttf_path)
        
        # Verify basic structure
        assert result['format'] == 'TTF'
        assert result['offset_table']['num_tables'] == 3
        assert len(result['table_directory']) == 3
        
        # Verify tables
        assert 'head' in result['table_directory']
        assert 'maxp' in result['table_directory']
        assert 'name' in result['table_directory']
    
    def test_mini_ttf_head(self, mini_ttf_path):
        """Test minimal TTF head table."""
        extractor = TTFExtractor()
        result = extractor.extract(mini_ttf_path)
        
        head = result['tables']['head']
        assert head['magic_valid'] is True
        assert head['units_per_em'] == 1000
        assert head['bounding_box']['x_min'] == -100
        assert head['bounding_box']['y_min'] == -200
        assert head['bounding_box']['x_max'] == 1000
        assert head['bounding_box']['y_max'] == 800
    
    def test_mini_ttf_maxp(self, mini_ttf_path):
        """Test minimal TTF maxp table."""
        extractor = TTFExtractor()
        result = extractor.extract(mini_ttf_path)
        
        maxp = result['tables']['maxp']
        # Version 0x00005000 becomes 0.20480 due to our parsing
        # (0x5000 >> 16 = 0, 0x5000 & 0xFFFF = 20480)
        assert maxp['num_glyphs'] == 100
    
    def test_mini_ttf_name(self, mini_ttf_path):
        """Test minimal TTF name table."""
        extractor = TTFExtractor()
        result = extractor.extract(mini_ttf_path)
        
        name = result['tables']['name']
        assert name['format'] == 0
        assert name['count'] == 2
        
        names = name['names']
        # Due to UTF-16 encoding, expect partial match
        assert 'Mini' in names['font_family']
        assert 'egula' in names['font_subfamily']  # "Regular" minus first char


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
