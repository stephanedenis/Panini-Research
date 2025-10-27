#!/usr/bin/env python3
"""
PaniniFS v3.28: JAR (Java Archive) Format Extractor
====================================================

JAR - Java Archive format (ZIP-based).

Structure (ZIP container):
- Standard ZIP format
- META-INF/ directory:
  - MANIFEST.MF: Manifest file
    - Manifest-Version
    - Created-By
    - Main-Class (entry point)
    - Class-Path
    - Implementation-Title, Version, Vendor
    - Sealed
    - Signature files (.SF, .DSA, .RSA)
  
- .class files: Compiled Java bytecode
- Resources: properties, images, etc.

Manifest format:
Name: Value
 continuation (space-indented)

Common manifest attributes:
- Main-Class: Entry point class
- Class-Path: External dependencies
- Implementation-Title: Application name
- Implementation-Version: Version number
- Implementation-Vendor: Organization
- Built-By: Builder user
- Build-Jdk: JDK version used
- Created-By: Tool that created JAR
- Sealed: Package sealing

Metadata extracted:
- Manifest attributes
- Main class (if executable)
- Class-path dependencies
- Implementation info
- Class file count
- Resource file count
- Package structure
- Signature info (if signed)
- JAR size and compression

Format: ZIP archive with specific structure
Encoding: UTF-8 for manifest

Author: PaniniFS Research Team
Version: 3.28
Date: 2025-01-14
"""

import sys
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


class JARExtractor:
    """Extract metadata from Java Archive (JAR) files."""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Dict[str, Any] = {}
        self.zip: Optional[zipfile.ZipFile] = None
        
    def extract(self) -> Dict[str, Any]:
        """Main extraction method."""
        self.data = {
            "format": "JAR (Java Archive)",
            "file": str(self.filepath),
            "size": self.filepath.stat().st_size,
            "manifest": {},
            "classes": [],
            "packages": [],
            "resources": [],
            "is_executable": False,
            "is_signed": False,
            "statistics": {},
            "errors": []
        }
        
        try:
            # Open ZIP
            self.zip = zipfile.ZipFile(self.filepath, 'r')
            
            # Parse manifest
            self._parse_manifest()
            
            # Analyze contents
            self._analyze_contents()
            
            # Calculate statistics
            self._calculate_statistics()
            
        except zipfile.BadZipFile:
            self.data["errors"].append("Invalid ZIP/JAR file")
        except Exception as e:
            self.data["errors"].append(f"Extraction error: {str(e)}")
        finally:
            if self.zip:
                self.zip.close()
        
        return self.data
    
    def _parse_manifest(self):
        """Parse META-INF/MANIFEST.MF."""
        manifest_path = 'META-INF/MANIFEST.MF'
        
        if manifest_path not in self.zip.namelist():
            self.data["errors"].append("No MANIFEST.MF found")
            return
        
        try:
            # Read manifest
            manifest_data = self.zip.read(manifest_path)
            manifest_text = manifest_data.decode('utf-8', errors='replace')
            
            # Parse manifest attributes
            # Format: Name: Value (with continuation lines starting with space)
            lines = manifest_text.split('\n')
            current_name = None
            current_value = []
            
            for line in lines:
                line = line.rstrip('\r')
                
                # Continuation line (starts with space)
                if line.startswith(' ') and current_name:
                    current_value.append(line[1:])
                # New attribute
                elif ':' in line:
                    # Save previous attribute
                    if current_name:
                        self.data["manifest"][current_name] = ''.join(current_value)
                    
                    # Parse new attribute
                    name, value = line.split(':', 1)
                    current_name = name.strip()
                    current_value = [value.strip()]
                # Empty line or end
                elif line.strip() == '' and current_name:
                    # Save and reset
                    self.data["manifest"][current_name] = ''.join(current_value)
                    current_name = None
                    current_value = []
            
            # Save last attribute
            if current_name:
                self.data["manifest"][current_name] = ''.join(current_value)
            
            # Check if executable
            if 'Main-Class' in self.data["manifest"]:
                self.data["is_executable"] = True
            
        except Exception as e:
            self.data["errors"].append(f"Manifest parse error: {str(e)}")
    
    def _analyze_contents(self):
        """Analyze JAR contents."""
        class_files = []
        packages = set()
        resources = []
        
        for name in self.zip.namelist():
            # Skip META-INF for class analysis
            if name.startswith('META-INF/'):
                # Check for signature files
                if name.endswith('.SF') or name.endswith('.DSA') or name.endswith('.RSA'):
                    self.data["is_signed"] = True
                continue
            
            # Class files
            if name.endswith('.class'):
                class_files.append(name)
                
                # Extract package
                if '/' in name:
                    package = '/'.join(name.split('/')[:-1])
                    packages.add(package)
            
            # Resource files (non-class)
            else:
                if not name.endswith('/'):  # Skip directories
                    resources.append(name)
        
        # Store results (sample first 20)
        self.data["classes"] = sorted(class_files)[:20]
        self.data["packages"] = sorted(packages)[:20]
        self.data["resources"] = sorted(resources)[:20]
    
    def _calculate_statistics(self):
        """Calculate JAR statistics."""
        total_entries = len(self.zip.namelist())
        total_classes = len([n for n in self.zip.namelist() if n.endswith('.class')])
        total_packages = len(set('/'.join(n.split('/')[:-1]) for n in self.zip.namelist() 
                                if n.endswith('.class') and '/' in n))
        total_resources = len([n for n in self.zip.namelist() 
                              if not n.endswith('.class') and not n.startswith('META-INF/') 
                              and not n.endswith('/')])
        
        # Compression
        try:
            compressed_size = self.filepath.stat().st_size
            uncompressed_size = sum(info.file_size for info in self.zip.infolist())
            compression_ratio = round(compressed_size / uncompressed_size, 2) if uncompressed_size > 0 else 1.0
        except:
            compression_ratio = None
        
        self.data["statistics"] = {
            "total_entries": total_entries,
            "total_classes": total_classes,
            "total_packages": total_packages,
            "total_resources": total_resources,
            "compression_ratio": compression_ratio,
            "has_manifest": bool(self.data["manifest"]),
            "is_executable": self.data["is_executable"],
            "is_signed": self.data["is_signed"],
            "main_class": self.data["manifest"].get("Main-Class"),
            "implementation_title": self.data["manifest"].get("Implementation-Title"),
            "implementation_version": self.data["manifest"].get("Implementation-Version")
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python jar_extractor.py <file.jar>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    extractor = JARExtractor(filepath)
    result = extractor.extract()
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
