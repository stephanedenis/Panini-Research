#!/usr/bin/env python3
"""
Shell Script Extractor - PaniniFS v3.45

This extractor analyzes shell scripts (.sh, executable shell scripts).
Shell scripts are text files containing commands for Unix/Linux shell interpreters
(bash, sh, zsh, ksh, csh, etc.).

Script Structure:
- Shebang line: #!/path/to/interpreter
- Comments: # comment
- Variables: VAR=value, $VAR, ${VAR}
- Control structures: if/then/else/fi, for/do/done, while/do/done, case/esac
- Functions: function_name() { ... } or function function_name { ... }
- Commands: Built-in and external commands

Common Interpreters:
- bash: Bourne-Again Shell (most common)
- sh: POSIX shell / Bourne shell
- zsh: Z shell (enhanced bash)
- ksh: Korn shell
- csh/tcsh: C shell
- fish: Friendly Interactive Shell
- dash: Debian Almquist Shell (fast, POSIX)

Script Categories:
- System initialization: /etc/init.d/, systemd scripts
- Package management: RPM/DEB scripts
- Build scripts: configure, make wrappers
- Utility scripts: wrappers, helpers
- User scripts: custom automation

Features Analyzed:
- Shebang interpreter detection
- Variable definitions and usage
- Function definitions
- Control structures (if, for, while, case)
- External command invocations
- Error handling (set -e, trap)
- Sourcing other scripts (source, .)
- Here documents (<<EOF)
- Pipes and redirections
- Comment density

This extractor provides:
- Interpreter identification
- Script type classification
- Line counts (total, code, comments, blank)
- Variable analysis
- Function counting
- Control structure analysis
- Command usage patterns
- Error handling detection
- Code complexity metrics

Author: PaniniFS Research Team
Version: 3.45
Target: Shell scripts in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Set
import re

class ShellScriptExtractor:
    """Extract metadata from shell scripts."""
    
    # Common shell interpreters
    INTERPRETERS = {
        'bash': 'Bourne-Again Shell',
        'sh': 'POSIX Shell / Bourne Shell',
        'zsh': 'Z Shell',
        'ksh': 'Korn Shell',
        'csh': 'C Shell',
        'tcsh': 'TENEX C Shell',
        'fish': 'Friendly Interactive Shell',
        'dash': 'Debian Almquist Shell',
        'ash': 'Almquist Shell',
    }
    
    # Control structure patterns
    CONTROL_PATTERNS = {
        'if': re.compile(r'\bif\s+'),
        'for': re.compile(r'\bfor\s+\w+\s+in\s+'),
        'while': re.compile(r'\bwhile\s+'),
        'case': re.compile(r'\bcase\s+'),
        'function': re.compile(r'(?:function\s+\w+|^\s*\w+\s*\(\s*\))'),
    }
    
    # Variable patterns
    VAR_DEFINITION = re.compile(r'^\s*([A-Z_][A-Z0-9_]*)\s*=')
    VAR_USAGE = re.compile(r'\$\{?([A-Z_][A-Z0-9_]*)\}?')
    
    # Special constructs
    HERE_DOC = re.compile(r'<<-?\s*[\'"]?(\w+)[\'"]?')
    SOURCE = re.compile(r'(?:source|\.)[\s]+[\'"]([\w/.]+)[\'"]')
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the shell script."""
        try:
            # Try to read as text
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            metadata = {
                "format": "Shell Script",
                "file_path": str(self.file_path),
                "file_size": self.file_path.stat().st_size,
                "is_executable": self.file_path.stat().st_mode & 0o111 != 0,
            }
            
            # Parse shebang
            shebang_info = self._parse_shebang(lines)
            if shebang_info:
                metadata.update(shebang_info)
            
            # Analyze script content
            analysis = self._analyze_content(lines)
            metadata.update(analysis)
            
            return metadata
            
        except Exception as e:
            return {
                "format": "Shell Script",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _parse_shebang(self, lines: List[str]) -> Dict[str, Any]:
        """Parse shebang line to identify interpreter."""
        if not lines or not lines[0].startswith('#!'):
            return {"has_shebang": False}
        
        shebang = lines[0].strip()
        result = {
            "has_shebang": True,
            "shebang": shebang,
        }
        
        # Extract interpreter
        parts = shebang[2:].strip().split()
        if not parts:
            return result
        
        interpreter_path = parts[0]
        result["interpreter_path"] = interpreter_path
        
        # Identify interpreter type
        interpreter_name = Path(interpreter_path).name
        
        # Handle env wrapper
        if interpreter_name == 'env' and len(parts) > 1:
            interpreter_name = parts[1]
            result["uses_env"] = True
        
        result["interpreter"] = interpreter_name
        
        if interpreter_name in self.INTERPRETERS:
            result["interpreter_description"] = self.INTERPRETERS[interpreter_name]
        
        # Extract interpreter options
        if len(parts) > 1:
            options = parts[1:] if not result.get("uses_env") else parts[2:]
            if options:
                result["interpreter_options"] = options
        
        return result
    
    def _analyze_content(self, lines: List[str]) -> Dict[str, Any]:
        """Analyze script content for structure and patterns."""
        result = {}
        
        # Line counting
        total_lines = len(lines)
        comment_lines = 0
        blank_lines = 0
        code_lines = 0
        
        # Variables and functions
        variables_defined: Set[str] = set()
        variables_used: Set[str] = set()
        functions_defined: List[str] = []
        
        # Control structures
        control_counts = {
            'if': 0,
            'for': 0,
            'while': 0,
            'case': 0,
            'function': 0,
        }
        
        # Special features
        here_docs: List[str] = []
        sourced_files: List[str] = []
        has_set_e = False
        has_trap = False
        has_pipefail = False
        
        in_here_doc = False
        here_doc_delimiter = None
        
        for line in lines:
            stripped = line.strip()
            
            # Blank lines
            if not stripped:
                blank_lines += 1
                continue
            
            # Handle here documents
            if in_here_doc:
                if stripped == here_doc_delimiter:
                    in_here_doc = False
                    here_doc_delimiter = None
                continue
            
            # Check for here document start
            here_match = self.HERE_DOC.search(line)
            if here_match:
                delimiter = here_match.group(1)
                here_docs.append(delimiter)
                in_here_doc = True
                here_doc_delimiter = delimiter
            
            # Comment lines
            if stripped.startswith('#'):
                # Skip shebang
                if not stripped.startswith('#!'):
                    comment_lines += 1
                continue
            
            # Code lines
            code_lines += 1
            
            # Variable definitions
            var_def = self.VAR_DEFINITION.match(stripped)
            if var_def:
                variables_defined.add(var_def.group(1))
            
            # Variable usage
            for var_match in self.VAR_USAGE.finditer(line):
                variables_used.add(var_match.group(1))
            
            # Control structures
            for struct_type, pattern in self.CONTROL_PATTERNS.items():
                if pattern.search(line):
                    control_counts[struct_type] += 1
                    
                    # Extract function names
                    if struct_type == 'function':
                        func_match = re.search(r'function\s+(\w+)|^\s*(\w+)\s*\(\s*\)', line)
                        if func_match:
                            func_name = func_match.group(1) or func_match.group(2)
                            if func_name and func_name not in functions_defined:
                                functions_defined.append(func_name)
            
            # Source/include detection
            source_match = self.SOURCE.search(line)
            if source_match:
                sourced_files.append(source_match.group(1))
            
            # Error handling
            if 'set -e' in line or 'set -o errexit' in line:
                has_set_e = True
            if 'set -o pipefail' in line:
                has_pipefail = True
            if re.search(r'\btrap\s+', line):
                has_trap = True
        
        # Build result
        result["line_counts"] = {
            "total": total_lines,
            "code": code_lines,
            "comments": comment_lines,
            "blank": blank_lines,
        }
        
        if code_lines > 0:
            result["comment_density"] = round(comment_lines / code_lines, 3)
        
        result["variables"] = {
            "defined_count": len(variables_defined),
            "used_count": len(variables_used),
            "defined_samples": sorted(list(variables_defined))[:20],
            "used_samples": sorted(list(variables_used))[:20],
        }
        
        result["functions"] = {
            "count": len(functions_defined),
            "names": functions_defined[:20],
        }
        
        result["control_structures"] = {
            k: v for k, v in control_counts.items() if v > 0
        }
        
        if here_docs:
            result["here_documents"] = {
                "count": len(here_docs),
                "delimiters": here_docs[:10],
            }
        
        if sourced_files:
            result["sourced_files"] = {
                "count": len(sourced_files),
                "files": sourced_files[:10],
            }
        
        result["error_handling"] = {
            "has_set_e": has_set_e,
            "has_pipefail": has_pipefail,
            "has_trap": has_trap,
        }
        
        # Calculate complexity score
        complexity = (
            control_counts['if'] * 1 +
            control_counts['for'] * 2 +
            control_counts['while'] * 2 +
            control_counts['case'] * 3 +
            control_counts['function'] * 5
        )
        result["complexity_score"] = complexity
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: shell_extractor.py <shell_script>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = ShellScriptExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
