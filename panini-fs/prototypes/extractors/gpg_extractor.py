#!/usr/bin/env python3
"""
PaniniFS v3.52 - GPG/PGP Format Extractor
OpenPGP/GPG cryptographic message and key format

Extracts:
- Armor blocks (PUBLIC KEY, PRIVATE KEY, MESSAGE, SIGNATURE)
- Key metadata (Version, Comment, Hash, Charset)
- Base64 content analysis (packets, length)
- CRC24 checksum validation
- Packet structure (basic parsing)
- Key fingerprints and key IDs
"""

import sys
import re
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

# OpenPGP armor block patterns
ARMOR_BEGIN = re.compile(r'^-----BEGIN PGP (.*?)-----$', re.MULTILINE)
ARMOR_END = re.compile(r'^-----END PGP (.*?)-----$', re.MULTILINE)
ARMOR_HEADER = re.compile(r'^([A-Za-z-]+): (.*)$', re.MULTILINE)
CRC24_LINE = re.compile(r'^=([A-Za-z0-9+/]{4})$', re.MULTILINE)

# OpenPGP packet tag patterns
PACKET_TAG_OLD = 0b10000000  # Bit 7 = 1
PACKET_TAG_NEW = 0b11000000  # Bits 7,6 = 11

# OpenPGP packet types
PACKET_TYPES = {
    0: "Reserved",
    1: "Public-Key Encrypted Session Key",
    2: "Signature",
    3: "Symmetric-Key Encrypted Session Key",
    4: "One-Pass Signature",
    5: "Secret-Key",
    6: "Public-Key",
    7: "Secret-Subkey",
    8: "Compressed Data",
    9: "Symmetrically Encrypted Data",
    10: "Marker",
    11: "Literal Data",
    12: "Trust",
    13: "User ID",
    14: "Public-Subkey",
    17: "User Attribute",
    18: "Sym. Encrypted and Integrity Protected Data",
    19: "Modification Detection Code",
}

# Public key algorithms
PKA_ALGORITHMS = {
    1: "RSA (Encrypt or Sign)",
    2: "RSA Encrypt-Only",
    3: "RSA Sign-Only",
    16: "Elgamal (Encrypt-Only)",
    17: "DSA (Digital Signature Algorithm)",
    18: "ECDH",
    19: "ECDSA",
    20: "Reserved (formerly Elgamal Encrypt or Sign)",
    21: "Reserved for Diffie-Hellman",
    22: "EdDSA",
}

# Hash algorithms
HASH_ALGORITHMS = {
    1: "MD5",
    2: "SHA1",
    3: "RIPEMD160",
    8: "SHA256",
    9: "SHA384",
    10: "SHA512",
    11: "SHA224",
}


def crc24(data: bytes) -> int:
    """Calculate CRC24 checksum for OpenPGP"""
    crc = 0xB704CE
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def parse_packet_header(data: bytes, offset: int) -> Optional[Tuple[int, int, int]]:
    """Parse OpenPGP packet header, return (tag, length, header_bytes)"""
    if offset >= len(data):
        return None
    
    tag_byte = data[offset]
    
    # Check if it's a valid packet tag
    if not (tag_byte & 0x80):
        return None
    
    # New format packet
    if (tag_byte & 0xC0) == 0xC0:
        tag = tag_byte & 0x3F
        if offset + 1 >= len(data):
            return None
        
        length_byte = data[offset + 1]
        if length_byte < 192:
            return (tag, length_byte, 2)
        elif length_byte < 224:
            if offset + 2 >= len(data):
                return None
            length = ((length_byte - 192) << 8) + data[offset + 2] + 192
            return (tag, length, 3)
        elif length_byte == 255:
            if offset + 5 >= len(data):
                return None
            length = (data[offset + 2] << 24) | (data[offset + 3] << 16) | \
                     (data[offset + 4] << 8) | data[offset + 5]
            return (tag, length, 6)
        else:
            # Partial body length
            return (tag, 1 << (length_byte & 0x1F), 2)
    
    # Old format packet
    else:
        tag = (tag_byte >> 2) & 0x0F
        length_type = tag_byte & 0x03
        
        if length_type == 0:
            if offset + 1 >= len(data):
                return None
            return (tag, data[offset + 1], 2)
        elif length_type == 1:
            if offset + 2 >= len(data):
                return None
            length = (data[offset + 1] << 8) | data[offset + 2]
            return (tag, length, 3)
        elif length_type == 2:
            if offset + 4 >= len(data):
                return None
            length = (data[offset + 1] << 24) | (data[offset + 2] << 16) | \
                     (data[offset + 3] << 8) | data[offset + 4]
            return (tag, length, 5)
        else:
            # Indeterminate length
            return (tag, len(data) - offset - 1, 1)


def parse_public_key_packet(data: bytes) -> Dict[str, Any]:
    """Parse public key packet for metadata"""
    result = {}
    
    if len(data) < 6:
        return result
    
    version = data[0]
    result['version'] = version
    
    if version == 4:
        # V4 key
        timestamp = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
        result['timestamp'] = timestamp
        
        if len(data) > 5:
            algorithm = data[5]
            result['algorithm'] = PKA_ALGORITHMS.get(algorithm, f"Unknown ({algorithm})")
            
            # RSA keys have modulus
            if algorithm in (1, 2, 3) and len(data) > 7:
                modulus_bits = (data[6] << 8) | data[7]
                result['key_bits'] = modulus_bits
    
    elif version == 3:
        # V3 key
        timestamp = (data[1] << 24) | (data[2] << 16) | (data[3] << 8) | data[4]
        validity_days = (data[5] << 8) | data[6]
        result['timestamp'] = timestamp
        result['validity_days'] = validity_days
        
        if len(data) > 7:
            algorithm = data[7]
            result['algorithm'] = PKA_ALGORITHMS.get(algorithm, f"Unknown ({algorithm})")
    
    return result


def analyze_packets(data: bytes) -> Dict[str, Any]:
    """Analyze OpenPGP packet structure"""
    packets = []
    packet_types = Counter()
    offset = 0
    total_parsed = 0
    
    while offset < len(data) and total_parsed < 100:  # Limit to prevent infinite loops
        header = parse_packet_header(data, offset)
        if not header:
            break
        
        tag, length, header_bytes = header
        packet_type = PACKET_TYPES.get(tag, f"Unknown ({tag})")
        packet_types[packet_type] += 1
        
        packet_info = {
            'type': packet_type,
            'tag': tag,
            'length': length,
            'offset': offset
        }
        
        # Parse key packets for additional metadata
        if tag in (5, 6, 7, 14):  # Key packets
            packet_start = offset + header_bytes
            packet_end = min(packet_start + length, len(data))
            key_data = data[packet_start:packet_end]
            key_info = parse_public_key_packet(key_data)
            packet_info.update(key_info)
        
        packets.append(packet_info)
        offset += header_bytes + length
        total_parsed += 1
    
    return {
        'packets': packets,
        'packet_types': dict(packet_types),
        'total_packets': len(packets),
        'bytes_parsed': offset
    }


def extract_gpg_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from GPG/PGP armored file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': len(content),
        'armor_blocks': []
    }
    
    # Find all armor blocks
    begin_matches = list(ARMOR_BEGIN.finditer(content))
    end_matches = list(ARMOR_END.finditer(content))
    
    if not begin_matches:
        return metadata
    
    metadata['block_count'] = len(begin_matches)
    
    # Parse each armor block
    for i, begin_match in enumerate(begin_matches):
        block_type = begin_match.group(1)
        begin_pos = begin_match.end()
        
        # Find corresponding end marker
        end_match = None
        for em in end_matches:
            if em.start() > begin_pos and em.group(1) == block_type:
                end_match = em
                break
        
        if not end_match:
            continue
        
        end_pos = end_match.start()
        block_content = content[begin_pos:end_pos].strip()
        
        block_info = {
            'type': block_type,
            'headers': {},
            'base64_lines': 0,
            'base64_chars': 0,
        }
        
        # Parse headers
        lines = block_content.split('\n')
        base64_data = []
        crc_value = None
        in_headers = True
        
        for line in lines:
            line = line.strip()
            if not line:
                in_headers = False
                continue
            
            if in_headers:
                header_match = ARMOR_HEADER.match(line)
                if header_match:
                    block_info['headers'][header_match.group(1)] = header_match.group(2)
                else:
                    in_headers = False
            
            if not in_headers:
                # Check for CRC24
                crc_match = CRC24_LINE.match(line)
                if crc_match:
                    crc_value = crc_match.group(1)
                    block_info['crc24'] = crc_value
                else:
                    # Base64 data
                    if re.match(r'^[A-Za-z0-9+/=]+$', line):
                        base64_data.append(line)
                        block_info['base64_lines'] += 1
                        block_info['base64_chars'] += len(line)
        
        # Decode base64 and analyze packets
        if base64_data:
            try:
                base64_string = ''.join(base64_data)
                decoded = base64.b64decode(base64_string)
                block_info['decoded_bytes'] = len(decoded)
                
                # Validate CRC24
                if crc_value:
                    calculated_crc = crc24(decoded)
                    stored_crc_bytes = base64.b64decode(crc_value)
                    stored_crc = (stored_crc_bytes[0] << 16) | \
                                 (stored_crc_bytes[1] << 8) | \
                                 stored_crc_bytes[2]
                    block_info['crc24_valid'] = (calculated_crc == stored_crc)
                
                # Analyze packet structure
                packet_info = analyze_packets(decoded)
                block_info['packets'] = packet_info
                
            except Exception as e:
                block_info['decode_error'] = str(e)
        
        metadata['armor_blocks'].append(block_info)
    
    return metadata


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes")
    
    if 'block_count' in metadata:
        print(f"\nArmor Blocks: {metadata['block_count']}")
        
        for i, block in enumerate(metadata['armor_blocks'], 1):
            print(f"\n--- Block {i}: {block['type']} ---")
            
            if block['headers']:
                print("Headers:")
                for key, value in block['headers'].items():
                    print(f"  {key}: {value}")
            
            print(f"Base64: {block['base64_lines']} lines, {block['base64_chars']:,} chars")
            
            if 'decoded_bytes' in block:
                print(f"Decoded: {block['decoded_bytes']:,} bytes")
            
            if 'crc24' in block:
                crc_status = "✓ Valid" if block.get('crc24_valid') else "✗ Invalid"
                print(f"CRC24: {block['crc24']} ({crc_status})")
            
            if 'packets' in block:
                pkt = block['packets']
                print(f"\nPackets: {pkt['total_packets']} packets, {pkt['bytes_parsed']:,} bytes parsed")
                
                if pkt['packet_types']:
                    print("Packet Types:")
                    for ptype, count in sorted(pkt['packet_types'].items(), 
                                               key=lambda x: x[1], reverse=True):
                        print(f"  {ptype}: {count}")
                
                # Show first few packets with details
                for j, packet in enumerate(pkt['packets'][:5], 1):
                    print(f"\n  Packet {j}: {packet['type']}")
                    if 'version' in packet:
                        print(f"    Version: {packet['version']}")
                    if 'algorithm' in packet:
                        print(f"    Algorithm: {packet['algorithm']}")
                    if 'key_bits' in packet:
                        print(f"    Key Size: {packet['key_bits']} bits")
                    if 'timestamp' in packet:
                        from datetime import datetime
                        ts = datetime.fromtimestamp(packet['timestamp'])
                        print(f"    Created: {ts.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if len(pkt['packets']) > 5:
                    print(f"  ... and {len(pkt['packets']) - 5} more packets")


def main():
    if len(sys.argv) != 2:
        print("Usage: python gpg_extractor.py <file.asc|file.gpg>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_gpg_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
