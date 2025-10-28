#!/usr/bin/env python3
"""
BZIP2 Compression Format Extractor for PaniniFS v3.10
Extracts metadata from BZIP2 compressed files.

Supports:
- BZIP2 file format (.bz2)
- Header parsing (magic, version, block size)
- Multiple block detection
- Compression statistics
- Block size analysis
"""

import struct
import sys
import json
from typing import Dict, Any, List, Optional


class BZIP2Extractor:
    """Extract metadata from BZIP2 compressed files."""
    
    # BZIP2 constants
    BZ_MAGIC = b'BZ'
    BZ_VERSION = ord('h')
    BZ_BLOCK_START = b'\x31\x41\x59\x26\x53\x59'  # π digits: 314159265359
    BZ_STREAM_END = b'\x17\x72\x45\x38\x50\x90'
    
    # Block sizes
    BLOCK_SIZES = {
        ord('1'): 100000,
        ord('2'): 200000,
        ord('3'): 300000,
        ord('4'): 400000,
        ord('5'): 500000,
        ord('6'): 600000,
        ord('7'): 700000,
        ord('8'): 800000,
        ord('9'): 900000
    }
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from BZIP2 file."""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        # Parse header
        header = self._parse_header()
        
        # Find blocks
        blocks = self._find_blocks()
        
        # Analyze structure
        stats = self._compute_statistics(header, blocks)
        
        return {
            'format': 'BZIP2',
            'header': header,
            'blocks': blocks,
            'statistics': stats
        }
    
    def _parse_header(self) -> Dict[str, Any]:
        """Parse BZIP2 header."""
        if len(self.data) < 4:
            raise ValueError("File too small for BZIP2 header")
        
        # Check magic
        magic = self.data[0:2]
        if magic != self.BZ_MAGIC:
            raise ValueError(f"Invalid BZIP2 magic: {magic}")
        
        # Check version
        version = self.data[2]
        if version != self.BZ_VERSION:
            raise ValueError(f"Invalid BZIP2 version: {chr(version)}")
        
        # Parse block size
        block_size_char = self.data[3]
        if block_size_char not in self.BLOCK_SIZES:
            raise ValueError(f"Invalid block size: {chr(block_size_char)}")
        
        block_size = self.BLOCK_SIZES[block_size_char]
        
        return {
            'magic': magic.decode('ascii'),
            'version': chr(version),
            'block_size_code': chr(block_size_char),
            'block_size_bytes': block_size,
            'block_size_human': self._human_size(block_size)
        }
    
    def _find_blocks(self) -> List[Dict[str, Any]]:
        """Find all BZIP2 blocks in the file."""
        blocks = []
        offset = 4  # Skip header
        block_num = 0
        
        while offset < len(self.data) - 10:
            # Look for block start marker (π digits)
            if self.data[offset:offset+6] == self.BZ_BLOCK_START:
                block_info = {
                    'block_number': block_num,
                    'offset': offset,
                    'type': 'data_block'
                }
                blocks.append(block_info)
                block_num += 1
                offset += 6
            elif self.data[offset:offset+6] == self.BZ_STREAM_END:
                block_info = {
                    'block_number': block_num,
                    'offset': offset,
                    'type': 'stream_end'
                }
                blocks.append(block_info)
                block_num += 1
                offset += 6
            else:
                offset += 1
        
        return blocks
    
    def _compute_statistics(self, header: Dict[str, Any], 
                           blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute BZIP2 statistics."""
        data_blocks = [b for b in blocks if b['type'] == 'data_block']
        stream_ends = [b for b in blocks if b['type'] == 'stream_end']
        
        return {
            'file_size': len(self.data),
            'file_size_human': self._human_size(len(self.data)),
            'total_blocks': len(blocks),
            'data_blocks': len(data_blocks),
            'stream_end_markers': len(stream_ends),
            'compression_overhead': len(self.data) > 0 and 
                                   (len(self.data) / header['block_size_bytes'] * 100)
        }
    
    def _human_size(self, size: int) -> str:
        """Convert size to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


def main():
    """Main extraction function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.bz2>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = BZIP2Extractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
