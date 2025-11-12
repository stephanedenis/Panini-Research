# 🚀 Guide Rapide : Notebook Colab DeepSeek Analysis

**Fichier** : `DeepSeek_NSM_Real_API.ipynb`  
**Durée totale** : ~15-20 minutes avec Colab Pro GPU  
**Prérequis** : Clé API DeepSeek, Google One, Colab Pro

---

## ⚡ Démarrage Rapide (5 min)

### 1. Ouvrir le Notebook

**Option A - Depuis Google Drive** :
1. Uploader `DeepSeek_NSM_Real_API.ipynb` sur votre Google Drive
2. Clic droit → Ouvrir avec → Google Colaboratory
3. ✅ Le notebook s'ouvre dans Colab

**Option B - Depuis GitHub directement** :
1. Aller sur https://colab.research.google.com
2. File → Open notebook → GitHub
3. Entrer : `stephanedenis/Panini-Research`
4. Sélectionner : `semantic-primitives/notebooks/DeepSeek_NSM_Real_API.ipynb`
5. ✅ Le notebook s'ouvre

---

### 2. Activer GPU

🔧 **Configuration Runtime** :
1. Menu : `Runtime` → `Change runtime type`
2. Hardware accelerator : **GPU**
3. GPU type : **A100** (ou V100 si A100 indisponible)
4. Runtime shape : **High-RAM** (optionnel, pour corpus > 500 phrases)
5. Cliquer **Save**

⚠️ **Important** : Sans GPU, encodage sera 100x plus lent !

---

### 3. Configurer Clé API DeepSeek

🔑 **Stocker clé sécurisée** :

1. Obtenir clé API : https://platform.deepseek.com/api_keys
   - Se connecter / Créer compte
   - Générer nouvelle clé API
   - Copier clé (format : `sk-...`)

2. Dans Colab, cliquer icône **🔑 Secrets** (barre gauche)

3. Ajouter nouveau secret :
   - Name : `DEEPSEEK_API_KEY`
   - Value : `sk-votre-cle-api-ici`
   - ✅ Cocher **Notebook access**

4. Cliquer **Add**

✅ **Clé sécurisée** : Jamais visible dans code, jamais commitée sur GitHub

---

## 🏃 Exécution Complète (10-15 min)

### Exécuter Toutes les Cellules

**Méthode rapide** :
1. Menu : `Runtime` → `Run all`
2. ☕ Attendre 10-15 minutes
3. ✅ Résultats apparaissent au fur et à mesure

**Progression attendue** :

| Étape | Durée | Status |
|-------|-------|--------|
| Setup environnement | 1 min | Installations pip |
| Clone repo GitHub | 30 sec | Téléchargement code |
| Exp1 - Encodage primitives | 2-3 min | 60 primitives × API |
| Exp1 - t-SNE visualization | 1 min | Calcul GPU |
| Exp1 - Clustering | 30 sec | K-means |
| Exp2 - Carrés sémiotiques | 3-4 min | 20 carrés × 4 positions |
| Exp2 - Heatmap | 1 min | Visualisation |
| Exp3 - Corpus 105 phrases | 5-7 min | Encodage batch |
| Exp3 - Isotopies | 1 min | Corrélations PCA |
| Viz 3D interactive | 2-3 min | t-SNE 3D + Plotly |
| Sauvegarde résultats | 30 sec | JSON + NPY |
| **TOTAL** | **15-20 min** | ✅ |

---

## 📊 Résultats Attendus

### Fichiers Générés (Google Drive)

**Dossier** : `/MyDrive/Panini/DeepSeek_Analysis/`

```
DeepSeek_Analysis/
├── tsne_primitives_nsm_real.png          # t-SNE 2D primitives
├── heatmap_carres_real.png               # 20 carrés sémiotiques
├── viz_3d_interactive.html               # Visualisation 3D Plotly
├── resultats_deepseek_20251112_143052.json  # Métriques JSON
└── embeddings_primitives.npy             # Embeddings 4096-dim
```

---

### Métriques Clés

**Expérience 1 - Clustering** :
```
Pureté clustering    : 0.XXX (seuil > 0.7)
Silhouette score     : 0.XXX (seuil > 0.5)
→ H1 : VALIDÉE / RÉFUTÉE
```

**Expérience 2 - Carrés** :
```
Taux validation      : XX% (seuil > 70%)
Carrés valides       : X/20
→ H2 : VALIDÉE / RÉFUTÉE
```

**Expérience 3 - Isotopies** :
```
Isotopies r > 0.6    : X/Y
Variance PCA         : XX%
→ H3 : VALIDÉE / RÉFUTÉE
```

---

## 🎯 Interprétation Résultats

### Scénario 1 : Convergence Forte (3/3 hypothèses validées)

**Conclusion** : NSM-Greimas et DeepSeek capturent la même réalité sémantique

**Actions** :
- ✅ Rédiger publication majeure (Nature Cognitive Science)
- ✅ Valider universalité primitives NSM
- ✅ Développer modèles hybrides NSM-LLM

---

### Scénario 2 : Convergence Partielle (1-2/3 validées)

**Conclusion** : Modèles convergent sur aspects basiques, divergent sur structure

**Typiquement** :
- ✅ H3 validée : Isotopies individuelles détectables (JE, PAS, VOULOIR)
- ❌ H1 réfutée : Catégories NSM non-linéaires dans DeepSeek
- ❌ H2 réfutée : Carrés Greimas non-géométriques

**Actions** :
- 📊 Analyser divergences en détail
- 🔬 Expérience 4 : Reconstruction linéaire (probing tasks)
- 📝 Publication ACL/EMNLP : "Partial Convergence..."

---

### Scénario 3 : Divergence (0/3 validées)

**Conclusion** : NSM-Greimas et DeepSeek modélisent réalités différentes

**Explications possibles** :
1. NSM = sémantique cognitive (théorique)
2. DeepSeek = distribution statistique (empirique)
3. Dimensions complémentaires, pas identiques

**Actions** :
- 🔍 Tester autres modèles (GPT-4, Claude, Gemini)
- 📚 Revisiter théorie NSM (extension primitives ?)
- 🧪 Expériences neurosciences (fMRI vs DeepSeek)

---

## 🔧 Troubleshooting

### Erreur : "Clé API non trouvée"

```
❌ Erreur : Clé API non trouvée dans secrets Colab
```

**Solution** :
1. Vérifier secret `DEEPSEEK_API_KEY` existe (🔑 barre gauche)
2. Vérifier "Notebook access" activé
3. Redémarrer runtime : `Runtime` → `Restart runtime`

---

### Erreur : "GPU not available"

```
⚠️ Pas de GPU détecté
```

**Solution** :
1. `Runtime` → `Change runtime type`
2. Hardware accelerator : **GPU**
3. Si "None available" → Attendre (quota Colab Pro)
4. Alternative : CPU (100x plus lent, ~3h au lieu de 15 min)

---

### Erreur : "Out of memory"

```
RuntimeError: CUDA out of memory
```

**Solution** :
1. `Runtime` → `Change runtime type` → Runtime shape : **High-RAM**
2. Réduire taille corpus (100 phrases au lieu de 1000)
3. Redémarrer runtime : `Runtime` → `Restart runtime`

---

### Erreur : "API rate limit"

```
RateLimitError: Too many requests
```

**Solution** :
1. Attendre 60 secondes
2. Relancer cellule problématique
3. Si persiste : Passer en mode simulation (config.api_key = None)

---

## 💰 Coûts Estimés

### DeepSeek API

**Tarifs** (novembre 2025) :
- Input : $0.14 / 1M tokens
- Output : $0.28 / 1M tokens

**Estimation notebook complet** :
- Exp1 (60 primitives) : ~10K tokens → $0.004
- Exp2 (20 carrés × 4) : ~20K tokens → $0.008
- Exp3 (105 phrases) : ~50K tokens → $0.014
- **TOTAL** : ~**$0.03** (3 centimes) par exécution

**Gratuit** : 2M tokens/jour (= ~70 exécutions notebook/jour)

---

### Colab Pro

**Abonnement** : $9.99/mois (déjà payé)

**Inclus** :
- GPU A100/V100 illimité
- 52 GB RAM
- 24h runtime
- Background execution

**Coût marginal notebook** : $0 (inclus abonnement)

---

## 🚀 Extensions Possibles

### 1. Corpus Étendu (1000+ phrases)

Charger corpus large depuis Drive :

```python
# Dans nouvelle cellule
corpus_large = pd.read_csv('/content/drive/MyDrive/Panini/corpus_1000p.csv')

analyse_large = analyseur.analyser_isotopies_corpus(
    corpus_large['phrase'].tolist(),
    nom_corpus="Corpus Large (1000 phrases)"
)
```

**Durée** : +30 min (avec GPU A100)

---

### 2. Multi-Modèles Comparaison

Tester convergence avec autres LLMs :

```python
# GPT-4
from openai import OpenAI
client_gpt4 = OpenAI(api_key=userdata.get('OPENAI_API_KEY'))

# Claude
import anthropic
client_claude = anthropic.Anthropic(api_key=userdata.get('ANTHROPIC_API_KEY'))

# Comparer convergences
compare_models(['DeepSeek', 'GPT-4', 'Claude'], embeddings_primitives)
```

---

### 3. Fine-tuning NSM-GPT2

Créer modèle hybride interprétable :

```python
from transformers import GPT2LMHeadModel, Trainer

model = GPT2LMHeadModel.from_pretrained('gpt2')
model.add_module('nsm_layer', torch.nn.Linear(768, 61))

# Training 8h sur A100
trainer = Trainer(model=model, args=training_args, train_dataset=nsm_dataset)
trainer.train()
```

---

## 📅 Planning Recommandé

### Semaine 1 (Cette semaine)

**Lundi** :
- ✅ Setup notebook Colab
- ✅ Première exécution complète (mode simulation)
- ✅ Validation pipeline

**Mardi** :
- 🔑 Obtenir clé API DeepSeek
- 🚀 Exécution avec API réelle
- 📊 Analyser premiers résultats

**Mercredi-Jeudi** :
- 📚 Corpus étendu (1000 phrases)
- 🔬 Expérience 4 : Reconstruction linéaire
- 📈 Visualisations avancées

**Vendredi** :
- 📝 Mise à jour rapport avec résultats réels
- 🎯 Conclusions + implications
- 📧 Partager résultats équipe

---

### Semaine 2 (Semaine prochaine)

**Objectifs** :
- 🔄 Itérations basées sur résultats semaine 1
- 📊 Analyses complémentaires (probing tasks)
- 📝 Rédaction draft publication

---

## ✅ Checklist Pré-Exécution

Avant de lancer le notebook, vérifier :

- [ ] Colab Pro activé (GPU disponible)
- [ ] Google Drive avec espace libre > 1 GB
- [ ] Clé API DeepSeek obtenue et testée
- [ ] Secret `DEEPSEEK_API_KEY` configuré dans Colab
- [ ] Runtime type = GPU (A100 ou V100)
- [ ] Réseau stable (éviter interruptions)

---

## 🖥️ FAQ : Modèle Local vs API ?

**Q : Peut-on exécuter DeepSeek en local sur Colab ?**

**R : Oui (V2-Lite), mais API recommandée pour qualité/coût**

| Critère | API V3 ✅ | Local V2-Lite ⚠️ |
|---------|-----------|------------------|
| Setup | 30 sec | 1h |
| Qualité | 685B params | 16B params |
| Vitesse | 15 min | 30 min+ |
| Coût | $0.03/run | $0 (setup 1h) |
| RAM | 2 GB | 32 GB |

**Recommandation** : **API pour résultats publiables**

📄 **Analyse complète** : Voir [`DEEPSEEK_LOCAL_VS_API.md`](../docs/DEEPSEEK_LOCAL_VS_API.md)

---

## 🎓 Ressources Supplémentaires

**Documentation** :
- DeepSeek API : https://platform.deepseek.com/docs
- Colab Pro : https://colab.research.google.com/signup
- NSM Theory : Wierzbicka (1996) "Semantics: Primes and Universals"
- Greimas : "Sémantique structurale" (1966)
- **Comparaison Local/API** : [`DEEPSEEK_LOCAL_VS_API.md`](../docs/DEEPSEEK_LOCAL_VS_API.md)

**Support** :
- Issues GitHub : https://github.com/stephanedenis/Panini-Research/issues
- Email : stephane@sdenis.com

---

**Dernière mise à jour** : 12 novembre 2025  
**Version notebook** : 1.0  
**Auteur** : Panini Research - Semantic Primitives Team

---

## 🚀 Lancement Immédiat

**Prêt ?** Cliquez ici pour ouvrir directement dans Colab :

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/stephanedenis/Panini-Research/blob/main/semantic-primitives/notebooks/DeepSeek_NSM_Real_API.ipynb)

**Durée totale estimée** : 15-20 minutes  
**Résultats** : 5 visualisations + données JSON + embeddings NPY

✅ Prêt pour publication ACL 2026 !
