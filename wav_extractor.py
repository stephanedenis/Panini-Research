#!/usr/bin/env python3
"""
PaniniFS v3.27: WAV (Waveform Audio File) Format Extractor
===========================================================

RIFF WAVE audio format - standard for uncompressed audio.

Structure (RIFF container):
- RIFF header:
  - ChunkID: "RIFF" (4 bytes)
  - ChunkSize: File size - 8 (4 bytes, little-endian)
  - Format: "WAVE" (4 bytes)
  
- fmt subchunk (format):
  - SubchunkID: "fmt " (4 bytes)
  - SubchunkSize: 16 for PCM (4 bytes)
  - AudioFormat: 1 = PCM, 3 = IEEE float, etc. (2 bytes)
  - NumChannels: 1 = mono, 2 = stereo (2 bytes)
  - SampleRate: 8000, 11025, 22050, 44100, 48000 Hz (4 bytes)
  - ByteRate: SampleRate * NumChannels * BitsPerSample/8 (4 bytes)
  - BlockAlign: NumChannels * BitsPerSample/8 (2 bytes)
  - BitsPerSample: 8, 16, 24, 32 bits (2 bytes)
  
- data subchunk:
  - SubchunkID: "data" (4 bytes)
  - SubchunkSize: NumSamples * NumChannels * BitsPerSample/8 (4 bytes)
  - Data: actual audio samples

Optional chunks:
- LIST: Info metadata (INAM, IART, ICMT, etc.)
- fact: Sample length for compressed audio
- cue: Cue points
- smpl: Sampler information

Metadata extracted:
- Audio format (PCM, IEEE float, etc.)
- Channels (mono, stereo, etc.)
- Sample rate (Hz)
- Bit depth
- Duration (seconds)
- Byte rate
- Total samples
- Metadata (title, artist, comments if present)

Format: Binary, RIFF container
Encoding: Little-endian
Common use: Sound effects, music, voice recordings

Author: PaniniFS Research Team
Version: 3.27
Date: 2025-01-14
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, Optional


class WAVExtractor:
    """Extract metadata from WAV audio files."""
    
    # Audio format codes
    AUDIO_FORMATS = {
        0x0001: "PCM",
        0x0003: "IEEE float",
        0x0006: "8-bit ITU-T G.711 A-law",
        0x0007: "8-bit ITU-T G.711 µ-law",
        0x0011: "IMA ADPCM",
        0x0016: "ITU-T G.723 ADPCM (Yamaha)",
        0x0031: "GSM 6.10",
        0x0040: "ITU-T G.721 ADPCM",
        0x0050: "MPEG",
        0xFFFE: "Extensible"
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "WAV (Waveform Audio)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "audio_format": None,
            "channels": None,
            "sample_rate": None,
            "bits_per_sample": None,
            "byte_rate": None,
            "duration_seconds": None,
            "total_samples": None,
            "metadata": {},
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Parse RIFF header
            self._parse_riff_header()
            
            # Parse chunks
            self._parse_chunks()
            
            # Calculate derived values
            self._calculate_duration()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_riff_header(self):
        """Parse RIFF header."""
        if len(self.raw_data) < 12:
            raise ValueError("File too small to be valid WAV")
        
        # Check RIFF signature
        riff_id = self.raw_data[0:4]
        if riff_id != b'RIFF':
            raise ValueError(f"Invalid RIFF signature: {riff_id}")
        
        # Read chunk size
        chunk_size = struct.unpack('<I', self.raw_data[4:8])[0]
        
        # Check WAVE format
        wave_id = self.raw_data[8:12]
        if wave_id != b'WAVE':
            raise ValueError(f"Invalid WAVE format: {wave_id}")
    
    def _parse_chunks(self):
        """Parse WAV subchunks."""
        offset = 12  # After RIFF header
        
        while offset + 8 <= len(self.raw_data):
            # Read subchunk ID and size
            chunk_id = self.raw_data[offset:offset+4]
            chunk_size = struct.unpack('<I', self.raw_data[offset+4:offset+8])[0]
            
            offset += 8
            
            # Check bounds
            if offset + chunk_size > len(self.raw_data):
                break
            
            # Parse by chunk type
            if chunk_id == b'fmt ':
                self._parse_fmt_chunk(offset, chunk_size)
            elif chunk_id == b'data':
                self._parse_data_chunk(offset, chunk_size)
            elif chunk_id == b'LIST':
                self._parse_list_chunk(offset, chunk_size)
            
            # Move to next chunk (align to even boundary)
            offset += chunk_size
            if chunk_size % 2 == 1:
                offset += 1
    
    def _parse_fmt_chunk(self, offset: int, size: int):
        """Parse format chunk."""
        if size < 16:
            return
        
        # Audio format
        audio_format_code = struct.unpack('<H', self.raw_data[offset:offset+2])[0]
        self.data["audio_format"] = self.AUDIO_FORMATS.get(
            audio_format_code, 
            f"Unknown (0x{audio_format_code:04X})"
        )
        
        # Number of channels
        num_channels = struct.unpack('<H', self.raw_data[offset+2:offset+4])[0]
        self.data["channels"] = num_channels
        
        # Sample rate
        sample_rate = struct.unpack('<I', self.raw_data[offset+4:offset+8])[0]
        self.data["sample_rate"] = sample_rate
        
        # Byte rate
        byte_rate = struct.unpack('<I', self.raw_data[offset+8:offset+12])[0]
        self.data["byte_rate"] = byte_rate
        
        # Block align
        block_align = struct.unpack('<H', self.raw_data[offset+12:offset+14])[0]
        
        # Bits per sample
        bits_per_sample = struct.unpack('<H', self.raw_data[offset+14:offset+16])[0]
        self.data["bits_per_sample"] = bits_per_sample
    
    def _parse_data_chunk(self, offset: int, size: int):
        """Parse data chunk."""
        self.data["data_size"] = size
        
        # Calculate total samples
        if self.data["channels"] and self.data["bits_per_sample"]:
            bytes_per_sample = self.data["bits_per_sample"] // 8
            total_samples = size // (self.data["channels"] * bytes_per_sample)
            self.data["total_samples"] = total_samples
    
    def _parse_list_chunk(self, offset: int, size: int):
        """Parse LIST chunk for metadata."""
        if size < 4:
            return
        
        # Read list type
        list_type = self.raw_data[offset:offset+4]
        
        if list_type == b'INFO':
            # Parse INFO metadata
            info_offset = offset + 4
            end = offset + size
            
            while info_offset + 8 < end:
                info_id = self.raw_data[info_offset:info_offset+4]
                info_size = struct.unpack('<I', self.raw_data[info_offset+4:info_offset+8])[0]
                
                info_offset += 8
                
                if info_offset + info_size > end:
                    break
                
                # Extract string value
                try:
                    value = self.raw_data[info_offset:info_offset+info_size]
                    value = value.decode('ascii', errors='ignore').rstrip('\x00')
                    
                    # Common INFO tags
                    info_id_str = info_id.decode('ascii', errors='ignore')
                    if info_id == b'INAM':
                        self.data["metadata"]["title"] = value
                    elif info_id == b'IART':
                        self.data["metadata"]["artist"] = value
                    elif info_id == b'ICMT':
                        self.data["metadata"]["comment"] = value
                    elif info_id == b'ICOP':
                        self.data["metadata"]["copyright"] = value
                    elif info_id == b'ICRD':
                        self.data["metadata"]["creation_date"] = value
                    elif info_id == b'IGNR':
                        self.data["metadata"]["genre"] = value
                    else:
                        self.data["metadata"][info_id_str] = value
                except:
                    pass
                
                info_offset += info_size
                if info_size % 2 == 1:
                    info_offset += 1
    
    def _calculate_duration(self):
        """Calculate audio duration."""
        if self.data["sample_rate"] and self.data["total_samples"]:
            duration = self.data["total_samples"] / self.data["sample_rate"]
            self.data["duration_seconds"] = round(duration, 2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python wav_extractor.py <file.wav>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = WAVExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
