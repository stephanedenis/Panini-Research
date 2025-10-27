#!/usr/bin/env python3
"""
Zstandard (.zst) Compression Format Extractor - PaniniFS v3.44

This extractor analyzes Zstandard compressed files.
Zstandard (zstd) is a fast lossless compression algorithm developed by Facebook
(Meta), offering high compression ratios with fast compression/decompression speeds.

Format Structure:
- Magic number: 0x28 0xB5 0x2F 0xFD (4 bytes)
- Frame Header: descriptor, window size, frame content size
- Compressed data blocks
- Optional checksum (XXH64)

Frame Header:
- Frame_Header_Descriptor (1 byte):
  - Frame_Content_Size_Flag (2 bits): size field presence
  - Single_Segment_Flag (1 bit)
  - Unused_bit (1 bit)
  - Reserved_bit (1 bit)
  - Content_Checksum_flag (1 bit)
  - Dictionary_ID_flag (2 bits)
- Window_Descriptor (0-1 byte)
- Dictionary_ID (0-4 bytes)
- Frame_Content_Size (0, 1, 2, 4, or 8 bytes)

Compression Levels:
- Level 1-3: Fast compression, lower ratio
- Level 4-9: Balanced (default: 3)
- Level 10-19: High compression, slower
- Level 20-22: Ultra compression (--ultra flag)
- Level -131072 to -1: Negative levels (fast, very low compression)

Use Cases:
- Linux kernel modules (.ko.zst)
- Package compression (RPM, DEB)
- Database backups
- Log file compression
- Network transfer compression
- Real-time data compression

Features:
- Fast compression (comparable to gzip)
- High compression ratio (comparable to xz)
- Dictionary support
- Streaming compression
- Frame concatenation
- Seekable format (skippable frames)

This extractor provides:
- Magic number verification
- Frame header parsing
- Compression properties detection
- Original size extraction (if available)
- Dictionary detection
- Checksum detection
- Compression ratio estimation

Author: PaniniFS Research Team
Version: 3.44
Target: Zstandard files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import struct

class ZstandardExtractor:
    """Extract metadata from Zstandard (.zst) compressed files."""
    
    # Zstandard magic number
    MAGIC = b'\x28\xb5\x2f\xfd'
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the Zstandard file."""
        try:
            with open(self.file_path, 'rb') as f:
                data = f.read(128)  # Read header
            
            metadata = {
                "format": "Zstandard",
                "file_path": str(self.file_path),
                "compressed_size": self.file_path.stat().st_size,
            }
            
            # Verify magic
            if not self._verify_magic(data):
                metadata["error"] = "Invalid Zstandard magic number"
                return metadata
            
            # Parse frame header
            offset = 4  # After magic
            frame_info = self._parse_frame_header(data, offset)
            
            if frame_info:
                metadata.update(frame_info)
                
                # Calculate compression ratio if original size known
                if "original_size" in frame_info and frame_info["original_size"]:
                    ratio = metadata["compressed_size"] / frame_info["original_size"]
                    metadata["compression_ratio"] = round(ratio, 3)
                    metadata["space_saving_percent"] = round((1 - ratio) * 100, 1)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Zstandard",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _verify_magic(self, data: bytes) -> bool:
        """Verify Zstandard magic number."""
        return data[:4] == self.MAGIC
    
    def _parse_frame_header(self, data: bytes, offset: int) -> Optional[Dict[str, Any]]:
        """Parse Zstandard frame header."""
        if offset >= len(data):
            return None
        
        result = {}
        
        # Frame_Header_Descriptor (1 byte)
        descriptor = data[offset]
        offset += 1
        
        # Parse descriptor bits
        frame_content_size_flag = (descriptor >> 6) & 0x3
        single_segment_flag = (descriptor >> 5) & 0x1
        content_checksum_flag = (descriptor >> 2) & 0x1
        dictionary_id_flag = descriptor & 0x3
        
        result["has_checksum"] = content_checksum_flag == 1
        result["single_segment"] = single_segment_flag == 1
        
        # Window_Descriptor (0-1 byte)
        window_size = None
        if single_segment_flag == 0:
            if offset < len(data):
                window_descriptor = data[offset]
                offset += 1
                
                # Calculate window size
                exponent = window_descriptor >> 3
                mantissa = window_descriptor & 0x7
                window_log = 10 + exponent
                window_base = 1 << window_log
                window_add = (window_base >> 3) * mantissa
                window_size = window_base + window_add
                
                result["window_size"] = window_size
        
        # Dictionary_ID (0-4 bytes)
        dict_id_size = [0, 1, 2, 4][dictionary_id_flag]
        if dict_id_size > 0 and offset + dict_id_size <= len(data):
            if dict_id_size == 1:
                dict_id = data[offset]
            elif dict_id_size == 2:
                dict_id = struct.unpack('<H', data[offset:offset+2])[0]
            else:  # 4 bytes
                dict_id = struct.unpack('<I', data[offset:offset+4])[0]
            result["dictionary_id"] = dict_id
            offset += dict_id_size
        
        # Frame_Content_Size (0, 1, 2, 4, or 8 bytes)
        if single_segment_flag == 1:
            fcs_size = [1, 2, 4, 8][frame_content_size_flag]
        else:
            fcs_size = [0, 2, 4, 8][frame_content_size_flag]
        
        if fcs_size > 0 and offset + fcs_size <= len(data):
            if fcs_size == 1:
                original_size = data[offset]
            elif fcs_size == 2:
                original_size = struct.unpack('<H', data[offset:offset+2])[0]
            elif fcs_size == 4:
                original_size = struct.unpack('<I', data[offset:offset+4])[0]
            else:  # 8 bytes
                original_size = struct.unpack('<Q', data[offset:offset+8])[0]
            
            result["original_size"] = original_size
            result["original_size_known"] = True
        else:
            result["original_size_known"] = False
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: zstandard_extractor.py <zst_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = ZstandardExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
