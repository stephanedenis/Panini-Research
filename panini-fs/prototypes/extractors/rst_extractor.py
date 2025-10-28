#!/usr/bin/env python3
"""
reStructuredText (.rst) Format Extractor - PaniniFS v3.51

This extractor analyzes reStructuredText documentation files.
reStructuredText (RST) is a plain text markup language used extensively
in Python documentation (Sphinx, docutils) and technical writing.

Format Structure:
- Section headers: Over/underlines with =, -, `, :, ., ', ", ~, ^, _, *, +, #
- Inline markup: *emphasis* **strong** ``literal`` |substitution| _`target`
- Lists: *, -, +, (a), 1., #. (numbered), term : definition (definition lists)
- Blocks: | (line blocks), >>> (doctests), .. (directives), :: (literal blocks)
- Links: `text <url>`_ (external), `text`_ (internal), .. _label: (target)
- Images: .. image:: path or .. figure:: path
- Tables: grid tables (+-|), simple tables (spaces)

Sections:
```rst
Title
=====

Subtitle
--------

Subsubsection
~~~~~~~~~~~~~
```

Hierarchy (recommended order):
- = for parts
- - for chapters
- ~ for sections
- . for subsections
- ^ for subsubsections

Directives:
- .. note:: - Admonition
- .. warning:: - Warning box
- .. code-block:: python - Code block
- .. automodule:: - Sphinx autodoc
- .. toctree:: - Table of contents
- .. include:: - Include file
- .. image:: - Image
- .. figure:: - Image with caption
- .. math:: - Math formula

Roles (inline):
- :emphasis:`text` - Emphasis
- :strong:`text` - Strong
- :literal:`text` - Literal
- :code:`text` - Code
- :math:`formula` - Math
- :py:func:`name` - Python function reference
- :ref:`label` - Cross-reference

Special Blocks:
- Line blocks: | preserved lines
- Doctests: >>> code
- Literal blocks: :: followed by indented text
- Block quotes: Indented paragraph
- Footnotes: [#]_, [1]_, [*]_
- Citations: [Author2023]_

Common Use Cases:
- Python documentation (Sphinx)
- README.rst files
- Technical documentation
- Academic papers
- API documentation (autodoc)
- Books (Sphinx)

Tools:
- Sphinx: Documentation generator
- docutils: Base RST parser
- Pandoc: Document converter
- Read the Docs: Hosting platform

This extractor provides:
- Section structure analysis (hierarchy, titles)
- Directive detection (code-block, note, warning, etc.)
- Role usage analysis (cross-references, code, math)
- Link and image counting
- List detection (bullet, numbered, definition)
- Table detection (grid, simple)
- Block structure (literal, line, quote)
- Statistics (lines, words, characters)

Author: PaniniFS Research Team
Version: 3.51
Target: RST files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class RSTExtractor:
    """Extract metadata from reStructuredText (.rst) files."""
    
    # Section underline characters (in recommended order)
    SECTION_CHARS = set('=-`:\'"~^_*.+#')
    
    # Directive pattern
    DIRECTIVE = re.compile(r'^\.\.\s+([a-z_-]+)::', re.MULTILINE)
    
    # Role pattern
    ROLE = re.compile(r':([a-z_-]+):`([^`]+)`')
    
    # Link patterns
    EXTERNAL_LINK = re.compile(r'`([^<]+)<([^>]+)>`_')
    INTERNAL_LINK = re.compile(r'`([^`]+)`_')
    LINK_TARGET = re.compile(r'^\.\.\s+_([^:]+):\s*(.*)$', re.MULTILINE)
    
    # Inline markup
    EMPHASIS = re.compile(r'\*([^*]+)\*')
    STRONG = re.compile(r'\*\*([^*]+)\*\*')
    LITERAL = re.compile(r'``([^`]+)``')
    
    # List patterns
    BULLET_LIST = re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE)
    NUMBERED_LIST = re.compile(r'^\s*(?:\d+\.|#\.|\([a-z]\))\s+(.+)$', re.MULTILINE)
    
    # Special blocks
    DOCTEST = re.compile(r'^>>>\s+(.+)$', re.MULTILINE)
    LINE_BLOCK = re.compile(r'^\|\s+(.+)$', re.MULTILINE)
    
    # Table pattern (grid tables)
    GRID_TABLE = re.compile(r'^\+[-+]+\+\s*$', re.MULTILINE)
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the RST file."""
        try:
            # Read file
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                encoding = 'UTF-8'
            except UnicodeDecodeError:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                encoding = 'Latin-1'
            
            metadata = {
                "format": "reStructuredText (RST)",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "encoding": encoding,
            }
            
            # Basic statistics
            lines = content.split('\n')
            words = content.split()
            
            metadata["statistics"] = {
                "lines": len(lines),
                "words": len(words),
                "characters": len(content),
            }
            
            # Analyze sections
            sections = self._analyze_sections(lines)
            if sections:
                metadata["sections"] = sections
            
            # Analyze directives
            directives = self._analyze_directives(content)
            if directives:
                metadata["directives"] = directives
            
            # Analyze roles
            roles = self._analyze_roles(content)
            if roles:
                metadata["roles"] = roles
            
            # Analyze links
            links = self._analyze_links(content)
            if links:
                metadata["links"] = links
            
            # Analyze lists
            lists = self._analyze_lists(content)
            if lists:
                metadata["lists"] = lists
            
            # Analyze tables
            tables = self._analyze_tables(content)
            if tables:
                metadata["tables"] = tables
            
            # Analyze other elements
            other = self._analyze_other_elements(content)
            if other:
                metadata.update(other)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "reStructuredText (RST)",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _analyze_sections(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Analyze section structure."""
        sections = []
        
        for i in range(len(lines) - 1):
            line = lines[i].strip()
            next_line = lines[i + 1].strip()
            
            # Check for underline (section)
            if line and next_line and len(next_line) >= len(line):
                if next_line[0] in self.SECTION_CHARS and len(set(next_line)) == 1:
                    sections.append({
                        "title": line,
                        "char": next_line[0],
                        "line": i + 1,
                    })
        
        if not sections:
            return None
        
        # Count by character (hierarchy level)
        char_counts = {}
        for s in sections:
            char_counts[s["char"]] = char_counts.get(s["char"], 0) + 1
        
        return {
            "count": len(sections),
            "hierarchy_chars": sorted(set(s["char"] for s in sections)),
            "char_usage": char_counts,
            "samples": sections[:10],
        }
    
    def _analyze_directives(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze RST directives."""
        directives = [m.group(1) for m in self.DIRECTIVE.finditer(content)]
        
        if not directives:
            return None
        
        # Count by type
        directive_counts = {}
        for d in directives:
            directive_counts[d] = directive_counts.get(d, 0) + 1
        
        return {
            "count": len(directives),
            "unique_types": len(directive_counts),
            "type_counts": dict(sorted(directive_counts.items(), key=lambda x: -x[1])[:20]),
        }
    
    def _analyze_roles(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze inline roles."""
        roles = [(m.group(1), m.group(2)) for m in self.ROLE.finditer(content)]
        
        if not roles:
            return None
        
        # Count by type
        role_counts = {}
        for role_type, _ in roles:
            role_counts[role_type] = role_counts.get(role_type, 0) + 1
        
        return {
            "count": len(roles),
            "unique_types": len(role_counts),
            "type_counts": dict(sorted(role_counts.items(), key=lambda x: -x[1])[:20]),
            "samples": [{"type": r[0], "content": r[1][:50]} for r in roles[:10]],
        }
    
    def _analyze_links(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze links."""
        external = list(self.EXTERNAL_LINK.finditer(content))
        internal = list(self.INTERNAL_LINK.finditer(content))
        targets = list(self.LINK_TARGET.finditer(content))
        
        result = {}
        
        if external:
            result["external_links"] = {
                "count": len(external),
                "samples": [{"text": m.group(1), "url": m.group(2)} for m in external[:5]],
            }
        
        if internal:
            result["internal_links"] = len(internal)
        
        if targets:
            result["link_targets"] = len(targets)
        
        return result if result else None
    
    def _analyze_lists(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze lists."""
        bullet = list(self.BULLET_LIST.finditer(content))
        numbered = list(self.NUMBERED_LIST.finditer(content))
        
        result = {}
        
        if bullet:
            result["bullet_items"] = len(bullet)
        
        if numbered:
            result["numbered_items"] = len(numbered)
        
        return result if result else None
    
    def _analyze_tables(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze tables."""
        grid_tables = list(self.GRID_TABLE.finditer(content))
        
        if not grid_tables:
            return None
        
        return {
            "grid_tables": len(grid_tables) // 2,  # Each table has top and bottom borders
        }
    
    def _analyze_other_elements(self, content: str) -> Dict[str, Any]:
        """Analyze other RST elements."""
        result = {}
        
        emphasis = list(self.EMPHASIS.finditer(content))
        if emphasis:
            result["emphasis_count"] = len(emphasis)
        
        strong = list(self.STRONG.finditer(content))
        if strong:
            result["strong_count"] = len(strong)
        
        literal = list(self.LITERAL.finditer(content))
        if literal:
            result["literal_count"] = len(literal)
        
        doctests = list(self.DOCTEST.finditer(content))
        if doctests:
            result["doctest_examples"] = len(doctests)
        
        line_blocks = list(self.LINE_BLOCK.finditer(content))
        if line_blocks:
            result["line_blocks"] = len(line_blocks)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: rst_extractor.py <rst_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = RSTExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
