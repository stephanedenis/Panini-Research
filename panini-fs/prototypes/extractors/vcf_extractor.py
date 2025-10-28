#!/usr/bin/env python3
"""
vCard (VCF) Format Extractor for PaniniFS v3.14
Extracts metadata from vCard contact files.

Supports:
- vCard 2.1, 3.0, and 4.0 formats
- Multiple contact parsing
- Name fields (FN, N)
- Phone numbers (TEL)
- Email addresses (EMAIL)
- Addresses (ADR)
- Organizations (ORG)
- Photos (PHOTO)
- Birthdays (BDAY)
- URLs and notes
"""

import sys
import json
import re
from typing import Dict, Any, List, Optional


class VCFExtractor:
    """Extract metadata from vCard files."""
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from vCard file."""
        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            self.data = f.read()
        
        # Parse vCards
        vcards = self._parse_vcards()
        
        # Analyze contacts
        analysis = self._analyze_contacts(vcards)
        
        return {
            'format': 'vCard',
            'contacts': vcards,
            'analysis': analysis
        }
    
    def _parse_vcards(self) -> List[Dict[str, Any]]:
        """Parse all vCards in file."""
        vcards = []
        
        # Split by BEGIN:VCARD
        vcard_blocks = re.split(r'BEGIN:VCARD', self.data, flags=re.IGNORECASE)
        
        for block in vcard_blocks[1:]:  # Skip first empty block
            # Find END:VCARD
            end_match = re.search(r'END:VCARD', block, re.IGNORECASE)
            if not end_match:
                continue
            
            vcard_text = block[:end_match.end()]
            vcard_data = self._parse_vcard(vcard_text)
            if vcard_data:
                vcards.append(vcard_data)
        
        return vcards
    
    def _parse_vcard(self, vcard_text: str) -> Optional[Dict[str, Any]]:
        """Parse a single vCard."""
        vcard = {
            'version': None,
            'formatted_name': None,
            'name': {},
            'organization': None,
            'title': None,
            'phones': [],
            'emails': [],
            'addresses': [],
            'url': None,
            'birthday': None,
            'note': None,
            'photo': None
        }
        
        lines = vcard_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('END:VCARD'):
                continue
            
            # Parse field
            if ':' not in line:
                continue
            
            # Handle properties with parameters
            field_match = re.match(r'([^:;]+)(?:;([^:]+))?:(.*)$', line)
            if not field_match:
                continue
            
            field_name = field_match.group(1).upper()
            field_params = field_match.group(2) or ''
            field_value = field_match.group(3)
            
            # Parse specific fields
            if field_name == 'VERSION':
                vcard['version'] = field_value
            
            elif field_name == 'FN':
                vcard['formatted_name'] = field_value
            
            elif field_name == 'N':
                # N:LastName;FirstName;MiddleName;Prefix;Suffix
                parts = field_value.split(';')
                vcard['name'] = {
                    'last': parts[0] if len(parts) > 0 else '',
                    'first': parts[1] if len(parts) > 1 else '',
                    'middle': parts[2] if len(parts) > 2 else '',
                    'prefix': parts[3] if len(parts) > 3 else '',
                    'suffix': parts[4] if len(parts) > 4 else ''
                }
            
            elif field_name == 'ORG':
                vcard['organization'] = field_value
            
            elif field_name == 'TITLE':
                vcard['title'] = field_value
            
            elif field_name == 'TEL':
                phone_type = self._parse_type(field_params)
                vcard['phones'].append({
                    'number': field_value,
                    'type': phone_type
                })
            
            elif field_name == 'EMAIL':
                email_type = self._parse_type(field_params)
                vcard['emails'].append({
                    'address': field_value,
                    'type': email_type
                })
            
            elif field_name == 'ADR':
                # ADR:POBox;Extended;Street;City;State;Zip;Country
                parts = field_value.split(';')
                address = {
                    'po_box': parts[0] if len(parts) > 0 else '',
                    'extended': parts[1] if len(parts) > 1 else '',
                    'street': parts[2] if len(parts) > 2 else '',
                    'city': parts[3] if len(parts) > 3 else '',
                    'state': parts[4] if len(parts) > 4 else '',
                    'zip': parts[5] if len(parts) > 5 else '',
                    'country': parts[6] if len(parts) > 6 else '',
                    'type': self._parse_type(field_params)
                }
                vcard['addresses'].append(address)
            
            elif field_name == 'URL':
                vcard['url'] = field_value
            
            elif field_name == 'BDAY':
                vcard['birthday'] = field_value
            
            elif field_name == 'NOTE':
                vcard['note'] = field_value
            
            elif field_name == 'PHOTO':
                # Store photo info (not the actual data)
                encoding = 'ENCODING=b' in field_params or 'ENCODING=BASE64' in field_params.upper()
                photo_type = self._parse_photo_type(field_params)
                vcard['photo'] = {
                    'encoded': encoding,
                    'type': photo_type,
                    'has_data': bool(field_value)
                }
        
        return vcard if vcard['formatted_name'] or vcard['name'].get('first') else None
    
    def _parse_type(self, params: str) -> str:
        """Parse TYPE parameter."""
        if not params:
            return 'default'
        
        # Look for TYPE=xxx
        type_match = re.search(r'TYPE=([^;,]+)', params, re.IGNORECASE)
        if type_match:
            return type_match.group(1).lower()
        
        # Check for direct type (e.g., "WORK,VOICE")
        params_lower = params.lower()
        for t in ['work', 'home', 'cell', 'pref', 'voice', 'fax', 'msg', 'pager', 'internet']:
            if t in params_lower:
                return t
        
        return 'default'
    
    def _parse_photo_type(self, params: str) -> Optional[str]:
        """Parse photo type from parameters."""
        if not params:
            return None
        
        type_match = re.search(r'TYPE=([^;,]+)', params, re.IGNORECASE)
        if type_match:
            return type_match.group(1).upper()
        
        # Check for common image types
        for img_type in ['JPEG', 'PNG', 'GIF', 'BMP']:
            if img_type in params.upper():
                return img_type
        
        return None
    
    def _analyze_contacts(self, vcards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contacts statistics."""
        total_contacts = len(vcards)
        
        # Count fields
        with_phone = sum(1 for v in vcards if v['phones'])
        with_email = sum(1 for v in vcards if v['emails'])
        with_address = sum(1 for v in vcards if v['addresses'])
        with_org = sum(1 for v in vcards if v['organization'])
        with_photo = sum(1 for v in vcards if v['photo'])
        with_birthday = sum(1 for v in vcards if v['birthday'])
        
        # Count total fields
        total_phones = sum(len(v['phones']) for v in vcards)
        total_emails = sum(len(v['emails']) for v in vcards)
        total_addresses = sum(len(v['addresses']) for v in vcards)
        
        # Version distribution
        versions = {}
        for v in vcards:
            ver = v['version'] or 'unknown'
            versions[ver] = versions.get(ver, 0) + 1
        
        return {
            'total_contacts': total_contacts,
            'contacts_with_phone': with_phone,
            'contacts_with_email': with_email,
            'contacts_with_address': with_address,
            'contacts_with_organization': with_org,
            'contacts_with_photo': with_photo,
            'contacts_with_birthday': with_birthday,
            'total_phone_numbers': total_phones,
            'total_email_addresses': total_emails,
            'total_addresses': total_addresses,
            'version_distribution': versions
        }


def main():
    """Main extraction function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <contacts.vcf>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = VCFExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
