# Panini Research Repository

**Organized**: October 28, 2025  
**Purpose**: Research initiatives for the Panini ecosystem

---

## 📚 Active Research Projects

### 1. 🔷 Panini-FS (Universal Format Digester)

**Location**: `panini-fs/`  
**Status**: Specifications complete, ready for Rust/TypeScript product implementation  
**Description**: Universal format digester with grammar-based decomposition and reconstruction

**⚠️ ARCHITECTURE DOCUMENTED**: Multi-repos Git (Public/Privé/Teams) avec time-travel immutable (Copy-on-Write) inspiré btrfs/ZFS  
**📚 Voir**: [`panini-fs/ARCHITECTURE_REFERENCE.md`](panini-fs/ARCHITECTURE_REFERENCE.md) - **RÉFÉRENCE PERMANENTE**

**Key Features**:
- 69+ format extractors (PNG, JPEG, MP3, PDF, ZIP, etc.)
- Grammar-based decomposition
- Content-addressed storage integration
- Lossless reconstruction capabilities
- Compression benchmarking
- **Multi-repos Git avec hiérarchie de confidentialité (Privé/Teams/Public)**
- **Time-travel & snapshots sémantiques (Rust TemporalIndex)**
- **Déduplication CAS (25-65% économies validées)**
- **Synchronisation hiérarchique intelligente**

**Structure**:
```
panini-fs/
├── ARCHITECTURE_REFERENCE.md  # ← RÉFÉRENCE PERMANENTE (ne pas supprimer!)
├── README_ARCHITECTURE.md     # ← Liens rapides vers toutes les specs
├── specs/              # Complete specifications for product
│   └── spec-kit/       # GitHub Spec-Kit templates
├── prototypes/         # Python research prototypes
│   ├── extractors/     # 69 format extractors
│   ├── grammars/       # Grammar analyzers
│   ├── decomposers/    # Binary decomposers
│   ├── reconstructors/ # Format reconstructors
│   └── validators/     # Validation tools
├── benchmarks/         # Performance results
├── docs/               # Documentation
└── tests/              # Test suites
```

**Architecture Validée** (Nov 2025):
- ✅ Multi-repos Git: 4 repos testés et synchronisés
- ✅ Time-travel Rust: TemporalIndex complet opérationnel
- ✅ CAS déduplication: 25-65% économies validées
- ✅ API REST: 10 endpoints (http://localhost:3000)
- ✅ Web UI: React/TypeScript (http://localhost:5173)
- 🔄 FUSE filesystem: En cours
- ⏳ Chiffrement AES-256: Planifié

**Documents Source de Vérité**:
- `research/misc/docs/PANINI_GIT_MULTI_REPOS_ACHIEVEMENT.md` (preuve implémentation)
- `research/misc/scripts/panini_hierarchical_architecture.py` (527 lignes)
- `research/misc/scripts/panini_git_repo_architecture.py` (900+ lignes)
- `docs/architecture/PANINIFS_MULTI_REPOS_TIME_TRAVEL_SPEC.md` (600+ lignes)
- `docs/architecture/PANINIFS_SPEC_SUMMARY.md` (résumé exécutif)

**Next Steps**: Generate Rust + TypeScript product using GitHub agents

---

### 2. ⚙️ Universal Engine (IP Management System)

**Location**: `universal-engine/`  
**Status**: ✅ 100% Complete (8/8 phases, 73/73 tests passing)  
**Description**: Complete intellectual property management for content-addressed storage

**Components**:
1. Provenance Manager - Derivation tracking
2. License Manager - License compatibility
3. Attribution Manager - Creator tracking
4. Access Control Manager - Permission management
5. Audit Manager - Activity logging
6. Signature Manager - Digital signatures
7. Reputation Manager - Governance & reputation
8. IP Manager - Unified orchestrator

**Status**: Production-ready, ~15,950 lines of code

See: [`universal-engine/README.md`](universal-engine/README.md)

---

### 3. 🧬 Semantic Primitives (Dhātu Research)

**Location**: `semantic-primitives/`  
**Status**: Active research  
**Description**: Universal semantic atoms for cross-linguistic representation

**Key Findings** (September 2025):
- 9 optimal dhātu primitives identified
- 71.7% semantic coverage achieved
- Cross-linguistic validation
- Conceptual composability analysis

**Structure**:
```
semantic-primitives/
├── discoveries/        # Research findings
├── analysis-scripts/   # Analysis tools
├── results/            # Data and metrics
└── docs/               # Documentation
```

---

### 4. 🔗 Content-Addressed Architecture

**Location**: `content-addressed-architecture/`  
**Status**: Architecture defined  
**Description**: Double-hash CAS with derivation tracking

**Features**:
- SHA-256 content addressing
- Derivation chains
- Immutable storage
- Deduplication

**Integration**: Used by Universal Engine and Panini-FS

---

### 5. 🌐 Web Interfaces

**Location**: `web-interfaces/`  
**Status**: Multiple prototypes  
**Description**: Web dashboards and interactive interfaces for Panini ecosystem

**Contents**:
```
web-interfaces/
├── dashboards/     # HTML dashboards
├── servers/        # Backend servers (Python)
└── data/           # Dashboard data (JSON)
```

---

### 6. 📊 Ecosystem Analysis

**Location**: `ecosystem-analysis/`  
**Status**: Ongoing analysis  
**Description**: Tools and reports analyzing the Panini ecosystem

**Categories**:
- **Size Analysis**: Repository size metrics and trends
- **Architecture**: Internal structure analysis
- **Optimization**: Performance optimization discoveries
- **Reports**: Analysis results and findings

---

### 7. 🤖 Autonomous Agents

**Location**: `autonomous-agents/`  
**Status**: Research & experimentation  
**Description**: Multi-agent orchestration and collaboration

**Contents**:
- Orchestrators for ecosystem coordination
- Multi-agent collaboration guides
- GitHub Copilot agent integration

---

### 8. 📦 Spec-Kit Integration

**Location**: `spec-kit-integration/`  
**Status**: In development  
**Description**: GitHub Spec-Kit templates for agent-driven product development

**Purpose**: Enable GitHub agents to generate production code from research specifications

---

### 9. 📖 Philosophy & Theory

**Location**: `philosophy-theory/`  
**Status**: Documentation  
**Description**: Philosophical foundations and theoretical frameworks

**Topics**:
- Panini philosophy and principles
- Intellectual property architecture
- Conceptual integration

---

## 📂 Repository Organization

### Directories

| Directory | Purpose |
|-----------|---------|
| `panini-fs/` | Universal format digester research + **ARCHITECTURE_REFERENCE.md** (permanent!) |
| `universal-engine/` | IP management system (complete) |
| `semantic-primitives/` | Dhātu semantic atoms research |
| `content-addressed-architecture/` | CAS architecture |
| `web-interfaces/` | Web prototypes and dashboards |
| `ecosystem-analysis/` | Ecosystem analysis tools |
| `autonomous-agents/` | Multi-agent orchestration |
| `spec-kit-integration/` | Spec-Kit templates |
| `philosophy-theory/` | Philosophical foundations |
| `sessions/` | Research session logs |
| `archives/` | Historical artifacts |
| `shared/` | Shared utilities and test data |

### 🔒 Fichiers de Référence Permanents (NE PAS SUPPRIMER)

| Fichier | Description |
|---------|-------------|
| **`PANINIFS_ARCHITECTURE_REFERENCE.md`** | Vue consolidée architecture multi-repos + time-travel |
| **`panini-fs/ARCHITECTURE_REFERENCE.md`** | Référence technique complète PaniniFS |
| **`panini-fs/README_ARCHITECTURE.md`** | Guide rapide + liens vers toutes specs |

### Key Files

- `PLAN_REORGANISATION_RESEARCH.md` - This reorganization plan
- `.gitignore` - Git ignore patterns
- `README.md` - This file

---

## 🚀 Getting Started

### For Panini-FS Development

1. **Review specifications**: `panini-fs/specs/`
2. **Explore prototypes**: `panini-fs/prototypes/`
3. **Check benchmarks**: `panini-fs/benchmarks/`
4. **Generate product**: Use GitHub Spec-Kit with specs

### For Universal Engine Integration

1. **Read README**: `universal-engine/README.md`
2. **Review tests**: `universal-engine/tests/`
3. **Check docs**: `universal-engine/docs/`
4. **Run tests**: `cd universal-engine && python3 -m pytest tests/ -v`

### For Research Contributions

1. **Pick an initiative**: Choose from active projects above
2. **Review existing work**: Check relevant directory
3. **Document findings**: Add to appropriate docs/
4. **Run experiments**: Use analysis scripts

---

## 🔄 Workflow: Research → Product

```
Research (this repo)
    ↓
Complete Specifications (panini-fs/specs/)
    ↓
GitHub Spec-Kit Templates
    ↓
GitHub Copilot Agents
    ↓
Production Code (Rust + TypeScript)
    ↓
Product Repository (separate)
```

**Key Principle**: Research provides complete specs, agents implement products

---

## 📊 Statistics (October 28, 2025)

**Before Reorganization**:
- 366 files at root level (chaos)
- Mixed research initiatives
- Difficult navigation

**After Reorganization**:
- ~174 files at root (remaining misc files)
- 12 organized initiative directories
- Clear separation of concerns
- Easy to find and contribute

**Major Migrations**:
- 69 extractors → `panini-fs/prototypes/extractors/`
- Universal Engine → `universal-engine/` (renamed, documented)
- Sessions → `sessions/`
- Archives → `archives/`
- Web interfaces → `web-interfaces/`
- Analysis tools → `ecosystem-analysis/`

---

## 🎯 Immediate Next Steps

1. **Panini-FS Product**: Generate Rust + TypeScript implementation via GitHub agents
2. **Universal Engine**: Integration into Panini ecosystem
3. **Semantic Primitives**: Continue dhātu research and validation
4. **Spec-Kit**: Complete templates for all research projects

---

## 📝 License

Part of the Panini ecosystem. Individual projects may have specific licenses.

---

## 🤝 Contributing

See individual project directories for contribution guidelines and research protocols.

For questions or collaboration: Check session logs in `sessions/` for context and history.

---

**Last Updated**: October 28, 2025  
**Maintainer**: Panini Research Team
