# Panini-FS Architecture Specification

**Version**: 1.0  
**Date**: October 28, 2025  
**Target**: Rust + TypeScript Product Implementation

---

## 🎯 Overview

Panini-FS is a **universal format digester** that can decompose any file format into content-addressed primitives and reconstruct them losslessly. It uses grammar-based analysis to understand format structure and achieves high compression through intelligent decomposition.

**Core Concept**: Every file format is a structured binary language with grammar rules. By extracting the grammar and decomposing according to structure, we can store content more efficiently and enable universal format processing.

---

## 🏗️ System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    Panini-FS Core                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Format     │  │  Decomposer  │  │ Reconstructor│ │
│  │   Detector   │→ │   Engine     │→ │   Engine     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓                  ↓                  ↑         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Grammar    │  │   Content    │  │  Validation  │ │
│  │   Registry   │  │   Store      │  │   Engine     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓                  ↓                           │
│  ┌─────────────────────────────────────────────────┐  │
│  │        Universal Engine (IP Management)         │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Format Detector
- **Input**: Binary file + optional MIME type
- **Output**: Format identification + grammar reference
- **Technology**: Magic byte analysis, structure patterns, MIME validation
- **Supported Formats**: 69+ formats (see FORMATS_SUPPORTED.md)

#### 2. Grammar Registry
- **Purpose**: Store and manage format grammars
- **Contents**: Format specifications, structure rules, validation patterns
- **Format**: Declarative grammar definitions (EBNF-style)
- **Extensibility**: Plugin architecture for new formats

#### 3. Decomposer Engine
- **Input**: File + grammar
- **Output**: Content-addressed primitives + reconstruction metadata
- **Algorithm**:
  1. Parse file according to grammar
  2. Extract logical chunks (headers, payloads, metadata)
  3. Store chunks in content-addressed storage
  4. Generate reconstruction recipe

#### 4. Content Store
- **Type**: Content-addressed storage (SHA-256)
- **Features**:
  - Automatic deduplication
  - Immutable objects
  - Derivation tracking
  - IP metadata (via Universal Engine)

#### 5. Reconstructor Engine
- **Input**: Reconstruction recipe + primitives
- **Output**: Reconstructed file (bit-identical)
- **Guarantees**: Lossless reconstruction, validation checks

#### 6. Validation Engine
- **Purpose**: Verify reconstruction integrity
- **Checks**:
  - Binary equality
  - Format-specific validation
  - Semantic equivalence
  - Hash verification

---

## 🔄 Processing Pipeline

### Ingestion (Decomposition)

```
File → Detect Format → Load Grammar → Parse Structure →
  Extract Chunks → Store Primitives → Generate Recipe →
    Register IP Metadata → Return Recipe ID
```

### Retrieval (Reconstruction)

```
Recipe ID → Load Recipe → Fetch Primitives →
  Reassemble Structure → Validate Output →
    Return File
```

---

## 📦 Data Model

### File Ingestion Record

```rust
struct IngestionRecord {
    /// Unique identifier (SHA-256 of original file)
    file_id: ContentHash,
    
    /// Original filename and metadata
    metadata: FileMetadata,
    
    /// Detected format
    format: FormatInfo,
    
    /// Grammar used for decomposition
    grammar_id: GrammarId,
    
    /// Decomposition result
    primitives: Vec<PrimitiveRef>,
    
    /// Reconstruction recipe
    recipe: ReconstructionRecipe,
    
    /// IP metadata
    ip_metadata: IPMetadata,
    
    /// Ingestion timestamp
    created_at: DateTime<Utc>,
}
```

### Format Grammar

```rust
struct FormatGrammar {
    /// Grammar unique identifier
    id: GrammarId,
    
    /// Format name
    format: String,
    
    /// MIME types
    mime_types: Vec<String>,
    
    /// Magic bytes for detection
    magic_bytes: Vec<MagicPattern>,
    
    /// Structure definition
    structure: GrammarDefinition,
    
    /// Validation rules
    validators: Vec<ValidationRule>,
    
    /// Metadata extractors
    extractors: Vec<MetadataExtractor>,
}
```

### Primitive

```rust
struct Primitive {
    /// Content hash (SHA-256)
    id: ContentHash,
    
    /// Binary content
    content: Vec<u8>,
    
    /// Type classification
    primitive_type: PrimitiveType,
    
    /// Metadata
    metadata: HashMap<String, Value>,
    
    /// Provenance
    provenance: ProvenanceInfo,
}

enum PrimitiveType {
    Header,
    Payload,
    Metadata,
    Checksum,
    Structure,
    Compressed,
    Raw,
}
```

### Reconstruction Recipe

```rust
struct ReconstructionRecipe {
    /// Recipe identifier
    id: RecipeId,
    
    /// Original file hash
    file_hash: ContentHash,
    
    /// Grammar to use
    grammar_id: GrammarId,
    
    /// Assembly instructions
    instructions: Vec<ReconstructionStep>,
    
    /// Validation checkpoints
    validators: Vec<ValidationCheckpoint>,
}

struct ReconstructionStep {
    /// Step number (ordered)
    order: u32,
    
    /// Operation type
    operation: Operation,
    
    /// Input primitives
    inputs: Vec<ContentHash>,
    
    /// Parameters
    params: HashMap<String, Value>,
}

enum Operation {
    Concatenate,
    Decompress,
    ApplyHeader,
    ApplyChecksum,
    Transform { function: String },
    Validate,
}
```

---

## 🎨 Grammar Definition Language

### Example: PNG Grammar

```ebnf
PNG := Signature ChunkList
Signature := 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A
ChunkList := Chunk+
Chunk := Length ChunkType ChunkData CRC

Length := U32_BE
ChunkType := BYTE[4]
ChunkData := BYTE[Length]
CRC := U32_BE

# Critical Chunks
IHDR := Width Height BitDepth ColorType Compression Filter Interlace
PLTE := ColorEntry[1..256]
IDAT := CompressedImageData
IEND := Empty

# Decomposition Rules
DECOMPOSE Signature → HEADER_PRIMITIVE
DECOMPOSE IHDR → METADATA_PRIMITIVE
DECOMPOSE PLTE → METADATA_PRIMITIVE
DECOMPOSE IDAT → COMPRESSED_PAYLOAD_PRIMITIVE
DECOMPOSE IEND → STRUCTURE_PRIMITIVE
```

### Grammar Features

- **Declarative structure definition**
- **Decomposition rules** specify how to split content
- **Validation rules** ensure correctness
- **Metadata extraction** rules identify important fields
- **Reconstruction hints** optimize reassembly

---

## 🔧 Implementation Guidelines

### Rust Core (Backend)

**Modules**:
- `format_detector/` - Format detection engine
- `grammar/` - Grammar parser and registry
- `decomposer/` - Decomposition engine
- `reconstructor/` - Reconstruction engine
- `store/` - Content-addressed storage
- `validator/` - Validation engine
- `ip_integration/` - Universal Engine integration

**Key Traits**:

```rust
trait FormatDetector {
    fn detect(&self, data: &[u8]) -> Result<FormatInfo>;
}

trait GrammarRegistry {
    fn get_grammar(&self, format: &str) -> Result<Arc<Grammar>>;
    fn register_grammar(&mut self, grammar: Grammar) -> Result<()>;
}

trait Decomposer {
    fn decompose(&self, file: &[u8], grammar: &Grammar) 
        -> Result<DecompositionResult>;
}

trait Reconstructor {
    fn reconstruct(&self, recipe: &Recipe, store: &dyn Store) 
        -> Result<Vec<u8>>;
}
```

**Dependencies**:
- `tokio` - Async runtime
- `serde` - Serialization
- `sha2` - SHA-256 hashing
- `flate2` - Compression support
- `pest` - Grammar parsing
- `bytes` - Efficient byte handling

### TypeScript API (Frontend)

**Modules**:
- `client/` - API client
- `types/` - Type definitions
- `formats/` - Format-specific helpers
- `validation/` - Client-side validation

**Key Interfaces**:

```typescript
interface PaniniFS {
  ingest(file: File): Promise<IngestionResult>;
  reconstruct(recipeId: string): Promise<Blob>;
  validate(recipeId: string, originalFile: File): Promise<ValidationResult>;
  getSupportedFormats(): Promise<FormatInfo[]>;
  getFormatStats(format: string): Promise<FormatStats>;
}

interface IngestionResult {
  fileId: string;
  recipeId: string;
  originalSize: number;
  primitivesCount: number;
  compressionRatio: number;
  format: FormatInfo;
}

interface ValidationResult {
  isValid: boolean;
  checks: ValidationCheck[];
  errors: string[];
}
```

**Dependencies**:
- `@panini/client` - Panini-FS client library
- `zod` - Runtime validation
- `typescript` - Type safety

---

## 🚀 Performance Requirements

### Decomposition

- **Throughput**: > 100 MB/s for common formats
- **Latency**: < 100ms for files < 10MB
- **Memory**: O(log n) for streaming processing
- **Concurrency**: Thread-safe, async-first

### Reconstruction

- **Throughput**: > 200 MB/s (faster than decomposition)
- **Latency**: < 50ms for files < 10MB
- **Validation**: < 10% overhead
- **Accuracy**: 100% bit-identical

### Storage

- **Deduplication**: Automatic, zero-overhead
- **Compression ratio**: 20-80% depending on format
- **Lookup**: O(1) content-addressed retrieval

---

## 🔒 Security Considerations

### Input Validation

- Magic byte verification
- Size limits enforcement
- Format-specific constraints
- Grammar validation

### Content Addressing

- SHA-256 for collision resistance
- Cryptographic integrity
- Tamper detection via Universal Engine

### Access Control

- IP metadata via Universal Engine
- Permission inheritance
- Audit trails

---

## 🧪 Testing Strategy

### Unit Tests

- Format detection accuracy (> 99.9%)
- Grammar parsing correctness
- Decomposition/reconstruction roundtrips
- Validation logic

### Integration Tests

- End-to-end ingestion → reconstruction
- Multi-format pipelines
- Universal Engine integration
- Performance benchmarks

### Format-Specific Tests

- One test suite per supported format
- Real-world file samples
- Edge cases and malformed inputs
- Compression ratio validation

**Test Corpus**: See `research/shared/test_samples/`

---

## 📊 Metrics & Monitoring

### Key Metrics

- **Ingestion rate**: Files/second by format
- **Compression ratio**: Original size / stored size
- **Reconstruction success rate**: % bit-identical
- **Format coverage**: % of real-world files supported
- **Performance**: p50, p95, p99 latencies

### Logging

- Structured JSON logs
- Distributed tracing (OpenTelemetry)
- Error categorization
- Audit integration with Universal Engine

---

## 🔮 Future Enhancements

### Phase 2

- Semantic search across primitives
- Cross-format transformations
- Format migration tools
- AI-powered grammar inference

### Phase 3

- Distributed storage backend
- Real-time streaming support
- Format fingerprinting
- Advanced compression techniques

---

## 📚 References

- Research prototypes: `research/panini-fs/prototypes/`
- Format specifications: `research/panini-fs/docs/`
- Universal Engine: `research/universal-engine/`
- Benchmarks: `research/panini-fs/benchmarks/`

---

**Next**: See `RUST_IMPLEMENTATION_SPEC.md` and `TYPESCRIPT_IMPLEMENTATION_SPEC.md` for detailed implementation guidance.
