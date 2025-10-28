#!/usr/bin/env python3
"""
SQLite Database Format Extractor for PaniniFS v3.9
Extracts metadata and structure from SQLite database files.

Supports:
- SQLite 3 format
- Database header parsing
- Schema extraction (tables, indexes, views)
- Table structure analysis
- Row counting
- Page size and encoding detection
"""

import struct
import sys
import json
from typing import Dict, Any, List, Optional, Tuple


class SQLiteExtractor:
    """Extract metadata from SQLite database files."""
    
    # SQLite constants
    SQLITE_MAGIC = b'SQLite format 3\x00'
    
    # Page types
    PAGE_TYPE_NAMES = {
        0x00: 'Unknown',
        0x02: 'Interior Index B-Tree',
        0x05: 'Interior Table B-Tree',
        0x0A: 'Leaf Index B-Tree',
        0x0D: 'Leaf Table B-Tree'
    }
    
    # Text encodings
    TEXT_ENCODINGS = {
        1: 'UTF-8',
        2: 'UTF-16le',
        3: 'UTF-16be'
    }
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from SQLite file."""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        # Parse database header
        header = self._parse_header()
        
        # Parse schema from sqlite_master
        schema = self._parse_schema(header)
        
        # Analyze tables
        table_stats = self._analyze_tables(schema)
        
        return {
            'format': 'SQLite',
            'header': header,
            'schema': schema,
            'statistics': table_stats
        }
    
    def _parse_header(self) -> Dict[str, Any]:
        """Parse SQLite database header (first 100 bytes)."""
        if len(self.data) < 100:
            raise ValueError("File too small for SQLite header")
        
        # Check magic
        magic = self.data[0:16]
        if magic != self.SQLITE_MAGIC:
            raise ValueError(f"Invalid SQLite magic: {magic[:10]}")
        
        # Parse header fields
        page_size_raw = struct.unpack('>H', self.data[16:18])[0]
        page_size = 65536 if page_size_raw == 1 else page_size_raw
        
        write_version = self.data[18]
        read_version = self.data[19]
        reserved_space = self.data[20]
        max_embedded_payload = self.data[21]
        min_embedded_payload = self.data[22]
        leaf_payload = self.data[23]
        file_change_counter = struct.unpack('>I', self.data[24:28])[0]
        database_size_pages = struct.unpack('>I', self.data[28:32])[0]
        first_freelist_page = struct.unpack('>I', self.data[32:36])[0]
        freelist_pages = struct.unpack('>I', self.data[36:40])[0]
        schema_cookie = struct.unpack('>I', self.data[40:44])[0]
        schema_format = struct.unpack('>I', self.data[44:48])[0]
        default_cache_size = struct.unpack('>I', self.data[48:52])[0]
        largest_root_page = struct.unpack('>I', self.data[52:56])[0]
        text_encoding = struct.unpack('>I', self.data[56:60])[0]
        user_version = struct.unpack('>I', self.data[60:64])[0]
        incremental_vacuum = struct.unpack('>I', self.data[64:68])[0]
        application_id = struct.unpack('>I', self.data[68:72])[0]
        version_valid_for = struct.unpack('>I', self.data[92:96])[0]
        sqlite_version = struct.unpack('>I', self.data[96:100])[0]
        
        # Calculate database size
        database_size_bytes = database_size_pages * page_size
        
        return {
            'version': '3',
            'page_size': page_size,
            'write_version': write_version,
            'read_version': read_version,
            'reserved_space': reserved_space,
            'file_change_counter': file_change_counter,
            'database_size_pages': database_size_pages,
            'database_size_bytes': database_size_bytes,
            'database_size_human': self._human_size(database_size_bytes),
            'first_freelist_page': first_freelist_page,
            'freelist_pages': freelist_pages,
            'schema_cookie': schema_cookie,
            'schema_format': schema_format,
            'default_cache_size': default_cache_size,
            'text_encoding': self.TEXT_ENCODINGS.get(text_encoding, f'Unknown ({text_encoding})'),
            'user_version': user_version,
            'incremental_vacuum': incremental_vacuum > 0,
            'application_id': application_id,
            'sqlite_version': self._format_version(sqlite_version)
        }
    
    def _parse_schema(self, header: Dict[str, Any]) -> Dict[str, Any]:
        """Parse schema from sqlite_master table."""
        # In SQLite, the first page (after header) contains the sqlite_master table
        # This is a simplified parser that looks for CREATE statements
        
        # Extract page 1 (database schema)
        page_size = header['page_size']
        
        # Page 1 starts at offset 100 (after database header on page 0)
        if len(self.data) < page_size:
            return {
                'tables': [],
                'indexes': [],
                'views': [],
                'triggers': []
            }
        
        # Find all CREATE statements in the database
        data_str = self.data.decode('utf-8', errors='replace')
        
        tables = []
        indexes = []
        views = []
        triggers = []
        
        # Simple parsing - look for CREATE TABLE, CREATE INDEX, etc.
        # This is simplified; a full parser would decode the B-tree structure
        import re
        
        # Extract table definitions
        table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\(([^)]+)\)'
        for match in re.finditer(table_pattern, data_str, re.IGNORECASE):
            table_name = match.group(1)
            columns_str = match.group(2)
            
            # Parse columns
            columns = []
            for col in columns_str.split(','):
                col = col.strip()
                if col:
                    parts = col.split()
                    if parts:
                        col_name = parts[0]
                        col_type = parts[1] if len(parts) > 1 else 'UNKNOWN'
                        constraints = ' '.join(parts[2:]) if len(parts) > 2 else ''
                        columns.append({
                            'name': col_name,
                            'type': col_type,
                            'constraints': constraints
                        })
            
            tables.append({
                'name': table_name,
                'columns': columns,
                'column_count': len(columns)
            })
        
        # Extract index definitions
        index_pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)'
        for match in re.finditer(index_pattern, data_str, re.IGNORECASE):
            indexes.append({
                'name': match.group(1),
                'table': match.group(2)
            })
        
        # Extract view definitions
        view_pattern = r'CREATE\s+VIEW\s+(\w+)'
        for match in re.finditer(view_pattern, data_str, re.IGNORECASE):
            views.append({
                'name': match.group(1)
            })
        
        # Extract trigger definitions
        trigger_pattern = r'CREATE\s+TRIGGER\s+(\w+)'
        for match in re.finditer(trigger_pattern, data_str, re.IGNORECASE):
            triggers.append({
                'name': match.group(1)
            })
        
        return {
            'tables': tables,
            'indexes': indexes,
            'views': views,
            'triggers': triggers
        }
    
    def _analyze_tables(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tables for statistics."""
        tables = schema.get('tables', [])
        indexes = schema.get('indexes', [])
        views = schema.get('views', [])
        triggers = schema.get('triggers', [])
        
        total_columns = sum(t.get('column_count', 0) for t in tables)
        
        return {
            'table_count': len(tables),
            'index_count': len(indexes),
            'view_count': len(views),
            'trigger_count': len(triggers),
            'total_columns': total_columns,
            'table_list': [t['name'] for t in tables],
            'index_list': [i['name'] for i in indexes]
        }
    
    def _format_version(self, version: int) -> str:
        """Format SQLite version number."""
        if version == 0:
            return 'Unknown'
        major = (version >> 16) & 0xFF
        minor = (version >> 8) & 0xFF
        patch = version & 0xFF
        return f'{major}.{minor}.{patch}'
    
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
        print(f"Usage: {sys.argv[0]} <database.sqlite>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = SQLiteExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
