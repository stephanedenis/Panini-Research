# PaniniFS v4.0 - Content-Addressed Pattern System (CAPS)

## 🎯 Vision Fondamentale: Double-Hash Architecture

**Principe Pāṇinien Étendu**: Chaque objet (pattern, grammar, file) est:
1. **Identifié** par hash de contenu exact (SHA-256) → immutabilité, deduplication
2. **Découvrable** par hash de ressemblance (entropie-négentropie) → généralisation, approximation

---

## 📐 Architecture Conceptuelle

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTENT-ADDRESSED STORE (CAS)                  │
│                     Git/IPFS-style immutability                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OBJECTS/ (stored by exact hash)                                │
│  ├── patterns/                                                  │
│  │   ├── a7f3d912e4c5b8f0/  # MAGIC_NUMBER pattern             │
│  │   │   ├── definition.json                                   │
│  │   │   ├── similarity_hash: e8d7c6b5                         │
│  │   │   └── metadata.json                                     │
│  │   ├── c2d4e6f8a0b1c3d5/  # CHUNK_STRUCTURE pattern          │
│  │   │   ├── definition.json                                   │
│  │   │   ├── similarity_hash: f9e8d7c6                         │
│  │   │   └── metadata.json                                     │
│  │   └── ...                                                    │
│  │                                                              │
│  ├── grammars/                                                  │
│  │   ├── b3f9a2c1d5e7f8a4/  # PNG grammar v1.0                 │
│  │   │   ├── grammar.yml                                       │
│  │   │   ├── similarity_hash: a1b2c3d4                         │
│  │   │   ├── pattern_refs: [a7f3d912, c2d4e6f8, ...]          │
│  │   │   └── metadata.json                                     │
│  │   ├── 8f7e6d5c4b3a2918/  # JPEG grammar v1.0                │
│  │   │   ├── grammar.yml                                       │
│  │   │   ├── similarity_hash: a1b2c3d8  # ← Similar to PNG!   │
│  │   │   └── ...                                               │
│  │   └── ...                                                    │
│  │                                                              │
│  ├── files/                                                     │
│  │   ├── 9d8e7f6a5b4c3d2e/  # example.png (original bytes)     │
│  │   │   ├── content (raw bytes)                               │
│  │   │   ├── similarity_hash: 1a2b3c4d                         │
│  │   │   └── detected_grammar: b3f9a2c1                        │
│  │   └── ...                                                    │
│  │                                                              │
│  └── extractions/                                               │
│      ├── 4a3b2c1d0e9f8g7h/  # Metadata from 9d8e7f6a5b4c3d2e  │
│      │   ├── metadata.json                                     │
│      │   ├── source_file: 9d8e7f6a5b4c3d2e                     │
│      │   ├── grammar_used: b3f9a2c1d5e7f8a4                    │
│      │   └── timestamp                                          │
│      └── ...                                                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│              SIMILARITY INDEX (Entropy-based)                   │
│           For discovering related patterns/grammars             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SIMILARITY_MAP/                                                │
│  ├── patterns/                                                  │
│  │   ├── e8d7c6b5 → [a7f3d912, b8c9d0e1, ...]  # Similar to   │
│  │   │                        MAGIC_NUMBER variants            │
│  │   ├── f9e8d7c6 → [c2d4e6f8, d3e5f7a9, ...]  # CHUNK-like   │
│  │   │                        structures                       │
│  │   └── ...                                                    │
│  │                                                              │
│  ├── grammars/                                                  │
│  │   ├── a1b2c3d4 → [b3f9a2c1, 8f7e6d5c, ...]  # Image formats │
│  │   ├── e5f6a7b8 → [3c4d5e6f, 7g8h9i0j, ...]  # Audio formats │
│  │   └── ...                                                    │
│  │                                                              │
│  └── entropy_clusters/                                          │
│      ├── high_structure/  # Low entropy (highly structured)    │
│      ├── medium_mix/      # Medium entropy                     │
│      └── high_entropy/    # High entropy (compressed/encrypted)│
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      SYMBOLIC REFS                              │
│              Human-readable names → hashes                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  refs/                                                          │
│  ├── patterns/                                                  │
│  │   ├── MAGIC_NUMBER → a7f3d912e4c5b8f0                       │
│  │   ├── CHUNK_STRUCTURE → c2d4e6f8a0b1c3d5                    │
│  │   ├── KEY_VALUE → d5e7f9a1b3c5d7e9                          │
│  │   └── ...                                                    │
│  │                                                              │
│  ├── grammars/                                                  │
│  │   ├── PNG/latest → b3f9a2c1d5e7f8a4                         │
│  │   ├── PNG/v1.0 → b3f9a2c1d5e7f8a4                           │
│  │   ├── JPEG/latest → 8f7e6d5c4b3a2918                        │
│  │   └── ...                                                    │
│  │                                                              │
│  └── files/                                                     │
│      ├── examples/test.png → 9d8e7f6a5b4c3d2e                  │
│      └── ...                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔢 Double-Hash System

### 1. **Exact Hash (Identity)**

**Purpose**: Immutability, deduplication, verification

**Algorithm**: SHA-256 (truncated to 16 hex chars for readability)

```python
def compute_exact_hash(content: bytes) -> str:
    """
    Compute exact content hash (SHA-256).
    
    Returns:
        16-char hex string (first 64 bits of SHA-256)
    """
    import hashlib
    full_hash = hashlib.sha256(content).hexdigest()
    return full_hash[:16]  # "a7f3d912e4c5b8f0"

# Example: Pattern definition
pattern_def = {
    "type": "MAGIC_NUMBER",
    "version": "1.0",
    "fields": {
        "offset": 0,
        "signature": "89504E47",
        "length": 8
    }
}

import json
pattern_bytes = json.dumps(pattern_def, sort_keys=True).encode('utf-8')
exact_hash = compute_exact_hash(pattern_bytes)
# → "a7f3d912e4c5b8f0"
```

**Properties**:
- **Deterministic**: Same content → same hash
- **Immutable**: Content cannot change without hash changing
- **Collision-resistant**: SHA-256 collision probability ≈ 0
- **Deduplication**: Identical patterns stored once

---

### 2. **Similarity Hash (Fuzzy Matching)**

**Purpose**: Discover similar patterns, suggest generalizations, approximate missing content

**Algorithm**: Entropy + Négentropie (Information-Theoretic Similarity)

```python
import math
from collections import Counter
from typing import Dict, Any

def compute_entropy(data: bytes) -> float:
    """
    Shannon entropy H(X) = -Σ p(x) log₂ p(x)
    
    Measures randomness/disorder.
    - Low entropy (0.0): Highly structured (e.g., all zeros)
    - High entropy (8.0): Random/compressed data
    """
    if not data:
        return 0.0
    
    byte_counts = Counter(data)
    total = len(data)
    
    entropy = 0.0
    for count in byte_counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    
    return entropy


def compute_negentropy(data: bytes) -> float:
    """
    Négentropie = Max_Entropy - Actual_Entropy
    
    Measures structure/order (inverse of entropy).
    - High négentropie: Structured data (patterns, repetitions)
    - Low négentropie: Random data
    """
    max_entropy = 8.0  # Maximum for byte data (2^8 = 256 symbols)
    return max_entropy - compute_entropy(data)


def extract_structural_features(content: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract structural features for similarity comparison.
    
    Features:
    - field_count: Number of fields in pattern
    - nesting_depth: Maximum nesting level
    - type_diversity: Shannon entropy of field types
    - repetition_score: Proportion of repeating structures
    """
    features = {}
    
    # Field count (normalized)
    if 'fields' in content:
        features['field_count'] = len(content['fields']) / 100.0
    
    # Type diversity
    if 'fields' in content:
        types = [f.get('type', 'unknown') for f in content['fields']]
        type_counts = Counter(types)
        type_entropy = 0.0
        total = len(types)
        for count in type_counts.values():
            p = count / total
            type_entropy -= p * math.log2(p) if p > 0 else 0
        features['type_diversity'] = type_entropy / 5.0  # Normalize
    
    # Repetition indicator
    features['has_repetition'] = 1.0 if content.get('repeating', False) else 0.0
    
    return features


def compute_similarity_hash(content: bytes, metadata: Dict[str, Any] = None) -> str:
    """
    Compute fuzzy similarity hash combining:
    1. Entropy (randomness measure)
    2. Négentropie (structure measure)
    3. Structural features (field types, nesting, etc.)
    
    Returns:
        8-char hex string encoding similarity signature
    """
    # 1. Entropy component (4 bits)
    entropy = compute_entropy(content)
    entropy_nibble = int((entropy / 8.0) * 15)  # Scale to 0-15
    
    # 2. Négentropie component (4 bits)
    negentropy = compute_negentropy(content)
    negentropy_nibble = int((negentropy / 8.0) * 15)
    
    # 3. Structural features (if metadata provided)
    if metadata:
        features = extract_structural_features(metadata)
        
        # Field count (4 bits)
        field_nibble = int(features.get('field_count', 0) * 15)
        
        # Type diversity (4 bits)
        type_nibble = int(features.get('type_diversity', 0) * 15)
        
        # Repetition (4 bits)
        rep_nibble = int(features.get('has_repetition', 0) * 15)
        
        # Reserved (4 bits)
        reserved = 0
    else:
        # No structural metadata, use content-only features
        field_nibble = 0
        type_nibble = 0
        rep_nibble = 0
        reserved = 0
    
    # Combine into 32-bit hash (8 hex chars)
    similarity_int = (
        (entropy_nibble << 28) |
        (negentropy_nibble << 24) |
        (field_nibble << 20) |
        (type_nibble << 16) |
        (rep_nibble << 12) |
        (reserved << 8) |
        # Last 8 bits: checksum of content
        (sum(content) & 0xFF)
    )
    
    return f"{similarity_int:08x}"  # "e8d7c6b5"


# Example: Two similar patterns
magic_png = {
    "type": "MAGIC_NUMBER",
    "fields": {"offset": 0, "signature": "89504E47", "length": 8}
}

magic_jpeg = {
    "type": "MAGIC_NUMBER",
    "fields": {"offset": 0, "signature": "FFD8FF", "length": 3}
}

png_bytes = json.dumps(magic_png, sort_keys=True).encode()
jpeg_bytes = json.dumps(magic_jpeg, sort_keys=True).encode()

sim_png = compute_similarity_hash(png_bytes, magic_png)
sim_jpeg = compute_similarity_hash(jpeg_bytes, magic_jpeg)

# sim_png ≈ sim_jpeg (same nibbles for entropy, structure)
# → Discoverable as similar patterns!
```

**Properties**:
- **Fuzzy matching**: Similar patterns → similar hashes
- **Entropy-aware**: Detects structured vs random data
- **Structure-sensitive**: Field count, types, nesting affect hash
- **Clustering**: Patterns with similar hashes can be grouped

---

## 🔍 Use Cases for Double-Hash System

### Use Case 1: **Automatic Deduplication**

```python
# Store pattern with exact hash
pattern_def = {...}
exact_hash = store_pattern(pattern_def)
# → "a7f3d912e4c5b8f0"

# Later: Try to store identical pattern
pattern_def2 = {...}  # Same content
exact_hash2 = store_pattern(pattern_def2)
# → "a7f3d912e4c5b8f0" (same hash, not stored again!)
```

---

### Use Case 2: **Discover Similar Patterns**

```python
# Find patterns similar to MAGIC_NUMBER
query_pattern = load_pattern("a7f3d912e4c5b8f0")
sim_hash = query_pattern.similarity_hash  # "e8d7c6b5"

similar_patterns = similarity_index.query(sim_hash, threshold=0.8)
# → [
#   ("b8c9d0e1f2a3b4c5", 0.95),  # MAGIC_NUMBER variant (JPEG)
#   ("c9d0e1f2a3b4c5d6", 0.87),  # MAGIC_NUMBER variant (GIF)
#   ...
# ]
```

---

### Use Case 3: **Generalization Discovery**

```python
# Cluster similar patterns
magic_cluster = get_similarity_cluster("e8d7c6b5")
# → [MAGIC_NUMBER_PNG, MAGIC_NUMBER_JPEG, MAGIC_NUMBER_GIF, ...]

# Suggest generalization
generalized_pattern = suggest_generalization(magic_cluster)
# → {
#   "type": "MAGIC_NUMBER_GENERIC",
#   "fields": {
#     "offset": 0,
#     "signature": "VARIABLE",  # ← Parameterized!
#     "length": "VARIABLE"
#   },
#   "instances": [
#     {"format": "PNG", "signature": "89504E47", "length": 8},
#     {"format": "JPEG", "signature": "FFD8FF", "length": 3},
#     ...
#   ]
# }
```

---

### Use Case 4: **Approximate Missing Content**

```python
# User wants to parse unknown format
unknown_file = read_bytes("mystery.bin")
file_entropy = compute_entropy(unknown_file[:1024])
file_sim_hash = compute_similarity_hash(unknown_file[:1024])

# Find grammars with similar structure
candidates = similarity_index.query_grammars(
    file_sim_hash,
    entropy_range=(file_entropy - 1.0, file_entropy + 1.0)
)
# → [
#   ("PNG", 0.82),  # Similar entropy and structure
#   ("BMP", 0.79),  # Also image format
#   ...
# ]

# Try parsing with top candidate
best_grammar = candidates[0][0]
result = parse_with_grammar(unknown_file, best_grammar)
```

---

### Use Case 5: **Grammar Evolution Tracking**

```python
# PNG grammar v1.0
png_v1_hash = "b3f9a2c1d5e7f8a4"
png_v1_sim = "a1b2c3d4"

# PNG grammar v1.1 (added new chunk type)
png_v1_1_hash = "c4e0b2d6f8a0c2e4"  # ← Different exact hash
png_v1_1_sim = "a1b2c3d5"           # ← Very similar!

# Discover evolution
related_grammars = get_similarity_neighbors("a1b2c3d4")
# → [
#   ("b3f9a2c1d5e7f8a4", 1.00, "PNG v1.0"),    # Exact match
#   ("c4e0b2d6f8a0c2e4", 0.98, "PNG v1.1"),    # Very close
#   ("8f7e6d5c4b3a2918", 0.75, "JPEG v1.0"),   # Different but related
# ]
```

---

## 🛠️ Implementation: Content-Addressed Storage

### Core Storage Interface

```python
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json
import hashlib

class ContentAddressedStore:
    """
    Git/IPFS-style content-addressed storage for PaniniFS.
    
    All objects (patterns, grammars, files) stored by exact hash.
    Similarity index maintained separately for discovery.
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.objects_path = base_path / "objects"
        self.refs_path = base_path / "refs"
        self.similarity_path = base_path / "similarity"
        
        # Create directories
        self.objects_path.mkdir(parents=True, exist_ok=True)
        self.refs_path.mkdir(parents=True, exist_ok=True)
        self.similarity_path.mkdir(parents=True, exist_ok=True)
    
    def store_object(
        self,
        content: bytes,
        object_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Store object with double-hash.
        
        Args:
            content: Raw bytes of object
            object_type: "pattern", "grammar", "file", "extraction"
            metadata: Optional structural metadata for similarity hash
        
        Returns:
            (exact_hash, similarity_hash)
        """
        # Compute exact hash
        exact_hash = compute_exact_hash(content)
        
        # Compute similarity hash
        similarity_hash = compute_similarity_hash(content, metadata)
        
        # Object directory
        obj_dir = self.objects_path / object_type / exact_hash[:2] / exact_hash
        obj_dir.mkdir(parents=True, exist_ok=True)
        
        # Store content
        (obj_dir / "content").write_bytes(content)
        
        # Store metadata
        meta = metadata or {}
        meta['exact_hash'] = exact_hash
        meta['similarity_hash'] = similarity_hash
        meta['object_type'] = object_type
        (obj_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2, sort_keys=True)
        )
        
        # Update similarity index
        self._index_similarity(object_type, exact_hash, similarity_hash)
        
        return exact_hash, similarity_hash
    
    def load_object(self, exact_hash: str, object_type: str) -> Optional[bytes]:
        """Load object by exact hash"""
        obj_path = (
            self.objects_path / object_type / exact_hash[:2] / 
            exact_hash / "content"
        )
        
        if obj_path.exists():
            return obj_path.read_bytes()
        return None
    
    def find_similar(
        self,
        similarity_hash: str,
        object_type: str,
        threshold: float = 0.8
    ) -> List[Tuple[str, float]]:
        """
        Find objects with similar hashes.
        
        Returns:
            List of (exact_hash, similarity_score) tuples
        """
        # Load similarity index
        index_file = self.similarity_path / object_type / f"{similarity_hash}.json"
        
        if not index_file.exists():
            return []
        
        index = json.loads(index_file.read_text())
        
        # Compute similarity scores
        results = []
        for entry in index:
            score = self._compute_similarity_score(
                similarity_hash,
                entry['similarity_hash']
            )
            if score >= threshold:
                results.append((entry['exact_hash'], score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _index_similarity(
        self,
        object_type: str,
        exact_hash: str,
        similarity_hash: str
    ):
        """Update similarity index"""
        index_dir = self.similarity_path / object_type
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Group by first 4 chars of similarity hash (coarse buckets)
        bucket = similarity_hash[:4]
        index_file = index_dir / f"{bucket}.json"
        
        # Load or create index
        if index_file.exists():
            index = json.loads(index_file.read_text())
        else:
            index = []
        
        # Add entry
        index.append({
            'exact_hash': exact_hash,
            'similarity_hash': similarity_hash
        })
        
        # Save
        index_file.write_text(json.dumps(index, indent=2))
    
    def _compute_similarity_score(self, hash1: str, hash2: str) -> float:
        """
        Compute similarity score between two similarity hashes.
        
        Compares nibbles (4-bit chunks) and returns proportion matching.
        """
        if len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)
```

---

## 📊 Pattern Storage Example

```python
# Initialize store
store = ContentAddressedStore(Path("/home/user/.panini/store"))

# Store MAGIC_NUMBER pattern
pattern_def = {
    "type": "MAGIC_NUMBER",
    "version": "1.0",
    "description": "PNG magic number signature",
    "fields": {
        "offset": 0,
        "signature": "89504E47",
        "length": 8,
        "required": True
    }
}

pattern_bytes = json.dumps(pattern_def, sort_keys=True).encode()
exact, similarity = store.store_object(
    pattern_bytes,
    "pattern",
    metadata=pattern_def
)

print(f"Exact hash: {exact}")       # "a7f3d912e4c5b8f0"
print(f"Similarity hash: {similarity}")  # "e8d7c6b5"

# Create symbolic ref
refs_dir = store.refs_path / "patterns"
refs_dir.mkdir(exist_ok=True)
(refs_dir / "MAGIC_NUMBER").write_text(exact)

# Later: Find similar patterns
similar = store.find_similar("e8d7c6b5", "pattern", threshold=0.75)
# → [("b8c9d0e1f2a3b4c5", 0.92), ...]
```

---

## 🎯 Next Steps

1. **Implement ContentAddressedStore** with double-hash
2. **Migrate patterns** to CAS (70 patterns → content-addressed)
3. **Build similarity index** for pattern discovery
4. **Create grammar loader** using hash references
5. **Implement approximation engine** using similarity search

Continue implementation? 🚀
