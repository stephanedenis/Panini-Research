# Guide de l'Audit Manager

## Vue d'ensemble

L'**Audit Manager** fournit un système de journalisation immuable pour toutes les opérations du système CAS. Il garantit la traçabilité complète, la conformité réglementaire et les capacités d'analyse forensique.

## Caractéristiques principales

### 1. Journalisation Immuable
- Chaîne d'intégrité avec hachage cryptographique
- Logs append-only (aucune modification/suppression)
- Vérification de l'intégrité de la chaîne

### 2. Suivi des Événements
- 20+ types d'événements prédéfinis
- Métadonnées complètes pour chaque événement
- Support pour événements personnalisés

### 3. Rapports de Conformité
- Rapports périodiques automatiques
- Analyse des violations
- Métriques de sécurité

### 4. Requêtes Temporelles
- Recherche par date, acteur, objet
- Analyse de timeline
- Requêtes par plage de dates

---

## Architecture

### Structure de stockage

```
store/audit/
├── by_date/
│   ├── 2025-10-28.jsonl          # Logs quotidiens
│   ├── 2025-10-29.jsonl
│   └── ...
├── by_actor/
│   ├── alice@example.com.jsonl   # Index par acteur
│   ├── bob@example.com.jsonl
│   └── ...
├── by_object/
│   ├── pattern_001.jsonl         # Index par objet
│   ├── pattern_002.jsonl
│   └── ...
└── chains/
    ├── chain_2025-10-28.json     # Chaînes d'intégrité
    ├── chain_2025-10-29.json
    └── ...
```

### Types d'événements

#### Opérations sur objets
- `CREATE` - Création d'objet
- `READ` - Lecture d'objet
- `UPDATE` - Modification d'objet
- `DELETE` - Suppression d'objet

#### Opérations de dérivation
- `DERIVE` - Dérivation d'objet
- `FORK` - Fork d'objet
- `MERGE` - Fusion d'objets

#### Opérations IP
- `LICENSE_APPLY` - Application de licence
- `LICENSE_CHANGE` - Changement de licence
- `ATTRIBUTION_ADD` - Ajout d'attribution
- `ATTRIBUTION_UPDATE` - Mise à jour d'attribution

#### Contrôle d'accès
- `ACCESS_GRANT` - Accordement d'accès
- `ACCESS_REVOKE` - Révocation d'accès
- `ACCESS_DENIED` - Accès refusé
- `ACCESS_ATTEMPT` - Tentative d'accès

#### Opérations système
- `EXPORT` - Export de données
- `IMPORT` - Import de données
- `BACKUP` - Sauvegarde
- `RESTORE` - Restauration

#### Gouvernance
- `VOTE_CAST` - Vote émis
- `REPUTATION_CHANGE` - Changement de réputation

---

## Utilisation

### Initialisation

```python
from audit_manager import AuditManager

audit = AuditManager("store")
```

### Journaliser un événement

```python
from audit_manager import AuditEventType, AuditOutcome, AuditSeverity

# Événement simple
event = audit.log_event(
    AuditEventType.CREATE,
    actor="alice@example.com",
    action="Created new phonological pattern",
    object_hash="pattern_001",
    object_type="pattern"
)

# Événement avec détails
event = audit.log_event(
    AuditEventType.ACCESS_DENIED,
    actor="bob@example.com",
    action="Attempted to delete pattern",
    object_hash="pattern_001",
    object_type="pattern",
    outcome=AuditOutcome.DENIED,
    severity=AuditSeverity.WARNING,
    details={
        'reason': 'insufficient permissions',
        'required_permission': 'DELETE'
    },
    metadata={
        'ip_address': '192.168.1.100',
        'user_agent': 'CAS Client v1.0'
    }
)
```

### Requêtes

#### Par date

```python
from datetime import datetime

today = datetime.utcnow().strftime("%Y-%m-%d")
events = audit.get_events_by_date(today)

print(f"Today's events: {len(events)}")
for event in events:
    print(f"  - {event.action} by {event.actor}")
```

#### Par acteur

```python
# Tous les événements d'un acteur
events = audit.get_events_by_actor("alice@example.com")

# Limiter le nombre de résultats
recent_events = audit.get_events_by_actor("alice@example.com", limit=10)
```

#### Par objet

```python
# Historique complet d'un objet
events = audit.get_events_by_object("pattern_001")

print(f"Object timeline ({len(events)} events):")
for event in events:
    print(f"  {event.timestamp}: {event.event_type.value} by {event.actor}")
```

#### Par plage de dates

```python
# Tous les événements
events = audit.get_events_in_range("2025-10-01", "2025-10-31")

# Filtrer par type
create_events = audit.get_events_in_range(
    "2025-10-01", 
    "2025-10-31",
    AuditEventType.CREATE
)
```

### Vérification d'intégrité

```python
# Vérifier la chaîne actuelle
chain_id = audit.current_chain.chain_id
valid = audit.verify_chain(chain_id)

if valid:
    print(f"✓ Chain {chain_id} is valid")
else:
    print(f"✗ Chain {chain_id} is COMPROMISED!")
```

### Rapports de conformité

```python
# Générer rapport mensuel
report = audit.generate_compliance_report(
    "2025-10-01",
    "2025-10-31"
)

print(f"Compliance Report {report.report_id}")
print(f"  Total events: {report.total_events}")
print(f"  Security events: {report.security_events}")
print(f"  Failures: {report.failures}")
print(f"  Violations: {len(report.violations)}")

# Analyser par type
for event_type, count in report.events_by_type.items():
    print(f"  {event_type}: {count}")

# Analyser par acteur
for actor, count in report.events_by_actor.items():
    print(f"  {actor}: {count} actions")

# Violations détaillées
for violation in report.violations:
    print(f"  - {violation['timestamp']}: {violation['action']}")
    print(f"    Actor: {violation['actor']}")
    print(f"    Outcome: {violation['outcome']}")
```

---

## Cas d'usage

### 1. Audit de sécurité

```python
# Traquer les tentatives d'accès non autorisées
audit.log_event(
    AuditEventType.ACCESS_DENIED,
    actor="suspicious@external.com",
    action="Attempted to access restricted pattern",
    object_hash="pattern_classified",
    outcome=AuditOutcome.DENIED,
    severity=AuditSeverity.SECURITY,
    details={
        'attempts': 5,
        'blocked_reason': 'external domain'
    },
    metadata={
        'ip_address': '10.0.0.1',
        'geolocation': 'Unknown'
    }
)

# Générer rapport de sécurité
report = audit.generate_compliance_report("2025-10-01", "2025-10-31")
if report.security_events > 0:
    print(f"⚠️  {report.security_events} security events detected!")
```

### 2. Analyse forensique

```python
# Investiguer un incident
object_hash = "pattern_suspect"
events = audit.get_events_by_object(object_hash)

print(f"Forensic timeline for {object_hash}:")
for event in events:
    print(f"{event.timestamp} - {event.event_type.value}")
    print(f"  Actor: {event.actor}")
    print(f"  Outcome: {event.outcome.value}")
    if event.details:
        print(f"  Details: {event.details}")
```

### 3. Conformité RGPD

```python
# Export des données d'un utilisateur
user_email = "alice@example.com"
events = audit.get_events_by_actor(user_email)

# Préparer export RGPD
export_data = {
    'user': user_email,
    'total_actions': len(events),
    'actions': [
        {
            'timestamp': e.timestamp,
            'action': e.action,
            'object': e.object_hash
        }
        for e in events
    ]
}

# Journaliser l'export
audit.log_event(
    AuditEventType.EXPORT,
    actor="system",
    action=f"GDPR data export for {user_email}",
    details={'record_count': len(events)}
)
```

### 4. Monitoring en temps réel

```python
from datetime import datetime, timedelta

# Détecter activité suspecte (trop de requêtes)
def check_rate_limiting(actor, threshold=100):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    events = audit.get_events_by_actor(actor)
    
    # Compter événements aujourd'hui
    today_events = [e for e in events if e.timestamp.startswith(today)]
    
    if len(today_events) > threshold:
        audit.log_event(
            AuditEventType.ACCESS_ATTEMPT,
            actor=actor,
            action=f"Rate limit exceeded ({len(today_events)} requests)",
            outcome=AuditOutcome.DENIED,
            severity=AuditSeverity.WARNING
        )
        return False
    return True
```

---

## Bonnes pratiques

### 1. Journaliser systématiquement

Journalisez **toutes** les opérations sensibles :
- Créations/modifications/suppressions
- Accès aux données
- Changements de permissions
- Opérations administratives

### 2. Fournir des détails riches

```python
# ❌ Mauvais - manque de contexte
audit.log_event(AuditEventType.UPDATE, actor="alice", action="update")

# ✅ Bon - contexte complet
audit.log_event(
    AuditEventType.UPDATE,
    actor="alice@example.com",
    action="Updated pattern phoneme inventory",
    object_hash="pattern_001",
    object_type="pattern",
    details={
        'changes': ['added /ʃ/', 'removed /θ/'],
        'reason': 'corpus analysis results'
    },
    metadata={
        'client': 'CAS Web UI',
        'session_id': 'sess_12345'
    }
)
```

### 3. Utiliser les niveaux de sévérité appropriés

- `DEBUG` - Informations de débogage
- `INFO` - Opérations normales
- `WARNING` - Événements inhabituels mais non critiques
- `ERROR` - Erreurs nécessitant attention
- `CRITICAL` - Erreurs critiques du système
- `SECURITY` - Événements de sécurité

### 4. Vérifier régulièrement l'intégrité

```python
# Vérification quotidienne automatique
from datetime import datetime, timedelta

def daily_integrity_check():
    # Vérifier les 7 derniers jours
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=i))
        chain_id = f"chain_{date.strftime('%Y-%m-%d')}"
        
        valid = audit.verify_chain(chain_id)
        if not valid:
            # Alerter administrateurs
            print(f"⚠️  INTEGRITY VIOLATION: {chain_id}")
```

### 5. Générer des rapports réguliers

```python
# Rapport hebdomadaire
def weekly_compliance_report():
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    
    report = audit.generate_compliance_report(
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    )
    
    # Sauvegarder rapport
    report_path = f"reports/compliance_{report.report_id}.json"
    with open(report_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    return report
```

---

## Intégration avec autres managers

### Avec ProvenanceManager

```python
from provenance_manager import ProvenanceManager
from audit_manager import AuditManager, AuditEventType

prov = ProvenanceManager("store")
audit = AuditManager("store")

# Créer objet et journaliser
origin = create_origin(SourceType.MANUAL_CREATION, "alice@example.com")
prov_chain = prov.create_provenance("obj001", "pattern", origin)

audit.log_event(
    AuditEventType.CREATE,
    actor="alice@example.com",
    action="Created pattern with provenance tracking",
    object_hash="obj001",
    object_type="pattern",
    details={'origin_type': origin.source_type.value}
)
```

### Avec LicenseManager

```python
from license_manager import LicenseManager

lic = LicenseManager("store")

# Appliquer licence et journaliser
obj_license = lic.apply_license("obj001", "MIT", applied_by="alice")

audit.log_event(
    AuditEventType.LICENSE_APPLY,
    actor="alice@example.com",
    action="Applied MIT license",
    object_hash="obj001",
    object_type="pattern",
    details={
        'license': 'MIT',
        'family': 'permissive'
    }
)
```

---

## Sécurité et conformité

### RGPD
- Droit à l'oubli : Export et suppression des données utilisateur
- Portabilité : Export des logs au format JSON
- Transparence : Accès complet à l'historique

### SOC 2
- Journalisation complète de tous les accès
- Intégrité cryptographique des logs
- Rapports de conformité automatisés

### ISO 27001
- Traçabilité des accès aux données sensibles
- Audit trail immuable
- Détection d'intrusion et monitoring

---

## Performance

### Optimisations

1. **Indexation multiple** : Recherche rapide par date/acteur/objet
2. **Logs journaliers** : JSONL pour append rapide
3. **Chaînes quotidiennes** : Vérification d'intégrité efficace

### Limites recommandées

- Événements par jour : ~100,000
- Rétention : 365 jours (configurable)
- Taille max par événement : 10 KB

---

## Statistiques

**Phase 5 : Audit Manager**
- Lignes de code : ~670
- Tests : 10/10 passing
- Types d'événements : 20+
- Niveaux de sévérité : 6
- Types de requêtes : 5

---

## Références

- **Architecture** : `audit_manager.py`
- **Tests** : `test_audit_manual.py`
- **Spécification** : Phase 5 du système IP

---

**Version** : 1.0  
**Date** : Octobre 2025  
**Statut** : ✅ Opérationnel
