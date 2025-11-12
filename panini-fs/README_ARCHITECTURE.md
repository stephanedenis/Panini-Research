# PaniniFS - Quick Architecture Links

> **⚡ Document d'orientation rapide** pour toujours retrouver les specs PaniniFS

---

## 🎯 Question Rapide?

**As-t-on documenté l'architecture multi-repos (public/privé/restreint) avec time-travel comme btrfs?**

✅ **OUI! Tout est documenté, implémenté, et testé.**

---

## 📚 Documents de Référence Permanents

### Dans ce répertoire `panini-fs/`

- **[ARCHITECTURE_REFERENCE.md](./ARCHITECTURE_REFERENCE.md)** ← **CE FICHIER EST LA RÉFÉRENCE PERMANENTE**
  - Architecture complète multi-repos
  - Time-travel & Copy-on-Write
  - CAS déduplication
  - Synchronisation hiérarchique
  - État d'implémentation
  - Commandes essentielles
  - Roadmap

### Dans `research/`

- **[PANINIFS_ARCHITECTURE_REFERENCE.md](../PANINIFS_ARCHITECTURE_REFERENCE.md)**
  - Vue d'ensemble consolidée
  - Liens vers tous les documents source
  - Scripts exécutables
  - Cas d'usage détaillés

### Dans `docs/architecture/`

- **[PANINIFS_MULTI_REPOS_TIME_TRAVEL_SPEC.md](../../docs/architecture/PANINIFS_MULTI_REPOS_TIME_TRAVEL_SPEC.md)** (600+ lignes)
  - Spécifications exhaustives
  - Code Rust TemporalIndex complet
  - Matrice synchronisation
  - Tous détails techniques

- **[PANINIFS_SPEC_SUMMARY.md](../../docs/architecture/PANINIFS_SPEC_SUMMARY.md)**
  - Résumé exécutif court
  - Tableaux comparatifs vs btrfs/ZFS
  - 3 points clés architecture

---

## 🏗️ Architecture en 30 Secondes

### Multi-Repos Git Hiérarchiques

```
🔒 PRIVÉ → 👥 TEAMS → 🌐 PUBLIC
    ↓         ↓          ↓
  Owner    Équipes   Everyone
  Manual    Auto      Auto
  AES-256   Option    Public
```

**Isolation**: Team A ↮ Team B (bloqué hardcoded)

### Time-Travel Immutable

```rust
TemporalIndex {
  snapshots: Map<String, Snapshot>,  // Tags sémantiques
  timeline: Map<DateTime, Version>,   // Historique complet
  dag: DAG<VersionNode>,             // Comme Git
}
```

**Features**: Snapshots, rollback instantané, queries temporelles, déduplication CAS

### Content-Addressed Storage

```
Contenu → SHA-256 → Hash → /cas/atoms/{ab}/{cd}/{hash}
Même contenu = 1 seule copie physique
Économies: 25-65% validées
```

---

## ✅ Status Implémentation (Nov 2025)

| Composant | Status |
|-----------|--------|
| Multi-repos Git | ✅ Fonctionnel (4 repos testés) |
| Time-travel Rust | ✅ Core complet |
| CAS déduplication | ✅ Opérationnel |
| API REST | ✅ 10 endpoints |
| Web UI | ✅ React/TypeScript |
| Snapshots | ✅ Avec tags |
| FUSE | 🔄 En cours |
| Chiffrement | ⏳ Planifié |

---

## 🔧 Commandes Rapides

```bash
# Créer architecture complète
python3 research/misc/scripts/panini_hierarchical_architecture.py

# Lancer serveur PaniniFS
cd research/panini-fs/rust-core/
cargo run --release

# API time-travel
curl "http://localhost:3000/api/time-travel?timestamp=2025-11-01T10:00:00Z"

# Créer snapshot
panini-fs snapshot create "stable_v1" --tag "production"

# Restaurer
panini-fs snapshot restore "stable_v1"
```

---

## 📖 Implémentations Source

- **`research/misc/docs/PANINI_GIT_MULTI_REPOS_ACHIEVEMENT.md`** - Preuve 4 repos fonctionnels
- **`research/misc/scripts/panini_hierarchical_architecture.py`** (527 lignes) - Architecture hiérarchique
- **`research/misc/scripts/panini_git_repo_architecture.py`** (900+ lignes) - Sync orchestrator
- **`docs/rapports/QUICKSTART_PANINI_FS.md`** - Guide utilisateur API

---

**⚠️ IMPORTANT**: Ce fichier pointe vers les références permanentes. **Ne jamais supprimer ces documents!**

**📅 Créé**: 12 novembre 2025
