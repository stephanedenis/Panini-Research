#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Données NSM simplifiées pour notebook Sentence-BERT
Compatible avec la structure panlang/
"""

from typing import Dict, List

# Structure simplifiée des primitives NSM
class PrimitiveNSM:
    def __init__(self, nom: str, forme_francaise: str, categorie: str, sanskrit: str = ""):
        self.nom = nom
        self.forme_francaise = forme_francaise
        self.categorie = categorie
        self.sanskrit = sanskrit

# Import depuis nsm_primitives.py du panlang/
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))
    from nsm_primitives import NSM_PRIMITIVES as NSM_RAW
    
    # Conversion vers structure simplifiée
    NSM_PRIMITIVES = {}
    for nom, data in NSM_RAW.items():
        NSM_PRIMITIVES[nom] = PrimitiveNSM(
            nom=nom,
            forme_francaise=nom.lower().replace('_', ' '),
            categorie=data.get('category', 'AUTRE'),
            sanskrit=data.get('sanskrit', '')
        )
    
except ImportError:
    # Fallback: données en dur pour Colab
    NSM_PRIMITIVES = {
        # SUBSTANTIFS (13)
        "JE": PrimitiveNSM("JE", "je", "SUBSTANTIFS", "aham"),
        "TOI": PrimitiveNSM("TOI", "toi", "SUBSTANTIFS", "tvam"),
        "QUELQU_UN": PrimitiveNSM("QUELQU_UN", "quelqu'un", "SUBSTANTIFS", "kascit"),
        "QUELQUE_CHOSE": PrimitiveNSM("QUELQUE_CHOSE", "quelque chose", "SUBSTANTIFS", "kim-cit"),
        "GENS": PrimitiveNSM("GENS", "gens", "SUBSTANTIFS", "janāḥ"),
        "CORPS": PrimitiveNSM("CORPS", "corps", "SUBSTANTIFS", "śarīra"),
        "PARTIE": PrimitiveNSM("PARTIE", "partie", "SUBSTANTIFS", "bhāga"),
        "ESPECE": PrimitiveNSM("ESPECE", "espèce", "SUBSTANTIFS", "jāti"),
        "COTE": PrimitiveNSM("COTE", "côté", "SUBSTANTIFS", "pārśva"),
        "ENDROIT": PrimitiveNSM("ENDROIT", "endroit", "SUBSTANTIFS", "sthāna"),
        "MOMENT": PrimitiveNSM("MOMENT", "moment", "SUBSTANTIFS", "kṣaṇa"),
        "MAINTENANT": PrimitiveNSM("MAINTENANT", "maintenant", "SUBSTANTIFS", "adhunā"),
        "AVANT": PrimitiveNSM("AVANT", "avant", "SUBSTANTIFS", "purā"),
        
        # DETERMINANTS (4)
        "CE": PrimitiveNSM("CE", "ce", "DETERMINANTS", "ayam"),
        "LE_MEME": PrimitiveNSM("LE_MEME", "le même", "DETERMINANTS", "sama"),
        "UN_AUTRE": PrimitiveNSM("UN_AUTRE", "un autre", "DETERMINANTS", "anya"),
        "UN": PrimitiveNSM("UN", "un", "DETERMINANTS", "eka"),
        
        # QUANTIFICATEURS (3)
        "DEUX": PrimitiveNSM("DEUX", "deux", "QUANTIFICATEURS", "dvi"),
        "BEAUCOUP": PrimitiveNSM("BEAUCOUP", "beaucoup", "QUANTIFICATEURS", "bahu"),
        "TOUT": PrimitiveNSM("TOUT", "tout", "QUANTIFICATEURS", "sarva"),
        
        # ATTRIBUTS (5)
        "BON": PrimitiveNSM("BON", "bon", "ATTRIBUTS", "su"),
        "MAUVAIS": PrimitiveNSM("MAUVAIS", "mauvais", "ATTRIBUTS", "dur"),
        "GRAND": PrimitiveNSM("GRAND", "grand", "ATTRIBUTS", "mahā"),
        "PETIT": PrimitiveNSM("PETIT", "petit", "ATTRIBUTS", "alpa"),
        
        # PREDICATS MENTAUX (5)
        "PENSER": PrimitiveNSM("PENSER", "penser", "MENTAUX", "man"),
        "SAVOIR": PrimitiveNSM("SAVOIR", "savoir", "MENTAUX", "jñā"),
        "VOULOIR": PrimitiveNSM("VOULOIR", "vouloir", "MENTAUX", "iṣ"),
        "SENTIR": PrimitiveNSM("SENTIR", "sentir", "MENTAUX", "vedayate"),
        "VOIR": PrimitiveNSM("VOIR", "voir", "MENTAUX", "paś"),
        
        # PREDICATS DE PAROLE (3)
        "DIRE": PrimitiveNSM("DIRE", "dire", "PAROLE", "vac"),
        "MOT": PrimitiveNSM("MOT", "mot", "PAROLE", "śabda"),
        "VRAI": PrimitiveNSM("VRAI", "vrai", "PAROLE", "satya"),
        
        # ACTIONS (4)
        "FAIRE": PrimitiveNSM("FAIRE", "faire", "ACTIONS", "kṛ"),
        "ARRIVER": PrimitiveNSM("ARRIVER", "arriver", "ACTIONS", "bhū"),
        "BOUGER": PrimitiveNSM("BOUGER", "bouger", "ACTIONS", "gam"),
        "TOUCHER": PrimitiveNSM("TOUCHER", "toucher", "ACTIONS", "spṛś"),
        
        # EXISTENCE (3)
        "ETRE": PrimitiveNSM("ETRE", "être", "EXISTENCE", "as"),
        "EXISTER": PrimitiveNSM("EXISTER", "exister", "EXISTENCE", "bhū"),
        "VIVRE": PrimitiveNSM("VIVRE", "vivre", "EXISTENCE", "jīv"),
        
        # RELATIONS (7)
        "AVOIR": PrimitiveNSM("AVOIR", "avoir", "RELATIONS", "dhṛ"),
        "ETRE_DANS": PrimitiveNSM("ETRE_DANS", "être dans", "RELATIONS", "antar"),
        "ETRE_DE": PrimitiveNSM("ETRE_DE", "être de", "RELATIONS", "bhū"),
        "AU_DESSUS": PrimitiveNSM("AU_DESSUS", "au-dessus", "RELATIONS", "upari"),
        "EN_DESSOUS": PrimitiveNSM("EN_DESSOUS", "en dessous", "RELATIONS", "adhas"),
        "LOIN": PrimitiveNSM("LOIN", "loin", "RELATIONS", "dūra"),
        "PRES": PrimitiveNSM("PRES", "près", "RELATIONS", "samīpa"),
        
        # LOGIQUE (5)
        "PAS": PrimitiveNSM("PAS", "pas", "LOGIQUE", "na"),
        "PEUT_ETRE": PrimitiveNSM("PEUT_ETRE", "peut-être", "LOGIQUE", "syāt"),
        "POUVOIR": PrimitiveNSM("POUVOIR", "pouvoir", "LOGIQUE", "śak"),
        "PARCE_QUE": PrimitiveNSM("PARCE_QUE", "parce que", "LOGIQUE", "yatas"),
        "SI": PrimitiveNSM("SI", "si", "LOGIQUE", "yadi"),
        
        # AUGMENTEURS (3)
        "TRES": PrimitiveNSM("TRES", "très", "AUGMENTEURS", "ati"),
        "PLUS": PrimitiveNSM("PLUS", "plus", "AUGMENTEURS", "bhūyas"),
        "COMME": PrimitiveNSM("COMME", "comme", "AUGMENTEURS", "iva"),
    }

# Couleurs par catégorie (pour visualisation)
COULEURS_CATEGORIES = {
    "SUBSTANTIFS": "#FF6B6B",    # Rouge
    "DETERMINANTS": "#4ECDC4",   # Cyan
    "QUANTIFICATEURS": "#45B7D1", # Bleu clair
    "ATTRIBUTS": "#96CEB4",      # Vert
    "MENTAUX": "#FFEAA7",        # Jaune
    "PAROLE": "#DFE6E9",         # Gris clair
    "ACTIONS": "#FD79A8",        # Rose
    "EXISTENCE": "#A29BFE",      # Violet
    "RELATIONS": "#74B9FF",      # Bleu
    "LOGIQUE": "#FAB1A0",        # Orange
    "AUGMENTEURS": "#FDCB6E",    # Orange clair
    "TEMPS": "#E17055",          # Orange foncé
}

# Carrés sémiotiques Greimas (20 carrés)
CARRES_SEMIOTIQUES = {
    "VIE_MORT": {
        "S1": "VIVRE",      # Position S1
        "S2": "MOURIR",     # Position S2 (contraire)
        "non_S1": "NE_PAS_VIVRE",  # ~S1 (contradictoire)
        "non_S2": "NE_PAS_MOURIR", # ~S2 (contradictoire)
    },
    "SAVOIR_IGNORER": {
        "S1": "SAVOIR",
        "S2": "IGNORER",
        "non_S1": "NE_PAS_SAVOIR",
        "non_S2": "NE_PAS_IGNORER",
    },
    "VOULOIR_REFUSER": {
        "S1": "VOULOIR",
        "S2": "REFUSER",
        "non_S1": "NE_PAS_VOULOIR",
        "non_S2": "NE_PAS_REFUSER",
    },
    "FAIRE_SUBIR": {
        "S1": "FAIRE",
        "S2": "SUBIR",
        "non_S1": "NE_PAS_FAIRE",
        "non_S2": "NE_PAS_SUBIR",
    },
    "ETRE_PARAITRE": {
        "S1": "ETRE",
        "S2": "PARAITRE",
        "non_S1": "NE_PAS_ETRE",
        "non_S2": "NE_PAS_PARAITRE",
    },
    "BON_MAUVAIS": {
        "S1": "BON",
        "S2": "MAUVAIS",
        "non_S1": "PAS_BON",
        "non_S2": "PAS_MAUVAIS",
    },
    "GRAND_PETIT": {
        "S1": "GRAND",
        "S2": "PETIT",
        "non_S1": "PAS_GRAND",
        "non_S2": "PAS_PETIT",
    },
    "VOIR_CACHER": {
        "S1": "VOIR",
        "S2": "CACHER",
        "non_S1": "NE_PAS_VOIR",
        "non_S2": "NE_PAS_CACHER",
    },
    "PENSER_OUBLIER": {
        "S1": "PENSER",
        "S2": "OUBLIER",
        "non_S1": "NE_PAS_PENSER",
        "non_S2": "NE_PAS_OUBLIER",
    },
    "SENTIR_IGNORER": {
        "S1": "SENTIR",
        "S2": "IGNORER",
        "non_S1": "NE_PAS_SENTIR",
        "non_S2": "NE_PAS_IGNORER",
    },
    "DIRE_TAIRE": {
        "S1": "DIRE",
        "S2": "TAIRE",
        "non_S1": "NE_PAS_DIRE",
        "non_S2": "NE_PAS_TAIRE",
    },
    "VRAI_FAUX": {
        "S1": "VRAI",
        "S2": "FAUX",
        "non_S1": "PAS_VRAI",
        "non_S2": "PAS_FAUX",
    },
    "AVOIR_MANQUER": {
        "S1": "AVOIR",
        "S2": "MANQUER",
        "non_S1": "NE_PAS_AVOIR",
        "non_S2": "NE_PAS_MANQUER",
    },
    "BOUGER_RESTER": {
        "S1": "BOUGER",
        "S2": "RESTER",
        "non_S1": "NE_PAS_BOUGER",
        "non_S2": "NE_PAS_RESTER",
    },
    "PRES_LOIN": {
        "S1": "PRES",
        "S2": "LOIN",
        "non_S1": "PAS_PRES",
        "non_S2": "PAS_LOIN",
    },
    "DESSUS_DESSOUS": {
        "S1": "AU_DESSUS",
        "S2": "EN_DESSOUS",
        "non_S1": "PAS_AU_DESSUS",
        "non_S2": "PAS_EN_DESSOUS",
    },
    "MAINTENANT_AVANT": {
        "S1": "MAINTENANT",
        "S2": "AVANT",
        "non_S1": "PAS_MAINTENANT",
        "non_S2": "PAS_AVANT",
    },
    "UN_BEAUCOUP": {
        "S1": "UN",
        "S2": "BEAUCOUP",
        "non_S1": "PAS_UN",
        "non_S2": "PAS_BEAUCOUP",
    },
    "MEME_AUTRE": {
        "S1": "LE_MEME",
        "S2": "UN_AUTRE",
        "non_S1": "PAS_LE_MEME",
        "non_S2": "PAS_UN_AUTRE",
    },
    "TOUT_PARTIE": {
        "S1": "TOUT",
        "S2": "PARTIE",
        "non_S1": "PAS_TOUT",
        "non_S2": "PAS_PARTIE",
    },
}

# Corpus de test pour isotopies (105 phrases)
CORPUS_TEST = [
    # Isotopie SAVOIR/CONNAISSANCE (15 phrases)
    "Je sais que tu penses à quelque chose",
    "Les gens veulent savoir la vérité",
    "Il pense souvent à cet endroit",
    "Elle voit ce qui arrive maintenant",
    "Quelqu'un connaît cette personne",
    "Je pense que c'est vrai",
    "Tu sais ce que je veux dire",
    "Les gens pensent beaucoup à cela",
    "Il sait où se trouve cet endroit",
    "Elle voit tout ce qui se passe",
    "Quelqu'un pense la même chose",
    "Je sais que tu as raison",
    "Tu vois ce que je vois",
    "Les gens savent ce qui est bon",
    "Il pense que c'est possible",
    
    # Isotopie VOULOIR/DESIR (15 phrases)
    "Je veux faire quelque chose de bien",
    "Tu veux que les gens soient heureux",
    "Il veut aller à cet endroit",
    "Elle veut savoir la vérité",
    "Les gens veulent vivre bien",
    "Quelqu'un veut dire quelque chose",
    "Je veux que tu saches cela",
    "Tu veux faire comme moi",
    "Il veut avoir beaucoup de choses",
    "Elle veut être près de toi",
    "Les gens veulent que ça arrive",
    "Quelqu'un veut toucher ce corps",
    "Je veux voir cet endroit",
    "Tu veux penser à autre chose",
    "Il veut que ce soit vrai",
    
    # Isotopie DIRE/PAROLE (15 phrases)
    "Je dis ce que je pense",
    "Tu dis des mots vrais",
    "Il dit quelque chose de bon",
    "Elle dit ce qu'elle veut",
    "Les gens disent beaucoup de choses",
    "Quelqu'un dit un mot",
    "Je dis que c'est vrai",
    "Tu dis ce que tu sais",
    "Il dit où se trouve cet endroit",
    "Elle dit ce qui arrive maintenant",
    "Les gens disent ce qu'ils pensent",
    "Quelqu'un dit la même chose",
    "Je dis ce que je vois",
    "Tu dis ce que tu sens",
    "Il dit ce qu'il veut faire",
    
    # Isotopie FAIRE/ACTION (15 phrases)
    "Je fais quelque chose de bien",
    "Tu fais ce que tu veux",
    "Il fait bouger ce corps",
    "Elle fait arriver des choses",
    "Les gens font beaucoup de choses",
    "Quelqu'un fait quelque chose maintenant",
    "Je fais comme toi",
    "Tu fais ce qui est bon",
    "Il fait ce qu'il peut",
    "Elle fait toucher deux choses",
    "Les gens font ce qu'ils veulent",
    "Quelqu'un fait la même chose",
    "Je fais ce que je dis",
    "Tu fais bouger cette partie",
    "Il fait arriver quelque chose de grand",
    
    # Isotopie ETRE/EXISTENCE (15 phrases)
    "Je suis une personne",
    "Tu es près de cet endroit",
    "Il est comme les autres gens",
    "Elle est dans ce corps",
    "Les gens sont vivants maintenant",
    "Quelque chose est vrai",
    "Je suis ici à ce moment",
    "Tu es quelqu'un de bon",
    "Il est au-dessus de cette partie",
    "Elle est avant quelqu'un d'autre",
    "Les gens sont d'une même espèce",
    "Quelque chose est très grand",
    "Je suis près de toi",
    "Tu es dans cet endroit",
    "Il est comme moi",
    
    # Isotopie RELATIONS SPATIALES (15 phrases)
    "Cet endroit est près de l'autre",
    "Une partie est au-dessus d'une autre partie",
    "Ce corps est dans cet endroit",
    "Quelque chose est loin de moi",
    "Un côté est en dessous de l'autre côté",
    "Cette partie touche une autre partie",
    "Cet endroit est près d'un autre endroit",
    "Une chose est au-dessus de deux choses",
    "Ce corps bouge vers cet endroit",
    "Quelque chose arrive à cet endroit",
    "Un côté est loin de l'autre côté",
    "Cette partie est dans un grand corps",
    "Cet endroit a beaucoup de choses",
    "Une chose est très près d'une autre",
    "Ce corps est en dessous de quelque chose",
    
    # Isotopie RELATIONS TEMPORELLES (15 phrases)
    "Maintenant c'est le bon moment",
    "Avant ce moment il y avait autre chose",
    "À ce moment quelque chose arrive",
    "Maintenant je pense à toi",
    "Avant maintenant c'était différent",
    "À ce moment les gens font quelque chose",
    "Maintenant je vois ce qui arrive",
    "Avant cela je ne savais pas",
    "À ce moment quelqu'un dit quelque chose",
    "Maintenant c'est comme avant",
    "Avant ce moment c'était très différent",
    "À ce moment je fais ce que je veux",
    "Maintenant les gens savent la vérité",
    "Avant cela personne ne savait",
    "À ce moment tout arrive ensemble",
]

def obtenir_primitives_par_categorie(categorie: str) -> List[PrimitiveNSM]:
    """Retourne toutes les primitives d'une catégorie donnée"""
    return [p for p in NSM_PRIMITIVES.values() if p.categorie == categorie]

def obtenir_categories() -> List[str]:
    """Retourne la liste des catégories uniques"""
    return list(set(p.categorie for p in NSM_PRIMITIVES.values()))

if __name__ == "__main__":
    print(f"✅ {len(NSM_PRIMITIVES)} primitives NSM")
    print(f"✅ {len(CARRES_SEMIOTIQUES)} carrés sémiotiques")
    print(f"✅ {len(CORPUS_TEST)} phrases corpus")
    print(f"✅ {len(obtenir_categories())} catégories")
