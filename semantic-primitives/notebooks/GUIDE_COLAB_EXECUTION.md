# 🚀 Guide d'Exécution : Notebook NSM-SentenceBERT dans Google Colab

## ✅ Pré-requis

- **Compte Google Colab** (gratuit ou Pro)
- **GPU recommandé** : T4 (gratuit), L4 (gratuit), ou A100 (Pro)
- **Temps d'exécution** : ~5 minutes total

---

## 📋 Instructions Étape par Étape

### 1️⃣ Ouvrir le Notebook dans Colab

**URL directe** :
```
https://colab.research.google.com/github/stephanedenis/Panini-Research/blob/main/semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb
```

Ou manuellement :
1. Aller sur [Google Colab](https://colab.research.google.com)
2. Cliquer sur **Fichier → Ouvrir un notebook**
3. Onglet **GitHub**
4. Entrer : `stephanedenis/Panini-Research`
5. Sélectionner : `semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb`

---

### 2️⃣ Configurer le GPU (Recommandé)

1. **Menu** : Runtime → Change runtime type
2. **Hardware accelerator** : GPU
3. **GPU type** :
   - **T4** ou **L4** : Gratuit (15 Go VRAM)
   - **A100** : Colab Pro uniquement (40 Go VRAM)

💡 **Note** : Le notebook fonctionne aussi sur CPU, mais sera plus lent (~10 min vs ~5 min).

---

### 3️⃣ Exécuter le Notebook

#### Option A : Exécution Automatique (Recommandé)

1. **Menu** : Runtime → Run all
2. Attendre ~5 minutes
3. ✅ Tous les résultats apparaissent automatiquement

#### Option B : Exécution Cellule par Cellule

1. **Cellule 1** : Installation des packages (~30 sec)
   ```
   ✅ Packages installés
   ```

2. **Cellule 2** : Clone du repo GitHub (~10 sec)
   ```
   ✅ Repo cloné
   ```

3. **Cellule 3** : Diagnostic environnement (~1 sec)
   ```
   🔍 DIAGNOSTIC ENVIRONNEMENT
   1️⃣ Repo cloné : True
   2️⃣ Fichier donnees_nsm.py : True
   3️⃣ Path notebooks : /content/Panini-Research/semantic-primitives/notebooks
   ✅ Diagnostic terminé
   ```

4. **Cellule 4** : Import données NSM (~1 sec)
   ```
   ✅ 61 primitives NSM chargées
   ✅ 20 carrés sémiotiques chargés
   ✅ 105 phrases corpus chargées
   ```

5. **Cellules 5+** : Chargement modèle + expériences (~3 min)
   - Loading Sentence-BERT (~1 min)
   - Clustering primitives (~30 sec)
   - Matrice similarités (~30 sec)
   - Visualisations (~1 min)

---

## 🎯 Résultats Attendus

### Expérience 1 : Clustering Primitives NSM
- **Dendrogramme** : Visualisation hiérarchique des 61 primitives
- **Groupes sémantiques** : Classification automatique par sens

### Expérience 2 : Matrice de Similarités
- **Heatmap** : Distances cosinus entre primitives
- **Top similarités** : Paires les plus proches (ex: PERSONNE ↔ QUELQU'UN)

### Expérience 3 : Projection 2D (t-SNE)
- **Carte sémantique** : Primitives dans espace 2D
- **Couleurs** : Par catégories NSM (substantifs, actions, déterminants, etc.)

### Expérience 4 : Carrés Sémiotiques
- **Structures Greimas** : 20 carrés analysés
- **Axes principaux** : Contrariété, contradiction, complémentarité

---

## 🔍 Dépannage

### ❌ Erreur : "ModuleNotFoundError: No module named 'donnees_nsm'"

**Cause** : Repo pas cloné ou path incorrect

**Solution** :
```python
# Ré-exécuter cellule 2 (git clone)
!git clone https://github.com/stephanedenis/Panini-Research.git

# Vérifier fichier existe
!ls -lh /content/Panini-Research/semantic-primitives/notebooks/donnees_nsm.py
```

---

### ❌ Erreur : "FileNotFoundError: donnees_nsm.py introuvable"

**Cause** : Fichier manquant dans le repo cloné

**Solution** :
```python
# Télécharger directement depuis GitHub
import urllib.request
url = "https://raw.githubusercontent.com/stephanedenis/Panini-Research/main/semantic-primitives/notebooks/donnees_nsm.py"
urllib.request.urlretrieve(url, "/content/donnees_nsm.py")

# Ajouter au path
import sys
sys.path.insert(0, "/content")
```

---

### ❌ Erreur : "RuntimeError: CUDA out of memory"

**Cause** : GPU trop petit pour le modèle

**Solutions** :
1. **Changer GPU** : Runtime → Change runtime type → GPU type : A100
2. **Utiliser CPU** : Runtime → Change runtime type → Hardware : CPU
3. **Réduire batch size** : Modifier `batch_size=8` → `batch_size=4`

---

### ❌ Erreur : "Installation lente sur CPU"

**Cause** : Pas de GPU activé

**Solution** :
```python
# Vérifier GPU disponible
import torch
print(f"GPU disponible : {torch.cuda.is_available()}")
print(f"GPU name : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Aucun'}")
```

Si `False` → Activer GPU (voir étape 2️⃣)

---

## 📊 Comparaison Backends Colab

| Backend | VRAM | Gratuit | Temps | Qualité |
|---------|------|---------|-------|---------|
| **CPU** | N/A | ✅ Oui | ~10 min | ✅ Identique |
| **T4** | 15 Go | ✅ Oui | ~5 min | ✅ Identique |
| **L4** | 24 Go | ✅ Oui | ~4 min | ✅ Identique |
| **A100** | 40 Go | ❌ Pro ($10/mois) | ~3 min | ✅ Identique |
| **TPU v2** | N/A | ✅ Oui | ~6 min | ✅ Identique |

**Recommandation** :
- **Gratuit** : T4 ou L4 (meilleur rapport vitesse/coût)
- **Colab Pro** : A100 (si besoin absolue vitesse)

---

## 🔗 Liens Utiles

- **Notebook GitHub** : [NSM_SentenceBERT_Local.ipynb](https://github.com/stephanedenis/Panini-Research/blob/main/semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb)
- **Données NSM** : [donnees_nsm.py](https://github.com/stephanedenis/Panini-Research/blob/main/semantic-primitives/notebooks/donnees_nsm.py)
- **Sentence-BERT Docs** : [sbert.net](https://www.sbert.net/)
- **Colab GPU Quotas** : [FAQ](https://research.google.com/colaboratory/faq.html)

---

## ✅ Validation Finale

Après exécution complète, vous devriez voir :

```
✅ 61 primitives NSM chargées
✅ 20 carrés sémiotiques chargés
✅ 105 phrases corpus chargées
✅ Modèle Sentence-BERT chargé
✅ Embeddings calculés (61 primitives)
✅ Dendrogramme généré
✅ Matrice similarités calculée
✅ Projection t-SNE générée
✅ Carrés sémiotiques analysés
```

🎉 **Notebook fonctionnel à 100% !**

---

## 📝 Support

Si problèmes persistent :

1. **Exécuter cellule diagnostic** (Cellule 3)
2. **Vérifier messages d'erreur**
3. **Consulter section Dépannage** ci-dessus
4. **Ouvrir issue GitHub** : [Panini-Research/issues](https://github.com/stephanedenis/Panini-Research/issues)

---

**Date mise à jour** : 2024-11-12  
**Version notebook** : 1.2  
**Tests validés** : ✅ T4, ✅ L4, ✅ A100, ✅ CPU
