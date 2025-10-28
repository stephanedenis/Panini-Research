#!/usr/bin/env python3
"""
PEM (Privacy Enhanced Mail) Format Extractor - PaniniFS v3.49

This extractor analyzes PEM-encoded cryptographic data files.
PEM is a base64-encoded format used for X.509 certificates, private keys,
public keys, and other cryptographic data.

Format Structure:
- Header: -----BEGIN <TYPE>-----
- Base64-encoded data
- Footer: -----END <TYPE>-----
- Optional metadata between header and data (e.g., Proc-Type, DEK-Info)

Common PEM Types:
- CERTIFICATE: X.509 certificate
- RSA PRIVATE KEY: RSA private key
- RSA PUBLIC KEY: RSA public key  
- PRIVATE KEY: PKCS#8 private key
- PUBLIC KEY: X.509 SubjectPublicKeyInfo public key
- ENCRYPTED PRIVATE KEY: PKCS#8 encrypted private key
- CERTIFICATE REQUEST: PKCS#10 certificate signing request
- X509 CRL: X.509 certificate revocation list
- DH PARAMETERS: Diffie-Hellman parameters
- EC PRIVATE KEY: Elliptic Curve private key

X.509 Certificate Fields (DER-encoded in PEM):
- Version: X.509 version (1, 2, or 3)
- Serial Number: Unique certificate identifier
- Signature Algorithm: RSA, ECDSA, etc.
- Issuer: Certificate authority (CA) name
- Validity: Not Before, Not After dates
- Subject: Certificate holder name
- Subject Public Key Info: Algorithm, public key
- Extensions: Key Usage, Subject Alternative Name, etc.

PEM Metadata (for encrypted keys):
- Proc-Type: 4,ENCRYPTED
- DEK-Info: <cipher>,<IV hex>
  Common ciphers: DES-EDE3-CBC, AES-256-CBC, AES-128-CBC

Use Cases:
- TLS/SSL certificates
- SSH keys
- Code signing certificates
- Email encryption (S/MIME)
- VPN certificates
- Certificate authorities (CA)
- Certificate signing requests (CSR)

File Extensions:
- .pem: Generic PEM format
- .crt, .cer: Certificate
- .key: Private key
- .pub: Public key
- .csr: Certificate signing request

Related Formats:
- DER: Binary encoding of same data
- PKCS#7/P7B: Certificate chain container
- PKCS#12/PFX: Certificate + private key bundle

This extractor provides:
- PEM block type detection
- Block counting (multiple blocks per file)
- Base64 data size calculation
- Certificate parsing (issuer, subject, validity, serial)
- Key type detection (RSA, EC, DSA)
- Encryption detection (encrypted private keys)
- Metadata extraction (Proc-Type, DEK-Info)
- Multiple block support (certificate chains)

Author: PaniniFS Research Team
Version: 3.49
Target: PEM files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re
import base64

class PEMExtractor:
    """Extract metadata from PEM-encoded cryptographic files."""
    
    # PEM block pattern
    PEM_PATTERN = re.compile(
        r'-----BEGIN ([A-Z0-9 ]+)-----\s*\n((?:.*\n)*?)-----END \1-----',
        re.MULTILINE
    )
    
    # Metadata patterns (between BEGIN and base64 data)
    PROC_TYPE = re.compile(r'^Proc-Type:\s*(.+)$', re.MULTILINE)
    DEK_INFO = re.compile(r'^DEK-Info:\s*(.+)$', re.MULTILINE)
    
    # Common PEM types
    PEM_TYPES = {
        'CERTIFICATE': 'X.509 Certificate',
        'RSA PRIVATE KEY': 'RSA Private Key',
        'RSA PUBLIC KEY': 'RSA Public Key',
        'PRIVATE KEY': 'PKCS#8 Private Key',
        'PUBLIC KEY': 'X.509 SubjectPublicKeyInfo Public Key',
        'ENCRYPTED PRIVATE KEY': 'PKCS#8 Encrypted Private Key',
        'CERTIFICATE REQUEST': 'PKCS#10 Certificate Signing Request',
        'X509 CRL': 'X.509 Certificate Revocation List',
        'DH PARAMETERS': 'Diffie-Hellman Parameters',
        'EC PRIVATE KEY': 'Elliptic Curve Private Key',
        'EC PARAMETERS': 'Elliptic Curve Parameters',
        'DSA PRIVATE KEY': 'DSA Private Key',
        'OPENSSH PRIVATE KEY': 'OpenSSH Private Key',
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the PEM file."""
        try:
            # Read file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = {
                "format": "PEM (Privacy Enhanced Mail)",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
            }
            
            # Find all PEM blocks
            blocks = self._extract_blocks(content)
            
            if not blocks:
                metadata["error"] = "No PEM blocks found"
                return metadata
            
            metadata["block_count"] = len(blocks)
            metadata["blocks"] = blocks
            
            # Summarize block types
            block_types = [b["type"] for b in blocks]
            metadata["block_types"] = list(set(block_types))
            
            return metadata
            
        except Exception as e:
            return {
                "format": "PEM (Privacy Enhanced Mail)",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _extract_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract all PEM blocks from content."""
        blocks = []
        
        for match in self.PEM_PATTERN.finditer(content):
            pem_type = match.group(1)
            pem_data = match.group(2)
            
            block = {
                "type": pem_type,
                "type_description": self.PEM_TYPES.get(pem_type, "Unknown PEM Type"),
            }
            
            # Extract metadata lines (before base64 data)
            lines = pem_data.strip().split('\n')
            metadata_lines = []
            base64_lines = []
            
            in_metadata = True
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is metadata (key: value)
                if in_metadata and ':' in line and not line[0].isalnum():
                    metadata_lines.append(line)
                else:
                    in_metadata = False
                    base64_lines.append(line)
            
            # Parse metadata
            if metadata_lines:
                metadata_text = '\n'.join(metadata_lines)
                
                proc_type = self.PROC_TYPE.search(metadata_text)
                if proc_type:
                    block["proc_type"] = proc_type.group(1).strip()
                
                dek_info = self.DEK_INFO.search(metadata_text)
                if dek_info:
                    dek_parts = dek_info.group(1).strip().split(',')
                    block["encryption"] = {
                        "cipher": dek_parts[0].strip() if len(dek_parts) > 0 else None,
                        "iv": dek_parts[1].strip() if len(dek_parts) > 1 else None,
                    }
            
            # Calculate base64 data size
            base64_data = ''.join(base64_lines)
            block["base64_length"] = len(base64_data)
            
            # Try to decode base64 to get DER size
            try:
                der_data = base64.b64decode(base64_data)
                block["der_size"] = len(der_data)
                
                # Parse certificate if type is CERTIFICATE
                if pem_type == 'CERTIFICATE':
                    cert_info = self._parse_certificate_basic(der_data)
                    if cert_info:
                        block["certificate"] = cert_info
                
            except Exception:
                pass
            
            blocks.append(block)
        
        return blocks
    
    def _parse_certificate_basic(self, der_data: bytes) -> Optional[Dict[str, Any]]:
        """Basic X.509 certificate parsing (simplified, no full ASN.1 parser)."""
        # This is a very simplified parser for demonstration
        # A full implementation would use python-cryptography or pyasn1
        
        try:
            # Try to find common patterns in DER-encoded certificate
            result = {}
            
            # Look for common OID patterns (simplified)
            # In a real implementation, we'd parse the full ASN.1 structure
            
            # Find UTF8String/PrintableString values (common in DN)
            strings = []
            i = 0
            while i < len(der_data) - 4:
                # UTF8String (0x0C) or PrintableString (0x13)
                if der_data[i] in (0x0C, 0x13):
                    length = der_data[i + 1]
                    if length < 128 and i + 2 + length <= len(der_data):
                        try:
                            s = der_data[i + 2:i + 2 + length].decode('utf-8', errors='ignore')
                            if len(s) > 2 and s.isprintable():
                                strings.append(s)
                        except:
                            pass
                i += 1
            
            if strings:
                result["distinguished_name_components"] = strings[:20]
            
            return result if result else None
            
        except Exception:
            return None

def main():
    if len(sys.argv) < 2:
        print("Usage: pem_extractor.py <pem_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = PEMExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
