#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extension NSM - Enrichissement du dictionnaire avec nouveaux concepts
Ajoute 30+ nouvelles molecules et 20+ nouveaux composes
"""

from nsm_primitives import NSM_PRIMITIVES


# NOUVELLES MOLECULES (30+)
NSM_MOLECULES_EXTENDED = {
    # Emotions avancees
    "ESPOIR": {
        "composition": ["SENTIR", "BON", "PENSER", "PEUT_ETRE", "ARRIVER"],
        "level": 1,
        "explanation": "Sentir du bien en pensant que peut-etre arrive",
        "sanskrit": "āśā"
    },
    "DESESPOIR": {
        "composition": ["SENTIR", "MAUVAIS", "PENSER", "PAS", "ARRIVER"],
        "level": 1,
        "explanation": "Sentir du mal en pensant que n'arrivera pas",
        "sanskrit": "nirāśā"
    },
    "JALOUSIE": {
        "composition": ["SENTIR", "MAUVAIS", "QUELQU_UN", "AVOIR", "VOULOIR"],
        "level": 1,
        "explanation": "Sentir du mal parce que quelqu'un a ce qu'on veut",
        "sanskrit": "īrṣyā"
    },
    "FIERTE": {
        "composition": ["SENTIR", "BON", "PARCE_QUE", "JE", "FAIRE", "BON"],
        "level": 1,
        "explanation": "Sentir du bien parce que j'ai fait quelque chose de bon",
        "sanskrit": "garva"
    },
    "HONTE": {
        "composition": ["SENTIR", "MAUVAIS", "PARCE_QUE", "JE", "FAIRE", "MAUVAIS"],
        "level": 1,
        "explanation": "Sentir du mal parce que j'ai fait quelque chose de mauvais",
        "sanskrit": "lajjā"
    },
    
    # Actions sociales
    "PARTAGER": {
        "composition": ["FAIRE", "AVOIR", "QUELQU_UN", "AUTRE", "LE_MEME"],
        "level": 1,
        "explanation": "Faire que quelqu'un d'autre ait la meme chose",
        "sanskrit": "vibhāj"
    },
    "ECHANGER": {
        "composition": ["DONNER", "AVOIR", "UN_AUTRE"],
        "level": 1,
        "explanation": "Donner et avoir autre chose",
        "sanskrit": "parivartan"
    },
    "VOLER": {
        "composition": ["PRENDRE", "PAS", "VOULOIR", "QUELQU_UN"],
        "level": 1,
        "explanation": "Prendre sans que quelqu'un veuille",
        "sanskrit": "cor"
    },
    "PROTEGER": {
        "composition": ["FAIRE", "PAS", "ARRIVER", "MAUVAIS"],
        "level": 1,
        "explanation": "Faire que n'arrive pas quelque chose de mauvais",
        "sanskrit": "rakṣ"
    },
    "ATTAQUER": {
        "composition": ["FAIRE", "MAUVAIS", "QUELQU_UN", "VOULOIR", "BLESSER"],
        "level": 1,
        "explanation": "Faire du mal a quelqu'un en voulant blesser",
        "sanskrit": "ākram"
    },
    
    # Cognition avancee
    "IMAGINER": {
        "composition": ["PENSER", "QUELQUE_CHOSE", "PAS", "ETRE"],
        "level": 1,
        "explanation": "Penser a quelque chose qui n'est pas",
        "sanskrit": "kalpan"
    },
    "CROIRE": {
        "composition": ["PENSER", "VRAI", "PAS", "SAVOIR"],
        "level": 1,
        "explanation": "Penser que c'est vrai sans savoir",
        "sanskrit": "viśvas"
    },
    "DOUTER": {
        "composition": ["PENSER", "PEUT_ETRE", "VRAI", "PEUT_ETRE", "PAS"],
        "level": 1,
        "explanation": "Penser que peut-etre vrai, peut-etre pas",
        "sanskrit": "saṃśay"
    },
    "DECIDER": {
        "composition": ["PENSER", "VOULOIR", "FAIRE", "CE"],
        "level": 1,
        "explanation": "Penser et vouloir faire ceci",
        "sanskrit": "niścay"
    },
    "CHOISIR": {
        "composition": ["PENSER", "VOULOIR", "CE", "PAS", "UN_AUTRE"],
        "level": 1,
        "explanation": "Penser vouloir ceci et pas autre chose",
        "sanskrit": "var"
    },
    
    # Mouvement et action
    "COURIR": {
        "composition": ["BOUGER", "TRES", "VITE"],
        "level": 1,
        "explanation": "Bouger tres vite",
        "sanskrit": "dhāv"
    },
    "SAUTER": {
        "composition": ["BOUGER", "AU_DESSUS", "ENDROIT"],
        "level": 1,
        "explanation": "Bouger au-dessus d'un endroit",
        "sanskrit": "plav"
    },
    "TOMBER": {
        "composition": ["BOUGER", "EN_DESSOUS", "PAS", "VOULOIR"],
        "level": 1,
        "explanation": "Bouger en dessous sans vouloir",
        "sanskrit": "pat"
    },
    "POUSSER": {
        "composition": ["FAIRE", "BOUGER", "LOIN", "JE"],
        "level": 1,
        "explanation": "Faire bouger loin de moi",
        "sanskrit": "nud"
    },
    "TIRER": {
        "composition": ["FAIRE", "BOUGER", "PRES", "JE"],
        "level": 1,
        "explanation": "Faire bouger pres de moi",
        "sanskrit": "karṣ"
    },
    
    # Perception et sensation
    "ENTENDRE": {
        "composition": ["SAVOIR", "QUELQUE_CHOSE", "PARCE_QUE", "DIRE"],
        "level": 1,
        "explanation": "Savoir quelque chose parce que quelqu'un dit",
        "sanskrit": "śru"
    },
    "SENTIR_ODEUR": {
        "composition": ["SAVOIR", "QUELQUE_CHOSE", "PARCE_QUE", "DANS"],
        "level": 1,
        "explanation": "Savoir quelque chose par ce qui est dans l'air",
        "sanskrit": "ghrā"
    },
    "GOUTER": {
        "composition": ["SAVOIR", "QUELQUE_CHOSE", "PARCE_QUE", "BOUCHE"],
        "level": 1,
        "explanation": "Savoir quelque chose par la bouche",
        "sanskrit": "svaد"
    },
    
    # Vie et temps
    "DORMIR": {
        "composition": ["PAS", "SAVOIR", "MAINTENANT", "PARCE_QUE", "CORPS"],
        "level": 1,
        "explanation": "Ne pas savoir maintenant a cause du corps",
        "sanskrit": "svap"
    },
    "REVEIL": {
        "composition": ["ARRIVER", "SAVOIR", "MAINTENANT", "APRES", "DORMIR"],
        "level": 1,
        "explanation": "Arriver a savoir maintenant apres dormir",
        "sanskrit": "bodh"
    },
    "ATTENDRE": {
        "composition": ["VOULOIR", "ARRIVER", "APRES", "MAINTENANT"],
        "level": 1,
        "explanation": "Vouloir que arrive apres maintenant",
        "sanskrit": "pratīkṣ"
    },
    "COMMENCER": {
        "composition": ["FAIRE", "ARRIVER", "MAINTENANT", "AVANT", "PAS"],
        "level": 1,
        "explanation": "Faire arriver maintenant ce qui avant n'etait pas",
        "sanskrit": "ārabh"
    },
    "FINIR": {
        "composition": ["FAIRE", "PAS", "ARRIVER", "APRES", "MAINTENANT"],
        "level": 1,
        "explanation": "Faire que n'arrive pas apres maintenant",
        "sanskrit": "samāp"
    },
    
    # Relations
    "RENCONTRER": {
        "composition": ["ARRIVER", "ETRE", "PRES", "QUELQU_UN"],
        "level": 1,
        "explanation": "Arriver a etre pres de quelqu'un",
        "sanskrit": "mili"
    },
    "SEPARER": {
        "composition": ["FAIRE", "ETRE", "LOIN", "UN_AUTRE"],
        "level": 1,
        "explanation": "Faire etre loin l'un de l'autre",
        "sanskrit": "viyuj"
    },
    "SUIVRE": {
        "composition": ["BOUGER", "APRES", "QUELQU_UN", "LE_MEME"],
        "level": 1,
        "explanation": "Bouger apres quelqu'un de la meme facon",
        "sanskrit": "anu"
    },
}


# NOUVEAUX COMPOSES (20+)
COMPOSED_CONCEPTS_EXTENDED = {
    # Communication avancee
    "RACONTER": {
        "molecules": ["DIRE", "ARRIVER", "AVANT"],
        "primitives": ["DIRE", "ARRIVER", "AVANT"],
        "level": 2,
        "explanation": "Dire ce qui est arrive avant",
        "sanskrit": "kathay"
    },
    "DISCUTER": {
        "molecules": ["DIRE", "ENTENDRE", "PENSER"],
        "primitives": ["DIRE", "SAVOIR", "PENSER"],
        "level": 2,
        "explanation": "Dire et entendre en pensant ensemble",
        "sanskrit": "vicār"
    },
    "ARGUMENTER": {
        "molecules": ["DIRE", "PARCE_QUE", "VOULOIR", "CROIRE"],
        "primitives": ["DIRE", "PARCE_QUE", "VOULOIR", "PENSER", "VRAI"],
        "level": 2,
        "explanation": "Dire pourquoi pour faire croire",
        "sanskrit": "tark"
    },
    "CRITIQUER": {
        "molecules": ["DIRE", "MAUVAIS", "FAIRE"],
        "primitives": ["DIRE", "MAUVAIS", "FAIRE"],
        "level": 2,
        "explanation": "Dire que ce qui est fait est mauvais",
        "sanskrit": "nindā"
    },
    "LOUER": {
        "molecules": ["DIRE", "BON", "FAIRE"],
        "primitives": ["DIRE", "BON", "FAIRE"],
        "level": 2,
        "explanation": "Dire que ce qui est fait est bon",
        "sanskrit": "praśaṃsā"
    },
    
    # Education et developpement
    "ETUDIER": {
        "molecules": ["VOULOIR", "APPRENDRE", "LIRE", "PENSER"],
        "primitives": ["VOULOIR", "SAVOIR", "VOIR", "MOT", "PENSER"],
        "level": 2,
        "explanation": "Vouloir apprendre en lisant et pensant",
        "sanskrit": "adhyay"
    },
    "PRATIQUER": {
        "molecules": ["FAIRE", "BEAUCOUP", "VOULOIR", "SAVOIR"],
        "primitives": ["FAIRE", "BEAUCOUP", "VOULOIR", "SAVOIR"],
        "level": 2,
        "explanation": "Faire beaucoup pour vouloir savoir mieux",
        "sanskrit": "abhyās"
    },
    "EXPLORER": {
        "molecules": ["ALLER", "VOULOIR", "VOIR", "SAVOIR"],
        "primitives": ["BOUGER", "ENDROIT", "VOULOIR", "VOIR", "SAVOIR"],
        "level": 2,
        "explanation": "Aller vers endroits pour voir et savoir",
        "sanskrit": "anveṣ"
    },
    "EXPERIMENTER": {
        "molecules": ["FAIRE", "VOULOIR", "SAVOIR", "VRAI"],
        "primitives": ["FAIRE", "VOULOIR", "SAVOIR", "VRAI"],
        "level": 2,
        "explanation": "Faire pour vouloir savoir si c'est vrai",
        "sanskrit": "parīkṣ"
    },
    
    # Creation et art
    "CREER": {
        "molecules": ["FAIRE", "ARRIVER", "ETRE", "IMAGINER"],
        "primitives": ["FAIRE", "ARRIVER", "ETRE", "PENSER", "PAS"],
        "level": 2,
        "explanation": "Faire arriver d'etre ce qu'on imaginait",
        "sanskrit": "sṛj"
    },
    "DESSINER": {
        "molecules": ["FAIRE", "VOIR", "QUELQUE_CHOSE", "IMAGINER"],
        "primitives": ["FAIRE", "VOIR", "QUELQUE_CHOSE", "PENSER"],
        "level": 2,
        "explanation": "Faire voir quelque chose qu'on imagine",
        "sanskrit": "citra"
    },
    "CHANTER": {
        "molecules": ["DIRE", "COMME", "MUSIQUE"],
        "primitives": ["DIRE", "COMME"],
        "level": 2,
        "explanation": "Dire comme de la musique",
        "sanskrit": "gā"
    },
    "DANSER": {
        "molecules": ["BOUGER", "COMME", "MUSIQUE", "SENTIR", "BON"],
        "primitives": ["BOUGER", "COMME", "SENTIR", "BON"],
        "level": 2,
        "explanation": "Bouger comme musique en sentant du bien",
        "sanskrit": "nṛt"
    },
    
    # Organisation sociale
    "ORGANISER": {
        "molecules": ["FAIRE", "ETRE", "BON", "ENDROIT", "MOMENT"],
        "primitives": ["FAIRE", "ETRE", "BON", "ENDROIT", "MOMENT"],
        "level": 2,
        "explanation": "Faire etre au bon endroit au bon moment",
        "sanskrit": "vyavasthā"
    },
    "DIRIGER": {
        "molecules": ["DIRE", "VOULOIR", "FAIRE", "QUELQU_UN"],
        "primitives": ["DIRE", "VOULOIR", "FAIRE", "QUELQU_UN"],
        "level": 2,
        "explanation": "Dire vouloir que quelqu'un fasse",
        "sanskrit": "netṛ"
    },
    "OBEIR": {
        "molecules": ["FAIRE", "PARCE_QUE", "QUELQU_UN", "DIRE"],
        "primitives": ["FAIRE", "PARCE_QUE", "QUELQU_UN", "DIRE"],
        "level": 2,
        "explanation": "Faire parce que quelqu'un dit",
        "sanskrit": "ājñā-pālan"
    },
    "COOPERER": {
        "molecules": ["FAIRE", "ENSEMBLE", "VOULOIR", "LE_MEME"],
        "primitives": ["FAIRE", "VOULOIR", "LE_MEME"],
        "level": 2,
        "explanation": "Faire ensemble en voulant la meme chose",
        "sanskrit": "sahakāra"
    },
    
    # Economie et echange
    "PAYER": {
        "molecules": ["DONNER", "QUELQUE_CHOSE", "AVOIR", "UN_AUTRE"],
        "primitives": ["FAIRE", "AVOIR", "QUELQU_UN", "AUTRE"],
        "level": 2,
        "explanation": "Donner quelque chose pour avoir autre chose",
        "sanskrit": "dā-mūlya"
    },
    "GAGNER": {
        "molecules": ["AVOIR", "APRES", "TRAVAILLER"],
        "primitives": ["AVOIR", "APRES", "FAIRE", "VOULOIR"],
        "level": 2,
        "explanation": "Avoir apres avoir travaille",
        "sanskrit": "labh"
    },
    "PERDRE": {
        "molecules": ["PAS", "AVOIR", "MAINTENANT", "AVANT", "AVOIR"],
        "primitives": ["PAS", "AVOIR", "MAINTENANT", "AVANT", "AVOIR"],
        "level": 2,
        "explanation": "Ne pas avoir maintenant ce qu'on avait avant",
        "sanskrit": "naś-dhana"
    },
}


def get_all_extended_concepts():
    """Retourne tous les concepts etendus (molecules + composes)"""
    return {
        "molecules": NSM_MOLECULES_EXTENDED,
        "composed": COMPOSED_CONCEPTS_EXTENDED,
        "total_molecules": len(NSM_MOLECULES_EXTENDED),
        "total_composed": len(COMPOSED_CONCEPTS_EXTENDED),
        "total": len(NSM_MOLECULES_EXTENDED) + len(COMPOSED_CONCEPTS_EXTENDED)
    }


if __name__ == "__main__":
    print("="*70)
    print("EXTENSION NSM - NOUVEAUX CONCEPTS")
    print("="*70)
    
    stats = get_all_extended_concepts()
    
    print("\nStatistiques:")
    print("  Nouvelles molecules: {}".format(stats["total_molecules"]))
    print("  Nouveaux composes: {}".format(stats["total_composed"]))
    print("  Total nouveaux concepts: {}".format(stats["total"]))
    
    print("\nCategories de molecules:")
    categories = {
        "Emotions": ["ESPOIR", "DESESPOIR", "JALOUSIE", "FIERTE", "HONTE"],
        "Actions sociales": ["PARTAGER", "ECHANGER", "VOLER", "PROTEGER"],
        "Cognition": ["IMAGINER", "CROIRE", "DOUTER", "DECIDER", "CHOISIR"],
        "Mouvement": ["COURIR", "SAUTER", "TOMBER", "POUSSER", "TIRER"],
        "Perception": ["ENTENDRE", "SENTIR_ODEUR", "GOUTER"],
        "Temps": ["DORMIR", "REVEIL", "ATTENDRE", "COMMENCER", "FINIR"],
        "Relations": ["RENCONTRER", "SEPARER", "SUIVRE"]
    }
    
    for cat, concepts in categories.items():
        print("  {}: {} concepts".format(cat, len(concepts)))
    
    print("\nExemples de decomposition:")
    print("  JALOUSIE = SENTIR + MAUVAIS + QUELQU'UN + AVOIR + VOULOIR")
    print("  COOPERER = FAIRE + ENSEMBLE + VOULOIR + LE_MEME")
    print("  EXPERIMENTER = FAIRE + VOULOIR + SAVOIR + VRAI")
    
    print("\n" + "="*70)
    print("Extension prete a etre integree au reconstructeur NSM")
    print("="*70)
