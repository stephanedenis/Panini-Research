#!/usr/bin/env python3
"""
Java CLASS (Compiled Java Bytecode) Format Extractor - PaniniFS v3.35

This extractor analyzes Java .class files (compiled bytecode for the JVM).
It extracts metadata from the class file structure including version,
class information, constant pool, methods, fields, and attributes.

Format Structure:
1. Magic number (0xCAFEBABE - 4 bytes)
2. Minor and major version (2 + 2 bytes)
3. Constant pool count and constants
4. Access flags (2 bytes)
5. This class, super class, interfaces
6. Fields, methods, attributes

Constant Pool Types:
- CONSTANT_Utf8 (1): UTF-8 string
- CONSTANT_Integer (3): 4-byte integer
- CONSTANT_Float (4): 4-byte float
- CONSTANT_Long (5): 8-byte long
- CONSTANT_Double (6): 8-byte double
- CONSTANT_Class (7): Class reference
- CONSTANT_String (8): String reference
- CONSTANT_Fieldref (9): Field reference
- CONSTANT_Methodref (10): Method reference
- CONSTANT_InterfaceMethodref (11): Interface method reference
- CONSTANT_NameAndType (12): Name and type descriptor

Access Flags:
- ACC_PUBLIC (0x0001): public
- ACC_FINAL (0x0010): final
- ACC_SUPER (0x0020): treat superclass methods specially
- ACC_INTERFACE (0x0200): interface
- ACC_ABSTRACT (0x0400): abstract
- ACC_SYNTHETIC (0x1000): synthetic (not in source)
- ACC_ANNOTATION (0x2000): annotation type
- ACC_ENUM (0x4000): enum type

Author: PaniniFS Research Team
Version: 3.35
Target: Java bytecode files in /run/media/stephane/babba1d2-aea8-4876-ba6c-d47aa6de90d1/
"""

import struct
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class ClassExtractor:
    """Extract metadata from Java CLASS bytecode files."""
    
    # Java version mapping (major version -> Java version)
    JAVA_VERSIONS = {
        45: "1.1",
        46: "1.2",
        47: "1.3",
        48: "1.4",
        49: "1.5 (5.0)",
        50: "1.6 (6.0)",
        51: "1.7 (7.0)",
        52: "1.8 (8.0)",
        53: "9",
        54: "10",
        55: "11",
        56: "12",
        57: "13",
        58: "14",
        59: "15",
        60: "16",
        61: "17",
        62: "18",
        63: "19",
        64: "20",
        65: "21",
    }
    
    # Constant pool tags
    CONSTANT_TAGS = {
        1: "Utf8",
        3: "Integer",
        4: "Float",
        5: "Long",
        6: "Double",
        7: "Class",
        8: "String",
        9: "Fieldref",
        10: "Methodref",
        11: "InterfaceMethodref",
        12: "NameAndType",
        15: "MethodHandle",
        16: "MethodType",
        18: "InvokeDynamic",
    }
    
    # Access flags
    ACCESS_FLAGS = {
        0x0001: "public",
        0x0002: "private",
        0x0004: "protected",
        0x0008: "static",
        0x0010: "final",
        0x0020: "super",
        0x0040: "synchronized",
        0x0080: "bridge",
        0x0100: "varargs",
        0x0200: "interface",
        0x0400: "abstract",
        0x0800: "strict",
        0x1000: "synthetic",
        0x2000: "annotation",
        0x4000: "enum",
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = b""
        self.offset = 0
        self.constant_pool = []
        
    def extract(self) -> Dict[str, Any]:
        """Extract all metadata from the CLASS file."""
        try:
            # Read entire file
            with open(self.file_path, 'rb') as f:
                self.data = f.read()
            
            metadata = {
                "format": "CLASS (Java Bytecode)",
                "file_path": str(self.file_path),
                "file_size": len(self.data),
            }
            
            # Parse components
            self._verify_magic()
            metadata.update(self._parse_version())
            metadata.update(self._parse_constant_pool())
            metadata.update(self._parse_class_info())
            metadata.update(self._parse_fields())
            metadata.update(self._parse_methods())
            metadata.update(self._parse_attributes())
            
            return metadata
            
        except Exception as e:
            return {
                "format": "CLASS (Java Bytecode)",
                "file_path": str(self.file_path),
                "error": str(e)
            }
    
    def _read_u1(self) -> int:
        """Read unsigned 1-byte integer."""
        value = self.data[self.offset]
        self.offset += 1
        return value
    
    def _read_u2(self) -> int:
        """Read unsigned 2-byte integer (big-endian)."""
        value = struct.unpack('>H', self.data[self.offset:self.offset+2])[0]
        self.offset += 2
        return value
    
    def _read_u4(self) -> int:
        """Read unsigned 4-byte integer (big-endian)."""
        value = struct.unpack('>I', self.data[self.offset:self.offset+4])[0]
        self.offset += 4
        return value
    
    def _read_bytes(self, count: int) -> bytes:
        """Read specified number of bytes."""
        value = self.data[self.offset:self.offset+count]
        self.offset += count
        return value
    
    def _verify_magic(self):
        """Verify CLASS magic number (0xCAFEBABE)."""
        magic = self._read_u4()
        if magic != 0xCAFEBABE:
            raise ValueError(f"Invalid CLASS magic number: 0x{magic:08X} (expected 0xCAFEBABE)")
    
    def _parse_version(self) -> Dict[str, Any]:
        """Parse minor and major version numbers."""
        minor = self._read_u2()
        major = self._read_u2()
        
        java_version = self.JAVA_VERSIONS.get(major, f"Unknown (major={major})")
        
        return {
            "version": {
                "minor": minor,
                "major": major,
                "java_version": java_version,
            }
        }
    
    def _parse_constant_pool(self) -> Dict[str, Any]:
        """Parse constant pool."""
        count = self._read_u2()
        
        # Constant pool is 1-indexed, [0] is reserved
        self.constant_pool = [None]
        
        i = 1
        while i < count:
            tag = self._read_u1()
            tag_name = self.CONSTANT_TAGS.get(tag, f"Unknown_{tag}")
            
            constant = {"tag": tag, "type": tag_name}
            
            if tag == 1:  # CONSTANT_Utf8
                length = self._read_u2()
                bytes_value = self._read_bytes(length)
                try:
                    constant["value"] = bytes_value.decode('utf-8')
                except UnicodeDecodeError:
                    constant["value"] = bytes_value.hex()
                    
            elif tag == 3:  # CONSTANT_Integer
                constant["value"] = struct.unpack('>i', self._read_bytes(4))[0]
                
            elif tag == 4:  # CONSTANT_Float
                constant["value"] = struct.unpack('>f', self._read_bytes(4))[0]
                
            elif tag == 5:  # CONSTANT_Long
                constant["value"] = struct.unpack('>q', self._read_bytes(8))[0]
                i += 1  # Long takes 2 slots
                
            elif tag == 6:  # CONSTANT_Double
                constant["value"] = struct.unpack('>d', self._read_bytes(8))[0]
                i += 1  # Double takes 2 slots
                
            elif tag == 7:  # CONSTANT_Class
                constant["name_index"] = self._read_u2()
                
            elif tag == 8:  # CONSTANT_String
                constant["string_index"] = self._read_u2()
                
            elif tag in (9, 10, 11):  # CONSTANT_Fieldref, Methodref, InterfaceMethodref
                constant["class_index"] = self._read_u2()
                constant["name_and_type_index"] = self._read_u2()
                
            elif tag == 12:  # CONSTANT_NameAndType
                constant["name_index"] = self._read_u2()
                constant["descriptor_index"] = self._read_u2()
                
            elif tag == 15:  # CONSTANT_MethodHandle
                constant["reference_kind"] = self._read_u1()
                constant["reference_index"] = self._read_u2()
                
            elif tag == 16:  # CONSTANT_MethodType
                constant["descriptor_index"] = self._read_u2()
                
            elif tag == 18:  # CONSTANT_InvokeDynamic
                constant["bootstrap_method_attr_index"] = self._read_u2()
                constant["name_and_type_index"] = self._read_u2()
                
            else:
                # Unknown tag, skip
                pass
            
            self.constant_pool.append(constant)
            i += 1
        
        # Get statistics
        tag_counts = {}
        for const in self.constant_pool[1:]:
            if const:
                tag_type = const.get("type", "Unknown")
                tag_counts[tag_type] = tag_counts.get(tag_type, 0) + 1
        
        return {
            "constant_pool": {
                "count": count - 1,  # Actual entries (excluding index 0)
                "tag_counts": tag_counts,
            }
        }
    
    def _get_utf8_constant(self, index: int) -> Optional[str]:
        """Get UTF-8 string from constant pool."""
        if index == 0 or index >= len(self.constant_pool):
            return None
        const = self.constant_pool[index]
        if const and const.get("type") == "Utf8":
            return const.get("value")
        return None
    
    def _get_class_name(self, index: int) -> Optional[str]:
        """Get class name from constant pool."""
        if index == 0 or index >= len(self.constant_pool):
            return None
        const = self.constant_pool[index]
        if const and const.get("type") == "Class":
            name_index = const.get("name_index")
            if name_index:
                return self._get_utf8_constant(name_index)
        return None
    
    def _decode_access_flags(self, flags: int) -> List[str]:
        """Decode access flags into list of flag names."""
        flag_names = []
        for flag_value, flag_name in self.ACCESS_FLAGS.items():
            if flags & flag_value:
                flag_names.append(flag_name)
        return flag_names
    
    def _parse_class_info(self) -> Dict[str, Any]:
        """Parse class information."""
        access_flags = self._read_u2()
        this_class = self._read_u2()
        super_class = self._read_u2()
        interfaces_count = self._read_u2()
        
        interfaces = []
        for _ in range(interfaces_count):
            interface_index = self._read_u2()
            interface_name = self._get_class_name(interface_index)
            if interface_name:
                interfaces.append(interface_name)
        
        return {
            "class_info": {
                "access_flags": access_flags,
                "access_flags_decoded": self._decode_access_flags(access_flags),
                "this_class": self._get_class_name(this_class),
                "super_class": self._get_class_name(super_class),
                "interfaces_count": interfaces_count,
                "interfaces": interfaces,
            }
        }
    
    def _parse_fields(self) -> Dict[str, Any]:
        """Parse field information."""
        fields_count = self._read_u2()
        
        fields = []
        for _ in range(fields_count):
            access_flags = self._read_u2()
            name_index = self._read_u2()
            descriptor_index = self._read_u2()
            attributes_count = self._read_u2()
            
            # Skip field attributes
            for _ in range(attributes_count):
                self._read_u2()  # attribute_name_index
                length = self._read_u4()
                self._read_bytes(length)
            
            field = {
                "access_flags": self._decode_access_flags(access_flags),
                "name": self._get_utf8_constant(name_index),
                "descriptor": self._get_utf8_constant(descriptor_index),
            }
            fields.append(field)
        
        return {
            "fields": {
                "count": fields_count,
                "fields_list": fields[:10],  # Sample first 10
            }
        }
    
    def _parse_methods(self) -> Dict[str, Any]:
        """Parse method information."""
        methods_count = self._read_u2()
        
        methods = []
        for _ in range(methods_count):
            access_flags = self._read_u2()
            name_index = self._read_u2()
            descriptor_index = self._read_u2()
            attributes_count = self._read_u2()
            
            # Parse method attributes to get Code attribute
            code_length = None
            for _ in range(attributes_count):
                attr_name_index = self._read_u2()
                attr_length = self._read_u4()
                attr_start = self.offset
                
                attr_name = self._get_utf8_constant(attr_name_index)
                if attr_name == "Code":
                    max_stack = self._read_u2()
                    max_locals = self._read_u2()
                    code_length = self._read_u4()
                    # Skip code bytes
                    self._read_bytes(code_length)
                    # Skip exception table and code attributes
                    self.offset = attr_start + attr_length
                else:
                    # Skip other attributes
                    self._read_bytes(attr_length)
            
            method = {
                "access_flags": self._decode_access_flags(access_flags),
                "name": self._get_utf8_constant(name_index),
                "descriptor": self._get_utf8_constant(descriptor_index),
            }
            if code_length is not None:
                method["code_length"] = code_length
            
            methods.append(method)
        
        return {
            "methods": {
                "count": methods_count,
                "methods_list": methods[:10],  # Sample first 10
            }
        }
    
    def _parse_attributes(self) -> Dict[str, Any]:
        """Parse class attributes."""
        attributes_count = self._read_u2()
        
        attributes = []
        source_file = None
        
        for _ in range(attributes_count):
            name_index = self._read_u2()
            length = self._read_u4()
            
            attr_name = self._get_utf8_constant(name_index)
            
            if attr_name == "SourceFile":
                sourcefile_index = self._read_u2()
                source_file = self._get_utf8_constant(sourcefile_index)
            else:
                # Skip attribute data
                self._read_bytes(length)
            
            attributes.append({
                "name": attr_name,
                "length": length,
            })
        
        result = {
            "attributes": {
                "count": attributes_count,
                "attributes_list": attributes,
            }
        }
        
        if source_file:
            result["source_file"] = source_file
        
        return result

def main():
    if len(sys.argv) < 2:
        print("Usage: class_extractor.py <class_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    extractor = ClassExtractor(file_path)
    metadata = extractor.extract()
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
