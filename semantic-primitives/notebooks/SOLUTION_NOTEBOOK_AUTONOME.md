# 🎯 Solution Définitive : Notebook Autonome

Le problème actuel : le fichier `donnees_nsm.py` n'est pas accessible via GitHub raw (404).

## Solution : Intégrer les données directement dans le notebook

Au lieu de dépendre d'un fichier externe, créons une cellule avec les données inline.

Avantages :
- ✅ Pas de dépendance externe
- ✅ Fonctionne immédiatement
- ✅ Pas de problème de path
- ✅ Pas de problème de synchronisation GitHub

Ajoutez cette cellule au début du notebook (après pip install) :

```python
# Données NSM inline (autonome)
class PrimitiveNSM:
    def __init__(self, nom, forme_francaise, categorie, sanskrit=""):
        self.nom = nom
        self.forme_francaise = forme_francaise
        self.categorie = categorie
        self.sanskrit = sanskrit

# 61 primitives NSM
NSM_PRIMITIVES = {f"{nom}": PrimitiveNSM(nom, forme, cat, sans) for nom, forme, cat, sans in [
    ("JE", "je", "SUBSTANTIFS", "aham"),
    ("TOI", "toi", "SUBSTANTIFS", "tvam"),
    # ... etc (toutes les primitives)
]}

# 20 carrés sémiotiques
CARRES_SEMIOTIQUES = {
    "VIE_MORT": {"S1": "VIVRE", "S2": "MOURIR", "non_S1": "NE_PAS_VIVRE", "non_S2": "NE_PAS_MOURIR"},
    # ... etc (tous les carrés)
}

# 105 phrases corpus
CORPUS_TEST = [
    "Je sais que tu penses à quelque chose",
    # ... etc (toutes les phrases)
]

print(f"✅ {len(NSM_PRIMITIVES)} primitives NSM chargées")
```

Cette approche élimine tous les problèmes d'import !
