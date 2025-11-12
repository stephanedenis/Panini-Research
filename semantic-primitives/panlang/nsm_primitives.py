#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NSM Primitives Database - Natural Semantic Metalanguage
Base sur les recherches d'Anna Wierzbicka (1972-2025)
65 primitives semantiques universelles validees sur 16+ langues
"""

# Niveau 0: ATOMES - 65 Primitives NSM avec mappings Sanskrit
NSM_PRIMITIVES = {
    # SUBSTANTIFS (13)
    "JE": {"category": "SUBSTANTIFS", "sanskrit": "aham", "dhatu": "AH", "level": 0},
    "TOI": {"category": "SUBSTANTIFS", "sanskrit": "tvam", "dhatu": "TV", "level": 0},
    "QUELQU_UN": {"category": "SUBSTANTIFS", "sanskrit": "kascit", "dhatu": "KA", "level": 0},
    "QUELQUE_CHOSE": {"category": "SUBSTANTIFS", "sanskrit": "kim-cit", "dhatu": "KIM", "level": 0},
    "GENS": {"category": "SUBSTANTIFS", "sanskrit": "janāḥ", "dhatu": "JAN", "level": 0},
    "CORPS": {"category": "SUBSTANTIFS", "sanskrit": "śarīra", "dhatu": "ŚRĪ", "level": 0},
    "PARTIE": {"category": "SUBSTANTIFS", "sanskrit": "bhāga", "dhatu": "BHAJ", "level": 0},
    "ESPECE": {"category": "SUBSTANTIFS", "sanskrit": "jāti", "dhatu": "JAN", "level": 0},
    "COTE": {"category": "SUBSTANTIFS", "sanskrit": "pārśva", "dhatu": "PṚ", "level": 0},
    "ENDROIT": {"category": "SUBSTANTIFS", "sanskrit": "sthāna", "dhatu": "STHĀ", "level": 0},
    "MOMENT": {"category": "SUBSTANTIFS", "sanskrit": "kṣaṇa", "dhatu": "KṢAṆ", "level": 0},
    "MAINTENANT": {"category": "SUBSTANTIFS", "sanskrit": "adhunā", "dhatu": "DHŪ", "level": 0},
    "AVANT": {"category": "SUBSTANTIFS", "sanskrit": "purā", "dhatu": "PUR", "level": 0},
    
    # DETERMINANTS (4)
    "CE": {"category": "DETERMINANTS", "sanskrit": "ayam", "dhatu": "AY", "level": 0},
    "LE_MEME": {"category": "DETERMINANTS", "sanskrit": "sama", "dhatu": "SAM", "level": 0},
    "UN_AUTRE": {"category": "DETERMINANTS", "sanskrit": "anya", "dhatu": "AN", "level": 0},
    "UN": {"category": "DETERMINANTS", "sanskrit": "eka", "dhatu": "EK", "level": 0},
    
    # QUANTIFICATEURS (3)
    "DEUX": {"category": "QUANTIFICATEURS", "sanskrit": "dvi", "dhatu": "DVI", "level": 0},
    "BEAUCOUP": {"category": "QUANTIFICATEURS", "sanskrit": "bahu", "dhatu": "BAH", "level": 0},
    "TOUT": {"category": "QUANTIFICATEURS", "sanskrit": "sarva", "dhatu": "SARV", "level": 0},
    
    # ATTRIBUTS (5)
    "BON": {"category": "ATTRIBUTS", "sanskrit": "su", "dhatu": "SU", "level": 0},
    "MAUVAIS": {"category": "ATTRIBUTS", "sanskrit": "dur", "dhatu": "DUR", "level": 0},
    "GRAND": {"category": "ATTRIBUTS", "sanskrit": "mahā", "dhatu": "MAH", "level": 0},
    "PETIT": {"category": "ATTRIBUTS", "sanskrit": "alpa", "dhatu": "ALP", "level": 0},
    "AUTRE": {"category": "ATTRIBUTS", "sanskrit": "anya", "dhatu": "AN", "level": 0},
    
    # PREDICATS MENTAUX (5)
    "PENSER": {"category": "MENTAUX", "sanskrit": "man", "dhatu": "MAN", "level": 0},
    "SAVOIR": {"category": "MENTAUX", "sanskrit": "jñā", "dhatu": "JÑĀ", "level": 0},
    "VOULOIR": {"category": "MENTAUX", "sanskrit": "iṣ", "dhatu": "IṢ", "level": 0},
    "SENTIR": {"category": "MENTAUX", "sanskrit": "vedayate", "dhatu": "VID", "level": 0},
    "VOIR": {"category": "MENTAUX", "sanskrit": "paś", "dhatu": "PAŚ", "level": 0},
    
    # PREDICATS DE PAROLE (3)
    "DIRE": {"category": "PAROLE", "sanskrit": "vac", "dhatu": "VAC", "level": 0},
    "MOT": {"category": "PAROLE", "sanskrit": "vāk", "dhatu": "VAC", "level": 0},
    "VRAI": {"category": "PAROLE", "sanskrit": "satya", "dhatu": "SAT", "level": 0},
    
    # ACTIONS ET MOUVEMENTS (4)
    "FAIRE": {"category": "ACTIONS", "sanskrit": "kṛ", "dhatu": "KṚ", "level": 0},
    "ARRIVER": {"category": "ACTIONS", "sanskrit": "bhū", "dhatu": "BHŪ", "level": 0},
    "BOUGER": {"category": "ACTIONS", "sanskrit": "cal", "dhatu": "CAL", "level": 0},
    "TOUCHER": {"category": "ACTIONS", "sanskrit": "spṛś", "dhatu": "SPṚŚ", "level": 0},
    
    # EXISTENCE ET POSSESSION (4)
    "ETRE": {"category": "EXISTENCE", "sanskrit": "as", "dhatu": "AS", "level": 0},
    "AVOIR": {"category": "EXISTENCE", "sanskrit": "dhā", "dhatu": "DHĀ", "level": 0},
    "VIVRE": {"category": "EXISTENCE", "sanskrit": "jīv", "dhatu": "JĪV", "level": 0},
    "MOURIR": {"category": "EXISTENCE", "sanskrit": "mṛ", "dhatu": "MṚ", "level": 0},
    
    # RELATIONS LOGIQUES (7)
    "PAS": {"category": "LOGIQUE", "sanskrit": "na", "dhatu": "NA", "level": 0},
    "PEUT_ETRE": {"category": "LOGIQUE", "sanskrit": "syāt", "dhatu": "AS", "level": 0},
    "POUVOIR": {"category": "LOGIQUE", "sanskrit": "śak", "dhatu": "ŚAK", "level": 0},
    "PARCE_QUE": {"category": "LOGIQUE", "sanskrit": "yataḥ", "dhatu": "YAT", "level": 0},
    "SI": {"category": "LOGIQUE", "sanskrit": "yadi", "dhatu": "YAD", "level": 0},
    "COMME": {"category": "LOGIQUE", "sanskrit": "iva", "dhatu": "IV", "level": 0},
    "TRES": {"category": "LOGIQUE", "sanskrit": "ati", "dhatu": "AT", "level": 0},
    
    # AUGMENTEURS (7)
    "PLUS": {"category": "AUGMENTEURS", "sanskrit": "adhika", "dhatu": "ADHI", "level": 0},
    "LOIN": {"category": "AUGMENTEURS", "sanskrit": "dūra", "dhatu": "DṚ", "level": 0},
    "PRES": {"category": "AUGMENTEURS", "sanskrit": "nikṛta", "dhatu": "NI", "level": 0},
    "DANS": {"category": "AUGMENTEURS", "sanskrit": "antar", "dhatu": "ANTAR", "level": 0},
    "AU_DESSUS": {"category": "AUGMENTEURS", "sanskrit": "upari", "dhatu": "UPA", "level": 0},
    "EN_DESSOUS": {"category": "AUGMENTEURS", "sanskrit": "adhas", "dhatu": "ADH", "level": 0},
    "OÙ": {"category": "AUGMENTEURS", "sanskrit": "kutra", "dhatu": "KU", "level": 0},
    
    # TEMPS (3)
    "QUAND": {"category": "TEMPS", "sanskrit": "kadā", "dhatu": "KAD", "level": 0},
    "APRES": {"category": "TEMPS", "sanskrit": "paścāt", "dhatu": "PAŚ", "level": 0},
    "LONGTEMPS": {"category": "TEMPS", "sanskrit": "cira", "dhatu": "CIR", "level": 0},
    
    # INTENSIFICATEURS (3)
    "BEAUCOUP_DE": {"category": "INTENSIFICATEURS", "sanskrit": "bahu", "dhatu": "BAH", "level": 0},
    "PEU_DE": {"category": "INTENSIFICATEURS", "sanskrit": "alpa", "dhatu": "ALP", "level": 0},
    "TOUT_LE": {"category": "INTENSIFICATEURS", "sanskrit": "sarva", "dhatu": "SARV", "level": 0},
}

# Niveau 1: MOLECULES - Compositions universelles (20+)
NSM_MOLECULES = {
    "ENSEIGNER": {
        "composition": ["VOULOIR", "FAIRE", "SAVOIR"],
        "level": 1,
        "explanation": "Vouloir faire que quelqu'un sache",
        "sanskrit": "śikṣ"
    },
    "APPRENDRE": {
        "composition": ["VOULOIR", "SAVOIR"],
        "level": 1,
        "explanation": "Vouloir savoir quelque chose",
        "sanskrit": "śikṣ/PAṬ"
    },
    "COMPRENDRE": {
        "composition": ["SAVOIR", "PARCE_QUE", "PENSER"],
        "level": 1,
        "explanation": "Savoir pourquoi en pensant",
        "sanskrit": "budh"
    },
    "OUBLIER": {
        "composition": ["PAS", "SAVOIR", "MAINTENANT", "AVANT", "SAVOIR"],
        "level": 1,
        "explanation": "Ne pas savoir maintenant ce qu'on savait avant",
        "sanskrit": "smṛ/VID"
    },
    "AIMER": {
        "composition": ["SENTIR", "BON", "VOULOIR", "ETRE", "PRES"],
        "level": 1,
        "explanation": "Sentir du bien et vouloir être près",
        "sanskrit": "prīy"
    },
    "DETESTER": {
        "composition": ["SENTIR", "MAUVAIS", "VOULOIR", "PAS", "ETRE", "PRES"],
        "level": 1,
        "explanation": "Sentir du mal et vouloir ne pas être près",
        "sanskrit": "dviṣ"
    },
    "CONTENT": {
        "composition": ["SENTIR", "BON", "PARCE_QUE", "ARRIVER", "VOULOIR"],
        "level": 1,
        "explanation": "Sentir du bien parce que quelque chose qu'on voulait arrive",
        "sanskrit": "tuṣ"
    },
    "TRISTE": {
        "composition": ["SENTIR", "MAUVAIS", "PARCE_QUE", "ARRIVER", "PAS", "VOULOIR"],
        "level": 1,
        "explanation": "Sentir du mal parce que quelque chose qu'on ne voulait pas arrive",
        "sanskrit": "śuc"
    },
    "PEUR": {
        "composition": ["SENTIR", "MAUVAIS", "PARCE_QUE", "PENSER", "PEUT_ETRE", "ARRIVER", "MAUVAIS"],
        "level": 1,
        "explanation": "Sentir du mal parce qu'on pense que peut-être quelque chose de mauvais arrivera",
        "sanskrit": "bhī"
    },
    "COLERE": {
        "composition": ["SENTIR", "MAUVAIS", "PARCE_QUE", "QUELQU_UN", "FAIRE", "MAUVAIS"],
        "level": 1,
        "explanation": "Sentir du mal parce que quelqu'un a fait quelque chose de mauvais",
        "sanskrit": "krudh"
    },
    "DONNER": {
        "composition": ["FAIRE", "AVOIR", "QUELQU_UN", "AUTRE"],
        "level": 1,
        "explanation": "Faire que quelqu'un d'autre ait",
        "sanskrit": "dā"
    },
    "PRENDRE": {
        "composition": ["FAIRE", "AVOIR", "JE"],
        "level": 1,
        "explanation": "Faire que j'aie",
        "sanskrit": "grah"
    },
    "AIDER": {
        "composition": ["FAIRE", "QUELQUE_CHOSE", "BON", "QUELQU_UN"],
        "level": 1,
        "explanation": "Faire quelque chose de bon pour quelqu'un",
        "sanskrit": "sah"
    },
    "BLESSER": {
        "composition": ["FAIRE", "QUELQUE_CHOSE", "MAUVAIS", "CORPS"],
        "level": 1,
        "explanation": "Faire quelque chose de mauvais au corps",
        "sanskrit": "hiṃs"
    },
    "TUER": {
        "composition": ["FAIRE", "MOURIR"],
        "level": 1,
        "explanation": "Faire mourir",
        "sanskrit": "han"
    },
    "NAITRE": {
        "composition": ["ARRIVER", "VIVRE", "MAINTENANT"],
        "level": 1,
        "explanation": "Arriver à vivre maintenant",
        "sanskrit": "jan"
    },
    "GRANDIR": {
        "composition": ["ARRIVER", "PLUS", "GRAND"],
        "level": 1,
        "explanation": "Arriver à être plus grand",
        "sanskrit": "vṛdh"
    },
    "CHANGER": {
        "composition": ["ARRIVER", "PAS", "LE_MEME"],
        "level": 1,
        "explanation": "Arriver à ne pas être le même",
        "sanskrit": "vṛt"
    },
    "RESTER": {
        "composition": ["PAS", "BOUGER", "LONGTEMPS"],
        "level": 1,
        "explanation": "Ne pas bouger pendant longtemps",
        "sanskrit": "sthā"
    },
    "VENIR": {
        "composition": ["BOUGER", "ENDROIT", "CE"],
        "level": 1,
        "explanation": "Bouger vers cet endroit",
        "sanskrit": "gam/ā"
    },
    "ALLER": {
        "composition": ["BOUGER", "ENDROIT", "UN_AUTRE"],
        "level": 1,
        "explanation": "Bouger vers un autre endroit",
        "sanskrit": "gam/i"
    },
}

# Niveau 2: COMPOSES - Concepts complexes (15+)
COMPOSED_CONCEPTS = {
    "ECRIRE": {
        "molecules": ["FAIRE", "VOIR", "MOT"],
        "primitives": ["FAIRE", "VOIR", "MOT"],
        "level": 2,
        "explanation": "Faire que des mots soient visibles",
        "sanskrit": "likh"
    },
    "LIRE": {
        "molecules": ["VOIR", "MOT", "SAVOIR"],
        "primitives": ["VOIR", "MOT", "SAVOIR"],
        "level": 2,
        "explanation": "Voir des mots et savoir leur sens",
        "sanskrit": "paṭh"
    },
    "PARLER": {
        "molecules": ["DIRE", "MOT"],
        "primitives": ["DIRE", "MOT"],
        "level": 2,
        "explanation": "Dire des mots",
        "sanskrit": "vad"
    },
    "ECOUTER": {
        "molecules": ["VOULOIR", "SAVOIR", "DIRE"],
        "primitives": ["VOULOIR", "SAVOIR", "DIRE"],
        "level": 2,
        "explanation": "Vouloir savoir ce que quelqu'un dit",
        "sanskrit": "śru"
    },
    "DEMANDER": {
        "molecules": ["DIRE", "VOULOIR", "SAVOIR"],
        "primitives": ["DIRE", "VOULOIR", "SAVOIR"],
        "level": 2,
        "explanation": "Dire qu'on veut savoir",
        "sanskrit": "pṛcch"
    },
    "REPONDRE": {
        "molecules": ["DIRE", "PARCE_QUE", "DEMANDER"],
        "primitives": ["DIRE", "PARCE_QUE", "VOULOIR", "SAVOIR"],
        "level": 2,
        "explanation": "Dire parce que quelqu'un a demandé",
        "sanskrit": "prati+vac"
    },
    "EXPLIQUER": {
        "molecules": ["DIRE", "PARCE_QUE", "VOULOIR", "COMPRENDRE"],
        "primitives": ["DIRE", "PARCE_QUE", "VOULOIR", "SAVOIR", "PENSER"],
        "level": 2,
        "explanation": "Dire pour faire comprendre",
        "sanskrit": "vi+ā+khyā"
    },
    "PROMETTRE": {
        "molecules": ["DIRE", "VOULOIR", "FAIRE", "APRES"],
        "primitives": ["DIRE", "VOULOIR", "FAIRE", "APRES"],
        "level": 2,
        "explanation": "Dire qu'on veut faire après",
        "sanskrit": "prati+jñā"
    },
    "MENTIR": {
        "molecules": ["DIRE", "PAS", "VRAI"],
        "primitives": ["DIRE", "PAS", "VRAI"],
        "level": 2,
        "explanation": "Dire ce qui n'est pas vrai",
        "sanskrit": "mṛṣā+vac"
    },
    "JOUER": {
        "molecules": ["FAIRE", "PARCE_QUE", "VOULOIR", "SENTIR", "BON"],
        "primitives": ["FAIRE", "PARCE_QUE", "VOULOIR", "SENTIR", "BON"],
        "level": 2,
        "explanation": "Faire parce qu'on veut sentir du bien",
        "sanskrit": "krīḍ"
    },
    "TRAVAILLER": {
        "molecules": ["FAIRE", "PARCE_QUE", "VOULOIR", "AVOIR"],
        "primitives": ["FAIRE", "PARCE_QUE", "VOULOIR", "AVOIR"],
        "level": 2,
        "explanation": "Faire parce qu'on veut avoir quelque chose",
        "sanskrit": "kṛ/karman"
    },
    "ACHETER": {
        "molecules": ["DONNER", "AVOIR"],
        "primitives": ["FAIRE", "AVOIR", "QUELQU_UN", "AUTRE", "AVOIR"],
        "level": 2,
        "explanation": "Donner quelque chose pour avoir autre chose",
        "sanskrit": "krī"
    },
    "VENDRE": {
        "molecules": ["DONNER", "AVOIR"],
        "primitives": ["FAIRE", "AVOIR", "QUELQU_UN", "AUTRE", "AVOIR"],
        "level": 2,
        "explanation": "Donner pour que quelqu'un ait et qu'on ait autre chose",
        "sanskrit": "vi+krī"
    },
    "CONSTRUIRE": {
        "molecules": ["FAIRE", "ARRIVER", "ETRE"],
        "primitives": ["FAIRE", "ARRIVER", "ETRE"],
        "level": 2,
        "explanation": "Faire qu'arrive d'être",
        "sanskrit": "nirmā"
    },
    "DETRUIRE": {
        "molecules": ["FAIRE", "PAS", "ETRE"],
        "primitives": ["FAIRE", "PAS", "ETRE"],
        "level": 2,
        "explanation": "Faire que ne soit plus",
        "sanskrit": "naś"
    },
}


# Fonctions utilitaires
def get_primitive(concept):
    """Retourne une primitive NSM"""
    return NSM_PRIMITIVES.get(concept.upper())


def get_molecule(concept):
    """Retourne une molecule NSM"""
    return NSM_MOLECULES.get(concept.upper())


def get_concept(concept):
    """Retourne un concept compose"""
    return COMPOSED_CONCEPTS.get(concept.upper())


def list_by_category(category):
    """Liste toutes les primitives d'une categorie"""
    return {
        k: v for k, v in NSM_PRIMITIVES.items()
        if v.get("category") == category
    }


def get_statistics():
    """Retourne les statistiques du systeme NSM"""
    categories = {}
    for prim in NSM_PRIMITIVES.values():
        cat = prim.get("category", "AUTRE")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_primitives": len(NSM_PRIMITIVES),
        "total_molecules": len(NSM_MOLECULES),
        "total_composed": len(COMPOSED_CONCEPTS),
        "categories": categories
    }


if __name__ == "__main__":
    print("=== Systeme NSM - Natural Semantic Metalanguage ===")
    print()
    stats = get_statistics()
    print("Statistiques:")
    for key, value in stats.items():
        if key != "categories":
            print("  {}: {}".format(key, value))
    print()
    print("Categories de primitives:")
    for cat, count in stats["categories"].items():
        print("  {}: {}".format(cat, count))
