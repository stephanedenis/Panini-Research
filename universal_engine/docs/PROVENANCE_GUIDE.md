# Provenance Manager - Guide d'Utilisation

## Vue d'Ensemble

Le **Provenance Manager** est le système de traçabilité du CAS (Content-Addressable Storage). Il enregistre l'origine, l'évolution et les contributions de chaque objet stocké, garantissant une transparence complète et une attribution appropriée.

## Architecture

### Composants Principaux

```
ProvenanceChain
├── Origin          # Origine de l'objet
├── Evolution       # Historique des événements
└── Contributors    # Contributeurs et crédits
```

### Storage Structure

```
store/
├── objects/{type}/{hash[:2]}/{hash}/
│   ├── content.json
│   ├── metadata.json
│   └── provenance.json  ← Chaîne de provenance
│
└── provenance/
    ├── by_creator/
    │   └── {creator_id}.json  # Index par créateur
    ├── by_origin/
    │   └── {source_type}.json  # Index par type d'origine
    └── timeline/
        └── {YYYY-MM-DD}.json  # Index chronologique
```

## Types de Données

### 1. SourceType (Type d'Origine)

```python
class SourceType(str, Enum):
    EMPIRICAL_ANALYSIS = "empirical_analysis"  # Extrait de corpus réels
    MANUAL_CREATION = "manual_creation"        # Créé manuellement
    DERIVED = "derived"                        # Dérivé d'autres objets
    IMPORTED = "imported"                      # Importé de source externe
    AI_GENERATED = "ai_generated"              # Généré par IA
    CONSENSUS = "consensus"                    # Approuvé par consensus
```

**Exemples:**
- `EMPIRICAL_ANALYSIS`: Pattern extrait de 70 extracteurs de format
- `MANUAL_CREATION`: Règle grammaticale écrite par un linguiste
- `DERIVED`: Variante créée à partir d'un pattern existant
- `IMPORTED`: Données importées de Wiktionnaire
- `AI_GENERATED`: Pattern suggéré par un modèle de ML
- `CONSENSUS`: Règle validée par vote communautaire

### 2. EventType (Type d'Événement)

```python
class EventType(str, Enum):
    CREATED = "created"          # Création initiale
    EXTRACTED = "extracted"      # Extraction de corpus
    REFINED = "refined"          # Raffinement/amélioration
    MERGED = "merged"            # Fusion avec autre objet
    FORKED = "forked"            # Dérivation/fork
    DEPRECATED = "deprecated"    # Déprécié
    CERTIFIED = "certified"      # Certifié/validé
    LICENSED = "licensed"        # Licence appliquée
    TRANSFERRED = "transferred"  # Transfert de propriété
```

### 3. AgentType (Type d'Agent)

```python
class AgentType(str, Enum):
    HUMAN = "human"                    # Humain
    AUTOMATED_SCRIPT = "automated_script"  # Script automatisé
    AI_ASSISTANT = "ai_assistant"      # Assistant IA
    CONSENSUS = "consensus"            # Décision de groupe
```

### 4. ContributorRole (Rôle de Contributeur)

```python
class ContributorRole(str, Enum):
    PRIMARY_AUTHOR = "primary_author"  # Auteur principal
    CO_AUTHOR = "co_author"            # Co-auteur
    MAINTAINER = "maintainer"          # Mainteneur
    CONTRIBUTOR = "contributor"        # Contributeur
    REVIEWER = "reviewer"              # Relecteur
    TESTER = "tester"                  # Testeur
    DOCUMENTER = "documenter"          # Documenteur
    TRANSLATOR = "translator"          # Traducteur
    SPONSOR = "sponsor"                # Sponsor/financeur
```

## API Reference

### ProvenanceManager

#### Création de Provenance

```python
from provenance_manager import ProvenanceManager, create_origin, create_event

manager = ProvenanceManager(store_root="/path/to/store")

# Créer une nouvelle chaîne de provenance
origin = create_origin(
    source_type="empirical_analysis",
    created_by="panini-research",
    dataset="70_format_extractors",
    confidence=0.95,
    validation_method="statistical_analysis"
)

chain = manager.create_provenance(
    object_hash="abc123",
    object_type="pattern",
    origin=origin
)
```

#### Enregistrement d'Événements

```python
# Enregistrer un événement de raffinement
event = create_event(
    event_type="refined",
    agent_identity="linguist-01",
    agent_type="human",
    description="Refined pattern based on corpus analysis",
    capabilities_added=["precision_improvement"]
)

manager.record_event("abc123", event)
```

#### Gestion des Contributeurs

```python
from provenance_manager import create_contributor

# Ajouter un contributeur
contributor = create_contributor(
    contributor_id="alice",
    role="primary_author",
    contributions=["initial_extraction", "refinement"],
    contribution_pct=40.0
)

manager.add_contributor("abc123", contributor)
```

#### Requêtes

```python
# Charger une provenance
chain = manager.load_provenance("abc123")

# Trouver par créateur
objects = manager.find_by_creator("panini-research")

# Trouver par type d'origine
objects = manager.find_by_origin("empirical_analysis")

# Vue chronologique
events = manager.timeline_view("2025-10-28")

# Historique complet
history = manager.get_full_history("abc123")
print(f"Created: {history['created_at']}")
print(f"Modified: {history['last_modified']}")
print(f"Events: {history['event_count']}")
```

#### Export/Import YAML

```python
# Export vers YAML
manager.export_to_yaml("abc123", "provenance.yml")

# Import depuis YAML
chain = manager.import_from_yaml("provenance.yml", "abc123")
```

## Exemples d'Usage

### Exemple 1: Pattern Extrait de Corpus

```python
from provenance_manager import ProvenanceManager, create_origin, create_event

manager = ProvenanceManager()

# 1. Créer la provenance initiale
origin = create_origin(
    source_type="empirical_analysis",
    created_by="pattern-extractor-v2",
    dataset="sanskrit_corpus_2024",
    analysis_hash="def456",
    confidence=0.92,
    validation_method="frequency_analysis",
    peer_reviewed=False
)

chain = manager.create_provenance(
    object_hash="pattern_001",
    object_type="pattern",
    origin=origin
)

# 2. Enregistrer l'extraction
event = create_event(
    event_type="extracted",
    agent_identity="pattern-extractor-v2",
    agent_type="automated_script",
    description="Extracted pattern from 1,200 occurrences",
    capabilities_added=["morphological_transformation"]
)
manager.record_event("pattern_001", event)

# 3. Ajouter le contributeur
contributor = create_contributor(
    contributor_id="extractor-team",
    role="primary_author",
    contributions=["automated_extraction"],
    contribution_pct=100.0
)
manager.add_contributor("pattern_001", contributor)
```

### Exemple 2: Raffinement Manuel

```python
# Charger la provenance existante
chain = manager.load_provenance("pattern_001")

# Enregistrer le raffinement
event = create_event(
    event_type="refined",
    agent_identity="linguist-marie",
    agent_type="human",
    description="Refined pattern edges, improved precision from 92% to 97%",
    capabilities_added=["edge_case_handling"]
)
manager.record_event("pattern_001", event)

# Ajouter le contributeur
contributor = create_contributor(
    contributor_id="linguist-marie",
    role="maintainer",
    contributions=["manual_refinement", "edge_case_analysis"],
    contribution_pct=25.0  # Ajouté à l'existant
)
manager.add_contributor("pattern_001", contributor)
```

### Exemple 3: Fork et Dérivation

```python
# Créer un fork pour une variante
fork_origin = create_origin(
    source_type="derived",
    created_by="linguist-john",
    parent_hashes=["pattern_001"],  # Parent original
    confidence=1.0
)

fork_chain = manager.create_provenance(
    object_hash="pattern_001_variant",
    object_type="pattern",
    origin=fork_origin
)

# Enregistrer le fork
event = create_event(
    event_type="forked",
    agent_identity="linguist-john",
    agent_type="human",
    description="Created variant for dialectal usage",
    capabilities_added=["dialectal_support"]
)
manager.record_event("pattern_001_variant", event)
```

### Exemple 4: Certification et Consensus

```python
# Enregistrer la certification
event = create_event(
    event_type="certified",
    agent_identity="peer-review-committee",
    agent_type="consensus",
    description="Peer-reviewed and certified by 5 experts",
    capabilities_added=["peer_reviewed_status"]
)
manager.record_event("pattern_001", event)

# Marquer comme peer-reviewed dans l'origine
chain = manager.load_provenance("pattern_001")
chain.origin.peer_reviewed = True
chain.origin.validation_method = "expert_consensus"
manager.save(chain)
```

## Bonnes Pratiques

### 1. Traçabilité Complète

**✓ FAIRE:**
- Enregistrer TOUS les événements significatifs
- Documenter les parents (`parent_hashes`) pour les dérivations
- Inclure les datasets sources dans l'origine
- Spécifier la méthode de validation

**✗ ÉVITER:**
- Créer des objets sans provenance
- Omettre les événements de modification
- Ignorer les contributeurs secondaires

### 2. Attribution Appropriée

**✓ FAIRE:**
- Distinguer les rôles (primary_author vs contributor)
- Calculer les pourcentages de contribution réalistes
- Lister toutes les contributions spécifiques
- Reconnaître les reviewers et testers

**✗ ÉVITER:**
- Attribution à 100% pour le dernier modifieur
- Oublier les contributeurs automatisés (scripts, IA)
- Rôles inappropriés (primary_author pour un fix mineur)

### 3. Confiance et Validation

**✓ FAIRE:**
- Définir un score de confiance (0.0-1.0) basé sur des critères objectifs
- Spécifier la méthode de validation
- Marquer `peer_reviewed=True` après validation experte
- Lier les analyses (`analysis_hash`) pour reproductibilité

**✗ ÉVITER:**
- Confiance à 1.0 sans validation
- Méthode de validation vague ("manual check")
- Peer-review non documenté

### 4. Évolution Documentée

**✓ FAIRE:**
- Un événement par modification significative
- Descriptions détaillées (`description` field)
- `capabilities_added` pour les nouvelles fonctionnalités
- Dates précises (ISO 8601)

**✗ ÉVITER:**
- Événements groupés ("multiple changes")
- Descriptions vagues ("updated")
- Oublier de marquer les dépréciations

## Intégration avec le CAS

### Au moment de la création d'un objet:

```python
from cas_core import CAS
from provenance_manager import ProvenanceManager, create_origin

cas = CAS()
prov = ProvenanceManager(store_root=cas.store_root)

# Créer l'objet
obj_hash = cas.store_object(
    object_type="pattern",
    content={"type": "nominal", "form": "..."}
)

# Créer la provenance
origin = create_origin(
    source_type="manual_creation",
    created_by="current-user"
)
prov.create_provenance(obj_hash, "pattern", origin)
```

### Au moment de la modification:

```python
from provenance_manager import create_event

# Charger et modifier l'objet
obj = cas.load_object(obj_hash)
obj["capabilities"].append("new_feature")
new_hash = cas.store_object("pattern", obj)

# Enregistrer l'événement
event = create_event(
    event_type="refined",
    agent_identity="current-user",
    description="Added new_feature capability"
)
prov.record_event(new_hash, event)
```

## Statistiques et Rapports

### Exemple: Rapport de Contributions

```python
# Charger toutes les provenances d'un créateur
objects = prov.find_by_creator("panini-research")

total_objects = len(objects)
by_type = {}

for obj_hash in objects:
    chain = prov.load_provenance(obj_hash)
    obj_type = chain.object_type
    by_type[obj_type] = by_type.get(obj_type, 0) + 1

print(f"Total objects: {total_objects}")
for obj_type, count in by_type.items():
    print(f"  {obj_type}: {count}")
```

### Exemple: Timeline d'Activité

```python
import datetime

# Activité des 30 derniers jours
today = datetime.date.today()
for i in range(30):
    date = (today - datetime.timedelta(days=i)).isoformat()
    events = prov.timeline_view(date)
    if events:
        print(f"{date}: {len(events)} events")
```

## Tests

Le système est livré avec une suite de tests complète:

```bash
# Tests manuels (sans pytest)
python3 test_provenance_manual.py

# Tests pytest (si disponible)
pytest test_provenance_manager.py -v
```

### Tests Couverts:

1. **Création de provenance basique**
2. **Enregistrement d'événements**
3. **Gestion des contributeurs**
4. **Requêtes (by_creator, by_origin, timeline)**
5. **Export/Import YAML**
6. **Historique complet**

## Prochaines Étapes

La Phase 1 (Provenance) est maintenant complète. Les phases suivantes ajouteront:

- **Phase 2**: License Manager - Gestion des licences et compatibilité
- **Phase 3**: Attribution Manager - Citations et crédits automatiques
- **Phase 4**: Access Control - Permissions et visibilité
- **Phase 5**: Audit Trail - Logs immuables et compliance
- **Phase 6**: Digital Signatures - Signatures cryptographiques
- **Phase 7**: Reputation & Governance - Système de réputation
- **Phase 8**: Integration - Orchestration complète du système IP

## Support

Pour toute question ou problème:
- Documentation: `/research/universal_engine/docs/`
- Tests: `test_provenance_manual.py`
- Code source: `provenance_manager.py` (650 lignes)

---

**Version**: 1.0.0  
**Date**: 2025-10-28  
**Auteurs**: Panini Research Team
