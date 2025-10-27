#!/usr/bin/env python3
"""
MBOX (Unix Mailbox) Format Extractor for PaniniFS v3.13
Extracts metadata and structure from MBOX mailbox files.

Supports:
- MBOX format (Unix mailbox)
- Multiple message parsing
- Message delimiter detection (From_ lines)
- Per-message header extraction
- Message counting and statistics
- Date range analysis
"""

import sys
import json
import re
import email
from email import policy
from email.parser import BytesParser
from typing import Dict, Any, List, Optional
from datetime import datetime
import mailbox


class MBOXExtractor:
    """Extract metadata from MBOX mailbox files."""
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.mbox = None
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from MBOX file."""
        # Open MBOX file
        self.mbox = mailbox.mbox(self.filepath)
        
        # Parse all messages
        messages = self._parse_messages()
        
        # Analyze mailbox
        analysis = self._analyze_mailbox(messages)
        
        return {
            'format': 'MBOX',
            'mailbox': {
                'total_messages': len(messages),
                'file_path': self.filepath,
            },
            'messages': messages[:10],  # First 10 messages as sample
            'analysis': analysis
        }
    
    def _parse_messages(self) -> List[Dict[str, Any]]:
        """Parse all messages in MBOX."""
        messages = []
        
        for idx, message in enumerate(self.mbox):
            try:
                msg_info = {
                    'index': idx,
                    'from': self._decode_header(message.get('From', '')),
                    'to': self._decode_header(message.get('To', '')),
                    'subject': self._decode_header(message.get('Subject', '')),
                    'date': message.get('Date', ''),
                    'message_id': message.get('Message-ID', ''),
                    'size': len(str(message))
                }
                
                # Parse date
                msg_info['date_parsed'] = self._parse_date(msg_info['date'])
                
                # Check for attachments
                msg_info['has_attachments'] = self._has_attachments(message)
                msg_info['is_multipart'] = message.is_multipart()
                
                messages.append(msg_info)
            except Exception as e:
                # Skip malformed messages
                messages.append({
                    'index': idx,
                    'error': str(e)
                })
        
        return messages
    
    def _has_attachments(self, message) -> bool:
        """Check if message has attachments."""
        if not message.is_multipart():
            return False
        
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get_filename():
                return True
        
        return False
    
    def _analyze_mailbox(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze mailbox statistics."""
        total_messages = len(messages)
        total_size = sum(msg.get('size', 0) for msg in messages if 'size' in msg)
        
        # Count messages with attachments
        with_attachments = sum(1 for msg in messages if msg.get('has_attachments', False))
        multipart = sum(1 for msg in messages if msg.get('is_multipart', False))
        
        # Extract senders
        senders = {}
        for msg in messages:
            if 'from' in msg and msg['from']:
                sender = msg['from']
                senders[sender] = senders.get(sender, 0) + 1
        
        # Top senders
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Date range
        dates = [msg.get('date_parsed') for msg in messages if msg.get('date_parsed')]
        dates = [d for d in dates if d]
        
        date_range = None
        if dates:
            date_range = {
                'earliest': min(dates),
                'latest': max(dates)
            }
        
        return {
            'total_messages': total_messages,
            'total_size': total_size,
            'total_size_human': self._human_size(total_size),
            'messages_with_attachments': with_attachments,
            'multipart_messages': multipart,
            'unique_senders': len(senders),
            'top_senders': [{'sender': s, 'count': c} for s, c in top_senders],
            'date_range': date_range
        }
    
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
        print(f"Usage: {sys.argv[0]} <mailbox.mbox>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = MBOXExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
