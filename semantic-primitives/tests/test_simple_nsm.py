#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test simplifie pour verifier l'installation NSM"""

import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))

try:
    from nsm_primitives import get_statistics
    from panlang_reconstructeur_enrichi import ReconstructeurEnrichi
    
    print("[OK] Imports reussis!")
    print("-" * 50)
    
    # Test 1: Statistiques NSM
    stats = get_statistics()
    print("\n[STATS] Statistiques NSM:")
    for key, value in stats.items():
        print("  {}: {}".format(key, value))
    
    # Test 2: Initialisation du reconstructeur
    reconstructeur = ReconstructeurEnrichi()
    print("\n[OK] Reconstructeur initialise")
    
    # Test 3: Decomposition simple
    print("\n[TEST] Test de decomposition:")
    decomp = reconstructeur.decomposer_concept("ENSEIGNER")
    print("ENSEIGNER = {}".format(decomp))
    
except Exception as e:
    print("[ERREUR]: {}".format(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
