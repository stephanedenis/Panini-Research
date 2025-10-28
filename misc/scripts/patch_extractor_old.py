#!/usr/bin/env python3
"""
PaniniFS v3.54 - PATCH/DIFF Format Extractor
Unified diff patch format (GNU diff, git diff)

Extracts:
- Patch metadata (author, date, subject)
- File modifications (additions, deletions, changes)
- Diff hunks with line numbers
- Statistics (files changed, lines +/-)
- Patch format detection (unified, context, git)
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

# Patch format patterns
GIT_HEADER = re.compile(r'^From ([0-9a-f]{40}) ')
GIT_FROM = re.compile(r'^From: (.+)$')
GIT_DATE = re.compile(r'^Date: (.+)$')
GIT_SUBJECT = re.compile(r'^Subject: (.+)$')

UNIFIED_HEADER = re.compile(r'^--- (.+)$')
UNIFIED_NEW = re.compile(r'^\+\+\+ (.+)$')
HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@ ?(.*)$')

CONTEXT_HEADER = re.compile(r'^\*\*\* (.+)$')
CONTEXT_NEW = re.compile(r'^--- (.+)$')
CONTEXT_HUNK = re.compile(r'^\*{15}$')

INDEX_LINE = re.compile(r'^index ([0-9a-f]+)\.\.([0-9a-f]+)( \d+)?$')
NEW_FILE = re.compile(r'^new file mode (\d+)$')
DELETED_FILE = re.compile(r'^deleted file mode (\d+)$')
RENAME_FROM = re.compile(r'^rename from (.+)$')
RENAME_TO = re.compile(r'^rename to (.+)$')
SIMILARITY = re.compile(r'^similarity index (\d+)%$')

# Line type markers
ADD_LINE = re.compile(r'^\+(.*)$')
DEL_LINE = re.compile(r'^-(.*)$')
CONTEXT_LINE = re.compile(r'^ (.*)$')


def detect_patch_format(lines: List[str]) -> str:
    """Detect patch format"""
    for line in lines[:20]:
        if GIT_HEADER.match(line):
            return "git"
        if CONTEXT_HEADER.match(line) and '***' in line:
            return "context"
        if UNIFIED_HEADER.match(line):
            return "unified"
    return "unknown"


def parse_git_metadata(lines: List[str]) -> Dict[str, Any]:
    """Parse git format-patch metadata"""
    metadata = {}
    
    for i, line in enumerate(lines):
        if GIT_HEADER.match(line):
            match = GIT_HEADER.match(line)
            metadata['commit'] = match.group(1)
        elif GIT_FROM.match(line):
            metadata['author'] = GIT_FROM.match(line).group(1)
        elif GIT_DATE.match(line):
            metadata['date'] = GIT_DATE.match(line).group(1)
        elif GIT_SUBJECT.match(line):
            subject = GIT_SUBJECT.match(line).group(1)
            # Collect multi-line subjects
            j = i + 1
            while j < len(lines) and lines[j].startswith(' '):
                subject += ' ' + lines[j].strip()
                j += 1
            metadata['subject'] = subject
        elif line.strip() == '---':
            break
    
    return metadata


def parse_file_diff(lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
    """Parse a single file diff starting at given index"""
    
    if start_idx >= len(lines):
        return None
    
    file_diff = {
        'old_file': None,
        'new_file': None,
        'hunks': [],
        'stats': {'additions': 0, 'deletions': 0, 'context': 0},
        'metadata': {}
    }
    
    i = start_idx
    
    # Parse file metadata
    while i < len(lines):
        line = lines[i]
        
        # Git extended headers
        if NEW_FILE.match(line):
            file_diff['metadata']['new_file'] = True
            file_diff['metadata']['mode'] = NEW_FILE.match(line).group(1)
        elif DELETED_FILE.match(line):
            file_diff['metadata']['deleted_file'] = True
            file_diff['metadata']['mode'] = DELETED_FILE.match(line).group(1)
        elif RENAME_FROM.match(line):
            file_diff['metadata']['rename_from'] = RENAME_FROM.match(line).group(1)
        elif RENAME_TO.match(line):
            file_diff['metadata']['rename_to'] = RENAME_TO.match(line).group(1)
        elif SIMILARITY.match(line):
            file_diff['metadata']['similarity'] = int(SIMILARITY.match(line).group(1))
        elif INDEX_LINE.match(line):
            match = INDEX_LINE.match(line)
            file_diff['metadata']['index'] = {
                'old': match.group(1),
                'new': match.group(2)
            }
        
        # File names
        elif UNIFIED_HEADER.match(line):
            file_diff['old_file'] = UNIFIED_HEADER.match(line).group(1)
            i += 1
            if i < len(lines) and UNIFIED_NEW.match(lines[i]):
                file_diff['new_file'] = UNIFIED_NEW.match(lines[i]).group(1)
            break
        
        i += 1
    
    # Parse hunks
    i += 1
    while i < len(lines):
        line = lines[i]
        
        # Check for next file or end
        if UNIFIED_HEADER.match(line) or line.startswith('diff --git'):
            break
        
        # Hunk header
        hunk_match = HUNK_HEADER.match(line)
        if hunk_match:
            hunk = {
                'old_start': int(hunk_match.group(1)),
                'old_count': int(hunk_match.group(2) or 1),
                'new_start': int(hunk_match.group(3)),
                'new_count': int(hunk_match.group(4) or 1),
                'context': hunk_match.group(5),
                'lines': []
            }
            
            # Parse hunk lines
            i += 1
            while i < len(lines):
                line = lines[i]
                
                if HUNK_HEADER.match(line) or UNIFIED_HEADER.match(line) or \
                   line.startswith('diff --git'):
                    i -= 1  # Back up so outer loop can process this line
                    break
                
                if ADD_LINE.match(line):
                    hunk['lines'].append(('add', ADD_LINE.match(line).group(1)))
                    file_diff['stats']['additions'] += 1
                elif DEL_LINE.match(line):
                    hunk['lines'].append(('del', DEL_LINE.match(line).group(1)))
                    file_diff['stats']['deletions'] += 1
                elif CONTEXT_LINE.match(line):
                    hunk['lines'].append(('ctx', CONTEXT_LINE.match(line).group(1)))
                    file_diff['stats']['context'] += 1
                
                i += 1
            
            file_diff['hunks'].append(hunk)
        
        i += 1
    
    return file_diff


def extract_patch_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from patch/diff file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    lines = content.split('\n')
    
    metadata = {
        'file': Path(file_path).name,
        'size_bytes': len(content),
        'line_count': len(lines),
        'format': detect_patch_format(lines),
        'files': [],
        'total_stats': {'additions': 0, 'deletions': 0, 'files_changed': 0}
    }
    
    # Parse git metadata if present
    if metadata['format'] == 'git':
        metadata['git'] = parse_git_metadata(lines)
    
    # Find all file diffs
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Start of file diff
        if UNIFIED_HEADER.match(line) or line.startswith('diff --git'):
            file_diff = parse_file_diff(lines, i)
            if file_diff and (file_diff['old_file'] or file_diff['new_file']):
                metadata['files'].append(file_diff)
                metadata['total_stats']['additions'] += file_diff['stats']['additions']
                metadata['total_stats']['deletions'] += file_diff['stats']['deletions']
                metadata['total_stats']['files_changed'] += 1
                
                # Skip to next file
                while i < len(lines) and not (UNIFIED_HEADER.match(lines[i]) or 
                                             lines[i].startswith('diff --git')):
                    i += 1
                continue
        
        i += 1
    
    return metadata


def print_metadata(metadata: Dict[str, Any]):
    """Print extracted metadata in readable format"""
    
    if 'error' in metadata:
        print(f"Error: {metadata['error']}")
        return
    
    print(f"File: {metadata['file']}")
    print(f"Size: {metadata['size_bytes']:,} bytes ({metadata['line_count']:,} lines)")
    print(f"Format: {metadata['format']}")
    
    # Git metadata
    if 'git' in metadata:
        git = metadata['git']
        print(f"\nGit Patch:")
        if 'commit' in git:
            print(f"  Commit: {git['commit'][:12]}...")
        if 'author' in git:
            print(f"  Author: {git['author']}")
        if 'date' in git:
            print(f"  Date: {git['date']}")
        if 'subject' in git:
            subject = git['subject']
            if len(subject) > 80:
                subject = subject[:77] + '...'
            print(f"  Subject: {subject}")
    
    # Overall statistics
    stats = metadata['total_stats']
    print(f"\nOverall Statistics:")
    print(f"  Files changed: {stats['files_changed']}")
    print(f"  Insertions: +{stats['additions']} lines")
    print(f"  Deletions: -{stats['deletions']} lines")
    print(f"  Net change: {stats['additions'] - stats['deletions']:+d} lines")
    
    # Per-file details
    if metadata['files']:
        print(f"\nFiles Modified ({len(metadata['files'])} files):")
        
        for i, file_diff in enumerate(metadata['files'][:10], 1):
            old_file = file_diff['old_file'] or '(new file)'
            new_file = file_diff['new_file'] or '(deleted)'
            
            # Shorten paths
            if old_file.startswith('a/'):
                old_file = old_file[2:]
            if new_file.startswith('b/'):
                new_file = new_file[2:]
            
            print(f"\n  {i}. {old_file}")
            if old_file != new_file:
                print(f"     → {new_file}")
            
            # Metadata
            if file_diff['metadata']:
                meta = file_diff['metadata']
                if meta.get('new_file'):
                    print(f"     [NEW FILE, mode {meta.get('mode', 'unknown')}]")
                elif meta.get('deleted_file'):
                    print(f"     [DELETED, was mode {meta.get('mode', 'unknown')}]")
                elif 'rename_from' in meta:
                    print(f"     [RENAMED from {meta['rename_from']}]")
                    if 'similarity' in meta:
                        print(f"     [Similarity: {meta['similarity']}%]")
            
            # Statistics
            fstats = file_diff['stats']
            print(f"     Changes: +{fstats['additions']} -{fstats['deletions']} "
                  f"({len(file_diff['hunks'])} hunks)")
            
            # Show first hunk summary
            if file_diff['hunks']:
                hunk = file_diff['hunks'][0]
                context = hunk['context']
                if context:
                    if len(context) > 60:
                        context = context[:57] + '...'
                    print(f"     First hunk: @@ -{hunk['old_start']},{hunk['old_count']} "
                          f"+{hunk['new_start']},{hunk['new_count']} @@ {context}")
        
        if len(metadata['files']) > 10:
            print(f"\n  ... and {len(metadata['files']) - 10} more files")


def main():
    if len(sys.argv) != 2:
        print("Usage: python patch_extractor.py <file.patch|file.diff>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    metadata = extract_patch_metadata(file_path)
    print_metadata(metadata)


if __name__ == '__main__':
    main()
