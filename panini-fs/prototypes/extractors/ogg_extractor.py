#!/usr/bin/env python3
"""
Ogg Container Format Extractor

Extracts comprehensive structure from Ogg container files (.ogg, .oga, .ogv, .ogx).

Ogg is a free, open container format for multimedia data (audio, video, text).
It uses a page-based structure where each page contains:
1. Page header (27+ bytes): capture pattern, version, flags, granule position, serial, sequence
2. Segment table: lengths of packet segments
3. Page data: actual packet data

Common codecs:
- Audio: Vorbis (.ogg), Opus (.opus), FLAC (.oga)
- Video: Theora (.ogv)
- Text: Kate, CMML

Structure:
- Multiple logical bitstreams can be multiplexed in one physical Ogg file
- Each logical bitstream has a unique serial number
- Pages are chained sequentially
- Special pages: BOS (Beginning of Stream), EOS (End of Stream)

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.5-alpha
"""

import struct
import os
from typing import Dict, List, Tuple, Any, Optional


class OggExtractor:
    """Extract structure and metadata from Ogg container files."""
    
    def __init__(self):
        """Initialize Ogg extractor."""
        self.file_path = None
        self.file_size = 0
        self.data = None
        
        # Ogg structure
        self.pages = []
        self.streams = {}
        self.codec_info = {}
        
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract complete structure from Ogg file.
        
        Args:
            file_path: Path to Ogg file
            
        Returns:
            Dictionary containing complete Ogg structure
        """
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        
        # Read entire file
        with open(file_path, 'rb') as f:
            self.data = f.read()
        
        # Parse Ogg pages
        self._parse_pages()
        self._analyze_streams()
        
        # Build result
        result = {
            'format': 'Ogg',
            'file_path': file_path,
            'file_size': self.file_size,
            'pages': self.pages[:20],  # First 20 pages
            'total_pages': len(self.pages),
            'streams': self.streams,
            'codec_info': self.codec_info,
            'statistics': self._compute_statistics()
        }
        
        return result
    
    def _parse_pages(self):
        """Parse all Ogg pages in the file."""
        offset = 0
        page_number = 0
        
        while offset < self.file_size - 27:  # Minimum page header size
            # Check for Ogg page capture pattern
            if self.data[offset:offset+4] != b'OggS':
                # Not a valid page, try to find next page
                next_ogg = self.data.find(b'OggS', offset + 1)
                if next_ogg == -1:
                    break
                offset = next_ogg
                continue
            
            # Parse page header (27 bytes + segment table)
            try:
                page_data = self._parse_page_header(offset, page_number)
                if page_data:
                    self.pages.append(page_data)
                    offset = page_data['next_offset']
                    page_number += 1
                else:
                    break
            except Exception as e:
                # Error parsing page, stop
                break
    
    def _parse_page_header(self, offset: int, page_num: int) -> Optional[Dict[str, Any]]:
        """Parse single Ogg page header."""
        if offset + 27 > self.file_size:
            return None
        
        # Ogg page header structure (27 bytes):
        # char[4] capture_pattern: "OggS"
        # uint8 version: 0
        # uint8 header_type: flags (continued, BOS, EOS)
        # uint64 granule_position: codec-specific position
        # uint32 bitstream_serial: unique stream ID
        # uint32 page_sequence: page number in stream
        # uint32 checksum: CRC32
        # uint8 page_segments: number of segments
        
        capture = self.data[offset:offset+4]
        if capture != b'OggS':
            return None
        
        version = self.data[offset + 4]
        header_type = self.data[offset + 5]
        granule_position = struct.unpack('<Q', self.data[offset+6:offset+14])[0]
        serial_number = struct.unpack('<I', self.data[offset+14:offset+18])[0]
        page_sequence = struct.unpack('<I', self.data[offset+18:offset+22])[0]
        checksum = struct.unpack('<I', self.data[offset+22:offset+26])[0]
        page_segments = self.data[offset + 26]
        
        # Parse flags
        continued = bool(header_type & 0x01)
        bos = bool(header_type & 0x02)  # Beginning of stream
        eos = bool(header_type & 0x04)  # End of stream
        
        # Read segment table
        if offset + 27 + page_segments > self.file_size:
            return None
        
        segment_table = []
        for i in range(page_segments):
            segment_table.append(self.data[offset + 27 + i])
        
        # Calculate total page size
        payload_size = sum(segment_table)
        header_size = 27 + page_segments
        total_size = header_size + payload_size
        
        if offset + total_size > self.file_size:
            # Incomplete page
            return None
        
        # Extract payload data (first 256 bytes for analysis)
        payload_offset = offset + header_size
        payload_preview = self.data[payload_offset:payload_offset+min(256, payload_size)]
        
        page_info = {
            'page_number': page_num,
            'offset': offset,
            'version': version,
            'header_type': header_type,
            'flags': {
                'continued': continued,
                'bos': bos,
                'eos': eos
            },
            'granule_position': granule_position,
            'serial_number': serial_number,
            'page_sequence': page_sequence,
            'checksum': checksum,
            'checksum_hex': f'0x{checksum:08X}',
            'page_segments': page_segments,
            'segment_table': segment_table[:20],  # First 20 segments
            'payload_size': payload_size,
            'header_size': header_size,
            'total_size': total_size,
            'next_offset': offset + total_size
        }
        
        # Detect codec on BOS pages
        if bos and payload_size > 8:
            codec = self._detect_codec(payload_preview)
            page_info['codec'] = codec
            
            # Parse codec-specific headers
            if codec == 'Vorbis':
                vorbis_info = self._parse_vorbis_header(payload_preview)
                page_info['vorbis_header'] = vorbis_info
            elif codec == 'Opus':
                opus_info = self._parse_opus_header(payload_preview)
                page_info['opus_header'] = opus_info
            elif codec == 'Theora':
                page_info['theora_header'] = {'detected': True}
        
        return page_info
    
    def _detect_codec(self, payload: bytes) -> str:
        """Detect codec from BOS page payload."""
        if len(payload) < 8:
            return 'Unknown'
        
        # Check for common codec signatures
        if payload[1:7] == b'vorbis':
            return 'Vorbis'
        elif payload[0:8] == b'OpusHead':
            return 'Opus'
        elif payload[1:7] == b'theora':
            return 'Theora'
        elif payload[0:4] == b'fLaC':
            return 'FLAC'
        elif payload[0:8] == b'fishead\x00':
            return 'Skeleton'
        elif payload[0:8] == b'\x80kate\x00\x00\x00':
            return 'Kate'
        else:
            return 'Unknown'
    
    def _parse_vorbis_header(self, payload: bytes) -> Dict[str, Any]:
        """Parse Vorbis identification header."""
        if len(payload) < 30:
            return {'error': 'Header too short'}
        
        # Vorbis identification header:
        # uint8 packet_type: 1
        # char[6] vorbis: "vorbis"
        # uint32 vorbis_version: 0
        # uint8 audio_channels
        # uint32 audio_sample_rate
        # int32 bitrate_maximum
        # int32 bitrate_nominal
        # int32 bitrate_minimum
        # uint8 blocksize: (blocksize_0 << 4) | blocksize_1
        # uint8 framing_flag: 1
        
        packet_type = payload[0]
        vorbis_str = payload[1:7]
        vorbis_version = struct.unpack('<I', payload[7:11])[0]
        channels = payload[11]
        sample_rate = struct.unpack('<I', payload[12:16])[0]
        bitrate_max = struct.unpack('<i', payload[16:20])[0]
        bitrate_nominal = struct.unpack('<i', payload[20:24])[0]
        bitrate_min = struct.unpack('<i', payload[24:28])[0]
        blocksize = payload[28]
        framing_flag = payload[29] if len(payload) > 29 else 0
        
        return {
            'packet_type': packet_type,
            'vorbis_version': vorbis_version,
            'channels': channels,
            'sample_rate': sample_rate,
            'bitrate_maximum': bitrate_max if bitrate_max > 0 else None,
            'bitrate_nominal': bitrate_nominal if bitrate_nominal > 0 else None,
            'bitrate_minimum': bitrate_min if bitrate_min > 0 else None,
            'blocksize_0': 1 << (blocksize & 0x0F),
            'blocksize_1': 1 << ((blocksize & 0xF0) >> 4),
            'framing_flag': framing_flag
        }
    
    def _parse_opus_header(self, payload: bytes) -> Dict[str, Any]:
        """Parse Opus identification header."""
        if len(payload) < 19:
            return {'error': 'Header too short'}
        
        # Opus identification header:
        # char[8] OpusHead
        # uint8 version: 1
        # uint8 channel_count
        # uint16 pre_skip
        # uint32 input_sample_rate: original sample rate
        # int16 output_gain
        # uint8 channel_mapping_family
        
        version = payload[8]
        channels = payload[9]
        pre_skip = struct.unpack('<H', payload[10:12])[0]
        input_sample_rate = struct.unpack('<I', payload[12:16])[0]
        output_gain = struct.unpack('<h', payload[16:18])[0]
        channel_mapping = payload[18]
        
        return {
            'version': version,
            'channels': channels,
            'pre_skip': pre_skip,
            'input_sample_rate': input_sample_rate,
            'output_gain': output_gain,
            'channel_mapping_family': channel_mapping
        }
    
    def _analyze_streams(self):
        """Analyze logical bitstreams in the Ogg file."""
        for page in self.pages:
            serial = page['serial_number']
            
            if serial not in self.streams:
                self.streams[serial] = {
                    'serial_number': serial,
                    'first_page': page['page_number'],
                    'page_count': 0,
                    'has_bos': False,
                    'has_eos': False,
                    'codec': 'Unknown',
                    'total_payload': 0
                }
            
            stream = self.streams[serial]
            stream['page_count'] += 1
            stream['total_payload'] += page['payload_size']
            stream['last_page'] = page['page_number']
            stream['last_granule'] = page['granule_position']
            
            if page['flags']['bos']:
                stream['has_bos'] = True
                if 'codec' in page:
                    stream['codec'] = page['codec']
                    
                    # Store codec-specific info
                    if page['codec'] == 'Vorbis' and 'vorbis_header' in page:
                        self.codec_info['vorbis'] = page['vorbis_header']
                        stream['codec_info'] = page['vorbis_header']
                    elif page['codec'] == 'Opus' and 'opus_header' in page:
                        self.codec_info['opus'] = page['opus_header']
                        stream['codec_info'] = page['opus_header']
            
            if page['flags']['eos']:
                stream['has_eos'] = True
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute Ogg file statistics."""
        stats = {
            'file_size': self.file_size,
            'file_size_kb': round(self.file_size / 1024, 2),
            'total_pages': len(self.pages),
            'num_streams': len(self.streams),
            'streams': {}
        }
        
        # Per-stream statistics
        for serial, stream in self.streams.items():
            stats['streams'][f'stream_{serial}'] = {
                'codec': stream['codec'],
                'page_count': stream['page_count'],
                'total_payload': stream['total_payload'],
                'payload_kb': round(stream['total_payload'] / 1024, 2),
                'has_complete_stream': stream['has_bos'] and stream['has_eos']
            }
            
            # Add codec-specific stats
            if 'codec_info' in stream:
                info = stream['codec_info']
                if stream['codec'] == 'Vorbis':
                    stats['streams'][f'stream_{serial}'].update({
                        'channels': info.get('channels'),
                        'sample_rate': info.get('sample_rate'),
                        'bitrate': info.get('bitrate_nominal')
                    })
                elif stream['codec'] == 'Opus':
                    stats['streams'][f'stream_{serial}'].update({
                        'channels': info.get('channels'),
                        'input_sample_rate': info.get('input_sample_rate')
                    })
        
        # Overall codec summary
        codecs = [s['codec'] for s in self.streams.values()]
        stats['codecs'] = list(set(codecs))
        
        return stats


def main():
    """Test Ogg extractor with command-line arguments."""
    import sys
    import json
    
    if len(sys.argv) != 2:
        print("Usage: python3 ogg_extractor.py <file.ogg>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    extractor = OggExtractor()
    result = extractor.extract(file_path)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
