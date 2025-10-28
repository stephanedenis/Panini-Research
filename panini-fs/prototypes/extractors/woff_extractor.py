#!/usr/bin/env python3
"""
PaniniFS v3.53 - WOFF/WOFF2 Web Font Format Extractor
Web Open Font Format (WOFF 1.0 and WOFF 2.0)

Extracts:
- WOFF version (1.0 or 2.0)
- Font flavor (TrueType, CFF/OpenType)
- File structure (header, table directory)
- Font metadata (total file size, original font size)
- Compression info (compressed vs uncompressed)
- Font tables (glyf, head, hhea, hmtx, etc.)
- Extended metadata (XML metadata block)
"""

import sys
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

# WOFF signatures
WOFF_SIGNATURE = b'wOFF'
WOFF2_SIGNATURE = b'wOF2'

# Font flavors (sfntVersion in WOFF)
FONT_FLAVORS = {
    0x00010000: "TrueType (OpenType with TrueType outlines)",
    0x4F54544F: "CFF (OpenType with CFF outlines)",  # 'OTTO'
    0x74727565: "TrueType (Apple)",  # 'true'
}

# Common OpenType table tags
COMMON_TABLES = {
    b'cmap': "Character to glyph mapping",
    b'head': "Font header",
    b'hhea': "Horizontal header",
    b'hmtx': "Horizontal metrics",
    b'maxp': "Maximum profile",
    b'name': "Naming table",
    b'OS/2': "OS/2 and Windows metrics",
    b'post': "PostScript information",
    b'cvt ': "Control Value Table",
    b'fpgm': "Font program",
    b'glyf': "Glyph data",
    b'loca': "Index to location",
    b'prep': "Control value program",
    b'gasp': "Grid-fitting/Scan-conversion",
    b'CFF ': "Compact Font Format",
    b'VORG': "Vertical Origin",
    b'GPOS': "Glyph positioning",
    b'GSUB': "Glyph substitution",
    b'GDEF': "Glyph definition",
}


def read_uint32(data: bytes, offset: int) -> int:
    """Read 32-bit unsigned integer (big-endian)"""
    return struct.unpack('>I', data[offset:offset+4])[0]


def read_uint16(data: bytes, offset: int) -> int:
    """Read 16-bit unsigned integer (big-endian)"""
    return struct.unpack('>H', data[offset:offset+2])[0]


def read_uint8(data: bytes, offset: int) -> int:
    """Read 8-bit unsigned integer"""
    return data[offset]


def extract_woff_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from WOFF/WOFF2 font file"""
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    if len(data) < 44:
        return {'error': 'File too small to be valid WOFF'}
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': len(data),
    }
    
    # Read signature
    signature = data[0:4]
    
    if signature == WOFF_SIGNATURE:
        metadata.update(parse_woff1(data))
    elif signature == WOFF2_SIGNATURE:
        metadata.update(parse_woff2(data))
    else:
        metadata['error'] = f"Unknown signature: {signature.hex()}"
    
    return metadata


def parse_woff1(data: bytes) -> Dict[str, Any]:
    """Parse WOFF 1.0 format"""
    
    result = {
        'format': 'WOFF 1.0',
        'version': '1.0'
    }
    
    # WOFF Header (44 bytes)
    offset = 4  # Skip signature
    
    flavor = read_uint32(data, offset)
    result['flavor'] = FONT_FLAVORS.get(flavor, f"Unknown (0x{flavor:08X})")
    offset += 4
    
    length = read_uint32(data, offset)
    result['length'] = length
    offset += 4
    
    num_tables = read_uint16(data, offset)
    result['num_tables'] = num_tables
    offset += 2
    
    reserved = read_uint16(data, offset)
    offset += 2
    
    total_sfnt_size = read_uint32(data, offset)
    result['total_sfnt_size'] = total_sfnt_size
    offset += 4
    
    # Compression ratio
    if total_sfnt_size > 0:
        result['compression_ratio'] = f"{(1 - length / total_sfnt_size) * 100:.1f}%"
    
    major_version = read_uint16(data, offset)
    minor_version = read_uint16(data, offset + 2)
    result['font_version'] = f"{major_version}.{minor_version}"
    offset += 4
    
    meta_offset = read_uint32(data, offset)
    meta_length = read_uint32(data, offset + 4)
    meta_orig_length = read_uint32(data, offset + 8)
    offset += 12
    
    if meta_length > 0:
        result['metadata_block'] = {
            'offset': meta_offset,
            'compressed': meta_length,
            'original': meta_orig_length
        }
    
    priv_offset = read_uint32(data, offset)
    priv_length = read_uint32(data, offset + 4)
    offset += 8
    
    if priv_length > 0:
        result['private_data'] = {
            'offset': priv_offset,
            'length': priv_length
        }
    
    # Table Directory
    tables = []
    table_tags = Counter()
    total_compressed = 0
    total_original = 0
    
    for i in range(num_tables):
        if offset + 20 > len(data):
            break
        
        tag = data[offset:offset+4]
        offset += 4
        
        table_offset = read_uint32(data, offset)
        comp_length = read_uint32(data, offset + 4)
        orig_length = read_uint32(data, offset + 8)
        orig_checksum = read_uint32(data, offset + 12)
        offset += 16
        
        tag_str = tag.decode('ascii', errors='replace')
        table_info = {
            'tag': tag_str,
            'description': COMMON_TABLES.get(tag, 'Unknown'),
            'offset': table_offset,
            'compressed_length': comp_length,
            'original_length': orig_length,
            'checksum': f"0x{orig_checksum:08X}"
        }
        
        if comp_length < orig_length:
            table_info['compression_ratio'] = f"{(1 - comp_length / orig_length) * 100:.1f}%"
        
        tables.append(table_info)
        table_tags[tag_str] += 1
        total_compressed += comp_length
        total_original += orig_length
    
    result['tables'] = tables
    result['table_tags'] = dict(table_tags)
    result['total_compressed_tables'] = total_compressed
    result['total_original_tables'] = total_original
    
    # Try to extract metadata XML
    if meta_length > 0 and meta_offset + meta_length <= len(data):
        try:
            compressed_meta = data[meta_offset:meta_offset + meta_length]
            decompressed_meta = zlib.decompress(compressed_meta)
            
            # Try to parse as XML (just extract basic info)
            meta_str = decompressed_meta.decode('utf-8', errors='ignore')
            if '<metadata' in meta_str:
                result['metadata_xml'] = {
                    'size': len(meta_str),
                    'preview': meta_str[:200] + '...' if len(meta_str) > 200 else meta_str
                }
        except Exception as e:
            result['metadata_error'] = str(e)
    
    return result


def parse_woff2(data: bytes) -> Dict[str, Any]:
    """Parse WOFF 2.0 format"""
    
    result = {
        'format': 'WOFF 2.0',
        'version': '2.0'
    }
    
    # WOFF2 Header (48 bytes minimum)
    offset = 4  # Skip signature
    
    flavor = read_uint32(data, offset)
    result['flavor'] = FONT_FLAVORS.get(flavor, f"Unknown (0x{flavor:08X})")
    offset += 4
    
    length = read_uint32(data, offset)
    result['length'] = length
    offset += 4
    
    num_tables = read_uint16(data, offset)
    result['num_tables'] = num_tables
    offset += 2
    
    reserved = read_uint16(data, offset)
    offset += 2
    
    total_sfnt_size = read_uint32(data, offset)
    result['total_sfnt_size'] = total_sfnt_size
    offset += 4
    
    # Compression ratio
    if total_sfnt_size > 0:
        result['compression_ratio'] = f"{(1 - length / total_sfnt_size) * 100:.1f}%"
    
    total_compressed_size = read_uint32(data, offset)
    result['total_compressed_size'] = total_compressed_size
    offset += 4
    
    major_version = read_uint16(data, offset)
    minor_version = read_uint16(data, offset + 2)
    result['font_version'] = f"{major_version}.{minor_version}"
    offset += 4
    
    meta_offset = read_uint32(data, offset)
    meta_length = read_uint32(data, offset + 4)
    meta_orig_length = read_uint32(data, offset + 8)
    offset += 12
    
    if meta_length > 0:
        result['metadata_block'] = {
            'offset': meta_offset,
            'compressed': meta_length,
            'original': meta_orig_length
        }
    
    priv_offset = read_uint32(data, offset)
    priv_length = read_uint32(data, offset + 4)
    offset += 8
    
    if priv_length > 0:
        result['private_data'] = {
            'offset': priv_offset,
            'length': priv_length
        }
    
    # WOFF2 uses Brotli compression and has a different table directory format
    # For simplicity, we'll just note that tables exist
    result['note'] = "WOFF2 uses Brotli compression with transformed glyf/loca tables"
    
    # Try to count known table tags in compressed data
    # (This is approximate since WOFF2 encodes table tags differently)
    table_tags = Counter()
    for tag, desc in COMMON_TABLES.items():
        if tag in data:
            table_tags[tag.decode('ascii', errors='replace')] += data.count(tag)
    
    if table_tags:
        result['detected_table_tags'] = dict(table_tags)
    
    return result


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes")
    print(f"Format: {metadata.get('format', 'Unknown')}")
    print(f"Font Flavor: {metadata.get('flavor', 'Unknown')}")
    
    if 'font_version' in metadata:
        print(f"Font Version: {metadata['font_version']}")
    
    if 'num_tables' in metadata:
        print(f"Number of Tables: {metadata['num_tables']}")
    
    if 'total_sfnt_size' in metadata:
        print(f"Original Font Size: {metadata['total_sfnt_size']:,} bytes")
        print(f"WOFF File Size: {metadata['length']:,} bytes")
        
        if 'compression_ratio' in metadata:
            print(f"Compression Ratio: {metadata['compression_ratio']}")
    
    if 'total_compressed_tables' in metadata:
        print(f"Total Compressed Table Data: {metadata['total_compressed_tables']:,} bytes")
        print(f"Total Original Table Data: {metadata['total_original_tables']:,} bytes")
    
    if 'metadata_block' in metadata:
        mb = metadata['metadata_block']
        print(f"\nMetadata Block:")
        print(f"  Offset: {mb['offset']}")
        print(f"  Compressed: {mb['compressed']:,} bytes")
        print(f"  Original: {mb['original']:,} bytes")
    
    if 'metadata_xml' in metadata:
        print(f"\nExtended Metadata (XML):")
        print(f"  Size: {metadata['metadata_xml']['size']:,} bytes")
        print(f"  Preview: {metadata['metadata_xml']['preview']}")
    
    if 'private_data' in metadata:
        pd = metadata['private_data']
        print(f"\nPrivate Data Block:")
        print(f"  Offset: {pd['offset']}")
        print(f"  Length: {pd['length']:,} bytes")
    
    if 'tables' in metadata:
        print(f"\nFont Tables ({len(metadata['tables'])} tables):")
        
        # Group by type
        glyph_tables = []
        layout_tables = []
        metric_tables = []
        other_tables = []
        
        for table in metadata['tables']:
            tag = table['tag']
            if tag in ('glyf', 'loca', 'CFF ', 'VORG'):
                glyph_tables.append(table)
            elif tag in ('GPOS', 'GSUB', 'GDEF'):
                layout_tables.append(table)
            elif tag in ('head', 'hhea', 'hmtx', 'maxp', 'name', 'OS/2', 'post'):
                metric_tables.append(table)
            else:
                other_tables.append(table)
        
        def print_table_group(name: str, tables: List[Dict]):
            if tables:
                print(f"\n  {name}:")
                for t in tables:
                    comp_str = ""
                    if 'compression_ratio' in t:
                        comp_str = f" (saved {t['compression_ratio']})"
                    print(f"    {t['tag']}: {t['description']}")
                    print(f"      Original: {t['original_length']:,} bytes, "
                          f"Compressed: {t['compressed_length']:,} bytes{comp_str}")
        
        print_table_group("Glyph Tables", glyph_tables)
        print_table_group("Layout Tables", layout_tables)
        print_table_group("Metric Tables", metric_tables)
        print_table_group("Other Tables", other_tables)
    
    if 'detected_table_tags' in metadata:
        print(f"\nDetected Table Tags: {', '.join(metadata['detected_table_tags'].keys())}")
    
    if 'note' in metadata:
        print(f"\nNote: {metadata['note']}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python woff_extractor.py <file.woff|file.woff2>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_woff_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
