#!/usr/bin/env python3
"""
PO/POT (Portable Object) Translation Format Extractor - PaniniFS v3.46

This extractor analyzes GNU gettext Portable Object translation files.
PO/POT files are used for software internationalization (i18n) and localization (l10n).

Format Structure:
- Header: Project metadata, translator info, plural forms
- Entries: Translation units with msgid/msgstr pairs
- Comments: Translator comments, extracted comments, references, flags

Entry Types:
- msgid: Original string (source language)
- msgstr: Translated string (target language)
- msgid_plural: Plural form of original string
- msgstr[n]: Translated plural forms (msgstr[0], msgstr[1], ...)
- msgctxt: Message context (disambiguate identical strings)

Comment Types:
- # translator comment
- #. extracted comment (from source code)
- #: reference (source file:line)
- #, flags (fuzzy, c-format, python-format, kde-format, no-wrap, etc.)
- #| previous msgid/msgctxt (for fuzzy entries)
- #~ obsolete entry (removed from source)

Special Features:
- Plural forms: nplurals=N; plural=EXPRESSION;
- Format specifiers: %s, %d, {0}, etc.
- Context strings: msgctxt for disambiguation
- Fuzzy translations: Need review (#, fuzzy)
- Obsolete entries: Removed strings (#~)

File Types:
- .po: Translation file (specific language)
- .pot: Template file (no translations, source strings only)
- .mo: Compiled binary format (not covered here)

Common Tools:
- msgfmt: Compile PO to MO
- msgmerge: Update PO from POT
- msginit: Create new PO from POT
- xgettext: Extract strings from source
- poedit: GUI editor

This extractor provides:
- Header metadata (project, translator, language, plural forms)
- Entry statistics (translated, untranslated, fuzzy, obsolete)
- Context usage analysis
- Plural form detection
- Format specifier analysis
- Translation coverage percentage
- Reference statistics
- Flag analysis

Author: PaniniFS Research Team
Version: 3.46
Target: PO/POT files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class POExtractor:
    """Extract metadata from PO/POT (Portable Object) translation files."""
    
    # Entry start patterns
    MSGID_PATTERN = re.compile(r'^msgid\s+"(.*)"$')
    MSGSTR_PATTERN = re.compile(r'^msgstr\s+"(.*)"$')
    MSGCTXT_PATTERN = re.compile(r'^msgctxt\s+"(.*)"$')
    MSGID_PLURAL_PATTERN = re.compile(r'^msgid_plural\s+"(.*)"$')
    MSGSTR_PLURAL_PATTERN = re.compile(r'^msgstr\[(\d+)\]\s+"(.*)"$')
    
    # Comment patterns
    TRANSLATOR_COMMENT = re.compile(r'^#\s+(.*)$')
    EXTRACTED_COMMENT = re.compile(r'^#\.\s+(.*)$')
    REFERENCE = re.compile(r'^#:\s+(.*)$')
    FLAG = re.compile(r'^#,\s+(.*)$')
    PREVIOUS = re.compile(r'^#\|\s+(.*)$')
    OBSOLETE = re.compile(r'^#~\s+(.*)$')
    
    # Continuation line
    CONTINUATION = re.compile(r'^"(.*)"$')
    
    # Header fields
    HEADER_FIELDS = [
        'Project-Id-Version',
        'Report-Msgid-Bugs-To',
        'POT-Creation-Date',
        'PO-Revision-Date',
        'Last-Translator',
        'Language-Team',
        'Language',
        'MIME-Version',
        'Content-Type',
        'Content-Transfer-Encoding',
        'Plural-Forms',
        'X-Generator',
        'X-Accelerator-Marker',
    ]
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the PO/POT file."""
        try:
            # Read file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            metadata = {
                "format": "PO/POT (Portable Object)",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "file_type": "POT" if self.file_path.suffix == '.pot' else "PO",
            }
            
            # Parse entries
            entries = self._parse_entries(lines)
            
            # Extract header
            if entries and entries[0]['msgid'] == '':
                header = self._parse_header(entries[0]['msgstr'])
                metadata["header"] = header
                entries = entries[1:]  # Remove header entry
            
            # Analyze entries
            analysis = self._analyze_entries(entries)
            metadata.update(analysis)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "PO/POT (Portable Object)",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_entries(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse PO file into entries."""
        entries = []
        current_entry = None
        current_field = None
        
        for line in lines:
            line = line.rstrip('\n')
            
            # Skip blank lines between entries
            if not line.strip():
                if current_entry:
                    entries.append(current_entry)
                    current_entry = None
                    current_field = None
                continue
            
            # Start new entry if needed
            if current_entry is None:
                current_entry = {
                    'msgid': '',
                    'msgstr': '',
                    'comments': [],
                    'references': [],
                    'flags': [],
                }
            
            # Check for msgctxt
            match = self.MSGCTXT_PATTERN.match(line)
            if match:
                current_entry['msgctxt'] = match.group(1)
                current_field = 'msgctxt'
                continue
            
            # Check for msgid
            match = self.MSGID_PATTERN.match(line)
            if match:
                current_entry['msgid'] = match.group(1)
                current_field = 'msgid'
                continue
            
            # Check for msgid_plural
            match = self.MSGID_PLURAL_PATTERN.match(line)
            if match:
                current_entry['msgid_plural'] = match.group(1)
                current_field = 'msgid_plural'
                continue
            
            # Check for msgstr
            match = self.MSGSTR_PATTERN.match(line)
            if match:
                current_entry['msgstr'] = match.group(1)
                current_field = 'msgstr'
                continue
            
            # Check for msgstr[n]
            match = self.MSGSTR_PLURAL_PATTERN.match(line)
            if match:
                index = int(match.group(1))
                if 'msgstr_plural' not in current_entry:
                    current_entry['msgstr_plural'] = {}
                current_entry['msgstr_plural'][index] = match.group(2)
                current_field = f'msgstr[{index}]'
                continue
            
            # Check for comments
            match = self.TRANSLATOR_COMMENT.match(line)
            if match:
                current_entry['comments'].append(match.group(1))
                current_field = None
                continue
            
            match = self.EXTRACTED_COMMENT.match(line)
            if match:
                current_entry['comments'].append(f"[extracted] {match.group(1)}")
                current_field = None
                continue
            
            match = self.REFERENCE.match(line)
            if match:
                current_entry['references'].append(match.group(1))
                current_field = None
                continue
            
            match = self.FLAG.match(line)
            if match:
                flags = [f.strip() for f in match.group(1).split(',')]
                current_entry['flags'].extend(flags)
                current_field = None
                continue
            
            match = self.OBSOLETE.match(line)
            if match:
                current_entry['obsolete'] = True
                current_field = None
                continue
            
            # Check for continuation line
            match = self.CONTINUATION.match(line)
            if match and current_field:
                # Append to current field
                if current_field.startswith('msgstr['):
                    index = int(current_field[7:-1])
                    current_entry['msgstr_plural'][index] += match.group(1)
                elif current_field in current_entry:
                    current_entry[current_field] += match.group(1)
        
        # Don't forget last entry
        if current_entry:
            entries.append(current_entry)
        
        return entries
    
    def _parse_header(self, header_str: str) -> Dict[str, str]:
        """Parse header string into fields."""
        header = {}
        
        # Split by \n
        lines = header_str.split('\\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Split by first colon
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                header[key] = value
        
        return header
    
    def _analyze_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze translation entries."""
        result = {}
        
        # Count statistics
        total = len(entries)
        translated = 0
        untranslated = 0
        fuzzy = 0
        obsolete = 0
        with_context = 0
        with_plural = 0
        
        all_flags: List[str] = []
        reference_count = 0
        
        for entry in entries:
            # Check if translated
            msgstr = entry.get('msgstr', '')
            msgstr_plural = entry.get('msgstr_plural', {})
            
            if entry.get('obsolete'):
                obsolete += 1
            elif 'fuzzy' in entry.get('flags', []):
                fuzzy += 1
            elif msgstr or msgstr_plural:
                translated += 1
            else:
                untranslated += 1
            
            # Context
            if 'msgctxt' in entry:
                with_context += 1
            
            # Plural
            if 'msgid_plural' in entry:
                with_plural += 1
            
            # Flags
            all_flags.extend(entry.get('flags', []))
            
            # References
            reference_count += len(entry.get('references', []))
        
        result["entry_statistics"] = {
            "total_entries": total,
            "translated": translated,
            "untranslated": untranslated,
            "fuzzy": fuzzy,
            "obsolete": obsolete,
        }
        
        if total > 0:
            coverage = (translated / total) * 100
            result["translation_coverage_percent"] = round(coverage, 1)
        
        result["features"] = {
            "entries_with_context": with_context,
            "entries_with_plural": with_plural,
            "total_references": reference_count,
        }
        
        # Flag analysis
        if all_flags:
            flag_counts = {}
            for flag in all_flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
            
            result["flags"] = {
                "unique_flags": len(flag_counts),
                "flag_counts": dict(sorted(flag_counts.items(), key=lambda x: -x[1])[:10]),
            }
        
        # Sample entries
        if entries:
            samples = []
            for entry in entries[:3]:
                sample = {
                    "msgid": entry['msgid'][:100] if entry['msgid'] else '',
                }
                if 'msgctxt' in entry:
                    sample['msgctxt'] = entry['msgctxt'][:50]
                if entry.get('msgstr'):
                    sample['msgstr'] = entry['msgstr'][:100]
                samples.append(sample)
            
            result["entry_samples"] = samples
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: po_extractor.py <po_or_pot_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = POExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
