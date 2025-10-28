"""
PaniniFS v4.0 - Content-Addressed Storage System

Double-hash architecture:
1. Exact hash (SHA-256) - Immutability & deduplication
2. Similarity hash (Entropy + Négentropie) - Discovery & approximation

Inspired by Git/IPFS but with similarity indexing for pattern discovery.
"""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ObjectMetadata:
    """Metadata for stored object"""
    exact_hash: str
    similarity_hash: str
    object_type: str  # "pattern", "grammar", "file", "extraction"
    created_at: str
    size_bytes: int
    entropy: float
    negentropy: float
    structural_features: Dict[str, float]


def compute_exact_hash(content: bytes) -> str:
    """
    Compute exact content hash (SHA-256, truncated to 16 hex chars).
    
    Args:
        content: Raw bytes to hash
    
    Returns:
        16-character hex string
    """
    full_hash = hashlib.sha256(content).hexdigest()
    return full_hash[:16]


def compute_entropy(data: bytes) -> float:
    """
    Shannon entropy H(X) = -Σ p(x) log₂ p(x)
    
    Measures randomness/disorder:
    - 0.0: Completely structured (all same byte)
    - 8.0: Maximum entropy (perfectly random)
    
    Args:
        data: Bytes to analyze
    
    Returns:
        Entropy value [0.0, 8.0]
    """
    if not data:
        return 0.0
    
    byte_counts = Counter(data)
    total = len(data)
    
    entropy = 0.0
    for count in byte_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def compute_negentropy(data: bytes) -> float:
    """
    Négentropie (Negentropy) = Max_Entropy - Entropy
    
    Measures structure/order (inverse of entropy):
    - High négentropie: Structured, patterned data
    - Low négentropie: Random, chaotic data
    
    Args:
        data: Bytes to analyze
    
    Returns:
        Negentropy value [0.0, 8.0]
    """
    max_entropy = 8.0  # For byte data (2^8 = 256 possible values)
    return max_entropy - compute_entropy(data)


def extract_structural_features(
    content: bytes,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Extract structural features for similarity comparison.
    
    Features (all normalized to [0.0, 1.0]):
    - field_count: Number of fields (if structured)
    - nesting_depth: Maximum nesting level
    - type_diversity: Variety of field types
    - repetition: Presence of repeating patterns
    - byte_distribution: Distribution uniformity
    
    Args:
        content: Raw bytes
        metadata: Optional JSON metadata with structure info
    
    Returns:
        Dict of normalized feature values
    """
    features = {}
    
    # If metadata provided, extract logical structure
    if metadata:
        # Field count (normalize to [0, 1], cap at 100 fields)
        if 'fields' in metadata:
            field_count = len(metadata['fields'])
            features['field_count'] = min(field_count / 100.0, 1.0)
        else:
            features['field_count'] = 0.0
        
        # Type diversity (entropy of types)
        if 'fields' in metadata and isinstance(metadata['fields'], list):
            types = [f.get('type', 'unknown') for f in metadata['fields']]
            if types:
                type_counts = Counter(types)
                type_entropy = 0.0
                total = len(types)
                for count in type_counts.values():
                    p = count / total
                    if p > 0:
                        type_entropy -= p * math.log2(p)
                # Normalize (max ~5 for reasonable type variety)
                features['type_diversity'] = min(type_entropy / 5.0, 1.0)
            else:
                features['type_diversity'] = 0.0
        else:
            features['type_diversity'] = 0.0
        
        # Repetition indicator
        features['repetition'] = 1.0 if metadata.get('repeating', False) else 0.0
        
        # Nesting depth
        def get_depth(obj, current=0):
            if isinstance(obj, dict):
                return max((get_depth(v, current + 1) for v in obj.values()), default=current)
            elif isinstance(obj, list):
                return max((get_depth(item, current + 1) for item in obj), default=current)
            return current
        
        depth = get_depth(metadata)
        features['nesting_depth'] = min(depth / 10.0, 1.0)  # Normalize, cap at 10
    else:
        # No metadata, use byte-level features only
        features['field_count'] = 0.0
        features['type_diversity'] = 0.0
        features['repetition'] = 0.0
        features['nesting_depth'] = 0.0
    
    # Byte distribution uniformity (from content)
    if content:
        byte_counts = Counter(content)
        # Compute chi-square statistic for uniformity
        expected = len(content) / 256.0
        chi_square = sum((count - expected) ** 2 / expected for count in byte_counts.values())
        # Normalize (chi-square for uniform ≈ 0, non-uniform >> 256)
        features['byte_uniformity'] = 1.0 / (1.0 + chi_square / 1000.0)
    else:
        features['byte_uniformity'] = 0.0
    
    return features


def compute_similarity_hash(
    content: bytes,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compute fuzzy similarity hash for pattern discovery.
    
    Hash encodes (32 bits = 8 hex chars):
    - Entropy (4 bits): Randomness measure
    - Négentropie (4 bits): Structure measure
    - Field count (4 bits): Number of fields
    - Type diversity (4 bits): Variety of types
    - Repetition (4 bits): Repeating pattern flag
    - Nesting (4 bits): Nesting depth
    - Reserved (4 bits): Future use
    - Checksum (4 bits): Content checksum
    
    Args:
        content: Raw bytes to hash
        metadata: Optional structural metadata
    
    Returns:
        8-character hex string
    """
    # Compute entropy and négentropie
    entropy = compute_entropy(content)
    negentropy = compute_negentropy(content)
    
    # Extract structural features
    features = extract_structural_features(content, metadata)
    
    # Convert to 4-bit nibbles (0-15)
    entropy_nibble = int((entropy / 8.0) * 15)
    negentropy_nibble = int((negentropy / 8.0) * 15)
    field_nibble = int(features.get('field_count', 0.0) * 15)
    type_nibble = int(features.get('type_diversity', 0.0) * 15)
    repetition_nibble = int(features.get('repetition', 0.0) * 15)
    nesting_nibble = int(features.get('nesting_depth', 0.0) * 15)
    uniformity_nibble = int(features.get('byte_uniformity', 0.0) * 15)
    
    # Content checksum (4 bits)
    checksum_nibble = (sum(content) if content else 0) & 0x0F
    
    # Combine into 32-bit integer
    similarity_int = (
        (entropy_nibble << 28) |
        (negentropy_nibble << 24) |
        (field_nibble << 20) |
        (type_nibble << 16) |
        (repetition_nibble << 12) |
        (nesting_nibble << 8) |
        (uniformity_nibble << 4) |
        checksum_nibble
    )
    
    return f"{similarity_int:08x}"


class ContentAddressedStore:
    """
    Content-addressed storage with similarity indexing.
    
    Stores objects (patterns, grammars, files) by exact hash,
    maintains similarity index for fuzzy discovery.
    
    Directory structure:
        store/
        ├── objects/
        │   ├── patterns/
        │   │   └── a7/f3d912e4c5b8f0/
        │   │       ├── content
        │   │       └── metadata.json
        │   ├── grammars/
        │   ├── files/
        │   └── extractions/
        ├── similarity/
        │   └── patterns/
        │       └── e8d7.json  # Bucket for similarity hash e8d7xxxx
        └── refs/
            ├── patterns/
            │   └── MAGIC_NUMBER → a7f3d912e4c5b8f0
            └── grammars/
                └── PNG/latest → b3f9a2c1d5e7f8a4
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize content-addressed store.
        
        Args:
            base_path: Root directory for store
        """
        self.base_path = Path(base_path)
        self.objects_path = self.base_path / "objects"
        self.similarity_path = self.base_path / "similarity"
        self.refs_path = self.base_path / "refs"
        
        # Create directories
        for obj_type in ["patterns", "grammars", "files", "extractions"]:
            (self.objects_path / obj_type).mkdir(parents=True, exist_ok=True)
            (self.similarity_path / obj_type).mkdir(parents=True, exist_ok=True)
            (self.refs_path / obj_type).mkdir(parents=True, exist_ok=True)
    
    def store(
        self,
        content: bytes,
        object_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, ObjectMetadata]:
        """
        Store object with double-hash.
        
        Args:
            content: Raw bytes to store
            object_type: Type ("pattern", "grammar", "file", "extraction")
            metadata: Optional structural metadata
        
        Returns:
            (exact_hash, similarity_hash, object_metadata)
        """
        # Compute hashes
        exact_hash = compute_exact_hash(content)
        similarity_hash = compute_similarity_hash(content, metadata)
        
        # Create object directory
        obj_dir = (
            self.objects_path / object_type / 
            exact_hash[:2] / exact_hash
        )
        obj_dir.mkdir(parents=True, exist_ok=True)
        
        # Store content
        content_file = obj_dir / "content"
        if not content_file.exists():  # Don't overwrite if exists
            content_file.write_bytes(content)
        
        # Create metadata
        obj_metadata = ObjectMetadata(
            exact_hash=exact_hash,
            similarity_hash=similarity_hash,
            object_type=object_type,
            created_at=datetime.now().isoformat(),
            size_bytes=len(content),
            entropy=compute_entropy(content),
            negentropy=compute_negentropy(content),
            structural_features=extract_structural_features(content, metadata)
        )
        
        # Add user metadata
        meta_dict = asdict(obj_metadata)
        if metadata:
            meta_dict['user_metadata'] = metadata
        
        # Store metadata
        (obj_dir / "metadata.json").write_text(
            json.dumps(meta_dict, indent=2, sort_keys=True)
        )
        
        # Update similarity index
        self._index_similarity(object_type, exact_hash, similarity_hash)
        
        return exact_hash, similarity_hash, obj_metadata
    
    def load(
        self,
        exact_hash: str,
        object_type: str
    ) -> Optional[Tuple[bytes, ObjectMetadata]]:
        """
        Load object by exact hash.
        
        Args:
            exact_hash: Exact content hash
            object_type: Object type
        
        Returns:
            (content, metadata) or None if not found
        """
        obj_dir = (
            self.objects_path / object_type / 
            exact_hash[:2] / exact_hash
        )
        
        content_file = obj_dir / "content"
        metadata_file = obj_dir / "metadata.json"
        
        if not content_file.exists():
            return None
        
        content = content_file.read_bytes()
        
        if metadata_file.exists():
            meta_dict = json.loads(metadata_file.read_text())
            metadata = ObjectMetadata(**{
                k: v for k, v in meta_dict.items() 
                if k in ObjectMetadata.__annotations__
            })
        else:
            # Fallback: compute metadata
            metadata = ObjectMetadata(
                exact_hash=exact_hash,
                similarity_hash="",
                object_type=object_type,
                created_at="",
                size_bytes=len(content),
                entropy=compute_entropy(content),
                negentropy=compute_negentropy(content),
                structural_features={}
            )
        
        return content, metadata
    
    def find_similar(
        self,
        similarity_hash: str,
        object_type: str,
        threshold: float = 0.75,
        max_results: int = 100
    ) -> List[Tuple[str, float]]:
        """
        Find objects with similar hashes.
        
        Args:
            similarity_hash: Query similarity hash
            object_type: Object type to search
            threshold: Minimum similarity score [0.0, 1.0]
            max_results: Maximum results to return
        
        Returns:
            List of (exact_hash, similarity_score) sorted by score descending
        """
        results = []
        
        # Search in buckets (first 4 chars)
        bucket = similarity_hash[:4]
        index_dir = self.similarity_path / object_type
        
        # Load bucket
        bucket_file = index_dir / f"{bucket}.json"
        if bucket_file.exists():
            entries = json.loads(bucket_file.read_text())
            
            for entry in entries:
                score = self._similarity_score(
                    similarity_hash,
                    entry['similarity_hash']
                )
                
                if score >= threshold:
                    results.append((entry['exact_hash'], score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:max_results]
    
    def create_ref(self, name: str, object_type: str, exact_hash: str):
        """
        Create symbolic reference to object.
        
        Args:
            name: Reference name (e.g., "MAGIC_NUMBER", "PNG/latest")
            object_type: Object type
            exact_hash: Target object hash
        """
        ref_path = self.refs_path / object_type / name
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_text(exact_hash)
    
    def resolve_ref(self, name: str, object_type: str) -> Optional[str]:
        """
        Resolve symbolic reference to exact hash.
        
        Args:
            name: Reference name
            object_type: Object type
        
        Returns:
            Exact hash or None if not found
        """
        ref_path = self.refs_path / object_type / name
        
        if ref_path.exists():
            return ref_path.read_text().strip()
        
        return None
    
    def _index_similarity(
        self,
        object_type: str,
        exact_hash: str,
        similarity_hash: str
    ):
        """Update similarity index with new object"""
        # Bucket by first 4 chars
        bucket = similarity_hash[:4]
        index_dir = self.similarity_path / object_type
        bucket_file = index_dir / f"{bucket}.json"
        
        # Load existing entries
        if bucket_file.exists():
            entries = json.loads(bucket_file.read_text())
        else:
            entries = []
        
        # Add new entry (avoid duplicates)
        if not any(e['exact_hash'] == exact_hash for e in entries):
            entries.append({
                'exact_hash': exact_hash,
                'similarity_hash': similarity_hash
            })
        
        # Ensure directory exists
        bucket_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        bucket_file.write_text(json.dumps(entries, indent=2))
    
    def _similarity_score(self, hash1: str, hash2: str) -> float:
        """
        Compute similarity score between two similarity hashes.
        
        Compares nibbles (hex chars) and returns proportion matching.
        
        Args:
            hash1, hash2: Similarity hashes (8 hex chars)
        
        Returns:
            Similarity score [0.0, 1.0]
        """
        if len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)
