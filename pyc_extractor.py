#!/usr/bin/env python3
"""
PaniniFS v3.34: PYC (Python Bytecode) Extractor
================================================

PYC - Python compiled bytecode format.

Structure (Python 3.7+):
- Magic number (4 bytes): identifies Python version
- Bit field (4 bytes): flags (hash-based, check-source, etc.)
- Hash/Timestamp (8 bytes):
  - Timestamp-based: modification time + file size
  - Hash-based: SipHash-2-4 of source code
- Code object (marshalled)

Magic numbers (examples):
- 3495 (0x0DA7): Python 3.11
- 3413 (0x0D55): Python 3.10
- 3392 (0x0D40): Python 3.9
- 3379 (0x0D33): Python 3.8
- 3394 (0x0D42): Python 3.7

Bit field flags (Python 3.7+):
- Bit 0: hash-based
- Bit 1: check-source (verify source matches hash)

Timestamp-based format:
- Bytes 4-7: modification time (Unix timestamp, little-endian)
- Bytes 8-11: file size (little-endian)

Hash-based format:
- Bytes 4-11: SipHash-2-4 of source (little-endian)

Code object (marshalled):
- Type code (1 byte): 'c' (0x63) for code objects
- argcount, kwonlyargcount, nlocals, stacksize, flags
- code (bytecode instructions)
- consts (constants tuple)
- names (names tuple)
- varnames, freevars, cellvars
- filename, name (function/module name)
- firstlineno
- linetable (line number table)

Metadata extracted:
- Python version (from magic number)
- Compilation type (hash-based or timestamp-based)
- Flags (check-source)
- Timestamp or hash value
- Module name
- Source filename
- Code statistics:
  - Number of constants
  - Number of names
  - Number of variables
  - Stack size
  - Code flags
- First line number
- Argument counts

Format: Binary, little-endian
Standard: Python internals

Author: PaniniFS Research Team
Version: 3.34
Date: 2025-01-14
"""

import sys
import struct
import marshal
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import importlib.util


class PYCExtractor:
    """Extract metadata from Python bytecode (.pyc) files."""
    
    # Python magic numbers (partial list)
    MAGIC_NUMBERS = {
        3495: "3.11",
        3494: "3.11",
        3493: "3.11",
        3492: "3.11",
        3491: "3.11",
        3485: "3.10",
        3413: "3.10",
        3412: "3.10",
        3411: "3.10",
        3392: "3.9",
        3391: "3.9",
        3390: "3.9",
        3389: "3.9",
        3379: "3.8",
        3378: "3.8",
        3377: "3.8",
        3376: "3.8",
        3375: "3.8",
        3374: "3.8",
        3373: "3.8",
        3372: "3.8",
        3371: "3.8",
        3361: "3.7",
        3351: "3.7",
        3350: "3.7",
        3349: "3.7",
        3345: "3.6",
        3344: "3.6",
        3343: "3.6",
        3342: "3.6",
        3341: "3.6",
        3340: "3.6",
        3339: "3.6",
        3320: "3.5",
        3310: "3.5"
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.raw_data: Optional[bytes] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "PYC (Python Bytecode)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "python_version": None,
            "magic_number": None,
            "compilation_type": None,
            "flags": [],
            "errors": []
        }
        
        try:
            # Read file
            with open(self.filepath, 'rb') as f:
                self.raw_data = f.read()
            
            # Parse header
            self._parse_header()
            
            # Parse code object
            self._parse_code_object()
            
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        
        return self.data
    
    def _parse_header(self):
        """Parse PYC file header."""
        if len(self.raw_data) < 16:
            raise ValueError("File too small to be valid PYC")
        
        # Magic number (2 bytes + 2 bytes padding/CRC)
        magic = struct.unpack('<H', self.raw_data[0:2])[0]
        
        self.data["magic_number"] = magic
        
        # Determine Python version
        version = self.MAGIC_NUMBERS.get(magic)
        if version:
            self.data["python_version"] = version
        else:
            self.data["python_version"] = f"Unknown (magic: {magic})"
            self.data["errors"].append(f"Unknown magic number: {magic}")
        
        # Bit field (bytes 4-7) - Python 3.7+
        if len(self.raw_data) >= 8:
            bit_field = struct.unpack('<I', self.raw_data[4:8])[0]
            
            # Check flags
            is_hash_based = bool(bit_field & 0x01)
            check_source = bool(bit_field & 0x02)
            
            if is_hash_based:
                self.data["compilation_type"] = "hash-based"
                if check_source:
                    self.data["flags"].append("check-source")
                
                # Read hash (bytes 8-15)
                if len(self.raw_data) >= 16:
                    hash_value = struct.unpack('<Q', self.raw_data[8:16])[0]
                    self.data["source_hash"] = f"0x{hash_value:016X}"
            else:
                self.data["compilation_type"] = "timestamp-based"
                
                # Read timestamp (bytes 8-11)
                if len(self.raw_data) >= 12:
                    timestamp = struct.unpack('<I', self.raw_data[8:12])[0]
                    try:
                        dt = datetime.fromtimestamp(timestamp)
                        self.data["source_timestamp"] = dt.isoformat()
                    except (ValueError, OSError):
                        self.data["source_timestamp"] = None
                
                # Read source size (bytes 12-15)
                if len(self.raw_data) >= 16:
                    source_size = struct.unpack('<I', self.raw_data[12:16])[0]
                    self.data["source_size"] = source_size
    
    def _parse_code_object(self):
        """Parse marshalled code object."""
        try:
            # Code object starts at byte 16 (after header)
            if len(self.raw_data) <= 16:
                return
            
            code_data = self.raw_data[16:]
            
            # Unmarshal code object
            try:
                code_obj = marshal.loads(code_data)
            except Exception as e:
                self.data["errors"].append(f"Marshal error: {str(e)}")
                return
            
            if not hasattr(code_obj, 'co_code'):
                return
            
            # Extract code object metadata
            code_info = {
                "name": code_obj.co_name,
                "filename": code_obj.co_filename,
                "first_line_number": code_obj.co_firstlineno,
                "argument_count": code_obj.co_argcount,
                "positional_only_arguments": getattr(code_obj, 'co_posonlyargcount', 0),
                "keyword_only_arguments": getattr(code_obj, 'co_kwonlyargcount', 0),
                "local_variables": code_obj.co_nlocals,
                "stack_size": code_obj.co_stacksize,
                "flags": code_obj.co_flags,
                "bytecode_size": len(code_obj.co_code),
                "constant_count": len(code_obj.co_consts),
                "name_count": len(code_obj.co_names),
                "variable_names_count": len(code_obj.co_varnames),
                "free_variables_count": len(code_obj.co_freevars),
                "cell_variables_count": len(code_obj.co_cellvars)
            }
            
            # Decode flags
            flag_descriptions = []
            flags = code_obj.co_flags
            
            if flags & 0x04:
                flag_descriptions.append("*args")
            if flags & 0x08:
                flag_descriptions.append("**kwargs")
            if flags & 0x20:
                flag_descriptions.append("generator")
            if flags & 0x40:
                flag_descriptions.append("no free variables")
            if flags & 0x100:
                flag_descriptions.append("coroutine")
            if flags & 0x200:
                flag_descriptions.append("iterable coroutine")
            if flags & 0x400:
                flag_descriptions.append("async generator")
            
            if flag_descriptions:
                code_info["flag_descriptions"] = flag_descriptions
            
            # Sample constants
            constants = []
            for const in code_obj.co_consts[:10]:  # First 10 constants
                if isinstance(const, (str, int, float, bool, type(None))):
                    constants.append({
                        "type": type(const).__name__,
                        "value": str(const)[:100] if isinstance(const, str) else const
                    })
                elif hasattr(const, 'co_code'):
                    # Nested code object
                    constants.append({
                        "type": "code",
                        "name": const.co_name
                    })
                else:
                    constants.append({
                        "type": type(const).__name__,
                        "value": None
                    })
            
            if constants:
                code_info["constants_sample"] = constants
            
            # Sample names (first 10)
            if code_obj.co_names:
                code_info["names_sample"] = list(code_obj.co_names[:10])
            
            # Variable names (first 10)
            if code_obj.co_varnames:
                code_info["variable_names_sample"] = list(code_obj.co_varnames[:10])
            
            self.data["code"] = code_info
            
        except Exception as e:
            self.data["errors"].append(f"Code object parse error: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python pyc_extractor.py <file.pyc>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = PYCExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
