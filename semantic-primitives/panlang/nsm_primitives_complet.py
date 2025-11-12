# -*- coding: utf-8 -*-
"""
NSM Primitives Complete Database - Version Enrichie

Base de donnees complete des primitives NSM (Natural Semantic Metalanguage)
avec extensions molecules et composes incluant les 51 nouveaux concepts.

Architecture multi-niveaux :
- NIVEAU 0 : 61 primitives universelles (atomes)
- NIVEAU 1 : 52 molecules (21 originales + 31 nouvelles)
- NIVEAU 2 : 35 composes (15 originaux + 20 nouveaux)
- NIVEAU 3 : Concepts culturels (a developper)

Reference:
- Wierzbicka, A. (1996). Semantics: Primes and Universals
- Goddard, C. (2002). The search for the shared semantic core of all languages
- Integration avec extension nsm_extension_concepts.py
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple

class CategorieNSM(Enum):
    """Categories semantiques des primitives NSM"""
    SUBSTANTIFS = "SUBSTANTIFS"
    DETERMINANTS = "DETERMINANTS"
    QUANTIFICATEURS = "QUANTIFICATEURS"
    ATTRIBUTS = "ATTRIBUTS"
    MENTAUX = "MENTAUX"
    PAROLE = "PAROLE"
    ACTIONS = "ACTIONS"
    EXISTENCE = "EXISTENCE"
    LOGIQUE = "LOGIQUE"
    AUGMENTEURS = "AUGMENTEURS"
    TEMPS = "TEMPS"
    INTENSIFICATEURS = "INTENSIFICATEURS"
    ESPACE = "ESPACE"

class PrimitiveNSM:
    """Representation d'une primitive NSM avec mapping Sanskrit"""
    
    def __init__(self, nom: str, categorie: CategorieNSM, 
                 dhatu: str, traduction_fr: str, traduction_en: str,
                 description: str = ""):
        self.nom = nom
        self.categorie = categorie
        self.dhatu = dhatu  # Racine Sanskrit correspondante
        self.traduction_fr = traduction_fr
        self.traduction_en = traduction_en
        self.description = description
    
    def __repr__(self):
        return f"<Primitive {self.nom} ({self.categorie.value})>"

# =============================================================================
# NIVEAU 0 : PRIMITIVES NSM (61 atomes universels)
# =============================================================================

NSM_PRIMITIVES: Dict[str, PrimitiveNSM] = {
    # SUBSTANTIFS (13)
    "JE": PrimitiveNSM("JE", CategorieNSM.SUBSTANTIFS, "aham", "je/moi", "I/me"),
    "TOI": PrimitiveNSM("TOI", CategorieNSM.SUBSTANTIFS, "tvam", "tu/toi", "you"),
    "QUELQU'UN": PrimitiveNSM("QUELQU'UN", CategorieNSM.SUBSTANTIFS, "kashchit", "quelqu'un", "someone"),
    "QUELQUE_CHOSE": PrimitiveNSM("QUELQUE_CHOSE", CategorieNSM.SUBSTANTIFS, "kimchit", "quelque chose", "something"),
    "GENS": PrimitiveNSM("GENS", CategorieNSM.SUBSTANTIFS, "janah", "gens/personnes", "people"),
    "CORPS": PrimitiveNSM("CORPS", CategorieNSM.SUBSTANTIFS, "sharira", "corps", "body"),
    "PARTIE": PrimitiveNSM("PARTIE", CategorieNSM.SUBSTANTIFS, "bhaga", "partie", "part"),
    "SORTE": PrimitiveNSM("SORTE", CategorieNSM.SUBSTANTIFS, "prakara", "sorte/type", "kind"),
    "COTE": PrimitiveNSM("COTE", CategorieNSM.SUBSTANTIFS, "paksha", "cote", "side"),
    "MOT": PrimitiveNSM("MOT", CategorieNSM.PAROLE, "shabda", "mot", "word"),
    "ENDROIT": PrimitiveNSM("ENDROIT", CategorieNSM.ESPACE, "desha", "endroit/lieu", "place"),
    "MOMENT": PrimitiveNSM("MOMENT", CategorieNSM.TEMPS, "kshana", "moment", "moment"),
    "CHOSE": PrimitiveNSM("CHOSE", CategorieNSM.SUBSTANTIFS, "vastu", "chose", "thing"),
    
    # DETERMINANTS (4)
    "CE": PrimitiveNSM("CE", CategorieNSM.DETERMINANTS, "etat", "ce/ceci", "this"),
    "LE_MEME": PrimitiveNSM("LE_MEME", CategorieNSM.DETERMINANTS, "sama", "le meme", "the same"),
    "UN_AUTRE": PrimitiveNSM("UN_AUTRE", CategorieNSM.DETERMINANTS, "anya", "un autre", "another"),
    "UN": PrimitiveNSM("UN", CategorieNSM.DETERMINANTS, "eka", "un", "one"),
    
    # QUANTIFICATEURS (3)
    "DEUX": PrimitiveNSM("DEUX", CategorieNSM.QUANTIFICATEURS, "dvi", "deux", "two"),
    "BEAUCOUP": PrimitiveNSM("BEAUCOUP", CategorieNSM.QUANTIFICATEURS, "bahu", "beaucoup", "much/many"),
    "TOUT": PrimitiveNSM("TOUT", CategorieNSM.QUANTIFICATEURS, "sarva", "tout", "all"),
    
    # ATTRIBUTS (5)
    "BON": PrimitiveNSM("BON", CategorieNSM.ATTRIBUTS, "sat", "bon", "good"),
    "MAUVAIS": PrimitiveNSM("MAUVAIS", CategorieNSM.ATTRIBUTS, "dushta", "mauvais", "bad"),
    "GRAND": PrimitiveNSM("GRAND", CategorieNSM.ATTRIBUTS, "maha", "grand", "big"),
    "PETIT": PrimitiveNSM("PETIT", CategorieNSM.ATTRIBUTS, "alpa", "petit", "small"),
    "AUTRE": PrimitiveNSM("AUTRE", CategorieNSM.ATTRIBUTS, "itara", "autre", "other"),
    
    # PREDICATS MENTAUX (5)
    "PENSER": PrimitiveNSM("PENSER", CategorieNSM.MENTAUX, "chint", "penser", "think"),
    "SAVOIR": PrimitiveNSM("SAVOIR", CategorieNSM.MENTAUX, "vid", "savoir", "know"),
    "VOULOIR": PrimitiveNSM("VOULOIR", CategorieNSM.MENTAUX, "ish", "vouloir", "want"),
    "SENTIR": PrimitiveNSM("SENTIR", CategorieNSM.MENTAUX, "anubhav", "sentir/ressentir", "feel"),
    "VOIR": PrimitiveNSM("VOIR", CategorieNSM.MENTAUX, "drish", "voir", "see"),
    
    # PREDICATS DE PAROLE (3)
    "DIRE": PrimitiveNSM("DIRE", CategorieNSM.PAROLE, "vach", "dire", "say"),
    "VRAI": PrimitiveNSM("VRAI", CategorieNSM.PAROLE, "satya", "vrai", "true"),
    
    # ACTIONS (4)
    "FAIRE": PrimitiveNSM("FAIRE", CategorieNSM.ACTIONS, "kri", "faire", "do"),
    "ARRIVER": PrimitiveNSM("ARRIVER", CategorieNSM.ACTIONS, "bhav", "arriver/se passer", "happen"),
    "BOUGER": PrimitiveNSM("BOUGER", CategorieNSM.ACTIONS, "chal", "bouger", "move"),
    "TOUCHER": PrimitiveNSM("TOUCHER", CategorieNSM.ACTIONS, "sprish", "toucher", "touch"),
    
    # EXISTENCE (4)
    "ETRE": PrimitiveNSM("ETRE", CategorieNSM.EXISTENCE, "as", "etre", "be"),
    "AVOIR": PrimitiveNSM("AVOIR", CategorieNSM.EXISTENCE, "labh", "avoir", "have"),
    "VIVRE": PrimitiveNSM("VIVRE", CategorieNSM.EXISTENCE, "jiv", "vivre", "live"),
    "MOURIR": PrimitiveNSM("MOURIR", CategorieNSM.EXISTENCE, "mri", "mourir", "die"),
    
    # LOGIQUE (7)
    "PAS": PrimitiveNSM("PAS", CategorieNSM.LOGIQUE, "na", "pas/ne...pas", "not"),
    "PEUT_ETRE": PrimitiveNSM("PEUT_ETRE", CategorieNSM.LOGIQUE, "syat", "peut-etre", "maybe"),
    "POUVOIR": PrimitiveNSM("POUVOIR", CategorieNSM.LOGIQUE, "shak", "pouvoir", "can"),
    "PARCE_QUE": PrimitiveNSM("PARCE_QUE", CategorieNSM.LOGIQUE, "yatah", "parce que", "because"),
    "SI": PrimitiveNSM("SI", CategorieNSM.LOGIQUE, "yadi", "si", "if"),
    "COMME": PrimitiveNSM("COMME", CategorieNSM.LOGIQUE, "iva", "comme", "like/as"),
    "TRES": PrimitiveNSM("TRES", CategorieNSM.INTENSIFICATEURS, "ati", "tres", "very"),
    
    # AUGMENTEURS SPATIAUX (7)
    "PLUS": PrimitiveNSM("PLUS", CategorieNSM.AUGMENTEURS, "adhika", "plus", "more"),
    "LOIN": PrimitiveNSM("LOIN", CategorieNSM.AUGMENTEURS, "dura", "loin", "far"),
    "PRES": PrimitiveNSM("PRES", CategorieNSM.AUGMENTEURS, "samipa", "pres", "near"),
    "DANS": PrimitiveNSM("DANS", CategorieNSM.AUGMENTEURS, "antar", "dans", "in/inside"),
    "AU_DESSUS": PrimitiveNSM("AU_DESSUS", CategorieNSM.AUGMENTEURS, "upari", "au-dessus", "above"),
    "EN_DESSOUS": PrimitiveNSM("EN_DESSOUS", CategorieNSM.AUGMENTEURS, "adhas", "en-dessous", "below"),
    "OU": PrimitiveNSM("OU", CategorieNSM.AUGMENTEURS, "kutra", "ou", "where"),
    
    # TEMPS (3)
    "QUAND": PrimitiveNSM("QUAND", CategorieNSM.TEMPS, "kada", "quand", "when"),
    "APRES": PrimitiveNSM("APRES", CategorieNSM.TEMPS, "anantaram", "apres", "after"),
    "LONGTEMPS": PrimitiveNSM("LONGTEMPS", CategorieNSM.TEMPS, "chiram", "longtemps", "a long time"),
    
    # INTENSIFICATEURS (3)
    "BEAUCOUP_INTENSITE": PrimitiveNSM("BEAUCOUP", CategorieNSM.INTENSIFICATEURS, "bhrisham", "tres", "very/much"),
    "MOINS": PrimitiveNSM("MOINS", CategorieNSM.INTENSIFICATEURS, "nyuna", "moins", "less"),
    "UN_PEU": PrimitiveNSM("UN_PEU", CategorieNSM.INTENSIFICATEURS, "kimchit", "un peu", "a little"),
}

# =============================================================================
# NIVEAU 1 : MOLECULES NSM (52 concepts = 21 originales + 31 nouvelles)
# =============================================================================

NSM_MOLECULES: Dict[str, Tuple[str, List[str]]] = {
    # --- MOLECULES ORIGINALES (21) ---
    
    # Education/Cognition (4)
    "ENSEIGNER": ("faire + quelqu'un + savoir + quelque_chose", ["FAIRE", "QUELQU'UN", "SAVOIR", "QUELQUE_CHOSE"]),
    "APPRENDRE": ("vouloir + savoir + quelque_chose", ["VOULOIR", "SAVOIR", "QUELQUE_CHOSE"]),
    "COMPRENDRE": ("savoir + parce_que + penser", ["SAVOIR", "PARCE_QUE", "PENSER"]),
    "OUBLIER": ("avant + savoir + maintenant + pas + savoir", ["SAVOIR", "PAS", "APRES"]),
    
    # Emotions (6)
    "AIMER": ("sentir + bon + a_cause_de + quelqu'un", ["SENTIR", "BON", "PARCE_QUE", "QUELQU'UN"]),
    "DETESTER": ("sentir + mauvais + a_cause_de + quelqu'un", ["SENTIR", "MAUVAIS", "PARCE_QUE", "QUELQU'UN"]),
    "CONTENT": ("sentir + bon", ["SENTIR", "BON"]),
    "TRISTE": ("sentir + mauvais", ["SENTIR", "MAUVAIS"]),
    "PEUR": ("sentir + mauvais + parce_que + pouvoir + arriver", ["SENTIR", "MAUVAIS", "PARCE_QUE", "POUVOIR", "ARRIVER"]),
    "COLERE": ("sentir + mauvais + parce_que + quelqu'un + faire + mauvais", ["SENTIR", "MAUVAIS", "PARCE_QUE", "QUELQU'UN", "FAIRE", "MAUVAIS"]),
    
    # Actions sociales (5)
    "DONNER": ("faire + quelqu'un + avoir + quelque_chose", ["FAIRE", "QUELQU'UN", "AVOIR", "QUELQUE_CHOSE"]),
    "PRENDRE": ("faire + je + avoir + quelque_chose", ["FAIRE", "JE", "AVOIR", "QUELQUE_CHOSE"]),
    "AIDER": ("faire + quelque_chose + pour + quelqu'un", ["FAIRE", "QUELQUE_CHOSE", "QUELQU'UN"]),
    "BLESSER": ("faire + quelque_chose + mauvais + a + quelqu'un", ["FAIRE", "QUELQUE_CHOSE", "MAUVAIS", "QUELQU'UN"]),
    "TUER": ("faire + quelqu'un + mourir", ["FAIRE", "QUELQU'UN", "MOURIR"]),
    
    # Existence/Transformation (6)
    "NAITRE": ("commencer + vivre", ["VIVRE", "APRES"]),
    "GRANDIR": ("devenir + grand", ["GRAND", "APRES"]),
    "CHANGER": ("devenir + autre", ["AUTRE", "APRES"]),
    "RESTER": ("etre + le_meme", ["ETRE", "LE_MEME"]),
    "VENIR": ("bouger + vers + ici", ["BOUGER", "PRES"]),
    "ALLER": ("bouger + vers + la", ["BOUGER", "LOIN"]),
    
    # --- NOUVELLES MOLECULES (31) ---
    
    # Emotions avancees (5)
    "ESPOIR": ("vouloir + penser + pouvoir + arriver", ["VOULOIR", "PENSER", "POUVOIR", "ARRIVER"]),
    "DESESPOIR": ("penser + pas + pouvoir + arriver + sentir + mauvais", ["PENSER", "PAS", "POUVOIR", "ARRIVER", "SENTIR", "MAUVAIS"]),
    "JALOUSIE": ("sentir + mauvais + quelqu'un + avoir + vouloir", ["SENTIR", "MAUVAIS", "QUELQU'UN", "AVOIR", "VOULOIR"]),
    "FIERTE": ("sentir + bon + je + faire + bon", ["SENTIR", "BON", "JE", "FAIRE", "BON"]),
    "HONTE": ("sentir + mauvais + je + faire + mauvais + gens + savoir", ["SENTIR", "MAUVAIS", "JE", "FAIRE", "MAUVAIS", "GENS", "SAVOIR"]),
    
    # Actions sociales avancees (4)
    "PARTAGER": ("donner + partie + a + quelqu'un", ["DONNER", "PARTIE", "QUELQU'UN"]),
    "ECHANGER": ("donner + prendre", ["DONNER", "PRENDRE"]),
    "VOLER": ("prendre + pas + vouloir + quelqu'un", ["PRENDRE", "PAS", "VOULOIR", "QUELQU'UN"]),
    "PROTEGER": ("faire + pas + arriver + mauvais + a + quelqu'un", ["FAIRE", "PAS", "ARRIVER", "MAUVAIS", "QUELQU'UN"]),
    
    # Cognition avancee (5)
    "IMAGINER": ("penser + pas + vrai + comme + voir", ["PENSER", "PAS", "VRAI", "COMME", "VOIR"]),
    "CROIRE": ("penser + vrai", ["PENSER", "VRAI"]),
    "DOUTER": ("pas + savoir + si + vrai", ["PAS", "SAVOIR", "SI", "VRAI"]),
    "DECIDER": ("penser + vouloir + faire", ["PENSER", "VOULOIR", "FAIRE"]),
    "CHOISIR": ("vouloir + ce + pas + autre", ["VOULOIR", "CE", "PAS", "UN_AUTRE"]),
    
    # Mouvement avance (5)
    "COURIR": ("bouger + tres + vite", ["BOUGER", "TRES"]),
    "SAUTER": ("bouger + au_dessus", ["BOUGER", "AU_DESSUS"]),
    "TOMBER": ("bouger + en_dessous + pas + vouloir", ["BOUGER", "EN_DESSOUS", "PAS", "VOULOIR"]),
    "POUSSER": ("toucher + faire + bouger + loin", ["TOUCHER", "FAIRE", "BOUGER", "LOIN"]),
    "TIRER": ("toucher + faire + bouger + pres", ["TOUCHER", "FAIRE", "BOUGER", "PRES"]),
    
    # Perception (3)
    "ENTENDRE": ("sentir + avec + partie + corps", ["SENTIR", "PARTIE", "CORPS"]),
    "SENTIR_ODEUR": ("sentir + avec + partie + corps", ["SENTIR", "PARTIE", "CORPS"]),
    "GOUTER": ("sentir + avec + partie + corps + dans + bouche", ["SENTIR", "PARTIE", "CORPS", "DANS"]),
    
    # Temps/Processus (5)
    "DORMIR": ("vivre + pas + savoir + longtemps", ["VIVRE", "PAS", "SAVOIR", "LONGTEMPS"]),
    "REVEIL": ("apres + dormir + savoir", ["APRES", "SAVOIR"]),
    "ATTENDRE": ("vouloir + arriver + pas + maintenant", ["VOULOIR", "ARRIVER", "PAS"]),
    "COMMENCER": ("avant + pas + maintenant + faire", ["PAS", "FAIRE"]),
    "FINIR": ("avant + faire + maintenant + pas + faire", ["FAIRE", "PAS"]),
    
    # Relations (3)
    "RENCONTRER": ("etre + pres + quelqu'un + avant + pas", ["ETRE", "PRES", "QUELQU'UN", "PAS"]),
    "SEPARER": ("faire + pas + pres", ["FAIRE", "PAS", "PRES"]),
    "SUIVRE": ("bouger + apres + quelqu'un", ["BOUGER", "APRES", "QUELQU'UN"]),
}

# =============================================================================
# NIVEAU 2 : COMPOSES NSM (35 concepts = 15 originaux + 20 nouveaux)
# =============================================================================

NSM_COMPOSES: Dict[str, Tuple[str, List[str]]] = {
    # --- COMPOSES ORIGINAUX (15) ---
    
    # Communication (6)
    "ECRIRE": ("faire + voir + mot", ["FAIRE", "VOIR", "MOT"]),
    "LIRE": ("voir + mot + savoir", ["VOIR", "MOT", "SAVOIR"]),
    "PARLER": ("dire + mot", ["DIRE", "MOT"]),
    "ECOUTER": ("vouloir + entendre + mot", ["VOULOIR", "SENTIR", "MOT"]),
    "DEMANDER": ("dire + vouloir + savoir", ["DIRE", "VOULOIR", "SAVOIR"]),
    "REPONDRE": ("dire + parce_que + demander", ["DIRE", "PARCE_QUE"]),
    
    # Actions complexes (3)
    "EXPLIQUER": ("dire + parce_que + vouloir + comprendre", ["DIRE", "PARCE_QUE", "VOULOIR", "SAVOIR"]),
    "PROMETTRE": ("dire + vouloir + faire + apres", ["DIRE", "VOULOIR", "FAIRE", "APRES"]),
    "MENTIR": ("dire + pas + vrai", ["DIRE", "PAS", "VRAI"]),
    
    # Activites (6)
    "JOUER": ("faire + vouloir + sentir + bon", ["FAIRE", "VOULOIR", "SENTIR", "BON"]),
    "TRAVAILLER": ("faire + parce_que + vouloir + avoir", ["FAIRE", "PARCE_QUE", "VOULOIR", "AVOIR"]),
    "ACHETER": ("donner + quelque_chose + pour + avoir", ["DONNER", "QUELQUE_CHOSE", "AVOIR"]),
    "VENDRE": ("donner + pour + avoir + quelque_chose", ["DONNER", "AVOIR", "QUELQUE_CHOSE"]),
    "CONSTRUIRE": ("faire + quelque_chose + devenir", ["FAIRE", "QUELQUE_CHOSE"]),
    "DETRUIRE": ("faire + quelque_chose + pas + etre", ["FAIRE", "QUELQUE_CHOSE", "PAS", "ETRE"]),
    
    # --- NOUVEAUX COMPOSES (20) ---
    
    # Communication avancee (5)
    "RACONTER": ("dire + arriver + avant", ["DIRE", "ARRIVER"]),
    "DISCUTER": ("dire + quelqu'un + dire + je", ["DIRE", "QUELQU'UN", "JE"]),
    "ARGUMENTER": ("dire + parce_que + vrai", ["DIRE", "PARCE_QUE", "VRAI"]),
    "CRITIQUER": ("dire + mauvais", ["DIRE", "MAUVAIS"]),
    "LOUER": ("dire + bon", ["DIRE", "BON"]),
    
    # Education (4)
    "ETUDIER": ("vouloir + savoir + faire + longtemps", ["VOULOIR", "SAVOIR", "FAIRE", "LONGTEMPS"]),
    "PRATIQUER": ("faire + beaucoup + vouloir + bon", ["FAIRE", "BEAUCOUP", "VOULOIR", "BON"]),
    "EXPLORER": ("bouger + vouloir + savoir + nouveau", ["BOUGER", "VOULOIR", "SAVOIR"]),
    "EXPERIMENTER": ("faire + vouloir + savoir + si + arriver", ["FAIRE", "VOULOIR", "SAVOIR", "SI", "ARRIVER"]),
    
    # Creation (4)
    "CREER": ("faire + nouveau + avant + pas", ["FAIRE", "PAS"]),
    "DESSINER": ("faire + voir + avec + main", ["FAIRE", "VOIR"]),
    "CHANTER": ("faire + entendre + mot + bon", ["FAIRE", "MOT", "BON"]),
    "DANSER": ("bouger + corps + vouloir + bon", ["BOUGER", "CORPS", "VOULOIR", "BON"]),
    
    # Organisation sociale (4)
    "ORGANISER": ("faire + gens + savoir + faire", ["FAIRE", "GENS", "SAVOIR", "FAIRE"]),
    "DIRIGER": ("dire + gens + vouloir + faire", ["DIRE", "GENS", "VOULOIR", "FAIRE"]),
    "OBEIR": ("faire + parce_que + quelqu'un + dire", ["FAIRE", "PARCE_QUE", "QUELQU'UN", "DIRE"]),
    "COOPERER": ("faire + ensemble + vouloir + le_meme", ["FAIRE", "VOULOIR", "LE_MEME"]),
    
    # Economie (3)
    "PAYER": ("donner + quelque_chose + parce_que + avoir", ["DONNER", "QUELQUE_CHOSE", "PARCE_QUE", "AVOIR"]),
    "GAGNER": ("faire + avoir + apres", ["FAIRE", "AVOIR", "APRES"]),
    "PERDRE": ("avant + avoir + maintenant + pas + avoir", ["AVOIR", "PAS"]),
}

# =============================================================================
# FONCTIONS D'ACCES
# =============================================================================

def get_primitive(nom: str) -> Optional[PrimitiveNSM]:
    """Recupere une primitive par son nom"""
    return NSM_PRIMITIVES.get(nom.upper())

def get_molecule(nom: str) -> Optional[Tuple[str, List[str]]]:
    """Recupere une molecule par son nom"""
    return NSM_MOLECULES.get(nom.upper())

def get_compose(nom: str) -> Optional[Tuple[str, List[str]]]:
    """Recupere un compose par son nom"""
    return NSM_COMPOSES.get(nom.upper())

def get_concept(nom: str) -> Optional[Tuple[str, List[str]]]:
    """Recupere n'importe quel concept (molecule ou compose)"""
    return get_molecule(nom) or get_compose(nom)

def list_by_category(categorie: CategorieNSM) -> List[PrimitiveNSM]:
    """Liste toutes les primitives d'une categorie donnee"""
    return [p for p in NSM_PRIMITIVES.values() if p.categorie == categorie]

def get_statistics() -> Dict[str, int]:
    """Retourne les statistiques globales du systeme NSM"""
    return {
        "primitives": len(NSM_PRIMITIVES),
        "molecules": len(NSM_MOLECULES),
        "composes": len(NSM_COMPOSES),
        "total": len(NSM_PRIMITIVES) + len(NSM_MOLECULES) + len(NSM_COMPOSES),
        "categories": len(CategorieNSM)
    }

def list_all_concepts() -> Dict[str, List[str]]:
    """Liste tous les concepts par niveau"""
    return {
        "NIVEAU_0_PRIMITIVES": list(NSM_PRIMITIVES.keys()),
        "NIVEAU_1_MOLECULES": list(NSM_MOLECULES.keys()),
        "NIVEAU_2_COMPOSES": list(NSM_COMPOSES.keys())
    }

# =============================================================================
# TEST ET VALIDATION
# =============================================================================

if __name__ == "__main__":
    print("=== NSM PRIMITIVES COMPLET - BASE DE DONNEES ENRICHIE ===\n")
    
    stats = get_statistics()
    print(f"Statistiques globales:")
    print(f"  - Primitives (NIVEAU 0) : {stats['primitives']}")
    print(f"  - Molecules (NIVEAU 1)  : {stats['molecules']}")
    print(f"  - Composes (NIVEAU 2)   : {stats['composes']}")
    print(f"  - TOTAL                 : {stats['total']} concepts")
    print(f"  - Categories            : {stats['categories']}")
    
    print("\n=== EXEMPLE DE DECOMPOSITION ===\n")
    
    # Test decomposition JALOUSIE
    concept = "JALOUSIE"
    decomp = get_molecule(concept)
    if decomp:
        print(f"{concept}:")
        print(f"  Formule : {decomp[0]}")
        print(f"  Primitives : {decomp[1]}")
    
    # Test decomposition COOPERER
    concept = "COOPERER"
    decomp = get_compose(concept)
    if decomp:
        print(f"\n{concept}:")
        print(f"  Formule : {decomp[0]}")
        print(f"  Primitives : {decomp[1]}")
    
    # Test decomposition EXPERIMENTER
    concept = "EXPERIMENTER"
    decomp = get_compose(concept)
    if decomp:
        print(f"\n{concept}:")
        print(f"  Formule : {decomp[0]}")
        print(f"  Primitives : {decomp[1]}")
    
    print("\n=== CATEGORIES PRIMITIVES ===\n")
    for cat in CategorieNSM:
        prims = list_by_category(cat)
        if prims:
            print(f"{cat.value} ({len(prims)}) : {', '.join([p.nom for p in prims[:5]])}{'...' if len(prims) > 5 else ''}")
    
    print("\n=== VALIDATION COMPLETE ===")
    print("Toutes les definitions sont chargees et accessibles.")
