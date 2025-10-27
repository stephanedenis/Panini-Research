#!/usr/bin/env python3
"""
Test suite for OpenType Font (OTF) extractor.

Tests comprehensive extraction of CFF-based font structure, metadata, and tables.

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.4-alpha
"""

import pytest
import struct
import os
from otf_extractor import OTFExtractor


class TestOTFExtractor:
    """Test OTF extractor with real STIX General Italic font."""
    
    @pytest.fixture
    def sample_otf_path(self):
        """Path to sample OTF file."""
        return 'test_sample.otf'
    
    def test_otf_offset_table(self, sample_otf_path):
        """Test offset table parsing for OTF."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify format
        assert result['format'] == 'OTF'
        
        # Verify offset table
        offset_table = result['offset_table']
        assert offset_table['sfnt_version'] == 0x4F54544F  # 'OTTO'
        assert offset_table['sfnt_version_str'] == 'OTTO'
        assert offset_table['font_type'] == 'OpenType (CFF)'
        assert offset_table['num_tables'] == 13
        
        # Verify search parameters
        assert offset_table['search_range'] > 0
        assert offset_table['entry_selector'] >= 0
    
    def test_otf_table_directory(self, sample_otf_path):
        """Test table directory parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify table directory
        table_dir = result['table_directory']
        assert len(table_dir) == 13
        
        # Check required tables for OTF
        required_tables = ['head', 'hhea', 'hmtx', 'maxp', 'name', 
                          'OS/2', 'post', 'cmap', 'CFF ']
        for table in required_tables:
            assert table in table_dir, f"Missing required table: {table}"
        
        # Verify CFF table presence (specific to OTF)
        assert 'CFF ' in table_dir
        cff_entry = table_dir['CFF ']
        assert cff_entry['tag'] == 'CFF '
        assert cff_entry['length'] > 0
        
        # Should NOT have glyf or loca (TrueType-specific)
        assert 'glyf' not in table_dir
        assert 'loca' not in table_dir
    
    def test_otf_head_table(self, sample_otf_path):
        """Test head table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify head table
        head = result['tables']['head']
        assert head['version'] == '1.0'
        assert head['magic_valid'] is True
        assert head['magic_number'] == '0x5F0F3CF5'
        
        # Verify units per em
        assert head['units_per_em'] > 0
        assert head['units_per_em'] == 1000  # STIX uses 1000
        
        # Verify bounding box
        bbox = head['bounding_box']
        assert bbox['x_max'] > bbox['x_min']
        assert bbox['y_max'] > bbox['y_min']
        
        # Index to loc format should be N/A for CFF fonts
        assert 'N/A' in head['index_to_loc_format']
    
    def test_otf_name_table(self, sample_otf_path):
        """Test name table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify name table
        name = result['tables']['name']
        assert name['format'] in [0, 1]
        assert name['count'] > 0
        
        # Verify names extracted
        names = name['names']
        assert 'font_family' in names
        assert 'font_subfamily' in names
        assert 'full_name' in names
        
        # Verify STIX-specific names
        assert names['font_family'] == 'STIXGeneral'
        assert names['font_subfamily'] == 'Italic'
        assert names['full_name'] == 'STIXGeneral-Italic'
    
    def test_otf_maxp_table(self, sample_otf_path):
        """Test maxp table parsing for CFF font."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify maxp table
        maxp = result['tables']['maxp']
        assert 'version' in maxp
        assert maxp['num_glyphs'] > 0
        assert maxp['num_glyphs'] == 1063  # STIX has 1063 glyphs
        
        # CFF fonts typically have version 0.5 (minimal maxp)
        # Should NOT have TrueType-specific fields
        # (but some OpenType fonts with CFF may have version 1.0)
    
    def test_otf_hhea_table(self, sample_otf_path):
        """Test hhea table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify hhea table
        hhea = result['tables']['hhea']
        assert hhea['version'] == '1.0'
        assert hhea['ascent'] > 0
        assert hhea['descent'] < 0
        assert hhea['line_gap'] >= 0
        
        # Verify metrics
        assert hhea['advance_width_max'] > 0
        assert hhea['num_long_hor_metrics'] > 0
    
    def test_otf_hmtx_table(self, sample_otf_path):
        """Test hmtx table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify hmtx table
        hmtx = result['tables']['hmtx']
        assert hmtx['num_glyphs'] == 1063
        assert hmtx['num_long_hor_metrics'] > 0
        
        # Verify metrics array
        metrics = hmtx['metrics']
        assert len(metrics) > 0
        
        # Verify structure
        first_metric = metrics[0]
        assert 'glyph_index' in first_metric
        assert 'advance_width' in first_metric
        assert 'left_side_bearing' in first_metric
    
    def test_otf_os2_table(self, sample_otf_path):
        """Test OS/2 table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify OS/2 table
        os2 = result['tables']['OS/2']
        assert 'version' in os2
        assert os2['weight_class'] == 400  # Regular weight
        assert os2['width_class'] == 5     # Medium width
        
        # Verify style flags for Italic
        assert os2['italic'] is True   # STIXGeneral-Italic
        assert os2['bold'] is False
    
    def test_otf_post_table(self, sample_otf_path):
        """Test post table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify post table
        post = result['tables']['post']
        assert 'version' in post
        assert post['italic_angle'] != 0.0  # Italic font has non-zero angle
        assert abs(post['italic_angle']) > 10  # Should be around -16.33
        assert post['is_fixed_pitch'] is False
    
    def test_otf_cmap_table(self, sample_otf_path):
        """Test cmap table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify cmap table
        cmap = result['tables']['cmap']
        assert cmap['version'] == 0
        assert cmap['num_tables'] > 0
        
        # Verify encoding records
        records = cmap['encoding_records']
        assert len(records) > 0
        
        first_record = records[0]
        assert 'platform_id' in first_record
        assert 'encoding_id' in first_record
        assert 'subtable_offset' in first_record
    
    def test_otf_cff_table(self, sample_otf_path):
        """Test CFF table detection and basic parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify CFF table
        assert 'CFF' in result['tables']
        cff = result['tables']['CFF']
        
        # Verify CFF header
        assert 'header' in cff
        header = cff['header']
        assert 'major' in header
        assert 'minor' in header
        assert 'version' in header
        assert header['major'] >= 1
        
        # Verify basic structure
        assert cff['offset'] > 0
        assert cff['length'] > 0
        
        # Verify name index
        assert 'name_index' in cff
        name_idx = cff['name_index']
        assert name_idx['count'] >= 1  # At least one font
        
        # Note about full parsing
        assert cff['parsed'] is False
        assert 'PostScript' in cff['note']
    
    def test_otf_metadata(self, sample_otf_path):
        """Test metadata extraction."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify metadata
        metadata = result['metadata']
        assert metadata['font_family'] == 'STIXGeneral'
        assert metadata['font_subfamily'] == 'Italic'
        assert metadata['full_name'] == 'STIXGeneral-Italic'
        assert metadata['postscript_name'] == 'STIXGeneral-Italic'
        
        # Verify metrics
        assert metadata['units_per_em'] == 1000
        assert metadata['num_glyphs'] == 1063
        assert metadata['ascent'] > 0
        assert metadata['descent'] < 0
        
        # Verify style
        assert metadata['weight_class'] == 400
        assert metadata['italic'] is True
        assert metadata['bold'] is False
        assert metadata['is_fixed_pitch'] is False
        assert metadata['italic_angle'] != 0.0
        
        # Verify outline format
        assert metadata['outline_format'] == 'CFF (PostScript Type 2 charstrings)'
    
    def test_otf_statistics(self, sample_otf_path):
        """Test statistics computation."""
        extractor = OTFExtractor()
        result = extractor.extract(sample_otf_path)
        
        # Verify statistics
        stats = result['statistics']
        assert stats['file_size'] == 141844
        assert stats['file_size_kb'] > 0
        assert stats['num_tables'] == 13
        assert stats['font_type'] == 'OpenType (CFF)'
        assert stats['sfnt_version'] == 'OTTO'
        assert stats['num_glyphs'] == 1063
        assert stats['units_per_em'] == 1000
        
        # Verify CFF presence
        assert stats['has_cff'] is True
        assert stats['outline_format'] == 'CFF (PostScript)'
        
        # Verify OpenType features
        assert stats['has_opentype_features'] is True
        
        # Verify tables present
        tables = stats['tables_present']
        assert 'CFF ' in tables
        assert 'GPOS' in tables
        assert 'GSUB' in tables
        
        # Should NOT have TrueType-specific tables
        assert 'glyf' not in tables
        assert 'loca' not in tables


class TestOTFMiniFont:
    """Test OTF extractor with minimal synthetic font."""
    
    @pytest.fixture
    def mini_otf_path(self, tmp_path):
        """Create minimal OTF file for testing."""
        font_path = tmp_path / "mini.otf"
        
        # Create minimal OTF with 4 tables: head, maxp, name, CFF
        with open(font_path, 'wb') as f:
            # Offset table (12 bytes)
            f.write(b'OTTO')                        # sfnt version
            f.write(struct.pack('>H', 4))           # num tables
            f.write(struct.pack('>H', 64))          # search range
            f.write(struct.pack('>H', 2))           # entry selector
            f.write(struct.pack('>H', 0))           # range shift
            
            # Table directory (16 bytes × 4 tables = 64 bytes)
            # CFF table entry
            f.write(b'CFF ')                        # tag (note space)
            f.write(struct.pack('>I', 0xAABBCCDD))  # checksum
            f.write(struct.pack('>I', 76))          # offset
            f.write(struct.pack('>I', 20))          # length
            
            # head table entry
            f.write(b'head')
            f.write(struct.pack('>I', 0x12345678))
            f.write(struct.pack('>I', 96))
            f.write(struct.pack('>I', 54))
            
            # maxp table entry
            f.write(b'maxp')
            f.write(struct.pack('>I', 0xABCDEF00))
            f.write(struct.pack('>I', 150))
            f.write(struct.pack('>I', 6))
            
            # name table entry
            f.write(b'name')
            f.write(struct.pack('>I', 0x11223344))
            f.write(struct.pack('>I', 156))
            f.write(struct.pack('>I', 60))
            
            # CFF table (20 bytes at offset 76)
            f.write(struct.pack('B', 1))            # major
            f.write(struct.pack('B', 0))            # minor
            f.write(struct.pack('B', 4))            # hdrSize
            f.write(struct.pack('B', 4))            # offSize
            # Name INDEX
            f.write(struct.pack('>H', 1))           # count
            f.write(struct.pack('B', 1))            # offSize
            f.write(struct.pack('B', 1))            # offset[0]
            f.write(struct.pack('B', 5))            # offset[1]
            f.write(b'Mini')                        # name data
            # Padding
            f.write(b'\x00' * 8)
            
            # head table (54 bytes at offset 96)
            f.write(struct.pack('>I', 0x00010000))
            f.write(struct.pack('>I', 0x00010000))
            f.write(struct.pack('>I', 0))
            f.write(struct.pack('>I', 0x5F0F3CF5))
            f.write(struct.pack('>H', 0))
            f.write(struct.pack('>H', 1000))
            f.write(struct.pack('>Q', 0))
            f.write(struct.pack('>Q', 0))
            f.write(struct.pack('>hhhh', -100, -200, 1000, 800))
            f.write(struct.pack('>H', 0))
            f.write(struct.pack('>H', 8))
            f.write(struct.pack('>h', 2))
            f.write(struct.pack('>h', 0))  # N/A for CFF
            f.write(struct.pack('>h', 0))
            
            # maxp table (6 bytes at offset 150) - version 0.5
            f.write(struct.pack('>I', 0x00005000))
            f.write(struct.pack('>H', 50))
            
            # name table (60 bytes at offset 156)
            f.write(struct.pack('>H', 0))
            f.write(struct.pack('>H', 2))
            f.write(struct.pack('>H', 28))
            
            # Name records
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>H', 1))
            f.write(struct.pack('>H', 0x0409))
            f.write(struct.pack('>H', 1))
            f.write(struct.pack('>H', 16))
            f.write(struct.pack('>H', 0))
            
            f.write(struct.pack('>H', 3))
            f.write(struct.pack('>H', 1))
            f.write(struct.pack('>H', 0x0409))
            f.write(struct.pack('>H', 2))
            f.write(struct.pack('>H', 14))
            f.write(struct.pack('>H', 16))
            
            # String data
            f.write('MiniFont'.encode('utf-16-be'))
            f.write('Regular'.encode('utf-16-be'))
        
        return str(font_path)
    
    def test_mini_otf_structure(self, mini_otf_path):
        """Test minimal OTF parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(mini_otf_path)
        
        # Verify basic structure
        assert result['format'] == 'OTF'
        assert result['offset_table']['sfnt_version_str'] == 'OTTO'
        assert result['offset_table']['font_type'] == 'OpenType (CFF)'
        assert result['offset_table']['num_tables'] == 4
        
        # Verify tables
        assert 'CFF ' in result['table_directory']
        assert 'head' in result['table_directory']
        assert 'maxp' in result['table_directory']
        assert 'name' in result['table_directory']
    
    def test_mini_otf_cff_header(self, mini_otf_path):
        """Test minimal CFF table parsing."""
        extractor = OTFExtractor()
        result = extractor.extract(mini_otf_path)
        
        cff = result['tables']['CFF']
        assert cff['header']['major'] == 1
        assert cff['header']['minor'] == 0
        assert cff['header']['version'] == '1.0'
        assert cff['header']['hdr_size'] == 4
        
        # Verify name index
        assert cff['name_index']['count'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
