#!/usr/bin/env python3
"""
EML (Email Message) Format Extractor for PaniniFS v3.12
Extracts metadata and structure from EML/RFC 822 email files.

Supports:
- RFC 822/2822/5322 email format
- Header parsing (From, To, Subject, Date, etc.)
- MIME multipart messages
- Content-Type detection
- Attachment enumeration
- Header field extraction (DKIM, SPF, ARC, etc.)
- Body structure analysis
"""

import sys
import json
import re
import email
from email import policy
from email.parser import BytesParser
from typing import Dict, Any, List, Optional
from datetime import datetime


class EMLExtractor:
    """Extract metadata from EML email files."""
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.message = None
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from EML file."""
        with open(self.filepath, 'rb') as f:
            self.message = BytesParser(policy=policy.default).parse(f)
        
        # Parse headers
        headers = self._parse_headers()
        
        # Parse MIME structure
        mime_info = self._parse_mime_structure()
        
        # Extract attachments
        attachments = self._extract_attachments()
        
        # Parse body
        body_info = self._parse_body()
        
        # Parse authentication headers
        auth_info = self._parse_authentication()
        
        return {
            'format': 'EML',
            'headers': headers,
            'mime': mime_info,
            'attachments': attachments,
            'body': body_info,
            'authentication': auth_info,
            'statistics': self._compute_statistics()
        }
    
    def _parse_headers(self) -> Dict[str, Any]:
        """Parse standard email headers."""
        headers = {}
        
        # Essential headers
        headers['from'] = self._decode_header(self.message.get('From', ''))
        headers['to'] = self._decode_header(self.message.get('To', ''))
        headers['subject'] = self._decode_header(self.message.get('Subject', ''))
        headers['date'] = self.message.get('Date', '')
        headers['message_id'] = self.message.get('Message-ID', '')
        
        # Optional headers
        headers['cc'] = self._decode_header(self.message.get('Cc', ''))
        headers['bcc'] = self._decode_header(self.message.get('Bcc', ''))
        headers['reply_to'] = self._decode_header(self.message.get('Reply-To', ''))
        headers['in_reply_to'] = self.message.get('In-Reply-To', '')
        headers['references'] = self.message.get('References', '')
        
        # Parse date
        headers['date_parsed'] = self._parse_date(headers['date'])
        
        return headers
    
    def _parse_mime_structure(self) -> Dict[str, Any]:
        """Parse MIME structure."""
        mime_info = {
            'content_type': self.message.get_content_type(),
            'content_disposition': self.message.get_content_disposition(),
            'charset': self.message.get_content_charset(),
            'is_multipart': self.message.is_multipart(),
            'parts': []
        }
        
        if self.message.is_multipart():
            for part in self.message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                part_info = {
                    'content_type': part.get_content_type(),
                    'content_disposition': part.get_content_disposition(),
                    'charset': part.get_content_charset(),
                    'filename': part.get_filename(),
                    'size': len(part.get_payload(decode=True) or b'')
                }
                mime_info['parts'].append(part_info)
        
        return mime_info
    
    def _extract_attachments(self) -> List[Dict[str, Any]]:
        """Extract attachment information."""
        attachments = []
        
        if not self.message.is_multipart():
            return attachments
        
        for part in self.message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            
            filename = part.get_filename()
            if filename:
                payload = part.get_payload(decode=True)
                attachments.append({
                    'filename': self._decode_header(filename),
                    'content_type': part.get_content_type(),
                    'size': len(payload or b''),
                    'size_human': self._human_size(len(payload or b'')),
                    'content_disposition': part.get_content_disposition()
                })
        
        return attachments
    
    def _parse_body(self) -> Dict[str, Any]:
        """Parse email body."""
        body_info = {
            'plain': None,
            'html': None,
            'parts_count': 0
        }
        
        if self.message.is_multipart():
            for part in self.message.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_info['plain'] = payload.decode(
                                part.get_content_charset() or 'utf-8',
                                errors='replace'
                            )[:500]  # First 500 chars
                    except:
                        pass
                
                elif content_type == 'text/html':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_info['html'] = payload.decode(
                                part.get_content_charset() or 'utf-8',
                                errors='replace'
                            )[:500]  # First 500 chars
                    except:
                        pass
                
                body_info['parts_count'] += 1
        else:
            # Single part message
            try:
                payload = self.message.get_payload(decode=True)
                if payload:
                    content_type = self.message.get_content_type()
                    text = payload.decode(
                        self.message.get_content_charset() or 'utf-8',
                        errors='replace'
                    )[:500]
                    
                    if content_type == 'text/plain':
                        body_info['plain'] = text
                    elif content_type == 'text/html':
                        body_info['html'] = text
            except:
                pass
        
        return body_info
    
    def _parse_authentication(self) -> Dict[str, Any]:
        """Parse authentication headers (DKIM, SPF, DMARC, ARC)."""
        auth_info = {}
        
        # DKIM
        dkim = self.message.get('DKIM-Signature', '')
        if dkim:
            auth_info['dkim'] = {
                'present': True,
                'algorithm': self._extract_field(dkim, 'a='),
                'domain': self._extract_field(dkim, 'd='),
                'selector': self._extract_field(dkim, 's=')
            }
        
        # SPF
        received_spf = self.message.get('Received-SPF', '')
        if received_spf:
            auth_info['spf'] = {
                'result': received_spf.split()[0] if received_spf else None,
                'detail': received_spf[:100]
            }
        
        # ARC
        arc_seal = self.message.get('ARC-Seal', '')
        arc_auth = self.message.get('ARC-Authentication-Results', '')
        if arc_seal or arc_auth:
            auth_info['arc'] = {
                'present': True,
                'seal': bool(arc_seal),
                'authentication': bool(arc_auth)
            }
        
        # DMARC (from Authentication-Results)
        auth_results = self.message.get('Authentication-Results', '')
        if 'dmarc=' in auth_results.lower():
            dmarc_match = re.search(r'dmarc=(\w+)', auth_results.lower())
            if dmarc_match:
                auth_info['dmarc'] = {
                    'result': dmarc_match.group(1)
                }
        
        # Mozilla status (Thunderbird)
        mozilla_status = self.message.get('X-Mozilla-Status', '')
        if mozilla_status:
            auth_info['mozilla'] = {
                'status': mozilla_status,
                'status2': self.message.get('X-Mozilla-Status2', ''),
                'keys': self.message.get('X-Mozilla-Keys', '')
            }
        
        return auth_info
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute email statistics."""
        stats = {
            'total_headers': len(self.message.keys()),
            'is_multipart': self.message.is_multipart(),
            'attachment_count': len(self._extract_attachments()),
            'has_html': False,
            'has_plain': False
        }
        
        # Check content types
        if self.message.is_multipart():
            for part in self.message.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html':
                    stats['has_html'] = True
                elif content_type == 'text/plain':
                    stats['has_plain'] = True
        else:
            content_type = self.message.get_content_type()
            if content_type == 'text/html':
                stats['has_html'] = True
            elif content_type == 'text/plain':
                stats['has_plain'] = True
        
        return stats
    
    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ''
        
        try:
            decoded_parts = email.header.decode_header(header)
            result = []
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    result.append(part.decode(encoding or 'utf-8', errors='replace'))
                else:
                    result.append(str(part))
            return ''.join(result)
        except:
            return header
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse email date string."""
        if not date_str:
            return None
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return None
    
    def _extract_field(self, header: str, field: str) -> Optional[str]:
        """Extract a field from header string."""
        match = re.search(f'{re.escape(field)}([^;\\s]+)', header)
        return match.group(1) if match else None
    
    def _human_size(self, size: int) -> str:
        """Convert size to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


def main():
    """Main extraction function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file.eml>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = EMLExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
