#!/usr/bin/env python3
"""
Markdown (.md) Format Extractor - PaniniFS v3.50

This extractor analyzes Markdown documentation files.
Markdown is a lightweight markup language with plain text formatting syntax,
widely used for documentation, README files, and content management.

Format Variants:
- CommonMark: Standard specification
- GitHub Flavored Markdown (GFM): GitHub extensions
- MultiMarkdown: Extended features
- Pandoc Markdown: Academic extensions
- Original Markdown: John Gruber's 2004 spec

Basic Syntax:
- Headers: # H1, ## H2, ### H3, etc. (ATX) or underlines (Setext)
- Emphasis: *italic* _italic_ **bold** __bold__ ***bold italic***
- Lists: - bullet, * bullet, + bullet, 1. numbered
- Links: [text](url) or [text][ref]
- Images: ![alt](url)
- Code: `inline` or ```language blocks
- Blockquotes: > quote
- Horizontal rules: ---, ***, ___

Extended Syntax (GFM):
- Tables: | Header | Header |
- Task lists: - [ ] unchecked, - [x] checked
- Strikethrough: ~~deleted~~
- Autolinks: <https://example.com>
- Footnotes: [^1] reference
- Definition lists: term : definition
- Emoji: :smile:
- Math: $inline$ or $$block$$

Structure Elements:
- Front matter: YAML/TOML metadata at top (---yaml---)
- TOC: Table of contents (often auto-generated)
- Badges: ![badge](url) (CI/CD status, version, etc.)
- Sections: Hierarchical heading structure
- Code blocks: Language-tagged fenced blocks
- Admonitions: !!! note, warning, etc. (MkDocs)

Common Use Cases:
- README.md: Project documentation
- CONTRIBUTING.md: Contribution guidelines
- CHANGELOG.md: Version history
- LICENSE.md: Software license
- Wiki pages: GitHub/GitLab wikis
- Blog posts: Static site generators
- Technical documentation: MkDocs, Docusaurus
- Academic papers: Pandoc conversion

Popular Tools:
- Parsers: marked.js, markdown-it, CommonMark
- Generators: MkDocs, Jekyll, Hugo, Gatsby
- Editors: Typora, Mark Text, VS Code
- Converters: Pandoc (MD → PDF, DOCX, HTML)

This extractor provides:
- Heading structure analysis (levels, hierarchy)
- Content statistics (lines, words, characters)
- Link analysis (internal, external, images)
- Code block detection (languages, inline/fenced)
- List analysis (ordered, unordered, task lists)
- Front matter extraction (YAML/TOML)
- GFM feature detection (tables, task lists, strikethrough)
- Badge counting (CI status, shields.io)
- Blockquote and emphasis counting

Author: PaniniFS Research Team
Version: 3.50
Target: Markdown files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class MarkdownExtractor:
    """Extract metadata from Markdown (.md) files."""
    
    # Header patterns
    ATX_HEADER = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    SETEXT_H1 = re.compile(r'^(.+)\n=+\s*$', re.MULTILINE)
    SETEXT_H2 = re.compile(r'^(.+)\n-+\s*$', re.MULTILINE)
    
    # Link patterns
    LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    AUTOLINK = re.compile(r'<(https?://[^>]+)>')
    
    # Code patterns
    INLINE_CODE = re.compile(r'`([^`]+)`')
    FENCED_CODE = re.compile(r'^```(\w*)\n(.*?)^```', re.MULTILINE | re.DOTALL)
    
    # List patterns
    UNORDERED_LIST = re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE)
    ORDERED_LIST = re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE)
    TASK_LIST = re.compile(r'^\s*[-*+]\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)
    
    # Other patterns
    BLOCKQUOTE = re.compile(r'^>\s+(.+)$', re.MULTILINE)
    HORIZONTAL_RULE = re.compile(r'^(\*{3,}|-{3,}|_{3,})\s*$', re.MULTILINE)
    BOLD = re.compile(r'\*\*([^*]+)\*\*|__([^_]+)__')
    ITALIC = re.compile(r'\*([^*]+)\*|_([^_]+)_')
    STRIKETHROUGH = re.compile(r'~~([^~]+)~~')
    TABLE = re.compile(r'^\|.+\|\s*$\n^\|[-:\s|]+\|\s*$', re.MULTILINE)
    
    # Front matter
    YAML_FRONT_MATTER = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
    TOML_FRONT_MATTER = re.compile(r'^\+\+\+\n(.*?)\n\+\+\+\n', re.DOTALL)
    
    # Badge
    BADGE = re.compile(r'!\[([^\]]*)\]\(https?://[^)]*(?:shields\.io|badge|svg)[^)]*\)')
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the Markdown file."""
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
                "format": "Markdown",
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
                "characters_no_whitespace": len(content.replace(' ', '').replace('\n', '')),
            }
            
            # Extract front matter
            front_matter = self._extract_front_matter(content)
            if front_matter:
                metadata["front_matter"] = front_matter
                # Remove front matter from content for analysis
                if front_matter["type"] == "YAML":
                    content = self.YAML_FRONT_MATTER.sub('', content, count=1)
                else:
                    content = self.TOML_FRONT_MATTER.sub('', content, count=1)
            
            # Analyze structure
            headings = self._analyze_headings(content)
            if headings:
                metadata["headings"] = headings
            
            # Analyze links
            links = self._analyze_links(content)
            if links:
                metadata["links"] = links
            
            # Analyze code
            code = self._analyze_code(content)
            if code:
                metadata["code"] = code
            
            # Analyze lists
            lists = self._analyze_lists(content)
            if lists:
                metadata["lists"] = lists
            
            # Analyze other elements
            other = self._analyze_other_elements(content)
            if other:
                metadata.update(other)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Markdown",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _extract_front_matter(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract YAML or TOML front matter."""
        # Try YAML
        match = self.YAML_FRONT_MATTER.match(content)
        if match:
            return {
                "type": "YAML",
                "content": match.group(1).strip(),
                "lines": len(match.group(1).strip().split('\n')),
            }
        
        # Try TOML
        match = self.TOML_FRONT_MATTER.match(content)
        if match:
            return {
                "type": "TOML",
                "content": match.group(1).strip(),
                "lines": len(match.group(1).strip().split('\n')),
            }
        
        return None
    
    def _analyze_headings(self, content: str) -> Dict[str, Any]:
        """Analyze heading structure."""
        atx_headings = []
        
        for match in self.ATX_HEADER.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            atx_headings.append({"level": level, "text": text})
        
        if not atx_headings:
            return {}
        
        # Count by level
        level_counts = {}
        for h in atx_headings:
            level_counts[h["level"]] = level_counts.get(h["level"], 0) + 1
        
        return {
            "count": len(atx_headings),
            "by_level": level_counts,
            "max_level": max(level_counts.keys()),
            "samples": atx_headings[:10],
        }
    
    def _analyze_links(self, content: str) -> Dict[str, Any]:
        """Analyze links and images."""
        links = list(self.LINK.finditer(content))
        images = list(self.IMAGE.finditer(content))
        autolinks = list(self.AUTOLINK.finditer(content))
        badges = list(self.BADGE.finditer(content))
        
        result = {}
        
        if links:
            result["links"] = {
                "count": len(links),
                "samples": [{"text": m.group(1), "url": m.group(2)} for m in links[:10]],
            }
        
        if images:
            result["images"] = {
                "count": len(images),
                "samples": [{"alt": m.group(1), "url": m.group(2)} for m in images[:10]],
            }
        
        if badges:
            result["badges"] = len(badges)
        
        return result
    
    def _analyze_code(self, content: str) -> Dict[str, Any]:
        """Analyze code blocks and inline code."""
        inline = list(self.INLINE_CODE.finditer(content))
        fenced = list(self.FENCED_CODE.finditer(content))
        
        result = {}
        
        if inline:
            result["inline_code_count"] = len(inline)
        
        if fenced:
            languages = [m.group(1) for m in fenced if m.group(1)]
            result["fenced_blocks"] = {
                "count": len(fenced),
                "languages": list(set(languages)) if languages else [],
            }
        
        return result
    
    def _analyze_lists(self, content: str) -> Dict[str, Any]:
        """Analyze list items."""
        unordered = list(self.UNORDERED_LIST.finditer(content))
        ordered = list(self.ORDERED_LIST.finditer(content))
        tasks = list(self.TASK_LIST.finditer(content))
        
        result = {}
        
        if unordered:
            result["unordered_items"] = len(unordered)
        
        if ordered:
            result["ordered_items"] = len(ordered)
        
        if tasks:
            checked = sum(1 for m in tasks if m.group(1).lower() == 'x')
            result["task_items"] = {
                "total": len(tasks),
                "checked": checked,
                "unchecked": len(tasks) - checked,
            }
        
        return result
    
    def _analyze_other_elements(self, content: str) -> Dict[str, Any]:
        """Analyze other Markdown elements."""
        result = {}
        
        blockquotes = list(self.BLOCKQUOTE.finditer(content))
        if blockquotes:
            result["blockquotes"] = len(blockquotes)
        
        hr = list(self.HORIZONTAL_RULE.finditer(content))
        if hr:
            result["horizontal_rules"] = len(hr)
        
        tables = list(self.TABLE.finditer(content))
        if tables:
            result["tables"] = len(tables)
        
        bold = list(self.BOLD.finditer(content))
        if bold:
            result["bold_count"] = len(bold)
        
        italic = list(self.ITALIC.finditer(content))
        if italic:
            result["italic_count"] = len(italic)
        
        strikethrough = list(self.STRIKETHROUGH.finditer(content))
        if strikethrough:
            result["strikethrough_count"] = len(strikethrough)
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: markdown_extractor.py <markdown_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = MarkdownExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
