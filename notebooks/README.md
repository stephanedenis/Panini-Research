# 🔬 Notebooks de Recherche - Projet Panini

**Date de création**: 2025-11-12

## 🎯 Objectif

Ce dossier contient les **notebooks Jupyter de recherche locale** utilisés pour l'expérimentation, le prototypage et l'analyse exploratoire.

⚠️ **Distinction importante**: 
- `/notebooks/` → Notebooks Colab (jobs système automatisés)
- `/research/notebooks/` → Notebooks locaux (expérimentation)

## 📁 Structure

```
research/notebooks/
├── README.md                                    # Ce fichier
├── Panini_Ecosystem_Coherence_Audit.ipynb      # Audit cohérence écosystème
├── debug_notebook_local.ipynb                  # Debug et tests locaux
└── ...                                          # Autres notebooks recherche
```

## 🔧 Notebooks Disponibles

### Audit et Analyse
- **Panini_Ecosystem_Coherence_Audit.ipynb**: Analyse cohérence inter-modules

### Debug et Tests
- **debug_notebook_local.ipynb**: Tests et debugging environnement local

## 🚀 Utilisation

### Lancer un Notebook

```bash
# Depuis la racine du projet
cd research/notebooks
jupyter notebook nom_du_notebook.ipynb
```

### Environnement Virtuel

```bash
# Activer l'environnement virtuel si nécessaire
source .venv/bin/activate

# Installer Jupyter si pas déjà fait
pip install jupyter notebook ipykernel
```

### Kernels Python

Les notebooks utilisent le kernel Python configuré pour le projet:

```bash
# Vérifier les kernels disponibles
jupyter kernelspec list

# Ajouter le kernel du projet si nécessaire
python -m ipykernel install --user --name=panini --display-name="Python (Panini)"
```

## 📝 Conventions

### Nommage
- Format: `{domaine}_{description}.ipynb`
- Exemples:
  - `dhatu_analysis_phonetic.ipynb`
  - `corpus_validation_multilingual.ipynb`
  - `performance_benchmark_tokenizer.ipynb`

### Structure d'un Notebook
1. **Cellule 1**: Titre et description
2. **Cellule 2**: Imports et configuration
3. **Cellule 3+**: Code et analyse
4. **Dernière cellule**: Résumé et conclusions

### Metadata
Chaque notebook doit inclure en début:
```markdown
# Titre du Notebook

**Date**: YYYY-MM-DD
**Auteur**: Nom
**Objectif**: Description courte
**Statut**: [Exploration|En cours|Validé|Archivé]
```

## ⚠️ Bonnes Pratiques

### À FAIRE ✅
- Documenter chaque cellule avec des commentaires clairs
- Inclure des visualisations pour les résultats
- Sauvegarder les résultats importants (JSON, CSV)
- Versionner les notebooks significatifs
- Nettoyer les outputs avant commit (si volumineux)

### À ÉVITER ❌
- Chemins absolus hardcodés
- Données sensibles en clair
- Outputs de plusieurs MB dans le notebook
- Code non documenté ou cryptique
- Dépendances non documentées

## 🔄 Workflow Recherche → Production

### 1. Expérimentation (Notebook)
```python
# Prototype dans research/notebooks/
# Tests rapides, itérations
```

### 2. Validation (Notebook propre)
```python
# Notebook nettoyé et documenté
# Résultats reproductibles
```

### 3. Migration (Code Python)
```python
# Extraction du code validé
# Intégration dans src/
# Tests unitaires
```

## 📊 Gestion des Résultats

### Sauvegarde
```python
import json
from datetime import datetime

results = {...}

# Sauvegarder dans data/
output_file = f"data/experiment_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)
```

### Visualisations
```python
import matplotlib.pyplot as plt

# Sauvegarder les figures
fig.savefig(f"research/figures/experiment_{name}.png", dpi=300)
```

## 🔗 Ressources

### Documentation
- Guide Jupyter: https://jupyter.org/documentation
- IPython: https://ipython.readthedocs.io/

### Outils Complémentaires
- **nbconvert**: Conversion notebooks → Python/HTML/PDF
- **papermill**: Exécution automatisée notebooks
- **nbdime**: Diff/merge notebooks dans Git

### Extensions Utiles
- **Variable Inspector**: Inspection variables
- **ExecuteTime**: Temps d'exécution cellules
- **Table of Contents**: Navigation notebook

## 📝 Historique

| Date       | Action                           | Auteur    |
|------------|----------------------------------|-----------|
| 2025-11-12 | Migration notebooks depuis modules/ | Système   |
| 2025-11-12 | Création structure research/notebooks/ | Système   |

## 🔗 Documentation Connexe

- Notebooks Colab: `/notebooks/`
- Code source: `/src/`
- Documentation: `/docs/`
- Résultats: `/data/`

---

**Maintenu par**: Équipe Panini  
**Dernière mise à jour**: 2025-11-12
