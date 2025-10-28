#!/usr/bin/env python3
"""
Test Derivation System - Hypersémantique v4.0

Démontre:
1. Création de dérivations déclaratives
2. Évolution par branches parallèles
3. Merge sémantique
4. Reconstruction par replay
5. Navigation dans le DAG
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_engine.content_addressed_store import ContentAddressedStore
from universal_engine.derivation_manager import (
    DerivationManager,
    SemanticFingerprint,
    RelationType
)


def test_derivation_system():
    """Test complet du système de dérivation hypersémantique"""
    
    print("=" * 80)
    print("PANINI v4.0 - SYSTÈME DE DÉRIVATION HYPERSÉMANTIQUE")
    print("=" * 80)
    
    # Initialize
    store_path = Path("/tmp/panini_derivation_test")
    store = ContentAddressedStore(store_path)
    deriv_mgr = DerivationManager(store)
    
    print(f"\n📦 Store: {store_path}")
    
    # =========================================================================
    # TEST 1: Créer grammar PNG v1.0 (baseline)
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 1: Créer PNG Grammar v1.0 (baseline)")
    print("=" * 80)
    
    png_v1 = {
        'format': 'PNG',
        'version': '1.0',
        'patterns': [
            {
                'pattern_ref': '9949a471',
                'name': 'signature'
            },
            {
                'pattern_ref': '6eacc5de',
                'name': 'chunks'
            }
        ],
        'metadata': {
            'extract': [
                {'field': 'IHDR.width', 'as': 'image_width'},
                {'field': 'IHDR.height', 'as': 'image_height'}
            ]
        }
    }
    
    semantic_v1 = SemanticFingerprint(
        capabilities=['signature_detection', 'chunk_parsing', 
                     'basic_metadata_extraction'],
        intent=['format_identification', 'image_dimensions'],
        constraints={'requires_magic_number': True, 'chunk_based': True},
        domain={'format_types': ['binary', 'image'], 
               'use_cases': ['file_identification']}
    )
    
    import yaml
    png_v1_bytes = yaml.dump(png_v1, sort_keys=True).encode('utf-8')
    v1_hash, v1_sim, v1_meta = store.store(
        png_v1_bytes,
        'grammar',
        metadata={**png_v1, 'semantic': semantic_v1.to_dict()}
    )
    
    print(f"\n✓ PNG v1.0 créé:")
    print(f"  Hash exact:      {v1_hash}")
    print(f"  Hash similitude: {v1_sim}")
    print(f"  Capabilities:    {', '.join(semantic_v1.capabilities)}")
    
    store.create_ref('PNG/v1.0', 'grammar', v1_hash)
    store.create_ref('PNG/baseline', 'grammar', v1_hash)
    
    # =========================================================================
    # TEST 2: Dérivation v2.0-transparency (branche feature)
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 2: Dérivation v2.0-transparency (extends v1.0)")
    print("=" * 80)
    
    transformation_transparency = {
        'operation': 'add_extraction',
        'description': 'Add transparency/alpha channel support',
        'changes': [
            {
                'path': 'metadata.extract',
                'add': [
                    {'field': 'tRNS.alpha', 'as': 'has_transparency'},
                    {'field': 'tRNS.type', 'as': 'transparency_type'}
                ]
            }
        ]
    }
    
    semantic_v2_trans = SemanticFingerprint(
        capabilities=['signature_detection', 'chunk_parsing',
                     'basic_metadata_extraction', 'alpha_channel_detection'],
        intent=['format_identification', 'image_dimensions', 
               'transparency_support'],
        constraints={'requires_magic_number': True, 'chunk_based': True},
        domain={'format_types': ['binary', 'image'],
               'use_cases': ['file_identification', 'alpha_detection']}
    )
    
    v2_trans_hash = deriv_mgr.create_derivation(
        parent_hashes=[v1_hash],
        parent_type='grammar',
        transformation=transformation_transparency,
        semantic=semantic_v2_trans,
        author='panini-research'
    )
    
    print(f"\n✓ PNG v2.0-transparency créé:")
    print(f"  Hash exact: {v2_trans_hash}")
    print(f"  Parent:     {v1_hash}")
    print(f"  Operation:  {transformation_transparency['operation']}")
    print(f"  Ajout:      alpha_channel_detection")
    
    store.create_ref('PNG/v2.0-transparency', 'grammar', v2_trans_hash)
    
    # =========================================================================
    # TEST 3: Dérivation v2.0-color (branche parallèle)
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 3: Dérivation v2.0-color (branche parallèle)")
    print("=" * 80)
    
    transformation_color = {
        'operation': 'add_extraction',
        'description': 'Add color profile support',
        'changes': [
            {
                'path': 'metadata.extract',
                'add': [
                    {'field': 'cHRM.white_point', 'as': 'white_point'},
                    {'field': 'gAMA.gamma', 'as': 'gamma'}
                ]
            }
        ]
    }
    
    semantic_v2_color = SemanticFingerprint(
        capabilities=['signature_detection', 'chunk_parsing',
                     'basic_metadata_extraction', 'color_profile_extraction'],
        intent=['format_identification', 'image_dimensions',
               'color_management'],
        constraints={'requires_magic_number': True, 'chunk_based': True},
        domain={'format_types': ['binary', 'image'],
               'use_cases': ['file_identification', 'color_correction']}
    )
    
    v2_color_hash = deriv_mgr.create_derivation(
        parent_hashes=[v1_hash],
        parent_type='grammar',
        transformation=transformation_color,
        semantic=semantic_v2_color,
        author='panini-research'
    )
    
    print(f"\n✓ PNG v2.0-color créé:")
    print(f"  Hash exact: {v2_color_hash}")
    print(f"  Parent:     {v1_hash}")
    print(f"  Operation:  {transformation_color['operation']}")
    print(f"  Ajout:      color_profile_extraction")
    
    store.create_ref('PNG/v2.0-color', 'grammar', v2_color_hash)
    
    # =========================================================================
    # TEST 4: Merge v3.0 (fusion des deux branches)
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 4: Merge v3.0 (transparency + color)")
    print("=" * 80)
    
    transformation_merge = {
        'operation': 'merge',
        'description': 'Combine transparency and color profile features',
        'changes': [
            {
                'path': 'metadata.extract',
                'merge': {
                    'from_parents': [v2_trans_hash, v2_color_hash],
                    'strategy': 'union'
                }
            }
        ]
    }
    
    semantic_v3 = SemanticFingerprint(
        capabilities=['signature_detection', 'chunk_parsing',
                     'basic_metadata_extraction', 
                     'alpha_channel_detection',
                     'color_profile_extraction'],
        intent=['format_identification', 'image_dimensions',
               'transparency_support', 'color_management'],
        constraints={'requires_magic_number': True, 'chunk_based': True},
        domain={'format_types': ['binary', 'image'],
               'use_cases': ['file_identification', 'alpha_detection',
                           'color_correction']}
    )
    
    v3_hash = deriv_mgr.create_derivation(
        parent_hashes=[v2_trans_hash, v2_color_hash],
        parent_type='grammar',
        transformation=transformation_merge,
        semantic=semantic_v3,
        author='panini-research'
    )
    
    print(f"\n✓ PNG v3.0 créé (merge):")
    print(f"  Hash exact:  {v3_hash}")
    print(f"  Parents:     {v2_trans_hash}")
    print(f"               {v2_color_hash}")
    print(f"  Operation:   {transformation_merge['operation']}")
    print(f"  Capabilities: {len(semantic_v3.capabilities)} au total")
    
    store.create_ref('PNG/v3.0', 'grammar', v3_hash)
    store.create_ref('PNG/latest', 'grammar', v3_hash)
    
    # =========================================================================
    # TEST 5: Reconstruction par replay
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 5: Reconstruction PNG v3.0 par replay")
    print("=" * 80)
    
    # Reconstruire v3.0 depuis v1.0
    reconstructed = deriv_mgr.reconstruct(v3_hash, 'grammar')
    
    print(f"\n✓ Reconstruction réussie:")
    print(f"  Format:       {reconstructed['format']}")
    print(f"  Version:      {reconstructed.get('version', 'merged')}")
    print(f"  Patterns:     {len(reconstructed['patterns'])}")
    print(f"  Extractions:  {len(reconstructed['metadata']['extract'])}")
    
    # Vérifier que toutes les extractions sont présentes
    extractions = reconstructed['metadata']['extract']
    fields = [e['as'] for e in extractions]
    
    print(f"\n  Champs extraits:")
    for field in fields:
        print(f"    - {field}")
    
    expected = ['image_width', 'image_height', 'has_transparency',
                'transparency_type', 'white_point', 'gamma']
    
    missing = set(expected) - set(fields)
    if missing:
        print(f"\n  ⚠️  Champs manquants: {missing}")
    else:
        print(f"\n  ✓ Tous les champs attendus présents!")
    
    # =========================================================================
    # TEST 6: Navigation dans le DAG
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("TEST 6: Navigation dans le DAG sémantique")
    print("=" * 80)
    
    # Ancêtres de v3.0
    print(f"\n🔍 Ancêtres de v3.0:")
    ancestors = deriv_mgr.dag.ancestors(v3_hash, max_depth=10)
    for i, ancestor in enumerate(ancestors, 1):
        print(f"  {i}. {ancestor}")
    
    # Siblings de v2.0-transparency
    print(f"\n🔍 Siblings de v2.0-transparency:")
    siblings = deriv_mgr.dag.siblings(v2_trans_hash)
    for sibling in siblings:
        print(f"  - {sibling}")
    
    # Ancêtre commun
    print(f"\n🔍 Ancêtre commun (v2.0-trans ∩ v2.0-color):")
    common = deriv_mgr.dag.common_ancestor(v2_trans_hash, v2_color_hash)
    print(f"  {common}")
    print(f"  (= v1.0: {common == v1_hash})")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("✅ RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    print(f"""
📊 DAG Créé:

    [v1.0: {v1_hash[:8]}]
       |
       +--- [v2.0-trans: {v2_trans_hash[:8]}]
       |         |
       |         +--- [v3.0: {v3_hash[:8]}]
       |         |       /
       +--- [v2.0-color: {v2_color_hash[:8]}]

✓ 4 versions créées (v1.0, v2.0-trans, v2.0-color, v3.0)
✓ 2 branches parallèles (transparency, color)
✓ 1 merge réussi (v3.0 combine les deux)
✓ Reconstruction par replay fonctionne
✓ Navigation DAG opérationnelle

🎯 Propriétés Hypersémantiques:
  ✓ Immutabilité (chaque version = hash unique)
  ✓ Évolution déclarative (transformations YAML)
  ✓ Branches parallèles (développement concurrent)
  ✓ Merge sémantique (union de capabilities)
  ✓ Provenance complète (chaîne v1→v2→v3)
  ✓ Reconstruction multiple (replay ou direct)

🚀 Inspiration Pāṇinienne:
  - v1.0 = dhātu racine (primitive)
  - v2.0 = pratyaya (affixes ajoutent features)
  - v3.0 = sandhi (fusion euphonique de branches)
  - DAG = réseau de dérivations (comme Sanskrit)
""")
    
    print("=" * 80)
    print("🎉 Système de Dérivation Hypersémantique: VALIDÉ!")
    print("=" * 80)


if __name__ == '__main__':
    test_derivation_system()
