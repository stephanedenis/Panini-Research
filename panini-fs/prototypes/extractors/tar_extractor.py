#!/usr/bin/env python3
"""
TAR.GZ Archive Format Extractor for PaniniFS v3.6
Extracts metadata and structure from TAR archives with GZIP compression.

Supports:
- GZIP wrapper (RFC 1952)
- POSIX ustar TAR format (512-byte blocks)
- Extended PAX headers
- File metadata: name, size, mode, owner, timestamps
- Directory structure analysis
"""

import struct
import sys
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import zlib
import time


@dataclass
class TarEntry:
    """Represents a TAR archive entry."""
    name: str
    mode: str
    uid: int
    gid: int
    size: int
    mtime: int
    checksum: int
    typeflag: str
    linkname: str
    magic: str
    version: str
    uname: str
    gname: str
    devmajor: int
    devminor: int
    prefix: str


class TarGzExtractor:
    """Extract metadata from TAR.GZ archives."""
    
    # TAR type flags
    TYPE_FLAGS = {
        '0': 'regular_file',
        '\x00': 'regular_file_null',
        '1': 'hard_link',
        '2': 'symbolic_link',
        '3': 'character_device',
        '4': 'block_device',
        '5': 'directory',
        '6': 'fifo',
        '7': 'contiguous_file',
        'g': 'global_extended_header',
        'x': 'extended_header',
        'L': 'long_name',
        'K': 'long_linkname'
    }
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        self.tar_data = None
        self.entries: List[TarEntry] = []
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from TAR.GZ file."""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        # Parse GZIP wrapper
        gzip_info = self._parse_gzip_header()
        
        # Decompress TAR data
        self.tar_data = self._decompress_gzip()
        
        # Parse TAR structure
        self._parse_tar_entries()
        
        # Analyze structure
        structure = self._analyze_structure()
        
        return {
            'format': 'TAR.GZ',
            'gzip': gzip_info,
            'tar': {
                'total_entries': len(self.entries),
                'entries': structure['entries'],
                'statistics': structure['stats']
            }
        }
    
    def _parse_gzip_header(self) -> Dict[str, Any]:
        """Parse GZIP header (RFC 1952)."""
        if len(self.data) < 10:
            raise ValueError("File too small for GZIP header")
        
        # Check magic number
        magic = struct.unpack('<H', self.data[0:2])[0]
        if magic != 0x8B1F:  # 0x1F8B in little-endian
            raise ValueError(f"Invalid GZIP magic: 0x{magic:04X}")
        
        # Parse header fields
        compression_method = self.data[2]
        flags = self.data[3]
        mtime = struct.unpack('<I', self.data[4:8])[0]
        extra_flags = self.data[8]
        os_type = self.data[9]
        
        # OS type names
        os_names = {
            0: 'FAT',
            1: 'Amiga',
            2: 'VMS',
            3: 'Unix',
            4: 'VM/CMS',
            5: 'Atari TOS',
            6: 'HPFS',
            7: 'Macintosh',
            8: 'Z-System',
            9: 'CP/M',
            10: 'TOPS-20',
            11: 'NTFS',
            12: 'QDOS',
            13: 'Acorn RISCOS',
            255: 'Unknown'
        }
        
        # Parse optional fields
        offset = 10
        extra_len = 0
        original_name = None
        comment = None
        
        # FEXTRA flag
        if flags & 0x04:
            extra_len = struct.unpack('<H', self.data[offset:offset+2])[0]
            offset += 2 + extra_len
        
        # FNAME flag
        if flags & 0x08:
            end = self.data.index(b'\x00', offset)
            original_name = self.data[offset:end].decode('latin-1', errors='replace')
            offset = end + 1
        
        # FCOMMENT flag
        if flags & 0x10:
            end = self.data.index(b'\x00', offset)
            comment = self.data[offset:end].decode('latin-1', errors='replace')
            offset = end + 1
        
        # FHCRC flag
        if flags & 0x02:
            offset += 2
        
        return {
            'magic': '0x1F8B',
            'compression_method': compression_method,
            'flags': {
                'text': bool(flags & 0x01),
                'crc16': bool(flags & 0x02),
                'extra': bool(flags & 0x04),
                'name': bool(flags & 0x08),
                'comment': bool(flags & 0x10)
            },
            'mtime': mtime,
            'mtime_str': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime)) if mtime else None,
            'extra_flags': extra_flags,
            'os': os_names.get(os_type, f'Unknown ({os_type})'),
            'original_name': original_name,
            'comment': comment,
            'header_size': offset
        }
    
    def _decompress_gzip(self) -> bytes:
        """Decompress GZIP data to get TAR content."""
        # Use zlib with wbits=-15 for raw DEFLATE (no header)
        # Or use wbits=16+15 to handle GZIP wrapper
        try:
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            return decompressor.decompress(self.data)
        except zlib.error as e:
            raise ValueError(f"GZIP decompression failed: {e}")
    
    def _parse_tar_entries(self):
        """Parse TAR archive entries."""
        offset = 0
        tar_size = len(self.tar_data)
        
        while offset < tar_size:
            # Check for end-of-archive (two consecutive zero blocks)
            if offset + 1024 <= tar_size:
                block = self.tar_data[offset:offset+1024]
                if block == b'\x00' * 1024:
                    break
            
            # Parse header block
            if offset + 512 > tar_size:
                break
            
            header = self.tar_data[offset:offset+512]
            
            # Check if block is empty (end of archive)
            if header == b'\x00' * 512:
                break
            
            try:
                entry = self._parse_tar_header(header)
                if entry:
                    self.entries.append(entry)
                    
                    # Skip file data blocks
                    if entry.size > 0:
                        # Round up to nearest 512-byte boundary
                        data_blocks = (entry.size + 511) // 512
                        offset += 512 + (data_blocks * 512)
                    else:
                        offset += 512
                else:
                    offset += 512
            except Exception:
                # Skip invalid blocks
                offset += 512
    
    def _parse_tar_header(self, header: bytes) -> Optional[TarEntry]:
        """Parse a single TAR header block."""
        if len(header) < 512:
            return None
        
        # Extract fields (POSIX ustar format)
        try:
            name = self._extract_string(header[0:100])
            mode = self._extract_string(header[100:108])
            uid = self._extract_octal(header[108:116])
            gid = self._extract_octal(header[116:124])
            size = self._extract_octal(header[124:136])
            mtime = self._extract_octal(header[136:148])
            checksum = self._extract_octal(header[148:156])
            typeflag = chr(header[156]) if header[156] else '\x00'
            linkname = self._extract_string(header[157:257])
            magic = self._extract_string(header[257:263])
            version = self._extract_string(header[263:265])
            uname = self._extract_string(header[265:297])
            gname = self._extract_string(header[297:329])
            devmajor = self._extract_octal(header[329:337])
            devminor = self._extract_octal(header[337:345])
            prefix = self._extract_string(header[345:500])
            
            # Validate checksum
            if not self._validate_checksum(header, checksum):
                return None
            
            # Combine prefix and name if needed
            if prefix:
                name = f"{prefix}/{name}"
            
            return TarEntry(
                name=name,
                mode=mode,
                uid=uid,
                gid=gid,
                size=size,
                mtime=mtime,
                checksum=checksum,
                typeflag=typeflag,
                linkname=linkname,
                magic=magic,
                version=version,
                uname=uname,
                gname=gname,
                devmajor=devmajor,
                devminor=devminor,
                prefix=prefix
            )
        except Exception:
            return None
    
    def _extract_string(self, data: bytes) -> str:
        """Extract null-terminated string."""
        end = data.find(b'\x00')
        if end == -1:
            end = len(data)
        return data[:end].decode('utf-8', errors='replace').strip()
    
    def _extract_octal(self, data: bytes) -> int:
        """Extract octal number from TAR header."""
        s = self._extract_string(data)
        if not s or s.isspace():
            return 0
        try:
            # Handle octal with optional trailing space/null
            s = s.strip()
            if not s:
                return 0
            return int(s, 8)
        except ValueError:
            return 0
    
    def _validate_checksum(self, header: bytes, expected: int) -> bool:
        """Validate TAR header checksum."""
        # Calculate checksum with checksum field as spaces
        temp = bytearray(header)
        temp[148:156] = b'        '
        calculated = sum(temp)
        return calculated == expected
    
    def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze TAR structure and generate statistics."""
        entries_info = []
        
        # Statistics counters
        total_size = 0
        file_count = 0
        dir_count = 0
        link_count = 0
        type_counts = {}
        
        for entry in self.entries:
            # Type classification
            type_name = self.TYPE_FLAGS.get(entry.typeflag, f'unknown_{ord(entry.typeflag)}')
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Count by category
            if entry.typeflag in ('0', '\x00'):
                file_count += 1
                total_size += entry.size
            elif entry.typeflag == '5':
                dir_count += 1
            elif entry.typeflag in ('1', '2'):
                link_count += 1
            
            # Entry info
            entry_info = {
                'name': entry.name,
                'type': type_name,
                'size': entry.size,
                'mode': entry.mode,
                'mtime': entry.mtime,
                'mtime_str': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry.mtime)) if entry.mtime else None,
                'owner': f"{entry.uname}:{entry.gname}" if entry.uname or entry.gname else f"{entry.uid}:{entry.gid}"
            }
            
            # Add link target for links
            if entry.linkname:
                entry_info['link_target'] = entry.linkname
            
            entries_info.append(entry_info)
        
        return {
            'entries': entries_info,
            'stats': {
                'total_entries': len(self.entries),
                'files': file_count,
                'directories': dir_count,
                'links': link_count,
                'total_size': total_size,
                'total_size_human': self._human_size(total_size),
                'types': type_counts
            }
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
        print(f"Usage: {sys.argv[0]} <file.tar.gz>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = TarGzExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
