#!/usr/bin/env python3
"""
OpenType Font (OTF) Format Extractor

Extracts comprehensive structure from OpenType font files (.otf).

OpenType fonts with CFF outlines are binary files containing:
1. Offset Table (12 bytes): sfnt version 'OTTO', table count, search parameters
2. Table Directory (16 bytes per table): tag, checksum, offset, length
3. Font Tables: Similar to TrueType but with CFF table instead of glyf/loca

Key Differences from TrueType:
- sfnt version: 'OTTO' (0x4F54544F) instead of 0x00010000
- Uses CFF (Compact Font Format) table for glyph outlines (PostScript curves)
- No 'glyf' or 'loca' tables
- CFF contains PostScript Type 2 charstrings

CFF Table Structure:
- Header (4 bytes): major, minor, header size, offset size
- Name INDEX: Font names
- Top DICT INDEX: Font-level metadata
- String INDEX: Custom strings
- Global Subr INDEX: Global subroutines
- Encodings: Character code to glyph mapping
- Charsets: Glyph names
- CharStrings INDEX: Glyph outline data (Type 2 charstrings)
- Private DICT: Private font data
- Local Subr INDEX: Local subroutines

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.4-alpha
"""

import struct
import os
from typing import Dict, List, Tuple, Any, Optional


class OTFExtractor:
    """Extract structure and metadata from OpenType Font files (CFF)."""
    
    def __init__(self):
        """Initialize OTF extractor."""
        self.file_path = None
        self.file_size = 0
        self.data = None
        
        # Font structure
        self.offset_table = {}
        self.table_directory = {}
        self.tables = {}
        
        # Metadata
        self.metadata = {}
        self.cff_data = {}
        
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract complete structure from OTF file.
        
        Args:
            file_path: Path to OTF file
            
        Returns:
            Dictionary containing complete font structure
        """
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        
        # Read entire file
        with open(file_path, 'rb') as f:
            self.data = f.read()
        
        # Parse font structure
        self._read_offset_table()
        self._read_table_directory()
        self._read_tables()
        
        # Build result
        result = {
            'format': 'OTF',
            'file_path': file_path,
            'file_size': self.file_size,
            'offset_table': self.offset_table,
            'table_directory': self.table_directory,
            'tables': self.tables,
            'metadata': self.metadata,
            'statistics': self._compute_statistics()
        }
        
        return result
    
    def _read_offset_table(self):
        """Read offset table (first 12 bytes)."""
        sfnt_version, num_tables, search_range, entry_selector, range_shift = \
            struct.unpack('>IHHHH', self.data[0:12])
        
        # Determine font type
        if sfnt_version == 0x4F54544F:  # 'OTTO'
            font_type = 'OpenType (CFF)'
        elif sfnt_version == 0x00010000:
            font_type = 'TrueType'
        else:
            font_type = f'Unknown (0x{sfnt_version:08X})'
        
        self.offset_table = {
            'sfnt_version': sfnt_version,
            'sfnt_version_hex': f'0x{sfnt_version:08X}',
            'sfnt_version_str': struct.pack('>I', sfnt_version).decode('ascii', errors='replace'),
            'font_type': font_type,
            'num_tables': num_tables,
            'search_range': search_range,
            'entry_selector': entry_selector,
            'range_shift': range_shift
        }
    
    def _read_table_directory(self):
        """Read table directory (16 bytes per table)."""
        num_tables = self.offset_table['num_tables']
        offset = 12
        
        for i in range(num_tables):
            tag_bytes = self.data[offset:offset+4]
            tag = tag_bytes.decode('ascii', errors='replace')
            
            checksum, table_offset, length = struct.unpack(
                '>III', self.data[offset+4:offset+16]
            )
            
            self.table_directory[tag] = {
                'tag': tag,
                'checksum': checksum,
                'checksum_hex': f'0x{checksum:08X}',
                'offset': table_offset,
                'length': length,
                'index': i
            }
            
            offset += 16
    
    def _read_tables(self):
        """Read and parse all font tables."""
        # Standard tables (same as TrueType)
        if 'head' in self.table_directory:
            self.tables['head'] = self._read_head_table()
        
        if 'name' in self.table_directory:
            self.tables['name'] = self._read_name_table()
        
        if 'maxp' in self.table_directory:
            self.tables['maxp'] = self._read_maxp_table()
        
        if 'hhea' in self.table_directory:
            self.tables['hhea'] = self._read_hhea_table()
        
        if 'hmtx' in self.table_directory:
            self.tables['hmtx'] = self._read_hmtx_table()
        
        if 'OS/2' in self.table_directory:
            self.tables['OS/2'] = self._read_os2_table()
        
        if 'post' in self.table_directory:
            self.tables['post'] = self._read_post_table()
        
        if 'cmap' in self.table_directory:
            self.tables['cmap'] = self._read_cmap_table()
        
        # CFF table (specific to OpenType)
        if 'CFF ' in self.table_directory:
            self.tables['CFF'] = self._read_cff_table()
        
        # Optional tables
        if 'GPOS' in self.table_directory:
            self.tables['GPOS'] = {'parsed': False, 'reason': 'Complex OpenType table'}
        
        if 'GSUB' in self.table_directory:
            self.tables['GSUB'] = {'parsed': False, 'reason': 'Complex OpenType table'}
        
        if 'GDEF' in self.table_directory:
            self.tables['GDEF'] = {'parsed': False, 'reason': 'Complex OpenType table'}
        
        # Build metadata
        self._build_metadata()
    
    def _read_head_table(self) -> Dict[str, Any]:
        """Read 'head' table (font header)."""
        entry = self.table_directory['head']
        offset = entry['offset']
        
        data = self.data[offset:offset+54]
        
        version = struct.unpack('>I', data[0:4])[0]
        font_revision = struct.unpack('>I', data[4:8])[0]
        checksum_adjustment = struct.unpack('>I', data[8:12])[0]
        magic_number = struct.unpack('>I', data[12:16])[0]
        flags = struct.unpack('>H', data[16:18])[0]
        units_per_em = struct.unpack('>H', data[18:20])[0]
        
        bbox_data = struct.unpack('>hhhh', data[36:44])
        mac_style = struct.unpack('>H', data[44:46])[0]
        lowest_rec_ppem = struct.unpack('>H', data[46:48])[0]
        font_direction_hint = struct.unpack('>h', data[48:50])[0]
        index_to_loc_format = struct.unpack('>h', data[50:52])[0]
        glyph_data_format = struct.unpack('>h', data[52:54])[0]
        
        return {
            'version': f'{version >> 16}.{version & 0xFFFF}',
            'font_revision': f'{font_revision >> 16}.{font_revision & 0xFFFF}',
            'checksum_adjustment': checksum_adjustment,
            'magic_number': f'0x{magic_number:08X}',
            'magic_valid': magic_number == 0x5F0F3CF5,
            'flags': flags,
            'units_per_em': units_per_em,
            'bounding_box': {
                'x_min': bbox_data[0],
                'y_min': bbox_data[1],
                'x_max': bbox_data[2],
                'y_max': bbox_data[3]
            },
            'mac_style': mac_style,
            'lowest_rec_ppem': lowest_rec_ppem,
            'font_direction_hint': font_direction_hint,
            'index_to_loc_format': 'N/A (CFF font)',
            'glyph_data_format': glyph_data_format
        }
    
    def _read_name_table(self) -> Dict[str, Any]:
        """Read 'name' table (font naming information)."""
        entry = self.table_directory['name']
        offset = entry['offset']
        
        format_version = struct.unpack('>H', self.data[offset:offset+2])[0]
        count = struct.unpack('>H', self.data[offset+2:offset+4])[0]
        string_offset = struct.unpack('>H', self.data[offset+4:offset+6])[0]
        
        names = {}
        name_records = []
        
        for i in range(count):
            record_offset = offset + 6 + (i * 12)
            
            platform_id, encoding_id, language_id, name_id, length, name_offset = \
                struct.unpack('>HHHHHH', self.data[record_offset:record_offset+12])
            
            str_offset = offset + string_offset + name_offset
            str_data = self.data[str_offset:str_offset+length]
            
            try:
                if platform_id == 0:
                    text = str_data.decode('utf-16-be', errors='replace')
                elif platform_id == 1:
                    text = str_data.decode('mac-roman', errors='replace')
                elif platform_id == 3:
                    text = str_data.decode('utf-16-be', errors='replace')
                else:
                    text = str_data.decode('utf-8', errors='replace')
            except:
                text = str_data.decode('utf-8', errors='replace')
            
            name_id_map = {
                0: 'copyright', 1: 'font_family', 2: 'font_subfamily',
                3: 'unique_id', 4: 'full_name', 5: 'version',
                6: 'postscript_name', 7: 'trademark', 8: 'manufacturer',
                9: 'designer', 10: 'description', 11: 'vendor_url',
                12: 'designer_url', 13: 'license', 14: 'license_url',
                16: 'typographic_family', 17: 'typographic_subfamily'
            }
            
            name_key = name_id_map.get(name_id, f'name_{name_id}')
            
            if platform_id == 3 and language_id == 0x0409:
                names[name_key] = text
            elif name_key not in names:
                names[name_key] = text
            
            name_records.append({
                'platform_id': platform_id,
                'encoding_id': encoding_id,
                'language_id': language_id,
                'name_id': name_id,
                'name_key': name_key,
                'text': text
            })
        
        return {
            'format': format_version,
            'count': count,
            'names': names,
            'records': name_records[:10]
        }
    
    def _read_maxp_table(self) -> Dict[str, Any]:
        """Read 'maxp' table (maximum profile)."""
        entry = self.table_directory['maxp']
        offset = entry['offset']
        
        version = struct.unpack('>I', self.data[offset:offset+4])[0]
        num_glyphs = struct.unpack('>H', self.data[offset+4:offset+6])[0]
        
        result = {
            'version': f'{version >> 16}.{version & 0xFFFF}',
            'num_glyphs': num_glyphs
        }
        
        # CFF fonts typically have version 0.5 (only 6 bytes)
        # TrueType-flavored OpenType has version 1.0 (32 bytes)
        if version == 0x00010000 and entry['length'] >= 32:
            remaining_data = self.data[offset+6:offset+32]
            if len(remaining_data) >= 26:
                data = struct.unpack('>13H', remaining_data[:26])
                result.update({
                    'max_points': data[0],
                    'max_contours': data[1],
                    'max_composite_points': data[2],
                    'max_composite_contours': data[3],
                    'max_zones': data[4],
                    'max_twilight_points': data[5],
                    'max_storage': data[6],
                    'max_function_defs': data[7],
                    'max_instruction_defs': data[8],
                    'max_stack_elements': data[9],
                    'max_size_of_instructions': data[10],
                    'max_component_elements': data[11],
                    'max_component_depth': data[12]
                })
        
        return result
    
    def _read_hhea_table(self) -> Dict[str, Any]:
        """Read 'hhea' table (horizontal header)."""
        entry = self.table_directory['hhea']
        offset = entry['offset']
        
        data = self.data[offset:offset+36]
        
        version = struct.unpack('>I', data[0:4])[0]
        ascent, descent, line_gap = struct.unpack('>hhh', data[4:10])
        advance_width_max = struct.unpack('>H', data[10:12])[0]
        min_lsb, min_rsb, x_max_extent = struct.unpack('>hhh', data[12:18])
        caret_slope_rise, caret_slope_run, caret_offset = struct.unpack('>hhh', data[18:24])
        metric_data_format = struct.unpack('>h', data[32:34])[0]
        num_long_hor_metrics = struct.unpack('>H', data[34:36])[0]
        
        return {
            'version': f'{version >> 16}.{version & 0xFFFF}',
            'ascent': ascent,
            'descent': descent,
            'line_gap': line_gap,
            'advance_width_max': advance_width_max,
            'min_left_side_bearing': min_lsb,
            'min_right_side_bearing': min_rsb,
            'x_max_extent': x_max_extent,
            'caret_slope_rise': caret_slope_rise,
            'caret_slope_run': caret_slope_run,
            'caret_offset': caret_offset,
            'metric_data_format': metric_data_format,
            'num_long_hor_metrics': num_long_hor_metrics
        }
    
    def _read_hmtx_table(self) -> Dict[str, Any]:
        """Read 'hmtx' table (horizontal metrics)."""
        entry = self.table_directory['hmtx']
        offset = entry['offset']
        
        num_glyphs = self.tables.get('maxp', {}).get('num_glyphs', 0)
        num_long_metrics = self.tables.get('hhea', {}).get('num_long_hor_metrics', 0)
        
        if num_glyphs == 0 or num_long_metrics == 0:
            return {'error': 'Missing maxp or hhea table'}
        
        metrics = []
        pos = offset
        
        for i in range(min(num_long_metrics, 20)):
            advance_width, lsb = struct.unpack('>Hh', self.data[pos:pos+4])
            metrics.append({
                'glyph_index': i,
                'advance_width': advance_width,
                'left_side_bearing': lsb
            })
            pos += 4
        
        return {
            'num_long_hor_metrics': num_long_metrics,
            'num_glyphs': num_glyphs,
            'metrics': metrics
        }
    
    def _read_os2_table(self) -> Dict[str, Any]:
        """Read 'OS/2' table (OS/2 and Windows metrics)."""
        entry = self.table_directory['OS/2']
        offset = entry['offset']
        length = entry['length']
        
        version = struct.unpack('>H', self.data[offset:offset+2])[0]
        
        if length >= 68:
            x_avg_char_width = struct.unpack('>h', self.data[offset+2:offset+4])[0]
            weight_class = struct.unpack('>H', self.data[offset+4:offset+6])[0]
            width_class = struct.unpack('>H', self.data[offset+6:offset+8])[0]
            fs_type = struct.unpack('>H', self.data[offset+8:offset+10])[0]
            family_class = struct.unpack('>H', self.data[offset+30:offset+32])[0]
            vendor_id = self.data[offset+58:offset+62].decode('ascii', errors='replace')
            fs_selection = struct.unpack('>H', self.data[offset+62:offset+64])[0]
            
            return {
                'version': version,
                'x_avg_char_width': x_avg_char_width,
                'weight_class': weight_class,
                'width_class': width_class,
                'fs_type': fs_type,
                'family_class': family_class,
                'vendor_id': vendor_id.strip(),
                'fs_selection': fs_selection,
                'italic': bool(fs_selection & 0x0001),
                'bold': bool(fs_selection & 0x0020)
            }
        
        return {'version': version, 'incomplete': True}
    
    def _read_post_table(self) -> Dict[str, Any]:
        """Read 'post' table (PostScript information)."""
        entry = self.table_directory['post']
        offset = entry['offset']
        
        if entry['length'] < 32:
            return {'error': 'Table too short'}
        
        version = struct.unpack('>I', self.data[offset:offset+4])[0]
        italic_angle = struct.unpack('>i', self.data[offset+4:offset+8])[0] / 65536.0
        underline_pos = struct.unpack('>h', self.data[offset+8:offset+10])[0]
        underline_thickness = struct.unpack('>h', self.data[offset+10:offset+12])[0]
        is_fixed_pitch = struct.unpack('>I', self.data[offset+12:offset+16])[0]
        
        return {
            'version': f'{version >> 16}.{version & 0xFFFF}',
            'italic_angle': italic_angle,
            'underline_position': underline_pos,
            'underline_thickness': underline_thickness,
            'is_fixed_pitch': bool(is_fixed_pitch)
        }
    
    def _read_cmap_table(self) -> Dict[str, Any]:
        """Read 'cmap' table (character to glyph mapping)."""
        entry = self.table_directory['cmap']
        offset = entry['offset']
        
        version = struct.unpack('>H', self.data[offset:offset+2])[0]
        num_tables = struct.unpack('>H', self.data[offset+2:offset+4])[0]
        
        encoding_records = []
        pos = offset + 4
        
        for i in range(min(num_tables, 10)):
            platform_id = struct.unpack('>H', self.data[pos:pos+2])[0]
            encoding_id = struct.unpack('>H', self.data[pos+2:pos+4])[0]
            subtable_offset = struct.unpack('>I', self.data[pos+4:pos+8])[0]
            
            encoding_records.append({
                'platform_id': platform_id,
                'encoding_id': encoding_id,
                'subtable_offset': subtable_offset
            })
            
            pos += 8
        
        return {
            'version': version,
            'num_tables': num_tables,
            'encoding_records': encoding_records
        }
    
    def _read_cff_table(self) -> Dict[str, Any]:
        """Read 'CFF ' table (Compact Font Format)."""
        entry = self.table_directory['CFF ']
        offset = entry['offset']
        length = entry['length']
        
        # CFF Header (4 bytes minimum)
        if length < 4:
            return {'error': 'CFF table too short'}
        
        major = self.data[offset]
        minor = self.data[offset + 1]
        hdr_size = self.data[offset + 2]
        off_size = self.data[offset + 3]
        
        cff_data = {
            'header': {
                'major': major,
                'minor': minor,
                'version': f'{major}.{minor}',
                'hdr_size': hdr_size,
                'off_size': off_size
            },
            'offset': offset,
            'length': length,
            'note': 'CFF contains PostScript Type 2 charstrings for glyph outlines'
        }
        
        # Try to read Name INDEX (first INDEX after header)
        if length >= hdr_size + 2:
            name_index_offset = offset + hdr_size
            name_count = struct.unpack('>H', self.data[name_index_offset:name_index_offset+2])[0]
            cff_data['name_index'] = {
                'count': name_count,
                'offset': name_index_offset
            }
            
            # If count > 0, read first font name
            if name_count > 0 and length >= name_index_offset + 3:
                name_off_size = self.data[name_index_offset + 2]
                cff_data['name_index']['off_size'] = name_off_size
        
        cff_data['parsed'] = False
        cff_data['reason'] = 'Full CFF parsing requires complex DICT and INDEX structure handling'
        
        return cff_data
    
    def _build_metadata(self):
        """Build metadata dictionary from parsed tables."""
        name_table = self.tables.get('name', {}).get('names', {})
        head_table = self.tables.get('head', {})
        os2_table = self.tables.get('OS/2', {})
        post_table = self.tables.get('post', {})
        maxp_table = self.tables.get('maxp', {})
        hhea_table = self.tables.get('hhea', {})
        
        self.metadata = {
            'font_family': name_table.get('font_family', 'Unknown'),
            'font_subfamily': name_table.get('font_subfamily', 'Regular'),
            'full_name': name_table.get('full_name', 'Unknown'),
            'version': name_table.get('version', 'Unknown'),
            'postscript_name': name_table.get('postscript_name', 'Unknown'),
            'designer': name_table.get('designer', 'Unknown'),
            'manufacturer': name_table.get('manufacturer', 'Unknown'),
            'copyright': name_table.get('copyright', 'Unknown'),
            'units_per_em': head_table.get('units_per_em', 0),
            'bounding_box': head_table.get('bounding_box', {}),
            'ascent': hhea_table.get('ascent', 0),
            'descent': hhea_table.get('descent', 0),
            'line_gap': hhea_table.get('line_gap', 0),
            'num_glyphs': maxp_table.get('num_glyphs', 0),
            'italic_angle': post_table.get('italic_angle', 0),
            'is_fixed_pitch': post_table.get('is_fixed_pitch', False),
            'weight_class': os2_table.get('weight_class', 400),
            'width_class': os2_table.get('width_class', 5),
            'italic': os2_table.get('italic', False),
            'bold': os2_table.get('bold', False),
            'outline_format': 'CFF (PostScript Type 2 charstrings)'
        }
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute font statistics."""
        return {
            'file_size': self.file_size,
            'file_size_kb': round(self.file_size / 1024, 2),
            'num_tables': self.offset_table.get('num_tables', 0),
            'font_type': self.offset_table.get('font_type', 'Unknown'),
            'sfnt_version': self.offset_table.get('sfnt_version_str', ''),
            'tables_present': sorted(list(self.table_directory.keys())),
            'num_glyphs': self.metadata.get('num_glyphs', 0),
            'units_per_em': self.metadata.get('units_per_em', 0),
            'has_cff': 'CFF ' in self.table_directory,
            'has_opentype_features': any(tag in self.table_directory 
                                        for tag in ['GPOS', 'GSUB', 'GDEF']),
            'outline_format': 'CFF (PostScript)' if 'CFF ' in self.table_directory else 'TrueType'
        }


def main():
    """Test OTF extractor with command-line arguments."""
    import sys
    import json
    
    if len(sys.argv) != 2:
        print("Usage: python3 otf_extractor.py <font_file.otf>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    extractor = OTFExtractor()
    result = extractor.extract(file_path)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
