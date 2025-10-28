# Panini-FS Rust Implementation Specification

**Target**: Rust 1.70+  
**Architecture**: Async-first, modular, high-performance

---

## 🏗️ Project Structure

```
panini-fs-rust/
├── Cargo.toml
├── src/
│   ├── lib.rs                  # Public API
│   ├── format_detector/        # Format detection
│   │   ├── mod.rs
│   │   ├── magic.rs           # Magic byte matching
│   │   └── mime.rs            # MIME type validation
│   ├── grammar/                # Grammar system
│   │   ├── mod.rs
│   │   ├── parser.rs          # Grammar parser
│   │   ├── registry.rs        # Grammar storage
│   │   └── definitions/       # Built-in grammars
│   ├── decomposer/             # Decomposition engine
│   │   ├── mod.rs
│   │   ├── engine.rs
│   │   └── strategies/        # Format-specific strategies
│   ├── reconstructor/          # Reconstruction engine
│   │   ├── mod.rs
│   │   └── engine.rs
│   ├── store/                  # Content-addressed storage
│   │   ├── mod.rs
│   │   ├── content_store.rs
│   │   └── recipe_store.rs
│   ├── validator/              # Validation
│   │   ├── mod.rs
│   │   └── engine.rs
│   ├── ip_integration/         # Universal Engine integration
│   │   ├── mod.rs
│   │   └── adapter.rs
│   └── types/                  # Shared types
│       ├── mod.rs
│       ├── hash.rs
│       ├── recipe.rs
│       └── format.rs
├── tests/
│   ├── integration/
│   └── fixtures/
└── benches/
    └── performance.rs
```

---

## 📦 Core Types

### Cargo.toml

```toml
[package]
name = "panini-fs"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1.32", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sha2 = "0.10"
bytes = "1.5"
thiserror = "1.0"
anyhow = "1.0"
pest = "2.7"
pest_derive = "2.7"
flate2 = "1.0"
async-trait = "0.1"
tracing = "0.1"
tracing-subscriber = "0.3"

[dev-dependencies]
criterion = "0.5"
tempfile = "3.8"
proptest = "1.2"
```

### Key Types (src/types/mod.rs)

```rust
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Content hash (SHA-256)
#[derive(Clone, Debug, Hash, Eq, PartialEq, Serialize, Deserialize)]
pub struct ContentHash([u8; 32]);

impl ContentHash {
    pub fn new(data: &[u8]) -> Self {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(data);
        Self(hasher.finalize().into())
    }
    
    pub fn to_hex(&self) -> String {
        hex::encode(&self.0)
    }
}

/// Format information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FormatInfo {
    pub name: String,
    pub mime_type: String,
    pub extension: Option<String>,
    pub version: Option<String>,
}

/// Primitive type classification
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PrimitiveType {
    Header,
    Payload,
    Metadata,
    Checksum,
    Structure,
    Compressed,
    Raw,
}

/// Reconstruction operation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Operation {
    Concatenate,
    Decompress,
    ApplyHeader,
    ApplyChecksum,
    Transform { function: String },
    Validate,
}
```

---

## 🔍 Format Detector

### src/format_detector/mod.rs

```rust
use anyhow::Result;
use crate::types::FormatInfo;

#[async_trait::async_trait]
pub trait FormatDetector: Send + Sync {
    async fn detect(&self, data: &[u8]) -> Result<FormatInfo>;
    fn supported_formats(&self) -> Vec<String>;
}

pub struct MagicByteDetector {
    patterns: HashMap<Vec<u8>, FormatInfo>,
}

impl MagicByteDetector {
    pub fn new() -> Self {
        let mut patterns = HashMap::new();
        
        // PNG
        patterns.insert(
            vec![0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A],
            FormatInfo {
                name: "PNG".to_string(),
                mime_type: "image/png".to_string(),
                extension: Some("png".to_string()),
                version: None,
            },
        );
        
        // JPEG
        patterns.insert(
            vec![0xFF, 0xD8, 0xFF],
            FormatInfo {
                name: "JPEG".to_string(),
                mime_type: "image/jpeg".to_string(),
                extension: Some("jpg".to_string()),
                version: None,
            },
        );
        
        // Add more formats...
        
        Self { patterns }
    }
}

#[async_trait::async_trait]
impl FormatDetector for MagicByteDetector {
    async fn detect(&self, data: &[u8]) -> Result<FormatInfo> {
        for (magic, format) in &self.patterns {
            if data.starts_with(magic) {
                return Ok(format.clone());
            }
        }
        Err(anyhow::anyhow!("Unknown format"))
    }
    
    fn supported_formats(&self) -> Vec<String> {
        self.patterns.values().map(|f| f.name.clone()).collect()
    }
}
```

---

## 🎨 Grammar System

### src/grammar/mod.rs

```rust
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Grammar {
    pub id: String,
    pub format: String,
    pub mime_types: Vec<String>,
    pub magic_bytes: Vec<Vec<u8>>,
    pub structure: GrammarDefinition,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GrammarDefinition {
    pub rules: Vec<GrammarRule>,
    pub decomposition: Vec<DecompositionRule>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GrammarRule {
    pub name: String,
    pub pattern: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DecompositionRule {
    pub source: String,
    pub target: PrimitiveType,
}

pub trait GrammarRegistry: Send + Sync {
    fn get_grammar(&self, format: &str) -> Result<Arc<Grammar>>;
    fn register_grammar(&mut self, grammar: Grammar) -> Result<()>;
    fn list_grammars(&self) -> Vec<String>;
}
```

---

## ⚙️ Decomposer Engine

### src/decomposer/mod.rs

```rust
use anyhow::Result;
use crate::{Grammar, ContentHash, PrimitiveType};

#[derive(Debug)]
pub struct Primitive {
    pub id: ContentHash,
    pub content: Vec<u8>,
    pub primitive_type: PrimitiveType,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug)]
pub struct DecompositionResult {
    pub primitives: Vec<Primitive>,
    pub recipe: ReconstructionRecipe,
    pub stats: DecompositionStats,
}

#[derive(Debug)]
pub struct DecompositionStats {
    pub original_size: usize,
    pub primitives_count: usize,
    pub compression_ratio: f64,
}

#[async_trait::async_trait]
pub trait Decomposer: Send + Sync {
    async fn decompose(
        &self,
        data: &[u8],
        grammar: &Grammar,
    ) -> Result<DecompositionResult>;
}

pub struct GrammarBasedDecomposer;

#[async_trait::async_trait]
impl Decomposer for GrammarBasedDecomposer {
    async fn decompose(
        &self,
        data: &[u8],
        grammar: &Grammar,
    ) -> Result<DecompositionResult> {
        // Parse data according to grammar
        // Extract chunks
        // Generate primitives
        // Create reconstruction recipe
        
        todo!("Implementation delegated to GitHub agents")
    }
}
```

---

## 🔧 Reconstructor Engine

### src/reconstructor/mod.rs

```rust
use anyhow::Result;
use crate::{ReconstructionRecipe, Store};

#[async_trait::async_trait]
pub trait Reconstructor: Send + Sync {
    async fn reconstruct(
        &self,
        recipe: &ReconstructionRecipe,
        store: &dyn Store,
    ) -> Result<Vec<u8>>;
}

pub struct DefaultReconstructor;

#[async_trait::async_trait]
impl Reconstructor for DefaultReconstructor {
    async fn reconstruct(
        &self,
        recipe: &ReconstructionRecipe,
        store: &dyn Store,
    ) -> Result<Vec<u8>> {
        let mut output = Vec::new();
        
        for step in &recipe.instructions {
            match &step.operation {
                Operation::Concatenate => {
                    for input_hash in &step.inputs {
                        let data = store.get(input_hash).await?;
                        output.extend_from_slice(&data);
                    }
                }
                Operation::Decompress => {
                    // Decompression logic
                    todo!()
                }
                _ => todo!("Other operations"),
            }
        }
        
        Ok(output)
    }
}
```

---

## 💾 Content Store

### src/store/mod.rs

```rust
use anyhow::Result;
use crate::ContentHash;

#[async_trait::async_trait]
pub trait Store: Send + Sync {
    async fn put(&self, data: Vec<u8>) -> Result<ContentHash>;
    async fn get(&self, hash: &ContentHash) -> Result<Vec<u8>>;
    async fn exists(&self, hash: &ContentHash) -> Result<bool>;
    async fn delete(&self, hash: &ContentHash) -> Result<()>;
}

pub struct FileSystemStore {
    base_path: std::path::PathBuf,
}

#[async_trait::async_trait]
impl Store for FileSystemStore {
    async fn put(&self, data: Vec<u8>) -> Result<ContentHash> {
        let hash = ContentHash::new(&data);
        let path = self.hash_to_path(&hash);
        tokio::fs::create_dir_all(path.parent().unwrap()).await?;
        tokio::fs::write(&path, data).await?;
        Ok(hash)
    }
    
    async fn get(&self, hash: &ContentHash) -> Result<Vec<u8>> {
        let path = self.hash_to_path(hash);
        tokio::fs::read(path).await.map_err(Into::into)
    }
    
    async fn exists(&self, hash: &ContentHash) -> Result<bool> {
        let path = self.hash_to_path(hash);
        Ok(path.exists())
    }
    
    async fn delete(&self, hash: &ContentHash) -> Result<()> {
        let path = self.hash_to_path(hash);
        tokio::fs::remove_file(path).await.map_err(Into::into)
    }
}

impl FileSystemStore {
    fn hash_to_path(&self, hash: &ContentHash) -> std::path::PathBuf {
        let hex = hash.to_hex();
        self.base_path.join(&hex[..2]).join(&hex[2..4]).join(&hex)
    }
}
```

---

## 🧪 Testing Guidelines

### Integration Tests (tests/integration/roundtrip.rs)

```rust
#[tokio::test]
async fn test_png_roundtrip() {
    let panini_fs = PaniniFS::new("./test_store").await.unwrap();
    
    // Load test PNG
    let original = include_bytes!("../fixtures/test.png");
    
    // Ingest
    let result = panini_fs.ingest(original).await.unwrap();
    
    // Reconstruct
    let reconstructed = panini_fs.reconstruct(&result.recipe_id).await.unwrap();
    
    // Validate bit-identical
    assert_eq!(original.as_slice(), reconstructed.as_slice());
}
```

---

## 🚀 Performance Targets

- **Ingestion**: > 100 MB/s
- **Reconstruction**: > 200 MB/s
- **Memory**: < 100 MB per instance
- **Concurrency**: Support 1000+ simultaneous operations

---

**Next**: TypeScript client implementation in `TYPESCRIPT_IMPLEMENTATION_SPEC.md`
