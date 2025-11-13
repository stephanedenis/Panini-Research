# 📓 Journal Automatique - 2025-11-13

**Host**: hauru  
**Début session**: 2025-11-13T00:31:10-05:00  
**Système**: Journalisation automatique via Git hooks

---


## [00:31:10] Commit `777974cb`

**Message**: feat: NSM SentenceBERT notebook + Reverse Engineering analysis

✅ NSM_SentenceBERT_Local.ipynb: Production-ready notebook
   - 27 cells, 80/80 primitives, 20 carrés sémiotiques
   - Hypothèses H1-H3 testées (résultats: réfutées)
   - Colab A100 ready avec instructions détaillées

✅ NSM_Reverse_Engineering_Analysis.ipynb: Deep analysis
   - 4 analyses systématiques (layer-wise, attention, probing, multi-model)
   - Examine pourquoi hypothèses réfutées via poids modèles
   - Visualisations: silhouette scores, entropy, t-SNE, probing accuracy
   - Support: SentenceBERT, Qwen-2.5, Llama-3, Mistral-7B

**Hash complet**: `777974cba4cb8004d90cb1507a38296f74c3258c`

### Fichiers modifiés

```
A	semantic-primitives/notebooks/NSM_Reverse_Engineering_Analysis.ipynb
```

### Statistiques

```
commit 777974cba4cb8004d90cb1507a38296f74c3258c
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:31:10 2025 -0500

    feat: NSM SentenceBERT notebook + Reverse Engineering analysis
    
    ✅ NSM_SentenceBERT_Local.ipynb: Production-ready notebook
       - 27 cells, 80/80 primitives, 20 carrés sémiotiques
       - Hypothèses H1-H3 testées (résultats: réfutées)
       - Colab A100 ready avec instructions détaillées
    
    ✅ NSM_Reverse_Engineering_Analysis.ipynb: Deep analysis
       - 4 analyses systématiques (layer-wise, attention, probing, multi-model)
       - Examine pourquoi hypothèses réfutées via poids modèles
       - Visualisations: silhouette scores, entropy, t-SNE, probing accuracy
       - Support: SentenceBERT, Qwen-2.5, Llama-3, Mistral-7B

 .../NSM_Reverse_Engineering_Analysis.ipynb         | 754 +++++++++++++++++++++
 1 file changed, 754 insertions(+)
```

---


## [00:34:39] Commit `347ec8f2`

**Message**: fix: Optimiser notebooks pour GitHub (outputs nettoyés)

✅ NSM_SentenceBERT_Local.ipynb: 27 cellules, métadonnées simplifiées
✅ NSM_Reverse_Engineering_Analysis.ipynb: 26 cellules, métadonnées simplifiées
🎯 Notebooks maintenant compatibles avec le viewer GitHub

**Hash complet**: `347ec8f295ea39000284b30bd28e4f936ff5c661`

### Fichiers modifiés

```
M	semantic-primitives/notebooks/NSM_Reverse_Engineering_Analysis.ipynb
M	semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb
```

### Statistiques

```
commit 347ec8f295ea39000284b30bd28e4f936ff5c661
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:34:39 2025 -0500

    fix: Optimiser notebooks pour GitHub (outputs nettoyés)
    
    ✅ NSM_SentenceBERT_Local.ipynb: 27 cellules, métadonnées simplifiées
    ✅ NSM_Reverse_Engineering_Analysis.ipynb: 26 cellules, métadonnées simplifiées
    🎯 Notebooks maintenant compatibles avec le viewer GitHub

 .../notebooks/NSM_Reverse_Engineering_Analysis.ipynb           | 10 ++++++++--
 semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb     | 10 ++++++++--
 2 files changed, 16 insertions(+), 4 deletions(-)
```

---


## [00:39:39] Commit `45f62cf8`

**Message**: fix: Simplifier installation packages (retirer numpy explicite)

✅ Évite conflits de dépendances numpy avec Colab
✅ Packages nécessaires installés automatiquement
🎯 Suppression warnings pip inutiles

**Hash complet**: `45f62cf8681320502454b77e8b0d4b749f123fff`

### Fichiers modifiés

```
M	semantic-primitives/notebooks/NSM_Reverse_Engineering_Analysis.ipynb
```

### Statistiques

```
commit 45f62cf8681320502454b77e8b0d4b749f123fff
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:39:39 2025 -0500

    fix: Simplifier installation packages (retirer numpy explicite)
    
    ✅ Évite conflits de dépendances numpy avec Colab
    ✅ Packages nécessaires installés automatiquement
    🎯 Suppression warnings pip inutiles

 .../notebooks/NSM_Reverse_Engineering_Analysis.ipynb                | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)
```

---


## [00:41:50] Commit `e6f5fa93`

**Message**: fix: Conversion types numpy en types Python pour JSON

✅ bool() pour booléens numpy
✅ int() pour entiers numpy
✅ float() déjà présent
🎯 Résout TypeError: Object of type bool is not JSON serializable

**Hash complet**: `e6f5fa9324561f1a8bd13e2406377791d21e49c0`

### Fichiers modifiés

```
M	semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb
```

### Statistiques

```
commit e6f5fa9324561f1a8bd13e2406377791d21e49c0
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:41:50 2025 -0500

    fix: Conversion types numpy en types Python pour JSON
    
    ✅ bool() pour booléens numpy
    ✅ int() pour entiers numpy
    ✅ float() déjà présent
    🎯 Résout TypeError: Object of type bool is not JSON serializable

 semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb | 14 +++++++-------
 1 file changed, 7 insertions(+), 7 deletions(-)
```

---


## [00:42:44] Commit `ada73ecc`

**Message**: fix: Résoudre conflit binaire numpy sur Colab

✅ Upgrade numpy avant installation autres packages
✅ Ajout scipy explicite (dépendance scikit-learn)
⚠️ Message utilisateur: redémarrer runtime si erreur persiste
🎯 Résout ValueError: numpy.dtype size changed

**Hash complet**: `ada73ecc0d70d8578a8bd013dd29fd4d4215d7af`

### Fichiers modifiés

```
M	semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb
```

### Statistiques

```
commit ada73ecc0d70d8578a8bd013dd29fd4d4215d7af
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:42:44 2025 -0500

    fix: Résoudre conflit binaire numpy sur Colab
    
    ✅ Upgrade numpy avant installation autres packages
    ✅ Ajout scipy explicite (dépendance scikit-learn)
    ⚠️ Message utilisateur: redémarrer runtime si erreur persiste
    🎯 Résout ValueError: numpy.dtype size changed

 semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
```

---


## [00:49:58] Commit `d9232d40`

**Message**: fix: Corriger URL GitHub donnees_nsm.py (retirer /research/)

✅ URL correcte: /main/semantic-primitives/... (pas /research/)
🔍 Cause: Repository GitHub root = research/ local
🎯 Résout 404 sur téléchargement direct donnees_nsm.py

**Hash complet**: `d9232d40f0508de33bc1905213be13838d0879aa`

### Fichiers modifiés

```
M	semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb
```

### Statistiques

```
commit d9232d40f0508de33bc1905213be13838d0879aa
Author: Stéphane Denis <stephane@sdenis.com>
Date:   Thu Nov 13 00:49:57 2025 -0500

    fix: Corriger URL GitHub donnees_nsm.py (retirer /research/)
    
    ✅ URL correcte: /main/semantic-primitives/... (pas /research/)
    🔍 Cause: Repository GitHub root = research/ local
    🎯 Résout 404 sur téléchargement direct donnees_nsm.py

 semantic-primitives/notebooks/NSM_SentenceBERT_Local.ipynb | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)
```

---

