#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier que donnees_nsm.py fonctionne
Simule l'environnement Colab
"""

import sys
import os

print("🧪 Test Import Données NSM (Simulation Colab)")
print("=" * 60)

# Simulation environnement Colab
base_path = "/home/stephane/GitHub/Panini/research/semantic-primitives"
notebooks_path = os.path.join(base_path, "notebooks")

# Ajouter au path (comme dans Colab)
if notebooks_path not in sys.path:
    sys.path.append(notebooks_path)
    print(f"✅ Path ajouté: {notebooks_path}")

# Test 1: Import module
print("\n📦 Test 1: Import module")
try:
    from donnees_nsm import (
        NSM_PRIMITIVES, 
        COULEURS_CATEGORIES, 
        CARRES_SEMIOTIQUES, 
        CORPUS_TEST,
        obtenir_categories,
        obtenir_primitives_par_categorie
    )
    print("✅ Import réussi")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)

# Test 2: Vérifier contenu
print("\n📊 Test 2: Vérifier contenu")
print(f"✅ Primitives NSM: {len(NSM_PRIMITIVES)}")
print(f"✅ Carrés sémiotiques: {len(CARRES_SEMIOTIQUES)}")
print(f"✅ Phrases corpus: {len(CORPUS_TEST)}")
print(f"✅ Couleurs catégories: {len(COULEURS_CATEGORIES)}")

# Test 3: Vérifier structure primitives
print("\n🔍 Test 3: Structure primitives")
if len(NSM_PRIMITIVES) > 0:
    prim = list(NSM_PRIMITIVES.values())[0]
    print(f"✅ Primitive exemple: {prim.nom}")
    print(f"   - forme_francaise: {prim.forme_francaise}")
    print(f"   - categorie: {prim.categorie}")
    print(f"   - sanskrit: {prim.sanskrit}")
else:
    print("❌ Aucune primitive trouvée")
    sys.exit(1)

# Test 4: Vérifier catégories
print("\n📑 Test 4: Catégories")
categories = obtenir_categories()
print(f"✅ {len(categories)} catégories: {', '.join(sorted(categories))}")

# Test 5: Vérifier carrés sémiotiques
print("\n🔲 Test 5: Carrés sémiotiques")
if len(CARRES_SEMIOTIQUES) > 0:
    carre_nom = list(CARRES_SEMIOTIQUES.keys())[0]
    carre = CARRES_SEMIOTIQUES[carre_nom]
    print(f"✅ Carré exemple: {carre_nom}")
    print(f"   - S1: {carre['S1']}")
    print(f"   - S2: {carre['S2']}")
    print(f"   - non_S1: {carre['non_S1']}")
    print(f"   - non_S2: {carre['non_S2']}")
else:
    print("❌ Aucun carré trouvé")
    sys.exit(1)

# Test 6: Vérifier corpus
print("\n📝 Test 6: Corpus")
if len(CORPUS_TEST) >= 3:
    print(f"✅ Phrase 1: {CORPUS_TEST[0]}")
    print(f"✅ Phrase 2: {CORPUS_TEST[1]}")
    print(f"✅ Phrase 3: {CORPUS_TEST[2]}")
    print(f"   ... ({len(CORPUS_TEST) - 3} autres phrases)")
else:
    print("❌ Corpus insuffisant")
    sys.exit(1)

# Test 7: Comptage par catégorie
print("\n📈 Test 7: Distribution par catégorie")
for cat in sorted(categories):
    prims_cat = obtenir_primitives_par_categorie(cat)
    print(f"   {cat}: {len(prims_cat)} primitives")

# Test 8: Vérifier accès attributs
print("\n🔑 Test 8: Accès attributs primitives")
try:
    # Test accès par clé
    if "JE" in NSM_PRIMITIVES:
        prim_je = NSM_PRIMITIVES["JE"]
        print(f"✅ NSM_PRIMITIVES['JE'].forme_francaise = '{prim_je.forme_francaise}'")
    
    # Test itération
    count = sum(1 for _ in NSM_PRIMITIVES.values())
    print(f"✅ Itération: {count} primitives accessibles")
    
except Exception as e:
    print(f"❌ Erreur accès: {e}")
    sys.exit(1)

# Test 9: Vérifier couleurs
print("\n🎨 Test 9: Couleurs catégories")
for cat in sorted(categories):
    if cat in COULEURS_CATEGORIES:
        print(f"✅ {cat}: {COULEURS_CATEGORIES[cat]}")
    else:
        print(f"⚠️  {cat}: pas de couleur définie")

print("\n" + "=" * 60)
print("✅ TOUS LES TESTS PASSÉS !")
print("=" * 60)
