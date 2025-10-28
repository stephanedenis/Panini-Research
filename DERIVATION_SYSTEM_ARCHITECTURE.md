# Système de Dérivation Hypersémantique - Architecture v4.0

**Inspiration**: IPFS (Merkle DAGs) + Git (commits/history) + Sémantique Pāṇinienne  
**Principe**: Tout est immutable, évolution par dérivation déclarative

---

## 1. Modèle Conceptuel

### 1.1 Merkle DAG Sémantique

```
                    [Grammar PNG v3.0]
                     hash: d0e3cf56
                     sim:  9500063a
                           |
                    parents: [b8e0fa23, c5d2be45]
                           / \
                          /   \
                         /     \
              [v2.0-mask]       [v2.0-offset]
              b8e0fa23           c5d2be45
              9500063b           9500063c
                   |                |
                   |                |
              parent: a7f3d912  parent: a7f3d912
                   |                |
                    \              /
                     \            /
                      \          /
                   [Grammar PNG v1.0]
                    hash: a7f3d912
                    sim:  9500036d
                    parents: []
```

**Propriétés**:
- Chaque nœud est **immutable** (content-addressed)
- Parents explicites → **DAG navigable**
- Similarity hash → **clustering sémantique**
- Merge naturel → **évolution parallèle**

---

## 2. Format de Dérivation Déclaratif

### 2.1 Objet "Derivation" (inspiré git commit)

```yaml
# Fichier: derivations/b8e0fa23.yml
# Stocké comme: objects/derivation/b8/e0fa23/content

type: derivation
object_type: pattern  # ou grammar, transformation, etc.
object_hash: b8e0fa23

# Généalogie (comme git)
parents:
  - hash: a7f3d912
    relation: extends  # extends, refines, merges, specializes
    similarity: 0.95

# Transformation sémantique (déclarative)
transformation:
  operation: add_field
  description: "Add mask support for partial signature matching"
  changes:
    - path: config.schema
      add:
        mask:
          type: bytes
          optional: true
          description: "Bitmask for partial matching"
    - path: logic.match
      modify:
        before: "signature == data[offset:offset+length]"
        after: "masked_match(signature, data[offset:offset+length], mask)"

# Métadonnées sémantiques
semantic:
  intent: ["flexibility", "partial_matching"]
  preserves: ["signature_detection", "offset_matching"]
  adds: ["mask_support", "bit_level_matching"]
  breaks: []  # Breaking changes

# Entropie/négentropie (héritage)
entropy:
  value: 4.8434
  delta: +0.0012  # Variation vs parent
negentropy:
  value: 3.1566
  delta: -0.0012

# Validation
tests:
  - name: "PNG with mask"
    input_hash: f9a2c1d5  # Test data content-addressed
    expected_match: true
  - name: "JPEG without mask"
    input_hash: e8b3d4f6
    expected_match: true

# Signature cryptographique (optionnel)
signature:
  author: "panini-research"
  timestamp: "2025-10-28T10:30:00Z"
  pgp_signature: "-----BEGIN PGP SIGNATURE-----..."
```

### 2.2 Objet "Merge" (fusion de branches)

```yaml
# derivations/d0e3cf56.yml

type: derivation
object_type: grammar
object_hash: d0e3cf56

# Multiple parents = merge
parents:
  - hash: b8e0fa23
    relation: merges
    branch: "feature/mask-support"
    similarity: 0.95
  - hash: c5d2be45
    relation: merges
    branch: "feature/variable-offset"
    similarity: 0.94

# Stratégie de merge (déclarative)
merge_strategy:
  type: union  # union, override, custom
  conflicts: []  # Pas de conflits
  resolution:
    - path: config.features
      action: combine
      result: ["mask", "variable_offset"]

transformation:
  operation: merge
  description: "Combine mask and variable offset features"
  changes:
    - path: config.schema
      merge:
        from_parents: [b8e0fa23, c5d2be45]
        strategy: union

semantic:
  intent: ["feature_combination", "enhanced_flexibility"]
  preserves: ["all_parent_features"]
  adds: ["combined_matching"]
  breaks: []
```

### 2.3 Objet "Specialization" (raffinement)

```yaml
# derivations/e1f4cd78.yml

type: derivation
object_type: pattern
object_hash: e1f4cd78

parents:
  - hash: a7f3d912
    relation: specializes
    similarity: 0.98

# Spécialisation pour un cas particulier
transformation:
  operation: specialize
  description: "PNG-specific magic number with strict validation"
  changes:
    - path: config.signature
      constrain:
        value: "89504E470D0A1A0A"
        was: "configurable"
        rationale: "PNG signature is fixed by spec"
    - path: config.validation
      add:
        check_crlf: true
        check_eof: true

semantic:
  intent: ["strict_validation", "format_specific"]
  preserves: ["signature_matching"]
  adds: ["png_specific_checks"]
  specializes_for: ["PNG"]
```

---

## 3. Opérations de Dérivation

### 3.1 Catalogue d'Opérations Déclaratives

```yaml
# operations.yml (définitions réutilisables)

operations:
  add_field:
    description: "Add new field to pattern schema"
    parameters:
      - name: path
        type: jsonpath
      - name: field_name
        type: string
      - name: field_spec
        type: schema
    semantic_impact:
      preserves: ["existing_fields"]
      adds: ["new_capability"]
      
  modify_logic:
    description: "Update matching logic"
    parameters:
      - name: path
        type: jsonpath
      - name: before
        type: expression
      - name: after
        type: expression
    semantic_impact:
      may_break: ["behavior"]
      
  constrain_value:
    description: "Restrict value to specific constant"
    parameters:
      - name: path
        type: jsonpath
      - name: value
        type: any
      - name: was
        type: string
    semantic_impact:
      specializes: true
      preserves: ["interface"]
      
  merge_schemas:
    description: "Combine multiple schemas"
    parameters:
      - name: parents
        type: list[hash]
      - name: strategy
        type: enum[union, intersection, custom]
    semantic_impact:
      combines: ["parent_features"]
      
  refactor_structure:
    description: "Restructure without changing semantics"
    parameters:
      - name: mappings
        type: dict[old_path, new_path]
    semantic_impact:
      preserves: ["semantics"]
      changes: ["structure"]
```

### 3.2 Application Déclarative

```python
# Système lit la dérivation et applique automatiquement

def apply_derivation(derivation_hash: str, store: ContentAddressedStore):
    """
    Applique une dérivation déclarative
    
    1. Charge l'objet derivation
    2. Valide les parents
    3. Applique les transformations déclaratives
    4. Vérifie que le hash résultant correspond
    """
    
    # 1. Charger dérivation
    deriv_content, deriv_meta = store.load(derivation_hash, "derivation")
    derivation = yaml.safe_load(deriv_content)
    
    # 2. Charger parent(s)
    parents = []
    for parent_spec in derivation['parents']:
        parent_content, _ = store.load(parent_spec['hash'], 
                                       derivation['object_type'])
        parents.append(yaml.safe_load(parent_content))
    
    # 3. Appliquer transformations
    result = apply_operation(
        parents,
        derivation['transformation']['operation'],
        derivation['transformation']['changes']
    )
    
    # 4. Vérifier hash
    result_bytes = yaml.dump(result).encode('utf-8')
    result_hash = compute_exact_hash(result_bytes)
    
    assert result_hash == derivation['object_hash'], \
        f"Derivation mismatch: {result_hash} != {derivation['object_hash']}"
    
    return result
```

---

## 4. Hypersémantique - Métadonnées Enrichies

### 4.1 Semantic Fingerprint (empreinte sémantique)

```yaml
semantic_fingerprint:
  # Capabilities (ce que l'objet peut faire)
  capabilities:
    - signature_matching
    - offset_detection
    - mask_support
    - variable_length
  
  # Intent (pourquoi l'objet existe)
  intent:
    - format_identification
    - header_validation
    - magic_number_detection
  
  # Constraints (limites/garanties)
  constraints:
    - fixed_offset: false
    - max_signature_length: 256
    - requires_mask: false
  
  # Compatibility (versions supportées)
  compatibility:
    backwards_compatible_with: ["v1.0", "v1.1"]
    breaks: []
    deprecates: []
  
  # Domain (domaine d'application)
  domain:
    format_types: ["binary", "image", "font"]
    use_cases: ["file_identification", "format_validation"]
```

### 4.2 Similarity Vector (au-delà de l'entropie)

```yaml
similarity_vector:
  # Entropie/négentropie (structure)
  entropy: 4.8434
  negentropy: 3.1566
  
  # Dimensions sémantiques (0.0-1.0)
  semantic_dimensions:
    structural_complexity: 0.35  # Complexité structure
    behavioral_flexibility: 0.67  # Flexibilité comportement
    domain_specificity: 0.89      # Spécificité domaine
    composability: 0.92           # Facilité composition
    abstraction_level: 0.45       # Niveau abstraction
  
  # Vector embedding (optionnel, pour ML)
  embedding:
    model: "panini-semantic-v1"
    dimensions: 128
    vector: [0.234, -0.456, 0.789, ...]  # 128 dimensions
```

### 4.3 Provenance Chain (chaîne de provenance)

```yaml
provenance:
  # Origine
  origin:
    source: "empirical_analysis"
    dataset: "70_format_extractors"
    analysis_hash: "b62a2d8f"
    confidence: 0.95
  
  # Évolution
  evolution:
    - timestamp: "2025-10-15T10:00:00Z"
      event: "extracted_from_analysis"
      agent: "pattern_consolidation_script"
      hash: "a7f3d912"
    
    - timestamp: "2025-10-20T14:30:00Z"
      event: "refined_with_mask"
      agent: "human_researcher"
      derivation: "b8e0fa23"
    
    - timestamp: "2025-10-22T09:15:00Z"
      event: "merged_with_offset_feature"
      agent: "automated_merger"
      derivation: "d0e3cf56"
  
  # Attribution
  contributors:
    - id: "panini-research"
      role: "primary_author"
      contributions: ["design", "implementation"]
    - id: "community"
      role: "refinement"
      contributions: ["testing", "feedback"]
```

---

## 5. Requêtes Hypersémantiques

### 5.1 Query Language (IPFS-style selectors + sémantique)

```yaml
# Trouver tous les patterns dérivés de MAGIC_NUMBER
query:
  type: pattern
  provenance:
    ancestor: "a7f3d912"  # Hash du MAGIC_NUMBER original
  semantic:
    capabilities:
      must_have: ["signature_matching"]
      may_have: ["mask_support"]
  similarity:
    entropy_range: [4.5, 5.5]
    semantic_distance:
      from: "a7f3d912"
      max_distance: 0.3
  
  result_format: graph  # graph, list, tree
```

### 5.2 API de Navigation

```python
# Navigation dans le DAG sémantique

class SemanticDAG:
    def __init__(self, store: ContentAddressedStore):
        self.store = store
    
    def ancestors(self, hash: str, max_depth: int = None) -> List[str]:
        """Tous les ancêtres (parents, grands-parents, ...)"""
        pass
    
    def descendants(self, hash: str, max_depth: int = None) -> List[str]:
        """Tous les descendants (enfants, petits-enfants, ...)"""
        pass
    
    def siblings(self, hash: str) -> List[str]:
        """Objets avec mêmes parents (branches parallèles)"""
        pass
    
    def common_ancestor(self, hash1: str, hash2: str) -> str:
        """Ancêtre commun le plus récent (comme git merge-base)"""
        pass
    
    def semantic_neighbors(self, hash: str, 
                          threshold: float = 0.8) -> List[Tuple[str, float]]:
        """Objets sémantiquement proches (pas forcément liés)"""
        pass
    
    def capability_search(self, capabilities: List[str]) -> List[str]:
        """Objets ayant certaines capacités"""
        pass
    
    def evolution_path(self, from_hash: str, to_hash: str) -> List[str]:
        """Chemin d'évolution entre deux versions"""
        pass
    
    def diff_semantic(self, hash1: str, hash2: str) -> Dict:
        """Différence sémantique entre deux objets"""
        pass
```

---

## 6. Compatibilité et Reconstruction

### 6.1 Compatibility Matrix (automatique)

```yaml
# Générée automatiquement à partir des derivations

compatibility_matrix:
  a7f3d912:  # MAGIC_NUMBER v1.0
    b8e0fa23: "compatible"      # v2.0-mask (extends)
    c5d2be45: "compatible"      # v2.0-offset (extends)
    d0e3cf56: "compatible"      # v3.0 (merge)
    e1f4cd78: "specialization"  # PNG-specific
    f2g5de89: "incompatible"    # Breaking change
  
  b8e0fa23:  # v2.0-mask
    a7f3d912: "backwards_compatible"
    d0e3cf56: "compatible"
    e1f4cd78: "specialization"
```

### 6.2 Reconstruction Déclarative

```yaml
# reconstruction.yml

reconstruction:
  target: "d0e3cf56"  # Version à reconstruire
  
  # Stratégie de reconstruction
  strategy:
    method: "replay_derivations"  # ou "direct_load", "recompute"
    verify_hashes: true
  
  # Plan de reconstruction
  execution_plan:
    - step: 1
      action: load_base
      hash: "a7f3d912"
      type: pattern
    
    - step: 2
      action: apply_derivation
      derivation: "b8e0fa23"
      verify: true
    
    - step: 3
      action: apply_derivation
      derivation: "c5d2be45"
      verify: true
    
    - step: 4
      action: merge
      parents: ["b8e0fa23", "c5d2be45"]
      derivation: "d0e3cf56"
      verify: true
  
  # Fallback en cas d'échec
  fallback:
    - try: "direct_load"
      from_hash: "d0e3cf56"
    - try: "semantic_equivalent"
      similarity_threshold: 0.95
```

---

## 7. Exemple Complet: Évolution PNG Grammar

```yaml
# === Version 1.0 (baseline) ===
# objects/grammar/a7/f3d912/content

format: PNG
version: "1.0"
patterns:
  - pattern_ref: "9949a471"  # MAGIC_NUMBER
    name: signature
  - pattern_ref: "6eacc5de"  # CHUNK_STRUCTURE
    name: chunks

metadata:
  extract:
    - field: IHDR.width
      as: image_width
    - field: IHDR.height
      as: image_height
```

```yaml
# === Derivation v2.0 (add transparency support) ===
# objects/derivation/b8/e0fa23/content

type: derivation
object_type: grammar
object_hash: b8e0fa23

parents:
  - hash: a7f3d912
    relation: extends

transformation:
  operation: add_extraction
  changes:
    - path: metadata.extract
      add:
        - field: tRNS.alpha
          as: has_transparency
        - field: tRNS.type
          as: transparency_type

semantic:
  intent: ["transparency_support"]
  preserves: ["basic_metadata_extraction"]
  adds: ["alpha_channel_detection"]
```

```yaml
# === Derivation v3.0 (merge transparency + color profile) ===
# objects/derivation/d0/e3cf56/content

type: derivation
object_type: grammar
object_hash: d0e3cf56

parents:
  - hash: b8e0fa23  # transparency
    relation: merges
  - hash: c5d2be45  # color profile
    relation: merges

transformation:
  operation: merge
  merge_strategy:
    type: union
  changes:
    - path: metadata.extract
      merge:
        from_parents: [b8e0fa23, c5d2be45]
        strategy: combine

semantic:
  intent: ["comprehensive_metadata"]
  preserves: ["all_parent_features"]
  adds: ["combined_transparency_and_color"]
```

---

## 8. Stockage IPFS-style

### 8.1 Structure Merkle DAG

```
store/
├── objects/
│   ├── pattern/
│   │   └── a7/f3d912/
│   │       ├── content          (YAML du pattern)
│   │       └── metadata.json    (ObjectMetadata)
│   │
│   ├── grammar/
│   │   └── d0/e3cf56/
│   │       ├── content          (YAML de la grammar)
│   │       └── metadata.json
│   │
│   ├── derivation/              ⬅️ NOUVEAU
│   │   └── b8/e0fa23/
│   │       ├── content          (YAML de la derivation)
│   │       └── metadata.json    (avec parents)
│   │
│   └── operation/               ⬅️ NOUVEAU
│       └── f9/a2c1d5/
│           ├── content          (définition opération)
│           └── metadata.json
│
├── indexes/                      ⬅️ NOUVEAU
│   ├── semantic/
│   │   ├── capabilities.json    (index par capability)
│   │   ├── intent.json           (index par intent)
│   │   └── domain.json           (index par domaine)
│   │
│   ├── genealogy/
│   │   ├── parents.json          (index enfant→parents)
│   │   ├── children.json         (index parent→enfants)
│   │   └── ancestors.json        (index ancêtres transitifs)
│   │
│   └── similarity/
│       ├── entropy_buckets.json
│       └── semantic_clusters.json
│
├── refs/
│   ├── heads/                    (comme git refs/heads/)
│   │   ├── patterns/main → a7f3d912
│   │   └── grammars/png/latest → d0e3cf56
│   │
│   └── tags/                     (versions nommées)
│       └── v1.0 → a7f3d912
│
└── provenance/                   ⬅️ NOUVEAU
    └── chains/
        └── a7f3d912.json         (chaîne de provenance)
```

---

## 9. Implémentation

### 9.1 Classe DerivationManager

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import yaml

@dataclass
class Derivation:
    """Représente une dérivation déclarative"""
    object_hash: str
    object_type: str
    parents: List[Dict]
    transformation: Dict
    semantic: Dict
    entropy: float
    negentropy: float

class DerivationManager:
    def __init__(self, store: ContentAddressedStore):
        self.store = store
        self.dag = SemanticDAG(store)
    
    def create_derivation(self,
                         parent_hashes: List[str],
                         transformation: Dict,
                         object_type: str) -> str:
        """
        Crée une nouvelle dérivation déclarative
        
        1. Charge les parents
        2. Applique la transformation
        3. Calcule les hashes
        4. Stocke la dérivation
        5. Met à jour les indexes
        """
        
        # 1. Charger parents
        parents = []
        for parent_hash in parent_hashes:
            content, meta = self.store.load(parent_hash, object_type)
            parents.append({
                'hash': parent_hash,
                'content': yaml.safe_load(content),
                'metadata': meta
            })
        
        # 2. Appliquer transformation
        result = self._apply_transformation(
            parents,
            transformation
        )
        
        # 3. Calculer hashes
        result_bytes = yaml.dump(result).encode('utf-8')
        exact_hash = compute_exact_hash(result_bytes)
        similarity_hash = compute_similarity_hash(result_bytes, result)
        
        # 4. Créer dérivation
        derivation = {
            'type': 'derivation',
            'object_type': object_type,
            'object_hash': exact_hash,
            'parents': [{'hash': p['hash'], 'relation': 'extends'} 
                       for p in parents],
            'transformation': transformation,
            'semantic': self._extract_semantic(result, parents),
            'entropy': compute_entropy(result_bytes),
            'negentropy': compute_negentropy(result_bytes)
        }
        
        # 5. Stocker dérivation
        deriv_bytes = yaml.dump(derivation).encode('utf-8')
        deriv_hash = self.store.store(
            deriv_bytes,
            'derivation',
            metadata=derivation
        )[0]
        
        # 6. Stocker objet résultant
        self.store.store(
            result_bytes,
            object_type,
            metadata={
                **result,
                'derivation': deriv_hash
            }
        )
        
        return exact_hash
    
    def reconstruct(self, target_hash: str) -> Dict:
        """Reconstruit un objet en rejouant les dérivations"""
        
        # Trouver le chemin de reconstruction
        path = self.dag.evolution_path('root', target_hash)
        
        # Rejouer les dérivations
        current = None
        for step_hash in path:
            if step_hash == 'root':
                continue
            
            # Charger la dérivation
            deriv_content, _ = self.store.load(step_hash, 'derivation')
            derivation = yaml.safe_load(deriv_content)
            
            # Appliquer
            current = self._apply_transformation(
                [current] if current else [],
                derivation['transformation']
            )
        
        return current
```

---

## 10. Avantages du Modèle Hypersémantique

### 10.1 vs Git
| Git | Panini Hypersémantique |
|-----|------------------------|
| Commits = blobs opaques | Dérivations = transformations déclaratives |
| Diff = lignes texte | Diff = changements sémantiques |
| Merge = conflits syntaxiques | Merge = compatibilité sémantique |
| History = linéaire/branches | DAG = hypergraphe avec similitude |

### 10.2 vs IPFS
| IPFS | Panini Hypersémantique |
|------|------------------------|
| Content-addressed | Content-addressed + similarity-addressed |
| Merkle DAG | Merkle DAG + semantic fingerprints |
| Links = hashes | Links = hashes + relations sémantiques |
| Immutable | Immutable + évolution déclarative |

### 10.3 Capacités Uniques
1. **Découverte par similitude** (au-delà des liens explicites)
2. **Compatibilité automatique** (via semantic fingerprints)
3. **Reconstruction multiple** (replay, direct, equivalent)
4. **Provenance complète** (origine + évolution + intent)
5. **Requêtes hypersémantiques** (capabilities, intent, domain)

---

## 11. Prochaines Étapes

1. ✅ Architecture définie
2. 🔄 Implémenter DerivationManager
3. 🔄 Créer indexes sémantiques
4. 🔄 Implémenter requêtes hypersémantiques
5. 🔄 Migrer patterns existants avec provenance
6. 🔄 Tests: évolution PNG grammar v1.0 → v3.0

---

**Vision**: Un système où chaque objet est **immutable** mais **évolutif**, où les transformations sont **déclaratives** et **rejouables**, et où la découverte se fait par **similitude sémantique** autant que par **liens généalogiques**.

**Inspiration Pāṇinienne**: Comme les *dhātus* Sanskrit évoluent par *pratyaya* (affixes) tout en restant reconnaissables, les patterns Panini évoluent par dérivations déclaratives tout en maintenant leur identité sémantique.
