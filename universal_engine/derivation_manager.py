"""
Derivation Manager - Hypersémantique v4.0

Gère l'évolution déclarative des objets content-addressed.
Inspiré de Git (commits) + IPFS (Merkle DAGs) + Pāṇini (dérivation par affixes).

Concepts:
- Dérivations = transformations déclaratives immuables
- DAG sémantique = graphe d'évolution + similitude
- Reconstruction = replay déclaratif des transformations
- Provenance = chaîne complète origine → version actuelle
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .content_addressed_store import (
    ContentAddressedStore,
    compute_exact_hash,
    compute_similarity_hash,
    compute_entropy,
    compute_negentropy
)


class RelationType(Enum):
    """Types de relations entre objets"""
    EXTENDS = "extends"          # Extension (ajout de features)
    REFINES = "refines"          # Raffinement (amélioration)
    SPECIALIZES = "specializes"  # Spécialisation (contraintes)
    MERGES = "merges"            # Fusion de branches
    DERIVES = "derives"          # Dérivation générique
    EQUIVALENT = "equivalent"    # Équivalent sémantique


class OperationType(Enum):
    """Types d'opérations de transformation"""
    ADD_FIELD = "add_field"
    MODIFY_LOGIC = "modify_logic"
    CONSTRAIN_VALUE = "constrain_value"
    MERGE_SCHEMAS = "merge_schemas"
    REFACTOR_STRUCTURE = "refactor_structure"
    ADD_EXTRACTION = "add_extraction"
    REMOVE_FIELD = "remove_field"
    SPLIT_PATTERN = "split_pattern"
    COMPOSE_PATTERNS = "compose_patterns"


@dataclass
class ParentRef:
    """Référence à un parent dans le DAG"""
    hash: str
    relation: RelationType
    similarity: float = 1.0  # Similitude sémantique
    branch: Optional[str] = None


@dataclass
class SemanticFingerprint:
    """Empreinte sémantique d'un objet"""
    capabilities: List[str]  # Ce qu'il peut faire
    intent: List[str]        # Pourquoi il existe
    constraints: Dict[str, Any]  # Limites/garanties
    domain: Dict[str, List[str]]  # Domaine d'application
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SemanticFingerprint':
        return cls(**data)


@dataclass
class Derivation:
    """
    Dérivation déclarative d'un objet
    
    Représente une transformation immuable d'un ou plusieurs parents
    vers un nouvel objet, avec métadonnées sémantiques complètes.
    """
    object_hash: str
    object_type: str
    parents: List[ParentRef]
    transformation: Dict[str, Any]
    semantic: SemanticFingerprint
    entropy: float
    negentropy: float
    timestamp: str
    author: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Convert enums to strings
        data['parents'] = [
            {
                'hash': p.hash,
                'relation': p.relation.value,
                'similarity': p.similarity,
                'branch': p.branch
            }
            for p in self.parents
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Derivation':
        # Convert dicts to ParentRef
        parents = [
            ParentRef(
                hash=p['hash'],
                relation=RelationType(p['relation']),
                similarity=p.get('similarity', 1.0),
                branch=p.get('branch')
            )
            for p in data['parents']
        ]
        
        # Convert dict to SemanticFingerprint
        semantic = SemanticFingerprint.from_dict(data['semantic'])
        
        return cls(
            object_hash=data['object_hash'],
            object_type=data['object_type'],
            parents=parents,
            transformation=data['transformation'],
            semantic=semantic,
            entropy=data['entropy'],
            negentropy=data['negentropy'],
            timestamp=data['timestamp'],
            author=data.get('author')
        )


class SemanticDAG:
    """
    DAG sémantique pour navigation dans l'espace d'évolution
    
    Permet de naviguer non seulement par liens généalogiques
    (parents/enfants) mais aussi par similitude sémantique.
    """
    
    def __init__(self, store: ContentAddressedStore):
        self.store = store
        self._indexes = {
            'parents': {},   # child -> [parents]
            'children': {},  # parent -> [children]
            'semantic': {}   # capability -> [objects]
        }
        self._build_indexes()
    
    def _build_indexes(self):
        """Construit les indexes à partir des dérivations stockées"""
        # TODO: Scanner objects/derivation/ et construire indexes
        pass
    
    def ancestors(self, hash: str, max_depth: Optional[int] = None) -> List[str]:
        """Retourne tous les ancêtres (parents récursifs)"""
        visited = set()
        to_visit = [hash]
        ancestors = []
        depth = 0
        
        while to_visit and (max_depth is None or depth < max_depth):
            current = to_visit.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            
            # Charger la dérivation
            try:
                deriv = self._load_derivation(current)
                parents = [p.hash for p in deriv.parents]
                ancestors.extend(parents)
                to_visit.extend(parents)
            except FileNotFoundError:
                # Pas de dérivation = objet racine
                pass
            
            depth += 1
        
        return ancestors
    
    def descendants(self, hash: str, max_depth: Optional[int] = None) -> List[str]:
        """Retourne tous les descendants (enfants récursifs)"""
        # Utiliser l'index children
        if hash not in self._indexes['children']:
            return []
        
        visited = set()
        to_visit = [hash]
        descendants = []
        depth = 0
        
        while to_visit and (max_depth is None or depth < max_depth):
            current = to_visit.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            children = self._indexes['children'].get(current, [])
            descendants.extend(children)
            to_visit.extend(children)
            depth += 1
        
        return descendants
    
    def siblings(self, hash: str) -> List[str]:
        """Retourne les objets avec mêmes parents (branches parallèles)"""
        try:
            deriv = self._load_derivation(hash)
            siblings = []
            
            for parent in deriv.parents:
                # Trouver tous les enfants de ce parent
                children = self._indexes['children'].get(parent.hash, [])
                siblings.extend([c for c in children if c != hash])
            
            return list(set(siblings))  # Dédupliquer
        except FileNotFoundError:
            return []
    
    def common_ancestor(self, hash1: str, hash2: str) -> Optional[str]:
        """Trouve l'ancêtre commun le plus récent (comme git merge-base)"""
        ancestors1 = set(self.ancestors(hash1))
        ancestors2 = set(self.ancestors(hash2))
        
        common = ancestors1 & ancestors2
        if not common:
            return None
        
        # Trouver le plus récent (= le plus proche)
        # TODO: Utiliser timestamps pour trouver le plus récent
        return list(common)[0]
    
    def semantic_neighbors(self, 
                          hash: str, 
                          threshold: float = 0.8) -> List[Tuple[str, float]]:
        """
        Trouve les objets sémantiquement proches
        (pas forcément liés généalogiquement)
        """
        # Charger l'objet cible
        content, meta = self.store.load(hash, meta.object_type)
        target_sim_hash = meta.similarity_hash
        
        # Recherche par similitude
        similar = self.store.find_similar(
            target_sim_hash,
            meta.object_type,
            threshold=threshold
        )
        
        return similar
    
    def capability_search(self, capabilities: List[str]) -> List[str]:
        """Trouve les objets ayant certaines capacités"""
        results = []
        
        for cap in capabilities:
            if cap in self._indexes['semantic']:
                results.extend(self._indexes['semantic'][cap])
        
        return list(set(results))  # Dédupliquer
    
    def evolution_path(self, from_hash: str, to_hash: str) -> List[str]:
        """
        Trouve le chemin d'évolution de from_hash à to_hash
        
        Retourne la séquence de dérivations à appliquer.
        """
        # BFS pour trouver le chemin le plus court
        queue = [(from_hash, [from_hash])]
        visited = set()
        
        while queue:
            current, path = queue.pop(0)
            
            if current == to_hash:
                return path
            
            if current in visited:
                continue
            visited.add(current)
            
            # Ajouter les enfants
            children = self._indexes['children'].get(current, [])
            for child in children:
                queue.append((child, path + [child]))
        
        return []  # Pas de chemin trouvé
    
    def diff_semantic(self, hash1: str, hash2: str) -> Dict:
        """Calcule la différence sémantique entre deux objets"""
        deriv1 = self._load_derivation(hash1)
        deriv2 = self._load_derivation(hash2)
        
        sem1 = deriv1.semantic
        sem2 = deriv2.semantic
        
        return {
            'capabilities': {
                'added': list(set(sem2.capabilities) - set(sem1.capabilities)),
                'removed': list(set(sem1.capabilities) - set(sem2.capabilities)),
                'common': list(set(sem1.capabilities) & set(sem2.capabilities))
            },
            'intent': {
                'added': list(set(sem2.intent) - set(sem1.intent)),
                'removed': list(set(sem1.intent) - set(sem1.intent)),
                'common': list(set(sem1.intent) & set(sem2.intent))
            },
            'entropy_delta': deriv2.entropy - deriv1.entropy,
            'negentropy_delta': deriv2.negentropy - deriv1.negentropy
        }
    
    def _load_derivation(self, hash: str) -> Derivation:
        """Charge une dérivation depuis le store"""
        content, meta = self.store.load(hash, 'derivation')
        data = yaml.safe_load(content)
        return Derivation.from_dict(data)


class DerivationManager:
    """
    Gestionnaire de dérivations hypersémantiques
    
    Crée, applique et reconstruit des objets via dérivations déclaratives.
    """
    
    def __init__(self, store: ContentAddressedStore):
        self.store = store
        self.dag = SemanticDAG(store)
    
    def create_derivation(self,
                         parent_hashes: List[str],
                         parent_type: str,
                         transformation: Dict,
                         semantic: SemanticFingerprint,
                         author: Optional[str] = None) -> str:
        """
        Crée une nouvelle dérivation déclarative
        
        Args:
            parent_hashes: Liste des hashes des parents
            parent_type: Type des objets parents (pattern, grammar, etc.)
            transformation: Dict décrivant la transformation
            semantic: Empreinte sémantique du résultat
            author: Auteur de la dérivation (optionnel)
        
        Returns:
            Hash de l'objet dérivé
        """
        # 1. Charger les parents
        parents = []
        for parent_hash in parent_hashes:
            content, meta = self.store.load(parent_hash, parent_type)
            parents.append({
                'hash': parent_hash,
                'content': yaml.safe_load(content),
                'metadata': meta
            })
        
        # 2. Appliquer la transformation
        result = self._apply_transformation(parents, transformation)
        
        # 3. Calculer les hashes
        result_bytes = yaml.dump(result, sort_keys=True).encode('utf-8')
        exact_hash = compute_exact_hash(result_bytes)
        similarity_hash = compute_similarity_hash(result_bytes, result)
        
        # 4. Calculer entropie/négentropie
        entropy = compute_entropy(result_bytes)
        negentropy = compute_negentropy(result_bytes)
        
        # 5. Créer les références aux parents
        parent_refs = []
        for parent in parents:
            # Calculer similitude avec le parent
            parent_bytes = yaml.dump(parent['content'], 
                                    sort_keys=True).encode('utf-8')
            parent_sim = compute_similarity_hash(parent_bytes, parent['content'])
            
            similarity_score = self.store._similarity_score(
                similarity_hash, 
                parent_sim
            )
            
            parent_refs.append(ParentRef(
                hash=parent['hash'],
                relation=RelationType.EXTENDS,  # TODO: Déduire du transformation
                similarity=similarity_score
            ))
        
        # 6. Créer la dérivation
        derivation = Derivation(
            object_hash=exact_hash,
            object_type=parent_type,
            parents=parent_refs,
            transformation=transformation,
            semantic=semantic,
            entropy=entropy,
            negentropy=negentropy,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            author=author
        )
        
        # 7. Stocker la dérivation
        deriv_bytes = yaml.dump(derivation.to_dict(), 
                               sort_keys=True).encode('utf-8')
        deriv_hash = self.store.store(
            deriv_bytes,
            'derivation',
            metadata=derivation.to_dict()
        )[0]
        
        # 8. Stocker l'objet résultant
        self.store.store(
            result_bytes,
            parent_type,
            metadata={
                **result,
                'derivation': deriv_hash,
                'semantic': semantic.to_dict()
            }
        )
        
        return exact_hash
    
    def reconstruct(self, 
                   target_hash: str, 
                   object_type: str) -> Dict:
        """
        Reconstruit un objet en rejouant ses dérivations
        
        Args:
            target_hash: Hash de l'objet à reconstruire
            object_type: Type de l'objet
        
        Returns:
            Objet reconstruit (dict)
        """
        # Essayer chargement direct d'abord
        try:
            content, _ = self.store.load(target_hash, object_type)
            return yaml.safe_load(content)
        except FileNotFoundError:
            pass
        
        # Fallback: reconstruction par replay
        return self._reconstruct_by_replay(target_hash, object_type)
    
    def _reconstruct_by_replay(self, 
                               target_hash: str, 
                               object_type: str) -> Dict:
        """Reconstruit en rejouant les dérivations depuis la racine"""
        # Trouver la racine (objet sans parents)
        root = self._find_root(target_hash)
        
        # Trouver le chemin d'évolution
        path = self.dag.evolution_path(root, target_hash)
        
        if not path:
            raise ValueError(f"Cannot find evolution path to {target_hash}")
        
        # Charger la racine
        content, _ = self.store.load(root, object_type)
        current = yaml.safe_load(content)
        
        # Rejouer les dérivations
        for step_hash in path[1:]:  # Skip root
            deriv = self.dag._load_derivation(step_hash)
            current = self._apply_transformation(
                [{'content': current}],
                deriv.transformation
            )
        
        return current
    
    def _apply_transformation(self, 
                             parents: List[Dict], 
                             transformation: Dict) -> Dict:
        """
        Applique une transformation déclarative
        
        Args:
            parents: Liste des parents avec leur contenu
            transformation: Dict décrivant l'opération
        
        Returns:
            Objet transformé
        """
        op_type = transformation.get('operation')
        changes = transformation.get('changes', [])
        
        if not parents:
            raise ValueError("Need at least one parent")
        
        # Commencer avec le premier parent
        result = parents[0]['content'].copy()
        
        if op_type == 'add_field':
            result = self._op_add_field(result, changes)
        elif op_type == 'add_extraction':
            result = self._op_add_extraction(result, changes)
        elif op_type == 'merge':
            result = self._op_merge([p['content'] for p in parents], changes)
        elif op_type == 'modify_logic':
            result = self._op_modify_logic(result, changes)
        elif op_type == 'constrain_value':
            result = self._op_constrain_value(result, changes)
        else:
            raise ValueError(f"Unknown operation: {op_type}")
        
        return result
    
    def _op_add_field(self, obj: Dict, changes: List[Dict]) -> Dict:
        """Opération: ajouter un champ"""
        result = obj.copy()
        
        for change in changes:
            path = change['path']
            field_data = change['add']
            
            # Naviguer jusqu'au parent du champ
            parts = path.split('.')
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Ajouter le champ
            current[parts[-1]] = field_data
        
        return result
    
    def _op_add_extraction(self, obj: Dict, changes: List[Dict]) -> Dict:
        """Opération: ajouter une règle d'extraction"""
        result = obj.copy()
        
        for change in changes:
            path = change['path']
            extractions = change['add']
            
            # Naviguer jusqu'à metadata.extract
            if 'metadata' not in result:
                result['metadata'] = {}
            if 'extract' not in result['metadata']:
                result['metadata']['extract'] = []
            
            # Ajouter les extractions
            if isinstance(extractions, list):
                result['metadata']['extract'].extend(extractions)
            else:
                result['metadata']['extract'].append(extractions)
        
        return result
    
    def _op_merge(self, parents: List[Dict], changes: List[Dict]) -> Dict:
        """Opération: merger plusieurs parents"""
        if len(parents) < 2:
            return parents[0].copy()
        
        # Stratégie simple: union des clés
        result = {}
        
        for parent in parents:
            for key, value in parent.items():
                if key not in result:
                    result[key] = value
                elif isinstance(value, list):
                    # Combiner les listes
                    if isinstance(result[key], list):
                        result[key].extend(value)
                    else:
                        result[key] = value
                elif isinstance(value, dict):
                    # Merger récursivement
                    if isinstance(result[key], dict):
                        result[key] = self._merge_dicts(result[key], value)
                    else:
                        result[key] = value
        
        return result
    
    def _op_modify_logic(self, obj: Dict, changes: List[Dict]) -> Dict:
        """Opération: modifier la logique"""
        # TODO: Implémenter modification de logique
        return obj.copy()
    
    def _op_constrain_value(self, obj: Dict, changes: List[Dict]) -> Dict:
        """Opération: contraindre une valeur"""
        result = obj.copy()
        
        for change in changes:
            path = change['path']
            value = change['value']
            
            # Naviguer et modifier
            parts = path.split('.')
            current = result
            for part in parts[:-1]:
                current = current[part]
            
            current[parts[-1]] = value
        
        return result
    
    def _merge_dicts(self, d1: Dict, d2: Dict) -> Dict:
        """Merge récursif de deux dicts"""
        result = d1.copy()
        
        for key, value in d2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_dicts(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key].extend(value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _find_root(self, hash: str) -> str:
        """Trouve la racine (objet sans parents) d'un hash"""
        ancestors = self.dag.ancestors(hash)
        
        if not ancestors:
            return hash
        
        # Trouver celui sans parents
        for ancestor in ancestors:
            try:
                deriv = self.dag._load_derivation(ancestor)
                if not deriv.parents:
                    return ancestor
            except FileNotFoundError:
                # Pas de dérivation = racine
                return ancestor
        
        return ancestors[-1]  # Fallback
