# 🔧 Guide Dépannage Colab : Erreurs Import

**Date** : 12 novembre 2025  
**Objectif** : Résoudre rapidement les erreurs d'import dans Colab

---

## ❌ Erreur Type 1 : ModuleNotFoundError

### Symptôme
```python
ModuleNotFoundError: No module named 'donnees_nsm'
```

### Causes Possibles

1. **Repo pas cloné** ❌
2. **Path incorrect** ❌
3. **Fichier pas poussé GitHub** ❌
4. **Typo nom fichier** ❌

### Solutions (dans l'ordre)

#### Solution 1.1 : Vérifier repo cloné
```python
import os
print("Repo existe ?", os.path.exists('/content/Panini-Research'))
```

**Si False** → Exécuter cellule clone repo :
```python
!git clone https://github.com/stephanedenis/Panini-Research.git
```

---

#### Solution 1.2 : Vérifier fichier existe
```python
import os
fichier = '/content/Panini-Research/research/semantic-primitives/notebooks/donnees_nsm.py'
print("Fichier existe ?", os.path.exists(fichier))
```

**Si False** → Fichier pas encore sur GitHub, attendre ou :
```python
# Forcer pull dernière version
!cd /content/Panini-Research && git pull origin main
```

---

#### Solution 1.3 : Vérifier path ajouté
```python
import sys
path_notebooks = '/content/Panini-Research/research/semantic-primitives/notebooks'
print("Path dans sys.path ?", path_notebooks in sys.path)

# Si False, ajouter :
sys.path.append(path_notebooks)
```

---

#### Solution 1.4 : Import direct absolu
```python
# Bypass sys.path, import direct
import sys
sys.path.insert(0, '/content/Panini-Research/research/semantic-primitives/notebooks')

from donnees_nsm import NSM_PRIMITIVES, COULEURS_CATEGORIES, CARRES_SEMIOTIQUES, CORPUS_TEST
```

---

## ❌ Erreur Type 2 : AttributeError

### Symptôme
```python
AttributeError: 'dict' object has no attribute 'forme_francaise'
```

### Cause
Structure primitive incorrecte (dict au lieu de PrimitiveNSM)

### Solution : Vérifier type
```python
prim = list(NSM_PRIMITIVES.values())[0]
print(type(prim))  # Doit être : <class 'donnees_nsm.PrimitiveNSM'>

# Si c'est dict, forcer réimport :
import importlib
import donnees_nsm
importlib.reload(donnees_nsm)
from donnees_nsm import NSM_PRIMITIVES
```

---

## ❌ Erreur Type 3 : KeyError

### Symptôme
```python
KeyError: 'JE'
```

### Cause
Primitive pas dans dictionnaire (mauvaise version)

### Solution : Vérifier contenu
```python
print("Nombre primitives :", len(NSM_PRIMITIVES))
print("Clés disponibles :", list(NSM_PRIMITIVES.keys())[:10])

# Si nombre != 61, réimporter :
!cd /content/Panini-Research && git pull origin main
import importlib
import donnees_nsm
importlib.reload(donnees_nsm)
```

---

## ❌ Erreur Type 4 : ImportError panlang

### Symptôme
```python
ImportError: cannot import name 'NSM_PRIMITIVES' from 'nsm_primitives'
```

### Cause
Fallback essaie d'importer depuis `panlang/` (pas nécessaire)

### Solution : Désactiver fallback
Éditer `donnees_nsm.py` ligne 20-30, commenter le try/except :

```python
# try:
#     import sys
#     import os
#     sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))
#     from nsm_primitives import NSM_PRIMITIVES as NSM_RAW
#     ...
# except ImportError:

# Utiliser directement fallback :
NSM_PRIMITIVES = {
    "JE": PrimitiveNSM("JE", "je", "SUBSTANTIFS", "aham"),
    # ...
}
```

---

## ✅ Cellule Debug Complète

Copiez-collez cette cellule pour diagnostiquer :

```python
import os
import sys

print("=" * 60)
print("🔍 DIAGNOSTIC IMPORT DONNÉES NSM")
print("=" * 60)

# Test 1 : Repo cloné ?
repo_path = '/content/Panini-Research'
print(f"\n1️⃣ Repo cloné ? {os.path.exists(repo_path)}")
if os.path.exists(repo_path):
    print(f"   ✅ Repo existe : {repo_path}")
else:
    print(f"   ❌ Cloner : !git clone https://github.com/stephanedenis/Panini-Research.git")

# Test 2 : Fichier existe ?
fichier_path = '/content/Panini-Research/research/semantic-primitives/notebooks/donnees_nsm.py'
print(f"\n2️⃣ Fichier existe ? {os.path.exists(fichier_path)}")
if os.path.exists(fichier_path):
    print(f"   ✅ Fichier trouvé : {fichier_path}")
    size = os.path.getsize(fichier_path)
    print(f"   📦 Taille : {size:,} bytes")
else:
    print(f"   ❌ Fichier manquant, pull : !cd {repo_path} && git pull")

# Test 3 : Path sys.path ?
notebooks_path = '/content/Panini-Research/research/semantic-primitives/notebooks'
print(f"\n3️⃣ Path dans sys.path ? {notebooks_path in sys.path}")
if notebooks_path not in sys.path:
    print(f"   ⚠️  Ajouter : sys.path.append('{notebooks_path}')")
    sys.path.append(notebooks_path)
else:
    print(f"   ✅ Path configuré")

# Test 4 : Import module ?
print(f"\n4️⃣ Test import module...")
try:
    from donnees_nsm import NSM_PRIMITIVES, COULEURS_CATEGORIES, CARRES_SEMIOTIQUES, CORPUS_TEST
    print(f"   ✅ Import réussi !")
    print(f"   📊 {len(NSM_PRIMITIVES)} primitives")
    print(f"   📊 {len(CARRES_SEMIOTIQUES)} carrés")
    print(f"   📊 {len(CORPUS_TEST)} phrases")
except Exception as e:
    print(f"   ❌ Erreur : {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 5 : Structure primitive ?
if 'NSM_PRIMITIVES' in locals():
    print(f"\n5️⃣ Test structure...")
    prim = list(NSM_PRIMITIVES.values())[0]
    print(f"   Type : {type(prim)}")
    try:
        print(f"   Nom : {prim.nom}")
        print(f"   Forme : {prim.forme_francaise}")
        print(f"   Catégorie : {prim.categorie}")
        print(f"   ✅ Structure valide")
    except AttributeError as e:
        print(f"   ❌ Structure incorrecte : {e}")

print("\n" + "=" * 60)
print("✅ DIAGNOSTIC TERMINÉ")
print("=" * 60)
```

---

## 🚀 Workflow Correct (Sans Erreur)

### Cellule 1 : Setup
```python
# Installation dépendances
!pip install -q sentence-transformers scikit-learn matplotlib seaborn plotly pandas tqdm
```

### Cellule 2 : Clone Repo
```python
# Clone repo Panini Research
import os
if not os.path.exists('Panini-Research'):
    !git clone https://github.com/stephanedenis/Panini-Research.git
    print("✅ Repo cloné")
else:
    print("✅ Repo déjà présent")
    # Optionnel : pull dernière version
    !cd Panini-Research && git pull origin main
```

### Cellule 3 : Config Path
```python
# Ajouter au path Python
import sys
sys.path.append('/content/Panini-Research/research/semantic-primitives/notebooks')
print("✅ Path configuré")
```

### Cellule 4 : Import Données ✅
```python
# Import données NSM
from donnees_nsm import NSM_PRIMITIVES, COULEURS_CATEGORIES, CARRES_SEMIOTIQUES, CORPUS_TEST

print(f"✅ {len(NSM_PRIMITIVES)} primitives NSM chargées")
print(f"✅ {len(CARRES_SEMIOTIQUES)} carrés sémiotiques chargés")
print(f"✅ {len(CORPUS_TEST)} phrases corpus chargées")
```

**Output attendu** :
```
✅ 61 primitives NSM chargées
✅ 20 carrés sémiotiques chargés
✅ 105 phrases corpus chargées
```

---

## 📞 Si Problème Persiste

### Option 1 : Copy-Paste Direct

Au lieu d'importer, copiez le code directement dans une cellule :

```python
# Définition classe PrimitiveNSM
class PrimitiveNSM:
    def __init__(self, nom: str, forme_francaise: str, categorie: str, sanskrit: str = ""):
        self.nom = nom
        self.forme_francaise = forme_francaise
        self.categorie = categorie
        self.sanskrit = sanskrit

# Données NSM (version minimale pour test)
NSM_PRIMITIVES = {
    "JE": PrimitiveNSM("JE", "je", "SUBSTANTIFS", "aham"),
    "TOI": PrimitiveNSM("TOI", "toi", "SUBSTANTIFS", "tvam"),
    "SAVOIR": PrimitiveNSM("SAVOIR", "savoir", "MENTAUX", "jñā"),
    # ... ajouter autres primitives
}

CARRES_SEMIOTIQUES = {
    "VIE_MORT": {
        "S1": "VIVRE",
        "S2": "MOURIR",
        "non_S1": "NE_PAS_VIVRE",
        "non_S2": "NE_PAS_MOURIR",
    },
    # ... ajouter autres carrés
}

CORPUS_TEST = [
    "Je sais que tu penses à quelque chose",
    "Les gens veulent savoir la vérité",
    # ... ajouter autres phrases
]

print(f"✅ {len(NSM_PRIMITIVES)} primitives définies")
```

### Option 2 : Upload Fichier Direct

1. Cliquez icône fichier 📁 (panneau gauche Colab)
2. Upload `donnees_nsm.py` depuis votre machine
3. Import direct :
```python
from donnees_nsm import NSM_PRIMITIVES
```

### Option 3 : wget Direct

```python
# Télécharger fichier direct depuis GitHub
!wget https://raw.githubusercontent.com/stephanedenis/Panini-Research/main/research/semantic-primitives/notebooks/donnees_nsm.py

# Import
from donnees_nsm import NSM_PRIMITIVES
```

---

## 📊 Checklist Pré-Exécution

Avant d'exécuter le notebook, vérifiez :

- [ ] Runtime configuré (GPU A100)
- [ ] Cellule 1 exécutée (pip install)
- [ ] Cellule 2 exécutée (git clone)
- [ ] Cellule 3 exécutée (sys.path.append)
- [ ] Cellule diagnostic exécutée (tests)
- [ ] Output "✅ 61 primitives" affiché
- [ ] Pas d'erreur rouge visible

**Si tous ✅ → Exécuter suite du notebook !**

---

**Date** : 12 novembre 2025  
**Version** : 1.0 - Guide Dépannage Complet  
**Auteur** : Panini Research - Support Technique
