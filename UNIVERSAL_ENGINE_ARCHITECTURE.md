# PaniniFS v4.0 - Universal Pattern Engine Architecture

## Executive Summary

**Mission**: Implement the theoretical Pāṇinian universal engine validated empirically in Phase 6 pattern consolidation analysis.

**Empirical Foundation**:
- 70 format extractors analyzed
- 12 universal patterns (Dhātu-FS) identified
- 43% pattern reusability measured
- 81.7% code reduction possible (26,517 → 4,850 lines)

**Goal**: Replace 70 specialized extractors with:
1. **ONE** universal pattern engine (~1000 lines)
2. **70** declarative grammar files (~50 lines each)

---

## Phase 6 Pattern Analysis Results (Empirical)

### Top 12 Universal Patterns (Dhātu-FS)

| Pattern | Usage | Description |
|---------|-------|-------------|
| **KEY_VALUE** | 87.0% | Metadata extraction (headers, tags, properties) |
| **HEADER_BODY** | 75.3% | Standard file structure (header + data sections) |
| **MAGIC_NUMBER** | 59.7% | Format identification signatures |
| **SEQUENTIAL_RECORDS** | 55.8% | Sequential data processing (log files, streams) |
| **BINARY_FIELD** | 50.6% | Binary struct unpacking |
| **LENGTH_PREFIXED** | 49.4% | Length-prefixed data structures |
| **COMPRESSED_DATA** | 45.5% | Compression detection/handling |
| **TEXT_MARKUP** | 31.2% | Text format parsing (XML, Markdown) |
| **OFFSET_TABLE** | 20.8% | Offset-based navigation (TOC, indices) |
| **CHECKSUM** | 19.5% | Integrity verification (CRC, hash) |
| **CHUNK_STRUCTURE** | 16.9% | Chunked data (PNG, IFF, RIFF) |
| **HIERARCHICAL_TREE** | 3.9% | Tree structures (XML, JSON) |

### Pattern Categories

1. **Structure** (30.0 avg usage): MAGIC_NUMBER, CHUNK, HEADER_BODY, TREE
2. **Data Encoding** (37.3 avg): LENGTH_PREFIX, BINARY_FIELD, COMPRESSED
3. **Integrity** (15.0 avg): CHECKSUM
4. **Organization** (42.0 avg): KEY_VALUE, SEQUENTIAL, OFFSET_TABLE
5. **Text Processing** (24.0 avg): TEXT_MARKUP

**Key Insight**: Top 5 patterns cover **65.7%** of all pattern uses across formats.

---

## v4.0 Architecture Design

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Universal Pattern Engine                  │
│                        (v4.0 Core)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Grammar Parser (DSL Interpreter)              │ │
│  │  - Parse declarative grammar files                    │ │
│  │  - Validate syntax                                    │ │
│  │  - Compile to pattern execution plan                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │      Pattern Matcher Engine (Core Executor)           │ │
│  │  - Execute pattern matching plan                      │ │
│  │  - Handle nested structures                           │ │
│  │  - Collect metadata                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │        12 Pattern Implementations (Dhātu-FS)          │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ 1. MagicNumberPattern      (format identification)    │ │
│  │ 2. KeyValuePattern         (metadata extraction)      │ │
│  │ 3. HeaderBodyPattern       (structure parsing)        │ │
│  │ 4. SequentialRecordPattern (stream processing)        │ │
│  │ 5. BinaryFieldPattern      (struct unpacking)         │ │
│  │ 6. LengthPrefixedPattern   (size-prefixed data)       │ │
│  │ 7. CompressedDataPattern   (compression detection)    │ │
│  │ 8. TextMarkupPattern       (text parsing)             │ │
│  │ 9. OffsetTablePattern      (offset navigation)        │ │
│  │ 10. ChecksumPattern        (integrity verification)   │ │
│  │ 11. ChunkStructurePattern  (chunk-based formats)      │ │
│  │ 12. HierarchicalTreePattern (tree structures)         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           Format Registry (Grammar Loader)            │ │
│  │  - Load grammar files from formats/ directory         │ │
│  │  - Cache parsed grammars                              │ │
│  │  - Auto-detect format from file content               │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │                      │                     │
          ▼                      ▼                     ▼
    ┌─────────┐           ┌─────────┐          ┌─────────┐
    │ png.yml │           │ zip.yml │          │ pdf.yml │
    │ (50 L)  │           │ (50 L)  │          │ (50 L)  │
    └─────────┘           └─────────┘          └─────────┘
         ... 70 grammar files (~3,500 lines total) ...
```

---

## Grammar DSL Design

### Declarative Syntax (YAML-based)

**Example: PNG Format Grammar**

```yaml
format:
  name: PNG
  extension: .png
  mime_type: image/png
  description: Portable Network Graphics

patterns:
  - pattern: MAGIC_NUMBER
    offset: 0
    signature: "\x89PNG\r\n\x1a\n"
    length: 8
    
  - pattern: CHUNK_STRUCTURE
    repeating: true
    chunk_format:
      length: UINT32_BE  # 4 bytes big-endian
      type: ASCII_TAG    # 4-byte ASCII tag (e.g., "IHDR", "IDAT")
      data: LENGTH_BYTES # Variable length from length field
      crc: UINT32_BE     # CRC32 checksum
    
    chunks:
      IHDR:
        pattern: HEADER_BODY
        required: true
        fields:
          - {name: width, type: UINT32_BE}
          - {name: height, type: UINT32_BE}
          - {name: bit_depth, type: UINT8}
          - {name: color_type, type: UINT8}
          - {name: compression, type: UINT8}
          - {name: filter, type: UINT8}
          - {name: interlace, type: UINT8}
      
      tEXt:
        pattern: KEY_VALUE
        repeating: true
        separator: "\x00"  # Null-terminated key
        encoding: latin-1
      
      IDAT:
        pattern: COMPRESSED_DATA
        compression: zlib
        repeating: true
      
      IEND:
        pattern: MAGIC_NUMBER
        required: true
        signature: ""
        length: 0

metadata:
  extract:
    - field: IHDR.width
      as: image_width
    - field: IHDR.height
      as: image_height
    - field: IHDR.bit_depth
      as: bits_per_pixel
    - field: tEXt.*
      as: text_metadata
    - chunk_count: IDAT
      as: data_chunks
```

**Grammar Size**: ~50-60 lines (vs 300+ lines in current png_extractor.py)

---

### Pattern Interface (Abstract Base)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Pattern(ABC):
    """Abstract base class for all patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def match(self, data: bytes, offset: int) -> Optional[Dict[str, Any]]:
        """
        Attempt to match pattern at given offset.
        
        Returns:
            - Dict with extracted metadata if match succeeds
            - None if match fails
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate pattern configuration"""
        pass
```

---

## Implementation Strategy

### Phase 7.1: Core Engine (Week 1)

**Goal**: Implement minimal viable engine with 3 patterns

**Files**:
- `universal_engine/` (new package)
  - `__init__.py`
  - `engine.py` - Main execution engine
  - `grammar_parser.py` - YAML DSL parser
  - `patterns/` - Pattern implementations
    - `__init__.py`
    - `base.py` - Pattern ABC
    - `magic_number.py`
    - `header_body.py`
    - `key_value.py`

**Deliverable**: Engine that can parse and execute 3 patterns

---

### Phase 7.2: Pattern Library (Week 2)

**Goal**: Implement remaining 9 patterns

**New Files**:
- `patterns/binary_field.py`
- `patterns/length_prefixed.py`
- `patterns/sequential_records.py`
- `patterns/compressed_data.py`
- `patterns/checksum.py`
- `patterns/chunk_structure.py`
- `patterns/offset_table.py`
- `patterns/text_markup.py`
- `patterns/hierarchical_tree.py`

**Testing**: Unit tests for each pattern with synthetic data

---

### Phase 7.3: Grammar Migration (Week 3)

**Goal**: Convert 3 diverse extractors to grammars

**Target Formats** (chosen for diversity):
1. **PNG** - Binary, chunked, checksums (CHUNK, MAGIC, COMPRESSED, CHECKSUM)
2. **JSON** - Text, hierarchical, simple (TREE, TEXT_MARKUP, KEY_VALUE)
3. **ZIP** - Binary, compressed, sequential (HEADER_BODY, COMPRESSED, SEQUENTIAL, OFFSET_TABLE)

**Grammar Files**:
- `formats/png.yml`
- `formats/json.yml`
- `formats/zip.yml`

**Validation**: Compare output with original extractors byte-for-byte

---

### Phase 7.4: Validation & Benchmarking (Week 4)

**Metrics**:
1. **Correctness**: Output identical to original extractors (100% match)
2. **Code Reduction**: 
   - Before: 3 extractors × 300 lines = 900 lines
   - After: 1 engine (1000 lines) + 3 grammars (150 lines) = 1150 lines
   - **Per-format savings**: 750 lines saved (83% reduction)
3. **Performance**: 
   - Acceptable if <2x slower than specialized extractors
   - Target: <1.5x overhead
4. **Maintainability**: 
   - New format: ~50 lines grammar (vs 300+ lines code)
   - Time to implement: <1 hour (vs ~4 hours)

---

## Code Size Projections

### Current State (v3.58)

```
70 extractors × 344 lines avg = 24,080 lines
+ grammar extractors = 26,517 lines total
```

### Target State (v4.0)

```
Universal engine:           1,000 lines
12 pattern implementations: 1,200 lines (100 lines each)
Grammar parser:              400 lines
Format registry:             200 lines
Testing infrastructure:      500 lines
─────────────────────────────────────
Core infrastructure:        3,300 lines

70 grammar files × 50 lines = 3,500 lines
─────────────────────────────────────
TOTAL:                      6,800 lines
```

**Code Reduction**: 26,517 → 6,800 = **74.4% reduction** (19,717 lines saved)

*(Slightly lower than theoretical 81.7% due to infrastructure overhead)*

---

## Grammar DSL Specification

### Top-Level Structure

```yaml
format:
  name: string           # Human-readable format name
  extension: string      # Primary file extension (e.g., ".png")
  extensions: [string]   # Alternative extensions (optional)
  mime_type: string      # MIME type (optional)
  description: string    # Format description

magic:                   # Optional magic number detection
  offset: int            # Byte offset (usually 0)
  signature: bytes       # Signature bytes (hex or string)
  mask: bytes           # Optional mask for partial matching

patterns:                # List of pattern applications
  - pattern: PATTERN_NAME
    offset: int | "auto" # Where to apply pattern
    config: {...}        # Pattern-specific configuration

metadata:                # What to extract
  extract:
    - field: path.to.value
      as: output_name
    - custom_expression
```

### Pattern-Specific Configs

**MAGIC_NUMBER**:
```yaml
pattern: MAGIC_NUMBER
offset: 0
signature: "\x89PNG\r\n\x1a\n"
length: 8
```

**HEADER_BODY**:
```yaml
pattern: HEADER_BODY
header_size: 512
fields:
  - {name: field_name, offset: 0, type: UINT32_BE}
  - {name: another_field, offset: 4, type: ASCII_STRING, length: 32}
```

**CHUNK_STRUCTURE**:
```yaml
pattern: CHUNK_STRUCTURE
repeating: true
chunk_format:
  length: UINT32_BE
  type: ASCII_TAG
  data: LENGTH_BYTES
  crc: UINT32_BE
end_marker: "IEND"  # Optional
```

**KEY_VALUE**:
```yaml
pattern: KEY_VALUE
format: "key=value"  # Or "key: value", "key\x00value", etc.
separator: "="
line_ending: "\n"
encoding: utf-8
```

---

## Success Criteria

### Phase 7 Complete When:

1. ✅ **Core engine implemented** (1000 lines)
2. ✅ **12 patterns working** with unit tests
3. ✅ **3 grammars migrated** (PNG, JSON, ZIP)
4. ✅ **Validation passed**: 100% metadata match with original extractors
5. ✅ **Performance acceptable**: <2x slowdown vs specialized code
6. ✅ **Documentation complete**: Grammar DSL reference, pattern catalog
7. ✅ **POC demonstrated**: New format implemented in <1 hour using grammar only

---

## Long-Term Vision (v4.1+)

### Full Migration Plan

**Phase 7.5**: Migrate remaining 67 formats (after POC validation)
- ~50 lines × 67 formats = ~3,350 lines of grammar
- Estimated: 2-3 weeks (batch migration with scripts)

**Phase 8**: Community contribution framework
- Grammar submission process
- Automated validation tests
- Format registry website

**Phase 9**: Advanced features
- Grammar composition (inherit common patterns)
- Custom pattern plugins
- Grammar optimization (compile to bytecode)
- Parallel format detection

---

## Pāṇinian Validation

### Theoretical Claim
> Just as ~2000 Sanskrit dhātus generate millions of words through compositional rules, ~12 universal patterns should generate parsing logic for any binary format through declarative grammars.

### Empirical Evidence (Phase 6)
- **Measured reusability**: 43.0%
- **Pattern coverage**: Top 5 patterns cover 65.7% of uses
- **Code reduction**: 81.7% theoretical, 74.4% realistic with infrastructure

### Phase 7 Goal
**Demonstrate constructively** that the universal engine works in practice:
1. Engine + 12 patterns = 3,300 lines (reusable core)
2. Each new format = ~50 lines (declarative grammar)
3. Full migration = 74.4% code reduction
4. Maintainability = 10x improvement (grammar vs code)

**If successful**: Pāṇinian hypothesis **validated both empirically and constructively**.

---

## Next Actions

1. **Create `universal_engine/` package structure**
2. **Implement Pattern ABC and 3 core patterns** (MAGIC, HEADER_BODY, KEY_VALUE)
3. **Build minimal grammar parser** (YAML → pattern execution plan)
4. **Create PNG grammar** as first POC
5. **Validate** against existing png_extractor.py output

**Start with**: `universal_engine/patterns/base.py` (Pattern ABC)
