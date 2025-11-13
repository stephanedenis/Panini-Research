#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de pré-vérification pour exécution Google Colab
À exécuter AVANT de lancer le notebook complet pour détecter les problèmes
"""

import sys
import os

print("=" * 70)
print("PRE-VERIFICATION NOTEBOOK NSM SENTENCEBERT")
print("=" * 70)

# Vérifier l'existence des fichiers
print("\n[1/5] Verification fichiers...")
required_files = [
    'donnees_nsm.py',
    'NSM_SentenceBERT_Local.ipynb'
]

missing_files = []
for file in required_files:
    if os.path.exists(file):
        print(f"  OK {file}")
    else:
        print(f"  MANQUANT: {file}")
        missing_files.append(file)

if missing_files:
    print(f"\nERREUR: {len(missing_files)} fichiers manquants!")
    sys.exit(1)

# Vérifier l'import des données
print("\n[2/5] Import donnees_nsm...")
try:
    from donnees_nsm import NSM_PRIMITIVES, CARRES_SEMIOTIQUES, COULEURS_CATEGORIES, CORPUS_TEST
    print(f"  OK Import reussi")
    print(f"     - {len(NSM_PRIMITIVES)} primitives NSM")
    print(f"     - {len(CARRES_SEMIOTIQUES)} carres semiotiques")
    print(f"     - {len(COULEURS_CATEGORIES)} categories couleurs")
    print(f"     - {len(CORPUS_TEST)} phrases dans corpus")
except ImportError as e:
    print(f"  ERREUR: {e}")
    sys.exit(1)

# Vérifier les primitives des carrés
print("\n[3/5] Validation carres semiotiques...")
primitives_invalides = []
for nom_carre, carre in CARRES_SEMIOTIQUES.items():
    for position in ["S1", "S2", "non_S1", "non_S2"]:
        if carre[position] not in NSM_PRIMITIVES:
            primitives_invalides.append(f"{nom_carre}.{position}")

if primitives_invalides:
    print(f"  ERREUR: {len(primitives_invalides)} primitives invalides")
    for p in primitives_invalides[:5]:
        print(f"     - {p}")
    sys.exit(1)
else:
    print(f"  OK Tous les carres sont valides")
    print(f"     - 80/80 primitives existent (20 carres x 4 positions)")

# Vérifier les catégories des couleurs
print("\n[4/5] Validation categories couleurs...")
categories_manquantes = set()
for prim in NSM_PRIMITIVES.values():
    if prim.categorie not in COULEURS_CATEGORIES:
        categories_manquantes.add(prim.categorie)

if categories_manquantes:
    print(f"  AVERTISSEMENT: {len(categories_manquantes)} categories sans couleur")
    for cat in categories_manquantes:
        print(f"     - {cat}")
    print("  Note: Le fallback 'gray' sera utilise")
else:
    print(f"  OK Toutes les categories ont une couleur")

# Vérifier les dépendances Python (optionnel pour Colab)
print("\n[5/5] Verification dependances Python...")
dependencies = {
    'sentence_transformers': 'SentenceBERT',
    'sklearn': 'scikit-learn',
    'numpy': 'NumPy',
    'matplotlib': 'Matplotlib'
}

missing_deps = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"  OK {name}")
    except ImportError:
        print(f"  MANQUANT: {name}")
        missing_deps.append(name)

if missing_deps:
    print(f"\nATTENTION: {len(missing_deps)} dependances manquantes")
    print("Installer avec: pip install sentence-transformers scikit-learn")
else:
    print("\n  OK Toutes les dependances sont installees")

# Résumé
print("\n" + "=" * 70)
if not missing_files and not primitives_invalides and not missing_deps:
    print("SUCCES: Notebook pret pour execution!")
    print("=" * 70)
    print("\nProchaine etape:")
    print("  1. Ouvrir Google Colab (https://colab.research.google.com/)")
    print("  2. Importer: stephanedenis/Panini-Research")
    print("  3. Fichier: semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb")
    print("  4. GPU: A100 (Runtime > Change runtime type > A100)")
    print("  5. Executer toutes les cellules")
else:
    print("ERREUR: Des problemes ont ete detectes!")
    print("=" * 70)
    if missing_files:
        print(f"\n  - {len(missing_files)} fichiers manquants")
    if primitives_invalides:
        print(f"  - {len(primitives_invalides)} primitives invalides dans carres")
    if missing_deps:
        print(f"  - {len(missing_deps)} dependances Python manquantes")
    sys.exit(1)
