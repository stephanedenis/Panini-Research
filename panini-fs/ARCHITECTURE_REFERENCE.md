# 🏗️ PaniniFS Architecture - Reference Permanente

> **⚠️ DOCUMENT DE RÉFÉRENCE CRITIQUE**  
> Ce fichier garantit que tout développement PaniniFS reste aligné avec l'architecture validée et documentée.

---

## 📍 Contexte de Ce Document

Ce document est créé le **12 novembre 2025** pour centraliser et rendre accessible en permanence les spécifications architecturales complètes de PaniniFS, notamment:

1. **Multi-Repos Git** avec hiérarchie de confidentialité (Privé/Teams/Public)
2. **Time-Travel** immutable inspiré btrfs/ZFS avec Copy-on-Write
3. **Content-Addressed Storage** (CAS) avec déduplication
4. **Synchronisation intelligente** inter-repos avec isolation stricte

**Pourquoi ce document?** Toutes ces spécifications existent déjà dans divers fichiers du projet, mais sont dispersées. Ce fichier les consolide pour garantir que **tout travail futur sur PaniniFS parte de ces bases validées**.

---

## 🎯 Architecture Validée & Implémentée

### ✅ Multi-Repos Git avec Hiérarchie de Confidentialité

**Status**: ✅ Implémenté et testé (voir `research/misc/docs/PANINI_GIT_MULTI_REPOS_ACHIEVEMENT.md`)

```
┌─────────────────────────────────────────────┐
│  🔒 PRIVÉ (Level 1)                         │
│  ├── panini-private-knowledge/              │
│  ├── Chiffrement: AES-256                   │
│  ├── Accès: Owner uniquement                │
│  └── Flux: Manual select → Teams            │
└─────────────────┬───────────────────────────┘
                  ↓ Filtrage sélectif
┌─────────────────────────────────────────────┐
│  👥 TEAMS (Level 2)                         │
│  ├── panini-team-a-knowledge/               │
│  ├── panini-team-b-knowledge/               │
│  ├── panini-teams-common/                   │
│  ├── Isolation: Team A ↮ Team B             │
│  └── Flux: ↔ Common, Auto → Public          │
└─────────────────┬───────────────────────────┘
                  ↓ Anonymisation automatique
┌─────────────────────────────────────────────┐
│  🌐 PUBLIC (Level 3)                        │
│  ├── panini-public-knowledge/               │
│  ├── Accès: Everyone                        │
│  └── Flux: ❌ AUCUN flux remontant          │
└─────────────────────────────────────────────┘
```

**Principes non-négociables**:
- `panini-data-models/` = seul repo avec contenu décomposé original (jamais dans knowledge repos)
- Team A ↮ Team B = isolation stricte hardcoded (zéro flux direct)
- Flux toujours descendant (Private → Teams → Public), jamais remontant
- Public → * = tous flux bloqués

### ✅ Time-Travel Immutable (Copy-on-Write)

**Status**: ✅ Implémenté en Rust (core complet)

**Inspiré de**: btrfs/ZFS snapshots + Git DAG

```rust
pub struct TemporalIndex {
    snapshots: BTreeMap<String, Snapshot>,      // Snapshots nommés
    timeline: BTreeMap<DateTime, VersionNode>,  // Timeline complète
    current_head: VersionId,
    dag: DirectedAcyclicGraph<VersionNode>,     // Historique complet
}

pub struct Snapshot {
    id: String,
    timestamp: DateTime<Utc>,
    semantic_tag: String,          // "stable_v1", "before_refactor"
    root_hash: ContentHash,        // Hash racine du snapshot
    metadata: HashMap<String, Value>,
}
```

**Fonctionnalités opérationnelles**:
- ✅ Snapshots avec tags sémantiques
- ✅ DAG de versions (comme Git mais pour tout le filesystem)
- ✅ Queries temporelles via API REST: `GET /api/time-travel?timestamp=...`
- ✅ Restauration instantanée (changement de pointeur, pas de copie physique)
- ✅ Déduplication automatique (même hash = 1 seule copie)

**API disponible** (voir `docs/rapports/QUICKSTART_PANINI_FS.md`):

```bash
# Créer snapshot
curl -X POST http://localhost:3000/api/snapshots \
  -H "Content-Type: application/json" \
  -d '{"name": "stable_v1", "tag": "production", "metadata": {}}'

# Lister snapshots
curl http://localhost:3000/api/snapshots

# Query temporel
curl "http://localhost:3000/api/time-travel?timestamp=2025-11-01T10:00:00Z"

# Restaurer snapshot
curl -X POST http://localhost:3000/api/snapshots/stable_v1/restore
```

### ✅ Content-Addressed Storage (CAS)

**Status**: ✅ Opérationnel avec déduplication validée (25-65% économies)

**Principe**: Contenu → SHA-256 → Hash unique → Stockage physique

```
panini-data-models/
└── .panini/
    ├── cas/
    │   └── atoms/
    │       ├── ab/cd/abcdef123456...     # Fichier unique 1
    │       ├── 12/34/123456789abc...     # Fichier unique 2
    │       └── ab/cd/abcdef123456...     # ← Même hash = 1 seule copie!
    ├── temporal/
    │   ├── snapshots.json               # Index des snapshots
    │   └── dag_index.json               # DAG des versions
    └── refs/
        └── content_refs.json            # Compteurs de références
```

**Algorithme**:

1. Fichier → Décomposition sémantique → Atoms
2. Atom → SHA-256(content) → Hash
3. Hash existe dans CAS? → Incrémenter `ref_count`
4. Hash nouveau? → Sauvegarder dans `cas/atoms/{ab}/{cd}/{hash}`
5. Économies typiques: 25-65% pour corpus Dhātu

**Garbage Collection**: Quand `ref_count == 0`, atom devient candidat à suppression

### ✅ Synchronisation Intelligente

**Status**: ✅ Sync orchestrator implémenté (Python, 900+ lignes)

**Workflow complet**:

```
┌─────────────────────┐
│ VFS (Virtual FS)    │  ← Lecture runtime par applications
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ panini-data-models/ │  ← Privé, chiffré, source de vérité
└──────────┬──────────┘
           ↓ Décomposeur sémantique
┌─────────────────────┐
│ [Atoms + Relations  │
│  + Context]         │
└──────────┬──────────┘
           ↓ Sync orchestrator
     ┌─────┴──────┬──────────┬────────┐
     ↓            ↓          ↓        ↓
┌─────────┐  ┌────────┐ ┌────────┐ ┌────────┐
│ Private │  │ Team A │ │ Team B │ │ Common │
└────┬────┘  └───┬────┘ └───┬────┘ └───┬────┘
     │           │          │          │
     └───────────┴──────────┴──────────┘
                     ↓ Anonymisation auto
              ┌─────────────┐
              │   Public    │
              └─────────────┘
```

**Matrice de flux** (voir `research/misc/scripts/panini_git_repo_architecture.py`):

| Source | → Private | → Team A | → Team B | → Common | → Public |
|--------|-----------|----------|----------|----------|----------|
| **Private** | ✓ (local) | ✓ manual | ✓ manual | ✓ manual | ✓ manual |
| **Team A** | ❌ | ✓ | ❌ **BLOCKED** | ✓ auto | ✓ auto |
| **Team B** | ❌ | ❌ **BLOCKED** | ✓ | ✓ auto | ✓ auto |
| **Common** | ❌ | ✓ read | ✓ read | ✓ | ✓ auto |
| **Public** | ❌ | ❌ | ❌ | ❌ | ✓ |

**Filtres de synchronisation**:
- Private → Teams: Sélection manuelle + filtres pertinence
- Teams → Common: Auto bidirectionnel (zone partagée)
- Common/Teams → Public: Anonymisation automatique (suppression métadonnées personnelles)
- Public → *: **Tous flux bloqués** (aucune remontée possible)

---

## 📚 Documents Source de Vérité

### Implémentations Complètes & Validées

| Document | Taille | Status | Contenu |
|----------|--------|--------|---------|
| **`research/misc/docs/PANINI_GIT_MULTI_REPOS_ACHIEVEMENT.md`** | ~800 lignes | ✅ Testé | Preuve implémentation 4 repos, tests sync, démonstration isolation |
| **`research/misc/scripts/panini_hierarchical_architecture.py`** | 527 lignes | ✅ Fonctionnel | Architecture hiérarchique complète, classes `ConfidentialityZone`, `HierarchicalRule` |
| **`research/misc/scripts/panini_git_repo_architecture.py`** | 900+ lignes | ✅ Fonctionnel | Design repos, sync orchestrator, matrice partage, access controls |
| **`docs/rapports/QUICKSTART_PANINI_FS.md`** | ~600 lignes | ✅ À jour | Guide utilisateur API time-travel, web UI, exemples CLI/REST |
| **`copilotage/knowledge/ESSENCE_PANINIFS.md`** | ~400 lignes | ✅ Nov 2025 | Vision globale, architecture modulaire, cloud resources |
| **`docs/architecture/PANINIFS_MULTI_REPOS_TIME_TRAVEL_SPEC.md`** | 600+ lignes | ✅ Nov 2025 | Spécifications exhaustives consolidées, code Rust TemporalIndex |
| **`docs/architecture/PANINIFS_SPEC_SUMMARY.md`** | ~500 lignes | ✅ Nov 2025 | Résumé exécutif 3 points, tableaux comparatifs, roadmap |

### Scripts Exécutables

```bash
# Créer architecture hiérarchique complète (5 zones)
python3 research/misc/scripts/panini_hierarchical_architecture.py

# Créer repos Git avec sync orchestrator
python3 research/misc/scripts/panini_git_repo_architecture.py

# Lancer serveur PaniniFS avec API REST
cd research/panini-fs/rust-core/
cargo run --release
# → http://localhost:3000 (API)
# → http://localhost:5173 (Web UI)
```

---

## ✅ État d'Implémentation (12 Nov 2025)

| Composant | Statut | Localisation | Notes |
|-----------|--------|--------------|-------|
| **Multi-Repos Git** | ✅ Fonctionnel | `research/misc/scripts/` | 4 repos testés avec sync |
| **Hierarchical Sync** | ✅ Implémenté | `panini_hierarchical_architecture.py` | 5 zones de confidentialité |
| **Time-Travel (Rust)** | ✅ Core complet | `research/panini-fs/rust-core/` | TemporalIndex opérationnel |
| **CAS Déduplication** | ✅ Opérationnel | `research/panini-fs/` | 25-65% économies validées |
| **API REST** | ✅ 10 endpoints | Port 3000 (Axum/Tokio) | CRUD snapshots + time-travel |
| **Web UI** | ✅ React/TypeScript | Port 5173 | Queries temporelles interactives |
| **Snapshots Sémantiques** | ✅ Avec tags | CLI + API | Tags custom + métadonnées |
| **Décomposeur Sémantique** | 🔄 En cours | `prototypes/decomposers/` | Python prototype complet |
| **FUSE Filesystem** | 🔄 En cours | `research/panini-fs/fuse/` | Montage virtuel Linux |
| **Chiffrement Repos** | ⏳ Planifié | - | AES-256 pour repos privés |
| **Remote Sync** | ⏳ Planifié | - | GitHub/GitLab integration |

**Légende**: ✅ Complet | 🔄 En développement actif | ⏳ Planifié mais pas démarré

---

## 🎯 Cas d'Usage Référence

### Workflow Typique: Développement Personnel → Publication

```bash
# 1. Travail dans repo privé avec time-travel
cd ~/panini/repos/panini-private-knowledge/
vim dhatu_aspectual_phase3.json

# 2. Créer snapshot sémantique avant partage
panini-fs snapshot create "stable_before_team_share" \
  --tag "production" \
  --metadata '{"version": "3.1", "context": "dhatu_aspectual"}'

# 3. Partager sélectivement vers team-a
panini-fs share select \
  --from private \
  --to team-a \
  --filter concepts="aspectual_evolution,dhatu_phase3" \
  --approve \
  --audit-log

# 4. Team A collabore (complètement isolé de Team B)
cd ~/panini/repos/panini-team-a-knowledge/
# Améliorations collaboratives...

# 5. Synchronisation automatique
# → Common: partage automatique vers zone inter-équipes
# → Public: anonymisation + publication automatique

# 6. Si problème détecté → rollback instantané
panini-fs snapshot restore "stable_before_team_share"
# (Restauration = changement de pointeur DAG, pas de copie physique!)
```

### Debugging avec Time-Travel

```bash
# Créer checkpoint avant refactoring risqué
panini-fs snapshot create "before_major_refactor" --tag "checkpoint"

# Effectuer modifications risquées
# ... modifications ...

# Comparer avec version stable
panini-fs diff \
  --snapshot "before_major_refactor" \
  --current \
  --format semantic_atoms

# Si erreur critique → restauration instantanée
panini-fs snapshot restore "before_major_refactor"

# Analyser ce qui a changé
panini-fs log --since "before_major_refactor" --format detailed
```

---

## 🔒 Garanties de Sécurité

### 1. Isolation Hiérarchique Stricte

**Hardcoded dans `panini_hierarchical_architecture.py`**:

```python
BLOCKED_FLOWS = [
    ("team_a_confidential", "team_b_confidential"),  # Team A → Team B: BLOQUÉ
    ("team_b_confidential", "team_a_confidential"),  # Team B → Team A: BLOQUÉ
    ("public_anonymized", "private_exclusive"),       # Public → Private: BLOQUÉ
    ("public_anonymized", "team_*"),                  # Public → Teams: BLOQUÉ
    ("teams_common_area", "private_exclusive"),       # Common → Private: BLOQUÉ
]
```

**Validation**: Tests automatisés vérifient qu'aucun flux bloqué ne peut se produire, même accidentellement.

### 2. Audit Trail Immutable

```rust
pub struct AuditEntry {
    timestamp: DateTime<Utc>,
    action: AuditAction,          // Read, Write, Share, Sync
    actor: UserId,
    source_repo: RepoId,
    target_repo: Option<RepoId>,
    affected_atoms: Vec<ContentHash>,
    signature: CryptoSignature,   // Chaîne cryptographique
}
```

**Garanties**:
- ✅ Toute action tracée dans timeline immutable (COW)
- ✅ Impossible de modifier historique rétroactivement
- ✅ Signature cryptographique chaînée (détection altération)
- ✅ Queries d'audit: "Qui a accédé à quoi quand?"

### 3. Chiffrement (En Cours)

**Planifié pour repos privés**:
- Algorithm: AES-256-GCM
- Key management: Per-repo keys
- Transparent encryption/decryption via FUSE

---

## 💡 Principes Architecturaux Non-Négociables

### 1. Immutabilité (Copy-on-Write)

**Inspiré btrfs/ZFS**:
- ❌ **Jamais** de modification en place
- ✅ Nouvelle version = nouveau nœud dans DAG
- ✅ Ancien état **toujours** accessible
- ✅ Rollback instantané (changement de pointeur)

**Bénéfices**:
- Time-travel gratuit (pas de copie physique)
- Snapshots sans overhead
- Historique complet garanti

### 2. Content-Addressed (CAS)

**Déduplication automatique**:
- Hash SHA-256 = identité unique du contenu
- Même contenu = 1 seule copie physique
- Ref-counting pour garbage collection
- Économies 25-65% validées sur corpus Dhātu

**Bénéfices**:
- Espace disque optimisé
- Intégrité garantie (hash vérifié)
- Partage sécurisé (content-hash = identité)

### 3. Hiérarchie Stricte (Flux Unidirectionnel)

**Toujours descendant** (jamais remontant):
- Private → Teams: Manual + filters
- Teams → Common: Auto bidirectionnel
- Common → Public: Auto + anonymisation
- Public → *: ❌ **Tous flux bloqués**
- Team A ↮ Team B: ❌ **Isolation totale**

**Bénéfices**:
- Confidentialité garantie par design
- Pas de fuite accidentelle vers niveau supérieur
- Isolation équipes hardcoded

### 4. Séparation Contenu/Knowledge

**Règle d'or**:
- `panini-data-models/`: **Seul** repo avec contenu original décomposé
- Autres repos: Knowledge graphs (atoms + relations) **uniquement**
- Reconstruction bit-perfect possible depuis n'importe quel repo via recipes
- Contenu original **jamais** dupliqué dans knowledge repos

**Bénéfices**:
- Source de vérité unique
- Pas de désynchronisation contenu
- Reconstruction garantie

---

## 🔧 Commandes Essentielles

### Snapshots

```bash
# Créer
panini-fs snapshot create <name> --tag <tag> --metadata '{...}'

# Lister
panini-fs snapshot list --format table

# Restaurer
panini-fs snapshot restore <name>

# Comparer
panini-fs snapshot diff <name1> <name2>

# Supprimer (avec confirmation)
panini-fs snapshot delete <name> --force
```

### Time-Travel

```bash
# Query à timestamp précis
panini-fs time-travel query --timestamp "2025-11-01T10:00:00Z"

# Query relative
panini-fs time-travel query --relative "-1h"  # Il y a 1 heure
panini-fs time-travel query --relative "-3d"  # Il y a 3 jours

# Liste changements période
panini-fs time-travel log --since "2025-11-01" --until "2025-11-10"
```

### Synchronisation

```bash
# Partager sélection vers autre repo
panini-fs share select \
  --from <source_repo> \
  --to <target_repo> \
  --filter concepts="concept1,concept2" \
  --approve

# Synchroniser tout (selon règles de flux)
panini-fs sync all

# Status synchronisation
panini-fs sync status --verbose
```

### API REST

```bash
# Créer snapshot
curl -X POST http://localhost:3000/api/snapshots \
  -H "Content-Type: application/json" \
  -d '{"name": "my_snapshot", "tag": "stable"}'

# Time-travel query
curl "http://localhost:3000/api/time-travel?timestamp=2025-11-01T10:00:00Z"

# Lister repos
curl http://localhost:3000/api/repos

# Status système
curl http://localhost:3000/api/status
```

---

## 🚀 Roadmap

### ✅ Déjà Implémenté (Nov 2025)

- [x] Multi-repos Git (4 repos fonctionnels)
- [x] Hiérarchie de confidentialité (5 zones)
- [x] Time-travel Rust (TemporalIndex complet)
- [x] CAS avec déduplication (25-65% savings)
- [x] API REST (10 endpoints Axum/Tokio)
- [x] Web UI React/TypeScript
- [x] Snapshots sémantiques avec tags
- [x] Sync orchestrator Python (900+ lignes)

### 🔄 En Cours (Cette Semaine)

- [ ] FUSE filesystem (montage virtuel `/panini/`)
- [ ] Intégration décomposeur sémantique complet
- [ ] Tests end-to-end multi-repos
- [ ] Documentation API complète

### ⏳ Court Terme (Ce Mois)

- [ ] Chiffrement AES-256 repos privés
- [ ] Remote sync GitHub/GitLab
- [ ] CI/CD workflows validation
- [ ] Monitoring & metrics

### 🎯 Moyen Terme (Q1 2026)

- [ ] Décomposeur Rust production
- [ ] FUSE avec time-travel intégré
- [ ] Interface web avancée (visualisation DAG)
- [ ] Support multi-utilisateurs

---

## 📖 Liens Rapides

### Documentation Principale

- **Architecture complète**: `../../docs/architecture/PANINIFS_MULTI_REPOS_TIME_TRAVEL_SPEC.md`
- **Résumé exécutif**: `../../docs/architecture/PANINIFS_SPEC_SUMMARY.md`
- **Guide utilisateur**: `../../docs/rapports/QUICKSTART_PANINI_FS.md`
- **Vision globale**: `../../copilotage/knowledge/ESSENCE_PANINIFS.md`

### Implémentations

- **Multi-repos achievement**: `../misc/docs/PANINI_GIT_MULTI_REPOS_ACHIEVEMENT.md`
- **Architecture hiérarchique**: `../misc/scripts/panini_hierarchical_architecture.py`
- **Repo architecture**: `../misc/scripts/panini_git_repo_architecture.py`

### Demos & Tests

```bash
# Demo multi-repos sync
python3 research/misc/scripts/demo_multi_repos.py

# Demo time-travel
cd research/panini-fs/rust-core/
cargo run --example time_travel_demo

# Demo CAS déduplication
python3 research/misc/scripts/demo_cas_savings.py
```

---

## ⚠️ IMPORTANT

**Ce document est la référence permanente pour PaniniFS**.

Toute recherche, développement, ou modification de PaniniFS **doit partir de ces spécifications validées**.

Si vous découvrez une incohérence entre ce document et une implémentation, **signaler immédiatement** pour mise à jour.

---

**📅 Créé**: 12 novembre 2025  
**📝 Dernière mise à jour**: 12 novembre 2025  
**👤 Auteur**: Consolidation specs existantes validées  
**🔒 Statut**: Reference permanente (ne pas supprimer)
