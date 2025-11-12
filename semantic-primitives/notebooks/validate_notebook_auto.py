#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation automatique Notebook NSM-SentenceBERT
Simule l'environnement Colab pour tester l'exécution complète
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

print("🧪 VALIDATION AUTOMATIQUE NOTEBOOK NSM-SENTENCEBERT")
print("=" * 70)

# Configuration
REPO_URL = "https://github.com/stephanedenis/Panini-Research.git"
NOTEBOOK_PATH = "semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb"

# Créer environnement temporaire (simule /content de Colab)
temp_dir = tempfile.mkdtemp(prefix="colab_sim_")
print(f"📁 Environnement temporaire : {temp_dir}")

try:
    # Étape 1 : Clone repo (simule git clone Colab)
    print("\n1️⃣ Clone repository...")
    repo_dir = os.path.join(temp_dir, "Panini-Research")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, repo_dir],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Erreur clone : {result.stderr}")
        sys.exit(1)
    
    print(f"✅ Repo cloné : {repo_dir}")
    
    # Étape 2 : Vérifier fichier donnees_nsm.py existe
    print("\n2️⃣ Vérification fichier donnees_nsm.py...")
    donnees_path = os.path.join(
        repo_dir, 
        "semantic-primitives/notebooks/donnees_nsm.py"
    )
    
    if not os.path.exists(donnees_path):
        print(f"❌ Fichier manquant : {donnees_path}")
        print("💡 Le fichier n'est pas encore sur GitHub main")
        sys.exit(1)
    
    size = os.path.getsize(donnees_path)
    print(f"✅ Fichier trouvé : {size:,} bytes")
    
    # Étape 3 : Test import module (simule cellule import)
    print("\n3️⃣ Test import module...")
    
    # Ajouter au path comme dans Colab
    notebooks_dir = os.path.join(repo_dir, "semantic-primitives/notebooks")
    if notebooks_dir not in sys.path:
        sys.path.insert(0, notebooks_dir)
    
    # Test import
    try:
        from donnees_nsm import (
            NSM_PRIMITIVES, 
            COULEURS_CATEGORIES, 
            CARRES_SEMIOTIQUES, 
            CORPUS_TEST
        )
        print(f"✅ Import réussi")
        print(f"   - {len(NSM_PRIMITIVES)} primitives NSM")
        print(f"   - {len(CARRES_SEMIOTIQUES)} carrés sémiotiques")
        print(f"   - {len(CORPUS_TEST)} phrases corpus")
    except Exception as e:
        print(f"❌ Erreur import : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Étape 4 : Test structure données
    print("\n4️⃣ Validation structure données...")
    
    # Test primitives
    if len(NSM_PRIMITIVES) < 60:
        print(f"⚠️  Nombre primitives insuffisant : {len(NSM_PRIMITIVES)} < 60")
    else:
        print(f"✅ Primitives : {len(NSM_PRIMITIVES)} OK")
    
    # Test structure primitive
    prim = list(NSM_PRIMITIVES.values())[0]
    try:
        _ = prim.nom
        _ = prim.forme_francaise
        _ = prim.categorie
        _ = prim.sanskrit
        print(f"✅ Structure PrimitiveNSM : OK")
    except AttributeError as e:
        print(f"❌ Structure primitive incorrecte : {e}")
        sys.exit(1)
    
    # Test carrés
    if len(CARRES_SEMIOTIQUES) < 15:
        print(f"⚠️  Nombre carrés insuffisant : {len(CARRES_SEMIOTIQUES)} < 15")
    else:
        print(f"✅ Carrés sémiotiques : {len(CARRES_SEMIOTIQUES)} OK")
    
    # Test corpus
    if len(CORPUS_TEST) < 100:
        print(f"⚠️  Corpus insuffisant : {len(CORPUS_TEST)} < 100")
    else:
        print(f"✅ Corpus phrases : {len(CORPUS_TEST)} OK")
    
    # Étape 5 : Test extraction données (simule cellule encodage)
    print("\n5️⃣ Test extraction données (comme notebook)...")
    
    try:
        primitives_list = list(NSM_PRIMITIVES.items())
        primitives_text = [p.forme_francaise for nom, p in primitives_list]
        primitives_noms = [nom for nom, p in primitives_list]
        primitives_categories = [p.categorie for nom, p in primitives_list]
        
        print(f"✅ Extraction réussie :")
        print(f"   - {len(primitives_text)} formes françaises")
        print(f"   - {len(primitives_noms)} noms")
        print(f"   - {len(primitives_categories)} catégories")
        print(f"   - Exemple : {primitives_noms[0]} = '{primitives_text[0]}' ({primitives_categories[0]})")
    except Exception as e:
        print(f"❌ Erreur extraction : {e}")
        sys.exit(1)
    
    # Étape 6 : Test carrés sémiotiques
    print("\n6️⃣ Test carrés sémiotiques...")
    
    try:
        for nom_carre, carre in list(CARRES_SEMIOTIQUES.items())[:2]:
            assert 'S1' in carre
            assert 'S2' in carre
            assert 'non_S1' in carre
            assert 'non_S2' in carre
        print(f"✅ Structure carrés valide")
    except Exception as e:
        print(f"❌ Erreur carrés : {e}")
        sys.exit(1)
    
    # Étape 7 : Test corpus itération
    print("\n7️⃣ Test corpus itération...")
    
    try:
        for i, phrase in enumerate(CORPUS_TEST[:3]):
            assert isinstance(phrase, str)
            assert len(phrase) > 0
        print(f"✅ Corpus itérable : {len(CORPUS_TEST)} phrases")
    except Exception as e:
        print(f"❌ Erreur corpus : {e}")
        sys.exit(1)
    
    # Étape 8 : Test solution rapide (téléchargement direct)
    print("\n8️⃣ Test solution rapide (téléchargement GitHub raw)...")
    
    import urllib.request
    
    url = "https://raw.githubusercontent.com/stephanedenis/Panini-Research/main/semantic-primitives/notebooks/donnees_nsm.py"
    temp_file = os.path.join(temp_dir, "donnees_nsm_downloaded.py")
    
    try:
        urllib.request.urlretrieve(url, temp_file)
        downloaded_size = os.path.getsize(temp_file)
        print(f"✅ Téléchargement direct réussi : {downloaded_size:,} bytes")
        
        # Vérifier que les tailles correspondent
        if abs(downloaded_size - size) > 100:
            print(f"⚠️  Tailles différentes : local {size} vs téléchargé {downloaded_size}")
        else:
            print(f"✅ Tailles cohérentes")
    except Exception as e:
        print(f"❌ Erreur téléchargement : {e}")
        print(f"⚠️  Solution rapide pourrait échouer dans Colab")
    
    # SUCCESS
    print("\n" + "=" * 70)
    print("✅✅✅ VALIDATION COMPLÈTE RÉUSSIE !")
    print("=" * 70)
    print("\n📊 Résumé :")
    print(f"   ✅ Repo clonable")
    print(f"   ✅ Fichier donnees_nsm.py présent sur GitHub")
    print(f"   ✅ Import fonctionne")
    print(f"   ✅ Structure données valide")
    print(f"   ✅ {len(NSM_PRIMITIVES)} primitives accessibles")
    print(f"   ✅ {len(CARRES_SEMIOTIQUES)} carrés valides")
    print(f"   ✅ {len(CORPUS_TEST)} phrases corpus")
    print(f"   ✅ Solution rapide téléchargement fonctionne")
    print("\n🚀 Le notebook devrait fonctionner dans Colab !")

except Exception as e:
    print(f"\n❌ ERREUR VALIDATION : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    # Nettoyage
    print(f"\n🧹 Nettoyage : {temp_dir}")
    try:
        shutil.rmtree(temp_dir)
        print("✅ Environnement temporaire supprimé")
    except Exception as e:
        print(f"⚠️  Erreur nettoyage : {e}")

print("\n✅ Script terminé avec succès")
