#!/usr/bin/env python3
"""
PaniniFS v3.54 - PATCH/DIFF Format Extractor (Simplified)
Unified diff patch format (GNU diff, git diff)

Extracts:
- Patch metadata (files changed, lines +/-)
- File modifications list
- Statistics per file
- Format detection (unified, git)
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

# Simple patterns
DIFF_HEADER = re.compile(r'^diff --git a/(.*) b/(.*)$')
UNIFIED_OLD = re.compile(r'^--- (.+)$')
UNIFIED_NEW = re.compile(r'^\+\+\+ (.+)$')
HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
GIT_FROM = re.compile(r'^From: (.+)$')
GIT_SUBJECT = re.compile(r'^Subject: (.+)$')


def extract_patch_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from patch/diff file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return {'error': str(e)}
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': sum(len(line) for line in lines),
        'line_count': len(lines),
        'files_changed': [],
        'total_additions': 0,
        'total_deletions': 0,
        'format': 'unknown'
    }
    
    # Detect format
    for line in lines[:20]:
        if line.startswith('diff --git'):
            metadata['format'] = 'git'
            break
        elif line.startswith('--- ') and not line.startswith('--- a/'):
            metadata['format'] = 'unified'
            break
    
    # Extract git metadata
    if metadata['format'] == 'git':
        for line in lines[:50]:
            if GIT_FROM.match(line):
                metadata['author'] = GIT_FROM.match(line).group(1).strip()
            elif GIT_SUBJECT.match(line):
                metadata['subject'] = GIT_SUBJECT.match(line).group(1).strip()
    
    # Parse files and stats
    current_file = None
    in_hunk = False
    
    for line in lines:
        # New file
        if DIFF_HEADER.match(line):
            match = DIFF_HEADER.match(line)
            current_file = {
                'old_file': match.group(1),
                'new_file': match.group(2),
                'additions': 0,
                'deletions': 0,
                'hunks': 0
            }
            metadata['files_changed'].append(current_file)
            in_hunk = False
            
        elif UNIFIED_OLD.match(line):
            if not current_file:
                current_file = {
                    'old_file': UNIFIED_OLD.match(line).group(1),
                    'new_file': None,
                    'additions': 0,
                    'deletions': 0,
                    'hunks': 0
                }
                metadata['files_changed'].append(current_file)
            in_hunk = False
            
        elif UNIFIED_NEW.match(line) and current_file:
            current_file['new_file'] = UNIFIED_NEW.match(line).group(1)
            
        # Hunk header
        elif HUNK_HEADER.match(line) and current_file:
            current_file['hunks'] += 1
            in_hunk = True
            
        # Count additions/deletions in hunk
        elif in_hunk and current_file:
            if line.startswith('+') and not line.startswith('+++'):
                current_file['additions'] += 1
                metadata['total_additions'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                current_file['deletions'] += 1
                metadata['total_deletions'] += 1
    
    return metadata


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes ({metadata['line_count']:,} lines)")
    print(f"Format: {metadata['format']}")
    
    if 'author' in metadata:
        print(f"Author: {metadata['author']}")
    if 'subject' in metadata:
        print(f"Subject: {metadata['subject']}")
    
    print(f"\nFiles Changed: {len(metadata['files_changed'])}")
    print(f"Total Additions: +{metadata['total_additions']} lines")
    print(f"Total Deletions: -{metadata['total_deletions']} lines")
    print(f"Net Change: {metadata['total_additions'] - metadata['total_deletions']:+d} lines")
    
    if metadata['files_changed']:
        print(f"\nFile Details:")
        for i, file_info in enumerate(metadata['files_changed'][:10], 1):
            old_file = file_info['old_file']
            new_file = file_info['new_file'] or old_file
            
            if old_file == new_file:
                filename = old_file
            else:
                filename = f"{old_file} → {new_file}"
            
            changes = f"+{file_info['additions']} -{file_info['deletions']}"
            hunks = f"{file_info['hunks']} hunk(s)"
            
            print(f"  {i}. {filename}")
            print(f"     Changes: {changes}, {hunks}")
        
        if len(metadata['files_changed']) > 10:
            print(f"  ... and {len(metadata['files_changed']) - 10} more files")


def main():
    if len(sys.argv) != 2:
        print("Usage: python patch_extractor_v2.py <file.patch|file.diff>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_patch_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
