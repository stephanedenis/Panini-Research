#!/usr/bin/env python3
"""
ELF (Executable and Linkable Format) Extractor for PaniniFS v3.7
Extracts metadata and structure from ELF executables and shared libraries.

Supports:
- ELF32 and ELF64
- All architectures (x86, x86-64, ARM, RISC-V, etc.)
- Executable, shared object, relocatable, core dump types
- Program headers (segments)
- Section headers
- Dynamic linking information
- Symbol tables
"""

import struct
import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


# ELF constants
EI_MAG0 = 0
EI_MAG1 = 1
EI_MAG2 = 2
EI_MAG3 = 3
EI_CLASS = 4
EI_DATA = 5
EI_VERSION = 6
EI_OSABI = 7
EI_ABIVERSION = 8
EI_PAD = 9
EI_NIDENT = 16

ELFCLASS32 = 1
ELFCLASS64 = 2

ELFDATA2LSB = 1
ELFDATA2MSB = 2

ET_NONE = 0
ET_REL = 1
ET_EXEC = 2
ET_DYN = 3
ET_CORE = 4

# Machine types
EM_NONE = 0
EM_M32 = 1
EM_SPARC = 2
EM_386 = 3
EM_68K = 4
EM_88K = 5
EM_860 = 7
EM_MIPS = 8
EM_S370 = 9
EM_MIPS_RS3_LE = 10
EM_PARISC = 15
EM_VPP500 = 17
EM_SPARC32PLUS = 18
EM_960 = 19
EM_PPC = 20
EM_PPC64 = 21
EM_S390 = 22
EM_V800 = 36
EM_FR20 = 37
EM_RH32 = 38
EM_RCE = 39
EM_ARM = 40
EM_FAKE_ALPHA = 41
EM_SH = 42
EM_SPARCV9 = 43
EM_TRICORE = 44
EM_ARC = 45
EM_H8_300 = 46
EM_H8_300H = 47
EM_H8S = 48
EM_H8_500 = 49
EM_IA_64 = 50
EM_MIPS_X = 51
EM_COLDFIRE = 52
EM_68HC12 = 53
EM_MMA = 54
EM_PCP = 55
EM_NCPU = 56
EM_NDR1 = 57
EM_STARCORE = 58
EM_ME16 = 59
EM_ST100 = 60
EM_TINYJ = 61
EM_X86_64 = 62
EM_AARCH64 = 183
EM_RISCV = 243

# Program header types
PT_NULL = 0
PT_LOAD = 1
PT_DYNAMIC = 2
PT_INTERP = 3
PT_NOTE = 4
PT_SHLIB = 5
PT_PHDR = 6
PT_TLS = 7
PT_GNU_EH_FRAME = 0x6474e550
PT_GNU_STACK = 0x6474e551
PT_GNU_RELRO = 0x6474e552

# Section header types
SHT_NULL = 0
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_RELA = 4
SHT_HASH = 5
SHT_DYNAMIC = 6
SHT_NOTE = 7
SHT_NOBITS = 8
SHT_REL = 9
SHT_SHLIB = 10
SHT_DYNSYM = 11


@dataclass
class ELFHeader:
    """ELF file header."""
    ei_class: int
    ei_data: int
    ei_version: int
    ei_osabi: int
    ei_abiversion: int
    e_type: int
    e_machine: int
    e_version: int
    e_entry: int
    e_phoff: int
    e_shoff: int
    e_flags: int
    e_ehsize: int
    e_phentsize: int
    e_phnum: int
    e_shentsize: int
    e_shnum: int
    e_shstrndx: int


@dataclass
class ProgramHeader:
    """ELF program header (segment)."""
    p_type: int
    p_flags: int
    p_offset: int
    p_vaddr: int
    p_paddr: int
    p_filesz: int
    p_memsz: int
    p_align: int


@dataclass
class SectionHeader:
    """ELF section header."""
    sh_name: int
    sh_type: int
    sh_flags: int
    sh_addr: int
    sh_offset: int
    sh_size: int
    sh_link: int
    sh_info: int
    sh_addralign: int
    sh_entsize: int


class ELFExtractor:
    """Extract metadata from ELF files."""
    
    MACHINE_NAMES = {
        EM_NONE: 'No machine',
        EM_M32: 'AT&T WE 32100',
        EM_SPARC: 'SPARC',
        EM_386: 'Intel 80386',
        EM_68K: 'Motorola 68000',
        EM_88K: 'Motorola 88000',
        EM_860: 'Intel 80860',
        EM_MIPS: 'MIPS R3000',
        EM_PARISC: 'HP PA-RISC',
        EM_PPC: 'PowerPC',
        EM_PPC64: 'PowerPC 64-bit',
        EM_S390: 'IBM S/390',
        EM_ARM: 'ARM',
        EM_SH: 'SuperH',
        EM_SPARCV9: 'SPARC v9 64-bit',
        EM_IA_64: 'Intel IA-64',
        EM_X86_64: 'AMD x86-64',
        EM_AARCH64: 'AArch64',
        EM_RISCV: 'RISC-V'
    }
    
    OSABI_NAMES = {
        0: 'UNIX System V',
        1: 'HP-UX',
        2: 'NetBSD',
        3: 'Linux',
        6: 'Solaris',
        7: 'AIX',
        8: 'IRIX',
        9: 'FreeBSD',
        10: 'Tru64',
        11: 'Novell Modesto',
        12: 'OpenBSD',
        97: 'ARM',
        255: 'Standalone'
    }
    
    TYPE_NAMES = {
        ET_NONE: 'NONE (Unknown)',
        ET_REL: 'REL (Relocatable)',
        ET_EXEC: 'EXEC (Executable)',
        ET_DYN: 'DYN (Shared object)',
        ET_CORE: 'CORE (Core dump)'
    }
    
    PT_NAMES = {
        PT_NULL: 'NULL',
        PT_LOAD: 'LOAD',
        PT_DYNAMIC: 'DYNAMIC',
        PT_INTERP: 'INTERP',
        PT_NOTE: 'NOTE',
        PT_SHLIB: 'SHLIB',
        PT_PHDR: 'PHDR',
        PT_TLS: 'TLS',
        PT_GNU_EH_FRAME: 'GNU_EH_FRAME',
        PT_GNU_STACK: 'GNU_STACK',
        PT_GNU_RELRO: 'GNU_RELRO'
    }
    
    SHT_NAMES = {
        SHT_NULL: 'NULL',
        SHT_PROGBITS: 'PROGBITS',
        SHT_SYMTAB: 'SYMTAB',
        SHT_STRTAB: 'STRTAB',
        SHT_RELA: 'RELA',
        SHT_HASH: 'HASH',
        SHT_DYNAMIC: 'DYNAMIC',
        SHT_NOTE: 'NOTE',
        SHT_NOBITS: 'NOBITS',
        SHT_REL: 'REL',
        SHT_SHLIB: 'SHLIB',
        SHT_DYNSYM: 'DYNSYM'
    }
    
    def __init__(self, filepath: str):
        """Initialize extractor with file path."""
        self.filepath = filepath
        self.data = None
        self.header: Optional[ELFHeader] = None
        self.is_64bit = False
        self.is_little_endian = False
        self.endian_char = '<'
        
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata from ELF file."""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        # Validate ELF magic
        if len(self.data) < 64 or self.data[0:4] != b'\x7fELF':
            raise ValueError("Not a valid ELF file (missing magic)")
        
        # Parse ELF header
        self.header = self._parse_header()
        
        # Parse program headers
        program_headers = self._parse_program_headers()
        
        # Parse section headers
        section_headers = self._parse_section_headers()
        
        # Get string tables
        section_names = self._get_section_names(section_headers)
        
        # Find interpreter
        interpreter = self._find_interpreter(program_headers)
        
        # Find dynamic libraries
        dynamic_libs = self._find_dynamic_libraries(section_headers, section_names)
        
        return {
            'format': 'ELF',
            'header': self._header_to_dict(),
            'segments': self._segments_to_dict(program_headers),
            'sections': self._sections_to_dict(section_headers, section_names),
            'interpreter': interpreter,
            'dynamic_libraries': dynamic_libs,
            'statistics': self._compute_statistics(program_headers, section_headers)
        }
    
    def _parse_header(self) -> ELFHeader:
        """Parse ELF header."""
        ei_class = self.data[EI_CLASS]
        ei_data = self.data[EI_DATA]
        
        if ei_class not in (ELFCLASS32, ELFCLASS64):
            raise ValueError(f"Invalid ELF class: {ei_class}")
        
        if ei_data not in (ELFDATA2LSB, ELFDATA2MSB):
            raise ValueError(f"Invalid ELF data encoding: {ei_data}")
        
        self.is_64bit = (ei_class == ELFCLASS64)
        self.is_little_endian = (ei_data == ELFDATA2LSB)
        self.endian_char = '<' if self.is_little_endian else '>'
        
        # Parse e_ident
        ei_version = self.data[EI_VERSION]
        ei_osabi = self.data[EI_OSABI]
        ei_abiversion = self.data[EI_ABIVERSION]
        
        # Parse rest of header
        if self.is_64bit:
            fmt = f'{self.endian_char}HHIQQQIHHHHHH'
            fields = struct.unpack(fmt, self.data[16:64])
        else:
            fmt = f'{self.endian_char}HHIIIIIHHHHHH'
            fields = struct.unpack(fmt, self.data[16:52])
        
        return ELFHeader(
            ei_class=ei_class,
            ei_data=ei_data,
            ei_version=ei_version,
            ei_osabi=ei_osabi,
            ei_abiversion=ei_abiversion,
            e_type=fields[0],
            e_machine=fields[1],
            e_version=fields[2],
            e_entry=fields[3],
            e_phoff=fields[4],
            e_shoff=fields[5],
            e_flags=fields[6],
            e_ehsize=fields[7],
            e_phentsize=fields[8],
            e_phnum=fields[9],
            e_shentsize=fields[10],
            e_shnum=fields[11],
            e_shstrndx=fields[12]
        )
    
    def _parse_program_headers(self) -> List[ProgramHeader]:
        """Parse all program headers."""
        headers = []
        offset = self.header.e_phoff
        
        for _ in range(self.header.e_phnum):
            if self.is_64bit:
                # 64-bit: p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align
                fmt = f'{self.endian_char}IIQQQQQQ'
                size = 56
            else:
                # 32-bit: p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align
                fmt = f'{self.endian_char}IIIIIIII'
                size = 32
            
            if offset + size > len(self.data):
                break
            
            fields = struct.unpack(fmt, self.data[offset:offset+size])
            
            if self.is_64bit:
                ph = ProgramHeader(
                    p_type=fields[0],
                    p_flags=fields[1],
                    p_offset=fields[2],
                    p_vaddr=fields[3],
                    p_paddr=fields[4],
                    p_filesz=fields[5],
                    p_memsz=fields[6],
                    p_align=fields[7]
                )
            else:
                ph = ProgramHeader(
                    p_type=fields[0],
                    p_flags=fields[6],
                    p_offset=fields[1],
                    p_vaddr=fields[2],
                    p_paddr=fields[3],
                    p_filesz=fields[4],
                    p_memsz=fields[5],
                    p_align=fields[7]
                )
            
            headers.append(ph)
            offset += self.header.e_phentsize
        
        return headers
    
    def _parse_section_headers(self) -> List[SectionHeader]:
        """Parse all section headers."""
        headers = []
        offset = self.header.e_shoff
        
        if offset == 0:
            return headers
        
        for _ in range(self.header.e_shnum):
            if self.is_64bit:
                fmt = f'{self.endian_char}IIQQQQIIQQ'
                size = 64
            else:
                fmt = f'{self.endian_char}IIIIIIIIII'
                size = 40
            
            if offset + size > len(self.data):
                break
            
            fields = struct.unpack(fmt, self.data[offset:offset+size])
            
            sh = SectionHeader(
                sh_name=fields[0],
                sh_type=fields[1],
                sh_flags=fields[2],
                sh_addr=fields[3],
                sh_offset=fields[4],
                sh_size=fields[5],
                sh_link=fields[6],
                sh_info=fields[7],
                sh_addralign=fields[8],
                sh_entsize=fields[9]
            )
            
            headers.append(sh)
            offset += self.header.e_shentsize
        
        return headers
    
    def _get_section_names(self, section_headers: List[SectionHeader]) -> Dict[int, str]:
        """Extract section names from string table."""
        names = {}
        
        if self.header.e_shstrndx >= len(section_headers):
            return names
        
        strtab_sh = section_headers[self.header.e_shstrndx]
        strtab = self.data[strtab_sh.sh_offset:strtab_sh.sh_offset + strtab_sh.sh_size]
        
        for i, sh in enumerate(section_headers):
            name_offset = sh.sh_name
            if name_offset < len(strtab):
                end = strtab.find(b'\x00', name_offset)
                if end == -1:
                    end = len(strtab)
                names[i] = strtab[name_offset:end].decode('utf-8', errors='replace')
        
        return names
    
    def _find_interpreter(self, program_headers: List[ProgramHeader]) -> Optional[str]:
        """Find interpreter path from PT_INTERP segment."""
        for ph in program_headers:
            if ph.p_type == PT_INTERP:
                offset = ph.p_offset
                size = ph.p_filesz
                if offset + size <= len(self.data):
                    interp = self.data[offset:offset+size]
                    # Remove trailing null
                    if interp and interp[-1] == 0:
                        interp = interp[:-1]
                    return interp.decode('utf-8', errors='replace')
        return None
    
    def _find_dynamic_libraries(self, section_headers: List[SectionHeader], 
                               section_names: Dict[int, str]) -> List[str]:
        """Find dynamic library dependencies."""
        # This is a simplified version - full implementation would parse .dynamic section
        libs = []
        
        for i, sh in enumerate(section_headers):
            name = section_names.get(i, '')
            if name == '.dynstr':
                # Parse dynamic string table for library names (NEEDED entries)
                offset = sh.sh_offset
                size = sh.sh_size
                if offset + size <= len(self.data):
                    dynstr = self.data[offset:offset+size]
                    # Extract strings that look like library names
                    strings = dynstr.split(b'\x00')
                    for s in strings:
                        try:
                            s_decoded = s.decode('utf-8', errors='replace')
                            if s_decoded and (s_decoded.startswith('lib') or '.so' in s_decoded):
                                libs.append(s_decoded)
                        except:
                            pass
        
        return list(set(libs))[:10]  # Limit to first 10 unique libraries
    
    def _header_to_dict(self) -> Dict[str, Any]:
        """Convert ELF header to dictionary."""
        h = self.header
        return {
            'class': '64-bit' if h.ei_class == ELFCLASS64 else '32-bit',
            'data': 'Little-endian' if h.ei_data == ELFDATA2LSB else 'Big-endian',
            'version': h.ei_version,
            'os_abi': self.OSABI_NAMES.get(h.ei_osabi, f'Unknown ({h.ei_osabi})'),
            'abi_version': h.ei_abiversion,
            'type': self.TYPE_NAMES.get(h.e_type, f'Unknown ({h.e_type})'),
            'machine': self.MACHINE_NAMES.get(h.e_machine, f'Unknown ({h.e_machine})'),
            'entry_point': f'0x{h.e_entry:x}',
            'program_headers_offset': h.e_phoff,
            'section_headers_offset': h.e_shoff,
            'flags': f'0x{h.e_flags:x}',
            'header_size': h.e_ehsize,
            'program_header_size': h.e_phentsize,
            'program_header_count': h.e_phnum,
            'section_header_size': h.e_shentsize,
            'section_header_count': h.e_shnum,
            'section_names_index': h.e_shstrndx
        }
    
    def _segments_to_dict(self, program_headers: List[ProgramHeader]) -> List[Dict[str, Any]]:
        """Convert program headers to dictionary list."""
        segments = []
        
        for ph in program_headers:
            segment = {
                'type': self.PT_NAMES.get(ph.p_type, f'0x{ph.p_type:x}'),
                'offset': ph.p_offset,
                'vaddr': f'0x{ph.p_vaddr:x}',
                'paddr': f'0x{ph.p_paddr:x}',
                'file_size': ph.p_filesz,
                'mem_size': ph.p_memsz,
                'flags': self._parse_segment_flags(ph.p_flags),
                'align': ph.p_align
            }
            segments.append(segment)
        
        return segments
    
    def _sections_to_dict(self, section_headers: List[SectionHeader], 
                          section_names: Dict[int, str]) -> List[Dict[str, Any]]:
        """Convert section headers to dictionary list."""
        sections = []
        
        for i, sh in enumerate(section_headers):
            section = {
                'index': i,
                'name': section_names.get(i, f'<unnamed_{i}>'),
                'type': self.SHT_NAMES.get(sh.sh_type, f'0x{sh.sh_type:x}'),
                'flags': f'0x{sh.sh_flags:x}',
                'addr': f'0x{sh.sh_addr:x}',
                'offset': sh.sh_offset,
                'size': sh.sh_size,
                'link': sh.sh_link,
                'info': sh.sh_info,
                'align': sh.sh_addralign,
                'entry_size': sh.sh_entsize
            }
            sections.append(section)
        
        return sections
    
    def _parse_segment_flags(self, flags: int) -> str:
        """Parse segment flags to readable string."""
        result = []
        if flags & 0x1:
            result.append('X')  # Execute
        if flags & 0x2:
            result.append('W')  # Write
        if flags & 0x4:
            result.append('R')  # Read
        return ''.join(result) if result else '-'
    
    def _compute_statistics(self, program_headers: List[ProgramHeader],
                           section_headers: List[SectionHeader]) -> Dict[str, Any]:
        """Compute ELF statistics."""
        load_segments = [ph for ph in program_headers if ph.p_type == PT_LOAD]
        total_load_size = sum(ph.p_filesz for ph in load_segments)
        total_mem_size = sum(ph.p_memsz for ph in load_segments)
        
        return {
            'total_segments': len(program_headers),
            'load_segments': len(load_segments),
            'total_sections': len(section_headers),
            'total_load_size': total_load_size,
            'total_mem_size': total_mem_size,
            'size_difference': total_mem_size - total_load_size
        }


def main():
    """Main extraction function."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <elf_file>", file=sys.stderr)
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    try:
        extractor = ELFExtractor(filepath)
        metadata = extractor.extract_metadata()
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
