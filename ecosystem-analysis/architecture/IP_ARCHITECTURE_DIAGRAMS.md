# 📊 PaniniFS IP Architecture - Diagrammes

## 1. Architecture Globale (Stack Complet)

```mermaid
graph TB
    subgraph "Application Layer"
        CLI[CLI Tools]
        API[REST API]
        UI[Web UI]
    end
    
    subgraph "IP Layer (NEW v4.0)"
        PM[Provenance Manager]
        LM[License Manager]
        AM[Attribution Manager]
        ACM[Access Manager]
        AL[Audit Logger]
        SM[Signature Manager]
        RM[Reputation Manager]
        GV[Governance Vote]
    end
    
    subgraph "Semantic Layer (v4.0)"
        DM[Derivation Manager]
        DAG[Semantic DAG]
        PE[Pattern Engine]
    end
    
    subgraph "CAS Layer (v4.0)"
        CAS[Content Addressed Store]
        EH[Exact Hash<br/>SHA-256]
        SH[Similarity Hash<br/>Entropy+Struct]
    end
    
    subgraph "Storage Layer"
        FS[(File System<br/>store/)]
    end
    
    CLI --> PM
    API --> LM
    UI --> AM
    
    PM --> DM
    LM --> DM
    AM --> DM
    ACM --> CAS
    AL --> CAS
    SM --> CAS
    
    DM --> DAG
    DAG --> PE
    PE --> CAS
    
    CAS --> EH
    CAS --> SH
    EH --> FS
    SH --> FS
    
    RM -.-> PM
    GV -.-> SM

    style PM fill:#e1f5e1
    style LM fill:#e1f5e1
    style AM fill:#e1f5e1
    style ACM fill:#e1f5e1
    style AL fill:#e1f5e1
    style SM fill:#e1f5e1
    style RM fill:#fff4e1
    style GV fill:#fff4e1
```

---

## 2. Provenance Chain Flow

```mermaid
sequenceDiagram
    participant User
    participant PM as Provenance Manager
    participant CAS as Content Addressed Store
    participant AL as Audit Logger
    participant FS as File System
    
    User->>CAS: Store object
    activate CAS
    CAS->>CAS: Compute exact hash
    CAS->>CAS: Compute similarity hash
    CAS->>FS: Write object/{hash}/content
    CAS-->>User: Return hash
    deactivate CAS
    
    User->>PM: Record creation event
    activate PM
    PM->>PM: Create EvolutionEvent
    PM->>PM: Create Origin record
    PM->>FS: Write provenance.json
    PM->>AL: Log audit event
    PM-->>User: Event recorded
    deactivate PM
    
    Note over User,FS: Later: Derivation
    
    User->>PM: Record refinement
    activate PM
    PM->>FS: Read existing provenance
    PM->>PM: Append EvolutionEvent
    PM->>PM: Update contributor list
    PM->>FS: Update provenance.json
    PM->>AL: Log audit event
    PM-->>User: Evolution tracked
    deactivate PM
```

---

## 3. License Compatibility Checking

```mermaid
flowchart TD
    Start[User creates derived object] --> LoadParents[Load parent objects]
    LoadParents --> ExtractLicenses[Extract parent licenses]
    ExtractLicenses --> CheckCompat{All licenses<br/>compatible?}
    
    CheckCompat -->|Yes| ComputeEffective[Compute effective license]
    CheckCompat -->|No| Error[❌ Reject: Incompatible licenses]
    
    ComputeEffective --> ChooseMost[Choose most permissive]
    ChooseMost --> InheritConds[Inherit conditions]
    InheritConds --> StoreComposite[Store composite license]
    StoreComposite --> Success[✅ License applied]
    
    Error --> End[End]
    Success --> End
    
    style CheckCompat fill:#ffe6e6
    style Error fill:#ffcccc
    style Success fill:#ccffcc
```

---

## 4. Access Control Decision

```mermaid
flowchart TD
    Request[User requests access] --> LoadPolicy[Load AccessPolicy]
    LoadPolicy --> CheckVis{Visibility<br/>scope?}
    
    CheckVis -->|PUBLIC| AllowRead[✅ Allow read]
    CheckVis -->|UNLISTED| CheckHash{Has exact<br/>hash?}
    CheckVis -->|PRIVATE| CheckOwner{Is owner?}
    CheckVis -->|RESTRICTED| CheckACL{In ACL?}
    CheckVis -->|EMBARGOED| CheckDate{After embargo<br/>date?}
    
    CheckHash -->|Yes| AllowRead
    CheckHash -->|No| Deny[❌ Deny: Not found]
    
    CheckOwner -->|Yes| AllowFull[✅ Allow full access]
    CheckOwner -->|No| Deny
    
    CheckACL -->|Yes| CheckPerm{Has required<br/>permission?}
    CheckACL -->|No| Deny
    
    CheckPerm -->|Yes| AllowPerm[✅ Allow with permissions]
    CheckPerm -->|No| Deny
    
    CheckDate -->|Yes| AllowRead
    CheckDate -->|No| Deny
    
    AllowRead --> LogAccess[Log access event]
    AllowFull --> LogAccess
    AllowPerm --> LogAccess
    Deny --> LogDenied[Log denied event]
    
    LogAccess --> End[End]
    LogDenied --> End
    
    style AllowRead fill:#ccffcc
    style AllowFull fill:#ccffcc
    style AllowPerm fill:#ccffcc
    style Deny fill:#ffcccc
```

---

## 5. Signature Verification Flow

```mermaid
sequenceDiagram
    participant User
    participant SM as Signature Manager
    participant CAS as Content Addressed Store
    participant GPG as GPG Keyring
    participant Trust as Trust Network
    
    User->>SM: Verify signature for object
    activate SM
    
    SM->>CAS: Load object content
    CAS-->>SM: Object data
    
    SM->>SM: Compute canonical hash
    
    SM->>GPG: Verify signature
    activate GPG
    GPG->>GPG: Check signature validity
    GPG->>GPG: Check key expiration
    GPG->>GPG: Check key revocation
    GPG-->>SM: Verification result
    deactivate GPG
    
    alt Signature valid
        SM->>Trust: Get signer trust score
        Trust-->>SM: Trust score
        
        SM->>SM: Combine signature + trust
        SM-->>User: ✅ VALID (trust: 0.87)
    else Signature invalid
        SM-->>User: ❌ INVALID
    else Key expired
        SM-->>User: ⚠️ EXPIRED
    else Key revoked
        SM-->>User: ❌ REVOKED
    end
    
    deactivate SM
```

---

## 6. Storage Structure (Extended)

```mermaid
graph TD
    Root[store/] --> Objects[objects/]
    Root --> Provenance[provenance/]
    Root --> Licenses[licenses/]
    Root --> Signatures[signatures/]
    Root --> Audit[audit/]
    Root --> Access[access/]
    
    Objects --> ObjType["{type}/"]
    ObjType --> ObjPrefix["{hash[:2]}/"]
    ObjPrefix --> ObjDir["{hash}/"]
    ObjDir --> Content[content]
    ObjDir --> Meta[metadata.json]
    ObjDir --> Prov[provenance.json]
    
    Provenance --> ProvCreator[by_creator/]
    Provenance --> ProvOrigin[by_origin/]
    Provenance --> ProvTimeline[timeline/]
    
    Licenses --> LicDef[definitions/]
    Licenses --> LicObj[by_object/]
    LicDef --> MIT[MIT.yml]
    LicDef --> GPL[GPL-3.0.yml]
    LicDef --> Apache[Apache-2.0.yml]
    
    Signatures --> SigGPG[gpg/]
    Signatures --> SigObj[by_object/]
    
    Audit --> AuditDate[by_date/]
    Audit --> AuditObj[by_object/]
    Audit --> AuditActor[by_actor/]
    Audit --> AuditAction[by_action/]
    
    Access --> AccessPolicies[policies/]
    
    style Content fill:#e1f5e1
    style Meta fill:#e1f5e1
    style Prov fill:#fff4e1
    style MIT fill:#e1e8f5
    style GPL fill:#e1e8f5
    style Apache fill:#e1e8f5
```

---

## 7. Reputation Calculation

```mermaid
flowchart LR
    subgraph "Input Metrics"
        OC[Objects Created]
        OM[Objects Maintained]
        RG[Reviews Given]
        RP[Reviews Received<br/>Positive]
        Citations[Citations]
        Usage[Usage in Grammars]
    end
    
    subgraph "Score Components"
        OC --> CS[Contribution Score<br/>0-25]
        OM --> CS
        
        RG --> QS[Quality Score<br/>0-25]
        RP --> QS
        
        Citations --> IS[Impact Score<br/>0-25]
        Usage --> IS
        
        Trust[Trust from<br/>Community] --> TS[Trust Score<br/>0-25]
    end
    
    subgraph "Final Score"
        CS --> Total[Total Reputation<br/>0-100]
        QS --> Total
        IS --> Total
        TS --> Total
    end
    
    Total --> Badge{Badge<br/>eligible?}
    Badge -->|80+| Trusted[🏆 Trusted]
    Badge -->|60+| Prolific[⭐ Prolific]
    Badge -->|40+| Contributor[✓ Contributor]
    
    style Total fill:#fff4e1
    style Trusted fill:#ccffcc
    style Prolific fill:#e1f5e1
    style Contributor fill:#f0f0f0
```

---

## 8. Governance Vote Flow

```mermaid
stateDiagram-v2
    [*] --> Proposed: Create proposal
    
    Proposed --> Open: Open for voting
    Open --> Voting: Collect votes
    
    Voting --> Counting: Voting period ends
    Counting --> CheckQuorum: Tally votes
    
    CheckQuorum --> Rejected: Quorum not reached
    CheckQuorum --> CheckThreshold: Quorum reached
    
    CheckThreshold --> Rejected: Threshold not met
    CheckThreshold --> Approved: Threshold met
    
    Approved --> Executed: Execute proposal
    Rejected --> [*]
    Executed --> [*]
    
    note right of Voting
        Weight by reputation (optional)
        Votes: YES, NO, ABSTAIN
    end note
    
    note right of CheckQuorum
        Quorum: 50% participation
        Threshold: 60% approval
    end note
```

---

## 9. Object Lifecycle with IP

```mermaid
timeline
    title Object Lifecycle with IP Tracking
    
    section Creation
        t0 : Created by user
           : Origin recorded
           : License applied (MIT)
           : Signature added
    
    section Evolution
        t1 : Refined (add mask support)
           : Derivation recorded
           : Co-author added
           : Access policy: PUBLIC
    
        t2 : Merged with another branch
           : Composite license computed
           : Multiple contributors
           : Community reviewed
    
        t3 : Certified by core team
           : Multi-signature added
           : Trust score increased
           : Featured in marketplace
    
    section Adoption
        t4 : Used in 50+ grammars
           : 100+ citations
           : Reputation: 85/100
           : Badge: Trusted
```

---

## 10. Multi-License Inheritance

```mermaid
graph TD
    subgraph "Source Objects"
        A[Object A<br/>License: MIT]
        B[Object B<br/>License: Apache-2.0]
        C[Object C<br/>License: BSD-3]
    end
    
    subgraph "Compatibility Matrix"
        A -.->|Compatible| Matrix{License<br/>Compatibility<br/>Checker}
        B -.->|Compatible| Matrix
        C -.->|Compatible| Matrix
    end
    
    subgraph "Derived Object"
        Matrix -->|All compatible| Derived[Object D<br/>Composite License]
        Derived --> Effective[Effective: MIT<br/>Most permissive]
        Derived --> Inherited[Inherited:<br/>- MIT from A<br/>- Apache-2.0 from B<br/>- BSD-3 from C]
        Derived --> Attribution[Attribution:<br/>Must credit A, B, C]
    end
    
    Matrix -.->|Incompatible| Error[❌ Cannot derive<br/>GPL-3.0 + MIT conflict]
    
    style Matrix fill:#ffe6e6
    style Derived fill:#ccffcc
    style Error fill:#ffcccc
```

---

## 11. Audit Trail Example

```mermaid
gantt
    title Audit Trail for Object a7f3d912
    dateFormat YYYY-MM-DD HH:mm
    
    section Creation
    Object created           :milestone, 2025-10-15 10:00, 0d
    License MIT applied      :2025-10-15 10:05, 1m
    Signature added          :2025-10-15 10:10, 1m
    
    section Access
    Read by alice@example    :2025-10-16 14:30, 1m
    Read by bob@example      :2025-10-17 09:15, 1m
    
    section Evolution
    Refined by stephane      :milestone, 2025-10-20 14:30, 0d
    Derivation created       :2025-10-20 14:35, 5m
    Co-author added          :2025-10-20 14:40, 1m
    
    section Governance
    Community review started :2025-10-21 09:00, 7d
    Certified by core team   :milestone, 2025-10-28 10:00, 0d
```

---

## 12. Trust Network

```mermaid
graph LR
    subgraph "Core Team"
        CT1[Core Member 1<br/>Trust: Ultimate]
        CT2[Core Member 2<br/>Trust: Ultimate]
    end
    
    subgraph "Maintainers"
        M1[Maintainer A<br/>Trust: Full]
        M2[Maintainer B<br/>Trust: Full]
        M3[Maintainer C<br/>Trust: Full]
    end
    
    subgraph "Contributors"
        C1[Contributor X<br/>Trust: Marginal]
        C2[Contributor Y<br/>Trust: Marginal]
        C3[Contributor Z<br/>Trust: Unknown]
    end
    
    CT1 -->|trusts| M1
    CT1 -->|trusts| M2
    CT2 -->|trusts| M2
    CT2 -->|trusts| M3
    
    M1 -->|trusts| C1
    M2 -->|trusts| C1
    M2 -->|trusts| C2
    M3 -->|trusts| C2
    
    C1 -.->|collaboration| C2
    C2 -.->|collaboration| C3
    
    style CT1 fill:#ccffcc
    style CT2 fill:#ccffcc
    style M1 fill:#e1f5e1
    style M2 fill:#e1f5e1
    style M3 fill:#e1f5e1
    style C1 fill:#fff4e1
    style C2 fill:#fff4e1
    style C3 fill:#f0f0f0
```

---

**Generated:** 2025-10-28  
**Format:** Mermaid diagrams for IP architecture visualization  
**License:** MIT
