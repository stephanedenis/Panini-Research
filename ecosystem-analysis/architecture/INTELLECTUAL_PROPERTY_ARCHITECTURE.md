# 🔐 PaniniFS v4.0 - Architecture de Propriété Intellectuelle

**Date:** 28 octobre 2025  
**Version:** 4.0-alpha  
**Status:** Proposition architecturale

---

## 📋 Table des Matières

1. [Vision Générale](#1-vision-générale)
2. [Provenance & Traçabilité](#2-provenance--traçabilité)
3. [Licensing & Copyright](#3-licensing--copyright)
4. [Attribution & Crédit](#4-attribution--crédit)
5. [Access Control & Visibilité](#5-access-control--visibilité)
6. [Audit & Compliance](#6-audit--compliance)
7. [Signatures Cryptographiques](#7-signatures-cryptographiques)
8. [Gouvernance Communautaire](#8-gouvernance-communautaire)
9. [Implémentation](#9-implémentation)

---

## 1. Vision Générale

### 1.1 Principes Fondamentaux

**PaniniFS** doit devenir un système de fichiers où **chaque objet a une histoire traçable, une licence claire, et une attribution vérifiable**. Inspiré par:

- **Git**: Provenance chains, commit authorship, GPG signatures
- **IPFS**: Content addressing, pinning, gatekeeping
- **Blockchain**: Immutable attribution, timestamping
- **Pāṇini**: Attribution des sūtras à leurs auteurs (tradition grammaticale sanskrite)
- **Academic Standards**: Peer review, citations, reproducibility

### 1.2 Objectifs Stratégiques

1. **Traçabilité Complète**: Chaque transformation documentée
2. **Propriété Claire**: Attribution sans ambiguïté
3. **Conformité Légale**: Respect copyright, brevets, marques
4. **Transparence**: Audit trails complets
5. **Flexibilité**: Support multi-licenses, composite rights
6. **Décentralisation**: Pas de single point of trust
7. **Marketplace-Ready**: Grammaires commercialisables avec IP protection

### 1.3 Cas d'Usage Cibles

- **Grammaires Open Source**: Attribution, forks, pull requests
- **Grammaires Propriétaires**: Licensing, royalties, DRM-free
- **Recherche Académique**: Citations, peer review, reproducibility
- **Enterprise**: Compliance, audit trails, access control
- **Community**: Reputation, contributions, governance

---

## 2. Provenance & Traçabilité

### 2.1 Provenance Chain (Extension de ObjectMetadata)

```python
@dataclass
class ProvenanceChain:
    """
    Chaîne de provenance complète pour un objet CAS
    
    Documente l'origine, les transformations, et l'évolution
    d'un objet dans le système.
    """
    
    # Origine
    origin: Origin
    
    # Chaîne de dérivations
    evolution: List[EvolutionEvent]
    
    # Attribution multi-niveau
    contributors: List[Contributor]
    
    # Licenses (potentiellement multiples si composite)
    licenses: List[License]
    
    # Signatures cryptographiques (optionnel)
    signatures: Optional[List[Signature]]
    
    # Metadata de traçabilité
    traceability_metadata: Dict[str, Any]


@dataclass
class Origin:
    """Origine d'un objet"""
    
    source_type: SourceType  # "empirical_analysis", "manual_creation", 
                              # "derived", "imported", "generated"
    
    # Détails spécifiques au type
    dataset: Optional[str]  # ex: "70_format_extractors"
    analysis_hash: Optional[str]  # Hash de l'analyse source
    parent_hashes: List[str]  # Parents directs si dérivé
    
    # Métadonnées
    created_at: str  # ISO 8601 timestamp
    created_by: str  # Identité du créateur
    location: Optional[str]  # URL, file path, etc.
    
    # Confidence & validation
    confidence: float  # [0.0, 1.0]
    validation_method: Optional[str]
    peer_reviewed: bool


@dataclass
class EvolutionEvent:
    """Un événement dans l'évolution de l'objet"""
    
    timestamp: str  # ISO 8601
    event_type: EventType  # "extracted", "refined", "merged", 
                           # "forked", "deprecated", "certified"
    
    agent: Agent  # Qui a fait la modification
    derivation_hash: Optional[str]  # Hash de la dérivation YAML
    
    # Changements sémantiques
    capabilities_added: List[str]
    capabilities_removed: List[str]
    breaking_changes: bool
    
    # Contexte
    reason: Optional[str]
    issue_refs: List[str]  # GitHub issues, etc.


@dataclass
class Agent:
    """Agent ayant effectué une action"""
    
    agent_type: AgentType  # "human", "automated_script", 
                           # "ai_assistant", "consensus"
    
    identity: str  # User ID, email, GPG key ID, etc.
    display_name: Optional[str]
    
    # Vérification
    verification_method: Optional[str]  # "gpg", "ssh_key", "oauth", "did"
    verified: bool


class SourceType(Enum):
    EMPIRICAL_ANALYSIS = "empirical_analysis"
    MANUAL_CREATION = "manual_creation"
    DERIVED = "derived"
    IMPORTED = "imported"
    AI_GENERATED = "ai_generated"
    CONSENSUS = "consensus"  # Community vote/approval


class EventType(Enum):
    EXTRACTED = "extracted"
    REFINED = "refined"
    MERGED = "merged"
    FORKED = "forked"
    DEPRECATED = "deprecated"
    CERTIFIED = "certified"
    LICENSED = "licensed"
    TRANSFERRED = "transferred"


class AgentType(Enum):
    HUMAN = "human"
    AUTOMATED_SCRIPT = "automated_script"
    AI_ASSISTANT = "ai_assistant"
    CONSENSUS = "consensus"
```

### 2.2 Storage Structure (Extension)

```
store/
├── objects/{type}/{hash[:2]}/{hash}/
│   ├── content (raw bytes)
│   ├── metadata.json (ObjectMetadata)
│   └── provenance.json (ProvenanceChain)  ← NEW
│
├── provenance/
│   ├── by_creator/{creator_id}/
│   │   └── objects.json  # Liste objets par créateur
│   ├── by_origin/{source_type}/
│   │   └── objects.json  # Liste objets par origine
│   └── timeline/
│       └── {YYYY-MM-DD}.json  # Événements par jour
│
├── licenses/
│   ├── definitions/
│   │   ├── MIT.yml
│   │   ├── GPL-3.0.yml
│   │   ├── Apache-2.0.yml
│   │   └── proprietary/
│   │       └── {custom-license-id}.yml
│   └── by_object/{hash}.json  # Licenses applicables
│
└── signatures/
    ├── gpg/
    │   └── {key_fingerprint}/
    │       └── signed_objects.json
    └── by_object/{hash}/
        └── signatures.json
```

### 2.3 Exemples YAML (Provenance)

```yaml
# provenance/objects/pattern/a7/a7f3d912/provenance.yml

origin:
  source_type: empirical_analysis
  dataset: "70_format_extractors"
  analysis_hash: "b62a2d8f"
  created_at: "2025-10-15T10:00:00Z"
  created_by: "panini-research"
  location: "research/pattern_analysis_report.md"
  confidence: 0.95
  validation_method: "automated_pattern_extraction"
  peer_reviewed: false

evolution:
  - timestamp: "2025-10-15T10:00:00Z"
    event_type: extracted
    agent:
      agent_type: automated_script
      identity: "pattern_consolidation_v3.0"
      display_name: "Pattern Consolidation Script"
      verified: true
      verification_method: "code_signature"
    derivation_hash: null
    capabilities_added: ["signature_matching"]
    capabilities_removed: []
    breaking_changes: false
    reason: "Extracted from 59.7% of format extractors"
    issue_refs: []

  - timestamp: "2025-10-20T14:30:00Z"
    event_type: refined
    agent:
      agent_type: human
      identity: "stephane@panini.dev"
      display_name: "Stéphane Denis"
      verified: true
      verification_method: "gpg"
    derivation_hash: "b8e0fa23"
    capabilities_added: ["mask_support"]
    capabilities_removed: []
    breaking_changes: false
    reason: "Add mask support for partial signature matching"
    issue_refs: ["#42"]

  - timestamp: "2025-10-22T09:15:00Z"
    event_type: certified
    agent:
      agent_type: consensus
      identity: "community_vote_2025-10-22"
      display_name: "PaniniFS Community"
      verified: true
      verification_method: "multi_sig"
    derivation_hash: null
    capabilities_added: ["certified_stable"]
    capabilities_removed: []
    breaking_changes: false
    reason: "Approved by community vote (87% approval)"
    issue_refs: ["#45", "#47"]

contributors:
  - id: "panini-research"
    role: primary_author
    contributions: ["design", "implementation", "testing"]
    contribution_pct: 75.0
    first_contribution: "2025-10-15T10:00:00Z"
    last_contribution: "2025-10-15T10:00:00Z"
  
  - id: "stephane@panini.dev"
    role: maintainer
    contributions: ["refinement", "documentation"]
    contribution_pct: 25.0
    first_contribution: "2025-10-20T14:30:00Z"
    last_contribution: "2025-10-20T14:30:00Z"

licenses:
  - license_id: "MIT"
    license_text_hash: "a3c4e8f2"  # Hash du texte MIT
    applies_to: "all"  # "all", "code", "schema", "data"
    granted_by: "panini-research"
    granted_at: "2025-10-15T10:00:00Z"
    conditions: []
    compatible_with: ["Apache-2.0", "GPL-3.0", "BSD-3-Clause"]

signatures:
  - signature_type: gpg
    key_id: "0x1234567890ABCDEF"
    key_fingerprint: "1234 5678 90AB CDEF 1234 5678 90AB CDEF 1234 5678"
    signer: "stephane@panini.dev"
    signed_at: "2025-10-20T14:30:00Z"
    signature: "-----BEGIN PGP SIGNATURE-----\n...\n-----END PGP SIGNATURE-----"
    verifiable_content_hash: "a7f3d912"

traceability_metadata:
  audit_trail_complete: true
  reproducible: true
  source_available: true
  dependencies: []
  build_info:
    tool: "panini-pattern-extractor"
    version: "v3.0.0"
    environment: "python-3.11"
```

---

## 3. Licensing & Copyright

### 3.1 License System

```python
@dataclass
class License:
    """Définition d'une license applicable à un objet"""
    
    license_id: str  # "MIT", "GPL-3.0", "Apache-2.0", "CC-BY-4.0", etc.
    license_text_hash: str  # Hash du texte complet de la license
    
    # Scope d'application
    applies_to: LicenseScope  # "all", "code", "schema", "data", "docs"
    
    # Attribution
    granted_by: str  # Identité du licensor
    granted_at: str  # ISO 8601
    
    # Conditions & restrictions
    conditions: List[LicenseCondition]
    restrictions: List[LicenseRestriction]
    
    # Compatibilité
    compatible_with: List[str]  # Autres licenses compatibles
    incompatible_with: List[str]
    
    # Metadata
    osi_approved: bool  # Open Source Initiative approved
    fsf_free: bool  # Free Software Foundation free
    copyleft: bool
    patent_grant: bool
    trademark_grant: bool


class LicenseScope(Enum):
    ALL = "all"
    CODE = "code"
    SCHEMA = "schema"
    DATA = "data"
    DOCUMENTATION = "documentation"


class LicenseCondition(Enum):
    ATTRIBUTION = "attribution"  # Must credit author
    SHARE_ALIKE = "share_alike"  # Derivatives same license
    DISCLOSE_SOURCE = "disclose_source"  # Source must be available
    NETWORK_USE = "network_use"  # Use over network = distribution
    PATENT_USE = "patent_use"  # Patent license included
    NO_SUBLICENSE = "no_sublicense"  # Cannot sublicense


class LicenseRestriction(Enum):
    COMMERCIAL_USE = "commercial_use"  # Cannot use commercially
    TRADEMARK_USE = "trademark_use"  # Cannot use trademarks
    LIABILITY = "liability"  # No warranty/liability
    MODIFICATION = "modification"  # Cannot modify
    DISTRIBUTION = "distribution"  # Cannot distribute
    PRIVATE_USE = "private_use"  # Cannot use privately
```

### 3.2 Composite Licenses

Pour objets dérivés de sources avec licenses différentes:

```yaml
# licenses/by_object/d0e3cf56.yml (objet merge de 2 parents)

composite_license:
  primary_license: "MIT"
  inherited_licenses:
    - source_hash: "b8e0fa23"
      license_id: "MIT"
      compatibility: compatible
    
    - source_hash: "c5d2be45"
      license_id: "Apache-2.0"
      compatibility: compatible
  
  effective_license:
    license_id: "MIT"  # Most permissive
    reason: "All source licenses compatible with MIT"
    conditions: ["attribution"]
    restrictions: ["liability"]
  
  attribution_requirements:
    - "Original MAGIC_NUMBER pattern © 2025 PaniniFS Research (MIT)"
    - "Mask support feature © 2025 Stéphane Denis (MIT)"
    - "Variable offset feature © 2025 Community Contributors (Apache-2.0)"
```

### 3.3 License Definitions (YAML)

```yaml
# licenses/definitions/MIT.yml

license_id: MIT
full_name: "MIT License"
short_name: "MIT"
spdx_identifier: "MIT"

text: |
  MIT License
  
  Copyright (c) {year} {copyright_holder}
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
  
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

properties:
  osi_approved: true
  fsf_free: true
  copyleft: false
  patent_grant: false
  trademark_grant: false

permissions:
  - commercial_use
  - modification
  - distribution
  - private_use

conditions:
  - attribution
  - include_license_text

limitations:
  - liability
  - warranty

compatible_licenses:
  - Apache-2.0
  - GPL-3.0
  - BSD-3-Clause
  - CC-BY-4.0

incompatible_licenses: []
```

### 3.4 Copyright Holder Registry

```python
@dataclass
class CopyrightHolder:
    """Détenteur de copyright"""
    
    holder_id: str  # Unique identifier
    legal_name: str  # Nom légal complet
    display_name: Optional[str]
    
    holder_type: HolderType  # "individual", "organization", "collective"
    
    # Contact
    email: Optional[str]
    website: Optional[str]
    
    # Vérification
    verified: bool
    verification_method: Optional[str]
    verification_date: Optional[str]
    
    # Rights
    jurisdiction: str  # ex: "US", "EU", "FR"
    copyright_year: int
    rights_statement: Optional[str]


class HolderType(Enum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    COLLECTIVE = "collective"  # ex: "PaniniFS Community"
    ANONYMOUS = "anonymous"
    PUBLIC_DOMAIN = "public_domain"
```

---

## 4. Attribution & Crédit

### 4.1 Contributor Model

```python
@dataclass
class Contributor:
    """
    Contributeur à un objet
    
    Supporte attribution fine et calcul de contribution
    """
    
    id: str  # Identité (email, GPG key ID, DID)
    role: ContributorRole
    
    # Contributions
    contributions: List[ContributionType]
    contribution_pct: float  # [0.0, 100.0]
    
    # Timeline
    first_contribution: str  # ISO 8601
    last_contribution: str  # ISO 8601
    
    # Metadata
    display_name: Optional[str]
    affiliation: Optional[str]
    orcid: Optional[str]  # Academic identifier
    
    # Rights
    copyright_holder: bool
    license_grant: Optional[str]


class ContributorRole(Enum):
    PRIMARY_AUTHOR = "primary_author"
    CO_AUTHOR = "co_author"
    MAINTAINER = "maintainer"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    TRANSLATOR = "translator"
    SPONSOR = "sponsor"


class ContributionType(Enum):
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    REFINEMENT = "refinement"
    BUG_FIX = "bug_fix"
    OPTIMIZATION = "optimization"
    TRANSLATION = "translation"
    FUNDING = "funding"
```

### 4.2 Citation Format

Pour objets académiques/recherche:

```yaml
# Fichier: objects/pattern/a7/a7f3d912/citation.yml

citation:
  # BibTeX
  bibtex: |
    @software{panini_magic_number_2025,
      author = {PaniniFS Research and Denis, Stéphane},
      title = {MAGIC\_NUMBER Pattern for Binary Format Recognition},
      year = {2025},
      version = {v2.0},
      url = {https://github.com/stephanedenis/Panini-Research},
      hash = {a7f3d912},
      license = {MIT}
    }
  
  # APA 7th
  apa: "PaniniFS Research, & Denis, S. (2025). MAGIC_NUMBER Pattern for Binary Format Recognition (v2.0) [Computer software]. https://github.com/stephanedenis/Panini-Research"
  
  # Chicago
  chicago: "PaniniFS Research and Stéphane Denis. MAGIC_NUMBER Pattern for Binary Format Recognition. Version 2.0. Computer software. 2025. https://github.com/stephanedenis/Panini-Research."
  
  # MLA
  mla: "PaniniFS Research, and Stéphane Denis. MAGIC_NUMBER Pattern for Binary Format Recognition. Version 2.0, 2025. Software."
  
  # DOI (optionnel si publié académiquement)
  doi: null
  
  # ORCID des auteurs
  authors_orcid:
    - name: "Stéphane Denis"
      orcid: "0000-0000-0000-0000"  # Exemple
```

### 4.3 Attribution Graph

Pour visualiser réseau de contributions:

```python
class AttributionGraph:
    """Graphe d'attribution pour analytics et visualisation"""
    
    def __init__(self, store: ContentAddressedStore):
        self.store = store
        self._graph = {}  # NetworkX graph
    
    def compute_impact_score(self, contributor_id: str) -> float:
        """
        Score d'impact d'un contributeur
        
        Basé sur:
        - Nombre d'objets créés
        - Nombre d'objets maintenus
        - Citations par d'autres objets
        - Usage dans grammaires
        - Reputation votes (si applicable)
        """
        pass
    
    def find_collaborators(self, contributor_id: str) -> List[str]:
        """Trouve co-contributeurs fréquents"""
        pass
    
    def contribution_timeline(self, contributor_id: str) -> Dict[str, int]:
        """Timeline de contributions (par mois/année)"""
        pass
    
    def top_contributors(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Top contributeurs par impact score"""
        pass
```

---

## 5. Access Control & Visibilité

### 5.1 Visibility Scopes

```python
class VisibilityScope(Enum):
    """Niveau de visibilité d'un objet"""
    
    PUBLIC = "public"  # Accessible par tous
    UNLISTED = "unlisted"  # Accessible par hash, mais pas indexed
    RESTRICTED = "restricted"  # Access control list
    PRIVATE = "private"  # Créateur seulement
    ORGANIZATION = "organization"  # Membres org seulement
    COLLABORATIVE = "collaborative"  # Collaborateurs explicites
    EMBARGOED = "embargoed"  # Public après date


@dataclass
class AccessPolicy:
    """Politique d'accès pour un objet"""
    
    visibility: VisibilityScope
    
    # Access Control List (si restricted/collaborative)
    acl: Optional[List[AccessRule]]
    
    # Embargo (si embargoed)
    embargo_until: Optional[str]  # ISO 8601
    
    # Organization (si organization scope)
    organization_id: Optional[str]
    
    # Audit
    access_logging: bool
    require_attribution: bool  # Log qui accède
    
    # Discovery
    discoverable: bool  # Apparaît dans recherches
    indexable: bool  # Indexé par similarity hash


@dataclass
class AccessRule:
    """Règle d'accès individuelle"""
    
    principal: str  # User ID, group ID, org ID
    principal_type: PrincipalType
    
    permissions: List[Permission]
    granted_by: str
    granted_at: str
    expires_at: Optional[str]


class PrincipalType(Enum):
    USER = "user"
    GROUP = "group"
    ORGANIZATION = "organization"
    SERVICE_ACCOUNT = "service_account"
    PUBLIC = "public"


class Permission(Enum):
    READ = "read"
    WRITE = "write"  # Créer dérivations
    DELETE = "delete"
    SHARE = "share"
    GRANT = "grant"  # Accorder accès à d'autres
    ADMIN = "admin"  # Full control
```

### 5.2 Storage avec ACL

```yaml
# objects/pattern/a7/a7f3d912/access.yml

access_policy:
  visibility: restricted
  discoverable: true
  indexable: true
  access_logging: true
  require_attribution: true
  
  acl:
    - principal: "panini-research"
      principal_type: organization
      permissions: [read, write, share, grant, admin]
      granted_by: "creator"
      granted_at: "2025-10-15T10:00:00Z"
      expires_at: null
    
    - principal: "stephane@panini.dev"
      principal_type: user
      permissions: [read, write]
      granted_by: "panini-research"
      granted_at: "2025-10-20T14:30:00Z"
      expires_at: null
    
    - principal: "community-reviewers"
      principal_type: group
      permissions: [read]
      granted_by: "panini-research"
      granted_at: "2025-10-21T09:00:00Z"
      expires_at: "2025-11-21T09:00:00Z"  # 1 mois
```

### 5.3 Privacy Model

Pour données sensibles:

```python
@dataclass
class PrivacyMetadata:
    """Métadonnées de confidentialité"""
    
    contains_pii: bool  # Personally Identifiable Information
    contains_confidential: bool
    data_classification: DataClassification
    
    # Compliance
    gdpr_applicable: bool
    ccpa_applicable: bool
    retention_period: Optional[int]  # jours
    
    # Anonymization
    anonymized: bool
    anonymization_method: Optional[str]
    
    # Encryption
    encrypted_at_rest: bool
    encryption_method: Optional[str]


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"
```

---

## 6. Audit & Compliance

### 6.1 Audit Trail

```python
@dataclass
class AuditEvent:
    """Événement d'audit"""
    
    event_id: str  # UUID
    timestamp: str  # ISO 8601 avec microseconds
    
    # Action
    action: AuditAction
    object_hash: str
    object_type: str
    
    # Actor
    actor: Agent
    actor_ip: Optional[str]
    actor_location: Optional[str]
    
    # Context
    success: bool
    error_message: Optional[str]
    
    # Changes (si applicable)
    changes: Optional[Dict[str, Any]]
    
    # Metadata
    request_id: Optional[str]
    session_id: Optional[str]


class AuditAction(Enum):
    # Object operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Derivations
    DERIVE = "derive"
    MERGE = "merge"
    FORK = "fork"
    
    # Access control
    GRANT_ACCESS = "grant_access"
    REVOKE_ACCESS = "revoke_access"
    
    # Licensing
    LICENSE = "license"
    RELICENSE = "relicense"
    
    # Metadata
    MODIFY_METADATA = "modify_metadata"
    SIGN = "sign"
    CERTIFY = "certify"
```

### 6.2 Audit Storage

```
store/
└── audit/
    ├── by_date/
    │   └── 2025-10-28/
    │       └── events.jsonl  # JSON Lines format
    ├── by_object/
    │   └── {hash}/
    │       └── audit.jsonl
    ├── by_actor/
    │   └── {actor_id}/
    │       └── audit.jsonl
    └── by_action/
        └── {action}/
            └── audit.jsonl
```

### 6.3 Compliance Reports

```python
class ComplianceReporter:
    """Générateur de rapports de compliance"""
    
    def generate_gdpr_report(self, object_hash: str) -> Dict:
        """
        Rapport GDPR pour un objet
        
        - Données personnelles contenues
        - Base légale du traitement
        - Durée de conservation
        - Droits des personnes concernées
        - Transferts internationaux
        """
        pass
    
    def generate_license_compliance_report(self, 
                                          object_hash: str) -> Dict:
        """
        Rapport de conformité des licenses
        
        - License actuelle
        - Licenses héritées
        - Compatibilité
        - Obligations (attribution, share-alike, etc.)
        - Violations potentielles
        """
        pass
    
    def generate_attribution_report(self, object_hash: str) -> Dict:
        """
        Rapport d'attribution requis
        
        - Tous les contributeurs
        - Notices de copyright
        - Textes de licenses
        - Citations recommandées
        """
        pass
```

---

## 7. Signatures Cryptographiques

### 7.1 GPG Signatures

```python
@dataclass
class Signature:
    """Signature cryptographique d'un objet"""
    
    signature_type: SignatureType  # "gpg", "ssh", "minisign", "did"
    
    # GPG-specific
    key_id: Optional[str]  # ex: "0x1234567890ABCDEF"
    key_fingerprint: Optional[str]
    key_type: Optional[str]  # "RSA", "Ed25519", etc.
    
    # Signer
    signer_identity: str
    signer_email: Optional[str]
    
    # Signature
    signature_data: str  # Armored signature
    signed_at: str  # ISO 8601
    
    # Verification
    verifiable_content_hash: str  # Hash signé
    verification_status: Optional[VerificationStatus]
    verified_at: Optional[str]
    verified_by: Optional[str]


class SignatureType(Enum):
    GPG = "gpg"
    SSH = "ssh"
    MINISIGN = "minisign"
    DID = "did"  # Decentralized Identifiers
    X509 = "x509"


class VerificationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN_KEY = "unknown_key"
    NOT_VERIFIED = "not_verified"
```

### 7.2 Signature Workflow

```python
class SignatureManager:
    """Gestion des signatures cryptographiques"""
    
    def sign_object(self, 
                   object_hash: str, 
                   key_id: str,
                   signature_type: SignatureType = SignatureType.GPG) -> Signature:
        """
        Signer un objet avec clé GPG/SSH
        
        1. Load object content
        2. Compute canonical hash
        3. Sign hash with key
        4. Store signature
        5. Update provenance
        """
        pass
    
    def verify_signature(self, 
                        object_hash: str, 
                        signature: Signature) -> VerificationStatus:
        """
        Vérifier une signature
        
        1. Load object content
        2. Compute canonical hash
        3. Verify signature against hash
        4. Check key validity (not revoked, not expired)
        5. Return status
        """
        pass
    
    def multi_sign(self, 
                  object_hash: str, 
                  required_signers: List[str],
                  threshold: int) -> bool:
        """
        Multi-signature (consensus)
        
        Require N out of M signatures pour certification
        """
        pass
```

### 7.3 Web of Trust

```python
class TrustNetwork:
    """Réseau de confiance entre contributeurs"""
    
    def __init__(self):
        self._trust_graph = {}  # NetworkX graph
    
    def add_trust(self, 
                 truster: str, 
                 trustee: str, 
                 trust_level: TrustLevel):
        """Ajouter relation de confiance"""
        pass
    
    def compute_trust_score(self, 
                           source: str, 
                           target: str) -> float:
        """
        Score de confiance entre 2 identités
        
        Basé sur:
        - Trust direct
        - Trust transitif (web of trust)
        - Reputation
        - Verification history
        """
        pass
    
    def trusted_by_community(self, identity: str) -> bool:
        """Identité de confiance pour la communauté?"""
        pass


class TrustLevel(Enum):
    UNKNOWN = 0
    MARGINAL = 1
    FULL = 2
    ULTIMATE = 3
```

---

## 8. Gouvernance Communautaire

### 8.1 Reputation System

```python
@dataclass
class ReputationScore:
    """Score de réputation d'un contributeur"""
    
    contributor_id: str
    
    # Scores composants
    contribution_score: float  # Quantité contributions
    quality_score: float  # Qualité (reviews, bugs, etc.)
    impact_score: float  # Impact (usage, citations)
    trust_score: float  # Trust from community
    
    # Score total [0.0, 100.0]
    total_score: float
    
    # Breakdown
    objects_created: int
    objects_maintained: int
    reviews_given: int
    reviews_received_positive: int
    citations: int
    
    # Timeline
    first_contribution: str
    last_contribution: str
    active_days: int


class ReputationManager:
    """Gestion de la réputation"""
    
    def compute_reputation(self, contributor_id: str) -> ReputationScore:
        """Calculer score de réputation"""
        pass
    
    def reputation_leaderboard(self, limit: int = 100) -> List[ReputationScore]:
        """Classement par réputation"""
        pass
    
    def badge_eligibility(self, contributor_id: str) -> List[Badge]:
        """Badges éligibles pour contributeur"""
        pass


class Badge(Enum):
    """Badges de reconnaissance"""
    CREATOR = "creator"  # Premier objet
    PROLIFIC = "prolific"  # 100+ objets
    MAINTAINER = "maintainer"  # Maintenance 1+ an
    REVIEWER = "reviewer"  # 50+ reviews
    PIONEER = "pioneer"  # Early adopter
    MENTOR = "mentor"  # Aide nouveaux contributeurs
    CERTIFIED = "certified"  # Objets certifiés
    TRUSTED = "trusted"  # High trust score
```

### 8.2 Governance Model

```yaml
# governance/policies/contribution.yml

contribution_policy:
  version: "1.0"
  effective_date: "2025-10-01"
  
  # Acceptance criteria pour nouveaux objets
  acceptance_criteria:
    - criterion: "passes_tests"
      required: true
    - criterion: "documented"
      required: true
    - criterion: "licensed"
      required: true
    - criterion: "peer_reviewed"
      required: false  # Optionnel mais recommandé
  
  # Review process
  review_process:
    required_reviewers: 2
    review_timeout_days: 7
    approval_threshold: 0.75  # 75% approval
  
  # Certification
  certification:
    enabled: true
    required_signatures: 3
    certifiers:
      - "core-team"
      - "trusted-maintainers"
    certification_threshold: 0.67  # 2/3
  
  # Conflict resolution
  conflict_resolution:
    escalation_path:
      - "maintainer-review"
      - "core-team-vote"
      - "community-vote"
    voting_quorum: 0.5
    voting_threshold: 0.6


# governance/policies/licensing.yml

licensing_policy:
  version: "1.0"
  
  # Licenses autorisées
  approved_licenses:
    - MIT
    - Apache-2.0
    - GPL-3.0
    - BSD-3-Clause
    - CC-BY-4.0
    - CC-BY-SA-4.0
  
  # License par défaut pour objets communautaires
  default_license: "MIT"
  
  # Compatibility checking
  enforce_compatibility: true
  
  # Proprietary licenses
  proprietary_allowed: true
  proprietary_requires_approval: true
```

### 8.3 Decision Making

```python
class GovernanceVote:
    """Vote de gouvernance"""
    
    def __init__(self, 
                 proposal_id: str,
                 proposal_type: ProposalType):
        self.proposal_id = proposal_id
        self.proposal_type = proposal_type
        self._votes = {}
    
    def cast_vote(self, 
                 voter_id: str, 
                 vote: Vote,
                 weight: Optional[float] = None):
        """
        Voter sur proposition
        
        Weight basé sur reputation (optionnel)
        """
        pass
    
    def tally_votes(self) -> VoteResult:
        """Compter les votes"""
        pass
    
    def quorum_reached(self, quorum: float = 0.5) -> bool:
        """Quorum atteint?"""
        pass


class ProposalType(Enum):
    OBJECT_CERTIFICATION = "object_certification"
    LICENSE_CHANGE = "license_change"
    POLICY_CHANGE = "policy_change"
    CONTRIBUTOR_BAN = "contributor_ban"
    FUNDING_ALLOCATION = "funding_allocation"


class Vote(Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"


@dataclass
class VoteResult:
    total_voters: int
    yes_votes: int
    no_votes: int
    abstain_votes: int
    yes_weight: float
    no_weight: float
    passed: bool
```

---

## 9. Implémentation

### 9.1 Phase 1: Provenance (2 semaines)

**Objectif**: Traçabilité complète

```python
# Implementation tasks:
1. ✅ Extend ObjectMetadata with provenance fields
2. ✅ Implement ProvenanceChain dataclass
3. ✅ Storage structure for provenance/
4. ✅ ProvenanceManager class:
   - record_event()
   - get_full_history()
   - find_by_creator()
   - timeline_view()
5. ✅ Integration avec DerivationManager
6. ✅ Tests (10 cases)
7. ✅ Documentation
```

**Deliverables**:
- `provenance_manager.py` (400 lines)
- `test_provenance.py` (250 lines)
- `PROVENANCE_GUIDE.md` (200 lines)

### 9.2 Phase 2: Licensing (1 semaine)

**Objectif**: Système de licenses

```python
# Implementation tasks:
1. ✅ License dataclass
2. ✅ License definitions (MIT, Apache, GPL, CC)
3. ✅ LicenseManager class:
   - apply_license()
   - check_compatibility()
   - compute_composite_license()
4. ✅ License validation dans store
5. ✅ Tests (8 cases)
6. ✅ Documentation
```

**Deliverables**:
- `license_manager.py` (350 lines)
- `licenses/definitions/*.yml` (20 licenses)
- `test_licensing.py` (200 lines)

### 9.3 Phase 3: Attribution (1 semaine)

**Objectif**: Crédit & citations

```python
# Implementation tasks:
1. ✅ Contributor dataclass
2. ✅ Citation generation (BibTeX, APA, etc.)
3. ✅ AttributionGraph class
4. ✅ Impact score calculation
5. ✅ Attribution requirements check
6. ✅ Tests (6 cases)
7. ✅ Documentation
```

**Deliverables**:
- `attribution_manager.py` (300 lines)
- `test_attribution.py` (180 lines)

### 9.4 Phase 4: Access Control (2 semaines)

**Objectif**: Visibilité & permissions

```python
# Implementation tasks:
1. ✅ AccessPolicy dataclass
2. ✅ ACL implementation
3. ✅ AccessManager class:
   - check_permission()
   - grant_access()
   - revoke_access()
4. ✅ Integration avec ContentAddressedStore
5. ✅ Privacy metadata
6. ✅ Tests (12 cases)
7. ✅ Documentation
```

**Deliverables**:
- `access_manager.py` (450 lines)
- `test_access_control.py` (300 lines)
- `ACCESS_CONTROL_GUIDE.md` (250 lines)

### 9.5 Phase 5: Audit (1 semaine)

**Objectif**: Audit trails & compliance

```python
# Implementation tasks:
1. ✅ AuditEvent dataclass
2. ✅ AuditLogger class
3. ✅ Audit storage (JSONL)
4. ✅ ComplianceReporter class
5. ✅ GDPR/CCPA compliance tools
6. ✅ Tests (8 cases)
7. ✅ Documentation
```

**Deliverables**:
- `audit_logger.py` (300 lines)
- `compliance_reporter.py` (400 lines)
- `test_audit.py` (200 lines)

### 9.6 Phase 6: Signatures (1 semaine)

**Objectif**: Cryptographic signatures

```python
# Implementation tasks:
1. ✅ Signature dataclass
2. ✅ SignatureManager class (GPG integration)
3. ✅ Verification workflow
4. ✅ Multi-signature support
5. ✅ TrustNetwork class
6. ✅ Tests (10 cases)
7. ✅ Documentation
```

**Deliverables**:
- `signature_manager.py` (400 lines)
- `trust_network.py` (250 lines)
- `test_signatures.py` (220 lines)

### 9.7 Phase 7: Governance (2 semaines)

**Objectif**: Community governance

```python
# Implementation tasks:
1. ✅ ReputationScore dataclass
2. ✅ ReputationManager class
3. ✅ GovernanceVote class
4. ✅ Policy definitions (YAML)
5. ✅ Badge system
6. ✅ Tests (8 cases)
7. ✅ Documentation
```

**Deliverables**:
- `reputation_manager.py` (350 lines)
- `governance_vote.py` (300 lines)
- `governance/policies/*.yml`
- `test_governance.py` (200 lines)
- `GOVERNANCE_GUIDE.md` (300 lines)

### 9.8 Phase 8: Integration & Testing (1 semaine)

**Objectif**: Tout intégré et testé

```python
# Implementation tasks:
1. ✅ Integration tests (end-to-end)
2. ✅ Performance benchmarks
3. ✅ Security audit
4. ✅ Documentation complète
5. ✅ Migration guide
6. ✅ CLI tools
```

**Deliverables**:
- `test_integration_ip.py` (400 lines)
- `IP_SYSTEM_GUIDE.md` (500 lines)
- `MIGRATION_v4.0_IP.md` (300 lines)

---

## 10. Architecture Intégrée (Vue d'ensemble)

### 10.1 Stack Complet

```
┌─────────────────────────────────────────────────────────┐
│              Application Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  CLI Tools  │  │  REST API   │  │   Web UI    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│           Intellectual Property Layer (NEW)              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │ Provenance │ │ Licensing  │ │Attribution │         │
│  │  Manager   │ │  Manager   │ │  Manager   │         │
│  └────────────┘ └────────────┘ └────────────┘         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │   Access   │ │   Audit    │ │ Signature  │         │
│  │  Manager   │ │  Logger    │ │  Manager   │         │
│  └────────────┘ └────────────┘ └────────────┘         │
│  ┌────────────┐ ┌────────────┐                         │
│  │ Reputation │ │ Governance │                         │
│  │  Manager   │ │    Vote    │                         │
│  └────────────┘ └────────────┘                         │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│            Semantic Layer (v4.0)                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │ Derivation │ │  Semantic  │ │  Pattern   │         │
│  │  Manager   │ │    DAG     │ │   Engine   │         │
│  └────────────┘ └────────────┘ └────────────┘         │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│         Content-Addressed Storage (v4.0)                 │
│  ┌────────────────────────────────────────────────────┐│
│  │          ContentAddressedStore                      ││
│  │  ┌──────────────┐  ┌──────────────┐               ││
│  │  │  Exact Hash  │  │Similarity Hash│              ││
│  │  │  (SHA-256)   │  │(Entropy+Struct)│              ││
│  │  └──────────────┘  └──────────────┘               ││
│  └────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                 Physical Storage                         │
│        store/ (objects, provenance, licenses,            │
│                audit, signatures, governance)            │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Data Flow (Exemple: Créer Pattern avec IP)

```python
# 1. User creates pattern
pattern_data = {
    "type": "MAGIC_NUMBER",
    "signature": "89504E47",
    # ...
}

# 2. Store in CAS (exact + similarity hash)
exact_hash = store.store(
    content=pattern_data,
    object_type="pattern"
)  # → "a7f3d912"

# 3. Record provenance
provenance_mgr.record_event(
    object_hash=exact_hash,
    event_type=EventType.CREATED,
    agent=Agent(
        agent_type=AgentType.HUMAN,
        identity="stephane@panini.dev",
        verified=True
    ),
    origin=Origin(
        source_type=SourceType.MANUAL_CREATION,
        created_by="stephane@panini.dev",
        created_at=datetime.utcnow().isoformat()
    )
)

# 4. Apply license
license_mgr.apply_license(
    object_hash=exact_hash,
    license_id="MIT",
    granted_by="stephane@panini.dev"
)

# 5. Add attribution
attribution_mgr.add_contributor(
    object_hash=exact_hash,
    contributor=Contributor(
        id="stephane@panini.dev",
        role=ContributorRole.PRIMARY_AUTHOR,
        contributions=[ContributionType.DESIGN, 
                      ContributionType.IMPLEMENTATION],
        contribution_pct=100.0
    )
)

# 6. Set access policy
access_mgr.set_policy(
    object_hash=exact_hash,
    policy=AccessPolicy(
        visibility=VisibilityScope.PUBLIC,
        discoverable=True,
        indexable=True,
        access_logging=True
    )
)

# 7. Sign object (optionnel)
signature_mgr.sign_object(
    object_hash=exact_hash,
    key_id="0x1234567890ABCDEF"
)

# 8. Audit logging (automatique)
# → AuditEvent enregistré pour chaque opération

# 9. Result: Fully traced, licensed, attributed object!
```

### 10.3 Query Examples

```python
# Find all objects by creator
objects = provenance_mgr.find_by_creator("stephane@panini.dev")

# Check license compatibility
compatible = license_mgr.check_compatibility(
    parent_licenses=["MIT", "Apache-2.0"],
    proposed_license="GPL-3.0"
)  # → True/False

# Compute contributor impact
impact = reputation_mgr.compute_reputation("stephane@panini.dev")
# → ReputationScore(total_score=87.5, objects_created=42, ...)

# Generate attribution text
attribution = attribution_mgr.generate_attribution_text("a7f3d912")
# → "MAGIC_NUMBER Pattern © 2025 Stéphane Denis. Licensed under MIT."

# Check access permission
allowed = access_mgr.check_permission(
    object_hash="a7f3d912",
    principal="alice@example.com",
    permission=Permission.READ
)  # → True/False

# Generate compliance report
report = compliance_reporter.generate_gdpr_report("a7f3d912")
# → {contains_pii: False, retention_period: null, ...}

# Verify signature
status = signature_mgr.verify_signature(
    object_hash="a7f3d912",
    signature=sig
)  # → VerificationStatus.VALID
```

---

## 11. Roadmap Complet (10 semaines)

| Phase | Semaines | Deliverable | LOC |
|-------|----------|-------------|-----|
| 1. Provenance | 2 | provenance_manager.py + tests + docs | 850 |
| 2. Licensing | 1 | license_manager.py + definitions + tests | 750 |
| 3. Attribution | 1 | attribution_manager.py + tests | 480 |
| 4. Access Control | 2 | access_manager.py + tests + docs | 1000 |
| 5. Audit | 1 | audit_logger.py + compliance + tests | 900 |
| 6. Signatures | 1 | signature_manager.py + trust + tests | 870 |
| 7. Governance | 2 | reputation + voting + policies + tests | 1150 |
| 8. Integration | 1 | integration tests + guides | 1200 |
| **TOTAL** | **10** | **IP System Complete** | **7200** |

---

## 12. Validation Pāṇinienne

### 12.1 Alignement Philosophique

| Concept Pāṇini | Équivalent PaniniFS | Validation |
|----------------|---------------------|------------|
| **Sūtra attribution** | Provenance chains | ✅ Chaque objet traçable à son auteur |
| **Commentaire tradition** | Derivation system | ✅ Commentaires = dérivations avec attribution |
| **Guru-shishya parampara** | Trust network | ✅ Chaîne de confiance maître-élève |
| **Vākya-padīya** | Citation format | ✅ Citations académiques standardisées |
| **Ācārya authority** | Certification | ✅ Experts certifient objets |
| **Smṛti vs Śruti** | Original vs Derived | ✅ Origine claire (empirique vs manuel) |

### 12.2 Principes Respectés

1. **Immutabilité**: Objets immutables, dérivations traçables
2. **Attribution**: Chaque contribution créditée
3. **Autorité**: Système de certification et réputation
4. **Transmission**: Chaîne de provenance documentée
5. **Vérifiabilité**: Signatures cryptographiques
6. **Communauté**: Gouvernance collective

---

## 13. Conclusion

Cette architecture de propriété intellectuelle pour PaniniFS v4.0 fournit:

✅ **Traçabilité Complète**: Provenance chains, audit trails, timeline  
✅ **Propriété Claire**: Attribution, copyright holders, licenses  
✅ **Conformité Légale**: GDPR, CCPA, license compatibility  
✅ **Transparence**: Audit logging, compliance reports  
✅ **Sécurité**: Cryptographic signatures, access control  
✅ **Gouvernance**: Reputation, voting, community policies  
✅ **Philosophie Pāṇinienne**: Attribution tradition respectée  

**Prêt pour marketplace de grammaires avec protection IP complète!**

---

**Status:** ✅ Proposition architecturale complète  
**Next Step:** Phase 1 implementation (Provenance Manager)  
**Author:** PaniniFS Research Team  
**License:** MIT  
**Date:** 2025-10-28
