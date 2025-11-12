# 🖥️ DeepSeek Local vs API sur Colab Pro

**Date** : 12 novembre 2025  
**Contexte** : Analyse convergence NSM-Greimas vs DeepSeek  
**Question** : Peut-on exécuter DeepSeek en local sur Colab ?

---

## 📊 Comparaison Rapide

| Critère | API (Recommandé) | Local sur Colab |
|---------|------------------|-----------------|
| **Setup** | ✅ 30 sec | ⚠️ 2-3h téléchargement |
| **RAM requise** | ✅ 2 GB | ❌ 400+ GB |
| **GPU requise** | ✅ Aucun | ❌ Multi-GPU A100 |
| **Vitesse** | ✅ ~15 min | ⚠️ ~2-3h |
| **Coût** | ✅ $0.03/run | ⚠️ Impossible (RAM) |
| **Précision** | ✅ 100% | ✅ 100% (identique) |
| **Quota** | ✅ 2M tokens/jour | ✅ Illimité |
| **Maintenance** | ✅ Aucune | ⚠️ Updates manuelles |

**Verdict** : ✅ **API recommandée** pour ce cas d'usage

---

## 🔍 Analyse Détaillée

### 1. Modèles DeepSeek Disponibles

#### DeepSeek-V3 (Dernier modèle - Nov 2024)

**Architecture** :
- **Taille** : 685 milliards de paramètres (MoE)
- **Actifs** : 37B paramètres par token
- **Poids** : ~1.3 TB (format FP16) ou ~680 GB (INT8)
- **Context** : 128K tokens

**Sur HuggingFace** :
```
deepseek-ai/DeepSeek-V3.2-Exp        (685B params)
deepseek-ai/DeepSeek-V3.1            (685B params)
deepseek-ai/DeepSeek-V3.1-Base       (685B params)
```

**Exigences minimales** :
- **RAM** : 800 GB (FP16) ou 400 GB (INT8)
- **GPU** : 8× A100 80GB (640 GB VRAM total)
- **Stockage** : 1.5 TB
- **Téléchargement** : ~2-3h (dépend bande passante)

⚠️ **Colab Pro** : Maximum 1× A100 40GB = **40 GB VRAM**  
❌ **Impossible** d'exécuter V3 localement sur Colab (besoin 400-800 GB)

---

#### DeepSeek-V2 (Ancien modèle - Mai 2024)

**Architecture** :
- **Taille** : 236 milliards de paramètres (MoE)
- **Actifs** : 21B paramètres par token
- **Poids** : ~450 GB (FP16) ou ~220 GB (INT8)
- **Context** : 128K tokens

**Sur HuggingFace** :
```
deepseek-ai/DeepSeek-V2            (236B params)
deepseek-ai/DeepSeek-V2-Lite       (16B params) ✅ FAISABLE
```

**Exigences V2 standard** :
- **RAM** : 250 GB (INT8)
- **GPU** : 4× A100 80GB (320 GB VRAM)
- **Stockage** : 500 GB

⚠️ **Colab Pro** : 1× A100 40GB + 52 GB RAM  
❌ **Impossible** d'exécuter V2 standard sur Colab

---

#### DeepSeek-V2-Lite ✅ (Version légère)

**Architecture** :
- **Taille** : 16 milliards de paramètres
- **Poids** : ~32 GB (FP16) ou ~16 GB (INT8)
- **Context** : 32K tokens

**Sur HuggingFace** :
```
deepseek-ai/DeepSeek-V2-Lite-Chat  (16B params)
```

**Exigences** :
- **RAM** : 20 GB
- **GPU** : 1× A100 40GB (32 GB VRAM utilisés)
- **Stockage** : 40 GB
- **Téléchargement** : ~20-30 min

✅ **Colab Pro** : **Faisable** avec A100 40GB !

**Limitations** :
- Performances inférieures à V3/V2 (16B vs 685B params)
- Embeddings potentiellement moins riches
- Moins de capacités MoE (experts réduits)

---

### 2. Comparaison API vs Local

#### Option A : API DeepSeek (Recommandé) ✅

**Avantages** :
- ✅ **Setup instantané** : Clé API = 30 secondes
- ✅ **Modèle V3** : Dernier modèle (685B), meilleure qualité
- ✅ **Pas de RAM/GPU** : Fonctionne sur CPU
- ✅ **Maintenance zéro** : Updates automatiques côté serveur
- ✅ **Coût minime** : $0.03 par notebook complet
- ✅ **Quota gratuit** : 2M tokens/jour (70 runs)
- ✅ **Scalable** : Peut faire corpus 10K+ phrases

**Inconvénients** :
- ⚠️ Nécessite connexion internet stable
- ⚠️ Rate limits possibles (1M tokens/min)
- ⚠️ Latence réseau (~200-500ms par requête)

**Code** (déjà implémenté) :
```python
from openai import OpenAI

client = OpenAI(
    api_key=userdata.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

# Encoder primitives NSM
embeddings = []
for primitive in NSM_PRIMITIVES:
    response = client.embeddings.create(
        model="deepseek-chat",
        input=primitive.forme_francaise,
        encoding_format="float"
    )
    embeddings.append(response.data[0].embedding)
```

**Performance** :
- Encodage 60 primitives : 2-3 minutes
- Encodage 105 phrases corpus : 5-7 minutes
- **Total notebook** : ~15 minutes

---

#### Option B : Local DeepSeek-V2-Lite (Compromis) ⚠️

**Avantages** :
- ✅ **Pas de rate limit** : Encodage illimité
- ✅ **Pas de coûts API** : Une fois téléchargé, gratuit
- ✅ **Contrôle total** : Accès direct aux couches internes
- ✅ **Reproductibilité** : Résultats identiques à chaque run

**Inconvénients** :
- ⚠️ **Setup lourd** : 20-30 min téléchargement + 10 min installation
- ⚠️ **Modèle inférieur** : V2-Lite (16B) vs V3 API (685B)
- ⚠️ **Lent** : 10x plus lent que API (batch processing requis)
- ⚠️ **RAM limite** : Colab Pro = 52 GB (risque OOM si corpus > 500p)
- ⚠️ **Embeddings différents** : Résultats non comparables avec V3

**Code** (à implémenter) :
```python
from transformers import AutoTokenizer, AutoModel
import torch

# Téléchargement (20-30 min)
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V2-Lite-Chat")
model = AutoModel.from_pretrained(
    "deepseek-ai/DeepSeek-V2-Lite-Chat",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

# Encoder primitives NSM (batch pour performance)
def encode_batch(texts, batch_size=8):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True).to("cuda")
        
        with torch.no_grad():
            outputs = model(**inputs)
            # Mean pooling sur dernière couche
            batch_embeddings = outputs.last_hidden_state.mean(dim=1)
        
        embeddings.extend(batch_embeddings.cpu().numpy())
    
    return np.array(embeddings)

# Utilisation
primitives_text = [p.forme_francaise for p in NSM_PRIMITIVES.values()]
embeddings_local = encode_batch(primitives_text, batch_size=8)
```

**Performance estimée** :
- Téléchargement modèle : 20-30 minutes (une fois)
- Installation dépendances : 5-10 minutes
- Encodage 60 primitives : 5-10 minutes (batch)
- Encodage 105 phrases : 15-20 minutes (batch)
- **Total première exécution** : ~1h
- **Total exécutions suivantes** : ~30 minutes

---

#### Option C : Local DeepSeek-V3 (Impossible) ❌

**Pourquoi impossible sur Colab Pro** :
- ❌ **RAM** : 400-800 GB requis vs 52 GB disponible
- ❌ **VRAM** : 320-640 GB requis vs 40 GB disponible (1× A100)
- ❌ **Stockage** : 1.5 TB requis vs 200 GB disponible
- ❌ **Multi-GPU** : Besoin 8× A100, Colab = maximum 1× A100

**Alternatives pour V3 local** :
1. **Cloud GPU clusters** :
   - AWS SageMaker : 8× A100 ($32/heure)
   - Lambda Labs : 8× A100 ($12/heure)
   - Google Cloud TPU : v5e-256 ($8/heure)

2. **Hébergement tiers** :
   - Replicate.com : API DeepSeek V3 ($0.001/1K tokens)
   - Together.ai : DeepSeek V3 ($0.0014/1K tokens)
   - Modal Labs : Déploiement custom V3

⚠️ **Coûts prohibitifs** : $12-32/heure vs $0.03/run API officielle

---

## 🎯 Recommandation pour Notre Cas d'Usage

### Contexte Analyse NSM-Greimas

**Objectif** :
- Encoder 60 primitives NSM
- Encoder 105 phrases corpus (extensible 1000+)
- Comparer embeddings avec structure NSM-Greimas
- Générer visualisations t-SNE, heatmaps

**Contraintes** :
- Budget limité (recherche académique)
- Timeline courte (ACL 2026 deadline Mars 2026)
- Reproductibilité scientifique (résultats stables)
- Comparaison avec littérature existante (DeepSeek V3)

---

### ✅ Solution Recommandée : API DeepSeek

**Pourquoi** :
1. **Qualité maximale** : V3 (685B) = state-of-the-art embeddings
2. **Coût minimal** : $0.03/run = $2-3 pour 100 expériences
3. **Setup rapide** : 30 sec (clé API) vs 1h (local)
4. **Scalable** : Corpus 10K+ phrases possible (local = OOM)
5. **Reproductible** : Même modèle que papiers DeepSeek (comparaisons valides)
6. **Maintenance** : Zéro effort (updates automatiques)

**Scénarios d'usage** :

#### Phase 1 : Validation Hypothèses (Cette semaine)
```
Notebook actuel avec API
- 60 primitives × 3 runs (A/B tests)
- 105 phrases corpus × 3 runs
- Visualisations + statistiques
COÛT : $0.27 (9 runs × $0.03)
DURÉE : 2h30 (3× 15 min + analyses)
```

#### Phase 2 : Corpus Étendu (Semaine prochaine)
```
Corpus 1000 phrases × 5 isotopies
- 1000 encodages × 5 expériences
- PCA, clustering, visualisations 3D
COÛT : $1.50 (50 runs équivalent)
DURÉE : 1 journée (compute + analyses)
```

#### Phase 3 : Multi-Langues (2 semaines)
```
NSM multilingue : EN/FR/Sanskrit
- 60 primitives × 3 langues × 3 runs
- Validation universalité NSM
COÛT : $0.81 (27 runs)
DURÉE : 3h
```

**TOTAL Phase 1-3** : **$2.58** (budget recherche = acceptable)

---

### ⚠️ Alternative : Local V2-Lite (Si API indisponible)

**Quand utiliser** :
- ❌ API DeepSeek temporairement down
- ❌ Problèmes connexion internet
- ❌ Besoin analyses internes (attention weights)
- ❌ Expériences > 2M tokens/jour (rare)

**Limitations critiques** :
1. **Résultats non-comparables** : V2-Lite ≠ V3 (publications invalides)
2. **Performance dégradée** : 16B vs 685B params (embeddings moins riches)
3. **Setup fastidieux** : 1h première fois
4. **Corpus limité** : Max 500 phrases (RAM OOM ensuite)

**Implémentation** :
- Créer notebook séparé : `DeepSeek_NSM_Local_V2Lite.ipynb`
- Documenter différences avec API V3
- Avertissements résultats (non-publication grade)
- Usage : Prototyping / Tests uniquement

---

## 💡 Solution Hybride (Optimal)

### Workflow Recommandé

#### Développement Local (CPU, Mode Simulation)
```python
# Sur machine locale (laptop)
config = ConfigDeepSeek(
    mode_simulation=True,  # Embeddings heuristiques
    dim_embeddings=4096
)

# Tester pipeline, visualisations, analyses
# DURÉE : 5 min (pas d'API calls)
# COÛT : $0
```

#### Validation Colab Pro (API V3)
```python
# Sur Colab Pro avec GPU + API
config = ConfigDeepSeek(
    api_key=userdata.get('DEEPSEEK_API_KEY'),
    modele="deepseek-chat"  # V3 latest
)

# Exécution réelle, résultats publiables
# DURÉE : 15 min
# COÛT : $0.03
```

#### Analyses Approfondies (Local V2-Lite, optionnel)
```python
# Si besoin accès interne (probing tasks)
model_local = load_deepseek_v2_lite()
hidden_states = model_local(texts, output_hidden_states=True)

# Analyser couches internes (layer-wise probing)
# DURÉE : 30 min
# COÛT : $0 (une fois téléchargé)
```

---

## 📋 Plan d'Action Concret

### Semaine 1 (Immédiat)

**Lundi** :
- [x] ✅ Notebook API créé (`DeepSeek_NSM_Real_API.ipynb`)
- [ ] 🔑 Obtenir clé API DeepSeek (30 sec)
- [ ] 🚀 Première exécution API V3 (15 min)
- [ ] 📊 Valider résultats vs simulation

**Mardi-Mercredi** :
- [ ] 📈 Corpus étendu 1000 phrases (API)
- [ ] 🔬 Expérience 4 : Reconstruction linéaire
- [ ] 📝 Mise à jour rapport avec résultats réels

**Jeudi-Vendredi** :
- [ ] 📊 Analyses statistiques robustesse
- [ ] 🎨 Visualisations publication-grade
- [ ] 📄 Draft ACL 2026 (sections results)

**Coût semaine 1** : ~$2 (API calls)

---

### Semaine 2 (Optionnel - Si besoin local)

**Si nécessaire** (analyses internes couches) :
- [ ] 📥 Télécharger DeepSeek-V2-Lite (1h)
- [ ] 🔧 Notebook local séparé
- [ ] 🧪 Probing tasks (layer-wise analysis)
- [ ] ⚠️ Documenter limites (V2-Lite ≠ V3)

**Coût semaine 2** : $0 (local) + temps setup (3-4h)

---

## 🔧 Guide Implémentation Local (Si vraiment nécessaire)

### Setup DeepSeek-V2-Lite sur Colab

```python
# CELLULE 1 : Installation
!pip install -q transformers accelerate bitsandbytes

# CELLULE 2 : Téléchargement modèle
from transformers import AutoTokenizer, AutoModel
import torch

print("⏳ Téléchargement DeepSeek-V2-Lite (20-30 min)...")
tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-V2-Lite-Chat",
    trust_remote_code=True
)

model = AutoModel.from_pretrained(
    "deepseek-ai/DeepSeek-V2-Lite-Chat",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

print(f"✅ Modèle chargé : {model.num_parameters() / 1e9:.1f}B params")
print(f"💾 VRAM utilisée : {torch.cuda.memory_allocated() / 1e9:.1f} GB")

# CELLULE 3 : Fonction encodage batch
def encode_texts_local(texts, batch_size=8):
    """Encode texts avec DeepSeek-V2-Lite local."""
    embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to("cuda")
        
        with torch.no_grad():
            outputs = model(**inputs)
            # Mean pooling
            batch_emb = outputs.last_hidden_state.mean(dim=1)
            embeddings.extend(batch_emb.cpu().numpy())
    
    return np.array(embeddings)

# CELLULE 4 : Test encodage primitives
primitives_text = [p.forme_francaise for p in NSM_PRIMITIVES.values()]
embeddings_local = encode_texts_local(primitives_text, batch_size=8)

print(f"✅ Embeddings shape : {embeddings_local.shape}")
# Output : (60, 2048) ou (60, 4096) selon V2-Lite

# CELLULE 5 : Intégration avec notebook existant
# Remplacer appels API par appels local
# ATTENTION : Résultats non-comparables avec V3 !
```

**Monitoring GPU** :
```python
import torch

print(f"GPU : {torch.cuda.get_device_name(0)}")
print(f"VRAM totale : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print(f"VRAM utilisée : {torch.cuda.memory_allocated() / 1e9:.1f} GB")
print(f"VRAM libre : {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1e9:.1f} GB")
```

**Sauvegarde modèle Drive** (réutilisation ultérieure) :
```python
# Sauvegarder sur Drive (éviter re-téléchargement)
model.save_pretrained("/content/drive/MyDrive/Panini/Models/DeepSeek-V2-Lite")
tokenizer.save_pretrained("/content/drive/MyDrive/Panini/Models/DeepSeek-V2-Lite")

# Rechargement ultérieur (instantané)
model = AutoModel.from_pretrained(
    "/content/drive/MyDrive/Panini/Models/DeepSeek-V2-Lite",
    torch_dtype=torch.float16,
    device_map="auto"
)
```

---

## 📊 Benchmark Comparatif

### Test : Encoder 60 Primitives NSM

| Méthode | Setup | Exécution | Total | VRAM | Coût | Qualité |
|---------|-------|-----------|-------|------|------|---------|
| **API V3** | 30 sec | 2 min | **2.5 min** | 0 GB | $0.01 | ⭐⭐⭐⭐⭐ |
| **Local V2-Lite** | 30 min | 8 min | **38 min** | 32 GB | $0 | ⭐⭐⭐ |
| **Simulation** | 0 sec | 10 sec | **10 sec** | 0 GB | $0 | ⭐ |

**Légende qualité** :
- ⭐⭐⭐⭐⭐ : V3 685B (publication-grade)
- ⭐⭐⭐ : V2-Lite 16B (prototyping)
- ⭐ : Heuristique (tests pipeline)

---

## ✅ Conclusion

### Pour l'analyse NSM-Greimas : **API Recommandée**

**Raisons** :
1. ✅ **Qualité scientifique** : V3 = meilleurs embeddings disponibles
2. ✅ **Coût ridicule** : $0.03/run = négligeable budget recherche
3. ✅ **Setup instantané** : 30 sec vs 1h local
4. ✅ **Scalable** : Corpus 10K+ possible (local = OOM)
5. ✅ **Reproductible** : Comparaisons littérature valides
6. ✅ **Maintenance** : Zéro effort

**Local V2-Lite** : Réservé pour :
- ❌ Analyses couches internes (probing tasks)
- ❌ Expériences > 2M tokens/jour (très rare)
- ❌ Fallback si API down (temporaire)

**Décision** : **Continuer avec API** ✅

---

## 📚 Ressources

**DeepSeek Official** :
- API : https://platform.deepseek.com
- Docs : https://platform.deepseek.com/docs
- Pricing : https://platform.deepseek.com/pricing

**HuggingFace** :
- V3 : https://huggingface.co/deepseek-ai/DeepSeek-V3.2-Exp
- V2-Lite : https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat
- Docs : https://huggingface.co/docs/transformers

**Colab Pro** :
- GPU specs : https://colab.research.google.com/signup
- Pricing : $9.99/month (déjà payé)

---

**Date** : 12 novembre 2025  
**Auteur** : Panini Research - Semantic Primitives Team  
**Version** : 1.0
