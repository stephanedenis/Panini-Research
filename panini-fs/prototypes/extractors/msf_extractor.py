#!/usr/bin/env python3
"""
PaniniFS v3.20 - MSF (Mozilla Summary File) Format Extractor
Author: Stéphane Denis (SDenis.ai)
Deconstructs MSF files to their finest details

Supports:
- Mozilla Mork database format
- Mail summary file structure
- Column definitions (aliases)
- Row data extraction
- Table analysis
- Message metadata
- Folder information
- Thread structure
- Character set detection
"""

import re
from typing import Dict, List, Any, Optional, Tuple

class MSFExtractor:
    """Extract metadata from MSF (Mozilla Summary File) files"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.metadata = {
            'format': 'MSF',
            'format_type': 'Mozilla Mork Database',
            'version': None,
            'charset': None,
            'columns': {},
            'tables': [],
            'rows': [],
            'folder_info': {},
            'statistics': {}
        }
        self.data = None
    
    def extract(self) -> Dict[str, Any]:
        """Extract all MSF metadata"""
        with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
            self.data = f.read()
        
        self._parse_header()
        self._parse_columns()
        self._parse_rows()
        self._parse_folder_info()
        self._analyze_database()
        
        return self.metadata
    
    def _parse_header(self):
        """Parse Mork database header"""
        # Version line: // <!-- <mdb:mork:z v="1.4"/> -->
        version_match = re.search(r'<mdb:mork:z v="([^"]+)"/>', self.data)
        if version_match:
            self.metadata['version'] = version_match.group(1)
        
        # Character set: (f=iso-8859-1) or similar
        charset_match = re.search(r'\(f=([^\)]+)\)', self.data)
        if charset_match:
            self.metadata['charset'] = charset_match.group(1)
    
    def _parse_columns(self):
        """Parse column definitions (aliases)"""
        # Column definitions are in format (XX=columnName)
        # They appear at the beginning of the file
        
        # Find all column definitions
        column_pattern = re.compile(r'\(([0-9A-F]{2})=([^\)]+)\)')
        
        for match in column_pattern.finditer(self.data):
            col_id = match.group(1)
            col_name = match.group(2)
            self.metadata['columns'][col_id] = col_name
    
    def _parse_rows(self):
        """Parse row data"""
        # Rows are in format {1:^80 ^81=value ^82=value}
        # or [1:^80(^81=value)(^82=value)]
        
        # Row pattern: {rowid:scope (col=val)(col=val)...}
        row_pattern = re.compile(r'\{([^}]+)\}')
        
        row_count = 0
        for match in row_pattern.finditer(self.data):
            if row_count >= 100:  # Limit to first 100 rows for metadata
                break
            
            row_data_str = match.group(1)
            row = self._parse_row(row_data_str)
            
            if row:
                self.metadata['rows'].append(row)
                row_count += 1
    
    def _parse_row(self, row_str: str) -> Optional[Dict[str, Any]]:
        """Parse a single row"""
        # Extract row ID and scope
        # Format: rowid:scope (col=val)...
        
        row = {}
        
        # Try to extract row ID
        id_match = re.match(r'([^:]+):([^\s]+)', row_str)
        if id_match:
            row['id'] = id_match.group(1)
            row['scope'] = id_match.group(2)
        
        # Extract column values
        # Pattern: (^XX=value) or ^XX=value
        col_pattern = re.compile(r'\^([0-9A-F]{2})=([^\)^\s]+)')
        
        for col_match in col_pattern.finditer(row_str):
            col_id = col_match.group(1)
            value = col_match.group(2)
            
            # Decode column name
            col_name = self.metadata['columns'].get(col_id, f'col_{col_id}')
            
            # Unescape value
            value = self._unescape_value(value)
            
            row[col_name] = value
        
        return row if len(row) > 2 else None  # Must have more than just id/scope
    
    def _unescape_value(self, value: str) -> str:
        """Unescape Mork value encoding"""
        # Mork uses $XX for hex escaping
        def replace_hex(match):
            hex_val = match.group(1)
            try:
                return chr(int(hex_val, 16))
            except:
                return match.group(0)
        
        value = re.sub(r'\$([0-9A-F]{2})', replace_hex, value)
        
        # Handle other escapes
        value = value.replace('\\n', '\n')
        value = value.replace('\\t', '\t')
        value = value.replace('\\\\', '\\')
        
        return value
    
    def _parse_folder_info(self):
        """Parse folder information from dbfolderinfo table"""
        # Look for rows with scope containing 'dbfolderinfo'
        for row in self.metadata['rows']:
            scope = row.get('scope', '')
            if 'dbfolderinfo' in scope.lower():
                # This is folder information
                folder_info = {}
                
                # Extract relevant fields
                if 'numMsgs' in row:
                    try:
                        folder_info['num_messages'] = int(row['numMsgs'])
                    except:
                        folder_info['num_messages'] = row['numMsgs']
                
                if 'numNewMsgs' in row:
                    try:
                        folder_info['num_new_messages'] = int(row['numNewMsgs'])
                    except:
                        folder_info['num_new_messages'] = row['numNewMsgs']
                
                if 'folderSize' in row:
                    try:
                        folder_info['folder_size'] = int(row['folderSize'])
                    except:
                        folder_info['folder_size'] = row['folderSize']
                
                if 'folderName' in row:
                    folder_info['folder_name'] = row['folderName']
                
                if 'folderDate' in row:
                    folder_info['folder_date'] = row['folderDate']
                
                if 'mailboxName' in row:
                    folder_info['mailbox_name'] = row['mailboxName']
                
                if 'version' in row:
                    folder_info['db_version'] = row['version']
                
                if folder_info:
                    self.metadata['folder_info'].update(folder_info)
                    break
    
    def _analyze_database(self):
        """Generate database statistics"""
        stats = {
            'column_count': len(self.metadata['columns']),
            'row_count': len(self.metadata['rows']),
            'has_folder_info': bool(self.metadata['folder_info']),
            'file_size': len(self.data)
        }
        
        # Analyze row types
        scope_types = {}
        for row in self.metadata['rows']:
            scope = row.get('scope', 'unknown')
            # Extract scope type (e.g., ^80 -> msg, ^9E -> dbfolderinfo)
            scope_clean = re.sub(r'\^[0-9A-F]{2}', 'scope', scope)
            scope_types[scope_clean] = scope_types.get(scope_clean, 0) + 1
        
        stats['scope_distribution'] = scope_types
        
        # Count message rows (rows with subject, sender, etc.)
        message_rows = 0
        for row in self.metadata['rows']:
            if 'subject' in row or 'sender' in row or 'message-id' in row:
                message_rows += 1
        
        stats['message_rows'] = message_rows
        
        # Identify common columns
        column_usage = {}
        for row in self.metadata['rows']:
            for key in row.keys():
                if key not in ['id', 'scope']:
                    column_usage[key] = column_usage.get(key, 0) + 1
        
        # Top 10 used columns
        top_columns = sorted(column_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        stats['top_columns'] = [{'column': col, 'count': count} for col, count in top_columns]
        
        # Extract sample messages
        sample_messages = []
        for row in self.metadata['rows'][:5]:
            if 'subject' in row:
                msg = {}
                if 'subject' in row:
                    msg['subject'] = row['subject']
                if 'sender' in row:
                    msg['sender'] = row['sender']
                if 'date' in row:
                    msg['date'] = row['date']
                if 'size' in row:
                    msg['size'] = row['size']
                
                if msg:
                    sample_messages.append(msg)
        
        if sample_messages:
            stats['sample_messages'] = sample_messages
        
        self.metadata['statistics'] = stats


def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python msf_extractor.py <file.msf>")
        sys.exit(1)
    
    filename = sys.argv[1]
    extractor = MSFExtractor(filename)
    
    try:
        metadata = extractor.extract()
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
